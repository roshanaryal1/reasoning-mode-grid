---
run_id: gpt__reasoning__p1-v1__r2
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
replicate: 2
date_stamped: '2026-10-14T12:46:15+00:00'
date_run: 2026-10-14T12:00:00+00:00/2026-10-14T12:24:00+00:00
date_note: >-
  Sent by hand on 15 Oct 2026 NZDT before the template was made; exact send time not recorded. The author reports the GPT runs were sent from 01:00 NZDT; the answer was on the clipboard by 01:45 NZDT after ChatGPT worked for 21 min 33 s, so it was sent by 01:24 NZDT.
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

GPT-6 | Knowledge cutoff: Not specified | Web browsing: Enabled | Tools: Enabled | Research date: 15 October 2026

# Autonomous AI workstation: Architecture research and implementation specification

The supplied brief specifies 31 August 2026. This assessment uses 15 October 2026, including developments released after August.

## Decisions at a glance

Recommended design: A local-first, persistent agent system built around Ollama, OpenCode, Python, SQLite and macOS launchd. Add specialized research workers, automated verification and secure remote access without deploying a heavyweight distributed infrastructure platform.

| Layer                   | Recommended technology                        | Decision                                         |
| ----------------------- | --------------------------------------------- | ------------------------------------------------ |
| Hardware                | Mac mini M6, 32 GB unified memory             | Suitable with concurrency limits                 |
| Local inference         | Ollama with Metal acceleration                | Primary engine                                   |
| Advanced inference      | llama.cpp                                     | Optional alternative for tuning                  |
| Everyday model          | Qwen3.5 9B                                    | Default local worker                             |
| Complex model           | Qwen3.5 35B-A3B                               | On-demand, single-user mode                      |
| Coding agent            | OpenCode                                      | Primary coding harness                           |
| Agent orchestration     | Python supervisor and durable SQLite queue    | Lightweight custom control plane                 |
| Long workflows          | LangGraph                                     | Add when checkpointed workflows become necessary |
| Research automation     | Playwright, academic APIs, evidence database  | Specialized research workers                     |
| Persistent memory       | Markdown, SQLite FTS5 and optional embeddings | Local, inspectable storage                       |
| Remote control          | Tailscale plus SSH                            | Private access from phone or laptop              |
| Scheduling and recovery | launchd, job leases and watchdog              | 24/7 operation                                   |
| Security                | Dedicated macOS user and isolated workspaces  | Least-privilege execution                        |

These are architectural recommendations, not claims that all components have been integration-tested together. The installation and acceptance tests below distinguish supported features from the engineering required to connect them.

## 1. Local inference

### 1.1 Hardware verification

Apple officially announced the M6 Mac mini on 25 August 2026, and its published specifications confirm that the base M6 can be configured with 32 GB unified memory and a 512 GB SSD.

For the specified 32 GB configuration, Apple lists a 12-core CPU, 12-core GPU and memory bandwidth of 170 GB/s. It supports Metal-based local inference through compatible software frameworks.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://support.apple.com\&sz=32)

Apple Support

+2



This means the requested machine is real and suitable for local AI development. However, it is constrained primarily by unified memory capacity, sustained inference throughput and context-cache growth.

### 1.2 The most important model decision

Do not make a 35B model the permanent default simply because it fits.

The currently available Qwen3.5 family includes 9B, 27B and 35B variants. Ollama lists approximately 6.6 to 7.6 GB for 9B, 17 to 20 GB for 27B and 22 GB for 35B, depending on the variant. These are model download sizes, not complete runtime memory requirements.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://ollama.com\&sz=32)

qwen3.5

+1



The 9B model is the better default for a machine that must simultaneously manage research, code, databases, browsers and autonomous tasks.

The 35B-A3B mixture-of-experts model is worth retaining as an on-demand option for difficult work. It has relatively few active parameters per token, but its full quantized weight set still occupies substantial memory.

The architecture should therefore optimize completed, verified tasks per hour rather than maximizing model size or the number of concurrently active agents.

### 1.3 Inference-engine comparison

| Engine       | Strengths                                                                                                   | Limitations                                                                | Verdict                          |
| ------------ | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------- |
| Ollama       | Simple installation, model management, local API, automatic model unloading, integration with coding agents | Less fine-grained control than direct llama.cpp                            | Primary                          |
| llama.cpp    | GGUF support, Metal acceleration, cache quantization, routing and detailed performance controls             | More configuration and operational responsibility                          | Advanced alternative             |
| MLX / mlx-lm | Apple-native inference, quantization and prompt-cache options                                               | MLX-LM's HTTP server is explicitly not recommended for production security | Benchmarking and experimentation |
| LM Studio    | Convenient graphical interface, local server and model testing                                              | GUI-centric workflow adds little to unattended orchestration               | Optional                         |
| vLLM         | Strong serving architecture on supported accelerator platforms                                              | Not the first choice for a single 32 GB Mac running Metal workloads        | Use on a future GPU server       |

Ollama introduced an MLX backend for Apple Silicon in March 2026. This makes the difference between Ollama and a standalone MLX deployment narrower than it was previously. Meanwhile, llama.cpp has an increasingly capable model-routing server.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://ollama.com\&sz=32)

Ollama Blog

+2



### 1.4 October 2026 model update

A material development after the brief's August date is the release of Qwen3.6, including 27B and 35B-A3B variants.

Qwen3.6 places additional emphasis on repository-level coding and agent execution. The official model distribution supports the 35B-A3B model, while Ollama provides quantized variants.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://ollama.com\&sz=32)

ollama.com

+2



I would therefore update the initial large-model choice:

- Primary 24/7 model: Qwen3.5 9B.
- Secondary coding model to benchmark: Devstral Small 2 24B, approximately 15 GB at Q4.
- Large on-demand model: Qwen3.6 35B-A3B, preferably tested against Qwen3.5 35B-A3B.
- Dense reasoning comparator: Qwen3.6 27B.
- Embedding model: Qwen3 Embedding 0.6B.

The 35B Qwen3.6 model's approximately 23–24 GB footprint leaves little space for macOS, multiple agent processes and long context caches. Run it alone with a restricted workload rather than alongside other large models.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://registry.ollama.com\&sz=32)

registry.ollama.com

+2



One independent community benchmark on an older 32 GB M1 Pro reported approximately 25 tokens/second for Qwen3.6 35B-A3B at Q4_K_S, with substantial swap use. This is useful evidence that it can run, not a reliable M6 performance estimate.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



### 1.5 Recommended inference settings

Start with a 16,384-token context for ordinary workers, increase to 32,768 for coding when memory permits, and reserve larger contexts for carefully controlled runs.

Use one active inference request initially. Ollama's documentation confirms that parallel processing increases total context-memory requirements and that model loading depends on available memory. It also provides configurable model keep-alive, Flash Attention and KV-cache quantization.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.ollama.com\&sz=32)

Ollama



The objective is to complete more work through retrieval, concise task context and reliable verification, not to keep entire repositories inside the model context.

## 2. Agent runtimes and harnesses

The agent harness and the orchestrator solve different problems.

The harness gives a model tools, context and an execution loop. The orchestrator decides which job to run, how long it may run, which permissions apply, how to recover after interruption and what to do next.

A coding agent by itself is not an always-on operating environment.

### 2.1 Candidate comparison

| Technology       | Best use                                               | Assessment for this Mac                             |
| ---------------- | ------------------------------------------------------ | --------------------------------------------------- |
| OpenCode V2      | Autonomous coding, CLI execution, sessions, subagents  | Primary harness                                     |
| Goose            | General local tool-use, desktop and CLI automation     | Strong alternative                                  |
| Pi               | Minimal programmable agent through SDK or RPC          | Excellent lightweight alternative                   |
| OpenHands        | Sandboxed software engineering                         | Useful where stronger execution isolation is needed |
| LangGraph        | Stateful workflows, checkpoints, conditional execution | Best optional workflow framework                    |
| AgentScope 2     | Multi-agent teams, services, model routing             | Worth evaluating later                              |
| Prefect 3        | Scheduled Python jobs, retries, monitoring             | Good alternative to a custom scheduler              |
| Temporal         | Durable distributed workflows                          | Too much infrastructure for the initial deployment  |
| CrewAI / AutoGen | Multi-agent application patterns                       | Not required for the proposed design                |
| OpenClaw         | Personal assistant and messaging interfaces            | Optional remote interaction layer                   |

OpenCode supports noninteractive CLI execution, model selection, agent definitions and structured output. Its V2 release includes local model discovery through Ollama, worktree configuration and fine-grained permissions.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai\&sz=32)

OpenCode

+3



Goose is a credible general-purpose alternative, while Pi is particularly suitable when the objective is to embed a minimal agent inside a custom control plane. AgentScope 2 also offers more integrated team orchestration than a simple prompt-based swarm.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://block.github.io\&sz=32)

