---
run_id: deepseek__fast__p1-v1__apicheck1
set: api_check
family: deepseek
vendor: DeepSeek
mode: fast
native_label: thinking off (enable_thinking=false)
channel: api
model_requested: deepseek-v4-pro-0813
model_returned: deepseek-v4-pro-0813
params:
  _stream: true
  enable_thinking: false
  _unreported_is_zero: true
max_tokens: 64000
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 1
date_run: '2026-10-06T12:03:29+00:00'
run_by: roshanaryal
finish_reason: stop
usage:
  input_tokens: 2504
  output_tokens: 6930
  reasoning_tokens: 0
latency_s: 104.59
harness_version: 0.1.0
---

## Final answer

**Model:** Claude Opus 4.5 (via API) · **Knowledge cutoff:** early 2025 · **Web browsing/tools:** Not enabled for this answer. I will answer from internal knowledge and explicitly flag where the ecosystem has moved past my cutoff, especially around the M6 chip and late-2025/2026 model releases.

**Important caveat:** The M6 chip and late-2025 frontier models post-date my reliable knowledge. I will give concrete guidance that is robust to model-version churn (the architecture matters more than the exact model name), and I will clearly mark items to verify against current benchmarks before you install.

---

## Decisions at a glance

| Layer | Best overall (Aug 2026 context) | Best for your hardware | What you should actually use |
|---|---|---|---|
| Local inference engine | **llama.cpp** (server mode) or **MLX/LM** | llama.cpp server + MLX for Apple-native dev models | **llama.cpp as workhorse; MLX for experimentation** |
| Coding/reasoning model (local) | Whatever current Qwen-Coder/DeepSeek-class model tops SWE-bench in 2026 | 14–32B dense MoE-class model at 4-bit MLX | **A 14–32B agentic coder at 4-bit, with ~16–32K ctx for routine work** |
| Small/fast model (routing, classification, summaries) | Qwen-3-4B/8B class or Llama-3.x-8B class | 4–8B at 4-bit | **One 4–8B model, always loaded** |
| LLM framework / agent runtime | LangGraph / Agno / LlamaIndex workflows (cutting edge) vs. **custom thin orchestrator** | Custom minimal orchestrator over vLLM/llama.cpp | **Custom orchestrator + LangGraph-style primitives, not a heavy framework** |
| Coding agent | Claude Code / Codex CLI / Cline / Aider (cloud-era) | Local-model coding agents | **Adapted Cline/Aider-style loop with local model + explicit permission layer** |
| Research agent | Deep Research clones | Local LiteLLM + search APIs + PDF tools | **Custom research pipeline with verified-citation discipline** |
| Persistent memory | SQLite + Markdown + optional vector index | SQLite + Markdown files; add embeddings later | **SQLite (metadata/graph) + Markdown (content) first** |
| Computer control | macOS user-level separation + command allowlists | Same | **Dedicated `agent` user + allowlisted tools, not full GUI automation** |
| Always-on | launchd + supervisor | launchd | **launchd + systemd-equivalent watchdog + queue on disk** |
| Remote access | Tailscale + local web UI | Tailscale | **Tailscale + authenticated local dashboard, no port-forwarding** |
| Task queue | Postgres/SQLite + worker pool; Celery/RQ style | SQLite-based queue + asyncio workers | **SQLite-backed durable queue, 2–4 concurrent workers** |

---

## 1. Local inference

**What matters for 32 GB M6:** useful tokens/hour, not model size. On Apple Silicon that means: quantized decoder models, modest context, high batch where possible, model swapping by task, and *not* trying to run a 70B.

**Realistic tier list for 32 GB unified memory:**

