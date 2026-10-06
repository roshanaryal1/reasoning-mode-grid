---
run_id: qwen__reasoning__p1-v1__apicheck1
set: api_check
family: qwen
vendor: Alibaba
mode: reasoning
native_label: thinking (enable_thinking=true)
channel: api
model_requested: qwen3.8-max
model_returned: qwen3.8-max
params:
  _stream: true
  enable_thinking: true
  _unreported_is_zero: true
max_tokens: 64000
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 1
date_run: '2026-10-06T12:01:44+00:00'
run_by: roshanaryal
finish_reason: stop
usage:
  input_tokens: 2634
  output_tokens: 37392
  reasoning_tokens: 23805
latency_s: 888.01
harness_version: 0.1.0
---

## Final answer

Model: Qwen3.8 | Knowledge cutoff: not exposed to me; reliable through late 2024, likely some 2025 ecosystem knowledge | Web browsing/tools: OFF

> Method note: I did **not** browse or verify live sources for 31 Aug 2026. I am answering from internal knowledge and stating that explicitly. I also cannot verify M6-specific benchmarks from training data. Therefore the design below is made decisive on stable constraints: **Apple Silicon Metal acceleration, 32 GB unified memory, macOS service model, and local-first autonomy**. Where a 2026-specific model release might supersede my pick, I give substitution rules rather than hedging the architecture.

## Decisions at a glance

| Layer | Final pick | Why |
|---|---|---|
| Local inference runtime | **llama.cpp `llama-server`** | Most mature Metal/GGUF path; fine-grained context/KV/quantization control; headless-friendly |
| Secondary inference runtime | **MLX** for experiments | Often excellent on Apple Silicon, but use llama.cpp as the stable service baseline |
| Primary deep local model | **Qwen3-30B-A3B-Instruct, 4-bit Q4_K_M GGUF** | Best practical quality/memory/speed balance for 32 GB; MoE active compute is favorable on base Apple Silicon |
| Coding executor | **Aider** wrapped by a custom supervisor | Git-native, repo-aware, local-model-friendly, lightweight enough for 32 GB |
| Optional heavy dev sandbox | **OpenHands** later, not day 1 | Strong autonomous dev environment, but heavier than ideal for your machine |
| Orchestration | **Custom Python supervisor + SQLite queue + LangGraph workflows** | Avoids heavyweight infra; durable enough; optimized for one machine |
| Model router | **LiteLLM proxy** | Clean local/cloud routing, fallbacks, budgets, OpenAI-compatible abstraction |
| Fast local model | **Qwen3-8B-Instruct Q4**; drop to **Qwen3-4B-Instruct Q4** if memory is tight | Routing, summarization, classification, light edits |
| Embedding model | **nomic-embed-text-v1.5 GGUF** | Small, strong enough, easy to run locally |
| Research architecture | **Custom evidence-grounded pipeline** using Semantic Scholar/OpenAlex/Crossref/arXiv + SearXNG/Brave + Docling/PyMuPDF | Best control over citations and hallucination prevention |
| Persistent memory | **Markdown + SQLite + FTS5 + sqlite-vec** | Minimal, robust, no premature vector DB infrastructure |
| Computer control | **Terminal + filesystem + Playwright browser only**, no GUI control by default | Highest reliability, lowest risk |
| Sandboxing | Dedicated macOS user + workspace ACLs + optional OrbStack/Colima containers | Practical isolation without giving the agent your whole life |
| Always-on | **launchd + pmset + healthchecks + task leases** | Native macOS recovery, no Kubernetes nonsense |
| Remote access | **Tailscale + SSH + local web dashboard + ntfy/Pushover alerts** | Private, simple, no public exposure |
| Storage split | Internal = active models/DB/workspaces; external = archive/papers/datasets/backups | Keeps latency-sensitive state on the internal SSD |
| What not to run | 100 simultaneous LLMs | You want 100 logical agents, not 100 model instances |

---

# 1. Local inference on a 32 GB M6 Mac mini

## 1.1 Hard constraints

Your bottleneck is not “can it load a model?” but:

- **Weights + KV cache + macOS + agent processes + browser/tools must stay under ~28–29 GB** before memory pressure becomes painful.
- Base M6 will have **less GPU headroom and memory bandwidth** than Pro/Max parts, so huge dense models are a bad trade.
- For autonomous work, **steady usable throughput under repeated tool loops** matters more than peak benchmark quality.

## 1.2 Inference runtime comparison

| Runtime | Verdict for you | Reason |
|---|---:|---|
| **llama.cpp / llama-server** | **Use** | Mature, Metal-accelerated, GGUF ecosystem, quantized KV cache, context control, OpenAI-compatible server, easy to run as a service |
| **MLX / mlx-lm** | Strong alternative | Very good Apple Silicon performance; excellent for experiments and some Qwen/MLX builds, but I would not make it the primary always-on service unless you personally benchmark it clearly ahead |
| **Ollama** | Do not use as primary | Easy, but less precise control over context, KV cache, parallelism, and service behavior |
| **LM Studio** | Do not use as primary | Nice GUI/model manager, not the best headless server foundation |
| **LocalAI** | Skip | Extra abstraction layer; more moving parts than needed on one machine |
| **llamafile** | Skip for this build | Great for quick portable runs, less ideal for a controlled production service |

## 1.3 What models to actually run

Do **not** choose the largest model that barely fits. Choose the model that produces the most completed work per hour.

### Primary deep model
**Pick: Qwen3-30B-A3B-Instruct, 4-bit Q4_K_M GGUF**

Why:
- Total parameter count gives stronger reasoning/coding than an 8B model.
- MoE with low active compute is much more sensible on a base M6 than a dense 32B if you care about throughput.
- Fits a 32 GB machine with a sane context window if KV cache is controlled.

Expected practical role:
- planning
- hard coding tasks
- debugging
- research synthesis
- final report generation

If a **Qwen3-Coder 30B-class variant** exists in verified GGUF form, prefer it for coding. If not, standard Qwen3-30B-A3B-Instruct is the right default.

### Dense alternative
**Qwen3-32B-Instruct Q4_K_M** is the fallback if:
- you value maximum local quality over speed,
- you accept slower iteration,
- you keep context modest.

But for your machine, I would still default to the MoE 30B-A3B class.

### Fast utility model
**Pick: Qwen3-8B-Instruct Q4_K_M**
- routing
- summarization
- classification
- small file edits
- draft research notes
- memory consolidation

If memory pressure appears when browser + tests + model are active, switch to:
**Qwen3-4B-Instruct Q4_K_M**

### Embedding model
**Pick: nomic-embed-text-v1.5 GGUF**
- lightweight
- good enough for code/document retrieval
- easy to serve locally

Optional later:
- **bge-m3** if multilingual retrieval matters
- **bge-reranker-v2-m3** if retrieval precision becomes a bottleneck

## 1.4 Quantization, context, concurrency

### Recommended settings
- **Weights:** Q4_K_M is the sweet spot
- **KV cache:** quantize if using llama.cpp (`q8_0` is a good default)
- **Context:**
  - fast model: 8k default
  - deep model: 16k default
  - avoid 32k+ unless the task truly requires it and nothing else heavy is running
- **Concurrency:**
  - deep model: **1 worker**
  - fast model: **1–2 workers** only when deep model is not loaded
  - embedding model: 1 worker
  - tool-only workers: 2–4 depending on CPU load

### Model loading strategy
Use **dynamic loading/unloading**:
- keep the **fast model resident**
- load the **deep model on demand**
- unload deep model after idle timeout (e.g., 5–10 minutes)
- do **not** try to keep many chat models resident simultaneously

This is much better than pretending you can run several large models at once.

## 1.5 Expected bottlenecks

The real bottlenecks will be:
1. **memory pressure**, not disk
2. **KV cache growth**
3. **browser + test tooling memory**
4. **thermal sustained-load throttling** on a small machine
5. **agent design** — a bad loop wastes more tokens than any model limitation

---

# 2. Agent runtimes / harnesses

You asked whether to use one existing harness, multiple complementary systems, or build a custom orchestration layer.

**Correct answer for your machine: build a thin custom control plane, use specialized executors underneath.**

A single off-the-shelf agent product will either:
- be too chatbot-like,
- be too heavy,
- be too cloud-oriented,
- or give you poor control over security and persistence.

## 2.1 Runtime/harness comparison

| System | Category | Verdict |
|---|---|---|
| **Aider** | coding executor | **Use** |
| **OpenHands** | full autonomous dev environment | Optional later; powerful but heavy |
| **SWE-agent** | issue-to-PR automation | Interesting, not the best general always-on base |
| **Goose** | extensible local agent | Watch it; not my primary for production stability |
| **LangGraph** | durable workflow engine | **Use inside custom control plane** |
| **Pydantic AI** | typed single-agent tool loops | Good, but LangGraph is better for long-lived workflows |
| **AutoGen / AG2** | conversational multi-agent | Too conversation-centric, less deterministic |
| **CrewAI** | role-based agents | Convenient, but too high-level and brittle for serious infrastructure |
| **Letta / MemGPT** | memory-centric agents | Interesting, but adds complexity before you need it |
| **smolagents** | lightweight code agents | Nice for small tasks, not the backbone |
| **Dify / n8n / Flowise** | low-code automation | Not the right core for serious filesystem/coding autonomy |

## 2.2 Recommended runtime architecture

Use **three layers**:

1. **Control plane**
   - custom Python service
   - SQLite task queue
   - approvals
   - policy enforcement
   - model lifecycle management
   - logging/audit

2. **Workflow layer**
   - **LangGraph** for durable multi-step pipelines:
     - coding task
     - research task
     - experiment task
     - documentation task

3. **Executors**
   - **Aider** for repo editing
   - **Playwright** for browser research
   - shell wrapper for commands
   - document parser pipeline for PDFs/Markdown

This gives you the best of both worlds:
- **strong autonomy**
- **strong control**

---

# 3. Multi-agent architecture on limited hardware

This is one of the most important design decisions in the whole system.

## 3.1 Key distinction

You do **not** want 100 model instances.

You want:
- **100+ logical agents**
- **1–3 model workers**
- **a queue**
- **role templates**
- **shared artifacts**

### Definitions
- **Logical agent** = persisted role, objective, permissions, memory scope, model tier
- **Worker** = actual process that borrows a model and executes one task slice
- **Task queue** = durable list of pending work with leases, retries, priorities
- **Model router** = chooses fast/deep/cloud based on task class and budget
- **Dynamic subagent** = newly created logical agent record from a template, not a new permanent daemon

## 3.2 Best topology for 32 GB

Use a **hierarchical coordinator/worker architecture**, not a free-form swarm.

Why:
- swarms on small hardware create redundant inference and context blowup
- hierarchical decomposition gives better cost control and easier recovery

Recommended topology:

- **Objective**
  - **Epic**
    - **Task**
      - **Step**

Example:
- Objective: “Improve reliability of repo X”
  - Epic: “Fix failing tests”
    - Task: “Diagnose test suite failures”
      - Step: “Run tests”
      - Step: “Read failure traces”
      - Step: “Patch code”
      - Step: “Verify tests”
      - Step: “Write summary”

## 3.3 Concurrency plan

### Practical worker pool
- **1 deep worker** using Qwen3-30B-A3B
- **1–2 fast workers** using Qwen3-8B or 4B
- **tool-only workers** for:
  - grep/search
  - file moves
  - PDF parsing
  - git operations
  - test execution

### Why this works
Most “agents” should be **waiting**, **reading**, or **writing artifacts**, not all doing LLM inference at the same time.

## 3.4 Dynamic agent creation

Do not manually define every agent.

Instead define **agent templates**, for example:
- repo-auditor
- test-runner
- dependency-updater
- literature-scout
- citation-verifier
- evidence-synthesizer
- doc-writer
- experiment-runner
- security-reviewer

When a coordinator sees a task type, it creates a new logical agent row with:
- role prompt
- allowed tools
- allowed directories
- model tier
- memory scope
- max steps
- max runtime

That is how you get 100+ logical agents without melting the machine.

---

# 4. Coding agents

## 4.1 What matters for you

You need:
- repository understanding
- file edits
- terminal execution
- tests
- debugging loops
- Git integration
- worktrees
- long-running autonomy
- local model support
- low memory overhead

## 4.2 Comparison

| Coding system | Verdict | Why |
|---|---|---|
| **Aider** | **Primary** | Git-native, repo-map aware, local-model friendly, lightweight, scriptable |
| **OpenHands** | Optional secondary | Strong end-to-end autonomy, but heavier and more infrastructure-like |
| **SWE-agent** | Secondary/research | Good at issue-to-PR flows, less ideal as your general workstation executor |
| **Cline / Roo Code** | Not primary | Excellent in IDE, but not the best headless autonomous backbone |
| **Claude Code / Codex-style cloud tools** | Not primary for your local-first requirement | Strong, but wrong default for private local autonomy |
| **Continue** | Not primary | IDE assistant, not autonomous enough |
| **Goose** | Watchlist | Promising, but I would not bet the core system on it yet |

## 4.3 Best coding architecture for your machine

Use:

**Aider + custom supervisor + Git worktrees + test wrapper**

### Workflow
1. Supervisor receives coding task
2. Create isolated git worktree:
   - `git worktree add ../worktrees/task-123 -b agent/task-123`
3. Generate repo context:
   - repo map
   - relevant docs
   - recent decisions
4. Run Aider with a strict instruction packet
5. Run tests/linters/builds
6. Feed failures back into a bounded retry loop
7. Produce patch + summary + follow-up tasks
8. Commit to agent branch only
9. Human approval required for:
   - merge to protected branch
   - force push
   - remote push if policy demands it

## 4.4 Why Aider wins here

Aider is not a full autonomous operating system — and that is good.

It gives you the **best coding executor** without forcing you into a heavy all-in-one agent platform. Your supervisor handles planning, delegation, persistence, and security.

---

# 5. Research agents

For autonomous research, **do not trust a generic agent to “just research”**. You need an evidence pipeline.

## 5.1 Best architecture

Use a **custom retrieval-grounded research pipeline**, not a single chat agent.

### Pipeline
1. **Question decomposition**
2. **Source discovery**
   - academic APIs
   - web search
3. **Fetch and snapshot**
4. **Parse to text**
5. **Chunk + embed + index**
6. **Evidence retrieval**
7. **Claim extraction**
8. **Claim verification**
9. **Synthesis with enforced citations**
10. **Report generation**

## 5.2 Best source discovery stack

### Academic/literature
Use APIs, not hallucinated memory:
- **Semantic Scholar**
- **OpenAlex**
- **Crossref**
- **arXiv API**
- **PubMed** if biomedical
- **Unpaywall** for OA lookup

### Web search
Best local/private:
- **SearXNG self-hosted**

Best convenient paid:
- **Brave Search API**
- **Tavily**
- **Serper**

For your requirements:
- start with **SearXNG** if you want maximum local control
- add **Brave/Tavily** as optional paid fallback when reliability matters

## 5.3 Document parsing

Use:
- **Docling** for strong document/table parsing
- **PyMuPDF** for fast PDF extraction
- **Marker** as an alternative/complement for PDF-to-Markdown

Recommendation:
- primary: **Docling**
- fallback: **PyMuPDF**
- optional: **Marker**

## 5.4 Preventing hallucinated citations

This is non-negotiable.

### Rules
1. The model may **never generate a bibliography from memory**
2. All references must come from the **source database**
3. Every claim must link to at least one stored evidence span
4. Every source must have:
   - URL or DOI or arXiv ID
   - retrieved timestamp
   - content hash where possible
5. A verifier agent checks:
   - does the cited text actually exist?
   - does it support the claim?
   - are contradictions recorded?

### Data model
Use tables like:
- `sources`
- `evidence_chunks`
- `claims`
- `claim_evidence_links`
- `contradictions`

This is how you avoid polished nonsense.

---

# 6. Persistent memory

## 6.1 What not to do

Do **not** start with:
- a giant vector database cluster
- a knowledge graph platform
- Postgres
- Elasticsearch
- a separate memory microservice

That is overbuilt for one machine.

## 6.2 Recommended memory architecture

### Start with:
1. **Filesystem Markdown memory**
   - human-readable
   - easy to diff
   - easy to audit

2. **SQLite**
   - structured task state
   - events
   - facts
   - source metadata
   - approvals

3. **SQLite FTS5**
   - keyword search

4. **sqlite-vec**
   - lightweight vector search

That is the right initial stack.

## 6.3 Memory split

| Memory type | Where it lives |
|---|---|
| Episodic task history | SQLite events table |
| Semantic facts | SQLite + Markdown |
| Project-specific memory | `memory/projects/<slug>/MEMORY.md` + DB rows |
| Global memory | curated Markdown + DB |
| Decision records | ADR-style Markdown |
| Research evidence | SQLite + filesystem artifacts |
| Semantic retrieval | sqlite-vec |

## 6.4 What to add later

Add only when needed:
- **LanceDB** if embedded vector scale grows
- **Qdrant** if you move to a server or many clients
- **Kuzu** or another graph DB only if relationship queries become genuinely important

For now:
**Markdown + SQLite + sqlite-vec is the correct answer.**

---

# 7. Computer control

You want maximum practical autonomy without handing over the keys to your personal life.

## 7.1 Best control strategy

Use this order:

1. **Terminal control**
2. **Filesystem control inside approved workspaces**
3. **Browser control via Playwright**
4. **GUI control only if absolutely necessary** — and even then, not by default

Why:
- terminal/filesystem are scriptable, auditable, and robust
- GUI automation is brittle and dangerous
- browser control is useful but must be isolated

## 7.2 Recommended isolation model

### Create a dedicated macOS user
Use a separate user like:
- `aiworker`

