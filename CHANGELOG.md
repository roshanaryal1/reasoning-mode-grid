# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow
[SemVer](https://semver.org/). Data releases are tagged `data-vN`.

## [Unreleased]

- 2026-10-28: submitted for double-blind review and to Preprints.org (named preprint, in
  screening). OSF registration linked to the v1.0.0 Zenodo record as data and analytic code.

## [1.0.0] - 2026-10-27

Scoring and analysis complete; paper drafts, JAIR and TMLR LaTeX, release metadata
updated to the result ("Model, Not Mode").

### Changed

- Blinding leak found after scoring: three Claude reasoning packets still contained the
  author's account name or home city. Reported in Results 4.6, Appendix D2 and the
  Deviations table; no scores changed.
- Robustness check 2 (length) now reports omega squared for mode and reasoning minus fast after
  removing log answer length, and `modegrid report` judges a shrinking mode effect on reasoning minus
  fast, not on delta. On the total the mode effect falls from 1.37 to 0.62. Recorded in the Deviations
  table. No earlier number changed.
- `modegrid own-vendor --replaced-out DIR` re-runs the analysis with each LLM rater's own-vendor scores
  replaced by the mean of the other raters (exploratory, not pre-registered). `make results` writes it
  to `results/own-vendor-replaced/`; H4 stays model > mode. Recorded in the Deviations table.
- Scoring complete: `data/scores/human.csv`, `llm-a.csv` and `llm-b.csv` (60 answers each), with
  run dates in `data/scores/raters.md`. Blinding key committed. `make results` written to `results/`.
- Human rater replaced: Rater H1's AI-made returns are not used; Rater H2 (anonymous) scored by hand,
  recorded after scoring. Recorded in the Deviations table.
- 18 `llm-a` sessions computed the memory check by hand (no code execution in claude.ai); the author
  re-ran every stated input and all results match. Recorded in the Deviations table.
- Human rater recorded as Rater H1 (anonymous at their request), before scoring.
- API check 2 ran on 2026-10-19. GPT-6 switch confirmed (0 vs 6,000 reasoning tokens). Grok 4.7 at
  effort xhigh stopped twice after a one-sentence preamble, so its check 2 is inconclusive; Grok stays
  lowest available on check 1. Recorded in the Deviations table. No analysis group changes.
- Fixed capture `qwen__reasoning__p1-v1__r2`: its answer section held the study prompt. The answer was
  re-copied from the original chat (nothing re-sent). Recorded in the Deviations table. Packets and
  rater kits rebuilt.
- Rater prompt rule 8: raters ignore the vendored rubric's leftover LA-P1 notes (file paths, the
  "Anchor" bullet naming a model, remarks about earlier raters naming DeepSeek answers, "Current
  scores"). The rubric is unchanged. Prompt and human brief re-hashed, kits rebuilt.
- Model correction, confirmed by the author: the GPT block ran GPT-6 and the Grok block ran Grok 4.7
  (both modes), not the pre-registered GPT-5.6 Sol and Grok 4.6. Rater `llm-b` is GPT-6. Recorded in
  the Deviations table, the mode registry, threats to validity and the paper drafts. The API checks for
  these two families ran on the planned models. No change to any analysis group.
- Rater packets drop conflict-of-interest disclosures in which an answer names its own maker
  ("Disclosure: I am a [REDACTED] model, so discount my view on ..."). 4 packets change. Rebuild
  packets before scoring.
- Rater packets drop removed self-identification lines with no marker, and the empty header shell
  they leave, because the markers' count and position differed by family. Rebuild packets before scoring.

- Pre-registration registered on OSF: <https://osf.io/nj2zp/>.
- Pre-registration frozen on 2026-10-13 (tag `prereg-v1`).
- App checks on 2026-10-13. Gemini moves to Google AI Studio with Gemini 3.8 Flash
  (Thinking level Low vs High, Search grounding off), because the free Gemini app now
  offers only "Auto", which can switch models by itself, and AI Studio marks 3.6 Flash as
  Paid. DeepSeek moves to DeepSeek-V4.1-Flash, the model chat.deepseek.com was seen
  serving. Both API checks re-run (Gemini 0 vs 4,911, DeepSeek 0 vs 1,367 reasoning
  tokens); the old checks are in `data/captures/superseded/`.
- Final fixes before freeze. The H4 total is defined as the sum of the nine consensus
  (median) scores. Analysis counts say "60, or 50 if a family is dropped". A replacement is
  captured straight after the failed attempt, inside the same family block. A rule for
  raters who guess mode above chance. The model table lists the API id each vendor
  returned, and app names are checked in each app before the first scored capture.
- Third review pass on the pre-registration. Blinding now masks a vendor or model name only
  where an answer refers to itself; names used as content stay, because D2 to D4 need the
  recommended models and tools. An outright refusal scores 0 on every dimension. Chosen
  model per family listed, with a tie-break rule. Family blocks follow manifest order, which
  keeps the seeded order and the 48-hour rule both true. Up to 2 replacements per cell for
  errors or cut-offs; a replaced capture moves to `data/captures/superseded/` and the
  replacement keeps the run id. `new-capture` writes an unedited `date_stamped`, and
  `validate` rejects a changed `date_run` with no `date_note`. Low-variance dimensions make
  their hypothesis inconclusive; a strong interaction labels support "average effect
  only"; the bootstrap CI decides and permutation disagreements are reported. `modegrid
  power` reports the full H4 rule beside delta alone; power.md no longer says the
  equal-effects rate is near 5% (it is 0.15 at 60 runs).
- Pre-registration tightened after two outside reviews: H4 is the single confirmatory test
  (H1-H3 secondary); H1, H2, H4 also need reasoning > fast; dimensions below alpha 0.667 are
  exploratory, with H4 gated on the total score's alpha; refusals are kept and scored;
  a failed re-run drops the family; exact omega squared formula, permutation null and
  bootstrap seed stated; interaction and per-family differences reported; low-variance
  dimensions reported as uninformative; length check reworded as non-causal; same-model
  verification, capture window, blinding procedure, pinned inputs and single-task scope
  written down. The arXiv 2505.24630 citation no longer quotes an unverified figure.
- Single author (2026-10-12). The author never scores; three blind raters (one human
  who is not an author, two LLMs from different vendors) score, and the median replaces
  hand adjudication. AUTHORS.md, collaboration.md, scoring.md, the pre-registration,
  runbook and threats to validity updated.
- Decided settings from the chat apps as seen on 2026-10-06: Claude moves to
  `claude-sonnet-5-5` (Effort Low vs High; Sonnet 5 is no longer in claude.ai),
  Gemini to `gemini-3.6-flash` (Extended thinking off vs on; API `minimal` vs
  `high`), Qwen to `qwen3.8-max` (Fast vs Thinking), GPT to `gpt-5.6-sol`
  (Thinking effort Instant vs High; API `none` vs `high`), Grok `grok-4.6` (low vs
  xhigh). Claude, Gemini and Grok cannot disable reasoning, so their fast mode is
  the lowest available level. No `FILL-ME` or `VERIFY` values remain. Threats to
  validity cover the Grok app mapping, "lowest available" fast modes and the Qwen
  model change from LA-P1.
- Filled researched API settings for GPT (gpt-5.5) and DeepSeek (deepseek-v4-pro, whose
  old API names were retired on 24 Jul 2026). Gemini, Qwen and Grok still need a
  model decision; research notes and sources are in the mode registry.
- The 60 scored runs are now captured in each vendor's chat app (`channel: web`), to
  match LA-P1 and real use. Each mode has a `web_label` naming what to select.
- The length robustness check uses answer length in words, comparable across chat apps
  and tokenizers.

### Added

- `modegrid report` writes `results/report.md`: every number `paper/results.md` asks for, in its
  order, with only the pre-registered rules applied. `make results` runs the whole of Phase 4 and
  the report in one step. `modegrid blinding-check --out` saves its table as CSV.

- `docs/scoring-day.md`: the author's checklist for running the 120 LLM rating sessions and
  collecting the human sheet, with fixes for every `rater-rows` error and an open question on the
  rubric's leftover LA-P1 notes.
- `docs/human-rater-brief.md`: a plain-language brief for the human rater. Restates the rules and
  adds none. Hashed with the other rater instructions.
- Second API checks on the models the apps served: `api_check_models` in the config (`gpt-6-sol`,
  `grok-4.7`) adds four `apicheck2` runs, appended so no existing run is renumbered. `run --dry-run`
  shows each run's model, and `check-modes` reports each API-check model on its own row. Runbook
  Phase 2b.
- `.zenodo.json` for the Zenodo GitHub integration (title, creator, licence, links to the OSF
  registration and the LA-P1 dataset), and the OSF registration in `CITATION.cff`.
- `make paper`: stitches the paper drafts into one manuscript (Markdown and HTML).
- Mode registry: vendor releases around the collection window, as pre-registration section 3
  requires. None inside the window. GPT-6 (7 October) and Grok 4.7 bear on which model ran, and
  the GPT and Grok screenshots need checking.
- `modegrid own-vendor`: each LLM rater's scores for its own vendor's family (`llm-a` on Claude,
  `llm-b` on GPT), as pre-registration section 4 requires: the gap to the other raters, the same
  gap on the other families, and their difference with a bootstrap CI.
- `paper/results.md`: a Results skeleton, written before scoring, that names the file and column
  behind every reported number.
- `modegrid blinding-audit`: before scoring, counts family fingerprints left in the packets per
  cell, exits non-zero if a leak probe hits, and writes `results/blinding_audit.csv`. The final
  packets have no leak hits.
- `modegrid cells`: cell means per family and mode (`results/cell_means.csv`), and with `--figure`
  Figure 1 of the paper outline (needs the new `paper` extra, matplotlib). Reruns give the same file.
- `modegrid rank-agreement`: Kendall's tau-b between each pair of raters and Kendall's W across all,
  on how they rank the 12 cells, for the total and each dimension. The LA-P5 portability check.
- `data/scores/RATER_SHA256SUMS`: hashes of the four files every rater kit is built from, recorded
  before scoring as pre-registration section 3 asks, and checked in CI.
- Paper drafts written before scoring: `paper/introduction.md`, `paper/related-work.md`,
  `paper/methods.md` and `paper/appendix.md`.
- `docs/related-work.md`: every citation re-checked on 2026-10-14, with corrected titles,
  peer-reviewed versions and five newer papers, two of them close to this design.
- `modegrid rater-kit` and `modegrid rater-rows`: one self-contained file per answer per rater (fixed
  prompt in `docs/rater-prompt.md`, rubric, protocol, memory checker, one answer), and collection of the
  CSV rows raters return, with checks, into `data/scores/<rater>.csv` once all 60 are in.
- `strip_app_artifacts`: rater packets drop chat-app clutter (ChatGPT citation chips, diagram style
  blocks, image embeds, `&#x20;`, Grok `[web:N]` tags) that would reveal the family. Captures are unchanged.
- `data/scores/raters.md`: the two LLM raters (Claude Opus 5.5, GPT-5.6 Sol) named before scoring.
- GPT block of the chat captures: 10 of 60 runs (chatgpt.com, GPT-5.6 Sol, Thinking effort Instant vs High),
  captured 2026-10-15 by hand. All 60 scored runs are now captured. Three Deviations rows record the send-time
  intervals and rejected duplicate copies, ChatGPT's built-in search and "GPT-6" self-reports, and the traces.
- Gemini block of the chat captures: 10 of 60 runs (aistudio.google.com, Gemini 3.8 Flash, Thinking level
  Low vs High, Search grounding off), captured 2026-10-14 by hand. Three Deviations rows record the send-time
  intervals, the Claude self-reports and the Thoughts panel.
- Claude block of the chat captures: 10 of 60 runs (claude.ai incognito, Sonnet 5.5, Effort Low vs
  High), captured 2026-10-14. Three usage-limit stops are in `data/captures/superseded/`; three
  Deviations rows record the operator and settings, the usage-limit handling and the fetch prompts.
- DeepSeek block of the chat captures: 10 of 60 runs (chat.deepseek.com, DeepThink off vs on,
  Search off), captured 2026-10-14 with browser-clock send times. Two set-aside attempts are in
  `data/captures/superseded/`; four Deviations rows record the operator, the app's paste and
  toggle behaviour, the two continued Fast answers and the Claude self-reports.
- Grok block of the chat captures: 10 of 60 runs (grok.com, Fast vs Expert), captured
  2026-10-14 with exact browser-clock send times. Three Deviations rows record the
  assistant-operated browser, Grok's built-in web search and the "Grok 4.7" self-report.
- Qwen block of the chat captures: 10 of 60 runs (Qwen3.8-Max, Fast vs Thinking), captured
  2026-10-13 to 2026-10-14. Two set-aside answers are in `data/captures/superseded/`; three
  Deviations rows record the extra chat, the wrong-mode attempt and the send-time intervals.
- `modegrid analyze` reports the signed mode effect (reasoning minus fast) with a bootstrap
  CI, omega squared for the interaction, per-family differences
  (`family_mode_effects.csv`) and hypothesis status; `--agreement` marks dimensions below
  the alpha bar as exploratory. `modegrid agreement` adds a total-score row.
- `modegrid analyze --families`: run the analysis on a subset of families. Used by
  pre-registered robustness check 4, which splits the grid into families with a true
  reasoning-off fast mode (GPT, Qwen, DeepSeek) and lowest-available ones (Claude,
  Gemini, Grok).
- `modegrid consensus`: median of an odd number of blind rater sheets, the analysis unit
  when the author cannot adjudicate blind.
- Per-family `max_tokens` for the API check (GPT 6,000 to fit a 10,000 tokens-per-minute
  account limit); the grid default rises to 64,000. Captures record the limit used.
- `modegrid agreement --out` writes `dimension,alpha` CSV, the input LA-P5's
  `specbench gate --alpha` reads.
- `modegrid blinding-check`: rater guess accuracy for family and mode against chance,
  with an exact one-sided binomial p-value.
- Streaming in the OpenAI-compatible adapter (`_stream: true`). Both Qwen modes use it,
  because some Qwen endpoints only return thinking output when streamed.
- Runbook steps for the per-rater robustness check and the LA-P5 hand-off.

- `api_check` run set: 1 API call per family and mode (12 calls) to verify each mode
  switch. Never blinded, scored or analysed with the grid.
- `modegrid check-modes`, which writes `results/mode_check.md`.
- `modegrid validate` flags a capture that still says `FILL IN`.
- `docs/related-work.md` with the closest prior work (HRBench, hybrid-thinking
  leakage, reasoning-model hallucination) and a competing prediction for H3.
- `docs/venues.md`: venue research with dates and sources, and the submission timeline.
- `docs/collaboration.md` and `AUTHORS.md`: co-author split, access rules that keep
  scoring blind, CRediT roles.

### Fixed

- `modegrid rater-rows` stopped with a Python traceback on a bad reply and did not say which file.
  It now prints one line naming the reply file and the problem, saves nothing from that batch, and
  exits 1. Found in a practice scoring run.
- `CITATION.cff` used the reference type `dataset`, which the CFF 1.2.0 schema does not allow, so
  GitHub could not offer "Cite this repository". It is now `data`, and the file validates.
- `modegrid analyze` computed the random-effects variance components but never wrote them. They are
  now in `variance_table.csv` (`vc_*`) and in an exploratory section of `variance_table.md`, as
  pre-registration section 5 lists them among the statistics reported for every dimension.
- Refusal counts per family and mode (pre-registration section 7): `cell_means.csv` gains
  `n_all_zero`, the answers whose consensus is 0 on all nine dimensions.
- `modegrid validate` failed on `data/scores/adjudicated-blind.csv` (keyed by `blind_id`) and on the
  per-rater `*-unblinded.csv` sheets (keyed by `run_id`), so the Phase 3 check could never pass. It now
  reads the id column from each sheet's header, and checks that `adjudicated.csv` covers exactly the
  manifest's 60 main runs. Found by a full rehearsal of Phases 3 and 4 on the real captures with
  made-up rater rows.
- The CI guard against committing the blinding key early looked for `data/scores/rater*.csv`, which
  never exists, so it would have failed the correct commit after scoring. It now needs all three sheets.
- The runbook adds the gitignored blinding key with `git add -f`.

## [0.1.0] - 2026-10-01

### Added

- `modegrid` CLI: plan, run, new-capture, validate, blind, unblind, agreement, analyze,
  demo, power, hash.
- Two-way variance decomposition with omega squared, bootstrap CIs, permutation tests,
  rank and length robustness checks.
- Krippendorff's alpha (nominal, ordinal, interval), cross-checked against the reference
  package.
- Adapters for the Anthropic Messages API and OpenAI-compatible endpoints. Mode settings
  in `configs/grid.yaml`.
- Blinded rater packets with identity redaction.
- Draft pre-registration, runbook, mode registry, scoring protocol, power analysis,
  threats to validity, paper plan.
- Vendored prompt v1, rubric v2 and memory checker from llm-architects@d5e39e7.
- LA-P1 DeepSeek pilot captures, flagged as exploratory.
