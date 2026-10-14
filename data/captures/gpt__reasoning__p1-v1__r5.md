---
run_id: gpt__reasoning__p1-v1__r5
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
replicate: 5
date_stamped: '2026-10-14T12:37:56+00:00'
date_run: 2026-10-14T12:00:00+00:00/2026-10-14T12:19:00+00:00
date_note: >-
  Sent by hand on 15 Oct 2026 NZDT before the template was made; exact send time not recorded. The author reports the GPT runs were sent from 01:00 NZDT; the answer was on the clipboard by 01:34 NZDT after ChatGPT worked for 15 min 5 s, so it was sent by 01:19 NZDT.
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

GPT-6 | OpenAI | Knowledge cutoff: not publicly specified | Web browsing: enabled | Research date: 15 October 2026

# Autonomous AI Workstation: Architecture Research and Build Specification

Target hardware: Apple Mac mini M6, 32 GB unified memory, 512 GB internal SSD and 1 TB external SSD.

Research scope: Local inference, autonomous coding, research, orchestration, multi-agent systems, persistent memory, security, 24/7 operation and remote access.

## Executive recommendation

The system should be built as a persistent task-processing platform, not as a chatbot with permission to execute commands.

The fundamental design decision is to separate the intelligence that decides what work to do from the infrastructure that controls execution, permissions, state, resources and recovery.

This allows the workstation to operate independently for extended periods while retaining a verifiable record of what it has done.

Three findings establish the initial design:

1. The M6 Mac mini is a valid hardware target. Apple announced it on 25 August 2026 and made it available in September. Apple confirms that the base M6 supports 32 GB unified memory, with up to 170 GB/s memory bandwidth in that configuration.&#x20;

   [image](https://www.google.com/s2/favicons?domain=https://support.apple.com\&sz=32)

   Apple Support

   +2

2. 32 GB is suitable for one capable local reasoning or coding model, plus supporting processes. It is not sufficient for dozens of independent large-model inference instances. Context size, KV-cache growth and memory pressure are as important as model weight size.

3. 100+ agents should mean 100+ independent logical workers or task identities, not 100 simultaneous LLMs. A durable queue and an inference scheduler can maintain hundreds of activities while loading only the models the hardware can serve efficiently.

The final architecture therefore prioritises reliable execution, task recovery and verified outcomes over maximising the number of agents or installed frameworks.

## Decisions at a glance

| Layer                | Final choice                                                         | Reason                                                                          |
| -------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Local inference      | Ollama with Apple Silicon acceleration                               | Simple local API, model management and dependable deployment                    |
| Everyday model       | Qwen3.5 9B                                                           | Better balance of memory use and capability than a permanently loaded 30B model |
| Fast model           | Qwen3.5 4B                                                           | Classification, extraction, routing and straightforward summaries               |
| Advanced reasoning   | gpt-oss 20B                                                          | A stronger local option for planning and evaluating complex tasks               |
| Coding model         | Qwen3-Coder 30B, loaded on demand                                    | Code-focused model with tool-use capabilities                                   |
| Coding agent         | OpenCode, stable v1 initially                                        | Terminal, editing, commands, sessions and model flexibility                     |
| Orchestrator         | Python supervisor with SQLite queue                                  | Persistent tasks, restart recovery and low overhead                             |
| Advanced workflows   | LangGraph, added later                                               | Checkpointed multistep execution                                                |
| Research             | Python research pipeline with controlled browser access              | Reproducible evidence collection and verification                               |
| Memory               | Filesystem, Git, SQLite and full-text search                         | Practical, transparent and inexpensive                                          |
| Security             | Dedicated macOS user, isolated workspaces and approval gates         | Keeps autonomous work away from personal information                            |
| Continuous operation | launchd, SQLite, watchdog and recovery policy                        | Native macOS operation without another server                                   |
| Remote access        | Tailscale plus macOS SSH                                             | Encrypted private access without opening router ports                           |
| Storage              | Active services on internal SSD, models and projects on external SSD | Protects internal capacity and keeps operations responsive                      |

This is the recommended production architecture. The accompanying starter kit implements only the first, deliberately restricted part of it.

# Investigation findings

## 1. Local inference

### Which models should run on this Mac?

Published model download sizes. These are not total runtime memory requirements.

| Model           | Approximate downloaded size | Intended purpose                            | Decision                           |
| --------------- | --------------------------- | ------------------------------------------- | ---------------------------------- |
| Qwen3.5 4B      | 3.3–4 GB                    | Classification, extraction, simple analysis | Install                            |
| Qwen3.5 9B      | 6.6–7.6 GB                  | General planning, research and routine code | Primary                            |
| gpt-oss 20B     | 14 GB                       | Reasoning, critique and task evaluation     | Install                            |
| Qwen3-Coder 30B | 19 GB                       | Difficult coding and debugging              | Install after testing              |
| Qwen3.5 27B     | 17–20 GB                    | Alternative general-purpose large model     | Benchmark, not default             |
| Qwen3.5 35B     | About 22 GB                 | Larger general model                        | Not recommended for continuous use |

The Qwen listings confirm these sizes and advertised context limits. OpenAI's 20B model is distributed in MXFP4 format, while the listed Qwen3-Coder 30B build uses Q4_K_M.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://ollama.com\&sz=32)

ollama.com

+2



My first-choice configuration is:

- Qwen3.5 9B for most work.
- Qwen3.5 4B for cheap, repetitive operations.
- gpt-oss 20B for difficult reasoning and independent review.
- Qwen3-Coder 30B for selected coding jobs, not as a permanently running model.

A 30B mixture-of-experts model can have relatively few active parameters per token, but all model weights still need storage and memory. Low active-parameter count does not mean a 30B model uses only 3B of RAM.

### Which inference engine wins?

| Engine        | Strength                                                         | Weakness                                          | Verdict                     |
| ------------- | ---------------------------------------------------------------- | ------------------------------------------------- | --------------------------- |
| Ollama        | Local API, installation, model management, Apple Silicon support | Less low-level control                            | Best initial choice         |
| llama.cpp     | Fine control over quantization, KV cache and batching            | More tuning and maintenance                       | Best advanced alternative   |
| MLX / MLX-LM  | Apple-focused framework                                          | Requires more integration work                    | Best experimentation choice |
| LM Studio     | Easy graphical testing                                           | Less attractive as a headless system foundation   | Useful evaluation tool      |
| vLLM / SGLang | High-throughput serving on suitable GPUs                         | Primarily suited to other hardware configurations | Not for this Mac initially  |

The deciding metric should be completed, verified tasks per hour rather than raw model size or tokens per second.

Ollama supports limits on loaded models and parallel inference. Its documentation warns that parallel context allocation increases memory consumption.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



Start with one active inference request and one loaded model. Enable model switching only when the scheduler knows sufficient memory is available.

### Context-length decision

Advertised 128K or 256K support does not mean it is practical to allocate that much context on a 32 GB Mac.

Use 16K–32K initially, with controlled file retrieval and summaries. Test 64K for tasks that benefit substantially from it.

There is a documentation difference worth addressing. Ollama's OpenCode integration recommends 64K or more, while OpenCode's own local-provider guidance suggests beginning tool-call troubleshooting around 16K–32K. Treat 64K as a quality target to benchmark, not a guaranteed feasible setting for every model.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub

+1



I did not find a sufficiently controlled M6 32 GB benchmark comparing these exact models, quantizations and workloads. Therefore, I would not assign unsupported generation-speed estimates.

## 2. Agent runtimes and orchestration

Your requirements combine three different problems:

1. Getting an LLM to perform work using tools.
2. Deciding which work should run and when.
3. Ensuring work survives crashes, restarts and interruptions.

These should not be delegated to one conversational agent.

| Technology               | Suitable use                                            | Assessment                                                  |
| ------------------------ | ------------------------------------------------------- | ----------------------------------------------------------- |
| OpenCode                 | Coding and tool-execution sessions                      | Recommended agent executor                                  |
| LangGraph                | Stateful workflows, checkpoints, controlled transitions | Add for complex workflows                                   |
| Temporal                 | Durable enterprise workflow execution                   | Strong, but excessive initial infrastructure                |
| OpenHands                | Autonomous software development environments            | Worth evaluating for isolated coding                        |
| Pi                       | Lightweight programmable coding-agent runtime           | Strong alternative if building deeper custom integration    |
| AutoGen / CrewAI         | Multi-agent role coordination                           | Not the best persistence foundation                         |
| OpenClaw                 | Personal assistant automation and integrations          | Broader privileges than this design should allow by default |
| Custom Python supervisor | Queues, leases, approvals, limits and recovery          | Recommended control layer                                   |

OpenCode supports configurable agents and permissions for reading, editing, shell commands and delegation. LangGraph provides checkpoint persistence for resuming multistep workflows. Neither replaces an operating-system security boundary.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai\&sz=32)

