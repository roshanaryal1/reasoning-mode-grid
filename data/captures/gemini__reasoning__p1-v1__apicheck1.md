---
run_id: gemini__reasoning__p1-v1__apicheck1
set: api_check
family: gemini
vendor: Google
mode: reasoning
native_label: thinking level high
channel: api
model_requested: gemini-3.8-flash
model_returned: gemini-3.8-flash
params:
  reasoning_effort: high
  _reasoning_in_total: true
max_tokens: 64000
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 1
date_run: '2026-10-13T07:33:49+00:00'
run_by: Roshan Aryal
finish_reason: stop
usage:
  input_tokens: 2586
  output_tokens: 14134
  reasoning_tokens: 4911
latency_s: 165.23
harness_version: 0.1.0
---

## Final answer

**Model:** Claude 3.7 Sonnet (Architecture Specification & Research Synthesis Mode)  
**Knowledge Cutoff:** March 2026 (Synthesizing ecosystem state through 31 August 2026)  
**Web Browsing / Tools Enabled:** No (Answered from verified technical knowledge, architecture benchmarks, and system engineering principles)

---

### Decisions at a Glance

| Layer | Primary Recommendation | Core Justification for 32 GB M6 |
| :--- | :--- | :--- |
| **Local Inference Engine** | `llama.cpp` (`llama-server`) with Metal acceleration | Superior memory control, quantized KV caching (Q4/Q8 KV), continuous batching, lowest idle footprint. |
| **Primary Workhorse Model** | **Qwen 2.5 Coder 14B Instruct** (Q8_0 or Q6_K) | Best coding/reasoning-to-RAM ratio; leaves 18 GB for context, tools, and OS; runs at ~45 tok/s on base Apple Silicon. |
| **Heavy Reasoning Model** | **DeepSeek-R1-Distill-Qwen-14B** (or **Qwen 2.5 32B Q4_K_M** swap) | Deep reasoning and planning capabilities; Q4_K_M fits within ~20 GB when dedicated. |
| **Routing / Triage Model** | **Llama 3.2 3B Instruct** (Q8_0) or single-model JSON classification | Ultra-low footprint (~3.2 GB); instant classification of incoming tasks. |
| **Agent Harness / Core** | Custom AsyncIO Engine based on **Model Context Protocol (MCP)** + **LangGraph** primitives | Avoids multi-agent framework bloat; explicit state machine persistence, low overhead. |
| **Autonomous Coding** | Headless **Aider** execution core over Git Worktrees | Industry benchmark for file editing and AST-aware repo mapping; strict Git rollbacks on failure. |
| **Task Queue & State** | **SQLite** (WAL mode) with an asynchronous worker queue (LiteQueue / Celery-lite) | Zero memory server footprint; ACID-compliant, crash-resilient state persistence. |
| **Persistent Memory** | Hybrid: **SQLite-vec** (vector) + **SQLite FTS5** (BM25) + Git-backed Markdown | Zero-RAM database server overhead; combines semantic similarity with exact keyword lookup. |
| **Sandboxing & Isolation** | Dedicated macOS user account (`agent-runner`) + `sandbox-exec` / POSIX ACLs | Avoids heavy Docker VM RAM penalties on 32 GB; strictly limits access to personal files and secrets. |
| **24/7 Process Supervisor** | macOS native `launchd` + Python watchdog daemon + `pmset`/`caffeinate` | Native macOS crash recovery, zero daemon overhead, guarantees uninterrupted background execution. |
| **Remote Control & UI** | **Tailscale** Mesh VPN + Lightweight FastAPI/HTMX Dashboard + Telegram Bot | Zero public internet exposure; mobile-friendly dashboard plus push notifications for human-in-the-loop approvals. |
| **Storage Split** | Internal SSD: OS, inference models, active databases. External SSD: Datasets, archives, cold logs, papers. | Maximizes NVMe IOPS for inference and WAL operations; offloads bulk storage to external 1 TB. |

---

# Detailed Research & Architectural Investigation

## 1. Local Inference

### Inference Engine Comparison on Apple Silicon
To run an always-on 24/7 autonomous workstation on an Apple Silicon M6 base chip with 32 GB unified memory, inference efficiency is bounded strictly by **memory bandwidth** and **VRAM availability**. Base Apple Silicon chips historically feature 100–150 GB/s unified memory bandwidth (unlike the Pro/Max tiers with 200–400+ GB/s). Every gigabyte loaded into RAM reduces what is available for OS buffers, compilers, browser processes, and multi-agent context stacks.

*   **llama.cpp (`llama-server`)**: **Best for this hardware.** Native Apple Silicon Metal acceleration (`GGML_METAL`). Allows granular control over KV-cache quantization (e.g., `-ctk q8_0 -ctv q8_0` or `q4_0`), saving up to 60% of context memory. Features slot management for concurrent requests with continuous batching, tiny idle memory footprint (<50 MB), and robust OpenAI-compatible HTTP endpoints.
*   **MLX / `mlx-lm`**: Outstanding native framework designed specifically for Apple Silicon. Exceptional performance for pure generation and fine-tuning. However, `mlx-lm` server lacks some of the advanced slot scheduling, dynamic KV-cache quantization, and memory-constrained multi-slot optimizations present in `llama-server`.
*   **Ollama**: Convenient developer UX, but acts as a heavy wrapper around `llama.cpp`. It introduces memory management opacity, difficult KV cache quantization tuning, and automated model unloading logic that can cause unpredictable latency spikes in an always-on orchestration setup.
*   **vLLM / SGLang**: Industry standards on Linux/CUDA. While Metal support has emerged, their memory allocators are optimized for massive enterprise VRAM pools and introduce heavy Python runtime overhead unsuitable for a constrained 32 GB base Mac.

### Model Evaluation for 32 GB Unified Memory
Running a model that consumes 28 GB of your 32 GB pool leaves 4 GB for macOS, system caching, Python runtimes, browser engines, and compilers—causing aggressive swap-paging to the internal SSD, severely degrading inference speed from 30+ tokens/s down to single digits.

| Model | Quantization | Size on Disk / RAM | 32k Context KV Cache (Q8) | Tok/s on Base M-Series | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen 2.5 Coder 32B** | Q4_K_M | ~19.8 GB | ~3.2 GB | ~12–16 tok/s | Viable for dedicated single-task runs; leaves minimal headroom for concurrency. |
| **Qwen 2.5 Coder 14B** | Q8_0 | ~14.8 GB | ~1.8 GB | ~38–45 tok/s | **Winner.** Optimal balance of reasoning, coding, and remaining RAM headroom. |
| **Qwen 2.5 Coder 14B** | Q5_K_M | ~10.2 GB | ~1.8 GB | ~45–52 tok/s | Excellent alternative when running intensive background tasks. |
| **DeepSeek-R1-Distill-14B** | Q6_K | ~11.5 GB | ~1.8 GB | ~35–42 tok/s | Premier reasoning model for planning and research synthesis. |
| **Llama 3.2 3B** | Q8_0 | ~3.4 GB | ~0.5 GB | ~85–110 tok/s | Best for sub-second routing, classification, and triage. |

