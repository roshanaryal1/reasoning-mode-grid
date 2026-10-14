---
run_id: claude__fast__p1-v1__r3
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
replicate: 3
date_stamped: '2026-10-14T02:42:14+00:00'
date_run: '2026-10-14T02:42:14+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

**Model:** Claude Sonnet 5.5 | **Knowledge cutoff:** end of June 2026 | **Browsing:** ON (about 10 web searches, no page fetches)

**Evidence caveats**
- The prompt gives two dates, 31 Aug and 14 Oct 2026. I used 14 Oct. That is consistent with the M6 mini, which shipped 22 Sep.
- I found no independent benchmark of this exact machine (M6, 32 GB) running these models. Every throughput figure below is my arithmetic from bandwidth, labeled as an estimate, or a third-party number from different hardware.
- I did not reach Apple's newsroom. Hardware facts come from press coverage that agrees across several outlets.
- Install commands marked (unverified) come from my memory and need a check against current docs.

---

## Decisions at a glance

| Layer | Pick |
|---|---|
| Resident model | Qwen3.6-35B-A3B at about 4-bit, the only large model kept loaded. |
| Inference server | llama.cpp `llama-server` for v1. Run a bake-off against vllm-mlx in week 1 and switch if it wins. |
| Coding harness | OpenCode in headless server mode, inside a sandbox. Pi is the fallback if OpenCode's prompt overhead is too large. |
| Orchestrator | A thin custom Python supervisor with a SQLite task queue. No agent framework. |
| Logical agents | Rows in SQLite (role, tools, budget, model tier). Only 2 to 3 inference slots run at once. |
| Memory | Markdown files plus SQLite (FTS5), then `sqlite-vec`. No vector DB or graph DB. |
| Research | A claims ledger with exact-span verification against stored source snapshots. |
| Isolation | Dedicated non-admin macOS user, plus Apple `container` VMs, an egress allowlist proxy, and host-side credential brokers. |
| 24/7 | launchd LaunchDaemons running as the agent user, a SQLite lease queue, and a watchdog with an external dead-man ping. |
| Remote | Tailscale only, `tailscale serve` dashboard, and ntfy for push and approvals. |
| Storage | The internal SSD holds models, DBs and hot worktrees. The external SSD holds cold data and backups. |
| Cloud | Optional escalation lane only, gated by a redaction scanner and a daily budget cap. |

---

## 1. Local inference

**Hardware facts.** The M6 has a 12-core CPU and a 12-core GPU with Neural Accelerators in each GPU core and up to 170GB/s of memory bandwidth, up from 153GB/s on M5. It tops out at 32GB and has three Thunderbolt 4 ports, not Thunderbolt 5. It was announced August 25, 2026 and reaches buyers September 22, and it ships with macOS 27.

**Wrong assumption to discard.** One retailer blog says 170GB/s only suits 7B or 8B models. That treats all models as dense. Decode is bandwidth-bound, so the right metric is active parameters per token, not total parameters.

**Decode ceiling (my estimate, not a benchmark).**

| Model type | Weights read per token | Ceiling at 170 GB/s | Realistic at 40 to 60% efficiency |
|---|---|---|---|
| 27B dense, 4-bit (about 15 GB) | about 15 GB | about 11 tok/s | 5 to 7 tok/s |
| 35B-A3B MoE, 4-bit (about 3B active, about 1.7 GB per token) | about 1.7 GB | about 100 tok/s | 40 to 60 tok/s |

Dense models of 27B and up are therefore the wrong choice for unattended work on this chip. A dense 31B such as Gemma 4 is roughly 2x worse on decode than Qwen's 27B.

**Why Qwen3.6-35B-A3B.** It was released by Alibaba on April 15, 2026, with upgrades in agentic coding and repository-level reasoning, and it is Apache-2.0. I did not independently verify its benchmark claims. Treat vendor numbers as upper bounds: they come from datacenter GPUs at higher precision, not 4-bit on 170 GB/s.

**Size and fit.**
- My arithmetic puts 35B at Q4_K_M (about 4.85 bits per weight) near 21 GB.
- A third-party calculator claims 30.7 GB for Q4_K_M and only 23 GB usable on a 32 GB M4. I think 30.7 GB is inflated, probably by KV and overhead.
- The usable-memory figure matters, though. macOS caps GPU-wired memory by default. Raise it with `sudo sysctl iogpu.wired_limit_mb=27000` and persist it via a LaunchDaemon (unverified on macOS 27).
- A community IQ3_XXS build is listed at 13 GB. That is your emergency fallback.