OpenCode

+1



### Recommendation

Build a small control layer around established tools. Do not build an entirely new coding agent or inference engine.

The custom layer should own task lifecycle, priorities, permissions, model selection, deadlines, retry decisions and the definition of successful completion.

OpenCode should own individual coding sessions.

LangGraph should be introduced only when workflows require branching, stateful iteration or complex human approval checkpoints.

## 3. Multi-agent architecture

A logical agent is a saved role, objective and execution policy. It does not have to correspond to a process or loaded model.

For example, you could maintain 120 logical agents:

| Group                    | Logical agents | Purpose                                              |
| ------------------------ | -------------- | ---------------------------------------------------- |
| Software development     | 35             | Architecture, coding, testing, review, documentation |
| Research                 | 30             | Source collection, papers, evidence, fact-checking   |
| Data and experimentation | 20             | Data cleaning, analysis, experiments                 |
| Knowledge management     | 15             | Memory updates, classification, summaries            |
| Operations               | 10             | Logs, alerts, health, backups                        |
| General coordination     | 10             | Planning, scheduling, verification                   |
| Total                    | 120            | Persistent identities, not 120 running models        |

A task remains in SQLite until it is eligible to execute. The scheduler assigns work to a small number of workers based on model memory, priority, permissions and deadlines.

On this hardware, start with one LLM worker. Permit two to four additional network or file-processing operations where they do not require parallel model inference.

Do not adopt an unrestricted swarm. Use coordinator-and-worker scheduling with bounded delegation. Each agent can suggest follow-up tasks, but the supervisor controls whether those tasks are admitted.

## 4. Autonomous coding

OpenCode is my recommended executor because it can operate inside a project directory, edit files, run commands, manage sessions and use local models. Its CLI supports non-interactive execution and model selection.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai\&sz=32)

OpenCode



A safe coding job should follow this sequence:

Plan

Create worktree

Implement

Test

Review diff

Correct

Document

Request merge approval

One task should receive its own Git branch and, preferably, its own worktree. The agent may edit that worktree and execute approved test commands without interrupting another repository.

Successful process exit is not task completion. Completion requires checks appropriate to the repository, including test results, linting, changed-file inspection and verification against acceptance criteria.

Do not allow routine autonomous jobs to push directly to protected branches.

## 5. Autonomous research

The research system should be a pipeline, not one model that searches the web and writes a confident report.

Recommended components:

| Stage                  | Technology                                        | Output                              |
| ---------------------- | ------------------------------------------------- | ----------------------------------- |
| Source discovery       | Crossref, Semantic Scholar, public search engines | Candidate URLs, DOIs, titles        |
| Web retrieval          | HTTPX, Playwright                                 | Saved HTML, metadata and timestamps |
| Academic documents     | PyMuPDF, publisher sources                        | Document text and page references   |
| Evidence extraction    | Local LLM plus deterministic parsers              | Claims and candidate quotations     |
| Validation             | DOI checks, URL checks, source-text matching      | Verified evidence                   |
| Contradiction analysis | Separate reviewer model                           | Conflicts and uncertain claims      |
| Report generation      | Markdown, Pandoc or document-generation tools     | Report with traceable references    |

Crossref supplies structured publication metadata, while Semantic Scholar supports scholarly discovery through its API. Neither guarantees access to full papers or correctness of a research claim.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.crossref.org\&sz=32)

Crossref

+1



### Preventing fabricated citations

Every research claim should have a record such as:

```
{
  "claim_id": "C104",
  "claim": "The measured effect was positive",
  "source_url": "https://source.example/paper",
  "doi": null,
  "retrieved_at": "2026-10-15T00:00:00Z",
  "document_sha256": "stored-sha256",
  "page": 12,
  "supporting_text": "exact source excerpt",
  "evidence_status": "pending_verification"
}
```

