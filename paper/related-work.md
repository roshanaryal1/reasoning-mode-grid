# 2. Related work (draft)

Draft written 2026-10-14, before any scoring. Sources and the checks behind each citation
are in `docs/related-work.md`. Every reference was re-checked on 2026-10-26 against its
arXiv, Crossref or DataCite record; the list is in the References section.

## Thinking modes in hybrid models

Hybrid models expose reasoning as a switch on one set of weights. Work on these models asks
how to switch and whether the switch is clean. HRBench compares prompt-based, routing and
speculative switching strategies on six models and five math, science and code benchmarks
[Ning et al., 2026]. Several studies show that the "off" mode is not fully off. S. Wang et al. [2026a] find only partial separation between think and no-think modes, with reasoning
behaviour leaking into no-think answers. Liu and Honavar [2026] attribute 42% to 79% of
no-think gains to leaked thinking behaviour, and Path-Lock Expert separates the two modes
at the architecture level to stop it [S. Wang et al., 2026b]. Thinking persists even under
explicit instructions not to think, more so as the answer space opens [Lei et al., 2026]. These results bear on our design in two ways. A fast mode may still reason on an
open-ended task, so we measure reasoning tokens for each mode through the API (Section
3.4). And three of our six families offer only a lowest setting, not an off switch, which
a pre-registered robustness check separates out.

The closest design to ours compares instant and thinking modes on the same checkpoints
across five frontier vendors, for moral judgments [Madur, 2026]. It finds that verdict agreement barely changes with thinking. It also
notes, as we do, that some vendors' lowest setting is not a clean off. That study works on
verdicts with a small answer space, through the API, and
measures agreement between models without separate raters. Ours works on an
open-ended design task with hard constraints, in the chat apps people use, with a human
rater among three blind raters.

## Model choice versus other factors

A growing line of work asks how much of the variation in LLM output comes from the model
and how much from something around it. On creative tasks, a variance decomposition across
12 models and 10 prompts finds that model choice explains about as much variance in
originality as the prompt, and more in fluency [Haase et al., 2026]. For coding agents, the
harness that runs the model can explain more variance than the model and can reverse model
rankings [Zhang et al., 2026]. Test-time compute work shows that extra inference compute,
spent well, can beat a larger model on math [Snell et al., 2025]. We apply the same
variance-decomposition logic to a factor none of these studies varies: the reasoning mode
of a fixed model, crossed with model identity, on a constrained task.

## Reasoning and factuality

Reasoning does not only help. Reasoning-oriented RL fine-tuning raises hallucination rates
[Li and Ng, 2025], reasoning LLMs hallucinate more than non-reasoning models on long-form
factuality [Chen et al., 2026], and thinking can turn a correct direct answer into a wrong
one [K. Wang et al., 2026]. On closed-book knowledge tasks, more test-time computation
does not reliably raise accuracy and often adds hallucinations [Zhao et al., 2026]. Reasoning-model errors on constrained problems often come
from inventing problem features that were never given [Heyman and Zylberberg, 2025]. These
works compare differently trained models or study training methods, not one model with
reasoning switched on and off at inference time. They motivate a competing prediction for
our hypothesis H3: if the effect carries over, reasoning mode would lower tool factuality
(D3) rather than leave it unchanged.

## Run-to-run variance and LLM raters

Repeated runs of one model with fixed settings give different outputs. Sources include
hosted-service non-determinism at temperature 0 [Atil et al., 2025], floating-point
non-associativity that shifts reasoning-model accuracy by up to 9% [Yuan et al., 2025], and
early divergence in agent trajectories that moves single-run scores by 2 to 6 points
[Bjarnason et al., 2026]. Across 12 models, 10 reasoning strategies and 30 trials
each, about three-quarters of score variance comes from benchmark, system and item
structure, with a residual that single runs absorb [Potamitis et al., 2025]. We therefore collect five replicates per cell and treat
replicate variance as the residual. LLM judges score the same input differently across
models and settings [Lau, 2026], and closed-book raters flag real tools released after
their training cutoff as fabricated [Aryal, in preparation]. We use three blind raters, one of them human,
take the median, require web verification for tool and model factuality, and report each
LLM rater's scores for its own vendor's family separately.

## LLMs as systems architects

LLMs are increasingly asked to design systems. On networked systems, Sahu et al. [2026]
find that LLMs cannot yet do architectural reasoning reliably and that how the LLM is
involved changes the outcome a lot. LA-P1 [Aryal, 2026] introduced the task and rubric we
reuse, and captured one family (DeepSeek) in three modes, one answer each, with no
controls. Its adjudicated totals did not show a reasoning advantage. That pilot cannot separate a mode effect from run-to-run noise. This paper is the
controlled test.

## What is new here

To our knowledge, no prior study crosses reasoning mode with model identity and decomposes
answer-quality variance on an open-ended, constrained design task. We add a pre-registered
6 x 2 design with replicates, a per-dimension decomposition with bias-corrected effect
sizes, blinded scoring by human and LLM raters with web verification, and a reusable
harness. The search was last repeated on 2026-10-26.
