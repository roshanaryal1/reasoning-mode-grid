# Appendix (draft)

Draft written 2026-10-14, before any scoring. Appendix B is filled after the analysis.
Sources: `docs/mode-registry.md`, `results/mode_check.md`, `data/pilot/`, and the
Deviations table in `docs/preregistration.md` (section 10).

## A. Mode registry

What each mode was, how it was switched, and the evidence. Chat settings were used for the
60 primary chat answers. Twelve original and four follow-up API calls measured
reported reasoning usage. They cannot verify hidden chat-app routing.

| Family | Chat app, fast | Chat app, reasoning | API model | API fast | API reasoning | Docs read | Reasoning tokens (fast vs reasoning) |
|---|---|---|---|---|---|---|---|
| Claude | claude.ai, Sonnet 5.5, Effort Low | claude.ai, Sonnet 5.5, Effort High | `claude-sonnet-5-5` | adaptive thinking, effort low | adaptive thinking, effort high | Anthropic API reference, 2026-10-06 | 0 vs 14,864 |
| GPT | chatgpt.com (paid), GPT-6, Thinking effort Instant | same, Thinking effort High | `gpt-5.6-sol` | `reasoning_effort: none` | `reasoning_effort: high` | OpenAI model page, 2026-10-06 | 0 vs 6,000 |
| Gemini | aistudio.google.com, Gemini 3.8 Flash, Thinking level Low, Search grounding off | same, Thinking level High | `gemini-3.8-flash` | `reasoning_effort: low` | `reasoning_effort: high` | Gemini thinking docs, 2026-10-13 | 0 vs 4,911 |
| Qwen | chat.qwen.ai, Qwen3.8-Max, Fast | same, Thinking | `qwen3.8-max` | `enable_thinking: false` | `enable_thinking: true` | Alibaba Model Studio docs, 2026-10-06 | 0 vs 23,805 |
| DeepSeek | chat.deepseek.com, DeepThink off, Search off | same, DeepThink on | `deepseek-v4.1-flash` (Alibaba-hosted) | `enable_thinking: false` | `enable_thinking: true` | Alibaba Model Studio docs, 2026-10-13 | 0 vs 1,367 |
| Grok | grok.com, Grok 4.7, Fast | grok.com, Grok 4.7, Expert | `grok-4.6` | `reasoning_effort: low` | `reasoning_effort: xhigh` | xAI reasoning docs, 2026-10-05 | 131 vs 4,627 |
| GPT follow-up | GPT-6, same app captures | Same | `gpt-6-sol` | `reasoning_effort: none` | `reasoning_effort: high` | 2026-10-19 | 0 vs 6,000, switch confirmed |
| Grok follow-up | Grok 4.7, same app captures | Same | `grok-4.7` | `reasoning_effort: low` | `reasoning_effort: xhigh` | 2026-10-19 | 1,648 vs 363, inconclusive |

Notes on the evidence:

- **Fast floor.** GPT, Qwen and DeepSeek can switch reasoning fully off. Claude Sonnet 5.5
  rejects `thinking: disabled`, Gemini 3.8 Flash has no level below low, and Grok 4.7
  cannot disable reasoning. For those three, "fast" is the lowest available setting. Claude
  and Gemini returned zero reasoning tokens at that setting on this one call, but we keep
  them in the lowest-available group because their documentation says reasoning cannot be
  turned off.
- **Limits of the API calls.** The GPT reasoning call spent its whole 6,000-token output
  limit, set by the account's rate limit, on reasoning and returned no visible answer. The
  Claude reasoning call stopped at its 32,000-token limit. The DeepSeek and Qwen calls ran
  on Alibaba Model Studio, a third-party host. None of this affects the evidence that the
  switch works.
- **Model identity in the app.** Claude, GPT, Gemini and Qwen show the model name in the
  model picker. The author confirmed that grok.com ran Grok 4.7 in both modes. DeepSeek
  shows no model name, so its model is the author's observation.
- **Planned and actual models.** The pre-registration listed GPT-5.6 Sol and Grok 4.6. GPT-6
  reached ChatGPT on 7 October 2026 and Grok 4.7 reached grok.com in early October, and the
  apps served those during collection. The API checks for these two families ran on the
  planned API models. Four follow-up calls checked GPT-6 and Grok 4.7 as served in the apps.
  The GPT-6 API switch was confirmed, but Grok 4.7 was inconclusive (Expert stopped early).
  Neither result verifies hidden chat-app routing or alters the frozen robustness groups. No release note for any of the six
  models was found inside the collection window. Sources are in the mode registry.
- **Superseded checks.** Earlier API checks for Gemini (on 3.6 Flash and before an adapter
  fix) and DeepSeek (on V4 Pro) are kept in `data/captures/superseded/` with the reason for
  each.

## B. Per-cell scores

[After the analysis: `results/cell_means.csv` (mean of each dimension and the total per
family and mode), `results/family_mode_effects.csv` (reasoning minus fast per family and
dimension), and the full `results/variance_table.md`.]

## C. Pilot data and why it is excluded

