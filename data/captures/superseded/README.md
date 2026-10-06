# Superseded captures

Kept for the record, never analysed. Loaders only read the top level of `data/captures/`.

| File | Run on | Why superseded |
|---|---|---|
| `gemini__fast__p1-v1__apicheck1.md`, `gemini__reasoning__p1-v1__apicheck1.md` | 2026-10-06 | Recorded before the adapter derived Gemini reasoning tokens from `total_tokens` (PR #7), so `reasoning_tokens` is null and the mode switch could not be confirmed. Re-run the same day with the fix. |
| `gemini__fast__p1-v1__apicheck1.second-run.md` | 2026-10-07 | Second run. Thinking gap was 0, but the adapter recorded it as null before `_reasoning_in_total` existed (PR fixing Gemini's measured zero). Re-run with the fix. |
