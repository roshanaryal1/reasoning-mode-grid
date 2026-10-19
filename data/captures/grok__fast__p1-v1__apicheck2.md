---
run_id: grok__fast__p1-v1__apicheck2
set: api_check
family: grok
vendor: xAI
mode: fast
native_label: reasoning effort low (lowest available, cannot be disabled)
channel: api
model_requested: grok-4.7
model_returned: grok-4.7
params:
  _stream: true
  reasoning_effort: low
max_tokens: 64000
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 2
date_run: '2026-10-19T06:11:22+00:00'
run_by: roshanaryal
finish_reason: stop
usage:
  input_tokens: 3746
  output_tokens: 6591
  reasoning_tokens: 1648
latency_s: 137.08
harness_version: 0.1.0
---

## Final answer

**Grok 4 (xAI), knowledge cutoff earlier than 31 August 2026, web browsing/tools: off.** This answer was not verified against live docs, release notes, or benchmarks dated 31 August 2026. Treat every version, M6-specific number, and “current winner” as a hypothesis to re-check before you install. I will not invent citations or tok/s figures.

**Decisions at a glance**

| Layer | Use | Not use |
|---|---|---|
| Inference | One Apple-native server (MLX if it is the mature Metal path on your OS; llama.cpp/Metal as fallback). One resident coding/reasoning quant that fits with KV cache. Optional tiny router only if it stays under ~3 GB. | vLLM, multi-70B, always-hot model zoo, Ollama+LM Studio+MLX together |
| Orchestrator | Small Python supervisor + SQLite queue + launchd. Agents are rows and role files, not processes with their own models. | CrewAI/AutoGen/swarm frameworks as the OS |
| Coding | One local-model CLI/harness with repo, tests, and git worktrees, called by the supervisor | A second overlapping IDE agent always running |
| Research | Fetch → store PDF/HTML → extract text → cite only from stored files → separate verifier pass | “Search and write the report in one prompt” |
| Memory | Git + Markdown + SQLite first. Embeddings later, same SQLite if possible | Neo4j, Milvus, a vector product on day one |
| Isolation | Dedicated macOS user, workspace jail, no Keychain, approval gate for push/delete/secrets | “Computer use” of your personal GUI session |
| Remote | Tailscale (or equivalent tailnet) + SSH + read-only status. No public ports | Exposing an agent API to the internet |
| Always-on | `launchd` KeepAlive, `pmset` sleep off on AC, queue is the source of truth | A chatbot window left open |

---

### 1. Local inference

On 32 GB unified memory the bottleneck is **weights + KV cache + macOS**, not parameter count. Useful work per hour favors a model you can keep resident at a context long enough for a repo slice or a paper, with stable tool-calling, over a larger model you must swap or that OOMs mid-edit.

**Budget (order of magnitude, not a benchmark):** macOS and background services often want roughly 5–8 GB; a browser or Xcode session can add several more. Plan **~16–20 GB for one inference process** (weights + KV), and keep **≥6 GB free** so the machine does not compress itself to death. A 30B-class 4-bit model can fit; a 70B-class model usually does not fit *with* a useful context, OS, and tools. Long context is often more valuable than extra parameters: KV cache grows with context length and batch size. Prefer **one sequence at a time** on the large model.

**What to run locally (classes, re-benchmark on your box):**
- **Primary worker:** best available open coding/agent model in the ~14–32B range, 4-bit or the Apple-native 4-bit/MLX quant that scores highest on *your* tool-use and edit tests, context capped around 16k–32k unless KV measurements show headroom.
- **Small worker:** 3–8B instruct model for classify, route, summarize, and “is this citation in the file?” checks. Load it only when the large model is idle, unless a memory reading shows both fit.
- **Do not default to the largest model that `fits`.** Swap cost on unified memory is real (bandwidth + reload). One stable model beats three specialists if specialists thrash.

**Engines:** Prefer the stack with first-class **Metal / unified-memory** support and a simple HTTP or CLI API. As of the last widely documented period, that meant **MLX** for Apple-native graphs and **llama.cpp (Metal)** for GGUF breadth. Wrappers (Ollama, LM Studio) are fine for *trying* models, then pin one server for 24/7 so you are not debugging three loaders. CUDA-first servers (vLLM and similar) are the wrong primary on a Mac mini.

