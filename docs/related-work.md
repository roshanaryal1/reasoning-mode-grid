# Related work

Collected 2026-10-02 by web search. Summaries come from abstracts and search
snippets. **Read each paper before citing it**, and check the arXiv version you cite.

Every entry was re-checked on 2026-10-14 by web search (arXiv itself is not reachable from
the build container, so abstracts were read through search results and mirrors). All 13
original papers exist with the ids given. Corrections and peer-reviewed versions are in
"Verification, 2026-10-14" below, and five newer papers are added there.

## How LA-P4 differs, in one paragraph

Prior work on reasoning modes measures accuracy on tasks with an answer key (math,
code, science QA) and usually inside one model family or one training recipe. LA-P4
asks a different question on a different kind of task: on an open-ended, constrained
design task with no answer key, how much of the variation in answer quality comes from
the mode switch versus from which vendor's model you use, decomposed per quality
dimension, across six vendors, in the chat apps people actually use, under a
pre-registered analysis.

## Closest prior work: thinking modes in hybrid models

| Paper | What it found | How to position LA-P4 |
|---|---|---|
| HRBench: Benchmarking and Understanding Thinking-Mode Switch Strategies in Hybrid-Reasoning LLMs. arXiv 2605.28398 | 6 models (Qwen3.5-2B to Kimi-K2.5), 5 math, code and science benchmarks, compares prompt-based, routing and speculative mode switching | Closest benchmark. It studies **how to switch**. LA-P4 studies **how much switching matters relative to model choice**, on an open-ended task |
| Demystifying Hybrid Thinking: Can LLMs Truly Switch Between Think and No-Think? arXiv 2510.12680 | No-think mode is not fully separated from think mode. It stays influenced by think training data | Supports the "mode is not a clean control" threat. Cite in threats to validity |
| Thinking Leakage: A Causal Audit of NoThink Post-Training in Hybrid Reasoning Models. arXiv 2609.28682 | Across 3 hybrid models and 3 post-training methods, no-think behaviour drifts toward think | Same threat, newer evidence |
| Path-Lock Expert: Separating Reasoning Mode in Hybrid Thinking via Architecture-Level Separation. arXiv 2604.27201 | Proposes architectural separation of modes | Shows mode leakage is recognised as a problem |

## Reasoning and factuality (bears on H3)

| Paper | What it found | Relevance |
|---|---|---|
| Li and Ng. Reasoning Models Hallucinate More: Factuality-Aware Reinforcement Learning for Large Reasoning Models. arXiv 2505.24630v2 (6 Nov 2025; v1 of 30 May 2025 was titled "The Hallucination Dilemma: Factuality-Aware Reinforcement Learning for Large Reasoning Models") | Reasoning-oriented RL fine-tuning "significantly increases the prevalence of hallucinations" (abstract). Compares differently trained models, not reasoning switched on and off within one model. No "10 to 13 points" figure appears in the paper's text (checked 2026-10-12) | **Direct tension with H3.** H3 predicts tool factuality is mode-stable. This work suggests reasoning can lower factuality. Discuss either outcome |
| Mitigating Factual Hallucination in Large Reasoning Models via Mixed-Mode Advantage Regularization. arXiv 2607.05861 | Names "thinking-induced hallucination": thinking turns a correct direct answer into a wrong one | Same tension, mechanism-level |
| Learning to Reason for Factuality. arXiv 2508.05618 | Methods to reduce hallucination in reasoning models | Background |
| Heyman and Zylberberg. Reasoning Large Language Model Errors Arise from Hallucinating Critical Problem Features. arXiv 2505.12151 | Errors come from hallucinated problem features | Background for D1 (misreading the hardware spec) |

## Test-time compute

| Paper | What it found | Relevance |
|---|---|---|
| Snell et al., Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters. arXiv 2408.03314 | More inference compute, allocated per prompt, can beat a larger model | The framing LA-P4 tests in the wild: does extra thinking beat a different model? |

## Run-to-run variance (justifies 5 replicates)

| Paper | What it found |
|---|---|
| Non-Determinism of "Deterministic" LLM Settings. arXiv 2408.04667 | Large variation across identical runs, even at temperature 0 |
| Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference. arXiv 2506.09501 | Hardware and batch settings change greedy outputs |
| On Randomness in Agentic Evals. arXiv 2602.07150 | Inference engines add non-determinism through batching and precision |

