"""Expand the grid into a randomised run manifest."""

from __future__ import annotations

import csv
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import Grid

MANIFEST_FIELDS = ["order", "run_id", "family", "mode", "primary", "prompt_id", "replicate", "channel", "set"]

MAIN = "main"  # the scored grid
API_CHECK = "api_check"  # one-off API calls that verify each mode switch, never scored


@dataclass(frozen=True)
class Run:
    order: int
    run_id: str
    family: str
    mode: str
    primary: bool
    prompt_id: str
    replicate: int
    channel: str
    set: str = MAIN


def make_run_id(family: str, mode: str, prompt_id: str, replicate: int, run_set: str = MAIN) -> str:
    tag = "r" if run_set == MAIN else "apicheck"
    return f"{family}__{mode}__{prompt_id}__{tag}{replicate}"


def build_manifest(grid: Grid) -> list[Run]:
    """Every family x mode x prompt x replicate, in a seeded random order.

    Randomising execution order stops time-of-day or same-day vendor changes from
    lining up with one mode or one family.

    API-check runs (one per family x primary mode, if `api_check.replicates` > 0)
    are listed after the main grid. They verify that each mode switch does what the
    mode registry claims. They are never blinded, scored or analysed with the grid.
    """
    cells = []
    for fam in grid.families:
        for mode in fam.modes.values():
            for prompt in grid.prompts:
                for rep in range(1, grid.replicates + 1):
                    cells.append((fam, mode, prompt, rep))
    rng = random.Random(grid.seed)
    rng.shuffle(cells)
    runs = [
        Run(
            order=i,
            run_id=make_run_id(fam.id, mode.id, prompt.id, rep),
            family=fam.id,
            mode=mode.id,
            primary=mode.primary,
            prompt_id=prompt.id,
            replicate=rep,
            channel=fam.channel,
        )
        for i, (fam, mode, prompt, rep) in enumerate(cells, start=1)
    ]
    order = len(runs)
    for fam in grid.families:
        if fam.adapter is None:
            continue
        for mode in fam.modes.values():
            if not mode.primary:
                continue
            for rep in range(1, grid.api_check_replicates + 1):
                order += 1
                prompt = grid.prompts[0]
                runs.append(
                    Run(
                        order=order,
                        run_id=make_run_id(fam.id, mode.id, prompt.id, rep, API_CHECK),
                        family=fam.id,
                        mode=mode.id,
                        primary=True,
                        prompt_id=prompt.id,
                        replicate=rep,
                        channel="api",
                        set=API_CHECK,
                    )
                )
    return runs


def write_manifest(runs: list[Run], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        for run in runs:
            writer.writerow(asdict(run))


def read_manifest(path: str | Path) -> list[Run]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return [
            Run(
                order=int(r["order"]),
                run_id=r["run_id"],
                family=r["family"],
                mode=r["mode"],
                primary=r["primary"] == "True",
                prompt_id=r["prompt_id"],
                replicate=int(r["replicate"]),
                channel=r["channel"],
                set=r.get("set") or MAIN,
            )
            for r in csv.DictReader(fh)
        ]