Your open source AI agent

+2



### 2.2 Recommended decision

Use OpenCode V2 for coding and repository operations, with separate Python research workers and a durable supervisor managing all scheduled and delegated jobs.

Do not install all the frameworks listed above. Install only components that add a capability missing from the existing stack.

Use LangGraph when a workflow needs explicit resumable stages, human-approval checkpoints or branching execution. LangGraph's official persistence system supports checkpoint recovery, although external side effects still need idempotency controls.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.langchain.com\&sz=32)

Docs by LangChain



The central design principle is that a worker can crash, lose its LLM context or be replaced without losing the system's authoritative task state.

## 3. Multi-agent architecture

### 3.1 What 100 agents should mean

A logical agent is a persistent identity with a defined purpose, policy, tool access and saved state. It does not need its own resident model.

| Concept                | Meaning                                   | Recommended limit                          |
| ---------------------- | ----------------------------------------- | ------------------------------------------ |
| Agent definitions      | Stored roles and capabilities             | 100–500+                                   |
| Pending tasks          | Jobs in persistent storage                | Hundreds or thousands                      |
| Active coordinators    | Processes deciding the next steps         | 1 initially                                |
| Research/fetch workers | Network and document-processing processes | 2–4                                        |
| Active LLM inference   | Model generation jobs                     | 1 initially, test 2                        |
| Large-model inference  | Complex tasks using 27B–35B               | 1 exclusively                              |
| Browser contexts       | Isolated web sessions                     | 1–2                                        |
| Coding worktrees       | Separate Git working directories          | Multiple, with serialized heavy operations |

For example, 120 agents could be registered as specialists covering Python, JavaScript, security, academic research, document analysis, statistics and verification.

Only a small subset would execute at any given moment. Others remain records in the agent registry until the scheduler assigns them work.

### 3.2 Recommended execution pattern

Use a coordinator-worker architecture with hierarchical task decomposition.

1. A coordinator receives an objective and creates an execution plan.
2. A deterministic supervisor validates the plan against budgets and permissions.
3. The task queue stores individual jobs and dependencies.
4. Available workers claim eligible jobs.
5. Workers request model time through one centralized inference scheduler.
6. Verification workers independently evaluate results.
7. Failed tasks are retried within a fixed budget or escalated.
8. Verified outputs are saved with evidence, and authorized follow-up jobs are created.

The queue must be authoritative. An LLM-generated plan is a proposal, not permission to execute arbitrary commands.

### 3.3 Agent data model

Each agent should have at least these fields:

| Field                 | Purpose                                     |
| --------------------- | ------------------------------------------- |
| agent_id              | Stable unique identifier                    |
| role                  | Specialist identity                         |
| system_prompt_version | Reproducible instructions                   |
| capabilities          | Allowed tools and actions                   |
| model_policy          | Default and escalation models               |
| workspace_scope       | Permitted directories                       |
| network_policy        | Permitted services                          |
| approval_policy       | Operations requiring authorization          |
| state                 | Available, running, blocked or disabled     |
| memory_namespace      | Global or project-specific knowledge        |
| concurrency_class     | CPU, browser, small LLM or large LLM        |
| execution_budget      | Runtime, tool calls, iterations and retries |

Agent definitions can be generated from approved templates. New agents must inherit a maximum-permission boundary that they cannot expand.

### 3.4 Task state machine

A separate terminal status such as `FAILED`, `CANCELLED` or `EXPIRED` prevents endless retry loops.

Use leases and heartbeats so that the supervisor can identify abandoned tasks. After a crash, operations with possible external side effects should enter a recovery-review state instead of being automatically repeated.

## 4. Coding agents

### 4.1 Recommended coding architecture

OpenCode V2 is the primary coding harness. It provides terminal and file tools, model selection, persistent sessions and configurable agents. Its documented worktree support makes it suitable for parallel work on distinct branches.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai\&sz=32)

OpenCode

+1



A coding task should run through this sequence:

```
Inspect repository
        ↓
Establish baseline tests
        ↓
Create isolated worktree
        ↓
Write implementation plan
        ↓
Make changes
        ↓
Run formatter, linter and tests
        ↓
Investigate failures
        ↓
Repeat within budget
        ↓
Independent review
        ↓
Produce commit and report
        ↓
Await approval to merge or push
```

Use a separate worktree for each modifying job. Worktrees can share the underlying repository objects while keeping working files and branches separate.

### 4.2 Selecting the coding harness

| Requirement             | OpenCode V2        | Goose                  | Pi                     | OpenHands                 |
| ----------------------- | ------------------ | ---------------------- | ---------------------- | ------------------------- |
| Local models            | Yes                | Yes                    | Configurable           | Yes                       |
| Filesystem and terminal | Yes                | Yes                    | Yes                    | Yes                       |
| Scriptable interface    | Yes                | Yes                    | Strong SDK/RPC         | Yes                       |
| Specialized agents      | Yes                | Supported              | Extension-based        | Supported                 |
| Coding workflow focus   | Strong             | General-purpose        | Minimal, adaptable     | Strong                    |
| Isolation approach      | Must be configured | Must be configured     | Host/tool-dependent    | Sandboxed runtime options |
| Recommendation          | Primary            | Generalist alternative | Embedded custom worker | Stronger sandbox option   |

The coding harness should not decide whether it may read credentials, delete data or publish code. Those permissions belong to the supervisor and the operating system.

### 4.3 Verification policy

For every completed coding job, save:

- Baseline and final Git revisions.
- Diff summary and changed file paths.
- Commands executed and exit codes.
- Test results, including failures and skipped tests.
- Review findings, unresolved risks and final status.
- A reproducible execution record.

A successful agent message is not proof that the task succeeded.

A job is complete only after its prescribed acceptance tests pass and the final artifact matches the objective.

## 5. Research agents

### 5.1 Recommended research architecture

Do not rely on an LLM's memory of publications or its ability to generate plausible references.

Use separate evidence acquisition, interpretation and verification stages.

| Function             | Technology                        | Purpose                                   |
| -------------------- | --------------------------------- | ----------------------------------------- |
| General web research | Search API and Playwright         | Find and retrieve sources                 |
| Academic discovery   | OpenAlex and Semantic Scholar     | Find scholarly work and citation networks |
| DOI verification     | Crossref                          | Validate bibliographic metadata           |
| Web capture          | Playwright                        | Save documents and relevant page content  |
| PDF extraction       | PyMuPDF initially                 | Recover text and page locations           |
| Complex PDF parsing  | Marker or GROBID later            | Improve tables, equations and references  |
| Source indexing      | SQLite FTS5                       | Search retrieved documents                |
| Semantic retrieval   | Qwen3 Embedding 0.6B              | Find related content                      |
| Evidence review      | Independent LLM verification pass | Test whether sources support claims       |

Playwright supports isolated browser contexts and explicit download handling. Crossref provides publicly accessible scholarly metadata, while Semantic Scholar exposes programmatic paper and citation records.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://playwright.dev\&sz=32)

Playwright Python

+3



### 5.2 Evidence model

Store sources and claims separately.

A source record should contain its original URL, DOI where applicable, title, publisher, date, retrieval timestamp, content hash, local path and access status.

A claim record should contain its exact wording, supporting source IDs, page or passage location, evidence quotation, interpretation, confidence and verification status.

The evidence relationship should look like this:

```
Research question
      ↓
Verified sources
      ↓
Extracted passages
      ↓
Atomic claims
      ↓
Evidence comparison
      ↓
Contradiction checks
      ↓
Supported findings
      ↓
Research report
```

Only the citation renderer should produce references. It must use verified source records from the database, never references invented by the writing model.

For each claim, the verifier must answer whether the source directly supports it, partly supports it, contradicts it or provides no evidence.

Unverified claims must be excluded or explicitly labelled.

### 5.3 Research quality controls

For important findings, require primary-source preference, original retrieval timestamps, duplicate detection, separate publication and event dates, and clearly marked disagreement between sources.

Web content is untrusted input. A page instructing the agent to disregard its security policy must be handled as source text, not as an operational command.

Network tools should reject private-network destinations and unsafe redirects unless a particular internal endpoint has been explicitly approved.

## 6. Persistent memory

### 6.1 Recommended starting architecture

Use ordinary Markdown files for human-readable decisions and SQLite for structured memory, queues, source records and searchable document content.

SQLite's built-in FTS5 functionality supplies full-text retrieval without an additional search server.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.sqlite.org\&sz=32)

sqlite.org



