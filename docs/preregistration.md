# Pre-registration: LA-P4

Status: **FROZEN** on 2026-10-13 (git tag `prereg-v1`). Every change after that goes in
the Deviations section at the bottom with a date and a reason.

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

| Family | Model | App | API id (returned by the API check) |
|---|---|---|---|
| Claude | Claude Sonnet 5.5 | claude.ai | `claude-sonnet-5-5`, 2026-10-06 |
| GPT | GPT-5.6 Sol | chatgpt.com | `gpt-5.6-sol`, 2026-10-06 |
| Gemini | Gemini 3.8 Flash | aistudio.google.com | `gemini-3.8-flash`, 2026-10-13 |
| Qwen | Qwen3.8-Max | chat.qwen.ai | `qwen3.8-max`, 2026-10-06 |
| DeepSeek | DeepSeek-V4.1-Flash | chat.deepseek.com | `deepseek-v4.1-flash` (Alibaba-hosted), 2026-10-13 |
| Grok | Grok 4.6 | grok.com | `grok-4.6`, 2026-10-06 |

Each API id is the model name the vendor's API returned in the API check
(`data/captures/*apicheck1.md`). The author checked each app's model picker on
2026-10-13; what each app showed is recorded in [mode-registry.md](mode-registry.md).
Every capture records the model name the app shows (`model_returned`). Two families do not
use the consumer app. Gemini runs in Google AI Studio, Google's own web app, because the
free Gemini app now offers only "Auto", which picks between Flash-Lite, Flash and Pro by
itself, so a mode change there could also change the model. chat.deepseek.com shows no
model picker; the author saw it serving V4.1-Flash, which the paper reports as the
author's observation.

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
- **Channel.** All 60 scored runs are captured in each vendor's own web app, the way
  people use these models and the way LA-P1 was captured: the consumer chat app for five
  families, Google AI Studio for Gemini (section 1). Fresh chat each time, signed
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
  registry. A family block that overruns 48 hours, or a collection that overruns 14 days
  (for example, an outage), is still completed, and the overrun is reported.
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
- **If raters guess mode above chance.** A rater beats chance on mode when the one-sided
  binomial p-value against 1/2 is below 0.05 (`modegrid blinding-check`). Reasoning answers
  may simply read differently, so this cannot be fully prevented and does not void the
  study, but it is handled as follows:
  - Any rater beats chance: the paper names the rater(s), and H1 to H4 are re-run on each
    rater's own scores as a sensitivity check. The paper reports whether the raters who
    did not beat chance reach the same conclusions.
  - All three raters beat chance: a supported H4 is described as tentative, whatever its
    alpha, and labelled "mode blinding failed".
  - Family guesses above chance (against 1/k, where k is the number of families retained)
    are reported the same way. They do not change any hypothesis's status, because family
    leaking through recommended model names is expected (see the blinding procedure
    above).
- **Refusals.** An outright refusal (the answer declines the task and recommends no
  models, tools or plan) scores 0 on all nine dimensions. The rubric assumes an answer
  exists; without this rule a refusal would earn 2s on D3, D5 and D9 for naming nothing.
  An answer that does part of the task is scored normally. Each rater applies the rule
  independently, and the median settles disagreement.
- The analysis unit is the median of the three raters' scores for each answer and
  dimension (`modegrid consensus`). No hand adjudication: the only possible adjudicator,
  the author, is not blind.

## 5. Primary analysis

The H4 total for an answer is the sum of its nine consensus (median) dimension scores,
D1 to D9, so it runs from 0 to 18. It is not the median of the three raters' totals. (The
reliability check in section 4 uses each rater's own total, the sum of that rater's nine
scores.)

For each dimension, and for the total, fit a balanced two-way fixed-effects decomposition
(family, mode, family x mode, residual) on all consensus scores (60, or 50 if a family is
dropped), each the median of the three raters.

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