**Concurrency:** One large-model worker. A second concurrent large inference is usually a net loss (both slow, KV doubles, jetsam risk). Parallelize downloads, git, tests, and PDF text extraction without a second LLM.

**M6:** I cannot confirm M6 specs, Neural Engine claims, or MLX support from this session. Assume the same design rules as prior Apple Silicon Mac minis: unified memory, Metal, no discrete VRAM, bandwidth-bound generation. Re-read Apple’s chip brief and the MLX/llama.cpp release notes before buying quants.

### 2. Agent runtimes / harnesses

You need a **queue-driven supervisor**, not a chat product.

A harness is worth adopting only if it already does: filesystem + shell, git, test runs, session resume, and **a local OpenAI-compatible or CLI model backend**. A framework is not worth adopting if its value is “100 agents talk to each other.”

**Recommended shape:** you own the supervisor (a few hundred to a couple thousand lines). It dequeues a task, builds a role prompt from a file, calls one coding harness or a research script, records stdout/exit/diff, and writes the next task. That is the autonomous loop: plan → delegate → execute → observe → verify → correct → document → continue.

Use an existing coding harness as a **subprocess**, not as the operating system. Graph frameworks (LangGraph-class) are optional later for research state machines. Multi-agent chat frameworks tend to multiply tokens and hide failures.

**Multiple complementary systems, narrowly:** one inference server, one supervisor, one coding harness, one research pipeline. Not three orchestrators.

### 3. Multi-agent architecture

| Idea | What it actually is | On 32 GB |
|---|---|---|
| 100 model instances | 100 weight copies or 100 KV caches | Impossible / useless |
| 100 logical agents | 100 role definitions + task rows | Correct |
| Worker pool | N processes allowed to call the LLM | N = 1 large, maybe 1 small when large is unloaded |
| Dynamic subagents | Supervisor inserts child tasks with a role id | Correct |
| Swarm | Peers message peers | High chatter, low throughput |
| Coordinator/worker | One planner writes tasks; workers execute | Correct |

**Design:** hierarchical, queue-backed, mostly sequential LLM steps.

- `agents/*.md` or YAML: role, tools allowed, model class (`large`/`small`), max minutes, max turns, approval policy.
- `tasks` table: id, parent_id, role, status, budget, workspace path.
- Supervisor never starts 100 LLM processes. It starts **one worker** that may run many roles over a night.
- Parallelism only for non-LLM work (fetch, unpack, `pytest` on CPU, hash files).
- A planner task (large model, short) may enqueue 20 child tasks. Children run one after another. That is how you get “100 agents” and still finish work.

Dynamic creation: if a task says “need a verifier,” the supervisor inserts a row with `role=citation_verifier`. No human config step. The role file must already exist or be generated into a sandbox and reviewed if it requests new tools.

### 4. Coding agents

Judge harnesses on: worktrees, patch application, test command, failure loop with a turn budget, local model support, and whether it writes outside the repo. Brand popularity is irrelevant.

**For this machine:** one harness that shells out and edits files under a worktree, driven by your queue, model pointed at localhost. Capabilities you should require before trusting overnight runs:
- Operates in `git worktree` so `main` is untouched.
- Runs the project’s own test command and stops on a configured failure count.
- Emits a diff and a short log the supervisor stores.
- Refuses network except via your proxy if you enable one.
- Does not hold your GitHub token; push is a separate approved task.

I will not name a single August 2026 “best” coding agent without a fresh comparison. Shortlist by those requirements (historically: tools in the Aider / OpenHands / Goose / SWE-agent / Claude-Code-class family). Pick the one whose **local-model** path is documented and whose last release is recent, then lock the version. Do not run two of them on the same repo.

### 5. Research agents

Hallucinated citations are a **process** failure, not a model-size failure.

**Pipeline:**
1. Search (local index first, then web/APIs you allow).
2. Download PDF/HTML into `research/sources/<id>/` with URL, retrieval time, and hash.
3. Extract text locally (PDF text layer; OCR only if needed).
4. Claims table: claim, supporting file path, quote span, extractor model.
5. Verifier role (can be the small model): reject any citation whose file is missing or whose quote does not match.
6. Synthesis role may only cite ids present in the claims table.
7. Report written to Markdown with a bibliography generated from the table, not from model memory.

Academic discovery: use publisher/open APIs and local PDFs you actually downloaded. Do not let the model “recall” DOIs. Contradiction detection is a second pass over the claims table, not a vibe in the final essay.