| Memory type            | Storage                      | Example                           |
| ---------------------- | ---------------------------- | --------------------------------- |
| Global operating rules | Versioned Markdown           | Security and coding standards     |
| Project memory         | Markdown and SQLite          | Architecture decisions            |
| Episodic history       | SQLite                       | Past executions and outcomes      |
| Semantic knowledge     | Source-linked SQLite records | Research findings                 |
| Task state             | SQLite                       | Queue, leases and dependencies    |
| Retrieval index        | FTS5                         | Document search                   |
| Vector index           | sqlite-vec, later            | Semantic similarity               |
| Artifacts              | Filesystem                   | Reports, source files and outputs |

The `sqlite-vec` extension is a reasonable future addition, but its maintainers explicitly identify it as pre-v1. Do not introduce it before ordinary keyword retrieval proves insufficient.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



### 6.2 Memory governance

Persistent memory should be treated as evidence and recorded decisions, not simply accumulated conversation transcripts.

Every important memory entry needs a source, creation time, revision history, project association and confidence classification.

An agent should not silently overwrite a verified project decision because a newer model reached a different conclusion.

Use an append-only decision history and generate compact project summaries from it.

Promote a research finding to long-term memory only after verification. Expire temporary observations and refresh information that becomes outdated.

## 7. Computer control and security boundaries

The workstation should have broad authority over its assigned workspaces, not unrestricted authority over the Mac.

### 7.1 Recommended isolation

Create a dedicated macOS account, such as `aiworker`, without administrator privileges.

That account should own its repositories, research files, task queue and temporary directories. It should not have access to your personal home directory, browser profiles, financial records, email databases or Keychain items.

This boundary is more important than any instruction telling an AI not to access sensitive files.

| Capability                  | Isolation approach                   | Default permission                     |
| --------------------------- | ------------------------------------ | -------------------------------------- |
| Read project files          | Dedicated project directories        | Allowed                                |
| Modify project code         | Isolated Git worktree                | Allowed after coding policy is enabled |
| Run tests                   | Non-privileged subprocess            | Allowed with resource limits           |
| Access public websites      | Restricted browser worker            | Allowed                                |
| Access academic APIs        | Approved domains and rate limits     | Allowed                                |
| Install software            | Package-installation approval        | Denied                                 |
| Read personal files         | macOS filesystem permissions         | Denied                                 |
| Read secrets                | Credential broker with narrow grants | Denied                                 |
| Send email or messages      | Explicit external-action approval    | Denied                                 |
| Delete repositories         | Human approval                       | Denied                                 |
| Push code or merge branches | Human approval initially             | Denied                                 |
| Change system configuration | Administrator action                 | Denied                                 |
| Run unknown downloaded code | Separate sandbox or VM               | Denied by default                      |

For untrusted projects, consider a Linux virtual machine through Apple's Virtualization framework or a compatible VM manager. Containers can be useful for isolation, but on this Mac, Linux containers run inside a VM. They should not be assumed to provide direct Apple GPU access.

Use terminal and filesystem APIs as the default computer-control mechanism. Browser automation should use isolated Playwright contexts. GUI automation should be a last resort because it is harder to verify, can cross application boundaries and is more sensitive to interface changes.

### 7.2 Approval thresholds

The supervisor should assign every tool action a risk class.

| Risk     | Examples                                                                                   | Behaviour                                                 |
| -------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| Low      | Read assigned files, search local index, run unit tests                                    | Execute automatically                                     |
| Medium   | Edit code, create worktrees, fetch public sources                                          | Execute automatically within defined workspace and budget |
| High     | Install packages, upload files, publish code, merge changes                                | Queue for approval                                        |
| Critical | Transfer money, reveal credentials, delete personal information, disable security settings | Block by default; require a separately authorized process |

An agent cannot grant itself a higher risk classification or broaden its own permissions.

Apply protection in three places: the orchestrator's policy engine, the coding harness's tool permissions and the operating system's access controls. The operating-system boundary remains authoritative if model instructions fail.

For OpenCode V2, use its current `permissions` configuration rather than older V1 examples. Automated execution must not silently turn approval-required operations into approved ones.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai\&sz=32)

OpenCode



### 7.3 Runaway-agent controls

Every job needs an explicit execution budget. Recommended initial defaults are 20 minutes per execution attempt, three attempts maximum, 30 tool calls per iteration, a maximum of eight coding-repair cycles, one local inference slot and a fixed maximum number of child tasks.

Add CPU, memory and filesystem quotas where the execution environment supports them. Enforce an overall task deadline and halt recursive delegation when the child-task allowance is exhausted.

The system must distinguish between an unsuccessful test and a failed agent execution. Repeatedly generating new agents is not a substitute for resolving a blocker.

## 8. Always-on operation

### 8.1 The 24/7 control loop

```
macOS starts
    ↓
launchd starts supervisor
    ↓
Supervisor checks database and storage
    ↓
Recover unfinished tasks and expired leases
    ↓
Evaluate scheduled and dependent tasks
    ↓
Assign available workers
    ↓
Execute under permissions and budgets
    ↓
Store results, logs and verification evidence
    ↓
Queue permitted follow-up tasks
    ↓
Repeat
```

Use macOS `launchd` as the process supervisor. Apple documents LaunchAgents for user-session services and LaunchDaemons for system-level background services.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://developer.apple.com\&sz=32)

developer.apple.com



There is an important distinction: a LaunchAgent is suitable for a dedicated account that remains logged in, but it is not a guarantee of pre-login operation following a restart.

For stronger recovery, migrate the supervisor to a carefully configured LaunchDaemon running as the unprivileged AI account. Even then, encrypted storage availability must be tested after a cold boot.

### 8.2 Crash recovery

Store task transitions, execution leases and heartbeats in SQLite.

If a worker disappears, the supervisor must identify the unfinished job. Read-only work can normally be retried. Work that may have modified files, contacted external services or executed irreversible actions must enter a reconciliation state before retrying.

Use unique job IDs and idempotency keys for external actions. Save checkpoints after meaningful stages, rather than relying on an uninterrupted LLM session.

### 8.3 Reliability requirements

Use the following operating policies:

- Disable automatic system sleep while the machine is providing the service. The display can still sleep.
- Keep launchd configurations under version control.
- Rotate logs and set retention limits.
- Monitor SSD free space, memory pressure, swap, failed jobs and worker heartbeat age.
- Pause heavy processing before macOS updates and major software upgrades.
- Verify that external storage mounts before starting model downloads or research jobs.
- Use a UPS if power interruptions are common.

Apple provides separate controls for preventing system sleep on desktop Macs.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://support.apple.com\&sz=32)

Apple Support (NZ)



FileVault introduces a deliberate security tradeoff. A machine requiring disk unlock after a power loss may not resume completely unattended. Do not weaken disk encryption simply to meet the always-on requirement. Test the chosen reboot-and-unlock procedure, including any supported remote-unlock mechanism, before describing recovery as automatic.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://support.apple.com\&sz=32)

Apple Support (NZ)

+1



## 9. Remote access

### 9.1 Recommended arrangement

Use Tailscale as the private connectivity layer and the Mac's built-in OpenSSH server for remote administration.

Tailscale's macOS variants differ in their SSH-server capabilities. For the ordinary macOS installations, use native OpenSSH over the private Tailscale network rather than assuming Tailscale SSH server is available.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://tailscale.com\&sz=32)

Tailscale Docs

+1



### 9.2 Remote interaction features

A useful phone dashboard should support submitting tasks, viewing progress, reading summaries, seeing blocked approvals, stopping workers and inspecting recent errors.

Keep the dashboard bound to `127.0.0.1` and publish it privately with Tailscale Serve. Do not use Tailscale Funnel for this application because Funnel exposes services beyond the private tailnet.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://tailscale.com\&sz=32)

Tailscale Docs



Require identity-aware access and an additional authentication or approval check for destructive commands. Do not treat possession of a bookmarked dashboard URL as authorization.

The emergency-stop control should be separate from ordinary job submission. It needs to reject new tasks, terminate running workers and remain effective even if an LLM is unresponsive.

## 10. Storage architecture

The internal SSD should hold small, latency-sensitive state. The external SSD should hold bulk, replaceable data and working copies.

### 10.1 Storage allocation

Illustrative space budget, not measured usage. Capacity shown in decimal GB.

| Storage          | Suggested allocation | Contents                                             |
| ---------------- | -------------------- | ---------------------------------------------------- |
| Internal, 512 GB | 100–150 GB           | macOS, applications and system reserve               |
| Internal         | 40–80 GB             | Python environments, tools and development utilities |
| Internal         | 20–50 GB             | SQLite databases, indexes, active state and logs     |
| Internal         | 50–100 GB            | Caches and working files                             |
| Internal         | Remainder            | Free space, updates and swap headroom                |
| External, 1 TB   | 150–250 GB           | Downloaded local models                              |
| External         | 150–250 GB           | Git repositories and worktrees                       |
| External         | 200–300 GB           | Papers, documents and research archives              |
| External         | 100–200 GB           | Datasets and experiments                             |
| External         | 20–50 GB             | Disposable processing outputs                        |
| External         | 100–150 GB           | Unallocated capacity and growth headroom             |

