# Power: why 6 families and 5 replicates

Produced with `modegrid power` (200 simulated studies per row, seeded). The simulation
draws scores from a latent model: a family effect (standard deviation `family_sd`), a
mode shift between fast and reasoning (`mode_shift`), and run-to-run noise (sd 0.6),
cut into 0, 1, 2. Two success rules are reported:

- **delta only**: the 95% CI for delta omega2 sits above zero.
- **H4 rule**: that, and the 95% CI for reasoning minus fast (from the same resamples)
  also sits above zero. This is the pre-registered rule for H4, H1 and H2.

The mode shift's variance is `(mode_shift / 2)^2`. Family variance is `family_sd^2`.
Mode only "beats" model when the first is clearly larger than the second.

| family_sd | mode_shift | Mode var / family var | 6 fam x 3 reps (36 runs) | 6 fam x 5 reps (60 runs) | 8 fam x 5 reps (80 runs) |
|---|---|---|---|---|---|
| 0.5 | 1.0 | 1.0 (no real difference) | 0.12 | 0.15 | 0.15 |
| 0.3 | 1.0 | 2.8 | 0.32 | 0.41 | 0.45 |
| 0.5 | 1.4 | 2.0 | 0.47 | 0.57 | 0.65 |
| 0.3 | 1.4 | 5.4 | 0.74 | 0.91 | 0.92 |
| 0.2 | 1.4 | 12.3 | 0.80 | 0.98 | 0.98 |

Every cell above is the same under both rules (re-run 2026-10-12). When reasoning raises
scores enough for delta's CI to clear zero, the reasoning-minus-fast CI clears zero too,
so the direction condition costs no power in these scenarios.

The direction condition does its job when reasoning lowers scores. With family_sd 0.3 and
mode_shift -1.4 (60 runs), delta alone is above zero in 0.88 of studies; under the H4
rule, 0.00.

## What this means for you

- **60 runs detects a strong mode effect reliably** (power about 0.9 when mode variance is
  five times family variance).
- **It will miss a moderate one** (power about 0.4 to 0.6). An "inconclusive" verdict on a
  dimension is then expected, not a failure. Say so in the paper.
- **Replicates beat families.** Going from 3 to 5 replicates gains more than going from
  6 to 8 families, and costs less, because extra families need new vendor work.
- **Under equal effects, 0.15 of simulated studies still show "mode > model"** at 60
  runs, three times the nominal 5%. Not all of these are errors: families are treated as
  fixed, and in some simulated studies the six drawn families really do vary less than
  mode does. The rest is small-sample bootstrap error. The paper states this rate beside
  the H4 result.

## Limits of this simulation

- It models one 0 to 2 dimension. H4 is tested on the total (sum of nine dimensions),
  which has finer steps and correlated parts; that is not simulated.
- With 5 replicates per cell, percentile bootstrap intervals can be too narrow, so the
  real false-positive rate may sit above 5% (see the equal-effects row).

## If budget allows

Add a second frozen prompt (a different constrained-design task) with the same grid.
That doubles the evidence and answers the "one prompt" objection. Analyse it as a
separate, pre-registered replication, not pooled.

## Reproduce

```bash
modegrid power --families 6 8 --replicates 3 5 --family-sd 0.3 --mode-shift 1.4 --sims 200
modegrid power --families 6 --replicates 5 --family-sd 0.3 --mode-shift -1.4 --sims 200
```
