---
run_id: gpt__fast__p1-v1__apicheck1
set: api_check
family: gpt
vendor: OpenAI
mode: fast
native_label: reasoning effort none
channel: api
model_requested: gpt-5.6-sol
model_returned: gpt-5.6-sol
params:
  _token_field: max_completion_tokens
  reasoning_effort: none
max_tokens: 6000
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 1
date_run: '2026-10-06T11:25:15+00:00'
run_by: roshanaryal
finish_reason: length
usage:
  input_tokens: 2501
  output_tokens: 6000
  reasoning_tokens: 0
latency_s: 79.99
harness_version: 0.1.0
---

## Final answer

**Model:** OpenAI ChatGPT (exact backend/version not exposed) | **Knowledge cutoff:** June 2024 | **Web browsing/tools:** **Off**

> **Evidence limitation:** I cannot research or verify the ecosystem as of **31 August 2026** in this session. Also, the base **Apple M6 Mac mini** and any post–June 2024 releases are beyond my verified knowledge. I therefore will not invent current versions, benchmarks, model names, or URLs. The architecture below is a concrete, production-oriented design based on established technologies through June 2024, with explicit **2026 verification gates** before installation.

## Decisions at a glance

| Layer | Final pick |
|---|---|
| Remote interface | **Tailscale** + SSH; small authenticated web UI; ntfy/Matrix notifications |
| Service supervision | **launchd**; optional `tmux` only for manual debugging |
| Orchestrator | **Custom Python service** built around **Temporal** workflows |
| Durable task queue/state | Temporal + **PostgreSQL**; use SQLite only for the MVP |
| Agent execution | Logical-agent records + bounded worker pools; subprocess/container isolation |
| Coding harness | **Aider** initially; evaluate OpenHands/SWE-agent as isolated workers |
| Research harness | Custom evidence pipeline using Playwright, scholarly APIs, GROBID/PyMuPDF |
| Local inference | **MLX/MLX-LM** on Apple Silicon; **llama.cpp** as compatibility fallback |
| Local model | One high-quality **14B–20B 4-bit** instruct/coding model, selected by current benchmarks |
| Embeddings | Small local embedding model; batch jobs, not permanently loaded initially |
| Memory | Markdown + Git + PostgreSQL/SQLite FTS; add `pgvector` only when justified |
| Browser | Playwright-controlled dedicated Chromium profile |
| Sandboxing | Dedicated macOS user + allowlisted workspaces + containers/VM for untrusted execution |
| Secrets | macOS Keychain or `1Password` CLI with scoped service credentials |
| Observability | Structured JSON logs + OpenTelemetry; Prometheus/Grafana later |
| Storage | Internal: OS/live DB/code; external: models, corpora, datasets, caches, archived worktrees |
| Concurrency | **1 large-model decode**, 2–4 tool workers, many queued logical agents |
| Cloud | Optional escalation only for hard planning, very large context, or critical verification |

---

# 1. Local inference

## Recommendation

Use **MLX-LM** as the first Apple-native backend and **llama.cpp** as the fallback/OpenAI-compatible server. Do not keep several substantial models resident on a 32 GB machine.

Because I cannot verify 2026 models, select the actual checkpoint using this gate:

1. Current permissive license.
2. Native MLX or GGUF quantization from a trustworthy publisher.
3. Strong current coding and tool-use evaluations.
4. Reliable structured-output/tool-call behavior.
5. Fits with **at least 7–9 GB free memory under real workloads**.
6. Test on your own repositories—not benchmark scores alone.

### Practical model envelope

A base M6 with 32 GB unified memory should target:

- **Primary model:** 14B–20B class, 4-bit.
- **Possible upper bound:** roughly 27B–32B at aggressive 4-bit quantization, but likely poor for sustained agent work once KV cache, macOS, browser, builds, and databases are included.
- **Small utility model:** 1.5B–7B, 4-bit, loaded on demand or retained only if measured benefit exceeds memory pressure.
- **Context:** default 16K–32K; increase only task-by-task.
- **Parallel decoding:** one primary decode stream. Continuous batching may support several requests, but simultaneous long generations usually reduce total useful throughput and increase memory pressure.

