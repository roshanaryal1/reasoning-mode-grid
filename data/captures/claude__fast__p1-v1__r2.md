---
run_id: claude__fast__p1-v1__r2
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
replicate: 2
date_stamped: '2026-10-14T02:40:02+00:00'
date_run: '2026-10-14T02:40:02+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

I'll verify the hardware and current ecosystem first, starting with whether an M6 Mac mini exists.

Hardware confirmed: 170 GB/s, 32 GB cap, Thunderbolt 4. Next, local models and inference engines.

**Claude Sonnet 5.5 | knowledge cutoff: end of June 2026 | web search ON (about 14 searches, snippet-level only, no full-page fetches)**

Date note: your brief says 31 Aug 2026 but the system clock says 14 Oct 2026. I used 14 Oct. Evidence quality: I verified hardware, models, inference engines, harnesses, sandboxes and remote access. Research tooling (GROBID, Docling, sqlite-vec) and the multi-agent frameworks (LangGraph, CrewAI) come from prior knowledge and are marked UNVERIFIED. Anything labeled "estimate" is my arithmetic, not a benchmark.

---

## Decisions at a glance

| Layer | Pick |
|---|---|
| Hardware reality | 170 GB/s bandwidth is the binding constraint, not the 32 GB capacity |
| Inference engine | mlx-lm server first, then oMLX (continuous batching + SSD prefix cache) after a soak test; llama.cpp as fallback |
| Quality lane model | Qwen3.8-27B dense, 4-bit MLX, with MTP/DFlash2 speculative decoding |
| Throughput lane model | Gemma 4 26B-A4B 4-bit (15.6 GB, same slot size). Qwen3.6-35B-A3B only as an opt-in if you accept 20 GB |
| Supervisor / always-on | Hermes Agent (pinned version) |
| Coding worker | OpenCode headless inside a sandbox, driven by Hermes |
| Orchestration | Thin custom `agentd` (about 800 lines Python) on SQLite. No swarm framework |
| Memory | Git-tracked Markdown + SQLite (FTS5), then sqlite-vec later. No vector DB, no graph DB |
| Research | Claim ledger with mechanical citation rendering + Crossref/OpenAlex/Semantic Scholar verification |
| Isolation | Dedicated non-admin `agent` user + Seatbelt for host tools; Colima Linux VM for execution; credential broker outside the sandbox |
| Remote | Tailscale (Serve, never Funnel; SSH; ACL tags; Tailnet Lock) + outbound-only Telegram/Signal gateway |
| Storage | Internal: hot models, SQLite, VM images, worktrees. External: cold models, papers, datasets, backups |
| Cloud | Off by default; per-task opt-in escalation for hard coding and claim judging, sanitized context only |

---

## 1. Local inference

**Hardware facts.** The M6 mini caps at 32 GB RAM with 170 GB/s bandwidth (up from 153 on M5). It has three Thunderbolt 4 ports, which means no Thunderbolt 5 clustering. The M5 Pro mini gets 307 GB/s and 64 GB.

**The key constraint: decode is bandwidth-bound.** A dense 27B at 4-bit reads about 15.5 GB per token, so the ceiling is about 11 tok/s (estimate). Reports on the M6 itself are consistent with this: about 8-9 tok/s on Qwen3.8-27B 4-bit with plain MLX, 16-19 with MTP, and about 5 tok/s at 8-bit. Treat those as secondary, and ignore the headline "53+ TPS" in that same article, which relies on an unexplained alternate engine.

MoE changes the picture. On a 32 GB M2 Max, Qwen3.6-35B-A3B Q4_K_M generated about 58 tok/s, roughly 5.4x a dense 27B. The M2 Max has 400 GB/s, so I expect about 30-50 tok/s on M6 for an A3B/A4B MoE (estimate, unmeasured). Prefill matters as much as decode in agent loops, because every tool call re-reads a growing context. A 9B Q4 model prefilled at 742 tok/s on M6 versus 210 on M4, thanks to the new GPU neural accelerators. A 27B is probably around 250 tok/s (estimate), so a cold 20K-token context costs about 80 s. Prefix/KV caching is therefore a first-order requirement.

**Model evidence.**