This user should:
- **not be admin**
- have access only to:
  - agent workspace
  - approved project directories
  - approved external volume
- have no default access to:
  - personal Documents
  - Mail
  - Messages
  - Photos
  - browser profiles with saved logins
  - financial files

### Workspace isolation
All autonomous writes happen under:
- `~/AgentLab/workspaces/`

Anything outside that requires approval.

## 7.3 Browser control

Use:
- **Playwright with Chromium**
- ephemeral profile
- no saved passwords
- no personal cookies
- strict download handling
- no automatic execution of downloaded files

Treat all web content as **untrusted input**.

## 7.4 Containers / VMs

Use containers for:
- untrusted test execution
- dependency isolation
- reproducible experiments

Recommended:
- **OrbStack** if you want the best Mac experience and are okay paying
- **Colima/Podman** if you want open-source/free

But do **not** make containers mandatory for every coding task, because host filesystem integration and performance matter.

---

# 8. Always-on operation

This is where many “agent” setups fail.

You need:
- service supervision
- crash recovery
- task persistence
- reboot survival
- sleep prevention
- watchdog behavior

## 8.1 Use macOS native mechanisms

### Service management
Use **launchd**, not ad hoc terminal sessions.

Run:
- supervisor as a LaunchDaemon/LaunchAgent
- model servers as child processes managed by the supervisor
- optional maintenance jobs as scheduled launchd tasks

### Power settings
Disable sleep:
- system sleep off
- disk sleep off
- display can sleep
- restart after power failure if possible

### Crash recovery
Design tasks with:
- leases
- heartbeats
- idempotent steps
- retry counts
- terminal failure states

If the machine reboots:
- launchd restarts supervisor
- supervisor reclaims stale leases
- queue resumes

## 8.2 Watchdog rules

You need:
- max runtime per task
- max steps per task
- max token budget
- repeated-action loop detection
- model server healthchecks
- automatic restart of hung workers

## 8.3 Sleep prevention

Use:
- `pmset`
- `caffeinate` where appropriate
- healthchecks to ensure the machine did not idle-sleep

---

# 9. Remote access

Do **not** expose your agent dashboard to the public internet.

## 9.1 Best remote architecture

Use:
- **Tailscale**
- SSH into the Mac mini
- local web dashboard bound to localhost/tailnet only
- notifications via ntfy or Pushover
- approvals via dashboard or CLI

This gives you:
- private remote control
- encrypted access
- no port forwarding
- phone/laptop access

## 9.2 Remote functions

You should be able to:
- view queue status
- submit tasks
- approve risky actions
- read logs
- stop all agents
- pause model loading
- trigger a report

## 9.3 Emergency stop

Provide three levels:
1. soft pause: stop new tasks
2. hard stop: terminate active workers
3. service stop: unload launchd service

Examples:
- dashboard button
- `ai-ctl stop-all`
- `launchctl bootout` for the supervisor

---

# 10. Storage architecture

## 10.1 Internal 512 GB SSD

Put latency-sensitive and critical state here:
- macOS
- applications
- orchestrator code
- SQLite databases
- active model weights
- active repos/worktrees
- recent logs
- caches

Do **not** put your primary database on the external drive if you can avoid it.

## 10.2 External 1 TB SSD

Put bulk/archive here:
- model archive
- papers
- datasets
- snapshots
- backups
- old logs
- git bare mirrors
- large research artifacts

## 10.3 Practical split

| Data class | Location |
|---|---|
| active models | internal |
| archived models | external |
| SQLite DBs | internal |
| active git worktrees | internal |
| large repos/mirrors | external if space is tight |
| papers/PDFs | external |
| datasets | external |
| logs | internal recent, external archive |
| backups | external |

## 10.4 Important caveat

If the external SSD is:
- Thunderbolt / high-speed USB: fine for archives and papers
- slow SATA-style USB: do not run databases or active models from it

Also:
- format external as **APFS encrypted**
- give it a stable mount name
- make the system degrade gracefully if it is missing

---

# A. Recommended technology stack

## A1. Market comparison matrix

| Category | Best overall | Best for your M6 32GB | Best open-source | Best lightweight | Best mature/stable | Best cutting-edge | What you should actually use |
|---|---|---|---|---|---|---|---|
| Local inference runtime | llama.cpp | llama.cpp | llama.cpp | Ollama | llama.cpp | MLX | **llama.cpp** |
| Apple-native inference alternative | MLX | MLX | MLX | MLX | llama.cpp | MLX | **MLX for experiments** |
| Deep local model class | strongest available 30B-class MoE / dense 32B | Qwen3-30B-A3B | Qwen3 / Llama / Mistral families | Qwen3-4B/8B | Llama/Qwen families | newest Qwen3 variants | **Qwen3-30B-A3B Q4** |
| Fast utility model | 7–8B instruct class | Qwen3-8B | Qwen3-8B | Qwen3-4B / Phi-mini | Llama 8B class | newest small instruct | **Qwen3-8B, fallback 4B** |
| Coding executor | OpenHands / Aider depending on scope | **Aider** | Aider | Aider | Aider | OpenHands | **Aider** |
| Heavy autonomous dev environment | OpenHands | OpenHands (optional) | OpenHands | not applicable | SWE-agent/Aider | OpenHands | **Optional later** |
| Orchestration | custom control plane + LangGraph | custom + LangGraph | LangGraph | Pydantic AI | SQLite + launchd | LangGraph/MCP ecosystems | **Custom + LangGraph** |
| Multi-agent framework | not one framework | custom queue | LangGraph | Pydantic AI | custom queue | agent ecosystem | **Custom queue** |
| Memory | Markdown + SQLite + vector extensions | Markdown + SQLite + sqlite-vec | SQLite/sqlite-vec | SQLite | SQLite | Letta/Mem0 style | **Markdown + SQLite + sqlite-vec** |
| Research pipeline | evidence-grounded custom | custom | custom + SearXNG | API-based search | Crossref/Semantic Scholar | agentic RAG | **Custom evidence pipeline** |
| Browser control | Playwright | Playwright | Playwright | curl/httpx | Playwright | browser-use style | **Playwright** |
| Remote access | Tailscale | Tailscale | WireGuard/Headscale | Tailscale | Tailscale | Tailnet serve | **Tailscale** |
| Notifications | ntfy / Pushover depending on needs | ntfy + optional Pushover | ntfy | ntfy | Pushover | self-hosted gotify | **ntfy, Pushover optional** |
| Queue/durable execution | SQLite leases + LangGraph | SQLite leases | SQLite | SQLite | SQLite | Temporal | **SQLite** |
| Sandbox | dedicated user + containers | dedicated user + OrbStack/Colima | Colima/Podman | macOS user | dedicated user | VM/container hybrid | **dedicated user + optional containers** |

## A2. Recommended stack table

| Layer | Recommended technology | Alternatives | Why |
|---|---|---|---|
| Inference server | llama.cpp `llama-server` | MLX, Ollama | Best control and maturity |
| Primary model | Qwen3-30B-A3B-Instruct Q4 | Qwen3-32B, DeepSeek-R1 distill 32B | Best speed/quality fit for 32 GB |
| Fast model | Qwen3-8B-Instruct Q4 | Qwen3-4B, Phi-mini | Resident utility model |
| Embeddings | nomic-embed-text-v1.5 | bge-m3 | Lightweight local retrieval |
| Model router | LiteLLM proxy | custom router | Easy local/cloud abstraction |
| Control plane | custom Python service | Temporal, Prefect | Right-sized for one machine |
| Workflow engine | LangGraph | Pydantic AI, AutoGen | Durable multi-step flows |
| Coding agent | Aider | OpenHands, SWE-agent | Lightweight, Git-native |
| Research pipeline | custom source/evidence system | GPT-Researcher, STORM | Prevents citation hallucinations |
| Memory store | SQLite + Markdown + sqlite-vec | Chroma, Qdrant, Letta | Minimal and robust |
| Browser automation | Playwright | Selenium | Best modern headless control |
| Service manager | launchd | systemd-style alternatives | Native macOS |
| Remote access | Tailscale | WireGuard | Private and practical |
| Notifications | ntfy | Pushover, Gotify | Self-hostable and simple |
| Container sandbox | OrbStack or Colima | Docker Desktop | Optional isolation layer |

---

# B. Complete architecture diagram

```text
                 +---------------------+
                 |  Phone / Laptop     |
                 +----------+----------+
                            |
                    Tailscale (private)
                            |
                 +----------v----------+
                 |  Remote Access      |
                 |  SSH / Dashboard /  |
                 |  Notifications      |
                 +----------+----------+
                            |
                 +----------v----------+
                 |  API/Gateway        |
                 |  FastAPI local UI   |
                 +----------+----------+
                            |
                 +----------v----------+
                 |  Supervisor         |
                 |  - task queue       |
                 |  - policies         |
                 |  - approvals        |
                 |  - budgets          |
                 |  - model lifecycle  |
                 +----+-----+-----+----+
                      |     |     |
          +-----------+     |     +-----------+
          |                 |                 |
+---------v------+  +-------v-------+  +------v-------+
| LangGraph flows|  | Tool workers  |  | Model router |
| coding/research|  | shell/git/pdf |  | LiteLLM      |
+---------+------+  +-------+-------+  +------+-------+
          |                 |                  |
          |                 |          +-------v--------+
          |                 |          | Local models   |
          |                 |          | llama.cpp      |
          |                 |          | deep/fast/emb  |
          |                 |          +----------------+
          |                 |
+---------v-----------------v----------+
| Executors                            |
| - Aider                              |
| - Playwright                         |
| - Docling / PyMuPDF                  |
| - Git worktree manager               |
| - Test runner                        |
+------------------+-------------------+
                   |
        +----------v-----------+
        | Persistent state     |
        | SQLite + Markdown    |
        | FTS5 + sqlite-vec    |
        +----------------------+
```

---

# C. Hardware/resource plan

## C1. Approximate RAM allocation

| Component | Target budget |
|---|---:|
| macOS + system services | 5–7 GB |
| Supervisor/router/queue | 0.5–1.5 GB |
| Agent/tool workers | 1–3 GB |
| Browser when used | 2–4 GB |
| SQLite / retrieval / parsers | 0.5–1.5 GB |
| Fast model weights | 3–6 GB |
| Deep model weights | 16–20 GB |
| KV cache | 2–5 GB |
| Filesystem cache | variable/reclaimable |

## C2. Practical operating modes

### Mode A: Fast mode
- fast model resident
- deep model unloaded
- browser allowed
- best for:
  - routing
  - light edits
  - research fetching
  - summarization

### Mode B: Deep mode
- deep model loaded
- fast model optionally unloaded
- browser minimized or closed
- best for:
  - planning
  - hard coding
  - synthesis

## C3. Concurrency limits

| Work type | Recommended concurrency |
|---|---:|
| deep LLM worker | 1 |
| fast LLM worker | 1–2 only if deep unloaded |
| embedding worker | 1 |
| shell/git/file workers | 2–4 |
| browser sessions | 1 at a time |
| test/build jobs | 1–2 depending thermals |

## C4. Storage plan

### Internal 512 GB
- OS + apps: 60–100 GB
- active models: 40–70 GB
- repos/worktrees: 50–100 GB
- DB/logs/cache: 5–15 GB
- keep 15–20% free

### External 1 TB
- model archive
- papers
- datasets
- backups
- old logs
- large snapshots

---

# D. Agent architecture for 100+ logical agents

## D1. Core principle

**Agents are records, not processes.**

A logical agent is:
- a role definition
- a permission profile
- a memory scope
- a model tier
- a budget
- a task assignment

It does **not** need its own dedicated LLM process.

## D2. Queue model

Use SQLite tables such as:

- `agents`
- `tasks`
- `task_events`
- `approvals`
- `policies`
- `models`
- `budgets`

### Task states
- `pending`
- `leased`
- `running`
- `waiting_approval`
- `waiting_human`
- `succeeded`
- `failed`
- `cancelled`

## D3. Worker pool design

### Worker classes
- `deep_worker`
- `fast_worker`
- `tool_worker`
- `browser_worker`

### Scheduling rules
- deep tasks serialize
- fast tasks can run limited parallelism
- tool-only tasks can run more freely
- browser tasks should usually serialize
- approvals block the task, not the whole system

## D4. Dynamic subagent creation

When a coordinator determines a task requires specialization:
1. choose template
2. create agent row
3. attach scoped memory
4. attach tool ACL
5. enqueue first task
6. terminate logical agent when done or archive for memory

This lets you have:
- 100+ logical agents
- but only a few active inference consumers

## D5. Best architecture for your hardware

Use:
**hierarchical coordinator + queue + specialized templates + shared worker pool**

Do **not** use:
- peer-to-peer swarm chatter
- one process per agent
- one model instance per agent

---

# E. Model strategy

## E1. Local model assignments

| Task | Recommended local model | Notes |
|---|---|---|
| High-level planning | Qwen3-30B-A3B | Use deep mode |
| Complex coding | Qwen3-30B-A3B | If Qwen3-Coder variant exists, prefer it |
| Debugging | Qwen3-30B-A3B | Feed minimal reproducible evidence |
| Code review | Qwen3-30B-A3B | Use diff + test results |
| Research synthesis | Qwen3-30B-A3B | Only from retrieved evidence |
| Summarization | Qwen3-8B | Fast mode |
| Classification/routing | Qwen3-8B or Qwen3-4B | Prefer rules first |
| Memory consolidation | Qwen3-8B | Batch offline |
| Documentation generation | Qwen3-8B or 30B depending quality need | Use repo facts |
| Embeddings | nomic-embed-text-v1.5 | Separate endpoint |

## E2. Cloud fallback strategy

Local-first, but cloud is genuinely useful for:
- very hard reasoning tasks
- large-scale cross-file refactors
- difficult research synthesis
- occasional failure recovery when local model loops

Recommended optional cloud classes:
- top-tier reasoning/coding API for hard tasks
- strong general API for synthesis
- search API if self-hosted search is flaky

Rules:
- never send secrets
- redact sensitive paths if possible
- require explicit policy opt-in per task class
- enforce budget caps

---

# F. 24/7 architecture

## F1. Core services

Run these as managed services:
1. supervisor
2. model servers (spawned by supervisor)
3. dashboard/API
4. notification service (optional)
5. Tailscale

## F2. Recovery design

### If a worker crashes
- supervisor detects lost heartbeat
- lease expires
- task requeued or failed depending retry policy

### If a model server crashes
- healthcheck fails
- supervisor restarts it
- active task is marked retryable

### If the machine reboots
- launchd restarts supervisor
- supervisor reads SQLite queue
- stale leases reclaimed
- background work resumes

## F3. Persistence requirements

Every unit of work must be:
- queued before execution
- checkpointed during long workflows
- resumable after restart
- auditable in logs

## F4. Recommended macOS settings

Use:
- disable system sleep
- disable disk sleep
- allow display sleep
- restart after power failure if supported
- keep machine plugged into reliable power
- ideally use a UPS

---

# G. Remote-control architecture

## G1. Recommended remote stack

- **Tailscale** for private networking
- **SSH** for direct control
- **local FastAPI dashboard** for status/approvals
- **ntfy** for alerts
- optional **Pushover** for high-reliability mobile notifications

## G2. Remote operations

You should support:
- submit task
- pause queue
- resume queue
- approve action
- deny action
- kill task
- kill all
- view logs
- view current model state
- request summary report

## G3. Exposure rules

- bind web services to localhost or tailnet only
- no public ports
- no direct cloud webhook ingress unless explicitly chosen
- require authentication for all control operations
- log all remote actions

---

# H. Security architecture

## H1. Trust model

The agent is:
- highly autonomous inside approved workspaces
- untrusted outside them
- never implicitly trusted with personal data, credentials, finance, or destructive operations

## H2. Zones

### Zone 1: Fully autonomous
- read/write inside `AgentLab/workspaces`
- local git branch creation
- running tests in approved project
- local file analysis
- local research artifact storage

### Zone 2: Logged but allowed
- repo cloning
- dependency installation inside project virtualenv/container
- local model loading/unloading
- report generation

### Zone 3: Approval required
- writes outside workspace
- any `sudo`
- package installs outside isolated env
- network requests involving credentials
- git push to protected branches
- force push
- deleting large numbers of files
- modifying launchd services
- changing security policy
- cloud API use above budget threshold
- sending email/message/notification with sensitive content

### Zone 4: Forbidden by default
- access to personal financial files
- access to password managers/keychains
- reading personal Messages/Mail
- disabling security controls
- destructive disk operations
- remote exposure of services to internet

## H3. Command controls

Use a wrapper executor that:
- logs every command
- enforces timeout
- enforces cwd restrictions
- blocks dangerous patterns
- captures stdout/stderr hashes
- requires approval for policy-matched commands

Examples of deny/approve patterns:
- `sudo`
- `rm -rf`
- `diskutil eraseDisk`
- `git push --force`
- `chmod -R 777`
- `curl | sh`
- writes to `/Library`
- changes to `~/Library/Keychains`

## H4. Secrets management

Do not store secrets in agent memory.

Use:
- macOS Keychain only where necessary and isolated
- short-lived environment injection after approval
- SSH deploy keys with minimal repo permissions
- no general-purpose API keys unless explicitly enabled

## H5. Runaway protection

Every task should have:
- max wall-clock time
- max steps
- max model tokens
- max cloud spend
- repeated output detection
- repeated failed command detection
- automatic suspension on policy violation

## H6. Kill switch

Implement:
- `STOP` file
- dashboard stop button
- `ai-ctl stop-all`
- launchd unload command

---

# I. Exact installation plan

Below is the practical roadmap. I am giving decisive choices, but because I have no live tool access, treat exact package versions as “latest stable at install time.”

## Directory structure

Create this as the base layout:

```text
/Users/aiworker/AgentLab/
  bin/
  config/
  control/
    control.db
  memory/
    global/
    projects/
  research/
    sources/
    pdfs/
    snapshots/
    reports/
  workspaces/
    repos/
    worktrees/
    tmp/
  models/
    active/
    archive/
  logs/
```

External volume:
```text
/Volumes/AgentVault/
  backups/
  models-archive/
  papers/
  datasets/
  git-mirrors/
  logs-archive/
```

---

## Phase 1 — Minimal working system

### Goal
Local model + local API + simple task execution.

### Technologies
- Homebrew
- uv
- llama.cpp
- LiteLLM
- SQLite
- Qwen3 models

### Commands

```bash
# 1. Install Xcode CLI tools
sudo xcode-select --install

# 2. Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 3. Install base tools
brew install git uv sqlite ripgrep fd tree-sitter htop

# 4. Install llama.cpp
# If the formula name differs on your system, install current llama.cpp via Homebrew or build from source.
brew install llama.cpp

# 5. Install LiteLLM proxy
uv tool install 'litellm[proxy]'

# 6. Install Hugging Face CLI
uv tool install huggingface_hub
```

### Download models
Use verified GGUF sources. Example pattern:

```bash
huggingface-cli download Qwen/Qwen3-30B-A3B-Instruct-GGUF \
  --include "*Q4_K_M.gguf" \
  --local-dir /Users/aiworker/AgentLab/models/active

huggingface-cli download Qwen/Qwen3-8B-Instruct-GGUF \
  --include "*Q4_K_M.gguf" \
  --local-dir /Users/aiworker/AgentLab/models/active

huggingface-cli download nomic-ai/nomic-embed-text-v1.5-GGUF \
  --include "*Q8_0.gguf" \
  --local-dir /Users/aiworker/AgentLab/models/active
```

### Test deep model manually

```bash
llama-server \
  -m /Users/aiworker/AgentLab/models/active/Qwen3-30B-A3B-Instruct-Q4_K_M.gguf \
  --host 127.0.0.1 \
  --port 8081 \
  --n-gpu-layers 999 \
  --ctx-size 16384 \
  --parallel 1 \
  --cache-type-k q8_0 \
  --cache-type-v q8_0 \
  --jinja
```

### Test fast model manually

```bash
llama-server \
  -m /Users/aiworker/AgentLab/models/active/Qwen3-8B-Instruct-Q4_K_M.gguf \
  --host 127.0.0.1 \
  --port 8082 \
  --n-gpu-layers 999 \
  --ctx-size 8192 \
  --parallel 2 \
  --cache-type-k q8_0 \
  --cache-type-v q8_0 \
  --jinja
```

### LiteLLM config example

`/Users/aiworker/AgentLab/config/litellm.yaml`

```yaml
model_list:
  - model_name: deep-local
    litellm_params:
      model: openai/deep-local
      api_base: http://127.0.0.1:8081/v1
      api_key: local
  - model_name: fast-local
    litellm_params:
      model: openai/fast-local
      api_base: http://127.0.0.1:8082/v1
      api_key: local
```

### Run proxy

```bash
litellm --config /Users/aiworker/AgentLab/config/litellm.yaml --port 4000
```

### Test
- send a chat completion request to LiteLLM
- verify deep and fast endpoints respond
- verify memory usage stays sane

### Common failures
- wrong model path
- insufficient RAM
- context too large
- Metal not fully offloaded

### Rollback
- stop servers
- remove model files
- nothing persistent is affected yet

---

## Phase 2 — Autonomous coding

### Goal
Aider + git worktrees + test loop.

### Technologies
- Aider
- Git
- ripgrep
- tree-sitter
- supervisor wrapper

### Commands

```bash
uv tool install aider-chat
aider --version
```

### Aider config example

`/Users/aiworker/AgentLab/config/aider.conf.yml`

```yaml
model: openai/deep-local
openai-api-base: http://127.0.0.1:4000/v1
openai-api-key: local
auto-commits: false
```

### Coding workflow
1. clone repo into `workspaces/repos/<repo>`
2. create worktree:
```bash
git -C /Users/aiworker/AgentLab/workspaces/repos/<repo> \
  worktree add ../../worktrees/task-001 -b agent/task-001
```
3. run Aider inside the worktree
4. execute tests
5. feed failure output back
6. commit only after verification

### Test
- use a toy repo with intentional failing test
- ask agent to fix it
- verify branch, patch, test pass

### Common failures
- model loops on bad edits
- tests not deterministic
- repo too large for context

### Rollback
- delete worktree
- discard agent branch
- no impact on main branch

---

## Phase 3 — Research agents

### Goal
Evidence-grounded research with citations.

### Technologies
- Docling
- PyMuPDF
- SearXNG or Brave/Tavily
- Semantic Scholar/OpenAlex/Crossref/arXiv
- SQLite evidence store

### Commands

```bash
uv tool install docling
uv pip install pymupdf requests beautifulsoup4
```

Optional self-hosted search:

```bash
brew install --cask orbstack
docker run -d --name searxng -p 127.0.0.1:8888:8080 searxng/searxng
```

### Research flow
1. create source records from APIs
2. download PDFs/HTML snapshots
3. parse to Markdown/text
4. chunk and embed
5. retrieve only stored evidence
6. synthesize report with source IDs

### Test
- ask for a comparison of 3 papers
- verify every claim has a stored evidence chunk
- verify no model-generated bibliography

### Common failures
- paywalled PDFs
- bad PDF extraction
- search engine rate limits

### Rollback
- delete research artifacts
- drop research DB tables
- rerun pipeline

---

## Phase 4 — Persistent memory

### Goal
Remember projects, decisions, and evidence.

### Technologies
- SQLite
- FTS5
- sqlite-vec
- Markdown memory files

### Minimal schema idea

```sql
CREATE TABLE agents(id TEXT PRIMARY KEY, name TEXT, template TEXT, config_json TEXT);
CREATE TABLE tasks(id TEXT PRIMARY KEY, parent_id TEXT, status TEXT, input_json TEXT, output_json TEXT);
CREATE TABLE task_events(id INTEGER PRIMARY KEY, task_id TEXT, kind TEXT, payload_json TEXT, created_at TEXT);
CREATE TABLE memory_facts(id INTEGER PRIMARY KEY, scope TEXT, content TEXT, source_path TEXT, created_at TEXT);
CREATE TABLE sources(id INTEGER PRIMARY KEY, url TEXT, doi TEXT, arxiv_id TEXT, title TEXT, metadata_json TEXT);
CREATE TABLE evidence(id INTEGER PRIMARY KEY, source_id INTEGER, chunk_text TEXT, hash TEXT);
```

### Implementation
- use one `control.db`
- use FTS5 virtual tables for text search
- add `sqlite-vec` for embedding search
- write memory summaries after task completion

### Test
- finish a task
- ask later: “what did we decide about X?”
- verify answer cites memory record

### Common failures
- overwriting good memory with bad summaries
- embedding drift after model swap

### Rollback
- restore SQLite backup
- restore memory folder from git

---

## Phase 5 — Multi-agent orchestration

### Goal
100+ logical agents, limited physical workers.

### Technologies
- SQLite queue
- LangGraph
- custom worker pool

### Commands

```bash
cd /Users/aiworker/AgentLab
uv init control-plane
cd control-plane
uv add fastapi uvicorn sqlalchemy aiosqlite apscheduler httpx litellm langgraph pydantic pyyaml
```

### Key design
- agent templates in config
- tasks table with leases
- worker processes check out tasks
- model router chooses tier
- dynamic subagents are new rows, not new daemons

### Test
- create 100 logical agents in DB
- enqueue 100 small tasks
- verify only 1–3 run at a time
- verify queue drains correctly

### Common failures
- lease starvation
- duplicate execution
- context bloat in coordinator

### Rollback
- reset queue DB
- restore previous supervisor config

---

## Phase 6 — 24/7 operation

### Goal
Survive reboots and crashes.

### Technologies
- launchd
- pmset
- log rotation
- healthchecks

### Example LaunchDaemon plist

`/Library/LaunchDaemons/local.ai.supervisor.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>local.ai.supervisor</string>
  <key>UserName</key>
  <string>aiworker</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/aiworker/AgentLab/bin/ai-supervisor</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/Users/aiworker/AgentLab</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <dict>
    <key>SuccessfulExit</key>
    <false/>
  </dict>
  <key>ThrottleInterval</key>
  <integer>30</integer>
  <key>StandardOutPath</key>
  <string>/Users/aiworker/AgentLab/logs/supervisor.out.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/aiworker/AgentLab/logs/supervisor.err.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/bin:/bin</string>
  </dict>
</dict>
</plist>
```

Load it:

```bash
sudo launchctl bootstrap system /Library/LaunchDaemons/local.ai.supervisor.plist
```

### Power settings

```bash
sudo pmset -a sleep 0 disksleep 0 displaysleep 10
sudo pmset -a womp 1
sudo systemsetup -setrestartfreeze on
```

### Test
- reboot machine
- verify supervisor restarts
- verify queue resumes
- kill worker and verify recovery

### Common failures
- FileVault blocks headless boot until local unlock
- Tailscale not up early enough
- external disk not mounted

### Rollback
- `launchctl bootout` the plist
- restore prior power settings

---

## Phase 7 — Remote access

### Goal
Secure control from phone/laptop.

### Technologies
- Tailscale
- SSH
- local dashboard
- ntfy

### Commands

```bash
brew install --cask tailscale
sudo systemsetup -setremotelogin on
```

Then:
- log into Tailscale
- restrict Remote Login to `aiworker`
- expose dashboard only via tailnet or SSH tunnel

Optional notification server:

```bash
brew install ntfy
```

### Test
- from phone over tailnet:
  - view dashboard
  - submit task
  - approve action
  - stop all

### Common failures
- Tailscale not running at boot
- SSH allowed for wrong users
- dashboard bound to all interfaces by accident

### Rollback
- disable Remote Login
- remove Tailscale
- bind services back to localhost only

---

## Phase 8 — Advanced optimization

### Goal
Squeeze useful work per hour.

### Optimize
- benchmark llama.cpp vs MLX on your exact machine
- tune context window
- tune KV cache quantization
- add reranker if retrieval is weak
- batch memory consolidation overnight
- cache repeated repo maps
- move large artifacts to external SSD

### Useful monitoring
- `top`
- `htop`
- `vm_stat`
- `memory_pressure`
- `llama-bench`

### Test
- compare completed tasks/hour across:
  - 8k vs 16k context
  - fast model resident vs unloaded
  - llama.cpp vs MLX

### Rollback
- keep known-good config snapshots
- keep prior model versions archived

---

# J. What NOT to install

These are popular but often wrong for your exact use case.

| Technology / pattern | Why not |
|---|---|
| 100 simultaneous local LLMs | impossible/wasteful on 32 GB |
| Kubernetes | absurd for one Mac mini |
| Kafka / RabbitMQ | overkill; SQLite queue is enough |
| Postgres as first DB | unnecessary early |
| Elasticsearch / OpenSearch | too heavy |
| Milvus / Weaviate / Qdrant cluster | premature |
| AutoGPT-style legacy autonomous loops | brittle and inefficient |
| Full GUI computer-use by default | fragile and risky |
| Docker Desktop as mandatory core | useful later, not required on day 1 |
| Cloud-first agent platforms | conflicts with local-first requirement |
| Multiple chat model servers “just in case” | wastes RAM |
| Fine-tuning stack | poor ROI for this machine |
| Heavy low-code agent builders | too generic and weak for serious coding autonomy |

---

# K. Future upgrade path

## If you move to 64 GB unified memory
- keep Qwen3-30B-A3B as deep worker
- run fast model concurrently more comfortably
- increase context to 32k where useful
- add reranker persistently
- consider one larger dense model for hard tasks

## If you move to 96–128 GB unified memory
- run stronger local models:
  - larger Qwen dense/MoE classes
  - 70B-class dense at 4-bit if memory bandwidth permits
- run multiple deep workers
- keep more models resident
- move from SQLite to Postgres if concurrency demands it
- consider dedicated vector DB if corpus grows

## If you add a dedicated GPU/server
- keep the Mac as control plane
- move inference to remote OpenAI-compatible endpoints
- keep local-first policy for sensitive work
- use remote node for:
  - heavy coding
  - large-context synthesis
  - batch embeddings
- consider Temporal or a real queue only when multi-machine

---

# Sources

I did **not** fetch these live. They are listed from knowledge and marked primary/secondary.

## Inference runtimes
- https://github.com/ggml-org/llama.cpp — primary  
- https://github.com/ml-explore/mlx — primary  
- https://github.com/ollama/ollama — primary  
- https://lmstudio.ai/docs — primary  
- https://github.com/mudler/LocalAI — primary  

## Models / model ecosystems
- https://huggingface.co/Qwen — primary  
- https://huggingface.co/meta-llama — primary  
- https://huggingface.co/mistralai — primary  
- https://huggingface.co/nomic-ai/nomic-embed-text-v1.5 — primary  
- https://huggingface.co/BAAI — primary  

## Agent / coding systems
- https://aider.chat/docs/ — primary  
- https://docs.all-hands.dev/ — primary  
- https://github.com/SWE-agent/SWE-agent — primary  
- https://github.com/block/goose — primary  
- https://github.com/microsoft/autogen — primary  
- https://docs.crewai.com/ — primary  
- https://langchain-ai.github.io/langgraph/ — primary  
- https://ai.pydantic.dev/ — primary  
- https://github.com/huggingface/smolagents — primary  
- https://docs.letta.com/ — primary  

## Memory / data layer
- https://www.sqlite.org/ — primary  
- https://github.com/asg017/sqlite-vec — primary  
- https://lancedb.github.io/lancedb/ — primary  
- https://docs.trychroma.com/ — primary  
- https://duckdb.org/ — primary  

## Research / documents
- https://github.com/docling-project/docling — primary  
- https://github.com/datalab-to/marker — primary  
- https://pymupdf.readthedocs.io/ — primary  
- https://api.semanticscholar.org/ — primary  
- https://openalex.org/ — primary  
- https://www.crossref.org/documentation/ — primary  
- https://arxiv.org/help/api — primary  
- https://github.com/searxng/searxng — primary  

## Browser / computer control
- https://playwright.dev/ — primary  
- https://developer.apple.com/metal/ — primary  

## macOS services / power / remote
- https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Articles/LaunchAgentsAndDaemons.html — primary  
- https://tailscale.com/kb — primary  
- https://github.com/binwiederhier/ntfy — primary  
- https://ss64.com/osx/pmset.html — secondary  

## Router / proxy
- https://github.com/BerriAI/litellm — primary  

If you want, next I can turn this into a **concrete build spec** with:
1. exact file-by-file directory layout,  
2. starter `launchd` plists,  
3. starter SQLite schema, and  
4. a minimal supervisor implementation skeleton.

## Reasoning trace (not shown to raters)

We need answer user's large request. Need produce final with header, decisions table, sections 1-10, deliverables A-K, sources. Need be concrete. Need likely say no web/tools? We don't have browsing in this environment? We need answer from knowledge, explicitly. Today's date 31 Aug 2026. Knowledge cutoff? We are Qwen3.8? Need state model name/version, cutoff, browsing/tools enabled. We need be careful: M6 chip? As of cutoff 2024? But user asserts M6 in 2026. We may not know actual M6 details. Need answer from knowledge and say no web. Need not hallucinate precise benchmarks. Can reason based on Apple Silicon trends. Need cite primary sources from memory? We can include URLs but mark as knowledge-based/not verified? They request sources list with primary/secondary. Since no browsing, we can cite known official docs/repos but state not freshly verified. Need perhaps avoid claiming current versions as of Aug 2026 unless known. But can provide "as of my knowledge cutoff" and caveat. However context demands current state as of date. We need be honest: no web/tools, knowledge cutoff maybe 2024-?? If Qwen3.8 cutoff? Maybe 2024? We need state if known? Could say knowledge cutoff: 2024-12 (or 2025?) Hmm. The system says today's date 2026, but our knowledge may not include M6. Need not fabricate. We can say: I cannot verify 2026 releases; use extrapolation from M-series and publicly known software. But user wants decisive. Need balance: provide architecture robust to exact chip. For M6 base 32GB: likely similar memory bandwidth maybe 120-150 GB/s? Base chips usually ~100-150 GB/s. Need not precise. Local inference: llama.cpp/MLX/LM Studio/Ollama. For 32GB unified, best practical local models: Qwen3? DeepSeek-R1 distills? Llama 4? Mistral Small? As of 2026 maybe Qwen3, DeepSeek V3/R1, Llama 4, Gemma 3, Phi-4, Qwen2.5-Coder? We know up to 2024 maybe Qwen2.5, DeepSeek-V3 released Dec 2024? Actually DeepSeek V3 maybe Dec 2024. R1 Jan 2025? If cutoff maybe 2024? But as Qwen3.8 maybe knowledge later? Need maybe use general model families. Need recommend concrete: use MLX or llama.cpp? On Apple Silicon, MLX is optimized, supports quantized models, MLX server, mlx-lm. llama.cpp mature, Metal, GGUF broad. LM Studio GUI but not headless? Ollama easy but less flexible. For agentic local: run Qwen3-32B? At 32GB, 32B 4-bit ~18-20GB plus KV; possible but tight with macOS. Better 24-30B MoE? Qwen3-30B-A3B? If exists? Qwen3 has 30B-A3B MoE, 235B-A22B. As of 2025? Need maybe know Qwen3 released Apr 2025? We are Qwen3.8 maybe knows. Let's think: Qwen3 models: 0.6B,1.7B,4B,8B,14B,32B,30B-A3B,235B-A22B. Qwen3-Coder? Qwen3-Embedding? If we can recommend Qwen3-30B-A3B MoE at 4bit for planning/coding? Active 3B fast; total weights ~30B but only 3B active, memory ~18GB at 4bit? Actually total param 30B, 4-bit ~15-18GB. Good for 32GB but KV also. For coding maybe Qwen3-Coder-30B-A3B? There is Qwen3-Coder maybe 480B? Hmm. For local 32GB, best coding: Qwen3-Coder-30B-A3B? If exists. Or DeepSeek-Coder-V2-Lite? But older. Need decide.