Browser use is optional and expensive. Prefer HTTP fetch and PDF tools. GUI browsing overnight is a stability and security liability.

### 6. Persistent memory

**Initial (enough for a real lab):**
- **Git** for code and for research reports.
- **Markdown** under `memory/` for decisions, ADRs, experiment notes (human-readable, diffable).
- **SQLite** for tasks, runs, tool logs, claims, and “what happened last night.”
- Project memory vs global memory = two directories or a `project_id` column. Start global-thin, project-fat.

**Later, only if search fails:**
- Embeddings in **sqlite-vec** (or equivalent in-process extension), not a separate database server.
- A tiny knowledge graph only if you have repeated multi-hop questions SQLite cannot answer. Most personal labs never need Neo4j.

Episodic memory = run logs. Semantic memory = curated Markdown the supervisor is allowed to retrieve by path and keyword before it embeds anything. Avoid “the vector DB is the memory.” It drifts and cannot be reviewed in git.

### 7. Computer control

**Maximum practical autonomy without personal-data exposure:**

- Dedicated user `agent` (no admin). Your human user stays logged out of that session’s secrets.
- Workspace root: e.g. `/Users/agent/work` and/or a folder on the external SSD. No access to your home, Mail, Messages, Photos, Keychain, browsers profiles, or `~/.ssh` of the human user.
- Shell: allowlisted commands in the workspace (`git`, language toolchains, `pytest`, `python`, `rg`). Deny `sudo`, `diskutil`, `launchctl` bootout of other users, `rm -rf /`, reading `/Users/<you>`.
- Git: commit inside worktrees is autonomous; **push, force-push, and tag** require approval.
- Secrets: a separate directory the agent cannot read. Inject short-lived tokens per approved task, or use a proxy that attaches credentials so the model never sees them.
- Network: default deny outbound except an allowlist (package mirrors you choose, research domains, model is already local). No inbound except tailnet SSH.
- GUI/computer-use: off by default. It sees your screen and your logged-in apps. If you ever need it, run it in the `agent` user’s GUI, not yours.
- Containers/VMs: a VM is stronger isolation but costs RAM you do not have. On 32 GB, **Unix user + directory permissions + command policy** beats Docker Desktop, which itself eats memory. Add a VM later on a bigger machine for untrusted code execution.
- Destructive ops (delete outside workspace, format, disable SIP, change users): hard deny, not “ask the model.”

### 8. Always-on operation

Mac mini on AC is the right host.

- `pmset -c sleep 0 disablesleep 1` (confirm flags on your macOS) so it does not sleep on power. Do not fight lid sleep; this is a mini.
- `launchd` LaunchAgent in the `agent` user (or a LaunchDaemon if you accept the privilege tradeoff—prefer Agent): `KeepAlive`, `ThrottleInterval`, logs to files.
- Supervisor loop: claim one `queued` task, mark `running` with heartbeat, run, mark `done`/`failed`/`blocked`. Crash → launchd restarts → stale `running` older than heartbeat becomes `queued` again (idempotent tasks) or `failed` (non-idempotent).
- Budgets: max wall clock, max model turns, max output tokens, max disk per task. Exceeded → `blocked` and notify. This is runaway protection.
- Watchdog: a tiny second plist that only checks heartbeat and the kill-file. If `STOP` exists, supervisor exits cleanly and does not dequeue.
- Logs: rotate. Do not let logs fill the 512 GB disk.
- After reboot, launchd starts the supervisor; the queue is the continuity. No “resume the chat window.”

### 9. Remote access

- **Tailscale** (or another WireGuard tailnet): phone and laptop join the tailnet. SSH to the mini as `agent` or as a control user that can only signal the queue.
- Submit work by appending a task file or a row (small CLI over SSH). Do not build a public web app first.
- Status: a read-only page bound to the tailnet interface, or `ssh` + `sqlite3` query. Phone: SSH client or a minimal tailnet-only dashboard.
- Notifications: ntfy, email, or a push service **outbound**. Approval requests go there: “push branch X? reply yes with token.”
- Emergency stop: SSH `touch STOP` and/or a Shortcut that does the same. Also a hardware option: you can power off; queue survives.
- Authentication: tailnet identity + SSH keys. No password agent API. No port forwards on the router.

### 10. Storage architecture

External SSDs are slower and less reliable than the internal drive (cable, sleep, unplug). **Source of truth for the queue and the running model should be internal.** External is capacity.

