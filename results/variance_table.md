# Variance decomposition: mode vs model vs residual

Confirmatory analysis, prereg-v1

Design: 6 families (claude, deepseek, gemini, gpt, grok, qwen) x 2 modes (fast, reasoning) x 5 replicates = 60 runs, 12 cells.

Primary statistic: delta = omega2(mode) - omega2(family), 95% bootstrap CI over replicates.

| Dim | Name | eta2 family | eta2 mode | eta2 FxM | eta2 resid | omega2 FxM | delta omega2 | 95% CI | reasoning - fast | 95% CI | p mode | p family | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 | hardware-constraint | 0.206 | 0.000 | 0.147 | 0.647 | 0.079 | -0.150 | [-0.386, -0.045] | 0.000 | [-0.200, 0.200] | 1.000 | 0.035 | model > mode |
| D2 | recency | 0.692 | 0.004 | 0.063 | 0.241 | 0.037 | -0.664 | [-0.840, -0.547] | 0.067 | [-0.067, 0.200] | 0.662 | 0.000 | model > mode |
| D3 | tool-factuality | 0.524 | 0.011 | 0.084 | 0.381 | 0.044 | -0.477 | [-0.710, -0.321] | -0.100 | [-0.233, 0.033] | 0.450 | 0.000 | model > mode |
| D4 | model-factuality | 0.415 | 0.029 | 0.161 | 0.395 | 0.119 | -0.350 | [-0.637, -0.175] | 0.167 | [0.000, 0.300] | 0.187 | 0.000 | model > mode |
| D5 | benchmark-factuality | 0.582 | 0.039 | 0.125 | 0.254 | 0.098 | -0.519 | [-0.656, -0.440] | 0.333 | [0.133, 0.533] | 0.041 | 0.000 | model > mode |
| D6 | citation-quality | 0.654 | 0.000 | 0.013 | 0.333 | -0.022 | -0.622 | [-0.805, -0.494] | 0.000 | [-0.133, 0.133] | 1.000 | 0.000 | model > mode |
| D7 | actionability | 0.187 | 0.058 | 0.213 | 0.542 | 0.155 | -0.083 | [-0.300, 0.008] | 0.200 | [0.033, 0.333] | 0.096 | 0.045 | inconclusive |
| D8 | security-model | 0.403 | 0.074 | 0.134 | 0.389 | 0.093 | -0.294 | [-0.485, -0.186] | 0.267 | [0.100, 0.400] | 0.020 | 0.000 | model > mode |
| D9 | internal-consistency | 0.316 | 0.066 | 0.226 | 0.392 | 0.184 | -0.216 | [-0.409, -0.095] | 0.433 | [0.167, 0.700] | 0.034 | 0.000 | model > mode |
| total | sum of D1-D9 | 0.595 | 0.053 | 0.200 | 0.152 | 0.184 | -0.527 | [-0.666, -0.417] | 1.367 | [0.767, 1.933] | 0.007 | 0.000 | model > mode |

## Pre-registered hypotheses

H4 is the single confirmatory test; H1-H3 are pre-specified secondary tests.

| ID | Role | Dimension | Predicted | Observed | Reasoning - fast (95% CI) | Supported |
|---|---|---|---|---|---|---|
| H1 | secondary | D1 (Constraint reasoning is mode-sensitive) | mode > model; reasoning > fast | model > mode | 0.000 [-0.200, 0.200] | exploratory (alpha 0.57 below 0.667) |
| H2 | secondary | D9 (Internal consistency is mode-sensitive) | mode > model; reasoning > fast | model > mode | 0.433 [0.167, 0.700] | exploratory (alpha 0.29 below 0.667) |
| H3 | secondary | D3 (Tool factuality is mode-stable) | model > mode | model > mode | -0.100 [-0.233, 0.033] | exploratory (alpha 0.25 below 0.667) |
| H4 | confirmatory | total (Headline: mode explains more of the total than model) | mode > model; reasoning > fast | model > mode | 1.367 [0.767, 1.933] | no |

## Sensitivity checks

| Dim | delta omega2 (raw) | delta omega2 (ranks) | delta omega2 (length-adjusted) | omega2 mode (raw) | omega2 mode (length-adjusted) | reasoning - fast (raw) | reasoning - fast (length-adjusted) |
|---|---|---|---|---|---|---|---|
| D1 | -0.150 | -0.145 | -0.120 | -0.013 | -0.004 | 0.000 | -0.093 |
| D2 | -0.664 | -0.664 | -0.618 | -0.001 | 0.012 | 0.067 | 0.128 |
| D3 | -0.477 | -0.477 | -0.432 | 0.003 | -0.008 | -0.100 | 0.011 |
| D4 | -0.350 | -0.341 | -0.346 | 0.021 | 0.022 | 0.167 | 0.171 |
| D5 | -0.519 | -0.462 | -0.575 | 0.034 | 0.013 | 0.333 | 0.224 |
| D6 | -0.622 | -0.645 | -0.575 | -0.007 | 0.018 | 0.000 | -0.153 |
| D7 | -0.083 | -0.079 | -0.124 | 0.046 | -0.014 | 0.200 | 0.001 |
| D8 | -0.294 | -0.294 | -0.180 | 0.065 | -0.002 | 0.267 | -0.080 |
| D9 | -0.216 | -0.219 | -0.232 | 0.057 | 0.051 | 0.433 | 0.412 |
| total | -0.527 | -0.570 | -0.655 | 0.050 | 0.008 | 1.367 | 0.621 |

## Random-effects variance components (exploratory)

Method of moments, truncated at zero. These read families as a sample from a wider
population; the primary analysis treats them as fixed, so these are exploratory.

| Dim | family | mode | family x mode | residual |
|---|---|---|---|---|
| D1 | 0.016 | 0.000 | 0.043 | 0.183 |
| D2 | 0.188 | 0.000 | 0.022 | 0.075 |
| D3 | 0.120 | 0.000 | 0.024 | 0.108 |
| D4 | 0.072 | 0.000 | 0.068 | 0.117 |
| D5 | 0.389 | 0.020 | 0.168 | 0.225 |
| D6 | 0.200 | 0.000 | 0.000 | 0.108 |
| D7 | 0.000 | 0.005 | 0.065 | 0.117 |
| D8 | 0.077 | 0.023 | 0.054 | 0.117 |
| D9 | 0.077 | 0.029 | 0.317 | 0.350 |
| total | 4.136 | 0.233 | 3.872 | 1.658 |
