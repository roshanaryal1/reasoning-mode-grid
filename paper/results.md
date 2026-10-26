# 4. Results (draft)

Skeleton written 2026-10-14, before any scoring. Filled 2026-10-26 from `results/report.md`,
in the skeleton's order. Every number has a source file and column, listed below. Every row
is reported, including the ones that fail. The pre-registration ranks H4 first.

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

All 60 planned answers were scored by all three raters (the human rater, `llm-a` and
`llm-b`), and all 60 have a consensus score. No answer has a consensus of 0 on all nine
dimensions (`n_all_zero` is 0 in every cell of `results/cell_means.csv`), so no answer was
treated as an outright refusal.

**Table 3.** Inter-rater reliability, three raters: Krippendorff's alpha, ordinal per
dimension and interval on the total.

| Dimension | alpha | Status |
|---|---|---|
| D1 hardware-constraint | 0.574 | below 0.667 |
| D2 recency | 0.283 | below 0.667 |
| D3 tool-factuality | 0.249 | below 0.667 |
| D4 model-factuality | 0.630 | below 0.667 |
| D5 benchmark-factuality | 0.599 | below 0.667 |
| D6 citation-quality | 0.539 | below 0.667 |
| D7 actionability | 0.858 | ok |
| D8 security-model | 0.862 | ok |
| D9 internal-consistency | 0.285 | below 0.667 |
| Total | 0.698 | ok |

Seven of nine dimensions fall below the 0.667 bar: D1, D2, D3, D4, D5, D6 and D9. Their
tests are exploratory. This includes all three secondary hypotheses (H1 on D1, H2 on D9,
H3 on D3). Only D7 and D8 clear the bar. The total clears 0.667 (alpha 0.698), so H4 stays
confirmatory. It does not clear 0.800, so any supported result on the total would be
tentative.

Pairwise, the human rater and `llm-a` have a mean exact agreement of 0.72 over D1 to D9
(range 0.18 to 0.93 across dimensions). The human rater and `llm-b` have 0.71 (range 0.45
to 0.95).

## 4.2 Confirmatory test (H4)

On the total score (Table 4, "total" row):

- delta omega squared (mode minus family) is -0.527, 95% CI [-0.666, -0.417];
- omega squared is 0.050 for mode and 0.577 for family;
- reasoning scores 1.37 points higher than fast out of 18, 95% CI [0.77, 1.93];
- permutation p is 0.007 for mode, in agreement with the reasoning-minus-fast interval,
  and below 0.001 for family (no separate interval is computed for the family effect);
- omega squared for the family x mode interaction is 0.184. It exceeds the mode effect
  (0.050) but not the family effect (0.577), so it does not exceed both main effects and
  the "average effect only" label does not apply.

Verdict: **model > mode**. H4 status: **no**. H4 predicted mode > model with reasoning
higher than fast. Reasoning did score higher than fast, with a CI above zero, but family
explained far more of the variance in the total than mode did, and the CI on delta lies
wholly below zero.

Power caveat: under equal mode and family effects, 15% of simulated studies still show
"mode > model" (Section 3.7). The simulation models a single 0 to 2 dimension, not the
nine-dimension total, so it is a proxy for H4 and says nothing about how often the
opposite verdict appears by chance; it is reported as pre-registered.

## 4.3 Secondary tests (H1 to H3) and the other dimensions

**Table 4.** Variance decomposition, all nine dimensions and the total
(`results/variance_table.md`). Delta is omega squared for mode minus omega squared for
family, with a 95% bootstrap CI over replicates.