| Data | Where | Why |
|---|---|---|
| macOS, toolchain, inference binary | Internal | Boot reliability |
| **Active** model weights | Internal if they fit | Bandwidth |
| Model archive / unused quants | External | Size |
| SQLite queue + memory DB | Internal, nightly copy to external | Crash/unplug safety |
| Hot git worktrees | Internal | Latency while coding |
| Bare repos, old worktrees | External | Bulk |
| PDFs, datasets, experiment artifacts | External | Bulk |
| Logs | Internal, rotated, archived external | Don’t fill either disk silently |
| Backups | External + one off-machine copy | External is not a backup of itself |

512 GB will fill with models and DerivedData. Cap the local model cache. 1 TB external is the library, not the brain.

---

## A. Recommended technology stack

| Layer | Recommended | Alternatives | Why |
|---|---|---|---|
| OS policy | Dedicated `agent` user, workspace ACLs | VM (later) | Autonomy without your Keychain; VM RAM is too costly now |
| Supervisor | Python 3 + stdlib + SQLite | Go rewrite later | You can read every line; queue is durable |
| Queue / state | SQLite | Postgres | Zero extra service |
| Inference | MLX **or** llama.cpp Metal, one server | Ollama as a temporary loader only | Apple memory path; one API |
| Coding execution | One pinned local coding CLI/harness | Second IDE agent | Worktrees + tests; avoid duplicate brains |
| Research I/O | `curl`/allowed APIs + PDF text extract + claims table | Full browser agent | Citations tied to files |
| Memory | Markdown + Git + SQLite | sqlite-vec later | Reviewable, no extra infra |
| Scheduling | launchd | cron | Restart and KeepAlive |
| Remote | Tailscale + SSH | VPN you already run | No public ports |
| Secrets | Files outside agent home; proxy or per-task inject | Model-visible `.env` | Model should not see long-lived secrets |
| Observability | Structured logs + `runs` table | Prometheus stack | A lab of one does not need a metrics cluster |

Re-verify names and install paths on 31 August 2026 before treating this table as a purchase order. I could not.

## B. Architecture

```text
Phone/laptop --Tailscale/SSH--> control CLI (enqueue, approve, STOP)
                                      |
                                      v
                         launchd --> supervisor (agent user)
                                      |
                    +-----------------+------------------+
                    |                 |                  |
                    v                 v                  v
              SQLite queue      role files         heartbeat/STOP
                    |
                    | one LLM worker at a time
                    v
         model router (rules, not a second big model)
           large: plan/code/debug/synthesize
           small: classify/verify/summarize (when memory allows)
                    |
                    v
            localhost inference (MLX or llama.cpp)
                    |
     +--------------+--------------+------------------+
     |              |              |                  |
     v              v              v                  v
  worktree      shell policy    research store     memory/*.md
  git commit    tests           PDFs + claims      runs log
     |
     +-- blocked if: push, secrets, delete outside root, budget exceeded
```

Change from the prompt’s sketch: the “100 agents” are not a layer under the orchestrator with their own inference. They are **queue rows**. The router is a function in the supervisor, not a service.

## C. Hardware / resource plan

| Consumer | Plan |
|---|---|
| macOS + agent services | ~5–8 GB |
| Inference weights | ~8–14 GB for the primary quant |
| KV cache | Budget 2–6 GB; shrink context if jetsam or swap appears |
| Coding tools, one test run | ~1–3 GB |
| Browser | **Off** during overnight runs |
| SQLite / logs | negligible if rotated |
| Free headroom | ≥6 GB |
| Concurrent large LLM workers | **1** |
| Concurrent small LLM workers | **0–1**, only if a memory snapshot shows both resident without swap |
| Model swapping | Worthwhile between *nights* or between task classes, not between every tool call |
| Expected bottleneck | Memory bandwidth and single-worker token rate, then disk if the external SSD holds the hot repo |

Do not treat these as measured M6 numbers.

**Storage:** keep ≥80 GB internal free. Put the live quant on internal. Everything archival on the 1 TB drive, with the SQLite file copied nightly to external and occasionally off-site.

## D. Agent architecture (100+ logical, not 100 LLMs)