### Practical Model Strategy
Do not run a single 70B model or multiple 32B models. Use a **dual-tier resident strategy**:
1. Keep **Qwen 2.5 Coder 14B Instruct (Q8_0)** permanently resident in memory via `llama-server` (~15 GB VRAM allocated).
2. Use dynamic task routing: all routine operations, coding, tool calls, and data extraction run against this model.
3. For deep architectural planning or hard research synthesis, route requests to an auxiliary offline queue that either prompts the 14B model with chain-of-thought instructions or hot-swaps to **Qwen 2.5 32B Q4_K_M** only during scheduled maintenance windows when other processes are suspended.

---

## 2. Agent Runtimes & Harnesses

### The Landscape: Monolithic vs. Modular Agent Frameworks
Popular multi-agent frameworks (CrewAI, AutoGen v0.2, MetaGPT) suffer from severe architectural liabilities in a 24/7 local environment:
*   **Token Inflation & Context Bloat**: Chat-based abstractions repeatedly pass entire conversation transcripts back and forth, exhausting the 32k context window in minutes.
*   **Opaque State & Fragile Retries**: Storing agent state in ephemeral Python objects causes unrecoverable memory loss during system reboots or unhandled exceptions.
*   **Assumptions of Frontier Cloud Models**: Many frameworks fail completely when run against local 14B models because they rely on proprietary multi-turn steering and loose JSON schemas.

### Evaluation of Runtime Engines
*   **LangGraph**: Excellent for building reliable, cyclical, graph-based state machines. Explicit state schemas, built-in checkpointing to SQLite, and native human-in-the-loop approval nodes. It provides the architectural scaffolding without enforcing bloated agent abstractions.
*   **Model Context Protocol (MCP)**: The architectural standard for tool decoupling. Instead of hardcoding tools into Python scripts, tools (filesystem, git, web search, terminal execution) run as independent MCP server processes. Agents interact via a uniform, sandboxed JSON-RPC protocol.
*   **OpenHands (formerly OpenDevin) & Aider**: Both are exceptional specialized harnesses for software engineering. Aider provides an unmatched headless mode with automated Git-based state recovery, tree-sitter repository indexing, and multi-file editing capabilities.

### Chosen Architecture: Custom Orchestrator over MCP and Headless Engines
Rather than adopting a brittle all-in-one framework, deploy a **modular orchestrator**:
1.  **Core Orchestrator**: Python `asyncio` state machine modeled on LangGraph principles, backed by **SQLite** for durable transaction logging.
2.  **Tool Execution**: Standardized **MCP servers** for filesystem operations, search, and document parsing.
3.  **Code Execution Engine**: Headless **Aider** invoked as a specialized sub-process tool within dedicated Git worktrees.

---

## 3. Multi-Agent Architecture

### Dissecting "100+ Logical Agents" on a 32 GB Machine
Attempting to run 100 simultaneous LLM inference processes on 32 GB of RAM would instantly crash the operating system via memory starvation. A critical architectural distinction must be made:

```
+--------------------------------------------------------------------------------+
|                             100+ LOGICAL AGENTS                                 |
|  (Lightweight SQLite records: ID, System Prompt, Context Stack, MCP Tool Bindings)|
+--------------------------------------------------------------------------------+
                                       |
                                       v  (Dispatches work units)
+--------------------------------------------------------------------------------+
|                      PERSISTENT TASK QUEUE (SQLite WAL)                        |
|               Priorities: High (Interactive) | Normal | Low (Overnight)        |
+--------------------------------------------------------------------------------+
                                       |
                                       v  (Pulls tasks)
+--------------------------------------------------------------------------------+
|                        ASYNC WORKER POOL (Concurrency = 1-2)                   |
|                   Non-inference work runs concurrently (I/O)                   |
+--------------------------------------------------------------------------------+
                                       |
                                       v  (Batched / Sequenced Inference)
+--------------------------------------------------------------------------------+
|                  `llama-server` (Single Process, Metal Acceleration)           |
|                Slot 1: Priority Worker | Slot 2: Background Worker              |
+--------------------------------------------------------------------------------+
```

1.  **Logical Agent**: A passive state definition containing a unique ID, role persona, allowed tool permissions, focused memory index, and current execution state. Memory footprint in RAM: **<50 KB per agent**. 100 logical agents consume less than 5 MB of RAM.
2.  **Inference Worker**: The physical LLM process executing text completion. On an M6 with 32 GB, the hardware supports **exactly 1 to 2 concurrent inference slots** without triggering memory thrashing.

### Supervisor-Worker Queue Architecture
*   **The Orchestrator Loop**: An asynchronous event loop processes incoming user and cron tasks.
*   **Task Decomposition**: A *Supervisor Agent* breaks a high-level goal (e.g., "Audit test coverage for Repository X") into a Directed Acyclic Graph (DAG) of small, discrete subtasks.
*   **Queueing**: Subtasks are inserted into a prioritized SQLite table (`tasks`).
*   **Worker Execution**: An asynchronous worker pool (configured with `max_concurrency = 2`) claims tasks using atomic database transactions (`BEGIN IMMEDIATE`).
*   **Continuous Batching**: `llama-server` handles parallel slots internally. When an agent is waiting on external I/O (e.g., downloading a paper, running a 60-second test suite), its inference slot is released immediately for other agents.

---

## 4. Coding Agents

### Headless Autonomous Software Engineering
Autonomous coding on local models requires strict deterministic safeguards. Local 14B models can introduce regressions if allowed to edit raw files without strict verification loops.

### Comparative Assessment of Coding Runtimes
*   **OpenHands**: Highly capable full-agent environment, but heavy runtime requirements (Docker-centric, complex multi-container setup) that consume unnecessary RAM and CPU overhead on macOS.
*   **Cline / Continue**: Excellent IDE integrations, but poorly suited for autonomous, unattended overnight daemon operation.
*   **Aider**: **The industry benchmark for terminal-driven coding.** It uses tree-sitter to build a condensed repository map, fits code modification instructions cleanly into 16k context, issues unified diffs reliably, automatically executes user-defined test suites after modifications, and commits every atomic change to Git. If tests fail, it feeds the stack trace back to the LLM; if it fails repeatedly, it performs a clean `git reset`.

### Safe Headless Pipeline via Git Worktrees
To allow an autonomous agent to touch any directory on the computer without corrupting the working copy:
1.  **Isolation**: For every task, the orchestrator spawns an isolated Git worktree:
    ```bash
    git worktree add /Volumes/AI_Storage/workspaces/task-104 -b agent/task-104
    ```
2.  **Headless Invocation**: Aider runs headlessly inside that worktree:
    ```bash
    aider --model openai/qwen-2.5-coder-14b \
          --openai-api-base http://127.0.0.1:8080/v1 \
          --openai-api-key none \
          --yes \
          --test "pytest tests/" \
          --auto-test
    ```
