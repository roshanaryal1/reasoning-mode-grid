---
run_id: claude__fast__p1-v1__r4
set: main
family: claude
vendor: Anthropic
mode: fast
native_label: claude.ai, Sonnet 5.5, Effort Low
channel: web
model_requested: Anthropic chat app, claude.ai, Sonnet 5.5, Effort Low
model_returned: Sonnet 5.5 (app model menu, Effort Low)
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 4
date_stamped: '2026-10-14T02:35:47+00:00'
date_run: '2026-10-14T02:35:47+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

Starting with verification of the hardware, since the whole memory budget depends on it.

# Local always-on autonomous workstation on an M6 Mac mini (32 GB): research and build spec

**Model:** Claude Sonnet 5.5 (Anthropic)
**Knowledge cutoff:** end of June 2026
**Browsing:** ON. I ran 8 standard-mode searches and did not fetch full pages, so most claims rest on search snippets.
**Date:** your prompt says 31 Aug 2026 but the session clock says 14 Oct 2026. I used 14 Oct 2026.

**Evidence tags:** [V] = seen in a search result this session (mostly secondary sources). [K] = from my training knowledge, not re-verified, so check before relying on it. [E] = my own estimate or extrapolation.

**Conflict of interest:** I'm built by Anthropic, so I deliberately did not make any closed vendor harness the core of this design.

**What I did not verify:** current state of Claude Code, Codex CLI, OpenHands, Aider, Tailscale, launchd on macOS 27, and the academic-metadata APIs. Those parts come from [K] and need a quick check.

---

## Decisions at a glance

| Layer | Pick |
|---|---|
| Hardware reality | M6: 12-core CPU, 12-core GPU with Neural Accelerators, 170 GB/s, 32 GB max, Thunderbolt 4 only [V] |
| Primary local model | Qwen3.6-35B-A3B (MoE, ~3B active), ~4-bit (~20 GB) |
| Fallback quant | 3-bit class (~13-16 GB) if memory pressure turns yellow in burn-in |
| Inference engine | llama.cpp `llama-server`, OpenAI-compatible, 2 slots. oMLX is the benchmarked challenger. |
| Orchestration | Custom thin conductor (Python, SQLite queue, launchd), not an LLM harness |
| Coding worker | OpenCode, headless, inside a sandbox. Pi plus little-coder is the lean fallback. |
| Research | Claim-ledger architecture: reader/actor split, verbatim span checks, no LLM-written bibliography |
| Memory | Markdown in Git, plus SQLite (FTS5 first, sqlite-vec later) |
| Sandbox | Dedicated non-admin macOS user, Apple `container` microVMs or Lima, default-deny egress proxy |
| Remote | Tailscale only (no public ports), outbound push notifications, signed approval tokens |
| 24/7 | LaunchDaemons with KeepAlive, leased tasks with heartbeats, `pmset`, UPS |
| Storage | Models, DBs and worktrees on internal. Cold archive and backups on external. |
| Cloud | Optional escalation only, with hard budget caps |

---

## 1. Local inference

**Hardware:** The M6 mini launched with 16 GB base, 32 GB max, 170 GB/s (153 GB/s at 16 GB), and 3x Thunderbolt 4 [V]. Apple's claim of 4.8x faster LLM prompt processing than M4 is a vendor figure [V].

**Why a small-active-parameter MoE:** Decode is memory-bandwidth-bound, so tokens/s is roughly bandwidth divided by active bytes per token. The OWC blog claims 170 GB/s only suits 7-8B models [V]. That ignores MoE: Qwen3.6-35B-A3B has 256 experts and ~3B active parameters [V], so it reads about 2 GB per token, not 20 GB.

**Measured data points (not on M6):**
- M2 Max 32 GB (400 GB/s) with Qwen3.6-35B-A3B Q4_K_M (20.22 GB): 58.6 tok/s on llama.cpp and 86.9 tok/s on MLX 4-bit. About 21.8 GB was wireable to the GPU [V].
- The prefill figure from the same dataset was 671 tok/s at pp4096 on llama.cpp [V].
- On M5 Max 128 GB, the dense Qwen3.6-27B reached 17 tok/s (MLX) and 32 tok/s (llama.cpp with MTP) [V].

**Estimate for M6:** Scaling by bandwidth (170/400 = 0.43) gives 25-37 tok/s single-stream for the MoE [E]. The dense 27B would land around 5-10 tok/s [E], so it is not a throughput model here. Treat the M6 numbers as unmeasured until you run the bench.

**Quality:** Qwen self-reports SWE-bench Verified 73.4 and Pro 49.5 for the 35B-A3B [V]. Those use Qwen's scaffold, so expect lower in your harness. Artificial Analysis composite: 27B scores 37, 35B-A3B scores 33 [V]. The dense model is slightly smarter but 3-5x slower on your bandwidth.

