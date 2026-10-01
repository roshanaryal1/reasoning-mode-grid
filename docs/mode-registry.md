# Mode registry

"Mode" means something different at every vendor. This file records exactly what each
cell's mode was, how it was switched, and the evidence that the switch worked. Reviewers
will ask. This is the answer.

Fill one row per family before the pre-registration is frozen.

The 60 scored runs use the **chat app** column. The **API check** column is the
documented API equivalent, run once per mode as evidence (`modegrid check-modes`).

| Family | Chat app: fast | Chat app: reasoning | API check: model | API check: fast | API check: reasoning | Doc URL and date read | API check verdict |
|---|---|---|---|---|---|---|---|
| Claude | claude.ai, Sonnet 5, extended thinking off | claude.ai, Sonnet 5, extended thinking on | `claude-sonnet-5` | `thinking: {type: disabled}` | `thinking: {type: adaptive}`, effort high | | |
| GPT | FILL-ME, one named model, thinking off | same model, thinking on | FILL-ME | lowest `reasoning_effort` | `reasoning_effort: high` | | |
| Gemini | FILL-ME, one model, thinking off | same model, thinking on | FILL-ME | thinking off | thinking high | | |
| Qwen | chat.qwen.ai, Thinking off | chat.qwen.ai, Thinking on | FILL-ME | `enable_thinking: false` | `enable_thinking: true` | | |
| DeepSeek | chat.deepseek.com, DeepThink off | chat.deepseek.com, DeepThink on | two API names, confirm same weights | non-thinking name | thinking name | | |
| Grok | grok.com, Fast | grok.com, Expert | FILL-ME | lowest reasoning setting | highest reasoning setting | | |

## Rules

1. **Same weights.** A mode may change thinking budget, reasoning effort, or a thinking
   toggle. It may not change the model. Flash vs Pro, mini vs full, or "auto" routers
   that may pick a different model are not modes.
2. **Lowest available, not "off".** Some vendors no longer offer a true no-reasoning
   setting. Then the fast mode is the lowest setting, and this file says so. Example:
   Claude Opus 5.5 rejects `thinking: disabled`, so the grid uses Sonnet 5, which accepts it.
3. **Evidence.** Two kinds. For every chat run, a dated screenshot of the model and mode
   selector. For every family, the API check: reasoning tokens should be zero or absent
   in fast mode and non-zero in reasoning mode. Paste the `modegrid check-modes` table here.
4. **Chat and API are not identical.** A chat app adds its own system prompt and may
   use a different snapshot. The API check proves the switch exists and what it does.
   It does not prove the chat app ran the same weights. Say this in the paper.
5. **Hidden routing.** If a vendor documents that it may route requests to different
   models, note it. It is a threat to validity, not a reason to hide the family.

## Known vendor caveats (as of 2026-10-01)

- **Anthropic.** On Claude Opus 5.5, Sonnet 5.5 and Fable 5.1, thinking cannot be fully
  disabled (`disabled` returns HTTP 400). Sonnet 5.5 offers `between_tools`, which is a
  different treatment. Sonnet 5 and Opus 4.8 accept `disabled`. Do not enable the
  server-side `fallbacks` parameter: it would answer from a different model on refusal.
- **DeepSeek.** The pilot used the web app. The API exposes modes as two model names.
  Confirm they serve the same base model on the run date.
- **Grok.** Fast vs Expert is a consumer UI switch. The underlying model may change
  without notice. Capture all 10 Grok runs within the same 48 hours. The API check can
  only approximate the switch with a reasoning setting.
- **All web channels.** Personalisation, memory and A/B tests are uncontrolled. Use a fresh
  chat with memory off and record the interface details in the capture.