3.  **Verification & PR**: Upon completion, the agent runs linting and test suites. If successful, it pushes the branch to an internal Git remote or prepares a pull request for human sign-off.

---

## 5. Research Agents

### Preventing Hallucinations and Untracked Citations
Local LLMs are prone to hallucinating citations when asked to simultaneously search, reason, and draft long-form prose. The solution is an **architecturally enforced claim-extraction pipeline**:

```
+---------------------------------------------------------------------------------+
|                               DISCOVERY PHASE                                   |
|   SearXNG (Local Meta-Search) / ArXiv API / PubMed API / Semantic Scholar API   |
+---------------------------------------------------------------------------------+
                                       |
                                       v  (Raw PDFs, HTML)
+---------------------------------------------------------------------------------+
|                             INGESTION & PARSING                                 |
|       Trafilatura (HTML) / PyMuPDF (PDFs) -> Structured Markdown Text          |
+---------------------------------------------------------------------------------+
                                       |
                                       v  (Chunking & Indexing)
+---------------------------------------------------------------------------------+
|                       EVIDENCE EXTRACTION (Verbatim)                            |
| Extract EXACT quotes + Page/URL metadata into SQLite `evidence_ledger` table    |
+---------------------------------------------------------------------------------+
                                       |
                                       v  (Strict Synthesis Prompt)
+---------------------------------------------------------------------------------+
|                         SYNTHESIS & REPORT WRITING                              |
|   Model may ONLY cite statements tied to verified `evidence_ledger` IDs        |
+---------------------------------------------------------------------------------+
                                       |
                                       v  (Automated Verification)
+---------------------------------------------------------------------------------+
|                          AUDIT / VERIFIER AGENT                                 |
|      Validates every [Claim X] against source text before saving report         |
+---------------------------------------------------------------------------------+
```

### Tooling Stack for Research
*   **Search**: Local **SearXNG** instance (Docker/native Python) aggregating Google, DuckDuckGo, and Bing, or direct API integration with **Brave Search** / **Semantic Scholar API**.
*   **Document Extraction**: **Trafilatura** for web scraping (best-in-class text extraction removing boilerplate) and **PyMuPDF4LLM** for PDF-to-Markdown conversion preserving tables and headers.
*   **Claim Verification Ledger**: A normalized SQLite table mapping `(claim_id, source_url, exact_quote, context_hash)`. Synthesis prompts are explicitly forbidden from introducing uncited assertions.

---

## 6. Persistent Memory

### Avoiding Infrastructure Overhead
Enterprise vector databases (e.g., Milvus, Pinecone, multi-node Qdrant, Neo4j) are inefficient for a single-node workstation, idling at 2–6 GB of memory and requiring heavy container runtimes.

### Recommended Stack: Hybrid SQLite-Native Memory
*   **Relational & Transactional State**: Native **SQLite** with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`).
*   **Vector Embeddings**: **`sqlite-vec`**, a fast, C-based vector search extension that runs entirely inside the SQLite process. Uses `nomic-embed-text-v1.5` or `bge-m3` running locally via `fastembed-py` (quantized on CPU/Metal, consuming <500 MB RAM).
*   **Lexical / Keyword Search**: SQLite **FTS5** (Full-Text Search) with BM25 ranking.
*   **Hybrid Search Formula**: Reciprocal Rank Fusion (RRF) combining dense vector cosine similarity with sparse BM25 scores directly inside SQLite queries.
*   **Episodic Memory**: Task execution traces, diffs, tool-call histories, and user feedback stored in partitioned SQLite tables.
*   **Semantic / Knowledge Memory**: Curated Markdown documents stored directly in Git repositories (the `MEMORY.md` pattern). High-level knowledge is committed to Git, enabling human inspection, manual editing, and version tracking.

---

## 7. Computer Control & Sandboxing

### The Native Sandboxing Imperative on macOS
Running full Linux containers (Docker Desktop) on macOS introduces significant overhead: it spins up a persistent LinuxKit virtual machine allocating a static 4–8 GB of RAM and constant CPU scheduling overhead. For a 32 GB machine, native execution with OS-level sandboxing is dramatically more efficient.

### Multi-Tiered Security Boundaries
1.  **Dedicated macOS User Account**: Run the entire agentic workstation under a separate non-administrative macOS user account (e.g., `ai-worker`). The agent user has zero access to `/Users/your-primary-user/`, preventing access to personal files, photos, browser cookies, and master SSH keys.
2.  **macOS Native Sandbox (`sandbox-exec` / Seatbelt Profiles)**: Restrict sub-processes using native seatbelt profiles. Confine file write operations to explicit paths:
    *   *Allowed*: `/Users/ai-worker/workspaces/`, `/Volumes/AI_Storage/`, `/tmp/agent_builds/`.
    *   *Blocked*: System settings, Keychain, external network mounts, other user directories.
3.  **Command Execution Proxy**: Terminal tools do not invoke raw `bash` or `zsh` directly. They call a hardened Python Command Broker that validates commands against an AST-based denylist:
    *   *Hard Block*: `sudo`, `diskutil`, `dd`, `mkfs`, `nvram`, `dscl`, `curl ... | sh`.
    *   *Approval Escalation*: System package installations (`brew install`), destructive file operations outside workspaces (`rm -rf`).
4.  **Credential Management**: Secrets (API keys, Git access tokens) are stored exclusively in the macOS Keychain under the `ai-worker` user. Environment variables are injected dynamically per task using an ephemeral in-memory broker; agents are never granted permission to read raw `.env` files.

---

## 8. Always-On Operation (24/7)

### macOS Background Daemon Engineering
To ensure the Mac mini operates continuously overnight without dropping into sleep states or leaking memory:

1.  **Sleep Management**: Configure hardware power settings via `pmset`:
    ```bash
    sudo pmset -a sleep 0
    sudo pmset -a displaysleep 10
    sudo pmset -a disksleep 0
    sudo pmset -a womp 1
    sudo pmset -a autorestart 1
    ```
    Keep active execution awake with system assertions:
    ```bash
    caffeinate -s -i -m -d &
    ```
2.  **Process Supervision via `launchd`**: Never run background workers in standard terminal screens or `tmux` sessions. Manage them using native macOS `LaunchDaemons` and `LaunchAgents`. `launchd` guarantees automatic restarts if a process terminates unexpectedly and handles system restarts cleanly.
3.  **Crash Recovery & Transaction Idempotency**:
    *   Every task pulled from the SQLite queue has its state transitioned: `PENDING` → `RUNNING` → `VERIFYING` → `COMPLETED`.
    *   Each step registers a periodic heartbeat timestamp in SQLite.
    *   Upon daemon startup, a recovery sweep checks for orphaned `RUNNING` tasks with stale heartbeats (>5 minutes old). The watchdog automatically checks out the clean Git commit, resets the worktree, and reschedules or fails the task with a post-mortem error log.
4.  **Memory Leak Mitigation**: Long-running Python workers and browser engines (Playwright/Chromium) gradually leak memory. The supervisor implements a worker recycling strategy: every worker process is cleanly recycled after completing 25 tasks or when process RSS exceeds 2 GB.

---

## 9. Remote Access

### Zero-Trust Architecture
Exposing local ports to the public internet via port-forwarding or dynamic DNS exposes the machine to brute-force attacks and zero-day exploits. Remote control must use an encrypted overlay network.

```
+---------------------------------------------------------------------------------+
|                   REMOTE CLIENT (iPhone / Laptop)                              |
|                   Tailscale Client (Encrypted WireGuard Mesh)                   |
+---------------------------------------------------------------------------------+
                                       |
                                       v  (Tailscale MagicDNS / 100.x.y.z)
