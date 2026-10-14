# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow
[SemVer](https://semver.org/). Data releases are tagged `data-vN`.

## [Unreleased]

### Changed

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
