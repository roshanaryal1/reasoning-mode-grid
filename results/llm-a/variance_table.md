# Variance decomposition: mode vs model vs residual

Design: 6 families (claude, deepseek, gemini, gpt, grok, qwen) x 2 modes (fast, reasoning) x 5 replicates = 60 runs, 12 cells.

Primary statistic: delta = omega2(mode) - omega2(family), 95% bootstrap CI over replicates.

| Dim | Name | eta2 family | eta2 mode | eta2 FxM | eta2 resid | omega2 FxM | delta omega2 | 95% CI | reasoning - fast | 95% CI | p mode | p family | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 | hardware-constraint | 0.206 | 0.000 | 0.147 | 0.647 | 0.079 | -0.150 | [-0.386, -0.045] | 0.000 | [-0.200, 0.200] | 1.000 | 0.035 | model > mode |
| D2 | recency | 0.767 | 0.001 | 0.006 | 0.226 | -0.018 | -0.744 | [-0.874, -0.634] | -0.033 | [-0.133, 0.067] | 1.000 | 0.000 | model > mode |
| D3 | tool-factuality | 0.531 | 0.018 | 0.022 | 0.429 | -0.022 | -0.473 | [-0.704, -0.314] | -0.133 | [-0.300, 0.033] | 0.285 | 0.000 | model > mode |
| D4 | model-factuality | 0.389 | 0.041 | 0.163 | 0.407 | 0.119 | -0.312 | [-0.587, -0.141] | 0.200 | [0.033, 0.367] | 0.110 | 0.000 | model > mode |
| D5 | benchmark-factuality | 0.348 | 0.063 | 0.149 | 0.439 | 0.102 | -0.246 | [-0.435, -0.138] | 0.333 | [0.100, 0.567] | 0.033 | 0.000 | model > mode |
| D6 | citation-quality | 0.551 | 0.000 | 0.013 | 0.436 | -0.032 | -0.510 | [-0.727, -0.347] | 0.000 | [-0.167, 0.167] | 1.000 | 0.000 | model > mode |
| D7 | actionability | 0.229 | 0.111 | 0.201 | 0.458 | 0.152 | -0.079 | [-0.334, 0.018] | 0.267 | [0.133, 0.400] | 0.012 | 0.012 | inconclusive |
| D8 | security-model | 0.403 | 0.093 | 0.147 | 0.357 | 0.109 | -0.279 | [-0.465, -0.159] | 0.300 | [0.133, 0.433] | 0.008 | 0.000 | model > mode |
| D9 | internal-consistency | 0.425 | 0.056 | 0.089 | 0.430 | 0.044 | -0.331 | [-0.599, -0.103] | 0.300 | [0.100, 0.533] | 0.038 | 0.000 | model > mode |
| total | sum of D1-D9 | 0.603 | 0.055 | 0.144 | 0.198 | 0.123 | -0.530 | [-0.674, -0.411] | 1.233 | [0.633, 1.800] | 0.006 | 0.000 | model > mode |

## Pre-registered hypotheses

H4 is the single confirmatory test; H1-H3 are pre-specified secondary tests.

| ID | Role | Dimension | Predicted | Observed | Reasoning - fast (95% CI) | Supported |
|---|---|---|---|---|---|---|
| H1 | secondary | D1 (Constraint reasoning is mode-sensitive) | mode > model; reasoning > fast | model > mode | 0.000 [-0.200, 0.200] | no |
| H2 | secondary | D9 (Internal consistency is mode-sensitive) | mode > model; reasoning > fast | model > mode | 0.300 [0.100, 0.533] | no |
| H3 | secondary | D3 (Tool factuality is mode-stable) | model > mode | model > mode | -0.133 [-0.300, 0.033] | yes, pending alpha |
| H4 | confirmatory | total (Headline: mode explains more of the total than model) | mode > model; reasoning > fast | model > mode | 1.233 [0.633, 1.800] | no |

## Sensitivity checks

| Dim | delta omega2 (raw) | delta omega2 (ranks) | delta omega2 (length-adjusted) |
|---|---|---|---|
| D1 | -0.150 | -0.145 | -0.120 |
| D2 | -0.744 | -0.744 | -0.663 |
| D3 | -0.473 | -0.473 | -0.475 |
| D4 | -0.312 | -0.297 | -0.303 |
| D5 | -0.246 | -0.268 | -0.336 |
| D6 | -0.510 | -0.523 | -0.454 |
| D7 | -0.079 | -0.079 | -0.172 |
| D8 | -0.279 | -0.279 | -0.236 |
| D9 | -0.331 | -0.304 | -0.349 |
| total | -0.530 | -0.572 | -0.650 |

## Random-effects variance components (exploratory)

Method of moments, truncated at zero. These read families as a sample from a wider
population; the primary analysis treats them as fixed, so these are exploratory.

| Dim | family | mode | family x mode | residual |
|---|---|---|---|---|
| D1 | 0.016 | 0.000 | 0.043 | 0.183 |
| D2 | 0.216 | 0.000 | 0.000 | 0.067 |
| D3 | 0.152 | 0.007 | 0.000 | 0.133 |
| D4 | 0.067 | 0.004 | 0.071 | 0.125 |
| D5 | 0.105 | 0.029 | 0.109 | 0.242 |
| D6 | 0.168 | 0.000 | 0.000 | 0.142 |
| D7 | 0.005 | 0.023 | 0.059 | 0.092 |
| D8 | 0.075 | 0.031 | 0.064 | 0.108 |
| D9 | 0.163 | 0.031 | 0.043 | 0.217 |
| total | 3.824 | 0.360 | 2.060 | 1.717 |
