# Variance decomposition: mode vs model vs residual



Design: 3 families (deepseek, gpt, qwen) x 2 modes (fast, reasoning) x 5 replicates = 30 runs, 6 cells.

Primary statistic: delta = omega2(mode) - omega2(family), 95% bootstrap CI over replicates.

| Dim | Name | eta2 family | eta2 mode | eta2 FxM | eta2 resid | omega2 FxM | delta omega2 | 95% CI | reasoning - fast | 95% CI | p mode | p family | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 | hardware-constraint | 0.199 | 0.004 | 0.199 | 0.598 | 0.146 | -0.167 | [-0.425, 0.018] | -0.067 | [-0.400, 0.267] | 1.000 | 0.081 | inconclusive |
| D2 | recency | 0.413 | 0.048 | 0.095 | 0.444 | 0.057 | -0.340 | [-0.693, -0.034] | 0.200 | [0.000, 0.400] | 0.329 | 0.002 | model > mode |
| D3 | tool-factuality | 0.335 | 0.005 | 0.118 | 0.543 | 0.071 | -0.301 | [-0.640, -0.074] | -0.067 | [-0.333, 0.200] | 1.000 | 0.009 | model > mode |
| D4 | model-factuality | 0.456 | 0.113 | 0.131 | 0.300 | 0.105 | -0.327 | [-0.690, -0.025] | 0.400 | [0.200, 0.600] | 0.041 | 0.000 | model > mode |
| D5 | benchmark-factuality | 0.217 | 0.154 | 0.217 | 0.411 | 0.180 | -0.045 | [-0.269, 0.149] | 0.600 | [0.267, 0.933] | 0.039 | 0.030 | inconclusive |
| D6 | citation-quality | 0.722 | 0.000 | 0.019 | 0.259 | -0.003 | -0.704 | [-0.880, -0.521] | 0.000 | [-0.200, 0.200] | 1.000 | 0.000 | model > mode |
| D7 | actionability | 0.118 | 0.078 | 0.275 | 0.529 | 0.225 | -0.017 | [-0.245, 0.156] | 0.267 | [0.000, 0.467] | 0.244 | 0.218 | inconclusive |
| D8 | security-model | 0.067 | 0.234 | 0.182 | 0.517 | 0.136 | 0.185 | [-0.073, 0.445] | 0.467 | [0.200, 0.733] | 0.021 | 0.437 | inconclusive |
| D9 | internal-consistency | 0.212 | 0.200 | 0.212 | 0.377 | 0.177 | 0.004 | [-0.291, 0.283] | 0.733 | [0.400, 1.067] | 0.018 | 0.019 | inconclusive |
| total | sum of D1-D9 | 0.502 | 0.146 | 0.222 | 0.130 | 0.210 | -0.348 | [-0.554, -0.161] | 2.533 | [1.667, 3.400] | 0.005 | 0.000 | model > mode |

## Pre-registered hypotheses

H4 is the single confirmatory test; H1-H3 are pre-specified secondary tests.

| ID | Role | Dimension | Predicted | Observed | Reasoning - fast (95% CI) | Supported |
|---|---|---|---|---|---|---|
| H1 | secondary | D1 (Constraint reasoning is mode-sensitive) | mode > model; reasoning > fast | inconclusive | -0.067 [-0.400, 0.267] | no |
| H2 | secondary | D9 (Internal consistency is mode-sensitive) | mode > model; reasoning > fast | inconclusive | 0.733 [0.400, 1.067] | no |
| H3 | secondary | D3 (Tool factuality is mode-stable) | model > mode | model > mode | -0.067 [-0.333, 0.200] | yes, pending alpha |
| H4 | confirmatory | total (Headline: mode explains more of the total than model) | mode > model; reasoning > fast | model > mode | 2.533 [1.667, 3.400] | no |

## Sensitivity checks

| Dim | delta omega2 (raw) | delta omega2 (ranks) | delta omega2 (length-adjusted) |
|---|---|---|---|
| D1 | -0.167 | -0.149 | -0.162 |
| D2 | -0.340 | -0.340 | -0.359 |
| D3 | -0.301 | -0.301 | -0.293 |
| D4 | -0.327 | -0.374 | -0.519 |
| D5 | -0.045 | -0.052 | -0.208 |
| D6 | -0.704 | -0.752 | -0.646 |
| D7 | -0.017 | 0.001 | -0.015 |
| D8 | 0.185 | 0.185 | -0.181 |
| D9 | 0.004 | 0.000 | -0.184 |
| total | -0.348 | -0.442 | -0.643 |

## Random-effects variance components (exploratory)

Method of moments, truncated at zero. These read families as a sample from a wider
population; the primary analysis treats them as fixed, so these are exploratory.

| Dim | family | mode | family x mode | residual |
|---|---|---|---|---|
| D1 | 0.000 | 0.000 | 0.140 | 0.233 |
| D2 | 0.100 | 0.000 | 0.037 | 0.117 |
| D3 | 0.080 | 0.000 | 0.053 | 0.167 |
| D4 | 0.173 | 0.033 | 0.113 | 0.133 |
| D5 | 0.000 | 0.053 | 0.320 | 0.300 |
| D6 | 0.380 | 0.000 | 0.000 | 0.117 |
| D7 | 0.000 | 0.000 | 0.157 | 0.150 |
| D8 | 0.000 | 0.067 | 0.097 | 0.150 |
| D9 | 0.000 | 0.127 | 0.363 | 0.317 |
| total | 4.600 | 0.767 | 6.970 | 1.783 |
