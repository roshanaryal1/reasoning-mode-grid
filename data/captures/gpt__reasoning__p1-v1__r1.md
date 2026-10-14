---
run_id: gpt__reasoning__p1-v1__r1
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
replicate: 1
date_stamped: '2026-10-14T13:30:17+00:00'
date_run: 2026-10-14T12:56:00+00:00/2026-10-14T13:08:00+00:00
date_note: >-
  Sent by hand on 15 Oct 2026 NZDT in a new chat after the prompt was put back on the clipboard at 01:56 NZDT; the answer was on the clipboard by 02:30 NZDT after ChatGPT worked for 21 min 54 s, so it was sent by 02:08 NZDT. Exact send time not recorded.
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

GPT-6 | Knowledge cutoff: Not disclosed | Web browsing: Enabled | Research tools: Enabled

Research reference date: 31 August 2026 Actual verification date: 15 October 2026 Hardware: Apple Mac mini M6, 32 GB unified memory, 512 GB internal SSD, 1 TB external SSD

# Autonomous AI Workstation: Research and Architecture Specification

## Executive recommendation

Build a local-first autonomous agent operating environment with a persistent task queue, controlled execution, local language models, independent verification, and secure remote management.

The best architecture is a hybrid of established open-source tools and a small, purpose-built orchestration service. Do not build an entire agent framework from scratch, and do not depend on a single autonomous-agent product to handle every workload.

Your Mac mini can support continuous coding, research, document processing, and multiple logical agents. However, 32 GB of unified memory imposes a significant limit on simultaneous model inference.

The design should optimise completed, verified work rather than how many agents appear to be running.

### Important hardware verification

Apple announced the M6 Mac mini on 25 August 2026, with availability scheduled from 22 September 2026. The 32 GB configuration is supported, with up to 170 GB/s unified memory bandwidth.

Therefore, the exact hardware was officially announced, but had not yet reached customers on the requested 31 August research date. M6-specific agent workloads had not yet been independently validated on generally available retail machines at that cutoff.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.apple.com\&sz=32)

Apple (NZ)

+1



The hardware resource estimates below are engineering estimates, not measured M6 inference benchmarks.

## Decisions at a glance

| Layer                | Recommended choice                                      | Decision                            |
| -------------------- | ------------------------------------------------------- | ----------------------------------- |
| Local inference      | Ollama, with llama.cpp as an advanced alternative       | Start with Ollama                   |
| Primary coding model | Qwen3-Coder 30B-A3B, Q4                                 | One large worker                    |
| General reasoning    | GPT-OSS 20B                                             | On-demand alternative               |
| Lightweight tasks    | Qwen3 4B or 8B                                          | Fast routing and extraction         |
| Coding runtime       | OpenCode                                                | Main coding agent                   |
| Orchestration        | Python supervisor and SQLite-backed queue               | Small custom control service        |
| Agent framework      | Pydantic AI                                             | Typed specialist agents             |
| Research             | Playwright, Python, external sources, evidence database | Dedicated research pipeline         |
| Memory               | SQLite, Markdown, Git, SQLite FTS5                      | Start without a vector server       |
| Embeddings           | Qwen3-Embedding 0.6B                                    | Add when required                   |
| Isolation            | Dedicated macOS account and isolated workspaces         | Mandatory                           |
| Background operation | launchd                                                 | Native macOS supervision            |
| Remote connection    | Tailscale                                               | Private network access              |
| Monitoring           | Structured logs, SQLite events, local dashboard         | No mandatory SaaS                   |
| Cloud models         | Optional escalation only                                | Never required for normal operation |

This is the recommended starting architecture. Additional frameworks, distributed queues, vector databases, and cloud inference should be introduced only when measurement shows they solve a real problem.

# Investigation findings

## 1. Local inference

### Inference engines

| Engine    | Strength                                                                    | Limitation                                              | Assessment                          |
| --------- | --------------------------------------------------------------------------- | ------------------------------------------------------- | ----------------------------------- |
| Ollama    | Easy installation, Metal support, model management, local API               | Less granular control than llama.cpp                    | Best starting choice                |
| llama.cpp | Quantisation, explicit memory controls, continuous batching, GGUF ecosystem | More configuration and tuning                           | Best advanced inference engine      |
| MLX-LM    | Native Apple Silicon development, MLX models, efficient experimentation     | Model-specific tool-call compatibility needs validation | Best for Apple-specific experiments |
| LM Studio | Convenient graphical interface and local server                             | Less suitable as the central unattended service         | Best desktop interface              |
| vLLM      | Advanced serving and batching for supported accelerators                    | Poor fit for this small macOS host                      | Use on future GPU server            |
| SGLang    | High-performance serving and agent-model integrations                       | Better suited to dedicated accelerator servers          | Future option                       |

Ollama documents parallel-request configuration, model loading and unloading, KV-cache quantisation, and model residency controls. llama.cpp provides a lower-level server with continuous batching and explicit parallel slots. MLX-LM is worth benchmarking separately, but compatibility with agent tool-calling must be tested per model.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.ollama.com\&sz=32)

Ollama

+2



My selection is Ollama for the initial system and llama.cpp for later performance experiments. Do not run both servers against different large models simultaneously.

### Local model comparison

Approximate download sizes, not full runtime memory requirements:

| Model                  | Model file          | Appropriate workload                           | Recommendation      |
| ---------------------- | ------------------- | ---------------------------------------------- | ------------------- |
| Qwen3 4B Q4            | 2.5 GB              | Classification, routing, extraction            | Lightweight worker  |
| Qwen3 8B Q4            | 5.2 GB              | Routine analysis and coding assistance         | Good alternative    |
| Qwen3.5 9B Q4          | 6.6 to 7.6 GB       | General reasoning, document analysis, planning | Daily general model |
| GPT-OSS 20B            | 14 GB               | Structured reasoning, critique, synthesis      | On-demand reasoning |
| Qwen3-Coder 30B-A3B Q4 | 19 GB               | Coding and repository-level tasks              | Primary specialist  |
| Qwen3.6 35B-A3B Q4     | Approximately 23 GB | More demanding coding and agent tasks          | Experimental only   |
| Qwen3-Embedding 0.6B   | 639 MB              | Semantic retrieval                             | Memory indexing     |

The size and architecture specifications are supported by the official model cards and Ollama model registry. Qwen3-Coder 30B-A3B has approximately 30.5 billion total parameters, with 3.3 billion activated per token. GPT-OSS 20B is a mixture-of-experts reasoning model designed for local deployment.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://ollama.com\&sz=32)

qwen3

+5



Choose three operational models initially: Qwen3.5 9B, Qwen3-Coder 30B-A3B, and Qwen3 4B.

Add GPT-OSS 20B after testing whether its reasoning and verification performance justifies the switching overhead.

Do not attempt to operate the 30B coding model and 20B reasoning model in memory together.

The advertised 128K or 256K model context length is an architectural capability, not an appropriate allocation target for 32 GB RAM.

Use these starting context limits:

| Workload                   | Context target                       |
| -------------------------- | ------------------------------------ |
| Routing and classification | 4K to 8K                             |
| General planning           | 16K to 24K                           |
| Document analysis          | 16K to 32K                           |
| Primary coding             | 16K initially                        |
| Larger coding task         | 24K to 32K only after memory testing |
| Research synthesis         | 16K to 24K with retrieved evidence   |

