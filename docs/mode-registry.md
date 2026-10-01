# Mode registry

"Mode" means something different at every vendor. This file records exactly what each
cell's mode was, how it was switched, and the evidence that the switch worked. Reviewers
will ask. This is the answer.

Fill one row per family before the pre-registration is frozen.

| Family | Model (fixed weights) | Fast mode setting | Reasoning mode setting | Channel | Doc URL and date read | Evidence switch works |
|---|---|---|---|---|---|---|
| Claude | `claude-sonnet-5` | `thinking: {type: disabled}` | `thinking: {type: adaptive}`, `output_config.effort: high` | API | | |
| GPT | FILL-ME | lowest supported `reasoning_effort` | `reasoning_effort: high` | API | | |
| Gemini | FILL-ME, one model | thinking off | thinking high | API (OpenAI-compatible endpoint) | | |
| Qwen | FILL-ME, hybrid-thinking model | `enable_thinking: false` | `enable_thinking: true` | API (DashScope compatible mode) | | |
| DeepSeek | V4-Pro class, confirm both API names serve it | non-thinking model name | thinking model name | API | | |
| Grok | as shown in the model picker | Fast | Expert | Web (grok.com) | | |

## Rules

1. **Same weights.** A mode may change thinking budget, reasoning effort, or a thinking
   toggle. It may not change the model. Flash vs Pro, mini vs full, or "auto" routers
   that may pick a different model are not modes.
2. **Lowest available, not "off".** Some vendors no longer offer a true no-reasoning
   setting. Then the fast mode is the lowest setting, and this file says so. Example:
   Claude Opus 5.5 rejects `thinking: disabled`, so the grid uses Sonnet 5, which accepts it.
3. **Evidence.** For API families, paste the usage block from one fast and one reasoning
   smoke-test call. Reasoning tokens should be zero or absent in fast mode and non-zero in
   reasoning mode. For web families, keep a dated screenshot of the mode picker.
4. **Hidden routing.** If a vendor documents that it may route requests to different
   models, note it. It is a threat to validity, not a reason to hide the family.

## Known vendor caveats (as of 2026-10-01)

- **Anthropic.** On Claude Opus 5.5, Sonnet 5.5 and Fable 5.1, thinking cannot be fully
  disabled (`disabled` returns HTTP 400). Sonnet 5.5 offers `between_tools`, which is a
  different treatment. Sonnet 5 and Opus 4.8 accept `disabled`. Do not enable the
  server-side `fallbacks` parameter: it would answer from a different model on refusal.
- **DeepSeek.** The pilot used the web app. The API exposes modes as two model names.
  Confirm they serve the same base model on the run date.
- **Grok.** Fast vs Expert is a consumer UI switch. The underlying model may change
  without notice. Capture all 10 Grok runs within the same 48 hours.
- **All web channels.** Personalisation, memory and A/B tests are uncontrolled. Use a fresh
  chat with memory off and record the interface details in the capture.
