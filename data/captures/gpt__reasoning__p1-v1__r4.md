---
run_id: gpt__reasoning__p1-v1__r4
set: main
family: gpt
vendor: OpenAI
mode: reasoning
native_label: chatgpt.com, paid plan, GPT-5.6 Sol, Thinking effort High (rightmost)
channel: web
model_requested: OpenAI chat app, chatgpt.com, paid plan, GPT-5.6 Sol, Thinking effort
  High (rightmost)
model_returned: GPT-5.6 Sol (ChatGPT model picker, Thinking effort High)
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 4
date_stamped: '2026-10-14T12:41:16+00:00'
date_run: 2026-10-14T12:00:00+00:00/2026-10-14T12:20:00+00:00
date_note: >-
  Sent by hand on 15 Oct 2026 NZDT before the template was made; exact send time not recorded. The author reports the GPT runs were sent from 01:00 NZDT; the answer was on the clipboard by 01:40 NZDT after ChatGPT worked for 20 min 30 s, so it was sent by 01:20 NZDT.
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

GPT-6 | Knowledge cutoff: Not disclosed | Web browsing: Enabled | Research date: 15 October 2026

# Autonomous AI Workstation

Technical research and recommended architecture for an Apple M6 Mac mini with 32 GB unified memory

## Executive decision

Build a local-first autonomous agent system using Ollama, OpenCode, a durable Python/SQLite task supervisor, specialized research tools, and Tailscale for remote access.

Do not build a system where dozens of language models run independently. Build one where dozens or hundreds of agents exist as persistent tasks and configurations, while a small number of inference workers execute their work.

The central design principle is to separate four responsibilities:

1. Intelligence: deciding what should happen.
2. Execution: changing files, running code, and collecting information.
3. Supervision: controlling progress, failures, budgets, and approvals.
4. Verification: independently checking results before declaring completion.

This is a substantially more reliable architecture than a collection of autonomous chat sessions.

## Decisions at a glance

| Layer                           | Recommended choice                                           | Reason                                                          |
| ------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------------- |
| Hardware                        | Existing base M6, 32 GB                                      | Suitable for a focused single-machine agent system              |
| Local inference                 | Ollama with MLX and GGUF support                             | Native Apple Silicon acceleration, simple API, model management |
| Everyday model                  | Qwen3.5 9B                                                   | Practical memory footprint for frequent agent calls             |
| Complex reasoning and coding    | Qwen3.8 27B, quantized                                       | Stronger specialist, loaded when needed                         |
| Fast task routing               | Qwen3.5 4B                                                   | Lower-cost classification and extraction                        |
| Coding agent                    | OpenCode                                                     | Terminal execution, editing, Git, local models, subagents       |
| Research system                 | Python, Playwright, OpenAlex, Crossref, Docling              | Explicit source acquisition and verification                    |
| Orchestration                   | Custom lightweight Python supervisor                         | Control over jobs, permissions, concurrency, and recovery       |
| Task queue                      | SQLite with leases and checkpoints                           | Persistent without requiring a database server                  |
| Persistent knowledge            | Markdown, SQLite FTS5, Git                                   | Searchable, portable, inspectable                               |
| Browser automation              | Playwright                                                   | Programmatic browser control with isolated sessions             |
| Always-on services              | macOS launchd                                                | Native startup, restart, and process supervision                |
| Remote access                   | Tailscale and a private dashboard                            | Encrypted access without public ports                           |
| Security                        | Dedicated standard user, isolated workspaces, approval gates | Restricts the consequences of agent mistakes                    |
| Optional advanced orchestration | LangGraph or Temporal later                                  | Add only when workflow complexity justifies it                  |

Apple confirms that the 2026 base M6 Mac mini supports 32 GB unified memory, has a 12-core GPU, and provides 170 GB/s memory bandwidth in the 32 GB configuration. Ollama now supports MLX-based inference on Apple Silicon, while OpenCode supports local models, scripted execution, and configurable permissions.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://support.apple.com\&sz=32)

Apple Support

+3



The specified hardware is real and supported. However, I did not find a sufficiently independent, reproducible benchmark of this exact M6/32 GB configuration running the proposed full agent workload. Model performance comparisons below therefore distinguish documented capabilities from sizing estimates and choices that require benchmarking on your machine.

## Investigation 1. Local inference

### Recommended model strategy

Rather than installing every available model family, use a small set with clearly defined responsibilities.

| Model                    | Approx. downloaded model size            | Primary role                                       | Decision                                     |
| ------------------------ | ---------------------------------------- | -------------------------------------------------- | -------------------------------------------- |
| Qwen3.5 4B               | 3.3 to 4 GB                              | Task classification, extraction, simple formatting | Install                                      |
| Qwen3.5 9B               | 6.6 to 7.6 GB                            | Everyday planning, tool calls, summarization       | Install                                      |
| Qwen3.8 27B              | 18 GB                                    | Complex coding, debugging, demanding reasoning     | Install                                      |
| Qwen3 Embedding 0.6B     | 0.64 GB                                  | Semantic document search                           | Install when indexing begins                 |
| Gemma 4 12B              | 7.7 to 8 GB                              | Alternative everyday reasoning and multimodal work | Benchmark challenger                         |
| Gemma 4 26B MoE          | 16 to 19 GB                              | Alternative higher-quality reasoning               | Benchmark challenger                         |
| Qwen3-Coder 30B A3B      | 19 GB                                    | Specialized coding alternative                     | Evaluate if coding performance is inadequate |
| GPT-OSS 20B              | \~14 GB                                  | Reasoning and tool-use alternative                 | Optional                                     |
| Qwen3-Coder-Next 80B A3B | Much larger than practical memory budget | Advanced coding                                    | Do not deploy locally                        |

The published sizes come from Ollama's model registry. They are downloaded-weight sizes, not complete runtime RAM consumption.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://ollama.com\&sz=32)

ollama.com

+6



Qwen3.8 27B is a strong candidate for difficult tasks because its official model card reports substantial improvements in agentic coding and terminal tasks. However, the published benchmark scores predominantly represent the model creator's evaluations, not independent measurements on your Mac.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://huggingface.co\&sz=32)

Hugging Face



### Why Ollama is the initial choice

Ollama provides straightforward model downloading, a local API, native Apple Silicon support, automatic model unloading, configurable context lengths, and compatibility with coding agents.

The important alternatives are:

| Engine    | Advantage                                         | Limitation for this system                           |
| --------- | ------------------------------------------------- | ---------------------------------------------------- |
| Ollama    | Simplest reliable starting point                  | Concurrency and memory scheduling require tuning     |
| llama.cpp | Fine-grained GGUF, KV-cache and batching controls | More operational configuration                       |
| MLX-LM    | Direct access to Apple's MLX ecosystem            | Requires more integration work                       |
| vllm-mlx  | Continuous batching and caching features          | Newer infrastructure with greater integration risk   |
| LM Studio | Convenient interactive testing                    | Not my first choice for unattended infrastructure    |
| BaseRT    | Promising native Metal performance                | Less proven as the sole production inference service |

The 2026 Ollama MLX engine is especially relevant, although an open issue documents sequential request processing in its MLX path. That is another reason to control concurrency in the supervisor rather than assuming unlimited parallel inference.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://registry.ollama.com\&sz=32)

Ollama Blog

+3



My initial choice is Ollama, with llama.cpp as the reference implementation for performance comparisons and as a possible replacement if workload testing shows a material improvement.

## Investigation 2. Agent runtimes and harnesses

The best coding harness is not necessarily the best autonomous operating system.

OpenCode is my recommended default for coding because it supports unattended CLI execution, reusable agents, model selection, permissions, and repository tools. Pi is a very good alternative for a smaller, highly customizable harness, but its own security guidance stresses that model-generated commands run with the operating-system permissions of the invoking user unless separately isolated.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.opencode.ai\&sz=32)

