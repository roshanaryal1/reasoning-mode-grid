---
run_id: gpt__fast__p1-v1__apicheck2
set: api_check
family: gpt
vendor: OpenAI
mode: fast
native_label: reasoning effort none
channel: api
model_requested: gpt-6-sol
model_returned: gpt-6-sol
params:
  _token_field: max_completion_tokens
  reasoning_effort: none
max_tokens: 6000
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 2
date_run: '2026-10-19T05:45:50+00:00'
run_by: roshanaryal
finish_reason: length
usage:
  input_tokens: 2501
  output_tokens: 6000
  reasoning_tokens: 0
latency_s: 76.1
harness_version: 0.1.0
---

## Final answer

**Model: OpenAI o3 (version not exposed) | Knowledge cutoff: not provided | Web browsing/tools: off**

**Evidence limit:** You specified 31 August 2026 as the research date, but I cannot browse or verify releases, benchmarks, prices, or hardware availability on that date. The runtime date available to me is **19 October 2026**, which conflicts with the date in your prompt. I will use **31 August 2026 as the requested design snapshot**, without claiming that any product or capability was verified as of then. In particular, I cannot verify the specifications or availability of a **base-M6 Mac mini**. The resource plan below is conditional on your stated **32 GB unified memory** and storage. This is a build design from existing knowledge and linked project documentation—not the current-market research you requested.

### Decisions at a glance

| Layer | Pick for this machine | Key qualification |
|---|---|---|
| Local inference | **Ollama first; benchmark llama.cpp/MLX before committing** | Choose on measured throughput, memory and tool reliability on the actual Mac. |
| Main local model | **One evaluated ~14B coding/instruct model at 4–5-bit quantization** | Select by tests, not a purported 2026 leaderboard. |
| Small model | **Evaluated ~3–8B instruct model** | Classification and cheap summaries; load only if useful. |
| Coding harness | **Aider** as a contained coding worker | Gate its command, file and Git permissions; local-model performance needs testing. |
| Orchestrator | **Small custom Python supervisor + SQLite task queue** | The durable task loop is the product; a chat UI is not. |
| Research | **Search/retrieval tools + local document extraction + evidence ledger** | Web search is an external network dependency even if inference is local. |
| Memory | **Markdown/artifacts + SQLite FTS5** | Add embeddings only after retrieval failures are demonstrated. |
| Isolation | **Dedicated macOS user + narrow workspaces; VM for higher-risk work** | A second user is a boundary, not a sandbox for arbitrary commands. |
| 24/7 service | **launchd, SQLite leases, restart/reconciliation loop** | Treat sleep, unmounts and partial work as normal failure cases. |
| Remote access | **Tailscale + SSH; approvals through a private interface** | Do not expose the inference server or dashboard publicly. |

## 1. Local inference

On a 32 GB unified-memory Mac, the governing quantity is **peak resident memory during an actual agent run**, not quantized weight size. macOS, the browser, terminals, repositories, KV cache, model server, and the coding worker all compete for the same pool. Start with **one 4–5-bit ~14B model**, a **moderate context target of 8K–16K**, and retrieval of relevant files instead of indiscriminately filling context. Run a ~3–8B model for cheap tasks only if the measured benefit exceeds loading and memory pressure.

The shortlist to test on the *actual hardware* is a current, permissively usable coding/instruct model in the **Qwen-Coder class**, plus a smaller instruct model. I cannot responsibly name an exact August 2026 release or claim which is best. Require the candidate to pass your own **tool-call, edit, test-repair, long-context and citation-grounding** evaluations. A model that is larger but slower or unreliable at tool calls can complete less useful work overnight.

- **Best overall:** cannot substantiate without current independent evaluations.
- **Best for this hardware:** the *best measured* ~14B 4–5-bit candidate, initially via Ollama.
- **Best open-source/open-weight and lightweight:** compare licenses and tested ~7B-class candidates; “open weights” does not necessarily mean open-source.
- **Most mature/stable inference choice:** llama.cpp is the low-level baseline; Ollama provides a simpler local server and model lifecycle.
- **Cutting-edge choice:** test MLX-based inference where the chosen model and agent client are supported.
- **Actually use:** Ollama initially, **one large inference slot**, then compare llama.cpp and MLX on the same prompts, context and quantization before changing backends.