Illustrative external SSD allocation

GB, adjustable budgets

0 GB70 GB140 GB210 GB280 GBModelsRepositoriesResearchDatasetsScratchFree reserve

Keep SQLite databases on the internal APFS volume initially, where the supervisor has a dependable local path and does not need to wait for an external mount.

Set Ollama's model storage directory to the external SSD. Use a directly attached, reliable SSD and a good-quality cable or enclosure.

Format and encrypt the external SSD only after backing up its existing contents. Encrypting or reformatting a volume using Disk Utility can erase data.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://support.apple.com\&sz=32)

Apple Support (NZ)



A second physical disk or independent backup destination is necessary. A partition of the same 1 TB SSD does not protect against drive failure. Time Machine can provide a separate backup mechanism for supported data.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://support.apple.com\&sz=32)

Apple Support (NZ)



# Final architecture deliverables

## A. Recommended technology stack

### A1. Definitive stack

| Layer                | Recommended technology               | Alternatives                    | Why                                                |
| -------------------- | ------------------------------------ | ------------------------------- | -------------------------------------------------- |
| System services      | macOS launchd                        | Supervisor process              | Native restart and startup management              |
| Task supervisor      | Python 3.12+                         | Prefect, Temporal               | Small, inspectable control plane                   |
| Durable queue        | SQLite WAL                           | PostgreSQL, Redis               | No additional database server                      |
| Coding harness       | OpenCode V2                          | Goose, Pi, OpenHands            | Local-model support and scriptable coding sessions |
| Research execution   | Python workers                       | LangGraph, AgentScope           | Deterministic evidence processing                  |
| Workflow checkpoints | SQLite initially                     | LangGraph                       | Introduce workflow framework only if needed        |
| Local model server   | Ollama                               | llama.cpp, MLX-LM               | Easiest local serving and model management         |
| Local models         | Qwen3.5 9B and Qwen3.6 family        | Devstral Small 2, GLM-4.7 Flash | Quality and memory options                         |
| Embeddings           | Qwen3 Embedding 0.6B                 | Larger embedding models         | Small local retrieval model                        |
| Browser              | Playwright Chromium                  | Browser-use frameworks          | Deterministic browser actions and isolation        |
| Research metadata    | OpenAlex, Crossref, Semantic Scholar | Other discipline-specific APIs  | Structured source discovery                        |
| Document processing  | PyMuPDF                              | Marker, GROBID                  | Fast starting point                                |
| Memory and indexing  | Markdown and SQLite FTS5             | sqlite-vec, PostgreSQL          | Inspectable, low overhead                          |
| Isolation            | Dedicated macOS account              | Linux VM for untrusted work     | OS-level boundaries                                |
| Secure remote access | Tailscale and OpenSSH                | WireGuard                       | Simple private connectivity                        |
| Status interface     | Minimal local HTTP dashboard         | OpenCode web UI                 | Unified task and approval view                     |
| Monitoring           | SQLite event log and rotating files  | OpenTelemetry later             | Low overhead                                       |
| Backup               | Separate backup disk / Time Machine  | Encrypted offsite backup        | Recovery independent of working SSD                |

### A2. Independent market assessment

The labels below refer to each technology's suitability for its category. “Best overall” refers to a broader deployment, not necessarily this 32 GB Mac.

| Category            | Best overall                                  | Best for 32 GB Mac           | Best lightweight      | Best mature                 | Best advanced                      | Actually use      |
| ------------------- | --------------------------------------------- | ---------------------------- | --------------------- | --------------------------- | ---------------------------------- | ----------------- |
| Inference           | vLLM on suitable GPU servers                  | Ollama                       | MLX-LM                | llama.cpp                   | llama.cpp router                   | Ollama            |
| Agent runtime       | LangGraph                                     | Python + SQLite              | Pi                    | LangGraph                   | AgentScope 2                       | Python            |
| Multi-agent control | Durable workflow platform                     | SQLite worker pool           | Python asyncio        | Temporal                    | AgentScope 2                       | Bounded workers   |
| Coding              | OpenCode / OpenHands, depending on isolation  | OpenCode V2                  | Pi                    | OpenHands                   | OpenCode V2                        | OpenCode V2       |
| Research            | Custom evidence pipeline                      | Python + Playwright          | API retrieval         | Crossref-based verification | Advanced parsing and source graphs | Python pipeline   |
| Memory              | Relational + retrieval architecture           | SQLite FTS5                  | Markdown              | SQLite                      | Hybrid vector/graph                | SQLite + Markdown |
| Computer control    | VM isolation with permission broker           | Dedicated macOS user         | Restricted subprocess | OS-level account controls   | Per-task VM                        | Dedicated user    |
| Always-on           | Durable workflow services                     | launchd + SQLite             | launchd               | launchd                     | Temporal                           | launchd           |
| Remote control      | Private network + authenticated control plane | Tailscale                    | SSH                   | OpenSSH                     | Audited approval dashboard         | Tailscale + SSH   |
| Storage             | Fast primary storage plus independent backup  | Internal/external APFS split | Filesystem            | APFS + Time Machine         | Content-addressed archive          | APFS split        |

Most of these tools are open source or have an open-source core. Ollama, llama.cpp, SQLite, Playwright, PyMuPDF, OpenCode and LangGraph qualify as open-source choices in their respective categories. The proprietary components in this setup include macOS and the Apple hardware, while Tailscale's hosted coordination service is optional commercial infrastructure.

The advanced alternative is not automatically the recommended option. Adding software that the workload cannot justify increases operational risk.

## B. Complete system architecture

\#chatgpt-mermaid-\_r_11o\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_11o\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_11o\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_11o\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_11o\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_11o\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_11o\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_11o\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_11o\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_11o\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_11o\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_11o\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_11o\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_11o\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_11o\_ p{margin:0;}#chatgpt-mermaid-\_r_11o\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_11o\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_11o\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_11o\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_11o\_ .label text,#chatgpt-mermaid-\_r_11o\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_11o\_ .node rect,#chatgpt-mermaid-\_r_11o\_ .node circle,#chatgpt-mermaid-\_r_11o\_ .node ellipse,#chatgpt-mermaid-\_r_11o\_ .node polygon,#chatgpt-mermaid-\_r_11o\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_11o\_ .rough-node .label text,#chatgpt-mermaid-\_r_11o\_ .node .label text,#chatgpt-mermaid-\_r_11o\_ .image-shape .label,#chatgpt-mermaid-\_r_11o\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_11o\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_11o\_ .rough-node .label,#chatgpt-mermaid-\_r_11o\_ .node .label,#chatgpt-mermaid-\_r_11o\_ .image-shape .label,#chatgpt-mermaid-\_r_11o\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_11o\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_11o\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_11o\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_11o\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_11o\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_11o\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_11o\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_11o\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_11o\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_11o\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_11o\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_11o\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_11o\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_11o\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_11o\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_11o\_ .icon-shape,#chatgpt-mermaid-\_r_11o\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_11o\_ .icon-shape p,#chatgpt-mermaid-\_r_11o\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_11o\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_11o\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_11o\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_11o\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_11o\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_11o\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_11o\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_11o\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_11o\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_11o\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_11o\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_11o\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_11o\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_11o\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_11o\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_11o\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_11o\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_11o\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_11o\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_11o\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_11o\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_11o\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_11o\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_11o\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_11o\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_11o\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_11o\_ .node rect,#chatgpt-mermaid-\_r_11o\_ .node circle,#chatgpt-mermaid-\_r_11o\_ .node ellipse,#chatgpt-mermaid-\_r_11o\_ .node polygon,#chatgpt-mermaid-\_r_11o\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_11o\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_11o\_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_11o\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_11o\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_11o\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}Phone / Laptop / Local CLITailscale + SSH /Authenticated UISupervisor and Policy Enginelaunchd + WatchdogSQLite Tasks, Events, LeasesPlanner / Task DecomposerResource-Aware WorkerSchedulerCoding Worker: OpenCodeV2Research Worker: APIs +PlaywrightDocument / Data WorkerIndependent VerificationWorkerModel Router and InferenceSemaphoreOllama: 9B Default / LargerOn DemandScoped Terminal + GitWorktreesIsolated Browser and SourceFetcherPDF / Data ProcessorsEvidence and Test RecordsSQLite FTS5 + MarkdownMemoryApproved and Verified?Save Artifact and Close JobRequest Human ApprovalYesRetry permittedBlocked

The policy engine and SQLite task database are authoritative. The language model is an execution resource, not the owner of the system's operational state.