- **Qwen3.8-27B** (Apache 2.0, Aug 2026). 4-bit weights are about 15 GB with 262K context. The model card claims 61.7 SWE-bench Pro and 73.0 Terminal-Bench 2.1, but no outside harness has reproduced these. One measurement says it is slower per token than Qwen3.6-27B but uses about a third of the tokens per answer, so wall-clock per finished answer is near parity (single blogger, M3 Ultra, Ollama). KV cost: about 11 GB at 128K, 23 GB at 256K.
- **Gemma 4 26B-A4B**. 15.6 GB peak RSS at 4-bit. The MTP drafter helped only this MoE variant, by +13% on an M1 Max; the dense and E4B variants got slower.
- **Qwen3.6-35B-A3B**. 20.4 GB peak RSS at 4-bit. Too large to co-reside with anything useful.
- **Qwen3-Coder-Next** (80B/3B MoE): about 44 GB at 4-bit, so it does not fit.
- **Lower-bit quants.** One engine's measurements show a 2-bit quant degrading tau2-Bench from 82.9 to 73.6 and IFBench from 68.0 to 58.5. Do not run sub-4-bit for agentic work.
- **Frontier open weights** (DeepSeek V4.1-Flash, Kimi K3, MiMo-V2.6-Pro) are irrelevant locally (hundreds of GB), but DeepSeek V4.1-Flash is a cheap API escalation candidate. It reports 90.6 Terminal-Bench 2.1 (vendor-reported).

**Engines.**

| Engine | Verdict |
|---|---|
| mlx-lm (Apple) | Most mature MLX path, OpenAI-compatible server, no continuous batching |
| oMLX | In one 9B benchmark, the only backend that actually batched under concurrency; coding-agent KV persistence to SSD. Young project, UNVERIFIED stability |
| vllm-mlx | 3.4x throughput at 5 concurrent requests; one correctness test found serving layer faithful to mlx-lm |
| LM Studio | mlx-engine continuous batching since 0.4.2; GUI app is closed source |
| Ollama | Queues requests serially in one benchmark (concurrency 2 and 4 simply queued). Not an agent backend |
| llama.cpp | Best fallback, wider model coverage, and better TTFT on short prompts |

Caveats: MLX output is nondeterministic across batch sizes. Hybrid linear-attention models (Qwen3.5/3.6) limit batching gains. So measure batching on your actual model, not on 9B results.

**Decision.** Start with `mlx-lm` (verified command, boring). Gate oMLX behind a 24-hour soak test and an A/B on determinism and tool-call validity. Keep llama.cpp for models MLX does not yet support.

## 2. Agent runtimes / harnesses

| Candidate | Evidence |
|---|---|
| Hermes Agent (Nous, MIT) | v0.21.6 on Oct 8 2026, about 252k stars; built-in cron that fires only while the gateway runs; 7 terminal backends (local, Docker, SSH, Daytona, Singularity, Modal, Vercel); ACP support; subagents in separate git worktrees. Gateway to Telegram/Signal/Slack, FTS5 session search |
| OpenCode (MIT) | 212k+ stars, 75+ providers, LSP, build/plan agents; headless server for self-hosting; quality depends on the model you point it at |
| Claude Code | Deepest hooks and a built-in sandbox runtime (Seatbelt + proxy), but Claude-family models only. Cloud-dependent, so it cannot be your base |
| Codex CLI | Local providers are the B-path |
| Qwen Code | Official CLI for Qwen models; viable alternative worker |
| Gemini CLI | Replaced by Antigravity CLI on June 18, 2026. Skip |

Disclosure: I am a Claude model, so discount my view on Claude Code accordingly. The ranking above rests on the model-agnostic requirement, not preference.

**Decision: complementary systems, with a thin custom layer.**

1. **Hermes** owns the always-on surface: gateway, cron, messaging, approvals, memory, delegation.
2. **OpenCode headless** is the coding worker inside the sandbox. Hermes shells out to it, which is a documented pattern (Hermes orchestrating OpenCode through its terminal and process tools).
3. **`agentd`** is a small custom scheduler (SQLite queue, lane-aware inference admission, budgets, leases). No existing harness does lane-aware admission against a single unified-memory inference server.

Risks to manage. Hermes went from v0.2 (March) to v0.21 (October), about 19 minor releases in 7 months: pin versions and use the `:stable` Docker tag. Its self-authored skills are an integrity risk: keep `skills/` in git, and require staged promotion. A third-party comparison credits Hermes with a credential-guard chokepoint; I could not verify that, so do not rely on it. One guide calls Hermes "formerly OpenClaw", while the Hermes docs treat them as separate projects with a migration tool. Treat OpenClaw as irrelevant.

## 3. Multi-agent architecture

