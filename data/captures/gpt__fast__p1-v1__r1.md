---
run_id: gpt__fast__p1-v1__r1
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
replicate: 1
date_stamped: '2026-10-14T12:43:34+00:00'
date_run: 2026-10-14T12:00:00+00:00/2026-10-14T12:43:00+00:00
date_note: >-
  Sent by hand on 15 Oct 2026 NZDT before the template was made; exact send time not recorded. Interval: 01:00 NZDT (author: GPT runs sent from 01:00) to 01:43 NZDT (answer on the clipboard; template made).
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

GPT-6 | Knowledge cutoff: Not disclosed | Web browsing: Enabled | Research date: 15 October 2026

# Autonomous AI Workstation: Architecture and Implementation Research

Target hardware: Apple Mac mini, stated M6 base chip, 32 GB unified memory, 512 GB internal SSD and 1 TB external SSD.

The objective is to build a local-first autonomous AI operating environment that can plan, execute, verify and continue work for extended periods, including overnight, with remote supervision and controlled access to the computer.

One important qualification: the hardware description must be verified before finalising the installation. An M6 Mac mini should not be assumed to be commercially available or supported by every inference engine simply because the chip is specified. The actual chip identifier, macOS version and Metal support will determine compatibility.

## Decisions at a glance

| Layer                 | Preliminary recommendation                                                    |
| --------------------- | ----------------------------------------------------------------------------- |
| Local inference       | MLX-based inference, with llama.cpp as a compatibility alternative            |
| Primary coding agent  | Aider or OpenCode, subject to current compatibility checks                    |
| Orchestration         | Python-based durable supervisor and worker pool                               |
| Task persistence      | SQLite with explicit task states and recovery                                 |
| Research              | Search, retrieval, document parsing and citation-verification pipeline        |
| Memory                | SQLite, project files and full-text search                                    |
| Multi-agent operation | 100+ logical agents, with only a small number actively using inference        |
| Background execution  | macOS launchd and persistent worker processes                                 |
| Remote access         | Tailscale, SSH and a private dashboard                                        |
| Security              | Dedicated macOS account, isolated workspaces and approval policies            |
| Storage               | Internal SSD for system-critical state, external SSD for models and bulk data |

These are architectural starting points, not yet verified product selections.

The main design decision is to separate the number of agents from the number of models running. A hundred logical agents can be represented as durable task records, policies and individual contexts. They do not need a hundred simultaneously loaded language models.

For 32 GB unified memory, a controlled inference queue is more appropriate than an unrestricted swarm. The system should prioritise completed, verified work over the number of agents it claims to run.

Apple's New Zealand website confirms that the M6 Mac mini is now available, with availability beginning 22 September 2026. This resolves the hardware availability question, although the installed macOS version and individual software compatibility still need checking.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.apple.com\&sz=32)

Apple (NZ)



## 1. Local inference

For the first deployment, I recommend starting with Ollama because it simplifies model management and offers a local API. MLX should be benchmarked as a second inference backend before deciding which to retain.

The important constraint is unified memory, not just model-file size. The model weights, KV cache, runtime buffers, operating system and other applications all compete for the same 32 GB.

| Model class | Approximate 4-bit weights | Recommended use                       |
| ----------- | ------------------------- | ------------------------------------- |
| 3B–4B       | 2–3 GB                    | Classification, routing, extraction   |
| 7B–8B       | 4–6 GB                    | Routine coding, summarisation         |
| 12B–14B     | 7–10 GB                   | Main coding and research tasks        |
| 20B–24B     | 12–16 GB                  | More demanding reasoning, selectively |
| 30B–32B     | 18–22 GB                  | Occasional single-worker use          |

These are planning estimates, not measurements of particular models. Actual allocations depend on architecture, quantisation, context and runtime.

My initial operating target would be one 12B–14B model at 4-bit quantisation, with a 16K-token context. Increase context to 32K only after measuring memory pressure and output quality.

The model router should distinguish tasks by difficulty. Simple extraction should not occupy the strongest model. Complex coding and research synthesis should have priority access to the main inference worker.

## 2. Agent runtimes and harnesses