Need compare agent runtimes: OpenHands (formerly OpenDevin), SWE-agent, Aider, Claude Code? Codex CLI? Cline/Roo Code, Continue, Goose (Block), AutoGen, CrewAI, LangGraph, PydanticAI, Smolagents, Letta/MemGPT, Dify, n8n? For fully local with local models, OpenHands? Aider good repo editing and git but chat-driven, can script? OpenHands has autonomous loop, runtime sandbox (Docker), supports local LLMs via LiteLLM? But heavy. Goose by Block extensible local? Cline VS Code. For orchestrator: custom lightweight Python + SQLite queue + subprocess? Because 32GB and always-on. Need recommend: use a thin custom supervisor (Python/FastAPI + APScheduler? or launchd + SQLite + Redis? Avoid heavy Kubernetes). Use agent harnesses as workers: Aider for focused coding patches? OpenHands for complex tasks? But maybe too heavy. Need decide one existing harness vs custom. For robust: build custom orchestration layer using LangGraph? LangGraph has durable execution/checkpoints, good for long-running. But maybe overhead. Could use Temporal? Too heavy? For local always-on, Temporal server (Go/SQLite?) could be robust but complex. Maybe use Python RQ/Dramatiq + SQLite? Need reliability. Could use Apple launchd + SQLite task queue + file locks. Multi-agent logic with Pydantic AI or LangGraph. Need not overcomplicate.

Need consider computer control: terminal/filesystem via dedicated macOS user, sudoers restrictions, workspace directories, Git safe.directory, no full disk. Browser automation: Playwright with Chromium isolated profile, no saved passwords. GUI control maybe not needed; avoid AppleScript/Accessibility unless necessary. If needed, use separate user, screen sharing, cliclick? But risky. For sandboxing: macOS sandbox-exec limited/deprecated? Docker Desktop/OrbStack/Colima for Linux containers; but Apple Silicon Linux VMs. For coding agent, use git worktrees in ~/agent/var/worktrees, run tests in containers if untrusted. Use dedicated user "aiworker" with no admin, FileVault, separate keychain. Credential isolation: 1Password CLI? macOS keychain? Use env secrets injected only for approved tasks, SSH keys deploy read-only. Need emergency stop: launchctl unload, kill process group, redis flag, web dashboard button, cron.

Always-on: launchd LaunchDaemon/LaunchAgent for supervisor, KeepAlive true, RunAtLoad, StandardOut logs, throttle interval, WatchPaths maybe. caffeinate -dimsu? pmset: sudo pmset -a sleep 0 disksleep 0 displaysleep 10; womp? For remote: Tailscale SSH, screen sharing, no port forwarding. Dashboard: local web app bound to localhost + Tailscale only, auth (Passkey? OAuth? token). Notifications: ntfy, Bark, Pushover (paid), email. Approvals via web or Telegram/Matrix bot.

Storage: internal fast: OS, apps, models? Models can be on external if Thunderbolt USB3? But 512GB limited. Need internal for active models and databases for speed/reliability? External 1TB for repos/papers/datasets/backups/logs/archive models. If external SSD is Thunderbolt/USB 3.2 10Gbps okay for repos/papers. Avoid running DB on external if it sleeps/unreliable. Use APFS encrypted. Maybe keep current model weights internal if fit (20-30GB) plus cache; archive models external. Git worktrees internal? Active repos maybe internal for speed, but 512GB. Use external for large datasets/papers, Time Machine backups.

Hardware memory allocation: macOS ~5-8GB, agent stack ~2-4GB, browser ~2-4GB if used, DB ~1GB, model weights ~14-20GB, KV cache ~3-6GB. Need recommend one large model loaded at a time plus small model resident. For 32GB: maybe run 24-32B 4-bit if no browser; but safe: primary "deep" model 24-32B Q4_K_M/QAT 4bit ~16-20GB, context 16k-32k, one worker. Small fast model 4-8B 4bit ~3-5GB resident for routing/summarization/classification, concurrent with large? If both loaded total 20-25GB, possible but tight. Use model router unload/load. Better keep small model loaded and load large on demand, or use MoE active small? For concurrency: one large worker, 1-2 small workers if small only; don't run multiple large. If using MoE Qwen3-30B-A3B active 3B can handle multiple sequences? Memory weights still high, compute active low, maybe 2-3 concurrent tasks okay but KV memory. Need caution. Context: 8-16k default, 32k if memory permits; avoid 128k. KV cache estimate: for 32B? If 64 layers, GQA maybe 8 KV heads *128 dim *2 bytes *32k *? huge? quantized KV? Could use llama.cpp --ctx-size and cache quantization (q8_0). For MLX? Need not precise. Recommend q4_k_m for weights, q8_0 KV if llama.cpp.

Model strategy: planning/coding/debugging: if local, Qwen3-30B-A3B or Qwen3-32B 4bit? For agentic, Qwen3-Coder maybe. Research synthesis: large model (cloud optional) or local 30B. Summarization/classification: Qwen3-8B / Llama-3.1-8B / Gemma 3 4B. Embeddings: nomic-embed-text-v1.5? bge-m3? Qwen3-Embedding? Apple Silicon local. For citations: use retrieval with exact quote extraction, store hashes, require source ids, verifier agent cross-checks. Could use local reranker (bge-reranker-v2-m3) and SQLite FTS5 + vector (sqlite-vec). Avoid huge vector DB; start SQLite FTS5 + sqlite-vec/lancedb/chroma? For memory: start with filesystem Markdown + SQLite (tasks, decisions, artifacts) and FTS5. Add vector only when needed; maybe LanceDB embedded or Chroma. Knowledge graph: optional later (Kuzu? Neo4j too heavy). Persistent memory: project memory directories: MEMORY.md, decisions ADRs, task ledger, experiment logs. Use SQLite for structured queue, events, claims, sources. Use embeddings for semantic recall but always retrieve raw snippets with file paths.

Coding agents comparison: Aider (mature, git-aware, repo map, local via LiteLLM/Ollama, good for targeted edits). OpenHands (full autonomous, Docker sandbox, event stream, web UI; heavier). SWE-agent (research oriented, ACI, GitHub issues, less general local). Goose (Block, local model support, extensions; maybe good). Cline/Roo Code (VS Code, human-in-loop, not headless). Codex CLI/Claude Code (cloud-first, not local; Claude Code can use local? no). Continue (IDE). For fully local headless: Aider + custom task harness maybe best. For complex multi-step: OpenHands with local LLM may be too demanding on 32GB, but can use for selected tasks in Docker. Need choose: Aider as primary coding executor wrapped by custom orchestrator; OpenHands optional later. But user wants serious repo understanding etc. Aider has repo map, lint/test hooks, git commits, Architect/editor modes, watch mode, headless yes? It can run with --yes, --message? It has scripting and benchmark. Supports local models via LiteLLM/Ollama. Need mention limitations: not a full planner; need supervisor.

Research agents: GPT Researcher? STORM? OpenResearcher? AutoGPT? Need local. GPT-Researcher supports local LLMs? Maybe via LiteLLM/Ollama, but web search needs API. For literature: Semantic Scholar API, arXiv API, Crossref, OpenAlex, PubMed, CORE, Unpaywall. Web search: SearXNG self-hosted? Tavily/Serper/Brave paid. To be local/private, self-host SearXNG with public engines, but rate limits; use DuckDuckGo? For claim verification: retrieval-augmented pipeline with source snapshots (save HTML/PDF hashes), citation extraction (GROBID? for PDFs), marker/docling for PDF to Markdown, tesseract OCR. Use a verifier agent that only accepts claims with evidence spans. Use SQLite evidence table. Avoid hallucinated citations by requiring DOI/arXiv ID from APIs, not generated; fetch metadata. Use Zotero? Could use local BibTeX. For PDF parsing: Docling (IBM), Marker, PyMuPDF4LLM, unstructured. Best? Docling strong for docs, tables; Marker good PDFs to MD. Use both? Start PyMuPDF4LLM + Docling optional.

Agent runtimes: Need compare many. For orchestration: LangGraph (graph, checkpoints, human-in-loop, local; can be complex), AutoGen/AG2 (conversational multi-agent), CrewAI (role agents, high-level, less low-level control), PydanticAI (typed, tool use, lightweight), smolagents (Hugging Face lightweight code agents), OpenAI Agents SDK? Maybe as of 2025. For local: Pydantic AI + LiteLLM? Could be good. But need long-running durable tasks: LangGraph + checkpointer (SQLite/Postgres) better. However heavy frameworks add overhead and brittle abstractions. Since 100+ logical agents and limited hardware, custom task ledger + worker pool might be best, using LangGraph only for complex workflows. Need decisive: Build thin custom orchestrator ("control plane") in Python using SQLite + file locks + launchd; use LangGraph as optional workflow engine for defined research/coding pipelines? Or choose Temporal? Let's evaluate.

Always-on, crash recovery: Temporal provides durable execution, retries, timers, visibility. Self-hosting Temporal server with SQLite? Temporal has single-binary? It may be heavyweight but robust. For personal system, might be overkill. Alternative: Restate, Inngest, Hitch? Local? Python: Prefect/Dagster for workflows, but agent loops? Prefect can schedule/retry. Simpler: SQLite queue with status, leases, retries, supervisor. Need 24/7 reliability; custom can be sufficient if designed idempotent. But user wants production-quality. Maybe use "Temporalite" or Temporal Cloud? But local/free? Could be too much RAM (Temporal server ~500MB-1GB). On 32GB okay, but complexity. Need avoid unnecessary infrastructure. So custom SQLite queue + launchd is enough. For durable multi-step workflows, store step state in SQLite and resume. Could use LangGraph checkpointing to SQLite.

Multi-agent architecture: 100 logical agents as rows in agent_definitions table, not processes. Task queue with priorities and resource classes. Worker pool: 1 "deep" worker (large model) and 2 "fast" workers (small model) maybe plus tool workers (no LLM). Agents request model tier. Coordinator creates subtasks. Use concurrency semaphores by tier. Use workspaces/worktrees per task. Agents are state machines; only active when assigned task. Dynamic agent creation: templates + capabilities. Use model router: classify task complexity, privacy, tool needs. Use local first; optional cloud for hard synthesis or web. Use caching.

Computer control security: dedicated user, no admin, separate APFS volume? Use folder permissions. Use `sandbox-exec`? Apple's App Sandbox not for arbitrary command? Could use Docker containers for untrusted code. But if agent modifies user projects, need host file access. Use git worktrees under workspace; tests run in Docker if dependencies risky. Use `fs_usage`? Audit via unified logging, command wrapper logging. Destructive command controls: denylist rm -rf, diskutil, sudo, launchctl unload? Use wrapper shell that logs and asks approval for commands matching patterns, writes outside workspace, network POST secrets, package install global. Use read-only credentials for research; deploy keys. Use macOS configuration profiles? Maybe.

Remote access: Tailscale (or Headscale self-hosted) for private mesh VPN. SSH with key + 2FA? macOS Remote Management/Screen Sharing over Tailscale. Web dashboard on localhost via Tailscale Serve? Tailscale Funnel not needed. Use SSH tunnels for web. Notifications via ntfy self-hosted? Could run ntfy server local and push via Tailscale; remote phone app. For approvals: web dashboard or Matrix/Telegram bot. If no cloud, use ntfy over Tailscale? Phone away needs internet; Tailscale connects to home from internet via DERP if no direct. Good. Could use WireGuard self-hosted but Tailscale easier. If privacy maximal, Headscale + NetBird? But choose Tailscale stable. Optional paid: Tailscale personal free? As of 2026 maybe changed. Need mention. SSH: enable Remote Login, disable passwords, use keys. Use `launchd` for service. For emergency stop: SSH command `ai-ctl stop`, dashboard button, or kill switch file. Use `pmset` schedule power restore after outage? `sudo pmset -a autorestart 1`? Actually `systemsetup -setrestartfreeze`? For power failure: `sudo systemsetup -setrestartpowerfailure 1` maybe. Need include.

Storage plan: Internal: /Applications, Homebrew, orchestrator code, SQLite DB, active repos (maybe limited), active model weights (one primary + small), caches, logs (recent). External: git bare repos/archives, datasets, papers, downloaded web snapshots, backups, old models, large vector indices maybe. Need ensure external not sleeping: `pmset disksleep 0`, use APFS encrypted, maybe Thunderbolt. If external disconnects, system should degrade; use symlinks? Use paths in config.

Need market tables for every category? User asks independently compare market for every major category identify 1-7. Could include in each section or deliverable A. Need maybe concise tables with categories. Need not too exhaustive but enough.

Need sources list: Since no browsing, mark as primary/secondary and note not verified at runtime. Include official docs URLs: Apple MLX, llama.cpp, Ollama, LM Studio, Hugging Face, OpenHands, Aider, SWE-agent, AutoGen, LangGraph, CrewAI, Pydantic AI, smolagents, Letta, Mem0, SQLite, sqlite-vec, LanceDB, Chroma, Qdrant, DuckDB, Playwright, SearXNG, Semantic Scholar API, OpenAlex, Crossref, arXiv, GROBID, Docling, Marker, Tailscale, launchd, pmset, caffeinate. Need maybe include model pages: Qwen, DeepSeek, Llama, Gemma, Phi. But if no web, say primary docs from memory. Need avoid fabricated URLs? We know many. For M6: Apple newsroom? Can't cite current. Could cite Apple developer docs on Metal, unified memory? Need say cannot verify M6 specifics.

Need answer as if senior architect. Must be decisive. Need mention "I do not have web browsing/tools in this answer; relying on internal knowledge up to cutoff; versions may have changed by 2026-08-31. Where 2026-specific claims would be required, I flag them as extrapolation." But user requested current. Need still give best. Maybe state: "Browsing/tools: disabled." "Knowledge cutoff: 2024-12" if known. But as Qwen3.8 maybe cutoff? The system says Qwen3.8? Maybe knowledge cutoff 2026? It says knowledge cutoff if known. Could say "knowledge cutoff: not exposed to me / around 2024-12"? Need avoid false. Maybe: "Knowledge cutoff: not precisely known to me (model reports Qwen3 series; training likely includes data through 2025)". Hmm. Better: "Knowledge cutoff: unknown/not exposed; my reliable knowledge ends around late 2024/early 2025." But asked if known. Could say "not disclosed to me". But need date? We'll state: "knowledge cutoff: not exposed; reliable knowledge through 2024, some 2025 ecosystem from training; not verified live." But if model is Qwen3.8 maybe maybe cutoff 2025? Hmm. Need header: "Model: Qwen3.8; Knowledge cutoff: unknown/not exposed (reliable through 2024-12; may include 2025); Browsing/tools: off." Good.

Need be careful with M6. Since M6 likely not in training. Need say: "I cannot verify M6-specific benchmark. Treat M6 base as Apple Silicon with Metal, unified memory; use memory/bandwidth constraints, not chip-specific features." The user wants exact. We can design for 32GB, not M6 specifics. Need perhaps assume M6 has Neural Engine but llama.cpp uses Metal/GPU not ANE. MLX uses Metal. No CUDA. Good.

Let's plan answer structure. Need long. Could produce with tables. Need not overdo but desired oververbosity 9. Must satisfy all deliverables. Need include installation commands. Since no live versions, use brew install commands, pipx, uv, etc. Need be executable but caveat versions. Need maybe use `uv` for Python env. Use Homebrew. Need choose local inference server: llama.cpp server or MLX? Need decide. Let's compare:

- llama.cpp: broad GGUF, quantization, Metal, server OpenAI-compatible, concurrency, cache quantization, model hot-swap? llama-server can load one model; can run multiple ports. Good for resource control. Supports grammars, tool calling? Some models with tool use. Mature. Use `llama-server` with `--jinja` for chat templates, `--n-gpu-layers 999`, `--ctx-size 16384`, `--cache-type-k q8_0 --cache-type-v q8_0`, `--parallel 1` for large. Can run small model separate port. Good.
- MLX: faster on Apple Silicon for some models, easy quantization, `mlx_lm.server` OpenAI-compatible? Supports prompt caching? Maybe less broad but optimized. MLX models in Hugging Face mlx-community. Could be faster for Qwen3? But llama.cpp is more mature and cross-platform. Need choose best for 32GB? MLX may have better performance for Apple Silicon. But agent ecosystem supports OpenAI-compatible either. Could recommend MLX for primary if using mlx-community Qwen3, and llama.cpp as fallback. But running multiple servers? Maybe simpler: use LM Studio? But headless? LM Studio has local server but GUI, paid? Not ideal for service. Ollama easy but less control (context, KV cache quant, parallel) and model support; but can run as launchd service. For production, llama.cpp or MLX. Need decisive: choose **llama.cpp** as primary inference runtime due to mature Metal backend, fine-grained memory controls, GGUF quantizations, OpenAI-compatible server, broad model support. Use **MLX** as optional for speed experiments, especially Qwen3/Apple-optimized MLX builds. But if MLX is faster, maybe choose MLX? Let's think. For always-on, llama.cpp more stable and configurable. Use llama.cpp.

