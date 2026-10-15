# 4. Results (skeleton)

Written 2026-10-14, before any scoring. Every number below has a source file and column, so
the section can be filled in once the analysis runs, without choosing what to report after
seeing the data. Report every row, including the ones that fail. Keep the order: the
pre-registration ranks H4 first.

Source files after Phase 4 of the runbook:

| File | Command | What it holds |
|---|---|---|
| `results/agreement.csv` | `modegrid agreement ... --out` | Krippendorff's alpha per dimension and for the total |
| `results/variance_table.md` and `.csv` | `modegrid analyze --agreement results/agreement.csv` | Decomposition, delta, CIs, p-values, verdicts, hypothesis table |
| `results/family_mode_effects.csv` | same | Reasoning minus fast per family and dimension |
| `results/cell_means.csv`, `results/figure1.pdf` | `modegrid cells --figure figure1.pdf` | Figure 1 and its table |
| `results/<rater>/variance_table.md` | robustness check 3 | The same analysis on each rater's own scores |
| `results/fast-off/`, `results/fast-lowest/` | robustness check 4 | True-off and lowest-available families |
| `results/blinding_check.csv` | `modegrid blinding-check ... --out` | Family and mode guess accuracy per rater, with p-values |
| `results/cell_rank_agreement.csv` | `modegrid rank-agreement` | Kendall's tau-b and W on cell rankings (exploratory) |
| `results/blinding_audit.csv` | `modegrid blinding-audit` | Pre-scoring audit (already done) |
| `results/own_vendor.csv` | `modegrid own-vendor` | Each LLM rater on its own vendor's family |
| `results/report.md` | `modegrid report` | All of the above, in this section's order (added 2026-10-15, before scoring) |

## 4.1 Data and reliability

[60 of 60 planned answers were scored by all three raters.] Refusals per family and mode: the
`n_all_zero` column of `results/cell_means.csv` counts answers whose consensus is 0 on all
nine dimensions, which the refusal rule gives an outright refusal. Check any non-zero count
against the raters' notes before calling it a refusal. [Expected 0.]

Inter-rater reliability (Table 3, from `results/agreement.csv`): ordinal alpha per dimension
and interval alpha on the total. Name every dimension below 0.667, which makes its test
exploratory. State whether the total clears 0.667 (H4 stays confirmatory) and whether it
clears 0.800 (firm, otherwise "tentative").

[One sentence each: human vs llm-a and human vs llm-b exact agreement, from the two
pairwise agreement files.]

## 4.2 Confirmatory test (H4)

From the "total" row of `results/variance_table.csv`:

- delta omega squared `delta_omega2` with 95% CI [`ci_low`, `ci_high`]
- omega squared for mode `omega2_mode` and for family `omega2_family`
- reasoning minus fast `mode_effect` with 95% CI [`mode_effect_ci_low`, `mode_effect_ci_high`],
  in points out of 18
- permutation p-values `p_mode` and `p_family`, and any disagreement with the CI
- omega squared for the interaction `omega2_interaction`, and whether it exceeds both main
  effects
- the verdict and the H4 status from the hypothesis table, word for word.

Then the power caveat: under equal effects 15% of simulated studies show "mode > model".

## 4.3 Secondary tests (H1 to H3) and the other dimensions

Table 4: the full `variance_table.md` decomposition, all nine dimensions plus the total.

For H1 (D1), H2 (D9) and H3 (D3): verdict, delta with CI, direction with CI, status, and
the multiplicity caveat. For H3, say which of the two pre-stated outcomes occurred: model >
mode (supports H3), mode > model with reasoning lower (supports the hallucination account),
or neither.

The random-effects variance components (`vc_*` columns, and the exploratory section of
`variance_table.md`) go in the appendix, labelled exploratory, as pre-registered.

For D2, D4 to D8: the verdict only, as descriptive. Name any "no variance" or
"uninformative" dimension, which is a finding about the rubric.

## 4.4 Where mode mattered: per-family differences

Figure 1 (`results/figure1.pdf`): cell means, fast vs reasoning, one line per family, for
the total, D1, D9 and D3.

From `results/family_mode_effects.csv`: for the total, each family's reasoning minus fast.
Say how many of the six families moved in the same direction. If the interaction exceeded
both main effects, interpret the per-family differences here, as the pre-registration
requires.

## 4.5 Robustness

1. Ranks: `rank_delta_omega2` per dimension. Same verdict or not.
2. Length: `length_adj_delta_omega2`. If the mode effect shrinks, report that it is not
   separable from answer length, not that length causes it.
3. Per rater: H4 verdict on each rater's own scores, from `results/<rater>/`.
4. Fast-mode floor: delta and direction in the true-off group and the lowest-available
   group. If H1, H2 or H4 holds only in the true-off group, say the claim holds for
   reasoning off vs on, not minimised vs on.

## 4.6 Blinding

From `modegrid blinding-check`: for each rater, the share of answers they guessed, their
accuracy on family (chance 1/6) and mode (chance 1/2), and the one-sided binomial p-value.
Apply the pre-registered rule: name any rater who beat chance on mode, re-run H1 to H4 on
each rater's scores, and if all three beat chance, label a supported H4 "tentative, mode
blinding failed". Family guesses above chance are expected (Appendix D2) and change no
status.

## 4.7 Rubric portability (exploratory, for LA-P5)

From `results/cell_rank_agreement.csv`: Kendall's W across the three raters on the 12 cell
means for the total, and tau-b for each pair. Name the dimensions with no variance, which a
benchmark cannot use.

## 4.8 Own-vendor scores

From `results/own_vendor.csv`, for `llm-a` on Claude answers and `llm-b` on GPT answers:
the gap to the other two raters on the same answers (`own_gap`), the same gap on the other
five families (`baseline_gap`), and their difference (`self_preference`) with its 95% CI,
for the total and each dimension. A positive self-preference with a CI above zero means the
rater scored its own vendor higher than it scored everyone else, relative to the other
raters. Descriptive: no hypothesis rests on it. If it is large, an exploratory check, not
pre-registered and labelled as such, can report H4 with that rater's own-vendor scores
replaced by the mean of the other two.
