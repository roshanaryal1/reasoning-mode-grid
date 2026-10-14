---
run_id: claude__fast__p1-v1__r5
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
replicate: 5
date_stamped: '2026-10-14T02:43:35+00:00'
date_run: '2026-10-14T02:43:35+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

Starting with hardware verification, since everything else depends on it.

Hardware confirmed. Date note: your brief says Aug 31, but the system date is Oct 14, 2026, and the M6 mini only shipped Sept 22, so I'm using Oct 14. Next: current models and runtimes.

**Model:** Claude Sonnet 5.5 (Anthropic). **Knowledge cutoff:** end of June 2026. **Browsing:** ON, 8 standard-mode searches, no page fetches. I verified hardware, the Qwen3.6 lineup, MLX server options, coding-agent landscape, Hermes/OpenClaw, and VM sandboxing. Items tagged [UNVERIFIED] come from prior knowledge or my own arithmetic and need a check before you rely on them. I am made by Anthropic, so discount any cloud lean toward Anthropic. I recommend provider-agnostic routing for that reason.

**Date discrepancy:** your brief says Aug 31, 2026, but the system date is Oct 14, 2026. The M6 mini only shipped Sept 22, so I used Oct 14.

---

## Decisions at a glance

| Layer | Pick | Confidence |
|---|---|---|
| Hardware reality | M6 mini, 32 GB, 170 GB/s. Decode is bandwidth-bound, so the MoE class wins | High |
| Inference server | llama.cpp `llama-server` (production). Benchmark oMLX in Phase 8 | Medium |
| Primary model | Qwen3.6-35B-A3B at a ~4-bit quant that leaves KV headroom | Medium (quant needs an eval) |
| Escalation model | Qwen3.6-27B dense, swapped in on demand | Medium |
| Orchestrator | Thin custom Python service on SQLite (WAL), supervised by launchd | High |
| Coding worker | OpenCode or Pi headless in sandbox, chosen by bake-off | Medium |
| Research worker | Custom loop over a verbatim-evidence store | High |
| Memory | Markdown in git + SQLite (FTS5 + sqlite-vec) | High |
| Sandbox | Colima/Lima Linux VM (vz) for workers, Lume macOS VM only if GUI is needed | Medium-high |
| Remote | Tailscale + SSH + outbound-only Telegram bot | Medium-high |
| Cloud | Optional escalation via a router, off by default | n/a |

---

## 1. Local inference

**Hardware facts.** The M6 mini has a 12-core CPU, 12-core GPU, 170 GB/s bandwidth, Wi-Fi 7 and 2.5 GbE. Bandwidth depends on RAM tier: 16 GB gets 153 GB/s, while 24 and 32 GB get 170 GB/s. You are on the 170 GB/s tier. It has three Thunderbolt 4 ports, not Thunderbolt 5, so no Thunderbolt 5 clustering. The GPU has Neural Accelerators in each core. Apple claims up to 4.8x faster prompt processing than M4 in LM Studio (vendor claim). That helps prefill, not decode.

**Challenge to one source.** OWC says 170 GB/s only suits 7B-8B models. That conflates "fits" with "fast enough." Dense decode is bandwidth-bound (tokens/s is roughly bandwidth divided by bytes read per token), but a MoE reads only its active experts. A 3B-active model reads about 1.7 GB per token at ~4.5 bits, so it is the right class for this chip.

**Models verified.** Qwen3.6 is the current open-weight Qwen line. Qwen3.6-35B-A3B arrived April 16 and the 27B dense on April 22, both open-weight, following Qwen3.5 in February. The 35B-A3B is Apache 2.0, activates 3B parameters per token, and is reported at 73.4 on SWE-bench Verified and 51.5 on Terminal-Bench 2.0. Treat those as vendor-reported, from an unquantized model on an unknown scaffold. They will not transfer cleanly to a 4-bit quant on 32 GB. Other candidates from secondary guides: Gemma 4 31B and gpt-oss-20b. Include both in the bake-off, but I would not choose them without data.

