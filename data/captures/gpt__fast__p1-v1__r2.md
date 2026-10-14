---
run_id: gpt__fast__p1-v1__r2
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
replicate: 2
date_stamped: '2026-10-14T12:54:19+00:00'
date_run: 2026-10-14T12:00:00+00:00/2026-10-14T12:54:00+00:00
date_note: >-
  Sent by hand on 15 Oct 2026 NZDT before the template was made; exact send time not recorded. Interval: 01:00 NZDT (author: GPT runs sent from 01:00) to 01:54 NZDT (answer on the clipboard; template made).
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

GPT-6 | Knowledge cutoff: Not disclosed | Web browsing: Enabled | Research date: 15 October 2026, with the requested 31 August 2026 cutoff distinguished where possible.

# Autonomous AI Workstation Architecture

## Mac mini M6, 32 GB Unified Memory, 24/7 Local Operation

The correct approach is to build a persistent, queue-driven autonomous execution system, rather than relying on a single chatbot or an unrestricted swarm of agents.

My initial architectural decision is to use one shared local inference service, a durable task queue, a small number of active workers, specialist coding and research tools, and a separate supervisor responsible for recovery, permissions and scheduling.

The distinction that matters most is that 100 logical agents do not require 100 running models. Your machine can maintain hundreds of agent definitions, tasks and checkpoints while only running one substantial inference workload at a time.

## Decisions at a glance

| Layer                 | Initial recommendation                                                        |
| --------------------- | ----------------------------------------------------------------------------- |
| Local inference       | llama.cpp with Metal, benchmarked against MLX                                 |
| Model serving         | llama-server with OpenAI-compatible API                                       |
| Primary model         | Quantised 14B-class coding/instruction model, subject to benchmarking         |
| Agent orchestration   | Python supervisor with durable SQLite queue                                   |
| Coding                | Aider or OpenHands, evaluated for local-model compatibility                   |
| Research              | Custom evidence-tracking pipeline with browser and academic search adapters   |
| Memory                | SQLite, Markdown, full-text search, optional vector retrieval                 |
| Multi-agent operation | 100+ logical agents, 1 primary inference worker                               |
| Computer control      | Dedicated macOS account, isolated workspaces, restricted tool execution       |
| Always-on operation   | macOS launchd, watchdogs and persistent checkpoints                           |
| Remote access         | Tailscale with authenticated private dashboard                                |
| Storage               | Internal SSD for operating services, external SSD for models and project data |
| Security              | Least privilege, approval gates, audit logs and emergency stop                |

These are provisional engineering choices. Exact model releases, tool versions, Apple M6 compatibility and comparative performance require verification against current primary sources before treating the design as a final build specification.

## 1. Local inference

The primary constraint is unified memory, not SSD capacity.

A 32 GB Mac can store many models but cannot efficiently run several substantial models simultaneously. Model weights, KV cache, Metal buffers, macOS and agent processes all compete for the same memory.

I recommend testing three inference approaches:

| Engine       | Advantage                                                         | Limitation                                       | Decision             |
| ------------ | ----------------------------------------------------------------- | ------------------------------------------------ | -------------------- |
| llama.cpp    | GGUF quantisation, Metal support, API server, broad compatibility | Requires tuning                                  | Primary              |
| MLX / MLX-LM | Designed for Apple Silicon                                        | Different model packaging and integrations       | Benchmark challenger |
| Ollama       | Simple installation and model management                          | Less direct control over some inference settings | Easiest fallback     |

The upstream llama.cpp project documents OpenAI-compatible serving, concurrent decoding, embeddings and constrained generation. These capabilities make it suitable as a shared inference backend.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



### Model sizing

Planning estimates, not measured M6 benchmarks

| Model class | Approximate 4-bit weights | Suitability                                                  |
| ----------- | ------------------------- | ------------------------------------------------------------ |
| 3B          | 2–3 GB                    | Classification, extraction, routing                          |
| 7B–8B       | 4.5–6 GB                  | Lightweight agent tasks                                      |
| 14B         | 8–11 GB                   | Primary coding and reasoning candidate                       |
| 24B         | 14–18 GB                  | More demanding tasks, lower throughput                       |
| 32B         | 19–23 GB                  | Tight memory headroom, poor default for continuous operation |

These ranges include approximate quantised model storage overhead, but exclude KV cache and runtime buffers. Actual requirements depend on architecture and quantisation.

My initial target is a 14B-class model at Q4 or Q5, with a context window of 16,384 tokens. Increase to 32,768 only after measuring memory pressure and successful task completion rates.

