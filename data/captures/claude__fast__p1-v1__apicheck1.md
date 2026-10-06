---
run_id: claude__fast__p1-v1__apicheck1
set: api_check
family: claude
vendor: Anthropic
mode: fast
native_label: adaptive thinking, effort low (lowest available, cannot be disabled)
channel: api
model_requested: claude-sonnet-5-5
model_returned: claude-sonnet-5-5
params:
  thinking:
    type: adaptive
  output_config:
    effort: low
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 1
date_run: '2026-10-06T09:02:28+00:00'
run_by: roshanaryal
finish_reason: end_turn
usage:
  input_tokens: 4096
  output_tokens: 5328
  reasoning_tokens: 0
latency_s: 43.05
harness_version: 0.1.0
---

## Final answer

**Header:** I'm Claude (Anthropic); I don't know my exact version string. My knowledge cutoff is early-to-mid 2025. **Web browsing/tools: OFF for this answer.** Everything below comes from training knowledge, not from research done on 31 Aug 2026. I could not verify the "M6 Mac mini", current versions, or ecosystem state. I have no data on anything released after my cutoff, so the model names below are *families to evaluate*, not verified current picks. Every version, benchmark and URL must be re-checked before you build. The Sources list contains only stable primary landing pages, not pages I fetched.

---

## 2. Decisions at a glance

