---
run_id: claude__reasoning__p1-v1__r4
set: main
family: claude
vendor: Anthropic
mode: reasoning
native_label: claude.ai, Sonnet 5.5, Effort High
channel: web
model_requested: Anthropic chat app, claude.ai, Sonnet 5.5, Effort High
model_returned: Sonnet 5.5 (app model menu, Effort High)
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 4
date_stamped: '2026-10-14T02:42:54+00:00'
date_run: '2026-10-14T02:42:54+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

Starting with the hardware, since the "M6 Mac mini" premise determines everything downstream.

**Claude Sonnet 5.5 (Anthropic) | reliable knowledge cutoff: end of June 2026 | web search and page fetch: ON (about 35 searches and 6 page fetches this session)**

**Before the content**
- **Date:** your brief says 31 Aug 2026, but the session clock says 14 Oct 2026. The M6 Mac mini only shipped on 22 Sep 2026, so I treated 14 Oct as today and used post-ship data.
- **Conflict of interest:** I am built by Anthropic, and Claude Code is an Anthropic product. I weighted it by third-party evidence and kept a fully open alternative in every slot.
- **Evidence tags:** [M] means a reported measurement on an M6 32 GB or close machine, from a secondary source. [V] means vendor-reported. [E] means my estimate or derivation from cited inputs.
- **Evidence quality:** nearly all M6 performance data is secondary (blog and GitHub summaries). I found no independent rigorous benchmark. Anything tagged [E] or [V] must pass the Phase 1 gates in section I before you build on it.

**Three facts that drive the design**
1. The 24 GB and 32 GB M6 tiers reach 170 GB/s memory bandwidth. Decode is bandwidth-bound, so a dense 27B model at 4-bit (16.1 GB on disk) has a theoretical ceiling of about 10.6 tok/s [E: 170 / 16.1].
2. The GPU can only wire a fraction of RAM by default. On 32 GB the default cap is roughly 21 to 24 GB. Whatever remains must also hold macOS, agents, sandboxes and the browser.
3. The M6 mini has three Thunderbolt 4 ports at 40 Gb/s; Thunderbolt 5 is reserved for the M5 Pro. The NAND is soldered and cannot be swapped, so SSD write endurance is a real constraint, not a footnote.

## Decisions at a glance

| Layer | Pick | Confidence |
|---|---|---|
| Machine posture | Dedicated agent appliance, no personal accounts; GPU wired limit raised to about 24 GB | 85% |
| Inference engine | oMLX (pinned) primary; llama-server fallback; Splash as a gated experiment | 65% |
| Models | Qwen3.6-35B-A3B 4-bit as worker, Qwen3.8-27B 4-bit as deep model, one resident at a time, plus an always-on embedding model. Flip to 27B-primary if the Splash/MTP gate passes | 60% |
| Worker harness | Claude Code pointed at the local Anthropic-compatible endpoint, version-pinned. OpenCode and Pi adapters kept ready | 55% |
| Orchestrator | Custom thin supervisor (Python) over a SQLite lease queue | 80% |
| Durable execution | SQLite plus git checkpoints; no Temporal or Hatchet | 85% |
| Memory | Git-tracked Markdown plus SQLite FTS5 now; sqlite-vec when needed | 85% |
| Research | Evidence ledger with deterministic citation checks before any LLM judge | 90% |
| PDF parsing | Docling by default, MinerU on demand | 60% |
| Sandbox | Dedicated users, Seatbelt via sandbox-runtime, Apple `container` VMs, pf egress rules | 75% |
| Remote | Tailscale, tailnet-only dashboard, tmux over Tailscale SSH, Web Push | 80% |
| Cloud | Optional escalation tier with hard caps and per-project `local-only` labels | 85% |

---

## 1. Local inference

**Measured behaviour on your exact chip [M]**
- A compiled report of 32 GB M6 results shows Qwen3.6-35B-A3B at about 64 tok/s and plain Qwen3.8-27B at about 11 to 12 tok/s.
- Qwen3.8-27B with Splash speculative decoding reached 45.2 tok/s on code generation and 67.7 on structured output.
- A separate hands-on reported 8 to 9 tok/s on plain MLX, 16 to 19 with multi-token prediction, and 26 to 56 with Splash.
- Splash is vendor-supported only above your RAM. It requires at least 36 GB and recommends 48 GB or more. Two secondary sources ran it on 32 GB anyway. Treat it as experimental: it may refuse to start or leave almost no KV headroom.

**Models**

| Model | Facts | Verdict |
|---|---|---|
| Qwen3.8-27B (dense) | Apache 2.0, 262K native context, vision, adjustable reasoning effort. Qwen reports 73.0 on Terminal-Bench 2.1 and 61.7 on SWE-bench Pro, versus 63.4 and 53.5 for Qwen3.6-27B. | Best quality that fits. Slow decode without speculation |
| Qwen3.6-35B-A3B (MoE) | 3B active parameters; 73.4 on SWE-bench Verified, 49.5 on SWE-bench Pro, 51.5 on Terminal-Bench 2.0 per Qwen. The dense 3.6-27B is stronger: 77.2 on SWE-bench Verified and 59.3 on Terminal-Bench 2.0. | About 5x faster decode, clearly weaker. Ideal bulk worker |
| Gemma 4 26B-A4B | Qwen's own comparison table lists 17.4 on SWE-bench Verified. A community write-up also reports tool refusals in agent loops (low confidence) | Reject for agent loops |
| GLM-5.3 and other 300B-class | GLM-5.3 reports 88.2 on Terminal-Bench 2.1 but is a 128 GB-class deployment | Does not fit; cloud-only option |

Benchmark numbers come from different harnesses and are not comparable across rows. One third-party datapoint matters for the harness choice: an 84-task Terminal-Bench 2.1 subset run through Claude Code 2.1.228 scored 73.81% pass@1 on an NVFP4 build of Qwen3.8-27B. That shows the model performs well inside that harness. It is also a subset on a different quantization, not your configuration.

**Why not just run the biggest thing that fits:** work per hour is quality × throughput.
- **Prefill:** agent loops are prefill-heavy, because they keep reading tool output. On a 48 GB M5 Pro, Splash prefilled the 27B at about 363 tok/s and the 35B-A3B at about 2,000 tok/s at 32K prompts. Your 12-core GPU is slower, perhaps 0.5 to 0.6x [E]. The MoE wins prefill by 4 to 6x.
- **Token efficiency:** one comparison found Qwen3.8-27B answering in about 1,000 tokens where Qwen3.6-27B used 2,000 to 3,300. That is one Mac Studio test on Q&A prompts, so confidence in it is low.
- **Wall time per answer [E]:** MoE about 39 s, 27B plain about 87 s, 27B with MTP about 59 s, 27B with Splash about 22 s.
- **Consequence:** 27B plain is too slow as a default worker. It is a strong "deep" model, and becomes viable as primary only if speculation works on your box.

