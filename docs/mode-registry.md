# Mode registry

"Mode" means something different at every vendor. This file records exactly what each
cell's mode was, how it was switched, and the evidence that the switch worked. Reviewers
will ask. This is the answer.

Fill one row per family before the pre-registration is frozen.

The 60 scored runs use the **chat app** column. The **API check** column is the
documented API equivalent, run once per mode as evidence (`modegrid check-modes`).

| Family | Chat app: fast | Chat app: reasoning | API check: model | API check: fast | API check: reasoning | Doc URL and date read | API check verdict |
|---|---|---|---|---|---|---|---|
| Claude | claude.ai, Sonnet 5.5, Effort Low | claude.ai, Sonnet 5.5, Effort High | `claude-sonnet-5-5` | `thinking: {type: adaptive}`, effort low (lowest available) | `thinking: {type: adaptive}`, effort high | Anthropic API reference (bundled, cached 2026-09-25), 2026-10-06 | switch confirmed (0 vs 14,864) |
| GPT | chatgpt.com (paid), GPT-5.6 Sol, Thinking effort Instant | chatgpt.com (paid), GPT-5.6 Sol, Thinking effort High | `gpt-5.6-sol` | `reasoning_effort: none` | `reasoning_effort: high` | <https://developers.openai.com/api/docs/models/gpt-5.6-sol>, 2026-10-06 | switch confirmed (0 vs 6,000) |
| Gemini | aistudio.google.com, Gemini 3.8 Flash, Thinking level Low, Search grounding off | aistudio.google.com, Gemini 3.8 Flash, Thinking level High, Search grounding off | `gemini-3.8-flash` | `reasoning_effort: low` (lowest available) | `reasoning_effort: high` | <https://ai.google.dev/gemini-api/docs/thinking>, 2026-10-13 | switch confirmed (0 vs 4,911; docs say low cannot disable thinking, so treated as lowest available) |
| Qwen | chat.qwen.ai, Qwen3.8-Max, Fast | chat.qwen.ai, Qwen3.8-Max, Thinking | `qwen3.8-max` | `enable_thinking: false` | `enable_thinking: true` | <https://www.alibabacloud.com/help/en/model-studio/deep-thinking>, 2026-10-06 | switch confirmed (0 vs 23,805) |
| DeepSeek | chat.deepseek.com, Deep thinking off, Smart Search off | chat.deepseek.com, Deep thinking on, Smart Search off | `deepseek-v4.1-flash` via Alibaba Model Studio | `enable_thinking: false` | `enable_thinking: true` | <https://www.alibabacloud.com/help/en/model-studio/deepseek-api>, 2026-10-13 | switch confirmed (0 vs 1,367) |
| Grok | grok.com, Fast | grok.com, Expert | `grok-4.6` | `reasoning_effort: low` (lowest available) | `reasoning_effort: xhigh` | <https://docs.x.ai/developers/model-capabilities/text/reasoning>, 2026-10-05 | lowest available (131 vs 4,627) |

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
| GPT | Paid plan: one GPT-5.6 Sol model with a 3-stop "Thinking effort" slider, High at the right. Secondary sources: Plus stops are Instant, Medium, High, all on Sol; Instant and Thinking were folded into Sol in Aug 2026. OpenAI help page returned 403 | GPT-5.6 Sol, Instant vs High. API: `gpt-5.6-sol`, `reasoning_effort` `none` vs `high`. True off. Confirm the leftmost label reads Instant |
| DeepSeek | DeepThink and Search toggles. Search was on by default | Unchanged. Turn Search off for every capture |
| Grok | Fast, Build, Auto, Expert, Heavy. Author has a premium Grok plan | Unchanged: Fast vs Expert. Record the exact plan name in each Grok capture |

API-check output limits: 64,000 tokens per call by default. GPT uses 6,000, because
the author's OpenAI account allows 10,000 tokens per minute (input is about 3,500). Each
capture records its `max_tokens`. The Claude checks ran before this change at 32,000; the
Claude reasoning answer stopped at that limit (`finish_reason: max_tokens`) after 14,864
thinking tokens. It was not re-run, to save cost: the switch evidence (0 vs 14,864
thinking tokens) does not depend on the answer being complete.