Do not promise a long advertised context window under this memory limit. Measure prompt-processing time, tokens/second, peak memory, cold-load time, and **successful tasks/hour**. Confirm Metal acceleration and model-format support with the installed versions.

## 2. Agent runtimes and harnesses

No single harness should be presumed to provide durable overnight orchestration, safe whole-computer permissions, excellent coding, trustworthy research citations and remote operations. Separate **workflow control** from **task execution**.

For this build, a custom, intentionally small supervisor owns task state, leases, budgets, approvals and audit events. It invokes replaceable workers through subprocesses or APIs. Aider is a plausible first coding worker; OpenHands and SWE-agent are comparison candidates for more autonomous coding workflows, but their dependency, sandbox and local-model requirements need a real-machine trial. LangGraph is worth evaluating if workflow branching and resumability outgrow the small supervisor; do not install a large orchestration stack merely to represent a queue.

- **Best overall/cutting-edge:** unverified for the requested date; evaluate OpenHands, SWE-agent and workflow runtimes against the same tasks.
- **Best for this hardware / lightweight:** small Python supervisor with SQLite; one active coding worker.
- **Best mature component:** SQLite for durable state, launchd for process supervision.
- **Best open-source approach:** compose an open coding harness with your own inspectable controller.
- **Actually use:** **custom durable controller + Aider worker**, behind a worker interface so either can be replaced.

Define the stop conditions *before* enabling unattended execution: accepted test/review result, deadline, retry cap, resource cap, approval request, or explicit cancellation. “Continue until complete” without these conditions is a runaway-job specification.

## 3. Multi-agent architecture

**100 agents** should mean **100 durable roles/tasks or agent instances in records**, not 100 loaded models. An agent definition specifies instructions, allowed tools, workspace, model tier and objective. A task record adds input, state, budget and artifacts. Workers execute a small number of tasks at once.

Use a **coordinator/worker queue**, not an unconstrained swarm:

1. Coordinator decomposes a goal into bounded tasks with explicit dependencies.
2. Scheduler places runnable tasks on a durable queue.
3. **One large-model worker** performs reasoning, coding or synthesis.
4. At most **one small-model worker**, enabled only if memory tests permit, handles classification or extraction.
5. Non-LLM tools—PDF extraction, tests, indexing and downloads—run concurrently within separate CPU, memory and network limits.
6. Verifier checks outputs against acceptance criteria; failure produces a bounded follow-up task.
7. Every new dynamic “agent” is a new task plus a versioned role definition, **not** a new daemon or model instance.

Prefer sequential large-model inference to oversubscription. Parallelize downloads, tests and document extraction where useful; use Git worktrees for genuinely independent coding tasks, but do not let two workers edit the same checkout.

## 4. Coding agents

Compare Aider, OpenHands and SWE-agent on **your own repositories**, not showcase demos. Aider offers a relatively lightweight terminal/Git workflow. OpenHands is a candidate when its broader autonomous execution and isolation justify more infrastructure. SWE-agent is a candidate for issue-to-patch evaluation. None should receive unrestricted access to all projects by default.

**Actual pick:** start with Aider as the coding executor, invoked in a **task-specific worktree**. The supervisor, not the worker, chooses the repository, branch, allowed commands and stopping policy. A coding cycle should be:

`inspect → plan → edit → run scoped tests → inspect diff → retry within budget → review → commit to task branch → report`

Default to **no automatic merge to protected branches**, no force push and no production deployment. Capture command transcripts, test outputs, final diff and the model’s completion claim separately. A passing self-report is not verification.

## 5. Research agents

A capable local research system still needs **external source access** when researching the current web. Use a search-provider adapter, publisher/official pages, academic metadata sources such as OpenAlex and Crossref where suitable, and document downloaders. For files, start with PyMuPDF or equivalent PDF text extraction; retain the original PDF and note OCR failures. Browser automation, for example Playwright, is a fallback for sources that require it—not the default method for every page.

Make citation correctness a **data constraint**, not a prompt request. Store an evidence record containing:

`claim_id, source_url/DOI, title, author/publisher, retrieval_time, document_hash, exact_quote_or_extracted_span, page/section, support_or_contradiction, confidence_notes`.

The report generator may cite **only registered evidence IDs**. A separate verifier reopens cited spans, checks whether the text supports the claim, flags conflicts and labels inaccessible or unverified material. Keep “source says X,” “inference from X,” and “not verified” distinct. Search results and model recollection are **discovery leads**, not citations. This workflow can reduce hallucinated citations; it cannot guarantee that a source is true.