**Engines:** The evidence conflicts, and which is faster depends on the machine and build.
- llama.cpp beat MLX for the MoE on M5 Max (105 vs 85 tok/s, with MTP) [V]. MLX beat llama.cpp on M2 Max (86.9 vs 58.6) [V].
- MLX has no schema-constrained decoding [V]. One source says MLX tool-calling trails llama.cpp [V]. Another reports oMLX 0.3.6 with Hermes outperforming other engines on agent/tool calling [V].
- oMLX offers an SSD KV-cache spill: one user reports 128K context with RAM capped around 22-24 GB on a 32 GB M5 [V, single anecdote].
- Ollama switched to an MLX backend in March 2026 (preview) and handles concurrency as a near-serial queue [V]. I exclude it.
- LM Studio's engine supports MLX continuous batching, but the app is closed-source [V]. I exclude it from the headless stack.

**Decision:** llama.cpp `llama-server` is the default because it is mature and supports grammar-constrained JSON for tool calls. Every component talks OpenAI-compatible HTTP, so swapping to oMLX is a config change. In Phase 8, run your own 20-task suite on both and switch if oMLX wins end-to-end task completion by more than 25%. Confidence in the default: 60%.

**Context and concurrency:** Run 2 slots at 48K tokens each, with q8_0 KV cache. Aggregate batch speedups exist (vllm-mlx reports 3.4x at 5 concurrent, and one paper reports 3.7x at batch 16 [V, secondary]). MoE gains less because different sequences activate different experts [K]. Start at 2 slots and test 3-4 for short-context jobs.

## 2. Agent runtimes and harnesses

- **OpenClaw** is the cautionary tale. Sources agree on multiple critical CVEs (including a CVSS 9.9), tens of thousands of exposed instances, and malicious marketplace skills, but disagree on counts (40k to 500k+ exposed) [V]. Prompt injection there persisted through memory files [V]. Do not use it as your control plane.
- **Hermes Agent** (Nous, open source): scheduler, messaging gateway, memory, skills, and first-party skills to drive OpenCode, Claude Code, Codex and others as sub-agents [V, secondary]. It overlaps your conductor. I could not verify its security posture. Evaluate it in Phase 5 as an optional skills/memory layer, not as the core.
- **OpenCode:** MIT, 75+ providers plus local, session compaction, headless loops [V]. **Pi:** leanest context, and the author of a June 2026 local-agent book uses it on a Mac mini M2 Pro 32 GB [V]. **Aider:** git discipline. **Claude Code, Codex CLI:** strong but tied to vendor models [K].
- The Stanford Meta-Harness claim that harness design is the top performance lever [V, secondary via PyPI page] is consistent with my experience but unaudited here.

**Decision:** Build a thin conductor yourself (~500-800 LOC). Queue, leases, budgets, kill switch and approvals are safety invariants and must not live inside an LLM loop. Use existing harnesses as workers inside sandboxes. This is a custom layer on top of existing technology, not a framework build.

## 3. Multi-agent architecture on 32 GB

Definitions, because the terms get conflated:
- **Logical agent:** a database row (role prompt, tool allowlist, permission profile, model class, budgets). Costs zero RAM when idle. 100+ is trivial.
- **Worker:** a process that leases a task, instantiates an agent from its row, and runs a loop.
- **Inference slot:** one concurrent decode stream in `llama-server`. This is the scarce resource: 2-4.
- **100 simultaneous model instances:** impossible. Each full copy is ~20 GB.

**Throughput model:** Wall time in agent work is dominated by tool execution (tests, builds, fetches), not decoding. So size three separate pools:
1. Inference slots: 2 (up to 4 for short contexts).
2. Sandbox executors: 2-3 microVMs, each memory-capped.
3. I/O workers (fetch, parse, PDF extraction): 8, no GPU use.

An agent blocked on a test run frees its slot for another agent. Priority classes keep interactive requests ahead of batch work.

**Architecture:** Coordinator/worker with hierarchical decomposition, with depth ≤ 3 and fan-out ≤ 5. Swarm-style free-for-all is wasteful on one slot-limited model. Dynamic agent creation goes through an agent factory: the planner emits a spec in a strict schema, and permissions must be a subset of the parent's (capability attenuation). A spawned agent can never gain access its parent lacks.

**Model swapping:** Not worthwhile. Reloading 20 GB takes roughly 7-10 s from internal NVMe [E], and the real cost is evicting the KV cache and warm state. One resident model plus a small embedder, with cloud escalation for hard tasks, beats swapping.

## 4. Coding agents

Evaluation axes for your machine are context overhead (48K per slot is small), tool-call reliability on a 3B-active model, headless operation, and worktree discipline.

| | Pick |
|---|---|
| Best overall (any model) | Claude Code / Codex CLI class [K, not re-verified] |
| Best for your hardware | Pi (lean prompt) or OpenCode |
| Best open source | OpenCode (MIT) |
| Lightweight | Pi plus little-coder |
| Mature/stable | OpenCode, Aider |
| Cutting edge | Hermes-orchestrated multi-harness |
| **Use** | OpenCode headless, via the conductor |