**Fit arithmetic (my estimates, [UNVERIFIED]).**
- 35B-A3B at ~4.8 bits per weight is about 21 GB of weights. A calculator site claims 30.7 GB for Q4_K_M, which disagrees with that arithmetic. Check the actual GGUF file size before planning around either number.
- A comparable M4 32 GB mini was assessed at about 23 GB usable for the GPU by default. You can raise this with `iogpu.wired_limit_mb`, but it resets on reboot and needs a launchd job.
- 27B dense at Q4 is about 16-17 GB. Its theoretical decode ceiling is 170/16.5, about 10 tok/s, so expect 6-9 in practice.
- 35B-A3B extrapolation: an M3 Max (400 GB/s) logged about 70 tok/s decode at 1k context, falling to 41 at 32k and 11 at 128k. Scaling by bandwidth with a lower-bit quant suggests **25-50 tok/s single-stream on M6, degrading with context**. This is not a measurement. Benchmark it on day 1.

**Runtime choice.**
- One comparison recommends llama.cpp Metal at 32 GB or less, and notes Ollama's MLX preview requires more than 32 GB. That source is secondary, but it matches the failure mode I would expect on a tight-memory box: GGUF quant granularity and layer-offload flexibility matter more than MLX's peak speed.
- oMLX is an Apache 2.0 server with continuous batching and a two-tier (RAM plus SSD) KV cache that survives restarts. It is about 2 months old (~11.6k stars at the time of that listing), so it is young. Its SSD KV cache directly suits long agent contexts with shared prefixes. vllm-mlx offers similar features with multi-model residency.
- **Ship llama-server. Trial oMLX in Phase 8** against it with identical weights and a recorded agent-trace replay.

**Concurrency.** oMLX's published batching numbers on a 35B-A3B show 4 concurrent streams give about 1.8x aggregate throughput, and 8 give about 2.3x. Per-stream speed drops, so the sweet spot is 2-4 slots.

---

## 2. Agent runtimes / harnesses

| Option | Verdict |
|---|---|
| OpenCode: MIT, ~165k stars, provider-agnostic, local models | Best open-source general harness. Open-weight local results are mixed in practice. |
| Pi | Minimal, scriptable, local-friendly. Probably lower prompt overhead, which matters at hundreds to low thousands of prefill tok/s. [UNVERIFIED] |
| Aider | Most mature, git-native, weak as an unattended long-horizon loop |
| Goose | ~46k stars, Linux Foundation, general MCP agent. Broad, not coding-optimal |
| Cline CLI 2.0 | Headless and parallel execution plus subagents with their own contexts since Feb 2026. Credible |
| Hermes Agent | Parent-subagent model, internal cron, FTS5-searchable memory, 7 execution backends, local model support, and a rapidly growing user base. Personal-assistant shaped |
| OpenClaw | A January 2026 audit reported 512 vulnerabilities, 8 critical. Gateway-first. Avoid as the trust boundary |

**Decision: custom thin orchestrator plus existing agents as workers.** The 24/7 control plane must be deterministic: queue, leases, budgets, retries, kill switch. An LLM-driven scheduler on a 3B-active model will drift over 8 hours. The agent loops inside tasks are the commodity part. Run workers headless inside the sandbox.

Run a **bake-off before standardizing**: 30 tasks from your own repos, the same model and quant, across OpenCode, Pi, and Cline CLI. Score pass@1, tokens per task, and loop-abort rate. This is the single most decision-relevant experiment, and no public benchmark substitutes for it.

Hermes is worth a trial for the interface/cron/memory role, but I would not make its self-modifying skill loop part of an unattended trust boundary.

---

## 3. Multi-agent architecture

Separate four things:

1. **Agent definition**: a row (role, system prompt, tool allowlist, permission profile, model tier, budget). 100 or 1,000 of these cost zero RAM.
2. **Task**: a row in the queue. A logical agent exists only while a task is leased to it.
3. **Worker**: a process or container executing the loop. Mostly waiting on tools (tests, builds, network).
4. **Inference slot**: the scarce resource. There is exactly one weight copy resident, with 2-4 parallel sequences.

**100 simultaneous model instances is wrong on this machine.** Weights are about 18-21 GB and memory-bandwidth-bound, so a second copy cannot fit and would not add throughput. One resident model with continuous batching reads the weights once per step for all sequences. That is the actual throughput lever.