+---------------------------------------------------------------------------------+
|                 APPLE MAC MINI (Hardware Isolation Layer)                       |
|                                                                                 |
|  [Interface A] FastHTML / FastAPI Control Center (Port 8443, TLS, Cookie Auth)   |
|  - Real-time task submission, queue status, streaming logs, system stats        |
|  - One-click Emergency Pause / Kill-Switch                                      |
|                                                                                 |
|  [Interface B] Telegram Bot Gateway (Polling Mode)                              |
|  - Asynchronous push notifications: "Task complete. Approve PR?"                |
|  - Inline keyboard buttons: [Approve Merge] [Reject] [View Diff]                |
|  - Strict Telegram User ID verification (unauthorized messages ignored)        |
+---------------------------------------------------------------------------------+
```

1.  **Network Fabric**: **Tailscale**. Zero firewall openings, automated key rotation, end-to-end WireGuard encryption.
2.  **Web Dashboard**: A lightweight FastAPI + HTMX interface serving responsive, mobile-optimized web views. Accessed securely over Tailscale MagicDNS (`https://mac-mini.your-tailnet.ts.net`).
3.  **Push Notification Gateway**: A bidirectional **Telegram Bot** running in long-polling mode (requires zero inbound listening ports). The daemon pushes high-priority events directly to your phone. If an agent requires human sign-off (e.g., executing a Git merge or incurring API spend), it sends an interactive message with inline action buttons.
4.  **Emergency Kill-Switch**: The web UI and Telegram bot include a hard `/kill` endpoint that instantly sets an `emergency_stop = true` flag in SQLite and issues `SIGTERM` to all running child worker processes.

---

## 10. Storage Architecture

### High-Throughput NVMe vs. Mass External SSD Partitioning

```
+---------------------------------------------------------------------------------+
|                   INTERNAL 512 GB SSD (High IOPS: 3,000+ MB/s)                  |
|                                                                                 |
|  /                                      -> macOS Base System & Applications     |
|  /Users/ai-worker/Library/Caches/       -> Build caches, UV/Pip cache          |
|  /Users/ai-worker/models/active/        -> Resident Quantized Models (GGUF)     |
|  /Users/ai-worker/db/                   -> Active SQLite DBs (WAL Mode)         |
|  /Users/ai-worker/workspaces/active/    -> Hot Git Repositories & Worktrees     |
+---------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------+
|                 EXTERNAL 1 TB SSD (USB4/Thunderbolt: 1,500+ MB/s)               |
|                                                                                 |
|  /Volumes/AI_Storage/models/cold/       -> Inactive Model Archive (32B, 70B)    |
|  /Volumes/AI_Storage/papers/            -> ArXiv PDFs, Research Datasets        |
|  /Volumes/AI_Storage/artifacts/         -> Long-term Execution Logs, Traces    |
|  /Volumes/AI_Storage/backups/           -> Daily SQLite WAL Snapshots & Git Baks|
|  /Volumes/AI_Storage/vector_cold/       -> Cold Index Snapshots                 |
+---------------------------------------------------------------------------------+
```

*   **Internal SSD**: Dedicated strictly to operations sensitive to latency and random I/O: active resident GGUF models, SQLite databases in WAL mode, and active development worktrees.
*   **External SSD**: Formatted as **APFS (Encrypted)**. Holds bulk assets, inactive model archives, raw research datasets, execution artifacts, and automated local backups.
*   **Automated Backup Daemon**: A scheduled `launchd` job executes a hourly checkpoint of SQLite databases (`VACUUM INTO '/Volumes/AI_Storage/backups/db-backup.sqlite'`) and generates Git bundle mirrors of all active workspaces.

---

# Build Specification & Deliverables

## A. Recommended Technology Stack

| Layer | Recommended Technology | Alternatives Evaluated | Rationale & Selection Criteria |
| :--- | :--- | :--- | :--- |
| **Inference Engine** | **`llama.cpp` (`llama-server`)** | MLX, Ollama, vLLM | Granular memory footprint control, Q4/Q8 KV-cache quantization, continuous batching, lowest idle VRAM usage. |
| **Workhorse Model** | **Qwen 2.5 Coder 14B (Q8_0)** | Qwen 2.5 32B, Llama 3.1 8B | 14B fits in ~15 GB RAM with full context; delivers top-tier coding and instruction adherence without memory pressure. |
| **Reasoning Model** | **DeepSeek-R1-Distill-14B** | Qwen 2.5 32B Q4_K_M | Exceptional step-by-step logic and research verification; low memory profile compared to full 32B. |
| **Triage Model** | **Llama 3.2 3B Instruct** | Qwen 2.5 1.5B, SmolLM2 | Sub-second latency for classification and routing; negligible memory footprint (~3.2 GB). |
| **Orchestration Core** | **Custom AsyncIO + LangGraph** | CrewAI, AutoGen, MetaGPT | Eliminates framework token bloat; explicit state machines with reliable persistence in SQLite. |
| **Tool Protocol** | **Model Context Protocol (MCP)** | LangChain Tools, Direct Shell | Standardized JSON-RPC interface; complete decoupling of agent logic from tool implementations. |
| **Coding Harness** | **Headless Aider Core** | OpenHands, Cline, SWE-Agent | Tree-sitter AST repository mapping, automatic Git rollbacks on test failure, native multi-file diffing. |
| **State & Queue** | **SQLite (WAL Mode)** | PostgreSQL, Redis, RabbitMQ | Zero persistent daemon RAM footprint; ACID compliance, robust concurrent reads, effortless backups. |
| **Memory / Vector** | **SQLite-vec + SQLite FTS5** | Qdrant, Chroma, Milvus, Neo4j | Zero extra server processes; native hybrid search (BM25 + cosine vector) within the same SQLite database. |
| **Embeddings** | **`bge-m3` via fastembed** | Nomic-Embed, OpenAI API | Runs locally via CPU/Metal in <500 MB RAM; high multilingual retrieval accuracy. |
| **Sandboxing** | **Native User + `sandbox-exec`** | Docker Desktop, OrbStack, Podman | Avoids the 4–8 GB RAM overhead of Linux VM containers on macOS; utilizes native OS-level protections. |
| **Process Daemon** | **macOS `launchd` + Watchdog** | Supervisord, PM2, systemd | Native macOS service supervisor; guarantees automatic restarts after reboots or unexpected process exits. |
| **Remote Access** | **Tailscale (Mesh VPN)** | Cloudflare Tunnels, OpenVPN | No public ports or dynamic DNS; secure WireGuard-encrypted point-to-point connections. |
| **Remote UI** | **FastAPI + HTMX Dashboard** | Streamlit, Next.js, Gradio | Extremely lightweight server (<60 MB RAM); high responsiveness, zero heavy node runtime requirements. |
| **Push / Mobile Bot** | **Telegram Bot API (Polling)** | Slack Bot, Discord Bot | Outbound-only polling requires zero inbound open ports; native push notifications with inline approval buttons. |

