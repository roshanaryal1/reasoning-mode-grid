# Analysis in plain language

## The question in numbers

Every answer gets a score. Scores differ for four reasons:

1. **Family.** Claude answers differently from Qwen.
2. **Mode.** Reasoning on answers differently from reasoning off.
3. **Interaction.** Reasoning helps some families more than others.
4. **Residual.** Run the same model in the same mode twice and you get different answers.

The analysis splits the total spread of scores into those four shares, one dimension at
a time. The claim "mode beats model" means share 2 is bigger than share 1.

## Why omega squared

The simple share is eta squared: the fraction of total spread each source explains.
It has a bias. Family has six levels and mode has two. Six random numbers spread out more
than two random numbers, even with no real effect. So eta squared would favour family by
chance. Omega squared subtracts what noise alone would produce for each source, which
makes the comparison fair.

## Why a bootstrap over replicates

The only randomness we measured directly is replicate noise: the same cell run five
times. The bootstrap redraws the five replicates in each cell, with replacement, 5,000
times, and recomputes delta each time. The middle 95% of those values is the CI.

Families are not resampled. The result is about these six families. The paper should not
claim it holds for every model ever released.

## Why permutation p-values

Scores are 0, 1 or 2. Classical F-tests assume smooth, normal data. A permutation test
shuffles the mode labels within each family thousands of times and asks how often a
shuffle produces a mode effect as large as the real one. No distribution assumption.

## The robustness checks

1. **Ranks.** Re-run on ranked scores. Guards against the 0/1/2 scale doing odd things.
2. **Length.** Reasoning modes write more. Remove the linear effect of log answer length
   in words and re-run. Length is itself affected by mode, so if the mode effect shrinks,
   the honest finding is that it is not separable from length, not that length caused it.
3. **Per rater.** Re-run on each rater's raw scores. A result that exists only in the
   median of three is fragile.
4. **Split by fast-mode floor.** Re-run on the true-off families and on the
   lowest-available families separately.

## Reading the output

`results/variance_table.md` has one row per dimension:

| Column | Meaning |
|---|---|
| eta2 family, mode, FxM, resid | Plain shares of the spread. They sum to 1 |
| omega2 FxM | Bias-corrected share of the family x mode interaction |
| delta omega2 | The primary statistic. Positive means mode explains more |
| 95% CI | Bootstrap interval for delta |
| reasoning - fast, 95% CI | Signed mode effect: positive means reasoning scored higher |
| p mode, p family | Permutation p-values (mode: shuffled within each family) |
| Verdict | mode > model, model > mode, inconclusive, uninformative (low variance), or no variance |

The hypotheses table below it marks H4 confirmatory and H1-H3 secondary. "Supported" needs
the predicted verdict, reasoning > fast where predicted, and rater alpha at or above 0.667
(pass `--agreement results/agreement.csv`). `results/family_mode_effects.csv` lists each
family's reasoning-minus-fast difference per dimension.

A dimension with "no variance" means every answer got the same score. That is a finding
about the rubric, not about mode or model. Report it.

## Reproducing

All randomness is seeded. Same data, same command, same numbers:

```bash
modegrid analyze --seed 20261001 --boot 5000 --perm 5000
```