The study grew out of three DeepSeek answers collected for LA-P1 on 2026-08-31, before this
study was designed: one per mode (deep reasoning, fast, and fast with the DeepThink toggle),
scored with the v1 rubric and adjudicated by hand.

| Pilot answer | Mode | Total (of 18) | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| deepseek-expert | reasoning | 8 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 2 | 0 |
| deepseek-instant | fast | 9 | 1 | 2 | 1 | 2 | 0 | 0 | 1 | 2 | 0 |
| deepseek-instant-deepthink | exploratory | 6 | 0 | 2 | 1 | 0 | 0 | 0 | 1 | 1 | 1 |

The pilot is excluded from every confirmatory analysis for three reasons: it predates the
pre-registration, it used the v1 rubric without the v2 anchors, and it has one answer per
mode, so it cannot separate a mode effect from run-to-run noise.
Its adjudicated totals do not show a reasoning advantage (8 versus 9), which the
pre-registration states so that the result cannot be framed as confirming the pilot. On the
original v1 fabrication audit the fast answers looked much worse, but most of those
"fabrications" were later shown to be real tools released after the auditor's training
cutoff, which is why D3 and D4 now require web verification.

## D. Deviations from the pre-registration

The pre-registration was frozen on 2026-10-13 and registered on OSF the same day. Every
later change is listed with its date and reason in section 10 of
`docs/preregistration.md`, which is reproduced in full in the released materials. In
summary:

| Area | Changes | Effect on the analysis |
|---|---|---|
| Operators and send times | Three blocks sent by an AI browser assistant at the author's request, three by the author. Send times recorded as exact times or as bounded intervals where chats ran side by side | None on scores. Disclosed for transparency |
| Replacements | 6 failed attempts replaced: 3 Claude reasoning runs stopped by a usage limit (treated as the app being down), 1 DeepSeek cut-off, 1 DeepSeek app error, 1 Qwen run sent in the wrong mode (treated like a wrong model). One extra Qwen chat kept, unscored | 60 valid answers from 66 attempts. No family dropped |
| App behaviour | Claude, GPT and Grok searched the web by themselves, with no switch to stop it. Two DeepSeek fast answers were finished with the app's own "Continue" button | Family differences may include live search. Stated as a limitation |
| Models that ran | GPT ran GPT-6 and Grok ran Grok 4.7, not the pre-registered GPT-5.6 Sol and Grok 4.6, confirmed by the author. Each ran one model in both modes. The GPT captures' `model_returned` field is corrected in the Deviations table, not in the write-once captures. Rater `llm-b` is GPT-6 too | Four follow-up calls: GPT-6 confirmed; Grok 4.7 inconclusive. No analysis group change |
| Model self-reports | DeepSeek and Gemini answers named Claude models, which is wrong. GPT ("GPT-6") and Grok ("Grok 4.7") answers named themselves correctly | DeepSeek contrast described as a vendor chat setting |
| Reasoning traces | Kept where the app showed them. One GPT trace not captured | None. Raters never see traces |
| Blinding, before scoring | Four fixes: chat-app clutter removed, bare "Model:" label lines removed, removed header lines leave no marker, and self-disclosures naming the answer's maker removed | Same rule for every packet. Key unchanged |
| Raters | Two LLM raters named after the freeze; human H1 registered anonymously 2026-10-19. One answer per session from a fixed kit, instructions hashed before scoring | Independent scores still pending |

## D2. Pre-scoring blinding audit

`results/blinding_audit.csv`, from `modegrid blinding-audit` on the final packets, before any
scoring. Each row counts the packets in each cell that contain a pattern.

| Pattern | Kind | Packets | Where |
|---|---|---|---|
| Masked self-reference, self-disclosure, app tracking parameters, app citation markup, Grok citation tags, app images, tool file links | leak | 0 | none |
| Tool-progress text ("I'll start by verifying ...") | style | 8 | Claude, 4 fast and 4 reasoning |
| Note that the real date differs from the prompt's | style | 8 | Claude, 4 fast and 4 reasoning |
| "As of my cutoff" | style | 8 | DeepSeek, 4 fast and 4 reasoning |
| LaTeX arrows in prose | style | 7 | Gemini, 4 fast and 3 reasoning |
| Mentions a downloadable archive | style | 1 | GPT, reasoning |

Style habits are the model's own text and stay, as the pre-registration requires. Each one
is confined to a single family but balanced across modes, so it can reveal family but not
mode. Family guesses above chance are expected and do not change any hypothesis's status
(pre-registration section 4).

## E. Data and code availability

Code (MIT) and data (CC-BY-4.0) at [GitHub tag] and [Zenodo DOI]. The release holds the
configuration, the randomised manifest, all 76 captures (60 primary chat answers, 12 initial and 4 follow-up API checks) and the
superseded attempts, the blinding rules (packets are rebuilt from the captures and the
committed key), the three rater sheets, the consensus scores and every analysis output.
The prompt, rubric and memory checker are vendored from LA-P1 at commit `d5e39e7` and
pinned by SHA-256. All randomness is seeded.