**Actually use:** retrieval adapters + saved source snapshots + SQLite evidence ledger + a verifier pass. Add an academic-specific framework only if your literature workload proves it necessary.

## 6. Persistent memory

Start with two layers:

- **Files:** versionable `PROJECT.md`, architecture decisions, reports, experiment manifests, diffs and original source documents.
- **SQLite:** tasks, leases, agent definitions, provenance, approvals, event log, artifact pointers and **FTS5** full-text search.

Separate **project memory** from **global operating preferences**. Store episodic records (“what was tried, with result and timestamp”) separately from promoted facts/decisions (“what should future tasks rely on”). Promotion requires a source or a verified local artifact. Expire or supersede stale entries; memory must not silently become authority.

**Actually use:** files + SQLite/FTS5. Add embeddings if lexical search misses a measured fraction of relevant material. A dedicated vector database, knowledge graph, PostgreSQL cluster or Redis queue is unnecessary initially.

## 7. Computer control and security boundaries

Give the worker **broad capability inside authorized workspaces**, not broad visibility into your personal home directory. Create a dedicated macOS account, `aiworker`, without administrator rights. Keep its home free of your browser profiles, SSH keys, password manager, financial files and personal cloud-sync folders. Give it access to selected project directories through explicit copying, worktrees or narrow permissions. Store credentials outside its accessible workspace; grant narrowly scoped, revocable tokens only to tasks that need them.

Use increasing isolation for increasing risk:

1. **Low risk:** read and edit an authorized project worktree; run allowlisted tests.
2. **Moderate risk:** install dependencies, launch a browser, fetch external content—restricted workspace, network policy and resource budget.
3. **High risk:** execute unknown code from the web or third-party repositories—prefer a disposable VM with no personal mounts or secrets.
4. **Never unattended by default:** read personal secrets; change security settings; access finance; make purchases; delete outside a scratch workspace; force-push; merge/deploy to production; grant itself permissions.

A dedicated user alone does **not** stop malicious code from accessing everything that user can read. Containers on macOS also do not erase the need to reason about mounts, network and credentials.

## 8. Always-on operation

Use **launchd to start and restart a small controller**, and SQLite to make *work* recoverable. On boot or restart, the controller checks for stale leases, inspects worktree/process state, reconciles partial results and either safely retries or marks a task for review. Make every task **idempotent where possible** and give side-effecting operations explicit checkpoints.

Provide task states such as `queued`, `leased`, `running`, `needs_approval`, `verifying`, `succeeded`, `failed`, `cancelled`. Record a heartbeat, attempt number, lease expiry and deadline. A watchdog may restart a crashed controller, but must not interpret “process restarted” as “side effect did not happen.”

Configure the Mac to remain awake on AC power and restart after power loss where supported; verify the relevant macOS settings on the actual machine. An external-SSD disconnect must **pause affected tasks**, not recreate empty directories or silently start a new database. Keep compact rotating logs and a separate audit trail.

## 9. Remote access

**Actual pick:** Tailscale between your phone/laptop and Mac, with SSH for administration and a small private status/approval interface later. Bind the inference API and task dashboard to localhost or the private interface; **do not open public router ports**. Use device authentication, MFA on the network account, SSH keys, and authorization checks inside the application. Network membership is not equivalent to approval for destructive actions.

Phone controls should be deliberately small: submit goal, inspect status/artifacts, approve or deny a named action, pause queue, cancel task, **emergency stop**. Notifications can contain task IDs and non-sensitive summaries; keep code, documents and secrets out of push-message bodies.

## 10. Storage architecture

| Location | Put here | Reason |
|---|---|---|
| **512 GB internal** | macOS, applications, supervisor code, SQLite task DB and WAL, active logs, active small workspaces, essential recovery files | Controller should boot and recover even if external storage is absent. |
| **1 TB external** | Large model files, repository mirrors/worktrees as appropriate, PDFs, datasets, experiment outputs, caches, archived logs | High-volume/recreatable or bulky content. |
| **Separate backup destination** | Encrypted backups of SQLite, decisions, reports, important repositories and evidence metadata | The external working SSD is **not** a backup. |