1. Author roles as files: `planner`, `coder`, `test_runner`, `reviewer`, `fetcher`, `extractor`, `citation_verifier`, `synthesizer`, `documenter`. Add roles by adding files.
2. A task names a role, a workspace, a goal, and budgets.
3. Planner (large model, few turns) may create child tasks. It does not call other models itself in a mesh.
4. Supervisor executes children FIFO or by priority, one LLM at a time.
5. Non-LLM children (download, hash, extract text) use a small process pool (2–4) with no model.
6. “Spawn agent” = `INSERT INTO tasks`.
7. Simultaneous LLM inference cap = 1 (config flag). Raising it on 32 GB is an experiment you measure, not a default.

That yields 100+ specialized agents over a week and one GPU-equivalent stream overnight.

## E. Model strategy

Re-benchmark; these are **roles**, not brand endorsements.

| Role | Model class | Notes |
|---|---|---|
| Planning, multi-file coding, debugging, final synthesis | Best local 14–32B coding/reasoning quant that tool-calls reliably | Resident overnight |
| Code review of a diff | Same large model, fresh context with only the diff + failing test | Do not reuse a 100k polluted chat |
| Research synthesis | Same large model, input restricted to claims table | |
| Classification, routing, “quote exists?” | 3–8B instruct | Swap in, or skip and use rules |
| Summarize a single PDF section | Small if quality holds; else large with a tight context | |
| Embeddings | Dedicated small embedding model, batch, not the chat model | Only after keyword search fails |

**Routing rules:** default large for any task that edits code or writes a report. Small for labels, dedup, and citation string match. Escalate to large if small confidence is low. Optional cloud model only when a task is marked `allow_cloud` and local failed twice—never as a silent default. The system must meet its bar with local only.

I will not assert which checkpoint is best on 31 August 2026.

## F. 24/7 architecture

- Power: AC, sleep disabled on charger, auto-restart after power failure if the mini supports it (`pmset` autorestart—confirm).
- Process: launchd KeepAlive on the supervisor.
- State: SQLite in WAL mode on internal SSD.
- Recovery: heartbeat; orphan `running` tasks reset; partial git worktrees left for inspection, not auto-deleted.
- Stop conditions: empty queue, `STOP` file, budget, or a task flag `requires_human`.
- Morning: supervisor can enqueue a `standup` task that summarizes `runs` since last human ack—still one model call, not a daemon chat.

## G. Remote-control architecture

1. Install tailnet; MagicDNS or fixed tailnet IP.
2. SSH key from phone and laptop; no password auth.
3. Commands: `enqueue`, `status`, `logs`, `approve <id>`, `stop`, `resume`.
4. Approvals are rows: supervisor blocks, notifies, continues only on a signed/SSH-issued approve.
5. Dashboard, if any, listens on the tailnet IP only.
6. Do not port-forward 22 or the inference port on the home router. Inference binds to `127.0.0.1`.

## H. Security architecture

**Autonomous:** read/write inside the active worktree; run tests; create branches/worktrees; commit; fetch public papers into the research store; write memory Markdown; enqueue follow-ups; classify and summarize.

**Always blocked:** `sudo`; access outside workspace and research store; Keychain; other users’ homes; disabling firewall; raw disk; exfiltration of `~/.ssh`, cookies, wallets, mail; installing launch daemons; changing the supervisor code without a human commit.

**Approval required:** `git push`, opening a PR, sending email/messages, spending money or calling a paid API, any new outbound domain, deleting files older than the current task, raising the LLM concurrency cap, changing permission policy.

**Controls:** Unix user, directory ACL, command allowlist, network allowlist, secrets outside the model context, per-task time/token/disk caps, `STOP` file, append-only run log, git history as audit of code. The model is not a root-equivalent admin. If a task needs a secret, a proxy injects it or a human runs that step.

## I. Installation plan (re-verify every package name on your OS)

**Phase 1 — minimal loop**
1. Create user `agent`. Log in once and create `~/work`, `~/lab/supervisor`, `~/lab/roles`, `~/lab/memory`.
2. Install Xcode CLT, Homebrew as that user or via a path the agent can execute without admin for daily runs.
3. Python venv in `~/lab/supervisor`. Supervisor: dequeue, call `llm` CLI against localhost, append log, exit.
4. Install **one** inference server; download **one** quant to internal disk; bind `127.0.0.1`.
5. Test: enqueue “write hello.py and run it”; confirm it cannot read `/Users/<you>`.