Use retrieval, rolling summaries, and project notes rather than putting entire repositories or research collections into model context.

## 2. Agent runtimes and orchestration

The key distinction is between an agent harness, which executes model-directed steps, and a durable orchestration system, which manages work across hours, failures, and restarts.

An autonomous coding harness is not automatically a complete unattended operating environment.

| Framework                 | Primary strength                                                    | Fit for your system                             |
| ------------------------- | ------------------------------------------------------------------- | ----------------------------------------------- |
| OpenCode                  | Terminal coding, tools, subagents, local models, headless execution | Primary coding harness                          |
| OpenHands                 | Development agents, workspaces, execution backends, automation      | Strong alternative, heavier                     |
| Aider                     | Repository understanding, code editing, Git integration             | Lightweight alternative                         |
| Pi coding agent           | Minimal extensible agent loop and integration interfaces            | Best minimalist experiment                      |
| Mini-SWE-Agent            | Issue-solving and benchmark-style coding                            | Testing and experimentation                     |
| Pydantic AI               | Typed tools, structured outputs, specialist agents                  | Primary agent SDK                               |
| LangGraph                 | Stateful graphs, checkpoints, resumable execution                   | Complex workflows later                         |
| Microsoft Agent Framework | Enterprise-style orchestration                                      | Not necessary initially                         |
| CrewAI                    | Role-based teams and task flows                                     | More abstraction than required                  |
| Temporal or DBOS          | Durable workflow execution                                          | Upgrade when SQLite supervision is insufficient |

OpenCode supports non-interactive runs, model selection, specialist agents, and tool permissions. Pydantic AI supports durable execution integrations, while the SWE-agent maintainers direct new users toward the simpler Mini-SWE-Agent.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai\&sz=32)

OpenCode

+3



### Decision

Use two complementary systems.

OpenCode handles coding tasks. Pydantic AI handles specialist non-coding agents.

A small Python supervisor owns the actual lifecycle of the system: task creation, admission control, execution, approval, verification, recovery, and state transitions.

The supervisor must be deterministic wherever possible. Let the language model propose actions, but let application code enforce permissions, resource budgets, and completion criteria.

Avoid running a separate independent agent platform for every role.

## 3. Multi-agent architecture

Your requirement for 100 or more agents is practical if agents are logical workers rather than individual loaded models.

An agent definition contains a role, instructions, permitted tools, assigned model, objectives, and output schema. It consumes almost no model memory while idle.

A running agent needs a model-inference allocation. Multiple logical agents can share the same inference server and work sequentially.

### Recommended 100-agent design

## 100+

Logical agent definitions

Specialist roles and task configurations

## 100–1,000+

Persisted tasks

SQLite queue, dependencies and priorities

# 1

Large-model inference worker

# 0–1

Small-model inference worker

# 2–4

I/O and research workers

# 1–2

CPU and test workers

These counts are initial configuration targets, not benchmark-proven maximums.

Use a coordinator-worker model rather than a free-form swarm. Agents communicate through structured task records and persisted artifacts, not unbounded conversations with other agents.

Each task should have a maximum number of child tasks, a permitted tool set, an execution budget, and a clear completion condition. A dynamically created agent should inherit the permissions of its parent or receive fewer permissions, never more.

## 4. Coding agents

OpenCode is the primary selection because it provides a scriptable coding workflow and supports local Ollama endpoints. Aider is particularly useful for focused edits because of its repository map. OpenHands is a credible alternative for fuller development workspaces, but its additional runtime components are not necessary for the initial setup.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai\&sz=32)

OpenCode

+2



The coding workflow should be:

1. Inspect the approved repository and record its baseline commit.
2. Create an isolated Git worktree and task branch.
3. Generate an implementation plan with measurable acceptance criteria.
4. Execute edits and tool calls inside an isolated environment.
5. Run formatting, linting, static analysis, and tests.
6. Review the resulting Git diff using a separate verification task.
7. Repeat within a strict retry budget.
8. Produce a summary containing test results, changed files, unresolved issues, and the worktree location.
9. Request approval before merging or pushing.

A coding job that exits successfully is not necessarily a successful software change.

Completion requires passing the agreed verification gates. A failed or inconclusive test should result in a failed or review-required task state.

## 5. Research agents

Use an evidence-first research pipeline instead of asking a single model to research a topic and produce a report.

Recommended components:

| Capability           | Choice                                             |
| -------------------- | -------------------------------------------------- |
| Website automation   | Playwright                                         |
| Search and discovery | Search APIs or approved web sources                |
| Academic metadata    | OpenAlex, Crossref, Semantic Scholar, arXiv        |
| PDF processing       | Docling and PyMuPDF                                |
| Content retrieval    | Python HTTP clients with rate limits               |
| Source storage       | Original files and SQLite metadata                 |
| Verification         | Deterministic checks plus independent model review |
| Report generation    | Markdown with source-linked citations              |

Playwright provides browser control and session isolation. Docling supports structured document conversion, including PDF layouts and tables. Crossref supplies DOI-linked publication metadata.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://playwright.dev\&sz=32)

Playwright Python

+2



Every factual claim in a generated research report should be linked to an evidence record containing:

- Source URL, title, publisher, retrieval date, and document hash.
- A quoted passage or extracted evidence span with page or section location.
- The exact claim that the evidence is meant to support.
- Verification status: supported, contradicted, ambiguous, or unsupported.

The verification stage should confirm that the URL or DOI exists, that the claimed passage appears in the retrieved material, and that the passage actually supports the assertion.

An unresolved claim should remain flagged. The final report should not silently convert uncertainty into certainty.

For published academic papers, distinguish peer-reviewed research from preprints and note retractions or corrections where identifiable.

## 6. Persistent memory

Start with SQLite, ordinary project files, and Git.

Use four forms of memory:

| Memory type | Store                                         | Purpose                             |
| ----------- | --------------------------------------------- | ----------------------------------- |
| Working     | Current model context and task artifacts      | Immediate execution                 |
| Episodic    | SQLite execution events                       | What happened previously            |
| Semantic    | Markdown project summaries and SQLite records | Decisions and established knowledge |
| Retrieval   | SQLite FTS5, later embeddings                 | Find relevant past information      |

Suggested database tables include `projects`, `tasks`, `dependencies`, `runs`, `events`, `artifacts`, `sources`, `claims`, `approvals`, `agent_definitions`, and `model_evaluations`.

Use SQLite WAL mode, transactions, and a single logical task-claim operation. Persist checkpoint data before performing external side effects.

Keep the actual project documents on disk. Store their paths, hashes, metadata, and extracted text in the database.

Add Qwen3-Embedding 0.6B and a small vector index once full-text search demonstrably misses useful material. A dedicated Qdrant or PostgreSQL deployment is unnecessary at the beginning.

## 7. Computer control

Use four execution levels.

| Level      | Examples                                                                               | Permission                   |
| ---------- | -------------------------------------------------------------------------------------- | ---------------------------- |
| Read only  | Inspect approved files, parse PDFs, read public websites                               | Automatic                    |
| Reversible | Create branches, edit isolated copies, write draft reports                             | Automatic inside isolation   |
| Controlled | Install packages, modify approved project configuration, access authenticated services | Restricted or approval-based |
| Privileged | Read secrets, delete important data, transfer money, publish, push production changes  | Explicit approval            |

