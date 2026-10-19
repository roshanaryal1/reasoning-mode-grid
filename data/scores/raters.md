# Raters

Named before any scoring starts (pre-registration section 4, scoring.md "LLM raters").
Raters never receive the key, the captures, the manifest or the reasoning traces.

| Sheet | Rater | Vendor | Model / person | Web search | Run date |
| --- | --- | --- | --- | --- | --- |
| `human.csv` | Human, not an author and not the observer | n/a | Rater H1, anonymous at their own request (identity known to the author; named 2026-10-19, before scoring) | Yes, for D3 and D4 | To be recorded |
| `llm-a.csv` | LLM | Anthropic | Claude Opus 5.5 (`claude-opus-5-5`) | Yes | To be recorded |
| `llm-b.csv` | LLM | OpenAI | GPT-6, Thinking effort High (changed from GPT-5.6 Sol on 2026-10-15, before scoring) | Yes | To be recorded |

Both LLM raters come from vendors whose families are scored. Their scores for their own
vendor's family (`llm-a` on `claude`, `llm-b` on `gpt`) are also reported separately.

Packets were first built on 2026-10-15 with `modegrid blind --raters human llm-a llm-b`, after
the chat-app clutter rule was added to `strip_app_artifacts` (see the Deviations table).
They must be rebuilt (`modegrid blind`, then `modegrid rater-kit`) before scoring, because on
2026-10-15 removed header lines stopped leaving a marker (Deviations table). The blinding key
does not change.

## Rater instructions, hashed before scoring

Pre-registration section 3 asks for the raters' instructions to be hashed before scoring
starts. Every kit file built by `modegrid rater-kit` is made from four of these files (all
but the human brief), the same for all three raters. Hashes recorded 2026-10-14, and for the
human brief 2026-10-15, before any real scoring. The rater prompt and the human brief were
re-hashed on 2026-10-15 after rule 8 was added (Deviations table). CI checks
them (`sha256sum -c data/scores/RATER_SHA256SUMS`), so an edit during scoring fails the
build and needs a Deviations row.

| File | Role in the kit | sha256 |
| --- | --- | --- |
| `docs/rater-prompt.md` | Fixed rater prompt (the block between the START and END markers) | `9ddd38ccf0d35003625780a8f7f186f06736212d0a727aeaea8b6b74149cc93f` |
| `docs/scoring.md` | Scoring protocol | `483479ff96358e7d6256e8f895f108a74fd298f48cdd18ba4e4e520a6c6ebb99` |
| `vendor/llm-architects/docs/rubric.md` | Rubric, v1 table plus v2 anchors | `515368bdf639e4a338425a47bc902d957d590f4d5aa9979e185e4d3a0f50c985` |
| `docs/human-rater-brief.md` | Plain-language brief for the human rater only. Restates the rules, adds none. Added 2026-10-15, before scoring | `d63dfd802d22cb521757a33c22a829163b13b984dc76fc568cbd5dc7c841cb2d` |
| `vendor/llm-architects/scripts/memory_budget.py` | Memory checker for D1 | `ebb13a82c62f6aab116958e9ea521e342adf59a45ce8d9a5ef1411ff0bd59991` |

The prompt block alone (the text the kit uses) hashes to
`30ab4e75238bdb7e1fb2e74227ce89ebee65fd29c2038f93eb95bd1f69f91c2d`.