- **100 logical agents** = 100 rows (Markdown + YAML definitions). Cost: zero RAM.
- **Running agents** = short-lived sessions. Each must acquire an inference slot and a tool-worker slot.
- **Real concurrency** is set by three things: inference slots (2-4, bound by KV memory and bandwidth), tool workers (4-6 sandboxed jobs, bound by 12 CPU cores), and the model-lane window.
- **Topology:** coordinator/worker, depth at most 2. Agents communicate via artifacts (files, DB rows), never free-form peer chat. Swarm peer chat multiplies tokens on a bandwidth-starved machine for no gain.
- **Dynamic agents:** an `agent-forge` meta-agent proposes a definition. A validator enforces a JSON schema and capability attenuation (a child can never hold tools or permissions its parent lacks). The agent is ephemeral with a TTL and promoted only after review.
- **Sequential vs parallel:** parallelize I/O-bound work (web fetch, test runs, PDF parsing) aggressively and LLM decode conservatively. Decode batching helps because it is bandwidth-bound, up to the compute knee, but measure it (see §1 caveats).

Back-of-envelope throughput (estimates). A typical turn is 3K fresh prefill + 600 decode tokens.

| Lane | Per turn | Turns/hour/slot |
|---|---|---|
| Dense 27B, plain | about 80 s | about 45 |
| Dense 27B + MTP | about 50 s | about 70 |
| MoE A4B | about 20 s | about 180 |

Swapping models is worthwhile only in batches: loading 16-20 GB costs roughly 5-15 s warm (estimate), which is negligible per window but destructive per request. The scheduler groups tasks by lane and swaps on queue thresholds or a nightly window.

## 4. Coding agents

OpenCode on the quality lane is the best fit for this machine: model-agnostic, headless server mode, LSP feedback, MIT. Hermes subagents use git worktrees for isolation. Claude Code and Codex are strongest in raw capability and harness depth but cloud-bound. Use them as an explicit escalation tier (§Cost), not the base. Qwen Code is a credible alternate if OpenCode's tool-call handling misbehaves with Qwen chat templates. Test both in Phase 2 on 20 of your own repo tasks and keep whichever has the higher pass rate.

Autonomy loop per task: create worktree → plan (dense lane) → edit/test loop with budgets → self-review in a fresh context → open branch or PR to `agent/*` only → log. Never commit to the default branch.

## 5. Research agents

I could not verify a single best OSS "deep research" product, and I would not adopt one wholesale. The evidence-backed pattern is a deterministic verification pipeline around the model.

- **Existence verification:** multiple audits and tools cross-check references against Crossref (DOI authority), OpenAlex and Semantic Scholar with fuzzy title matching. The problem is real: over 100 hallucinated citations were found in NeurIPS 2025 papers that passed peer review.
- **Claim ledger design:**
  1. Every claim is a row: `claim_text, source_id, verbatim_span, span_offset, content_hash, status`.
  2. The report writer may only emit `[@source_id]` tokens. A renderer resolves them from the DB, so the model never types a citation string.
  3. The verbatim span must string-match the stored PDF/HTML text.
  4. DOI resolves via Crossref, with OpenAlex/Semantic Scholar as second-source existence and a Crossref retraction check.
  5. A separate judge pass checks entailment (span supports claim) with a different prompt and, for high-stakes claims, optionally a cloud model that sees only the claim and span.
  6. Contradictions: cluster claims by entity/topic, pairwise judge within clusters, and store `contradicts` edges.
- **Rate limits:** the Semantic Scholar free tier is slow (about 1 QPS), so cache aggressively and use Crossref/OpenAlex first.
- **Discovery:** SearxNG (self-hosted), arXiv API, OpenAlex, Unpaywall, Europe PMC. **Parsing (UNVERIFIED current best):** PyMuPDF for text, GROBID on demand for references (heavy, so run only when needed).
- **Injection defense:** web readers run with no write tools and no credentials and return structured JSON only (quarantined-reader pattern).

## 6. Persistent memory

| Option | Verdict |
|---|---|
| Markdown in git (`AGENTS.md`, ADRs, project notes) | Day 1. Human-auditable, diffable, rollbackable |
| SQLite + FTS5 | Day 1. Tasks, events, claims, session search. Hermes already uses FTS5 |
| sqlite-vec (UNVERIFIED current status) | Phase 4, when keyword recall fails |
| Dedicated vector DB, Neo4j, GraphRAG | No. A relational `edges` table covers the graph need at this scale |

Rules: agent memory writes go to a staging table with source pointer, timestamp, and `unverified` status. A curator job promotes them. This blunts memory poisoning from injected web content. Keep project-scoped memory separate from global memory by directory and DB.

## 7. Computer control