A dedicated macOS account is a useful first boundary, but it does not replace a sandbox.

The key improvement is to execute untrusted code in isolated containers or virtual machines with specifically mounted workspaces.

The host account should retain control over credentials, the model server, the task database, and approval decisions.

Treat web pages, repository instructions, PDF content, and agent-generated commands as untrusted input. None of those sources should be permitted to change the security policy.

## 8. Always-on operation

Use macOS launchd to start and supervise the control service. Apple documents `RunAtLoad` and `KeepAlive` for launch jobs.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://developer.apple.com\&sz=32)

Apple Developer



A reliable persistent task runner needs more than process auto-restart:

- SQLite-backed task status and execution leases.
- Heartbeats for active workers.
- Recovery of abandoned tasks after a crash.
- Retries with bounded exponential backoff.
- Idempotency keys for operations that can safely be retried.
- A review state for uncertain side effects.
- Persistent logs and a resource monitor.
- A global stop flag enforced by the supervisor.

A machine restart must not cause the agent to resend a message, repeat a payment, publish twice, or overwrite work simply because it could not confirm the previous outcome.

If FileVault requires the Mac to be unlocked after a cold boot, that is a practical recovery limitation. Test restart behaviour with the actual macOS configuration before depending on unattended recovery.

## 9. Remote access

Use Tailscale for network access and a private dashboard for job management.

Tailscale Serve can make a local HTTP service accessible inside your private tailnet without exposing it publicly. It remains subject to your tailnet access rules.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://tailscale.com\&sz=32)

Tailscale Docs



The dashboard should allow task submission, queue inspection, cancellation requests, approval, log review, resource monitoring, and an emergency-stop action.

Use separate authentication and authorisation inside the control service. Possession of access to the tailnet should not automatically authorise destructive tasks.

For remote terminal access, standard macOS SSH over Tailscale is sufficient. Note that Tailscale's own SSH server feature has separate macOS installation requirements.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://tailscale.com\&sz=32)

Tailscale Docs



Do not expose Ollama, OpenCode, SSH, or a development dashboard directly through router port forwarding.

## 10. Storage architecture

Keep the operating system, applications, active database, and small control files on the internal SSD.

Use the external SSD primarily for large models, repositories, source collections, caches, and disposable worktrees.

The external drive should be formatted APFS, preferably encrypted. Assign it a stable volume name and have the supervisor verify that it is mounted before accepting work.

| Internal SSD, 512 GB                  | External SSD, 1 TB             |
| ------------------------------------- | ------------------------------ |
| macOS and applications                | Quantised models               |
| Supervisor and configuration          | Git repositories and worktrees |
| Active SQLite databases               | Research papers and datasets   |
| Authentication and sensitive settings | Parsed document collections    |
| Critical logs and manifests           | Experiment artifacts           |
| Recovery utilities                    | Rebuildable caches             |

Keep at least one independent encrypted backup. Two folders on the external SSD do not constitute a backup.

# Required deliverables A–K

## A. Recommended technology stack

The following table separates the best overall option from the best fit for this particular machine. These are architecture judgements, not claims that every candidate has won a directly comparable benchmark.

| Category                 | Best overall                           | Best for 32 GB Mac           | Lightweight     | Mature option       | Advanced option                | Install                 |
| ------------------------ | -------------------------------------- | ---------------------------- | --------------- | ------------------- | ------------------------------ | ----------------------- |
| Local inference          | llama.cpp                              | Ollama                       | Ollama          | llama.cpp           | MLX-LM                         | Ollama                  |
| Coding runtime           | OpenHands or OpenCode                  | OpenCode                     | Aider or Pi     | Aider               | OpenHands                      | OpenCode                |
| Agent orchestration      | Durable workflow service               | Python + SQLite              | Python queue    | Temporal            | LangGraph + durable execution  | Python + SQLite         |
| Multi-agent coordination | Structured coordinator-workers         | Queued agents                | Process pool    | Temporal workers    | Dynamic DAGs                   | Custom scheduler        |
| Research                 | Evidence-first pipeline                | Playwright + PyMuPDF         | HTTPX + PyMuPDF | Playwright          | Docling + verification system  | Python research workers |
| Memory                   | Hybrid structured and semantic storage | SQLite + FTS5                | Files + Git     | SQLite              | Embeddings + knowledge graph   | SQLite                  |
| Computer execution       | Isolated VM with permissions           | Dedicated user + isolated VM | Dedicated user  | VM-based isolation  | Policy-controlled tool gateway | Dedicated user, then VM |
| Background service       | Durable supervisor                     | launchd + SQLite             | launchd         | launchd             | Temporal or DBOS               | launchd                 |
| Remote access            | Private network with identity controls | Tailscale                    | SSH             | WireGuard/Tailscale | Private dashboard + ACLs       | Tailscale               |
| Monitoring               | Events, metrics, audit trails          | Local structured logs        | Log files       | Prometheus          | OpenTelemetry                  | SQLite events + logs    |
| Storage                  | Tiered storage with independent backup | Internal SSD + external APFS | Filesystem      | APFS + Git          | Object storage later           | APFS + backup           |

All selected components have a free or open-source operating path. Some offer optional paid products or services.

A distinction matters: the best system for a dedicated 128 GB server is not necessarily the best system for a 32 GB personal workstation. Complexity has a cost in memory, maintenance, and failure modes.

## B. Complete architecture diagram

\#chatgpt-mermaid-\_r_1g7\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_1g7\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_1g7\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_1g7\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_1g7\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1g7\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_1g7\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_1g7\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_1g7\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_1g7\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_1g7\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_1g7\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_1g7\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_1g7\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_1g7\_ p{margin:0;}#chatgpt-mermaid-\_r_1g7\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1g7\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1g7\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1g7\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_1g7\_ .label text,#chatgpt-mermaid-\_r_1g7\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1g7\_ .node rect,#chatgpt-mermaid-\_r_1g7\_ .node circle,#chatgpt-mermaid-\_r_1g7\_ .node ellipse,#chatgpt-mermaid-\_r_1g7\_ .node polygon,#chatgpt-mermaid-\_r_1g7\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_1g7\_ .rough-node .label text,#chatgpt-mermaid-\_r_1g7\_ .node .label text,#chatgpt-mermaid-\_r_1g7\_ .image-shape .label,#chatgpt-mermaid-\_r_1g7\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_1g7\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_1g7\_ .rough-node .label,#chatgpt-mermaid-\_r_1g7\_ .node .label,#chatgpt-mermaid-\_r_1g7\_ .image-shape .label,#chatgpt-mermaid-\_r_1g7\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_1g7\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_1g7\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_1g7\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_1g7\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_1g7\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_1g7\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_1g7\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_1g7\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_1g7\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_1g7\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_1g7\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1g7\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1g7\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_1g7\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1g7\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_1g7\_ .icon-shape,#chatgpt-mermaid-\_r_1g7\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_1g7\_ .icon-shape p,#chatgpt-mermaid-\_r_1g7\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_1g7\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_1g7\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_1g7\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_1g7\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_1g7\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_1g7\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_1g7\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_1g7\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_1g7\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1g7\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_1g7\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_1g7\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_1g7\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1g7\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_1g7\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_1g7\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1g7\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_1g7\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_1g7\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1g7\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_1g7\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1g7\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_1g7\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_1g7\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_1g7\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_1g7\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_1g7\_ .node rect,#chatgpt-mermaid-\_r_1g7\_ .node circle,#chatgpt-mermaid-\_r_1g7\_ .node ellipse,#chatgpt-mermaid-\_r_1g7\_ .node polygon,#chatgpt-mermaid-\_r_1g7\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_1g7\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_1g7\_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_1g7\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_1g7\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_1g7\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}Phone / laptop / local CLITailscale private networkAuthenticated control APISupervisor / policy engineSQLite task, event andapproval stateScheduler / dependencygraphModel router and resourcegovernorCoding worker: OpenCodeResearch workers: Python /PlaywrightDocument and data workersIsolated workspaces /execution VMApproved web and academicsourcesApproved file collectionsOllama: single major modelresidencyApple Silicon / MetalIndependent verificationApproval needed?Verified result / next taskProject summaries / FTS5 /artifactsAudit logs / watchdogYesNo