OpenCode

+2



Other credible choices include OpenHands for container-isolated software engineering, Aider for Git-centred assisted development, Hermes Agent for persistent assistant workflows, and OpenClaw for gateways and scheduled personal-agent operations. I would avoid stacking all of them together. It creates overlapping permissions, memory systems, and schedulers.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub

+3



The autonomous supervisor should own the task lifecycle. OpenCode should be an execution worker, not the system's ultimate authority.

## Investigation 3. Multi-agent architecture

You can maintain 100 or more logical agents on this Mac because a logical agent is not a running model.

A logical agent consists of a role, instructions, tool permissions, memory references, objectives, and task state. Its definition can remain on disk until work needs to be performed.

# 100+

Logical agent definitions

# 2–4

Active tool/process workers

# 1

Large-model inference worker

Recommended initial limits, not measured maximum capacities.

A coding worker may be running unit tests while a research worker downloads papers and a document worker indexes files. These processes can operate simultaneously without requiring three simultaneous large-model generations.

The supervisor should schedule expensive model calls separately, prioritize interactive requests, and defer non-urgent generation until resources become available.

This architecture supports dynamic agents and delegation without overwhelming unified memory.

## Investigation 4. Autonomous coding agents

The coding agent must be capable of finishing a development task, not merely generating code.

Its operating cycle should be:

\#chatgpt-mermaid-\_r_o2\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_o2\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_o2\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_o2\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_o2\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_o2\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_o2\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_o2\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_o2\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_o2\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_o2\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_o2\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_o2\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_o2\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_o2\_ p{margin:0;}#chatgpt-mermaid-\_r_o2\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_o2\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_o2\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_o2\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_o2\_ .label text,#chatgpt-mermaid-\_r_o2\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_o2\_ .node rect,#chatgpt-mermaid-\_r_o2\_ .node circle,#chatgpt-mermaid-\_r_o2\_ .node ellipse,#chatgpt-mermaid-\_r_o2\_ .node polygon,#chatgpt-mermaid-\_r_o2\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_o2\_ .rough-node .label text,#chatgpt-mermaid-\_r_o2\_ .node .label text,#chatgpt-mermaid-\_r_o2\_ .image-shape .label,#chatgpt-mermaid-\_r_o2\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_o2\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_o2\_ .rough-node .label,#chatgpt-mermaid-\_r_o2\_ .node .label,#chatgpt-mermaid-\_r_o2\_ .image-shape .label,#chatgpt-mermaid-\_r_o2\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_o2\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_o2\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_o2\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_o2\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_o2\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_o2\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_o2\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_o2\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_o2\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_o2\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_o2\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_o2\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_o2\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_o2\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_o2\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_o2\_ .icon-shape,#chatgpt-mermaid-\_r_o2\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_o2\_ .icon-shape p,#chatgpt-mermaid-\_r_o2\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_o2\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_o2\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_o2\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_o2\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_o2\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_o2\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_o2\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_o2\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_o2\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_o2\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_o2\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_o2\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_o2\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_o2\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_o2\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_o2\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_o2\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_o2\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_o2\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_o2\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_o2\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_o2\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_o2\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_o2\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_o2\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_o2\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_o2\_ .node rect,#chatgpt-mermaid-\_r_o2\_ .node circle,#chatgpt-mermaid-\_r_o2\_ .node ellipse,#chatgpt-mermaid-\_r_o2\_ .node polygon,#chatgpt-mermaid-\_r_o2\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_o2\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_o2\_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_o2\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_o2\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_o2\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}Inspect repositoryPlan changeCreate worktreeEdit codeRun testsTests and checks pass?Diagnose and repairIndependent reviewCommit to task branchReport evidence and resultsNoYes

The supervisor must impose a maximum number of iterations and a time budget. Failure to pass tests should produce a recorded failure or a request for assistance, never a false completion report.

### Comparison

| Coding agent     | Strength                                                                                | Weakness                                                     | Verdict                             |
| ---------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ----------------------------------- |
| OpenCode V2      | Local-model integration, configurable agents, terminal tools, non-interactive execution | Needs careful permissions and model testing                  | Primary choice                      |
| OpenHands        | Isolated development environments and substantial coding workflows                      | More infrastructure overhead                                 | Best isolation-oriented alternative |
| Pi               | Lightweight, programmable, adaptable                                                    | Safety boundaries must be supplied externally                | Best minimal harness alternative    |
| Aider            | Mature Git-centred editing workflow                                                     | Less appropriate as the whole autonomous supervisor          | Useful fallback                     |
| Claude Code      | Strong commercial coding environment                                                    | Cloud dependency conflicts with local-first objective        | Optional escalation, not baseline   |
| Roo Code / Cline | Flexible IDE-centred tool use                                                           | IDE and session dependencies complicate unattended operation | Developer workstation alternative   |

These judgments concern architectural fit rather than a claim that one tool wins every coding benchmark. OpenCode's current CLI supports non-interactive `opencode run`, making it practical to invoke from a persistent task supervisor.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai\&sz=32)

OpenCode

+3



A critical detail: OpenCode V2 permissions use `permissions`, `shell`, and `subagent`. Older V1 examples use different field names. Copying a V1 policy into V2 could leave the actual security configuration weaker than intended.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai\&sz=32)

OpenCode



For your machine, run one model-intensive coding task at a time. Keep other agents working on downloads, test collection, indexing, and queued reviews.

## Investigation 5. Autonomous research

Research requires a different pipeline from software development.

The research system should first gather identifiable sources, then extract evidence, and only then ask an LLM to interpret the material.

\#chatgpt-mermaid-\_r_ob\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_ob\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_ob\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_ob\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_ob\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ob\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_ob\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_ob\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_ob\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_ob\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_ob\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_ob\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ob\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ob\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_ob\_ p{margin:0;}#chatgpt-mermaid-\_r_ob\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ob\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ob\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ob\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_ob\_ .label text,#chatgpt-mermaid-\_r_ob\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ob\_ .node rect,#chatgpt-mermaid-\_r_ob\_ .node circle,#chatgpt-mermaid-\_r_ob\_ .node ellipse,#chatgpt-mermaid-\_r_ob\_ .node polygon,#chatgpt-mermaid-\_r_ob\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_ob\_ .rough-node .label text,#chatgpt-mermaid-\_r_ob\_ .node .label text,#chatgpt-mermaid-\_r_ob\_ .image-shape .label,#chatgpt-mermaid-\_r_ob\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_ob\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_ob\_ .rough-node .label,#chatgpt-mermaid-\_r_ob\_ .node .label,#chatgpt-mermaid-\_r_ob\_ .image-shape .label,#chatgpt-mermaid-\_r_ob\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_ob\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_ob\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ob\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ob\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_ob\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_ob\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_ob\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_ob\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_ob\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_ob\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_ob\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ob\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ob\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_ob\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ob\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_ob\_ .icon-shape,#chatgpt-mermaid-\_r_ob\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_ob\_ .icon-shape p,#chatgpt-mermaid-\_r_ob\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_ob\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_ob\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_ob\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_ob\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_ob\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_ob\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_ob\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_ob\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_ob\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ob\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_ob\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_ob\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_ob\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ob\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_ob\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_ob\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ob\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_ob\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_ob\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ob\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_ob\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ob\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_ob\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_ob\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_ob\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_ob\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_ob\_ .node rect,#chatgpt-mermaid-\_r_ob\_ .node circle,#chatgpt-mermaid-\_r_ob\_ .node ellipse,#chatgpt-mermaid-\_r_ob\_ .node polygon,#chatgpt-mermaid-\_r_ob\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_ob\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_ob\_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_ob\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_ob\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ob\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}Research questionSearch planningOpenAlex / CrossrefWeb search and browserFetch original sourcesExtract text and metadataSource and claim ledgerFind corroboration andconflictsLLM synthesisDeterministic citation checksAll material claimssupported?Further research or qualifyclaimReport with sourcereferencesNoYes