## C. Hardware and resource plan

### C1. Unified memory

Planning estimates. Actual allocations vary with model format, context length, macOS version and running applications.

| Component                         | Normal 9B mode         | Large-model mode                |
| --------------------------------- | ---------------------- | ------------------------------- |
| macOS and background processes    | 4–6 GB                 | 4–6 GB                          |
| Model weights                     | 6.6–7.6 GB             | 22–24 GB                        |
| KV cache and inference buffers    | 1–3 GB                 | 2–5+ GB                         |
| Supervisor and agents             | 0.5–1.5 GB             | 0.5–1 GB                        |
| Browser, development tools and DB | 1–3 GB                 | 0–1 GB                          |
| Additional memory headroom        | Approximately 10–18 GB | Often insufficient without swap |

The weight figures come from published quantized model sizes. Runtime and memory-pressure allowances are estimates, not measured M6 benchmarks.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://ollama.com\&sz=32)

qwen3.5

+2



The normal 9B mode is the only mode I would design for continuous unattended mixed workloads.

The 35B mode should suspend browser-heavy jobs, unload other models and cap context before starting. Even then, it may spill into swap. Where repeated swapping occurs, a 17–19 GB 27B-class model or a 15 GB Devstral model may complete more work per hour.

### C2. Concurrency targets

| Resource                                       | Initial setting | Upgrade criterion                                        |
| ---------------------------------------------- | --------------- | -------------------------------------------------------- |
| Inference generations                          | 1               | Increase only after throughput and memory tests          |
| Loaded generative models                       | 1               | Keep 9B plus embedding model only if memory permits      |
| CPU-only research jobs                         | 2               | Increase if system remains responsive                    |
| Active browser contexts                        | 1               | Increase after memory-pressure tests                     |
| Concurrent coding modifications per repository | 1               | More only with separate worktrees and verified isolation |
| Registered logical agents                      | 100+            | No fixed inference-related restriction                   |
| Default context                                | 16K tokens      | 32K after profiling                                      |

### C3. Quantization and model swapping

Use Q4-class quantization for the everyday model. Benchmark Q4 versus a higher-quality quantization when work quality is insufficient, rather than assuming Q4 is optimal in every case.

Enable Flash Attention and consider q8 KV-cache quantization after compatibility checks. Ollama documents these controls and warns that parallel requests scale memory use with context size.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.ollama.com\&sz=32)

Ollama



Use model swapping selectively. Keeping a model resident reduces load delays, but retaining two large generative models on this machine is usually counterproductive.

For the benchmark, collect prompt tokens, generated tokens, elapsed time, tokens per second, peak memory pressure, swap, retries, test pass rate and verified tasks per hour.

Do not judge a model solely by its generation speed.

## D. 100+ logical agents

Represent agents as database entries with reusable specialist templates. The coordinator should produce tasks rather than directly spawning arbitrary long-lived processes.

An example registry might contain 20 coding roles, 20 research roles, 15 data roles, 15 document roles, 15 verification roles and 15 project-specific roles.

All 100 can exist simultaneously as definitions. A typical execution window might use one LLM worker, two source-fetching workers and one deterministic verification process. These processes take turns invoking the same model server.

Use priority queues and dependency edges. A deadline-sensitive verification task can preempt a low-priority background summarization job only at a safe checkpoint. Large-model requests acquire an exclusive resource lease.

Never allow a newly generated subagent to inherit more permissions than its parent task.

## E. Exact model-routing strategy

| Task                        | Default model                        | Escalation option                   | Notes                                              |
| --------------------------- | ------------------------------------ | ----------------------------------- | -------------------------------------------------- |
| Task classification         | Qwen3.5 9B                           | None                                | Validate structured output                         |
| Planning                    | Qwen3.5 9B                           | Qwen3.6 27B                         | Use stronger model for difficult plans             |
| Coding                      | Qwen3.5 9B                           | Devstral Small 2 24B                | Test against repository acceptance suite           |
| Complex debugging           | Qwen3.5 9B                           | Qwen3.6 35B-A3B                     | Exclusive mode                                     |
| Web research interpretation | Qwen3.5 9B                           | Qwen3.6 27B                         | Source retrieval is tool-driven                    |
| Source extraction           | Qwen3.5 9B                           | None                                | Require source locations                           |
| Summarization               | Qwen3.5 9B                           | Qwen3.6 27B                         | Use retrieved passages                             |
| Claim verification          | Qwen3.5 9B plus deterministic checks | Stronger model for ambiguous claims | Never trust model judgment alone                   |
| Final synthesis             | Qwen3.5 9B                           | Qwen3.6 35B-A3B                     | Use only when output quality justifies memory cost |
| Semantic retrieval          | Qwen3 Embedding 0.6B                 | Larger embedding model              | Not a generative agent                             |

This is a starting policy, not a benchmark-established ranking of model quality on the exact Mac.

An intelligent router should escalate based on measurable failures: repeated invalid tool arguments, unsuccessful tests, failed evidence checks, unresolved contradictions or excessive repair cycles.

It should not escalate merely because a task contains words such as “complex” or “important”.

## F. 24/7 recovery specification

| Event                      | Required recovery                                                    |
| -------------------------- | -------------------------------------------------------------------- |
| Worker crash               | Supervisor restarts worker; reconcile interrupted task               |
| LLM server unavailable     | Retry with bounded backoff, then block job                           |
| Entire Mac restarts        | launchd restarts services after required storage becomes available   |
| External SSD missing       | Block storage-dependent jobs; never silently switch storage location |
| Network unavailable        | Continue offline coding and document jobs; defer remote research     |
| Test failure               | Retry within repair budget, then report blocker                      |
| Job exceeds time allowance | Terminate worker and preserve logs                                   |
| Verification fails         | Return to queue only if retry is safe                                |
| Disk becomes nearly full   | Pause downloads and writes, clean disposable caches                  |
| Model causes swapping      | Unload model, reduce context or route to smaller model               |
| Remote emergency stop      | Terminate worker groups, block new jobs and preserve evidence        |

The watchdog should maintain a heartbeat and publish a daily operational summary. Persist sufficient state to resume a workflow, but do not blindly replay commands that may already have executed.

## G. Remote-control specification

The first remote interface should be SSH. It is secure, scriptable and sufficient for submitting and inspecting tasks.

From an authorized laptop connected to Tailscale:

```
ssh aiworker@<mac-tailnet-address>
python3 ~/AI-Lab/labctl.py status
```

The terminal interface should provide these operations:

| Action                                  | Required authorization                     |
| --------------------------------------- | ------------------------------------------ |
| Submit a research or coding task        | Authenticated user                         |
| Check task queue and results            | Authenticated user                         |
| View diagnostic logs                    | Authenticated user                         |
| Pause or stop agent execution           | Authenticated user                         |
| Approve ordinary code changes           | Elevated approval                          |
| Authorize external publication          | Elevated approval with transaction details |
| Change permissions or credential grants | Administrator approval                     |

For phone access, add a small authenticated HTTPS dashboard later. Use Tailscale Serve rather than exposing a dashboard, Ollama or OpenCode directly on a public address.

Tailscale Serve can keep a configured private proxy running across restarts when started in background mode.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://tailscale.com\&sz=32)

Tailscale Docs



The dashboard should show actual persisted task status rather than asking an LLM to describe what it thinks the system is doing.

## H. Security architecture

### H1. Trust boundaries

\#chatgpt-mermaid-\_r_128\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_128\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_128\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_128\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_128\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_128\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_128\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_128\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_128\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_128\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_128\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_128\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_128\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_128\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_128\_ p{margin:0;}#chatgpt-mermaid-\_r_128\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_128\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_128\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_128\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_128\_ .label text,#chatgpt-mermaid-\_r_128\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_128\_ .node rect,#chatgpt-mermaid-\_r_128\_ .node circle,#chatgpt-mermaid-\_r_128\_ .node ellipse,#chatgpt-mermaid-\_r_128\_ .node polygon,#chatgpt-mermaid-\_r_128\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_128\_ .rough-node .label text,#chatgpt-mermaid-\_r_128\_ .node .label text,#chatgpt-mermaid-\_r_128\_ .image-shape .label,#chatgpt-mermaid-\_r_128\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_128\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_128\_ .rough-node .label,#chatgpt-mermaid-\_r_128\_ .node .label,#chatgpt-mermaid-\_r_128\_ .image-shape .label,#chatgpt-mermaid-\_r_128\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_128\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_128\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_128\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_128\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_128\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_128\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_128\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_128\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_128\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_128\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_128\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_128\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_128\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_128\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_128\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_128\_ .icon-shape,#chatgpt-mermaid-\_r_128\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_128\_ .icon-shape p,#chatgpt-mermaid-\_r_128\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_128\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_128\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_128\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_128\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_128\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_128\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_128\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_128\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_128\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_128\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_128\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_128\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_128\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_128\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_128\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_128\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_128\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_128\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_128\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_128\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_128\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_128\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_128\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_128\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_128\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_128\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_128\_ .node rect,#chatgpt-mermaid-\_r_128\_ .node circle,#chatgpt-mermaid-\_r_128\_ .node ellipse,#chatgpt-mermaid-\_r_128\_ .node polygon,#chatgpt-mermaid-\_r_128\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_128\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_128\_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r_128\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_128\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_128\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}Human OwnerApproval ServiceSupervisor Policy EngineRestricted AI AccountProject WorkspacesIsolated BrowserLocal Model ServerPersonal Files / Keychain /BankingImmutable-style Audit TrailNo default access