Models: Need decide exact. For local/private and 32GB. Need recommend:
- Primary deep agentic/coding: **Qwen3-30B-A3B-Instruct (MoE) 4-bit** or **Qwen3-32B 4-bit**? Need choose. Qwen3-30B-A3B active 3B gives speed and decent quality; total weights 30B memory maybe 17GB Q4, fits. 32B dense Q4 maybe 19GB plus KV, slower. For useful work/hour, MoE active 3B may be faster but maybe lower quality than dense 32B. For coding, active 3B might be okay but complex tasks may need 32B. On base M6 bandwidth maybe limited, MoE active small is faster. Recommend primary: Qwen3-Coder-30B-A3B if available; else Qwen3-30B-A3B-Instruct. For planning/coding/debugging. If quality insufficient, use cloud API for hard tasks. Also keep a small model: Qwen3-8B-Instruct 4-bit or Gemma 3 4B/Phi-4-mini? Need pick Qwen3-8B for tool use. For ultra-small routing: Qwen3-4B or Llama-3.2-3B. But memory: maybe keep Qwen3-8B Q4 ~5GB. If large loaded, total 22GB. macOS 6, agents 3 = 31, tight. Maybe use 4B small ~2.5GB. Use small for routing/classification/summarization. Could also use MoE primary with active 3B as both deep and fast? But if weights loaded, memory high. Could use one model only to reduce memory: Qwen3-30B-A3B as primary and small not loaded. But for routing many small tasks, active 3B okay. Yet 30B weights memory high but active compute low. Could run one model only. But need concurrent small workers? If model loaded, can handle multiple requests? llama-server parallel maybe 2 with KV. But memory. Alternative use Qwen3-8B as resident and load 30B on-demand for hard tasks; unload after. Model swapping overhead but saves memory. For always-on, maybe keep 8B resident, load 30B when deep task queued. If deep task long, load 30B and stop small? Could have router: fast tier uses 8B; deep tier loads 30B and unloads 8B if memory pressure. But server per model; need process management. Simpler: run 8B all the time; spawn 30B only when needed and set parallel=1, ctx=16k. 32GB should handle both? 8B Q4 ~5GB, 30B Q4 ~17GB, KV maybe 3GB, total 25 + OS 6 =31, borderline. Could disable small when large runs to be safe. Use launchd resource management? Custom router can stop small server while large active, but then routing can't use LLM. Use heuristics. Or use Qwen3-4B small (2.5GB) to fit. Need recommend: Primary deep: Qwen3-30B-A3B Q4_K_M, context 16k, one worker. Fast: Qwen3-4B or 8B? For quality, 8B; memory maybe Q3_K_M? Hmm. Use 4B for routing/summarization if memory constrained. But coding summarization maybe 8B better. We can say: start with Qwen3-8B Q4 if you don't run browser simultaneously; if memory pressure, switch to Qwen3-4B Q4. For 100 agents, most tasks queued, not concurrent.

Embeddings: nomic-embed-text-v1.5 (0.13B) or bge-small? For multilingual, bge-m3 568M. On 32GB, small. Use `llama.cpp` embedding server or `mlx-embeddings`. Use sqlite-vec. Reranker: bge-reranker-v2-m3 maybe 568M, optional.

Cloud optional: Anthropic Claude, OpenAI GPT, Google Gemini for hard coding/research; use only when local fails or for high-stakes synthesis. Need mention cost and privacy. Web search APIs: Brave/Tavily/Serper if self-hosted SearXNG unreliable. Use local first.

Need agent runtime recommendation: Use **LiteLLM Proxy** as model router? It can route OpenAI-compatible endpoints, fallbacks, budgets, model aliases. But it's a proxy, not agent. Use LiteLLM to unify local llama.cpp and cloud. It can run lightweight. Good. But if avoiding extra, custom router. Recommend LiteLLM as model router because handles providers, fallback, logging. But on 32GB, Python process fine. Use config.yaml with model tiers. Use local endpoints. Cloud keys optional. For model selection, orchestrator chooses tier, LiteLLM can route based on model name. Could also use OpenRouter? Not local. Use LiteLLM local.

Agent runtime: Need maybe choose **Pydantic AI** for building typed agents with tools and **LangGraph** for durable workflows? Or one? Let's design:
- Control plane: Python service `ai-supervisor` using FastAPI + SQLite (WAL) + APScheduler/launchd. Provides REST API, task queue, agent registry, permissions, approvals.
- Workflow engine: **LangGraph** with SQLite checkpointer for multi-step workflows (coding task, research task). It can pause/resume, human-in-loop. LangGraph is popular but has maturity. It supports local models via LangChain chat models (ChatOpenAI pointed to LiteLLM). Could be heavy but okay. Alternative: Prefect for scheduling? Maybe not.
- Execution harnesses: Aider for coding, Playwright for browser, custom shell tool with approval. OpenHands optional.
- Multi-agent: agents are LangGraph nodes or task rows; not separate processes except workers.

Could use **Temporal** for durable queue instead of custom. Need decide. User wants production-quality. Temporal gives retries, timers, visibility, but installation more complex. On Mac, `temporalite` or `temporal server start-dev` not production. Self-host with docker compose maybe. But local no docker? Could use SQLite? Temporal requires Cassandra/MySQL/Postgres? It supports SQLite for dev? Not production. Could be too much. Custom SQLite robust enough.

Need compare agent runtimes:
- OpenHands: best full autonomous software dev platform; Docker sandbox, web UI, local LLM via LiteLLM; heavy, memory high, may be overkill but useful as worker.
- Aider: best lightweight git-native coding CLI; local model support; not full autonomous orchestrator; use as coding tool.
- SWE-agent: strong for GitHub issue-to-PR, containerized, research; less general local always-on.
- Goose: extensible local agent with MCP? It supports local models and extensions; maybe good, but maturity? Could mention.
- Cline/Roo: best IDE copilot, not headless.
- AutoGen/AG2: multi-agent conversation, research; less deterministic.
- CrewAI: high-level roles, easy; less low-level control.
- LangGraph: best durable graph orchestration; more code.
- Pydantic AI: typed single-agent/tool loops; lightweight.
- Letta/MemGPT: memory-centric agents; interesting but heavier.
- Dify/n8n: low-code, not ideal for autonomous filesystem coding.
Decision: custom control plane + LangGraph + Aider + optional OpenHands.

Need maybe mention MCP (Model Context Protocol) as tool integration standard. As of 2026 likely widespread. Use MCP servers for filesystem, Git, SQLite, fetch, Playwright? But security. Could use MCP to connect tools. But avoid making everything MCP? It can standardize. Need include? User didn't ask specifically but relevant. Need maybe recommend use MCP only for tool adapters, not as orchestrator. Use local MCP servers with permissions. But if building custom, Python tools easier. Mention not to install many MCP servers by default.