## LLM-as-judge reliability (for the scoring section)

| Paper | Relevance |
|---|---|
| Lau. Same Input, Different Scores: A Multi Model Study on the Inconsistency of LLM Judge. arXiv 2603.04417 | Why LLM raters need disclosure and a human rater |
| LA-P2, The Rater Is Stale (in preparation) | Why D3 and D4 need web verification |

## Verification, 2026-10-14

### Corrections and versions to cite

| Entry | Finding | Cite as |
|---|---|---|
| arXiv 2603.04417 | Full title is "Same Input, Different Scores: A Multi Model Study on the Inconsistency of LLM Judge", single author Fiona Lau, 4 Feb 2026. Five judge models (GPT-4o, GPT-4o-mini, Gemini-2.5-Flash, Claude Haiku 4.5, Claude Sonnet 4.5). Scores varied across models even at temperature 0 | arXiv preprint, full title |
| arXiv 2505.12151 | Title says "Reasoning Large Language Model Errors", not "Reasoning LLM Errors". Heyman and Zylberberg, 17 May 2025. Graph colouring: reasoning models invent edges the prompt never gave | arXiv preprint, corrected title |
| arXiv 2408.03314 | Snell, Lee, Xu, Kumar. Published at ICLR 2025 (oral) as "Scaling LLM Test-Time Compute Optimally Can be More Effective than Scaling Parameters for Reasoning" | ICLR 2025 title |
| arXiv 2505.24630 | Li and Ng (NUS). Accepted at NeurIPS 2025. The abstract sentence "reasoning-oriented RL fine-tuning significantly increases the prevalence of hallucinations" is confirmed | NeurIPS 2025 |
| arXiv 2506.09501 | Yuan, Li and others (Rice, Minnesota, Adobe). NeurIPS 2025 oral. Up to 9% accuracy and 9,000-token length variation for a reasoning model under bfloat16 greedy decoding, depending on GPU count, type and batch size | NeurIPS 2025 |
| arXiv 2408.04667 | Atil and 12 co-authors (Penn State, Comcast). Also published at the 5th Eval4NLP workshop as "Non-Determinism of 'Deterministic' LLM System Settings in Hosted Environments" | Workshop version |
| arXiv 2602.07150 | Bjarnason, Silva, Monperrus (KTH). ICLR 2026. 60,000 SWE-Bench-Verified trajectories: single-run pass@1 moved 2.2 to 6.0 points with the run chosen, SD above 1.5 at temperature 0 | ICLR 2026 |
| arXiv 2508.05618 | Chen and seven co-authors (FAIR at Meta, UW). ICML 2026. Reports that reasoning LLMs hallucinate more than non-reasoning models on long-form factuality, which adds to the H3 competing prediction | ICML 2026 |
| arXiv 2510.12680, 2604.27201 | Same first author (Shouren Wang). Path-Lock Expert: on Qwen3-4B, AIME24, no-think reflective tokens fall from 2.54 to 0.39 | arXiv preprints |
| arXiv 2609.28682 | Liu and Honavar (Penn State). Leakage ratio 42% to 79% across nine aligned checkpoints | arXiv preprint |
| arXiv 2607.05861 | Wang, Zheng, Cui, Chen, Xiong, Huang. MARGO, "thinking-induced hallucination" | arXiv preprint |
| arXiv 2605.28398 | Ning, Liu, Ye, Zhang, Liu (HKUST Guangzhou, Tencent), 27 May 2026 | arXiv preprint |

### Newer or missed work, found 2026-10-14