**Highest-throughput design:**
- A coordinator/worker hierarchy at depth 2 (planner, then workers). Deeper swarms multiply tokens and error compounding with no capacity gain on this hardware.
- The scheduler groups runnable tasks by model tier and fills slots. Tool-wait time on one task is inference time for another. Expect 6-10 concurrent worker containers sharing 2-4 inference slots.
- Dynamic agent creation: the planner emits an agent spec as JSON validated against a schema (tools drawn only from an allowlist, permission profile may not exceed the parent's). New specs are stored and reusable, and the planner cannot grant itself new capability.
- Sequential beats parallel when tasks touch the same files. Use git worktrees per task and rebase at merge time.

---

## 4. Coding agents

For your machine, the bottleneck is local-model reliability over long loops, not harness features. Preference: OpenCode or Pi (provider-agnostic, headless), with Cline CLI as the fallback if its parallel/subagent mode wins the bake-off. Claude Code, Codex CLI and similar are excellent but cloud-bound. Codex CLI is open source and tuned for OpenAI models. Use cloud-bound agents only as optional escalation, never as the default, because you require operation without mandatory cloud.

Harness features that matter for local models: short system prompt, compact tool schemas, prefix-stable prompts (so the KV prefix cache hits), explicit test-run tool, bounded output truncation, and a loop-detector. Build the loop detector into your orchestrator rather than trusting the harness.

---

## 5. Research agents

**Anti-hallucination architecture (evidence-first):**
1. **Evidence store** (SQLite): `source(id, url/doi, fetched_at, content_hash, raw_text_path)`, `span(id, source_id, start, end, verbatim_text)`.
2. Extraction agents write only spans, copied verbatim from stored text.
3. The writer may cite **only span IDs**. Free-text citations are rejected by a post-processor.
4. **Mechanical verifier**: every quoted span must substring-match the stored source. Fails are dropped.
5. **Semantic verifier**: a separate pass checks entailment (claim vs span). A weaker model can do this, but it must not be the same sampled context as the writer.
6. **Bibliographic verifier**: every DOI/arXiv ID resolves against Crossref/OpenAlex/Semantic Scholar/arXiv APIs, and title and authors must match. [UNVERIFIED current API limits.]
7. **Contradiction pass**: cluster claims by embedding, flag opposing-polarity pairs for adjudication.

Tooling [UNVERIFIED this session]: self-hosted SearXNG for search, Playwright or trafilatura for fetch, Docling or PyMuPDF4LLM for PDFs, OpenAlex plus arXiv for literature. Prefer local PDF parsing; only fall back to a cloud parser if layout-heavy PDFs fail.

---

## 6. Persistent memory

Start with two things only:
- **Markdown in a git repo** (`memory/global/`, `memory/projects/<name>/`): decisions, conventions, lessons. Human-readable, diffable, rollbackable.
- **SQLite**: tasks, events, evidence, run logs, with FTS5 for keyword search and `sqlite-vec` for embeddings (~0.5-1 GB resident embedding model). One DB file, no server.

Add later only if measured retrieval failure justifies it: a graph layer (entities/relations as SQLite tables first, not Neo4j), episodic summarization jobs, and cross-encoder reranking. Skip vector DB servers (Qdrant, Weaviate, Chroma-as-a-service). At your scale (<10M chunks) sqlite-vec is sufficient. Memory writes should go through a curator step with provenance (task id, timestamp) so bad memories can be revoked. Unreviewed self-written memory is how agents accumulate stale beliefs.

---

## 7. Computer control and sandboxing

**Principle: the agent box holds no personal secrets, and workers never touch the host user.**

- **Host layer:** a dedicated non-admin macOS user `agent`. Your personal account is separate, with FileVault and your keychain.
- **Worker layer:** workers run in a Linux VM. Cloister (a wrapper over Colima for Linux and Lume for macOS VMs) describes VM isolation as stronger than Docker because it has a separate kernel, services in the VM are unreachable from the host unless tunneled, and there is an instant stop. I would use Colima/Lima directly (fewer moving parts) and treat Cloister as optional.
- **GUI/computer-use:** Lume gives near-native macOS/Linux VMs on Apple Silicon, and the Cua framework lets agents see and drive the desktop inside them. Use this for any app control. Do not give a model GUI control of the host desktop.
- **Network:** egress through an allowlist proxy; the VM reaches the host's inference port only.
- **Your "any directory" requirement:** satisfy it with read-only virtiofs mounts of selected host directories plus bare-mirror clones. Writes go to `agent/*` worktrees and come back as patches or PRs. Truly unrestricted host write access is the one thing I would not grant.
- **Metal is unavailable inside VMs**, so inference stays on the host, bound to localhost/bridge only.

---

## 8. Always-on operation

- `sudo pmset -a sleep 0 disksleep 0 displaysleep 0 autorestart 1 womp 1` (verify flags on macOS 27).
- LaunchDaemons (system domain, `UserName=agent`) with `KeepAlive` and `ThrottleInterval`: inference server, orchestrator, SearXNG, embedding service, Colima VM start.
- **FileVault tradeoff:** with FileVault on, a power cut leaves the machine at the unlock screen until you physically unlock it, which defeats unattended recovery. Because this box holds no personal secrets by design, I would run it with FileVault off and encrypt the external SSD (APFS encrypted, key in the agent keychain). If your threat model includes physical theft, reverse this and accept manual unlock after outages.
- **Crash recovery:** tasks carry leases with heartbeats (60s). An expired lease returns the task to `queued` with `attempt+1`. Tasks must be idempotent (worktree reset to the base commit on retry). Dead-letter after 3 attempts.
- **Watchdog:** a tiny separate launchd job checks inference `/health`, orchestrator heartbeat, memory pressure, disk free, SSD mounted, and escalates via Telegram. It must not depend on the orchestrator or any LLM.
- Reapply the GPU wired-limit sysctl at boot via a launchd job.

---

## 9. Remote access

- **Tailscale** (no inbound ports, WireGuard-based) with ACLs allowing only your phone and laptop to reach the mini. [UNVERIFIED current feature set.] `tailscale serve` for a status dashboard on the tailnet only. SSH over tailnet for full control.
- **Notifications and approvals:** a small Telegram bot using outbound long-polling, so no webhooks and no public endpoint. Messages carry task id and a diff summary, with inline Approve/Deny buttons. Allowlist your numeric Telegram user ID, and require a short-lived signed token for approvals. Alternative: self-hosted ntfy over tailnet for notifications only.
- **Emergency stop:** `/stop` in Telegram, `ssh mini ./kill-all`, and a `KILL` file the orchestrator polls every loop. Optionally a smart plug for hard power-off.
- Hermes/OpenClaw-class agents become a risk if exposed on a public network. That applies to anything you build too.

---

## 10. Storage architecture

| Location | Contents | Why |
|---|---|---|
| Internal 512 GB | macOS and apps (~60), hot models (35B-A3B ~19 GB, 27B ~17 GB, embedder ~1), SQLite DBs and WAL, memory repo, active worktrees, oMLX/llama KV cache, logs (current) | Low latency, no unplug risk, fsync-safe |
| External 1 TB | Cold model library, paper PDFs, datasets, bare git mirrors, Colima disk image if large, log archive, nightly snapshots | Bulk, sequential access. TB4 NVMe at ~2 GB/s loads a 20 GB model in ~10 s |

Never put SQLite WAL files on the external drive (fsync latency, unmount corruption). Back up with a nightly `sqlite3 .backup` plus `git bundle` to the external disk, and keep one offline copy off-box, because the external disk sharing the same desk is not a backup strategy.

---

## A. Technology stack

| Layer | Recommended | Alternatives | Why |
|---|---|---|---|
| Inference | llama.cpp server | oMLX, vllm-mlx, LM Studio | Mature, parallel slots, tool-call templates, quant flexibility at 32 GB |
| Models | Qwen3.6-35B-A3B + 27B dense | Gemma 4 31B, gpt-oss-20b | MoE decode economics |
| Orchestrator | Custom Python + SQLite | Temporal, Prefect, LangGraph | Deterministic, zero infra |
| Coding worker | OpenCode or Pi | Cline CLI, Aider, Goose | Bake-off decides |
| Sandbox | Colima (vz) Linux VM | Lume, Cloister, Docker Desktop | Separate kernel, simple |
| Search/fetch | SearXNG, Playwright | Brave API | Local and free |
| Memory | Markdown + SQLite/FTS5/sqlite-vec | Mem0, Honcho, graph DBs | Minimal |
| Remote | Tailscale + Telegram bot | WireGuard, Cloudflare Tunnel | No inbound exposure |
| Supervision | launchd + watchdog | supervisord | Native, boot-safe |

**Category-by-category summary** (best overall / this hardware / OSS / lightest / most mature / cutting edge / what I'd use):

| Category | Overall | This HW | OSS | Light | Mature | Cutting edge | Use |
|---|---|---|---|---|---|---|---|
| Inference | vLLM (GPU servers) | llama.cpp or oMLX | llama.cpp | llama.cpp | llama.cpp | oMLX | llama-server |
| Coding harness | Claude Code (cloud) | OpenCode/Pi | OpenCode | Pi | Aider | Cline CLI 2.0 | bake-off |
| Agent platform | Hermes (assistant role) | custom | Hermes | Pi | Aider | Hermes | custom |
| Memory | Postgres+pgvector | SQLite | SQLite | markdown | SQLite | graph layers | SQLite |

---

## B. Architecture diagram

```
 Phone/Laptop ── Tailscale ──┬─ SSH / tmux
                              ├─ Dashboard (tailscale serve)
 Telegram (outbound only) ────┘
        │  approvals / status / stop
 ┌──────▼──────────────── macOS host, user "agent" ─────────────────┐
 │ launchd ► watchdog (no LLM)                                      │
 │ launchd ► Orchestrator (Python)                                  │
 │    SQLite: tasks, leases, budgets, evidence, events, memory idx  │
 │    Scheduler: priority + model-tier batching, kill-file check    │
 │    Policy engine: approval matrix, egress rules, budget caps     │
 │ launchd ► llama-server :8080 (127.0.0.1)  1 model, 2-4 slots     │
 │ launchd ► embedder, SearXNG                                      │
 │ ┌── Colima VM (4 GB cap) ───────────────────────────────────┐    │
 │ │ N worker containers (coding / research / docs agents)     │    │
 │ │ read-only mounts + agent/* worktrees; allowlist proxy     │    │
 │ └───────────────────────────────────────────────────────────┘    │
 └────────────── internal SSD (hot) │ external SSD (cold/backups) ──┘
```

---

## C. Hardware/resource plan (32 GB)

| Consumer | GB |
|---|---|
| macOS + daemons (headless) | 3.5 |
| Colima VM (workers, headless browser) | 4.0 |
| Orchestrator, SQLite, embedder, SearXNG | 1.5 |
| Model weights (35B-A3B at ~4-bit, ~18.5) | 18.5 |
| KV cache + compute buffers (2 slots x 64k) | 2.5 |
| Page cache / headroom | 2.0 |
| **Total** | **32.0** |

This is tight. The KV figure assumes Qwen3.6's hybrid attention keeps KV small, [UNVERIFIED], and 2 slots at 64k is conservative. If memory pressure turns yellow under load, drop to Q3-class weights or reduce slots. Model swapping is worthwhile because loading 17 GB from internal NVMe takes seconds. Do not keep two large models co-resident. Expected bottlenecks: decode bandwidth, then context growth (decode falls steeply by 64k+), then RAM headroom.

Storage: internal ~120 GB used steady-state; external ~300-600 GB depending on datasets.

---

## D. 100+ logical agents without 100 LLMs

Agents are rows in `agent_defs`. A planner decomposes an objective into a DAG of tasks, each referencing an agent def. The scheduler leases up to 6-10 tasks to worker containers. Workers call the single inference endpoint. The server batches 2-4 sequences. Everything else queues. The 100th agent costs nothing until it has a runnable task, and throughput is capped by one weight read per decode step shared across sequences.

---

## E. Model strategy

| Role | Model / mode |
|---|---|
| Planning | 27B dense, thinking on (swap in), or 35B-A3B thinking |
| Coding | 35B-A3B |
| Debugging | 35B-A3B thinking; escalate to 27B after 2 failed iterations |
| Research extraction/summarization | 35B-A3B non-thinking, batched 4 wide |
| Classification/routing | Rules first, then the same model with JSON-constrained output |
| Final synthesis | 27B dense or optional cloud |
| Embeddings | Small dedicated embedder (e.g. a ~0.6B model), pick by retrieval eval |

Before committing: run the 35B-A3B at two quants and the 27B on your 30-task set, and choose by pass rate per hour, not per token.

---

## F. 24/7 architecture

Queue persisted in SQLite; leases and heartbeats; idempotent task restarts; a nightly "wake" cron that enqueues standing jobs (repo triage, research follow-ups); stop conditions per objective (max tasks, max wall time, max tokens, success predicate). A morning digest is sent over Telegram. A power-loss test (pull the plug mid-task) is a Phase 6 exit criterion.

---

## G. Remote-control architecture

Phone to Telegram (outbound bot) for status, task submission, approvals, stop. Phone/laptop to Tailscale to SSH or the dashboard for logs and deeper control. No public ports, no inbound webhooks.

---

## H. Security architecture

**Approval matrix**

| Fully autonomous | Requires approval | Hard-denied |
|---|---|---|
| Read mounted dirs; edit in worktrees; run tests in the VM | Merge to main | Credential stores, keychain, personal docs, finance |
| Commit/push to `agent/*` branches | New dependency with install scripts | Force-push, branch-protection changes |
| Allowlisted web GET and search | Egress to a non-allowlisted domain | Disabling logs, kill switch, or policy |
| Draft PRs | Any POST or form submission to external sites | Host-side sudo |
| Pinned installs (`--ignore-scripts` default) | Sending any message or email; spending money | |
| | Diff over ~1500 LOC or deleting 50+ files | |
| | Edits to agent definitions, policy, or orchestrator (self-modification) | |
| | Sending private project content to cloud APIs | |

**Controls:** per-task caps (e.g. 90 min wall, 400 tool calls, 2M tokens), a nightly token ceiling, and loop detection (same tool+args hash 3x aborts). Immutable append-only audit log (JSONL plus hash chain). Secrets stay on the host in a broker, which injects scoped fine-grained tokens per call. The model never sees them. Branch protection on remotes. Treat all fetched web content and repo files as untrusted input that cannot grant permissions, since prompt injection through retrieved content is the main practical threat.

---

## I. Installation plan (by phase)

All commands [UNVERIFIED on macOS 27]. Check flags against `--help`.

**Phase 1: minimal inference**
```
sudo sysadminctl -addUser agent -fullName "Agent" -password -
brew install llama.cpp huggingface-cli
hf download unsloth/Qwen3.6-35B-A3B-GGUF --include "*IQ4_XS*" --local-dir /Volumes/ext/models
sudo sysctl iogpu.wired_limit_mb=25600
llama-server -m <gguf> -c 131072 --parallel 2 -ngl 99 --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0 --host 127.0.0.1 --port 8080
```
Test: curl a tool-call request and record tok/s at 1k/16k/32k/64k. Failure modes: OOM at higher context, wrong chat template breaking tool calls. Rollback: kill the process.

**Phase 2: autonomous coding.** `brew install colima docker`, then `colima start --vm-type vz --cpu 4 --memory 4 --mount-type virtiofs` with explicit read-only mounts. Install the candidate harnesses inside the VM and run the 30-task bake-off. Exit: a harness chosen by data.

**Phase 3: research agents.** SearXNG, evidence-store schema, verifier scripts. Test: plant a fake citation and confirm it is rejected.

**Phase 4: memory.** `sqlite-vec` extension, memory git repo, curator step.

**Phase 5: orchestration.** Task/lease/agent_def tables, scheduler, worker launcher, budgets. Test: kill a worker mid-task and confirm the lease expires and the retry is clean.

**Phase 6: 24/7.** LaunchDaemons for each service, `pmset` settings, watchdog. Test: pull power mid-run and confirm full recovery without intervention.

**Phase 7: remote.** Tailscale with ACLs, the Telegram bot, the dashboard. Test: stop and approve from cellular.

**Phase 8: optimization.** Trial oMLX against llama-server on a replayed trace, run quant evals, and optionally add a cloud router.

Directory layout: `/Users/agent/{orchestrator,memory,worktrees,logs}`, `/Volumes/ext/{models,papers,datasets,mirrors,backups}`.

---

## J. What NOT to install

- **OpenClaw as core.** Its security record (see above) disqualifies it as the trust boundary.
- **Vector DB servers, Neo4j, Kubernetes, Temporal.** Infrastructure without a problem at this scale.
- **Ollama as the primary server.** It is fine for convenience, but its MLX path is gated above 32 GB and it adds a layer between you and llama.cpp flags.
- **Multiple resident models or 100 model processes.** Bandwidth-bound; no throughput gain.
- **Host-level GUI computer-use.** Use a VM.
- **Auto-self-improving skill loops in unattended mode.** They are self-modification without a review gate.

---

## K. Upgrade path

- **64 GB (M5 Pro mini, 307 GB/s, TB5):** the M5 Pro mini starts at $1,699 with 24 GB and configures to 64 GB. It nearly doubles bandwidth. Run 35B-A3B at Q6-Q8 plus a resident 27B dense, and 4-6 slots. Apple pitches Thunderbolt 5 for linking minis to run larger models, which the M6 cannot do.
- **96-128 GB+ (Mac Studio):** the M5 Ultra Studio is announced at 1.2 TB/s. That makes Qwen3.5-122B-A10B-class models practical, and oMLX/vllm-mlx become more valuable.
- **NVIDIA GPU server:** vLLM or SGLang with tensor parallelism and real concurrency. The mini becomes the control plane, with the same orchestrator and a different model endpoint.

---

## Sources

| Source | Type |
|---|---|
| igeeksblog.com M6/M5 Pro launch (price, ship date) | Secondary |
| 9to5mac M6 mini bandwidth tiers | Secondary (reputable) |
| camerajabber.com M6 mini analysis (TB4, bandwidth) | Secondary |
| owc.com M6 mini article | Secondary (claim challenged above) |
| macstories.net M6 tag (M5 Ultra 1.2 TB/s) | Secondary |
| t2online.in launch coverage (Neural Accelerators, TB5 clustering) | Secondary |
| rits.shanghai.nyu.edu Qwen3.6-35B-A3B | Secondary (vendor benchmarks) |
| github.com/QwenLM/Qwen3.6 mirror (release dates) | Primary, via mirror |
| huggingface.co/Prince-1/Qwen3.6-27B (model card copy) | Primary, via mirror |
| omlx.ai community benchmarks (M3 Max, M1 Max) | Secondary (community) |
| sourcepulse.org / jimmysong.io oMLX summaries | Secondary |
| pypi.org/project/vllm-mlx, vllm-mlx.is-a.dev | Primary-ish (package/docs) |
| openclawdc.com MLX vs llama.cpp | Secondary |
| willitrunai.com Qwen3.6 on M4 32 GB | Secondary |
| pinggy.io open-source CLI agents | Secondary |
| composio.dev, fast.io, pasqualepillitteri.it Hermes/OpenClaw | Secondary |
| pkg.go.dev Cloister; hunted.space Cua/Lume | Secondary |

I did not fetch any page, so no primary document was read in full. Re-verify: the GGUF file sizes, llama-server flag names on the current build, Tailscale and `pmset` behavior on macOS 27, SearXNG/OpenAlex/Docling details, and every M6 throughput number (I have none measured).

## Reasoning trace (not shown to raters)

Claude responded: Starting with hardware verification, since everything else depends on it.
Resolving a date discrepancy before starting the research.
Resolving a date discrepancy before starting the research.

Starting with hardware verification, since everything else depends on it.

Searched the web

Searched the web

Hardware confirmed. Date note: your brief says Aug 31, but the system date is Oct 14, 2026, and the M6 mini only shipped Sept 22, so I’m using Oct 14. Next: current models and runtimes.

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
switch, and Claude searched the web by itself. Send time 2026-10-14T02:43:39.355Z (browser clock, read right after
sending). Chat: https://claude.ai/chat/0b513fe0-f611-4dca-b0c2-5a7906bce09d?incognito (incognito chats are not kept in history).
Operated by the assistant (Claude, via the Claude in Chrome extension) in the author's signed-in browser,
at the author's request; the runs were opened in separate tabs and sent in manifest order without waiting
for earlier answers. The app turns long pastes into an attachment, so the prompt was inserted as plain
text in eight line-aligned pieces from one clipboard paste and checked against the original (1,782 words,
same text) before sending. Answer copied with the app's Copy button (it includes any short lines the model
wrote before its searches) and written verbatim from the clipboard; the reasoning trace is the visible
process panel (step summaries and search queries) copied from the page text.