**Phase 2 — autonomous coding**
1. Install one coding harness; point it at localhost.
2. Policy: worktrees under `~/work/<project>`.
3. Test: failing unit test → harness loops until pass or turn cap → supervisor marks done and writes the diff hash.
4. Rollback: `git worktree remove` and delete the task row.

**Phase 3 — research**
1. Directories `research/sources`, `research/claims`.
2. Fetch script stores bytes + hash before any model sees them.
3. Verifier rejects reports with unknown ids.
4. Test: ask for a citation you did not download; pipeline must refuse.

**Phase 4 — memory**
1. SQLite schema: `tasks`, `runs`, `claims`, `decisions`.
2. Markdown ADRs committed in a `lab-memory` git repo.
3. Test: kill -9 supervisor mid-task; relaunch; task resumes or fails cleanly, decision file intact.

**Phase 5 — multi-agent**
1. Role files and parent/child tasks.
2. Concurrency config hard-coded to 1 LLM.
3. Test: planner enqueues 10 roles; only one inference process appears in Activity Monitor.

**Phase 6 — 24/7**
1. launchd plist, KeepAlive, logs.
2. `pmset` sleep policy on AC.
3. STOP file check each loop.
4. Test: `kill` the process; launchd restarts within throttle; queue consistent.

**Phase 7 — remote**
1. Tailscale; SSH keys; inference still on localhost.
2. Test from phone on cellular: `status`, `stop`. Confirm router has no new forwards.

**Phase 8 — optimize**
1. Measure RAM with one model at 8k/16k/32k.
2. Drop context or quant if swap > 0 during a coding task.
3. Add sqlite-vec only after you can show keyword search misses.
4. Consider a paid API only as an explicit `allow_cloud` escalation.

**Directory sketch**

```text
/Users/agent/lab/supervisor/     # code + venv
/Users/agent/lab/roles/
/Users/agent/lab/memory/
/Users/agent/lab/queue.db        # internal
/Users/agent/work/               # git worktrees
/Volumes/External/models-archive/
/Volumes/External/research/
/Volumes/External/backups/queue.db
```

**Communication:** supervisor ↔ inference via localhost HTTP or CLI; supervisor ↔ harness via subprocess argv and a workspace path; no agent-to-agent sockets.

**Common failures:** OOM jetsam, launchd throttle loop, external disk missing at boot, harness ignoring the worktree root, logs filling the disk, model server bound to `0.0.0.0`.

**Rollback:** unload the plist, stop the model server, boot as your user. Your home was never in the agent ACL. Delete `~/lab` to remove the system.

I am not providing a full plist and a 2,000-line supervisor here; the behavior above is the spec. Write the supervisor yourself so you can audit it—copy-pasting an unreviewed agent OS is the wrong first commit.

## J. What NOT to install

- A second and third inference GUI “just in case.”
- Kubernetes, Docker Desktop as the control plane, Redis, Postgres, Neo4j, Milvus, Weaviate on day one.
- Two multi-agent frameworks plus an IDE agent plus a research agent all with their own loops.
- Public exposure of Ollama/MLX/Open WebUI.
- A 70B quant “because it fits if nothing else runs.”
- GUI computer-use against your personal desktop session.
- Always-on cloud agents that require an API key for the basic loop.
- Anything that needs the agent user to be admin.

## K. Upgrade path

| Change | What to revisit |
|---|---|
| 64 GB | Resident large model + small model together; longer context; maybe a second small worker for verification in parallel |
| 96–128 GB | Larger coding model or longer KV; optional lightweight VM for untrusted test execution |
| Dedicated GPU server | Move **inference only** there; keep the Mac as supervisor, queue, and disk. Do not move secrets with the model server. Prefer tailnet between them |
| More disks | Internal remains queue + hot model; add off-site backup before more agent autonomy |

When memory grows, raise **context and verification quality** before you raise agent chatter.

---

### Sources

Browsing was **off**. I am not listing URLs as if they were fetched on 31 August 2026. That would fake a literature review.

**You should treat as primary and open today:**
- Apple technical notes for the M6 Mac mini (memory, Metal, power states) — primary, hardware.
- MLX and llama.cpp official docs and release notes — primary, inference.
- The coding harness you shortlist: its README, security model, and local-model docs — primary.
- Apple `launchd`/`pmset` man pages — primary, always-on.
- Tailscale (or your VPN) docs on SSH and ACLs — primary, remote.
- SQLite docs (WAL, backup) — primary, state.