| Paper | What it found | Relevance |
|---|---|---|
| Haase, Gonnermann-Müller, Hanel, Leins, Kosch, Mendling, Pokutta. Within-Model vs Between-Prompt Variability in Large Language Models for Creative Tasks. arXiv 2601.21339 (29 Jan 2026). A version titled "It's Not Just the Prompt: Model Choice Dominates LLM Creative Output" has DOI 10.1145/3772363.3799284. Confirm it is the same work before citing | 12 LLMs, 10 creativity prompts, 100 samples each. Variance split into model, prompt, within-model and interaction. For originality, model 41%, prompt 36%, within-model 11%. The authors note the balance may shift on constrained tasks | **Closest method.** Same variance-decomposition logic, but model vs prompt, not model vs mode, and on an unconstrained task. LA-P4 is the constrained-task, mode-axis counterpart |
| How Does Thinking Mode Change LLM Moral Judgments? A Controlled Instant-vs-Thinking Comparison Across Five Frontier Models. arXiv 2605.04488 (May 2026). Authors not confirmed | Same checkpoint, instant vs thinking, five vendors, 3,000 API calls. Verdict agreement barely changes (alpha 0.781 vs 0.789). Notes that Gemini's minimal level is not a clean off | **Closest design.** Same crossed vendor x mode idea, but moral verdicts with an answer space, API not chat apps, LLM judges only. Its note on Gemini matches our "lowest available" group |
| Zhang, Wang, Ge, Xu, Hamm, Reddy. Stop Comparing LLM Agents Without Disclosing the Harness. arXiv 2605.23950, ICML 2026 position paper | Harness-induced variance can exceed model-induced variance and reverse model rankings. Proposes a variance-decomposition protocol | Same argument shape: a setting around the model can matter more than the model. Supports the "report mode alongside model" discussion point |
| Thinking Inertia: LLMs Keep Thinking When Told Not To. arXiv 2610.11765 (Oct 2026, about a week old when found). Authors not confirmed | Six LLMs keep reasoning under explicit no-thinking controls, more so as the answer space opens. On open-ended tasks accuracy drops about 15 points as controls tighten | Threat to validity: a "fast" setting may still reason on an open-ended task like ours. Supports reporting reasoning tokens per mode (API check) |
| Sahu, Bothra, Arun, Godfrey, Narayan, Saeed. Assistants, Not Architects: The Role of LLMs in Networked Systems Design. arXiv 2604.25506 (Apr 2026) | LLMs cannot yet reliably do architectural reasoning for networked systems. How the LLM is involved in design changes outputs a lot | Task-domain context: LLMs as systems architects, the LA-P1 and LA-P4 task family |

No study found that crosses reasoning mode with model identity and decomposes variance on an
open-ended, constrained design task. That gap is the paper's contribution claim. Repeat this
search before submission.

## Verification, 2026-10-26

Re-checked against the arXiv API (all 18 ids), Crossref and DataCite before writing
`paper/references.md`.

- All 18 arXiv ids resolve with the titles and authors above.
- Authors now confirmed: arXiv 2610.11765 (Thinking Inertia) is Lei, Lin, Lu, Torr and Zou,
  accepted at NeurIPS 2026 per its arXiv comment. arXiv 2605.04488 is by Sai Sourabh Madur.
- Venues stated in the arXiv record: Li and Ng (NeurIPS 2025), Chen et al. (ICML 2026),
  Lei et al. (NeurIPS 2026). The other venues listed on 2026-10-14 (Snell ICLR 2025, Yuan
  NeurIPS 2025, Atil Eval4NLP, Bjarnason ICLR 2026, Zhang ICML 2026) were not re-confirmed,
  so the paper cites those as arXiv preprints.
- Checked in the full text: HRBench evaluates 6 models on 5 benchmarks; Path-Lock reports
  2.54 vs 0.39 reflective tokens in Table 4 (the abstract's figure is 6.01 vs 0.35 on a
  different backbone); Thinking Inertia reports about 15 points lower accuracy on
  open-ended tasks; Atil et al. set temperature 0 on hosted APIs.
- Correction: Madur (2605.04488) uses provider APIs and a lexical heuristic, not LLM judges.
  The "LLM judges only" note above is wrong.
- DOI 10.1145/3772363.3799284 is CHI 2026 Extended Abstracts, same seven authors as arXiv
  2601.21339, different title. DOI 10.5281/zenodo.22245991 is the LA-P1 dataset and code.

### Literature search repeated, 2026-10-26

Two web searches for newer work crossing reasoning mode with model choice. None found that
does this on an open-ended task. Added after checking the arXiv records:

| Paper | Finding (from the abstract) | Use |
|---|---|---|
| Potamitis et al. ReasonBENCH: Benchmarking the (In)Stability of LLM Reasoning. arXiv 2512.07795 | 30 trials across 10 strategies, 12 models, 6 tasks; three-quarters of score variance from benchmark, system and item structure | Run-to-run variance |
| Zhao, Hooi and Ng. Test-Time Scaling in Reasoning Models Is Not Effective for Knowledge-Intensive Tasks Yet. arXiv 2509.06861, COLM 2026 per arXiv comment | 14 reasoning models; more test-time computation often adds hallucinations | H3 competing prediction |