**Prefill is the real bottleneck.** Agent loops are prefill-heavy. A community quant card reports prompt evaluation of 105 to 144 tokens/s across tested Macs, which is poor. At that speed a cold 10K-token system prompt costs about 70 to 100 s. The M6's GPU Neural Accelerators should help matmul-bound prefill, and Apple claims up to 4x on AI tasks, but I have no M6 prefill benchmark. Design for prefix-cache hits: stable prompt prefixes, small harness prompts, KV slot persistence.

**Runtime.** Sources conflict:
- One says use llama.cpp Metal at 32GB or less.
- Another says MLX is 20 to 87% faster below 14B and Ollama's MLX backend needs 32GB+. A third says more than 32GB, which would exclude you. Skip Ollama.
- vllm-mlx has continuous batching with 4.3x aggregate throughput at 16 concurrent requests on an M4 Max. It also offers paged KV cache, prefix cache, SSD tiering, and OpenAI plus Anthropic APIs. That is the single most relevant feature for your concurrency goal.
- One June source says MLX agentic tool-calling still trails llama.cpp.

My decision (confidence about 60%): ship llama.cpp first for tool-call and chat-template maturity, then run a one-day bake-off. Switch to vllm-mlx if it gives at least 25% more aggregate tok/s at 3 concurrent agents with 100% valid tool-call JSON over 200 calls.

**MoE batching caveat.** Different sequences activate different experts, so batching gains for MoE are sublinear compared with dense. Expect real but smaller gains than 4.3x. Measure.

## 2. Agent runtimes and harnesses

| Option | Verified facts | Verdict |
|---|---|---|
| OpenCode | MIT, 75+ providers, client/server architecture for Docker and remote execution, fastest-growing open-source coding agent | **Ship.** The server mode fits headless and remote use. |
| Pi | Minimal open-source agent with four tools | Fallback. Its tiny prompt helps prefill, but you would build the rest. |
| Codex CLI | Apache 2.0, mostly Rust | Good code, but tuned for OpenAI models. Not for the local lane. |
| Claude Code | Proprietary; system prompt over 10K tokens (pre-Claude 5). Anthropic cut over 80% of it for Claude 5 models in July 2026 | Useful as the cloud-lane worker. For local models the prompt size is costly at about 100 tok/s prefill. |
| Hermes Agent | MIT, released Feb 25 2026, memory in local SQLite, self-improving skills | Interesting. I would not run it in v1 because unsupervised self-written skills widen the attack surface. Revisit in Phase 8. |
| OpenClaw | Runs with high system privileges: shell, filesystem, credentials | Skip. The privilege model is the opposite of what you want. |

**Decision.** Use a hybrid: a custom supervisor, with harnesses as interchangeable workers. No existing system provides all of: a task queue, per-agent permissions, budgets, lease-based crash recovery, and model routing. Frameworks would fight your queue. A supervisor in about 1.5 to 2K lines of Python is cheaper than adapting any of them.

## 3. Multi-agent architecture

- **100 simultaneous model instances:** impossible. Each would need its own weights, and decode is bandwidth-bound, so they would just divide 170 GB/s.
- **100 logical agents:** a row in SQLite with a role prompt, tool allowlist, model tier, budget, sandbox profile and memory scope. Cost is near zero when idle.
- **Throughput comes from batching, not process count.** One loaded model serves N sequences per step. Use 3 slots: 1 interactive, 2 background.
- **Topology:** coordinator/worker, with depth capped at 2. Swarms and peer-to-peer chat burn tokens on coordination, which hurts most at 40 to 60 tok/s.
- **Parallelize where tokens are not the bottleneck.** Tests, builds, web fetching and PDF parsing run in parallel in VMs while the model processes one thing.
- **Model swapping:** worthwhile only at queue boundaries. Group tasks by model and drain the queue. Avoid per-task swaps, since a cold 20 GB load is likely 5 to 10 s or more from internal SSD.

## 4. Coding agents

