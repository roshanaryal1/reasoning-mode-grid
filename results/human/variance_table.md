# Variance decomposition: mode vs model vs residual



Design: 6 families (claude, deepseek, gemini, gpt, grok, qwen) x 2 modes (fast, reasoning) x 5 replicates = 60 runs, 12 cells.

Primary statistic: delta = omega2(mode) - omega2(family), 95% bootstrap CI over replicates.

| Dim | Name | eta2 family | eta2 mode | eta2 FxM | eta2 resid | omega2 FxM | delta omega2 | 95% CI | reasoning - fast | 95% CI | p mode | p family | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 | hardware-constraint | 0.187 | 0.012 | 0.078 | 0.722 | 0.003 | -0.113 | [-0.375, -0.025] | -0.100 | [-0.300, 0.100] | 0.551 | 0.057 | model > mode |
| D2 | recency | 0.650 | 0.001 | 0.074 | 0.274 | 0.045 | -0.623 | [-0.808, -0.524] | 0.033 | [-0.100, 0.167] | 1.000 | 0.000 | model > mode |
| D3 | tool-factuality | 0.305 | 0.067 | 0.369 | 0.259 | 0.340 | -0.214 | [-0.364, -0.159] | 0.167 | [0.100, 0.233] | 0.057 | 0.003 | model > mode |
| D4 | model-factuality | 0.360 | 0.055 | 0.402 | 0.183 | 0.382 | -0.289 | [-0.364, -0.279] | 0.200 | [0.100, 0.300] | 0.066 | 0.000 | uninformative (low variance) |
| D5 | benchmark-factuality | 0.710 | 0.045 | 0.050 | 0.194 | 0.030 | -0.647 | [-0.759, -0.594] | 0.367 | [0.167, 0.533] | 0.007 | 0.000 | model > mode |
| D6 | citation-quality | 0.590 | 0.022 | 0.015 | 0.374 | -0.024 | -0.533 | [-0.742, -0.358] | 0.167 | [0.000, 0.333] | 0.167 | 0.000 | model > mode |
| D7 | actionability | 0.238 | 0.049 | 0.130 | 0.584 | 0.068 | -0.139 | [-0.402, -0.020] | 0.200 | [0.033, 0.367] | 0.123 | 0.010 | model > mode |
| D8 | security-model | 0.415 | 0.029 | 0.161 | 0.395 | 0.119 | -0.350 | [-0.525, -0.260] | 0.167 | [0.000, 0.333] | 0.168 | 0.000 | model > mode |
| D9 | internal-consistency | 0.202 | 0.091 | 0.076 | 0.631 | 0.010 | -0.058 | [-0.359, 0.061] | 0.367 | [0.133, 0.600] | 0.023 | 0.018 | inconclusive |
| total | sum of D1-D9 | 0.562 | 0.101 | 0.151 | 0.185 | 0.131 | -0.444 | [-0.631, -0.284] | 1.567 | [1.033, 2.100] | 0.001 | 0.000 | model > mode |

## Pre-registered hypotheses

H4 is the single confirmatory test; H1-H3 are pre-specified secondary tests.

| ID | Role | Dimension | Predicted | Observed | Reasoning - fast (95% CI) | Supported |
|---|---|---|---|---|---|---|
| H1 | secondary | D1 (Constraint reasoning is mode-sensitive) | mode > model; reasoning > fast | model > mode | -0.100 [-0.300, 0.100] | no |
| H2 | secondary | D9 (Internal consistency is mode-sensitive) | mode > model; reasoning > fast | inconclusive | 0.367 [0.133, 0.600] | no |
| H3 | secondary | D3 (Tool factuality is mode-stable) | model > mode | model > mode | 0.167 [0.100, 0.233] | yes, pending alpha (average effect only; interaction exceeds both main effects) |
| H4 | confirmatory | total (Headline: mode explains more of the total than model) | mode > model; reasoning > fast | model > mode | 1.567 [1.033, 2.100] | no |

## Sensitivity checks

| Dim | delta omega2 (raw) | delta omega2 (ranks) | delta omega2 (length-adjusted) |
|---|---|---|---|
| D1 | -0.113 | -0.113 | -0.071 |
| D2 | -0.623 | -0.623 | -0.577 |
| D3 | -0.214 | -0.214 | -0.267 |
| D4 | -0.289 | -0.311 | -0.363 |
| D5 | -0.647 | -0.651 | -0.550 |
| D6 | -0.533 | -0.538 | -0.556 |
| D7 | -0.139 | -0.137 | -0.165 |
| D8 | -0.350 | -0.350 | -0.093 |
| D9 | -0.058 | -0.089 | -0.044 |
| total | -0.444 | -0.502 | -0.591 |

## Random-effects variance components (exploratory)

Method of moments, truncated at zero. These read families as a sample from a wider
population; the primary analysis treats them as fixed, so these are exploratory.

| Dim | family | mode | family x mode | residual |
|---|---|---|---|---|
| D1 | 0.027 | 0.000 | 0.001 | 0.183 |
| D2 | 0.168 | 0.000 | 0.027 | 0.083 |
| D3 | 0.000 | 0.000 | 0.085 | 0.033 |
| D4 | 0.000 | 0.000 | 0.168 | 0.042 |
| D5 | 0.597 | 0.052 | 0.055 | 0.183 |
| D6 | 0.221 | 0.012 | 0.000 | 0.150 |
| D7 | 0.027 | 0.009 | 0.034 | 0.150 |
| D8 | 0.072 | 0.000 | 0.068 | 0.117 |
| D9 | 0.056 | 0.056 | 0.009 | 0.292 |
| total | 2.984 | 0.861 | 1.915 | 1.400 |