**Quantization and context**
- **Weights:** use 4-bit. Higher quants of the 27B do not leave room for context. Roughly 4 to 6 GB must stay free for macOS. Do not use 3-bit builds for tool-calling agents until you have measured tool-call accuracy against 4-bit.
- **KV cache:** Qwen3.8-27B is a hybrid. Only 16 of its 64 layers keep a growing KV cache, at 64 KB per token in fp16. The other layers hold a fixed recurrent state per sequence. That state is roughly 80 to 150 MB per live sequence [E, derived from SGLang's token-equivalent figures]. An 8-bit KV cache halves the per-token cost to about 32 KB.
- **MoE KV:** I did not verify the 35B-A3B's KV per token. It shares the hybrid decoder family, so it is probably similar. Read its `config.json` in Phase 1.
- **Context budget:** the total live context across all concurrent sequences is about 85K tokens in worker profile and about 175K in deep profile (section C) [E]. Set a per-request ceiling of 64K for coding and 128K only for sequential research ingest.

**Engines**
- **oMLX (pick):** continuous batching and tiered RAM/SSD KV caching, installable via Homebrew. It serves LLMs, VLMs, embeddings and rerankers from one server. It exposes OpenAI and Anthropic APIs and defaults to 8 concurrent requests. The README lists M1 to M4, so verify M6 support. It is young, so pin versions.
- **vllm-metal:** the official vLLM plugin; a September 2026 post shows paged KV and concurrency-4 results close to oMLX. Watch it, and keep it as the likely successor if you outgrow oMLX.
- **LM Studio headless:** version 0.4 added parallel requests, a headless daemon (llmster) and remote linking. The MLX engine added continuous batching. This is a good alternate and the easiest path to the Splash backend.
- **llama.cpp:** keep as a fallback. MLX was reported to lag at prefill and at 30K+ contexts.
- **Ollama:** its MLX preview targeted Macs with more than 32 GB. On the 27B it decoded at about 24 tok/s versus oMLX at 38 and Splash at 74 [V]. Skip it.

**Batching reality check [V]:** Inco's four-way test shows oMLX moving from 38 tok/s single-stream to only 43 tok/s combined on the 27B, while Splash went from 74 to 170. That is a competitor's measurement, but it matches the physics: a dense model is bandwidth-bound, so extra streams barely add throughput without speculation. Plan on 2 decode streams, not 8.

---

## 2. Agent runtimes and harnesses

**The landscape**
- **Hermes Agent (Nous, MIT):** a built-in cron scheduler, isolated parallel subagents and seven terminal backends. It runs commands directly on the host by default and recommends a sandboxed backend. Subagents get their own terminal sessions and cannot write shared memory or schedule more work. It is pre-1.0 and ships security fixes as named releases. It is the closest off-the-shelf match to your brief.
- **OpenClaw:** researchers cataloged six 2026 CVEs, including a one-click RCE that worked against a localhost-bound instance, plus hundreds of malicious marketplace skills. Do not use it for an unattended machine.
- **Pi:** four tools and a system prompt under 1,000 tokens, MIT, with subagents available via packages. There are deliberately no permission popups; the intended guardrail is a container. The project moved to Earendil in 2026, and some future enterprise features may become Fair Source.
- **OpenCode:** MIT, about 202K stars, provider-agnostic with Ollama support.
- **Aider:** no commits since May 2026 (verify). Skip it.
- **Codex CLI:** Apache-2.0, and the top-ranked harness on Terminal-Bench 2.1 with GPT-5.6 Sol. That result is for a cloud model; local support exists but I did not test it.
- **Claude Code:** subagents, background agents, hooks, an Agent SDK, scheduled tasks, and support for third-party providers. Remote Control, teleport and cloud Routines require a claude.ai subscription. LM Studio 0.4.1+ and Ollama 0.14+ expose Anthropic-compatible local endpoints, so no proxy is needed. oMLX exposes one too. One local-cache gotcha: a documented setting disables the attribution header, which otherwise alters the prompt prefix and can defeat KV prefix reuse. Verify this in Phase 1.

**Decision: build a thin supervisor; use harnesses as replaceable workers.**
- None of these systems schedules against a single-GPU model lease, a memory-weighted admission budget, per-project sensitivity labels, or verification gates. Those are your actual differentiators.
- Adopting a monolithic "agent OS" splits state across its memory, its cron and your queue.
- Hermes's self-authored skills and memory are a persistence vector for injected instructions.
- The supervisor is about 1.5 to 2.5K lines of Python [E]. Keep it small by pushing everything that is not scheduling, policy, audit or verification into existing tools.
- **Fallback if you want zero custom code:** Hermes with the Docker backend and its approval mode on. Accept the churn and the skill-learning risk.
- **Subscription caveat:** a secondary source says Anthropic changed its policy in April 2026 on routing subscription OAuth through third-party harnesses. Use API keys, not consumer-subscription tokens, in any third-party tool, and re-check the terms.

---

## 3. Multi-agent architecture

**Definitions (as they matter here)**
- **100 simultaneous model instances:** impossible. The KV alone for 100 sequences at 32K is at least 100 GiB even at 8-bit.
- **100 logical agents:** 100 rows in a table. They cost nothing at rest.
- **Agent definition:** a versioned role prompt, toolset, permission profile, model class, budgets and memory scopes.
- **Task:** an objective with machine-checkable acceptance criteria.
- **Run:** one attempt of an agent on a task.
- **Worker pool:** 3 to 4 harness processes of about 0.4 GB each [E].

**Throughput design**
- **Concurrency:** GPU decode is the shared bottleneck. Useful concurrency is about 1 / (1 − tool-wait fraction) [E]. If agents spend half their time in tests, builds and fetches, two streams saturate the GPU. The rest of the queue waits.
- **Admission control:** gate by memory weight, not by count. Each task class declares RAM cost. The scheduler refuses anything that pushes committed memory past about 31 GB.
- **Semaphores:** `gpu_decode` (2, up to 4), `big_prefill` (1 active, chunked), `sandbox_vm` (1 to 2), `browser` (1), `pdf_parse` (1), `net_fetch` (8).
- **Model leases:** the scheduler batches "deep" tasks into lease windows (overnight by default) and "worker" tasks into day windows. A swap costs 10 to 30 s [E; 16 to 20 GB from internal NVMe at about 6.4 GB/s measured on a 512 GB M6 unit]. Keep both model files on internal storage and let the SSD KV tier preserve prefixes across swaps.
- **Shape:** coordinator/worker, depth at most 2. A Planner (deep model) emits a task DAG with acceptance checks. Workers execute. An independent Verifier runs deterministic checks first, then an LLM judge. A Librarian is the only agent that writes memory.
- **Spawn limits:** depth 3, fan-out 8, 200 tasks per objective, plus token and wall-clock budgets. A dynamic agent is an LLM-written spec. It is validated against a schema and a capability-attenuation rule (a child may never hold more permissions than its parent), then stored inactive until it passes validation.
- **No free-form swarm chatter:** agents communicate through typed artifacts in the DB and files. Debate patterns multiply contexts, and every extra token costs KV memory and prefill time on a 170 GB/s machine.
- **Prefix discipline:** keep system prompts stable and contexts append-only. Pin same-project tasks to the same slot to keep caches hot.
- **Fewer LLM calls:** classification uses embeddings plus a small classifier or constrained-JSON on the resident model with thinking off. Use low or disabled reasoning effort on easy tasks.

---

## 4. Coding agents

- **Choice:** Claude Code as the primary worker on the local endpoint. The evidence is that Qwen reports its SWE-bench Pro numbers using this harness, and the third-party run above scored 73.81%. OpenCode is the fully open alternative; Pi is the lightweight one.
- **Decision gate:** run a bake-off in Phase 2. Take 20 historical issues from your own repos with tests as the oracle. Score pass rate, wall time and tokens per adapter. If Pi or OpenCode matches Claude Code within about 5 points, switch to the open one.
- **Mechanics:** each task gets `git worktree add` under the agent's work dir on branch `agent/<task-id>`, with a `wip` checkpoint commit every N minutes. The agent never touches the default branch. The workflow loop is plan, edit, test, debug, self-review, then verifier. A separate review pass uses a different model than the author.
- **Permissions:** run the harness in bypass-permissions mode only inside the sandbox (section 7). The sandbox, not the harness, is the boundary.
- **Stop conditions:** acceptance checks pass; budget exhausted; same tool call plus arguments three times; diff size over threshold; or a `needs-human` flag.

---

## 5. Research agents

**Principle:** the LLM never writes a bibliographic entry, and a citation is a database foreign key, not generated text.

**Pipeline**
1. **Discovery:** OpenAlex, Semantic Scholar, arXiv, Crossref, plus a web search layer. OpenAlex needs a free API key for a usable daily budget. For web search, a self-hosted SearXNG is the local default and a paid search API is optional (neither verified this session).
2. **Acquisition and parsing:** prefer arXiv LaTeX or HTML where available (from my own knowledge, not verified). For PDFs, Docling by default. Docling is CPU-viable but scored lower than Marker 2 and MinerU on born-digital PDFs. MinerU adds VLM and OCR backends and supports Apple Silicon. One comparison rates its formula recognition best for scientific papers. MinerU wants at least 16 GB RAM and recommends 32 GB. Run it only in a window with the LLM unloaded. Note MinerU's AGPL license if you ever expose it as a service.
3. **Evidence store:** SQLite tables `sources`, `spans` (page and char offsets), `claims`, `claim_evidence`, `verdicts`, `conflicts`.
4. **Extraction:** the 35B-A3B worker extracts claims, each with a verbatim quote and a `span_id`.
5. **Deterministic gates, before any LLM judge:**
   - the quote must be a normalized substring of the parsed text;
   - the DOI, arXiv ID or title must resolve across Crossref, OpenAlex and Semantic Scholar;
   - retraction flags are checked.

   RefChecker uses the same multi-database cascade across five sources and escalates suspicious cases to a web-search LLM pass. A 2026 audit found hallucinated references surviving peer review at conferences. Reported LLM-judge detection drops sharply in real-world settings (96% to 33% F1 for one model), which is why deterministic checks come first.
6. **Entailment:** the deep 27B, deliberately a different model from the extractor, labels each claim and span as supports, partial, contradicts or unrelated. Only "supports" passes. Related work verifies claims by embedding them and matching against the cited paper's sections, then checks the cited papers' own bibliographies.
7. **Contradictions:** cluster claims by entity and question, run pairwise NLI, and keep both sides in a conflict table with sources.
8. **Synthesis:** every sentence carries claim IDs. A lint step fails the build on untagged factual sentences. Unsupported content is stripped or labeled as inference. Bibliography entries are rendered from Crossref or OpenAlex metadata, never from the model.

---

## 6. Persistent memory

**Start with files and SQLite; add vectors later.**
- **Git-tracked Markdown** under `memory/` is the source of truth: `global/`, `projects/<slug>/{README,decisions/ADR-*,notes}`, `research/<topic>/`, `experiments/<id>/`. It is diffable, rollbackable and human-editable.
- **SQLite (WAL)** holds tasks, runs, events, artifacts and the evidence ledger, with FTS5 over memory and run logs. Lexical search already covers identifiers and error strings well.
- **Write path:** agents propose memory patches into a staging area. Only the Librarian, running deterministic rules plus sampled human review, promotes them to the repo. This blocks memory poisoning.
- **Phase 4 addition:** sqlite-vec plus embeddings, fused with FTS5 by reciprocal rank fusion. One survey recommends exactly this combination and says it works well up to about 100K vectors. That is a secondary claim; your corpus may exceed it. A local example runs Qwen3-Embedding-0.6B at 1024 dimensions with MLX. One benchmark found no embedding model dominates across domains. Run a small eval on your own data before committing. Serve embeddings from oMLX so there is no extra process.
- **Later only if measurements demand it:** a vector index beyond SQLite, or a graph. The evidence ledger already captures most relational structure.

---

## 7. Computer control

**Core stance:** do not give the agent your session. Give it a separate machine identity.

| Capability | Mechanism | Autonomy |
|---|---|---|
| Terminal and filesystem | Dedicated non-admin user `agent`; sandbox-runtime (Seatbelt) per command; read-only project mounts or per-task worktrees | Full inside the sandbox |
| Untrusted code and installs | Apple `container`, one VM per container | Full inside the VM |
| Network | pf rules keyed on the agent UID, forcing egress through an allowlist proxy | Allowlist only |
| Browser | Headless Chromium with a fresh profile, no logins, 1 slot | Read-only research |
| GUI computer-use | Throwaway macOS VM, Phase 8 only | Gated |
| Credentials | Broker process outside the agent's reach | Never exposed |

- **Apple `container`:** runs OCI Linux containers as lightweight VMs on macOS 26+, but stability is only guaranteed within patch versions. Each container gets its own VM. The Virtualization framework lacks ballooning, so VM RAM is a static carve-out. Budget 1.5 to 2 GB each.
- **Seatbelt alone is not enough:** a Seatbelt-only driver blocks writes outside the workspace but does not bound network egress; Anthropic's sandbox-runtime adds an OS-enforced egress allowlist. Use it, and also enforce egress at pf. Verify both layers independently.
- **Project registry:** to work across "any directory", use `agentctl project add <path> --mode ro|worktree`. Projects are exposed as read-only references or as per-task worktrees. Do not mount your home directory or another machine's drive.
- **GUI control:** Qwen reports 84.3 on OSWorld-Verified for the 27B, so GUI agents are plausible. Keep them in a disposable VM with no personal accounts. The VM needs RAM, so run it only in a deep-profile window.

---

## 8. Always-on operation

- **Power:** `sudo pmset -a sleep 0 disksleep 0 displaysleep 0 autorestart 1 womp 1`. The recommended recipe is no system sleep plus automatic restart after power failure. Skip the undocumented `disablesleep` flag; it is not a supported API. A small UPS is worth it.
- **FileVault trade-off:** FileVault stops an unattended machine at pre-boot unlock, and an authenticated restart covers only planned reboots. My recommendation is FileVault off, no auto-login, a password on the operator account, services started by LaunchDaemons with a `UserName` key, and no personal data on the box. That gives crash and power-loss recovery. A thief meets a login window, and the data worth stealing is not there. You can choose differently, at the price of manual unlock after a power cut.
- **Services:** three LaunchDaemons run as root or the service user.
  - `iogpu` sysctl.
  - pf rules.
  - `tailscaled`: the Tailscale SSH server needs the headless daemon, not the menu-bar app.

  A fourth, run as `agentd`, starts oMLX, the supervisor and the proxy. Test that Metal works from a daemon with no GUI session in Phase 1; I could not verify that it does.
- **Crash recovery:** launchd `KeepAlive` brings services back. The supervisor requeues any task whose lease has expired. Coding state lives in git checkpoints and research state in the evidence DB, so a rerun resumes rather than restarts. Durable execution frameworks recover control flow, but LLM steps are non-deterministic, so checkpoints matter more than replay.
- **Health loop** (every 30 s):
  - a one-token generation probe;
  - `memory_pressure` and swap;
  - disk free;
  - external SSD mounted;
  - thermals via `powermetrics`.

  Actions are restart the inference server, drop concurrency, or pause the queue. Heat is a real watch item: reviews saw stable behaviour under repeated load at around 64 C, while one GitHub report recorded about 95 C near the voltage regulators during long LLM runs. Give it airflow.
- **Dead-man:** a root watchdog kills the agent user's processes if the supervisor heartbeat stops. A content-free ping to an external uptime checker tells you when the machine itself is down.

---

## 9. Remote access

- **Transport:** Tailscale only. No port forwarding and never Funnel. `tailscale serve` is the tailnet-only option; Funnel exposes services to the public internet.
- **Policy:** use grants, not legacy ACLs. Tailscale recommends grants for all new policy. Tag the node, allow only your own devices, and use SSH `check` mode. Keep the client current: recent bulletins describe a Services grant that could reach loopback listeners on non-advertised ports, and a missing state directory that skips Tailnet Lock checks. Run `tailscaled` with `--statedir`, bind the dashboard to loopback behind `serve`, and consider Tailnet Lock.
- **Interfaces:**
  - **Dashboard:** a small FastAPI plus htmx app at `https://agent-mini.<tailnet>.ts.net`. It covers queue, runs, log tails, approvals, submit and a red kill button.
  - **Auth:** Tailscale identity headers, plus a passkey for approve and kill actions.
  - **Notifications:** Web Push from the dashboard as the primary channel (a comparable agent dashboard uses the same pattern), with ntfy as backup. Messages contain a task ID and state only, with no content.
  - **Phone terminal:** Tailscale SSH into tmux sessions.
- **Not recommended by default:** third-party chat bots carrying task content, and Claude Code Remote Control. The latter is subscription-tied and routes through a cloud relay. It is fine as an optional convenience if you accept that.

---

## 10. Storage

**Internal 512 GB** (fast, about 6.4 GB/s sequential per the review above [M]): OS and apps, both model files, SQLite and memory (WAL needs fast fsync), active repos and worktrees, container images, and the SSD KV cache. Cap the KV cache at about 30 GB and monitor write volume, since the NAND is soldered.

**External 1 TB, Thunderbolt 4** (practical sequential speed about 2.5 to 3 GB/s [E]; front USB-C ports are limited to 10 Gb/s): cold model library, paper corpus and parsed output, datasets, restic snapshots of DB, memory and audit logs, archived logs. Never put a live database or an active worktree there. Add a mount-check guard to every job that touches it. Keep one encrypted offsite copy of the small, critical set (memory repo, ledger, audit).

---

## Cross-category market matrix

| Category | Best overall | Best for your HW | Best open source | Best lightweight | Best mature | Best cutting-edge | Use |
|---|---|---|---|---|---|---|---|
| Local engine | Splash on supported RAM | oMLX | oMLX / vllm-mlx | mlx-lm server | llama.cpp | Splash | oMLX, llama-server fallback |
| Coding model | GLM-5.3 (cloud-class) | Qwen3.6-35B-A3B (speed) and Qwen3.8-27B (quality) | Qwen3.8-27B | Qwen3.6-35B-A3B | Qwen3.6-27B | Qwen3.8-27B + MTP | Both Qwen models, leased |
| Worker harness | Claude Code / Codex CLI | Pi (smallest prompt) | OpenCode | Pi | Claude Code | Hermes | Claude Code, adapters for Pi/OpenCode |
| Orchestration | Temporal | SQLite queue | Restate | SQLite queue | Temporal | Restate | SQLite lease queue |
| PDF parsing | MinerU (formulas) | Docling | Docling | Docling / pdf text layer | Marker 2 | MinerU VLM | Docling, MinerU on demand |
| Memory | Hybrid SQLite + vectors | SQLite FTS5 | sqlite-vec | Markdown + FTS5 | SQLite | Agent-managed memory | Markdown + SQLite |
| Sandbox | Apple container VMs | Seatbelt + container | sandbox-runtime | Seatbelt | Dedicated OS user | macOS VM | All three layers |
| Remote | Tailscale | Tailscale | Headscale / WireGuard | Tailscale SSH | Tailscale | Web Push dashboard | Tailscale + serve |

---

## A. Recommended technology stack

| Layer | Recommended | Alternatives | Why |
|---|---|---|---|
| Interface | Tailnet dashboard + Web Push; tmux over Tailscale SSH | Telegram bot, Claude Remote Control | Private, content-free notifications |
| Supervisor / policy / audit | Custom Python (uv, asyncio) | Hermes gateway | Owns policy, kill, audit |
| Orchestrator + queue | SQLite lease queue with DAG | Restate, DBOS, Temporal | Single node, no extra service |
| Agents | Claude Code (pinned) adapter, Pi and OpenCode adapters | Hermes, Codex CLI | Evidence-backed with Qwen |
| Model router | In-supervisor router with lease manager | LiteLLM | GPU leasing and sensitivity labels |
| Inference | oMLX | LM Studio headless, llama-server, Splash | Batching, tiered KV cache |
| Models | Qwen3.6-35B-A3B and Qwen3.8-27B, 4-bit | Gemma 4 (reject) | Section 1 |
| Tools | Sandboxed shell, git, Playwright | MCP servers (allowlisted only) | Supply-chain control |
| Memory | Git Markdown + SQLite FTS5 (+ sqlite-vec) | Vector DB, graph | Minimal infrastructure |
| Research | OpenAlex, Semantic Scholar, Crossref, arXiv, Docling/MinerU | Paid search APIs | Deterministic citation verification |

## B. Architecture diagram

```
 PHONE / LAPTOP (tailnet only)
   | HTTPS via tailscale serve (passkey on approve/kill)     | Tailscale SSH -> tmux
   v                                                         v
 +---------------- agent-mini (Mac mini M6 32GB) ------------------------------+
 | LaunchDaemons: pf rules | iogpu wired limit | tailscaled | watchdog         |
 |                                                                              |
 | [agentd user]                                                                |
 |   Dashboard/API --> SUPERVISOR --> POLICY engine --> AUDIT log (hash chain)  |
 |                        |             |                                       |
 |                  SQLite lease queue   +--> Credential BROKER (unix socket)   |
 |                  (tasks, runs, evidence ledger, memory index)                |
 |                        |                                                     |
 |             SCHEDULER (memory-weighted admission, model leases)              |
 |                        |                                                     |
 |   MODEL ROUTER ---> oMLX :8000 (OpenAI + Anthropic API, SSD KV tier)         |
 |       |               one resident LLM: 35B-A3B or 27B  + embedding model     |
 |       +--> optional cloud tier (capped, redacted, label-checked)             |
 |                                                                              |
 | [agent user]  3-4 WORKERS: Claude Code / Pi / OpenCode adapters              |
 |       | sandbox-runtime (Seatbelt)  | Apple container VM | headless browser  |
 |       v                                                                      |
 |   egress: pf (UID rule) --> allowlist proxy :3128 --> internet (logged)      |
 |   worktrees: /Users/agent/work/<project>/<task>   branch agent/<task>        |
 +------------------------------------------------------------------------------+
   Internal SSD: models, DBs, worktrees, KV cache   External SSD: archive, backups
```

## C. Hardware and resource plan

**RAM profiles** (the GPU wired limit starts at 24 GB, so `iogpu.wired_limit_mb=24576`; tune by about 1 GB steps against `memory_pressure`). All figures other than the model weights are [E].

| Component | Worker profile (35B-A3B) | Deep profile (27B) |
|---|---|---|
| macOS + system | 3.5 GB | 3.5 GB |
| Model weights | about 20 GB | 16.1 GB + 1.2 GB draft/MTP |
| Embedding model | 0.5 | 0.5 |
| KV + states + scratch | 3.0 | 4.0 to 5.5 |
| Supervisor, proxy, tailscaled | 0.6 | 0.6 |
| Workers | 3 x 0.4 = 1.2 | 4 x 0.4 = 1.6 |
| Sandbox VMs | 1 x 1.5 | 1 x 1.5 |
| Browser | not concurrent | 1.0 (or a second VM) |
| Headroom / page cache | 1.0 | 1.0 |
| **Total** | **about 31.3 GB** | **about 31 GB** |

The worker profile is at the edge. If `memory_pressure` goes yellow, drop to 2 workers. Swap should stay under about 1 GB sustained.

**Answers to the sizing questions**
- **Ideal sizes:** 27B and 35B-A3B at 4-bit. 8-bit KV. 64K context cap per request, with 128K reserved for sequential research ingest.
- **Concurrency:** one large resident model, 2 decode streams (up to 4 with Splash). No separate small LLM at first; the embedding model is the only always-on small model.
- **Swapping and co-residency:** swapping at batch boundaries is worthwhile. Two large models do not fit together (20 + 16.1 GB).
- **Expected bottlenecks, in order:**
  1. Decode bandwidth.
  2. Cold prefill on the 27B.
  3. RAM headroom.
  4. SSD wear.
  5. Heat.

**Storage plan (internal, about 370 GB planned, about 120 GB unallocated) [E]:** OS and apps 45, toolchains and images 25, models 55, DB and memory 10 (growing), worktrees 80 (APFS-quota volume), KV cache 30, hot logs 5, VM and swap 20, free headroom 100. **External:** model library 150, papers and parsed output 200, datasets 250, backups 300, log archive 50, spare 50.

## D. Agent architecture: 100+ logical agents on one GPU

```
agent_defs   (id, role, prompt_ref@version, toolset, permission_profile,
              model_class, ram_cost_gb, budgets, memory_scopes, output_schema)
tasks        (id, parent_id, objective, acceptance[], state, lease_until,
              attempt, not_before, priority, budget_tokens, budget_wall_s,
              project, sensitivity, idempotency_key)
runs         (id, task_id, agent_id, model, tokens, started, ended, result_ref)
state machine: queued -> leased -> running -> verifying -> done|failed|blocked|cancelled
```

- **Scheduler loop:** pick the highest priority (with aging) task whose `ram_cost_gb` fits the committed budget and whose semaphores are free. Lease it with a heartbeat. On heartbeat loss, requeue with `attempt+1`.
- **Escalation ladder:** worker (35B-A3B), then deep (27B), then cloud tier (if the project label permits), then `needs-human`. Each step needs a recorded failed attempt with a verifier verdict.
- **Experiments:** each experiment is a task with a pinned environment, resource caps, and outputs as artifacts (CSV/Parquet plus metadata JSON) in a content-addressed folder. A separate analysis task reads artifacts only.
- **Documentation:** a Documenter task runs after each merge-ready branch. It updates `docs/` and ADRs in the same branch, then executes every documented command in the sandbox to check that it works.

## E. Model strategy

| Role | Model | Notes |
|---|---|---|
| Planning / decomposition | Qwen3.8-27B | Reasoning medium to xhigh, MTP on, deep lease |
| Coding (routine) | Qwen3.6-35B-A3B | Tests as oracle; thinking on only when needed |
| Coding (hard) / debugging | Qwen3.8-27B | Escalation after failed attempts |
| Research extraction | Qwen3.6-35B-A3B | Prefill-heavy, long documents |
| Verification judge | Qwen3.8-27B | Always a different model from the extractor |
| Summarization | Qwen3.6-35B-A3B, thinking off | Or the embedding model plus extractive methods |
| Classification / routing | Embeddings + classifier, or constrained JSON on the resident model | No extra residency |
| Figures, tables, screenshots | Qwen3.8-27B (multimodal) | No separate VLM |
| Final synthesis | Qwen3.8-27B xhigh; optional cloud polish | Cloud only for non-`local-only` projects |

**Promotion rule:** if the Phase 1 gate shows Splash or MTP sustaining at least 30 tok/s on coding workloads without memory pressure, make the 27B the primary coder and keep the MoE for bulk work.

**Cloud policy**
- Local-only by default.
- Escalate only for stuck tasks, final synthesis, or architecture decisions.
- The router sends minimal redacted context, enforces a hard monthly cap, and refuses any `local-only` project.
- Keys live in the broker. Verify pricing and terms at call time; I did not check pricing this session.
- Open-weight cloud models such as GLM-5.3 are a cheaper tier than frontier closed models for coding escalation, which is worth evaluating against your cap.

## F. 24/7 architecture

Section 8 covers the mechanics. The nightly cycle is:
1. At 22:00 the scheduler switches to the deep profile and drains the hard queue.
2. At 06:00 it swaps back to the worker profile.
3. The supervisor posts a digest to the dashboard.
4. Any approvals are waiting in a queue rather than blocking.

Recovery guarantees:
- A crash or reboot costs at most the work since the last checkpoint.
- A stuck run is killed on budget or loop detection.
- A dead supervisor triggers the dead-man watchdog.

## G. Remote-control architecture

Phone, Tailscale, the dashboard (identity headers plus passkey for approve and kill), Web Push for alerts, and Tailscale SSH into tmux for hands-on work. Emergency stop is available three ways: the dashboard button, `agentctl halt` over SSH, and the dead-man watchdog. Halt sets the HALT flag, stops worker process groups, stops running containers and kills the agent user's processes.

## H. Security architecture

**Principle:** never let one path hold all three of private data, untrusted content and an exfiltration channel. That combination is the pattern behind most prompt-injection findings. A common heuristic is that an unsupervised agent should hold at most two of the three. Recent CVEs show that coding-agent allowlists can themselves be turned into attack surface, so enforce boundaries at the OS and network layers, not inside the harness.

**Agent classes**
- **Researcher:** web access plus untrusted content, with no personal data, no credentials and no repo access. It emits typed artifacts only.
- **Coder:** repo access plus code execution, with network default-deny to package mirrors via the proxy. Anything it fetched from the internet is tainted.
- **Privileged:** git push, installs and credentials. Never autonomous.

**Approval matrix**

| Tier | Operations |
|---|---|
| Fully autonomous | Read allowlisted projects; write inside the task worktree; build and test in sandbox or VM; commit to `agent/*` branches; GET-only fetch via allowlist proxy; stage memory patches; generate docs; spend within per-task budget |
| Needs phone approval | Any `git push` or PR; merge; adding a domain to the allowlist; reading outside the project registry; creating an agent type with new tools; cloud spend above cap; package installs outside the lockfile; extending a run beyond its wall-clock budget; deleting more than N files; loosening a policy |
| Impossible by construction | sudo or root; `~/.ssh`, keychains, browser profiles, Mail/Messages/financial data; force-push or protected-branch writes; editing supervisor code, policy or audit logs; unlisted egress; sending email or messages; disabling the kill switch |

**Controls**
- **Secrets:** the broker holds a repo-scoped deploy key and any cloud API keys. The agent sees only a unix socket. The broker enforces branch prefix and no force-push.
- **Network:** pf rule examples (verify with `pfctl -sr` and a curl test as the agent user; I did not verify UID matching on macOS 27):
  ```
  pass out quick on lo0 proto tcp from any to 127.0.0.1 port { 8000, 3128 } user agent
  block drop out quick from any to any user agent
  ```
  Block UDP 53 for the agent user and let the proxy resolve DNS.
- **Taint tracking:** once a context has ingested external content, the task is tainted. Its writes are restricted to its own output directory and it loses egress beyond what it needs.
- **Supply chain:** pin harness versions, disable auto-update, allowlist MCP servers explicitly, and do not install marketplace skills. A package that shipped fifteen clean versions before adding exfiltration code is documented.
- **Limits:** per-run wall clock (default 4 h), token ceilings, tool-call counts, loop detection, diff caps, APFS quota on the workspace volume, and CPU/RAM limits on VMs [E, tune these].
- **Audit:** an append-only, hash-chained JSONL written by the supervisor into a root-owned directory the agent cannot write, with a periodic copy to the external SSD. It records every tool call, diff, proxy request and approval.

## I. Installation plan

**Phase 0: host prep (operator account)**
```bash
sudo pmset -a sleep 0 disksleep 0 displaysleep 0 autorestart 1 womp 1
# standard (non-admin) users: agentd (supervisor) and agent (workers)
#   via System Settings or `sudo sysadminctl -addUser <name> ...`
brew install uv git gh jq ripgrep tmux tailscale tinyproxy
sudo tailscaled install-system-daemon     # verify against current Tailscale docs
sudo tailscale up --ssh --advertise-tags=tag:agent-host --hostname=agent-mini
```
Apply the grants policy and Tailnet Lock. Install the Apple `container` package from the GitHub releases page and run `container system start`.

**Phase 1: minimal working system**
```bash
# GPU wired limit via LaunchDaemon (com.local.iogpu-wired-limit.plist)
# ProgramArguments: /usr/sbin/sysctl iogpu.wired_limit_mb=24576
brew tap jundot/omlx https://github.com/jundot/omlx && brew install omlx
omlx serve --model-dir ~/models --paged-ssd-cache-dir ~/.omlx/cache --max-concurrent-requests 2
# models (verify repo IDs): mlx-community/Qwen3.8-27B-4bit, a Qwen3.6-35B-A3B 4-bit MLX build
```
Run the engine as a LaunchDaemon with `UserName`, not `brew services`, so it starts without a GUI login.

*Gates (all must pass before Phase 2):*
- **G1:** Metal works from a daemon with no GUI session.
- **G2:** oMLX runs on M6 with macOS 27.
- **G3:** tok/s and TTFT on your repos for both models, with and without MTP, and with Splash if it starts.
- **G4:** the 35B-A3B KV per token from its `config.json`.
- **G5:** prefix caching actually hits across turns in Claude Code with the attribution header disabled.
- **G6:** tool-call accuracy at 4-bit versus 3-bit on 100 of your own tool-call traces.
- **G7:** `memory_pressure` stays green under 2 streams.

*Failure modes:* Metal OOM; chat-template or tool-parser mismatches (use the `qwen3_coder` tool parser and the Qwen reasoning parser); runaway thinking loops. *Rollback:* `brew bundle` file in git; delete the plist and run `sudo sysctl iogpu.wired_limit_mb=0`.

**Phase 2: autonomous coding**
Install Claude Code (`curl -fsSL https://claude.ai/install.sh | bash` or the Homebrew cask), then set `ANTHROPIC_BASE_URL=http://127.0.0.1:8000`, `ANTHROPIC_AUTH_TOKEN=local` and `CLAUDE_CODE_ATTRIBUTION_HEADER=0`. Disable auto-update and telemetry (variable names unverified; check the docs). Build the supervisor skeleton (SQLite schema from D, lease loop, worktree manager) and the bake-off harness. Install `@anthropic-ai/sandbox-runtime`, and a Pi adapter (package scope may have moved to `@earendil-works`; verify). *Test:* the 20-issue bake-off. *Failure modes:* prompt-cache misses; subagent features that rely on cloud models. *Rollback:* adapters are interchangeable.

**Phase 3: research agents**
`uv pip install docling` (and `"mineru[all]"` for the on-demand path), set an OpenAlex key, and implement the ledger, quote-substring gate, resolver cascade, and an entailment pass using the 27B. *Test:* seed 30 fabricated and 30 real citations; require 100% catch on fabrications and no false rejects among real ones. *Failure modes:* paywalled PDFs, parse errors on equations, API rate limits.

**Phase 4: memory**
Set up the Git memory repo, the Librarian and the FTS5 index. Then add sqlite-vec and the embedding model, with RRF. *Test:* retrieval hit rate on 50 held-out questions about past tasks. *Rollback:* `git revert` on the memory repo.

**Phase 5: multi-agent orchestration**
Implement memory-weighted admission, semaphores, the Planner, the Verifier, the escalation ladder and model leases. *Test:* a 40-task DAG overnight; confirm no memory-pressure events and correct requeue after a forced kill.

**Phase 6: 24/7 operation**
Run the supervisor, proxy and inference as LaunchDaemons; add the health loop and dead-man watchdog; add the external uptime ping. *Test:* kill -9 each service, pull the power cable, and reboot with a running queue.

**Phase 7: remote access**
Build the dashboard, serve it through `tailscale serve`, and add the passkey, Web Push and the halt endpoints. *Test:* approve and kill from a phone off your home network.

**Phase 8: optimization**
Adopt Splash if gate G3 shows it is stable on 32 GB; enable KV quantization where it helps; tune per-project prefix pinning; optionally LoRA-tune the judge or router (mlx-lm supports LoRA and QLoRA); and consider the GUI VM.

**Phase 1 gates in one line:** do not proceed past a phase whose exit tests have not passed.

## J. What NOT to install
- **OpenClaw:** CVE history and the malicious-skills record (section 2).
- **Ollama as the primary engine:** slower in the vendor's comparison and gated on more RAM for its MLX path.
- **Agent frameworks as the control plane (LangGraph, CrewAI, AutoGen):** I did not evaluate them in this pass, but nothing I found shows they help on a single bandwidth-bound GPU, and a thin supervisor already does what you need.
- **Temporal, Hatchet, Kubernetes, Docker Desktop:** Temporal needs a split server-and-worker architecture, and Hatchet adds a service you will not use on one node. Docker Desktop duplicates the VM layer.
- **Vector DB servers and graph memory (Qdrant, Milvus, pgvector, Neo4j, Letta, mem0):** unjustified at this scale.
- **Open WebUI and similar chat front ends:** extra attack surface; the dashboard covers your needs.
- **Gemma 4 26B-A4B as a coding model, and any 70B-class dense model:** do not fit or underperform.
- **Marketplace skills, unvetted MCP servers:** supply-chain risk.
- **`--dangerously-skip-permissions` outside the sandbox, Tailscale Funnel, router port forwards:** self-explanatory.
- **Claude Code Remote Control as the only remote path:** subscription-tied cloud relay.

## K. Upgrade path

- **M5 Pro Mac mini (24 to 64 GB):** starts at $1,699 and goes up to 64 GB. It has Thunderbolt 5. Its bandwidth is 307 GB/s, about 1.8x yours, which directly raises decode speed for dense models. If you are still inside a return window and decode-bound, that is the single highest-leverage hardware change.
- **64 GB:** both models co-resident, the 27B at 6-bit, and no lease swapping.
- **96 to 128 GB (Mac Studio):** Mac Studio M5 Max starts at $2,499 with up to 128 GB. Much larger MoE models become viable.
- **Dedicated NVIDIA GPU or server:** vLLM publishes recipes for Qwen3.8-27B on a single Blackwell GPU. Keep the Mac as the control plane (supervisor, memory, browser, sandboxes), and point the model router at the GPU box over Tailscale. The router abstraction means no other layer changes.

---

## Sources

P = primary, S = secondary.

- Apple M6 overview (S): https://en.wikipedia.org/wiki/Apple_M6
- M6 launch coverage (S): https://appleinsider.com/articles/26/08/25/m6-mac-mini-arrives-in-ram-and-ssd-constrained-environment ; https://9to5mac.com/2026/08/25/apple-announces-new-mac-mini-heres-everything-new/
- M6 review, ports and storage (S): https://appleinsider.com/articles/26/10/02/m6-mac-mini-review-excellent-hardware-badly-hampered-by-too-small-ssd ; https://everymac.com/systems/apple/mac_mini/mac-mini-silicon-faq/mac-mini-silicon-external-thunderbolt-usb-storage-options.html ; https://www.macworld.com/article/2964754/2026-mac-mini-m5-pro-design-specs-release-date.html
- M6 LLM measurements (S): https://note.com/thegadget/n/ne16cddf6d40d?hl=en ; https://daily.dev/posts/mac-mini-m6-first-look-qwen3-8-27b-hits-53-tps-locally-eqglitifc (the underlying GitHub benchmark repo was not fetched)
- Splash engine (P, vendor benchmarks): https://inco.ai/blog/splash/ ; https://lmstudio.ai/blog/splash-engine
- Qwen3.8-27B (P mirror of model card): https://lmstudio.ai/models/qwen3.8 ; config: https://huggingface.co/Qwen/Qwen3.8-27B/blob/main/config.json ; serving: https://lmsysorg.mintlify.app/cookbook/autoregressive/Qwen/Qwen3.8-27B ; https://recipes.vllm.ai/Qwen/Qwen3.8-27B
- KV cache math (S): https://dev.to/purpledoubled/run-qwen-38-27b-locally-real-gguf-sizes-the-kv-cache-trick-and-the-template-trap-114j
- Qwen3.6-35B-A3B (P): https://qwen.ai/blog?id=qwen3.6-35b-a3b ; comparison gist (S): https://gist.github.com/hungson175/61a805368649c225026a69adf2ad87e0
- Terminal-Bench subset on Claude Code (S): https://huggingface.co/RadixArk/Qwen3.8-27B-NVFP4
- Inference engines: oMLX (P): https://github.com/jundot/omlx ; vllm-metal (P): https://vllm.ai/blog/2026-09-22-vllm-metal-v0-28-0 ; vllm-mlx (P): https://github.com/waybarrios/vllm-mlx ; LM Studio engine (P): https://lmstudio.ai/blog/mlx-engine-agentic-workloads ; LM Studio 0.4 (S): https://insiderllm.com/guides/lm-studio-tips-and-tricks/ ; MLX vs llama.cpp (S): https://yage.ai/share/mlx-apple-silicon-en-20260331.html
- GPU wired limit: MLX docs (P): https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.set_wired_limit.html ; defaults (S): https://github.com/ivanopcode/devnote-override-macos-metal-vram-cap ; https://localaimaster.com/mac/best-llm-32gb-mac
- Harnesses: Hermes (P): https://github.com/nousresearch/hermes-agent ; https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation ; Pi (S/P): https://www.npmjs.com/package/@mariozechner/pi-coding-agent ; https://www.eesel.ai/blog/pi-coding-agent ; OpenClaw security (S): https://www.theaienterprise.io/p/self-host-your-own-ai-agent ; agent landscape (S): https://pinggy.io/blog/best_open_source_cli_coding_agents/ ; https://www.morphllm.com/ai-coding-agent
- Claude Code docs (P): https://code.claude.com/docs/en/overview ; local endpoint setup (S): https://gist.github.com/renezander030/39249215616a095d74fe6c66b0348641 ; https://jonathansblog.co.uk/using-claude-code-with-local-llm-models-the-complete-guide
- Sandboxing: Apple container (P): https://github.com/apple/container ; one VM per container (S): https://thenewstack.io/apple-containers-on-macos-a-technical-comparison-with-docker/ ; ballooning (S): https://linuxsecurity.com/news/vendors-products/apples-native-macos-container-tool ; sandbox-runtime egress (S): https://pypi.org/project/boundary-envelope/
- Prompt-injection security (S): https://www.sysdig.com/learn-cloud-native/prompt-injection ; https://www.helpnetsecurity.com/2026/06/11/owasp-prompt-injection-ai-security-failures/ ; https://dev.to/sagar_jain4010/the-lethal-trifecta-securing-ai-agents-against-prompt-injection-29a
- Citation verification: RefChecker (P): https://github.com/markrussinovich/refchecker ; papers (P): https://arxiv.org/pdf/2604.03173 ; https://arxiv.org/pdf/2604.08501 ; https://arxiv.org/pdf/2607.00738
- PDF parsing: MinerU (S mirror): https://github.com/gogelabs/mineru ; comparison (S): https://builderai.tools/blog/pdf-parsing-for-rag-mineru-docling-marker-compared
- Memory (S): https://github.com/NousResearch/hermes-agent/issues/844 ; https://pypi.org/project/kbx/ ; https://arxiv.org/html/2604.15484v1
- Always-on and remote: headless Mac setup (S): https://servey.in/blog/headless-mac-mini-setup ; https://github.com/jnovack/cloudkey/wiki/macOS-AutoSSH ; Tailscale bulletins (P): https://tailscale.com/security-bulletins ; grants (P): https://tailscale.com/s/acl-format ; `tailscale serve` dashboard (S): https://github.com/AltanS/collie/wiki ; Tailscale on macOS (S): https://github.com/Scarletbobcat/dotfiles
- Durable execution (S): https://www.pandastack.ai/blog/best-durable-execution-platforms-2026/ ; Hatchet (P): https://pkg.go.dev/github.com/hatchet-dev/hatchet@v0.108.0

**Not verified this session and flagged inline:** the HDZucht benchmark repo contents, Splash behaviour on 32 GB, oMLX on M6, Metal under a no-GUI daemon, pf UID matching on macOS 27, exact Pi package name and flags, exact Hugging Face repo IDs, Claude Code environment-variable names for telemetry and updates, cloud pricing, and the 35B-A3B KV per token.

## Reasoning trace (not shown to raters)

Claude responded: Starting with the hardware, since the "M6 Mac mini" premise determines everything downstream.
Starting a large-scale research task on the request.
Starting a large-scale research task on the request.

Starting with the hardware, since the “M6 Mac mini” premise determines everything downstream.

Searched the web, read 5 pages

Searched the web, read 5 pages






4 hours ago

## Run notes

claude.ai incognito chat (no history or memory), model menu Sonnet 5.5, Effort High; the menu showed
"Sonnet 5.5 High". Connectors were switched off in the composer menu; the composer has no web-search
switch, and Claude searched the web by itself. Send time 2026-10-14T02:42:59.244Z (browser clock, read right after
sending). Chat: https://claude.ai/chat/e043bc92-664d-4ed9-a24d-32431bd2df78?incognito (incognito chats are not kept in history).
Operated by the assistant (Claude, via the Claude in Chrome extension) in the author's signed-in browser,
at the author's request; the runs were opened in separate tabs and sent in manifest order without waiting
for earlier answers. The app turns long pastes into an attachment, so the prompt was inserted as plain
text in eight line-aligned pieces from one clipboard paste and checked against the original (1,782 words,
same text) before sending. Answer copied with the app's Copy button (it includes any short lines the model
wrote before its searches) and written verbatim from the clipboard; the reasoning trace is the visible
process panel (step summaries and search queries) copied from the page text.
During generation the app paused with "Claude wants to fetch a web page". The author chose "Allow
once" and the assistant clicked it about four hours later (the session had paused); the answer then
finished. The other runs read web pages without asking.