Gemini API free tier: `gemini-3.6-flash` is free of charge, and free-tier content may be
used to improve Google products. Acceptable for the 2 API-check calls, because the prompt
is public.

Sources:

- Claude Sonnet 5.5 thinking and effort: Anthropic API reference bundled with Claude Code (cached 2026-09-25); confirm with the API check
- Gemini models and status: <https://ai.google.dev/gemini-api/docs/models>
- Gemini 3.6 Flash thinking levels: <https://ai.google.dev/gemini-api/docs/generate-content/thinking>
- Gemini API pricing and free tier: <https://ai.google.dev/gemini-api/docs/pricing>
- Qwen3.8-Max thinking: <https://www.alibabacloud.com/help/en/model-studio/deep-thinking>
- GPT-5.6 Sol API: <https://developers.openai.com/api/docs/models/gpt-5.6-sol>
- ChatGPT thinking effort levels (secondary): <https://www.ai-toolbox.co/chatgpt-models/chatgpt-reasoning-modes-instant-thinking-pro-2026>
- GPT-5.6 in ChatGPT (OpenAI help, 403 when fetched): <https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt>

## DeepSeek API check host, 2026-10-07 (superseded 2026-10-13)

The DeepSeek API check runs on Alibaba Model Studio's hosted `deepseek-v4-pro-0813`, on
the author's free quota, instead of DeepSeek's own API. The 10 scored DeepSeek runs still
come from chat.deepseek.com. Limits of this evidence: a third-party host and a dated
snapshot, so it shows that the thinking switch works on DeepSeek V4 Pro weights, not that
the chat app runs the same snapshot. Alibaba's docs list `deepseek-v4-pro` as a hybrid
thinking model switched by `enable_thinking`. The page names `deepseek-v4-pro-0813` as a
dated snapshot in its model list but not in its list of hybrid thinking models, so a free
test was run first: 0 vs 59 reasoning tokens on a short prompt. The full API check then
gave 0 vs 10,546. DashScope omits the
reasoning count when the model does not think, so `_unreported_is_zero` records it as 0
(also set for Qwen, on the same host).

Source: <https://www.alibabacloud.com/help/en/model-studio/deepseek-api>

## App check and decisions, 2026-10-13

The author opened each app again before the freeze and screenshotted the menus. This
section supersedes the 2026-10-06 Gemini and 2026-10-07 DeepSeek decisions.

| Family | Seen in the app | Decision |
|---|---|---|
| GPT | Thinking effort slider: Instant at the left, High at the right | Unchanged |
| Qwen | Qwen3.8-Max, mode menu Auto, Thinking, Fast | Unchanged: Fast vs Thinking, never Auto |
| DeepSeek | No model picker. Author saw it serving DeepSeek-V4.1-Flash. Toggles "Deep thinking" and "Smart Search"; Smart Search was on | DeepSeek-V4.1-Flash, Deep thinking off vs on, Smart Search off. API check re-run on Alibaba-hosted `deepseek-v4.1-flash` |
| Gemini | Free Gemini app: only "Auto (Gemini 3 models)" plus thinking levels Low, Medium, High. No manual model choice | Moved to Google AI Studio. AI Studio marks Gemini 3.6 Flash as Paid, so Gemini 3.8 Flash (current Flash): Thinking level Low vs High, Grounding with Google Search off (it was on by default). API check re-run on `gemini-3.8-flash`, `reasoning_effort` `low` vs `high` |
| Claude, Grok | Not re-checked on 2026-10-13 | Check before the first capture of that family block |

Why Gemini moved: press reports say the free app's Auto mode sends most prompts to
Flash-Lite and may escalate to Flash or Pro, so in that app a thinking-level change could
also change the model. In AI Studio the model is picked by hand.

DeepSeek V4.1-Flash: released 2026-09-10 per DeepSeek's API changelog; DeepSeek's own API
name is `deepseek-flash`. The chat app shows no model name, so "V4.1-Flash" is the author's
observation on 2026-10-13, not a vendor statement about the app.

Google's thinking docs list low, medium (default) and high for `gemini-3.8-flash`, with
no minimal level and no off, so Gemini fast is "lowest available" (low).

Sources:

- Gemini app Auto and thinking levels: <https://9to5google.com/2026/10/09/gemini-auto-free-users/>
- Gemini app models (Google help): <https://support.google.com/gemini/answer/18648722>
- Gemini thinking levels: <https://ai.google.dev/gemini-api/docs/thinking>
- DeepSeek V4.1-Flash release: <https://api-docs.deepseek.com/news/news260910/>
- DeepSeek changelog: <https://api-docs.deepseek.com/updates/>

## API check results, 2026-10-12 (Gemini and DeepSeek re-run 2026-10-13)

One API call per family and mode (`modegrid check-modes`, `results/mode_check.md`).
Reasoning tokens are as reported by each API, or derived where the API omits them (see
`_reasoning_in_total` and `_unreported_is_zero` in `configs/grid.yaml`). Five families
show zero reasoning tokens in fast mode; Grok, which cannot disable reasoning, shows far
fewer in fast mode than in reasoning mode. GPT's reasoning answer is empty because its
6,000-token limit (account rate limit) went on thinking; Claude's reasoning answer stopped
at the 32,000-token limit in force when it ran. Neither affects the switch evidence.

| Family | Words fast | Words reasoning | Reasoning tokens fast | Reasoning tokens reasoning | Model returned | Verdict |
|---|---|---|---|---|---|---|
| claude | 2108 | 6051 | 0 | 14864 | claude-sonnet-5-5 | switch confirmed |
| deepseek | 6916 | 10043 | 0 | 1367 | deepseek-v4.1-flash | switch confirmed |
| gemini | 4592 | 6482 | 0 | 4911 | gemini-3.8-flash | switch confirmed |
| gpt | 4014 | 0 | 0 | 6000 | gpt-5.6-sol | switch confirmed |
| grok | 1990 | 7393 | 131 | 4627 | grok-4.6 | lowest available: fast reasons less, not zero; record both counts |
| qwen | 3315 | 7587 | 0 | 23805 | qwen3.8-max | switch confirmed |

## Vendor releases around the collection window (researched 2026-10-15)

Pre-registration section 3: "Vendor release notes published during the window are recorded
in the mode registry." The window ran from 2026-10-13 10:45 UTC (first Qwen run) to
2026-10-14 13:08 UTC (last GPT run). Searched after collection, before any scoring. arXiv
and the OpenAI help centre were not reachable from the build container, so most sources
below are search results and third-party trackers. Treat dates from trackers as
approximate.

**Inside the window.** No vendor release note for any of the six models was found dated
13 or 14 October 2026. The only item found on those dates is a Google Cloud note (13
October) that CodeMender and AlphaEvolve can use Gemini 4 Argon, with Gemini 3.8 Flash
staying the default. That concerns Google Cloud products, not AI Studio.

**Before the window, bearing on which model ran.** Two releases in the week before
collection bear on the model table in pre-registration section 1. Neither can be settled
from search results. The author's screenshots of each app's model menu are the evidence.

| Family | What was found | Bearing on this study | To check |
|---|---|---|---|
| GPT | GPT-6 launched in ChatGPT on 7 October 2026 for Plus, Pro, Business and Enterprise, taking the "Latest" slot. OpenAI's help article "GPT-6 and other models in ChatGPT" says the rollout does not retire older selectable models and that an explicit GPT-5.6 Sol selection stays on GPT-5.6. A third-party guide says GPT-6 Sol replaced GPT-5.6 Sol in standard chat, and a user report (10 October) says GPT-5.6 Sol was missing from one Plus account's iOS picker | Every GPT answer names itself "GPT-6". Under OpenAI's own statement, an explicit GPT-5.6 Sol choice ran GPT-5.6 Sol and the self-report is wrong. If the menu showed only GPT-6 or "Latest", the GPT family is GPT-6 and section 1's table needs a Deviations row | The GPT screenshots: was "GPT-5.6 Sol" chosen by name, and did the Thinking effort control sit under it? |
| Grok | Grok 4.7 was released on 21 September 2026 for the API, Cursor and Grok Build. Sources disagree on the app: one says it has been rolling into grok.com since 1 to 7 October and names the app's hardest modes, another says it is not yet on grok.com and the app runs Grok 4.6. xAI's news page lists an "Introducing Grok 4.7" item dated 12 October | Every Grok answer, Fast and Expert alike, names itself "Grok 4.7". If Expert moved to 4.7 while Fast stayed on 4.6, the Grok mode contrast is also a model contrast. The pre-registration already describes Grok as vendor chat settings, not a verified same-weights manipulation, because the app shows no model name | The Grok screenshots: does any mode entry name a model version? |
| Claude | Claude Haiku 5.5 released 7 October 2026. Sonnet 5.5 unchanged since 28 September | None. Sonnet 5.5 was picked by name | Nothing |
| Gemini | AI Studio changelog, 8 October: Gemini 3.7 Flash deprecated and routed to 3.8 Flash | None. 3.8 Flash was picked by name | Nothing |
| Qwen | No update found after the Qwen3.8-Max launch | None | Nothing |
| DeepSeek | Last API change found: V4.1-Flash on 10 September 2026. No October changelog entry | None found. The app shows no model name, as already recorded | Nothing |

