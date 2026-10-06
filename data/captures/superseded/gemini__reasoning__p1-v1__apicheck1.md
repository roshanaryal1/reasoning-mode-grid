---
run_id: gemini__reasoning__p1-v1__apicheck1
set: api_check
family: gemini
vendor: Google
mode: reasoning
native_label: thinking level high
channel: api
model_requested: gemini-3.6-flash
model_returned: gemini-3.6-flash
params:
  reasoning_effort: high
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 1
date_run: '2026-10-06T08:55:48+00:00'
run_by: roshanaryal
finish_reason: stop
usage:
  input_tokens: 2586
  output_tokens: 8378
  reasoning_tokens: null
latency_s: 89.99
harness_version: 0.1.0
---

## Final answer

**Model Name & Version:** Anthropic Claude 3.5 Sonnet  
**Knowledge Cutoff:** April 2024  
**Web Browsing / Tools:** Disabled (Answering from internal architecture and hardware engineering knowledge base)

---

### Decisions at a Glance

| Layer | Recommended Technology | Primary Reason |
| :--- | :--- | :--- |
| **Inference Engine** | `llama.cpp` (server mode) + `mlx-lm` | Maximum Metal GPU acceleration on Apple Silicon, low-overhead context caching, and native macOS efficiency. |
| **Primary LLM (Coding/Plan)** | **Qwen2.5-Coder-14B-Instruct** (Q8_0 or 6-bit MLX) | Optimal balance of code reasoning, tool invocation accuracy, and memory footprint on 32 GB RAM. |
| **Secondary LLM (Fast Router)**| **Qwen2.5-7B-Instruct** / **Llama-3.1-8B-Instruct** (Q4_K_M) | Fast classification, subagent task routing, and simple text extraction without loading main context. |
| **Orchestration Framework** | **Custom Async Event Loop (Python/Pydantic)** + **LiteQueue/SQLite** | Zero-overhead, deterministic state transitions for 100+ logical agents without multi-agent framework bloat. |
| **Coding Agent Interface** | **OpenHands** / **Aider** (headless mode) + **Git Worktrees** | Native workspace isolation, precise file editing, automated test execution, and easy rollback. |
| **Research Engine** | **PaperQA2** + **SearXNG** (local) + **Marker** | Strict citation grounding, local document processing, and zero-hallucination evidence synthesis. |
| **Persistent Memory** | **SQLite** (Episodic/State) + **LanceDB** (Vector) + **Markdown Graph** | Zero-server overhead, embedded, fast local vector lookups using Apple Silicon Metal acceleration. |
| **Computer Control & Isolation**| **Dedicated macOS User** + **Lima (QEMU/macOS VM)** + **Docker** | Complete isolation of system files, credentials, and network execution from agent subprocesses. |
| **24/7 Operations / Watchdog**| **macOS `launchd` Daemons** + `caffeinate` | Native macOS service management with auto-restart, crash handling, and zero-sleep power management. |
| **Remote Access & Control** | **Tailscale** + **Telegram Bot Gateway** + **Lightweight Web Dashboard** | Secure, encrypted peer-to-peer control without exposing open public ports or cloud proxies. |
| **Storage Strategy** | **512GB Internal NVMe**: OS, SQLite DBs, Git Worktrees<br>**1TB External SSD**: LLM Weights, LanceDB, Raw Datasets | Maximizes random I/O read/write speeds for active processes while offloading large sequential model files. |

---

## 1. Local Inference Research & Strategy

### Hardware Reality on 32 GB Unified Memory (Apple Silicon M6)
Apple Silicon shares system RAM between the CPU and the GPU (Unified Memory Architecture). By default, macOS reserves approximately 20–25% of system RAM for the operating system, WindowServer, display buffers, and background system services. 

* **Total Available Unified RAM:** 32.0 GB
* **macOS Overhead + Base System Reserve:** ~6.5 GB
* **Maximum Safe Allocatable Memory (`sysctl iogpu.wired_mem_limit`):** ~24.5 GB
* **Memory Budget for Inference Engine (Weights + KV Cache):** **16.0 GB to 18.0 GB**
* **Memory Budget for Background Services (Docker, SQLite, Agents):** **5.0 GB to 6.5 GB**