I ranked by fit to a 170 GB/s, 32 GB box:
1. OpenCode (headless, local endpoint, git worktrees under my supervisor).
2. Pi (minimal prompt).
3. Codex CLI or Claude Code as cloud-lane workers for escalations.

Public leaderboards are model plus harness combined, so they say little about your local setup. Build a private golden set of 20 to 30 tasks from your own repos (see Phase 2) and decide on that.

## 5. Research agents

Hallucinated-citation prevention is architecture, not prompting:
1. **Source snapshots.** Every fetched page or PDF is stored (content hash, URL, timestamp). PDFs go through PyMuPDF text extraction (docling is the heavier option).
2. **Claims ledger.** The agent can only add a claim as `(claim_text, source_id, quoted_span, location)`.
3. **Mechanical verification.** The quoted span must appear verbatim (whitespace-normalized) in the snapshot. No match means the claim is rejected. No model is involved.
4. **Bibliographic verification.** Resolve DOI/arXiv IDs through Crossref, OpenAlex or the arXiv API (unverified current endpoints) and compare title, authors and year with what the agent claimed.
5. **Generation by reference.** The report writer receives claim IDs only. Citations in prose are rendered from the ledger, never typed by the model.
6. **Independent verifier pass.** A fresh-context pass judges whether the span supports the claim, with thinking on.
7. **Contradiction detection.** Group claims by (entity, metric) and flag opposing values for human review.

Search: self-hosted SearXNG for the free tier, with an optional paid search API when quality matters. I did not benchmark either.

## 6. Persistent memory

- **Now:** `memory/` Markdown (decisions, project notes, ADRs) plus SQLite with FTS5 for events, runs and claims. This covers over 90% of retrieval needs, and BM25 is strong on code and identifiers.
- **Phase 4b:** `sqlite-vec` and a small (about 0.5B) embedding model, giving a hybrid BM25 and vector search in one file.
- **Skip for now:** Qdrant/Chroma servers and knowledge-graph DBs. Model relations as SQLite tables and recursive CTEs until query patterns prove otherwise.
- **Scopes:** global, per-project, per-task episodic. Write memory only through a reviewed `memory.propose` tool, so an agent can't silently poison its own future context.

## 7. Computer control

Most-to-least isolated:
1. Disposable Linux VM per task. Apple's `container` CLI needs macOS 26+, with one lightweight VM per container. A tool vendor claims about 10 to 20x faster startup than Lima and about 3x less RAM per cage. That is a vendor claim, so I would still benchmark it. Lima remains the mature fallback.
2. Host-level Seatbelt sandboxing for tools that must run natively: Anthropic's open-source Sandbox Runtime (Seatbelt on macOS plus a network-filtering proxy). Note `sandbox-exec` is deprecated but still functional, with no announced replacement.
3. A dedicated standard macOS user, with no admin rights and a separate home and keychain.
4. GUI computer-use only in a throwaway macOS VM (Tart), and only when a task truly needs it. Defer it.

Caveat: Claude's auth lives in the macOS Keychain, which containers and Linux VMs can't reach. Any cloud-lane harness needs a host-side broker or an env-injected token.

## 8. Always-on operation

- Run services as LaunchDaemons with `UserName=agent` and `KeepAlive`, so they start at boot with no GUI login.
- `sudo pmset -a sleep 0 disksleep 0 womp 1 autorestart 1` keeps the machine awake and restarts after power loss.
- **FileVault trade-off.** With FileVault on, an unplanned reboot stops at the pre-boot unlock screen, so the system stays dead until you unlock it. My pick is FileVault on, plus a small UPS, plus `fdesetup authrestart` for planned updates. Your secrets on disk matter more than a rare power-loss outage.
- Crash recovery: tasks are leased with a visibility timeout. Every step is idempotent and checkpointed. When a lease expires, the supervisor requeues the task from its last checkpoint.
- Watchdog: a separate launchd job checks supervisor heartbeat and inference health, restarts them, and pings an external dead-man service so you hear about it if the whole box dies.

## 9. Remote access

