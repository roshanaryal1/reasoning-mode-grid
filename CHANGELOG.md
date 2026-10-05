# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow
[SemVer](https://semver.org/). Data releases are tagged `data-vN`.

## [Unreleased]

### Changed

- Decided Gemini (`gemini-3.8-flash`, reasoning effort low vs high) and Grok
  (`grok-4.6`, low vs xhigh). Neither can disable reasoning, so fast is the lowest
  available level. Gemini chat labels follow the app's new picker (Flash plus a
  thinking level; Fast and Thinking were removed on 17 May 2026). No `FILL-ME` or
  `VERIFY` values remain. Two new threats to validity cover the Grok app mapping
  and "lowest available" fast modes.
- Filled researched API settings for GPT (gpt-5.5) and DeepSeek (deepseek-v4-pro, whose
  old API names were retired on 24 Jul 2026). Gemini, Qwen and Grok still need a
  model decision; research notes and sources are in the mode registry.
- The 60 scored runs are now captured in each vendor's chat app (`channel: web`), to
  match LA-P1 and real use. Each mode has a `web_label` naming what to select.
- The length robustness check uses answer length in words, comparable across chat apps
  and tokenizers.

### Added

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