### Recommended research tools

| Function                       | Preferred tool                                 | Alternative               |
| ------------------------------ | ---------------------------------------------- | ------------------------- |
| Scholarly discovery            | OpenAlex                                       | Semantic Scholar          |
| DOI and publication metadata   | Crossref                                       | Publisher metadata        |
| Interactive website navigation | Playwright                                     | Browser-use frameworks    |
| PDF structure extraction       | Docling                                        | GROBID or PyMuPDF         |
| Scholarly reference extraction | GROBID when necessary                          | Publisher reference lists |
| Web evidence acquisition       | Controlled Python requests and search services | Search APIs               |
| Text and metadata storage      | SQLite FTS5 and source files                   | PostgreSQL later          |
| Claim validation               | Deterministic source-ID and quotation checks   | Manual final audit        |

OpenAlex and Crossref provide structured academic metadata, while Docling supports document conversion and structured extraction. However, bibliographic metadata alone does not establish that a research paper's contents support a claim.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://help.openalex.org\&sz=32)

OpenAlex Help Center

+3



Each research finding should have:

- A source identifier, canonical URL or DOI, author, publication date, and retrieval timestamp.
- A locally saved source document or extracted passage with its content hash.
- The exact page, section, or text span relevant to the claim.
- A status such as verified, single-source, contradicted, or unsupported.
- An audit trail recording which agent extracted and checked it.

For peer-reviewed literature, additionally distinguish published papers, preprints, reviews, and unpublished claims.

No citation should reach the final report unless the cited source was actually retrieved and the reference can be resolved. The model should never be allowed to create source IDs or DOI references from memory alone.

## Investigation 6. Persistent memory

Use three complementary forms of memory rather than immediately installing a vector database and a knowledge graph.

| Memory type        | Storage                       | Contents                                            |
| ------------------ | ----------------------------- | --------------------------------------------------- |
| Project memory     | Markdown in Git               | Architecture, requirements, decisions, instructions |
| Operational memory | SQLite                        | Tasks, attempts, leases, costs, outcomes, approvals |
| Research memory    | SQLite FTS5 plus source files | References, evidence, claims, extracted content     |

An agent should retrieve relevant memory when starting a task and write a concise, structured summary when the task ends. Do not continuously append every model response to one enormous prompt.

My recommended database entities are `projects`, `tasks`, `task_dependencies`, `task_attempts`, `agents`, `artifacts`, `sources`, `claims`, `decisions`, `approvals`, and `events`.

SQLite FTS5 supports local full-text retrieval, and WAL mode supports practical concurrent readers while a writer updates the task database.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.sqlite.org\&sz=32)

sqlite.org

+1



Later, introduce local embeddings using the Qwen3 embedding model. Use SQLite-backed vector storage or a small embedded vector index first. Add a dedicated vector database only when indexing scale or query latency demonstrates a need. A knowledge graph should be reserved for relationship-heavy research where ordinary relational links are demonstrably insufficient.

## Investigation 7. Computer control and isolation

Grant the agent broad capability within an authorized environment, not broad authority over the entire personal computer.

Use a separate standard macOS account for AI execution, with no administrator privileges. Give it access only to registered project directories, isolated working copies, research downloads, and the specific applications it needs.

The preferred control hierarchy is:

1. Direct APIs and structured tools for deterministic work.
2. Git, terminal commands, and filesystem operations inside isolated workspaces.
3. Playwright for browser-based work, using dedicated browser profiles.
4. GUI automation only where no reliable programmatic interface exists.

Avoid granting general Accessibility, Screen Recording, Full Disk Access, personal browser access, or access to your primary macOS Keychain by default.

OpenCode itself explicitly warns that shell commands execute using the host user's authority and that its command-based directory detection is only best effort. Its permissions are an additional control, not an operating-system sandbox.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai\&sz=32)

OpenCode



For untrusted repositories or code obtained from the internet, execute tests inside a disposable VM/container with restricted network access. On Apple Silicon, do not plan to run the GPU inference server inside a generic macOS Docker container and assume Metal acceleration will remain available. Keep local inference on the host.

## Investigation 8. Always-on operation

Use `launchd` to maintain the model service, supervisor, and status interface. The supervisor should own all task state in SQLite, rather than treating an LLM conversation as the authoritative queue.

A durable task should move through:

`queued → leased → running → verifying → completed`

Additional states should include `blocked`, `awaiting_approval`, `retryable_failure`, `failed`, `cancelled`, and `recovery_review`.

For crash recovery:

- Each job gets a unique ID and a renewable execution lease.
- A supervisor restart inspects unfinished jobs.
- Expired jobs are checked for artifacts or external side effects before re-execution.
- Retry limits and backoff prevent endless loops.
- A job that might have sent a message, published content, or changed remote state is never blindly repeated.
- `launchd` restarts crashed services, while the task database determines what needs to resume.

Apple documents `KeepAlive`, `RunAtLoad`, and process arguments for launchd-managed jobs.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://developer.apple.com\&sz=32)

developer.apple.com



There is one important macOS limitation. A user-level LaunchAgent ordinarily requires its user session to become available. FileVault unlocking and automatic service recovery after an unattended power failure therefore need explicit testing. Do not assume installing a LaunchAgent means the whole system can operate immediately after every cold boot.

## Investigation 9. Remote access

Use Tailscale as the private transport between your phone, laptop, and Mac mini.

The remote interface should provide task submission, queue status, completion reports, logs, pending approvals, pause/resume, and an emergency stop. It should not directly expose a general terminal, the Ollama API, or OpenCode's execution interface through a public URL.

Tailscale Serve can expose a local HTTP application privately within your tailnet, and its background configuration can persist across normal client restarts. Tailscale Funnel, which exposes services publicly, is not appropriate here.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://tailscale.com\&sz=32)

Tailscale Docs



Start with SSH through Tailscale plus a read-only local status interface. Introduce authenticated write actions and approvals only after authentication and authorization are tested. Require an additional confirmation for actions capable of changing project state.

## Investigation 10. Storage design

Keep critical operational state on the internal SSD. Keep large, replaceable files on the external SSD.

| Internal SSD: 512 GB                | External SSD: 1 TB                      |
| ----------------------------------- | --------------------------------------- |
| macOS and development applications  | Downloaded models and quantizations     |
| Python supervisor and configuration | Git worktrees and cloned repositories   |
| SQLite queue and approval database  | Downloaded research papers              |
| Small metadata and search indexes   | Large document collections and datasets |
| Security policy files               | Embeddings and bulky indexes            |
| Essential logs and recovery records | Temporary experiment outputs            |
| Local monitoring services           | Regenerable model and processing caches |

Use an encrypted APFS external volume with a stable name such as `AI-Lab`. The supervisor must verify that it is mounted before accepting a job that depends on it.

Maintain free-space limits, periodically prune abandoned worktrees and caches, and back up the internal state database and irreplaceable research artifacts to a separate destination. The external working SSD is not itself a backup.

# Required architecture and implementation deliverables

## A. Recommended technology stack