Do not put the sole live queue database on a detachable drive. Check external volume identity and mount health before any task writes to it. Budget free space for model downloads and temporary quantized files; avoid filling the internal SSD with inference caches.

# Required deliverables

## A. Recommended technology stack

The categories below identify an *operational choice*, not verified 2026 market winners.

| Layer | Recommended technology | Alternatives | Why |
|---|---|---|---|
| Interface | CLI first; private status UI later | Chat front end, mobile web app | Queue and approvals matter more than chat. |
| Supervisor | Python service under launchd | Larger workflow platform | Small, auditable, restartable. |
| Queue/state | SQLite WAL | PostgreSQL, Redis | Durable and sufficient for one machine. |
| Coding agent | Aider worker in Git worktree | OpenHands, SWE-agent | Lightweight starting point; replace if trials show better results. |
| Research | Search adapters, OpenAlex/Crossref, PyMuPDF, evidence ledger | Research-agent frameworks | Explicit provenance and citation verification. |
| Browser | Playwright when needed | GUI computer-use | Less fragile than screen-coordinate control. |
| Local inference | Ollama initially | llama.cpp, MLX-based serving | Easy first deployment; benchmark alternatives. |
| Memory | Markdown + SQLite FTS5 | Embeddings/vector DB, graph DB | Minimal infrastructure and inspectable records. |
| Isolation | Dedicated user; disposable VM for untrusted execution | Containers with restricted mounts | Match boundary to risk. |
| Remote | Tailscale + SSH | Other private VPN/overlay | Avoid public service exposure. |
| Observability | Structured JSON logs + SQLite events | Full telemetry stack | Enough to diagnose one workstation. |

For **best overall**, **cutting-edge**, and exact **best open-source** rankings across these categories, I cannot provide an evidence-based winner without the requested browsing and benchmark verification. The table states what I would **actually pilot on this hardware**.

## B. Complete architecture diagram

```text
Phone/laptop -- private Tailscale network --> SSH / private status + approval UI
                                                   |
                                           task submission / kill switch
                                                   |
                                        launchd --> Python supervisor
                                                   |
                                   SQLite queue, leases, audit, budgets
                                      /            |              \
                              coordinator     approval gate      verifier
                                  |                |                  |
                           role/task records -----+------------ evidence ledger
                                  |
                       bounded worker scheduler
                        /          |           \
                coding worker  research worker  non-LLM jobs
                Aider/worktree search/PDF/browser tests/index/download
                        \          |           /
                         model router + inference semaphore
                                      |
                            Ollama on localhost
                         one ~14B slot; optional small slot
                                      |
                 files/artifacts + SQLite FTS5 + external SSD corpus

Untrusted-code path: staged input --> disposable VM --> inspected output
```

## C. Hardware/resource plan

These are **planning envelopes, not measured M6 benchmarks**.

| Consumer | Approximate allowance |
|---|---:|
| macOS and ordinary background services | 5–8 GB |
| ~14B 4–5-bit weights | roughly 8–11 GB, format-dependent |
| KV cache/runtime overhead at moderate context | roughly 2–6+ GB, highly variable |
| Supervisor, SQLite, tools, terminal and coding harness | 1–3 GB |
| Browser, tests, build tools | 2–6+ GB |
| Headroom/filesystem cache | aim for **at least 3–5 GB** |

These ranges can overlap or exceed 32 GB under load. Set a **memory-pressure guard**: when macOS begins sustained swapping, stop the small-model worker, reduce context or test parallelism, and then reconsider the main model size. Begin with **one large worker and zero concurrent small workers**; enable one small worker only after a full coding-plus-browser workload remains stable. Repeated model swapping is rarely worthwhile for tightly interleaved tasks; batch small tasks if cold-load cost is significant.

Storage policy: reserve meaningful free capacity on both drives, keep the live DB internal, store large weights/corpus external, and back up irreplaceable state elsewhere. Measure actual model weight, cache and worktree sizes before setting fixed quotas.

## D. Agent architecture: 100+ logical agents

Represent logical agents in rows, for example:

`agent_id, role_version, tool_policy, model_tier, workspace_scope, parent_task, objective, status, budget`.

The scheduler can retain **100+ such records** while allowing **one large-model inference and, conditionally, one small-model inference** at a time. Run cheap deterministic jobs in a separately limited pool. Require each delegation to include an artifact contract, acceptance criteria, deadline and maximum children; otherwise recursive delegation can explode the queue.

