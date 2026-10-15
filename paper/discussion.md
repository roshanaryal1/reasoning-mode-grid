# 5. Discussion (draft)

Draft written 2026-10-14, before any scoring. Only the limitations are written, because
they do not depend on the result. The interpretation paragraphs are outlined with
placeholders and are written after the analysis, for whichever way H4 goes.

## 5.1 What the result means for evaluation practice

[If mode > model on the total: a comparison that names the model but not the mode is
confounded. Leaderboards and papers should report the mode, and a user's choice of mode
deserves as much care as their choice of vendor.]

[If model > mode: on this task, which model you use matters more than how hard it thinks.
That runs against the LA-P1 observation and is worth reporting with equal weight.]

[If inconclusive: say what the CIs rule out, with the power analysis (Section 3.7). A
moderate mode effect was expected to be missed about half the time.]

## 5.2 Mode-sensitive and mode-stable dimensions

[Which dimensions moved with mode and which with family. Link back to H1 to H3, including
the competing prediction for D3 from the reasoning-and-factuality literature. Report the
interaction and the per-family differences where they matter.]

## 5.3 Limitations

**One task.** All 60 answers respond to one prompt. Replicates measure variability on that
task, not across design tasks. The task is long, open-ended and constrained by a stated
memory budget, so it may favour careful reasoning more than a typical request does.

**Six families, treated as fixed.** The conclusions are about these six models in these
settings during one 26-hour collection window, not about models in general. The models are
not matched on size or price, and some are not their vendor's strongest model.

**Mode is not one control.** "Fast" means reasoning switched off for GPT, Qwen and
DeepSeek, and the lowest available level for Claude, Gemini and Grok. Even an off switch
may not stop all reasoning on an open-ended task. The API check shows each switch changes
how much the model reasons, but it cannot show what a chat app runs internally. The
pre-registered split by fast-mode floor shows whether a result holds only for off versus
on.

**Chat apps, not the API.** Each vendor's app adds its own system prompt and may change
without notice. This matches how people use these models and how LA-P1 collected its
answers, but it trades away control. In particular, three apps (Claude, GPT and Grok)
searched the web by themselves with no way to turn it off, while two (Gemini and DeepSeek)
ran with search off. Differences between families may partly reflect live search.

**Model identity.** Chat apps change their models without asking. Two of six apps had
moved to a newer model by the time of collection (GPT-6 and Grok 4.7 instead of the
pre-registered GPT-5.6 Sol and Grok 4.6). Each still ran one model in both modes, so the
contrasts stay mode switches, but the API evidence for those two switches comes from the
planned models. DeepSeek's app shows no model name at all. This is the cost of testing the
apps people use rather than a fixed API snapshot, and the reason every capture is dated.

**Family is confounded with date and operator.** Families were captured one block at a
time, so family is partly confounded with time of day, and three blocks were sent by an AI
browser assistant and three by the author. Neither is confounded with mode, because fast
and reasoning runs were interleaved within each block.

**Blinding is partial.** Raters see recommended models and tools, which D2 to D4 need, and
an answer that favours its own vendor's models may reveal its family. Reasoning answers may
also read differently. We measure this as the rate at which raters guess family and mode
above chance, and the pre-registration sets what follows if they do.

**LLM raters.** Two of three raters are LLMs from vendors whose families are scored. We
report each one's scores for its own vendor's family separately, report agreement between
the human and each LLM, and use the median of three. A single human rater limits what the
study can say about human judgment.

**Small cells.** Five replicates per cell detect a strong mode effect reliably but miss a
moderate one about half the time, and percentile bootstrap intervals at this size can be
too narrow. Under equal effects, 15% of simulated studies still show "mode > model". We
report permutation p-values beside every interval.

**Single author.** No second author checked the analysis. The plan was registered before
collection, the author did not score, and all data and code are released so anyone can
re-run it.