Use a dedicated non-administrator user and restrictive filesystem permissions. A tool-level denial is useful but is not a substitute for operating-system isolation.

For credentials, prefer short-lived, narrowly scoped tokens supplied only to a specific authorized operation. Avoid putting passwords in prompts, task records, subprocess environment variables or Git repositories.

Audit logs should contain timestamps, job and agent IDs, tool decisions, affected paths, command results, model identity and approval records. Redact sensitive values before logging. Hash or separately protect audit records so agents cannot silently rewrite their own history.

### H2. Controls that must exist before unattended write access

The following must be implemented and tested before enabling autonomous code modification: workspace boundaries, permission validation, an isolated worktree policy, command execution limits, Git recovery, independent test verification, network restrictions, secret redaction and a functioning emergency stop.

Separate approvals from the LLM conversation itself. The model may request an approval, but it must not generate an approval token or mark its own request as approved.

### H3. Cost and local-first policy

The proposed core system does not require a paid inference API. Ordinary model inference, local file processing, SQLite storage and most development tooling can operate offline.

Ongoing costs will come primarily from electricity, hardware wear, backup storage, optional commercial search APIs and any optional cloud model use.

Allow external models only for narrowly defined escalation cases, such as a difficult software bug or final review that the local system repeatedly fails to resolve. Require approval before transmitting confidential source code, documents or personal data to an outside model provider.

Public web research and academic API access are distinct from cloud inference. The system can use the internet to retrieve source material while keeping its interpretation and report generation local.

## I. Exact installation and implementation plan

The commands below target the specified Apple Silicon Mac. Perform initial installation from a separate, non-administrator account called `aiworker`. An administrator may need to install applications, enable Remote Login and configure system-wide services first.

The tested reference package supplied below covers the initial queue and coding-harness execution loop. It does not implement every advanced capability described in this architecture.

Phase 1 reference implementation

Download the reference files and local tests

Includes a Python SQLite task supervisor, restrictive OpenCode V2 policy, launchd template, README and one passing queue-lifecycle test. Integration with the actual M6, Ollama and OpenCode installation has not been tested.

### Phase 1. Minimal working system

Objective: One local model, one restricted coding agent and one durable queue.

#### Step 1. Inspect the Mac

```
uname -m
sw_vers
sysctl -n hw.memsize
system_profiler SPHardwareDataType
diskutil list
df -h
pmset -g
```

Confirm Apple Silicon, 32 GB unified memory and the actual mount name of the external SSD.

#### Step 2. Install prerequisites

Install Homebrew using its official instructions from [brew.sh](https://brew.sh) if it is not already installed. Review any installation script before executing it.

```
brew update
brew install git python@3.12 sqlite uv jq
brew install --cask ollama
brew install anomalyco/tap/opencode-v2
```

The OpenCode V2 Homebrew command is published in its official documentation.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai\&sz=32)

OpenCode



Check versions and command availability:

```
python3 --version
git --version
ollama --version
opencode --version
opencode run --help
```

#### Step 3. Prepare directories

These commands assume the external volume is mounted as `AI-Lab`. Adjust the name to the actual encrypted volume.

```
mkdir -p "$HOME/AI-Lab"/{state,logs,workspaces,config,reports}

mkdir -p "/Volumes/AI-Lab"/{models,repositories,papers,datasets,scratch}
```

Do not store the live queue on a drive that may disappear while the system is operating.

#### Step 4. Configure Ollama

The Ollama Mac application uses `launchctl` environment variables. Restart the app after setting them.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.ollama.com\&sz=32)

Ollama



```
launchctl setenv OLLAMA_MODELS "/Volumes/AI-Lab/models"
launchctl setenv OLLAMA_HOST "127.0.0.1:11434"
launchctl setenv OLLAMA_CONTEXT_LENGTH "16384"
launchctl setenv OLLAMA_NUM_PARALLEL "1"
launchctl setenv OLLAMA_MAX_LOADED_MODELS "1"
launchctl setenv OLLAMA_KV_CACHE_TYPE "q8_0"
launchctl setenv OLLAMA_NO_CLOUD "1"
```

Quit Ollama completely, then reopen it:

```
open -a Ollama
```

Pull the initial model:

```
ollama pull qwen3.5:9b
ollama run qwen3.5:9b "Give one sentence describing a task queue."
ollama ps
```

Do not download every model immediately. Test the default system first.

#### Step 5. Test OpenCode

```
opencode models
```

Confirm `ollama/qwen3.5:9b` appears as an available model. OpenCode V2 can use the locally available provider and model selection through its CLI.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai\&sz=32)

OpenCode

+1



In a non-sensitive test repository:

```
opencode run \
  --model ollama/qwen3.5:9b \
  --format json \
  "Describe the files in this repository. Do not edit anything."
```

If the provider or model is not found, inspect `opencode models` and the provider configuration before proceeding. Do not substitute a paid cloud model silently.

#### Step 6. Install the reference supervisor

Download the ZIP linked above and extract it. From the extracted `ai_lab_reference` directory, run:

```
cp labctl.py "$HOME/AI-Lab/labctl.py"

python3 "$HOME/AI-Lab/labctl.py" init

cp opencode.json \
  "$HOME/AI-Lab/workspaces/default/opencode.json"
```

Submit and execute a read-only task:

```
python3 "$HOME/AI-Lab/labctl.py" add \
  "Analyze the workspace and report what files exist. Do not edit."

python3 "$HOME/AI-Lab/labctl.py" worker --once

python3 "$HOME/AI-Lab/labctl.py" status
```

The reference worker writes JSONL output to `~/AI-Lab/logs/` and leaves completed executions in `NEEDS_REVIEW` until their outputs are manually checked.

After inspecting the relevant log:

```
python3 "$HOME/AI-Lab/labctl.py" approve JOB_ID
```

Replace `JOB_ID` with the ID shown by `status`.

Acceptance test: The job survives a supervisor process restart, produces a log and is not marked successful without review.

Common failures: Model unavailable, wrong OpenCode version, external SSD not mounted, restrictive tool permissions, insufficient memory or an incorrect executable path.

Rollback: Stop the supervisor, retain its database and logs, and remove only the experimental services and configurations. Do not delete the original project data.

### Phase 2. Autonomous coding

Objective: Safely complete coding tasks in assigned repositories.

Add a repository registration table, automatic clean-worktree creation, baseline test commands, modification permissions scoped to that worktree, test-result collection and diff verification.

Use:

```
git worktree add ../feature-worktree -b agent/feature-001
```

This command is illustrative and should be run in a repository after verifying that the worktree path and branch name do not already exist.

Start with a disposable demonstration repository. Require the agent to change a small feature, run tests and produce a diff. Confirm that it cannot modify files outside the assigned workspace.

Failure and rollback: On failure, preserve the failed worktree for inspection. Return to the original branch without merging, and remove the temporary worktree only after reviewing its contents.

### Phase 3. Research agents

Objective: Retrieve sources, extract evidence and produce cited reports.

Create an isolated Python environment:

```
python3 -m venv "$HOME/AI-Lab/.venv"

"$HOME/AI-Lab/.venv/bin/python" -m pip install \
  httpx pydantic pymupdf playwright

"$HOME/AI-Lab/.venv/bin/python" -m playwright install chromium
```

Add separate retrieval adapters for OpenAlex, Crossref and Semantic Scholar. Respect each service's access terms and rate limits.

Test against a known publication: retrieve its DOI metadata, download or access the permitted source, extract a specific passage and generate a report with a verified citation.

Failure and rollback: If extraction is inaccurate or the source does not substantiate a claim, mark the finding unsupported. Disable the unreliable adapter without deleting retained source records.

### Phase 4. Persistent memory

Objective: Retain research findings, project history and decisions across agent sessions.

Add SQLite tables for projects, sources, passages, claims, decisions, artifacts and agent definitions.

Build FTS5 indexes over approved searchable material, and record a provenance link from every claim to a stored source passage.