| Layer | Pick | Confidence |
|---|---|---|
| Inference engine | **MLX / mlx-lm** (served via `mlx-lm server` or LM Studio's MLX backend); llama.cpp (Metal) as fallback | High on direction, medium on versions |
| Model serving/router | **LiteLLM proxy** (or a thin custom router) in front of local servers and optional cloud | Medium |
| Primary local model | Best ~30B-class MoE coder/agent model at 4-bit (Qwen3-Coder-30B-A3B family or its successor) | Verify |
| Small/fast model | 4–8B instruct at 4-bit (Qwen3 4B/8B-class or successor) | Verify |
| Embeddings | A small open embedding model (bge-m3 / Qwen3-Embedding class) | Verify |
| Coding agent | **Claude Code or OpenCode/Aider-style CLI** running headless, with local models via the router. Choose after a bake-off on your own repos | Medium |
| Orchestrator | **Custom thin Python supervisor + SQLite queue**, on top of existing harnesses | High |
| Memory | Markdown files + **SQLite (FTS5 + sqlite-vec)** | High |
| Sandbox | Dedicated macOS user + per-task git worktrees + Apple `container` or Docker/Colima/Lima VM for untrusted execution | High |
| Always-on | `launchd` LaunchAgents/LaunchDaemons + `caffeinate`/`pmset` | High |
| Remote | **Tailscale** + SSH/tmux + a small web dashboard + ntfy notifications | High |
| Storage | Internal: OS, tools, active models, DBs. External: archives, backups, papers | High |

## 1. Local inference

- **Memory budget logic (reliable arithmetic):** a 4-bit model needs roughly 0.55–0.6 GB per billion parameters. A 30B model is ~17–19 GB, a 14B is ~8–9 GB, and an 8B is ~5 GB.
- **MoE models fit this machine best.** A 30B-total, ~3B-active MoE gives 30B-class knowledge at small-model decode speed. On Apple Silicon decode is memory-bandwidth-bound, and the base-tier chip has limited bandwidth compared with Pro/Max. Active parameters, not total, determine tokens/sec.
- **Dense 27–32B at 4-bit** is likely too slow for agent loops on a base chip. Avoid dense models above ~14B for the main loop.
- **Engines:**
  - MLX is Apple-native and usually fastest on Metal. It has good batching support in recent mlx-lm.
  - llama.cpp is the most mature, has GGUF, and the broadest model support.
  - Ollama is convenient but adds a layer and gives less control.
  - LM Studio is useful for model management and also offers an MLX backend.
  - vLLM-metal and similar projects are immature; don't rely on them.
- **Concurrency:** one large model loaded serves several concurrent requests via continuous batching, which is far cheaper than multiple copies. Aggregate throughput rises with batching while per-request speed drops, so this is where your throughput gains come from.
- **Context:** the KV cache grows with context. Cap the working context at 32k tokens for the main model and use retrieval and summarization rather than 128k windows. Quantize the KV cache to 8-bit if supported.
- **Model swapping:** avoid it. Loading takes 5–20 s from the internal SSD and is much slower from the external one. Keep the large model plus a small model resident.

## 3. Multi-agent architecture

- **Logical agents are rows in a database, not processes.** An agent is a definition (role prompt, tool allowlist, model tier, permissions, budget). It runs only when a task is leased.
- **Worker pool:** 2–4 concurrent LLM requests to the shared server, 1–2 concurrent heavy tool-running sandboxes, and unlimited queued tasks.
- Use a coordinator/worker pattern with a depth limit of 2 and a global cap on spawned agents. Most "100 agents" workloads are sequential pipelines with a few parallel branches.
- Dynamic agent creation: the planner emits an agent spec (JSON schema); a validator clamps permissions to a template ceiling, so an agent can never grant itself more than its parent has.
- **Routing:** rules first (task type → tier), then escalation on failure (small → main → optional cloud). Log outcomes to tune routing.

## 4. Coding agents

I cannot verify the 2026 ranking. Evaluate candidates on 10 of your own tasks with the same local model:
- **Claude Code**: strongest harness features (subagents, hooks, headless mode, worktrees), but it is designed for Anthropic models; local use requires a compatible proxy and is not first-class.
- **OpenCode, Aider, Goose, Cline/Roo, OpenHands, Codex CLI**: these support local OpenAI-compatible endpoints. OpenHands has the strongest built-in sandboxing but is heavier.
- **My default:** a headless CLI harness that supports OpenAI-compatible endpoints (OpenCode or Aider), one git worktree per task, a test-gated loop, and optional cloud escalation to a frontier model for hard tasks. Local 30B-class models are noticeably weaker than frontier models on long-horizon SWE tasks, so expect to need verification gates and to tolerate lower first-pass success.

## 5. Research agents

- Pipeline: query planning → search (self-hosted SearXNG, plus the arXiv, Semantic Scholar, OpenAlex and Crossref APIs) → fetch → PDF-to-text (pymupdf or Docling) → chunk → extract claims **with quote spans**.
- **Anti-hallucination design:** every claim stores (source id, exact quote, location). A verifier step checks that the quote is a literal substring of the stored source text, and that every DOI/arXiv ID resolves via Crossref/arXiv. The final report may cite only IDs in the evidence table. Unverified claims are marked or removed. Run a separate contradiction pass that compares claims on the same entity.
- Use the strongest available model for final synthesis, and a cloud model optionally if you allow it.

## 6. Memory

Start with markdown (human-readable project notes, decisions, `AGENTS.md`) plus a single SQLite file holding tasks, runs, events, claims, and FTS5 search. Add sqlite-vec for embeddings once the corpus is large. Add a knowledge graph only if you run into relational queries that SQL can't answer. Skip a vector DB server and Neo4j initially.

## 7. Computer control

- Create a dedicated macOS standard user (`agent`) with no access to your home directory, Keychain, or iCloud.
- Run risky execution in a Linux VM or container, using Apple's `container` tooling, Lima/Colima or Docker.
- Browser: Playwright with a separate profile and no logged-in sessions.
- GUI computer-use: avoid by default; it is slow and risky with local models.
- Credentials: scoped, short-lived tokens, injected per task by a broker, never stored in the agent's environment. Use a separate GitHub account or deploy keys with push access only to `agent/*` branches.
- Network: egress allowlist (pf rules or a proxy) per task class.

## 8. Always-on

- `sudo pmset -a sleep 0 disablesleep 1`, auto-restart after power failure on, and auto-login for the agent user (or a LaunchDaemon).
- LaunchAgents with `KeepAlive` for the inference server, the supervisor and the dashboard.
- Durable queue in SQLite (WAL mode) with leases and heartbeats; a task whose lease expires is requeued, and steps are idempotent.
- A watchdog checks the health endpoint, RAM pressure and disk space, and kills processes over their limits.
- Disable automatic macOS updates or schedule them.

## 9. Remote access

Tailscale (no public ports) with Tailscale SSH + tmux, a small FastAPI/htmx dashboard bound to the tailnet only, ntfy or Pushover for notifications with approval links, and a kill-switch file/endpoint (`touch STOP`) that the supervisor polls. Approvals go through signed, single-use links or authenticated dashboard buttons.

## 10. Storage

- **Internal 512 GB:** macOS, tools, active models (~40 GB), SQLite DBs, active worktrees, and caches.
- **External 1 TB:** model archive, papers/PDFs, datasets, Time Machine or restic backups, cold logs.
- **Rule:** nothing on the external drive is required for the system to boot; the external SSD is not the hot path. Make the backups encrypted and keep a copy off-machine.

---

## A. Stack
See the "Decisions at a glance" table; the alternatives are named in sections 1–10.

## B. Architecture
```
Phone/Laptop → Tailscale → Dashboard/SSH/ntfy
                    ↓
 Supervisor (launchd) ── watchdog, kill switch, budgets
                    ↓
 Orchestrator (Python) ↔ SQLite queue + memory (WAL)
                    ↓
 Agent runner: spec → harness (OpenCode/Aider/Claude Code) in sandbox
                    ↓
 Model router (LiteLLM) → MLX server (30B MoE + 4–8B small + embeddings)
                         → optional cloud (escalation only)
 Tools: git worktrees, VM/container, Playwright, SearXNG, paper APIs
```

## C. Resource plan (32 GB, estimates)
| Item | GB |
|---|---|
| macOS + services | 5–6 |
| 30B MoE 4-bit weights | ~17–18 |
| Small model (4–8B) | 2.5–5 (optional) |
| KV cache (several streams, 32k) | 2–4 |
| VM/containers | 2–4 |
| Browser/dev tools/DB | 2–3 |

This is tight: 32 GB can't hold everything at once, so run the small model **or** a smaller main model if memory pressure is high. Alternatively, use a ~14B main model and a 4B helper. Monitor `memory_pressure` and swap, and treat sustained swap as a failure.

## D. 100+ logical agents
Agent definitions live in the DB. The scheduler leases tasks to at most N workers. Each worker makes stateless calls to the shared server, with the state held in the DB. 100 agents means 100 rows plus a queue, not 100 processes.

## E. Model strategy
- **Planning, debugging, final synthesis:** the best local reasoning-capable model (the 30B MoE in thinking mode), or cloud escalation if enabled.
- **Coding:** a 30B-class coder MoE.
- **Research extraction and summarization:** small or mid model.
- **Classification and routing:** 4B model or rules.
- **Embeddings:** a dedicated small embedding model.

## F. 24/7
LaunchAgents, leases, heartbeats, idempotent steps, a nightly "plan of record", per-task wall-clock/token/step budgets, a morning digest, and a daily backup.

## G. Remote
See section 9. Phone: Tailscale app + Termius/Blink + the dashboard + ntfy.

## H. Security
- **Autonomous:** read/write inside task worktrees, run tests, web read-only, commit to `agent/*` branches, install packages inside the sandbox, and write to the agent's own memory.
- **Approval required:** pushing to protected branches or merging, any access outside the workspace, new network destinations, spending money, sending email/messages, handling credentials, deleting data above a threshold, `sudo`, installing system software, and changing the agent's own permissions.
- **Never:** reading the Keychain/personal home directory, financial sites, or disabling the audit log.
- Additionally: append-only audit log, resource limits via `ulimit`/cgroups in the VM, loop detection (the same tool call repeated more than N times), and a global kill switch. Treat all fetched web content as untrusted, since it is a prompt-injection vector: no agent that reads the web should also hold write credentials.

## I. Install plan (verify each command first)
```
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install uv git tmux tailscale sqlite colima docker
uv venv ~/agent/.venv && uv pip install mlx-lm litellm fastapi uvicorn playwright
mlx_lm.server --model <verified-4bit-model> --port 8080
sudo pmset -a sleep 0 disablesleep 1 autorestart 1
```
Then: create the `agent` user, write launchd plists in `~/Library/LaunchAgents` with `KeepAlive`, `tailscale up`, create the SQLite schema (tasks, agents, runs, events, claims), and start with one task type end to end before adding more. Phase order is as you specified: minimal system → coding → research → memory → multi-agent → 24/7 → remote → optimize. Test each phase with a fixed task suite, and roll back via git tags plus a snapshot of the DB.

## J. Do NOT install
Kubernetes; a separate vector DB server; Neo4j (initially); AutoGen/CrewAI/LangGraph as the core (they add abstraction over a simple queue; try them only if you need them); multiple full harnesses at once; GUI computer-use agents as the primary mechanism; dense 70B models; Ollama and LM Studio both running alongside MLX.

## K. Upgrade path
- **64 GB:** a ~70B-class MoE or dense 32B at higher quantization, plus a resident small model.
- **96–128 GB+:** several resident models, larger contexts, and a true parallel worker pool.
- **Dedicated GPU/server:** move inference to vLLM/SGLang on that server and keep the Mac as the orchestrator.

## Sources (stable primary landing pages, NOT fetched)
- https://github.com/ml-explore/mlx-lm (primary)
- https://github.com/ggml-org/llama.cpp (primary)
- https://github.com/BerriAI/litellm (primary)
- https://docs.anthropic.com/en/docs/claude-code (primary)
- https://github.com/sst/opencode (primary)
- https://aider.chat (primary)
- https://github.com/All-Hands-AI/OpenHands (primary)
- https://tailscale.com/kb (primary)
- https://github.com/asg017/sqlite-vec (primary)
- https://github.com/searxng/searxng (primary)
- https://playwright.dev (primary)
- https://huggingface.co/Qwen (primary, check for the current model line)

## Reasoning trace (not shown to raters)

NONE

## Run notes