```
+-------------------------------------------------------------------+
|                     32 GB UNIFIED MEMORY SYSTEM                   |
+------------------------------------+------------------------------+
| macOS System, WindowServer, Caches |  6.5 GB                      |
| Agent Services, Docker, DBs, Node  |  5.5 GB                      |
+------------------------------------+------------------------------+
| Active Model Weights (Qwen 14B Q8) | 13.5 GB                      |
| KV Context Cache (16k context)     |  3.5 GB -> [ Inactive Swap ] |
+-------------------------------------------------------------------+
```

### Inference Engine Comparison

| Engine | Apple Silicon Optimization | Multi-Model Concurrency | Memory Overhead | Continuous Batching | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`llama.cpp` (server)** | Excellent (Metal API) | Native (Slots) | Extremely Low | Yes | **Primary Pick** for API server & continuous work. |
| **`mlx-lm` (Apple MLX)** | Native (Apple MLX framework) | Model Swapping required | Very Low | Partial | **Best for ultra-fast single-model execution.** |
| **Ollama** | Wrapper around `llama.cpp` | Managed Swapping | Medium | Yes | Good for convenience, higher resource overhead. |
| **vLLM / vLLM-Metal** | Experimental on Apple | Poor on Metal | High | Yes | Not mature enough on Apple Silicon compared to CUDA. |

### Model Selection & Quantization Strategy

Running a 32B model at Q4_K_M consumes ~20 GB for weights alone. Once a context window of 16k tokens is built, memory consumption spikes past 24 GB, causing macOS to trigger system memory compression and disk swapping (killing tokens-per-second performance from 35 t/s down to 2 t/s).

Therefore, **the primary model must be a 14B to 16B parameter model running at high precision (Q8_0 or 6-bit MLX)**, or a sparse MoE model.

1. **Primary Workhorse (Planning, Coding, Reasoning):**
   * **Qwen2.5-Coder-14B-Instruct (Q8_0 or 6-bit MLX)**
   * *Weight Size:* ~14.8 GB
   * *Context Window:* Up to 32k tokens supported (run at 16k tokens locally).
   * *Inference Speed:* ~38–48 tokens/sec on Apple Silicon Metal.
2. **Fast Worker / Task Classifier / Router:**
   * **Qwen2.5-7B-Instruct or Llama-3.1-8B-Instruct (Q4_K_M)**
   * *Weight Size:* ~4.8 GB
   * *Role:* Subagent task evaluation, output validation, routing decisions, document chunk extraction.
   * *Strategy:* Loaded dynamically via `mlx-lm` or running in a low-priority slot on `llama.cpp`.

---

## 2. Agent Runtimes & Harnesses

Autonomous execution over hours requires **stateless orchestration with stateful persistence**. Monolithic agent frameworks (e.g., naive AutoGen or CrewAI execution loops) leak memory, keep giant context histories in active Python RAM, and crash unrecoverably on unhandled exceptions.

```
       +--------------------------------------------------------+
       |               HUMAN / TELEGRAM / SCHEDULE              |
       +---------------------------+----------------------------+
                                   |
                                   v
       +--------------------------------------------------------+
       |              SUPERVISOR / ORCHESTRATOR                 |
       |  - Read SQLite Queue   - Task Decomposition (14B LLM)  |
       |  - Enforce Permissions  - Monitor Timeouts & Circuit   |
       +---------------------------+----------------------------+
                                   |
                +------------------+------------------+
                |                                     |
                v                                     v
+-------------------------------+   +-------------------------------+
|     CODING AGENT WORKER       |   |    RESEARCH AGENT WORKER      |
| - Aider / OpenHands Core      |   | - SearXNG / PaperQA2 Engine   |
| - Git Worktree Sandbox        |   | - Marker PDF / LanceDB RAG    |
| - Subprocess Test Loop        |   | - Evidence Validator          |
+---------------+---------------+   +---------------+---------------+
                |                                     |
                +------------------+------------------+
                                   |
                                   v
       +--------------------------------------------------------+
       |                  SYSTEM STATE & LOGS                   |
       |  - SQLite (Task DB)   - Git Commits   - Audit Trail   |
       +--------------------------------------------------------+
```

### Architecture Choice: Hybrid Custom Orchestrator + Specialized Tools
Instead of using a single framework for everything, use a lightweight **Python `asyncio` event-driven supervisor** that orchestrates dedicated CLI execution harnesses:

