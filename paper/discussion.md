# 5. Discussion (draft)

Limitations written 2026-10-14, before any scoring. Sections 5.1, 5.2 and the conclusion
written 2026-10-26, after the analysis, for the result that occurred (model > mode).

## 5.1 What the result means for evaluation practice

On this task, which model answered mattered far more than how hard it was told to think.
Family explained 58% of the variance in the total score after bias correction, mode 5%,
and the interval on their difference lies wholly below zero (Section 4.2). Every dimension
points the same way, and the verdict survives rank transformation, each rater's own
scores, both fast-mode groups and the removal of each LLM rater's own-vendor scores. That
runs against the observation that motivated the study: LA-P1 saw one family's answers
change across modes and asked whether mode could rival the choice of vendor. In a
controlled grid it does not.

The result does not say mode is irrelevant. Reasoning scored 1.37 points higher than fast
out of 18, with an interval above zero. But that average hides most of the story. Three of
six families improved, one did not move and two got worse (Table 5). Qwen alone rose by
6.80 points; the other five averaged +0.28. The gain sits almost entirely in the families
whose fast mode turns reasoning off (+2.53), not in those where it only lowers it (+0.20).
And it is tied to length: once answer length is removed, the mode effect on the total
falls to 0.62 points and mode's share of the variance to 0.008 (Section 4.5). Reasoning
answers are longer, and longer answers score higher on this rubric. The design cannot say
whether the extra length carries the extra quality or merely accompanies it.

For anyone comparing models, the practical reading is twofold. First, the choice of model
should come first: no mode setting closed the gap between the strongest and weakest
families (GPT at 15.0 and 16.4, Gemini at 9.4 in both modes). Second, mode should
still be reported, because its effect is not one number. The family x mode interaction
(omega squared 0.184) is larger than the average mode effect (0.050), so "reasoning helps"
is true for some models and false for others. A leaderboard that names the mode lets a
reader see that; one that does not hides a difference of up to 6.8 points for a single
model.

The LLM raters add a caution of their own. Each scored its own vendor's answers about 1.1
to 1.5 points higher, relative to the other raters, than it scored everyone else (Section
4.8). That is as large as the average mode effect. The H4 verdict does not depend on it,
but a study that compares modes or models with a single LLM judge from one of the vendors
being compared could easily mistake self-preference for an effect.

## 5.2 Mode-sensitive and mode-stable dimensions

No dimension was mode-sensitive in the pre-registered sense. Family dominated eight of
nine, and the ninth (D7, actionability) was inconclusive. The secondary hypotheses that
predicted a mode effect, H1 on hardware-constraint adherence and H2 on internal
consistency, both failed in direction, and all three secondary tests are exploratory
because their dimensions did not reach the reliability bar.

Within that pattern, the dimensions differ in how much mode moved them. D9, internal
consistency, had the largest reasoning gain (+0.43 of 2) and the only gain that survived
the length adjustment (+0.41). It also had the largest interaction (eta squared 0.226),
as Claude (0.4 to 1.4) and Qwen (0.0 to 1.8) rose while Grok fell (2.0 to 1.2). If any part of the answer
benefits from reasoning beyond writing more, it is keeping the deliverables consistent with
each other. D9's agreement was low (alpha 0.29), so this is a lead for future work, not a
finding. D1, the memory-budget check that H1 expected reasoning to improve, did not move at
all on average (0.00), even though it is the dimension where a careful calculation should
help most.

D3, tool factuality, was mode-stable, as H3 predicted. The competing account, that
reasoning models invent more tools, did not appear: reasoning minus fast on D3 was -0.10
with an interval that includes zero. This dimension carries a reliability warning of its
own. Its alpha was the lowest of all (0.25), and the human rater's ranking of the 12 cells
on D3 was unrelated to either LLM rater's (Section 4.7), even though all three
web-verified every tool. What counts as a real, correctly described tool is where the
raters disagreed most.

The two dimensions most closely tied to family, D2 (recency, eta squared 0.69) and D6
(citation quality, 0.65), are the ones that depend most on current information. The three
families whose apps searched the web on their own (Claude, GPT, Grok) scored 1.4 to 2.0 on
D2, and the families that ran without search (Gemini, DeepSeek) and Qwen scored 1.0 to 1.2.
This is consistent with live search driving part of the family effect, but search was not
varied within a family, so the study cannot separate it from the model itself (Section
5.3).

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
study can say about human judgment. Both LLM raters did score their own vendor's family
higher than the other raters did (Section 4.8); removing those scores leaves H4 unchanged.
Two of three raters, the human and `llm-a`, guessed mode above chance, so mode blinding was
partial for them (Section 4.6).

**Answer length.** Reasoning answers are longer, and after removing log length the mode
effect on the total falls by more than half (Section 4.5). As pre-registered, we report
that the mode effect cannot be separated from answer length. We do not claim length causes
it, and we do not claim it does not.

**Small cells.** Five replicates per cell detect a strong mode effect reliably but miss a
moderate one about half the time, and percentile bootstrap intervals at this size can be
too narrow. Under equal effects, 15% of simulated studies still show "mode > model". We
report permutation p-values beside every interval.

**Single author.** No second author checked the analysis. The plan was registered before
collection, the author did not score, and all data and code are released so anyone can
re-run it.

## 6. Conclusion

We crossed six model families with two reasoning modes on one demanding, constrained design
task, collected five answers per cell in the vendors' own chat apps, and had three blind
raters score all 60. On the pre-registered test, family explained far more of the variance
in answer quality than mode did (delta omega squared -0.527, 95% CI [-0.666, -0.417]).
Reasoning helped on average, by 1.37 points of 18, but the gain came mostly from one family
and from switching reasoning off rather than turning it down, and it halved once answer
length was taken into account. On this task, choosing the model matters more than choosing
how hard it thinks. Mode should still be reported, because what it does differs from one
model to the next. The data, code and every departure from the plan are released.