| Dim | eta2 family | eta2 mode | eta2 FxM | eta2 resid | omega2 FxM | delta omega2 | 95% CI | reasoning - fast | 95% CI | p mode | p family | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 | 0.206 | 0.000 | 0.147 | 0.647 | 0.079 | -0.150 | [-0.386, -0.045] | 0.000 | [-0.200, 0.200] | 1.000 | 0.035 | model > mode |
| D2 | 0.692 | 0.004 | 0.063 | 0.241 | 0.037 | -0.664 | [-0.840, -0.547] | 0.067 | [-0.067, 0.200] | 0.662 | 0.000 | model > mode |
| D3 | 0.524 | 0.011 | 0.084 | 0.381 | 0.044 | -0.477 | [-0.710, -0.321] | -0.100 | [-0.233, 0.033] | 0.450 | 0.000 | model > mode |
| D4 | 0.415 | 0.029 | 0.161 | 0.395 | 0.119 | -0.350 | [-0.637, -0.175] | 0.167 | [0.000, 0.300] | 0.187 | 0.000 | model > mode |
| D5 | 0.582 | 0.039 | 0.125 | 0.254 | 0.098 | -0.519 | [-0.656, -0.440] | 0.333 | [0.133, 0.533] | 0.041 | 0.000 | model > mode |
| D6 | 0.654 | 0.000 | 0.013 | 0.333 | -0.022 | -0.622 | [-0.805, -0.494] | 0.000 | [-0.133, 0.133] | 1.000 | 0.000 | model > mode |
| D7 | 0.187 | 0.058 | 0.213 | 0.542 | 0.155 | -0.083 | [-0.300, 0.008] | 0.200 | [0.033, 0.333] | 0.096 | 0.045 | inconclusive |
| D8 | 0.403 | 0.074 | 0.134 | 0.389 | 0.093 | -0.294 | [-0.485, -0.186] | 0.267 | [0.100, 0.400] | 0.020 | 0.000 | model > mode |
| D9 | 0.316 | 0.066 | 0.226 | 0.392 | 0.184 | -0.216 | [-0.409, -0.095] | 0.433 | [0.167, 0.700] | 0.034 | 0.000 | model > mode |
| total | 0.595 | 0.053 | 0.200 | 0.152 | 0.184 | -0.527 | [-0.666, -0.417] | 1.367 | [0.767, 1.933] | 0.007 | 0.000 | model > mode |

p = 0.000 means p < 0.001 at 5,000 permutations.

All three secondary tests are exploratory, because their dimensions fall below the alpha
bar (Table 3). They are reported uncorrected for multiplicity, as pre-registered, and
cannot by themselves carry a claim.

- **H1** (D1, predicted mode > model and reasoning > fast): model > mode, delta -0.150
  [-0.386, -0.045]. Reasoning minus fast is 0.00 [-0.20, 0.20]. The prediction fails in
  direction. Exploratory (alpha 0.57).
- **H2** (D9, predicted mode > model and reasoning > fast): model > mode, delta -0.216
  [-0.409, -0.095]. Reasoning scores higher than fast, 0.43 [0.17, 0.70], but family still
  explains more variance than mode. The prediction fails in direction. Exploratory
  (alpha 0.29).
- **H3** (D3, predicted model > mode): model > mode, delta -0.477 [-0.710, -0.321].
  Reasoning minus fast is -0.10 [-0.23, 0.03]. Of the pre-stated outcomes, model > mode
  occurred, the direction H3 predicted; the competing hallucination account (mode > model
  with reasoning lower) did not occur. D3's alpha is 0.25, below the bar, so under the
  pre-registered rule this pattern can neither confirm nor refute H3.

For each of H1 to H4 the permutation p for mode agrees with its interval.

Other dimensions, descriptive: D2, D4, D5, D6 and D8 are model > mode. D7 is inconclusive
(delta -0.083 [-0.300, 0.008]). On D7 the interaction explains more than both main effects
(omega squared 0.155, against 0.129 for family and 0.046 for mode), so as pre-registered
its main-effect comparison is labelled "average effect only; interaction exceeds both main
effects" and the per-family differences are the better summary: reasoning minus fast was
+0.8 for GPT, +0.4 for Claude and Qwen, 0.0 for Gemini and Grok, and -0.4 for DeepSeek. D7
also shows a disagreement the pre-registration asks us to report: its reasoning-minus-fast
interval is above zero ([0.033, 0.333]) while the mode permutation p is 0.096. The
permutation tests the strict null that mode changes nothing in any family, which is a
different question from the average effect, so we report both and resolve neither. No dimension had no variance or was uninformative in the
full design. Delta is negative on every dimension.

The random-effects variance components are in Appendix B, labelled exploratory.

## 4.4 Where mode mattered: per-family differences

Figure 1 (`results/figure1.pdf`) shows cell means, fast vs reasoning, one line per family,
for the total, D1, D9 and D3.

**Table 5.** Total score (out of 18) by family and mode, consensus means over five
replicates (`results/family_mode_effects.csv`).

| Family | Fast | Reasoning | Reasoning - fast |
|---|---|---|---|
| Claude | 13.80 | 15.60 | +1.80 |
| DeepSeek | 11.80 | 11.20 | -0.60 |
| Gemini | 9.40 | 9.40 | 0.00 |
| GPT | 15.00 | 16.40 | +1.40 |
| Grok | 13.60 | 12.40 | -1.20 |
| Qwen | 6.80 | 13.60 | +6.80 |

