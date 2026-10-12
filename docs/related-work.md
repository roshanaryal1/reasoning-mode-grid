# Related work

Collected 2026-10-02 by web search. Summaries come from abstracts and search
snippets. **Read each paper before citing it**, and check the arXiv version you cite.

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
| Reasoning Models Hallucinate More: Factuality-Aware Reinforcement Learning for Large Reasoning Models. arXiv 2505.24630 | Reasoning-oriented RL fine-tuning "significantly increases the prevalence of hallucinations" (abstract). Compares differently trained models, not reasoning switched on and off within one model. No "10 to 13 points" figure appears in the paper's text (checked 2026-10-12) | **Direct tension with H3.** H3 predicts tool factuality is mode-stable. This work suggests reasoning can lower factuality. Discuss either outcome |
| Mitigating Factual Hallucination in Large Reasoning Models via Mixed-Mode Advantage Regularization. arXiv 2607.05861 | Names "thinking-induced hallucination": thinking turns a correct direct answer into a wrong one | Same tension, mechanism-level |
| Learning to Reason for Factuality. arXiv 2508.05618 | Methods to reduce hallucination in reasoning models | Background |
| Reasoning LLM Errors Arise from Hallucinating Critical Problem Features. arXiv 2505.12151 | Errors come from hallucinated problem features | Background for D1 (misreading the hardware spec) |

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
| A Multi Model Study on the Inconsistency of LLM Judge. arXiv 2603.04417 | Why LLM raters need disclosure and a human rater |
| LA-P2, The Rater Is Stale (in preparation) | Why D3 and D4 need web verification |

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