Do not choose a 32B model solely because its weights fit.

## 2. Agent runtimes and harnesses

The workstation needs two distinct control systems.

The first is a durable supervisor that owns tasks, priorities, retries, approvals and checkpoints. The second is an agent runtime that executes individual coding or research tasks.

OpenHands is a credible coding-runtime candidate because it provides agent execution environments and sandbox support. Its documentation confirms Docker-based sandboxing and different execution backends. However, it also notes that strong models are important for effective operation.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub

+1



Aider is lighter and supports local OpenAI-compatible inference. Its documentation warns that weaker models may generate code without successfully applying edits.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://aider.chat\&sz=32)

aider



I would not make either tool the overall operating system. Use a small Python supervisor as the system of record and invoke coding tools as bounded workers.

## 3. Multi-agent architecture

100 logical agents, one shared inference resource

Each logical agent is a database record containing a role, goal, allowed tools, context references, current state and execution budget.

An agent becomes active only when the scheduler assigns its next task. On completion or interruption, it saves a checkpoint and releases the inference resource.

Start with one LLM worker and two non-inference workers. Increase concurrency only after measuring throughput, memory pressure and failure rates.

## 4. Coding agents

Use Aider for the first implementation because it is lightweight, Git-oriented and supports local models. Use OpenHands as a second-stage experiment where isolated execution and more complex autonomous coding loops justify its overhead.

Every coding task should run in its own Git worktree. The execution cycle should be:

1. Inspect repository and acceptance criteria.
2. Create a worktree and task branch.
3. Implement one bounded change.
4. Run relevant tests and static checks.
5. Review the diff.
6. Retry with an explicit error summary if validation fails.
7. Save results and request approval before merging into protected branches.

A successful agent response is not evidence that code works. Tests, exit codes and diff review are required.

## 5. Research agents

Research needs a separate evidence pipeline, not just a browser-enabled language model.

Use a search adapter, browser extraction, academic metadata sources such as Crossref and OpenAlex, PDF extraction, a claim-evidence database and a report generator.

Every factual claim in a final research report should point to a stored source record containing its URL or DOI, retrieval timestamp, source title, relevant passage and verification status.

The verifier must reject invented citations, flag contradictory evidence and distinguish source claims from model interpretation. For research requiring current information, local inference does not remove the need for internet access.

## 6. Persistent memory

Start with SQLite plus Markdown files.

SQLite should store task state, agent definitions, checkpoints, decisions, source records, tool events and execution budgets. Markdown should hold human-readable project instructions, summaries and final reports.

Add SQLite FTS5 for keyword retrieval. Introduce embeddings only when keyword search demonstrably fails to retrieve relevant context. A dedicated vector database or knowledge graph is unnecessary initially.

Separate global operational memory from project-specific memory. Never place credentials or private personal documents into general agent memory.

## 7. Computer control

The agent should not run as your normal macOS user.

Create a dedicated standard user account and place authorised workspaces under its control. Allow command execution within approved directories. Prefer isolated containers for untrusted code, with explicit mount and network restrictions.

The critical security distinction is between filesystem access and authority. An agent may be able to read a project without having permission to delete it, publish it, or access unrelated personal files.

GUI automation should be a later addition. Terminal and browser tools are easier to audit, restrict and reproduce.

## 8. Always-on operation

Use macOS launchd to supervise the queue service and inference service. Each task must have a lease, heartbeat, timeout, retry limit and persisted checkpoint.

After a crash, expired task leases return to the queue. Non-idempotent operations, such as sending messages or publishing changes, must not be repeated automatically without checking their previous outcome.

Prevent system sleep while allowing the display to sleep. Ensure FileVault and restart behaviour are compatible with unattended recovery. A powered-on Mac with FileVault enabled may still require an interactive unlock after a full reboot.

## 9. Remote access

Use Tailscale for private network access from your phone and laptop. Keep the dashboard bound to localhost or a carefully restricted tailnet interface, with no public port forwarding.

Tailscale documents encrypted private connectivity and SSH access controls. On macOS, its managed SSH server has a specific requirement for the open-source daemon variant, so ordinary SSH over the Tailscale network may be simpler initially.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://tailscale.com\&sz=32)

Tailscale Docs

+1



The mobile interface should support submitting tasks, checking status, viewing logs, approving restricted operations and triggering an emergency stop.

## 10. Storage architecture

