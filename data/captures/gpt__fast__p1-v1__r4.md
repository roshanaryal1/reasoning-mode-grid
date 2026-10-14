---
run_id: gpt__fast__p1-v1__r4
set: main
family: gpt
vendor: OpenAI
mode: fast
native_label: chatgpt.com, paid plan, GPT-5.6 Sol, Thinking effort Instant (leftmost)
channel: web
model_requested: OpenAI chat app, chatgpt.com, paid plan, GPT-5.6 Sol, Thinking effort
  Instant (leftmost)
model_returned: GPT-5.6 Sol (ChatGPT model picker, Thinking effort Instant)
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 4
date_stamped: '2026-10-14T12:51:40+00:00'
date_run: 2026-10-14T12:00:00+00:00/2026-10-14T12:51:00+00:00
date_note: >-
  Sent by hand on 15 Oct 2026 NZDT before the template was made; exact send time not recorded. Interval: 01:00 NZDT (author: GPT runs sent from 01:00) to 01:51 NZDT (answer on the clipboard; template made).
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

GPT-6 | OpenAI | Knowledge cutoff: not disclosed | Web browsing: enabled | Research date: 15 October 2026, with the requested 31 August 2026 historical cutoff distinguished where possible.

# Autonomous Local AI Workstation: Architecture and Build Specification

Your proposed system should be built as a persistent, queue-driven AI execution platform, not as a chatbot with an extended prompt.

The central architectural decision is to separate task management, model inference, tool execution, security and persistent memory. This allows the workstation to continue operating even when an individual model, coding agent or research worker fails.

For your Mac mini with 32 GB unified memory, I recommend one primary inference worker, a durable task queue, independently supervised agent processes and a strict approval system for sensitive operations.

## Decisions at a glance

| Layer                 | Recommended starting technology                                               |
| --------------------- | ----------------------------------------------------------------------------- |
| Local inference       | llama.cpp with Metal acceleration                                             |
| Alternative inference | MLX-LM                                                                        |
| Coding agent          | Aider, with OpenHands evaluated separately                                    |
| Agent orchestration   | LangGraph with durable checkpoints                                            |
| Task queue            | SQLite-backed queue                                                           |
| Research              | Python tools, Playwright, scholarly APIs                                      |
| Persistent memory     | SQLite, Markdown and SQLite FTS5                                              |
| Semantic retrieval    | Local embeddings, added after baseline testing                                |
| Background operation  | macOS launchd                                                                 |
| Remote access         | Tailscale and SSH                                                             |
| Security              | Dedicated macOS user, isolated workspaces, restricted tools                   |
| Storage               | Internal SSD for operating services, external SSD for models and working data |
| Monitoring            | Structured JSON logs, task history and a local dashboard                      |

These are the proposed baseline choices. The current research must still determine which model checkpoints and software versions are best, and whether newer agent systems outperform this stack.

## 1. Local inference

The main limitation is memory bandwidth and usable unified memory, not simply whether a model's weights fit on the machine.

Compare three inference engines:

| Engine    | Strength                                                         | Limitation                                       | Decision                   |
| --------- | ---------------------------------------------------------------- | ------------------------------------------------ | -------------------------- |
| llama.cpp | GGUF quantization, Metal, server deployment, broad model support | Requires careful tuning                          | Primary                    |
| MLX-LM    | Native Apple Silicon framework, efficient model experimentation  | Different model packaging and serving workflows  | Benchmark alternative      |
| Ollama    | Simple installation and model management                         | Less direct control over some inference settings | Easiest initial deployment |

llama.cpp explicitly supports Apple Silicon and Metal. Apple's MLX framework is designed around unified memory. Both deserve direct testing on the actual machine.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub

+1



### Recommended model sizes

Use 4-bit quantization initially.

| Model class   | Approximate weight memory | Role                                    |
| ------------- | ------------------------- | --------------------------------------- |
| 3B–4B dense   | 2–3 GB                    | Classification, routing                 |
| 7B–9B dense   | 4–6 GB                    | General tasks, summaries                |
| 14B dense     | 8–10 GB                   | Coding, research synthesis              |
| 20B–24B dense | 12–16 GB                  | Complex tasks, subject to benchmarking  |
| 30B–35B       | 18–23 GB                  | Experimental, not the always-on default |

These estimates cover quantized weights, not total runtime memory. KV cache, model architecture and context length can substantially increase consumption.

OpenHands' documentation identifies Qwen3.6-35B-A3B as a local agentic coding candidate. It is worth evaluating, but its suitability for continuous operation on 32 GB remains unproven without actual memory and throughput measurements.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