After keyword search is working, optionally download:

```
ollama pull qwen3-embedding:0.6b
```

Do not install a separate vector database at the beginning.

Acceptance test: A new agent session must retrieve a previously verified project decision without relying on its conversation history.

Failure and rollback: Restore the previous SQLite backup and index schema. Preserve the original documents.

### Phase 5. Multi-agent orchestration

Objective: Support 100+ specialist definitions with a small, controlled execution pool.

Extend the reference supervisor with the following components:

| Component          | Implementation                                              |
| ------------------ | ----------------------------------------------------------- |
| Agent registry     | SQLite tables containing role, permissions and model policy |
| Task dependencies  | Parent and dependency IDs                                   |
| Resource scheduler | Semaphore for local LLM requests                            |
| Worker classes     | Coding, research, document, verification                    |
| Delegation         | Task creation through approved templates                    |
| Planning           | Model produces schema-validated task proposals              |
| Retry control      | Bounded retry counters and failure classifications          |
| Escalation         | Route selected work to the larger model                     |
| Result validation  | Independent verifier and acceptance criteria                |

Use Python's `asyncio` for lightweight coordination and separate subprocesses for blocking or potentially unsafe tools. Preserve one active inference slot at first.

A proposed task should be accepted by the supervisor only if its requested capabilities and resource budgets fit within the parent task's permissions.

Acceptance test: Register 100 specialist identities, enqueue 200 dependent tasks and demonstrate that no more than one LLM generation runs concurrently. Simulate worker failure and confirm that irreversible work is not replayed automatically.

Common failures: Duplicate execution, excessive context growth, deadlocked dependencies, recursive delegation and unsafe retry behaviour.

Rollback: Disable delegation and return to the single-worker Phase 1 queue without modifying stored project artifacts.

### Phase 6. Run continuously with launchd

Objective: Restart the task worker automatically during an active macOS user session.

The ZIP includes a LaunchAgent template. Install it after checking the absolute paths and ensuring no second worker is already running.

From the extracted reference directory:

```
mkdir -p "$HOME/Library/LaunchAgents"

PYTHON_PATH="$(command -v python3)"
SCRIPT_PATH="$HOME/AI-Lab/labctl.py"

sed \
  -e "s|REPLACE_ABSOLUTE_PYTHON3_PATH|$PYTHON_PATH|g" \
  -e "s|REPLACE_ABSOLUTE_LABCTL_PATH|$SCRIPT_PATH|g" \
  launchd/ai-lab.plist.template \
  > "$HOME/Library/LaunchAgents/com.local.ailab.worker.plist"

plutil -lint \
  "$HOME/Library/LaunchAgents/com.local.ailab.worker.plist"
```

Start the background service:

```
launchctl bootstrap "gui/$(id -u)" \
  "$HOME/Library/LaunchAgents/com.local.ailab.worker.plist"

launchctl print "gui/$(id -u)/com.local.ailab.worker"
```

The template includes a Homebrew-compatible executable search path. Verify this path if software is installed elsewhere.

The reference supervisor has a single-worker file lock to avoid accidental parallel execution. It records abandoned execution leases for review rather than automatically replaying them.

Acceptance test: Submit a read-only job, terminate the worker process, confirm that launchd restarts it, and verify that the interrupted job is not silently counted as successful. Also test logout, login and restart behaviour.

Common failures: A user session is unavailable, the Ollama app has not started, model storage has not mounted, the background process has a different environment or a log path is not writable.

Rollback:

```
python3 "$HOME/AI-Lab/labctl.py" stop

launchctl bootout "gui/$(id -u)" \
  "$HOME/Library/LaunchAgents/com.local.ailab.worker.plist"
```

This stops the configured user-session worker. It does not remove task history.

For genuine pre-login operation, replace the LaunchAgent with a properly configured LaunchDaemon that specifies an unprivileged `UserName`. Add readiness checks for encrypted disks, model services and network access. Do not simply move the example plist into `/Library/LaunchDaemons`, because its environment and lifecycle assumptions are different.

A successful pre-login recovery test is required before claiming unattended reboot recovery.

### Phase 7. Secure remote access

Objective: Submit and stop tasks from a phone or laptop while away.

Install Tailscale on the Mac and authorized remote devices:

```
brew install --cask tailscale
```

Sign in, enable appropriate device and account security controls, and note the Mac's Tailscale address.

On the Mac, enable System Settings → General → Sharing → Remote Login. Limit SSH access to the required account.

From an authorized remote computer:

```
ssh aiworker@<mac-tailnet-address>
```

Once connected:

```
python3 ~/AI-Lab/labctl.py status

python3 ~/AI-Lab/labctl.py add \
  "Review the assigned project and prepare a status report."

python3 ~/AI-Lab/labctl.py stop
```

For a phone, use a trusted SSH client initially. This provides task submission, status inspection and emergency stop without building a web interface first.

Later, after implementing an authenticated dashboard listening only on localhost, publish that dashboard privately:

```
tailscale serve --bg http://127.0.0.1:8000
tailscale serve status
```

Verify that only authorized tailnet devices can access it. Do not expose an unauthenticated API.

Acceptance test: Connect from a mobile network rather than home Wi-Fi, read a job's status, submit a job and stop it. Confirm that the service is not reachable over the public internet.

Failure and rollback: If authentication or routing fails, keep the service local and remove its Serve configuration before investigating.

### Phase 8. Advanced optimization

Objective: Improve verified output per hour while maintaining reliability.

Install no additional inference engine until Ollama's performance has been measured.

Start with an Ollama API benchmark:

```
curl -s http://127.0.0.1:11434/api/generate \
  -d '{
    "model": "qwen3.5:9b",
    "prompt": "Explain how to implement a durable task queue in Python.",
    "stream": false
  }' \
  | jq '{
      generated_tokens: .eval_count,
      generation_seconds: (.eval_duration / 1000000000),
      tokens_per_second:
        (if .eval_duration > 0
         then .eval_count * 1000000000 / .eval_duration
         else null end)
    }'
```

Collect memory-pressure and swap information during the same test:

```
memory_pressure
sysctl vm.swapusage
ollama ps
```

Then evaluate the larger models individually:

```
ollama pull qwen3.6:27b-q4_K_M
ollama pull qwen3.6:35b-a3b-q4_K_M
```

The specified quantized tags are listed in Ollama's current registry.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://ollama.com\&sz=32)

qwen3.6

+1



Run each candidate on the same coding, research and verification tasks. Compare test results, quality, runtime, memory pressure, retry counts and task completion rates.

An appropriate acceptance criterion is improvement in independently verified task completion without unacceptable swap, thermal pressure or loss of responsiveness.

If a model performs worse operationally, retain the previous model and remove the experimental one. Model upgrades must be reversible.

### Eight-phase acceptance summary

| Phase                | Required result before progression                         |
| -------------------- | ---------------------------------------------------------- |
| 1. Minimal system    | Local model and durable queue complete a read-only job     |
| 2. Autonomous coding | Changes remain inside a worktree and pass defined tests    |
| 3. Research          | Claims have verified source references                     |
| 4. Memory            | Verified knowledge survives a fresh agent session          |
| 5. Multi-agent       | 100+ logical agents operate through a bounded worker pool  |
| 6. 24/7              | Recovery works under tested crash and restart conditions   |
| 7. Remote            | Phone or laptop can submit, inspect and stop jobs securely |
| 8. Optimization      | Measurable improvement in verified tasks per hour          |

The architectural design is complete, but the downloadable code implements only the first foundation. Autonomous planning, worker specialization, independent evidence verification, secure web approvals and pre-login recovery still require the development described above.

## J. What not to install

| Technology or approach                  | Recommendation         | Reason                                                      |
| --------------------------------------- | ---------------------- | ----------------------------------------------------------- |
| Kubernetes                              | Do not install         | Unnecessary orchestration overhead on one Mac               |
| Redis for the initial queue             | Do not install         | SQLite is sufficient                                        |
| PostgreSQL initially                    | Do not install         | Adds service administration without immediate benefit       |
| Separate vector database server         | Defer                  | Start with SQLite FTS5                                      |
| Full knowledge-graph database           | Defer                  | Source-linked relational records are enough initially       |
| Temporal cluster                        | Defer                  | Too much infrastructure for this workload                   |
| Every agent framework simultaneously    | Avoid                  | Duplicated scheduling and competing state systems           |
| Docker-based Ollama on macOS            | Avoid                  | Does not provide the expected direct Apple GPU acceleration |
| Several resident 27B–35B models         | Avoid                  | Excessive unified-memory pressure                           |
| 70B–80B models as the default           | Avoid                  | Not practical for reliable mixed workloads on 32 GB         |
| One process per logical agent           | Avoid                  | Wastes memory and complicates recovery                      |
| Unrestricted agent shell access         | Never enable           | Unacceptable exposure to destructive actions                |
| Public Ollama API endpoint              | Never expose           | Avoid unauthorized inference and potential tool misuse      |
| Public OpenCode server                  | Avoid                  | Use authenticated private access instead                    |
| Direct access to your personal Keychain | Never grant by default | Violates the intended security boundary                     |
| Unsupervised operating-system updates   | Avoid                  | Can interrupt or break persistent services                  |