OpenCode is the stronger initial candidate for an integrated coding harness. Its documentation describes primary agents, specialised subagents, configurable permissions and task delegation.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.opencode.ai\&sz=32)

OpenCode

+1



Aider remains useful as a simpler coding alternative. It supports local models through Ollama and warns about context truncation when Ollama is configured with insufficient context.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



Neither should be treated as the entire autonomous operating environment.

The recommended separation is:

- Coding harness: performs repository-level development.
- Supervisor: manages goals, task state and stopping conditions.
- Worker pool: controls simultaneous execution.
- Policy engine: decides which actions are permitted.
- Verification service: independently checks outputs.
- Memory layer: preserves decisions, evidence and task history.

This prevents a coding agent's session state from becoming the sole record of a long-running project.

## 3. Multi-agent architecture

A 100-agent system should be implemented as 100 or more logical agent identities, not 100 concurrent inference sessions.

Each logical agent needs an identifier, role, permissions, assigned tasks, memory namespace, model preference and resource budget.

The worker scheduler should use a small number of active inference slots. A starting configuration is one main inference worker and one lightweight worker, provided both fit without memory pressure. Other tasks can proceed concurrently when they do not require inference, such as running tests, downloading permitted documents or waiting for external processes.

Tasks should move through explicit states:

`queued → leased → running → verifying → completed`

Failure paths should include retry, blocked, awaiting approval and failed permanently.

Every lease needs an expiry. If a worker crashes, the supervisor should recover the task without blindly repeating irreversible actions.

## 4. Coding agents

Use OpenCode as the initial coding harness, but run it inside a restricted workspace.

For each development task, the supervisor should create a task-specific Git branch or worktree, supply acceptance criteria and invoke the coding worker. The worker can inspect code, edit files, run permitted commands and execute tests.

Completion should require a separate verification step. A successful agent response is not sufficient evidence that the feature works.

The verifier should check the Git diff, test results, exit codes, changed files and acceptance criteria. Failed checks should generate a bounded repair task.

OpenCode's permission system supports allow, ask and deny decisions. This is useful, but its permissions must be supplemented with operating-system isolation because a configuration file is not a complete security boundary.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://opencode.ai\&sz=32)

OpenCode



## 5. Research agents

Research should be implemented as an evidence pipeline rather than one agent browsing the web and writing a report from memory.

The proposed sequence is:

1. Decompose the research question into verifiable claims.
2. Search official, academic and other relevant sources.
3. Retrieve and preserve source documents.
4. Extract passages with source identifiers and page references.
5. Compare claims across independent sources.
6. Record conflicts and uncertainty.
7. Generate a report using the evidence records.
8. Audit every citation before release.

Every cited claim should link to a stored source, an exact passage or page, and a retrieval timestamp. A verifier should reject invented URLs, nonexistent references and claims unsupported by the cited material.

For literature research, the system should support DOI lookup, scholarly metadata, PDF extraction and reference reconciliation. A report must distinguish verified findings from inference.

## 6. Persistent memory

Start with SQLite and ordinary project files.

SQLite should store task histories, agent definitions, decisions, source metadata, approvals and execution results. Project Markdown files should preserve human-readable plans and conclusions. SQLite full-text search is sufficient for the first deployment.

Add embeddings only when keyword and metadata retrieval demonstrably fail. A separate vector database and knowledge graph are not justified at the beginning.

Memory should also have provenance and revision rules. A later finding must not silently overwrite an earlier decision without recording the change.

## 7. Computer control

Use terminal and filesystem tools as the primary execution mechanisms. They are easier to audit and constrain than unrestricted GUI automation.

Browser automation should run in a separate profile without access to personal browser cookies. GUI control should be introduced only for applications that cannot be operated through an API, command-line interface or supported file format.

A dedicated non-administrator macOS account is the preferred first boundary. Agents should receive access only to explicitly approved project directories. They should not inherit access to the personal home directory, keychain, email, banking or password managers.

For stronger isolation, high-risk workloads should execute in a dedicated virtual machine or another independently enforced sandbox.

## 8. Always-on operation

Use macOS launchd to start and supervise the persistent controller. Apple's developer documentation identifies launchd as the native macOS service-management system.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://developer.apple.com\&sz=32)

Apple Developer Documentation