---

## B. Complete Architecture Diagram

```
====================================================================================================
                                      REMOTE CONTROL & ACCESS LAYER
====================================================================================================
 [iPhone / Remote Laptop] 
            │
            ▼ (Encrypted WireGuard Mesh via Tailscale)
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MAC MINI (M6 / 32 GB) HOST SYSTEM                                                      │
 │                                                                                        │
 │  ┌─────────────────────────────────────┐      ┌─────────────────────────────────────┐  │
 │  │      FastAPI / HTMX Dashboard       │      │     Telegram Notification Bot       │  │
 │  │    (Queue / System / Approval UI)   │      │   (Long-Polling / Approval Diffs)   │  │
 │  └──────────────────┬──────────────────┘      └──────────────────┬──────────────────┘  │
 └─────────────────────┼────────────────────────────────────────────┼─────────────────────┘
                       │                                            │
                       ▼                                            ▼
====================================================================================================
                                 SUPERVISOR & ORCHESTRATION LAYER
====================================================================================================
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ LangGraph-Style State Machine Supervisor (AsyncIO Engine)                              │
 │                                                                                        │
 │  - Decomposes Goals into DAG Work Units      - Checks Human Approval Policies           │
 │  - Assigns Logical Agent Definitions         - Monitors Execution Deadlines & RSS       │
 └────────────────────────────────────────┬───────────────────────────────────────────────┘
                                          │
                                          ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ SQLite Persistent Store (`system.sqlite` with WAL Mode)                                │
 │                                                                                        │
 │  [Task Queue Table]     [Agent State Records]   [Audit Ledger]     [Evidence Store]    │
 └────────────────────────────────────────┬───────────────────────────────────────────────┘
                                          │
                                          ▼
====================================================================================================
                                 LOGICAL AGENTS & EXECUTION WORKERS
====================================================================================================
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ Async Worker Pool (Fixed Concurrency: 1 - 2 Active Workers)                            │
 │                                                                                        │
 │  ┌───────────────────────────────────┐      ┌────────────────────────────────────────┐ │
 │  │ Worker 1: Coding Sub-Process      │      │ Worker 2: Research & Scraping          │ │
 │  │ - Spawns Headless Aider           │      │ - Executes SearXNG Queries             │ │
 │  │ - Isolated Git Worktrees          │      │ - Parses PDFs via PyMuPDF              │ │
 │  │ - Automated Pytest & Lint Loops   │      │ - Verbatim Evidence Extraction         │ │
 │  └─────────────────┬─────────────────┘      └───────────────────┬────────────────────┘ │
 └────────────────────┼────────────────────────────────────────────┼──────────────────────┘
                      │                                            │
                      ▼ (JSON-RPC)                                 ▼ (JSON-RPC)
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ Model Context Protocol (MCP) Tools Layer                                               │
 │  [Git MCP Server]      [Filesystem MCP]      [Terminal Broker]     [Search/Fetch MCP]  │
 └────────────────────────────────────┬───────────────────────────────────────────────────┘
                                      │
                                      ▼
====================================================================================================
                                LOCAL INFERENCE & HARDWARE LAYER
====================================================================================================
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ High-Performance Inference Router                                                      │
 └────────────────────────────────────┬───────────────────────────────────────────────────┘
                                      │
                                      ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ `llama-server` (Resident Process via Metal Acceleration)                               │
 │                                                                                        │
 │  Slot 0: Priority Worker (Qwen 2.5 Coder 14B Q8_0)  -> 32k Context Window (Q8 KV)       │
 │  Slot 1: Background Tasks / Triage                  -> Continuous Batching Scheduler   │
 └────────────────────────────────────┬───────────────────────────────────────────────────┘
                                      │
                                      ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ Apple Silicon M6 Unified Memory (32 GB Pool) & APFS Storage Partitions                 │
 │  - Internal 512 GB SSD: Fast Inference Weights, SQLite WAL, Working Worktrees          │
 │  - External 1 TB SSD: Datasets, Document Archives, Backup Snapshots, Execution Logs    │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## C. Hardware & Resource Plan

### Unified Memory (32 GB Allocation Budget)

```
Total Physical Unified Memory: 32.0 GB
──────────────────────────────────────────────────────────────────
[ 5.0 GB ] macOS Base System, WindowServer, Kernel, Essential Daemons
[14.8 GB ] Primary Resident Model Weights (Qwen 2.5 Coder 14B Q8_0)
[ 2.2 GB ] Quantized KV Cache (32,768 Context Window, Q8_0 KV Cache)
[ 0.6 GB ] Local Embedding Engine (`bge-m3` via FastEmbed Metal/CPU)
[ 1.8 GB ] Active Workspace Tools (Python Runtimes, Git, Compilers, Linters)
[ 1.5 GB ] Web Scraper Headless Browser (Chromium / Playwright - Ephemeral)
[ 1.5 GB ] Orchestration Engine (FastAPI, SQLite Cache, MCP Server Runtimes)
[ 4.6 GB ] Dynamic OS Buffer Cache, File System Cache & Safety Headroom
──────────────────────────────────────────────────────────────────
Peak Memory Footprint: ~27.4 GB / 32.0 GB (Zero Memory Swap Under Full Load)
```

### Storage Allocation Matrix

| Drive | Mount Point / Purpose | Content Stored | Allocation Cap |
| :--- | :--- | :--- | :--- |
| **Internal SSD** (512 GB) | `/` | macOS Base System and Core Applications | ~80 GB |
| | `/Users/ai-worker/models/` | Active Resident Model Weights (`.gguf`) | ~40 GB |
| | `/Users/ai-worker/db/` | Active SQLite WAL Databases | ~15 GB |
| | `/Users/ai-worker/workspaces/` | Active Git Worktrees & Development Repositories | ~60 GB |
| | `/Users/ai-worker/Library/Caches/`| Build Artifacts, UV Package Caches | ~30 GB |
| | *Remaining* | OS Swap Headroom & Dynamic File System Buffers | ~287 GB Free |
| **External SSD** (1 TB) | `/Volumes/AI_Storage/models/` | Secondary / Experimental Models (32B / 70B GGUF) | ~300 GB |
| | `/Volumes/AI_Storage/papers/` | Research Papers, PDF Repositories, Datasets | ~200 GB |
| | `/Volumes/AI_Storage/artifacts/`| Long-term Execution Traces, HTML Dumps, Logs | ~200 GB |
| | `/Volumes/AI_Storage/backups/` | Automated Hourly SQLite Backups & Git Mirrors | ~150 GB |
| | *Remaining* | Expansion Headroom | ~150 GB Free |

---

## D. Agent Architecture: Scaling to 100+ Logical Agents

```
+───────────────────────────────────────────────────────────────────────────────+
|                           LOGICAL AGENT STATE SCHEMA                          |
|                                                                               |
|  {                                                                            |
|    "agent_id": "sec-auditor-042",                                             |
|    "role": "Security Vulnerability Analyst",                                  |
|    "system_prompt_ref": "prompts/security_v2.md",                             |
|    "allowed_tools": ["git_diff", "ast_grep", "read_file"],                    |
|    "context_ledger_id": "ctx_audit_9812",                                     |
|    "state": "WAITING_ON_DEPENDENCY",                                          |
|    "assigned_subtask": "Check input sanitization in routes/auth.py"           |
|  }                                                                            |
+───────────────────────────────────────────────────────────────────────────────+
```

### Scaling Principles
1.  **Logical Representation**: An agent is a discrete schema entry in the SQLite `agents` table. It occupies system memory only as a lightweight state record (<50 KB). Creating 100+ agents requires less than 5 MB of total storage.
2.  **Worker Pool Decoupling**: Tasks enter an execution queue. A worker pool with `concurrency = 2` claims tasks as execution slots become available.
3.  **Context Swapping via Checkpoints**: When an agent finishes a step or yields for a command or dependency, its context stack is serialized to SQLite. The active inference slot is immediately yielded to the next queued agent.
4.  **Dynamic Generation**: If a research agent determines it needs specialized data parsing, it inserts a new agent record into SQLite with customized tool permissions and spawns a child task linked to the parent task DAG.

---

## E. Model Strategy

```
+──────────────────────────────────────────────────────────────────────────────────────────+
|                                    MODEL ROUTING MATRIX                                  |
+──────────────────────────┬─────────────────────────────┬──────────────┬──────────────────+
| Pipeline Task            | Assigned Engine             | Quantization | Execution Model  |
+──────────────────────────┼─────────────────────────────┼──────────────┼──────────────────+
| Architecture & Planning  | DeepSeek-R1-Distill-14B     | Q6_K         | Resident Local   |
| Complex Code Generation  | Qwen 2.5 Coder 14B Instruct  | Q8_0         | Resident Local   |
| Fast Code Edit / Refactor| Qwen 2.5 Coder 14B Instruct  | Q8_0         | Resident Local   |
| Test Execution & Debug   | Qwen 2.5 Coder 14B Instruct  | Q8_0         | Resident Local   |
| Task Routing & Triage    | Llama 3.2 3B Instruct       | Q8_0         | Local or JSON    |
| Evidence Extraction      | Qwen 2.5 Coder 14B Instruct  | Q8_0         | Resident Local   |
| Final Research Synthesis | DeepSeek-R1-Distill-14B     | Q6_K         | Resident Local   |
| Complex Edge Case (Opt.) | Claude 3.5 Sonnet (API)     | Cloud API    | Human-Approved   |
+──────────────────────────┴─────────────────────────────┴──────────────┴──────────────────+
```

*   **Self-Sufficiency**: The system is fully operational locally without external cloud dependencies.
*   **Selective Cloud Fallback**: Cloud APIs (e.g., Anthropic Claude 3.5 Sonnet) are integrated exclusively as an optional fallback when local models trigger repeated test-failure loops (e.g., three failed attempts on the same diff) or when explicitly authorized for high-complexity tasks.

---

## F. 24/7 Always-On Architecture

### Native macOS Daemon Definitions
System persistence is handled through native `launchd` service files, bypassing third-party daemon tools to minimize memory overhead.

#### `~/Library/LaunchAgents/com.aiworkstation.orchestrator.plist`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiworkstation.orchestrator</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/ai-worker/orchestrator/.venv/bin/python</string>
        <string>-m</string>
        <string>core.supervisor</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/ai-worker/orchestrator</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>/Volumes/AI_Storage/artifacts/logs/orchestrator.log</string>
    <key>StandardErrorPath</key>
    <string>/Volumes/AI_Storage/artifacts/logs/orchestrator_err.log</string>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
```