Approximate 4-bit weight sizes before runtime overhead:

- 7B: ~4–5 GB
- 14B: ~8–10 GB
- 20B: ~11–14 GB
- 32B: ~18–22 GB

Exact size depends on architecture and quantization metadata. KV cache can consume several additional gigabytes and grows with layers, width, context, batch size, and cache precision.

## Backend comparison

| Category | Best overall | Best for this Mac | Open source | Lightweight | Mature/stable | Cutting edge | Use |
|---|---|---|---|---|---|---|---|
| Inference | Hardware-dependent | MLX-LM | llama.cpp | llama.cpp | llama.cpp | MLX ecosystem | MLX-LM primary; llama.cpp fallback |
| Desktop convenience | Ollama | Ollama | Ollama | Ollama | Ollama | — | Optional development adapter, not core scheduler |
| High-throughput NVIDIA | vLLM | Not appropriate | vLLM | — | vLLM | vLLM | Future GPU server only |

**Why not Ollama as the core?** It is convenient, but the production architecture should control model lifecycle, context, queueing, health, and resource admission explicitly. It remains a good compatibility layer if its current Apple backend and API behavior test well.

## Bottlenecks

1. Memory bandwidth during token generation.
2. KV-cache growth and context prefill.
3. Browser/build/test processes competing for unified memory.
4. Thermal behavior during continuous workloads.
5. SSD model swapping and repeated cold loads.
6. Prompt construction and repository indexing—not just decoding.

Model swapping is worthwhile between phases, not between every request. Keep one primary model warm during active periods and unload it before memory-heavy builds or data analysis.

---

# 2. Agent runtimes and harnesses

## Decision

No single harness should own the whole workstation. Use:

- **Temporal** for durable workflows, retries, timers, cancellation, heartbeats, and restart recovery.
- A custom **policy-aware orchestrator** for task decomposition, routing, budgets, and approval rules.
- Existing specialist harnesses as replaceable workers.
- OpenTelemetry and immutable audit records around every tool call.

Temporal’s critical advantage is durable execution: an overnight job must survive a Python crash, service restart, or reboot without relying on an LLM transcript as its source of truth.

## Market comparison

| Runtime type | Best overall | Best for this hardware | Best OSS | Lightweight | Mature | Cutting-edge | Recommendation |
|---|---|---|---|---|---|---|---|
| Durable workflows | Temporal | Temporal | Temporal | SQLite job queue | Temporal | Agent-specific durable graphs | Temporal after MVP |
| Agent graph | LangGraph-style state graph | Custom small state machine | LangGraph | Plain Python | Plain Python + tests | Dynamic graph systems | Use only inside workflows if needed |
| Multi-agent dialogue | AutoGen/CrewAI class | Usually unnecessary | Several | Plain Python roles | Custom queue | Swarm frameworks | Do not make chat-based “swarms” the core |
| General computer agent | OpenHands class | Isolated worker | OpenHands | Shell worker | Terminal harness | Computer-use agents | Evaluate, do not grant host-wide trust |

Verify 2026 project activity, licenses, APIs, and local-model support before choosing among current descendants.

## State machine

Every task should have explicit states:

`QUEUED → PLANNING → READY → RUNNING → VERIFYING → REVIEWING → COMPLETED`

with alternatives:

`WAITING_APPROVAL`, `BLOCKED`, `RETRY_DELAY`, `FAILED`, `CANCELLED`, `BUDGET_EXHAUSTED`.

Store plans, tool results, artifacts, test evidence, commits, source records, and stop reasons independently of chat history.

---

# 3. Multi-agent architecture

## Key distinction