| Layer                 | Recommended technology                                                         | Alternatives                    | Why                                                             |
| --------------------- | ------------------------------------------------------------------------------ | ------------------------------- | --------------------------------------------------------------- |
| Local model service   | Ollama                                                                         | llama.cpp, MLX-LM, vllm-mlx     | Simplest suitable operational baseline                          |
| Models                | Qwen3.5 9B, Qwen3.5 4B, Qwen3.8 27B                                            | Gemma 4, GPT-OSS, Qwen3-Coder   | Balance capability and memory                                   |
| Coding execution      | OpenCode V2                                                                    | Pi, OpenHands, Aider            | Scripted execution with local-model support                     |
| Central supervisor    | Python service                                                                 | LangGraph, Temporal             | Explicit control without excessive infrastructure               |
| Durable queue         | SQLite                                                                         | PostgreSQL, Redis-based queues  | Transactional, local, low maintenance                           |
| Browser and research  | Playwright, requests, OpenAlex, Crossref, Docling                              | GROBID, browser-use systems     | Traceable research and controlled browser operation             |
| Memory                | Markdown, Git, SQLite FTS5                                                     | Vector stores, knowledge graphs | Inspectable and straightforward to recover                      |
| Isolation             | Dedicated macOS user, registered directories, disposable VM for untrusted code | Docker, sandboxed containers    | Security without restricting trusted project work unnecessarily |
| Services              | launchd                                                                        | Supervisor scripts              | Native restart and startup management                           |
| Remote administration | Tailscale, SSH, private dashboard                                              | WireGuard, ZeroTier             | Private encrypted network                                       |
| Observability         | JSON logs, SQLite events, system metrics                                       | OpenTelemetry, Grafana          | Sufficient initially without another server stack               |

### Six-way market comparison

These are architecture judgments for their respective use cases. “Best overall” does not mean the best fit for your Mac.

| Category                  | Best overall at scale                                     | Best for 32 GB Mac           | Best open-source          | Lightest practical | Mature choice   | Most promising advanced option        | Actually use                    |
| ------------------------- | --------------------------------------------------------- | ---------------------------- | ------------------------- | ------------------ | --------------- | ------------------------------------- | ------------------------------- |
| Inference                 | vLLM on NVIDIA servers                                    | Ollama                       | llama.cpp                 | llama.cpp server   | llama.cpp       | vllm-mlx, BaseRT                      | Ollama                          |
| Agent harness             | OpenHands for isolated engineering                        | OpenCode                     | OpenCode / Pi             | Pi                 | Aider           | Newer OpenCode V2 agent features      | OpenCode                        |
| Multi-agent orchestration | Temporal for durable distributed workflows                | Python/SQLite                | LangGraph                 | Python queue       | Temporal        | Adaptive task and model scheduling    | Python/SQLite                   |
| Coding                    | Strong cloud coding agents for unrestricted model quality | OpenCode with local models   | OpenCode                  | Pi                 | Aider           | OpenHands-based isolated workers      | OpenCode                        |
| Research                  | Evidence-verified research pipeline                       | Local Python pipeline        | OpenAlex, Docling, GROBID | Python scripts     | Zotero / GROBID | Multi-stage claim-verification agents | Custom pipeline                 |
| Memory                    | PostgreSQL with hybrid indexing                           | SQLite FTS5                  | SQLite                    | Markdown files     | SQLite          | Graph-plus-vector retrieval           | SQLite and Git                  |
| Computer control          | Dedicated isolated execution environments                 | Standard user and Playwright | Playwright                | CLI subprocesses   | Playwright      | GUI agents in disposable VMs          | API/CLI first                   |
| Always-on service         | systemd in Linux environments                             | launchd                      | launchd / systemd         | launchd            | launchd         | Durable multi-host failover           | launchd                         |
| Remote access             | Private network plus authenticated application            | Tailscale                    | WireGuard                 | SSH                | Tailscale       | Fine-grained approval service         | Tailscale                       |
| Storage                   | Database and object storage separation                    | APFS, SQLite, Git            | SQLite and Git            | Filesystem         | SQLite          | Distributed artifact storage          | Internal state, external assets |

Temporal is more appropriate when execution must coordinate many hosts and long-lived business workflows. LangGraph is useful for checkpointed agent graphs. Neither solves the basic constraint of how much model inference fits into 32 GB of unified memory.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.temporal.io\&sz=32)

Temporal Documentation

+1



## B. Complete system architecture

Local autonomous AI environment

\#chatgpt-mermaid-\_r_ok\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_ok\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_ok\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_ok\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_ok\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ok\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_ok\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_ok\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_ok\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_ok\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_ok\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_ok\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ok\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ok\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_ok\_ p{margin:0;}#chatgpt-mermaid-\_r_ok\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ok\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ok\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ok\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_ok\_ .label text,#chatgpt-mermaid-\_r_ok\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ok\_ .node rect,#chatgpt-mermaid-\_r_ok\_ .node circle,#chatgpt-mermaid-\_r_ok\_ .node ellipse,#chatgpt-mermaid-\_r_ok\_ .node polygon,#chatgpt-mermaid-\_r_ok\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_ok\_ .rough-node .label text,#chatgpt-mermaid-\_r_ok\_ .node .label text,#chatgpt-mermaid-\_r_ok\_ .image-shape .label,#chatgpt-mermaid-\_r_ok\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_ok\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_ok\_ .rough-node .label,#chatgpt-mermaid-\_r_ok\_ .node .label,#chatgpt-mermaid-\_r_ok\_ .image-shape .label,#chatgpt-mermaid-\_r_ok\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_ok\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_ok\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ok\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ok\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_ok\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_ok\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_ok\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_ok\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_ok\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_ok\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_ok\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ok\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ok\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_ok\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ok\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_ok\_ .icon-shape,#chatgpt-mermaid-\_r_ok\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_ok\_ .icon-shape p,#chatgpt-mermaid-\_r_ok\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_ok\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_ok\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_ok\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_ok\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_ok\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_ok\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_ok\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_ok\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_ok\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ok\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_ok\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_ok\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_ok\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ok\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_ok\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_ok\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ok\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_ok\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_ok\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ok\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_ok\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ok\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_ok\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_ok\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_ok\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_ok\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_ok\_ .node rect,#chatgpt-mermaid-\_r_ok\_ .node circle,#chatgpt-mermaid-\_r_ok\_ .node ellipse,#chatgpt-mermaid-\_r_ok\_ .node polygon,#chatgpt-mermaid-\_r_ok\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_ok\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_ok\_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_ok\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_ok\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ok\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}Phone or laptopTailscale private networkAuthenticated control andapproval APISupervisor and policy brokerSchedules and triggersSQLite task queue andeventsPlanner and dependencyresolverResource scheduler andmodel routerCoding workerResearch workerDocument and data workerVerification workerOpenCode and Git worktreesPlaywright and research APIsParsers and PythonexperimentsTests and evidence validatorOllama on Apple MetalProject and artifact storageSQLite FTS5 and embeddingsAudit log and watchdog

The resource scheduler serializes expensive inference, while independent I/O and CPU jobs may run concurrently. External network access belongs to explicitly authorized research tools, not every agent.

### How the layers communicate

The supervisor creates a durable task record with its project, role, required capabilities, acceptance tests, limits, and dependencies. A worker takes a leased task and receives only the context and permissions required. Model requests go through a single scheduling point that checks available memory and loaded models.

The worker writes artifacts into a job-specific workspace and records evidence in the task database. A separate verifier evaluates the result. Only the verifier can promote a job from executed to successfully completed. The supervisor then releases any dependent tasks and optionally creates follow-ups within the approved objective.

This separation matters because an LLM's own statement that it has finished is not reliable proof of completion.

## C. Hardware and resource plan

### Estimated 32 GB unified-memory allocation

Engineering budgets, not measured memory usage on this exact M6 configuration.

