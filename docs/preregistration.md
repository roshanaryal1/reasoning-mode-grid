# Pre-registration: LA-P4

Status: **DRAFT.** Frozen when the `prereg-v1` git tag exists. After that, every change
goes in the Deviations section at the bottom with a date and a reason.

Author: Roshan Aryal, Independent Researcher, Auckland, New Zealand.

## 1. Question

When an LLM answers a hard, constrained systems-design task, does turning its reasoning
mode on or off change answer quality more than swapping to a comparable model from a
different vendor?

## 2. Hypotheses

Measured with the LA-P1 rubric (v2 anchors), nine dimensions scored 0, 1 or 2.

| ID | Dimension | Prediction | Why |
|---|---|---|---|
| H1 | D1 hardware-constraint adherence | mode > model | Fitting a 32 GB budget is arithmetic that benefits from deliberate reasoning |
| H2 | D9 internal consistency | mode > model | The LA-P1 fast-mode DeepSeek captures held the recommend-then-forbid contradictions |
| H3 | D3 tool factuality | model > mode | Which tools a model knows is set by training data, not by thinking time |
| H4 | Total score (sum of D1 to D9) | mode > model | The headline claim |

D2, D4, D5, D6, D7, D8 are reported with the same statistics but carry no directional
prediction.

"Mode > model" on a dimension means the primary statistic below is positive and its
95% CI excludes zero. "Model > mode" means it is negative and the CI excludes zero.
Anything else is "inconclusive".

## 3. Design

- **Factors.** Model family (6 levels: Claude, GPT, Gemini, Qwen, DeepSeek, Grok) crossed
  with mode (2 levels: fast, reasoning). Within a family the weights are fixed. The
  vendor-specific settings for each level are in `configs/grid.yaml` and
  [mode-registry.md](mode-registry.md).
- **Replicates.** 5 independent runs per cell, fresh session each time. 60 runs total.
  Rationale in [power.md](power.md).
- **Prompt.** `prompt-v1` from LA-P1, unchanged, sha256 pinned in the config.
- **Order.** Execution order is randomised with seed 20261001 (`data/manifest/runs.csv`).
- **Settings.** Vendor default sampling settings. Browsing and tools off where the
  interface allows it. `max_tokens` 32,000.

## 4. Measurement

- Rubric: `vendor/llm-architects/docs/rubric.md`, v2 hard anchors for D1, D7, D8, D9.
- At least two independent raters, blind to family and mode (see [scoring.md](scoring.md)).
- D3 and D4 require web verification of every named tool and model, as of the capture date.
- D1 requires running `memory_budget.py` on the answer's co-resident model set.
- Reliability: Krippendorff's ordinal alpha per dimension. Bar: 0.667.
- Disagreements are adjudicated with a written reason. The adjudicated score is the
  analysis unit.

## 5. Primary analysis

For each dimension, and for the total, fit a balanced two-way fixed-effects decomposition
(family, mode, family x mode, residual) on the 60 adjudicated scores.

Primary statistic:

```text
delta = omega2(mode) - omega2(family)
```

omega squared is used rather than eta squared because family has 5 degrees of freedom and
mode has 1. eta squared rewards extra degrees of freedom even when they carry only noise.

Uncertainty: 95% percentile bootstrap CI for delta, 5,000 resamples, resampling the
replicates within each cell. Families are treated as fixed, so the inference is about
these six families, not all possible models. The paper will say so.

Secondary statistics, reported for every dimension: eta squared for each source,
permutation p-values for the mode and family main effects (5,000 permutations), and the
random-effects variance components.

No correction for multiple comparisons across the four hypotheses, because each one is a
separate pre-stated prediction. The 6 non-directional dimensions are descriptive.

## 6. Robustness checks (pre-registered, reported regardless of result)

1. Rank transform: the same analysis on ranked scores.
2. Length adjustment: residualise scores on log output tokens, then re-run. If the mode
   effect vanishes, the paper reports that reasoning modes score higher because they write
   longer answers, not because they reason better.
3. Rater-level analysis: run the decomposition on each rater's raw scores separately.

## 7. Exclusions and replacements

- A run is **replaced** (re-run once, same cell, new run id suffix `-rerun`) only if:
  the API returned an error, the output was truncated by `max_tokens`, or the vendor
  refused the request outright. The original capture stays in the repo with a note.
- A run is **never** replaced because its score is low or the answer is odd.
- If a family cannot complete both modes (vendor removes the mode, account blocked),
  the whole family is dropped and reported. The design stays balanced.
- Minimum to report confirmatory results: 5 complete families.

## 8. Stopping rule

Data collection stops at 60 runs. No interim analysis of real scores. The demo and power
commands use synthetic data only.

## 9. Pilot data

The three DeepSeek captures from LA-P1 (`data/pilot/`) were collected before this
pre-registration, with the v1 rubric, n = 1 per cell. They motivated the study. They are
not part of the confirmatory analysis. Their adjudicated totals (reasoning 8, fast 9,
instant plus DeepThink 6) do not show a reasoning advantage on the total score, which is
stated here so the result cannot be framed as a confirmation of the pilot.

## 10. Deviations

| Date | Change | Reason |
|---|---|---|
| | | |