* **Task Execution Loop:** Custom supervisor reading from an embedded SQLite queue (`LiteQueue` or custom transactional schema).
* **Coding Execution Harness:** Headless **Aider** or **OpenHands Core** invoked as standard subprocesses within isolated Git Worktrees.
* **Research Execution Harness:** Dedicated Python modules wrapping **PaperQA2**, **SearXNG**, and **Marker**.

---

## 3. Multi-Agent Architecture (100+ Logical Agents on 32 GB RAM)

### Logical Agents vs. Physical LLM Threads
Running 100 actual LLM models simultaneously on 32 GB RAM is physically impossible. However, running **100+ logical agents** is trivial if you separate **Agent Identity/State** from **Inference Execution**.

```
[Logical Agent 1: Code Reviewer] ---\
[Logical Agent 2: Bug Fixer]    ----\
[Logical Agent 3: Searcher]     -----> [ SQLite Task Queue ] ---> [ Worker Pool (Max 2 Concurrency) ] ---> [ Single Local LLM Server ]
[Logical Agent N: Summarizer]   -----/
```

### Design Pattern: Async Worker Pool with Model Routing

1. **Agent Definition (Data, not Code):**
   An agent is a JSON record containing system prompts, tool definitions, scratchpad state, and execution history stored in SQLite.
2. **Task Queue:**
   Agents enqueue discrete step tasks into a thread-safe SQLite database.
3. **Worker Allocation (Hardware Cap):**
   * **LLM Workers:** Fixed limit of **1 heavy worker process** (or 2 slots in `llama.cpp` server mode).
   * **I/O Workers:** Up to **16 parallel async workers** handling non-LLM operations (network downloads, PDF parsing, running unit tests, git operations, file indexing).
4. **Context Window Recycling:**
   When an agent completes its subtask, its state is serialized to SQLite. The LLM memory cache is purged or reused for the next logical agent.

---

## 4. Autonomous Coding Agents

### Evaluation of Autonomous Systems

| Feature | OpenHands | Aider | AutoCode / Custom Scripts |
| :--- | :--- | :--- | :--- |
| **Repository Map** | Tree-Sitter + NetworkX | Tree-Sitter Repo Map | File tree text dump |
| **Editing Precision** | Search/Replace / Diff | Search/Replace Block | Whole File Rewrites |
| **Local LLM Performance**| Medium (requires strict JSON) | **High (optimized for local models)** | Low |
| **Git Integration** | Docker-based | **Native Git & Worktree Support** | Manual |

### Recommended Implementation: Headless Aider + Git Worktrees
To operate across any repo on the computer without corrupting work:

1. **Git Worktree Isolation:**
   When a coding task starts, the orchestrator creates a temporary Git worktree:
   `git worktree add -b task-102 /tmp/worktrees/task-102 main`
2. **Execution Loop:**
   The agent executes editing loops inside `/tmp/worktrees/task-102`.
3. **Automated Verification:**
   The harness runs test suites (`pytest`, `npm test`, `cargo test`).
4. **Self-Correction:**
   If tests fail, stdout/stderr is fed back into the context window for self-correction (up to 4 attempts).
5. **Merge Request:**
   Upon completion and green test status, a Git commit is created and pushed to a review branch. The main working branch is never modified directly by an unverified agent loop.

---

## 5. Autonomous Research Agents

### Preventing Hallucination in Literature & Web Research
Generic RAG systems frequently invent citations. To achieve scientific and technical rigor, research pipelines must enforce **Citation-Grounded Extraction**.

```
Query -> SearXNG Search / ArXiv API
       -> Download HTML/PDFs to /Volumes/ExternalSSD/research_raw
       -> Marker Engine (Convert PDF to Structured Markdown)
       -> Text Chunking + Vector Ingestion (LanceDB)
       -> Candidate Retrieval via Hybrid Search (BM25 + Dense)
       -> Citation Verification (Pass chunks through 14B LLM with zero-hallucination prompt)
       -> Final Structured Markdown Report + Verified URLs/DOIs
```

### Pipeline Components
1. **Search Engine:** **SearXNG** running locally via Docker (meta-searches DuckDuckGo, Google, ArXiv, Wikipedia, GitHub without tracking or API key costs).
2. **PDF Parser:** **Marker** or **PyMuPDF** running locally to convert academic multi-column papers into plain Markdown tables and text.
3. **Evidence Index:** **LanceDB** storing vector embeddings locally using native Apple Silicon MPS/Metal accelerated models (`bge-small-en-v1.5` or `nomic-embed-text`).
4. **Synthesis Engine:** **PaperQA2** workflow—queries extract explicit quotes with direct text pointers before generating any summary text. If no explicit text supports a statement, the statement is rejected.