| Storage      | Allocation      | Contents                                             |
| ------------ | --------------- | ---------------------------------------------------- |
| Internal SSD | 50–100 GB       | macOS, applications, Python environments, supervisor |
| Internal SSD | 10–30 GB        | Active SQLite database, indexes, operational logs    |
| External SSD | 250–400 GB      | Model weights and alternate quantisations            |
| External SSD | 200–300 GB      | Repositories, worktrees, research documents          |
| External SSD | 100–200 GB      | Datasets, experiments and caches                     |
| External SSD | Remaining space | Working reserve                                      |

Keep the authoritative task database on the internal SSD, where an external-drive disconnect cannot interrupt writes. Use the external SSD for large replaceable assets and project data.

An external SSD is not a backup. Maintain a separate encrypted backup destination.

# A–K. Final architecture and implementation specification

## A. Recommended technology stack

| Layer      | Selected               | Alternatives           | Reason                                |
| ---------- | ---------------------- | ---------------------- | ------------------------------------- |
| Inference  | llama.cpp              | MLX-LM, Ollama         | Control over quantisation and serving |
| Model      | 14B-class Q4/Q5        | 8B, 24B                | Balance of memory and capability      |
| Supervisor | Python 3.12+           | Temporal, Prefect      | Low overhead and full control         |
| Queue      | SQLite WAL             | Redis, PostgreSQL      | Durable without another server        |
| Coding     | Aider                  | OpenHands, OpenCode    | Lightweight local integration         |
| Research   | Python + Playwright    | Browser-use, LangGraph | Verifiable evidence workflow          |
| Documents  | PyMuPDF, pandas        | Docling                | Practical extraction and analysis     |
| Memory     | SQLite FTS5 + Markdown | Qdrant, LanceDB        | Simple and inspectable                |
| Scheduling | APScheduler + launchd  | cron                   | Persistent jobs and process recovery  |
| Remote     | Tailscale              | WireGuard              | Private access without public ports   |
| Dashboard  | FastAPI                | Streamlit              | Small authenticated control API       |
| Monitoring | Structured JSON logs   | Prometheus, Grafana    | Lower initial overhead                |

This is a recommended design, not a completed benchmark-based ranking of every current product. The web evidence checked supports the main infrastructure choices, but does not establish a definitive best model or runtime as of 31 August 2026.

## B. Complete architecture

\#chatgpt-mermaid-\_r_gt\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_gt\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_gt\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_gt\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_gt\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_gt\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_gt\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_gt\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_gt\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_gt\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_gt\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_gt\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_gt\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_gt\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_gt\_ p{margin:0;}#chatgpt-mermaid-\_r_gt\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_gt\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_gt\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_gt\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_gt\_ .label text,#chatgpt-mermaid-\_r_gt\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_gt\_ .node rect,#chatgpt-mermaid-\_r_gt\_ .node circle,#chatgpt-mermaid-\_r_gt\_ .node ellipse,#chatgpt-mermaid-\_r_gt\_ .node polygon,#chatgpt-mermaid-\_r_gt\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_gt\_ .rough-node .label text,#chatgpt-mermaid-\_r_gt\_ .node .label text,#chatgpt-mermaid-\_r_gt\_ .image-shape .label,#chatgpt-mermaid-\_r_gt\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_gt\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_gt\_ .rough-node .label,#chatgpt-mermaid-\_r_gt\_ .node .label,#chatgpt-mermaid-\_r_gt\_ .image-shape .label,#chatgpt-mermaid-\_r_gt\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_gt\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_gt\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_gt\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_gt\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_gt\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_gt\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_gt\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_gt\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_gt\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_gt\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_gt\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_gt\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_gt\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_gt\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_gt\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_gt\_ .icon-shape,#chatgpt-mermaid-\_r_gt\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_gt\_ .icon-shape p,#chatgpt-mermaid-\_r_gt\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_gt\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_gt\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_gt\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_gt\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_gt\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_gt\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_gt\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_gt\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_gt\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_gt\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_gt\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_gt\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_gt\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_gt\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_gt\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_gt\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_gt\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_gt\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_gt\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_gt\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_gt\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_gt\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_gt\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_gt\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_gt\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_gt\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_gt\_ .node rect,#chatgpt-mermaid-\_r_gt\_ .node circle,#chatgpt-mermaid-\_r_gt\_ .node ellipse,#chatgpt-mermaid-\_r_gt\_ .node polygon,#chatgpt-mermaid-\_r_gt\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_gt\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_gt\_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_gt\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_gt\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_gt\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}Phone / LaptopTailscaleAuthenticated FastAPISupervisorSQLite Task QueuePolicy / Approval EngineWorker SchedulerCoding AgentResearch AgentDocument AgentModel Routerllama.cpp / MetalGit / Terminal / TestsBrowser / Academic APIsPDF / Data ToolsProject MemoryAudit Logs / Checkpoints