- **100 model instances:** 100 separately loaded or active inference processes—impossible and unnecessary here.
- **100 logical agents:** database records defining role, objective, permissions, memory scope, model policy, and current task.
- **Agent definitions:** reusable templates such as researcher, implementer, reviewer, tester.
- **Workers:** actual OS processes that lease queued tasks.
- **Inference slots:** scarce capacity controlled independently from worker count.

## Recommended topology

A hierarchical coordinator/worker architecture:

- One deterministic supervisor.
- One planner workflow when decomposition is needed.
- Project coordinators represented as state, not resident processes.
- Bounded pools:
  - 1 primary local-LLM generation slot.
  - 0–1 small-model slot.
  - 2 shell/test workers.
  - 1 browser worker.
  - 1 PDF/document extraction worker.
  - 1 indexing/embedding worker during idle windows.
- 100+ logical agents and thousands of queued tasks are acceptable.

Use parallelism for **tools**, not mostly for local LLM decoding. While the model plans task B, tests for task A can run, a browser can fetch sources, and a parser can process PDFs.

### Scheduling policy

Priority score should include:

- task priority and deadline;
- dependency readiness;
- expected value;
- estimated inference/tool cost;
- project fairness;
- memory requirement;
- approval status;
- retry count;
- whether execution conflicts with another task’s files.

Use per-project and global budgets for time, model tokens, disk, processes, and network requests.

---

# 4. Coding agents

## Recommendation

Start with **Aider** as the interactive/worker-level coding harness because it is comparatively lightweight, Git-aware, and model-provider agnostic. Wrap it rather than making it the supervisor.

Evaluate **OpenHands** or a current equivalent for longer autonomous issues, but run it in a container/VM or constrained workspace. Evaluate **SWE-agent**-style systems for benchmark-like issue resolution. Verify their 2026 status first.

| Criterion | Aider class | OpenHands class | SWE-agent class | Custom worker |
|---|---:|---:|---:|---:|
| Git-aware editing | Strong | Strong | Strong | Must build |
| Lightweight | Strong | Moderate/low | Moderate | Strong |
| Long autonomous loop | Moderate | Strong | Strong | Strong if engineered |
| Local model flexibility | Strong | Varies | Varies | Complete |
| Sandboxing | External | Often integrated | External/integrated | Complete control |
| General workstation scope | Worker only | Worker only | Issue-oriented | Best |
| Recommendation | **Initial coding worker** | Evaluate later | Specialized | Supervisor wrapper |

## Coding workflow

1. Create a task branch and isolated `git worktree`.
2. Inspect repository instructions and dependency files.
3. Build a repository map using language-native tools and targeted search.
4. Produce a bounded plan with acceptance tests.
5. Modify files using patch operations.
6. Run formatters, linters, type checks, unit tests, then targeted integration tests.
7. Ask a separate reviewer role to inspect the diff and evidence.
8. Fix findings.
9. Commit using a task ID.
10. Produce a completion report with changed files, tests, risks, and rollback.

Agents must not merge to protected branches. An autonomous commit is acceptable; a merge, force push, release, or deployment requires approval.

---

# 5. Research agents

## Architecture

Use an evidence-first pipeline rather than a general “research chatbot”:

1. **Question decomposition**
2. **Search-plan generation**
3. **Source discovery**
4. **URL/DOI canonicalization**
5. **Fetch and immutable snapshot**
6. **Document parsing**
7. **Claim extraction**
8. **Evidence linking**
9. **Contradiction search**
10. **Synthesis**
11. **Citation validation**
12. **Final report**

### Components

- Browser: Playwright with a dedicated profile.
- General web discovery: configurable search API, direct site search, and browser fallback.
- Literature: Crossref, OpenAlex, Semantic Scholar, arXiv, PubMed/Europe PMC where applicable.
- PDFs: GROBID for scholarly structure; PyMuPDF for general extraction; OCRmyPDF/Tesseract for scans.
- Metadata: DOI-first canonical records.
- Storage: content-addressed snapshots plus relational metadata.
- Citations: generated only from stored source records.