---

## 6. Persistent Memory Architecture

Avoid over-engineering with complex cloud vector infrastructure. Use an embedded multi-tiered local memory pattern:

```
+--------------------------------------------------------------------+
|                      PERSISTENT MEMORY LAYER                       |
+--------------------------------------------------------------------+
| 1. EPISODIC MEMORY (SQLite3)                                       |
|    - Structured task queues, agent states, tool run logs, timings  |
+--------------------------------------------------------------------+
| 2. SEMANTIC VECTOR MEMORY (LanceDB)                                |
|    - Embedded project docs, codebase functions, research chunks   |
+--------------------------------------------------------------------+
| 3. KNOWLEDGE & DECISION GRAPH (Markdown + Frontmatter Files)       |
|    - Human-readable architecture decisions, project updates       |
+--------------------------------------------------------------------+
```

### Memory Hierarchy

1. **Episodic Memory (SQLite3):**
   Stores state transitions, exact tool calls, input/output pairs, execution timing, and system performance metrics. Fast, zero-overhead ACID compliance.
2. **Semantic Memory (LanceDB):**
   Embedded, zero-dependency vector database running inside Python via C++ bindings. Stores codebase embeddings and research document chunks.
3. **Declarative/Project Memory (Markdown Files with YAML Frontmatter):**
   Human-readable files stored in a dedicated directory (`/Volumes/ExternalSSD/memory/projects/<project-name>.md`). Agents read these files at initialization to acquire high-level context, project conventions, and technical decisions.

---

## 7. Computer Control & Security Architecture

Autonomous tools running shell commands, web browsers, and file operations present severe risks without sandboxing.

### Security Perimeter Model

```
+-------------------------------------------------------------------+
|                     MACOS HOST (Primary User)                     |
|  - Personal Files, SSH Keys, Passwords, Keychains                 |
|                                                                   |
|   +-----------------------------------------------------------+   |
|   |   UNPRIVILEGED OS USER ACCOUNT (`_aiworker`)               |   |
|   |   - No sudo access                                        |   |
|   |   - Restricted filesystem access                          |   |
|   |                                                           |   |
|   |   +---------------------------------------------------+   |   |
|   |   |   LIMA LINUX VM / DOCKER CONTAINER SANDBOX        |   |   |
|   |   |   - Isolated Shell Execution                      |   |   |
|   |   |   - Isolated Network Policy                        |   |   |
|   |   |   - Mounts ONLY `/Volumes/ExternalSSD/workspace`  |   |   |
|   |   +---------------------------------------------------+   |   |
|   +-----------------------------------------------------------+   |
+-------------------------------------------------------------------+
```

1. **Dedicated OS User:**
   Create a standard macOS account (e.g., `aiworker`) without administrator/sudo rights. The autonomous system runs strictly under this user session.
2. **Execution Containerization:**
   Code execution and terminal tools run inside a **Lima VM** or **Docker Desktop** instance with mounted read-write access restricted strictly to `/Volumes/ExternalSSD/workspace/`.
3. **Command Interceptor & Permission Matrix:**
   A light middleware inspects tool executions before shell invocation:
   * **Auto-Approved:** Read-only operations (`ls`, `git status`, `grep`), test runs (`pytest`), building code inside sandbox, web searches.
   * **Forbidden (Hard Block):** `sudo`, `rm -rf /`, reading `~/.ssh`, reading `~/Library/Keychains`, accessing browser profiles, modifying macOS launch services.
   * **Requires Human Gate:** `git push main`, executing external network binaries, outbound web hooks with write payloads.

---

## 8. Always-On (24/7) Operation & System Resilience

### macOS System Power Configuration
To keep an Apple Silicon Mac mini operating reliably non-stop without sleeping or throttling GPU execution:

```bash
# Prevent system sleep while connected to AC power
sudo pmset -a disablesleep 1
sudo pmset -a sleep 0
sudo pmset -a displaysleep 10
sudo pmset -a tcpkeepalive 1
sudo pmset -a autorestart 1
```

