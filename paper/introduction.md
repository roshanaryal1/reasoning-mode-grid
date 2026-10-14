# 1. Introduction (draft)

Draft written 2026-10-14, before any scoring. The last paragraph has placeholders for the
results. Write it, and the title, to match the result whichever way it goes, as the outline
says.

Leaderboards rank models. People who use these models choose more than a model. In every
major chat app they also choose how hard the model thinks: Instant or High in ChatGPT,
Effort Low or High in Claude, Fast or Expert in Grok, DeepThink on or off in DeepSeek. The
same weights can then behave like a different system. If the mode switch changes answer
quality as much as switching vendor does, a comparison that names the model but not the
mode is confounded, and a user who picks a vendor carefully but leaves the mode on its
default may be optimising the smaller factor.

Prior work on reasoning modes mostly measures accuracy on tasks with an answer key, such as
math, code and science questions, and usually within one model family or one training
recipe (Section 2). Real requests are often open-ended and constrained: there is no single
right answer, but there are hard limits a good answer must respect. For these tasks we do
not know how much of the variation in quality comes from the mode and how much from the
model.

We test this directly. We hold one demanding prompt fixed: design a fully local, always-on
autonomous AI workstation for one stated machine, a Mac mini with 32 GB of unified memory.
We cross six model families with two modes, fast and reasoning, and collect five answers
per cell in each vendor's own web app, for 60 answers. Three blind raters, one human and
two LLMs from different vendors, score every answer on a nine-dimension rubric with
mechanical checks for the memory budget and internal consistency and web verification for
every named tool and model. A pre-registered two-way variance decomposition then asks, per
dimension, whether mode explains more of the variance than family does, and whether
reasoning scores higher.

The question came from an observation. LA-P1 [Aryal, 2026] captured one model family in
three modes and saw answers that looked different in ways that mattered, but with one answer
per mode and no controls its adjudicated scores could not separate a mode effect from
run-to-run noise, and did not show a reasoning advantage. This paper is the controlled test.

Our contributions are:

1. A crossed 6 x 2 model-by-mode design with five replicates per cell, run in the chat apps
   people use, with an API check that each mode switch changes how much the model reasons.
2. A pre-registered analysis (OSF, frozen before the first capture) that decomposes
   answer-quality variance into family, mode, interaction and residual per rubric
   dimension, using bias-corrected omega squared, bootstrap intervals and permutation tests,
   with one confirmatory hypothesis.
3. Evidence on rubric portability across a grid the rubric's authors never saw:
   inter-rater reliability per dimension and agreement between raters on how the 12 cells
   rank, which a follow-up benchmark (LA-P5) needs.
4. An open harness, `modegrid`, that covers planning, capture, blinding, scoring and
   analysis, and the full data: 60 verbatim answers, blinded packets' build rules, all rater
   sheets and every departure from the plan.

[Results paragraph. One sentence each: the H4 verdict with delta omega squared and its
95% CI, the direction of the mode effect with its CI, the dimensions where mode or family
dominated, and the rubric-portability result. Then one sentence on the implication for
evaluation practice.]
