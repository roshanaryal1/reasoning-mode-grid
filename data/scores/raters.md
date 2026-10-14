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