- **Network:** Tailscale (WireGuard mesh) with ACLs. No port forwarding and no public listeners. (`brew install tailscale` plus `tailscaled install-system-daemon` for headless, unverified.)
- **Dashboard:** a small FastAPI app on localhost, exposed to the tailnet with `tailscale serve`. Read Tailscale identity headers for authentication.
- **Push and approvals:** ntfy with action buttons. Self-hosted works, but iOS push needs the upstream relay (unverified), which sees only a poll trigger. Telegram is the simpler alternative, but it adds a third party to the control plane. I prefer ntfy.
- **High-risk approvals:** require a TOTP step-up on the dashboard, not just a tap on a notification.
- **Emergency stop:** `agentctl kill` writes `/var/agent/STOP`, checked by every worker between steps, then runs `launchctl bootout` on the worker jobs. It is available as a dashboard button and over Tailscale SSH.

## 10. Storage

M6 has Thunderbolt 4 (40 Gb/s), so a 1 TB NVMe enclosure should reach roughly 2.5 to 3 GB/s. That is fine for sequential reads but worse for small-file build I/O.

| Data | Location | Reason |
|---|---|---|
| macOS, apps, agent user home | Internal | |
| Active model(s), about 21 GB primary plus 1 to 2 alternates | Internal | Load time |
| `queue.db`, `memory.db` | **Internal** | SQLite WAL on a hot-unpluggable drive risks corruption |
| Active worktrees and build caches | Internal | Small-file latency |
| Cold models, papers, datasets, snapshots, logs older than 7 days | External | |
| Backups | External (restic/Kopia), plus optional encrypted offsite | Time Machine to the same box is weak |

Add a mount check to every job that touches the external SSD. If the volume is missing, tasks that need it pause instead of failing noisily.

---

## A. Technology stack

| Layer | Recommended | Alternatives | Why |
|---|---|---|---|
| Interface | Dashboard on tailnet plus ntfy | Telegram bot | Private, no third party in the control plane |
| Supervisor | Python 3.12, launchd, watchdog | systemd-style wrappers | Native to macOS |
| Orchestrator and queue | Custom, SQLite WAL | Temporal, Celery | Single node, no brokers to maintain |
| Agents | OpenCode headless | Pi, Codex, Claude Code (cloud) | Local-model support, client/server |
| Model router | About 150 lines of Python | LiteLLM | Few routes; fewer dependencies |
| Inference | llama.cpp, with vllm-mlx contender | MLX-LM, LM Studio | Tool-call maturity vs batching throughput |
| Sandbox | Apple `container`, fallback Lima | Tart, Seatbelt (srt) | VM isolation with fast startup |
| Memory | Markdown plus SQLite FTS5, then sqlite-vec | Qdrant, graph DB | No extra infrastructure |
| Search | SearXNG | Paid search API | Free, private |
| Network | Tailscale | WireGuard by hand | Easy ACLs |

## B. Architecture diagram

```
 Phone/Laptop ── Tailscale ── Dashboard + ntfy (approvals, kill)
                                   │
        ┌──────────────────────────▼─────────────────────────┐
        │ Supervisor (launchd, user: agent)                  │
        │  heartbeat · budgets · STOP file · lease reaper    │
        └───────┬────────────────────────────┬───────────────┘
                │                            │
        ┌───────▼────────┐          ┌────────▼──────────┐
        │ Orchestrator   │          │ Task queue + state│
        │ planner→spec   │◄────────►│ SQLite WAL (int.) │
        └───────┬────────┘          └───────────────────┘
                │ AgentSpec (role, tools, budget, tier)
        ┌───────▼─────────────────────────────────────────┐
        │ Worker pool (N=3 LLM-bound, M≤2 sandbox VMs)    │
        │ OpenCode / research workers                     │
        └───┬─────────────┬──────────────┬────────────────┘
            │             │              │
   ┌────────▼──┐  ┌───────▼─────┐  ┌─────▼────────────┐
   │ Model     │  │ Sandbox VM  │  │ Host brokers     │
   │ router    │  │ (container) │  │ git push, web,   │
   └──┬─────┬──┘  │ egress proxy│  │ secrets (narrow) │
      │     │     └─────────────┘  └──────────────────┘
 ┌────▼──┐ ┌▼────────────┐
 │ Local │ │ Cloud lane  │  redaction scan, daily cap
 │ server│ │ (optional)  │
 └───┬───┘ └─────────────┘
     │
 Memory: Markdown + SQLite FTS5/vec · Snapshots · Claims ledger
```