| Resource                           | Normal 9B operation | Demanding 27B operation |
| ---------------------------------- | ------------------- | ----------------------- |
| macOS and essential services       | 4–6 GB              | 4–6 GB                  |
| Model weights                      | 6.6–7.6 GB          | About 18 GB             |
| KV cache and inference overhead    | 1.5–5 GB            | 1–4+ GB                 |
| Python, OpenCode, and task workers | 1–3 GB              | 1–3 GB                  |
| Browser or document tooling        | 1–3 GB              | 0–1.5 GB                |
| SQLite, indexes, monitoring        | 0.3–1 GB            | 0.3–1 GB                |
| Filesystem cache and safety margin | Remaining memory    | Very limited            |

The 9B configuration leaves useful operating headroom. The 27B configuration can approach or exceed available memory when context lengths and other processes grow. Its usable context window should therefore be substantially smaller than the model's advertised maximum.

Indicative active memory budgets

Illustrative configurations, not hardware benchmarks

9B configuration

27B configuration

0 GB5 GB10 GB15 GB20 GBOSModel weightsKV / runtimeWorkers / toolsDatabase / cache

In this illustration, everyday operation uses approximately 22 GB before variable additional workloads. Demanding operation uses approximately 31 GB and is therefore close to the practical limit.

### Initial inference settings

| Setting                       | Default                      | Reason                                       |
| ----------------------------- | ---------------------------- | -------------------------------------------- |
| Simultaneously loaded models  | 1                            | Prevents competing memory allocations        |
| Concurrent inference requests | 1                            | Predictable latency and memory use           |
| Everyday model context        | Test 32K, then 64K           | Coding harnesses benefit from longer context |
| 27B specialist context        | Begin 8K–16K; test 32K       | Preserve memory headroom                     |
| Quantization                  | Approximately 4-bit          | Best starting balance for memory             |
| Tool-only workers             | 2–4                          | Parallel downloads, tests, extraction        |
| Heavy browser instances       | 1                            | Browser RAM can compete with inference       |
| Model swapping                | Only between task batches    | Avoid repeated model loading                 |
| Persistent model              | 9B during routine work       | Eliminates unnecessary switches              |
| Embedding model               | Load during indexing batches | No need to keep resident continually         |

Ollama documents adjustable context lengths, model residence controls, parallel request settings, and methods for inspecting active memory allocation. Its registry lists model context capabilities, but these are not guarantees that every advertised context length is practical on 32 GB hardware.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.ollama.com\&sz=32)

Ollama

+2



The target is useful verified work per hour, not maximum tokens generated per second.

### Benchmark before changing defaults

Use 10 representative coding tasks, 10 research tasks, and 10 document-processing tasks. Measure successful verified tasks per hour, time spent loading models, context failures, memory pressure, swap usage, citation validity, and retry frequency.

Keep one fixed task set across the 9B, 27B, Gemma 4, and coding-specialist challengers. Test complete workflows, not isolated answers. Do not accept model-provider benchmark claims as a substitute for the results on this machine.

## D. Agent architecture: 100+ logical agents

A logical agent is a record with configuration and responsibility. It does not need a dedicated model process.

For example, the system can maintain 20 coding specialists, 20 research specialists, 20 verification specialists, 15 data-processing specialists, 15 documentation specialists, and 10 planning or operational specialists.

That produces 100 logical agents but does not require 100 concurrent model loads.

### Suggested logical agent specification

```

{
  "agent_id": "code-review-security",
  "role": "reviewer",
  "objective": "Review proposed changes for security defects",
  "model_tier": "everyday",
  "workspace_scope": ["project:example-app"],
  "allowed_tools": ["read", "grep", "git_diff"],
  "write_permission": false,
  "network_access": false,
  "max_duration_seconds": 900,
  "max_model_calls": 20,
  "requires_independent_verification": true
}

```

### Scheduling policies

An agent is selected because its capabilities match the task. A new agent definition can be generated dynamically from an approved template, but its permissions must be assigned by the policy broker, not invented by the model.

Use a priority queue with interactive, urgent, routine, and overnight work classes. Limit the number of tool-running workers separately from model-running workers. Use deadlines, backoff, and dependency checks to prevent a large batch from starving urgent jobs.

Avoid free-form swarms where agents continually create more agents without a budget or a stopping condition. Every generated subtask must belong to a parent objective and consume part of that objective's allocated resources.

## E. Model strategy and routing

Use a rule-based model router initially. It should consider task complexity, required context, current memory pressure, and whether the relevant model is already loaded. The language model can recommend an escalation, but the scheduler should make the final resource decision.

| Task                            | Default model        | Escalation                         |
| ------------------------------- | -------------------- | ---------------------------------- |
| Planning                        | Qwen3.5 9B           | Qwen3.8 27B                        |
| Routine coding                  | Qwen3.5 9B           | Qwen3.8 27B                        |
| Complex debugging               | Qwen3.8 27B          | Optional cloud model with approval |
| Repository review               | Qwen3.5 9B           | Qwen3.8 27B                        |
| Research question decomposition | Qwen3.5 9B           | Qwen3.8 27B                        |
| Source extraction               | Qwen3.5 4B           | Qwen3.5 9B                         |
| Summarization                   | Qwen3.5 9B           | Qwen3.8 27B                        |
| Classification                  | Qwen3.5 4B           | Qwen3.5 9B                         |
| Final research synthesis        | Qwen3.8 27B          | Optional cloud review              |
| Embeddings                      | Qwen3 Embedding 0.6B | None initially                     |

There is an operational qualification to this table. A task may be better handled by the already-loaded 9B model than by unloading it and loading the 4B model for one short classification request. Batch small tasks and group expensive 27B requests.

The 27B model should receive compact, retrieved context rather than an entire long-running agent history. The 9B model should handle workflows requiring a longer active context.

### Model escalation policy

```

START TASK
  |
  |-- Deterministic script can solve it?
  |       Use Python / SQL / Git, no LLM
  |
  |-- Small, independent text operation?
  |       Use 4B if already loaded or tasks are batched
  |
  |-- Normal agentic work?
  |       Use 9B
  |
  |-- Repeated failed verification or complex reasoning?
  |       Summarize verified state
  |       Unload current model
  |       Use 27B with compact context
  |
  |-- Local models still fail acceptance criteria?
          Mark blocked, or request approval for
          a cloud escalation with limited data

```

The system must remain useful without cloud inference. Optional paid models should be reserved for exceptionally difficult coding, advanced synthesis, or external review, and only after the user approves what information can leave the Mac.

No model should decide whether its own unsupported claim becomes verified.

## F. 24/7 architecture and recovery

The Mac needs three independently recoverable services:

| Service                        | Restart mechanism | Persistent state              |
| ------------------------------ | ----------------- | ----------------------------- |
| Ollama model server            | launchd           | Model weights on external SSD |
| Autonomous supervisor          | launchd           | SQLite on internal SSD        |
| Remote status and approval API | launchd           | SQLite and audit log          |

The supervisor operates on a repeated cycle:

`Check prerequisites → inspect queue → select eligible work → allocate resources → execute → verify → commit state → schedule follow-up`

### Operating limits

Set a maximum execution time per task, maximum retries, maximum repair iterations, maximum concurrent browser sessions, and maximum outstanding subtasks per parent objective. Treat repeated identical failures as a reason to stop rather than another opportunity to repeat the same command.

I would begin with a 45-minute limit for a coding attempt, three repair cycles within that limit, one heavy inference slot, and up to three additional I/O workers. These are policy defaults to tune, not demonstrated hardware limits.

A watchdog should check service responsiveness, disk space, external drive availability, and whether the task queue is making progress. If available memory drops sharply or swapping becomes sustained, stop admitting new model-intensive tasks.

### Cold boot and power failures

Keep FileVault enabled. Test the complete sequence of power restoration, disk unlocking, account login, external SSD mounting, Ollama startup, supervisor recovery, and Tailscale reconnection.