### Anti-hallucination rules

- The prose model cannot directly invent bibliography entries.
- Every factual claim receives a `claim_id`.
- Every citation resolves to a stored `source_id`.
- Evidence stores exact quotation or table cell, page/section, extraction method, and snapshot hash.
- Final citation rendering is deterministic from metadata.
- A validator checks that cited text exists, the page is valid, and the source supports the claim.
- Unsupported statements are removed or marked as inference.
- Conflicting sources are retained, not averaged away.
- Critical conclusions require either two independent sources or an explicit single-source caveat.

A vector store helps discovery; it does not establish truth.

---

# 6. Persistent memory

## Initial design

Use simple, inspectable memory:

- **Markdown + Git** for decisions, plans, runbooks, and project summaries.
- **SQLite** for MVP task state and FTS5 search.
- Move operational state to **PostgreSQL** when enabling Temporal and concurrent workers.
- Store raw artifacts in the filesystem using content hashes.
- Add `pgvector` only after keyword/metadata retrieval demonstrably fails.
- Do not begin with a separate vector database or knowledge graph.

### Memory types

| Memory | Storage |
|---|---|
| Working memory | Current workflow state and bounded prompt |
| Episodic | Task runs, events, tool calls, outcomes |
| Semantic | Curated project facts and summaries |
| Procedural | Versioned agent instructions, runbooks, policies |
| Evidence | Sources, snapshots, passages, claim links |
| Artifact | Files, reports, patches, test logs |
| Global | Minimal cross-project preferences and policies |

Agents should write memory through structured APIs, not append arbitrary “facts.” Important memory needs provenance, confidence, scope, author, timestamp, and supersession links.

---

# 7. Computer control

## Capability order

Prefer, in this order:

1. Filesystem API and patches.
2. Shell commands with structured capture.
3. Application/HTTP APIs.
4. Browser DOM automation.
5. GUI accessibility APIs.
6. Pixel-based mouse/keyboard control only as a last resort.

## Isolation model

- Create a dedicated non-admin macOS account, e.g. `agent`.
- No access to the personal home directory.
- Explicitly share only project roots.
- Use dedicated browser profiles with no personal cookies.
- Run untrusted builds in containers or a Linux VM.
- Keep secrets out of prompts and logs.
- Use separate, narrowly scoped Git and API credentials.
- Disable unrestricted `sudo`.

macOS containers run through a Linux VM and are not a perfect host sandbox. For hostile or unknown code, use a disposable VM; for trusted repositories, a dedicated user plus worktree and command policy is lighter.

### Approval matrix

**Fully autonomous**

- Read/write inside approved worktrees.
- Create branches and commits.
- Install project-local dependencies inside approved environments.
- Run tests and local services on non-public ports.
- Fetch public web content under rate limits.
- Write reports and issue drafts.
- Delete generated files inside disposable task workspaces.

**Require approval**

- Access personal home folders, Photos, Mail, Messages, browser profiles, contacts, cloud drives.
- Read or export secrets.
- Use `sudo`, change macOS security/privacy settings, install kernel/system extensions.
- Delete outside disposable workspaces.
- Force push, merge protected branches, publish packages, deploy, send messages externally.
- Spend money, purchase resources, use paid APIs beyond preset budgets.
- Financial, legal, identity, medical, or account changes.
- Bind services to public interfaces or alter firewall/VPN configuration.
- Execute downloaded unsigned binaries outside a sandbox.
- Actions that are irreversible or affect third parties.

---

# 8. Always-on operation

## Design

Use `launchd`, not shell loops, as the service manager.

Services:

- `ai.supervisor`
- `ai.temporal` or its container/VM wrapper
- `ai.postgres`
- `ai.inference`
- `ai.worker.code`
- `ai.worker.browser`
- `ai.worker.documents`
- `ai.dashboard`
- `ai.watchdog`