## E. Model strategy

Because I cannot verify August 2026 model releases or evaluate the M6, the following are **exact selection tiers and runtime roles**, not falsely precise model names:

| Task | Initial model assignment | Escalation |
|---|---|---|
| Planning/delegation | Evaluated ~14B coding/instruct, 4–5-bit | Human approval for high-impact plans; optional cloud frontier model only by explicit choice |
| Coding/debugging/review | Same ~14B; repository retrieval + tools | Reattempt with different prompt/context; cloud only for demonstrably hard cases |
| Research source triage | ~3–8B if stable, otherwise main model | Main model for ambiguous evidence |
| Extraction/classification | Deterministic parser first; small model if needed | Main model |
| Summarization | Small model for source-local summaries | Main model for cross-source synthesis |
| Final synthesis | Main model using registered evidence only | Optional manually approved cloud pass |

**Acceptance gate for choosing actual model IDs:** record license, quantization, context, memory peak and local results on at least several representative repo fixes, tool-use tasks and sourced reports. Do not route by model branding alone.

## F. 24/7 architecture

`launchd → supervisor restart → DB integrity/mount check → recover expired leases → reconcile worktree and command results → resume bounded tasks → periodic checkpoint and backup`.

Add a hard daily compute/time budget, per-task attempt limit, subprocess timeout, disk-free threshold, memory-pressure pause and alert on repeated crash loops. Do not automatically retry a command with external side effects unless its result can be established.

## G. Remote-control architecture

Tailscale provides the private path; SSH provides break-glass access; a minimal authenticated UI presents status and **action-specific** approvals. Store approvals with task ID, exact proposed command/action, affected paths/resources, requester, timestamp and expiry. A phone “stop” should first pause scheduling and terminate workers, then leave the supervisor and logs running for inspection.

## H. Security architecture

**Autonomous:** read authorized repositories and public sources; create task branches/worktrees; edit within those worktrees; run allowlisted local tests; write reports; make commits on task branches.

**Approval required:** network publishing; opening new directories; running newly downloaded executables outside a disposable VM; installing system software; reading credential-bearing locations; sending private documents to cloud models; merging or pushing protected branches; deleting non-scratch data; payments, financial actions, security-setting changes and production deployment.

Enforce this in the **tool gateway and OS access controls**, not merely in an agent prompt. Keep command/output audit records, restrict mounts and tokens, and maintain a physical/remote kill procedure. Treat prompt injection in web pages and repository files as untrusted instructions.

## I. Exact installation plan

The commands below are a **starting scaffold**, not a verified August 2026 installer. Check current official installation instructions, macOS compatibility, package signatures and licenses before execution. Do **not** run third-party install scripts fetched directly into a shell.

**Phase 1 — Minimal working system**

1. Create a non-admin `aiworker` account using macOS Users & Groups. Grant only selected project access.
2. Install Xcode Command Line Tools and a package manager from their official instructions; verify architecture and versions.
3. Under `aiworker`, create the layout:

```sh
mkdir -p ~/ai-lab/{app,config,state,logs,artifacts,worktrees}
mkdir -p /Volumes/AIData/{models,corpus,repos,datasets,experiments,cache}
```

4. Install Python in an isolated environment, SQLite support and your chosen inference server according to their official documentation. Bind inference to `127.0.0.1`. Create one SQLite DB at `~/ai-lab/state/lab.sqlite3` with `tasks`, `events`, `approvals`, `artifacts`, `agents` and `evidence` tables.
5. Implement one `enqueue → lease → execute → verify → complete/fail` loop. **Test:** kill the worker mid-task and confirm recovery without duplicating a file-changing action. **Rollback:** stop the controller; retain DB and artifacts.

**Phase 2 — Autonomous coding**

Install Aider in its own Python environment using the then-current official instructions. Connect it to the local inference endpoint, initially with **one small test repository**. The supervisor creates a Git worktree and task branch and invokes the worker with scoped instructions. **Test:** a failing-test-to-passing-test task, plus a deliberately impossible task that must stop. **Failure/rollback:** stop worker, inspect diff, remove only its worktree; preserve task artifacts.

**Phase 3 — Research agents**

Add search adapters, document downloading, PyMuPDF-style extraction and the evidence table. **Test:** deliberately seed a false citation and require the verifier to reject it. **Rollback:** disable network research and keep local documents/search index.