Three of six families (Claude, GPT, Qwen) moved in the same direction as the average
(+1.37). Gemini did not move, and DeepSeek and Grok scored lower in reasoning. Qwen's +6.80
is the largest single difference; without Qwen the mean of the other five is +0.28. The
interaction did not exceed both main effects (Section 4.2), so the pre-registration does
not require interpreting these differences. They are reported as descriptive.

## 4.5 Robustness

**Table 6.** Robustness checks 1 and 2: delta omega squared on raw scores and on ranks, and
delta, omega squared for mode and reasoning minus fast after removing the linear effect of
log answer length (`results/variance_table.md`, sensitivity checks).

| Dim | delta (raw) | delta (ranks) | Same sign | delta (length-adj.) | omega2 mode (raw) | omega2 mode (length-adj.) | Reasoning - fast (raw) | Reasoning - fast (length-adj.) |
|---|---|---|---|---|---|---|---|---|
| D1 | -0.150 | -0.145 | yes | -0.120 | -0.013 | -0.004 | 0.000 | -0.093 |
| D2 | -0.664 | -0.664 | yes | -0.618 | -0.001 | 0.012 | 0.067 | 0.128 |
| D3 | -0.477 | -0.477 | yes | -0.432 | 0.003 | -0.008 | -0.100 | 0.011 |
| D4 | -0.350 | -0.341 | yes | -0.346 | 0.021 | 0.022 | 0.167 | 0.171 |
| D5 | -0.519 | -0.462 | yes | -0.575 | 0.034 | 0.013 | 0.333 | 0.224 |
| D6 | -0.622 | -0.645 | yes | -0.575 | -0.007 | 0.018 | 0.000 | -0.153 |
| D7 | -0.083 | -0.079 | yes | -0.124 | 0.046 | -0.014 | 0.200 | 0.001 |
| D8 | -0.294 | -0.294 | yes | -0.180 | 0.065 | -0.002 | 0.267 | -0.080 |
| D9 | -0.216 | -0.219 | yes | -0.232 | 0.057 | 0.051 | 0.433 | 0.412 |
| total | -0.527 | -0.570 | yes | -0.655 | 0.050 | 0.008 | 1.367 | 0.621 |

1. **Ranks.** Delta on ranks has the same sign as on raw scores on every dimension and the
   total. The total moves from -0.527 to -0.570. These are point estimates; the
   sensitivity checks have no bootstrap intervals, so they show that the direction holds,
   not a verdict.
2. **Length.** After removing log answer length, the mode effect on the total falls by more
   than half: reasoning minus fast drops from 1.37 to 0.62 points, and omega squared for mode
   from 0.050 to 0.008. The adjusted delta stays negative (-0.655, a point estimate). As pre-registered, we
   report that the mode effect is not separable from answer length, not that length causes
   it. Reasoning answers are longer, and longer answers score higher; this design cannot
   tell the two apart. The effect also shrinks on D3, D5, D7 and D8, and almost vanishes on
   D7 and D8. On D9 it barely changes (0.43 to 0.41), the largest positive estimate left
   after adjustment; D2, D4 and D5 also stay positive (0.13, 0.17 and 0.22). These adjusted
   values are point estimates without intervals. The first version of this check judged shrinking on
   delta rather than on the mode effect; the Deviations table records the correction
   (Appendix D).
3. **Per rater.** Each rater's own scores give the same H4 verdict as the consensus.

   | Rater | H1 (D1) | H2 (D9) | H3 (D3) | H4 (total) |
   |---|---|---|---|---|
   | Human | model > mode, -0.10 [-0.30, 0.10] | inconclusive, 0.37 [0.13, 0.60] | model > mode, 0.17 [0.10, 0.23] | model > mode, 1.57 [1.03, 2.10] |
   | `llm-a` | model > mode, 0.00 [-0.20, 0.20] | model > mode, 0.30 [0.10, 0.53] | model > mode, -0.13 [-0.30, 0.03] | model > mode, 1.23 [0.63, 1.80] |
   | `llm-b` | model > mode, 0.07 [-0.10, 0.23] | model > mode, 0.20 [-0.13, 0.53] | model > mode, -0.07 [-0.23, 0.10] | model > mode, 1.20 [0.53, 1.87] |

   Cells give the verdict, then reasoning minus fast with its 95% CI. All three raters give
   model > mode on H4, with reasoning above fast and a CI above zero. On H2 the human
   rater's verdict is inconclusive where the other two give model > mode. On H3 the human
   rater scored reasoning higher than fast on D3 (0.17 [0.10, 0.23]), where the two LLM
   raters show no clear difference.