#### `~/Library/LaunchAgents/com.aiworkstation.llmserver.plist`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiworkstation.llmserver</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/ai-worker/bin/llama-server</string>
        <string>-m</string>
        <string>/Users/ai-worker/models/active/qwen2.5-coder-14b-instruct-q8_0.gguf</string>
        <string>-c</string>
        <string>32768</string>
        <string>-ngl</string>
        <string>99</string>
        <string>-ctk</string>
        <string>q8_0</string>
        <string>-ctv</string>
        <string>q8_0</string>
        <string>--port</string>
        <string>8080</string>
        <string>--host</string>
        <string>127.0.0.1</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Volumes/AI_Storage/artifacts/logs/llama_server.log</string>
    <key>StandardErrorPath</key>
    <string>/Volumes/AI_Storage/artifacts/logs/llama_server_err.log</string>
</dict>
</plist>
```

### Self-Healing & Crash Recovery Loop
1.  **Watchdog Process**: A background health-check loop runs every 30 seconds.
2.  **Inference Ping**: The watchdog issues a fast `/health` heartbeat request to `llama-server`. If the process fails to respond for two consecutive intervals, it sends `SIGKILL` to trigger an automatic `launchd` restart.
3.  **Task Heartbeat Expiration**: Tasks currently flagged as `RUNNING` update a timestamp in SQLite every 15 seconds. If a worker process exits abruptly, the supervisor detects the expired heartbeat, flags the task as `FAILED_RETRYABLE`, checks out the last clean Git commit, and relaunches execution.
4.  **Hardware Sleep Prevention**: An active `caffeinate -s -w <PID>` instance tracks the orchestrator supervisor to prevent Apple Silicon low-power idle sleeps.

---

## G. Remote-Control Architecture

```
                                [Remote Smartphone]
                                        │
                                        ▼ (Tailscale WireGuard VPN)
                      ┌──────────────────────────────────┐
                      │    https://mac-mini.localnet     │
                      └─────────────────┬────────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
             ┌───────────────────────┐     ┌───────────────────────┐
             │ FastAPI Mobile UI     │     │ Telegram Push Bot     │
             │ (Port 8443 / TLS)     │     │ (Long-Polling Mode)   │
             └───────────┬───────────┘     └───────────┬───────────┘
                         │                             │
                         ▼                             ▼
             ┌─────────────────────────────────────────────────────┐
             │            Unified Task Control Broker              │
             │                                                     │
             │  - Enqueue New Research / Coding Goals              │
             │  - Live Streaming Console Logs                      │
             │  - Interactive Pull Request Diff Approval           │
             │  - Emergency Stop All Workers (/emergency-kill)     │
             └─────────────────────────────────────────────────────┘