My starting configuration would be a capable 14B-class model at 4-bit quantization, with 16K context. Test 32K context only after measuring memory pressure and task completion rates.

## 2. Agent runtimes and harnesses

LangGraph is the strongest initial orchestration candidate because it supports persisted execution state, checkpoints, interrupts and recovery. Its checkpointing and long-term stores are distinct components.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://langchain-ai.github.io\&sz=32)

Docs by LangChain

+1



However, LangGraph is not a complete autonomous workstation. You still need a task scheduler, tool permissions, worker management, resource accounting and a remote interface.

My choice is LangGraph for individual workflows, with a small Python supervisor around it. Avoid building a large custom agent framework before demonstrating one reliable end-to-end workflow.

## 3. Multi-agent architecture

The correct design is 100 or more logical agents sharing a very small inference pool.

An agent is a persistent definition containing its role, objectives, tools, permissions, memory namespace and execution state. It does not require a permanently loaded model.

Initially permit one large-model generation at a time. Parallelize network fetching, deterministic tests, file indexing and other non-LLM work.

Use queue priorities, per-task budgets, leases, heartbeat renewal and a maximum retry count. Each task should have a unique identifier and an idempotency policy.

## 4. Coding agents

Aider is a reasonable first choice because it works with local models and integrates code editing with Git. Its documentation specifically warns that insufficient context allocation can cause local models to lose important input.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



OpenHands offers a more integrated agent environment and supports local inference endpoints, but may impose greater resource and operational overhead.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



Start with Aider operating in disposable Git worktrees. The supervisor should run tests, collect diffs and decide whether another iteration is justified. Never let an autonomous agent merge into the protected main branch without approval.

## 5. Research agents

Build research around a verifiable evidence store rather than relying on the model to remember its sources.

Each claim should link to a stored source identifier, URL, retrieval timestamp, document hash and relevant extracted passage.

A research pipeline should use source discovery, document retrieval, extraction, claim generation, independent verification and report compilation. Reject unsupported citations before publishing a report.

Use official APIs such as Crossref, OpenAlex and arXiv where appropriate, and Playwright for permitted browser automation. Web access necessarily means this component is not fully offline.

## 6. Persistent memory

Start with SQLite and files, not a standalone vector database or knowledge graph.

SQLite should store tasks, execution history, source metadata, decisions, approvals, project references and agent configurations. Markdown files should retain readable project notes and research summaries.

Use FTS5 for keyword retrieval. Add local embeddings only when retrieval tests show a meaningful improvement over keyword search.

Keep factual memory separate from generated interpretations. Record when information was obtained, its source and whether it has been verified.

## 7. Computer control

Give agents access to designated project directories through a dedicated macOS account. Use allowlisted tool wrappers rather than unrestricted shell commands.

GUI control should be an optional capability, not the primary method of interacting with the system. Prefer APIs and command-line tools because their results are easier to validate and reproduce.

For untrusted code, use stronger isolation such as a dedicated virtual machine or isolated runner. A separate macOS account alone is not a complete sandbox.

## 8. Always-on operation

Use launchd to start and restart the supervisor. The supervisor should restore task state from SQLite, identify abandoned leases, requeue safe tasks and resume checkpointed workflows.

A task must be recoverable without depending on the model's current context window.

Set up watchdog checks, bounded logs, disk-space monitoring, model-server health checks and automatic recovery procedures. Prevent system sleep when continuous processing is required, while retaining normal display sleep.

## 9. Remote access

Use Tailscale to reach the Mac privately from your phone or laptop. Keep the dashboard bound to localhost or the private Tailscale interface.

Tailscale supports SSH access, although its integrated SSH server has specific installation requirements on macOS. Standard SSH over a Tailscale connection is another option.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://tailscale.com\&sz=32)

Tailscale Docs

+1



Your phone interface should support submitting tasks, reviewing progress, granting approvals, cancelling tasks and stopping execution.

Do not publicly expose the inference server, task database or agent command endpoint.

## 10. Storage architecture

| Storage                     | Recommended contents                                                                      |
| --------------------------- | ----------------------------------------------------------------------------------------- |
| Internal 512 GB             | macOS, applications, supervisor, active SQLite database, configuration and essential logs |
| External 1 TB               | Model weights, research documents, datasets, Git worktrees, experiment outputs, caches    |
| Separate backup destination | Database snapshots, configuration, important research and completed projects              |