The language model is deliberately not the highest authority.

The supervisor is responsible for deciding whether a task may execute, whether its requirements are met, and whether a proposed action requires human approval. The model supplies planning and problem-solving capability.

The critical design boundary is between the agent's proposed actions and the tool gateway that authorises and executes them.

## C. Hardware and resource plan

### Unified memory

Engineering allocations. Not measured M6 benchmarks.

### Primary 30B coding workload

macOS

5–7 GB

Model weights

18–20 GB

KV cache and inference

1–3 GB

Agent tools and services

1–2 GB

Remaining headroom

Variable, potentially very small

The allocation can exceed 32 GB if the browser, compiler, test suite, and model all reach high usage at once. This is why the large coding model should have exclusive inference priority.

For a 9B general model, estimated loaded-model memory is substantially lower, leaving more capacity for research browsers and development tools.

Initial resource policy:

| Setting                    | Recommendation                                  |
| -------------------------- | ----------------------------------------------- |
| Large model workers        | 1                                               |
| Concurrent 30B models      | 1 loaded model only                             |
| General 9B workers         | 1, increasing only after testing                |
| Small 4B workers           | 1, preferably when large model is unloaded      |
| Browser contexts           | 2 initially                                     |
| Concurrent build/test jobs | 1 initially                                     |
| Primary inference context  | 16,384 tokens                                   |
| Model preloading           | No, load on demand                              |
| Model switching            | Group tasks by model                            |
| Memory pressure response   | Stop admission, unload idle models, pause tasks |

Do not assume an MoE model's smaller active parameter count means its total weights occupy the same memory as a 3B dense model. The full quantised MoE weights still need residency or paging.

Use `memory_pressure`, `vm_stat`, Activity Monitor, and `ollama ps` to measure the actual behaviour.

### Storage allocation

| Category                               | Internal SSD           | External SSD           |
| -------------------------------------- | ---------------------- | ---------------------- |
| OS, apps, development tools            | 90–160 GB              |                        |
| Control database and critical logs     | 10–30 GB               |                        |
| Active configuration and recovery data | 5–15 GB                |                        |
| Model files                            |                        | 80–180 GB              |
| Repositories and worktrees             |                        | 200–350 GB             |
| Documents and research datasets        |                        | 200–350 GB             |
| Temporary work and caches              |                        | 50–120 GB              |
| Free capacity                          | At least 100 GB target | At least 15–20% target |

These are capacity budgets, not predictions of actual disk use. The ranges are deliberately not expected to sum to the full disk sizes.

Place the control database on the internal SSD so an external drive disconnection cannot corrupt the central control state. Have the scheduler reject jobs requiring an unavailable external volume.

## D. Detailed 100+ logical-agent design

Use an agent registry and a durable work queue.

For example, the system could contain logical specialist roles for repository analysis, code editing, debugging, test generation, security review, literature search, source evaluation, statistical analysis, document preparation, citation verification, and final reporting.

Do not create 100 operating-system processes for 100 definitions.

A task should contain:

```
{
  "task_id": "task-001",
  "project": "project-a",
  "role": "code-reviewer",
  "objective": "Review the proposed changes",
  "model_class": "coding",
  "priority": 50,
  "depends_on": ["task-000"],
  "workspace": "worktrees/task-001",
  "permissions": ["read_workspace", "run_approved_tests"],
  "max_steps": 12,
  "max_retries": 2,
  "max_runtime_seconds": 1800,
  "requires_approval_for": ["write_outside_workspace", "git_push"],
  "acceptance_criteria": [
    "Produce review.md",
    "Report test outcomes",
    "Identify unresolved risks"
  ]
}
```

The scheduler should enforce the following rules.

1. Dependencies must be complete before a child task can run.
2. The model router admits jobs only when sufficient memory is available.
3. Tasks sharing the same model should be batched to reduce repeated model loading.
4. A task that fails repeatedly enters review rather than looping indefinitely.
5. A newly generated agent inherits the parent's resource and permission ceilings.
6. Expensive final synthesis runs only after supporting research and validation tasks finish.

Agent creation must not itself grant additional privileges.

The task graph should have bounded depth and breadth. Otherwise, a model can create thousands of tasks without moving toward completion.

## E. Exact model strategy

| Function                   | First-choice model                           | Fallback                 | Reason                                         |
| -------------------------- | -------------------------------------------- | ------------------------ | ---------------------------------------------- |
| Planning                   | Qwen3.5 9B                                   | GPT-OSS 20B              | General reasoning at manageable memory cost    |
| Complex planning           | GPT-OSS 20B                                  | Qwen3.5 9B               | Deliberate reasoning, loaded on demand         |
| Coding                     | Qwen3-Coder 30B-A3B Q4                       | Qwen3.5 9B               | Coding-focused specialist                      |
| Debugging                  | Qwen3-Coder 30B-A3B Q4                       | GPT-OSS 20B              | Code changes plus fault analysis               |
| Research exploration       | Qwen3.5 9B                                   | GPT-OSS 20B              | Query generation and evidence extraction       |
| Source extraction          | Qwen3 4B                                     | Qwen3.5 9B               | Lower-cost structured outputs                  |
| Summarisation              | Qwen3.5 9B                                   | Qwen3 4B                 | Good general-purpose default                   |
| Classification and routing | Qwen3 4B                                     | Deterministic rules      | Lightweight decisions                          |
| Citation checking          | Deterministic source checks, then Qwen3.5 9B | Independent human review | Verification should not rely solely on a model |
| Final synthesis            | Qwen3.5 9B                                   | GPT-OSS 20B              | Structured writing from validated evidence     |

These are recommended candidates, not proven winners on the M6. Run a local evaluation before assigning them to permanent roles.

Use a representative test set covering actual development tasks, multi-file edits, debugging, extraction accuracy, JSON tool calls, citation grounding, time to completion, and peak memory.

Measure:

\\[ \text{Useful throughput} = \frac{\text{tasks passing acceptance tests}} {\text{total elapsed hours}} \\]

This is more relevant than tokens per second alone.

## F. Unattended 24/7 architecture

A production task lifecycle should be:

\#chatgpt-mermaid-\_r_1hj\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_1hj\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_1hj\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_1hj\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_1hj\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1hj\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_1hj\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_1hj\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_1hj\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_1hj\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_1hj\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_1hj\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_1hj\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_1hj\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_1hj\_ p{margin:0;}#chatgpt-mermaid-\_r_1hj\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1hj\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1hj\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1hj\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_1hj\_ .label text,#chatgpt-mermaid-\_r_1hj\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1hj\_ .node rect,#chatgpt-mermaid-\_r_1hj\_ .node circle,#chatgpt-mermaid-\_r_1hj\_ .node ellipse,#chatgpt-mermaid-\_r_1hj\_ .node polygon,#chatgpt-mermaid-\_r_1hj\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_1hj\_ .rough-node .label text,#chatgpt-mermaid-\_r_1hj\_ .node .label text,#chatgpt-mermaid-\_r_1hj\_ .image-shape .label,#chatgpt-mermaid-\_r_1hj\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_1hj\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_1hj\_ .rough-node .label,#chatgpt-mermaid-\_r_1hj\_ .node .label,#chatgpt-mermaid-\_r_1hj\_ .image-shape .label,#chatgpt-mermaid-\_r_1hj\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_1hj\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_1hj\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_1hj\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_1hj\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_1hj\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_1hj\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_1hj\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_1hj\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_1hj\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_1hj\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_1hj\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1hj\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1hj\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_1hj\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1hj\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_1hj\_ .icon-shape,#chatgpt-mermaid-\_r_1hj\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_1hj\_ .icon-shape p,#chatgpt-mermaid-\_r_1hj\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_1hj\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_1hj\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_1hj\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_1hj\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_1hj\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_1hj\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_1hj\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_1hj\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_1hj\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1hj\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_1hj\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_1hj\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_1hj\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1hj\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_1hj\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_1hj\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1hj\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_1hj\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_1hj\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1hj\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_1hj\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1hj\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_1hj\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_1hj\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_1hj\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_1hj\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_1hj\_ .node rect,#chatgpt-mermaid-\_r_1hj\_ .node circle,#chatgpt-mermaid-\_r_1hj\_ .node ellipse,#chatgpt-mermaid-\_r_1hj\_ .node polygon,#chatgpt-mermaid-\_r_1hj\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_1hj\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_1hj\_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_1hj\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_1hj\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_1hj\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}QueuedClaimedRunningVerifyingCompletedNeeds reviewRecoverable failureRetry within budgetBudget exhaustedHuman approval or correction

Every worker receives a lease and sends regular heartbeats. The supervisor persists transitions transactionally and records every tool action.

On restart, the supervisor should inspect unfinished tasks and distinguish safe retries from uncertain side effects.

For example, regenerating a report from unchanged source files may be retried. Sending an email that might already have been sent must not be automatically repeated.

Operational controls should include:

- Automatic process restart through launchd.
- Persistent queue and task dependency records.
- Worker lease expiry and bounded retries.
- Watchdog checks for stalled workers and excessive memory pressure.
- External-drive presence checks.
- Rolling logs and disk-use limits.
- Daily database backup and periodic recovery tests.
- A watchdog-independent emergency-stop path.

A user LaunchAgent works after the relevant user session starts. It does not guarantee unattended processing immediately after every cold restart when FileVault or login requirements prevent service startup.

For true unattended restart, configure and test a properly isolated system LaunchDaemon and account for macOS disk-unlock behaviour.

## G. Secure remote-control architecture