| Model tier | Size at 4-bit | Fits? | Role |
|---|---|---|---|
| 70B+ | 40 GB+ | No (system + KV + context won't fit) | Don't run locally |
| 27–32B dense / MoE | 16–22 GB | Yes, one at a time, tight | Heavy coding/reasoning bursts |
| 8–14B | 5–10 GB | Yes, one + small model | Daily driver coding |
| 3–4B | 2–3 GB | Always resident | Router, classification, quick checks |

**Context window:** KV cache on Apple Silicon grows fast. A 14B at 32K ctx can add 8–16 GB of KV depending on implementation. Practical settings for this machine:
- Routine coding: **16–32K context**
- Long-file analysis: **truncate/chunk + retrieval**, don't try 128K contexts on a 14B constantly.
- Keep the big context work for cloud bursts if ever needed.

**Engines:**
- **llama.cpp / llama-server**: mature, Metal-optimized, easy slot management, model swapping, embedding support. **Use this as the stable workhorse.**
- **MLX / MLX-LM**: Apple-native, memmap-friendly, great for development and rapid iteration; less mature server/concurrency story than llama.cpp historically, but very efficient. **Use for experimentation and for models published only in MLX.**
- **Ollama**: convenient but adds an abstraction layer and historically less control over slot/context than raw llama.cpp. Skip as primary; use if you value convenience over control.

**What to run locally (verify current names against benchmarks as of Aug 2026):**
- A current 14–32B agentic coding model known for function-calling and terminal use (historically Qwen-Coder family, DeepSeek-Coder, or fine-tunes thereof).
- A 3–8B generalist for fast operations (classification, routing, short summaries, command triage).

**Multiple models:** Keep one small model resident; load/unload the heavy coder per heavy session. Model swapping on Apple Silicon is fast enough (a few seconds) that it beats trying to keep two 14B models resident.

---

## 2. Agent runtimes / harnesses

**Market shape as of my knowledge, expected to be more mature by Aug 2026:**

- **LangGraph / LangChain:** complete but heavy; good for prototyping complex graphs, not ideal as your 24/7 spine.
- **Agno / PydanticAI / LlamaIndex workflows:** leaner, developer-friendly, well-typed.
- **CrewAI / AutoGen / MetaGPT:** multi-agent conveniences; often abstract away model control and make fine-grained permissioning harder.
- **Claude Code / Codex CLI / Cline / Aider:** coding-specific, not general orchestration.
- **Your own thin orchestrator:** SQLite queue + workers + tool wrappers + typed state.

**Recommendation:** Build a **thin custom chief/worker orchestrator** in Python (or TypeScript) where each agent is "role definition + model + tools + permission scope + context." Use a workflow library (LangGraph or PydanticAI workflows) *inside* individual complex agents if needed, but don't make the whole system depend on a heavy framework.

This gives you: exact model routing, permission per agent, durable queue, easy logging, and no dependency on a framework's opinionated agent loop.

---

## 3. Multi-agent architecture

**Key distinction:**
- **Logical agents** = definitions/configs + state in DB. You can have 100+; they cost almost nothing until invoked.
- **Concurrent inference processes** = actual loaded models generating tokens. On 32 GB, realistically **1–3 concurrent generation streams**, plus small-model routing.

**Best architecture for your hardware:**

```
Task queue (SQLite) → Scheduler → Worker pool (2–4 inference slots)
   → Model Router (load/unload models as needed)
   → Tool executor (terminal, filesystem, browser, search)
   → Memory (SQLite + Markdown + optional embeddings)
```

- **Coordinator/chief agent** reads the queue, plans, decomposes, spawns subagents.
- **Subagents** are cheap definitions; they run sequentially or in small parallel batches under a single model process where possible.
- **Swarm/hierarchical mixing:** a responsive chief with task-specific subagents is the reliable pattern; full peer swarms are less predictable and harder to observe.
- **Model routing decision:** a small classifier model (3–4B) classifies each task (code, research, summarize, classify, fact-check) and selects model + tools + context budget.
- **Queue discipline:** throttle heavy agents; batch small-model jobs; preempt when urgent interactive command arrives.

**Simulating 100 agents:** run them as queued, stateful definitions — not simultaneous LLM sessions. The user-visible effect is "many concurrent projects," not "100 GPUs worth of inference."

---

## 4. Coding agents

**As of my knowledge, the landscape is dominated by cloud-first agents (Claude Code, Codex CLI, Cline, Aider, Cursor). Local-model support exists but is less mature.**

For your system, the best raw loop to adapt:

```
understand repo → plan → edit → run tests → observe → debug → commit/worktree → repeat
```

- **Aider:** proven local-model support, Git-native, chunked context. Good engine borrow.
- **Cline/Claude Code architecture:** superior permission and plan/execute loops, but historically tied to specific frontier cloud models.
- **Your adaptation:** implement the loop yourself using llama.cpp server + your local coder model, with:
  - `git worktree` support using term "worktree" in my response for isolated branches
  - test-running as a tool
  - diff review before commit
  - hard context budget per iteration

**Why not install an existing coding agent as-is:** most assume a stronger model than your local one, or expect cloud keys. Your value comes from the permission layer + queue + memory, which existing tools don't give you.

---

## 5. Research agents

**Core problem: hallucinated citations.** The architecture that helps most:

- All research is done via **tool-calling**: search first, get URLs, fetch pages, extract text, then cite *only URLs/components actually retrieved*.
- **No citation is allowed unless the tool-chain actually fetched it.** Enforce in the prompt + schema: citations must map to fetched-source IDs.
- Store raw sources first, claims second, synthesis third.
- Use **PDF extraction** (pymupdf, Marker/Unstructured for layout-heavy PDFs) into Markdown, then chunk.
- For literature: arXiv/Semantic Scholar/OpenAlex APIs + those URLs.
- Evidence tracking: a `sources` table and `claims` table with source IDs and verification status: `unverified / verified / contradicted / unsupported`.
- Synthesis is a final step that may use a stronger model, but only reads from collected evidence store.

For web search locally, use a search API (paid or self-hosted SearXNG). SearXNG gives private meta-search; commercial APIs (Brave, Tavily, Exa) are more reliable for verified source URLs.

---

## 6. Persistent memory

**Start with boring, scalable infrastructure:**

- **SQLite** (file or WAL): projects, agents, tasks, runs, decisions, experiments, source registry, claims, logs metadata.
- **Markdown files** on disk: human-readable project notes, research reports, agent memos.
- **Embeddings/vector DB:** only when retrieval becomes clearly useful (hundreds+ documents). At first, SQLite full-text search + direct file reads is enough. Add `sqlite-vec` or Chroma later.
- **No need for knowledge graph on day one.** A graph only pays off with hundreds of entities; SQLite foreign keys cover most of it initially.

Storage: keep SQLite + Markdown on internal SSD for speed/reliability; large corpora and PDFs can live external.

---

## 7. Computer control

**Principle: broad capability, narrow blast radius.**

- **Dedicated macOS user `agent`** with a separate home directory.
- All tools wrapped in **allowlisted command libraries** (Python functions / small CLI), not raw shell by default.
- **Filesystem:** agent home/workspace by default; other project directories explicitly granted; `~/.ssh`, `~/Desktop`, `~/Documents`, `~/Library`, Dropbox etc. blocked by default.
- **Terminal:** allowlist of commands (git, python, node, uv, rg, cat, grep, mkdir, etc.) with explicit flags review for destructive patterns (`rm -rf`, `git push --force`, `sudo`, `shutdown`, `diskutil`, `security`, `passwd`).
- **Browser:** use a browser automation tool with a separate profile; block financial/personal domains in the default profile.
- **Secrets:** agent has no access to your credential store; use separate API keys where needed, kept in `agent` user's own keychain/`.env` with minimal scope.
- **Network isolation:** optional per-agent network policy; local agents default to localhost + allowlisted domains.
- **Sandboxing heavy arbitrary code:** prefer per-task cloned repos and ephemeral worktrees; for untrusted code, Docker or a lightweight VM. On Apple Silicon, `lima`/Colima or `containerd` gives container isolation without huge overhead.

**Approval policy (what needs human sign-off):**
- Destructive system operations
- Pushes to remote repos
- Any command containing credentials or security tools
- Installing system-level packages
- >N file deletions outside workspace
- Large external API spend beyond a threshold

**Fully autonomous (in workspace):**
- Reading project files
- Creating/editing files in workspace
- Running tests/builds
- Git branches/commits locally
- Search and fetch public web pages
- Writing docs/reports

---

## 8. Always-on operation

**Use macOS-native mechanisms:**

- **launchd LaunchAgent** for your supervisor/orchestrator, `KeepAlive`, `RunAtLoad`.
- **Durable task queue on disk** (SQLite) — tasks survive restarts.
- **Watchdog:** supervisor monitors worker heartbeats; on stall/crash, mark task retryable, reload model if needed.
- **Sleep prevention:** `caffeinate -s` during active runs; allow system sleep when idle to save power, with Wake-on-LAN or a scheduled wake if needed. A launchd job can call `pmset` sparingly.
- **Logging:** structured logs (JSON Lines) + rotation; keep raw logs on external SSD if large.
- **Crash recovery:** queue-based design means failed tasks stay in DB and retry with backoff. Model server restarts automatically.
- **Health endpoint:** local HTTP health check that remote dashboard can query.

---

## 9. Remote access

**Do not expose raw services to the public internet.**

- **Tailscale** (or Headscale self-hosted) as the network layer — encrypted, no open ports.
- **Local web dashboard** (e.g., a small FastAPI/Next.js UI) on `127.0.0.1`, reachable over Tailscale.
- **Authentication:** Tailscale identity + app-level token/TOTP.
- **Notifications:** Tailscale + app (e.g., ntfy.sh self-hosted or Pushover) for task completion/failure/approval requests.
- **Emergency stop:** `/stop`, `/pause`, `/kill-workers` endpoints; a separate kill script that flushes queue and terminates workers immediately.
- **Submission:** CLI or phone/web UI to enqueue tasks, view logs, approve dangerous ops.

This gives you: check progress, add tasks, see logs, approve actions — from phone/laptop anywhere, without port-forwarding.

---

## 10. Storage architecture

| Location | Contents | Why |
|---|---|---|
| Internal 512 GB | macOS, apps, orchestrator code, SQLite, Markdown memory, active project workspaces, current models (if fitting), small caches | Fast random I/O for DB and active editing |
| External 1 TB SSD | Model weights (large), datasets, PDFs, research corpora, old logs, backups, cached web dumps, container images, archives | Sequential/bulk data, lower-speed-tolerant mass storage |

**Notes:**
- Keep the DB and current workspace on internal SSD for low-latency agent loop; move completed projects to external.
- Model files can live externally if load time acceptable; on Apple Silicon loading from external SSD is usually fine after first load. Keep one active small model on internal for instant startup.
- Back up SQLite + Markdown + config to external SSD nightly and optionally to encrypted cloud.

---

# A. Recommended technology stack

| Layer | Recommended technology | Alternatives | Why |
|---|---|---|---|
| LLM runtime | llama.cpp server | MLX-LM, Ollama | Control, slots, swapping, Metal maturity |
| Fast model (routing/summary) | Qwen-3-4B/8B-class 4-bit | Llama-3.x-8B, Phi-class | Speed + reasonable quality at tiny size |
| Heavy coder (local) | Current 14–32B agentic coder 4-bit MLX/GGUF | DeepSeek/Qwen-Coder fine-tunes | Best tokens-to-quality/effort on your RAM |
| Orchestration spine | Custom Python asyncio + SQLite queue | LangGraph, Agno | Full control over routing/perms/queue |
| Workflow library (optional inside agents) | LangGraph or PydanticAI workflows | CrewAI | Complex multi-step graphs without global lock-in |
| Coding loop | Custom loop (Aider/Cline-style) | Aider, Cline with local model | Merge permission model + local model + worktree |
| Research | Custom pipeline: SearXNG/Search API → fetch → PDF extract → cite | Deep Research cloud clones | Citation verification is the moat |
| Memory | SQLite + Markdown | sqlite-vec, Chroma | Simple, durable, human-readable; add vectors later |
| Version control | Git + worktrees | — | Isolation per task |
| Scheduling/shepherding | launchd + custom supervisor | systemd (if Linux) | Native macOS, robust |
| Remote access | Tailscale + local web UI | Tailscale SSH + CLI | Encrypted, no port-forwarding |
| Browser automation | Playwright or Chrome DevTools Protocol with separate profile | Any browser agent | Site interaction + crawl control |
| PDF extraction | pymupdf; Marker/Unstructured for complex PDFs | — | Text + layout extraction |

---

# B. Complete architecture diagram

```
[Phone/Laptop anywhere]
       │ Tailscale (encrypted)
       ▼
[Mac mini — launchd keeps alive]
       │
[Remote dashboard / CLI / approval WebUI]
       │
[Supervisor (chief agent)]
   ├─ reads/writes Task Queue (SQLite)
   ├─ plans, decomposes, spawns subagents
   ├─ enforces permissions & approval policy
   ├─ writes/direct audit log
   ├─ routes models via Model Router
   └─ monitors heartbeats; retries on failure

[Model Router]
   ├─ small classifier model (always loaded) decides task type
   ├─ loads/unloads heavy coder model when needed
   └─ calls llama.cpp server (Metal)

[Worker Pool: 1–3 concurrent inference streams]
   └─ wraps subagent executions: coder, researcher, summarizer...

[Tool Layer — all permission-checked]
   ├─ Terminal (allowlisted executor)
   ├─ Filesystem (scoped to workspace + granted dirs)
   ├─ Browser (separate profile, domain allowlist)
   ├─ Search (SearXNG/API)
   ├─ PDF/Document parser
   ├─ Git (worktrees per task)
   └─ Experiment runner

[Persistent Memory]
   ├─ SQLite: projects, tasks, decisions, sources, claims, audit
   ├─ Markdown: notes/reports (human-readable)
   └─ (later) Vector index for retrieval

[Storage]
   ├─ internal: active workspace + SQLite + markdown + fast models
   └─ external: large models + datasets + PDFs + logs + backups
```

---

# C. Hardware/resource plan (expected)

**32 GB unified memory budget (indicative, not benchmarked):**

| Component | Typical | Peak |
|---|---|---|
| macOS + background | 8–10 GB | 12 GB |
| llama.cpp + small model (3–4B 4-bit) | 3–4 GB | 5 GB |
| Heavy coder (14–32B 4-bit, 16K ctx) | 14–20 GB | 22 GB |
| Workers/agent processes + tools | 2–3 GB | 4 GB |
| Browser/Playwright | 1–2 GB | 3 GB |
| Filesystem cache | 1–2 GB | 2 GB |

**Practical rule of thumb:**
- Keep macOS + small model + one heavy model ≤ ~28 GB; leave headroom.
- Run **1 heavy generation stream at a time**, or 2 if using a smaller heavy model with short context.
- Run **2–4 small-model stream** in parallel easily.
- Model swapping heavy coder in/out per burst is worthwhile; don't try to keep two heavy coders loaded.

**Storage:** internal holds active workspace + DBs + one small model; external holds large model files, corpora, logs.

---

# D. Agent architecture — 100+ logical agents without 100 LLMs

```
100+ logical agents = definitions in DB (role, model, tools, permissions, context budget)
                ↓ invoked →
Scheduler queries pending subagents
                ↓
Worker pool (2–4 inferences)
                ↓
Heavy tasks serialized on the heavy model; light tasks parallel on small model
```

- **Definitions:** each agent is a row: `agent_id, role_prompt, model_policy, tool_policy, permission_scope, context_budget, parent_agent`.
- **Instantiation** happens only when the scheduler spawns a task for that role.
- **Batching:** several light subagents can be evaluated sequentially within one small-model session.
- **Hierarchy:** chief/planner sees the project graph; workers handle slices; results return to chief; chief synthesizes and updates memory.

This yields the *experience* of many active agents without overcommitting memory or GPU.

---

# E. Model strategy

| Task | Model choice (verify current benchmarks) | Context budget | Notes |
|---|---|---|---|
| Planning/decomposition | Heavy coder/agentic model, 14–32B, 4-bit | 8–32K | Use only for non-trivial plans |
| Coding/refactoring | Strongest local coder at 14–32B | 16–32K | One heavy session at a time |
| Debugging | Same local coder, short focused context | 8–16K | Pull relevant trace/test excerpts only |
| Research/search/fetch | Small generalist 3–8B for URL/topic extraction | 8K | Tools do the real retrieval |
| Summarization/report synthesis | Heavy model if quality matters, else small | 8–32K | Use heavy for final reports |
| Classification/routing | Tiny 3–4B always loaded | 2–4K | Fast decisions |
| Fact/claim verification | Small/medium + strict citation tooling | 8–16K | Tool-verified citations only |

**Optional cloud bursts:** If a one-off frontier-quality task arises (a hard research synthesis, a very complex refactor), use a cloud API key *temporarily* with explicit budget cap. Keep the system useful without it.

---

# F. 24/7 architecture

- `launchd` LaunchAgent keeps supervisor and model server alive.
- Durable SQLite queue means in-flight tasks survive agent crashes and reboots.
- Supervisor treats each task as a state machine: `queued → running → verifying → done/retryable/failed`.
- Stuck workers are killed after timeout; tasks retried with backoff.
- Health endpoint + periodic ping to dashboard; failures logged and optionally notify your phone.
- Overnight mode: lower-priority background jobs run when CPU/memory headroom is high; `caffeinate` during active work, `pmset` schedule for sleep when idle.

---

# G. Remote-control architecture

- All remote access via **Tailscale**; no public ports.
- Local FastAPI dashboard binds to `127.0.0.1`, exposed only to Tailnet.
- Auth: Tailscale identity + app token/TOTP.
- Actions: submit task, view queue/logs, approve/reject high-risk ops, pause/resume/kill.
- Notifications via ntfy.sh (self-host optional) or Pushover.
- Emergency stop: authenticated `/pause` and `/kill` endpoints + separate local kill script.

---

# H. Security architecture

- **Dedicated `agent` macOS user**, not your personal user.
- **Tool allowlists**: terminal commands, filesystem paths, browser domains, network endpoints.
- **Workspace isolation**: each task gets its own directory/worktree; agent cannot touch `~/.ssh`, keychain, Documents, Photos by default.
- **Secrets**: separate minimal-scope keys for external APIs; never expose iCloud/personal accounts.
- **Destructive command guard**: intercept `rm -rf`, `sudo`, `shutdown`, `security`, `passwd`, `git push --force`, etc.; require human approval.
- **Human approval thresholds:** destructive ops, remote pushes, installing system packages, large API spend, deleting >N files.
- **Resource/time limits per task**: max tokens, runtime, CPU, disk writes.
- **Runaway-agent protection:** watchdog + task budgets + circuit breakers on repeated failures.
- **Audit log**: every tool call, model routing decision, file change is logged immutably (append-only table).

---

# I. Exact installation plan

**Phase 0: Foundations**
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# Core tools
brew install git python@3.12 uv ripgrep jq htop
# Tailscale
brew install --cask tailscale
# SearXNG optional for private search
# (Install via Docker/colima or brew/source)
```
- Create `agent` user and dedicated home.
- Create directories:
```
~/agent/
  config/
  workspace/
  memory/   # SQLite + markdown
  models/   # or symlink to external SSD
  logs/
  tools/
  tasks/
```

**Phase 1: Minimal working system**
- Install llama.cpp (`brew install llama.cpp` or build from source).
- Download small classifier (3–4B GGUF) + heavy coder (14–32B GGUF/MLX).
- Run llama-server with `--n-gpu-layers` tuned; verify Metal acceleration.
- Write a minimal Python orchestrator:
  - SQLite queue
  - one agent loop: read task → choose model → call llama-server → tool executor → write result
  - permission wrapper around terminal/filesystem
- Test: "Create a file hello.txt with content X in workspace." Then: "Summarize article Y using search tool."

**Phase 2: Autonomous coding**
- Add `git worktree` tool.
- Add test runner tool.
- Implement plan→edit→test→debug→commit loop.
- Add diff-before-commit and approval for remote push.
- Test on a real repo: fix a failing unit test autonomously.

**Phase 3: Research agents**
- Add search tool (SearXNG or API) with URL capture.
- Add web fetch (Playwright) + PDF extractor.
- Enforce citation discipline: claims must reference fetched source IDs.
- Test: "Research X, cite sources, identify contradictions, write report in Markdown."

**Phase 4: Persistent memory**
- Design SQLite schema (projects, tasks, runs, decisions, sources, claims, audit).
- Write memory tools: remember, recall, update project state.
- Keep human-readable Markdown exports.
- Test: across two sessions, recall the decision history of a project.

**Phase 5: Multi-agent orchestration**
- Agent registry table; role/prompt/tool/permission per agent.
- Scheduler with worker pool; model router.
- Small batch jobs on small model; heavy jobs serialized.
- Test: spawn 20+ logical subagents on 3 concurrent inference streams without OOM.

**Phase 6: 24/7 operation**
- launchd plist for supervisor KeepAlive.
- Health checks + auto-restart.
- Test: kill the supervisor; verify restart + queue recovery.

**Phase 7: Remote access**
- Add FastAPI dashboard on localhost; protect with token + Tailscale.
- Mobile-friendly UI: queue, logs, approvals, pause/kill.
- Add ntfy notifications.
- Test from phone on cellular.

**Phase 8: Advanced optimization**
- Add embeddings only if retrieval quality demands it.
- Model swap tuning.
- Night jobs for low-priority research/analysis.
- Add cloud API burst capability with hard budget.

**Rollback:** keep config in Git; snapshot SQLite nightly; keep prior GGUF versions until new ones validated.

---

# J. What NOT to install

- **Ollama** (as primary): adds an abstraction layer that reduces slot/context/swap control. Use llama.cpp directly.
- **Heavy multi-agent frameworks (CrewAI/AutoGen/MetaGPT as the spine):** too opinionated, less transparent, harder to enforce your permission model.
- **Full Kubernetes/Docker Swarm on one Mac:** overkill for 32 GB; containers only for untrusted code.
- **Separate vector DB (Pinecone/Weaviate) initially:** premature; SQLite + FTS is enough until your corpus is large.
- **Knowledge graph DB (Neo4j) initially:** premature; foreign keys cover early needs.
- **GUI automation tools (computer-use vision models) for daily use:** brittle and high-risk; use them only for rare specific tasks.
- **Multiple heavy coding models resident simultaneously:** memory waste; swap per burst instead.
- **Direct port-forwarding of your dashboard:** use Tailscale instead.

---

# K. Future upgrade path

**Moving to 64/96/128+ GB unified memory:**
- Keep a 32–70B coder resident longer; run 2–3 heavy streams.
- Increase default context windows substantially.
- Add a local vision/OCR model for document-heavy research.
- Run embedding models locally and vector DB without swapping.
- Consider a larger MoE model as daily driver.

**Adding a dedicated GPU/server:**
- Run heavy inference remotely on the GPU box over Tailscale.
- Use Mac mini as low-latency controller/dashboard and fast-model inference node.
- Move SQLite/Markdown/queue to the server with backups; Mac becomes the edge/UI device.
- Evaluate vLLM or SGLang on the GPU server for batching/concurrency.

---

## Sources

Primary:
- llama.cpp GitHub — https://github.com/ggml-org/llama.cpp
- MLX — https://github.com/ml-explore/mlx
- MLX-LM — https://github.com/ml-explore/mlx-lm
- Aider — https://github.com/Aider-AI/aider
- Cline — https://github.com/cline/cline
- LangGraph — https://github.com/langchain-ai/langgraph
- PydanticAI — https://github.com/pydantic/pydantic-ai
- Tailscale — https://tailscale.com/
- SearXNG — https://github.com/searxng/searxng
- launchd man page — https://keith.github.io/xcode-man-pages/launchd.8.html
- SQLite docs — https://www.sqlite.org/docs.html

Secondary: Apple silicon ML/LLM community benchmarks, Ollama public docs (for comparison), Hugging Face model cards, indie SWE-bench/local LLM leaderboards (verify with current data as of Aug 2026).

**Note:** Because web browsing was off for this answer, version-specific details — especially regarding the M6 chip, current 2026 open-weights models, and tool-specific changelogs — must be verified against current primary sources before finalizing the install. The architecture, memory strategy, permission model, queue design, and storage split are stable recommendations for a 32 GB always-on agentic workstation.

## Reasoning trace (not shown to raters)

NONE

## Run notes


