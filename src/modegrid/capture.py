"""Capture files: one Markdown file per run, YAML front-matter plus verbatim output.

Layout:

    ---
    <front-matter>
    ---

    ## Final answer
    <verbatim, never edited>

    ## Reasoning trace (not shown to raters)
    <verbatim if the vendor exposed one, else NONE>

    ## Run notes
    <free text, append-only>
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

FINAL = "## Final answer"
TRACE = "## Reasoning trace (not shown to raters)"
NOTES = "## Run notes"

REQUIRED_KEYS = (
    "run_id",
    "family",
    "mode",
    "native_label",
    "channel",
    "model_requested",
    "model_returned",
    "prompt_id",
    "prompt_sha256",
    "replicate",
    "date_run",
    "run_by",
)


class CaptureError(ValueError):
    pass


@dataclass
class Capture:
    meta: dict[str, Any]
    final_answer: str
    reasoning_trace: str = "NONE"
    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def run_id(self) -> str:
        return str(self.meta["run_id"])

    def render(self) -> str:
        fm = yaml.safe_dump(self.meta, sort_keys=False, allow_unicode=True).strip()
        return (
            f"---\n{fm}\n---\n\n"
            f"{FINAL}\n\n{self.final_answer.rstrip()}\n\n"
            f"{TRACE}\n\n{(self.reasoning_trace or 'NONE').rstrip()}\n\n"
            f"{NOTES}\n\n{self.notes.rstrip()}\n"
        )


def write_capture(capture: Capture, directory: str | Path, overwrite: bool = False) -> Path:
    path = Path(directory) / f"{capture.run_id}.md"
    if path.exists() and not overwrite:
        raise CaptureError(f"{path} exists. Captures are write-once.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(capture.render(), encoding="utf-8")
    return path


def parse_capture(text: str) -> Capture:
    if not text.startswith("---\n"):
        raise CaptureError("capture must start with YAML front-matter")
    _, fm, body = text.split("---\n", 2)
    meta = yaml.safe_load(fm) or {}
    for heading in (FINAL, TRACE, NOTES):
        if heading not in body:
            raise CaptureError(f"missing section {heading!r}")
    final = body.split(FINAL, 1)[1].split(TRACE, 1)[0].strip()
    trace = body.split(TRACE, 1)[1].split(NOTES, 1)[0].strip()
    notes = body.split(NOTES, 1)[1].strip()
    return Capture(meta=meta, final_answer=final, reasoning_trace=trace, notes=notes)


def read_capture(path: str | Path) -> Capture:
    return parse_capture(Path(path).read_text(encoding="utf-8"))


def check_capture(capture: Capture) -> list[str]:
    problems = [f"missing front-matter key {k!r}" for k in REQUIRED_KEYS if k not in capture.meta]
    if not capture.final_answer or capture.final_answer.startswith("<!--"):
        problems.append("final answer is empty")
    return problems


def manual_template(meta: dict[str, Any]) -> str:
    """Template for a web-UI run. The operator pastes the answer verbatim."""
    meta = {**meta, "model_returned": meta.get("model_returned", "as shown in UI, else 'not shown'")}
    cap = Capture(
        meta=meta,
        final_answer="<!-- Paste the model's final answer VERBATIM. Do not edit. -->",
        reasoning_trace="<!-- Paste the visible reasoning/thinking panel if the UI shows one, else NONE -->",
        notes="<!-- UI path used to select the mode, screenshots taken, anything unusual. -->",
    )
    return cap.render()
