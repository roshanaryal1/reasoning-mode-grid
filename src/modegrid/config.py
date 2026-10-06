"""Load and check configs/grid.yaml."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PLACEHOLDER_MARKERS = ("FILL-ME", "VERIFY")


class ConfigError(ValueError):
    """Raised when the grid config is malformed."""


@dataclass(frozen=True)
class Mode:
    id: str
    native_label: str
    params: dict[str, Any]
    primary: bool = True
    model: str | None = None  # per-mode override, for vendors that expose a mode as a model name
    web_label: str | None = None  # what to select in the chat app, for web runs

    @property
    def chat_label(self) -> str:
        return self.web_label or self.native_label


@dataclass(frozen=True)
class Family:
    """One model family. `model` is the fixed weights, modes only change how they run."""

    id: str
    vendor: str
    channel: str  # channel for the main runs: "web" (chat app) or "api"
    adapter: str | None
    model: str
    modes: dict[str, Mode]
    base_url: str | None = None
    api_key_env: str | None = None
    redact_terms: tuple[str, ...] = ()
    notes: str = ""
    max_tokens: int | None = None  # API-check output limit for this family; None uses the grid's


@dataclass(frozen=True)
class PromptSpec:
    id: str
    path: Path
    sha256: str
    extract: str = "between-markers"

    def text(self) -> str:
        raw = self.path.read_text(encoding="utf-8")
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        if digest != self.sha256:
            raise ConfigError(
                f"prompt {self.id}: sha256 mismatch ({digest} != {self.sha256}). "
                "Prompts are frozen. Add a new prompt id instead of editing one."
            )
        if self.extract == "whole-file":
            return raw
        # Markers count only on a line of their own. The file header mentions them inline.
        match = re.search(r"^=== PROMPT START ===\s*$(.*?)^=== PROMPT END ===\s*$", raw, re.M | re.S)
        if not match:
            raise ConfigError(f"prompt {self.id}: missing PROMPT START / PROMPT END marker lines")
        return match.group(1).strip() + "\n"


@dataclass(frozen=True)
class Grid:
    study: str
    seed: int
    replicates: int
    max_tokens: int
    prompts: tuple[PromptSpec, ...]
    families: tuple[Family, ...]
    global_redact_terms: tuple[str, ...] = field(default_factory=tuple)
    api_check_replicates: int = 0  # API calls per family x mode, outside the main grid

    def family(self, family_id: str) -> Family:
        for fam in self.families:
            if fam.id == family_id:
                return fam
        raise KeyError(family_id)

    def prompt(self, prompt_id: str) -> PromptSpec:
        for p in self.prompts:
            if p.id == prompt_id:
                return p
        raise KeyError(prompt_id)


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return any(m in value for m in PLACEHOLDER_MARKERS)
    if isinstance(value, dict):
        return any(_contains_placeholder(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_placeholder(v) for v in value)
    return False


def load_grid(path: str | Path) -> Grid:
    path = Path(path)
    root = path.resolve().parent.parent  # configs/ lives at the repo root
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError("grid config must be a mapping")

    try:
        prompts = tuple(
            PromptSpec(
                id=p["id"],
                path=(root / p["path"]),
                sha256=p["sha256"],
                extract=p.get("extract", "between-markers"),
            )
            for p in data["prompts"]
        )
        families = []
        for f in data["families"]:
            modes = {
                mid: Mode(
                    id=mid,
                    native_label=m["native_label"],
                    params=m.get("params") or {},
                    primary=bool(m.get("primary", True)),
                    model=str(m["model"]) if m.get("model") else None,
                    web_label=m.get("web_label"),
                )
                for mid, m in f["modes"].items()
            }
            families.append(
                Family(
                    id=f["id"],
                    vendor=f["vendor"],
                    channel=f["channel"],
                    adapter=f.get("adapter"),
                    model=str(f["model"]),
                    modes=modes,
                    base_url=f.get("base_url"),
                    api_key_env=f.get("api_key_env"),
                    redact_terms=tuple(f.get("redact_terms") or ()),
                    notes=f.get("notes", ""),
                    max_tokens=_family_max_tokens(f),
                )
            )
        grid = Grid(
            study=data["study"],
            seed=int(data["seed"]),
            replicates=int(data["replicates"]),
            max_tokens=int(data.get("max_tokens", 32000)),
            prompts=prompts,
            families=tuple(families),
            global_redact_terms=tuple(data.get("global_redact_terms") or ()),
            api_check_replicates=int((data.get("api_check") or {}).get("replicates", 0)),
        )
    except KeyError as exc:
        raise ConfigError(f"missing required key: {exc}") from exc

    check_grid(grid)
    return grid


def _family_max_tokens(f: dict[str, Any]) -> int | None:
    value = f.get("max_tokens")
    if value is None:
        return None
    if type(value) is not int:  # bool is an int subclass; reject it and floats explicitly
        raise ConfigError(f"{f.get('id')}: max_tokens must be a whole number, got {value!r}")
    return value


def check_grid(grid: Grid) -> None:
    """Structural rules. Placeholders are allowed here and caught by `unready_families`."""
    if grid.replicates < 3:
        raise ConfigError("replicates must be >= 3 (pre-registered minimum)")
    if grid.api_check_replicates < 0:
        raise ConfigError("api_check.replicates must be >= 0")
    ids = [f.id for f in grid.families]
    if len(ids) != len(set(ids)):
        raise ConfigError("family ids must be unique")
    for fam in grid.families:
        if fam.channel not in {"api", "web"}:
            raise ConfigError(f"{fam.id}: channel must be 'api' or 'web'")
        if fam.max_tokens is not None and fam.max_tokens <= 0:
            raise ConfigError(f"{fam.id}: max_tokens must be positive")
        if fam.channel == "api" and fam.adapter not in {"anthropic", "openai_compatible"}:
            raise ConfigError(f"{fam.id}: api families need adapter anthropic|openai_compatible")
        if fam.adapter not in {None, "anthropic", "openai_compatible"}:
            raise ConfigError(f"{fam.id}: unknown adapter {fam.adapter!r}")
        primary = {m.id for m in fam.modes.values() if m.primary}
        if primary != {"fast", "reasoning"}:
            raise ConfigError(
                f"{fam.id}: exactly the primary modes 'fast' and 'reasoning' are required, "
                f"got {sorted(primary)}. Mark extra modes 'primary: false'."
            )


def unready_families(grid: Grid) -> list[str]:
    """Families whose API settings still hold FILL-ME / VERIFY placeholders."""
    out = []
    for fam in grid.families:
        fields: list[Any] = [fam.model, fam.base_url or ""]
        fields += [m.params for m in fam.modes.values()]
        fields += [m.model or "" for m in fam.modes.values()]
        if any(_contains_placeholder(x) for x in fields):
            out.append(fam.id)
    return out
