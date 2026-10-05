# Threats to validity

Each threat has a mitigation and the place in the paper where it is reported.

## Construct validity

| Threat | Mitigation |
|---|---|
| "Mode" is not the same control across vendors. One vendor's off is another's low. | Mode registry documents each setting with evidence. Harmonised to two levels. Discussed as a limitation. |
| A vendor routes fast mode to a smaller model. | Rule: same weights only. Record the model the app shows in every capture, plus a screenshot. The API check records which model answered. |
| Chat apps are less controlled than an API (hidden system prompt, snapshot changes). | Matches real use and LA-P1. API check per mode as evidence of the switch. Limitation stated in the paper. |
| Grok app Fast may not be the same model as Expert. xAI does not document it, and the API (`grok-4.6`) cannot disable reasoning. | API check uses `grok-4.6` low vs xhigh as an approximation. Model name the app shows recorded in every capture. Grok results reported with this caveat. |
| Gemini and Grok have no true "off", so "fast" is the lowest available level there. | Recorded per family in the mode registry. The API check shows how many reasoning tokens the lowest level still uses. |
| The rubric measures length, not quality. | Length-adjusted robustness check. |
| One prompt. | Optional second prompt as a pre-registered replication. Prompt-sensitivity data from LA-P1 (v2, v3 paraphrases) cited. |

## Internal validity

| Threat | Mitigation |
|---|---|
| Raters know which mode wrote an answer. Reasoning answers can look different. | Blinded packets, identity redaction, rater guesses recorded and reported as a blinding-failure rate. |
| Vendors change models during data collection. | Randomised run order. All runs for a family inside a short window. Dated captures. |
| Personalisation in chat apps. | Fresh chat, memory off, no custom instructions, recorded in each capture. |
| A co-author or rater sees the captures before scoring. | Raters get only the blinded packet. Repo access for raters only after unblinding (see collaboration.md). |
| Raters with old training data flag real new tools as fake (the LA-P2 effect). | Mandatory web verification for D3 and D4. UNRESOLVED scores as 1. |
| Analysis choices made after seeing data. | Pre-registration tagged before the first capture. Deviations logged. |

## Statistical conclusion validity

| Threat | Mitigation |
|---|---|
| Small n per cell. | 5 replicates. Power analysis published. Inconclusive verdicts reported as such. |
| Ordinal 0/1/2 scores. | Permutation tests, rank-transform check. |
| Unequal degrees of freedom favour family. | omega squared as the primary statistic. |
| Low inter-rater agreement on some dimensions (LA-P1 kappa about 0.15 on D1, D7, D8, D9 under v1). | v2 anchors. Pre-registered alpha bar. Dimensions under the bar labelled unreliable. |

## External validity

| Threat | Mitigation |
|---|---|
| Six families are not all models. | Families treated as fixed. Claims limited to the families tested. |
| One task domain (systems architecture under a hardware budget). | Stated scope. Second prompt if budget allows. |
| Results date fast. | Every capture is dated. Data release archived with a DOI. |

## Author bias

The author proposed the claim. The pilot does not clearly support it. The pre-registration
says so in advance, so a negative or mixed result is reported with the same weight as a
positive one.