4. **Fast-mode floor.** The same analysis on the true-off families (GPT, Qwen, DeepSeek)
   and the lowest-available families (Claude, Gemini, Grok), 30 runs each, descriptive.

   | Group | Measure | delta (95% CI) | Reasoning - fast (95% CI) | Verdict |
   |---|---|---|---|---|
   | True-off | total | -0.348 [-0.554, -0.161] | 2.53 [1.67, 3.40] | model > mode |
   | True-off | D1 | -0.167 [-0.425, 0.018] | -0.07 [-0.40, 0.27] | inconclusive |
   | True-off | D9 | 0.004 [-0.291, 0.283] | 0.73 [0.40, 1.07] | inconclusive |
   | Lowest-available | total | -0.736 [-0.853, -0.617] | 0.20 [-0.60, 1.00] | model > mode |
   | Lowest-available | D1 | -0.163 [-0.538, 0.066] | 0.07 [-0.13, 0.27] | inconclusive |
   | Lowest-available | D9 | -0.357 [-0.612, -0.156] | 0.13 [-0.27, 0.53] | model > mode |

   H1, H2 and H4 hold in neither group, so the pre-registered true-off rule is not
   triggered. Both groups give model > mode on the total. The mode effect on the total is
   larger where fast mode turns reasoning off (+2.53, CI above zero) than where it only
   lowers it (+0.20, CI includes zero), and delta is closer to zero in the true-off group.
   The reasoning-over-fast gain in the full design comes mainly from the true-off families,
   Qwen above all (Table 5).

## 4.6 Blinding

**Table 7.** Blinding check: share of answers guessed, guess accuracy against chance, and
the exact one-sided binomial p-value (`results/blinding_check.csv`).

| Rater | Guess | Guessed | Accuracy | Chance | p |
|---|---|---|---|---|---|
| Human | family | 60 of 60 | 0.15 | 0.17 | 0.688 |
| Human | mode | 60 of 60 | 0.70 | 0.50 | 0.001 |
| `llm-a` | family | 60 of 60 | 0.75 | 0.17 | < 0.001 |
| `llm-a` | mode | 60 of 60 | 0.68 | 0.50 | 0.003 |
| `llm-b` | family | 60 of 60 | 0.20 | 0.17 | 0.292 |
| `llm-b` | mode | 60 of 60 | 0.60 | 0.50 | 0.078 |

Two raters beat chance on mode: the human rater (0.70, p = 0.001) and `llm-a` (0.68,
p = 0.003). `llm-b` did not (0.60, p = 0.078). As pre-registered, H1 to H4 were re-run on
each rater's scores (Section 4.5, check 3). `llm-b`, the rater who did not beat chance,
reaches the same H4 verdict as the consensus (model > mode). Not all three raters beat
chance, so the "mode blinding failed" label does not apply. H4 is not supported in any
case.

On family, `llm-a` guessed right on 75% of answers (chance 17%, p < 0.001). The human rater
(15%) and `llm-b` (20%) did not beat chance. Family leaking through recommended model names
is expected (Appendix D2) and changes no hypothesis's status. It does mean that `llm-a`
correctly identified the family of most answers it scored. Section 4.8 reports how each
LLM rater scored its own vendor's answers.

One leak was found after scoring. Three packets, all Claude reasoning answers, still
contained the author's account name or home city, which the claude.ai app had passed to
the model although memory was off; the pre-scoring audit had no probe for it. All three
raters guessed "reasoning" for all three packets, and `llm-a` guessed Claude for all three
(the human rater and `llm-b` for one each). Three of 60 answers cannot move the rates in
Table 7 by more than 0.05; no scores were changed (Appendix D).

## 4.7 Rubric portability (exploratory, for LA-P5)

**Table 8.** Agreement of the three raters on the ranking of the 12 cell means: Kendall's W
across raters and Kendall's tau-b for each pair (`results/cell_rank_agreement.csv`).

| Measure | Kendall's W | Human ~ `llm-a` | Human ~ `llm-b` | `llm-a` ~ `llm-b` |
|---|---|---|---|---|
| D1 | 0.891 | 0.87 | 0.67 | 0.75 |
| D2 | 0.675 | 0.72 | 0.39 | 0.19 |
| D3 | 0.544 | -0.05 | 0.10 | 0.61 |
| D4 | 0.685 | 0.48 | 0.34 | 0.63 |
| D5 | 0.842 | 0.51 | 0.65 | 0.80 |
| D6 | 0.875 | 0.93 | 0.62 | 0.68 |
| D7 | 0.948 | 0.83 | 0.90 | 0.94 |
| D8 | 0.951 | 0.86 | 0.79 | 0.95 |
| D9 | 0.870 | 0.63 | 0.61 | 0.85 |
| total | 0.955 | 0.88 | 0.81 | 0.80 |