Each task lease has a heartbeat and expiry. On worker death, the task returns to the queue after checking whether the previous tool operation was idempotent.

### Reliability controls

- Persist state before and after every external action.
- Use idempotency keys.
- Cap retries and use exponential backoff.
- Write atomic files via temp file + rename.
- Maintain disk-space and memory-pressure circuit breakers.
- Stop launching new work during thermal, memory, or disk pressure.
- Save model-independent checkpoints.
- Restore services after reboot with `RunAtLoad`/`KeepAlive`.
- Keep the Mac awake while jobs are active using `caffeinate` or system power settings.
- Schedule maintenance and backup windows.
- Test reboot recovery deliberately.

A UPS is strongly recommended for real 24/7 operation.

---

# 9. Remote access

## Recommendation

Use **Tailscale** or an equivalent WireGuard-based private overlay. Do not expose SSH, inference, Temporal, PostgreSQL, or the dashboard to the public Internet.

### Remote functions

- Submit/cancel/pause tasks.
- View status, logs, artifacts, diffs, budgets, and model state.
- Approve or deny gated actions.
- Receive completion/failure/security notifications.
- Trigger emergency stop.

### Controls

- Tailscale ACLs and device approval.
- SSH keys only; disable passwords.
- WebAuthn/passkey or Tailscale identity for dashboard authentication.
- Dashboard bound to localhost or tailnet address only.
- Short-lived approval tokens bound to a specific action hash.
- Audit every remote command.
- Emergency stop:
  1. revoke new leases;
  2. cancel workflows;
  3. terminate worker process groups;
  4. stop inference;
  5. optionally disable agent network access.

Notifications can use ntfy, Matrix, or another end-to-end/private channel. Do not put secrets or source code in notification payloads.

---

# 10. Storage architecture

## Placement

### Internal 512 GB

Keep latency-sensitive and recovery-critical data here:

- macOS and applications.
- Supervisor/orchestrator source and Python environment.
- PostgreSQL/SQLite active database and WAL.
- Current task state and policy configuration.
- Active Git metadata where feasible.
- Small current logs.
- Credentials in Keychain, never external plaintext.
- At least 80–100 GB free for updates, swap, builds, and filesystem health.

### External 1 TB SSD

Use an APFS volume, encrypted, with a stable mount point:

- Model weights.
- Research corpus and PDFs.
- Datasets.
- Embedding/index files.
- Build caches.
- Archived worktrees.
- Container/VM images if supported reliably.
- Compressed historical logs.
- Download cache and temporary artifacts.

Do not put the only copy of the operational database on a removable external disk. Keep content hashes and backups so external artifacts can be reconstructed or detected as missing.

### Suggested budget

| Data | Budget |
|---|---:|
| Models | 150–300 GB |
| Repositories/worktrees | 100–200 GB |
| Papers/research corpus | 100–200 GB |
| Datasets | 200–350 GB |
| Caches/containers | 100–200 GB |
| Logs/artifacts | 50–100 GB |
| Free reserve | ≥15–20% |

The external SSD is capacity, not backup. Use another disk or encrypted remote backup for irreplaceable data.

---

# A. Recommended technology stack