Rejected: a search summary said ActuBench (arXiv 2604.20273) reports about 3.5 points
gained from reasoning mode across six provider pairs. Its text has no such comparison, so
it is not cited.

## Published versions, 2026-10-27

Checked with Semantic Scholar, then confirmed on Crossref (DOIs) or OpenReview (venue
records with author lists). The paper now cites these versions.

| arXiv | Published version | Checked on |
|---|---|---|
| 2505.24630 Li and Ng | NeurIPS 2025, Advances in NeurIPS 38, pp. 167712-167733, doi:10.52202/085713-5052 | Crossref |
| 2506.09501 Yuan et al. | NeurIPS 2025, Advances in NeurIPS 38, pp. 188045-188077, doi:10.52202/085713-5653 | Crossref |
| 2408.03314 Snell et al. | ICLR 2025 (oral), title "... than Scaling Parameters for Reasoning", forum 4FWAwZtd2n | OpenReview |
| 2508.05618 Chen et al. | ICML 2026, forum byZ7DoyDNd. The ICML record lists 7 authors; arXiv lists 8 (adds Jason Weston). Cited with the ICML list | OpenReview |
| 2509.06861 Zhao et al. | COLM 2026, forum pSt4QKgs1j | OpenReview |
| 2604.27201 S. Wang et al. | COLM 2026, forum vifGxn9AUq. The COLM record spells the second author "Van Yang"; arXiv and the CoRR record say "Wang Yang". Cited as "Wang Yang" | OpenReview |
| 2408.04667 Atil et al. | Eval4NLP 2025 workshop proceedings (ACL), pp. 135-148, doi:10.18653/v1/2025.eval4nlp-1.12, title "... System Settings in Hosted Environments" | Crossref |

Workshop only, cited as arXiv with a note: Bjarnason et al. (ICLR 2026 workshop AIWILD, not
the main conference as noted on 2026-10-14), Zhang et al. (ICML 2026 workshop AIWILD, not a
main-track position paper), Heyman and Zylberberg (NeurIPS 2025 workshop FoRLM), Potamitis
et al. (ICLR 2026 workshop P-AGI, 3 authors against 6 on arXiv). Lei et al.: accepted at
NeurIPS 2026 per the arXiv comment, conference not yet held. S. Wang et al. 2025
(2510.12680) was withdrawn from ICLR 2026. No published version found for HRBench, Thinking
Leakage, MARGO, Lau, Madur or Sahu et al.

## Second check, 2026-10-27 (Codex verification pass)

- 2510.12680 S. Wang et al. was published at EMNLP 2026, pp. 3491-3511
  (aclanthology.org/2026.emnlp-main.151, BibTeX checked: same seven authors). Now cited as
  EMNLP 2026; in the text it is S. Wang et al. 2026a and Path-Lock is 2026b.
- Path-Lock Expert: the arXiv PDF's author metadata (and XMP creator) give "Wang Yang";
  the COLM OpenReview record says "Van Yang". "Wang Yang" kept.

## Own prior work

- LA-P1, LLMs as Systems Architects (Cureus, under review; Zenodo DOI 10.5281/zenodo.22245991). Source of the prompt, rubric and the DeepSeek pilot.

## Links

- <https://arxiv.org/abs/2605.28398>
- <https://arxiv.org/abs/2510.12680>
- <https://arxiv.org/html/2609.28682v1>
- <https://arxiv.org/pdf/2604.27201>
- <https://arxiv.org/abs/2505.24630>
- <https://arxiv.org/pdf/2607.05861>
- <https://arxiv.org/abs/2508.05618>
- <https://arxiv.org/pdf/2505.12151>
- <https://arxiv.org/abs/2408.03314>
- <https://arxiv.org/pdf/2408.04667>
- <https://arxiv.org/html/2506.09501v2>
- <https://arxiv.org/pdf/2602.07150>
- <https://arxiv.org/pdf/2603.04417>
- <https://arxiv.org/abs/2601.21339>
- <https://doi.org/10.1145/3772363.3799284>
- <https://arxiv.org/abs/2605.04488>
- <https://arxiv.org/abs/2605.23950>
- <https://arxiv.org/abs/2610.11765>
- <https://arxiv.org/abs/2604.25506>
