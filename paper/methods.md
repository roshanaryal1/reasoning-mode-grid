# 3. Method (draft)

Draft written 2026-10-14, before any scoring. Every fact here comes from the frozen
pre-registration (`docs/preregistration.md`, tag `prereg-v1`), its Deviations table, the
mode registry, `results/mode_check.md` and the capture files. Nothing here depends on
scores. Items in `[brackets]` are filled once scoring is done.

This is the full-length version for arXiv and TMLR. The ICLR workshop version has about one
page for Method: keep 3.1, Table 1, the first paragraph of 3.4, 3.5 and 3.6 in short form,
and move the rest to the appendix.

## 3.1 Design overview

We ran a crossed 6 x 2 design: six model families (Claude, GPT, Gemini, Qwen, DeepSeek,
Grok) by two modes (fast, reasoning), with five independent replicates per cell, for 60
scored answers. Every answer responds to the same fixed prompt. Within a family, the model
is held fixed and only the vendor's reasoning control changes. The study was
pre-registered before the first scored capture: the plan was frozen on 2026-10-13 (git tag
`prereg-v1`) and registered on OSF the same day (<https://osf.io/nj2zp/>). The single
confirmatory test (H4) asks whether mode explains more variance in the total rubric score
than family does, and whether reasoning scores higher than fast. Three secondary tests
(H1 to H3) ask the same of single rubric dimensions (section 3.6).

## 3.2 Task and prompt

The task is the frozen prompt `prompt-v1` from LA-P1 [Aryal, 2026], reused unchanged and
pinned by SHA-256 (`ba2acba8...0370e0`). It asks the model to act as a senior AI
infrastructure architect and design a fully local, always-on autonomous AI workstation for
one stated machine: an Apple Mac mini with a base M6 chip, 32 GB unified memory, a 512 GB
internal SSD and a 1 TB external SSD. The prompt fixes the date as 31 August 2026, asks for
research into ten areas (local inference, agent runtimes, multi-agent architecture, coding
agents, research agents, memory, computer control, always-on operation, remote access,
storage), and requires eleven labelled deliverables (A to K), including a memory plan (C),
an installation plan (I) and a list of what not to install (J). It is 1,782 words long.

The task has no answer key. It has hard constraints that can be checked: the memory
budget, internal consistency between the recommendations and deliverable J, and whether
each named tool and model exists. That makes it a test of grounding and constraint
reasoning rather than recall. The scope of every conclusion is this one task.

## 3.3 Models and modes

For each vendor we chose a current general-purpose chat model, available to the author's
individual account in the vendor's own web app, that offers both a fast and a reasoning
setting. Table 1 lists the settings. The choice was fixed in the pre-registration before any
capture. These are not all each vendor's top model, and they are not matched on size or
price.

**Table 1.** Models and mode settings. Chat settings were used for the 60 scored runs. API
settings were used once per cell to check that the switch works (section 3.4). The
pre-registration listed GPT-5.6 Sol and Grok 4.6. Both apps had moved to newer models by the
time of collection, GPT-6 and Grok 4.7, and both ran the same model in both modes (Appendix
D).

| Family | Model | Web app | Fast (chat) | Reasoning (chat) | API fast | API reasoning | Fast floor |
|---|---|---|---|---|---|---|---|
| Claude | Claude Sonnet 5.5 | claude.ai | Effort Low | Effort High | adaptive thinking, effort low | adaptive thinking, effort high | lowest available |
| GPT | GPT-6 | chatgpt.com (paid) | Thinking effort Instant | Thinking effort High | `reasoning_effort: none` | `reasoning_effort: high` | off |
| Gemini | Gemini 3.8 Flash | aistudio.google.com | Thinking level Low | Thinking level High | `reasoning_effort: low` | `reasoning_effort: high` | lowest available |
| Qwen | Qwen3.8-Max | chat.qwen.ai | Fast | Thinking | `enable_thinking: false` | `enable_thinking: true` | off |
| DeepSeek | DeepSeek-V4.1-Flash | chat.deepseek.com | DeepThink off | DeepThink on | `enable_thinking: false` | `enable_thinking: true` | off |
| Grok | Grok 4.7 | grok.com | Fast | Expert | `reasoning_effort: low` | `reasoning_effort: xhigh` | lowest available |

**Two kinds of contrast.** Three families can switch reasoning fully off (GPT, Qwen,
DeepSeek). The other three can only set it to a minimum (Claude Sonnet 5.5 rejects
`thinking: disabled`, Gemini 3.8 Flash has no level below low, Grok 4.7 cannot disable
reasoning). For those three the contrast is "low versus high reasoning", not "off versus
on". A pre-registered robustness check analyses the two groups separately (section 3.7).

**Same model in both modes.** We excluded any switch that changes the model (Flash versus
Pro, mini versus full) and any automatic router ("Auto" in ChatGPT, Grok, Qwen and the
consumer Gemini app). Gemini was therefore run in Google AI Studio, Google's own web app,
where the model is picked by name. The consumer Gemini app offered only "Auto", which can
route between Flash-Lite, Flash and Pro by itself. For Claude, GPT, Gemini and Qwen the app
showed the same model name in both modes. The author confirmed that grok.com ran Grok 4.7 in
both Fast and Expert. chat.deepseek.com shows no model name, and the DeepSeek model is the
author's observation of what the app served on 2026-10-13. For DeepSeek we therefore describe
the contrast as the vendor's exposed chat setting, not a verified same-weights manipulation,
as the pre-registration requires.

**Model self-reports.** The prompt asks each model to name itself. Every GPT answer named
"GPT-6" and every Grok answer "Grok 4.7", which is correct. Every DeepSeek and Gemini answer
named an Anthropic Claude model, which is wrong: the app's model picker (Gemini) and the
author's observation (DeepSeek) are the evidence of which model ran. Every self-report is
kept in its capture.

## 3.4 Checking each mode switch through the API

Chat apps do not report reasoning tokens. To show that each documented switch changes how
much the model reasons, we made one API call per family and mode (12 calls) with the
documented API equivalent of each chat setting (Table 1) and the same prompt. These calls
are evidence about the switch only: they were never scored, blinded or pooled with the
chat answers, and they cannot show what a chat app runs internally.

**Table 2.** API mode check. Reasoning tokens as reported by each API (or derived where the
API omits them).

| Family | Model returned | Reasoning tokens, fast | Reasoning tokens, reasoning | Verdict |
|---|---|---|---|---|
| Claude | `claude-sonnet-5-5` | 0 | 14,864 | switch confirmed |
| GPT | `gpt-5.6-sol` | 0 | 6,000 | switch confirmed |
| Gemini | `gemini-3.8-flash` | 0 | 4,911 | switch confirmed |
| Qwen | `qwen3.8-max` | 0 | 23,805 | switch confirmed |
| DeepSeek | `deepseek-v4.1-flash` | 0 | 1,367 | switch confirmed |
| Grok | `grok-4.6` | 131 | 4,627 | lowest available |

The DeepSeek and Qwen checks ran on Alibaba Model Studio, a third-party host. The GPT
reasoning call spent its whole 6,000-token output limit (set by the account's rate limit)
on reasoning and returned no visible answer, and the Claude reasoning call stopped at its
32,000-token limit. Neither affects the evidence that the switch works. The GPT and Grok
checks ran on the pre-registered models (`gpt-5.6-sol`, `grok-4.6`), not on the GPT-6 and
Grok 4.7 that the apps served, so for those two families they show the documented switch on
the planned model only. A second check on 2026-10-19 used the served models. GPT-6 (`gpt-6-sol`) returned 0
reasoning tokens in fast and 6,000 in reasoning, so the switch is confirmed on the model
the app ran. Grok 4.7 (`grok-4.7`) answered in full at effort low with 1,648 reasoning
tokens, but at effort xhigh it stopped twice after a one-sentence preamble, with about
300 to 360 reasoning tokens, as if waiting for a search tool the API call did not offer.
We made no third attempt and changed no setting, so the second Grok check is
inconclusive, and Grok stays in the lowest-available group on the first check. Claude and Gemini
show zero reasoning tokens at their lowest setting on this call, although their
documentation says reasoning cannot be disabled, so we keep them in the "lowest available"
group.

## 3.5 Collecting the answers

All 60 scored answers were collected in each vendor's web app, the way people use these
models and the way LA-P1 was collected. The run order came from a manifest randomised with
seed 20261001. Families were captured one block at a time, in the order each first appears
in the manifest (Qwen, Grok, DeepSeek, Claude, Gemini, GPT). Inside a block, runs followed
manifest order, which mixes fast and reasoning runs, so a vendor change during a block does
not line up with one mode. Each block had to finish within 48 hours and the whole
collection within 14 days.

Each run used a new chat, signed in, with memory off, no custom instructions and no files.
The prompt text was pasted unchanged. Web search was turned off where the app allows it
(DeepSeek's Search toggle and AI Studio's Google Search grounding, both on by default).
Three apps offer no way to turn search off in the chosen mode, and their models searched the
web by themselves: Claude, GPT and Grok. We record this as app behaviour (section 3.8). A
capture file was created immediately before each send with `modegrid new-capture`, which
stamps the UTC time in a field that is never edited. Where a send time was not recorded
exactly (Qwen runs 3 to 10, sent before their capture files were made, and the Gemini and
GPT blocks, whose chats ran side by side), the capture gives the send time as an interval
bounded by known events instead of a guess. Each capture
stores the final answer verbatim, the model name the app showed, the interface settings,
and, where the app shows one, the reasoning panel. Raters never see the reasoning panel.

The Qwen, Gemini and GPT blocks were sent by the author by hand. The Grok, DeepSeek and
Claude blocks were sent, at the author's request, by an AI assistant operating the author's
signed-in browser through a browser extension, with the same settings and one new chat per
run (Appendix D). Collection took place from 2026-10-13 10:45 UTC to
2026-10-14 13:08 UTC, about 26 hours. Every block finished well inside 48 hours: Qwen took
12.9 hours, Claude 4.6, Grok 1.8, GPT 1.1, Gemini 0.6 and DeepSeek 0.2.

**Replacements.** A run was replaced only for an app error, an answer cut off in
transmission, or the wrong model or mode. It was never replaced for a low score or an odd
answer. The replacement was captured straight away in the same block and kept the run id.
The failed attempt was kept in a separate folder and never scored. Getting 60 valid answers
took 66 attempts: one DeepSeek answer cut off at the app's output limit, one DeepSeek app
error, one Qwen run sent in the wrong mode by the operator, and three Claude reasoning runs
stopped by the account's five-hour usage limit. The pre-registration lists errors, cut-offs
and wrong models as reasons to replace. We treated an operator choosing the wrong mode the
same way as a wrong model, and we treated the usage limit as the app being unavailable, so
those three redos did not count toward the two-replacement limit per cell. One extra Qwen
fast chat was sent by mistake and is kept but assigned to no run. No family was dropped.
No answer was an outright refusal: no consensus score is 0 on all nine dimensions. Every
departure from the frozen plan is listed with its date and reason in Appendix D.

## 3.6 Scoring

**Rubric.** Answers were scored on the nine-dimension rubric from LA-P1, each dimension
0, 1 or 2 (total 0 to 18): D1 hardware-constraint adherence, D2 recency, D3 tool
factuality, D4 model factuality, D5 benchmark factuality, D6 citation quality, D7
actionability, D8 security model, and D9 internal consistency. We used the v2 hard anchors
for D1, D7, D8 and D9, which were written to fix low agreement on those four dimensions in
LA-P1. Two checks are mechanical. For D1 the rater runs the memory checker
`memory_budget.py` from LA-P1 on the set of models the answer keeps loaded at the same
time. For D9 the rater first compares deliverable J ("what not to install") with the rest
of the answer, and recommending something J forbids scores 0. An outright refusal scores 0
on every dimension.

**Web verification.** For D3 and D4 the rater searches the web for every recommended tool,
framework and model before scoring. A name that resolves is real. A name that cannot be
found either way is unresolved and scores 1, not 0. Only a name that a search shows does not
exist, or a wrong load-bearing attribute (such as model size), scores 0. We added this rule
because closed-book raters in LA-P1 flagged real tools released after their training cutoff
as fabricated [Aryal, in preparation].

**Raters.** The author collected the captures, so the author does not score. Three raters
score every answer independently and blind: one human who is not an author, and two LLMs
from different vendors, each with live web search: `llm-a`, Claude Opus 5.5 (Anthropic),
and `llm-b`, GPT-6 at Thinking effort High (OpenAI). The human rater (Rater H2) is not an
author and asked that neither their name nor their background be published; the author
knows their identity. Rater H2 replaced an earlier human rater whose returns
were made with AI tools and were not used (Appendix D). `llm-b` scored on 2026-10-19,
`llm-a` from 2026-10-19 to 2026-10-20, and Rater H2 from 2026-10-24 to 2026-10-26. Both LLM raters come from vendors whose
families are scored, so each one's scores for its own vendor's family are also reported
separately.

**Sessions.** Each rater scored one answer per session, from a single file that holds the
fixed rater prompt, the rubric, the scoring protocol, the memory checker and one blinded
answer. Each LLM rater used a new chat for every answer with memory, history and personal
connectors off and web search on, and returned one CSV row. Each rater had their own
random reading order. All three raters got the same instructions. The rubric, reused
unchanged from LA-P1, still carries notes about that study: one names a model, and another
describes what earlier raters missed in certain answers. A rule in the rater prompt told raters
to ignore those parts.

**Blinding.** Raters saw only the final answer. Reasoning panels, interface labels,
timestamps and capture metadata were removed. Self-identification lines near the top of an
answer (the model's own name, which the prompt asks for) were removed without a trace,
and a vendor or model name was masked only where the answer refers to itself. Names used as content were
kept, because the prompt asks for a model and tool stack and D2 to D4 cannot be scored with
the recommendations hidden. A conflict-of-interest disclosure in which an answer names its
own maker ("so discount my view on" that vendor's product) was removed as well. We also
removed clutter that the chat apps add to copied text and that would name the family
outright, such as ChatGPT's citation chips and Grok's citation tags. The original captures
are never edited. Before scoring, an automated audit
(`modegrid blinding-audit`) checked every packet for app clutter, self-disclosure and
masked self-references, and found none. It also counted the model's own style habits that
survive blinding: four habits each appear in only one family (tool-progress text and notes
on the real date in Claude answers, "as of my cutoff" in DeepSeek answers, LaTeX arrows in
Gemini answers), and each is split evenly between fast and reasoning runs, so it can hint
at family but not at mode. Raters guessed the family and mode of every answer, and we
report how often they beat chance as the blinding-failure rate (section 3.7).

**Consensus.** The analysis unit is the median of the three raters' scores for each answer
and dimension. There is no hand adjudication, because the only person who could adjudicate,
the author, is not blind. The total for an answer is the sum of its nine median scores.

**Reliability.** We report Krippendorff's ordinal alpha per dimension across the three
raters, and interval alpha on each rater's total. The pre-registered bar is 0.667. A
dimension below the bar is reported in full but treated as exploratory. H4 stays
confirmatory if the total score's alpha clears the bar. A supported result with alpha
between 0.667 and 0.800 is described as tentative.

## 3.7 Analysis

**Primary statistic.** For each dimension and for the total, we fit a balanced two-way
fixed-effects decomposition (family, mode, family x mode, residual) on the 60 consensus
scores, and compute

delta = omega2(mode) - omega2(family),

where omega2(effect) = (SS_effect - df_effect x MS_residual) / (SS_total + MS_residual).
Negative estimates are kept. We use omega squared rather than eta squared because family
has 5 degrees of freedom and mode has 1, and eta squared rewards extra degrees of freedom
even when they carry only noise. The direction of the mode effect is the mean of reasoning
minus the mean of fast.

**Uncertainty.** We use a 95% percentile bootstrap with 5,000 resamples (seed 20261001),
resampling the five replicates within each cell. Families are treated as fixed, so
conclusions are about these six families. Permutation p-values (5,000 permutations) are
reported beside each interval. The mode permutation shuffles scores between modes within
each family, so it tests the strict null that mode makes no difference in any family. Where
the interval and the p-value disagree, we report both. The bootstrap interval decides every
verdict.

**Decision rule.** "Mode > model" on a dimension means delta is positive and its 95% CI
excludes zero. "Model > mode" means delta is negative and its CI excludes zero. Anything
else is inconclusive. H1, H2 and H4 also require reasoning to score higher than fast, with
a 95% CI above zero. If 90% or more of a dimension's scores share one value, the dimension
is reported as uninformative and its hypothesis as inconclusive.

**Hypotheses.**

- H4 (confirmatory): on the total score, mode > model and reasoning > fast.
- H1 (secondary): on D1 hardware-constraint adherence, mode > model and reasoning > fast.
- H2 (secondary): on D9 internal consistency, mode > model and reasoning > fast.
- H3 (secondary): on D3 tool factuality, model > mode.

H4 is the only confirmatory test and is not corrected for multiplicity. H1 to H3 are
reported uncorrected, with that caveat. The other six dimensions are descriptive. For every
dimension we also report omega squared for the family x mode interaction and each family's
reasoning-minus-fast difference. If the interaction explains more than both main effects,
the H4 verdict is labelled "average effect only".

**Robustness checks** (pre-registered, reported whatever the result):

1. The same analysis on rank-transformed scores.
2. The same analysis after removing the linear effect of log answer length in words. Mode
   changes length, so a shrinking mode effect would mean the two cannot be separated, not
   that length causes the effect.
3. The same analysis on each rater's own scores.
4. The same analysis on the three true-off families (GPT, Qwen, DeepSeek) and on the three
   lowest-available families (Claude, Gemini, Grok). With 30 runs each, these are
   descriptive.

**Blinding failure.** For each rater, we test whether family and mode guesses beat chance
with an exact one-sided binomial test (mode against 1/2, family against 1/6). If any rater
beats chance on mode, H1 to H4 are re-run on each rater's scores and we report whether the
raters who did not beat chance reach the same conclusions. If all three beat chance, a
supported H4 is labelled tentative.

**Power.** Simulation (`modegrid power`, Appendix) gives power of about 0.9 to detect a
mode effect whose variance is five times the family variance, and about 0.4 to 0.6 for a
moderate effect. Under equal effects, 15% of simulated studies still show "mode > model",
which we report beside the H4 result.

## 3.8 Departures from the plan that bear on interpretation

The Deviations table (Appendix D) lists every change. Four bear on how to read the results:

- **Web search.** Claude, GPT and Grok searched the web by themselves in every run, in both
  modes, because their apps offer no switch for it. Gemini and DeepSeek ran with search
  off, and Qwen with no search option turned on. Differences between families can therefore
  include differences in live search, which is how these apps are used.
- **Operators.** Three blocks were sent by the author and three by an AI assistant in the
  author's browser. Settings and procedure were the same.
- **Model identity.** The GPT and Grok apps ran newer models than pre-registered, GPT-6
  and Grok 4.7, released shortly before collection. Each ran one model in both modes, so
  both contrasts remain mode switches, but their API checks cover the planned models.
  DeepSeek shows no model name, so its contrast is the vendor's exposed setting.
- **Blinding fixes before scoring.** Four leaks were found and fixed before any real
  scoring: app clutter copied with the answers, bare "Model:" label lines missed by the
  self-identification rule, the marker lines left where header lines were removed, whose
  count and position differed by family, and conflict-of-interest disclosures that named
  the answer's maker through its own product even with the name masked. All four fixes
  apply to every packet in the same way, and the blinding key did not change.

## 3.9 Materials and code

The harness (`modegrid`), configuration, captures, packets' build rules, scores and analysis
outputs are released at [GitHub tag and Zenodo DOI]. The prompt, rubric and memory checker
are vendored from LA-P1 at commit `d5e39e7` and pinned by SHA-256. All randomness (run
order, reading orders, bootstrap, permutations) is seeded, so the analysis reproduces
exactly from the released scores with `modegrid analyze --seed 20261001 --boot 5000
--perm 5000`.
