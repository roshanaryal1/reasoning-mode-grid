# Mode registry

"Mode" means something different at every vendor. This file records exactly what each
cell's mode was, how it was switched, and the evidence that the switch worked. Reviewers
will ask. This is the answer.

Fill one row per family before the pre-registration is frozen.

The 60 scored runs use the **chat app** column. The **API check** column is the
documented API equivalent, run once per mode as evidence (`modegrid check-modes`).

| Family | Chat app: fast | Chat app: reasoning | API check: model | API check: fast | API check: reasoning | Doc URL and date read | API check verdict |
|---|---|---|---|---|---|---|---|
| Claude | claude.ai, Sonnet 5.5, Effort Low | claude.ai, Sonnet 5.5, Effort High | `claude-sonnet-5-5` | `thinking: {type: adaptive}`, effort low (lowest available) | `thinking: {type: adaptive}`, effort high | Anthropic API reference (bundled, cached 2026-09-25), 2026-10-06 | |
| GPT | chatgpt.com (paid), GPT-5.5 Instant picked by hand | GPT-5.5 Thinking picked by hand | `gpt-5.5` | `reasoning_effort: none` | `reasoning_effort: high` | | |
| Gemini | gemini.google.com, 3.6 Flash, Extended thinking off | gemini.google.com, 3.6 Flash, Extended thinking on | `gemini-3.6-flash` | `reasoning_effort: minimal` (lowest available) | `reasoning_effort: high` | <https://ai.google.dev/gemini-api/docs/generate-content/thinking>, 2026-10-06 | |
| Qwen | chat.qwen.ai, Qwen3.8-Max, Fast | chat.qwen.ai, Qwen3.8-Max, Thinking | `qwen3.8-max` | `enable_thinking: false` | `enable_thinking: true` | <https://www.alibabacloud.com/help/en/model-studio/deep-thinking>, 2026-10-06 | |
| DeepSeek | chat.deepseek.com, DeepThink off | chat.deepseek.com, DeepThink on | `deepseek-v4-pro` | `thinking: {type: disabled}` | thinking on (default), effort high | | |
| Grok | grok.com, Fast | grok.com, Expert | `grok-4.6` | `reasoning_effort: low` (lowest available) | `reasoning_effort: xhigh` | <https://docs.x.ai/developers/model-capabilities/text/reasoning>, 2026-10-05 | |

## Rules

1. **Same weights.** A mode may change thinking budget, reasoning effort, or a thinking
   toggle. It may not change the model. Flash vs Pro, mini vs full, or "auto" routers
   that may pick a different model are not modes.
2. **Lowest available, not "off".** Some vendors no longer offer a true no-reasoning
   setting. Then the fast mode is the lowest setting, and this file says so. Example:
   Claude Sonnet 5.5 rejects `thinking: disabled`, so the grid's Claude fast mode is effort low.
3. **Evidence.** Two kinds. For every chat run, a dated screenshot of the model and mode
   selector. For every family, the API check: reasoning tokens should be zero or absent
   in fast mode and non-zero in reasoning mode. For a "lowest available" family (Gemini,
   Grok), fast reasoning tokens are expected to be above zero but below reasoning mode;
   `check-modes` reports this as "lowest available" and both counts go in the paper.
   Paste the `modegrid check-modes` table here.
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

## Research notes and decisions, 2026-10-05

Gemini and Grok decided. Vendor docs were read on 2026-10-05; app details come from press
and secondary sources and are marked as such.

| Family | Finding | Source type | Decision |
|---|---|---|---|
| Gemini | `gemini-3.8-flash` is GA. Thinking levels low, medium (default), high. `minimal` returns an error. Thinking cannot be disabled | Vendor docs | Fast = `low` (lowest available), reasoning = `high` |
| Gemini | On the OpenAI-compatible endpoint, `none` works only on Gemini 2.5. Reasoning cannot be turned off for 2.5 Pro or any Gemini 3 model | Vendor docs | 2.5 Flash rejected: true off, but not in the app |
| Gemini app | Since 17 May 2026 the picker lists Flash-Lite, Flash and Pro. Thinking is a level set on the chosen model. Fast and Thinking are gone, so the 2026-10-02 app note is out of date | Secondary | Use Flash in both modes, never Pro |
| Gemini app | An October 2026 update adds low, medium and high effort levels per model. From 9 Oct 2026 free accounts get Flash-Lite only, and AI Plus keeps Flash | Press | Use AI Plus or higher. Write the exact level label into each capture. All 10 Gemini runs in one 48-hour window |
| Gemini app | 3.8 Flash went GA on 2 Sep 2026 and became the app's default Flash | Secondary, [UNVERIFIED] by Google | Confirm the model name the app shows on capture day |
| Grok | `grok-4.6` accepts `reasoning_effort` low, medium, high (default), xhigh. Reasoning cannot be disabled on 4.5, 4.6, 4.7 | Vendor docs | Fast = `low` (lowest available), reasoning = `xhigh` |
| Grok | `grok-4.3` is still listed on the models page but no longer on the reasoning page, which supersedes the 2026-10-02 note that it accepts `none` | Vendor docs | Not used. It is not the app model |
| Grok app | Every grok.com plan runs Grok 4.6. Grok 4.7 (21 Sep 2026) launched for Cursor, Grok Build and the API, with no app announcement | Secondary (15 Sep 2026) and vendor news | API model `grok-4.6` |
| Grok app | xAI does not document whether app Fast is 4.6 at low effort or a separate non-reasoning model | None found | Kept as a threat to validity. Record the app's model name in every capture |