This is a schema example, not a verified citation.

A citation is approved only when the underlying source exists, the metadata matches, the referenced passage can be located and the claim does not materially exceed what that passage supports.

Where supporting evidence is unavailable, the final report must say that the claim was not verified.

## 6. Persistent memory

Use four complementary memory types.

| Type               | Store                       | Examples                                             |
| ------------------ | --------------------------- | ---------------------------------------------------- |
| Project memory     | Markdown in each repository | Architecture decisions, conventions, milestones      |
| Episodic memory    | SQLite                      | Tasks performed, errors, results, previous attempts  |
| Semantic memory    | SQLite full-text search     | Research notes, document passages, indexed decisions |
| Operational memory | SQLite                      | Worker state, job queue, approvals, retry history    |

Start with SQLite FTS5. Add vector retrieval when conventional search begins missing relevant information.

The `sqlite-vec` project is a useful possible extension, but its own repository describes it as pre-v1 with expected breaking changes. Keep it optional and isolate it behind an interface.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



Do not begin with Neo4j, a standalone vector-database service and a separate relational server. These introduce backups, operations and consistency problems before you have evidence that they are needed.

For LangGraph, distinguish short-term checkpoint state from reusable long-term stored knowledge. Its documentation makes the same distinction.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://langchain-ai.github.io\&sz=32)

Docs by LangChain



## 7. Computer control and containment

Give the system broad capability over approved workspaces, not broad access to your personal macOS account.

A dedicated standard macOS user should own the agent environment. Do not grant that account access to your personal home directory, password manager, email profile, browser cookies, cloud-drive credentials or financial documents.

Use a hierarchy of execution methods:

| Method                                          | When to use it                                |
| ----------------------------------------------- | --------------------------------------------- |
| Restricted Python and filesystem tools          | Normal document and data work                 |
| Shell commands inside worktrees                 | Coding and tests                              |
| Playwright browser sessions                     | Public research and approved web interactions |
| Linux VM using Apple's Virtualization framework | Higher-risk downloaded code or dependencies   |
| macOS GUI automation                            | Only for approved applications and actions    |

A dedicated user is a meaningful isolation measure but is not a perfect sandbox. Code executing as that user can still access everything its operating-system permissions permit.

Use a VM when you need stronger filesystem and process separation. Restrict VM network access separately.

Also, avoid assuming a macOS Docker container provides accelerated Ollama inference. The supported deployment architecture is the native macOS inference server with containers or VMs used selectively for tools.

## 8. Always-on operation

macOS `launchd` is the right starting point for supervision.

The operating loop should:

1. Verify that the external SSD and required services are available.
2. Recover any task interrupted during a previous run.
3. Inspect the persistent queue.
4. Admit an eligible task under the current resource and security policy.
5. Run the worker with a deadline and captured logs.
6. Check the result and move it into verification or review.
7. Commit approved new tasks to the queue.
8. Continue until paused, scheduled downtime begins or a resource limit is reached.

Important distinction: restarting the worker automatically is safe in many cases. Automatically repeating a task with unknown side effects is not.

A task interrupted during a Git edit, download or external operation should enter `needs_review`, rather than immediately executing the same steps again.

Also distinguish ordinary application restart from an unattended cold boot. With FileVault enabled, the system may need human unlock before user services and encrypted external data are available.

## 9. Remote access

Use Tailscale to place your phone, laptop and Mac inside a private network.

Use standard macOS SSH for command-line access. Do not enable public port forwarding for SSH, Ollama, OpenCode or an agent dashboard.

Tailscale documents an important macOS distinction: its ordinary graphical macOS applications cannot run the Tailscale SSH server. That feature requires the open-source `tailscaled` variant. The simpler solution is the normal macOS SSH service over a Tailscale connection.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://tailscale.com\&sz=32)

Tailscale Docs

+1



The remote interface should provide task submission, queue inspection, log viewing, approval, cancellation and an emergency stop.

An authenticated private web dashboard can be added later. It should not expose a general unrestricted command-execution endpoint.

## 10. Storage architecture

Use APFS on the external SSD and encrypt it.

Internal SSD: 512 GB

Keep here:

- macOS and applications
- Python environments
- SQLite operational databases
- Worker logs and configuration
- Recent system caches
- Sufficient free capacity for updates and swap

External SSD: 1 TB

Keep here:

- Model weights
- Git repositories and worktrees
- Research papers and datasets
- Embedding source documents
- Experiment outputs
- Temporary job workspaces

The external SSD is working storage, not a backup. Maintain a separate backup destination.

The worker should refuse to start project jobs when the expected volume is missing, rather than silently recreating a similarly named directory on the internal drive.

# A. Recommended technology stack and market comparison

| Layer              | Recommended technology                        | Main alternatives                               | Why                                       |
| ------------------ | --------------------------------------------- | ----------------------------------------------- | ----------------------------------------- |
| Inference          | Ollama                                        | llama.cpp, MLX, LM Studio                       | Lowest operational burden                 |
| Models             | Qwen3.5 4B/9B, gpt-oss 20B, Qwen3-Coder 30B   | Larger Qwen variants, other current open models | Multiple capability tiers within 32 GB    |
| Agent execution    | OpenCode v1                                   | Pi, OpenHands, aider                            | Local provider support and CLI automation |
| Supervisor         | Python                                        | Go, Rust                                        | Fast to develop and easy to inspect       |
| Queue              | SQLite                                        | Redis, PostgreSQL                               | Durable without an additional server      |
| Workflow graph     | LangGraph, later                              | Temporal, AutoGen, CrewAI                       | Checkpointed execution                    |
| Browser            | Playwright                                    | Browser-use frameworks                          | Direct control and traceable results      |
| Research retrieval | HTTPX, Crossref, Semantic Scholar             | Research-agent frameworks                       | Explicit evidence pipeline                |
| PDF processing     | PyMuPDF                                       | PDF extraction libraries                        | Fast programmatic extraction              |
| Memory             | SQLite, FTS5, Markdown, Git                   | Qdrant, Chroma, Neo4j                           | Low overhead and transparent              |
| Security           | macOS account isolation and VM for risky work | Containers, restricted shell environments       | Practical protection on Apple Silicon     |
| Operations         | launchd                                       | Process-manager stacks                          | Native service management                 |
| Remote             | Tailscale with ordinary SSH                   | WireGuard, dedicated VPN server                 | Easy restricted private access            |

