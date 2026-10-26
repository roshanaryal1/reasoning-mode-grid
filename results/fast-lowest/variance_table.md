# Variance decomposition: mode vs model vs residual



Design: 3 families (claude, gemini, grok) x 2 modes (fast, reasoning) x 5 replicates = 30 runs, 6 cells.

Primary statistic: delta = omega2(mode) - omega2(family), 95% bootstrap CI over replicates.

| Dim | Name | eta2 family | eta2 mode | eta2 FxM | eta2 resid | omega2 FxM | delta omega2 | 95% CI | reasoning - fast | 95% CI | p mode | p family | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 | hardware-constraint | 0.208 | 0.008 | 0.016 | 0.768 | -0.047 | -0.163 | [-0.538, 0.066] | 0.067 | [-0.133, 0.267] | 1.000 | 0.110 | inconclusive |
| D2 | recency | 0.871 | 0.005 | 0.010 | 0.115 | -0.000 | -0.857 | [-1.000, -0.663] | -0.067 | [-0.200, 0.000] | 1.000 | 0.000 | model > mode |
| D3 | tool-factuality | 0.727 | 0.023 | 0.045 | 0.205 | 0.028 | -0.690 | [-1.000, -0.379] | -0.133 | [-0.267, 0.000] | 0.445 | 0.000 | model > mode |
| D4 | model-factuality | 0.074 | 0.012 | 0.025 | 0.889 | -0.048 | -0.024 | [-0.271, 0.069] | -0.067 | [-0.267, 0.133] | 1.000 | 0.764 | uninformative (low variance) |
| D5 | benchmark-factuality | 0.819 | 0.001 | 0.021 | 0.159 | 0.007 | -0.806 | [-0.899, -0.735] | 0.067 | [-0.200, 0.333] | 1.000 | 0.000 | model > mode |
| D6 | citation-quality | 0.500 | 0.000 | 0.000 | 0.500 | -0.041 | -0.469 | [-0.842, -0.174] | 0.000 | [-0.200, 0.200] | 1.000 | 0.002 | model > mode |
| D7 | actionability | 0.308 | 0.038 | 0.077 | 0.577 | 0.028 | -0.239 | [-0.538, -0.000] | 0.133 | [-0.067, 0.267] | 0.518 | 0.020 | model > mode |
| D8 | security-model | 0.715 | 0.005 | 0.009 | 0.271 | -0.013 | -0.691 | [-1.000, -0.600] | 0.067 | [-0.133, 0.267] | 1.000 | 0.000 | model > mode |
| D9 | internal-consistency | 0.387 | 0.006 | 0.186 | 0.421 | 0.148 | -0.357 | [-0.612, -0.156] | 0.133 | [-0.267, 0.533] | 0.795 | 0.003 | model > mode |
| total | sum of D1-D9 | 0.751 | 0.002 | 0.058 | 0.189 | 0.042 | -0.736 | [-0.853, -0.617] | 0.200 | [-0.600, 1.000] | 0.796 | 0.000 | model > mode |

## Pre-registered hypotheses

H4 is the single confirmatory test; H1-H3 are pre-specified secondary tests.

| ID | Role | Dimension | Predicted | Observed | Reasoning - fast (95% CI) | Supported |
|---|---|---|---|---|---|---|
| H1 | secondary | D1 (Constraint reasoning is mode-sensitive) | mode > model; reasoning > fast | inconclusive | 0.067 [-0.133, 0.267] | no |
| H2 | secondary | D9 (Internal consistency is mode-sensitive) | mode > model; reasoning > fast | model > mode | 0.133 [-0.267, 0.533] | no |
| H3 | secondary | D3 (Tool factuality is mode-stable) | model > mode | model > mode | -0.133 [-0.267, 0.000] | yes, pending alpha |
| H4 | confirmatory | total (Headline: mode explains more of the total than model) | mode > model; reasoning > fast | model > mode | 0.200 [-0.600, 1.000] | no |

## Sensitivity checks

| Dim | delta omega2 (raw) | delta omega2 (ranks) | delta omega2 (length-adjusted) |
|---|---|---|---|
| D1 | -0.163 | -0.163 | -0.083 |
| D2 | -0.857 | -0.857 | -0.823 |
| D3 | -0.690 | -0.690 | -0.670 |
| D4 | -0.024 | -0.024 | 0.007 |
| D5 | -0.806 | -0.775 | -0.743 |
| D6 | -0.469 | -0.469 | -0.395 |
| D7 | -0.239 | -0.239 | -0.221 |
| D8 | -0.691 | -0.691 | -0.070 |
| D9 | -0.357 | -0.351 | -0.063 |
| total | -0.736 | -0.747 | -0.717 |

## Random-effects variance components (exploratory)

Method of moments, truncated at zero. These read families as a sample from a wider
population; the primary analysis treats them as fixed, so these are exploratory.

| Dim | family | mode | family x mode | residual |
|---|---|---|---|---|
| D1 | 0.040 | 0.000 | 0.000 | 0.133 |
| D2 | 0.300 | 0.000 | 0.000 | 0.033 |
| D3 | 0.200 | 0.000 | 0.017 | 0.050 |
| D4 | 0.007 | 0.000 | 0.000 | 0.100 |
| D5 | 0.907 | 0.000 | 0.017 | 0.150 |
| D6 | 0.120 | 0.000 | 0.000 | 0.100 |
| D7 | 0.040 | 0.000 | 0.010 | 0.083 |
| D8 | 0.260 | 0.000 | 0.000 | 0.083 |
| D9 | 0.220 | 0.000 | 0.330 | 0.383 |
| total | 6.753 | 0.000 | 0.833 | 1.533 |