| Layer | Recommended technology | Alternatives | Why |
|---|---|---|---|
| Private network | Tailscale | Headscale, plain WireGuard | Secure remote access without public ports |
| Service management | launchd | Docker restart policies, supervisord | Native macOS boot/restart integration |
| Durable orchestration | Temporal | Prefect, Dagster, custom queue | Strong durable workflow semantics |
| Initial task DB | SQLite | PostgreSQL | Minimal MVP |
| Production task DB | PostgreSQL | SQLite | Concurrency, durability, indexing |
| Supervisor | Custom Python/FastAPI service | Go/Rust | Fast integration and broad library support |
| Inference | MLX-LM | llama.cpp, Ollama | Apple-native path |
| Compatibility inference | llama.cpp server | Ollama | Broad model/quantization support |
| Coding worker | Aider | OpenHands, SWE-agent | Lightweight and Git-aware |
| Browser | Playwright + Chromium | Selenium | Reliable DOM automation and tracing |
| PDF extraction | GROBID + PyMuPDF | pdfminer, Docling-class tools | Structured papers plus general PDF handling |
| OCR | OCRmyPDF/Tesseract | Cloud OCR | Local and auditable |
| Literature metadata | Crossref/OpenAlex/S2/arXiv/PubMed | Search APIs | Canonical identifiers and metadata |
| Memory | Markdown/Git + PostgreSQL FTS | SQLite FTS | Simple and inspectable |
| Semantic retrieval | pgvector later | Qdrant, LanceDB | Avoid another service initially |
| Secrets | macOS Keychain / 1Password CLI | `sops` | Scoped credentials |
| Telemetry | JSON logs + OpenTelemetry | Prometheus/Grafana | Correlation and portability |
| Sandbox | Dedicated user + container/VM | macOS Sandbox profiles | Layered containment |
| Notifications | ntfy or Matrix | Email, Pushover | Simple remote alerts |
| Backups | APFS snapshots + encrypted backup | Restic/Borg | Recovery, not mere replication |

---

# B. Complete architecture diagram

```text
 Phone / Laptop
      |
 Tailscale ACL + device identity
      |
 SSH ───────────── Dashboard/API ───── Notifications
                         |
                 Policy / Approval Gate
                         |
                  Durable Supervisor
            (budgets, leases, kill switch)
                         |
              Temporal Workflow Engine
                         |
          PostgreSQL: tasks/events/memory
                         |
        +----------------+----------------+
        |                |                |
   Planner queue     Tool queues      Review queue
        |                |                |
        +---------- Model Router ----------+
                         |
             Admission control: 1 large slot
                  +------|------+
                  |             |
               MLX-LM       llama.cpp
                  |
      +-----------+------------+-------------+
      |           |            |             |
 Coding worker Browser worker PDF worker  Index worker
      |           |            |             |
 Worktree      Playwright   GROBID/OCR   FTS/embeddings
 shell/tests   isolated     source store
      |
 container/VM for untrusted execution

 Persistent stores:
 - Git + Markdown decisions/runbooks
 - PostgreSQL operational and evidence records
 - Content-addressed artifact filesystem
 - External SSD: models/corpus/datasets/caches
 - Internal SSD: live database/config/current state
```

---

# C. Hardware/resource plan

## RAM during normal autonomous work

| Consumer | Approximate allocation |
|---|---:|
| macOS and background services | 5–7 GB |
| Primary 14B–20B 4-bit model | 8–14 GB |
| KV cache/runtime/context | 2–5 GB |
| Supervisor, DB, workers | 1–2 GB |
| Browser | 1–3 GB |
| IDE/build/test processes | 2–6 GB |
| Filesystem cache/headroom | 4–6 GB |
| Total | ~23–43 GB depending on workload |

Because the worst case exceeds physical RAM, enforce admission control:

- Default to one browser context, one large decode, and two tool workers.
- Pause/unload inference before memory-heavy compiles or analytics.
- Avoid 64K+ context except for tightly controlled tasks.
- Reject new jobs if memory pressure is elevated.
- Treat sustained swap as a scheduling failure, not normal operation.

**Recommended steady state:** one 14B-class 4-bit model, 16K–32K context, one active generation, and enough headroom for development tools. A 20B model is acceptable only after workload tests.

---

# D. Agent architecture

An `agent_definition` contains:

```yaml
role: implementer
objective_template: "Implement an approved task"
tools: [read_repo, patch, shell, git]
workspace_scope: project_worktree
network: dependency_registries_only
model_policy: primary_local
max_wall_time: 90m
max_model_tokens: 60000
max_tool_calls: 200
approval_policy: coding_standard
memory_scope: project
```