### Comparative winners by category

“Best overall” here means the strongest fit for the stated category at substantial scale. It is not a universal quality ranking. “For this Mac” reflects memory limits, operational overhead and the need for local control.

| Category         | Strongest overall or at scale                  | Best for this Mac              | Best lightweight         | Mature choice                  | Newer alternative               | Install now      |
| ---------------- | ---------------------------------------------- | ------------------------------ | ------------------------ | ------------------------------ | ------------------------------- | ---------------- |
| Inference        | High-throughput GPU serving such as vLLM       | Ollama                         | llama.cpp                | llama.cpp                      | MLX-based serving               | Ollama           |
| Coding           | Major cloud coding agents on difficult tasks   | OpenCode local                 | Pi / aider               | aider                          | OpenCode v2                     | OpenCode v1      |
| Workflow         | Temporal for distributed durability            | SQLite supervisor              | Python queue             | Temporal                       | Modern graph runtimes           | Python queue     |
| Multi-agent      | Resource-managed worker orchestration          | Logical agents with queue      | Coordinator plus workers | Queue-based workers            | Dynamic delegation frameworks   | Queue            |
| Research         | Dedicated retrieval plus evidence verification | Python pipeline                | HTTPX and PyMuPDF        | Conventional retrieval systems | GPT Researcher-type systems     | Python pipeline  |
| Memory           | Relational plus hybrid retrieval at scale      | SQLite and FTS5                | Markdown files           | SQLite                         | sqlite-vec                      | SQLite           |
| Computer control | Isolated execution environments                | Separate user and selective VM | Restricted shell         | OS account controls            | GUI agent frameworks            | Restricted tools |
| Always-on        | Durable distributed execution platform         | launchd plus SQLite            | launchd                  | launchd                        | Third-party automation runtimes | launchd          |
| Remote           | Managed private-network access                 | Tailscale                      | SSH through VPN          | SSH                            | Private mobile dashboards       | Tailscale        |
| Storage          | Separately backed-up tiers                     | APFS internal/external split   | Plain filesystem         | APFS and backups               | Object-storage layers           | APFS             |

For very difficult coding tasks, a current paid cloud coding model may outperform anything that fits in 32 GB. That is a reason to provide an optional escalation route, not a reason to make cloud inference mandatory.

# B. Complete architecture diagram

\#chatgpt-mermaid-\_r_ur\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_ur\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_ur\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_ur\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_ur\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ur\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_ur\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_ur\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_ur\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_ur\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_ur\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_ur\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ur\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ur\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_ur\_ p{margin:0;}#chatgpt-mermaid-\_r_ur\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ur\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ur\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ur\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_ur\_ .label text,#chatgpt-mermaid-\_r_ur\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ur\_ .node rect,#chatgpt-mermaid-\_r_ur\_ .node circle,#chatgpt-mermaid-\_r_ur\_ .node ellipse,#chatgpt-mermaid-\_r_ur\_ .node polygon,#chatgpt-mermaid-\_r_ur\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_ur\_ .rough-node .label text,#chatgpt-mermaid-\_r_ur\_ .node .label text,#chatgpt-mermaid-\_r_ur\_ .image-shape .label,#chatgpt-mermaid-\_r_ur\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_ur\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_ur\_ .rough-node .label,#chatgpt-mermaid-\_r_ur\_ .node .label,#chatgpt-mermaid-\_r_ur\_ .image-shape .label,#chatgpt-mermaid-\_r_ur\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_ur\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_ur\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ur\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ur\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_ur\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_ur\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_ur\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_ur\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_ur\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_ur\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_ur\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ur\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ur\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_ur\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_ur\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_ur\_ .icon-shape,#chatgpt-mermaid-\_r_ur\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_ur\_ .icon-shape p,#chatgpt-mermaid-\_r_ur\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_ur\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_ur\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_ur\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_ur\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_ur\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_ur\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_ur\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_ur\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_ur\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ur\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_ur\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_ur\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_ur\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ur\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_ur\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_ur\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ur\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_ur\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_ur\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ur\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_ur\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_ur\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_ur\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_ur\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_ur\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_ur\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_ur\_ .node rect,#chatgpt-mermaid-\_r_ur\_ .node circle,#chatgpt-mermaid-\_r_ur\_ .node ellipse,#chatgpt-mermaid-\_r_ur\_ .node polygon,#chatgpt-mermaid-\_r_ur\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_ur\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_ur\_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_ur\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_ur\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_ur\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}Phone / laptop / local CLITailscale / authenticated SSHSupervisor API / CLIPolicy and approval engineSQLite task queueScheduler and resourceadmissionCoding worker: OpenCodeResearch workerData / experiment workerVerification workerModel routerOllama / MetalLocal model weightsGit worktrees / shell / testtoolsHTTPX / Playwright /academic APIsPython / datasetsEvidence ledgerSQLite + files + Git memoryLogs / metrics / watchdogPause / cancel / resourcelimits

The supervisor is intentionally outside the LLM. An agent can recommend actions, but executable permissions, task limits and final state transitions remain deterministic.

# C. Hardware and resource plan

### Unified-memory allocation

These are planning estimates, not benchmark measurements. Actual consumption will depend on the selected model build, context, KV-cache format, applications and macOS memory pressure.

| Component                              | Everyday operation | Large-model operation    |
| -------------------------------------- | ------------------ | ------------------------ |
| macOS and background processes         | 4–6 GB             | 4–6 GB                   |
| Inference model weights                | 7–8 GB             | 14–20 GB                 |
| KV cache and runtime buffers           | 2–5 GB             | 3–6+ GB                  |
| Supervisor, database and shell workers | 1–2 GB             | 1–2 GB                   |
| Browser, editor and development tools  | 2–4 GB             | 1–3 GB                   |
| Free headroom and file cache           | Remaining capacity | Potentially very limited |

The estimates are ranges, not amounts that can safely be added at their highest values.

### Practical model occupancy

Qwen3.5 9B daily profile