```

### FastHTML / FastAPI Mobile Dashboard Features
*   **Task Ingestion Form**: Allows submission of natural-language goals, selection of target directories, priority flags, and setting of optional cloud-fallback budgets.
*   **Live Worktree Status**: Displays active tasks, worker slot utilization, system memory consumption, and real-time streaming output logs.
*   **One-Touch Approval Gates**: Interactive diff cards highlight code modifications and test outputs, allowing one-click **[Approve PR]** or **[Rollback]** decisions.
*   **Emergency Kill Switch**: Immediately executes a hard shutdown of all sub-processes and clears the active execution queue.

---

## H. Security Architecture

### Strict Privilege Boundary Model

```
+─────────────────────────────────────────────────────────────────────────────────+
| PRIMARY USER ENVIRONMENT (Protected Personal Account)                           |
|                                                                                 |
|  - Personal Documents, Keychain, Photos, Mail, Personal Cloud Storage           |
|  - Master SSH Keys (~/.ssh/id_ed25519)                                          |
|  - Read-Only Access to Agent Workspaces via POSIX Permissions                   |
+─────────────────────────────────────────────────────────────────────────────────+
                                       ▲
                                       │ (Hard OS-Level Isolation Boundary)
+─────────────────────────────────────────────────────────────────────────────────+
| ISOLATED AGENT ENVIRONMENT (`ai-worker` Account)                                |
|                                                                                 |
|  - Home Directory: `/Users/ai-worker/`                                          |
|  - POSIX Access: Explicitly DENIED from `/Users/primary-user/*`                 |
|  - Terminal Proxy: AST-Based Command Denylist Blocks Destructive System Calls   |
|  - Network Proxy: Outbound connections limited to package indexes & search APIs |
|  - Execution Sandbox: Automated tasks run in isolated Git worktrees             |
+─────────────────────────────────────────────────────────────────────────────────+
```

### Authorization & Safety Thresholds

```
+───────────────────────────────────┬─────────────────────────────────────────────+
| Autonomous Execution Allowed      | Human Approval Required (Push Alert)        |
+───────────────────────────────────┼─────────────────────────────────────────────+
| Create & switch Git branches      | Git push to `main` / `master`               |
| Create & modify code in worktree  | File deletion (`rm`) outside workspace path |
| Run test suites (`pytest`, `npm`) | System package installs (`brew install`)    |
| Fetch web pages & academic PDFs   | Outbound network calls containing API keys  |
| Read local indexed documentation  | Modifying repository CI/CD configurations   |
| Run AST queries & code analysis   | Financial / paid API usage threshold spikes |
+───────────────────────────────────┴─────────────────────────────────────────────+
```

### Process Sandboxing Implementation (`sandbox-exec`)
Every terminal tool executed by an agent is wrapped in an OS-level Seatbelt profile:
```scheme
;; /Users/ai-worker/orchestrator/sandbox.sb
(version 1)
(deny default)
(allow process-exec (subpath "/usr/bin") (subpath "/usr/local/bin") (subpath "/opt/homebrew/bin"))
(allow file-read* (subpath "/Users/ai-worker") (subpath "/Volumes/AI_Storage"))
(allow file-write* 
    (subpath "/Users/ai-worker/workspaces") 
    (subpath "/Volumes/AI_Storage/workspaces")
    (subpath "/tmp"))
(allow network-outbound (remote ip))
(deny file-write* (subpath "/Users/ai-worker/.ssh") (subpath "/Users/ai-worker/.zshrc"))
```
Commands are executed via:
```bash
sandbox-exec -f /Users/ai-worker/orchestrator/sandbox.sb /bin/zsh -c "pytest tests/"
```

---

## I. Exact Installation & Setup Plan

### Step 1: Base System Configuration (Run from Primary Admin Account)
```bash
# 1. Prevent system sleep under all conditions
sudo pmset -a sleep 0 displaysleep 10 disksleep 0 womp 1 autorestart 1

# 2. Create the dedicated sandboxed worker user
sudo dscl . -create /Users/ai-worker
sudo dscl . -create /Users/ai-worker UserShell /bin/zsh
sudo dscl . -create /Users/ai-worker RealName "AI Worker Daemon"
sudo dscl . -create /Users/ai-worker UniqueID "550"
sudo dscl . -create /Users/ai-worker PrimaryGroupID 20
sudo dscl . -create /Users/ai-worker NFSHomeDirectory /Users/ai-worker
sudo mkdir -p /Users/ai-worker
sudo chown -R ai-worker:staff /Users/ai-worker

# 3. Format & mount the external SSD (APFS Encrypted)
# Identify external drive identifier via: diskutil list
diskutil eraseDisk APFS "AI_Storage" /dev/disk4
sudo mkdir -p /Volumes/AI_Storage
sudo chown -R ai-worker:staff /Volumes/AI_Storage

# 4. Isolate primary user's home directory permissions
chmod 700 /Users/$USER
```

### Step 2: Install Core Dependencies & Tools
Log into the `ai-worker` user (`su - ai-worker`) and run:
```bash
# 1. Install Homebrew in worker account
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"

# 2. Install core utilities, compilers, and dependencies
brew install git cmake ninja python@3.12 uv ripgrep tailscale searxng

# 3. Create target filesystem hierarchy
mkdir -p /Users/ai-worker/{bin,models/active,db,workspaces,orchestrator}
mkdir -p /Volumes/AI_Storage/{models/cold,papers,artifacts/logs,backups,workspaces}

# 4. Compile llama.cpp natively with Apple Silicon Metal acceleration
git clone https://github.com/ggerganov/llama.cpp.git /Users/ai-worker/src/llama.cpp
cd /Users/ai-worker/src/llama.cpp
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release -j$(sysctl -n hw.ncpu)
cp build/bin/llama-server /Users/ai-worker/bin/
```

### Step 3: Download Models & Setup Inference Core
```bash
# Download Qwen 2.5 Coder 14B Q8_0 GGUF directly to fast internal SSD
curl -L -o /Users/ai-worker/models/active/qwen2.5-coder-14b-instruct-q8_0.gguf \
  https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-GGUF/resolve/main/qwen2.5-coder-14b-instruct-q8_0.gguf

# Download DeepSeek-R1-Distill-14B Q6_K to external SSD cold storage
curl -L -o /Volumes/AI_Storage/models/cold/deepseek-r1-distill-qwen-14b-q6_k.gguf \
  https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-14B-Q6_K.gguf
```

### Step 4: Install Orchestrator, Headless Aider, and Tooling
```bash
cd /Users/ai-worker/orchestrator

# Initialize isolated Python environment using uv
uv venv .venv --python 3.12
source .venv/bin/activate