Sources:

- OpenAI help, GPT-6 and other models in ChatGPT: <https://help.openai.com/en/articles/20001354-gpt-6-and-other-models-in-chatgpt>
- ChatGPT release notes: <https://help.openai.com/en/articles/6825453-chatgpt-release-notes>
- GPT-5.6 Sol missing from picker (user report): <https://github.com/openai/codex/issues/52992>
- ChatGPT versions guide (third party): <https://www.gradually.ai/en/chatgpt-versions/>
- Introducing Grok 4.7: <https://x.ai/news/grok-4-7>
- Grok 4.7 availability (third party): <https://www.lindy.ai/blog/grok-4-7>
- Grok models guide (third party): <https://www.ai-toolbox.co/grok-models/grok-models-explained-2026>
- Anthropic release tracker (third party): <https://releasebot.io/updates/anthropic/claude>
- Gemini API changelog: <https://ai.google.dev/gemini-api/docs/changelog>
- Gemini Enterprise release notes: <https://docs.cloud.google.com/gemini/enterprise/docs/release-notes>
- Qwen3.8-Max blog: <https://qwen.ai/blog?id=qwen3.8>
- DeepSeek V4.1-Flash release: <https://api-docs.deepseek.com/news/news260910/>

## Author confirmation, 2026-10-15

The two open questions above are settled by the author, from the apps:

| Family | Model that ran | Both modes | Effect |
|---|---|---|---|
| GPT | GPT-6 in chatgpt.com, Thinking effort Instant vs High | Same model | Section 1 listed GPT-5.6 Sol. Deviations row. The API check ran on `gpt-5.6-sol`, so it shows the switch on the planned model, not on GPT-6. OpenAI documents `reasoning.effort: none` for GPT-6 Sol, so GPT stays in the true-off group. A check on the GPT-6 API model would confirm it |
| Grok | Grok 4.7 in grok.com, Fast vs Expert | Same model | Section 1 listed Grok 4.6. Deviations row. The Fast and Expert model split is ruled out. The API check ran on `grok-4.6`. Grok 4.7 cannot disable reasoning (low, medium, high, xhigh), so Grok stays in the lowest-available group |

The GPT and Grok self-reports ("GPT-6", "Grok 4.7") were correct. The DeepSeek and Gemini
self-reports (Claude model names) remain model errors.

`configs/grid.yaml` still names `gpt-5.6-sol` and `grok-4.6`, because those are the models
the API check called, and the API-check captures record them.

Sources for the reasoning settings:

- OpenAI reasoning guide (GPT-6 Sol and Luna accept `none`): <https://developers.openai.com/api/docs/guides/reasoning>
- Using GPT-6: <https://developers.openai.com/api/docs/guides/latest-model>
- Grok 4.7 on Oracle Cloud (effort levels, reasoning cannot be turned off): <https://docs.oracle.com/iaas/Content/generative-ai/x-ai-grok-4-7.htm>

### API checks on the served models (added 2026-10-15)

`configs/grid.yaml` lists `api_check_models: [gpt-6-sol]` under GPT and `[grok-4.7]` under
Grok. They add four API-check runs (`apicheck2`) with the same mode settings, appended to
the manifest. Runbook Phase 2b says how to run them. The `gpt-6-sol` id is the GPT-6 variant
that OpenAI documents as accepting `reasoning_effort: none`. Confirm it in the account's
model list before running.