## C. Resource plan (32 GB, estimates)

| Consumer | GB |
|---|---|
| macOS plus services | 4 |
| Primary model weights (4-bit) | 20 to 21 |
| KV cache, 3 slots at 32K each (architecture-dependent; measure) | 2 to 4 |
| Embedding model | 0.6 |
| One sandbox VM (3 GB cap) | 3 |
| Browser, DBs, tools, page cache | 2 to 3 |
| **Total** | **32 to 36** |

That is over budget. Rules to stay inside it:
- **One resident LLM only.** Any second resident model breaks the budget.
- **Memory-pressure gate.** After loading, run a 2-hour soak with 3 slots, 1 VM and a browser, and watch `memory_pressure`. Pressure must stay green.
- **If it fails,** step down in this order: lower context per slot, KV quantization to q8, IQ4_XS, then switch to Gemma 4 26B-A4B (about 15 GB; quality unverified by me) or IQ3_XXS.
- **Concurrency:** 1 large worker, 2 to 3 sequences batched on it, 1 to 2 VMs. Beyond that you are trading latency for nothing.

## D. Agent architecture (100+ logical agents)

```sql
CREATE TABLE agents(id TEXT PRIMARY KEY, role TEXT, prompt TEXT, tools JSON,
  model_tier TEXT, budget JSON, sandbox TEXT, mem_scope TEXT, parent TEXT);
CREATE TABLE tasks(id INTEGER PRIMARY KEY, agent_id TEXT, state TEXT, payload JSON,
  lease_until INT, attempts INT, parent_task INT, priority INT, checkpoint JSON);
CREATE TABLE events(ts INT, task_id INT, kind TEXT, data JSON);
CREATE TABLE claims(id INTEGER PRIMARY KEY, text TEXT, source_id TEXT, span TEXT, verified INT);
```

- **Dynamic creation:** the planner emits an `AgentSpec` JSON, validated against a schema. A child can never exceed its parent's tools, budget or filesystem scope (capability attenuation). Specs are stored for reuse.
- **Scheduling:** a priority queue gated by semaphores: LLM slots 3, VMs 2, network fetch 8. Interactive tasks preempt at step boundaries. Tasks are grouped by model tier to limit swaps.
- **Stop conditions** (every task has all of these): token cap, wall-clock cap, tool-call cap, diff-size cap, and a no-progress detector (same error hash 3 times, or test status unchanged for N loops).

## E. Model strategy

| Task | Model | Settings |
|---|---|---|
| Planning | Qwen3.6-35B-A3B | Thinking on, bounded budget |
| Coding and debugging | Same | Thinking on for debugging, off for mechanical edits |
| Research extraction and verification | Same | Constrained JSON; verifier in a fresh context |
| Summarization | Same | Thinking off |
| Classification and routing | Rules plus embeddings first, the same model with grammar-constrained output as fallback | |
| Final synthesis | Local by default. Cloud optional for high-stakes deliverables | Redaction scan first |

Local-first is a real constraint on this machine, not a slogan. A single resident model with different thinking budgets beats a zoo of small models that can't co-reside. **Cloud escalation triggers:** three failed local attempts, a task tagged `hard`, or context above what the slots can hold. Which frontier model to use is something to settle with your golden set, not with leaderboards.

## F. 24/7 architecture

- launchd jobs, each with `KeepAlive`: `agent.inference`, `agent.supervisor`, `agent.dashboard`, `agent.searxng`, and `agent.watchdog` (a separate job and user).
- A durable queue with leases and checkpoints. After a crash, the lease reaper requeues the task and the worker resumes from its checkpoint. OpenCode sessions are persisted, so resumption is cheap.
- A nightly job rotates logs, runs a SQLite integrity check, backs up the DBs, and reports a morning digest.
- Self-heal ladder: restart the worker, then restart inference, then page you.

## G. Remote-control architecture

Phone (Tailscale app) → tailnet → `tailscale serve` → dashboard (queue view, logs, task submit, approve/deny, kill). Push notifications come from ntfy, with approval buttons for medium-risk actions and TOTP step-up for high-risk ones. No service listens on a public interface. Tailscale ACLs allow only your devices to reach the dashboard and SSH ports.

## H. Security architecture

**Principle:** treat the agent as a competent but injectable contractor. Anything it reads from the web or a repo is untrusted input.