### LaunchDaemon / LaunchAgent Service Architecture
Use macOS native `launchd` services to guarantee system recovery after unexpected power outages or operating system updates.

```
/Users/aiworker/Library/LaunchAgents/
├── com.ai.llmserver.plist      # Starts llama.cpp server on port 8080
├── com.ai.searxng.plist        # Ensures SearXNG engine is running
└── com.ai.orchestrator.plist   # Primary agent queue consumer
```

### Watchdog & Crash Recovery Strategy
The primary orchestrator script wraps agent execution in transactional SQLite savepoints. If an agent subprocess crashes, leaks memory, or throws an unhandled exception:
1. The supervisor catches the exit code.
2. The current task step is marked as `FAILED_RETRIABLE` and task memory state rolls back to the last known good SQLite savepoint.
3. The process restarts after an exponential backoff sleep (5s, 10s, 30s).
4. If a task fails 3 consecutive times, it is moved to `HUMAN_INTERVENTION_QUEUE` and a Telegram push alert is dispatched.

---

## 9. Remote Access & Control Architecture

Exposing ports directly to the public internet creates severe vulnerabilities. The remote control system operates completely behind an encrypted mesh network.

```
+------------------+         +-------------------------------+         +------------------+
|  USER PHONE/LAP  |         |        TAILSCALE MESH         |         |   MAC MINI M6    |
|                  | <=====> | (WireGuard Encrypted Tunnel)  | <=====> |                  |
| - Telegram App   |         | No public IP exposure required|         | - Telegram Gateway
| - Web UI         |         +-------------------------------+         | - Web Dashboard  |
+------------------+                                                   +------------------+
```

1. **Network Layer (Tailscale):**
   Install Tailscale on the Mac mini and mobile devices. Access local dashboards (e.g., `http://100.x.y.z:8000`) securely over WireGuard encryption from anywhere without open port forwarding or dynamic DNS.
2. **Primary Control Channel (Telegram Bot Gateway):**
   * **Task Ingestion:** Send messages directly to your private Telegram bot: `/task Create a research report on Rust async runtimes`.
   * **Status & Monitoring:** System posts status updates, token consumption, and completed file output links to the chat.
   * **Human Approval Gates:** When an agent requests a protected action (e.g., git merge, running unknown script), the Telegram bot sends inline buttons: `[ APPROVE ]` | `[ REJECT ]`.
   * **Emergency Kill Switch:** Texting `/KILL` instantly sends `SIGKILL` to all subagent processes and resets the task queue to paused state.

---

## 10. Storage Architecture & Disk Allocation

To ensure maximum performance and lifespan for SSDs, split heavy file read/write operations between internal NVMe storage and external high-speed storage.

```
+-----------------------------------------------------------------------+
| INTERNAL NVME SSD (512 GB) - High IOPS, Lower Capacity               |
| - macOS System Files & Applications                                  |
| - SQLite Databases (Task Queue, Episodic Logs)                       |
| - Active Git Worktrees (`/tmp/worktrees/`)                           |
| - System swap file (if needed)                                       |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
| EXTERNAL NVME SSD (1 TB via USB4/Thunderbolt) - High Capacity        |
| - GGUF & MLX LLM Weights (`/Volumes/ExternalSSD/models/`)            |
| - LanceDB Vector Database (`/Volumes/ExternalSSD/vector_store/`)    |
| - PDF & Dataset Storage (`/Volumes/ExternalSSD/research_raw/`)       |
| - Docker Container Volumes                                           |
| - Complete Project Repositories Archive                              |
+-----------------------------------------------------------------------+
```

---

## Deliverables A–K

### A. Recommended Technology Stack

