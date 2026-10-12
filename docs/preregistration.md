# Pre-registration: LA-P4

Status: **DRAFT.** Frozen when the `prereg-v1` git tag exists. After that, every change
goes in the Deviations section at the bottom with a date and a reason.

Author: Roshan Aryal, Independent Researcher, Auckland, New Zealand.

## 1. Question

When an LLM answers a hard, constrained systems-design task, does turning its reasoning
mode on or off change answer quality more than swapping to a comparable model from a
different vendor?

**Estimand.** The primary test compares the *average* (main) effect of mode with the
average effect of family: how much of the score variance each explains. It is not the
typical size of one family's individual mode switch; those per-family differences and the
family x mode interaction are reported alongside (section 5). Two claims are kept apart:
"mode matters more than family" (variance) and "reasoning improves quality" (direction).
Hypotheses H1, H2 and H4 need both.

**Scope.** Conclusions are limited to the LA-P1 prompt, these six families, the tested chat
settings, and the collection period. One prompt means the replicates measure variability on
that task, not across systems-design tasks.

**Comparable models.** For each vendor: a current general-purpose chat model in the
vendor's own app, available to the author's individual account, that offers both a fast and
a reasoning setting. Where an app offers more than one such model, the tie-break is the one
recorded in `configs/grid.yaml` before the first scored capture. The choice is fixed here:

| Family | Model | App |
|---|---|---|
| Claude | Claude Sonnet 5.5 | claude.ai |
| GPT | GPT-5.6 Sol | chatgpt.com |
| Gemini | Gemini 3.6 Flash | gemini.google.com |
| Qwen | Qwen3.8-Max | chat.qwen.ai |
| DeepSeek | DeepSeek-V4-Pro | chat.deepseek.com |
| Grok | Grok 4.6 | grok.com |

These are not all each vendor's top model (Claude Opus 5.5 and Gemini 3.1 Pro exist), and
they are not matched on size or price. The paper says so. The mode settings for each are
in [mode-registry.md](mode-registry.md).

## 2. Hypotheses

Measured with the LA-P1 rubric (v2 anchors), nine dimensions scored 0, 1 or 2.

| ID | Role | Dimension | Prediction | Why |
|---|---|---|---|---|
| H4 | **Confirmatory** | Total score (sum of D1 to D9) | mode > model, and reasoning > fast | The headline claim |
| H1 | Secondary | D1 hardware-constraint adherence | mode > model, and reasoning > fast | Fitting a 32 GB budget is arithmetic that benefits from deliberate reasoning |
| H2 | Secondary | D9 internal consistency | mode > model, and reasoning > fast | The LA-P1 fast-mode DeepSeek captures held the recommend-then-forbid contradictions |
| H3 | Secondary | D3 tool factuality | model > mode | Which tools a model knows is set by training data, not by thinking time |

H4 is the single confirmatory test. H1 to H3 are pre-specified secondary tests, reported
uncorrected with an explicit multiplicity caveat; they cannot by themselves carry the
paper's conclusion.

D2, D4, D5, D6, D7, D8 are reported with the same statistics but carry no directional
prediction.

