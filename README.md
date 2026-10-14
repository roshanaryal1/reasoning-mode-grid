# Reasoning Mode Beats Model Identity

[![CI](https://github.com/roshanaryal1/reasoning-mode-grid/actions/workflows/ci.yml/badge.svg)](https://github.com/roshanaryal1/reasoning-mode-grid/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Code: MIT](https://img.shields.io/badge/code-MIT-green)
![Data: CC--BY--4.0](https://img.shields.io/badge/data-CC--BY--4.0-lightgrey)

A controlled model x mode grid. It tests one claim:

> Holding weights and prompt fixed, switching a model's reasoning mode on or off changes
> the grounding and constraint-reasoning quality of its answer more than switching
> between comparable models does.

This is paper **LA-P4** in the llm-architects programme. It reuses the frozen prompt and
the v2 rubric from [LLMs as Systems Architects](https://github.com/roshanaryal1/llm-architects)
(LA-P1), and it unblocks LA-P5 (the benchmark), which needs proof that the rubric is
portable across a grid.

## Status

| | |
|---|---|
| Stage | Harness built and tested. Pre-registration frozen 2026-10-13 (tag `prereg-v1`) and registered on OSF: <https://osf.io/nj2zp/>. **All 60 chat captures and the 12 API checks are collected** (2026-10-13 to 2026-10-15). No scores yet. |
| Pilot | n = 1 family (DeepSeek, 3 modes, web app, v1 rubric). See [the pilot note](data/pilot/README.md): the adjudicated pilot scores do **not** yet support the claim. |
| Design | 6 families x 2 modes x 5 replicates = 60 chat-app runs, 12 cells, plus 12 API calls that verify each mode switch |
| Venue | arXiv, then an ICLR 2027 workshop (about Feb 2027) plus TMLR. See [venues](docs/venues.md) |
| Next | Blind scoring by three raters ([runbook](docs/runbook.md) Phase 3). The LLM raters are named in [`data/scores/raters.md`](data/scores/raters.md). The human rater is still to be named. API check results: [`results/mode_check.md`](results/mode_check.md) |

## What you get

- `modegrid`, a Python CLI that covers the whole pipeline: plan, run, capture, blind,
  score, agreement, analysis, power.
- A pre-registered analysis: a two-way variance decomposition (model family, mode,
  interaction, residual) per rubric dimension, with bootstrap CIs, permutation tests,
  a rank-based check and a length-adjusted check.
- Chat-app capture templates for the 60 scored runs, plus API adapters for a 12-call
  check that each mode switch works. The reasoning switch lives in YAML, not code.
- Blinded rater packets, so raters never see which model or mode wrote an answer.
- CI that runs lint, types, tests on Python 3.10 to 3.13, and validates the data.

## Quick start

```bash
git clone https://github.com/roshanaryal1/reasoning-mode-grid
cd reasoning-mode-grid
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,providers]"

make check          # lint, types, tests, data validation
modegrid demo       # full pipeline on SYNTHETIC data, no API calls, no cost
modegrid plan       # writes data/manifest/runs.csv (60 runs, random order)
modegrid new-capture claude__fast__p1-v1__r1   # template for one chat run
modegrid run --dry-run                          # the 12 API mode checks
```

The full step-by-step guide is [docs/runbook.md](docs/runbook.md).

## How the study works

```text
configs/grid.yaml --plan--> runs.csv --new-capture (60 chat) / run (12 API)--> data/captures/*.md
                                                                  |
                                                                blind
                                                                  v
              packets/answers/B001.md ... + scoresheet-human.csv, scoresheet-llm-a.csv, scoresheet-llm-b.csv
                                                                  |
                                          raters score blind (v2 rubric + web verification)
                                                                  v
                 agreement --> consensus (median of 3) --> unblind --> data/scores/adjudicated.csv
                                                                                |
                                                                             analyze
                                                                                v
                                                                 results/variance_table.md
```

## Repository layout

| Path | What it holds |
|---|---|
| `configs/grid.yaml` | The experimental design: families, modes, vendor parameters |
| `src/modegrid/` | The harness and the statistics |
| `tests/` | Unit and pipeline tests. No network, no keys |
| `vendor/llm-architects/` | Frozen prompt, rubric and memory-budget checker, pinned by commit and hash |
| `data/manifest/` | The randomised run order |
| `data/captures/` | One verbatim capture per run (write-once) |
| `data/scores/` | Rater sheets and the adjudicated table |
| `data/pilot/` | The three DeepSeek captures from LA-P1, exploratory only |
| `results/` | Analysis outputs |
| `docs/` | Runbook, pre-registration, mode registry, scoring, analysis, power, threats |
| `paper/` | Paper outline |

## Documentation

- [Runbook](docs/runbook.md): what to do, in order, from today to submission
- [Pre-registration](docs/preregistration.md): hypotheses, design, primary analysis, exclusions
- [Mode registry](docs/mode-registry.md): what "fast" and "reasoning" mean for each vendor
- [Scoring protocol](docs/scoring.md): blinding, rubric v2, web verification, adjudication
- [Analysis](docs/analysis.md): the statistics in plain language
- [Power](docs/power.md): why 5 replicates
- [Threats to validity](docs/threats-to-validity.md)
- [Scorers and outside help](docs/collaboration.md): how scoring stays blind with a single author
- [Venues and timeline](docs/venues.md): where to submit and how long each route takes
- [Related work](docs/related-work.md): closest prior work and how this study differs
- [Paper plan](docs/paper-plan.md) and [outline](paper/outline.md)

## Citation

See [CITATION.cff](CITATION.cff). Please also cite LA-P1, whose instrument this reuses.

## Licence

Code: MIT ([LICENSE](LICENSE)). Data, prompts and docs: CC-BY-4.0 ([LICENSE-DATA](LICENSE-DATA)).
Captured model output stays attributable to the system that produced it.

Affiliation on every export: **Independent Researcher, Auckland, New Zealand.**