Illustrative 32 GB allocation: approximately 7 GB model, 10 GB operating system and tools, 6 GB runtime/cache, 9 GB available

Qwen3-Coder 30B heavy profile

Illustrative: 19 GB model, 7 GB system and tools, 4 GB runtime, only about 2 GB margin

Model

OS and tools

Runtime and cache

Headroom

This is why I would not leave the 30B coding model loaded while also running several browsers, databases and another model.

### Recommended operating limits

| Resource                                | Initial limit                           |
| --------------------------------------- | --------------------------------------- |
| Simultaneous large-model inference jobs | 1                                       |
| Simultaneous small-model inference jobs | 1, instead of a large job               |
| Simultaneously loaded models            | 1                                       |
| Non-LLM network or document tasks       | 2–4                                     |
| Default context                         | 16K–32K, tested per model               |
| Higher context                          | 64K only after memory and quality tests |
| Maximum individual task duration        | 90 minutes initially                    |
| Maximum task retries                    | 2, after failure classification         |
| Automatic delegation depth              | 2 levels                                |
| New child tasks per parent              | 3 initially                             |

Memory pressure and swap are important health signals. If the machine starts swapping heavily, reduce context, unload another model or suspend background tools.

# D. Architecture for 100+ logical agents

Each logical agent should have a persisted definition similar to this:

```
{
  "agent_id": "code-reviewer-017",
  "role": "Review changed code and test coverage",
  "allowed_tools": ["read", "git_diff", "test_results"],
  "model_tier": "routine",
  "project_scope": "project-42",
  "maximum_runtime_minutes": 30,
  "can_spawn_subtasks": false,
  "approval_policy": "read_only"
}
```

The definition does not launch a model. It becomes active only when a task is scheduled.

The coordinator maintains a state machine:

`proposed → approved/queued → leased → running → verifying → completed`

Alternative terminal states are `blocked`, `cancelled`, `failed` and `needs_review`.

Require task leases, attempt counters, deadlines, idempotency identifiers and a durable record of side effects.

Use scheduling priorities for security fixes, user-requested work, scheduled maintenance and background research. Reserve some capacity for urgent jobs rather than allowing an overnight research project to monopolise the machine indefinitely.

# E. Model strategy by role

| Role                | Default model   | Escalation model           | Additional control        |
| ------------------- | --------------- | -------------------------- | ------------------------- |
| Task classification | Qwen3.5 4B      | Qwen3.5 9B                 | Strict structured output  |
| Simple planning     | Qwen3.5 9B      | gpt-oss 20B                | Explicit milestones       |
| Complex planning    | gpt-oss 20B     | Optional paid cloud model  | Budget and policy review  |
| Everyday coding     | Qwen3.5 9B      | Qwen3-Coder 30B            | Tests required            |
| Difficult coding    | Qwen3-Coder 30B | Optional paid cloud model  | Isolated worktree         |
| Debugging           | Qwen3.5 9B      | Qwen3-Coder 30B            | Reproduce first           |
| Research extraction | Qwen3.5 4B      | Qwen3.5 9B                 | Exact source spans        |
| Research synthesis  | Qwen3.5 9B      | gpt-oss 20B                | Evidence-ledger gate      |
| Summarisation       | Qwen3.5 4B      | Qwen3.5 9B                 | Input-document validation |
| Final review        | gpt-oss 20B     | Optional external reviewer | Independent verification  |

A model router should consider task difficulty, active memory, available context, required tool calls, latency budget and previous model failures.

It must not route solely by matching keywords to model names.

For the first month, collect results manually and with a small evaluation suite. Compare successful test completion, valid tool calls, unsupported citations, elapsed time and peak memory. Change routing only when your own results justify it.

# F. 24/7 execution and recovery

The operational design needs four safeguards.

First, durable queue state. SQLite records every job before execution. Interrupted work remains visible after a restart.

Second, supervised processes. `launchd` restarts the supervisor after abnormal termination. Jobs run as subprocesses with captured output, process identifiers and time limits.

Third, independent health checks. Verify more than an HTTP response from Ollama. Run a minimal inference periodically and confirm that it returns meaningful output. Also check the queue age, disk availability, memory pressure and whether work is progressing.

Fourth, safe recovery. An interrupted process goes to review. It should not immediately repeat an operation that may have modified files or used an external service.

Recommended operational checks:

| Check                      | Frequency                        | Response                               |
| -------------------------- | -------------------------------- | -------------------------------------- |
| Queue and worker heartbeat | Every 1–5 minutes                | Alert or restart supervisor            |
| Ollama sample inference    | Every 30–60 minutes while active | Reset worker or change model           |
| Free disk capacity         | Hourly                           | Pause large downloads and new jobs     |
| Memory pressure            | During every task                | Reduce concurrency or context          |
| SQLite integrity           | Scheduled maintenance            | Stop writes and restore if required    |
| Backups                    | Daily                            | Record success and verify periodically |
| Security approvals         | At each restricted action        | Block until authorised                 |

A UPS is worth considering. It reduces the risk of power loss during database writes or long research tasks.

# G. Remote-control architecture

Start with SSH, not a custom mobile app.

```

Phone or laptop
      |
   Tailscale
      |
Encrypted private network
      |
macOS Remote Login (SSH)
      |
AgentLab CLI
      |
Queue, approvals, logs, pause

```

Example remote commands:

```
ssh agentuser@your-mac-tailnet-name
python3 ~/AgentLab/agentlab.py list
python3 ~/AgentLab/agentlab.py show TASK_ID
python3 ~/AgentLab/agentlab.py approve TASK_ID
python3 ~/AgentLab/agentlab.py pause
```

The example path assumes you install the starter at `~/AgentLab`. Use the actual installation path otherwise.

Enable SSH keys and restrict which Tailscale devices and users can connect. Disable password-based SSH access after confirming key authentication works.

Later, expose a small dashboard only through the tailnet, with separate authentication, short-lived sessions, explicit approval actions and an emergency-stop control.

Notifications can use a private channel or an optional external push service. The system should still operate if the notification provider is unavailable.

# H. Security architecture

The most effective security policy distinguishes operations by consequence, not simply by which agent requests them.

