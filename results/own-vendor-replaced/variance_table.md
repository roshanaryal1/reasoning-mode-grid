# Variance decomposition: mode vs model vs residual

Exploratory, not pre-registered: consensus with each LLM rater's own-vendor scores replaced by the mean of the other raters (llm-a on claude, llm-b on gpt)

Design: 6 families (claude, deepseek, gemini, gpt, grok, qwen) x 2 modes (fast, reasoning) x 5 replicates = 60 runs, 12 cells.

Primary statistic: delta = omega2(mode) - omega2(family), 95% bootstrap CI over replicates.

| Dim | Name | eta2 family | eta2 mode | eta2 FxM | eta2 resid | omega2 FxM | delta omega2 | 95% CI | reasoning - fast | 95% CI | p mode | p family | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 | hardware-constraint | 0.207 | 0.000 | 0.146 | 0.647 | 0.078 | -0.151 | [-0.377, -0.055] | -0.017 | [-0.200, 0.183] | 1.000 | 0.028 | model > mode |
| D2 | recency | 0.620 | 0.001 | 0.048 | 0.331 | 0.013 | -0.587 | [-0.823, -0.431] | -0.033 | [-0.150, 0.100] | 0.821 | 0.000 | model > mode |
| D3 | tool-factuality | 0.458 | 0.011 | 0.099 | 0.432 | 0.053 | -0.407 | [-0.650, -0.255] | -0.100 | [-0.250, 0.050] | 0.368 | 0.000 | model > mode |
| D4 | model-factuality | 0.430 | 0.030 | 0.167 | 0.373 | 0.127 | -0.366 | [-0.647, -0.184] | 0.167 | [0.017, 0.317] | 0.127 | 0.000 | model > mode |
| D5 | benchmark-factuality | 0.560 | 0.045 | 0.132 | 0.263 | 0.104 | -0.490 | [-0.624, -0.416] | 0.350 | [0.133, 0.567] | 0.024 | 0.000 | model > mode |
| D6 | citation-quality | 0.717 | 0.000 | 0.013 | 0.269 | -0.014 | -0.691 | [-0.836, -0.627] | 0.000 | [-0.117, 0.117] | 1.000 | 0.000 | model > mode |
| D7 | actionability | 0.210 | 0.048 | 0.204 | 0.538 | 0.146 | -0.116 | [-0.346, -0.024] | 0.183 | [0.017, 0.333] | 0.096 | 0.023 | model > mode |
| D8 | security-model | 0.430 | 0.069 | 0.139 | 0.362 | 0.101 | -0.328 | [-0.512, -0.221] | 0.250 | [0.100, 0.383] | 0.015 | 0.000 | model > mode |
| D9 | internal-consistency | 0.305 | 0.051 | 0.224 | 0.420 | 0.178 | -0.218 | [-0.424, -0.089] | 0.367 | [0.100, 0.633] | 0.058 | 0.001 | model > mode |
| total | sum of D1-D9 | 0.565 | 0.044 | 0.224 | 0.167 | 0.206 | -0.506 | [-0.646, -0.400] | 1.167 | [0.583, 1.733] | 0.020 | 0.000 | model > mode |

## Pre-registered hypotheses

H4 is the single confirmatory test; H1-H3 are pre-specified secondary tests.

| ID | Role | Dimension | Predicted | Observed | Reasoning - fast (95% CI) | Supported |
|---|---|---|---|---|---|---|
| H1 | secondary | D1 (Constraint reasoning is mode-sensitive) | mode > model; reasoning > fast | model > mode | -0.017 [-0.200, 0.183] | no |
| H2 | secondary | D9 (Internal consistency is mode-sensitive) | mode > model; reasoning > fast | model > mode | 0.367 [0.100, 0.633] | no |
| H3 | secondary | D3 (Tool factuality is mode-stable) | model > mode | model > mode | -0.100 [-0.250, 0.050] | yes, pending alpha |
| H4 | confirmatory | total (Headline: mode explains more of the total than model) | mode > model; reasoning > fast | model > mode | 1.167 [0.583, 1.733] | no |

## Sensitivity checks

| Dim | delta omega2 (raw) | delta omega2 (ranks) | delta omega2 (length-adjusted) | omega2 mode (raw) | omega2 mode (length-adjusted) | reasoning - fast (raw) | reasoning - fast (length-adjusted) |
|---|---|---|---|---|---|---|---|
| D1 | -0.151 | -0.153 | -0.115 | -0.013 | -0.001 | -0.017 | -0.102 |
| D2 | -0.587 | -0.620 | -0.470 | -0.005 | 0.007 | -0.033 | 0.101 |
| D3 | -0.407 | -0.386 | -0.336 | 0.002 | -0.008 | -0.100 | 0.035 |
| D4 | -0.366 | -0.333 | -0.367 | 0.023 | 0.022 | 0.167 | 0.166 |
| D5 | -0.490 | -0.419 | -0.544 | 0.039 | 0.019 | 0.350 | 0.256 |
| D6 | -0.691 | -0.787 | -0.653 | -0.006 | 0.014 | 0.000 | -0.118 |
| D7 | -0.116 | -0.130 | -0.145 | 0.037 | -0.013 | 0.183 | -0.017 |
| D8 | -0.328 | -0.318 | -0.186 | 0.061 | 0.003 | 0.250 | -0.090 |
| D9 | -0.218 | -0.220 | -0.235 | 0.042 | 0.035 | 0.367 | 0.343 |
| total | -0.506 | -0.555 | -0.611 | 0.040 | 0.007 | 1.167 | 0.573 |

## Random-effects variance components (exploratory)

Method of moments, truncated at zero. These read families as a sample from a wider
population; the primary analysis treats them as fixed, so these are exploratory.

| Dim | family | mode | family x mode | residual |
|---|---|---|---|---|
| D1 | 0.016 | 0.000 | 0.041 | 0.177 |
| D2 | 0.128 | 0.000 | 0.006 | 0.077 |
| D3 | 0.095 | 0.000 | 0.028 | 0.119 |
| D4 | 0.072 | 0.000 | 0.070 | 0.106 |
| D5 | 0.349 | 0.025 | 0.171 | 0.223 |
| D6 | 0.157 | 0.000 | 0.000 | 0.062 |
| D7 | 0.001 | 0.003 | 0.061 | 0.117 |
| D8 | 0.079 | 0.019 | 0.055 | 0.102 |
| D9 | 0.065 | 0.008 | 0.286 | 0.348 |
| total | 3.189 | 0.000 | 3.870 | 1.627 |