**Phase 4 — Persistent memory**

Add SQLite FTS5 over approved summaries and artifact metadata; maintain project-level Markdown decisions. **Test:** retrieve a superseded decision and confirm the latest state is distinguishable. **Rollback:** rebuild the FTS index from files and DB records.

**Phase 5 — Multi-agent orchestration**

Add role definitions, dependency edges, child-task caps and inference semaphores. **Test:** enqueue 100 logical tasks, verify that only the configured number execute concurrently and that cancellations propagate. **Rollback:** reduce worker count to one; queue remains intact.

**Phase 6 — 24/7 operation**

Create a `launchd` job for the **controller**, not one job per agent. A per-user LaunchAgent is appropriate if the worker must run in that login context; choose a system-managed service strategy only after testing boot-before-login requirements and permissions. Configure restart, mount checks, backups and monitoring. **Test:** reboot, worker crash, external-drive disconnect and low-disk condition. **Rollback:** unload/disable the job and run the controller manually.

**Phase 7 — Remote access**

Install Tailscale from official instructions, enable SSH only as needed, then deploy a status/approval interface on the private network. **Test:** deny a proposed protected action from the phone, then invoke emergency stop. **Rollback:** disable the UI and SSH; local CLI still works.

**Phase 8 — Optimization**

Benchmark the chosen 14B and small-model candidates under a representative coding/research mix. Trial llama.cpp or MLX using identical tasks. Change one variable at a time and retain a configuration you can restore. **Test:** completed verified tasks per hour, memory pressure, citation error rate and recovery success—not tokens/second alone.

A starter configuration should contain enforceable values such as `max_large_inferences: 1`, `max_small_inferences: 0`, `max_child_tasks_per_task`, `max_attempts`, `task_deadline`, `allowed_workspace_roots`, `approval_rules`, `external_volume_id` and `min_free_bytes`. The worker must not be able to edit its own policy or mark its own verification as passed.

## J. What **not** to install initially

- **A fleet of 100 model servers**: logical concurrency is not inference concurrency.
- **Kubernetes, Redis, a graph DB and a standalone vector DB**: operational cost without a demonstrated single-Mac need.
- **Multiple overlapping agent frameworks**: makes state and permissions ambiguous.
- **Always-on GUI computer-use** as the default: prefer filesystem, CLI, APIs and browser DOM automation.
- **A huge model solely because it loads**, or a maximal context solely because it is advertised.
- **Publicly exposed Ollama, dashboards or SSH ports**.
- **An unrestricted agent running as your personal/admin user**.
- **A backup that exists only on the working external SSD**.

## K. Future upgrade path

At **64 GB**, benchmark a stronger single model and a genuinely concurrent small worker before increasing agent count. At **96/128+ GB**, consider a larger high-quality model, longer *measured* context, separate model pools and more independent worktrees; preserve queue and permission boundaries. With a **dedicated GPU/server**, move inference behind a private authenticated API while keeping the Mac’s supervisor, approval ledger and local sensitive-data tools separate. Do not automatically move documents or credentials to that server. Scale workers only when task throughput—not nominal model capacity—improves.

### Sources

These are **primary project/documentation entry points**, provided for implementation and independent verification. I **did not access them during this answer** and therefore do **not** cite them as proof of their August 2026 state or of comparative superiority.

- **[Primary]** Apple `launchd` documentation: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html
- **[Primary]** Apple Virtualization framework: https://developer.apple.com/documentation/virtualization
- **[Primary]** SQLite WAL: https://www.sqlite.org/wal.html ; FTS5: https://www.sqlite.org/fts5.html
- **[Primary]** Ollama: https://github.com/ollama/ollama
- **[Primary]** llama.cpp: https://github.com/ggml-org/llama.cpp
- **[Primary]** Apple MLX: https://github.com/ml-explore/mlx
- **[Primary]** Aider: https://aider.chat/docs/
- **[Primary]** OpenHands: https://github.com/All-Hands-AI/OpenHands
- **[Primary]** SWE-agent: https://github.com/SWE-agent/SWE-agent
- **[Primary]** LangGraph: https://github.com/langchain-ai/langgraph
- **[Primary]** Playwright: https://playwright.dev/docs/intro

## Reasoning trace (not shown to raters)

NONE

## Run notes

finish_reason=length. Check for truncation or refusal before scoring.