| Operation                                                 | Policy                                       |
| --------------------------------------------------------- | -------------------------------------------- |
| Read files within an approved project                     | Autonomous                                   |
| Search public websites                                    | Autonomous, with network limits              |
| Create analysis and documentation in an isolated project  | Autonomous                                   |
| Edit files inside an approved Git worktree                | Autonomous after project-level authorisation |
| Execute a predefined test command                         | Autonomous in an isolated environment        |
| Install new packages or execute downloaded scripts        | Approval or isolated VM                      |
| Access another project outside the assigned scope         | Approval                                     |
| Push a branch or open a public PR                         | Approval                                     |
| Merge into a protected branch                             | Approval                                     |
| Send emails or messages                                   | Approval                                     |
| Open private cloud accounts or personal browser sessions  | Denied by default                            |
| Access passwords, banking or financial information        | Denied by default                            |
| Delete significant data outside a disposable workspace    | Approval, often denied                       |
| Modify firewall, SSH, permissions or system configuration | Human administration only                    |
| Execute `sudo`, erase disks or disable security controls  | Hard deny                                    |

### Required safeguards

Use a dedicated non-administrator account. Keep secrets out of prompts, logs and model context. Provide project-specific credentials only where essential, preferably short-lived and scoped.

Separate execution policy from model instructions. An agent instruction saying “do not delete files” is not a security boundary.

The supervisor must impose deadlines, job counts, disk quotas, subprocess termination, network restrictions and a global pause.

For untrusted code, use a disposable VM with limited mounted directories and restricted connectivity.

Store an audit record covering the actor, task, permission decision, commands invoked, changed files, approvals and outcome. Do not place raw secrets in the audit log.

# I. Exact installation and implementation roadmap

I recommend eight stages. Do not enable fully autonomous overnight coding during the first installation.

## Starter kit

Download M6 AgentLab Starter Kit

ZIP containing Python supervisor, SQLite task queue, OpenCode configuration, launchd installer and setup instructions.

The Python files passed syntax checks, and the ZIP contents were verified. The kit has not been tested on an M6 Mac or against a live local model. Treat it as a starting implementation, not a security-certified deployment.

The code jobs require explicit approval. An agent process that exits successfully still enters `needs_review`, rather than being automatically accepted as complete.

### Phase 1. Minimal local system