Apple documents remote FileVault unlocking capabilities on recent Apple Silicon macOS systems, but that does not establish that a Tailscale connection or all user LaunchAgents will be operational before login. Treat unattended cold-boot recovery as a specific acceptance test, not an assumption.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://support.apple.com\&sz=32)

Apple Support

+1



Use Ethernet where practical and a UPS if uninterrupted overnight operation is important. Configure the Mac to avoid automatic system sleep while work is active, while allowing the display to sleep normally. Schedule operating-system updates rather than allowing an update to interrupt a long-running experiment without warning.

## G. Remote-control architecture

\#chatgpt-mermaid-\_r_pg\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_pg\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_pg\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_pg\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_pg\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_pg\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_pg\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_pg\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_pg\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_pg\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_pg\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_pg\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_pg\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_pg\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_pg\_ p{margin:0;}#chatgpt-mermaid-\_r_pg\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_pg\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_pg\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_pg\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_pg\_ .label text,#chatgpt-mermaid-\_r_pg\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_pg\_ .node rect,#chatgpt-mermaid-\_r_pg\_ .node circle,#chatgpt-mermaid-\_r_pg\_ .node ellipse,#chatgpt-mermaid-\_r_pg\_ .node polygon,#chatgpt-mermaid-\_r_pg\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_pg\_ .rough-node .label text,#chatgpt-mermaid-\_r_pg\_ .node .label text,#chatgpt-mermaid-\_r_pg\_ .image-shape .label,#chatgpt-mermaid-\_r_pg\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_pg\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_pg\_ .rough-node .label,#chatgpt-mermaid-\_r_pg\_ .node .label,#chatgpt-mermaid-\_r_pg\_ .image-shape .label,#chatgpt-mermaid-\_r_pg\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_pg\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_pg\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_pg\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_pg\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_pg\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_pg\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_pg\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_pg\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_pg\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_pg\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_pg\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_pg\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_pg\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_pg\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_pg\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_pg\_ .icon-shape,#chatgpt-mermaid-\_r_pg\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_pg\_ .icon-shape p,#chatgpt-mermaid-\_r_pg\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_pg\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_pg\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_pg\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_pg\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_pg\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_pg\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_pg\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_pg\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_pg\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_pg\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_pg\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_pg\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_pg\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_pg\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_pg\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_pg\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_pg\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_pg\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_pg\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_pg\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_pg\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_pg\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_pg\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_pg\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_pg\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_pg\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_pg\_ .node rect,#chatgpt-mermaid-\_r_pg\_ .node circle,#chatgpt-mermaid-\_r_pg\_ .node ellipse,#chatgpt-mermaid-\_r_pg\_ .node polygon,#chatgpt-mermaid-\_r_pg\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_pg\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_pg\_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_pg\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_pg\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_pg\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}Phone or remote laptopTailscalePrivate authenticatedinterfaceQueue and statusLogs and artifactsApproval requestsPause and emergency stopSupervisor

Use three levels of remote functionality.

| Level       | Capability                                                            | Authentication requirement                      |
| ----------- | --------------------------------------------------------------------- | ----------------------------------------------- |
| Read-only   | Check progress, logs, reports, metrics                                | Tailnet identity plus application access policy |
| Operational | Submit, pause, resume, reorder tasks                                  | Authenticated account with action authorization |
| Privileged  | Approve external side effects, change permissions, emergency shutdown | Strong reauthentication and audit record        |

For first deployment, SSH through the private tailnet is enough:

```
ssh agent@your-mac-tailnet-name
python3 ~/ai-lab/bin/labctl.py status
```

When an authenticated dashboard exists and is tested locally, bind it only to `127.0.0.1`, then publish it privately:

```
tailscale serve --bg http://127.0.0.1:8787
tailscale serve status
```

This command should only be run after the local dashboard exists. Tailscale's documented Serve functionality is private to the tailnet, unlike public Funnel exposure.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://tailscale.com\&sz=32)

Tailscale Docs



Do not expose a raw shell execution endpoint through the dashboard. Approvals should be narrowly scoped to a particular task and operation.

## H. Security architecture

The security design should assume that an autonomous model will eventually produce an incorrect command, misunderstand a document, or encounter malicious instructions in retrieved content.

### Approval boundaries

| Operation                                                             | Default treatment                           |
| --------------------------------------------------------------------- | ------------------------------------------- |
| Read an approved project                                              | Autonomous                                  |
| Search local indexed documents                                        | Autonomous                                  |
| Read public websites through research tools                           | Autonomous, with network limits             |
| Edit files in a disposable worktree                                   | Autonomous                                  |
| Create a task branch                                                  | Autonomous within a registered repository   |
| Run approved tests on trusted code                                    | Autonomous inside the permitted environment |
| Create internal documentation                                         | Autonomous                                  |
| Commit to a disposable task branch                                    | Autonomous after verification               |
| Push to remote repository                                             | Approval                                    |
| Merge into protected branches                                         | Approval                                    |
| Delete substantial project data                                       | Approval                                    |
| Modify files outside registered workspaces                            | Approval and explicit access grant          |
| Read private credentials or personal financial files                  | Denied by default                           |
| Send emails, post content, publish research, or contact third parties | Approval                                    |
| Spend money, purchase services, or change financial accounts          | Approval                                    |
| Install system software or change macOS security settings             | Administrator action                        |
| Use unrestricted GUI computer control                                 | Denied by default                           |
| Access personal browser sessions or password manager                  | Denied by default                           |

### Five security mechanisms that must be independent

Operating-system isolation. The execution user should be a dedicated standard account. Sensitive personal files should not be made accessible to that account. Repository permissions and OpenCode configuration are not substitutes for actual filesystem isolation.

Tool permissions. Maintain distinct policies for planner, coder, researcher, document processor, and verifier. The verifier normally receives read-only access. A planner should not automatically inherit terminal execution rights.

Secrets management. A privileged, non-LLM component should retrieve narrowly scoped credentials when approved. Never place long-lived passwords or API tokens directly into agent prompts, logs, or repository configuration. Consider short-lived tokens and per-service credentials.

Side-effect control. Use operation identifiers and an approval record for every external action. Never automatically replay a potentially successful email, payment, remote write, or publication after a crash.

Audit and containment. Record the task ID, selected model, tool invocation, working directory, policy decision, timestamps, exit status, and artifact hashes. Restrict log access and redact secrets. Keep a tested emergency-stop mechanism independent of the model.

For security testing, include prompt-injection attempts embedded in README files, web pages, PDFs, and tool output. They must not be able to override task policy or approve an external action.

## I. Exact installation and implementation plan

I have prepared an executable reference starter containing a Python/SQLite task supervisor, a conservative OpenCode V2 policy, macOS LaunchAgent generation, external-drive startup checking, and installation instructions.

Download the Autonomous AI Lab Starter ZIP

Includes labctl.py, serve_ollama.py, install_launchd.py, opencode.jsonc, and README.md.

The Python files were syntax checked. The SQLite queue, workspace registration, execution lifecycle, and emergency-control commands passed a local smoke test using a simulated OpenCode executable. I have not run the complete system on an M6 Mac.

This package is a foundation, not a finished production autonomous system. It does not yet implement verified multi-agent delegation, independent artifact verification, research citation enforcement, or a remote approval dashboard.

### Phase 1. Establish local inference and the task queue

Create a separate non-administrator `agent` user in macOS. Use an administrator account to install trusted shared development tools, then carry out agent operations under the isolated account.

Check hardware:

```

uname -m
sysctl -n hw.memsize
system_profiler SPHardwareDataType
diskutil info /Volumes/AI-Lab

```

Install Apple's command-line development tools where necessary:

```
xcode-select --install
```

Using a trusted Homebrew installation:

```
brew install ollama opencode python git ripgrep jq uv
```

Prepare the directories:

```
mkdir -p ~/ai-lab/{state,logs,bin}
mkdir -p /Volumes/AI-Lab/{models,projects,worktrees,papers,datasets,cache}
```

Start a single model server in a terminal for the first test:

```

OLLAMA_HOST=127.0.0.1:11434 \
OLLAMA_MODELS=/Volumes/AI-Lab/models \
OLLAMA_NO_CLOUD=1 \
OLLAMA_MAX_LOADED_MODELS=1 \
OLLAMA_NUM_PARALLEL=1 \
OLLAMA_CONTEXT_LENGTH=65536 \
ollama serve

```

In another terminal:

```

ollama pull qwen3.5:9b
ollama pull qwen3.5:4b
ollama pull qwen3.8:27b
ollama pull qwen3-embedding:0.6b

ollama list
ollama ps

```

Ollama now provides MLX-based options alongside other supported model formats. Test the actual model/backend selected rather than assuming one format will always be faster.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://registry.ollama.com\&sz=32)

Ollama Blog

+2



OpenCode V2 discovers a local Ollama server automatically. Its model names use the `ollama/model-name` format.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai\&sz=32)

OpenCode



Unpack the starter ZIP and follow its README for installing the policy, registering one test workspace, and submitting the first job.

The acceptance test is simple: a submitted job must receive an ID, appear in the durable queue, run in the approved directory, write its output to a log, and preserve its result after the supervisor restarts.

Rollback: Stop the test process, restore the previous OpenCode configuration if one existed, and leave project files unchanged. Do not delete the task database until it has been inspected.

### Phases 2–8. Build the complete operating environment

| Phase                        | Exact technologies and work                                       | Required test                                                                   | Common failure                            | Rollback                                                     |
| ---------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------ |
| 2. Autonomous coding         | OpenCode V2, Git worktrees, test runner, task verifier            | Make a change, fail a test, repair it, pass tests and produce a reviewable diff | Model loops or changes unrelated files    | Stop task and discard its disposable worktree                |
| 3. Research agents           | Python requests, Playwright, OpenAlex, Crossref, Docling          | Produce a report whose references resolve to stored evidence                    | Missing pages or fabricated references    | Mark claims unsupported and regenerate from verified sources |
| 4. Persistent memory         | SQLite FTS5, Markdown, Git, embedding index                       | Stop and restart, then retrieve earlier decisions accurately                    | Stale or incorrect memory retrieval       | Rebuild index from versioned source records                  |
| 5. Multi-agent orchestration | Dependency-aware SQLite queue, role registry, inference semaphore | Run 100 logical agents with only the configured number of active workers        | Worker starvation or recursive delegation | Freeze new tasks and restore scheduler settings              |
| 6. Always-on operation       | launchd, checkpoints, resource watchdog                           | Restart supervisor during work and recover safely                               | Duplicate side effects or stalled work    | Disable LaunchAgents, inspect recovery state                 |
| 7. Remote access             | Tailscale, SSH, authenticated FastAPI control interface           | Submit and stop a task from a phone on another network                          | Authentication or authorization mistake   | Disable Serve and remote write endpoints                     |
| 8. Optimization              | Task benchmarks, KV tuning, context management, model routing     | Higher verified throughput without excessive swap                               | Large-model memory pressure               | Revert context and concurrency settings                      |

For the research phase, install the Python components in a dedicated virtual environment:

```
python3 -m venv ~/ai-lab/venv
source ~/ai-lab/venv/bin/activate

python -m pip install requests playwright docling pymupdf
python -m playwright install chromium
```

Docling can have significant dependencies and document-processing overhead. Run extraction as a bounded worker rather than loading its entire processing environment permanently beside a large model.

For a later dashboard:

```
source ~/ai-lab/venv/bin/activate
python -m pip install fastapi uvicorn
```

Start it locally only after implementing authentication, authorization, and read-only endpoints:

```
uvicorn dashboard:app --host 127.0.0.1 --port 8787
```

Here `dashboard:app` is the application you must implement during Phase 7. It is not included in the starter ZIP.

### Production queue requirements beyond the starter

Before switching on unsupervised overnight execution, extend the starter to support independent verification, dependency graphs, approved dynamic agent creation, idempotent side effects, a real model routing service, and a security policy that repository-local configuration cannot override.

OpenCode V2 supports managed machine policies. For untrusted repositories, have an administrator enforce tool restrictions at that level and execute the repository inside a separate sandbox. The starter's user-level OpenCode policy is intentionally not presented as sufficient isolation for hostile code.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai\&sz=32)

OpenCode

+1



### Acceptance tests before overnight autonomy

1. A 60-minute unattended coding task produces a verified change or a recorded failure, without falsely declaring success.
2. Ten concurrent queued tasks cause no more than one large-model generation at a time.
3. A forced supervisor crash does not erase queued work or blindly repeat side effects.
4. Disconnecting the external SSD stops affected work and does not corrupt the internal task queue.
5. An injected instruction inside a web page cannot trigger a prohibited command.
6. A report with an invented citation is rejected before release.
7. An emergency stop from the remote interface terminates active work.
8. A complete cold reboot and login restores the intended services.
9. Backups can restore the queue, project metadata, and research source ledger.
10. An entire overnight session respects its time, memory, disk, and task-generation budgets.

All ten should pass before calling the system production-ready.

## J. What not to install initially

| Technology or approach                               | Why to avoid it now                                          | When to reconsider                                    |
| ---------------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------- |
| Kubernetes                                           | Large administrative burden for one Mac                      | Multiple execution hosts                              |
| Redis and Celery                                     | Additional running services when SQLite can handle the queue | Distributed workers and higher scheduling load        |
| PostgreSQL and pgvector                              | Unnecessary for the first local project database             | Large indexes and concurrent multi-host writes        |
| A dedicated vector database plus knowledge graph     | Duplicated indexing and operational complexity               | Demonstrated retrieval deficiencies                   |
| Temporal and LangGraph together                      | Overlapping workflow abstractions                            | Specific complex workflow requirements                |
| Multiple overlapping agent gateways                  | Conflicting schedulers, permissions, and memories            | One clearly identified missing capability             |
| Large 70B+ models on this 32 GB Mac                  | Memory pressure and poor practical throughput                | Larger-memory host or dedicated accelerator           |
| Several permanently loaded local models              | Wasted unified memory                                        | Proven benefit under profiling                        |
| Docker-hosted Ollama expecting Mac GPU passthrough   | Wrong assumption about macOS container GPU access            | Separate GPU server                                   |
| Unrestricted GUI automation                          | Exposes unrelated personal applications and data             | Isolated GUI session or VM with defined permissions   |
| Automated installation scripts from unknown websites | High-risk privilege escalation path                          | Manual review, checksum and trusted source validation |
| Large, unrestricted subagent swarms                  | Unbounded work generation and repeated model calls           | Scheduler-enforced limits and proven throughput       |

OpenClaw, Hermes Agent, Pi, and OpenHands may still be useful, but I would evaluate them individually against a defined missing capability rather than operating them all as competing autonomous supervisors.

## K. Future upgrade path

| Available memory or hardware | Recommended changes                                                                                 | Practical benefit                                                 |
| ---------------------------- | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| 32 GB now                    | One active 9B model or one constrained 27B model                                                    | Reliable local-first starting point                               |
| 64 GB unified memory         | Keep a medium model resident with more context and larger caches                                    | Fewer model switches and better multitasking                      |
| 96 GB unified memory         | Evaluate a larger reasoning model and a smaller simultaneous worker                                 | Better complex-task throughput                                    |
| 128 GB+ unified memory       | Test high-quality 70B-class quantized models with substantial context                               | Stronger local reasoning and synthesis                            |
| Dedicated NVIDIA GPU machine | Move large-model inference to a private network service using vLLM or another CUDA-optimized engine | Higher concurrency and separation of inference from Mac workloads |
| Multiple execution computers | Add distributed task workers and durable orchestration                                              | Parallel execution across hosts                                   |

