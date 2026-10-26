# Variance decomposition: mode vs model vs residual

Design: 6 families (claude, deepseek, gemini, gpt, grok, qwen) x 2 modes (fast, reasoning) x 5 replicates = 60 runs, 12 cells.

Primary statistic: delta = omega2(mode) - omega2(family), 95% bootstrap CI over replicates.

| Dim | Name | eta2 family | eta2 mode | eta2 FxM | eta2 resid | omega2 FxM | delta omega2 | 95% CI | reasoning - fast | 95% CI | p mode | p family | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 | hardware-constraint | 0.335 | 0.005 | 0.103 | 0.557 | 0.045 | -0.280 | [-0.519, -0.146] | 0.067 | [-0.100, 0.233] | 0.738 | 0.001 | model > mode |
| D2 | recency | 0.264 | 0.002 | 0.146 | 0.589 | 0.083 | -0.210 | [-0.476, -0.075] | 0.033 | [-0.133, 0.200] | 1.000 | 0.009 | model > mode |
| D3 | tool-factuality | 0.476 | 0.004 | 0.130 | 0.390 | 0.089 | -0.435 | [-0.655, -0.308] | -0.067 | [-0.233, 0.100] | 0.741 | 0.000 | model > mode |
| D4 | model-factuality | 0.204 | 0.047 | 0.112 | 0.637 | 0.045 | -0.102 | [-0.440, 0.052] | 0.267 | [0.033, 0.533] | 0.113 | 0.022 | inconclusive |
| D5 | benchmark-factuality | 0.451 | 0.051 | 0.169 | 0.329 | 0.134 | -0.371 | [-0.517, -0.281] | 0.400 | [0.133, 0.667] | 0.038 | 0.000 | model > mode |
| D6 | citation-quality | 0.527 | 0.007 | 0.055 | 0.411 | 0.012 | -0.482 | [-0.777, -0.255] | -0.067 | [-0.200, 0.067] | 0.649 | 0.000 | model > mode |
| D7 | actionability | 0.161 | 0.043 | 0.174 | 0.622 | 0.108 | -0.065 | [-0.299, 0.018] | 0.167 | [0.000, 0.333] | 0.177 | 0.087 | inconclusive |
| D8 | security-model | 0.333 | 0.042 | 0.153 | 0.472 | 0.103 | -0.250 | [-0.465, -0.143] | 0.200 | [0.033, 0.367] | 0.121 | 0.001 | model > mode |
| D9 | internal-consistency | 0.296 | 0.012 | 0.223 | 0.469 | 0.173 | -0.243 | [-0.450, -0.149] | 0.200 | [-0.133, 0.533] | 0.441 | 0.004 | model > mode |
| total | sum of D1-D9 | 0.494 | 0.042 | 0.255 | 0.209 | 0.232 | -0.432 | [-0.570, -0.338] | 1.200 | [0.533, 1.867] | 0.033 | 0.000 | model > mode |

## Pre-registered hypotheses

H4 is the single confirmatory test; H1-H3 are pre-specified secondary tests.

| ID | Role | Dimension | Predicted | Observed | Reasoning - fast (95% CI) | Supported |
|---|---|---|---|---|---|---|
| H1 | secondary | D1 (Constraint reasoning is mode-sensitive) | mode > model; reasoning > fast | model > mode | 0.067 [-0.100, 0.233] | no |
| H2 | secondary | D9 (Internal consistency is mode-sensitive) | mode > model; reasoning > fast | model > mode | 0.200 [-0.133, 0.533] | no |
| H3 | secondary | D3 (Tool factuality is mode-stable) | model > mode | model > mode | -0.067 [-0.233, 0.100] | yes, pending alpha |
| H4 | confirmatory | total (Headline: mode explains more of the total than model) | mode > model; reasoning > fast | model > mode | 1.200 [0.533, 1.867] | no |

## Sensitivity checks

| Dim | delta omega2 (raw) | delta omega2 (ranks) | delta omega2 (length-adjusted) |
|---|---|---|---|
| D1 | -0.280 | -0.277 | -0.285 |
| D2 | -0.210 | -0.210 | -0.182 |
| D3 | -0.435 | -0.444 | -0.382 |
| D4 | -0.102 | -0.113 | -0.139 |
| D5 | -0.371 | -0.363 | -0.447 |
| D6 | -0.482 | -0.497 | -0.429 |
| D7 | -0.065 | -0.062 | -0.090 |
| D8 | -0.250 | -0.250 | -0.160 |
| D9 | -0.243 | -0.243 | -0.264 |
| total | -0.432 | -0.463 | -0.551 |

## Random-effects variance components (exploratory)

Method of moments, truncated at zero. These read families as a sample from a wider
population; the primary analysis treats them as fixed, so these are exploratory.

| Dim | family | mode | family x mode | residual |
|---|---|---|---|---|
| D1 | 0.060 | 0.000 | 0.023 | 0.150 |
| D2 | 0.024 | 0.000 | 0.034 | 0.125 |
| D3 | 0.113 | 0.000 | 0.059 | 0.133 |
| D4 | 0.041 | 0.019 | 0.041 | 0.300 |
| D5 | 0.268 | 0.027 | 0.255 | 0.325 |
| D6 | 0.092 | 0.000 | 0.005 | 0.083 |
| D7 | 0.000 | 0.003 | 0.042 | 0.125 |
| D8 | 0.052 | 0.005 | 0.060 | 0.142 |
| D9 | 0.076 | 0.000 | 0.362 | 0.508 |
| total | 2.439 | 0.000 | 4.763 | 2.225 |
