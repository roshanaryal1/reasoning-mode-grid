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
| GPT | chatgpt.com (paid), GPT-5.5 Instant picked by hand | GPT-5.5 Thinking picked by hand | `gpt-5.5` | `reasoning_effort: none` | `reasoning_effort: high` | | |
| Gemini | gemini.google.com, Fast (3 Flash) | gemini.google.com, Thinking (3 Flash) | FILL-ME, the Flash version the app runs | lowest accepted level | thinking high | | |
| Qwen | chat.qwen.ai, Qwen3.7-Plus, Thinking off | chat.qwen.ai, Qwen3.7-Plus, Thinking on | `qwen3.7-plus` | `enable_thinking: false` | `enable_thinking: true` | | |
| DeepSeek | chat.deepseek.com, DeepThink off | chat.deepseek.com, DeepThink on | `deepseek-v4-pro` | `thinking: {type: disabled}` | thinking on (default), effort high | | |
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

## Research notes, 2026-10-02

Found by web search. Each line still needs confirming against the vendor's own docs on
the day of the API check, and the API check itself is the evidence.

| Family | Finding | Effect on the design |
|---|---|---|
| GPT | GPT-5.5 accepts `reasoning_effort` none, low, medium (default), high, xhigh. Base GPT-5 accepts minimal to high, not none | Use GPT-5.5 with `none` vs `high` |
| GPT | In ChatGPT, "Instant" can route a request to Thinking automatically. Free plans can fall back to GPT-5.5 Instant Mini | Paid plan, pick the mode by hand, record any thinking trace in a fast capture |
| Gemini | Gemini 3.x cannot turn thinking off. Gemini 2.5 Flash can (budget 0 or `reasoning_effort: none`). Some 3.x Flash models reject `minimal` | Decide between an older model with true off, or a current model at its lowest level |
| Qwen | `enable_thinking` toggles thinking on Qwen3 to 3.7 hybrid models via DashScope's OpenAI-compatible endpoint. Thinking returns as `reasoning_content` | Settings as configured, pick the model |
| DeepSeek | `deepseek-chat` and `deepseek-reasoner` stopped resolving on 24 Jul 2026. V4 models think by default. `thinking: {type: disabled}` turns it off. `reasoning_effort: none` returns 400 | Use `deepseek-v4-pro`, the same base model as the pilot |
| Gemini app | Fast and Thinking are both Gemini 3 Flash. Pro is a different model | App Fast vs Thinking is valid. Never use Pro |
| Qwen | API model `qwen3.7-plus`, `enable_thinking` in the request body. chat.qwen.ai has a Thinking toggle | Fully specified |
| Grok app | Fast skips reasoning, Expert forces deep reasoning, Auto routes between them | Use Fast and Expert, never Auto |
| Grok | `grok-4.3` accepts `reasoning_effort` none to xhigh. 4.5: low to high. 4.6 and 4.7: low to xhigh | Only 4.3 has a true off. The chat app's Fast vs Expert may not map to one API model |

Sources:

- OpenAI GPT-5.5 model page: <https://developers.openai.com/api/docs/models/gpt-5.5>
- OpenAI GPT-5 model page: <https://developers.openai.com/api/docs/models/gpt-5>
- GPT-5.5 in ChatGPT (Instant routing): <https://help.openai.com/en/articles/11909943-gpt-5-5-in-chatgpt>
- Gemini thinking: <https://ai.google.dev/gemini-api/docs/generate-content/thinking>
- Gemini OpenAI compatibility: <https://ai.google.dev/gemini-api/docs/openai>
- Qwen deep thinking via API: <https://www.alibabacloud.com/help/en/model-studio/deep-thinking>
- DeepSeek legacy name retirement: <https://www.developersdigest.tech/blog/deepseek-chat-to-v4-migration-guide>
- DeepSeek V4 thinking disabled (400 on reasoning_effort none): <https://github.com/OpenWhispr/openwhispr/issues/1260>
- xAI reasoning: <https://docs.x.ai/developers/model-capabilities/text/reasoning>
- Gemini app Fast and Thinking on 3 Flash: <https://9to5google.com/2025/12/17/gemini-app-3-flash-rollout/>
- Qwen3.7-Plus: <https://qwen.ai/blog?id=qwen3.7-plus>
- Grok modes: <https://mundobytes.com/en/What-are-the-heavy--expert--fast--and-auto-modes-in-Grok-used-for/>