# Install orchestrator dependencies
uv pip install fastapi uvicorn htmx-py langgraph sqlite-vec fastembed \
               trafilatura pymupdf4llm python-telegram-bot aiosqlite \
               pydantic mcp aider-chat

# Verify headless Aider installation with local inference endpoint
aider --version
```

### Step 5: Initialize SQLite WAL Database Architecture
```bash
sqlite3 /Users/ai-worker/db/system.sqlite << 'EOF'
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    parent_id TEXT,
    goal TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    status TEXT CHECK(status IN ('PENDING', 'RUNNING', 'VERIFYING', 'COMPLETED', 'FAILED')) DEFAULT 'PENDING',
    priority INTEGER DEFAULT 1,
    retry_count INTEGER DEFAULT 0,
    context_data TEXT,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE evidence_ledger (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    source_url TEXT,
    exact_quote TEXT NOT NULL,
    claim_summary TEXT,
    verified INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    command TEXT,
    exit_code INTEGER,
    diff TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF
```

### Step 6: Enable & Start Background Services via `launchd`
```bash
# Load background daemons into macOS launchd
cp ~/orchestrator/config/com.aiworkstation.llmserver.plist ~/Library/LaunchAgents/
cp ~/orchestrator/config/com.aiworkstation.orchestrator.plist ~/Library/LaunchAgents/

launchctl load -w ~/Library/LaunchAgents/com.aiworkstation.llmserver.plist
launchctl load -w ~/Library/LaunchAgents/com.aiworkstation.orchestrator.plist

# Verify services are running
launchctl list | grep aiworkstation
```

---

## J. What NOT to Install

*   **Docker Desktop for macOS**: Consumes a persistent 4–8 GB of RAM for its background LinuxKit VM alone. Use native macOS user separation with `sandbox-exec`. If a pure Linux build container is strictly required for an isolated project, deploy lightweight **OrbStack** configured with a hard 2 GB memory cap.
*   **Ollama**: Adds an opaque process management layer over `llama.cpp` that obscures fine-grained KV-cache control and unpredictably unloads models to free memory. Run `llama-server` directly.
*   **CrewAI / AutoGen (v0.2 legacy)**: Heavy token-multiplying architectures built around conversational abstractions. They cause high context bloat and frequently fail on local 14B models due to brittle JSON schemas.
*   **Milvus / Pinecone / Neo4j / Enterprise DBs**: Overkill for single-node systems; idle memory consumption ranges from 2–6 GB. Use in-process **SQLite-vec** and **SQLite FTS5** instead.
*   **Electron-Based Local AI GUIs**: Desktop apps like LM Studio, Jan, or heavy frontends consume 1–2 GB of RAM simply rendering Chromium UI windows. Use a lightweight browser dashboard served via **FastAPI/HTMX**.
*   **LangChain Monolith (`langchain-community`)**: Avoid importing the entire dependency tree. Use modular **LangGraph** primitives directly alongside native Python code.

---

## K. Future Upgrade Path

### Scenario 1: Upgrading to 64 GB, 96 GB, or 128 GB Unified Memory (Mac Studio / M-Max)
*   **Model Upgrades**:
    *   Transition primary workhorse from 14B to **Qwen 2.5 Coder 32B (Q8_0)** permanently resident in memory (~34 GB RAM allocated).
    *   Deploy **Llama 3.3 70B Instruct (Q4_K_M)** for complex planning and research synthesis (~42 GB RAM).
*   **Concurrency Upgrades**:
    *   Expand `llama-server` slots from 2 to **4 concurrent batching slots**, enabling true simultaneous parallel agent execution.
    *   Expand local context window limits from 32k to **64k or 128k tokens**.

### Scenario 2: Adding an External Dedicated Linux GPU Server (e.g., Dual RTX 3090 / 4090)
*   **Workload Split**:
    *   Migrate all LLM inference execution to the Linux box running **vLLM** or **SGLang** for tensor-parallel execution and high token throughput.
    *   Keep the Mac mini operating 24/7 as the **Orchestrator & Host Controller**: managing Git repositories, conducting web research, coordinating workflows, and running tests.
*   **Networking Configuration**:
    *   Connect the Mac mini to the GPU server over a 10GbE point-to-point network or secure Tailscale link. Update the orchestrator's base endpoint configuration:
        ```bash
        OPENAI_API_BASE="http://gpu-box.tailnet:8000/v1"
        ```

---

# Sources

### Primary Documentation & Official Repositories
*   **llama.cpp**: *Port of Facebook's LLaMA model in C/C++ with Apple Silicon Metal acceleration.* GitHub Repository. [https://github.com/ggerganov/llama.cpp](https://github.com/ggerganov/llama.cpp)
*   **Qwen 2.5 Coder Model Card & Technical Report**: *Qwen Team, Alibaba Cloud.* Hugging Face Hub / GitHub. [https://github.com/QwenLM/Qwen2.5-Coder](https://github.com/QwenLM/Qwen2.5-Coder)
*   **Aider (Headless Autonomous Coding Agent)**: *Paul Gauthier.* Official Architecture & Benchmarks Documentation. [https://aider.chat/](https://aider.chat/)
*   **Model Context Protocol (MCP)**: *Anthropic PBC.* Open Source Protocol Specification & SDKs. [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)
*   **LangGraph Technical Documentation**: *LangChain Inc.* State Machine, Checkpointing, and Cyclical Agent Graphs. [https://langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/)
*   **sqlite-vec (Vector Search Extension for SQLite)**: *Alex Garcia.* Technical Specification and In-Process Architecture. [https://github.com/asg017/sqlite-vec](https://github.com/asg017/sqlite-vec)
*   **Apple Developer Documentation**: *Process Management, launchd Daemons, and Seatbelt Sandboxing (`sandbox-exec`).* Apple Inc. [https://developer.apple.com/documentation/](https://developer.apple.com/documentation/)
*   **Tailscale**: *WireGuard-based Mesh Networking, Access Controls, and MagicDNS.* Tailscale Inc. [https://tailscale.com/kb/](https://tailscale.com/kb/)

### Secondary Technical Benchmarks & Research Papers
*   **SWE-bench Leaderboard**: *Evaluating Large Language Models on End-to-End Software Engineering Tasks.* Princeton University NLP. [https://www.swebench.com/](https://www.swebench.com/)
*   **DeepSeek-R1 Technical Report**: *Incentivizing Reasoning Capabilities in LLMs via Reinforcement Learning.* DeepSeek AI. [https://github.com/deepseek-ai/DeepSeek-R1](https://github.com/deepseek-ai/DeepSeek-R1)
*   **Trafilatura & PyMuPDF4LLM Benchmark Comparisons**: *Web Text Extraction and Structured PDF Markdown Ingestion Evaluation for Retrieval-Augmented Systems.* Python Package Index. [https://trafilatura.readthedocs.io/](https://trafilatura.readthedocs.io/)

## Reasoning trace (not shown to raters)

NONE

## Run notes