The controller should recover incomplete tasks from SQLite, check expired leases and restart interrupted work when safe.

The machine must be configured to remain awake, maintain network connectivity and restart services after a reboot. Background operation should not depend on an open Terminal window.

Automatic retries must be bounded. The supervisor should stop work when a task exceeds its execution budget, repeatedly fails verification or encounters an approval requirement.

## 9. Remote access

Tailscale is the preferred private networking layer.

It supports encrypted connections between authorised devices. Standard SSH can operate over the private network. Tailscale's documentation also explains that its integrated SSH server has macOS installation-specific requirements.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://tailscale.com\&sz=32)

Tailscale Docs

+1



The remote interface should expose task submission, queue status, logs, approvals, pause and emergency stop.

Do not publish the inference API, SQLite database or supervisor dashboard directly to the public internet.

## 10. Storage architecture

| Storage                     | Recommended contents                                                                      |
| --------------------------- | ----------------------------------------------------------------------------------------- |
| Internal 512 GB             | macOS, applications, supervisor, active SQLite database, configuration, essential logs    |
| External 1 TB               | Model weights, Git worktrees, research documents, datasets, experiment outputs and caches |
| Separate backup destination | Database backups, configuration backups, completed research and important repositories    |

Keep the active SQLite database on the internal drive to reduce the consequences of an external SSD disconnecting. Store large, reproducible assets on the external drive.

The external SSD should use a reliable enclosure and connection, with the filesystem and mount path verified before starting workers. If it disconnects, the supervisor should stop affected jobs rather than writing into an unintended replacement directory.

# Final architecture deliverables

## A. Recommended technology stack

| Layer                 | Recommended               | Alternative                      | Reason                                   |
| --------------------- | ------------------------- | -------------------------------- | ---------------------------------------- |
| Local inference       | Ollama initially          | MLX LM, llama.cpp                | Simplest first deployment                |
| Main model            | Qwen3 14B                 | Other benchmarked 12B–14B models | Reasonable memory and capability balance |
| Small model           | Qwen3 4B                  | Qwen3 8B                         | Routing and routine tasks                |
| Advanced coding model | Qwen3-Coder 30B-A3B       | Cloud coding model               | Optional, higher memory demand           |
| Coding                | OpenCode                  | Aider                            | Agents, permissions, coding tools        |
| Orchestration         | Python supervisor         | LangGraph, Temporal              | Full control with limited infrastructure |
| Database              | SQLite                    | PostgreSQL                       | Durable local task state                 |
| Research              | Python retrieval pipeline | Dedicated research framework     | Evidence tracking and verification       |
| Documents             | PyMuPDF, pandas           | Other specialised parsers        | Local processing                         |
| Remote access         | Tailscale and SSH         | WireGuard                        | Private remote connectivity              |
| Background services   | launchd                   | Dedicated service manager        | Native macOS support                     |
| Dashboard             | FastAPI                   | Streamlit                        | Lightweight API and status interface     |

Qwen's published model card confirms that Qwen3-Coder-30B-A3B uses 30.5 billion total parameters but activates approximately 3.3 billion per token. This makes it worth benchmarking for coding. Its full model weights still need to fit in memory, however, and its large advertised context does not mean that the full context is practical on this machine.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://huggingface.co\&sz=32)

Hugging Face



The choices above are a deployment shortlist. They are not a completed independent benchmark of every current product.

## B. Complete architecture diagram

Remote interface

Phone / laptop / private dashboard / SSH

Supervisor and policy engine

Approvals · resource budgets · watchdog · emergency stop

Durable task queue and orchestrator

SQLite · task dependencies · leases · retries · scheduling

Coding

Git · tests · fixes

Research

Sources · evidence

Verification

Checks · review

Model router and inference scheduler

Qwen3 4B · Qwen3 14B · optional larger model

Tools

Terminal, browser, filesystem, Git

Memory

SQLite, files, evidence, history

## C. Hardware and resource plan

Illustrative allocation for 32 GB unified memory

macOS and services

5 GB

Main model weights

10 GB

KV cache and inference

4 GB

Agent tools and browser

4 GB

Small model or workers

3 GB

Headroom and cache

6 GB