Evidence of what exists: Seatbelt wrappers (Anthropic's sandbox runtime, Tart, SandVault), a dedicated macOS user plus sandbox-exec pattern, Lume/Cua VMs for GUI agents, and Apple-native container tooling. One third-party write-up reports known escapes and broad filesystem reads in Seatbelt-based sandboxes, so treat Seatbelt as a speed bump, not a wall.

Layered decision:

1. **Dedicated standard (non-admin) `agent` user.** Personal data lives in your account and is unreadable via POSIX permissions.
2. **Execution inside a Linux VM** (Colima, `vz` backend) for builds, tests, and any untrusted code. Hermes's Docker backend targets it.
3. **Seatbelt on host-side tools** that must touch the host (defense in depth).
4. **Credentials never enter the sandbox.** A host-side broker, running as a different user, performs `git push` using repo-scoped deploy keys, restricted to `agent/*` branches, with remote branch protection on `main`.
5. **Network:** VM egress through a domain-allowlist proxy, with pf rules blocking direct egress.
6. **GUI/computer-use:** not on the host. If needed, use a throwaway Lume/Tart macOS VM with a burner account.
7. **Browser:** headless Playwright inside the VM with an empty profile. No logged-in personal sessions.

## 8. Always-on operation

- **Power:** `pmset` no-sleep, `autorestart 1`, a UPS, and a TB4 external SSD on the same UPS.
- **Services:** system LaunchDaemons with `UserName=agent` and `KeepAlive`.
- **GPU wired limit:** a root boot daemon sets `iogpu.wired_limit_mb`. This sysctl is not persistent (UNVERIFIED on macOS 27).
- **Durability:** SQLite WAL queue with leases and heartbeats. Crash recovery returns expired leases to `queued` with `attempt+1`. Idempotency comes from a git worktree per task and checkpoint rows in `task_events`.
- **Watchdogs:** inference health check (a 1-token completion every 60 s, restart on failure), memory-pressure monitor (pause lanes when swap grows or `memory_pressure` goes critical), and a dead-man heartbeat to your phone.
- **Open risks to test in Phase 6:**
  - Metal/MLX from a no-login LaunchDaemon. I could not verify this. The fallback is auto-login for `agent` plus LaunchAgents.
  - FileVault: with it on, a power cut leaves the machine waiting at pre-boot unlock, unreachable remotely. That is a security versus availability call. My recommendation is FileVault ON plus UPS, and accept occasional manual unlock.

## 9. Remote access

Tailscale only. Use `tailscale serve`, not `funnel`, so nothing is internet-reachable. Use Tailscale SSH and, if you adopt it, disable the macOS sshd to avoid a second access path. Tag the node `tag:agent` and write ACLs so the agent node can reach nothing else on your tailnet. Tailnet Lock requires device approval from your phone or laptop before any new node joins. For phone control: Termius or similar over Tailscale SSH, plus the Hermes Telegram/Signal gateway (outbound-only, user-ID allowlist, inline approve/deny buttons). Dashboard: a small read-only status page via `tailscale serve` on loopback. Emergency stop is in §H.

## 10. Storage

| Where | What | Why |
|---|---|---|
| Internal 512 GB | OS and apps, active models (about 60 GB), SQLite DBs, oMLX KV cache, VM disk images, active worktrees, logs (rotated) | Random IO, fsync-heavy, latency-sensitive |
| External 1 TB (APFS, not exFAT) | Cold model archive, papers corpus, datasets, restic backups, run archives | Sequential or cold; TB4 is fine for this. Unplug or power glitch tolerant only for cold data |

Never keep a live SQLite WAL on the external drive. Back up internal to external nightly (restic), with an optional encrypted offsite copy. Cap the VM disk and the log directory with quotas.

---

# Deliverables

## A. Technology stack

| Layer | Recommended | Alternatives | Why |
|---|---|---|---|
| Interface | Telegram/Signal via Hermes gateway + SSH | Slack, web dashboard | Outbound-only, no inbound ports |
| Supervisor | Hermes Agent (pinned) | OpenCode server, custom only | Cron, gateway, memory, subagents already built |
| Orchestrator + queue | `agentd` + SQLite | Temporal, Celery/Redis | Single host, durable enough, zero infra |
| Agents | Markdown/YAML defs | LangGraph, CrewAI (UNVERIFIED) | Definitions are data, not a framework dependency |
| Model router | `agentd` lane scheduler | LiteLLM-style proxy | Needs memory-aware admission control |
| Inference | mlx-lm then oMLX | vllm-mlx, LM Studio, llama.cpp | Maturity first, batching second |
| Models | Qwen3.8-27B + Gemma 4 26B-A4B | Qwen3.6-35B-A3B | Fits memory and bandwidth |
| Coding worker | OpenCode headless | Qwen Code, Claude Code/Codex (cloud) | Model-agnostic |
| Sandbox | `agent` user + Seatbelt + Colima VM | Apple container CLI, Tart, Lume | Cheap and layered |
| Memory | Git Markdown + SQLite FTS5 (+ sqlite-vec) | Qdrant, Neo4j | Avoid unnecessary infra |
| Research | SearxNG + OpenAlex/Crossref/S2 + ledger | Hosted deep-research products | Verifiable citations |
| Remote | Tailscale | WireGuard, Cloudflare Tunnel | ACLs, SSH, Lock |
| Backup | restic | Time Machine | Scriptable, verifiable |

## B. Architecture

```
 Phone/Laptop ──Tailscale (ACL tag:agent)──┐
 Telegram/Signal (outbound only) ──────────┤
                                           ▼
 ┌─────────── Mac mini M6 32GB ──────────────────────────────────────────┐
 │ LaunchDaemons (KeepAlive): sysctl-wired, inference, agentd, hermes,   │
 │                            watchdog, tailscaled                       │
 │                                                                       │
 │  Hermes gateway/cron  ──►  agentd (supervisor + scheduler)            │
 │   (approvals, chat)         │ SQLite queue.db: tasks, leases, events  │
 │                             │ agent defs (md/yaml), budgets, policy   │
 │                             ▼                                         │
 │            ┌────────── lane scheduler / model router ─────────┐       │
 │            │ Lane Q (dense 27B)       Lane T (MoE A4B)        │       │
 │            │ one resident at a time, 2-4 batched slots        │       │
 │            └───────────────────────┬──────────────────────────┘       │
 │                                    ▼                                  │
 │        mlx-lm / oMLX  (OpenAI-compatible, 127.0.0.1:8080)             │
 │                                                                       │
 │  Tool workers (4-6) ──► Colima VM (egress via allowlist proxy)        │
 │    OpenCode headless, tests, headless browser, PDF parse              │
 │  Credential broker (separate user): git push agent/*, no secrets in VM│
 │                                                                       │
 │  Memory: git Markdown + memory.db (FTS5, later sqlite-vec)            │
 │  Research: claim ledger db + verifier (Crossref/OpenAlex/S2)          │
 └───────────────┬───────────────────────────────────────────────────────┘
                 ▼
   External APFS SSD: cold models, papers, datasets, restic backups
```

## C. Resource plan (32 GB, estimates)

| Item | GB |
|---|---|
| macOS 27 + system services | 4.5 |
| Qwen3.8-27B 4-bit weights | 15.5 |
| KV cache: 2 slots x about 24K ctx (about 86 MB per 1K tokens from the 11 GB@128K figure; less with KV quantization) | about 4 |
| Embedding model | 0.5 |
| Hermes + agentd + SQLite + Python | 1.0 |
| Colima VM | 2.5 |
| Headless browser (on demand) | 1.2 |
| Build/test bursts | 1-2 |
| **Total** | about 30-31 |

Set the wired limit to about 22-24 GB. This is tight: do not run a 20 GB MoE alongside anything else. Swap the lane, do not stack models. Gemma 4 26B-A4B (15.6 GB) occupies the same slot as the 27B. Expected bottlenecks: decode bandwidth, cold prefill, and memory pressure during builds. Storage: about 60 GB models, 80-120 GB worktrees and images, and the remaining internal space for DBs and logs, with the corpus and datasets on the external.

## D. 100+ logical agents on one model server

Agent definition, stored as `agents/<name>.md`:

```yaml
name: py-test-fixer
lane: quality          # quality | bulk
tools: [fs.read, fs.write.worktree, shell.sandbox, git.local]
permissions: {network: none, secrets: none, max_diff_lines: 400}
budget: {wall_min: 45, tokens: 400000, tool_calls: 150}
context: [AGENTS.md, repo-map]
```

Queue schema essentials:

```sql
CREATE TABLE tasks(id INTEGER PRIMARY KEY, parent_id INT, agent TEXT, lane TEXT,
  priority INT, status TEXT, lease_until INT, attempt INT, budget_json TEXT,
  workspace TEXT, created INT);
CREATE TABLE task_events(task_id INT, ts INT, kind TEXT, payload TEXT);
```

The scheduler loop:

1. Pick the highest-priority task whose lane matches the resident lane.
2. Admit while slots are free and memory pressure is normal.
3. Swap lanes only when the other lane's queue exceeds a threshold or its window opens (for example a nightly 01:00-05:00 bulk window).

Loop guard: abort a task after three identical tool calls or two consecutive no-diff test failures.

## E. Model strategy

| Role | Model | Notes |
|---|---|---|
| Planning | Qwen3.8-27B (thinking) | Escalate to cloud only on repeated failure |
| Coding | Qwen3.8-27B | Quality over speed; MTP on |
| Debugging | Qwen3.8-27B | Fresh-context second opinion pass |
| Research extraction/triage | Gemma 4 26B-A4B | Bulk lane, nightly window |
| Summarization | Gemma 4 26B-A4B | |
| Classification/routing | Gemma 4 26B-A4B (or a small resident 4B if memory allows) | |
| Claim judging | Qwen3.8-27B; cloud optional for high-stakes | Different prompt from the writer |
| Final synthesis | Qwen3.8-27B | Renders only ledger-backed claims |
| Embeddings | small embedding model, about 0.5 GB | Phase 4 |

This is a hypothesis, not a result. Build a 50-100 task golden set from your own repos and research questions first, and re-decide using pass rate per hour, not leaderboards.

## F. 24/7 architecture

Everything above in §8, summarized: boot to daemons, `agentd` reclaims expired leases, Hermes cron enqueues scheduled jobs, the nightly plan is: 01:00 research bulk lane, 05:00 swap to quality lane, run a verification sweep, send a 07:00 digest to your phone. If a task fails twice it is parked in `blocked` with a failure summary and you are notified, never retried forever.

## G. Remote control

- Phone: Telegram/Signal commands `/status /queue /approve <id> /deny <id> /pause /stop`, plus Termius via Tailscale SSH for logs.
- Approvals arrive as inline buttons with the diff summary. Auth: user-ID allowlist, and approvals that change permissions require a second factor (a code shown over SSH).
- Dashboard: a read-only page via `tailscale serve`. No public ports.

## H. Security architecture

Autonomy tiers:

| Tier | Operations |
|---|---|
| Fully autonomous | Read/write inside the task worktree; run tests in VM; branch/commit locally; allowlisted web fetch; write to staging memory; create `agent/*` branches |
| Notify, no approval | Push `agent/*` to remote; install packages in VM; large downloads under quota |
| Require approval | Merge to default branch; any network domain outside the allowlist; permission or tool grants to new agents; deleting more than N files or outside the worktree; touching your personal home directory; spending cloud money; any financial, credential, or email action; changing launchd or system config |
| Never | Reading `~/` of your main account; keychain access; `sudo`; disabling the sandbox; accessing banking/password manager |

Controls:

- **Per-task limits:** wall time, token cap, tool-call cap, disk quota, 2 GB RSS cap on tool workers.
- **Git safeguards:** protected `main`, branch-name allowlist, force-push blocked, deploy keys scoped per repo.
- **Prompt injection:** any content from web or files is data. Readers have no tools.
- **Audit:** append-only `task_events` plus command log shipped to the external drive nightly.
- **Kill switch:** `agentctl stop` (SIGTERM all, drain), a `STOP` file the scheduler polls, Telegram `/stop`, and hard stop via `launchctl bootout` or revoking the Tailscale node.

## I. Installation plan (phased, with tests and rollback)

**Phase 0: host hardening (30 min).**

```bash
sudo sysadminctl -addUser agent -fullName "Agent" -password -   # standard user
sudo pmset -a sleep 0 disksleep 0 autorestart 1 womp 1 powernap 0
brew install uv git gh ripgrep tailscale colima docker
sudo tailscale up --ssh      # then tag the node, set ACLs, enable Tailnet Lock
```

Rollback: `sudo sysadminctl -deleteUser agent`, restore pmset defaults. Failure mode: the wired-limit sysctl does not persist, so put it in a boot daemon.

**Phase 1: minimal working system.**

```bash
uv tool install mlx-lm
mlx_lm.server --model mlx-community/Qwen3.8-27B-4bit --port 8080   # model id from HF card mirror
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
hermes config set terminal.backend docker
hermes doctor
```

Colima: `colima start --cpu 4 --memory 3 --disk 60 --vm-type vz`. Point Hermes at `http://127.0.0.1:8080/v1` through `hermes model` custom endpoint. Test: a "write a failing test and fix it" task round trip; measure tok/s and TTFT. Failure modes: tool-call template mismatches (validate JSON tool calls), OOM at long context (cap `max_tokens` and ctx). Rollback: stop the daemons and delete `~/.hermes`.

**Phase 2: autonomous coding.** Install OpenCode per opencode.ai docs (UNVERIFIED install syntax). Config sketch, verify against the current schema:

```json
{"provider":{"local":{"npm":"@ai-sdk/openai-compatible","options":{"baseURL":"http://127.0.0.1:8080/v1"},
 "models":{"qwen3.8-27b":{"name":"Qwen3.8 27B"}}}},"model":"local/qwen3.8-27b"}
```

Run it inside the VM against a worktree. Test: 20 real repo tasks, record pass rate and wall time. Failure modes: infinite edit loops (loop guard), flaky tests (rerun policy). Rollback: `git worktree remove` and delete branch.

**Phase 3: research agents.** SearxNG in the VM, verifier scripts hitting Crossref/OpenAlex/S2, ledger DB, renderer. Test: plant 10 fabricated references and 10 real ones; require 100% of fabricated flagged and 0 false accepts. Failure modes: Semantic Scholar rate limits, books and reports not in the databases (mark `unvalidatable`, never `verified`).

**Phase 4: memory.** `memory/` git repo, `memory.db` with FTS5, staging table and curator job. Add sqlite-vec only if recall tests fail. Test: ask about a decision made 3 days earlier and require a cited source row. Rollback: `git revert` and restore the DB from restic.

**Phase 5: multi-agent orchestration.** Build `agentd` (queue, leases, lane scheduler, budgets, agent-forge validator). Trial oMLX behind a flag and run the soak test (24 h, 3 concurrent clients, compare outputs against mlx-lm on 50 prompts). Failure modes: lane thrash (hysteresis), KV exhaustion (per-slot ctx cap).

**Phase 6: 24/7.** LaunchDaemons with `KeepAlive`, `ThrottleInterval`, `UserName=agent`; test by killing each daemon, then a hard power-cycle with a task mid-run, and confirm lease recovery. Verify Metal works without a login session, else switch to auto-login plus LaunchAgents.

**Phase 7: remote.** Tailscale ACLs, `tailscale serve --bg` for the dashboard, Telegram allowlist, approval flow, kill switch. Test from cellular with Wi-Fi off, and test that revoking the node cuts access.

**Phase 8: optimization.** MTP/DFlash2 speculative decoding (DFlash 2 has an MLX backend with Qwen3.8-27B checkpoints), KV quantization, prefix-cache tuning, and a monthly re-evaluation of models on your golden set.

Directory layout:

```
/Users/agent/lab/{agentd/, agents/, queue.db, workspaces/<task>/, repos/, memory/, research/{ledger.db,corpus/}, logs/}
/Volumes/LabData/{models-cold/, papers/, datasets/, backups/, archive/}
```

## J. What NOT to install

Ollama as the agent backend (serial queueing). OpenClaw (redundant with Hermes; unverified security posture). LangChain, CrewAI, AutoGen swarms (token blowup, extra surface). Qdrant, Milvus, Chroma, Neo4j, GraphRAG (premature). Redis, Celery, Kafka, Kubernetes, Temporal (single host). Docker Desktop (heavier than Colima). Open WebUI, n8n (extra internet-facing surface). A large MCP server zoo. Host-level GUI computer-use agents. Any 2-bit quantized model for agent work. Abliterated or uncensored models (they add risk, not capability, for this use). Cursor (GUI-centric; now owned by SpaceX) and Gemini CLI (discontinued). Qwen3-Coder-Next 80B (does not fit).

## K. Upgrade path

| Change | Effect |
|---|---|
| M5 Pro mini, 64 GB, 307 GB/s | Roughly 1.8x bandwidth. 27B at 8-bit, two models co-resident, Qwen3-Coder-Next at 4-bit (about 44 GB) becomes feasible |
| Mac Studio M5 Max/Ultra | M5 Ultra reaches 1.2 TB/s. Larger MoE models, real concurrency |
| 128 GB+ | Poolside Laguna S 2.1 class (68 GB at 4-bit), more slots, longer contexts |
| Linux box with 24-48 GB GPUs | vLLM/SGLang with real PagedAttention batching; keep the Mac as the supervisor and tool host |

No Thunderbolt 5 clustering on M6, so scaling means replacing hardware, not adding minis.

---

## Cost summary

Everything above is free or open source. Optional paid: cloud escalation for hard coding tasks (Claude Code, Codex, or a cheap open-weight API such as DeepSeek V4.1-Flash) and a cloud claim-judge. I did not verify current pricing, so check before budgeting. Local wins for privacy, overnight bulk work, and anything touching private repos. Cloud wins for the hardest 5-10% of coding tasks and high-stakes claim verification. Send only sanitized context.

## Biggest uncertainties

- **oMLX stability and batching on hybrid models (about 50% it passes the soak test).**
- **Metal under a no-login daemon (UNVERIFIED).**
- **Real M6 tok/s for 26B-A4B and 35B-A3B (my 30-50 estimate has no measurement behind it).**
- **Qwen3.8-27B benchmark claims, which no outside harness has reproduced.**

## Sources

**Primary**
- Hermes Agent repo: https://github.com/NousResearch/hermes-agent and docs https://hermes-agent.nousresearch.com/
- mlx-serve repo: https://github.com/ddalcu/mlx-serve
- Qwen3.8-27B MLX HF cards: https://huggingface.co/srv-sngh/Qwen3.8-27B-mlx-4bit , https://huggingface.co/p4ik/Qwen3.8-27B-MLX-OptiQ-4bit
- DFlash: https://pypi.org/project/dflash/
- Citation hallucination papers: https://arxiv.org/pdf/2605.07723 , https://arxiv.org/pdf/2603.03299 , https://arxiv.org/html/2602.15871v1 , https://arxiv.org/pdf/2609.07652
- MLX comparison paper: https://arxiv.org/pdf/2511.05502
- Sandbox lists: https://github.com/fishman/awesome-agent-sandbox
- Benchmark dataset: https://huggingface.co/datasets/RaynarDM/apple-silicon-llm-benchmarks

**Secondary**
- M6 mini launch coverage: https://macrumors.com/2026/08/25/apple-announces-2026-mac-mini , https://www.igeeksblog.com/mac-mini-m6-m5-pro-price-specs-release-date/ , https://camerajabber.com/?p=1423800 , https://www.macstories.net/?p=198258 (Apple's own press release was not fetched)
- M6 local-AI measurements: https://www.mindstudio.ai/blog/m6-mac-mini-local-ai-performance , https://daily.dev/posts/mac-mini-m6-first-look-qwen3-8-27b-hits-53-tps-locally-eqglitifc , https://medium.com/data-science-collective/best-local-llms-for-apples-new-mac-mini-and-mac-studio-7d7bcf08add1
- Model roundups: https://vdf.ai/blog/best-local-llm-for-coding/ , https://rapidmlx.com/blog/best-local-llm-for-your-mac-by-ram , https://pinggy.io/blog/best_open_source_self_hosted_llms_for_coding/ , https://terminalbytes.com/run-qwen-3-8-27b-locally , https://youmind.com/ar/landing/x-viral-articles/qwen38-27b-mac-deployment-guide
- Engine benchmarks: https://yage.ai/share/mlx-apple-silicon-en-20260331.html , https://jaesolshin.com/posts/apple-silicon-llm-backends/ , https://pypi.org/project/infer-check/0.1.0/
- Gemma MTP: https://lilting.ch/en/articles/google-gemma-4-open-model-family
- Harness comparisons: https://pinggy.io/blog/top_cli_based_ai_coding_agents/ , https://www.firecrawl.dev/blog/best-ai-coding-agents , https://parallel.ai/articles/what-is-hermes-agent
- Sandboxes and remote: https://www.codeofhonor.com/projects/sandvault/ , https://dev.to/aniketmaurya/disposable-macos-sandboxes-for-ai-agents-test-safely-every-time-3och , https://lobster.shahine.com/security/tailscale-ssh/ , https://mager.co/blog/2026-02-22-openclaw-mac-mini-tailscale/
- Research tooling skills: https://skillselion.com/skills/ar9av/paperorchestra/literature-review-agent , https://skillselion.com/skills/brycewang-stanford/awesome-agent-skills-for-empirical-research/check-citations

## Reasoning trace (not shown to raters)

Claude responded: I'll verify the hardware and current ecosystem first, starting with whether an M6 Mac mini exists.
Resolving a date discrepancy before starting the research.
Resolving a date discrepancy before starting the research.

I’ll verify the hardware and current ecosystem first, starting with whether an M6 Mac mini exists.

Searched the web

Searched the web





4 hours ago

## Run notes

claude.ai incognito chat (no history or memory), model menu Sonnet 5.5, Effort Low; the menu showed
"Sonnet 5.5 Low". Connectors were switched off in the composer menu; the composer has no web-search
switch, and Claude searched the web by itself. Send time 2026-10-14T02:40:18.033Z (browser clock, read right after
sending). Chat: https://claude.ai/chat/b8a4b75f-e21b-4c97-92ef-e23cfebff32e?incognito (incognito chats are not kept in history).
Operated by the assistant (Claude, via the Claude in Chrome extension) in the author's signed-in browser,
at the author's request; the runs were opened in separate tabs and sent in manifest order without waiting
for earlier answers. The app turns long pastes into an attachment, so the prompt was inserted as plain
text in eight line-aligned pieces from one clipboard paste and checked against the original (1,782 words,
same text) before sending. Answer copied with the app's Copy button (it includes any short lines the model
wrote before its searches) and written verbatim from the clipboard; the reasoning trace is the visible
process panel (step summaries and search queries) copied from the page text.