**Secondary / not verified this session:** any 2026 leaderboard, Reddit/YouTube “best local agent” roundup, and my class-level memory of Qwen/DeepSeek/Llama/Gemma-style open models. Use those only to build a shortlist, then score them on your mini with a fixed task (edit a repo, fix a test, refuse a missing citation).

**Decision rule if two tools tie:** choose the one you can pin, sandbox under `agent`, and remove with one plist unload. That property matters more than a two-point benchmark gap you cannot reproduce.

## Reasoning trace (not shown to raters)

I am preparing a comprehensive architecture research document for a local autonomous AI workstation on a 32 GB M6 Mac mini.

I cannot browse the web or verify current specs. I am Grok 4 with a knowledge cutoff before August 2026. Apple's M6 chip is unconfirmed; I will rely on general M-series performance estimates.

I will rely on established Apple Silicon patterns rather than inventing M6-specific benchmarks or version numbers. The architecture will clearly separate verified facts from reasonable assumptions about 2026 hardware.

I will avoid recommending any malware or jailbreak tools. The architecture will be strictly legitimate.

I am now calculating the 32 GB unified memory budget. macOS and applications likely consume 6–10 GB. Filesystem cache needs headroom. A single large model should fit within roughly 14–20 GB of weights.

I am narrowing the model selection to 14–32 billion parameter classes. A single heavy inference worker plus a small always-loaded classifier is the practical layout. Model swapping is expensive on unified memory, so one resident coder and a lightweight router are preferable. MLX is the native Apple path, llama.cpp with Metal is a mature fallback, and Ollama provides a convenient wrapper. vLLM is CUDA-oriented and unsuitable for this Mac mini. Agent harnesses drawn from early 2025 patterns remain sound.

I will not recommend any swarm framework. LangGraph, CrewAI, and AutoGen are overkill for this workload. A thin custom Python orchestrator is the better fit for 24/7 queue management, permissions, and model routing.

The orchestrator will use a supervisor process with an SQLite task queue. A single coding harness—likely Aider or a CLI agent using MCP—will handle local model calls. MCP remains a viable integration layer for tooling.

Data will live in filesystem storage and SQLite for tasks, episodes, and decisions. sqlite-vec or a small embedding index can be added later if needed. Neo4j, full vector databases, Kubernetes, and Redis are unnecessary overhead.

Git repositories will serve as the source of truth for code.

A dedicated macOS user named `agent` will isolate the autonomous system.

The workspace will be isolated in a dedicated directory with no access to personal files, Keychain, or Mail. Sudo is denied and git pushes require manual approval.

Network access will use an allowlist or proxy. launchd will keep the system always-on.

Remote access will rely on Tailscale instead of public ports. A simple status page bound to the tailnet, plus ntfy or local alerts, will provide visibility. Cloudflare tunnels exposing the agent shell to the internet are not used by default.

For 24/7 operation, sleep will be disabled via caffeinate or pmset when the Mac mini is on power. SQLite queues will survive crashes so work resumes automatically.

Exact August 2026 model rankings cannot be verified. The architecture will recommend strong open families such as Qwen2.5-Coder, DeepSeek-Coder/R1 distill, Llama 3.x, Gemma, and Mistral for the 14–32 billion parameter range. A small 3–8 billion model will handle routing and classification. Cloud inference is optional but not required. MLX community quantized variants are noted. The sources section will list conceptual primary types for the user to verify rather than inventing URLs.

I will cite canonical project homepages and mark them as not re-verified for August 2026 rather than fabricating current benchmarks. The M6 chip is treated as an unconfirmed Apple Silicon unified-memory Mac mini class with Metal and MLX support. I am refining the memory budget: macOS, WindowServer, and the launchd stack consume roughly 4–8 GB, while the agent Python process, git, and any browser use another 2–4 GB.

SQLite consumes negligible memory. Roughly 18–22 GB of unified memory remains available for inference, with 24 GB as an aggressive ceiling. A 32k context window on a 32B model can consume several gigabytes of KV cache.

The primary worker should be a single 14–32B Q4_K_M or MLX 4-bit model with 16–32k context. An optional 3–8B router can stay loaded only if memory allows; on a 32GB Mac mini it is safer to avoid two large models and let the small model swap in during classification bursts.

One physical worker is sufficient even for 100 logical agents, since tasks are stored in SQLite rows and prompt templates.

## Run notes