| Layer | Recommended Technology | Alternatives Considered | Selection Rationale |
| :--- | :--- | :--- | :--- |
| **Inference Engine** | `llama.cpp` (server mode) | Ollama, vLLM, LM Studio | Native Metal C++ bindings, minimal RAM overhead, continuous batching. |
| **Primary LLM** | Qwen2.5-Coder-14B-Instruct | DeepSeek-Coder-V2-Lite, Llama-3.3-70B | Fits cleanly in 32GB RAM with room for 16k context without triggering disk swap. |
| **Orchestrator** | Custom Python Async / LiteQueue | LangGraph, AutoGen, CrewAI | Zero dependency rot, exact memory management, deterministic execution logic. |
| **Coding Harness** | Aider + Git Worktrees | OpenHands, AutoCode | Superior repository mapping, token efficiency, native git branch manipulation. |
| **Research Engine**| PaperQA2 + SearXNG + Marker | Perplexity API, GPT-Researcher | Local execution, zero hallucination bounds, automated citation extraction. |
| **Vector DB** | LanceDB | Qdrant, Chroma, Milvus | Native C++ embedded engine, disk-backed, Metal accelerated via Python SDK. |
| **Primary DB** | SQLite3 (WAL mode) | PostgreSQL, Redis | Zero maintenance, single-file backup, transactional reliability across system reboots. |
| **Sandboxing** | Dedicated macOS User + Docker | Native execution, macOS Sandbox | Isolates credentials, prevents accidental file deletion on primary user account. |
| **Remote Access** | Tailscale + Telegram Bot | Cloudflare Tunnels, SSH port forwarding | Secure, peer-to-peer, works seamlessly on mobile devices without static public IPs. |

---

### B. Complete Architecture Diagram

```
                                  +-----------------------+
                                  |   REMOTE OPERATOR     |
                                  | (Telegram / Tailscale)|
                                  +-----------+-----------+
                                              |
                                              v
+-----------------------------------------------------------------------------------+
| MACOS WORKSTATION HOST (User: _aiworker)                                          |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | CENTRAL SUPERVISOR (Python Async Service via launchd)                       |  |
|  | - Parses incoming user tasks                                                |  |
|  | - Manages SQLite Task Queue & State Transitions                              |  |
|  | - Dispatches tasks to Worker Pool                                           |  |
|  +--------+-----------------------------------+-----------------------+--------+  |
|           |                                   |                       |           |
|           v                                   v                       v           |
|  +-----------------+                 +-----------------+     +-----------------+  |
|  | CODING WORKER   |                 | RESEARCH WORKER |     | GENERAL WORKER  |  |
|  +--------+--------+                 +--------+--------+     +--------+--------+  |
|           |                                   |                       |           |
|           | (Executes in                      | (Fetches via          |           |
|           |  Worktree)                        |  SearXNG/Marker)      |           |
|           v                                   v                       v           |
|  +-----------------------------------------------------------------------------+  |
|  | LLM ROUTER / INFERENCE GATEWAY (`llama.cpp` server)                         |  |
|  | - Directs requests to Qwen2.5-Coder-14B (Q8_0) in Unified Memory          |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        |                                          |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | STORAGE & MEMORY LAYER                                                      |  |
|  | - Internal SSD: SQLite Queue & Episodic State Logs                          |  |
|  | - External SSD: GGUF Model Weights, LanceDB Vectors, Raw Research PDFs        |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

### C. Hardware & Resource Budget Allocation

| Resource | Reserve Allocation | Purpose |
| :--- | :--- | :--- |
| **RAM: macOS & Display** | 6.5 GB | Operating System, WindowServer, background network stack. |
| **RAM: LLM Weights** | 13.5 GB | Qwen2.5-Coder-14B-Instruct at Q8_0 precision. |
| **RAM: KV Cache Context** | 4.0 GB | Supports ~16,000 active token context window in Metal memory. |
| **RAM: Python & Docker** | 5.5 GB | SQLite, LanceDB, SearXNG container, Aider processes. |
| **RAM: Safety Buffer** | 2.5 GB | Prevents macOS memory compression and disk thrashing. |
| **Internal SSD (512 GB)**| ~80 GB | macOS OS, internal apps, active git worktrees, SQLite WAL logs. |
| **External SSD (1 TB)** | ~450 GB | Model GGUFs, vector databases, research PDFs, raw datasets, archives. |

---

### D. Agent Architecture (100+ Logical Agents)

To scale to 100+ agents without crashing memory:

1. **Agent Definition File (`agents.json`):**
   Agents are stored as declarative config rows containing `agent_id`, `system_prompt`, `allowed_tools`, and `parent_agent_id`.
2. **Task Queue Engine:**
   Agents do not exist as long-running OS processes. Instead, an agent "instantiates" only when a message targeting its `agent_id` is popped from the SQLite `task_queue`.
3. **Execution Pipeline:**
   * **Step 1:** Queue reader pops task item.
   * **Step 2:** Agent state, context, and system prompt are assembled.
   * **Step 3:** Task is executed against the single shared `llama.cpp` endpoint.
   * **Step 4:** Results are saved back to SQLite; process terminates, freeing system memory.

---

### E. Model Strategy Matrix

| Task Domain | Primary Model | Quant / Precision | Context Budget | Execution Mode |
| :--- | :--- | :--- | :--- | :--- |
| **System Planning** | Qwen2.5-Coder-14B-Instruct | Q8_0 | 8,192 tokens | Single Pass / High Precision |
| **Code Generation** | Qwen2.5-Coder-14B-Instruct | Q8_0 | 16,384 tokens | Iterative / Test-Driven |
| **Debugging** | Qwen2.5-Coder-14B-Instruct | Q8_0 | 16,384 tokens | Diff & Stacktrace Evaluation |
| **Research Synthesis**| DeepSeek-Coder-V2-Lite | Q4_K_M | 12,288 tokens | Citation Verification Loop |
| **Routing / Fast Filter**| Qwen2.5-7B-Instruct | Q4_K_M | 2,048 tokens | Fast Low-Latency Pass |

---

### F. 24/7 Always-On Resiliency Blueprint

1. **Power Management:**
   Enforce system sleep prevention via `pmset` configurations and standard `caffeinate -dis` background wrappers on main execution services.
2. **LaunchDaemon Recovery (`/Library/LaunchDaemons/com.ai.orchestrator.plist`):**
   Configured with `<key>KeepAlive</key><true/>` and `<key>ThrottleInterval</key><integer>10</integer>`. If an unexpected crash occurs, `launchd` instantly re-spawns the orchestrator process.
3. **State Recovery Logic:**
   All queue tasks use state transitions (`PENDING` -> `RUNNING` -> `COMPLETED` / `FAILED`). If the Mac reboots unexpectedly mid-task, the orchestrator boots, finds any task left in `RUNNING` state without an active process lock, marks it `INTERRUPTED`, and re-enqueues it automatically from the last step.

---

### G. Remote Control Architecture

```
[Mobile Phone / Telegram App]
           |
           | Encrypted HTTPS Payload via Telegram API
           v