| Area | Control |
|---|---|
| Identity | Separate `agent` macOS user, no admin, own keychain, no access to your home |
| Filesystem | Work happens on worktrees or APFS clones in an agent workspace. Originals are never touched |
| Execution | VM per task, destroyed afterwards, resource-capped |
| Network | Egress allowlist proxy, default deny. Package registries and chosen docs sites only |
| Secrets | None in VMs. Brokers on the host expose narrow actions (push to `agent/*`, read one API) |
| Git | Branch protection on `main`. The agent can only push `agent/*`. Merges require you |
| Audit | Append-only event log of every tool call, plus the egress proxy log |
| Limits | Per-task token, time, tool-call and diff caps, plus a global daily cloud cap |

**Approval matrix**

| Fully autonomous | Needs approval | Forbidden |
|---|---|---|
| Read and edit in workspace, run tests, install deps in VM, fetch allowlisted web, commit to `agent/*`, write memory proposals | Push or open a PR, merge, new network domain, install host software, delete over N files, spend cloud budget over cap, create a new agent with broader scope | Touch the keychain, your home, or financial or credential files; run `sudo`; disable the sandbox, logging or the kill switch; modify launchd or its own supervisor |

Defenses against prompt injection from fetched content:
- Fetched text is treated as data and never as instructions.
- Research workers get no write tools and no shell.
- Egress is allowlisted, so exfiltration has nowhere to go.

## I. Installation and phased plan

**Phase 1: Minimal working system** (day 1)
```
brew install llama.cpp uv git
sudo sysctl iogpu.wired_limit_mb=27000
# download the Qwen3.6-35B-A3B Q4 GGUF (imatrix quant) to ~/models
llama-server -m ~/models/qwen3.6-35b-a3b-q4.gguf -c 98304 --parallel 3 \
  --cont-batching -ngl 99 -fa on --jinja --cache-reuse 256 \
  --host 127.0.0.1 --port 8080
```
Flags need checking against current llama.cpp (unverified). Test: 3 concurrent requests, and `memory_pressure` stays green. Failure modes: OOM at load (drop the quant), slow prefill (check prefix cache hits). Rollback: stop the job.

**Phase 2: Autonomous coding**
- Create the `agent` user. Install Apple `container` from the GitHub release `.pkg`, then run `container system start`. (Fallback: `brew install lima`.)
- Install OpenCode (`npm i -g opencode-ai`, unverified) in the base image and point it at `http://host:8080/v1`.
- Write the golden set of 20 to 30 tasks. Measure pass rate and wall-clock per task.
- Failure: tool-call JSON errors (fix the chat template), or long cold prefill. Rollback: delete the VM and the worktree.

**Phase 3: Research agents.** Add SearXNG (in a container), PyMuPDF, the claims-ledger code and the verifier. Test with a known question: seed a fake citation and confirm the pipeline rejects it.

**Phase 4: Persistent memory.** Markdown directories plus `memory.db` (FTS5), then `sqlite-vec`. Test with a retrieval set of 30 questions from your past projects.

**Phase 5: Multi-agent orchestration.** Implement the schema from section D, the semaphores, AgentSpec validation and attenuation. Test with a 20-agent fan-out and confirm there are never more than 3 active slots. Rollback: flip a flag to run single-agent mode.

**Phase 6: 24/7.** Write the launchd plists, `pmset`, the lease reaper and the watchdog. Test by `kill -9` on each component, then a hard reboot.

**Phase 7: Remote access.** Tailscale, dashboard, ntfy. Test from cellular data with Wi-Fi off, and run the kill-switch drill.

**Phase 8: Optimization.** Run the vllm-mlx bake-off, evaluate Hermes Agent's memory loop, tune prefix caching and KV quantization. Re-benchmark after each change.

Directory layout:
```
/Users/agent/{bin,config,memory,workspaces}      # internal
/Volumes/Work/{archive,papers,datasets,logs,backups}   # external
```

## J. What NOT to install