The supervisor, rather than an LLM, owns scheduling, task leases, approval enforcement and restart recovery.

## C. Hardware and resource plan

Illustrative peak memory budget for a 14B-class quantised model

32 GB unified memory

Estimated allocation

macOS and background services

6 GB

Quantised model weights

10 GB

KV cache and inference buffers

5 GB

Agent tools, browser and databases

5 GB

Headroom and filesystem cache

6 GB

These are budgeting allowances, not guaranteed resident-memory figures. Start with one substantial inference worker, no simultaneously loaded second large model, and a 16K context window. Model switching is reasonable between batches of tasks, but frequent swapping will reduce throughput.

## D. Agent architecture

Store agent definitions separately from task executions. An agent record identifies its role and permissions. A task record identifies a specific unit of work.

Use these states:

`queued → leased → running → verifying → completed`

Also support `waiting_approval`, `retry_pending`, `failed` and `cancelled`.

A task may generate child tasks, but enforce a maximum delegation depth of three, a maximum number of child tasks and a fixed execution budget. This prevents runaway delegation.

## E. Model strategy

For the first build, use one primary local coding/instruction model and a smaller classification model. The exact current model selection remains subject to a verified model-card and Mac benchmark comparison.

| Workload        | Model strategy                               |
| --------------- | -------------------------------------------- |
| Planning        | Primary 14B-class model                      |
| Coding          | Primary model, coding-specialised checkpoint |
| Debugging       | Same coding model with test outputs          |
| Research        | Primary model with retrieval tools           |
| Summarisation   | 7B–8B model if measured throughput improves  |
| Classification  | 3B-class model or deterministic rules        |
| Final synthesis | Primary model with citation verification     |

Test candidate models on 20 real tasks, including repository edits, test repair, tool calling, source attribution and long-context retrieval. Record success rate, time per accepted task, peak memory and manual corrections.

Do not select a model based only on general chat benchmarks.

## F. 24/7 architecture

Use launchd to restart the supervisor after a process failure. The supervisor should recover expired task leases and resume only operations that are safe to repeat.

Persist every task transition. Record the last successful checkpoint, Git commit, tool execution and verification outcome.

A nightly maintenance job should check database integrity, archive logs, clean abandoned worktrees and produce a short activity report.

## G. Remote-control architecture

The first remote interface should expose task submission, queue status, approvals, logs and an emergency stop.

Restrict access to authenticated devices on Tailscale. Do not expose the inference server or supervisor API directly to the internet.

For the emergency stop, provide a control that disables new scheduling, terminates active worker processes and revokes outstanding task leases. Preserve logs and task state for later inspection.

## H. Security architecture

| Operation                                  | Permission               |
| ------------------------------------------ | ------------------------ |
| Read approved project files                | Automatic                |
| Create worktrees and branches              | Automatic                |
| Edit files inside assigned workspace       | Automatic                |
| Run approved tests                         | Automatic                |
| Download public research material          | Automatic, within limits |
| Install system-level software              | Approval                 |
| Read credentials or private folders        | Approval or deny         |
| Delete files outside disposable workspaces | Approval                 |
| Merge into protected branches              | Approval                 |
| Send external emails or publish content    | Approval                 |
| Make payments or financial transactions    | Deny by default          |
| Change security settings                   | Approval                 |

Keep credentials outside agent-readable workspaces. Use allowlisted commands, restricted network access, subprocess timeouts and structured audit logs.

An LLM must never be able to grant itself additional permissions.

## I. Installation plan

The following is a bootstrap sequence, not the entire production deployment. Run it under a dedicated standard macOS user account.

Phase 1. Install core dependencies

```
xcode-select --install

brew install python@3.12 git jq sqlite llama.cpp

python3.12 -m venv ~/ai-lab/venv
source ~/ai-lab/venv/bin/activate

python -m pip install --upgrade pip
python -m pip install fastapi uvicorn apscheduler \
  httpx pydantic psutil pytest
```

Homebrew must be installed first. Confirm package availability and installed versions before deployment.

Phase 2. Create the directory structure

```
mkdir -p ~/ai-lab/{config,supervisor,agents,tools}
mkdir -p ~/ai-lab/{database,logs,reports,tests}
mkdir -p ~/ai-lab/{scripts,backups}

mkdir -p /Volumes/AI-DATA/{models,repositories}
mkdir -p /Volumes/AI-DATA/{research,datasets}
mkdir -p /Volumes/AI-DATA/{worktrees,cache}
```