Direction: `mode_effect = mean(reasoning) - mean(fast)` over all consensus scores (60, or 50 if a family is dropped), with a
95% percentile bootstrap CI from the same resamples as delta.

Interaction: omega squared for family x mode, and each family's reasoning-minus-fast
difference, are reported for every dimension (`results/family_mode_effects.csv`). If the
interaction's omega squared exceeds both main effects, the paper states that the main-effect
comparison does not summarise the data well and interprets the per-family differences.
This does not change H4's status, because H4's estimand is the average effect (section 1);
the result is labelled "average effect only; interaction exceeds both main effects".

Low variance: if 90% or more of a dimension's consensus scores share one value, the
dimension is reported as uninformative and any hypothesis on it as inconclusive; omega
squared and its bootstrap are unstable near zero variance. If all its scores are identical,
omega squared is
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
   Gemini 3.8 Flash, Grok 4.6; see [mode-registry.md](mode-registry.md)). Run the
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
  selected (visible in the screenshot). The replacement is captured immediately after the
  failed attempt, as the next capture inside the same family block, before the block moves
  on to the next run in manifest order. If the app is down, the block waits until it works
  again. The block may then run past 48 hours, and the whole study past 14 days; both
  overruns are reported (section 3) and do not by themselves drop the family. The
  replacement keeps the same run id; the failed capture moves to `data/captures/superseded/` as `<run_id>.attemptN.md`, with a line in
  that folder's README saying why. It is never deleted.
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
| 2026-10-13 | Registered on OSF: <https://osf.io/nj2zp/> (public, registered 2026-10-13 08:31 UTC, file SHA-256 matches the frozen plan). Record only; the protocol is unchanged. | Independent timestamp for the frozen plan |
| 2026-10-14 | Qwen block: one unplanned extra Fast chat was sent between runs 2 and 3. It is kept in `data/captures/superseded/qwen__fast__p1-v1__extra1.md`, assigned to no run and never scored. | Operator error; kept on record so no answer is silently dropped |
| 2026-10-14 | Qwen block: the first attempt at `qwen__reasoning__p1-v1__r5` ran in Fast instead of Thinking. It is in `superseded/` as `qwen__reasoning__p1-v1__r5.attempt1.md`, not scored, and the run was redone in Thinking with the same run id, inside the block. Section 7 lists errors, cut-offs and wrong models as replacement causes; a wrong mode chosen by the operator is treated the same way. | Operator error; the capture does not match its cell |
| 2026-10-14 | Qwen block: runs 3 to 10 (`qwen__reasoning__p1-v1__r5`, `qwen__fast__p1-v1__r3`, `qwen__fast__p1-v1__r5`, `qwen__reasoning__p1-v1__r2`, `qwen__reasoning__p1-v1__r1`, `qwen__reasoning__p1-v1__r4`, `qwen__reasoning__p1-v1__r3`, `qwen__fast__p1-v1__r4`) were sent before their templates were made, so the exact send time was not recorded. Each `date_run` is an ISO 8601 interval bounded by known events, with a `date_note`; `date_stamped` is unedited. Manifest order and the 48-hour block window (2026-10-13 10:45 UTC to 23:38 UTC) were kept. | Operator workflow; timestamps reported as intervals rather than guessed |
| 2026-10-14 | Grok block: the ten chats were operated by an AI assistant (Claude, through the Claude in Chrome extension) in the author's signed-in browser, at the author's request, not by the author by hand. Each run had its own new chat; the runs were opened in separate tabs and sent in manifest order without waiting for earlier answers. Templates were made seconds before each send and each capture records the browser-clock send time. Runs 1 to 4 were sent 00:13 to 00:16 UTC and runs 5 to 10 02:00 to 02:03 UTC after a pause; run 5's `date_run` is corrected with a `date_note`. | Operator workflow; exact send times kept |
| 2026-10-14 | Grok block: Grok ran web searches by itself in all ten runs (Fast and Expert). The app offers no switch to turn this off and DeepSearch was not used. Recorded per section 3 ("If an app cannot turn search off, that is recorded"). | App behaviour, not a protocol change |
| 2026-10-14 | Grok block: the app shows only the mode, not a model name. Every answer's own header names "Grok 4.7", while section 1 lists Grok 4.6. Per section 3, where the app shows no model name the Grok contrast is described as vendor-exposed chat settings, not a proven same-weights manipulation; the self-report is recorded in `model_returned`. | Vendor naming cannot be verified from the app |
| 2026-10-14 | DeepSeek block: operated by the AI assistant in the author's browser at the author's request, as for Grok (separate tabs, sent in manifest order 02:12 to 02:17 UTC, browser-clock send times). The app's toggles now read "DeepThink" and "Search"; Search was on by default and was switched off in every chat. The app turned the long paste into a file chip, so "Paste original" was clicked to send the prompt as plain text. | Operator workflow and app labels; settings as planned |
| 2026-10-14 | DeepSeek block: two Fast answers (`deepseek__fast__p1-v1__r3` replacement 1, `deepseek__fast__p1-v1__r1`) stopped at the app's output limit and showed a "Continue" button. The author pressed Continue, with no new message typed, and the app finished the same answer in the same message; the full answer is the capture. The first `deepseek__fast__p1-v1__r3` attempt, cut off and not continued, was replaced under section 7. | Section 7 replaces answers cut off in transmission; finishing the app's own truncated message keeps the cell complete without exceeding the replacement limit |
| 2026-10-14 | DeepSeek block: `deepseek__reasoning__p1-v1__r2` attempt 1 got the app error "A message is being generated, please try again later" while other chats were generating; replaced under section 7, sent alone. Replacements used: 1 of 2 in each DeepSeek cell. | App error |
| 2026-10-14 | DeepSeek block: the app shows no model name, and every answer's own header names an Anthropic Claude model (for example "Claude Sonnet 4.5"). The answers are recorded as given; per section 3 the DeepSeek contrast is described as vendor-exposed chat settings. | Model self-report cannot be verified from the app |
| 2026-10-14 | Claude block: operated by the AI assistant in the author's browser at the author's request (separate tabs, sent in manifest order, browser-clock send times). Chats used claude.ai incognito mode, so no history or memory applied, without changing the author's memory setting. The connectors listed in the composer (Gmail, Google Drive, Slack, Claude in Chrome and others) were switched off before the runs. The composer has no web-search switch and Claude searched the web by itself. The app turns long pastes into an attachment, so the prompt was inserted as plain text in line-aligned pieces from one clipboard paste and checked against the original before sending. | Operator workflow; settings as close to the plan as the app allows |
| 2026-10-14 | Claude block: three Effort High runs (`claude__reasoning__p1-v1__r2`, `r5`, `r3`) were stopped by the author's claude.ai 5-hour usage limit. By the author's decision this is treated as the app being down under section 7 (the block waits until the app works again), not as per-run failures, so the redos do not use the 2-replacement limit. The attempts are in `superseded/`; the runs were redone after the limit reset, about 4.5 hours later. | Account usage limit; app unavailable rather than a faulty answer |
| 2026-10-14 | Claude block: two Effort High runs (`claude__reasoning__p1-v1__r1`, `r4`) paused with a "Claude wants to fetch a web page" permission prompt. By the author's decision "Allow once" was clicked, about four hours later, and the answers finished. Other runs read pages without asking. | App permission prompt; keeps the runs comparable |
| 2026-10-14 | Gemini block: all 10 runs were sent by the author by hand in aistudio.google.com (Gemini 3.8 Flash picked by name, Thinking level Low or High, Grounding with Google Search and all other tools off, defaults otherwise, a new chat per run). Chats were run side by side and the exact send times were not recorded, so each `date_run` is an ISO 8601 interval from 20:35 NZDT (start of the block; AI Studio stamped run 1's reply 8:38 PM) to the time its template was made, with a `date_note`; `date_stamped` is unedited. The author reports runs 1 to 3 were sent between 20:38 and 20:45 NZDT and all runs in manifest order. Answers were copied with AI Studio's markdown copy and written verbatim from the clipboard. | Operator workflow; timestamps reported as intervals rather than guessed |
| 2026-10-14 | Gemini block: every answer names itself as a Claude model ("Claude 3.5 Sonnet" or "Claude 3.7 Sonnet") in its opening metadata, while the AI Studio model picker showed Gemini 3.8 Flash. `model_returned` records the picker, and the self-report is treated as a model error, not a model switch, as with the DeepSeek block. A first full-page copy of run 1 also showed a separate block headed "Model: GPT-4o" above the answer; its origin was not confirmed and it is not part of the capture. | Model self-report error; the app's model picker is the evidence |
| 2026-10-14 | Gemini block: AI Studio shows a Thoughts panel (thought summaries) only at Thinking level High; the five High captures include it, copied by the author. Low runs have no panel, so their trace is NONE. `gemini__fast__p1-v1__r3` was written before the author confirmed this and says the panel was "not captured"; there was no panel to capture. | Clarifies the reasoning-trace field; no data lost |
| 2026-10-15 | GPT block: all 10 runs were sent by the author by hand in chatgpt.com (paid plan, GPT-5.6 Sol picked in the model menu, Thinking effort Instant or High as confirmed by the author, a new chat per run). Exact send times were not recorded, so each `date_run` is an ISO 8601 interval with a `date_note`: from 01:00 NZDT (author) to the time the answer reached the clipboard, less ChatGPT's "Worked for" duration where shown. Answers were copied with ChatGPT's copy button and written verbatim from the clipboard. Copies that repeated an earlier answer byte for byte (or with only the page diagram ID changed) were rejected; runs 9 and 10 (`gpt__fast__p1-v1__r3`, `gpt__reasoning__p1-v1__r1`) were then sent in new chats from 01:56 NZDT. The author did not confirm which of two Instant chats was run 7 and which run 8; the captures follow the order the answers were copied. | Operator workflow; timestamps reported as intervals rather than guessed |
| 2026-10-15 | GPT block: ChatGPT searched the web by itself in every run, Instant included (live citations), and the High runs also built downloadable ZIP files with its tools; the app offers no way to turn this off within the chosen mode, so it is recorded as app behaviour, as with the Grok and Claude blocks. Most answers used the real date (15 October 2026) instead of the prompt's 31 August 2026; two High runs kept 31 August as a reference date. Every answer names itself "GPT-6"; `model_returned` records the model picker (GPT-5.6 Sol), and the self-report is treated as a model error. | App behaviour and model self-report; settings as close to the plan as the app allows |
| 2026-10-15 | GPT block reasoning traces: the High runs' activity panels were kept where the author supplied them. `gpt__reasoning__p1-v1__r5` and `r1` were read from the clipboard; `r4` and `r2` were transcribed by the assistant from the author's paste in the operator chat; `r3` was not captured. No panel was copied for the Instant runs. Traces are never shown to raters. | Incomplete optional field; no effect on scored answers |
| 2026-10-15 | Blinding: rater packets also drop chat-app clutter copied with the answers, via `strip_app_artifacts` in `src/modegrid/blind.py`: ChatGPT citation chips (favicon image link, source label, "+N" count), its diagram style blocks (the diagram labels are kept) and image embeds, the `&#x20;` entity, and Grok's `[web:N]` citation tags. It changed all 10 GPT packets and 3 Grok packets and no others. These come from the app, not the model's text, and would have named the family outright. Captures are unchanged; the same rule applies to every packet. | Blinding leak found when building packets; the frozen rule (mask self-naming only) did not cover app artifacts |
| 2026-10-15 | Raters named before scoring: `llm-a` Claude Opus 5.5 (Anthropic), `llm-b` GPT-5.6 Sol, Thinking effort High (OpenAI), both with live web search; the human rater is named in `data/scores/raters.md` before scoring starts. Both LLM vendors have a scored family, so `llm-a` on `claude` and `llm-b` on `gpt` are also reported separately, as section 4 requires. | Rater choice after the freeze, recorded as section 4 asks |
| 2026-10-15 | Rating sessions: each rater scores one answer per session from a single file built by `modegrid rater-kit` (the fixed prompt in `docs/rater-prompt.md`, the rubric, `scoring.md`, the memory checker and one blinded answer), in the rater's own reading order; an LLM rater uses a new chat per answer with memory and connectors off and web search on, and returns one CSV row that `modegrid rater-rows` checks and collects. Same instructions for all three raters. | Operational detail written down before scoring; keeps answers scored independently |
| 2026-10-15 | Blinding: the self-identification header rule missed bare "Model:" label lines ("**Model:** Claude 3.7 Sonnet ..."), which an LLM rater spotted in a test session before any real scoring. `HEADER_PATTERN` now also removes a line in the first 12 lines that starts with a `Model...:` label, plain or in markdown, but not table rows. The test session's score was discarded and packets and kits were rebuilt; the blinding key did not change. | Blinding leak found in a pre-scoring test |
| 2026-10-15 | Blinding: removed self-identification header lines are now dropped with no `[REDACTED] (self-identification line removed)` marker, and the empty shell they leave at the top of an answer (a "Response Header" or "Metadata" label, a leading rule, blank lines) is dropped too, only when a header line was removed. Before any scoring. The same rule applies to every packet; the blinding key and the answer bodies are unchanged. Packets and kits must be rebuilt with `modegrid blind` and `modegrid rater-kit`. | Blinding leak found when reviewing packets: how many marker lines an answer showed, and under which heading, differed by family |
| 2026-10-15 | Blinding: rater packets also drop conflict-of-interest disclosures in which an answer names its own maker (`strip_self_disclosure` in `src/modegrid/blind.py`): a first-person sentence opening with "Disclosure:" or "Conflict of interest:", the sentence "Conflict of interest noted.", and the parenthetical "(disclosure above)". It changed 4 packets, all from one family, and no others. The recommendations those sentences qualify stay. Before any scoring; same rule for every packet; the blinding key and every rater's reading order are unchanged. Packets and kits must be rebuilt. | Blinding leak found in a scan of the rebuilt packets: with the name masked, "I am a [REDACTED] model, so discount my view on Claude Code" still names the vendor through its own product, so the self-reference rule did not cover it |
| 2026-10-15 | Model correction, GPT: the GPT block ran **GPT-6** in chatgpt.com (Thinking effort Instant vs High), not GPT-5.6 Sol as section 1 lists. The author confirmed this from the app on 2026-10-15. GPT-6 reached ChatGPT on 7 October 2026 and took the default slot. Both modes ran the same model, so the same-model rule holds. The `model_returned` field of the 10 GPT captures, written as "GPT-5.6 Sol", is wrong and is corrected here rather than by editing the write-once captures. Every GPT answer's own "GPT-6" self-report was correct. The API check (`gpt-5.6-sol`, 0 vs 6,000 reasoning tokens) was run on the planned model, so it shows the switch on GPT-5.6 Sol, not on GPT-6. GPT stays in the true-off group of robustness check 4: OpenAI documents `reasoning.effort: none` for GPT-6 Sol, but the ChatGPT Instant setting is not documented as none, which a GPT-6 API check would settle. | The planned model was replaced in the app by a release a week before collection. Found by checking vendor releases after collection |
| 2026-10-15 | Model correction, Grok: the Grok block ran **Grok 4.7** in grok.com in both Fast and Expert, not Grok 4.6 as section 1 lists. The author confirmed this on 2026-10-15. Both modes ran the same model, so the Grok contrast is a mode switch on one model, and the earlier concern that Fast and Expert might differ in model is resolved. Every Grok answer's own "Grok 4.7" self-report was correct. The API check (`grok-4.6`, 131 vs 4,627 reasoning tokens) was run on the planned model. Grok 4.7, like 4.6, cannot disable reasoning, so Grok stays in the lowest-available group of robustness check 4. | As for GPT |
| 2026-10-15 | Rater `llm-b` is **GPT-6, Thinking effort High** (OpenAI), not GPT-5.6 Sol, because GPT-6 is now ChatGPT's model. Changed before any scoring. It is still from OpenAI, so its scores for the `gpt` family are still reported separately. | Rater model follows what the app serves |
| 2026-10-15 | Four API-check runs added (`gpt__*__apicheck2` on `gpt-6-sol`, `grok__*__apicheck2` on `grok-4.7`), with the same mode settings as the first checks. They are appended to the manifest after every existing run, so no run is renumbered. Like the first checks they are never scored, blinded or pooled, and `check-modes` reports them on their own rows. | The apps served GPT-6 and Grok 4.7, while the first checks called the planned models. These show the switch on the models that ran |
| 2026-10-15 | The human rater also gets `docs/human-rater-brief.md`, a plain-language summary of the task, the three careful checks (D1 memory, D3 and D4 web verification, D9 deliverable J), the fixed date and the guesses. It restates `scoring.md` and the rater prompt, adds no rule, and says those win where they seem to differ. Hashed in `data/scores/RATER_SHA256SUMS` before any scoring. | A rater from outside the project needs the protocol in plain words. The LLM raters' instructions are unchanged |
| 2026-10-15 | Rater prompt rule 8 added, before any scoring: raters ignore the parts of the vendored LA-P1 rubric that refer to that study (its file paths, the "Anchor" bullet that names a model, the remarks about what earlier raters missed, including one that names DeepSeek answers, and its "Current scores" section). Every scoring rule in the rubric still applies. The vendored rubric is unchanged and keeps its hash. The human brief restates the rule, so all three raters get the same instruction. `docs/rater-prompt.md` and `docs/human-rater-brief.md` were re-hashed and the kits rebuilt. The blinding key and reading orders are unchanged. | A practice run found that every kit carried rubric notes naming a model and DeepSeek answers, which could prime raters and break blinding |
| 2026-10-19 | API check 2 results. GPT-6 (`gpt-6-sol`): 0 reasoning tokens in fast, 6,000 in reasoning, switch confirmed, so GPT stays in the true-off group. Grok 4.7 (`grok-4.7`): fast (effort low) answered in full with 1,648 reasoning tokens, but reasoning (effort xhigh) stopped twice after a one-sentence preamble ("I'll research ... Starting with ...", about 50 output and 300 to 360 reasoning tokens, `finish_reason` stop, about 5 s), as if waiting for a search tool the API call does not offer. Attempt 1 is kept in `data/captures/superseded/`, attempt 2 is the capture. No third attempt and no change to the effort setting or tools. The Grok check 2 is reported as inconclusive. Grok stays in the lowest-available group on the first check (Grok 4.6: 131 vs 4,627). A first try at the four calls hung for 16 minutes on Grok, was stopped and saved nothing for Grok. | A changed setting or added tool would break comparability with every other API check; the analysis groups do not change |
| 2026-10-19 | Capture corrected, `qwen__reasoning__p1-v1__r2` (Qwen run 6, 14 Oct): its Final answer section held the study prompt, not the answer, because the clipboard still had the prompt when the file was written. Found before any scoring, when the human rater's returned files showed one packet with no answer to score. The author re-copied the answer from the same chat.qwen.ai Thinking chat on 2026-10-19 (9,126 words, the count recorded on 14 Oct; matches no other capture). Nothing was re-sent and the reasoning trace is unchanged. A scan of all 60 scored captures found no other case; `modegrid validate` now fails when an answer contains the prompt. Packets and rater kits rebuilt; the blinding key is unchanged. | The answer existed in the original chat; recovering it keeps the run as sent instead of using a replacement |
| 2026-10-19 | The human rater is recorded as **Rater H1**, anonymous at their own request, instead of by name. The author knows who they are and confirms they are not an author and not the observer. Recorded in `data/scores/raters.md` before any scoring. | Rater privacy; the rater's independence from the authors is unchanged |
| 2026-10-26 | Human rater replaced. Rater H1 returned three sheets (2026-10-19, 2026-10-21, 2026-10-22) that were made with AI tools: each file describes itself as an AI assessment or AI-assisted pass, scored all 60 answers in one session, and used repeated template notes. None of Rater H1's scores are used. A second human, **Rater H2** (anonymous at their own request, not an author and not the observer), scored all 60 answers by hand from the same human kit between 2026-10-24 and 2026-10-26, and the author confirms no AI tools were used. Rater H2 was recorded in `data/scores/raters.md` after scoring, not before. Every memory-checker input Rater H2 stated reproduces exactly with `memory_budget.py`. | Section 4 needs a human rater; AI-made sheets cannot stand in for one. Naming before scoring was not possible because the replacement was found after Rater H1's returns were rejected |
| 2026-10-26 | In 18 of the 60 `llm-a` sessions (B019, B042, B016, B011, B005, B020, B014, B009, B021, B022, B030, B026, B053, B015, B031, B060, B045, B013), the claude.ai chat had no code execution, so the rater worked `memory_budget.py` through by hand instead of running it. The author re-ran the script on every input set those replies state: every total and verdict is identical. No score changed. | Section 7 says D1 requires running the checker; the hand results match it exactly |
| 2026-10-26 | Robustness check 2 (length) asks whether the mode effect shrinks after removing log answer length. The first `make results` reported only delta omega squared after adjustment, and `modegrid report` called the effect "shrinking" when the absolute value of delta fell. Delta is mode share minus family share, so it can move for reasons unrelated to the mode effect. The analysis now also reports omega squared for mode and reasoning minus fast after adjustment, and the report judges shrinking on reasoning minus fast. No pre-registered number changed; the new columns are added beside the old ones. On the total, reasoning minus fast falls from 1.37 to 0.62 and omega squared for mode from 0.050 to 0.008, so the mode effect is reported as not separable from answer length. | The pre-registered rule names the mode effect; the first implementation tested a different quantity. Found while writing the Results section |
| 2026-10-26 | Added an exploratory check, not pre-registered: H4 re-run with each LLM rater's own-vendor scores (`llm-a` on Claude, `llm-b` on GPT) replaced by the mean of the other two raters (`modegrid own-vendor --replaced-out`, `results/own-vendor-replaced/`). Section 4.8 of the results skeleton (written 2026-10-14) allows this check when self-preference is large. Both LLM raters showed self-preference on the total with a CI above zero. Result: model > mode, unchanged. | Self-preference was of the same size as the mode effect; the check shows whether it drives the H4 verdict |
| 2026-10-27 | Blinding leak found after scoring. Three blinded packets, all Claude reasoning answers (B015 `claude__reasoning__p1-v1__r2`, B048 `__r5`, B050 `__r3`), still contained the author's account name (`roshan`, as a macOS user name, three times each in B048 and B050) or "Auckland time" (once, B015). claude.ai passed the account's name and location to the model although memory was off. The pre-scoring audit (`modegrid blinding-audit`) had no probe for the author's name, so it did not catch this. All three raters guessed reasoning on all three packets; `llm-a` guessed Claude on all three, the human rater and `llm-b` on one each. No scores are changed; the leak is reported in Results 4.6 and Appendix D2. | Found while checking the repository before release; reported rather than corrected because scoring is complete |