- **OpenClaw:** its privilege model is the opposite of what you need.
- **Ollama:** the MLX path has conflicting 32 GB support claims. It adds a layer without helping.
- **Qdrant, Chroma or Neo4j:** unnecessary at this scale.
- **LangChain, CrewAI or AutoGen:** they add abstraction around a queue you need to own.
- **Dense 27B to 31B models as the main driver:** about 5 to 7 tok/s is too slow for unattended loops.
- **Multiple resident LLMs:** they break the memory budget.
- **Kubernetes or Docker Desktop:** heavy, with no benefit on one node.
- **Any agent with a public skill marketplace**, in the early phases.

## K. Upgrade path

| Hardware | Change |
|---|---|
| M5 Pro 64 GB (307GB/s, Thunderbolt 5) | Roughly 1.8x the bandwidth. Allows a larger MoE and a second resident model. This is the first upgrade I would make. |
| 96 to 128 GB (Mac Studio class) | Large MoE models, a dedicated small router model, more parallel slots |
| Clustering | Needs Thunderbolt 5, which the M6 mini lacks |
| Dedicated GPU server | Move batch inference there and keep the Mac as the control plane. The queue and agent schema don't change |

---

## Sources

| Source | URL | Type |
|---|---|---|
| MacRumors, M6 and M5 Pro Mac mini | https://macrumors.com/2026/08/25/apple-announces-2026-mac-mini | Secondary (press) |
| M6 Mac mini spec page | https://www.starryhope.com/minipcs/models/mac-mini-2026-m6/ | Secondary |
| OWC on Mac mini lineup | https://www.owc.com/blog/apple-updates-mac-mini-lineup-with-m5-pro-and-new-m6-chips | Secondary (disputed claims noted) |
| vllm-mlx paper (arXiv 2601.19139) | https://arxiv.org/abs/2601.19139v1 | Primary |
| vllm-mlx repository | https://github.com/waybarrios/vllm-mlx/wiki | Primary |
| Qwen3.6-35B-A3B GGUF card | https://huggingface.co/batiai/Qwen3.6-35B-A3B-GGUF | Secondary (community quant) |
| Memory-fit calculator | https://willitrunai.com/de/can-run/qwen-3.6-35b-a3b-on-m4-mini-32gb | Secondary (low confidence) |
| MLX vs llama.cpp comparison | https://openclawdc.com/blog/mlx-vs-llama-cpp-apple-silicon/ | Secondary |
| Apple Silicon inference guide | https://blog.starmorph.com/blog/apple-silicon-llm-inference-optimization-guide | Secondary |
| Harness comparison | https://techstackups.com/comparisons/coding-agent-harness-comparison-2026/ | Secondary |
| Pi vs Claude Code | https://composio.dev/blog/pi-agent-vs-claude-code | Secondary |
| OpenClaw vs Hermes | https://toolradar.com/blog/openclaw-vs-hermes-agent | Secondary |
| OpenClaw security notes | https://github.com/Desu403/claw-local | Secondary |
| Sandbox landscape | https://gist.github.com/wincent/2752d8d97727577050c043e4ff9e386e | Secondary |
| agentcage (Apple container backend) | https://pypi.org/project/agentcage/0.22.11/ | Secondary (vendor claims) |
| workmux sandbox docs | https://workmux.raine.dev/guide/sandbox/features/ | Secondary |

Not verified, and worth checking first: M6 benchmark numbers, Qwen3.6 quality at 4-bit, current install commands, and the iOS push behavior of self-hosted ntfy.

## Reasoning trace (not shown to raters)

Claude responded: Model: Claude Sonnet 5.5 | Knowledge cutoff: end of June 2026 | Browsing: ON (about 10 web searches, no page fetches)
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
switch, and Claude searched the web by itself. Send time 2026-10-14T02:42:18.495Z (browser clock, read right after
sending). Chat: https://claude.ai/chat/6ca8dab2-103a-4837-b615-efa8480f08a4?incognito (incognito chats are not kept in history).
Operated by the assistant (Claude, via the Claude in Chrome extension) in the author's signed-in browser,
at the author's request; the runs were opened in separate tabs and sent in manifest order without waiting
for earlier answers. The app turns long pastes into an attachment, so the prompt was inserted as plain
text in eight line-aligned pieces from one clipboard paste and checked against the original (1,782 words,
same text) before sending. Answer copied with the app's Copy button (it includes any short lines the model
wrote before its searches) and written verbatim from the clipboard; the reasoning trace is the visible
process panel (step summaries and search queries) copied from the page text.
