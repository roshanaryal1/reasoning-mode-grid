# Superseded captures

Kept for the record, never analysed. Loaders only read the top level of `data/captures/`.

| File | Run on | Why superseded |
|---|---|---|
| `gemini__fast__p1-v1__apicheck1.md`, `gemini__reasoning__p1-v1__apicheck1.md` | 2026-10-06 | Recorded before the adapter derived Gemini reasoning tokens from `total_tokens` (PR #7), so `reasoning_tokens` is null and the mode switch could not be confirmed. Re-run the same day with the fix. |
| `gemini__fast__p1-v1__apicheck1.second-run.md` | 2026-10-07 | Second run. Thinking gap was 0, but the adapter recorded it as null before `_reasoning_in_total` existed (PR fixing Gemini's measured zero). Re-run with the fix. |
| `gemini__fast__p1-v1__apicheck1.attempt4.md`, `gemini__reasoning__p1-v1__apicheck1.attempt3.md` | 2026-10-12 | Valid check on `gemini-3.6-flash`. Superseded 2026-10-13 when Gemini moved to Gemini 3.8 Flash in AI Studio (mode registry, 2026-10-13). |
| `deepseek__fast__p1-v1__apicheck1.attempt1.md`, `deepseek__reasoning__p1-v1__apicheck1.attempt1.md` | 2026-10-06 | Valid check on `deepseek-v4-pro-0813`. Superseded 2026-10-13 when the app was seen serving V4.1-Flash (mode registry, 2026-10-13). |
| `qwen__fast__p1-v1__extra1.md` | 2026-10-13 | Unplanned extra Qwen Fast answer, sent without a template between runs 2 and 3. Not assigned to any run, never scored. |
| `qwen__reasoning__p1-v1__r5.attempt1.md` | 2026-10-14 | Wrong mode by the operator: the chat ran in Fast, but this run is a Thinking run. Not scored; the run is redone in Thinking with the same run id. |
| `deepseek__fast__p1-v1__r3.attempt1.md` | 2026-10-14 | Cut off: the app stopped at its output limit and showed "Continue"; Continue was not pressed in this chat. Not scored; replaced in the same block (replacement 1 of 2 for the cell). |
| `deepseek__reasoning__p1-v1__r2.attempt1.md` | 2026-10-14 | App error, no answer: "A message is being generated, please try again later" (too many chats generating at once). Not scored; replaced in the same block, sent alone (replacement 1 of 2 for the cell). |
| `claude__reasoning__p1-v1__r2.attempt1.md`, `claude__reasoning__p1-v1__r5.attempt1.md`, `claude__reasoning__p1-v1__r3.attempt1.md` | 2026-10-14 | Stopped by the author's claude.ai 5-hour usage limit while ten chats ran at once; partial text kept. Treated as app downtime under section 7 (not counted against the 2-replacement limit), per the author's decision; redone after the limit reset. Not scored. |