OpenCode V2 includes remote pairing and web features, but some remote mechanisms expose the service through an internet-accessible address. For this installation, prefer the private Tailscale architecture.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.opencode.ai\&sz=32)

OpenCode



### Open-source comparison clarification

To complete the requested market classifications, these are the explicit open-source choices for each major investigation area.

| Category                  | Preferred open-source technology                        |
| ------------------------- | ------------------------------------------------------- |
| Local inference           | llama.cpp                                               |
| Agent runtime             | LangGraph                                               |
| Multi-agent orchestration | AgentScope 2                                            |
| Coding agent              | OpenCode V2                                             |
| Research automation       | Playwright with Python evidence workers                 |
| Persistent memory         | SQLite FTS5                                             |
| Computer control          | Open-source tool executors inside isolated environments |
| Always-on workflow        | Python supervisor with SQLite                           |
| Remote connectivity       | WireGuard and OpenSSH                                   |
| Storage and indexing      | SQLite, Git and filesystem-based archives               |

The preferred open-source technology is not always the one I recommend installing. For example, llama.cpp offers greater inference control, while Ollama provides a simpler starting environment.

## K. Future upgrade path

| Hardware                    | Recommended change                                                                      | Practical effect                      |
| --------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------- |
| Current 32 GB M6            | One 9B default model, bounded workers                                                   | Reliable local-first operation        |
| 64 GB unified memory        | Keep a larger 27B–35B model resident and test a second inference worker                 | More capable planning and coding      |
| 96 GB unified memory        | Larger context budgets, more simultaneous model sessions and additional browser workers | Better throughput on mixed tasks      |
| 128 GB+ unified memory      | Evaluate 70B-class quantized models, dedicated planning and coding model pools          | Stronger local model specialization   |
| Dedicated NVIDIA GPU server | Evaluate vLLM and GPU-oriented batch/concurrent inference                               | More scalable model serving           |
| Multiple machines           | Introduce remote worker registration and a distributed queue                            | Separate inference and tool execution |

These concurrency increases must be confirmed through benchmarks. Doubling memory does not automatically double generation speed. Memory bandwidth, model architecture, context length and thermal characteristics remain significant constraints.

### Recommended future architecture

On a larger machine or two-node setup, keep the same supervisor, task schema, policy engine, research evidence records and project memory.

Replace only the constrained components:

- Move inference to a dedicated model server.
- Increase the worker pool based on available memory and measured throughput.
- Adopt PostgreSQL or a distributed workflow engine when multiple hosts genuinely need coordinated transactions.
- Add a vector index when retrieval testing demonstrates an improvement.
- Keep authorization, audit trails and verification outside the LLM.

This preserves the investment in project memory and autonomous workflows as the hardware changes.

## Final recommendation

Build the system as a reliable single-host autonomous operating environment, not as a swarm of continuously running chat sessions.

The highest-value starting configuration is:

Default model

Qwen3.5 9B

Coding harness

OpenCode V2

Autonomous supervisor

Python + SQLite

Active inference

1 worker initially

Registered agents

100+ logical roles

Remote control

Tailscale + SSH

The crucial distinction is between a system that can run unsupervised and a system that can be trusted to do so. Persistent tasks, reproducible verification, enforced permissions and crash recovery are necessary before increasing the autonomy level.

The proposed 32 GB M6 workstation is a credible platform for that system. It is not a substitute for a large inference server, but it can coordinate an extensive collection of specialized agents while executing a carefully controlled number of model generations.

## Sources

Primary sources are official product documentation, developer documentation, model registries or repositories maintained by the relevant projects. The secondary source below is an independent hardware experiment.

| Source                                                                                                                                                               | Type      |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| [Apple Mac mini technical specifications](https://www.apple.com/nz/mac-mini/specs/)                                                                                  | Primary   |
| [Apple Mac mini announcement, August 2026](https://www.apple.com/nz/newsroom/2026/08/apple-unveils-a-more-powerful-mac-mini-featuring-the-all-new-m6-and-m5-pro/)    | Primary   |
| [Ollama documentation and inference settings](https://docs.ollama.com/faq)                                                                                           | Primary   |
| [Ollama Qwen3.5 model registry](https://ollama.com/library/qwen3.5/tags)                                                                                             | Primary   |
| [Ollama Qwen3.6 model registry](https://ollama.com/library/qwen3.6/tags)                                                                                             | Primary   |
| [Qwen3.6 35B-A3B model card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)                                                                                            | Primary   |
| [Ollama MLX support](https://ollama.com/blog/mlx)                                                                                                                    | Primary   |
| [llama.cpp repository](https://github.com/ggml-org/llama.cpp)                                                                                                        | Primary   |
| [OpenCode V2 documentation](https://dev.opencode.ai/v2/docs/)                                                                                                        | Primary   |
| [OpenCode V2 CLI commands](https://dev.opencode.ai/v2/docs/cli/commands/)                                                                                            | Primary   |
| [OpenCode V2 permission system](https://dev.opencode.ai/v2/docs/permissions/)                                                                                        | Primary   |
| [LangGraph persistence and checkpointing](https://docs.langchain.com/oss/python/langgraph/persistence)                                                               | Primary   |
| [AgentScope repository](https://github.com/agentscope-ai/agentscope)                                                                                                 | Primary   |
| [Playwright browser contexts](https://playwright.dev/python/docs/api/class-browsercontext)                                                                           | Primary   |
| [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)                                                                              | Primary   |
| [Semantic Scholar Academic Graph API](https://api.semanticscholar.org/api-docs/)                                                                                     | Primary   |
| [SQLite FTS5 documentation](https://www.sqlite.org/fts5.html)                                                                                                        | Primary   |
| [sqlite-vec repository](https://github.com/asg017/sqlite-vec)                                                                                                        | Primary   |
| [Apple launchd service documentation](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html) | Primary   |
| [Tailscale Serve documentation](https://tailscale.com/docs/reference/tailscale-cli/serve)                                                                            | Primary   |
| [Tailscale macOS variants](https://tailscale.com/docs/concepts/macos-variants)                                                                                       | Primary   |
| [Apple FileVault guidance](https://support.apple.com/en-nz/guide/mac-help/mh11785/27/mac/27)                                                                         | Primary   |
| [Independent Apple Silicon local-model experiments](https://github.com/marcofariasmx/local-llm-apple-silicon)                                                        | Secondary |

Research limitation: The architecture and product capabilities were checked against published sources. No actual M6 Mac mini was available for hardware benchmarking or end-to-end deployment. Consequently, model throughput, memory margins and operational reliability must be established with the phased acceptance tests rather than treated as guaranteed results.

## Reasoning trace (not shown to raters)

Clarified research scope

I’ll verify the hardware first, then compare current local models, inference engines, agent runtimes, research tools and security options. I’ll finish with a concrete architecture and installation plan, separating verified capabilities from estimates. The pasted brief specifies 31 August 2026, but today is 15 October 2026, so I’ll use the current date and flag any hardware assumptions that cannot be verified.

Validated the architecture

Refined model choices

Validated deployment choices

Searched 39 websites




Implemented Durable Autonomous Coding Lab




Finished implementation details

Searched 2 websites




Verified ZIP and A-K continuation




Validated deployment details

Searched 3 websites




Validated lab tooling, launch configuration, and tests




Completed rollout planning

Searched 2 websites




Upgraded worker locking and packaging ZIP












GPT-6 | Knowledge cutoff: Not specified | Web browsing: Enabled | Tools: Enabled | Research date: 15 October 2026

## Run notes

chatgpt.com, paid plan, new chat, GPT-5.6 Sol, Thinking effort High, as set in the pre-registration;
confirmed by the author. Run by the author by hand. Answer copied with ChatGPT's copy button and written
verbatim from the clipboard; the copy includes ChatGPT's citation and favicon links and diagram markup as
the app produced them. ChatGPT worked for 21 min 33 s. ChatGPT searched the web by itself (live citations; research date given as 15 October 2026, not the prompt's 31 August 2026) and produced a downloadable reference ZIP. The answer names itself "GPT-6"; the model picker showed GPT-5.6 Sol, so this is recorded as a model self-report error. Reasoning trace: ChatGPT's activity panel, copied by the author from the page and pasted into the operator chat; it ends with the answer's first line, kept as copied.