Treat these as architectural upgrade opportunities, not precise capacity guarantees. Larger context windows can consume substantial memory even when model weights fit.

### Storage growth plan

For the existing 1 TB external SSD, begin with this flexible allocation:

| Category                        | Initial space budget |
| ------------------------------- | -------------------- |
| Downloaded model variants       | 100–150 GB           |
| Git repositories and worktrees  | 150–200 GB           |
| Research papers and documents   | 150–200 GB           |
| Datasets and experiments        | 150–200 GB           |
| Embeddings and derived indexes  | 50–100 GB            |
| Caches and temporary processing | 50–100 GB            |
| Free-space reserve              | At least 100 GB      |

These are planning budgets, not expected initial consumption. Avoid filling every allocation at the outset. Set automated cleanup for regenerable caches, but require approval before removing original source data or Git branches containing unmerged work.

### Expected costs

The core stack uses locally executable tools and models and does not require a paid model API. Remaining costs include electricity, storage and backup hardware, and any optional paid research services.

Research involving the public internet is not fully offline. OpenAlex provides an initial free API allowance, with higher usage subject to its published pricing and limits.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://help.openalex.org\&sz=32)

OpenAlex Help Center

&#x20;Search providers, publisher access, and some academic resources may also involve usage restrictions or fees.



The system should distinguish local data processing from external retrieval and record network destinations and paid API consumption.

## Final recommendation

For this Mac, the highest-value first milestone is not 100 agents. It is one autonomous coding worker and one research worker that reliably recover from crashes, preserve evidence, respect permissions, and report verified outcomes.

Once that is working, adding 100 logical agents is mainly a matter of task definitions, resource scheduling, and dependency management. The hardware constraint remains the number of active large-model generations, not the number of registered agents.

The proposed architecture is feasible for substantial unattended work. Its limitation is that a 32 GB local workstation cannot be expected to match the reasoning quality, throughput, and long-context performance of large cloud models on every difficult task. Reliable tool use, bounded execution, source verification, and selective escalation matter more than the nominal number of autonomous agents.

## Sources

The following are the principal references used in the assessment. Primary means official documentation, a project's source repository, or the model creator's material. Creator-published benchmarks are primary-source claims, not independent validation.

| Source                                                                                                                                                           | Type                        |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| [Apple Mac mini M6 technical specifications](https://support.apple.com/en-mide/128108)                                                                           | Primary                     |
| [Ollama MLX performance announcement](https://registry.ollama.com/blog/mlx-performance)                                                                          | Primary, vendor benchmark   |
| [Ollama configuration and memory FAQ](https://docs.ollama.com/faq)                                                                                               | Primary                     |
| [Qwen3.5 model registry and model variants](https://ollama.com/library/qwen3.5)                                                                                  | Primary                     |
| [Qwen3.8 27B model registry](https://ollama.com/library/qwen3.8)                                                                                                 | Primary                     |
| [Qwen3.8 official model card](https://huggingface.co/Qwen/Qwen3.8-27B?chat_template=default)                                                                     | Primary, creator benchmarks |
| [OpenCode V2 CLI documentation](https://opencode.ai/v2/docs/cli)                                                                                                 | Primary                     |
| [OpenCode V2 Ollama integration](https://opencode.ai/v2/docs/providers)                                                                                          | Primary                     |
| [OpenCode V2 permissions and security boundaries](https://opencode.ai/v2/docs/permissions)                                                                       | Primary                     |
| [OpenCode V2 configuration](https://opencode.ai/v2/docs/config)                                                                                                  | Primary                     |
|                                                                                                                                                                  | Primary                     |
|                                                                                                                                                                  | Primary                     |
| [LangGraph persistence documentation](https://docs.langchain.com/oss/python/langgraph/persistence)                                                               | Primary                     |
| [Temporal self-hosting documentation](https://docs.temporal.io/self-hosted-guide)                                                                                | Primary                     |
| [OpenAlex API documentation](https://help.openalex.org/api/)                                                                                                     | Primary                     |
|                                                                                                                                                                  | Primary                     |
|                                                                                                                                                                  | Primary                     |
|                                                                                                                                                                  | Primary                     |
| [Playwright Python documentation](https://github.com/microsoft/playwright/blob/main/docs/src/library-python.md)                                                  | Primary                     |
| [SQLite FTS5 documentation](https://www.sqlite.org/fts5.html)                                                                                                    | Primary                     |
| [SQLite WAL documentation](https://www.sqlite.org/wal.html)                                                                                                      | Primary                     |
| [Apple launchd job configuration](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html) | Primary                     |
| [Tailscale Serve CLI documentation](https://tailscale.com/docs/reference/tailscale-cli/serve)                                                                    | Primary                     |
| [Apple macOS Tahoe enterprise security changes](https://support.apple.com/en-us/124963)                                                                          | Primary                     |

The key uncertainties remaining are actual sustained M6 inference throughput, KV-cache memory consumption for each candidate model at your chosen context length, local-model success rates on your real repositories, and unattended restart behaviour with your FileVault and external SSD configuration. Those require direct testing on the target workstation before the system is trusted with extended autonomous operation.

## Reasoning trace (not shown to raters)

Worked for 20m 30s
I’ll verify the Mac mini hardware assumptions first, then compare local models, inference engines, agent runtimes, security controls, and 24/7 operations. I’ll use the current date, 15 October 2026, for the research and separate verified capabilities from performance estimates.

Compared model options


Searched 14 websites

Apple’s specifications confirm that the base M6 Mac mini supports 32 GB unified memory. The main design constraint is not storage or the number of agent definitions. It is how many active model contexts fit in memory without slowing the machine through swapping. I’m comparing a smaller always-available model with a larger model loaded for demanding tasks.

Structured the recommendation

Designed and handled local deployment setup

Compared deployment paths


Searched 58 websites

A security finding changes the implementation plan: OpenCode V2 uses a different permissions format from V1, and its default permissions are too broad for an unattended agent. I’m basing the configuration on the current V2 documentation and placing operating-system isolation around the coding worker, rather than relying on prompt instructions to protect files.

Built the starter kit

Created autonomous AI lab controller script


Searched 2 websites

Strengthened the local design

Fixed Kit scripts, tested workflows, and updated configuration files

Finalized and consolidated the complete architecture design

Finalized local autonomy


Searched 8 websites

Hardened the Autonomous AI Lab Starter Kit

GPT-6 | Knowledge cutoff: Not disclosed | Web browsing: Enabled | Research date: 15 October 2026

## Run notes

chatgpt.com, paid plan, new chat, GPT-5.6 Sol, Thinking effort High, as set in the pre-registration;
confirmed by the author. Run by the author by hand. Answer copied with ChatGPT's copy button and written
verbatim from the clipboard; the copy includes ChatGPT's citation and favicon links and diagram markup as
the app produced them. ChatGPT worked for 20 min 30 s. ChatGPT searched the web by itself (live citations; research date given as 15 October 2026, not the prompt's 31 August 2026) and produced a downloadable starter ZIP. The answer names itself "GPT-6"; the model picker showed GPT-5.6 Sol, so this is recorded as a model self-report error. Reasoning trace: ChatGPT's "Worked for 20m 30s" activity panel, copied by the author from the
page and pasted into the operator chat; it ends with the answer's first line, kept as copied.