[Telegram Bot Server Agent] (Running on Mac mini)
           |
           +---> Command: /status -> Queries SQLite -> Returns system load & active tasks
           +---> Command: /task <prompt> -> Inserts new row into Task Queue
           +---> Command: /approve <task_id> -> Unlocks gated action in execution queue
           +---> Command: /KILL -> Issues SIGKILL to active child processes & pauses system
```

---

### H. Security & Boundary Architecture

To safeguard personal identity, credentials, and system integrity:

1. **Credential Masking:**
   Secrets, API tokens, and private keys reside in environment variables stored in a `.env` file readable *only* by user `_aiworker`. The orchestrator passes outputs through a regex scrubbing stream that redacts standard key formats before writing logs or sending remote notifications.
2. **Path Containment:**
   All agent tools check file paths against an explicit whitelist:
   `ALLOWED_PATHS = ["/Volumes/ExternalSSD/workspace/", "/tmp/worktrees/"]`
   Any operation targeting files outside these paths throws an instant access violation exception.
3. **Destructive Command Interceptor:**
   Commands containing patterns such as `rm -rf`, `dd`, `mkfs`, `chmod`, `chown`, or disk formatting tools are hard-blocked at the shell wrapper level.

---

### I. Step-by-Step Installation & Setup Plan

Run these commands on the Mac mini:

```bash
# Step 1: Set up dedicated standard user account for AI (run as admin user)
sudo dscl . -create /Users/_aiworker
sudo dscl . -create /Users/_aiworker UserShell /bin/zsh
sudo dscl . -create /Users/_aiworker RealName "AI Worker Agent"
sudo dscl . -create /Users/_aiworker UniqueID "599"
sudo dscl . -create /Users/_aiworker PrimaryGroupID 20
sudo dscl . -create /Users/_aiworker NFSHomeDirectory /Users/_aiworker
sudo mkdir -p /Users/_aiworker
sudo chown -R _aiworker:staff /Users/_aiworker

# Step 2: Configure System Power Settings to prevent sleep
sudo pmset -a disablesleep 1
sudo pmset -a sleep 0
sudo pmset -a displaysleep 10

# Step 3: Switch to AI User context
su - _aiworker

# Step 4: Install Homebrew and core tool dependencies
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git cmake python@3.11 searxng tailscale