**Competing prediction for H3.** Work on reasoning-trained models reports that they
hallucinate more than comparable non-reasoning models (for example Li and Ng, arXiv
2505.24630v2, who find that reasoning-oriented RL fine-tuning "significantly increases the
prevalence of hallucinations"). That work compares differently trained models, not one
model with inference-time reasoning switched on and off, so it is motivation, not direct
evidence about this manipulation. If the pattern carries over, mode would matter for D3
too, in the direction of reasoning scoring lower. H3 stays as stated. A result of "mode > model" on D3 with
reasoning lower would support the hallucination account, and the paper will say so.
See [related-work.md](related-work.md).

"Mode > model" on a dimension means the primary statistic below is positive and its
95% CI excludes zero. "Model > mode" means it is negative and the CI excludes zero.
Anything else is "inconclusive". A dimension flagged low-variance (section 5) makes its
hypothesis inconclusive, whatever the CI says. "Reasoning > fast" means the reasoning-minus-fast mean
difference (section 5) has a 95% CI entirely above zero. A hypothesis that predicts both
is supported only if both hold; "mode > model" with reasoning not better is reported as
"mode matters, but reasoning is not better", not as support.

## 3. Design

- **Factors.** Model family (6 levels: Claude, GPT, Gemini, Qwen, DeepSeek, Grok) crossed
  with mode (2 levels: fast, reasoning). Within a family the weights are fixed. The
  vendor-specific settings for each level are in `configs/grid.yaml` and
  [mode-registry.md](mode-registry.md).
- **Channel.** All 60 scored runs are captured in each vendor's own chat app, the way
  people use these models and the way LA-P1 was captured. Fresh chat each time, signed
  in, memory off, no custom instructions, no files. A screenshot of the mode selector is
  kept for every run.
- **Same model in both modes.** Each capture records the model name the app shows and a
  screenshot of the selector. A family passes if the app shows the same model name in both
  modes and the vendor documents the setting as a mode of that model (see
  [mode-registry.md](mode-registry.md)). If a capture shows a different model, that run is
  replaced once (section 7); if it recurs, the family is dropped. Where the app shows no
  model name or the vendor's routing cannot be verified, the paper describes that family's
  contrast as vendor-exposed chat settings, not a proven same-weights manipulation.
- **Capture window and drift.** Each family's 10 runs inside 48 hours; all 60 inside 14
  days. Vendor release notes published during the window are recorded in the mode
  registry. A family block that overruns 48 hours (for example, an outage) is still
  completed, and the overrun is reported.
- **Timestamps.** `modegrid new-capture` writes `date_stamped` and `date_run`, both the UTC
  time the template was made. Make the template immediately before sending the prompt.
  `date_stamped` is never edited. If the prompt was sent later, `date_run` is corrected and
  `date_note` says why; `modegrid validate` rejects a changed `date_run` with no note.
- **Replicates.** 5 independent runs per cell. 60 runs total. Rationale in [power.md](power.md).
- **API mode check.** Separately, 1 API call per family and mode (12 calls) with the
  documented API equivalent of each chat mode. These show that each mode switch changes
  reasoning (reasoning tokens or a reasoning trace) and record which model answered. They
  do not prove what the chat app runs internally; they show the documented switch exists
  and does what the vendor says.
  They are never scored, never blinded and never pooled with the 60 chat runs. Results
  go to `results/mode_check.md` and the paper appendix.
- **Pinned inputs.** `prompt-v1` from LA-P1, unchanged, sha256 pinned in the config. The
  rubric and `memory_budget.py` are pinned by sha256 in `vendor/llm-architects/SHA256SUMS`.
  The `modegrid` code is pinned by the commit of the `prereg-v1` tag. The LLM raters'
  instructions are written, hashed (sha256) and recorded in `data/scores/raters.md` before
  scoring starts.
- **Order.** The manifest (`data/manifest/runs.csv`) is a random order made with seed
  20261001. Families are captured one block at a time, in the order each family first
  appears in the manifest. Inside a block, runs follow manifest order, which mixes fast and
  reasoning runs. This keeps the seeded order and the 48-hour block rule both true; it means
  family is partly confounded with calendar date, which the paper states.
- **Settings.** Vendor defaults. Web search and tools off where the app allows it. If an
  app cannot turn search off, that is recorded in the capture and the mode registry.

## 4. Measurement

- Rubric: `vendor/llm-architects/docs/rubric.md`, v2 hard anchors for D1, D7, D8, D9.
- Three independent raters, blind to family and mode: one human who is not an author and
  two LLMs from different vendors, each named with model id and run date before scoring,
  with live web search (see [scoring.md](scoring.md)). The author does not score.
- LLM raters' scores for their own vendor's family are also reported separately.
- D3 and D4 require web verification of every named tool and model. Raters record the date
  they scored and the URL checked. A tool counts as real if it existed by the capture date;
  a source showing it was released after the capture date is noted.
- D1 requires running `memory_budget.py` on the answer's co-resident model set.
- Reliability: Krippendorff's ordinal alpha per dimension across the three raters, and
  interval alpha on the total score. Bar: 0.667. A dimension below the bar is reported in
  full but is exploratory: it cannot confirm or refute its hypothesis. H4 stays
  confirmatory if the total score's alpha is at or above the bar, even when some component
  dimensions fall below it. 0.667 is the conventional floor for tentative conclusions, with
  0.800 the usual level for firm ones; a supported result with alpha between the two is
  described as tentative.
- Blinding procedure (`modegrid blind`). Raters see only the final answer: reasoning
  traces, interface labels, timestamps and capture metadata are never in the packet.
  Self-identification lines near the top of an answer are removed. In the body, a vendor or
  model name is masked as `[REDACTED]` only inside a self-reference ("I'm Claude", "As
  ChatGPT, ...", "developed by Google"). Names used as content stay: the prompt asks for a
  model and tool stack, and D2 to D4 cannot be scored if recommended models and tools are
  hidden. An answer that favours its own vendor's models may still hint at its family;
  the guess check below measures that. Formatting is left as written, because it is part
  of the answer. Each rater gets an independent reading order. Raters guess family and mode
  for every answer; the guess accuracy against chance is reported as the blinding-failure
  rate (`modegrid blinding-check`). The original captures are never edited.
- **Refusals.** An outright refusal (the answer declines the task and recommends no
  models, tools or plan) scores 0 on all nine dimensions. The rubric assumes an answer
  exists; without this rule a refusal would earn 2s on D3, D5 and D9 for naming nothing.
  An answer that does part of the task is scored normally. Each rater applies the rule
  independently, and the median settles disagreement.
- The analysis unit is the median of the three raters' scores for each answer and
  dimension (`modegrid consensus`). No hand adjudication: the only possible adjudicator,
  the author, is not blind.

## 5. Primary analysis

For each dimension, and for the total, fit a balanced two-way fixed-effects decomposition
(family, mode, family x mode, residual) on the 60 consensus scores (median of the three
raters).

Primary statistic:

```text
delta = omega2(mode) - omega2(family)
```

Omega squared is the non-partial form, with the total as denominator:

```text
omega2(effect) = (SS_effect - df_effect * MS_residual) / (SS_total + MS_residual)
```

Negative estimates are kept, not truncated at zero. Omega squared is used rather than eta
squared because family has 5 degrees of freedom and mode has 1, and eta squared rewards
extra degrees of freedom even when they carry only noise.

Direction: `mode_effect = mean(reasoning) - mean(fast)` over all 60 consensus scores, with a
95% percentile bootstrap CI from the same resamples as delta.

Interaction: omega squared for family x mode, and each family's reasoning-minus-fast
difference, are reported for every dimension (`results/family_mode_effects.csv`). If the
interaction's omega squared exceeds both main effects, the paper states that the main-effect
comparison does not summarise the data well and interprets the per-family differences.
This does not change H4's status, because H4's estimand is the average effect (section 1);
the result is labelled "average effect only; interaction exceeds both main effects".

Low variance: if 90% or more of a dimension's 60 scores share one value, the dimension is
reported as uninformative and any hypothesis on it as inconclusive; omega squared and its
bootstrap are unstable near zero variance. If all 60 scores are identical, omega squared is
undefined and the dimension is reported as "no variance", also inconclusive. Bootstrap
resamples in which omega squared is undefined are dropped before the CI is computed.

Uncertainty: 95% percentile bootstrap CI for delta, 5,000 resamples, resampling the
replicates within each cell, seed 20261001. Families are treated as fixed, so the inference is about
these six families, not all possible models. The paper will say so. The bootstrap CI decides
every verdict. With 5 replicates per cell percentile intervals can be too narrow, so the
permutation p-values are reported beside them, and any disagreement (CI excludes zero but
p >= 0.05, or the reverse) is reported, not resolved in favour of either.

Secondary statistics, reported for every dimension: eta squared for each source;
permutation p-values for the mode and family effects (5,000 permutations); and the
random-effects variance components, labelled exploratory because a random-effects reading
assumes something different about families than the fixed-family primary analysis. The
mode permutation shuffles scores across the two modes within each family (and the family
permutation across families within each mode), so it tests the strict null that mode makes
no difference in any family. It is labelled as such and is not a test of the average mode
effect. It assumes runs within a family are exchangeable across modes under that null.

Multiplicity: H4 is the only confirmatory test and is not corrected. H1 to H3 are reported
uncorrected as secondary tests, with the multiplicity caveat stated beside them. The 6
non-directional dimensions are descriptive.

Power ([power.md](power.md)) was simulated for delta alone and for the full H4 rule (delta
CI above zero and reasoning-minus-fast CI above zero). The two agree in every scenario
where reasoning helps; the simulation models one 0 to 2 dimension, not the nine-part total.

## 6. Robustness checks (pre-registered, reported regardless of result)

1. Rank transform: the same analysis on ranked scores.
2. Length adjustment: residualise scores on log answer length in words, then re-run.
   Words, not tokens, because chat apps report no token counts and tokenizers differ. This
   is a sensitivity analysis. Answer length is itself affected by mode, so if the mode
   effect shrinks after adjustment, the paper reports that the mode effect is not separable
   from answer length, not that length caused it.
3. Rater-level analysis: run the decomposition on each rater's raw scores separately.
4. Split by fast-mode floor. Three families can switch reasoning fully off in fast mode
   (GPT, Qwen, DeepSeek). Three can only lower it to a minimum (Claude Sonnet 5.5,
   Gemini 3.6 Flash, Grok 4.6; see [mode-registry.md](mode-registry.md)). Run the
   primary analysis on each group of three separately
   (`modegrid analyze --families gpt,qwen,deepseek` and
   `--families claude,gemini,grok`). Each group has 30 runs, so these are descriptive
   and carry no hypothesis test of their own. If H1, H2 or H4 holds in the pooled
   analysis but only in the true-off group, the paper reports the claim as holding for
   reasoning off vs on, not for reasoning minimised vs on. If a family is dropped
   under section 7, its group is analysed with the families that remain, and a group
   with fewer than 2 families is not analysed.

## 7. Exclusions and replacements

- A run is **replaced** only if: the app or API returned an error, the answer was visibly
  cut off in transmission, or the app silently used a different model or mode than the one
  selected (visible in the screenshot). The replacement keeps the same run id; the failed
  capture moves to `data/captures/superseded/` with a line in its README saying why. It is
  never deleted.
- Up to **2 replacements per cell** for errors or cut-offs, so one bad day for an app does
  not cost the family. A different model showing up is handled separately: one
  replacement, and if it happens again in that family, the family is dropped.
- An outright **refusal is an outcome, not a failure.** It is kept, blinded and scored with
  the rubric like any other answer, and refusal counts are reported per family and mode.
- If a cell still has no valid run after its replacements, that cell is incomplete and the
  family is dropped under the rule below. The number of attempted captures is reported
  next to the 60 planned valid runs.
- A run is **never** replaced because its score is low or the answer is odd.
- If a family cannot complete both modes (vendor removes the mode, account blocked),
  the whole family is dropped and reported. The design stays balanced.
- Minimum to report confirmatory results: 5 complete families.

## 8. Stopping rule

Data collection stops at 10 valid runs per family for every family still in the study:
60 if no family is dropped, 50 if one is (plus any permitted re-runs). No interim analysis
of real scores. The demo and power commands use synthetic data only.

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