Research agents architecture: Need separate pipeline:
1. Task: question, scope, stop conditions.
2. Planner creates subqueries.
3. Source discovery: arXiv/Semantic Scholar/OpenAlex/Crossref APIs for academic; SearXNG or Brave for web; save metadata.
4. Fetcher: download PDFs/HTML to external storage, hash. Convert to markdown via Docling/Marker/PyMuPDF.
5. Evidence extraction: chunk with section headings, embed, store in sqlite-vec; FTS5 keyword. Retrieval returns source_id + quote.
6. Claim/evidence table: claim text, status, supporting evidence IDs, contradicting evidence IDs.
7. Writer only sees evidence packs; must cite [S#]. Verifier checks each claim against evidence with NLI? Use local model to check entailment and quote existence; if unsupported mark. Final synthesis by deep model, with citations. Use DOI/arXiv ID from API, no model-generated citation.
8. Report Markdown + BibTeX + evidence appendix.

Need prevent hallucinated citations: never allow LLM to create reference list from memory; build references from retrieved metadata; citation IDs only from DB; verifier cross-check; require quotes; reject if no evidence.

Memory architecture:
- Filesystem: `~/ai/` internal? Maybe `/Users/aiworker/AgentLab/`. Structure: `control/`, `workspaces/`, `memory/`, `research/`, `models/`, `logs/`. Markdown for human-readable. ADRs. Project memory: `MEMORY.md`, `TASKS.md`, `DECISIONS.md`.
- SQLite: `control.db` (tasks, agents, leases, events, approvals, models, costs), `memory.db` (facts, entities, source metadata, evidence, embeddings via sqlite-vec). Use WAL, foreign keys. Backup nightly to external.
- Vector: start sqlite-vec; if >1M chunks or multi-user, LanceDB/Qdrant. Avoid heavy Postgres/pgvector initially.
- Knowledge graph optional: Kuzu embedded or Neo4j? Later.

Need always-on details:
- dedicated user `aiworker`, auto-login? For headless after restart, need LaunchDaemon maybe root? But avoid root. LaunchAgent runs after login. Need auto-login to aiworker with FileVault? FileVault pre-boot requires password, unless auto-login disabled? For server, maybe enable automatic login for dedicated user? Security tradeoff. Or use LaunchDaemon root to start service as aiworker? macOS LaunchDaemons run as root or UserName. Could create LaunchDaemon with UserName aiworker, KeepAlive. It starts before GUI login. But some macOS user keychain/accessibility may not be available. For terminal/file tasks, okay. Use `launchd` plist in /Library/LaunchDaemons/com.local.ai.supervisor.plist with UserName aiworker, WorkingDirectory, ProgramArguments `/Users/aiworker/.local/bin/ai-supervisor`, RunAtLoad, KeepAlive, StandardOutPath, StandardErrorPath, Nice, LowPriorityIO? Need maybe `ProcessType=Background`, `SoftResourceLimits`? Use `ExitTimeOut`. Also `LaunchOnlyIfNetworkAvailable`? For network. Use `ThrottleInterval=30`.
- `pmset`: sleep disabled, display sleep, restart after power failure, wake on network? `sudo pmset -a sleep 0 disksleep 0 displaysleep 10 womp 1 autorestart 1`? Actually `autorestart` is `sudo systemsetup -setrestartfreeze`? Need provide commands with caveat. `sudo pmset -a powernap 0`? Use `caffeinate -dims` as wrapper if needed. For scheduled jobs: launchd StartCalendarInterval for maintenance.
- crash recovery: supervisor process restarts workers; tasks have leases and heartbeat; if worker dies, task returns to pending; idempotent steps; Git worktrees cleaned. Use `launchd KeepAlive`. Use `ai-ctl doctor`.
- logging: stdout JSON to logs, `log` unified, rotate with `newsyslog` or `logrotate`. Use `os_log`? Simpler.

Remote access:
- Tailscale installed as system extension; enable SSH. Use `tailscale up --ssh` maybe. Use Tailscale ACL, 2FA. Access dashboard via `http://mac-mini.tailnet:8080` bound to tailscale0 or localhost with `tailscale serve`. Do not expose public. For phone: Tailscale app, open dashboard, or SSH with Termius/Blink. Notifications: self-host ntfy on Mac mini, subscribe phone over internet? ntfy can be local but phone needs push; if self-hosted no APNs? ntfy apps can connect to self-hosted over Tailscale? If away, Tailscale connects. Could use ntfy public server for non-sensitive alerts only. For secure, use Matrix or Telegram? But cloud. Use local `gotify`? Push via APNS requires third-party. Maybe use ntfy with self-hosted and phone app over Tailscale; may need background refresh. Alternative: Pushover (paid) for reliable. Recommend ntfy local for detailed, Pushover optional for critical.
- Approvals: dashboard with token/passkey; or SSH command. Require approvals for destructive actions. Use HMAC signed requests. Use audit log.

Security details:
- Three zones: Personal (no agent), Agent workspace (full), Restricted (needs approval). Use Unix user and ACLs. Personal data not readable by aiworker? If agent needs documents, create specific shared folders. Use macOS Full Disk Access disabled. Keychain: do not give aiworker login keychain password; use separate keychain for agent secrets, locked; use 1Password CLI with biometric/service token? Maybe. SSH keys for git with restricted deploy keys. Use `.netrc` avoided. Use `security` command? Secrets in macOS Keychain but only accessible after approval? Simpler: store secrets in `op` items, inject ephemeral env after approval, no disk.
- Git safeguards: no force push to main, branch naming `agent/*`, require signed commits? Use pre-commit hooks, `git config --global alias`? Use `--no-verify` only with approval. Worktrees isolated. Run tests before commit. Limit file size.
- Destructive command policy: wrapper `ai-exec` logs all commands, denies by regex: `sudo`, `rm -rf /`, `diskutil erase`, `launchctl unload`, `defaults write`, `chmod -R`, writes outside workspace, `git push --force`, `curl | sh`, package manager global install. For allowed but risky, create approval request with command, cwd, timeout; human approves. Use process groups and timeouts. Resource limits: `ulimit`, nice, memory limit? macOS lacks cgroups; use `launchd` resource limits? Could use `ulimit -t`, `ulimit -v` not fully. Use timeouts and watchdog. Token limits: per task budget, daily budget; local token count and cloud cost. Runaway: max steps, max runtime, max cost, heartbeat, stop if loops detected (repeated command/output). Kill switch: file `/Users/aiworker/AgentLab/STOP`, `ai-ctl stop-all`, launchctl unload, Tailscale dashboard button.
- Network controls: application firewall enabled, block incoming except SSH/Tailscale; outbound allowlist optional; no agent direct access to banking; use separate browser profile no cookies. For research, use isolated browser container? Playwright with ephemeral profile. If untrusted web content, treat as prompt injection; never execute instructions from web without verification; disable auto-run downloaded files.

Implementation roadmap: Need phases with exact technologies and commands. Need maybe long. Provide step-by-step.

Phase 1 Minimal: install Homebrew, uv, git, llama.cpp, LiteLLM, SQLite, download models, create aiworker user, directories, simple FastAPI supervisor, launchd, Tailscale optional. Test: send task to summarize file, model responds. Commands: `brew install git uv llama.cpp liteLLM?` Actually litellm via pip/uv tool. `brew install --cask tailscale` maybe. `brew install sqlite` (built-in). `brew install mlx`? Python packages: `uv tool install litellm[proxy]`, `uv tool install llama-cpp-python?` But llama.cpp via brew? There is `llama.cpp` formula? I think Homebrew has `llama.cpp`? It may install `llama-server`. If not, build from source. Could use `brew install llama.cpp`? Need be careful. As of 2024 Homebrew formula `llama.cpp` exists? Maybe. Could say install from Homebrew or build. `brew install ollama` optional? But we choose llama.cpp. For models: use Hugging Face CLI `hf download` or `curl` from HF. Need maybe `brew install huggingface-cli`? `pipx install huggingface_hub`. Use `hf download`? In 2025 CLI maybe `hf download`. Could use `huggingface-cli download`. Need include commands but caveat.

Phase 2 Autonomous coding: install aider via `uv tool install aider-chat`, configure repo map, local model via OpenAI endpoint. Create coding worker that clones repo, creates worktree, runs aider with prompt, runs tests, commits branch. Add Git safeguards. Test on toy repo.

Phase 3 Research: install SearXNG via Docker? But no Docker? Could use `docker` via OrbStack/Colima. Need decide if containers needed. For security and research services, Docker useful. But on Mac, Docker VM uses memory. OrbStack efficient but paid? Colima free. Use Podman? For local, maybe avoid Docker initially; run SearXNG in Python venv? SearXNG can run from source. But self-hosting search may be complicated. Could use `uv` run. Or use Brave API. For literature no container. PDF parsing: `uv tool install docling`? `marker`? PyMuPDF. Use Python libs. Need maybe no Docker until security sandbox. For untrusted code, use OrbStack/Colima. For phase 3, install `uv add docling pymupdf` etc. Use Semantic Scholar/OpenAlex. Test produce report with citations.

Phase 4 Memory: SQLite schemas, FTS5, sqlite-vec, embeddings. Use `llama-server --embedding` with nomic embed. Test recall.

Phase 5 Multi-agent orchestration: LangGraph? Or custom queue. Need install `uv add langgraph langchain-openai litellm`. Define agent templates, worker pool. Test 100 logical agents by generating tasks; only 2 workers run.

Phase 6 24/7: launchd plists, pmset, log rotation, backups, watchdog. Test reboot.

Phase 7 Remote: Tailscale, SSH keys, dashboard (FastAPI + HTMX maybe), ntfy. Test phone.

Phase 8 Optimization: model swap, cache quantization, context tuning, optional cloud fallback, metrics (Prometheus? Grafana? Avoid heavy). Use `ai-ctl metrics`.

Need include directory structure. Example:
```
/Users/aiworker/AgentLab/
  bin/
  config/
    litellm.yaml
    supervisor.yaml
    policies.yaml
  control/control.db
  memory/
    global/
    projects/<project-slug>/MEMORY.md
  research/
    sources/
    pdfs/
    snapshots/
    reports/
  workspaces/
    repos/
    worktrees/<task-id>/
  models/
    active/
    archive/
  logs/
  tmp/
```
External: `/Volumes/AgentVault/` with backups, models archive, datasets, papers.

Need communication: REST/JSON local, SQLite queue, file artifacts, MCP optional. Use OpenAI-compatible API for models. Use webhook for notifications. Use SSH for remote.

Need exact model downloads. Need choose model repos. Since no browsing, can list examples:
- `Qwen/Qwen3-30B-A3B-Instruct-GGUF`? Maybe community bartowski? Use `bartowski/Qwen3-30B-A3B-Instruct-GGUF`? Need not exact if uncertain. Could say search Hugging Face for official/community GGUF of Qwen3-30B-A3B-Instruct, choose Q4_K_M. But user wants exact. Need be decisive but not hallucinate exact repo. Could recommend `unsloth/Qwen3-30B-A3B-Instruct-GGUF` if exists? Unsloth likely provides GGUFs. For Qwen3 maybe yes. Need maybe use `lmstudio-community`? But for llama.cpp, `bartowski` is reliable. As of 2025, bartowski quantizes many. Could say: `huggingface-cli download bartowski/Qwen3-30B-A3B-Instruct-GGUF --include "*Q4_K_M.gguf"`. But if not exists? Hmm. Need maybe use official Qwen GGUF? Qwen may provide `Qwen/Qwen3-30B-A3B-Instruct-GGUF`. I think Qwen releases GGUF? Maybe. Could use `Qwen/Qwen3-30B-A3B-Instruct-GGUF`. Let's be safe: "Use any verified GGUF from official Qwen or trusted quantizer (bartowski/unsloth); example filename Qwen3-30B-A3B-Instruct-Q4_K_M.gguf". That avoids exact repo. But installation commands need model. Could provide placeholder and instructions to verify SHA. Good.

Small model: `Qwen/Qwen3-8B-Instruct-GGUF` Q4_K_M or `Qwen/Qwen3-4B-Instruct-GGUF`. Embedding: `nomic-ai/nomic-embed-text-v1.5-GGUF`. Reranker optional `BAAI/bge-reranker-v2-m3-GGUF` if available. Need mention use `--embedding` server.

Need include local inference commands:
```
llama-server -m ~/AgentLab/models/active/qwen3-30b-a3b-q4_k_m.gguf \
 --host 127.0.0.1 --port 8081 --n-gpu-layers 999 --ctx-size 16384 \
 --parallel 1 --threads <perf> --cache-type-k q8_0 --cache-type-v q8_0 \
 --jinja --chat-template-file? maybe not.
```
Small:
```
llama-server -m ...qwen3-8b... --port 8082 --ctx-size 8192 --parallel 2
```
Embedding:
```
llama-server -m nomic-embed... --embedding --port 8083 --ctx-size 8192
```
LiteLLM config:
```
model_list:
 - model_name: deep/local
   litellm_params:
     model: openai/qwen3-30b
     api_base: http://127.0.0.1:8081/v1
     api_key: local
 - model_name: fast/local
   ... 8082
 - model_name: embed/local
   ... maybe embeddings not via chat; use custom.
```
LiteLLM proxy run: `litellm --config config/litellm.yaml --port 4000`. But LiteLLM can route embeddings? Maybe. Use direct for embeddings.

Need mention model loading/unloading: use supervisor to start/stop llama-server processes based on queue; avoid leaving deep model loaded if idle; use idle timeout. On 32GB, model swap takes seconds to minute from SSD; acceptable. Keep small loaded. Use `launchd` or Python subprocess with health checks.

Need compare market for categories. Could include a big table in A, but also in sections. Need include (1) best overall etc. For every major category maybe too much. We can provide category comparison tables concise. Need include alternatives may not know: e.g., local inference: exo? distributed? Not relevant. MLX, llama.cpp, Ollama, LM Studio, Msty? Apple's Foundation Models? As of 2026 Apple may have on-device AI but not headless. Agent runtimes: OpenHands, Aider, Goose, SWE-agent, Cline, AutoGen, LangGraph, CrewAI, PydanticAI, Letta, Smolagents. Memory: Letta, Mem0, Zep, Khoj? Vector DBs: LanceDB, Chroma, Qdrant, sqlite-vec, DuckDB FTS. Research: GPT-Researcher, STORM, OpenScholar? Need mention. Computer control: Playwright, Browserbase? Anthropic computer use? OpenInterpreter? Use terminal-first not GUI. Always-on: launchd, Temporal, Prefect, n8n. Remote: Tailscale, WireGuard, Cloudflare Tunnel (avoid public). Storage: APFS, Disk Utility, Thunderbolt.

Need mention not to install: Kubernetes/Docker Swarm, heavy Kafka/RabbitMQ, Postgres/pgvector initially, Elasticsearch, Weaviate/Milvus cluster, AutoGPT/AgentGPT legacy, many vector DBs, cloud-only agent platforms, GUI computer-use by default, Ollama if using llama.cpp? Maybe Ollama not bad but redundant. LM Studio for headless? Not. LangChain for everything? Avoid huge chains. Open WebUI? Could be nice but not necessary. n8n? Not for coding. Ray? heavy. CUDA stuff. ROS. Heavy observability stack. Don't install unvetted MCP servers. Don't run 100 model instances. Don't use base M6 for training/fine-tuning.

Need include future upgrade: 64/96/128GB: run 70B Q4 or 235B MoE Q2? Actually 235B too big. At 128GB can run DeepSeek-V3/R1 671B? no, needs >400GB. But can run 70B dense, 120B MoE, multiple 30B workers, larger context, local rerankers, Postgres, Qdrant. Dedicated GPU/server: move inference to server with vLLM/TensorRT-LLM? For Apple, maybe Mac Studio with M-series. Use networked OpenAI-compatible endpoint; orchestrator unchanged. Add object storage, NAS. Use Temporal when multi-node. Use containerized sandboxes.

Need include cost: local free; optional paid cloud APIs (Claude/GPT/Gemini/DeepSeek), search APIs (Brave/Tavily/Serper), push notifications (Pushover), Tailscale paid if needed, OrbStack license. When cloud worth: very large repo synthesis, state-of-art reasoning, difficult debugging, PDF complex tables, web search reliability. Local better: privacy, bulk code, overnight tasks, iterative loops, sensitive repos.

Need perhaps include performance estimates. Need not precise. Could say base M6 memory bandwidth likely ~120 GB/s? Need not claim. Maybe use "32 GB unified memory is the hard constraint; assume 100–150 GB/s class bandwidth; do not trust exact tok/s". But user asks calculate. We can estimate by model size: token generation roughly bandwidth / bytes read. For 30B active 3B MoE, active weights ~1.5GB at 4bit? Actually active 3B at 4bit ~1.5-2GB per token, so if 120GB/s, theoretical 60 tok/s, overhead lower. Dense 32B Q4 reads 16GB per token -> 7.5 tok/s theoretical. But MoE has routing overhead, KV. Could include as approximate. Need careful: MoE active parameters 3B, but expert selection; memory bandwidth still loads active experts; maybe 3B active gives faster. This supports Qwen3-30B-A3B. For small 8B Q4 ~4GB -> 30 tok/s theoretical. We'll say rough upper bounds, real lower. Useful work/hour: MoE 30B-A3B likely best balance. KV cache: context 16k for 30B maybe 1-3GB with GQA/q8; dense 32B maybe 3-6GB. Need not exact.

Need decide if use MLX for Qwen3-30B-A3B? MLX might have 4bit mlx models; can be faster. But llama.cpp can run MoE. Maybe MLX MoE support? likely. For production, use llama.cpp. But mention MLX alternative if benchmarks on your machine show >20% improvement; use same OpenAI API? MLX server. Could have both installed but only one active.

Need maybe mention Apple's Foundation Models (on-device) not suitable due to limited API and no autonomous headless. If macOS 26 has Apple Intelligence? Not for custom agents. Avoid.

Need maybe cite "M6 base not Pro/Max" constraints: fewer GPU cores, lower memory bandwidth than Pro/Max, no need for huge models. Use low quantization. Need maybe ensure external SSD not bottleneck: if Thunderbolt 3/4 or USB 3.2 2x2, fine; if USB 2, avoid DB. Use `diskutil info` and `fio` to test. Recommend APFS exFAT? Use APFS encrypted for external.

Need maybe include exact commands for user creation: macOS System Settings > Users & Groups; or `sudo sysadminctl -addUser aiworker -password ... -home /Users/aiworker -shell /bin/zsh`? Need careful. `sysadminctl` can create. Provide:
```
sudo sysadminctl -addUser aiworker -fullName "AI Worker" -password '...' -shell /bin/zsh -home /Users/aiworker
```
Need not make admin. Then create dirs, chown. Enable SSH: `sudo systemsetup -setremotelogin on`. Add key to `/Users/aiworker/.ssh/authorized_keys`. Tailscale: `brew install --cask tailscale`, open app, login. Or `brew install tailscale` and `sudo tailscaled`? On macOS app easier. Use `tailscale up --ssh`. Need mention.

Need exact launchd plist examples. Could include one for supervisor, one for model servers? Supervisor can manage model servers. Use LaunchDaemon for supervisor. Example:
```
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
 <key>Label</key><string>local.ai.supervisor</string>
 <key>UserName</key><string>aiworker</string>
 <key>ProgramArguments</key>
 <array>
  <string>/Users/aiworker/AgentLab/bin/ai-supervisor</string>
 </array>
 <key>WorkingDirectory</key><string>/Users/aiworker/AgentLab</string>
 <key>RunAtLoad</key><true/>
 <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
 <key>ThrottleInterval</key><integer>30</integer>
 <key>StandardOutPath</key><string>/Users/aiworker/AgentLab/logs/supervisor.out.log</string>
 <key>StandardErrorPath</key><string>/Users/aiworker/AgentLab/logs/supervisor.err.log</string>
 <key>EnvironmentVariables</key><dict><key>PATH</key><string>/opt/homebrew/bin:/usr/bin:/bin</string></dict>
</dict>
</plist>
```
Load: `sudo launchctl bootstrap system /Library/LaunchDaemons/local.ai.supervisor.plist`? Modern: `sudo launchctl load -w /Library/LaunchDaemons/...` maybe. Use `bootstrap` for newer. Provide both? Use `sudo launchctl bootstrap system /Library/LaunchDaemons/local.ai.supervisor.plist`. For user agent: `launchctl bootstrap gui/$UID`. Since dedicated user and no login, LaunchDaemon better. But if requires user environment, LaunchAgent with auto-login. Need mention.

Need maybe use `ai-ctl` commands. Could define CLI: `ai task add`, `ai status`, `ai approve`, `ai stop`. Implementation in Python.

Need architecture diagram: ASCII. Include layers: Phone -> Tailscale -> Gateway (FastAPI) -> Supervisor -> SQLite queue -> Worker pool -> LangGraph workflows -> Harnesses (Aider, Research pipeline, Browser) -> LiteLLM router -> local model servers (llama.cpp) / cloud optional -> Tools (shell wrapper, Git, FS, Playwright, retrieval) -> Memory (SQLite, files, vector). Observability: logs, dashboard, notifications. Security: policy engine, approval, sandbox.

Need "decisions at a glance" table: Layer | Pick | Why. Include inference runtime, primary model, fast model, embeddings, router, orchestration, coding agent, research pipeline, memory, queue, sandbox, remote, security, storage, dashboard. Need be decisive.

Need sources: list with primary/secondary. Since no browsing, mark "primary (not fetched live)". Need maybe group. Include URLs:
- https://github.com/ggml-org/llama.cpp (primary)
- https://github.com/ml-explore/mlx (primary)
- https://github.com/ollama/ollama (primary)
- https://lmstudio.ai/docs (primary?)
- https://qwen.readthedocs.io/ or https://huggingface.co/Qwen (primary)
- https://huggingface.co/nomic-ai/nomic-embed-text-v1.5 (primary)
- https://aider.chat/docs/ (primary)
- https://docs.all-hands.dev (OpenHands) (primary)
- https://github.com/SWE-agent/SWE-agent (primary)
- https://github.com/block/goose (primary)
- https://langchain-ai.github.io/langgraph/ (primary)
- https://ai.pydantic.dev/ (primary)
- https://microsoft.github.io/autogen/ (primary)
- https://docs.crewai.com/ (primary)
- https://github.com/huggingface/smolagents (primary)
- https://docs.letta.com (primary)
- https://www.sqlite.org/ (primary)
- https://github.com/asg017/sqlite-vec (primary)
- https://lancedb.github.io/lancedb/ (primary)
- https://docs.trychroma.com (primary)
- https://playwright.dev/python/docs/ (primary)
- https://github.com/searxng/searxng (primary)
- https://api.semanticscholar.org/ (primary)
- https://openalex.org/ (primary)
- https://www.crossref.org/documentation/ (primary)
- https://arxiv.org/help/api (primary)
- https://github.com/docling-project/docling (primary)
- https://github.com/datalab-to/marker (primary?) Actually marker repo maybe datalab-to/marker. primary.
- https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Articles/LaunchAgentsAndDaemons.html (primary)
- https://developer.apple.com/documentation/power-management/pmset? maybe https://ss64.com/osx/pmset.html secondary.
- https://tailscale.com/kb (primary)
- https://github.com/binwiederhier/ntfy (primary)
- https://github.com/BerriAI/litellm (primary)
- https://github.com/huggingface/text-embeddings-inference? not needed.
- Apple Silicon tuning? maybe https://developer.apple.com/metal/ primary.
Need maybe include independent benchmarks? Since no browsing, mention llama.cpp perplexity? Not exact. Could cite community benchmark repos? `llama.cpp discussion`? But no. Need say secondary sources not used for decisive claims.

Need maybe mention current state as of 2026? Could say "I cannot verify 2026-08-31 releases; choose technologies with stable interfaces and local-first properties. If Qwen3.5/DeepSeek etc exist, substitute equivalent model family using same criteria." But user wants decisive. Need perhaps include a "2026 caveat" but still recommend.

Need ensure no contradictions. Need maybe not claim M6 benchmarks. Use conditional.

Need think about exact hardware allocation. Let's produce table:
- macOS + desktop services: 5-7 GB
- Supervisor/queue/LiteLLM/logs: 0.5-1.5 GB
- Agent workers (Python/LangGraph/Aider): 1-3 GB
- Browser/Playwright (only when used): 2-4 GB; terminate after tasks
- Databases/embeddings: 0.5-1.5 GB
- Primary deep model weights: 16-20 GB Q4 for 30B MoE/32B dense
- KV cache: 2-5 GB at 8-16k with quantized cache
- Fast model (optional resident): 3-5 GB (8B Q4) or 2-3 GB (4B)
- File cache: variable; macOS uses free memory, reclaimable.
Recommended: Do not keep both 30B and 8B loaded if browser needed. Use profiles:
- Coding deep profile: unload fast model, load 30B, ctx 16k, parallel 1.
- Fast profile: load 8B, ctx 8k, parallel 2; no deep.
- Research retrieval: embeddings small always okay; reranker on-demand.
Number of concurrent workers: deep 1; fast 2 if only fast; tool-only workers 2-4. Model swapping worthwhile due to memory; use idle timeout 5-10 min.

Need maybe calculate storage:
Internal 512GB:
- macOS/apps: 60-100GB
- active models: 40-70GB (30B Q4 18-22GB, 8B 5GB, embed 0.5GB, rerank 2GB, caches)
- orchestrator/code/logs: 5-10GB
- active repos/worktrees: 50-100GB (limit)
- SQLite: <5GB
External 1TB:
- model archive: 200-500GB
- datasets/papers/snapshots: 300-700GB
- backups: 100-300GB
- git bare mirrors: 50-200GB
Need keep at least 15-20% free on internal.

Need maybe include benchmarking commands: `llama-bench`, `mlx_lm.benchmark`, `fio`, `time`. Use to validate.

Need maybe include "what to actually use" for each category. We can include in A table. But user asks for every major category identify 1-7. Need maybe provide a separate "Market comparison matrix" with columns: Best overall, best for your hardware, best open-source, lightweight, mature, cutting-edge, use. Categories: local inference runtime, local model, coding agent, agent orchestration, memory, research pipeline, browser control, sandbox, queue/durable execution, remote access, notifications, storage/vector DB. Could be a big table. Need ensure not too wide? Markdown table may be wide. Could split into multiple tables.

Need maybe mention alternatives less known: `exo`, `inference.sh`, `LocalAI`, `vLLM`? vLLM not Apple? It supports CPU? Not optimal. `PowerInfer`? `llamafile`? `Msty`? `Jan`? `GPT4All`? `KoboldCpp`? For Apple, llama.cpp/MLX. `KTransformers`? For MoE CPU? Not on Mac. `Ollama` popular but less control. `LocalAI` can be OpenAI-compatible but heavy. `LM Studio` user-friendly but not server-hardened. Need mention.

Agent harness alternatives: `Open Interpreter` (computer control, risky), `gptme`, `fabric`? `mentat`, `devika`? Could mention not needed. `CAMEL`, `MetaGPT`, `ChatDev`, `AutoDev`? Maybe not.

Need maybe mention "Model Context Protocol (MCP)" as emerging standard; use for tools if needed. But avoid using MCP as orchestration. Good.

Need perhaps mention "100 logical subagents" with examples: "repository-auditor", "test-runner", "dependency-updater", "literature-scout", "citation-verifier", etc. They are templates. Only active tasks consume workers. Use priority queues: critical interactive, background deep, batch. Use leases and token budgets. Use hierarchical coordinator: Objective -> Epic -> Task -> Step. Coordinator can spawn subagents by creating task rows with template. Avoid swarm free-for-all; hierarchical is best on limited hardware. Swarm can cause loops and memory blowup. Use deterministic state machine.

Need maybe include exact schema? Could provide minimal SQLite tables:
- tasks(id, parent_id, type, status, priority, agent_template, model_tier, input_json, output_json, lease_id, lease_expires, attempts, max_attempts, token_budget, created_at, updated_at)
- agents(id, name, template, permissions_json, model_tier, status)
- events(id, task_id, kind, payload_json, created_at)
- approvals(id, task_id, action, status, requested_at, decided_at)
- memory_facts(id, scope, kind, content, source_path, created_at)
- sources(id, kind, url, doi, arxiv_id, title, metadata_json, sha256)
- evidence(id, source_id, chunk_text, page, hash, embedding)
- claims(id, report_id, text, status)
Maybe include.

Need include policy config YAML example? Could. Example:
```
models:
 deep: qwen3-30b-a3b
 fast: qwen3-8b
 limits:
 max_concurrent_deep: 1
 max_concurrent_fast: 2
 task_timeout_min: 120
 daily_cloud_usd: 2
security:
 allow_write_paths: [~/AgentLab/workspaces]
 deny_commands_regex: [...]
 approval_required:
   - git push origin main
   - network post with secrets
   - rm -r
```
Need maybe not too much.

Need maybe discuss "operate the computer autonomously". We should say terminal/file/browser first, not GUI. GUI computer-use on macOS is brittle and risky. If needed later, use screen sharing + AppleScript with approval, dedicated user, no passwords. Better to use CLI APIs. For browser, Playwright headless with no saved credentials. For macOS apps, use `osascript` only for low-risk actions; require approval for Messages/Mail/Notes? Avoid.

Need include "research current ecosystem" but no browsing. Need maybe explicitly state "I did not use web/tools; this is based on internal knowledge. Since your date is 2026, verify model names/versions; however architecture is designed to be model-substitutable." This might disappoint but required. Need still decisive.

Need maybe mention "Apple M6 base may not support high memory pressure; use memory_pressure command to monitor." Use `memory_pressure`, `vm_stat`, `top`, `powermetrics`. Use `sudo powermetrics --samplers gpu_power,cpu_power,thermal`? Could for tuning.

Need maybe include testing and rollback in each phase. Could provide common failure modes:
- OOM: reduce ctx, unload models, use smaller quant.
- Model server hangs: healthcheck, restart.
- Prompt injection from web: policy, no auto-execute.
- Git conflicts: rebase fail, abort task.
- External SSD disconnect: mount check, stop tasks requiring it.
- Launchd not starting after reboot due to FileVault: need auto-login or local LaunchDaemon without GUI.
- Tailscale not connected: fallback local LAN.
- Runaway loops: step limits.
Need include rollback: config versioned in git, snapshots, Time Machine, model archive, database backup before migration.

Need maybe include exact commands to benchmark:
```
llama-bench -m model.gguf -p 512 -n 256
```
Maybe.

Need maybe include "avoid unnecessary infrastructure" explicitly: no Kubernetes, no Kafka, no Postgres initially, no Docker unless sandbox, no vector DB cluster. Good.

Need maybe answer in requested format exactly: 1. Header line, 2. decisions at a glance table, 3. numbered sections 1-10, 4. lettered deliverables A-K, 5. Sources. Need ensure no extra before header except header line. The first line should state model name etc. Could be:
`Model: Qwen3.8 | Knowledge cutoff: not exposed/reliable through 2024-12 (some 2025); browsing/tools: OFF`
Need maybe if knowledge cutoff known? Use "not exposed". But user says if known. Maybe: "Knowledge cutoff: unknown/not exposed (reliable knowledge through 2024; may include later training data)". Good.

Need make answer comprehensive. Need avoid too many caveats but include. Need be decisive. Let's outline final:

1 Header line.

2 Note? They ask short decisions table. Could include caveat after header? Maybe include "Method note" small. But format says header line then decisions table. We can include a one-sentence method note under header? Might violate? It's okay. But need state no browsing. Already header. Maybe table.

Decisions at a glance table:
Layer | Pick | Why
- Inference runtime: llama.cpp (llama-server) | mature Metal, quantization, ctx/KV controls.
- Primary model: Qwen3-30B-A3B-Instruct Q4_K_M | best agentic/coding per GB on 32GB; MoE active ~3B.
- Fast model: Qwen3-8B-Instruct Q4 (or 4B if memory) | routing/summarization.
- Embeddings: nomic-embed-text-v1.5 GGUF | small, strong retrieval.
- Model router: LiteLLM proxy | local/cloud routing, budgets.
- Orchestration: custom Python supervisor + SQLite + LangGraph workflows | lightweight durable, no heavy infra.
- Coding executor: Aider (headless) wrapped by supervisor | git-native, repo map, local models.
- Heavy dev sandbox: OpenHands optional later | full environment but heavy.
- Research: custom retrieval-augmented pipeline with Semantic Scholar/OpenAlex/SearXNG + Docling/PyMuPDF | evidence-grounded.
- Memory: Markdown + SQLite FTS5 + sqlite-vec | minimal.
- Queue: SQLite WAL with leases | enough.
- Sandbox: dedicated macOS user + workspaces + optional OrbStack/Colima for untrusted tests | security.
- Browser: Playwright ephemeral Chromium | controlled.
- Remote: Tailscale + SSH + local FastAPI dashboard + ntfy | private.
- 24/7: launchd + pmset + healthchecks | robust.
- Storage: internal active, external archive.

Then sections 1-10.

Section 1 Local inference:
- constraints, runtime comparison table: llama.cpp, MLX, Ollama, LM Studio, LocalAI, llamafile? Best for M6 32GB. Models to run: Qwen3-30B-A3B, Qwen3-8B, nomic embed. Quantization: Q4_K_M, maybe Q3 if memory. Context: 8-16k. Concurrency. Commands. Benchmarks. Maybe include model swapping.

Section 2 Agent runtimes/harnesses:
- comparison table. Decide custom control plane + Aider + LangGraph. Explain why not one product. OpenHands optional.

Section 3 Multi-agent architecture:
- concepts, hierarchical queue, 100 logical agents, worker pools, model routing, concurrency. Use SQLite. No 100 instances.

Section 4 Coding agents:
- compare Aider, OpenHands, SWE-agent, Goose, Cline/Roo, Codex/Claude Code, AutoDev? Pick Aider primary, OpenHands optional. Git worktree flow. Local model support.

Section 5 Research agents:
- pipeline, sources, PDF, citations, hallucination prevention. Tools.

Section 6 Persistent memory:
- compare options, pick filesystem+SQLite+sqlite-vec. Later graph.

Section 7 Computer control:
- terminal-first, dedicated user, sandbox, browser, GUI not default, credential isolation.

Section 8 Always-on:
- launchd, pmset, crash recovery, monitoring.

Section 9 Remote access:
- Tailscale, SSH, dashboard, notifications, approvals, emergency stop.

Section 10 Storage:
- internal/external plan, APFS, backups.

Deliverables A-K:
A. Recommended tech stack table (more detailed than decisions? maybe include alternatives and why). Need include categories. Could duplicate but okay. Maybe A table with Layer | Recommended | Alternatives | Why.
B Architecture diagram ASCII.
C Hardware/resource plan tables.
D Agent architecture details.
E Model strategy table.
F 24/7 architecture.
G Remote-control architecture.
H Security architecture.
I Exact installation plan. This needs detailed step-by-step. Could be long. Need include commands. Maybe break into phases. But implementation plan also requested separately? They asked implementation plan phases; final deliverables include I exact installation. Need maybe combine? Could provide implementation roadmap after deliverables? The user asks "Implementation plan Give practical roadmap phases" before final deliverables. We can include as part of I or separate section? To satisfy, include "Implementation roadmap" maybe after sections and before final deliverables? But format says numbered sections 1-10, lettered A-K. Implementation plan can be within I or separate after? Need ensure. Could include "Implementation roadmap" as part of Deliverable I (exact installation plan) with phases. Good.

J What NOT to install.
K Future upgrade path.

Sources list.

Need ensure final answer not too enormous but can be long. Need maybe compress some. But user expects huge. We can be thorough but manageable.

Let's develop details for each.

Section 1 local inference deeper:
Comparison table:
- llama.cpp: best maturity/control; model support GGUF; Metal; server; quant; concurrency; hot loading? Not automatic but process manager. Use.
- MLX: best Apple-native speed for MLX weights; simpler; less memory controls; use for experiments.
- Ollama: easiest; good for casual; limited ctx/KV/parallel; not primary.
- LM Studio: good GUI/model management; not headless/server; avoid for always-on.
- LocalAI: OpenAI-compatible multi-backend; heavy complexity; not needed.
- llamafile: single-file, easy; less control; not primary.
Models:
- Deep: Qwen3-30B-A3B-Instruct (MoE) Q4_K_M/QAT if available. Why: fits 32GB, active 3B faster, strong tool use/coding. If Qwen3-Coder 30B variant exists use it. If quality insufficient, cloud fallback.
- Dense alternative: Qwen3-32B-Instruct Q4 if you value quality over speed, but slower and memory tight. Use only with no browser.
- Fast: Qwen3-8B-Instruct Q4, fallback Qwen3-4B if memory. For classification/routing, 4B.
- Embeddings: nomic-embed-text-v1.5, bge-m3 if multilingual. Reranker optional bge-reranker-v2-m3.
- Avoid: 70B Q2/Q3, 123B MoE? Not fit or slow; 235B impossible; 8bit 32B too memory heavy; fp16.
Context and quant:
- Weights Q4_K_M or QAT 4-bit. Use KV q8_0 if llama.cpp. ctx 8192 default; 16384 for deep; avoid 32k unless no other processes and cache quant. Use prompt caching. Use `--parallel 1` for deep. `--batch-size` maybe 512. `--threads` physical CPU? Not too high. Use Metal GPU layers all.

Section 2 runtimes:
Comparison categories:
- OpenHands: best complete dev agent; Docker sandbox, UI, events; heavy; local LLM possible but 32GB limited. Use as optional heavy worker.
- Aider: lightweight coding; repo map, git, test/lint; needs orchestration; use primary.
- SWE-agent: issue-to-PR, container, benchmarks; less general; optional research.
- Goose: local/extensible MCP; promising; not primary due maturity? Maybe mention.
- LangGraph: durable orchestration; use for workflows.
- Pydantic AI: typed agents; use if custom tools; could be used inside workers. Maybe choose LangGraph for multi-step; Pydantic AI for simple agents? Need decide. Could say use Pydantic AI for single-purpose subagents and LangGraph for long workflows, but to reduce stack, use LangGraph only. Hmm.
- AutoGen/CrewAI: multi-agent but conversation-heavy, less deterministic; not primary.
- Letta/MemGPT: memory agents; interesting but adds complexity; not initial.
- Smolagents: lightweight code-as-action; could be used for quick tasks; not primary.
Decision: custom supervisor + LangGraph + Aider. If want less code, use Pydantic AI instead of LangGraph? But need durable. LangGraph checkpointer SQLite. Good.

Section 3 multi-agent: Need define terms. Use "logical agent = persisted role/profile/task state; runtime agent = worker process + model context." 100 logical agents stored in DB. Worker pool limited by hardware. Model router decides tier. Use task states: pending, leased, running, waiting_approval, done, failed. Use priority and budgets. Hierarchical coordinator. Dynamic agents created from templates with generated system prompt, tool ACLs, memory scope. Avoid peer-to-peer swarm; use message passing via task queue and artifacts. Concurrency: 1 deep, 1-2 fast, tool-only 2. For CPU-only tools (tests/builds) can run 1-2 concurrently depending CPU/thermal. Use workspaces. Use `nice`. Use model swapping. Throughput: maximize sequential deep tasks, parallel fast tasks. Use batch small tasks overnight.

Section 4 coding agents: compare table. Need mention repository understanding: Aider repo map uses tree-sitter; OpenHands uses runtime and browsing; SWE-agent uses search. Git worktrees: custom wrapper. Aider can commit; need configure `--auto-commits`, `--subtree-only`? Need maybe. It supports `--read-only`? It has `--yes` for auto. Use `aider --model openai/deep/local --message ...`? Actually aider CLI: `aider --message "..." --yes --no-auto-commits?` Need maybe not exact. It uses `.aider.conf.yml`. Need mention model via OpenAI compatible: set `OPENAI_API_BASE=http://127.0.0.1:4000/v1`, `OPENAI_API_KEY=local`, `AIDER_MODEL=openai/deep/local`? Aider model names maybe `openai/llama`? Need be careful. We can say configure via `--model openai/deep/local` with LiteLLM base. It supports `--model` with litellm? Aider supports any LiteLLM model string, e.g. `openai/model`. Good.
Testing: wrapper runs tests; if fail, feed errors back. Limit iterations. Code review: separate verifier agent reads diff. Use `git worktree add`, branch `agent/task-id`. Push only to local bare repo or remote with approval. For repository understanding: generate repo map, ADRs, symbol index; optionally use embeddings for large repos. But avoid embedding entire repo if huge; use ripgrep/tree-sitter.

Section 5 research agents: compare existing: GPT-Researcher, STORM, OpenResearcher? Pick custom because citation control. Could use GPT-Researcher as inspiration but not rely. Use APIs. For web search: self-host SearXNG; optional Brave/Tavily. For academic: Semantic Scholar, OpenAlex, Crossref, arXiv. For PDFs: Unpaywall, CORE. For parsing: Docling, Marker, PyMuPDF. Evidence DB. Claim verification. Reports. Need include hallucination prevention.

Section 6 memory: compare. Use SQLite + files. Use embeddings for retrieval. Avoid vector DB first. Add LanceDB/Qdrant if >1M chunks or multi-process concurrency. Knowledge graph later if relationships matter; use Kuzu embedded or RDF? Not initial. Episodic memory in events table. Semantic facts in memory_facts. Project memory markdown. Global memory curated. Memory writer agent summarizes completed tasks into ADRs. Need human review optional.

Section 7 computer control: compare terminal, filesystem, browser, GUI, VMs/containers, user accounts. Pick terminal/file/browser, no GUI. Dedicated user. Containers for untrusted. Use macOS sandbox? limited. Use OrbStack/Colima/Podman. Use separate APFS volume? Maybe. Credential isolation. Network. Approval matrix.

Section 8 always-on: details. Need include launchd, pmset, sleep prevention, watchdog. Use health endpoints. Use `launchd KeepAlive`. Use `ai-supervisor` heartbeats. Use `caffeinate`? If pmset enough. Use `pmset schedule`? Use power failure restart. Use Time Machine backup. Use log rotation. Need remote access after reboot: Tailscale as launch daemon? The app may need login? Tailscale Mac App Store version runs as app; for headless, install `tailscale` CLI? There is Tailscale client as system extension; may start at boot? Need ensure. Could use `brew install tailscale` and run `sudo tailscaled` as daemon? On macOS, official standalone? Tailscale has `tailscale` in Mac App Store and standalone. For headless, use standalone with login item? Need not go too deep. Mention enable automatic login for aiworker if using LaunchAgent, or use LaunchDaemon and ensure Tailscale starts. Maybe use `sudo tailscale up --ssh` after boot. If FileVault, physical access needed after reboot; for remote server, disable FileVault? Security tradeoff. Better keep FileVault and accept needing local unlock after power failure, or use secure token? Could mention. For 24/7, use UPS.

Section 9 remote: Tailscale, SSH, dashboard, ntfy, approvals. No public internet. Use `tailscale serve` to expose local dashboard within tailnet. Use passkeys if possible. Emergency stop: `ai-ctl stop-all`, `launchctl unload`, `touch STOP`. Use audit.

Section 10 storage: as above. Need include external SSD throughput: if Thunderbolt 3/4 ~20-40Gbps, fine; USB 3.2 10Gbps fine; if cheap SATA USB 3 ~5Gbps okay for archive but not DB. Use `diskutil apfs addVolume`? Maybe. Use encrypted APFS. Use mount stable `/Volumes/AgentVault`. Use `fstab`? For external, use UUID. But if not mounted, degrade. Keep active DB internal. Use rsync/Time Machine. Models on internal active; archive external.

Deliverables A-K. Need avoid redundancy but okay.

A table maybe:
| Layer | Recommended | Alternatives | Why |
Could include 20 rows. Need include categories and market labels? User wants for every category identify best overall etc. Maybe A can be the market comparison. Let's design A as table with columns Category | Best overall | Best for M6 32GB | Best OSS | Best lightweight | Best mature | Best cutting-edge | Use. But also they ask Layer | Recommended technology | Alternatives | Why. Hmm. Could provide A1 "Recommended stack" and A2 "Market comparison matrix". But final deliverables only A table? It says A. Recommended technology stack — table: Layer | Recommended technology | Alternatives | Why. The market comparison separately requested "Independently compare the market For every major category identify..." Could include in sections or a separate table before A? Maybe include as part of A with an additional table. Need not strictly one table. We can provide A with recommended stack, and a preceding "Market comparison matrix" in section? To satisfy, include a "Market comparison (major categories)" table maybe after decisions. But user requested final deliverables A-K; maybe market comparison can be inside A as "A1 market matrix". Let's include both: A1 Market comparison matrix, A2 Recommended stack. But A says table with Layer etc. Could be okay.

B diagram ASCII.
C hardware/resource plan. Include memory allocation table and storage table.
D agent architecture. Include concepts, queue schema, worker pool.
E model strategy. Table with task -> model -> local/cloud fallback -> context. Include exact model names.
F 24/7 architecture. Include launchd, recovery.
G remote. Include Tailscale.
H security. Include approval matrix.
I exact installation plan. Step-by-step with commands. Need be careful not to overwhelm. Could include phases and commands. Need exact? We'll provide. Since no versions, commands may need adapt. Include "verify with --version". Need maybe use `sudo -v`.

Let's draft I in detail:
0. Backup, update macOS, create external volume.
1. Create dedicated user:
```
sudo sysadminctl -addUser aiworker -fullName "AI Worker" -shell /bin/zsh -password 'CHANGE-ME'
sudo dscl . -append /Groups/com.apple.access_ssh GroupMembership aiworker  # maybe allow SSH? Not exact. Could just allow all users? macOS Remote Login can allow all users or specific. Use System Settings. Maybe avoid exact group. Provide command? `sudo sysadminctl -ssh allow`? Not sure. Better: System Settings > General > Sharing > Remote Login, allow aiworker only.
```
Need maybe `sudo systemsetup -setremotelogin on`.
2. Create dirs:
```
sudo -u aiworker mkdir -p /Users/aiworker/AgentLab/{bin,config,control,memory/{global,projects},research/{sources,pdfs,snapshots,reports},workspaces/{repos,worktrees,tmp},models/{active,archive},logs}
```
External:
```
diskutil list
diskutil apfs addVolume diskX APFS AgentVault -passphrase
mkdir /Volumes/AgentVault/{backups,models,papers,datasets,git-mirrors}
```
Need not exact diskX.
3. Install base tools:
```
sudo xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew update
brew install git uv sqlite ripgrep fd tree-sitter gh huggingface-cli? (huggingface-cli via uv)
```
Homebrew formula names? `ripgrep`, `fd`, `gh`, `tree-sitter`. `uv` via brew. `llama.cpp` maybe `brew install llama.cpp`? Need maybe if not, use `brew install ggml/llama.cpp/llama.cpp`? Hmm. To be safe: "brew install llama.cpp (or build from source if formula unavailable)". Use `brew install --cask tailscale` maybe. `brew install --cask orbstack` optional later.
4. Download models as aiworker:
```
uv tool install huggingface_hub
hf download Qwen/Qwen3-30B-A3B-Instruct-GGUF --include "*Q4_K_M.gguf" --local-dir ~/AgentLab/models/active
```
But `hf` command? In huggingface_hub 0.26, CLI is `huggingface-cli download`. Newer maybe `hf`. Use `huggingface-cli download`. Example:
```
huggingface-cli download Qwen/Qwen3-30B-A3B-Instruct-GGUF "*Q4_K_M.gguf" --local-dir ~/AgentLab/models/active
```
Need syntax: `huggingface-cli download repo_id [files] --include`. Could be. Use placeholder. For small and embedding.
5. Start model servers manually test:
```
llama-server -m ... --port 8081 ...
curl http://127.0.0.1:8081/v1/chat/completions ...
```
6. Install LiteLLM:
```
uv tool install 'litellm[proxy]'
```
Config. Run test.
7. Install supervisor skeleton: use `uv init`, `uv add fastapi uvicorn sqlalchemy apscheduler langgraph litellm pydantic httpx`. But exact code not needed. Provide commands. `ai-supervisor` script. Could include minimal FastAPI? Not full code. Need exact installation plan but not code? Could provide commands. Maybe include a minimal `ai-ctl` placeholder. But too long. We can say create Python package and provide key commands. Need be executable. Maybe provide `uv run uvicorn app.main:app --host 127.0.0.1 --port 8090`. But without code not executable. Could provide minimal `app.py`? Might be too long but possible. Need maybe not full production code. But user wants exact installation. We can give commands to clone a repo? There is no repo. Could provide skeleton commands and schema. Hmm.

Maybe we can say: "The control plane is small; bootstrap with these files" and include code snippets for `supervisor.py`? That would be huge. But final answer already huge. Need enough. Could provide high-level exact commands, not full code. User likely expects architecture not code. But says installation commands where applicable. We can include commands for dependencies and services, not implement entire supervisor.

Could recommend existing supervisor: Use `Launchd` + custom scripts. Need exact.

For coding agent:
```
uv tool install aider-chat
aider --version
```
Config `.aider.conf.yml`:
```
model: openai/deep/local
openai-api-base: http://127.0.0.1:4000/v1
openai-api-key: local
auto-commits: false
```
Actually aider config keys? Need check: `model`, `openai-api-base`, `openai-api-key`, `auto-commits`? likely. Could be okay.

Research:
```
uv tool install docling
uv add pymupdf requests beautifulsoup4
```
SearXNG optional: `brew services`? Could use Docker. Maybe skip self-host initially; use Brave API. But local/private? SearXNG self-host. Install from source? Could be heavy. Maybe say phase 3 uses Brave/Tavily if you accept cloud; otherwise install SearXNG with Podman/OrbStack. Commands:
```
brew install --cask orbstack
docker run -d --name searxng -p 127.0.0.1:8888:8080 searxng/searxng
```
But Docker on Mac via OrbStack. This uses container. Good. If avoid Docker, use paid search API. For security, SearXNG local but queries to public engines.

Memory:
SQLite schema commands. Could provide `sqlite3 control.db < schema.sql`.

Launchd plist as above. Use `sudo cp local.ai.supervisor.plist /Library/LaunchDaemons/`, `sudo launchctl bootstrap system ...`.

Power:
```
sudo pmset -a sleep 0 disksleep 0 displaysleep 10 womp 1 autorestart 1
sudo systemsetup -setrestartpowerfreeze on? 
```
Need verify commands. `pmset` parameters: `sleep`, `disksleep`, `displaysleep`, `womp` (Wake On Magic Packet), `ring`, `autorestart`? `pmset -g` shows `autorestart`? On macOS, `sudo pmset -a autorestart 1` may be valid. `sudo systemsetup -setrestartfreeze on` restarts after freeze. `sudo systemsetup -setrestartpowerfreeze on`? There is `setrestartfreeze` and `setrestartpowerfreeze`. We can include "if available". To avoid wrong, say use System Settings > Energy Saver/Battery to disable sleep and restart after power failure, or:
```
sudo pmset -a sleep 0 disksleep 0 displaysleep 10
sudo pmset -a womp 1
sudo systemsetup -setrestartfreeze on
```
Good.

Remote:
```
brew install --cask tailscale
open -a Tailscale
tailscale up --ssh
sudo systemsetup -setremotelogin on
```
Use Tailscale Serve:
```
tailscale serve --bg --https=443 http://127.0.0.1:8090
```
But `tailscale serve` on Mac? yes. Or SSH tunnel.

Notifications:
```
brew install ntfy
ntfy serve
```
Phone app subscribe to `https://mac-mini.tailnet:port`. Could use `tailscale serve` for ntfy.

Need J What NOT install: list with reasons.
Need K future upgrade.

Sources: Need list. Mark primary/secondary. Need maybe include note "not fetched live". Could include 30 sources. Keep manageable. Need maybe not include all. But user asks sources list with URLs marking primary/secondary. We'll include major.

Need think about potential hallucination of model names. Since date 2026, Qwen3 maybe okay. But if our knowledge cutoff not know Qwen3? We are Qwen3.8, likely know. Need maybe include "if newer Qwen3.x/DeepSeek models exist with same memory profile, swap in; criteria unchanged." Good.

Need maybe mention M6 not known. Could say: "I cannot verify M6-specific model support as of 2026; all recommendations depend only on Apple Silicon Metal and 32GB unified memory. Run `llama-bench` and `mlx_lm.benchmark` to confirm." Good.

Need maybe mention "web/tools disabled" in header. Good.

Need maybe avoid saying "current state as of 31 Aug 2026" with certainty. Could phrase: "Because browsing is off, I cannot confirm releases after my cutoff; the decisive choices below are based on stable architectural properties. If a materially newer Qwen3.x/MLX/llama.cpp release exists, use it if it passes the same memory/quality gates." This is honest. But user asked research current. We'll still deliver.

Need maybe cite "primary sources" but not verified. We can mark "primary (from memory; not fetched today)". Good.

Need maybe include "decisions are decisive". Good.

Let's draft final carefully.

Potential issue: The final answer may be extremely long. Need maintain clarity. Use markdown. Need ensure no hidden chain-of-thought. Final only.

Let's start constructing final in analysis then final. Need maybe write in one go.

Detailed content:

Header:
`Model: Qwen3.8 | Knowledge cutoff: not exposed to me; reliable through 2024-12, possibly later training; browsing/tools: OFF`
Maybe add "I answered from internal knowledge; verify 2026-08-31 versions." But format says header line then table. Could add small italic note after header. Fine.

Decisions at a glance table:
Need include "Layer" and "Final pick". Good.

Then maybe "Method note" short: no browsing, M6 caveat. But maybe after decisions? Let's include a short note before sections.

Section 1: Local inference.
Tables. Need include commands? Maybe later installation. But can include.

Let's write section 1:
- Hardware constraint: 32GB unified, base M6 lower bandwidth. Rule: weights + KV + macOS + tools <= 28GB. Use 4-bit.
- Runtime comparison table:
Runtime | Strength | Weakness | Verdict.
llama.cpp, MLX, Ollama, LM Studio, LocalAI, llamafile.
- Models table:
Role | Model | Quant | Why | Memory.
Deep: Qwen3-30B-A3B-Instruct Q4_K_M 16-20GB. Dense alt Qwen3-32B Q4 18-22GB slower. Fast: Qwen3-8B Q4 4-6GB, fallback Qwen3-4B 2.5-3.5GB. Embeddings nomic. Rerank optional.
- Context: default 8k, deep 16k, avoid 32k. KV q8. Concurrency: deep 1; fast 2 if no deep; tool-only 2. Model swapping yes. Use llama-server idle timeout. Use `llama-bench`.

Section 2: Agent runtimes. Table: OpenHands, Aider, SWE-agent, Goose, LangGraph, Pydantic AI, AutoGen/AG2, CrewAI, Letta, smolagents. Verdict. Need explain custom orchestration. Use LangGraph for workflows. Aider as coding executor. Optional OpenHands later. Good.

Section 3: Multi-agent. Terms and design. Include schema. Worker pool. Hierarchical. Dynamic agents. Throughput. Good.

Section 4: Coding agents. Table. Pick Aider. Include workflow. OpenHands optional.

Section 5: Research agents. Pipeline. Compare GPT-Researcher/STORM vs custom. Pick custom. Source APIs. Evidence. Good.

Section 6: Memory. Table options. Pick. Good.

Section 7: Computer control. Compare. Pick terminal-first. Dedicated user. Containers. GUI no. Good.

Section 8: Always-on. launchd etc.

Section 9: Remote. Tailscale etc.

Section 10: Storage. Drives.

Deliverables:
A: Maybe include market comparison matrix and recommended stack. To avoid too huge, maybe A table recommended stack, and earlier sections already compare. But user explicitly asks for every major category identify 1-7. Need maybe include a matrix. Let's include "A1. Market comparison matrix (major categories)" with columns: Category, Best overall, Best for your M6 32GB, Best OSS, Best lightweight, Best mature, Best cutting-edge, Use. This can satisfy. Then "A2. Recommended stack" maybe redundant but required. Could combine: In A1, "Use" is recommended. But required table Layer | Recommended technology | Alternatives | Why. Could make A2. This is a lot but okay.

Need keep tables manageable. Maybe A1 with 10 rows. A2 with 15 rows. Fine.

B diagram ASCII.
C hardware/resource plan: memory table, storage table, bottleneck. Good.
D agent architecture: detailed. Include queue states, worker pools, dynamic agent creation, 100 logical. Good.
E model strategy: table. Include fallbacks.
F 24/7: services and recovery.
G remote: Tailscale, dashboard, notifications.
H security: zones, approval matrix, kill switch.
I installation plan: step-by-step phases with commands. Need maybe long. Include phases 1-8 as requested implementation plan. Could label I.1 Phase 1 etc. Include exact commands. Need include rollback and testing in each phase? User asked for every phase provide technologies, commands, config, directory, architecture, communication, test, failure modes, rollback. That's massive. We can provide concise bullet for each phase. Need enough. Maybe include a table per phase? Could be too huge. But need satisfy. We'll provide phase sections with bullets: Tech, install/config, test, failure modes, rollback. Directory structure once. Communication once. Good.

J not install.
K upgrade path.

Sources list. Need maybe include note "Primary = official docs/repo; Secondary = independent analysis; none fetched live." Good.

Let's craft specifics.

Potential exact commands: Need be careful with `uv tool install litellm[proxy]`: shell quoting. Use `uv tool install 'litellm[proxy]'`. For aider: `uv tool install aider-chat`. For huggingface: `uv tool install huggingface_hub` then `huggingface-cli`. For docling: `uv tool install docling` maybe. For SearXNG via Docker: optional.

Need include Python supervisor skeleton commands:
```
sudo -u aiworker -H bash -lc '
cd ~/AgentLab
uv init control-plane
cd control-plane
uv add fastapi uvicorn sqlalchemy aiosqlite apscheduler httpx litellm langgraph pydantic pyyaml
'
```
But `uv init` creates project. `ai-supervisor` script maybe `uv run uvicorn control_plane.main:app`. Launchd ProgramArguments could be `/Users/aiworker/AgentLab/control-plane/.venv/bin/python -m control_plane`. Need not exact.

Maybe provide minimal `config/supervisor.yaml` example. Good.

Need include SQLite schema? Could include in D or I. Maybe D includes minimal schema. Good.

Need include `models` config. Example LiteLLM config:
```
model_list:
  - model_name: deep-local
    litellm_params:
      model: openai/deep-local
      api_base: http://127.0.0.1:8081/v1
      api_key: local
  - model_name: fast-local
...
router_settings:
  routing_strategy: simple-shard
```
Need maybe not exact. Good.

Need include `llama-server` service management: supervisor starts. But can provide manual commands.

Need include security approval matrix:
Operation | Autonomous | Approval required. Examples. Good.

Need include kill switch:
- file STOP
- `ai-ctl stop-all`
- dashboard button
- `launchctl bootout system/local.ai.supervisor`
- `sudo kill -TERM -1`? No.

Need include audit logs: all commands to JSONL, Git commits signed? Use GPG? Maybe SSH signing. Good.

Need include "human approval thresholds": cost > $X, cloud API, push to protected branch, installing packages, writing outside workspace, network requests with credentials, deleting > N files, database schema changes. Good.

Need include "runaway-agent protection": max steps 50, max runtime 2h, token budget, output hash loop detection, resource CPU >90% for 30min? Use watchdog. Good.

Need include "remote emergency stop" via SSH or dashboard. Good.

Need include "backups" and rollback: Time Machine, sqlite `.backup`, git branches, config in git, model archive. Good.

Need mention "use external SSD for model archive but active models internal; if internal too full, move less-used models external and load from there if Thunderbolt fast enough; monitor load times." Good.

Need include "expected bottlenecks": memory pressure, KV cache, SSD space, base M6 GPU cores, thermal (Mac mini fan? M6 mini maybe fan; sustained loads may throttle), web search rate limits, PDF parsing CPU, tests/builds CPU. Good.

Need maybe include "macOS unified memory pressure" command: `memory_pressure -l`. Use.

Need maybe include "do not fine-tune locally" as waste. Good.

Need maybe include "model selection automatic": router uses classifier fast model to label task: complexity, privacy, tool. But avoid LLM classification for every tiny task; use rules first. Model tiers: `tool-only`, `fast`, `deep`, `cloud-optional`. Good.

Need maybe include "research claims verification" use local NLI? Could use LLM as judge but require quotes. Maybe add optional `nli` model? Not needed.

Need maybe include "document generation": docs agents produce Markdown from code, ADRs, runbooks. Use fast model and repo map. Good.

Need maybe include "experiments": agent can run scripts, save artifacts to `research/experiments/<id>`, metadata in SQLite, analyze with pandas. Use Python env per project via `uv`. Avoid global installs. Good.

Need maybe include "datasets": store external, use DuckDB for analysis? Could mention DuckDB as optional lightweight analytical DB. But avoid unnecessary. If experiments need tabular analysis, use DuckDB local. Could include as optional. But not core. Maybe in future.

Need maybe include "100+ subagents" management: templates not processes. Good.

Need maybe include "MCP" in tools: Use MCP servers for filesystem? But security. Maybe include "If you use MCP, run only local, scoped MCP servers; do not allow a generic filesystem MCP outside workspace." Good.

Need maybe include "best cutting-edge" options: MLX, LangGraph, MCP, Qwen3 MoE, Docling. Good.

Need ensure final sources not too many but enough. Let's list ~35.

Need perhaps mention "Apple Foundation Models / Apple Intelligence" as not recommended. Could be in J. Good.

Now let's start writing final in mind. Need maintain markdown. Could be long. Ensure no analysis leaks.

Potential problem: We may not know exact Qwen3 model names. But we can use Qwen3. Need maybe if not exist by 2026? It likely does. Could mention "substitute current Qwen3.x equivalent". But decisive.

Need maybe mention "DeepSeek-R1 distill Qwen 32B"? For reasoning, DeepSeek-R1-Distill-Qwen-32B Q4 could be good. But 32B dense. Could be alternative. For agentic, Qwen3-Instruct better. For coding, Qwen2.5-Coder-32B? But older. Maybe include alternatives: DeepSeek-R1-Distill-Qwen-32B for reasoning, Llama-3.3-70B impossible, Mistral Small 24B? Good.

Need maybe mention "Qwen3-30B-A3B is MoE; if you prefer dense and can tolerate slower, Qwen3-32B." Good.

Need maybe include "Phi-4-mini"? For fast, Microsoft Phi-4-mini 3.8B good reasoning? Could be alternative. Gemma 3 4B/12B? But tool use maybe less. Keep Qwen.

Need maybe include "Mistral Small 3.2 24B"? Fits? 24B Q4 ~14GB; good. Alternative. But Qwen likely stronger coding. Good.

Need maybe mention "Llama 4 Scout/Maverick?" As of 2025 maybe Llama 4 models? Not sure. Avoid. Could mention "Meta Llama 3.1/3.2" as mature. But not best for 32GB? Llama 3.1 8B good, 70B not. Good.

Need maybe include "OpenAI-compatible endpoints". Good.

Need maybe include "local inference stable with Metal; do not use ROCm/CUDA". Good.

Need maybe include "Use `sysctl hw.memsize`? 32GB". Not needed.

Need maybe include "monitor with `asitop`?" As of 2026, `asitop` for Apple Silicon. Could mention for tuning. But not necessary. Could include in testing. `pipx install asitop`? Maybe.

Need maybe include "Mac mini thermal: set power mode to always plugged in, enable fans; avoid `sudo powermetrics` long". Good.

Let's write the final. Need be concise enough but detailed. We'll use headings. Ensure required order: header line, decisions table, numbered sections 1-10, lettered deliverables A-K, sources. We can include implementation plan within I. Good.

Let's produce final now.

## Run notes