These allocations are provisional budgets. They must be adjusted after testing the actual model and inference backend. The 6 GB headroom is important for avoiding sustained swap activity.

## D. Agent architecture

Use one coordinator, a durable queue and a bounded worker pool.

A task can dynamically create child tasks for planning, research, coding or verification. Those child tasks inherit restrictions from their parent and cannot grant themselves additional permissions.

One hundred agent identities can remain registered while only one or two inference jobs execute. Parallelism should be concentrated in deterministic operations such as independent tests and document downloads.

A parent task completes only when required child tasks pass verification.

## E. Model strategy

| Function                 | First-choice model                               |
| ------------------------ | ------------------------------------------------ |
| Planning                 | Qwen3 14B                                        |
| Coding                   | Qwen3 14B, benchmark against Qwen3-Coder 30B-A3B |
| Debugging                | Qwen3 14B                                        |
| Research reasoning       | Qwen3 14B                                        |
| Summarisation            | Qwen3 4B or 14B                                  |
| Classification           | Qwen3 4B                                         |
| Final synthesis          | Qwen3 14B                                        |
| Independent verification | Rules and tests first, LLM second                |

Qwen3 14B is available through Ollama with documented tool and reasoning support.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://ollama.com\&sz=32)

Ollama



The model router should use task-level benchmarks, not only synthetic reasoning scores. Measure successful tool calls, correct code edits, passing tests, citation accuracy, completion time and peak memory.

## F. 24/7 operation

The supervisor should maintain a persistent heartbeat and save task checkpoints. On restart, it should identify abandoned leases and recover only operations that can be safely repeated.

Each task should have a maximum runtime, retry count and resource budget. Long-running research may continue overnight, but it should pause for approval before executing consequential external actions.

A crash-recovery test should terminate a worker during execution, restart the supervisor and confirm that the task resumes or enters a safe recovery state.

## G. Remote-control architecture

Use Tailscale between the Mac, phone and laptop. Keep the dashboard on the private network.

The dashboard should display current tasks, progress, pending approvals, resource use and recent failures. It should offer pause, resume, cancel and emergency-stop functions.

Require authenticated access to the dashboard in addition to private networking. Emergency stop must work without consulting an LLM.

## H. Security architecture

| Operation                                      | Policy                                   |
| ---------------------------------------------- | ---------------------------------------- |
| Read approved project files                    | Allow                                    |
| Create temporary worktrees                     | Allow                                    |
| Edit approved project files                    | Allow                                    |
| Run approved test commands                     | Allow                                    |
| Read public web pages                          | Allow with logging                       |
| Install dependencies                           | Approval or tightly controlled allowlist |
| Access files outside approved directories      | Deny by default                          |
| Access passwords or personal financial records | Deny                                     |
| Delete important files or repositories         | Approval                                 |
| Push code to remote repositories               | Approval                                 |
| Send email or publish content                  | Approval                                 |
| Spend money or execute financial transactions  | Approval                                 |
| Change system security settings                | Deny                                     |

The strongest protection is isolation enforced outside the agent. Prompt instructions and agent permission settings alone are insufficient.

## I. Exact installation plan

This is a first-stage installation, not the complete production deployment. Run it from a dedicated macOS account after reviewing the commands.

### Phase 1. Verify hardware and prepare directories

```
sw_vers
uname -m
sysctl -n hw.memsize
system_profiler SPHardwareDataType
df -h
```

Confirm the external SSD's mounted volume name, then create the workspace:

```
mkdir -p ~/ai-lab/{config,db,logs,agents,projects,research,backups}
```