Do not treat the external working SSD as a backup. Ensure the system detects a missing or disconnected drive and stops affected tasks safely.

# Final deliverables A–K

## A. Recommended technology stack

The following is my proposed build stack, not a completed comparative benchmark of every available product.

| Layer            | Selection              | Alternative            | Reason                           |
| ---------------- | ---------------------- | ---------------------- | -------------------------------- |
| Inference        | llama.cpp              | MLX-LM, Ollama         | Local Metal inference            |
| Model management | GGUF model registry    | Ollama                 | Quantization control             |
| Orchestration    | LangGraph              | Custom state machine   | Durable workflows                |
| Queue            | SQLite                 | PostgreSQL             | Low overhead                     |
| Coding           | Aider                  | OpenHands              | Git-oriented development         |
| Research         | Python, Playwright     | Browser-use frameworks | Reproducible evidence collection |
| Memory           | SQLite, FTS5, Markdown | LanceDB                | Simple persistence               |
| API              | FastAPI                | Flask                  | Local control endpoints          |
| Supervisor       | launchd, Python        | systemd on Linux       | Native macOS services            |
| Remote           | Tailscale              | WireGuard              | Private network access           |
| Monitoring       | JSON logs, SQLite      | Prometheus             | Minimal infrastructure           |

The primary sources establish that these technologies support important parts of the architecture. They do not establish that every choice is the highest-performing option as of 31 August 2026.

## B. Complete architecture diagram

\#chatgpt-mermaid-\_r_j6\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_j6\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_j6\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_j6\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_j6\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_j6\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_j6\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_j6\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_j6\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_j6\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_j6\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_j6\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_j6\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_j6\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_j6\_ p{margin:0;}#chatgpt-mermaid-\_r_j6\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_j6\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_j6\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_j6\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_j6\_ .label text,#chatgpt-mermaid-\_r_j6\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_j6\_ .node rect,#chatgpt-mermaid-\_r_j6\_ .node circle,#chatgpt-mermaid-\_r_j6\_ .node ellipse,#chatgpt-mermaid-\_r_j6\_ .node polygon,#chatgpt-mermaid-\_r_j6\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_j6\_ .rough-node .label text,#chatgpt-mermaid-\_r_j6\_ .node .label text,#chatgpt-mermaid-\_r_j6\_ .image-shape .label,#chatgpt-mermaid-\_r_j6\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_j6\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_j6\_ .rough-node .label,#chatgpt-mermaid-\_r_j6\_ .node .label,#chatgpt-mermaid-\_r_j6\_ .image-shape .label,#chatgpt-mermaid-\_r_j6\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_j6\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_j6\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_j6\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_j6\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_j6\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_j6\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_j6\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_j6\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_j6\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_j6\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_j6\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_j6\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_j6\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_j6\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_j6\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_j6\_ .icon-shape,#chatgpt-mermaid-\_r_j6\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_j6\_ .icon-shape p,#chatgpt-mermaid-\_r_j6\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_j6\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_j6\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_j6\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_j6\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_j6\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_j6\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_j6\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_j6\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_j6\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_j6\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_j6\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_j6\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_j6\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_j6\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_j6\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_j6\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_j6\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_j6\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_j6\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_j6\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_j6\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_j6\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_j6\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_j6\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_j6\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_j6\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_j6\_ .node rect,#chatgpt-mermaid-\_r_j6\_ .node circle,#chatgpt-mermaid-\_r_j6\_ .node ellipse,#chatgpt-mermaid-\_r_j6\_ .node polygon,#chatgpt-mermaid-\_r_j6\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_j6\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_j6\_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_j6\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_j6\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_j6\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}Phone / LaptopTailscaleLocal FastAPI Control APISupervisorSQLite Task QueueApproval and Security PolicyLangGraph OrchestratorCoding AgentResearch AgentDocument AgentVerification AgentModel Routerllama.cpp Metal ServerRestricted Tool RunnerGit / Browser / Files / TestsPersistent MemoryLogs and Watchdog

Every executable task passes through the security policy and supervisor. An agent cannot grant itself additional permissions.

## C. Hardware and resource plan

Illustrative 32 GB unified memory allocation

macOS: 5 GB

Model weights: 10 GB

KV cache / inference overhead: 5 GB

Tools / browser / agents: 6 GB

Filesystem / system reserve: 4 GB

Safety margin: 2 GB

This is a planning budget, not a measured memory profile. macOS memory pressure and swap usage should determine the final configuration.