An `agent_instance` is a database row, not a process. It becomes active only when a worker leases its task.

For 100+ agents:

- Store all agents and task DAGs durably.
- Materialize prompts only at execution.
- Keep histories summarized and artifact-linked.
- Use weighted fair scheduling by project.
- Permit at most one local large-model generation.
- Permit many waiting, blocked, or tool-running agents.
- Dynamically create agents from approved templates; a generated agent may narrow permissions but never broaden them.
- Use separate reviewer and verifier roles to reduce self-confirmation.

---

# E. Model strategy

Since current 2026 checkpoints cannot be verified here, the exact names must be selected through a bake-off.

| Function | Model class | Execution |
|---|---|---|
| Planning | Best local 14B–20B reasoning/instruct model | Local primary; optional cloud escalation |
| Coding | Best local coding-capable 14B–20B model | Local primary |
| Debugging | Same primary model with logs/tests | Local |
| Research extraction | Primary model or 7B utility model | Local |
| Summarization | 3B–7B instruct model | On demand |
| Classification/routing | Rules first; small model second | Local |
| Embeddings | Small current multilingual/text embedding model | Batched local |
| Final synthesis | Primary model; cloud only for high-stakes/huge context | Local by default |
| Verification | Deterministic tools plus separate model pass | Local |

### Bake-off

Use 30–50 representative tasks:

- repository edit with tests;
- multi-file refactor;
- bug diagnosis;
- tool-call JSON adherence;
- source-grounded report;
- citation validation;
- long-context retrieval;
- instruction-following under adversarial content.

Measure completion rate, test pass rate, unsupported claims, tool-call validity, wall time, peak memory, and human correction—not only tokens per second.

---

# F. 24/7 architecture

1. `launchd` starts DB, workflow service, inference, supervisor, workers, dashboard.
2. Supervisor restores task leases and checks incomplete side effects.
3. Temporal resumes timers/workflows.
4. Workers heartbeat and checkpoint every meaningful operation.
5. Watchdog monitors:
   - process health;
   - queue age;
   - memory pressure;
   - disk reserve;
   - external drive presence;
   - network failure;
   - repeated model errors.
6. Circuit breaker pauses work after repeated failures.
7. Nightly backup and database integrity checks run during an idle window.
8. Morning digest reports completed, blocked, failed, approvals needed, budget use, and changed repositories.

---

# G. Remote-control architecture

- Tailscale on Mac and phone.
- Tailnet-only dashboard/API.
- SSH with keys for emergency administration.
- Passkey/identity authentication.
- Signed approval request containing exact command, arguments, cwd, data scope, side effects, expiry, and hash.
- Push notifications with task ID and safe summary.
- One-tap pause and emergency stop.
- No inbound public port forwarding.
- No direct remote exposure of model server, DB, or workflow engine.

---

# H. Security architecture

## Trust zones

1. **Control zone:** supervisor, policy engine, DB, audit log.
2. **Trusted workspace:** owned repositories and documents.
3. **Untrusted execution:** downloaded repositories, arbitrary builds, unknown binaries.
4. **Sensitive personal zone:** inaccessible by default.
5. **Network zone:** deny by default per worker; allow destinations by task policy.

## Mandatory safeguards

- Dedicated non-admin account.
- Read/write allowlists.
- Per-task worktrees.
- No personal browser profile.
- Scoped credentials and rotation.
- Command normalization before policy evaluation.
- Block shell obfuscation and nested privilege escalation.
- Process group termination, wall-time limits, file-size limits, disk quotas where possible.
- Git protected-branch rules.
- Append-only or tamper-evid

## Reasoning trace (not shown to raters)

NONE

## Run notes

finish_reason=length. Check for truncation or refusal before scoring.
