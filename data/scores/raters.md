# Raters

Named before any scoring starts (pre-registration section 4, scoring.md "LLM raters").
Raters never receive the key, the captures, the manifest or the reasoning traces.

| Sheet | Rater | Vendor | Model / person | Web search | Run date |
| --- | --- | --- | --- | --- | --- |
| `human.csv` | Human, not an author and not the observer | n/a | To be named before scoring | Yes, for D3 and D4 | To be recorded |
| `llm-a.csv` | LLM | Anthropic | Claude Opus 5.5 (`claude-opus-5-5`) | Yes | To be recorded |
| `llm-b.csv` | LLM | OpenAI | GPT-5.6 Sol, Thinking effort High | Yes | To be recorded |

Both LLM raters come from vendors whose families are scored. Their scores for their own
vendor's family (`llm-a` on `claude`, `llm-b` on `gpt`) are also reported separately.

Packets were built on 2026-10-15 with `modegrid blind --raters human llm-a llm-b`, after
the chat-app clutter rule was added to `strip_app_artifacts` (see the Deviations table).

## Rater instructions, hashed before scoring

Pre-registration section 3 asks for the raters' instructions to be hashed before scoring
starts. Every kit file built by `modegrid rater-kit` is made from these four files, the
same for all three raters. Hashes recorded 2026-10-14, before any real scoring. CI checks
them (`sha256sum -c data/scores/RATER_SHA256SUMS`), so an edit during scoring fails the
build and needs a Deviations row.

| File | Role in the kit | sha256 |
| --- | --- | --- |
| `docs/rater-prompt.md` | Fixed rater prompt (the block between the START and END markers) | `31994d35ab03a7760d52bf9b0d350ec05f6374e70f213245e00683ddf5079446` |
| `docs/scoring.md` | Scoring protocol | `483479ff96358e7d6256e8f895f108a74fd298f48cdd18ba4e4e520a6c6ebb99` |
| `vendor/llm-architects/docs/rubric.md` | Rubric, v1 table plus v2 anchors | `515368bdf639e4a338425a47bc902d957d590f4d5aa9979e185e4d3a0f50c985` |
| `vendor/llm-architects/scripts/memory_budget.py` | Memory checker for D1 | `ebb13a82c62f6aab116958e9ea521e342adf59a45ce8d9a5ef1411ff0bd59991` |

The prompt block alone (the text the kit uses) hashes to
`d41b8da761719bdecc4a621dbae7225a90eaf64e0f89767d04731d61e31ed924`.
