# Threats to validity

Each threat has a mitigation and the place in the paper where it is reported.

## Construct validity

| Threat | Mitigation |
|---|---|
| "Mode" is not the same control across vendors. One vendor's off is another's low. | Mode registry documents each setting with evidence. Harmonised to two levels. Discussed as a limitation. |
| A vendor routes fast mode to a smaller model. | Rule: same weights only. Record the model the app shows in every capture, plus a screenshot. The API check records which model answered. |
| Chat apps are less controlled than an API (hidden system prompt, snapshot changes). | Matches real use and LA-P1. API check per mode as evidence of the switch. Limitation stated in the paper. |
| Grok app Fast may not be the same model as Expert. xAI does not document it, and the API (`grok-4.6`) cannot disable reasoning. | API check uses `grok-4.6` low vs xhigh as an approximation. Model name the app shows recorded in every capture. Grok results reported with this caveat. |
| Claude (Sonnet 5.5), Gemini and Grok have no true "off", so "fast" is the lowest available level for 3 of 6 families. The contrast is "low vs high reasoning" there and "off vs on" for GPT, Qwen and DeepSeek. | Recorded per family in the mode registry. The API check shows how many reasoning tokens the lowest level still uses. Pre-registered robustness check 4 analyses the two groups separately; if the effect holds only in the true-off group, the claim is reported for off vs on only. |
| Qwen uses Qwen3.8-Max, while LA-P1 used Qwen3.7-Plus. | Qwen results are not compared directly with LA-P1. Stated in the paper. |
| The rubric measures length, not quality. | Length-adjusted robustness check. |
| One prompt. | Optional second prompt as a pre-registered replication. Prompt-sensitivity data from LA-P1 (v2, v3 paraphrases) cited. |

## Internal validity

| Threat | Mitigation |
|---|---|
| Raters know which mode wrote an answer. Reasoning answers can look different. | Blinded packets, self-identification removed, rater guesses recorded and reported as a blinding-failure rate. |
| Answers recommend their own vendor's models, which hints at the family. Masking those names would make D2 to D4 unscorable. | Names used as content are kept; only self-reference is masked. The family-guess accuracy reports how much this leaks. |
| Vendors change models during data collection. | Randomised run order inside each family block. All runs for a family inside 48 hours. Dated captures with an unedited `date_stamped`. Family blocks run on different days, so family is partly confounded with date; stated in the paper. |
| Personalisation in chat apps. | Fresh chat, memory off, no custom instructions, recorded in each capture. |
| A rater sees the captures before scoring. | The author, who collected the captures, never scores. Raters get only the blinded packet and never get repo access (see collaboration.md). |
| LLM raters favour their own vendor or reasoning-style answers. | Two LLMs from different vendors plus one human; median of three; own-vendor scores reported separately; human-vs-LLM agreement reported. |
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
positive one. The study has a single author, so no second author checks the analysis;
the data and code are released so anyone can re-run it, and the author does no
scoring.