I'd make this a bake-off in Phase 2 over 20 private tasks and 2 days. Default OpenCode, because 24/7 unattended work favors an org-backed project over a one-maintainer one. Switch to Pi if context truncation failures exceed ~10% of runs. Confidence: 60%.

Realistic expectation: a 3B-active local model handles well-scoped bug fixes, test writing and module-level refactors with verification gates. It is unreliable on cross-cutting architecture. One user report says multi-file agentic work with a 30B coder caused swap spikes and killed sessions on 32 GB [V]. This is why the memory plan below is conservative.

## 5. Research agents

I found no single product that solves citation integrity, so design it as a pipeline. The key principle: **the LLM never writes a citation. It references IDs that a deterministic system already verified.**

1. **Discover:** web search plus arXiv, Crossref, OpenAlex and Semantic Scholar APIs [K].
2. **Snapshot:** store every source as an immutable file (HTML or PDF) with URL, fetch time and SHA-256.
3. **Reader plane (untrusted):** a no-tools, no-secrets model call extracts `{claim, quote, char_offsets}` from the snapshot into the SQLite ledger.
4. **Deterministic check:** the quote must appear verbatim at those offsets in the snapshot. A mismatch means the claim is rejected.
5. **Entailment check:** a second pass with a separate prompt judges whether the quote supports the claim (supported / partial / contradicted).
6. **Contradiction detection:** cluster claims by entity and topic via embeddings, then compare pairs flagged by the entailment pass.
7. **Writer:** composes prose referencing claim IDs only. The renderer builds the bibliography from ledger rows, and any sentence without a claim ID is flagged "unsourced".
8. **DOI/URL resolution:** done by code, not the model.

Prompt injection from web content is the main threat. The OWASP-aligned view is that it is architectural rather than patchable [V]. The reader/actor split plus the verbatim check contain it.

## 6. Persistent memory

**Start with:** Markdown files in a Git repo as the source of truth (decisions, project notes, experiment logs), plus SQLite for tasks, events, claims and run metadata, with FTS5 for keyword search.

**Add at Phase 4:** `sqlite-vec` [K] with a small embedding model (e.g. Qwen3-Embedding-0.6B or EmbeddingGemma-300M [K, not verified]) for hybrid BM25+vector retrieval. Memory is scoped per project, with a global tier for preferences.

**Do not add:** a knowledge graph, Postgres or a vector server. Add a graph only if relationship queries demonstrably fail with FTS+vector. A real risk is memory poisoning, where injected text gets written to memory and persists. The OpenClaw persistence incidents show this [V]. Mitigation: agents propose memory writes, the conductor stores them with provenance and a trust label, and untrusted-origin entries never enter system prompts.

## 7. Computer control

**Threat model:** the "lethal trifecta" of private data, untrusted content, and an exfiltration path [V, framing from the agentcage docs]. Remove at least one leg per worker.