Sources:

- Gemini 3.8 Flash: <https://ai.google.dev/gemini-api/docs/latest-model>
- Gemini thinking levels per model: <https://ai.google.dev/gemini-api/docs/generate-content/thinking>
- Gemini OpenAI compatibility, `reasoning_effort` mapping: <https://ai.google.dev/gemini-api/docs/openai>
- Gemini app tier limits and effort levels, Oct 2026: <https://9to5google.com/2026/10/03/gemini-model-limits-oct-26/>
- Gemini app picker change, 17 May 2026 (secondary): <https://www.izzedo.chat/blog/gemini-thinking-vs-pro>
- xAI reasoning: <https://docs.x.ai/developers/model-capabilities/text/reasoning>
- xAI models: <https://docs.x.ai/developers/models>
- Grok 4.7 launch: <https://x.ai/news/grok-4-7>
- Grok app runs 4.6 on every plan (secondary): <https://www.ai-toolbox.co/grok-models/grok-models-explained-2026>

## App check and decisions, 2026-10-06

The author opened each chat app and screenshotted the model and mode menus. Where an app
and an earlier note disagree, the app wins. This section supersedes the 2026-10-05
Gemini decision.

| Family | Seen in the app | Decision |
|---|---|---|
| Claude | claude.ai picker: Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 4.5. Effort menu: Low, Medium, High, Extra, Max. No Sonnet 5, no thinking on/off switch | Sonnet 5.5, Effort Low vs High. API: `claude-sonnet-5-5`, adaptive thinking, effort `low` vs `high`. `thinking: disabled` returns 400 on Sonnet 5.5, so fast is lowest available |
| Gemini | Picker: 3.5 Flash-Lite, 3.6 Flash, 3.1 Pro, plus "Extended thinking". No 3.8 Flash | 3.6 Flash, Extended thinking off vs on. API: `gemini-3.6-flash` (Stable), `reasoning_effort` `minimal` vs `high`. Google: minimal "does not guarantee that thinking is off". The 2026-10-05 note that 3.8 Flash is the app default was wrong for this account |
| Qwen | Picker includes Qwen3.7-Plus and Qwen3.8-Max. Mode menu on Qwen3.7-Plus: Auto, Thinking, Fast | Qwen3.8-Max, Fast vs Thinking, never Auto. API: `qwen3.8-max`, hybrid thinking on by default, `enable_thinking` false vs true. Not directly comparable with LA-P1, which used Qwen3.7-Plus |
| GPT | Free plan seen; author will use a paid plan | Unchanged: paid plan, GPT-5.5 Instant vs Thinking picked by hand |
| DeepSeek | DeepThink and Search toggles. Search was on by default | Unchanged. Turn Search off for every capture |
| Grok | Fast, Build, Auto, Expert, Heavy. SuperGrok upgrade banner on a free account | Unchanged: Fast vs Expert. Confirm Expert is usable on the plan before capture |

Gemini API free tier: `gemini-3.6-flash` is free of charge, and free-tier content may be
used to improve Google products. Acceptable for the 2 API-check calls, because the prompt
is public.

Sources:

- Claude Sonnet 5.5 thinking and effort: Anthropic API reference bundled with Claude Code (cached 2026-09-25); confirm with the API check
- Gemini models and status: <https://ai.google.dev/gemini-api/docs/models>
- Gemini 3.6 Flash thinking levels: <https://ai.google.dev/gemini-api/docs/generate-content/thinking>
- Gemini API pricing and free tier: <https://ai.google.dev/gemini-api/docs/pricing>
- Qwen3.8-Max thinking: <https://www.alibabacloud.com/help/en/model-studio/deep-thinking>