Run one 14B-class model as the initial default. Use one active LLM generation worker, with perhaps two to four non-inference tool workers. Test larger models only if they improve verified task completion per hour.

## D. Agent architecture

Each logical agent should be represented by a database record, rather than a permanently running process.

Recommended fields include agent ID, role, objective, model preference, tool permissions, workspace, parent task, state, priority, retry count, token budget, time budget and last checkpoint.

A coordinator can generate temporary specialist agent definitions for a task. Those definitions enter the queue and run when capacity is available. Use hierarchical delegation, but cap delegation depth to prevent recursive agent creation.

A starting limit is 100 stored agent definitions, one inference worker, four tool workers and no more than three levels of delegation.

## E. Model strategy

I would not lock the production system to a model checkpoint until it has passed a local evaluation.

| Function        | Initial model class                  |
| --------------- | ------------------------------------ |
| Planning        | 14B reasoning/instruction model      |
| Coding          | 14B coding-focused model             |
| Debugging       | Same coding model with test feedback |
| Research        | 14B instruction model                |
| Summarization   | 7B–9B instruction model              |
| Classification  | 3B–4B model or deterministic rules   |
| Final synthesis | Strongest locally validated model    |

Qwen-family open-weight models should be included in the evaluation, alongside other current models with suitable licences, tool calling and GGUF or MLX support.

Use a common evaluation set containing coding fixes, repository analysis, source-grounded research, tool calls and long-running tasks. Measure completed tasks, failures, memory use, elapsed time and unsupported claims. A model that produces fewer tokens but completes more verified work is preferable.

## F. 24/7 architecture

The operating loop should be:

1. Load pending tasks.
2. Select the highest-priority eligible task.
3. Check permissions and available resources.
4. Reserve the task with a time-limited lease.
5. Execute one checkpointed workflow step.
6. Verify the result and record evidence.
7. Retry, delegate, request approval or complete.
8. Release resources and select the next task.

On restart, the supervisor must distinguish between safe-to-retry operations and actions that may already have produced external effects.

Use explicit idempotency keys for operations such as sending messages, modifying remote systems and publishing content.

## G. Remote-control architecture

The private control API should expose authenticated endpoints for task submission, task status, logs, approvals, cancellation and emergency shutdown.

For example:

```
GET    /health
GET    /tasks
POST   /tasks
GET    /tasks/{id}
POST   /tasks/{id}/cancel
POST   /approvals/{id}/decision
POST   /system/pause
```

The dashboard should require authentication even when accessed through Tailscale. Separate read-only status access from permissions to approve or execute commands.

## H. Security architecture

| Operation                           | Policy                           |
| ----------------------------------- | -------------------------------- |
| Read approved project files         | Automatic                        |
| Create branches and worktrees       | Automatic                        |
| Edit files in isolated worktrees    | Automatic                        |
| Run approved tests                  | Automatic                        |
| Retrieve public research sources    | Automatic                        |
| Install dependencies                | Approval or restricted allowlist |
| Delete project directories          | Approval                         |
| Merge protected branches            | Approval                         |
| Access private credentials          | Explicit permission              |
| Send emails or publish content      | Approval                         |
| Transfer sensitive data externally  | Approval                         |
| Change system security settings     | Approval                         |
| Execute destructive system commands | Deny by default                  |

An emergency stop must terminate worker processes, prevent new task dispatch and preserve the audit log.

## I. Installation plan

The following commands establish a development foundation. They are not, by themselves, a complete production deployment.

### Phase 1. Basic environment