Install Homebrew if necessary using the instructions at [Homebrew](https://brew.sh/).

In Terminal, on the dedicated agent user's account:

```
brew update
brew install git python uv ollama
brew install anomalyco/tap/opencode

ollama --version
opencode --version
python3 --version
```

Homebrew supports installing Ollama as a native service. OpenCode's stable v1 documentation lists the installation command above. OpenCode v2 is also available separately, but its configuration and packaging should be evaluated before switching.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://formulae.brew.sh\&sz=32)

Homebrew Formulae

+2



Create a dedicated project location on your external SSD. The following assumes that the SSD is mounted as `AgentLab`.

```
mkdir -p /Volumes/AgentLab/models
mkdir -p /Volumes/AgentLab/projects
mkdir -p /Volumes/AgentLab/datasets
mkdir -p /Volumes/AgentLab/papers
mkdir -p /Volumes/AgentLab/worktrees

export AGENTLAB_PROJECTS=/Volumes/AgentLab/projects
```

Configure Ollama model storage and initial resource limits before starting its service:

```
launchctl setenv OLLAMA_MODELS /Volumes/AgentLab/models
launchctl setenv OLLAMA_HOST 127.0.0.1:11434
launchctl setenv OLLAMA_MAX_LOADED_MODELS 1
launchctl setenv OLLAMA_NUM_PARALLEL 1
launchctl setenv OLLAMA_CONTEXT_LENGTH 32768

brew services start ollama
```

This assumes a user-session Homebrew service. Persist these environment settings in your service configuration before relying on them after reboot. Avoid installing a second copy of Ollama through its graphical app while the Homebrew server is using the same port.

Check the server and pull the initial models:

```
curl http://127.0.0.1:11434/api/tags

ollama pull qwen3.5:4b
ollama pull qwen3.5:9b

ollama run qwen3.5:9b \
  "Return a short JSON object with status set to ready."
```

Do not download the larger models until you have checked everyday task performance and memory use.

Test: Confirm `ollama ps` displays your active model, output is non-empty and macOS memory pressure remains acceptable.

Rollback: Stop the Homebrew service and remove only the newly downloaded model data, after verifying the location.

### Phase 2. Autonomous coding in isolated repositories

Unzip the starter kit into a stable directory accessible to the agent user. From that directory:

```
mkdir -p ~/.config/opencode
cp opencode.json ~/.config/opencode/opencode.json

python3 agentlab.py init
```

Create or clone an isolated test repository inside `/Volumes/AgentLab/projects`.

Submit a read-only inspection job:

```
python3 agentlab.py submit \
  --kind research \
  --project /Volumes/AgentLab/projects/demo \
  --prompt "Inspect this repository and report its structure and test commands."
```

Run one job:

```
python3 agentlab.py work-once
python3 agentlab.py list
```

Submit a code task:

```
python3 agentlab.py submit \
  --kind code \
  --project /Volumes/AgentLab/projects/demo \
  --prompt "Add a small unit test and explain the result."
```

It remains in `pending_approval` until you run:

```
python3 agentlab.py approve TASK_ID
python3 agentlab.py work-once
python3 agentlab.py show TASK_ID
```

The starter provides queue-level approval but does not yet create per-job Git worktrees automatically. That is an essential Phase 2 enhancement.

For a real repository, create a separate worktree before dispatch:

```
git -C /Volumes/AgentLab/projects/demo worktree add \
  -b agent/task-001 \
  /Volumes/AgentLab/projects/demo-task-001 \
  HEAD
```

Dispatch against the new worktree directory, not the original checkout.

Test: Introduce a deliberate failing test and verify the result remains unapproved.

Failure mode: The model edits outside expected files or fails to invoke tools correctly.

Rollback: Stop the task, inspect its worktree and remove the test worktree after preserving useful logs.

### Phase 3. Autonomous research

Add research dependencies:

```
mkdir -p ~/AgentLab/research
cd ~/AgentLab/research

uv init
uv add httpx pymupdf playwright beautifulsoup4 lxml
uv run playwright install chromium
```

Implement source discovery, retrieval, claim extraction and verification as separate functions.

For public literature research, integrate Crossref and Semantic Scholar APIs with rate limits and retry handling.

Test: Give the research pipeline a known paper DOI, an intentionally incorrect claim and a nonexistent source URL. The incorrect claim and invalid URL must not pass verification.

Rollback: Disable its scheduled tasks and retain saved sources and metadata for inspection.

### Phase 4. Persistent memory

Create SQLite tables for projects, tasks, episodes, documents, claims, evidence and decisions.

Index document text with FTS5 and retain source identifiers, content hashes and modification timestamps.

Store durable architecture decisions in project Markdown files committed to Git.

Test: Restart the supervisor and demonstrate that task history and research notes remain searchable.

Rollback: Restore from an SQLite online backup. Do not copy an active WAL database casually while writes are occurring.

### Phase 5. Multi-agent orchestration

Introduce LangGraph for workflows that genuinely benefit from stateful branching.

Create roles for planner, implementer, reviewer, researcher and verifier, but schedule them through the same central queue.

Do not allow arbitrary recursive spawning. Initially limit delegation to two levels, with a maximum of three children per parent task.

Test: Submit 100 logical tasks and verify that only one LLM inference task runs at a time.

Rollback: Disable dynamic delegation while leaving the basic queue operating.

### Phase 6. Continuous operation

The starter includes a `launchd` generator.

Make sure `AGENTLAB_PROJECTS` is set before generating the service configuration:

```
export AGENTLAB_PROJECTS=/Volumes/AgentLab/projects

python3 install-launchagent.py
launchctl bootstrap gui/$(id -u) \
  ~/Library/LaunchAgents/nz.agentlab.worker.plist

launchctl print gui/$(id -u)/nz.agentlab.worker
```

If you change the service environment, regenerate the plist and reload it.

Test cancellation and recovery:

```
python3 agentlab.py pause
python3 agentlab.py list
python3 agentlab.py resume
```

Terminate a disposable test worker unexpectedly. On restart, its interrupted job should enter `needs_review` rather than running a second time.

Test: Run overnight with only low-risk research and repository inspection tasks. Check that the queue and logs survive a supervisor crash.

Rollback:

```
launchctl bootout gui/$(id -u)/nz.agentlab.worker
```

The provided LaunchAgent operates after user login. Fully unattended cold-boot operation requires a separate service and FileVault analysis, not simply another plist setting.

### Phase 7. Secure remote access

Install Tailscale on the Mac and your phone. Join both to the same private network.

On the Mac, enable Remote Login for the dedicated agent user only. Configure SSH keys, restrict the Tailscale access policy and disable public router port forwarding.

From your laptop or mobile SSH client:

```
ssh agentuser@your-mac-tailnet-name
```

Test: Connect while outside your home Wi-Fi. Confirm the connection works only from an authorised device.

Rollback: Disable Remote Login and revoke the agent Mac's Tailscale access if necessary.

### Phase 8. Performance and advanced controls

Measure a repeatable workload across Qwen3.5 4B, Qwen3.5 9B and the larger models.

Record total completion time, model load duration, token generation rates, valid tool calls, successful tests, unsupported research claims and peak memory pressure.

Experiment with llama.cpp or MLX only if the results justify operating an alternative server.

Add a disposable VM for untrusted code execution and introduce a private dashboard once command-line administration is dependable.

Test: Confirm that optimisation improves verified tasks completed per hour, not merely model token throughput.

Rollback: Revert model-routing configuration and restart the original Ollama service.

### Suggested final directory structure

```
~/Library/Application Support/AgentLab/
    jobs.sqlite3
    logs/
    backups/
    PAUSED

~/AgentLab/
    agentlab.py
    opencode.json
    research/
    policies/
    config/

/Volumes/AgentLab/
    models/
    projects/
    worktrees/
    papers/
    datasets/
    experiments/
    artifacts/
    caches/
```

The external drive should be mounted and validated before work begins.

# J. What not to install initially

| Technology or approach                          | Reason to avoid now                                  |
| ----------------------------------------------- | ---------------------------------------------------- |
| Kubernetes                                      | Unnecessary cluster-management overhead              |
| Redis or RabbitMQ                               | SQLite handles the initial queue                     |
| PostgreSQL plus a separate vector database      | Additional operations without demonstrated need      |
| Neo4j                                           | No initial requirement for graph-specific querying   |
| A large fixed swarm of LLM agents               | Wastes memory and increases coordination failures    |
| Several permanently loaded 20B–35B models       | Excessive memory pressure                            |
| 70B models as the default                       | Unsuitable for efficient 32 GB operation             |
| vLLM or SGLang on this Mac                      | Better suited to supported server-GPU configurations |
| Ollama inside macOS Docker for GPU acceleration | Not the intended native Metal deployment             |
| Multiple competing coding-agent frameworks      | Duplicated sessions, permissions and maintenance     |
| Unrestricted browser and GUI automation         | Unacceptable access to personal data                 |
| Publicly exposed Ollama or agent-control APIs   | Unnecessary attack surface                           |
| Mandatory paid search or LLM APIs               | Contradicts your local-first requirement             |

There is no advantage in installing a large framework simply because it advertises autonomous agents. Durability, permissions and verification must be assessed independently.

# K. Future hardware upgrade path

| Upgrade                     | What changes                                                                                                 | What stays                                           |
| --------------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------- |
| 64 GB unified memory        | More comfortable use of 30B–35B models, longer contexts, possibly two carefully controlled inference workers | SQLite supervisor, security policy, evidence system  |
| 96 GB unified memory        | Larger quantised models, several resident small models, greater concurrency                                  | Task queue and role architecture                     |
| 128 GB unified memory       | 70B-class quantised models become practical to evaluate, with more room for context and tooling              | Orchestration and verification layers                |
| Dedicated Linux GPU server  | Add vLLM or SGLang for GPU-serving workloads and route selected inference requests over a private network    | Mac remains the control plane                        |
| Multiple inference machines | Distribute model workers according to memory and capability                                                  | Central queue, approvals, audit and task definitions |

Do not redesign the entire platform when upgrading hardware. Introduce a model-router interface early so the workstation can later send inference to a more powerful local server without moving task ownership or sensitive project memory.

### Cost position

Core costs are the Mac, SSD, power consumption, Internet access and separate backup storage. The recommended Python, SQLite, Git, Ollama, OpenCode and research-tool stack can operate without mandatory cloud-model subscriptions.

Optional costs include hosted search APIs, paid research databases, cloud reasoning models and notification services.

The platform should continue processing local tasks when those external services are unavailable.

# Final implementation decision

Build the system in this order: Ollama, OpenCode, durable SQLite supervisor, isolated coding worktrees, evidence-based research, persistent memory, scheduled operation, private remote access, then dynamic multi-agent workflows.

The principal engineering challenge is not getting an LLM to perform another tool call. It is establishing when a task is authorised, whether the observed result is correct, what should happen after failure and whether the system is allowed to continue independently.

A reliable workstation with one model completing verified work overnight will be more useful than a system advertising 100 simultaneously active agents but producing unreviewed changes.

## Sources

All sources below are primary sources, unless labelled otherwise. They support the technology and capability assessments, not any claim that the complete recommended architecture has been benchmarked on the specified M6 machine.

| Source                                                                                                            | Type    | Purpose                                 |
| ----------------------------------------------------------------------------------------------------------------- | ------- | --------------------------------------- |
| [Apple Mac mini specifications](https://www.apple.com/mac-mini/specs/)                                            | Primary | M6 hardware and memory configurations   |
| [Ollama Qwen3.5 model family](https://ollama.com/library/qwen3.5)                                                 | Primary | Model sizes and available variants      |
| [Ollama Qwen3-Coder](https://ollama.com/library/qwen3-coder)                                                      | Primary | Coding model size and architecture      |
| [Ollama gpt-oss](https://ollama.com/library/gpt-oss)                                                              | Primary | Local reasoning model                   |
| [OpenAI gpt-oss repository](https://github.com/openai/gpt-oss)                                                    | Primary | Model and inference implementation      |
| [Ollama FAQ](https://docs.ollama.com/faq)                                                                         | Primary | Memory, parallelism and model loading   |
| [Ollama OpenCode integration](https://github.com/ollama/ollama/blob/main/docs/integrations/opencode.mdx)          | Primary | Local coding-agent integration          |
| [OpenCode documentation](https://opencode.ai/docs/)                                                               | Primary | Agent execution and configuration       |
| [OpenCode agents and permissions](https://opencode.ai/docs/agents/)                                               | Primary | Tool permission mechanisms              |
| [OpenCode CLI](https://dev.opencode.ai/docs/cli/)                                                                 | Primary | Non-interactive execution               |
| [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)                              | Primary | Checkpoints and long-term memory        |
| [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)                           | Primary | Publication metadata                    |
| [Semantic Scholar API](https://www.semanticscholar.org/product/api)                                               | Primary | Academic literature research            |
| [Playwright Python](https://playwright.dev/python/docs/intro)                                                     | Primary | Browser automation                      |
| [sqlite-vec repository](https://github.com/asg017/sqlite-vec)                                                     | Primary | Optional SQLite vector search           |
| [Apple Virtualization framework](https://developer.apple.com/documentation/virtualization)                        | Primary | Isolated virtual machines               |
| [Apple launchd guidance](https://support.apple.com/guide/terminal/script-management-with-launchd-apdc6c1077b/mac) | Primary | macOS background services               |
| [Tailscale SSH](https://tailscale.com/docs/features/tailscale-ssh)                                                | Primary | SSH support and limitations             |
| [Tailscale macOS variants](https://tailscale.com/docs/concepts/macos-variants)                                    | Primary | macOS remote-access selection           |
| [Homebrew Ollama formula](https://formulae.brew.sh/formula/ollama)                                                | Primary | macOS installation and service commands |

The research establishes a defensible architecture and an initial implementation path. Production readiness still requires testing the chosen models, OpenCode integration, filesystem permissions, unattended startup and recovery behaviour on the actual workstation.

## Reasoning trace (not shown to raters)

I’ll verify the hardware premise first, then compare current local models, agent runtimes, coding and research tools, and security options. I’ll use the findings to produce one recommended architecture, with resource estimates, installation steps, recovery procedures, and alternatives. The pasted brief specifies 31 August 2026, but I’ll use the current date, 15 October 2026, for the technology checks.

Planned the comparison

Refined the implementation

Searched 44 websites




The current model catalog supports a practical two-tier setup: a 4B or 9B model for routine work and a roughly 20B to 30B model for harder tasks, loaded selectively. I also confirmed an important remote-access detail: Tailscale’s ordinary macOS app does not provide the Tailscale SSH server feature. The safer standard setup is macOS Remote Login over a restricted Tailscale connection.

Built the prototype

Assembled toolkit, finalized safeguards, and prepared launch setup

Searched 6 websites




I’m turning the design into an implementation plan with a small starter kit for the Mac. It will include a persistent SQLite task queue, controlled coding jobs, logs, time limits and a launchd service. The starter will deliberately require approval before code-writing tasks run. Broader autonomous permissions belong in a later phase, after isolation and recovery tests pass.

Built a production-grade Python agent worker kit




Tested the toolkit

Searched 1 website




Inspected AgentLab files and reviewed starter configurations




Balanced compatibility considerations

Searched 8 websites




Patched worker locking, inspected artifacts, and validated starter kit ZIP




Searched 4 websites




Validated package syntax and contents




Preparing the comparison

Searched 4 websites












GPT-6 | OpenAI | Knowledge cutoff: not publicly specified | Web browsing: enabled | Research date: 15 October 2026

## Run notes

chatgpt.com, paid plan, new chat, GPT-5.6 Sol, Thinking effort High, as set in the pre-registration;
confirmed by the author. Run by the author by hand. Answer copied with ChatGPT's copy button and written
verbatim from the clipboard; the copy includes ChatGPT's citation and favicon links and diagram markup as
the app produced them. ChatGPT worked for 15 min 5 s. ChatGPT searched the web by itself (the answer carries live citations and gives the research date as 15 October 2026, not the prompt's 31 August 2026) and produced a downloadable starter-kit ZIP. The answer names itself "GPT-6"; the model picker showed GPT-5.6 Sol, so this is recorded as a model self-report error. Reasoning trace: ChatGPT's "Thought for 15m 5s" activity panel, selected and copied by the
author from the page; the copy ends with the answer's first line, kept as copied.