- **Isolation ladder** (weakest to strongest): macOS Seatbelt-style sandboxes (e.g. Claude Code's `sandbox-runtime`) [V]; Apple `container` microVMs (macOS 26+, ~10-20x faster than Lima and ~3x less RAM per cage, per agentcage docs) [V]; Lima VMs using Apple Virtualization.framework (Lima v2.1 targets agent sandboxing; its macOS guests are experimental) [V].
- **Tools seen:** `agentcage` (default-deny egress, TLS-inspecting proxy, placeholder secret injection; its own README warns it is experimental) [V]. Others: `drydock`, `sand`, `agent-vm`, `muthr` (llama.cpp on host, opencode in Lima VMs reaching the host via `host.lima.internal`) [V].
- **Browser:** Playwright inside the sandbox with a throwaway profile, no logged-in sessions [K].
- **GUI computer use:** off by default. If ever needed, use a disposable macOS guest VM, never your main desktop.

**Decision:** Dedicated standard-user account, workers in Apple `container` microVMs (Lima as fallback), egress through an allowlist proxy that injects secrets. Evaluate `agentcage` first, and fall back to your own Squid/mitmproxy allowlist if it proves unstable. Never run agents as your main user.

## 8. Always-on operation

- LaunchDaemons (start at boot, `KeepAlive`) for `llama-server`, the conductor and the proxy. The conductor reaps expired task leases on boot, so a crash mid-task becomes a requeue, not a loss.
- `sudo pmset -a sleep 0 disksleep 0 autorestart 1 womp 1` [K], plus a UPS.
- **FileVault trade-off [K, ~85% confident]:** with FileVault on, a reboot waits at the unlock screen and daemons do not start. That defeats unattended recovery. My recommendation: treat the mini as a dedicated agent host, keep no personal data on it, use FileVault OFF, and hold only scoped, revocable, spend-limited API keys. If you must keep sensitive data on it, keep FileVault ON, add a UPS, and accept manual unlock after a total power loss.
- An HDMI dummy plug is usually needed for headless GPU/screen-sharing sessions [K].
- Watchdog: a second tiny LaunchDaemon pings the conductor and inference endpoints every 30 s, restarts them on failure, and sends a push alert after 3 consecutive restarts.

## 9. Remote access

- **Tailscale** [K]: no inbound ports, WireGuard-based, ACLs restricting the phone to the dashboard port only. Bind the dashboard to the tailnet interface, never `0.0.0.0`. OpenClaw's exposed-gateway disaster [V] is the failure mode to avoid.
- **Notifications:** outbound-only push (ntfy self-hosted, or a Telegram bot with a fixed chat-ID allowlist).
- **Approvals:** the conductor creates a one-time, expiring, signed token tied to the exact action hash. Approving over the tailnet resumes that action only.
- **Emergency stop:** (a) a button on the dashboard, (b) an SSH shortcut on the phone, (c) a `KILL` file that every worker checks each loop and that the supervisor enforces by stopping all containers. Optional: a smart plug as a last-resort hardware cut.
- **Task submission:** `POST /tasks` on the dashboard or a Telegram command, authenticated by tailnet identity plus a token.

## 10. Storage

| Item | Location | Reason |
|---|---|---|
| macOS, tools, sandbox images | Internal | Speed |
| Main model GGUF/MLX (~20 GB), embedder | Internal | Weights are mmap'd, and page faults over external TB4 would hurt |
| SQLite DBs (WAL), ledger | Internal | Never on a removable volume: a disconnect can corrupt WAL |
| Active repos, worktrees, build caches | Internal | Small-file heavy, wants low latency |
| Logs (hot 30 days) | Internal | Rotate to external after 30 days |
| Alternate models, papers, datasets, source snapshots (cold) | External | Capacity, sequential reads |
| Backups (restic/Time Machine) | External | Keep the Git remote off-box as well |

**Reliability:** External drives can fail to mount at boot or disappear on power events. The conductor must treat the external volume as optional: check the mount, degrade gracefully, and never write primary state to it. The external 1 TB SSD is not a backup of itself. Add an off-site copy of Git remotes and the memory repo.

---

## Independent market comparison

| Category | Best overall | Best for your HW | Best open source | Lightweight | Mature/stable | Cutting edge | **Use** |
|---|---|---|---|---|---|---|---|
| Inference engine | llama.cpp / MLX | llama.cpp or oMLX | llama.cpp | llama.cpp | llama.cpp | oMLX (SSD KV cache) | llama-server |
| Model | Frontier cloud | Qwen3.6-35B-A3B | Qwen3.6 family | Small Qwen/Gemma 4 | Qwen3.6-27B | Fine-tunes like Ornith-1.0-35B (self-reported 75.6 SWE-V) [V] | Qwen3.6-35B-A3B |
| Coding agent | Claude Code / Codex [K] | Pi / OpenCode | OpenCode | Pi | Aider / OpenCode | Hermes-driven | OpenCode |
| Control plane | Custom | Custom | Hermes Agent | Custom | Custom | Hermes | Custom conductor |
| Memory | Hybrid | SQLite+FTS5 | SQLite | Files | SQLite | Graph+vector | Files+SQLite |
| Sandbox | Firecracker/VMs | Apple container | Lima | Seatbelt (srt) | Lima | agentcage | Apple container + egress proxy |
| Remote | Tailscale | Tailscale | Headscale | SSH | Tailscale | n/a | Tailscale |

---

# Deliverables

## A. Technology stack

| Layer | Recommended | Alternatives | Why |
|---|---|---|---|
| Interface | Tailnet-only dashboard (FastAPI + simple PWA) plus Telegram/ntfy push | Hermes gateway | No public exposure, minimal code |
| Supervisor | launchd watchdog daemon | Hermes scheduler | Survives conductor crashes |
| Orchestrator | Custom Python conductor | Hermes, LangGraph | Safety invariants outside the LLM |
| Task queue | SQLite (WAL) with leases | Redis, Postgres | One machine, no extra service |
| Agents | Rows in `agents` table | Framework classes | Zero idle cost |
| Router | Rules + embedding kNN + budget policy in conductor | LiteLLM | Fewer dependencies |
| Inference | llama.cpp llama-server | oMLX | Constrained decoding, maturity |
| Coding worker | OpenCode headless | Pi, Aider | Local endpoint, MIT |
| Research | Claim ledger pipeline | Off-the-shelf deep-research tools | Citation integrity |
| Memory | Git+Markdown, SQLite FTS5, sqlite-vec | Graph DB | Avoid infra |
| Sandbox | Apple container microVMs, Lima fallback | agentcage | Hardware boundary |
| Remote | Tailscale | WireGuard direct | Easiest correct option |

## B. Architecture diagram

```
 Phone / Laptop
   │ Tailscale (WireGuard, no public ports)        ntfy/Telegram (outbound push)
   ▼                                                    ▲
 Dashboard (tailnet-bound) ── approvals / kill / submit ┘
   │
   ▼
 Watchdog (LaunchDaemon) ──restarts──► Conductor (LaunchDaemon)
                                         │  SQLite: tasks, leases, budgets, events, ledger
                                         │  Policy engine: permissions, limits, approvals
                                         ├──► Router ─► llama-server :8080 (Qwen3.6-35B-A3B, 2 slots)
                                         │           └► [optional] cloud API, budget-capped
                                         │
        ┌────────────────────────────────┼────────────────────────┐
        ▼                                ▼                        ▼
  Coding worker                    Research READER           Research ACTOR
  (microVM: OpenCode,              (microVM, no tools,       (tools, never sees raw web
   git worktree, tests)             no secrets, sees web)     text, only ledger rows)
        │                                │                        │
        └──── egress proxy (allowlist, secret injection, audit) ──┘
                                         │
 Memory: Markdown+Git  |  SQLite FTS5 + sqlite-vec  |  Source snapshots (external SSD)
```

## C. Hardware and resource plan

Allocation on 32 GB, with the GPU wired limit raised to ~25 GB (default ~21.8 GB per the M2 Max data [V]; `sudo sysctl iogpu.wired_limit_mb=25600` [K], resets on reboot, so persist it with a LaunchDaemon):

| Component | RAM |
|---|---|
| macOS plus system daemons (headless) | ~4.0 GB |
| Model weights (Q4_K_M-class) | ~20.2 GB [V] |
| KV cache and compute buffers (2 slots × 48K, q8_0) | ~2.0 GB [E] |
| Embedder | ~0.7 GB |
| Conductor, proxy, Tailscale, SQLite | ~0.8 GB |
| 2 microVMs capped at 1.5 GB each | ~3.0 GB |
| **Total** | **~30.7 GB** |

That leaves ~1.3 GB of headroom, which is too thin for heavy builds. Pre-committed rule: run a 48-hour burn-in and watch `memory_pressure` and swap. If pressure goes yellow or swap exceeds ~2 GB sustained, drop to the 3-bit class (~13-16 GB; IQ3_S at 12.74 GB measured 51-55 tok/s on M2 Max [V], quality loss unmeasured by me). Skip a host browser on the mini, and run builds inside capped VMs.

**Counts:** 1 resident large model, 0 concurrent large-model workers beyond slots, 2 inference slots, 2-3 sandbox executors, 8 I/O workers, 1 embedder.

**Disk (internal, ~512 GB):** models ~25-40 GB, repos and worktrees 40-80 GB, DBs and logs 10-30 GB, sandbox images 10-20 GB, OS and tools ~60 GB. External: papers, datasets, snapshots, backups, alternate models.

**Output budget [E]:** at ~30 tok/s single-stream, 8 overnight hours is ~860K output tokens per stream, more with 2 slots.

## D. Agent architecture (100+ logical agents)

```sql
CREATE TABLE agents(id TEXT PRIMARY KEY, role TEXT, system_prompt TEXT,
  tools JSON, perm_profile TEXT, model_class TEXT, max_tokens INT, max_wall_s INT, parent TEXT);
CREATE TABLE tasks(id TEXT PRIMARY KEY, project TEXT, agent_id TEXT, parent_id TEXT,
  state TEXT CHECK(state IN ('queued','leased','running','verifying',
                             'needs_approval','done','failed','dead')),
  priority INT, lease_expires INT, attempts INT, budget_tokens INT, spec JSON, result JSON);
```

- **Loop:** plan, decompose into child tasks, workers lease tasks (heartbeat every 15 s), execute in a sandbox, verify (tests, linters, ledger checks), then either spawn follow-ups or finish. Verification gates, not the model's self-assessment, decide "done".
- **Limits:** depth ≤ 3, fan-out ≤ 5, ≤ 100 live definitions per run. A task fails after 3 identical tool calls, or after 5 iterations with no diff or test progress.
- **Stopping conditions:** queue empty, run budget exhausted, 3 consecutive task failures (pause and notify), or the `KILL` file.
- **Dynamic spawn:** the planner proposes a spec, the conductor validates it against the schema and parent permissions, and it is audit-logged.

## E. Model strategy

One resident model keeps the system stable. Roles differ by prompt, thinking mode and tool set, not by weights.

| Role | Model | Notes |
|---|---|---|
| Planning | Qwen3.6-35B-A3B, thinking on | Escalate epics to cloud (optional) |
| Coding | Same | Test-gated; escalate after 2 failed attempts |
| Debugging | Same, thinking on | Escalate after N failures with full trace |
| Research extraction/verify | Same, thinking off, constrained JSON | Deterministic span checks do the real work |
| Summarization | Same, thinking off | |
| Classification/routing | Rules + embedding kNN; model fallback with grammar | |
| Final synthesis | Same locally; optional cloud pass | Citations come only from the ledger |

Cloud is genuinely worth it for hard architecture planning, stubborn debugging and final polish. Local wins for bulk work, anything touching private repos, and overnight volume. I'm not quoting API prices: check vendor pages. Keep the system useful with cloud disabled.

## F. 24/7 architecture

- LaunchDaemons: `llama-server`, conductor, proxy, watchdog, wired-limit sysctl. All `RunAtLoad` and `KeepAlive`.
- State lives in SQLite. On start, the conductor requeues any task whose lease expired, with a fresh worktree reset (tasks must be idempotent).
- The watchdog health-checks `/health` on inference and the conductor, then restarts and alerts.
- Nightly: back up the DBs and memory repo to external plus off-site, rotate logs, prune worktrees and sandbox images.
- Morning digest pushed to your phone: completed, failed, awaiting approval, spend.

## G. Remote-control architecture

Phone to Tailscale to dashboard (bound to the tailnet IP only). Tailscale ACLs allow the phone to reach only the dashboard port and SSH. Push comes from ntfy/Telegram, outbound only. Approvals use signed single-use tokens bound to an action hash. Three stop paths: dashboard, SSH shortcut, and `KILL` file. Rotate tokens quarterly and keep the dashboard free of any shell endpoint.

## H. Security architecture

**Accounts and filesystem:** Run everything as a standard (non-admin) `agentd` user. Workers see only their worktree. The human user's home, Keychain, SSH keys, browser profiles, Messages and Photos are never mounted.

**Network:** Default-deny egress. All outbound goes through the proxy with a domain allowlist, request logging and secret-pattern scanning.

**Secrets:** Agents hold placeholders, and the proxy injects real values outbound (agentcage pattern [V]). Use per-repo deploy keys and low-limit API keys that are revocable.

**Two-plane rule:** Any worker that has read untrusted web content runs without secrets, without push rights and without write access outside its sandbox. Only structured, verified outputs cross into the actor plane.

**Git safeguards:** Per-task worktrees on `agent/<task-id>` branches. The agent can push only to `agent/*` refs. Main is protected, so merging to it needs a human PR approval. Force-push is disabled.

**Fully autonomous:**
- Read granted workspaces
- Edit inside a task worktree
- Run tests and linters in the sandbox
- Install dependencies from lockfiles via an allowlisted, pinned, hash-checked mirror
- Fetch allowlisted web domains
- Commit and push to `agent/*`
- Write to its own scratch space and propose memory entries

**Requires approval:**
- Push to or merge into any protected ref
- Deleting more than N files, or anything outside the worktree
- Any non-allowlisted egress, and any allowlist change
- Using a credential outside its scoped binding
- Sending email or messages
- Any financial site
- Cloud spend above the per-task cap
- Modifying conductor config, launchd or policy
- Creating an agent with permissions above its parent's

**Never allowed:** `sudo`, access to the human user's data, disabling the kill switch or audit log, GUI control of your real desktop.

**Limits and audit:** Per-task wall-clock 2 h, token budgets, per-night cloud cap, and loop detection (the numbers are my starting proposals, to tune from logs). Append-only audit log of every tool call and approval, hash-chained, with a copy shipped off-box. Container CPU and memory limits are enforced.

## I. Installation plan

**Phase 1: Minimal working system (inference plus a sandboxed coding run)**

```bash
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install llama.cpp uv git gh jq ripgrep lima sqlite
pip install -U "huggingface_hub[cli]"
hf download unsloth/Qwen3.6-35B-A3B-GGUF --include "Qwen3.6-35B-A3B-UD-Q4_K_M.gguf" --local-dir ~/models
sudo sysctl iogpu.wired_limit_mb=25600   # persist via LaunchDaemon
llama-server -m ~/models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf -ngl 99 -c 98304 --parallel 2 \
  --jinja --host 127.0.0.1 --port 8080 -ctk q8_0 -ctv q8_0
```

Flag names such as flash-attention differ between builds, so run `llama-server --help` to confirm. Install Apple `container` from its GitHub release `.pkg` (macOS 26+) [V], and OpenCode per its current docs (I could not verify the canonical install command). Create the `agentd` standard user. *Test:* `curl localhost:8080/v1/chat/completions` returns a valid tool-call response, and OpenCode in a VM edits a throwaway repo. *Failure modes:* OOM or swap (drop to the 3-bit quant), tool-call template errors (ensure `--jinja`). *Rollback:* stop the daemon, delete the VM.

**Phase 2: Autonomous coding.** Git worktree per task, the bake-off (OpenCode vs Pi), and a test-gated loop. *Test:* 20-task private suite, with the pass rate recorded as the baseline. *Failure modes:* infinite edit loops (loop detector) and context truncation. *Rollback:* `git worktree remove`, and delete the `agent/*` branch.

**Phase 3: Research agents.** Build the ledger (sources, passages, claims tables), reader/actor split, and the verbatim checker. *Test:* feed in a paper containing a known false claim, and confirm it is flagged. *Failure modes:* PDF extraction noise breaking offsets (store plain-text extraction alongside the raw file). *Rollback:* the ledger is append-only, so re-run from snapshots.

**Phase 4: Persistent memory.** Markdown repo, SQLite FTS5, then sqlite-vec with an embedding model. *Test:* retrieve a decision made two weeks ago by keyword and by paraphrase. *Failure modes:* memory poisoning (provenance labels), index drift (rebuild from the Markdown). *Rollback:* `git revert` and rebuild.

**Phase 5: Multi-agent orchestration.** Conductor with `agents` and `tasks` tables, leases, heartbeats, spawn validation and priority queues. *Test:* kill a worker mid-task and confirm it requeues. *Failure modes:* slot starvation (priority classes), runaway fan-out (hard caps). *Rollback:* disable spawning, run sequentially.

**Phase 6: 24/7 operation.** LaunchDaemon plists (`KeepAlive`, `RunAtLoad`), `pmset`, the watchdog and UPS. *Test:* pull power, then confirm automatic recovery and requeue. *Failure modes:* external volume not mounted at boot, and FileVault blocking daemons. *Rollback:* `launchctl bootout` each daemon.

**Phase 7: Remote access.** Tailscale, dashboard, push, approval tokens and kill paths. *Test:* from cellular, submit a task, approve an action, trigger the kill switch. *Failure modes:* the dashboard accidentally bound to all interfaces (verify with `lsof -i`). *Rollback:* `tailscale down`.

**Phase 8: Advanced optimization.** Benchmark oMLX against llama.cpp, tune slot count, try MTP/speculative decoding (+75% on the dense 27B and +12% on the MoE in one measurement [V], so low value for your MoE), and consider the 3-bit quant if memory pressure demands. *Test:* the Phase 2 suite. *Rollback:* config revert.

**Directory layout:**
```
/Users/agentd/{conductor, state/{tasks.db,ledger.db,memory.db}, mirrors/, worktrees/<task-id>/, memory-repo/}
/Volumes/Work/{archive/, papers/, datasets/, snapshots/, backups/}
```

## J. What NOT to install

- **OpenClaw as the control plane:** reported critical CVEs, malicious marketplace skills and mass exposure [V], with persistent prompt-injection backdoors.
- **Ollama** for the serving path: near-serial concurrency and a preview MLX backend [V]. Its single-binary convenience is not worth it for a batching workload.
- **LM Studio** for the headless stack: closed-source app.
- **LangChain/LangGraph/CrewAI-style frameworks:** you need a task queue with leases, not a graph DSL.
- **Docker Desktop:** heavier than Apple `container` or Lima, and its VM competes for your tight RAM.
- **Vector DB servers, Neo4j, Postgres, Redis:** unnecessary infrastructure at one machine.
- **Dense 27B as the main worker:** slower by 3-5x in this memory-bandwidth regime [E].
- **A second large model resident:** it will not fit.
- **Third-party agent skills or marketplace plugins unaudited:** one audit found roughly 36% of reviewed OpenClaw skills had injection content [V].
- **GUI computer-use on your real desktop.**

## K. Future upgrade path

- **M5 Pro Mac mini, 64 GB, 307 GB/s [V]:** about 1.8x bandwidth and 2x RAM. The dense 27B becomes usable, two models can be resident (a fast MoE for workers plus a stronger verifier), and slots can double. It has Thunderbolt 5 [V], so Apple's multi-mini clustering becomes possible, but that does not exist on your M6 [V].
- **Mac Studio M5 Ultra (1.2 TB/s per Apple's announcement [V]) or 128 GB+ machines:** large MoE models become practical, the memory ceiling stops dominating, and you can raise to 4-6 slots.
- **Dedicated NVIDIA GPU server with vLLM:** best for many concurrent agents. One A100 test showed vLLM at 793 tok/s vs Ollama at 41 under concurrency [V], though that is a datacenter GPU and an Ollama comparison. Keep the Mac mini as the control plane and sandbox host, and point the router at the GPU box over the tailnet.
- **At every step:** the conductor, ledger and memory carry over unchanged because everything speaks OpenAI-compatible HTTP and SQLite.

---

## Sources

Primary means official or first-party data. Most of what I found was secondary, and I did not fetch Apple's own newsroom page.

| URL | Type |
|---|---|
| https://github.com/stared/benching-local-llms-on-apple-silicon | Primary measurements (third-party benchmark repo, M5 Max) |
| https://huggingface.co/datasets/RaynarDM/apple-silicon-llm-benchmarks | Primary measurements (community dataset, M2 Max 32 GB) |
| https://huggingface.co/Litwein/Qwable-v2-oQ4e-DWQ-MTP-MLX | Primary (model card, community fine-tune) |
| https://huggingface.co/RigCodeAI/Qwen3.6-35B-A3B | Primary (model card, community repackage; reports Qwen's benchmarks) |
| https://pypi.org/project/agentcage/0.40.2/ | Primary (tool docs) |
| https://github.com/sandst1/agent-vm | Primary (repo) |
| https://docs.rs/crate/muthr/latest/source/README.md | Primary (repo README) |
| https://github.com/fishman/awesome-agent-sandbox | Secondary (curated list) |
| https://github.com/manjunathshiva/turboquant-mlx | Primary (repo, unaudited claims) |
| https://github.com/ag2-space/agent-connect | Primary (repo) |
| https://pypi.org/project/polyharness/ | Primary (project page; cites the Meta-Harness paper secondhand) |
| https://arxiv.org/pdf/2511.05502v1 | Primary (paper, Apple Silicon framework comparison) |
| https://www.igeeksblog.com/mac-mini-m6-m5-pro-price-specs-release-date/ | Secondary (hardware specs) |
| https://t2online.in/tech/tech-news/apple-mac-mini-launches-with-m6--m5-pro-chips/2007528 | Secondary (quotes Apple statements) |
| https://www.macstories.net/tag/m6/ | Secondary (hardware) |
| https://www.owc.com/blog/apple-updates-mac-mini-lineup-with-m5-pro-and-new-m6-chips | Secondary (a claim I disagree with, see §1) |
| https://camerajabber.com/photography-news/apples-m6-mac-mini-brings-2nm-silicon-and-a-300-price-rise/ | Secondary |
| https://www.starryhope.com/minipcs/models/mac-mini-2026-m6/ | Secondary |
| https://tinyweights.dev/posts/run-qwen3-6-35b-a3b-locally/ | Secondary |
| https://yage.ai/share/mlx-apple-silicon-en-20260331.html | Secondary |
| https://www.emergentmind.com/topics/mlx | Secondary |
| https://vercel.com/i/ollama-vs-vllm | Secondary |
| https://www.digitalapplied.com/blog/run-local-llms-ollama-vs-lm-studio-vs-vllm-2026-guide | Secondary |
| https://bestllmfor.com/guides/mlx-local-llm-apple-silicon/ | Secondary (low reliability) |
| https://capitalandcompute.net/best-ai-agent-harnesses/ | Secondary |
| https://notes.dsebastien.net/30+Areas/33+Permanent+notes/33.02+Content/Hermes+Agent | Secondary |
| https://leanpub.com/read/local-coding-agents/preface-the-rise-of-local-coding-agents | Secondary (practitioner book) |
| https://reddit.sentinel-team.org/posts/1uw2hir/snapshots/2026-07-17T18%3A53%3A30.39359Z | Secondary (single anecdote) |
| https://lucaberton.com/blog/lima-v21-ai-agent-sandboxing-macos-2026/ | Secondary |
| https://www.techradar.com/pro/here-are-the-openclaw-security-risks-you-should-know-about | Secondary |
| https://www.techzine.eu/news/security/138633/over-40000-openclaw-agents-vulnerable/ | Secondary |
| https://clawdocs.org/security/overview | Secondary (aggregator) |
| https://betterclaw.io/blog/openclaw-security-2026 | Secondary (counts vary widely across sources) |

**Confidence summary:** the hardware facts and the MoE-over-dense reasoning are the strongest parts. The engine choice (llama.cpp vs oMLX), the OpenCode vs Pi pick, and the M6 tok/s figures are the weakest, and each has a test in the roadmap that resolves it. Next I'd run Phase 1's bench on the actual M6 and replace every [E] number with a measured one.

## Reasoning trace (not shown to raters)

Claude responded: Starting with verification of the hardware, since the whole memory budget depends on it.
Resolving a date discrepancy before starting the research.
Resolving a date discrepancy before starting the research.

Starting with verification of the hardware, since the whole memory budget depends on it.

Searched the web

Searched the web
Searched the web
Mac mini M6 release memory bandwidth specs

Researching local models and agent harnesses for the setup.
Searched the web
best local coding model 32GB Mac MLX agentic 2026

Searched the web
MLX vs llama.cpp vs Ollama Apple Silicon concurrency continuous batching 2026

Searched the web
open source coding agent harness local models OpenCode Hermes Agent comparison 2026

Researching tools and setup for running a local sandboxed environment.
Searched the web
Qwen3.6-35B-A3B MLX 4-bit memory GB tok/s SWE-bench Apple Silicon

Searched the web
macOS sandbox AI agent Tart VM Apple container Lima isolation autonomous agent 2026

Searched the web
OpenClaw security vulnerabilities exposed instances 2026 prompt injection

Rating model choices and quantization fallback by benchmark evidence.






4 hours ago

## Run notes

claude.ai incognito chat (no history or memory), model menu Sonnet 5.5, Effort Low; the menu showed
"Sonnet 5.5 Low". Connectors were switched off in the composer menu; the composer has no web-search
switch, and Claude searched the web by itself. Send time 2026-10-14T02:35:50.508Z (browser clock, read right after
sending). Chat: https://claude.ai/chat/ce5960a1-4c7e-4af2-841e-7c1610105c48?incognito (incognito chats are not kept in history).
Operated by the assistant (Claude, via the Claude in Chrome extension) in the author's signed-in browser,
at the author's request; the runs were opened in separate tabs and sent in manifest order without waiting
for earlier answers. The app turns long pastes into an attachment, so the prompt was inserted as plain
text in eight line-aligned pieces from one clipboard paste and checked against the original (1,782 words,
same text) before sending. Answer copied with the app's Copy button (it includes any short lines the model
wrote before its searches) and written verbatim from the clipboard; the reasoning trace is the visible
process panel (step summaries and search queries) copied from the page text.
