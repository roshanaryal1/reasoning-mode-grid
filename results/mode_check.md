# Mode check (API)

One API call per family and mode. Evidence that each mode switch works. Not scored.

| Family | Words fast | Words reasoning | Reasoning tokens fast | Reasoning tokens reasoning | Model returned | Verdict |
|---|---|---|---|---|---|---|
| claude | 2108 | 6051 | 0 | 14864 | claude-sonnet-5-5 | switch confirmed |
| deepseek | 6916 | 10043 | 0 | 1367 | deepseek-v4.1-flash | switch confirmed |
| gemini | 4592 | 6482 | 0 | 4911 | gemini-3.8-flash | switch confirmed |
| gpt | 4014 | 0 | 0 | 6000 | gpt-5.6-sol | switch confirmed |
| gpt (check 2) | 4034 | 0 | 0 | 6000 | gpt-6-sol | switch confirmed |
| grok | 1990 | 7393 | 131 | 4627 | grok-4.6 | lowest available: fast reasons less, not zero; record both counts |
| grok (check 2) | 4412 | 35 | 1648 | 363 | grok-4.7 | CHECK: reasoning tokens do not separate the modes |
| qwen | 3315 | 7587 | 0 | 23805 | qwen3.8-max | switch confirmed |
