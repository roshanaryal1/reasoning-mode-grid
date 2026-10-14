# Reasoning Mode Beats Model Identity? A Controlled Model x Mode Grid on a Constrained Design Task

Roshan Aryal, Independent Researcher, Auckland, New Zealand

The question mark stays in the title until the data is in. Change the title to match the
result, whichever way it goes.

Drafts written before scoring (nothing in them depends on scores):
[introduction](introduction.md), [related work](related-work.md), [method](methods.md),
[discussion, limitations only](discussion.md), [appendix](appendix.md). Figure 1 comes from `modegrid cells --figure figure1.pdf`.

## Abstract (write last, 150 words)

Problem. Design. Headline numbers (delta omega2 with CI for the total and for H1 to H3).
One-sentence implication for evaluation practice.

## 1. Introduction (0.75 page)

- Leaderboards compare models. Users also pick a mode, and the same model can behave like
  a different one.
- LA-P1 observed this once (DeepSeek, three modes) with no controls.
- Contribution list: a crossed 6 x 2 design with replicates, a pre-registered variance
  decomposition, a reusable harness, and evidence on rubric portability.

## 2. Related work (0.5 page)

- Test-time compute and reasoning-effort scaling.
- LLM-as-judge reliability and the stale-rater effect (cite LA-P2).
- Prompt sensitivity and evaluation variance across runs.
- Hallucination taxonomies used in LA-P1.

## 3. Method (1 page)

- Task and prompt (from LA-P1, unchanged).
- The grid and the mode registry table (Table 1).
- Capture procedure, blinding, rubric v2, web verification.
- Analysis: decomposition, omega squared, bootstrap, permutation, robustness checks.

## 4. Results (1.25 pages)

- Table 2: variance decomposition per dimension (from `results/variance_table.md`).
- Figure 1: cell means, fast vs reasoning, one line per family, per key dimension.
- Hypotheses H1 to H4, each with verdict and CI.
- Robustness: ranks, length, per rater.
- Inter-rater reliability and blinding-failure rate.

## 5. Discussion (0.5 page)

- What it means for leaderboards: report mode alongside model, or the comparison is
  confounded.
- Mode-sensitive vs mode-stable dimensions and why.
- Limits: one prompt, six families, vendor modes are not identical controls.

## 6. Conclusion (0.25 page)

## Appendix

- A: full mode registry with doc links and dates.
- B: per-cell score tables.
- C: pilot data and why it is excluded.
- D: deviations from the pre-registration.
- E: data and code availability (Zenodo DOI, GitHub tag).