Install Homebrew if needed, using its official instructions at [brew.sh](https://brew.sh).

```
brew install python git jq
```

### Phase 2. Install local inference

Install Ollama from its [official macOS download](https://ollama.com/download/mac) and verify that its service is running.

```
ollama --version
ollama pull qwen3:4b
ollama pull qwen3:14b
ollama list
```

Test the smaller model first:

```
ollama run qwen3:4b
```

Then benchmark the larger model with identical tasks. Record response time, token throughput, peak memory and tool-call success.

### Phase 3. Install the coding harness

Install OpenCode using the current instructions at [OpenCode documentation](https://opencode.ai/docs).

Configure the local Ollama endpoint, choose the model and set default-deny permissions for external directories and sensitive commands.

Test it against a disposable Git repository containing a small program and automated tests.

### Phase 4. Implement research workers

Create a Python virtual environment:

```
cd ~/ai-lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install requests beautifulsoup4 pymupdf pandas
```

Implement separate source-retrieval, document-extraction, claim-validation and report-generation functions.

### Phase 5. Add durable orchestration and memory

Use Python's built-in SQLite library for the initial task queue. Add transaction-safe task leasing, retries, dependency tracking and checkpointing.

The minimum task schema should include:

`task_id, parent_id, objective, status, priority, agent_role, workspace, attempts, lease_expiry, created_at, updated_at, result_path`

Also maintain separate tables for events, approvals, evidence and agent definitions.

### Phase 6. Enable 24/7 execution

Create a launchd service configuration for the supervisor. Set its working directory, executable path, logging destinations and restart policy.

Test recovery after terminating the supervisor and after a normal system reboot. Do not enable unattended operation until both tests pass.

### Phase 7. Configure remote access

Install Tailscale on the Mac and authorised devices. Configure standard SSH over the private network and restrict access to the dedicated agent account.

Only after authentication is working should you deploy the dashboard.

### Phase 8. Optimise

Benchmark Ollama against MLX LM, then test larger models only if they deliver more completed tasks per hour.

Add a second inference slot only when memory and latency measurements justify it.

## J. What not to install initially

Avoid Kubernetes, a full distributed orchestration platform, a separate vector database, a knowledge graph, multiple competing agent frameworks and a large collection of always-running MCP servers.

Also avoid loading several large models simultaneously, using unrestricted auto-approval, exposing local inference ports publicly and building GUI automation before simpler tools have been exhausted.

These technologies may become useful later, but they increase operational complexity without solving the first deployment's main problems.

## K. Future upgrade path

| Hardware             | Recommended change                                             |
| -------------------- | -------------------------------------------------------------- |
| 32 GB                | One primary model, limited inference concurrency               |
| 64 GB                | Larger coding model, more context, additional small worker     |
| 96 GB                | Multiple persistent models and more independent inference jobs |
| 128 GB+              | More substantial concurrent research and coding workloads      |
| Dedicated GPU server | Separate inference from orchestration and tool execution       |

At higher memory capacities, preserve the same durable task and security architecture. Replace the inference backend or increase worker concurrency without rebuilding the entire system.

## Sources

Primary sources used in this initial research:

- [Apple: Mac mini hardware](https://www.apple.com/nz/mac-mini/)
- [Ollama: macOS installation](https://ollama.com/download/mac)
- [Ollama: Qwen3 14B](https://ollama.com/library/qwen3:14b)
- [Qwen: official coding model card](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct)
- [MLX LM: source repository](https://github.com/ml-explore/mlx-lm)
- [OpenCode: agents](https://opencode.ai/docs/agents/)
- [OpenCode: permissions](https://opencode.ai/docs/permissions/)
- [Aider: local Ollama integration](https://aider.chat/docs/llms/ollama.html)
- [Apple: launchd](https://developer.apple.com/documentation/xpc/launchd)
- [Tailscale: SSH architecture](https://tailscale.com/docs/features/tailscale-ssh)

This is an initial, evidence-supported architecture rather than the exhaustive market study requested. In particular, current independent benchmark comparisons, measured M6 throughput, detailed framework rankings, production-ready supervisor code and complete rollback scripts remain outstanding. Those should be completed and tested before describing the workstation as production-ready.

## Reasoning trace (not shown to raters)

Not captured: no thinking panel was copied by the operator for this Instant run.

## Run notes

chatgpt.com, paid plan, new chat, GPT-5.6 Sol, Thinking effort Instant, as set in the pre-registration;
confirmed by the author. Run by the author by hand. Answer copied with ChatGPT's copy button and written
verbatim from the clipboard; the copy includes ChatGPT's citation and favicon links and diagram markup as
the app produced them. ChatGPT searched the web by itself even at Instant (live citations; research date given as 15 October 2026, not the prompt's 31 August 2026). The answer names itself "GPT-6"; the model picker showed GPT-5.6 Sol, so this is recorded as a model self-report error.