Install Homebrew if it is not already installed, using the instructions at [brew.sh](https://brew.sh).

Then:

```
brew install python git uv cmake llama.cpp
brew install tailscale
```

Check the installed versions:

```
python3 --version
git --version
uv --version
llama-server --help
```

Create the project directories:

```
mkdir -p ~/ai-lab/{config,src,logs,tests}
mkdir -p ~/ai-lab/{memory,backups}
```

Create the Python environment:

```
cd ~/ai-lab
uv venv
source .venv/bin/activate

uv pip install \
  langgraph \
  langgraph-checkpoint-sqlite \
  fastapi \
  uvicorn \
  pydantic \
  httpx \
  playwright \
  pytest
```

Install the Playwright browser:

```
python -m playwright install chromium
```

### Phase 2. Inference

Download a validated GGUF checkpoint from its official publisher or a trusted conversion source.

Start the server using the checkpoint's actual file path:

```
llama-server \
  -m /path/to/model.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  -c 16384
```

Check the service:

```
curl http://127.0.0.1:8080/health
```

Do not enable public network binding.

### Phase 3. Coding

Install Aider in a separate environment using its documented installation procedure.

Create a disposable Git worktree for each coding task. Run Aider against the local inference endpoint, verify the diff and execute tests before marking the task complete.

### Phase 4. Research and memory

Implement SQLite tables for tasks, agents, evidence, claims, approvals and execution history.

Store retrieved source documents by content hash. Keep generated reports separate from their evidence records.

### Phase 5. Multi-agent execution

Implement the scheduler with one model worker and a small tool-worker pool. Test queue recovery, retries, cancellations and delegation limits.

### Phase 6. Always-on service

Create a launchd service for the supervisor with automatic restart. Test recovery by deliberately terminating the worker during a checkpointed task.

### Phase 7. Remote access

Configure Tailscale, SSH permissions and private dashboard access. Test from a mobile network rather than only your home Wi-Fi.

### Phase 8. Optimization

Run repeated benchmarks across models, quantizations, context sizes and worker counts. Retain the configuration that maximizes verified completed tasks per hour without sustained memory pressure.

Each phase should be committed to Git, with a known-good configuration snapshot and a rollback test before proceeding.

## J. What not to install initially

Avoid Kubernetes, a distributed message broker, a dedicated vector database, a knowledge graph server and several competing orchestration frameworks.

Also avoid running multiple large inference servers continuously. They will compete for the same unified memory and memory bandwidth.

Do not install an autonomous browser or desktop-control framework with unrestricted access to your personal account.

## K. Future upgrade path

| Hardware             | Architectural change                                                       |
| -------------------- | -------------------------------------------------------------------------- |
| 32 GB                | One main inference worker, small tool pool                                 |
| 64 GB                | Larger models or two moderate inference workers                            |
| 96 GB                | More model residency, larger contexts, greater concurrency                 |
| 128 GB+              | Multiple specialised models and more simultaneous inference                |
| Dedicated GPU server | Move inference off the Mac, retain the Mac as supervisor and control plane |

The task queue, agent definitions, memory and security policies should remain largely unchanged as hardware capacity increases. This separation is one of the main benefits of the proposed architecture.

## Research limitations and final decision

The evidence reviewed supports the core technical choices, particularly Metal inference, Apple MLX, LangGraph persistence, local coding-agent integration and private remote access.

However, this is not yet the exhaustive, independently benchmarked August 2026 market comparison requested. In particular, I have not verified the exact M6 Mac mini configuration, benchmarked inference on that chip, established the best current checkpoint across every model family, or validated the full installation and crash-recovery process on your machine. I would not present those as completed findings.

My recommendation is to build a minimal, measurable system first, with llama.cpp, LangGraph, SQLite, a restricted coding worker and Tailscale. Expand to research and dynamically generated agents only after the base system survives unattended execution and restart testing.

## Primary sources

- [llama.cpp GitHub repository](https://github.com/ggml-org/llama.cpp). Primary.
- [Apple MLX GitHub repository](https://github.com/ml-explore/mlx). Primary.
- [LangGraph durable execution](https://langchain-ai.github.io/langgraph/concepts/durable_execution/). Primary.
- [LangGraph persistence documentation](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx). Primary.
- [Aider local-model integration](https://aider.chat/docs/llms/ollama.html). Primary.
- [OpenHands local LLM documentation](https://github.com/OpenHands/docs/blob/main/openhands/usage/llms/local-llms.mdx). Primary.
- [Tailscale SSH documentation](https://tailscale.com/docs/features/tailscale-ssh). Primary.
- [Apple Service Management documentation](https://developer.apple.com/documentation/servicemanagement). Primary.

These are the technical references used for the recommendations. They should be supplemented by release-specific records and reproducible hardware benchmarks before treating the design as a final production build specification.

## Reasoning trace (not shown to raters)

Not captured: no thinking panel was copied by the operator for this Instant run.

## Run notes

chatgpt.com, paid plan, new chat, GPT-5.6 Sol, Thinking effort Instant, as set in the pre-registration;
confirmed by the author. Run by the author by hand. Answer copied with ChatGPT's copy button and written
verbatim from the clipboard; the copy includes ChatGPT's citation and favicon links and diagram markup as
the app produced them. ChatGPT searched the web by itself even at Instant (live citations; research date given as 15 October 2026, with the prompt's 31 August 2026 noted as a historical cutoff). The answer names itself "GPT-6"; the model picker showed GPT-5.6 Sol, so this is recorded as a model self-report error.