Replace `AI-DATA` with the actual external SSD volume name. Format the drive appropriately, preferably APFS for this macOS-only workload.

Phase 3. Start inference

After downloading and verifying a compatible GGUF model:

```
llama-server \
  -m /Volumes/AI-DATA/models/primary.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  -c 16384 \
  -np 1
```

Test the server:

```
curl http://127.0.0.1:8080/v1/models
```

This verifies API availability, not model quality.

Phases 4–8. Deployment sequence

| Phase             | Implementation              | Acceptance test                 | Rollback                   |
| ----------------- | --------------------------- | ------------------------------- | -------------------------- |
| Autonomous coding | Aider, Git worktrees        | Fix a seeded failing test       | Discard worktree           |
| Research          | Playwright, source registry | Report with verified citations  | Disable browser worker     |
| Memory            | SQLite, FTS5                | Recover project decisions       | Restore database backup    |
| Multi-agent       | Queue and worker scheduler  | Complete 20 delegated tasks     | Set worker limit to one    |
| Always-on         | launchd, watchdog           | Recover after forced crash      | Unload service             |
| Remote            | Tailscale, FastAPI          | Submit and cancel task remotely | Disable remote listener    |
| Optimisation      | Benchmark runner            | Improve accepted tasks/hour     | Restore prior model config |

Do not enable unattended overnight operation until crash recovery, cancellation, approval enforcement and backup restoration have passed tests.

## J. What not to install initially

Avoid Kubernetes, a distributed message broker, multiple vector databases, a large knowledge-graph stack and several competing agent orchestration frameworks.

Also avoid running OpenHands, Aider and other coding agents continuously at the same time. Evaluate them separately, then retain the tools that demonstrate measurable value.

Do not give agents administrator access or mount your entire home directory into a sandbox.

## K. Future upgrade path

| Hardware             | Recommended change                                             |
| -------------------- | -------------------------------------------------------------- |
| 32 GB                | One primary 14B-class worker                                   |
| 64 GB                | Evaluate 24B–32B models, larger context                        |
| 96 GB                | Consider concurrent primary and specialist models              |
| 128 GB+              | Larger reasoning models and multiple inference workers         |
| Dedicated GPU/server | Move inference to a separate service, retain Mac as supervisor |

Adding memory does not automatically improve task quality. Measure model capability, memory bandwidth, inference latency and accepted tasks per hour before upgrading.

## Sources

Primary documentation consulted:

- [llama.cpp official repository](https://github.com/ggml-org/llama.cpp)
- [MLX-LM official repository](https://github.com/ml-explore/mlx-lm)
- [OpenHands documentation](https://docs.openhands.dev/)
- [Aider model integration documentation](https://aider.chat/docs/llms.html)
- [Tailscale SSH documentation](https://tailscale.com/docs/features/tailscale-ssh)
- [Apple launchd source repository](https://github.com/apple-oss-distributions/launchd)

## Research limitations and final decision

The research completed here verifies several foundational technologies, but it does not satisfy the full market-wide comparison and benchmark requirement in your brief. In particular, I have not independently verified the base M6 Mac mini specifications, measured inference on that hardware, compared the latest model releases against one another, or audited release activity for every proposed component as of 31 August 2026.

I would therefore classify this as a reference architecture suitable for prototyping, not yet a production-ready, fully validated build specification.

The strongest decision is architectural: use a durable supervisor, shared local inference, bounded workers, persistent evidence and checkpoints, and explicit security controls.

The next technical gate is to benchmark current local models and agent harnesses on your actual Mac. Those results should determine the final model, coding runtime and concurrency settings before you invest in the full autonomous system.

## Reasoning trace (not shown to raters)

Not captured: no thinking panel was copied by the operator for this Instant run.

## Run notes

chatgpt.com, paid plan, new chat, GPT-5.6 Sol, Thinking effort Instant, as set in the pre-registration;
confirmed by the author. Run by the author by hand. Answer copied with ChatGPT's copy button and written
verbatim from the clipboard; the copy includes ChatGPT's citation and favicon links and diagram markup as
the app produced them. ChatGPT searched the web by itself even at Instant (live citations; research date given as 15 October 2026, with the prompt's 31 August 2026 noted as a cutoff). The answer names itself "GPT-6"; the model picker showed GPT-5.6 Sol, so this is recorded as a model self-report error. Two earlier copies for this run repeated the run 7 answer byte for byte and were rejected before this copy.
