"""LLM raters' scores for their own vendor's family, reported separately.

Pre-registration section 4: both LLM raters come from vendors whose families are scored
(`llm-a` Anthropic on `claude`, `llm-b` OpenAI on `gpt`, see data/scores/raters.md), so
their scores for their own vendor's family are also reported on their own.

For one rater and one family this gives, per measure:

- own-family gap: the rater's score minus the mean of the other raters, averaged over that
  family's answers;
- baseline gap: the same on every other family, which captures a rater who is simply
  stricter or more lenient everywhere;
- self-preference: own-family gap minus baseline gap. Positive means the rater scored its
  own vendor's answers higher, relative to the other raters, than it scored the rest.

95% percentile bootstrap CIs resample answers within the own family and within the rest,
seeded. Descriptive: no hypothesis rests on this.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping
from pathlib import Path

import numpy as np

from . import DIMS
from .scores import Scores

MEASURES: tuple[str, ...] = ("total", *DIMS)


def _value(row: dict[str, int], measure: str) -> float:
    return float(sum(row[d] for d in DIMS)) if measure == "total" else float(row[measure])


def _gaps(sheets: dict[str, Scores], rater: str, ids: list[str], measure: str) -> np.ndarray:
    others = [name for name in sheets if name != rater]
    return np.array(
        [_value(sheets[rater][i], measure) - np.mean([_value(sheets[o][i], measure) for o in others]) for i in ids]
    )


def own_vendor(
    sheets: dict[str, Scores],
    rater: str,
    family: str,
    measures: tuple[str, ...] = MEASURES,
    n_boot: int = 5000,
    seed: int = 20261001,
) -> list[dict[str, str | float | int]]:
    if rater not in sheets:
        raise ValueError(f"no sheet for rater {rater!r}; have {sorted(sheets)}")
    if len(sheets) < 2:
        raise ValueError("own-vendor scores need at least one other rater to compare with")
    common = sorted(set.intersection(*(set(s) for s in sheets.values())))
    own = [i for i in common if i.split("__")[0] == family]
    rest = [i for i in common if i.split("__")[0] != family]
    if not own or not rest:
        raise ValueError(f"family {family!r} needs answers both in and outside it (found {len(own)} and {len(rest)})")
    rng = np.random.default_rng(seed)
    rows: list[dict[str, str | float | int]] = []
    for m in measures:
        g_own, g_rest = _gaps(sheets, rater, own, m), _gaps(sheets, rater, rest, m)
        b_own = np.array([rng.choice(g_own, g_own.size).mean() for _ in range(n_boot)])
        b_rest = np.array([rng.choice(g_rest, g_rest.size).mean() for _ in range(n_boot)])
        b_self = b_own - b_rest
        rows.append(
            {
                "rater": rater,
                "family": family,
                "measure": m,
                "n_own": len(own),
                "n_rest": len(rest),
                "own_gap": float(g_own.mean()),
                "own_gap_ci_low": float(np.percentile(b_own, 2.5)),
                "own_gap_ci_high": float(np.percentile(b_own, 97.5)),
                "baseline_gap": float(g_rest.mean()),
                "self_preference": float(g_own.mean() - g_rest.mean()),
                "self_preference_ci_low": float(np.percentile(b_self, 2.5)),
                "self_preference_ci_high": float(np.percentile(b_self, 97.5)),
            }
        )
    return rows


def replaced_consensus(sheets: Mapping[str, Scores], pairs: list[tuple[str, str]]) -> dict[str, dict[str, float]]:
    """Median of the raters after each LLM rater's own-vendor scores are replaced.

    For every (rater, family) pair, that rater's scores on the family's answers become
    the mean of the other raters' scores. Exploratory and not pre-registered: it asks
    whether H4 survives without self-preference. With three raters the median is then
    the mean of the other two, so half points can appear.
    """
    names = list(sheets)
    if len(names) < 3 or len(names) % 2 == 0:
        raise ValueError(f"replaced consensus needs an odd number of raters (3 or more), got {len(names)}")
    for rater, _ in pairs:
        if rater not in sheets:
            raise ValueError(f"no sheet for rater {rater!r}; have {sorted(names)}")
    ids = set(sheets[names[0]])
    if any(set(s) != ids for s in sheets.values()):
        raise ValueError("all raters must score the same answers")
    own = set(pairs)  # a rater may be paired with more than one family
    out: dict[str, dict[str, float]] = {}
    for uid in sorted(ids):
        family = uid.split("__")[0]
        out[uid] = {}
        for d in DIMS:
            values = []
            for name in names:
                if (name, family) in own:
                    values.append(float(np.mean([sheets[o][uid][d] for o in names if o != name])))
                else:
                    values.append(float(sheets[name][uid][d]))
            out[uid][d] = float(np.median(values))
    return out


FIELDS = [
    "rater",
    "family",
    "measure",
    "n_own",
    "n_rest",
    "own_gap",
    "own_gap_ci_low",
    "own_gap_ci_high",
    "baseline_gap",
    "self_preference",
    "self_preference_ci_low",
    "self_preference_ci_high",
]


def write_own_vendor(rows: list[dict[str, str | float | int]], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: f"{v:.4f}" if isinstance(v, float) else v for k, v in r.items()})
    return path