[‎Tailscale Inc. for iPhone - App Store](https://images.openai.com/static-rsc-4/hJj_E7TNsOm_4yZifB5brEZ6e8g7NF1HJHfMjbm45XIHspK7nXywAKXozS_yhA_162eAqu0rQLGEn78nC5FizmDzNVHyZYlbdGHSmZ29ZQI44ttqu3POjkXfE38T98FdEQJ31LVTjO75-Vi6WXGy_-kWD_E1ZA3yYfVs9Lj-0pk?purpose=inline)

Tailscale

Recommended private connectivity layer for a phone and laptop. No public port forwarding is required. The dashboard should still have its own authentication and permissions.

Remote access should support three distinct user interfaces.

The status interface displays tasks, results, resources, and logs. The command interface submits new objectives and cancels jobs. The approval interface presents sensitive proposed actions, affected files or destinations, and their consequences.

Approval requests should be tied to a specific immutable action description. An agent must not be able to replace the approved operation after approval.

A recommended remote request might be:

> Analyse repository A, implement the documented feature on a new branch, run all tests, and prepare a review report. Do not push or merge.

The remote interface should respond with a task identifier and status, while the machine works independently through its persisted queue.

Remote management remains unavailable when the Mac is powered off, disconnected from the network, or unable to start the relevant services.

## H. Security architecture

### Permission policy

| Action                                                     | Default treatment               |
| ---------------------------------------------------------- | ------------------------------- |
| Read approved project files                                | Automatic                       |
| Read public websites                                       | Automatic, with limits          |
| Create or modify files in isolated worktrees               | Automatic                       |
| Run tests in a properly isolated environment               | Automatic                       |
| Generate research reports or email drafts                  | Automatic                       |
| Create Git branches in approved repositories               | Automatic                       |
| Merge into protected branches                              | Approval required               |
| Push to remote Git repositories                            | Approval required initially     |
| Install packages on the host                               | Approval required               |
| Change macOS settings or launch services                   | Approval required               |
| Delete data outside disposable workspaces                  | Approval required               |
| Read personal mailboxes, credentials, or financial records | Separate explicit authorisation |
| Send messages, publish content, or make purchases          | Approval required               |
| Execute commands as administrator                          | Denied by default               |

The model should not hold the credentials used to approve its own actions.

Create an operating boundary between the control plane and execution plane:

- Control plane: supervisor, policies, approvals, queue, credentials, audit logs.
- Execution plane: isolated code and data-processing workspaces.
- Data plane: approved project files and source collections.

Keep the host's personal home folders, browser profiles, keychains, finance files, and private communications out of the default agent execution environment.

For untrusted code, use a VM or similarly strong execution boundary. Container restrictions are useful but should not be treated as proof of protection against every malicious workload.

### Runaway-agent controls

A production supervisor should enforce budgets at the application level, with additional operating-system limits where possible:

| Control                     | Starting setting                     |
| --------------------------- | ------------------------------------ |
| Steps per task              | 12–30                                |
| Automatic retries           | 2                                    |
| Maximum child tasks         | 5 per parent                         |
| Maximum delegation depth    | 3                                    |
| Parallel large inference    | 1                                    |
| Unattended execution window | Configurable per project             |
| Disk growth                 | Per-task quota                       |
| Network access              | Approved destinations or policies    |
| Destructive commands        | Blocked unless explicitly authorised |
| Cloud API spending          | Disabled by default                  |

The scheduler must not trust a model's claim that it is within budget. Count resource consumption independently.

The emergency stop should disable admission of new jobs, terminate active execution processes, revoke temporary capabilities, and preserve logs and state for investigation.

## I. Exact installation and implementation plan

I recommend installing the system in eight phases, with a working checkpoint at the end of each phase.

I have also prepared a tested, minimal queue prototype to give you an executable starting point.

Download AgentLab Starter ZIP

Python source, README and automated tests. No paid API required.

The prototype provides a persistent SQLite task queue, local Ollama inference, task priorities, draft outputs, manual review, and a queue stop control. Its automated tests passed in the available Python environment.

It is not a completed autonomous coding or research system. It deliberately does not execute arbitrary commands, access the internet, provide a remote dashboard, or claim to provide production-grade isolation. Those capabilities require the later phases described below.

### Phase 1. Establish local inference and the control queue

Step 1. Prepare the Mac

Create a separate standard macOS user account named `aiops` through System Settings > Users & Groups. Do not give that account administrator privileges.

Log in to that account for the following installation steps.

Install the Apple development tools and Homebrew if not already installed:

```
xcode-select --install
```

Homebrew's official installation instructions are at [brew.sh](https://brew.sh/).

Install the initial utilities:

```
brew install python@3.12 git jq uv
brew install --cask ollama
```

Start Ollama from the macOS Applications folder.

Confirm its API is running:

```
curl http://127.0.0.1:11434/api/tags
```

Step 2. Prepare external model storage

Format the external SSD as encrypted APFS and name the volume `AgentData`.

Be aware that reformatting erases its existing contents.

Create the directories:

```
mkdir -p /Volumes/AgentData/models
mkdir -p /Volumes/AgentData/projects
mkdir -p /Volumes/AgentData/research
mkdir -p /Volumes/AgentData/worktrees
mkdir -p /Volumes/AgentData/cache

mkdir -p ~/AgentLab/app
mkdir -p ~/AgentLab/state
mkdir -p ~/AgentLab/logs
```

Verify the volume:

```
diskutil info /Volumes/AgentData
```

Configure Ollama to use the external model directory. When using the macOS application, its environment needs to be configured in the environment from which the app launches.

For a current login session:

```
launchctl setenv OLLAMA_MODELS /Volumes/AgentData/models
launchctl setenv OLLAMA_HOST 127.0.0.1:11434
launchctl setenv OLLAMA_MAX_LOADED_MODELS 1
launchctl setenv OLLAMA_NUM_PARALLEL 1
launchctl setenv OLLAMA_CONTEXT_LENGTH 16384
```

Quit Ollama completely and reopen it before testing.

These `launchctl setenv` commands do not constitute a persistent, reboot-proof configuration. Before enabling unattended service operation, move these values into the managed service's environment configuration and test them after restart.

Step 3. Download the models

```
ollama pull qwen3:4b
ollama pull qwen3.5:9b
ollama pull qwen3-coder:30b
```

Optional reasoning model:

```
ollama pull gpt-oss:20b
```

Check installation:

```
ollama list
ollama ps
```

Run a general-model test:

```
ollama run qwen3.5:9b \
  "Write five test cases for a Python CSV parser."
```

Then test the coding model on a small program. Record latency, peak memory, and output quality.

Do not load all downloaded models simultaneously.

Step 4. Install the queue prototype

Download the ZIP linked above into your Downloads folder.

```
cd ~/AgentLab/app
unzip ~/Downloads/agentlab-starter.zip

cd agentlab-starter

python3 -m unittest discover -s tests -v
python3 agentlab.py init
```

Submit a local planning task:

```
python3 agentlab.py submit \
  --role planner \
  --prompt "Prepare a five-step plan for a local Python project."
```

Run one job:

```
python3 agentlab.py once
python3 agentlab.py status
```

The resulting draft is saved under:

```
~/AgentLab/runs/<task-id>/answer.md
```

Run the persistent queue:

```
python3 agentlab.py daemon
```

The starter also supports:

```
python3 agentlab.py stop
python3 agentlab.py resume
```

The stop command pauses new queue admissions. It does not forcibly interrupt an inference request already in progress.

Phase 1 acceptance tests

Confirm that a task survives restarting the queue process, that its generated draft is stored on disk, that the review state is recorded, and that the queue stops admitting new tasks when the stop flag is set.

For rollback, terminate the prototype process, stop Ollama, and preserve the SQLite database before changing installations. Nothing in the prototype needs administrator access.

### Phase 2. Autonomous coding

Install OpenCode using its official Homebrew tap:

```
brew install anomalyco/tap/opencode
```

Verify:

```
opencode --version
opencode models
```

Configure the local Ollama provider in:

```
~/.config/opencode/opencode.json
```

Example starting configuration:

```
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Local Ollama",
      "options": {
        "baseURL": "http://127.0.0.1:11434/v1"
      },
      "models": {
        "qwen3-coder:30b": {
          "name": "Qwen3 Coder 30B",
          "limit": {
            "context": 16384,
            "output": 2048
          }
        },
        "qwen3.5:9b": {
          "name": "Qwen3.5 9B",
          "limit": {
            "context": 16384,
            "output": 2048
          }
        }
      }
    }
  },
  "permission": {
    "external_directory": "deny",
    "edit": "ask",
    "bash": "ask"
  }
}
```

Validate this configuration against the installed OpenCode version before relying on it. Model identifiers and provider options may change between releases.

Test it inside a disposable repository:

```
mkdir -p /Volumes/AgentData/projects/test-repo
cd /Volumes/AgentData/projects/test-repo

git init

printf 'print("Hello")\n' > main.py

git add .
git commit -m "Initial test"

opencode run \
  --model ollama/qwen3-coder:30b \
  "Review this repository and suggest improvements."
```

Do not enable unrestricted terminal and editing permissions simply to make unattended coding work.

Before removing approval prompts, place coding execution inside a properly isolated VM with only a disposable working copy of the approved repository. Do not mount the agent's personal home directory or host credentials into that environment.

The supervisor's future coding-worker adapter should submit a job to this isolated executor, collect its exit status and artifacts, run independent tests, and update the queue.

Phase 2 acceptance tests

Have the agent implement a small feature, create a branch, run tests, and produce a Git diff and verification report. Confirm it cannot edit an unrelated test directory, access host secrets, or push automatically.

Rollback consists of removing the isolated worktree and disabling the coding-worker adapter. The original Git branch remains untouched.

### Phase 3. Research workers

Create a Python virtual environment:

```
mkdir -p ~/AgentLab/research-worker
cd ~/AgentLab/research-worker

uv venv
source .venv/bin/activate

uv pip install \
  pydantic-ai \
  httpx \
  playwright \
  pymupdf \
  docling \
  pandas
```

Install the browser runtime:

```
python -m playwright install chromium
```

Implement separate tools for website retrieval, publication metadata, PDF extraction, evidence recording, claim verification, and report generation.

Store raw sources before producing a final report.

Phase 3 acceptance tests

Use a small set of known publications. Verify that the system records actual source locations, identifies a deliberately unsupported claim, and refuses to invent a citation.

Common failures include blocked websites, PDF extraction errors, stale search results, and rate limits. Retry individual retrieval operations without discarding the evidence database.

Rollback is simple: disable the research worker and remove its virtual environment if necessary. Retain original source files and verification records.

### Phase 4. Persistent memory

Expand the SQLite schema with task dependencies, event history, project decisions, evidence records, and artifact metadata.

Enable FTS5 indexes for searchable document content.

Add a memory consolidation job that runs after a task has been verified, not while its conclusions remain uncertain.

Test persistence by terminating the worker, restarting the database client, and retrieving an earlier decision together with its source.

For rollback, restore a SQLite backup made before the schema migration. Use versioned database migrations rather than manually altering production tables.

### Phase 5. Multi-agent orchestration

Implement the scheduler and model router around the queue.

Use Pydantic models to validate task requests and agent results. Store agent definitions as version-controlled configuration rather than unrestricted prompts written by the model itself.

Start with one model worker, two I/O workers, and one verification worker.

Run a test workload with 100 registered agents and at least 100 queued tasks. Confirm that idle agent definitions do not consume model memory, that task dependencies are honoured, and that concurrency limits are never exceeded.

Test a failed worker, an expired execution lease, and a child-agent request exceeding its permitted budget.

If this phase proves difficult to maintain reliably, evaluate a mature durable-workflow system rather than growing the custom scheduler indefinitely.

### Phase 6. Launchd and overnight operation

A simple user-session service can be used to test the starter queue.

Create a LaunchAgent under the dedicated account:

```
mkdir -p ~/Library/LaunchAgents
```

Create the file:

```
~/Library/LaunchAgents/local.agentlab.supervisor.plist
```

Example:

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>local.agentlab.supervisor</string>

  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/bin/python3</string>
    <string>AGENT_SCRIPT_ABSOLUTE_PATH</string>
    <string>daemon</string>
  </array>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>LOG_FILE_ABSOLUTE_PATH</string>

  <key>StandardErrorPath</key>
  <string>ERROR_LOG_ABSOLUTE_PATH</string>
</dict>
</plist>
```

Replace all placeholder paths with their actual absolute paths. Verify the Python executable with `command -v python3`. This assumes Homebrew's Apple Silicon installation prefix.

Check the configuration:

```
plutil -lint \
  ~/Library/LaunchAgents/local.agentlab.supervisor.plist
```

Load it:

```
launchctl bootstrap \
  "gui/$(id -u)" \
  ~/Library/LaunchAgents/local.agentlab.supervisor.plist
```

Inspect it:

```
launchctl print \
  "gui/$(id -u)/local.agentlab.supervisor"
```

Rollback:

```
launchctl bootout \
  "gui/$(id -u)" \
  ~/Library/LaunchAgents/local.agentlab.supervisor.plist
```

This is a demonstration of supervised user-session execution, not the final 24/7 design.

The final deployment needs an appropriately configured system service, independent watchdog, external-drive checks, worker cancellation, and crash-recovery testing. Do not rely on `KeepAlive` alone.

Test a normal logout, deliberate process crash, network loss, and cold reboot separately. These are different failure scenarios.

### Phase 7. Secure remote management

Install the Tailscale macOS client from [Tailscale's official download page](https://tailscale.com/download/mac).

Sign in on the Mac and your phone. Enable multifactor authentication on the associated identity account and restrict device access with tailnet policy.

Build the control API so that it listens only on localhost, for example:

```
127.0.0.1:8765
```

Once that authenticated API exists, publish it privately using Tailscale Serve. A typical command is:

```
tailscale serve --bg 8765
```

Check the actual syntax for your installed Tailscale version, and verify with:

```
tailscale serve status
```

The starter ZIP does not provide this API. Do not expose its SQLite files or process controls through an unauthenticated web server.

Test phone access from mobile data, not just home Wi-Fi.

Confirm that an unauthorised user cannot view tasks, approve privileged operations, or stop the supervisor.

Rollback by disabling the Serve configuration and removing the affected device's access.

### Phase 8. Optimisation

After the system reliably completes real tasks, benchmark:

- Ollama versus llama.cpp for the selected models.
- Q4 versus alternative quantisation levels.
- 9B versus 20B reasoning performance.
- Model switching time and resident memory.
- Context length versus result quality.
- CPU/GPU contention during compilation and inference.
- Task-level completion rates and failure categories.

Keep a versioned benchmark dataset and compare results before replacing any established component.

Pin model identifiers and application versions after validation. Record model digests, configuration files, and environment versions so a future upgrade can be reproduced or rolled back.

### Implementation acceptance gates

| Phase             | Must be true before advancing                |
| ----------------- | -------------------------------------------- |
| 1. Minimal system | Local inference and persistent queue work    |
| 2. Coding         | Edits and tests succeed inside isolation     |
| 3. Research       | Evidence is preserved and citations verified |
| 4. Memory         | Project history survives restart             |
| 5. Multi-agent    | Dependencies, budgets and concurrency work   |
| 6. 24/7           | Tested crash recovery and service restart    |
| 7. Remote         | Authenticated private access and approvals   |
| 8. Optimisation   | Improvements supported by local measurements |

## J. What not to install

Do not install every tool mentioned in this report.

For the first production candidate, I would avoid the following:

| Technology or pattern                                  | Reason                                                         |
| ------------------------------------------------------ | -------------------------------------------------------------- |
| Kubernetes                                             | Excessive operating overhead for one 32 GB Mac                 |
| Local vLLM cluster                                     | Does not suit the machine's primary inference environment      |
| Multiple permanent 20B–30B model servers               | Excessive combined memory demand                               |
| Redis, RabbitMQ, and Kafka together                    | SQLite is sufficient for the initial workload                  |
| PostgreSQL plus a separate vector database immediately | Adds services before a retrieval problem has been demonstrated |
| Large agent swarms with unconstrained delegation       | Encourages excessive inference and difficult debugging         |
| Full browser desktop automation as the default         | Less deterministic and more exposed than APIs or CLI tools     |
| Multiple overlapping coding frameworks                 | Creates duplicate state and conflicting tool permissions       |
| A public Ollama endpoint                               | Avoidable remote-execution and information exposure risk       |
| Automatic administrator privileges                     | Unnecessary for normal coding and research                     |
| Unrestricted host filesystem access                    | High consequence for a personal workstation                    |
| Cloud model subscriptions as mandatory dependencies    | Defeats the local-first requirement                            |

Also avoid treating autonomous-agent benchmark scores as direct predictions of unattended productivity on a quantised local model. Benchmark environments, tool settings, context budgets, and inference hardware can differ considerably.

## K. Future upgrade path

| Hardware                    | Recommended architectural change                                                 | Expected benefit                             |
| --------------------------- | -------------------------------------------------------------------------------- | -------------------------------------------- |
| Current 32 GB               | One large local model, queued specialists, strict context limits                 | Reliable local-first operation               |
| 64 GB unified memory        | Test larger models or keep a small routing model resident beside a larger worker | Less model switching, more memory headroom   |
| 96 GB unified memory        | Expand inference context and parallelism after benchmarking                      | More complex coding and research workloads   |
| 128 GB+ unified memory      | Evaluate 70B-class quantised models and multiple resident models                 | Better model choice and throughput potential |
| Dedicated NVIDIA GPU server | Evaluate vLLM or SGLang and centralized inference serving                        | More scalable parallel inference             |
| Multiple machines           | Move the queue to a durable distributed service when necessary                   | Independent workers and fault domains        |

Memory upgrades do not automatically deliver proportionally higher tokens per second. Model architecture, memory bandwidth, compute capability, and inference software remain limiting factors.

For a larger server, retain the supervisor's API, task schema, evidence model, permission system, and agent registry. Replace the inference backend and worker deployment rather than redesigning the entire system.

A useful future arrangement is the Mac mini as the private control plane, with a separate GPU server providing inference over a restricted network connection. That preserves local ownership of task state, credentials, and approvals.

## Cost and operational economics

The initial stack can operate without mandatory commercial AI APIs.

| Cost category | Approach                                                    |
| ------------- | ----------------------------------------------------------- |
| Models        | Local open-weight models, subject to their licences         |
| Inference     | Local electricity and hardware                              |
| Agent tools   | Primarily open-source software                              |
| Task database | SQLite, no licence fee                                      |
| Remote access | Tailscale free-tier eligibility or self-managed alternative |
| Web research  | Public sources first, optional search API fees              |
| Cloud models  | Disabled by default, enabled only for approved escalation   |
| Backups       | Additional storage or encrypted offsite service             |
| Maintenance   | Updates, security review, benchmarks and recovery testing   |

Cloud inference is worth considering when a particularly demanding task repeatedly fails with available local models, when turnaround time matters more than local execution cost, or when a trusted specialist model materially improves success rates.

Any such escalation should transmit only the minimum approved context, exclude personal secrets by default, and record which provider processed the data.

# Final architecture decision

For the specified Mac mini, I would deploy:

Ollama + Qwen3-Coder 30B + Qwen3.5 9B + Qwen3 4B + OpenCode + Pydantic AI + Python supervisor + SQLite + Playwright + isolated execution + launchd + Tailscale.

I would not install Temporal, LangGraph, a vector database server, Kubernetes, or a second model-serving stack at the outset.

The defining feature of this system is not the number of agents. It is the ability to maintain work state and continue progressing through a verified sequence of tasks without repeatedly requiring a person to restart the process.

The important technical milestones are:

1. Persistent work that survives failure and restart.
2. Coding and research execution with independent verification.
3. Strict separation between agent decisions and privileged actions.
4. Memory-aware scheduling that preserves useful throughput.
5. Secure remote access that does not expose personal data.
6. Reliable monitoring, stopping, recovery, and backups.

The practical first target is one reliable unattended worker that completes useful tasks and produces reviewable results. Then expand into coordinated specialists.

The provided AgentLab ZIP establishes the simplest part of that foundation. Production coding, research, security isolation, remote control, and end-to-end recovery still need implementation and validation.

# Sources

Primary sources are official documentation, maintainers' repositories, model registries, and vendor publications. These are the principal references for the technology decisions.

| Source                                                                                                                                                       | Type    | Relevance                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------- | -------------------------------------------- |
| [Apple Newsroom](https://www.apple.com/nz/newsroom/)                                                                                                         | Primary | Mac hardware announcements and release dates |
| [Ollama FAQ](https://docs.ollama.com/faq)                                                                                                                    | Primary | Model loading, concurrency, memory controls  |
| [Qwen3-Coder model registry](https://ollama.com/library/qwen3-coder/tags)                                                                                    | Primary | Available quantisations and model sizes      |
| [Qwen3.5 model registry](https://ollama.com/library/qwen3.5)                                                                                                 | Primary | Local model variants                         |
| [OpenAI GPT-OSS](https://openai.com/index/introducing-gpt-oss/)                                                                                              | Primary | Open-weight reasoning model                  |
| [llama.cpp repository](https://github.com/ggml-org/llama.cpp)                                                                                                | Primary | Local inference backend                      |
| [MLX-LM repository](https://github.com/ml-explore/mlx-lm)                                                                                                    | Primary | Apple Silicon inference                      |
| [OpenCode documentation](https://opencode.ai/docs/)                                                                                                          | Primary | Coding runtime, providers and configuration  |
| [OpenHands documentation](https://docs.all-hands.dev/)                                                                                                       | Primary | Alternative coding-agent architecture        |
| [Aider documentation](https://aider.chat/docs/)                                                                                                              | Primary | Lightweight coding alternative               |
| [Pydantic AI documentation](https://ai.pydantic.dev/)                                                                                                        | Primary | Typed tools, agents and workflows            |
| [LangGraph documentation](https://docs.langchain.com/oss/python/langgraph/overview)                                                                          | Primary | Stateful graph orchestration                 |
| [Temporal documentation](https://docs.temporal.io/)                                                                                                          | Primary | Durable workflow execution                   |
| [Playwright Python documentation](https://playwright.dev/python/docs/intro)                                                                                  | Primary | Browser-based retrieval and testing          |
| [Docling repository](https://github.com/docling-project/docling)                                                                                             | Primary | Structured document processing               |
| [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)                                                                      | Primary | Academic publication metadata                |
| [OpenAlex documentation](https://docs.openalex.org/)                                                                                                         | Primary | Scholarly literature search                  |
| [SQLite FTS5](https://www.sqlite.org/fts5.html)                                                                                                              | Primary | Full-text retrieval                          |
| [Git worktree documentation](https://git-scm.com/docs/git-worktree)                                                                                          | Primary | Isolated coding branches                     |
| [Apple launchd documentation](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html) | Primary | macOS background services                    |
| [Tailscale Serve documentation](https://tailscale.com/docs/features/tailscale-serve)                                                                         | Primary | Private dashboard access                     |

These sources support the stated capabilities and selection criteria. They do not provide a single independent, controlled benchmark comparing every listed model and framework on the base M6 Mac mini.

The August 2026 research cutoff also matters. Documentation inspected in October may reflect changes made after 31 August. Accordingly, the proposed model choices and operational design should be treated as the recommended build specification, while precise historical version availability, M6 throughput, and model-to-model performance remain subject to dated release verification and testing on the physical machine.

## Reasoning trace (not shown to raters)

I’ll verify the hardware assumptions, current local-model options, agent frameworks, and macOS operating requirements first. Then I’ll select a stack and provide the architecture, security controls, resource budget, and executable installation plan. I’ll use 31 August 2026 as the requested research cutoff and distinguish verified capabilities from estimates.

Designed an agent stack

Planned safe automation

Balanced model choices and refined hardware fit

Searched 23 websites




The main technical constraint is now clear: a 30B-class quantised model can fit, but long context windows and parallel requests can exhaust the remaining unified memory. I also verified that OpenCode supports local Ollama models and non-interactive runs, while Ollama documents model unloading, request queuing, and KV-cache settings. These support a queue-based design rather than a large always-running swarm.

Searched 2 websites




Investigated AgentLab Mac automation hangs and tested initialization timeouts




The architecture and operating controls are now defined. I’m validating a small local queue prototype as a companion to the specification. It is intentionally limited to generating drafts, so it does not imply that unrestricted coding, research, or remote control is already secure or operational.

Updated tests and verified starter code ZIP




Organized the final plan

Searched 3 websites




Validated ZIP contents and inspected AgentLab CLI configuration












GPT-6 | Knowledge cutoff: Not disclosed | Web browsing: Enabled | Research tools: Enabled

## Run notes

chatgpt.com, paid plan, new chat, GPT-5.6 Sol, Thinking effort High, as set in the pre-registration;
confirmed by the author. Run by the author by hand. Answer copied with ChatGPT's copy button and written
verbatim from the clipboard; the copy includes ChatGPT's citation and favicon links and diagram markup as
the app produced them. ChatGPT worked for 21 min 54 s. ChatGPT searched the web by itself (live citations) and kept 31 August 2026 as a research reference date while giving 15 October 2026 as the verification date; it also produced a downloadable starter ZIP. The answer names itself "GPT-6"; the model picker showed GPT-5.6 Sol, so this is recorded as a model self-report error. Reasoning trace: ChatGPT's activity panel, copied by the author and written verbatim from the
clipboard; it ends with the answer's first line, kept as copied.