The raters rank the 12 cells almost the same way on the total (W = 0.955), even though
their per-answer agreement on several dimensions is low (Table 3). D3 is the weakest: the
human rater's ranking is unrelated to either LLM rater's (tau-b -0.05 and 0.10), while the
two LLM raters agree moderately (0.61). D2 and D4 are also low. No dimension had no
variance, so none is unusable as a benchmark dimension on that ground.

## 4.8 Own-vendor scores

**Table 9.** Each LLM rater on its own vendor's family (`results/own_vendor.csv`). Own gap
is the rater's mean score minus the mean of the other two raters on its own vendor's
answers. Baseline gap is the same on the other five families. Self-preference is own gap
minus baseline gap, with a 95% CI. Descriptive: no hypothesis rests on it.

| Rater | Family | Measure | Own gap | Baseline gap | Self-preference (95% CI) |
|---|---|---|---|---|---|
| `llm-a` | Claude | total | 0.30 | -0.81 | 1.11 [0.52, 1.71] |
| `llm-a` | Claude | D1 | -0.05 | 0.00 | -0.05 [-0.18, 0.06] |
| `llm-a` | Claude | D2 | 0.35 | -0.09 | 0.44 [0.25, 0.62] |
| `llm-a` | Claude | D3 | 0.05 | -0.34 | 0.39 [0.10, 0.66] |
| `llm-a` | Claude | D4 | 0.00 | -0.02 | 0.02 [-0.13, 0.18] |
| `llm-a` | Claude | D5 | 0.05 | 0.26 | -0.21 [-0.63, 0.18] |
| `llm-a` | Claude | D6 | 0.25 | 0.00 | 0.25 [0.01, 0.47] |
| `llm-a` | Claude | D7 | 0.05 | 0.04 | 0.01 [-0.19, 0.26] |
| `llm-a` | Claude | D8 | 0.00 | -0.03 | 0.03 [-0.03, 0.09] |
| `llm-a` | Claude | D9 | -0.40 | -0.63 | 0.23 [-0.18, 0.67] |
| `llm-b` | GPT | total | 0.10 | -1.40 | 1.50 [0.70, 2.34] |
| `llm-b` | GPT | D1 | 0.10 | -0.15 | 0.25 [0.01, 0.51] |
| `llm-b` | GPT | D2 | 0.05 | -0.33 | 0.38 [0.05, 0.69] |
| `llm-b` | GPT | D3 | 0.15 | -0.12 | 0.27 [0.06, 0.51] |
| `llm-b` | GPT | D4 | -0.10 | -0.12 | 0.02 [-0.23, 0.22] |
| `llm-b` | GPT | D5 | 0.00 | -0.27 | 0.27 [0.10, 0.46] |
| `llm-b` | GPT | D6 | -0.15 | -0.16 | 0.01 [-0.34, 0.33] |
| `llm-b` | GPT | D7 | -0.10 | -0.02 | -0.08 [-0.29, 0.05] |
| `llm-b` | GPT | D8 | -0.15 | 0.03 | -0.18 [-0.43, 0.05] |
| `llm-b` | GPT | D9 | 0.30 | -0.26 | 0.56 [0.18, 0.99] |

Both LLM raters show self-preference on the total, with a CI above zero: `llm-a` by 1.11
points of 18 on Claude answers and `llm-b` by 1.50 points on GPT answers. Each scores the
other five families lower than the other two raters do, but scores its own vendor's family
about level with them. These self-preference estimates (1.11 and 1.50, own gap minus
baseline gap) are of the same size as the mode effect on the total (+1.37); the direct gaps
on their own vendor's answers are only 0.30 and 0.10. For `llm-a` the preference sits in D2, D3 and D6. For `llm-b` it sits in D1, D2,
D3, D5 and D9. `llm-b`'s overall family guesses did not beat chance (Table 7), but whether
it recognised GPT answers in particular is not tested here.

Because the self-preference is as large as the mode effect, we ran one further check,
exploratory and not pre-registered (Appendix D): H4 with each LLM rater's own-vendor scores
replaced by the mean of the other two raters (`results/own-vendor-replaced/`). The verdict is
unchanged, model > mode: delta -0.506 [-0.646, -0.400], omega squared 0.040 for mode and
0.546 for family, and reasoning minus fast 1.17 [0.58, 1.73]. Self-preference does not drive
the H4 result.