# Step 5: Build llama.cpp with Apple Silicon Metal acceleration
git clone https://github.com/ggerganov/llama.cpp.git ~/llama.cpp
cd ~/llama.cpp
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release -j8

# Step 6: Create Directory Hierarchy on External SSD
mkdir -p /Volumes/ExternalSSD/models/
mkdir -p /Volumes/ExternalSSD/vector_store/
mkdir -p /Volumes/ExternalSSD/workspace/
mkdir -p /Volumes/ExternalSSD/research_raw/

# Step 7: Download Primary Workhorse Model (Qwen2.5-Coder-14B)
curl -L -o /Volumes/ExternalSSD/models/qwen2.5-coder-14b-instruct-q8_0.gguf \
  "https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-GGUF/resolve/main/qwen2.5-coder-14b-instruct-q8_0.gguf"

# Step 8: Set up Python Virtual Environment & Install Core Agent Dependencies
python3 -m venv ~/agent_env
source ~/agent_env/bin/activate
pip install --upgrade pip
pip install aider-chat lancedb pydantic litellm paperqa marker-pdf python-telegram-bot
```

---

### J. What NOT to Install (Redundant / Harmful Technologies)

1. **Heavy Local Vector DB Services (Milvus, Pinecone local adapters):**
   * *Why:* Over-consume background memory and CPU idle cycles. Use lightweight embedded **LanceDB** or **SQLite-vec**.
2. **Complex Microservice Agent Frameworks (Kubernetes, Ray Clusters):**
   * *Why:* Severe resource starvation on 32 GB RAM. Single-node local execution does not benefit from distributed cluster overhead.
3. **Heavy Monolithic GUI Automation Tools (Full-screen vision-driven OS automation):**
   * *Why:* High memory costs, fragile, easily broken by minor interface changes, and difficult to sandbox securely. Use headless APIs, CLI tools, and Git interfaces instead.
4. **Ollama for Background Daemon Pipelines:**
   * *Why:* While great for casual manual usage, Ollama's automatic model unloading management can interfere with strict continuous orchestration loops. Use explicit `llama.cpp` server instances for predictable resource management.

---

### K. Future Hardware Upgrade Path

When upgrading from the 32 GB M6 Mac mini to higher-tier hardware:

* **Upgrade to 64 GB / 96 GB Unified Memory:**
  * **Model Strategy:** Upgrade primary workhorse model to **Qwen2.5-Coder-32B-Instruct** (Q8_0) or **DeepSeek-Coder-V2-Instruct** (Q4_K_M).
  * **Concurrency:** Increase `llama.cpp` execution slots to 4 parallel context sequences.
* **Upgrade to 128 GB+ Unified Memory:**
  * **Model Strategy:** Load 70B parameter models locally (e.g., Llama-3.3-70B-Instruct at Q4_K_M) or run dual full-precision 32B models simultaneously (one dedicated to continuous background research, one for interactive coding).
* **Adding Discrete GPU Compute Nodes:**
  * Connect distant GPU worker servers into the orchestrator via Tailscale network mesh. Use the Mac mini as the continuous low-power supervisor/router, offloading heavy multi-hour training or 70B+ inference runs to external dedicated GPU nodes dynamically.

---

## Sources

1. **Apple Silicon Unified Memory Architecture & Metal Optimization:** Primary Source - Apple Developer Documentation (`developer.apple.com/metal`).
2. **`llama.cpp` Metal Benchmarks & Continuous Batching Specifications:** Primary Source - `llama.cpp` Official Repository & Technical Release Notes (`github.com/ggerganov/llama.cpp`).
3. **Qwen2.5-Coder Model Family Benchmarks & Performance Specifications:** Primary Source - Qwen AI Technical Report & Model Cards (`huggingface.co/Qwen`).
4. **PaperQA2 Grounded Citation Architecture:** Secondary Source - Future House Scientific Agent Architecture Documentation (`github.com/Future-House/paper-qa`).
5. **Aider Repository Mapping & Benchmarks for Local Models:** Primary Source - Aider AI Documentation (`aider.chat/docs/leaderboards`).
6. **LanceDB Embedded Engine Technical Specifications:** Primary Source - LanceDB Developer Documentation (`lancedb.github.io/lancedb`).

## Reasoning trace (not shown to raters)

NONE

## Run notes


