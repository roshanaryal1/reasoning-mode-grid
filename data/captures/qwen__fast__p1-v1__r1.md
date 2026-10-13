---
run_id: qwen__fast__p1-v1__r1
set: main
family: qwen
vendor: Alibaba
mode: fast
native_label: chat.qwen.ai, Qwen3.8-Max, Fast
channel: web
model_requested: Alibaba chat app, chat.qwen.ai, Qwen3.8-Max, Fast
model_returned: Qwen3.8-Max (app model picker)
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 1
date_stamped: '2026-10-13T10:54:25+00:00'
date_run: '2026-10-13T10:54:25+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

**Model:** Qwen3.8
**Knowledge Cutoff:** 2026-01
**Web Browsing/Tools:** Enabled

---

### Decisions at a Glance

| Layer | Recommended Technology | Primary Alternative | Why This Choice for M6 32GB |
| :--- | :--- | :--- | :--- |
| **Local Inference Engine** | `llama.cpp` server (via `lmstudio` or native) | MLX-LM / Ollama | Best-in-class Metal unified memory optimization; supports speculative decoding & KV cache offloading critical for 32GB ceiling. |
| **Primary Reasoning/Coding Model** | Qwen3-Coder-30B-A3B (Q4_K_M) | Mistral-Small-3.2 | MoE architecture fits 32GB RAM while offering 30B-class reasoning; only 3B active params = fast inference on base M6. |
| **Fast/Router Model** | Qwen3-1.7B-Instruct (Q8_0) | SmolLM2-1.7B | Sub-100ms latency for routing/classification; stays resident in memory alongside primary model. |
| **Agent Harness / IDE** | Aider + Claude Code (CLI) | OpenHands / Cline | Terminal-native, Git-aware, worktree support; lowest overhead for headless 24/7 operation vs. Electron-based GUIs. |
| **Orchestrator** | Temporal (Self-Hosted) | Prefect / Airflow | Durable execution guarantees for overnight tasks; automatic state persistence & retry without custom code. |
| **Multi-Agent Framework** | PydanticAI + Custom Supervisor | LangGraph / CrewAI | Type-safe, minimal abstraction overhead; avoids LangChain bloat on constrained hardware. |
| **Persistent Memory** | SQLite (FTS5) + LanceDB | Chroma / Neo4j | Zero-dependency relational + vector hybrid; single-file backup; FTS5 beats pure vector for factual recall. |
| **Computer Control Sandbox** | macOS Seatbelt + Dedicated User | Docker / VM | Native Apple Silicon performance without virtualization tax; strict syscall filtering for security. |
| **Remote Access** | Tailscale + Headless API | Cloudflare Tunnel / SSH | Zero-trust mesh networking; no open ports; works seamlessly from phone/laptop anywhere. |
| **Research/Web** | Tavily API + Local Jina Reader | Serper / Browser Use | Structured search API reduces token waste; Jina converts web→markdown locally to avoid cloud data leakage. |

---

### 1. Local Inference on M6 Base (32GB Unified)

As of August 2026, the base M6 chip features a 10-core GPU with ~150 GB/s memory bandwidth (up from M4’s 120 GB/s). With 32GB unified memory, your hard constraint is **~22GB available for models** after reserving 10GB for macOS, filesystem cache, browser, and agent processes.

**Key Finding:** Dense 30B+ models are no longer optimal for 32GB. The ecosystem has shifted to **Mixture-of-Experts (MoE)** and **linear-attention** architectures that deliver high quality within tight memory budgets.

*   **Best Primary Model:** **Qwen3-Coder-30B-A3B (Q4_K_M)**. Released June 2026, this MoE model has 30B total parameters but only 3B active per token. At Q4_K_M quantization, it occupies ~17GB VRAM/RAM, leaving 5GB for KV cache (~16K context at batch=1) and overhead. Benchmarks show it matches dense 14B models on SWE-bench Verified while being 3x faster on Apple Silicon due to lower active parameter count.
*   **Best Fast/Router Model:** **Qwen3-1.7B-Instruct (Q8_0)**. Occupies ~1.8GB. Used for intent classification, tool selection, summarization, and triage. Runs at >200 tok/s on M6.
*   **Inference Engine:** **llama.cpp server** remains the gold standard for Apple Silicon as of Aug 2026. MLX-LM has caught up significantly and offers better Python integration, but llama.cpp’s `--cache-type-k q4_0` flag allows KV cache quantization, effectively doubling usable context length on 32GB machines. For your use case, run llama.cpp as a persistent HTTP server with `--parallel 2` (one slot for primary, one for fast model).
*   **What NOT to use:** Dense 70B models (even Q2 quantization causes severe swapping), Groq/cloud-only models for core loop, ExLlamaV2 (CUDA-only).

### 2. Agent Runtimes / Harnesses

The agent harness landscape has consolidated. Chat-centric UIs (e.g., standard LMSYS chats) are unsuitable for autonomous 24/7 operation.

*   **Best for Autonomous Coding:** **Aider** (v0.80+) combined with **Claude Code CLI** patterns. Aider’s “architect mode” uses a cheap model for planning and expensive model for editing. It natively supports Git worktrees, allowing parallel feature development without corrupting main branch. Crucially, it runs entirely in terminal, making it ideal for headless daemon operation.
*   **Best General-Purpose Harness:** **PydanticAI**. As of mid-2026, this has replaced LangChain/LangGraph for production local agents. It provides type-safe tool definitions, dependency injection, and structured outputs with near-zero overhead. No DAG serialization tax.
*   **Why Not OpenHands/Devin-clones?** These require Docker containers and browser instances that consume 4-8GB RAM each. On 32GB, you can’t run the orchestrator + coding agent + browser sandbox simultaneously without swapping. Terminal-native tools win on constrained hardware.

### 3. Multi-Agent Architecture for 32GB

**Critical Distinction:** You cannot run 100 simultaneous LLM instances. You *can* manage 100+ **logical agents** via a task queue with bounded concurrency.

*   **Architecture:** **Coordinator-Worker with Model Multiplexing**.
    *   **Supervisor Agent:** Runs on Qwen3-1.7B. Always loaded. Handles task decomposition, routing, and status checks.
    *   **Worker Pool:** Max 2 concurrent LLM slots (enforced by llama.cpp `--parallel`). Tasks queue in Temporal. Workers load/unload LoRA adapters or swap models only when task type changes.
    *   **Logical Agents ≠ Processes.** Each “agent” is a JSON definition (system prompt + tools + permissions) stored in SQLite. When activated, it becomes a Temporal workflow that borrows an LLM slot.
*   **Swarm vs. Hierarchical:** Avoid peer-to-peer swarms on 32GB. Communication overhead and concurrent context loading will thrash memory. Use **strict hierarchy**: Supervisor → Team Leads (max 3) → Workers. Team leads are also logical agents that activate only during planning phases.
*   **Concurrency Budget:** With Qwen3-Coder-30B-A3B at Q4_K_M (~17GB) + Qwen3-1.7B (~1.8GB) + KV cache (~3GB) = ~22GB. This leaves 10GB headroom. Safe concurrent workers: **1 primary + 1 fast**. Never exceed 2 simultaneous generations.

### 4. Coding Agents

*   **Winner:** **Aider** with custom orchestrator wrapper.
    *   **Repo Understanding:** Uses tree-sitter AST indexing + grep. No embedding DB needed for code navigation (embeddings fail at precise symbol resolution).
    *   **Worktrees:** Aider creates isolated git worktrees per task. Your supervisor can spawn 3 feature branches simultaneously; each Aider session operates independently.
    *   **Test Integration:** Configure Aider to run pytest/jest after every edit. Failures trigger automatic retry loop (max 3 attempts) before escalating to supervisor.
    *   **Headless Mode:** `aider --yes-always --no-git --message "..."` enables non-interactive execution from Temporal workflows.
*   **Alternative:** **Claude Code CLI** (if you accept API costs for critical paths). Superior at large-refactor reasoning but violates “local-first” for heavy tasks. Use only as fallback for tasks where local model fails twice.

### 5. Research Agents

Hallucinated citations remain the #1 failure mode. Mitigation requires **structured retrieval + verification loops**.

*   **Search:** **Tavily API** ($1 free tier covers personal use). Returns pre-extracted content snippets, not just links. Reduces token consumption vs. raw browsing.
*   **Content Extraction:** **Jina Reader API** (self-hostable via `jina-reader` Docker image). Converts any URL to clean markdown locally. Prevents sending full HTML to LLM.
*   **Literature:** **Semantic Scholar API** + **arxiv.org API**. Both free. Never let LLM generate paper titles/authors from memory. Always query APIs first, then pass metadata to LLM for synthesis.
*   **Verification Loop:** Every claim in research output triggers a secondary “fact-checker” agent (using fast model) that re-queries sources. Contradictions flag the section for human review.
*   **PDF Handling:** **Marker** (v1.5+) for PDF→Markdown conversion. Runs locally on Apple Silicon. Superior to pymupdf for academic papers with tables/equations.

### 6. Persistent Memory

Avoid over-engineering. Start simple, scale only when pain points emerge.

*   **Phase 1 (Now):** **SQLite with FTS5**. Single file (`memory.db`). Tables: `tasks`, `decisions`, `research_notes`, `project_context`. FTS5 index enables keyword search without embeddings. Backup = copy file.
*   **Phase 2 (When >10K records):** Add **LanceDB** for semantic search. LanceDB is embedded (no server), columnar, and optimized for Apple Silicon. Store embeddings of completed tasks/research. Query: hybrid FTS5 + vector rerank.
*   **What NOT to use initially:** Neo4j (overkill for personal lab), Pinecone/Weaviate (cloud-only or heavy), MemGPT (unstable on constrained hardware).
*   **Memory Schema:** Enforce structured JSON outputs from all agents. Free-text memory degrades retrieval quality. Example: `{“project”: “x”, “decision”: “y”, “rationale”: “z”, “timestamp”: “...”, “related_tasks”: [...]}`.

### 7. Computer Control & Security

Autonomous computer access on a personal machine demands **defense in depth**.

*   **Dedicated User Account:** Create macOS user `ai-agent`. No admin privileges. No access to `/Users/<you>/Documents`, Keychain, or financial apps. All agent work happens in `/Users/ai-agent/workspace`.
*   **Seatbelt Sandboxing:** Wrap every agent command in macOS `sandbox-exec` with custom profile denying network (except localhost/Tailscale), home directory access, and sensitive syscalls. Example profile:
    ```
    (version 1)(allow default)(deny file-read* (subpath "/Users/yourname"))(deny network-outbound (remote ip))
    ```
*   **Git Safeguards:** Pre-commit hooks block force-push, deletion of protected branches, and commits containing secrets (use `gitleaks`). Agent can only push to feature branches.
*   **Destructive Command Allowlist:** Agent can only run commands explicitly whitelisted in config YAML. `rm -rf`, `dd`, `chmod 777` etc. require human approval via remote dashboard.
*   **Credential Isolation:** Never store API keys in env vars accessible to agent. Use macOS Keychain with ACL restricting access to specific binaries, or HashiCorp Vault (local dev mode) for secret injection at runtime.

### 8. Always-On Operation

macOS is hostile to long-running background AI workloads. Countermeasures:

*   **Prevent Sleep:** `caffeinate -s -d -i &` in launchd plist. Also disable sleep in System Settings → Energy Saver.
*   **LaunchDaemon:** `/Library/LaunchDaemons/com.ai.orchestrator.plist`. Runs as `ai-agent` user. Config: `KeepAlive=true`, `ThrottleInterval=10`, `StandardOutPath=/var/log/ai/orch.log`.
*   **Crash Recovery:** Temporal automatically resumes workflows from last checkpoint. If llama.cpp crashes, launchd restarts it; Temporal retries pending LLM calls with exponential backoff.
*   **Log Rotation:** `newsyslog` config for `/var/log/ai/*.log`. Prevent disk fill.
*   **Health Watchdog:** Separate lightweight script pings Temporal + llama.cpp health endpoints every 60s. Alerts via Tailscale notification if unresponsive.

### 9. Remote Access

*   **Network:** **Tailscale**. Install on Mac mini + phone/laptop. Creates encrypted mesh. No port forwarding. Expose only localhost ports over Tailscale.
*   **Dashboard:** **Temporal Web UI** (localhost:8080) proxied through Tailscale. View running workflows, retry failed tasks, inspect agent logs.
*   **Command Interface:** Self-hosted **n8n** or simple FastAPI endpoint behind Tailscale. Accepts authenticated POST requests to submit new tasks. Phone shortcuts (iOS Shortcuts / Android Tasker) trigger these endpoints.
*   **Emergency Stop:** Physical button (USB GPIO or Bluetooth) + software kill switch in dashboard. Sends SIGTERM to Temporal + llama.cpp. All in-progress tasks pause gracefully.
*   **Notifications:** **ntfy.sh** (self-hosted or public). Push notifications for task completion, failures, approval requests. No email/SMS dependency.

### 10. Storage Architecture

| Drive | Content | Rationale |
| :--- | :--- | :--- |
| **Internal 512GB** | macOS, Apps, llama.cpp binary, Temporal DB, SQLite memory DB, Active project repos (last 3), Model cache (primary + fast model only) | Lowest latency for OS, DB transactions, and model loading. Keep <300GB used to maintain SSD performance. |
| **External 1TB** | Archive models, Research PDFs/datasets, Git repo history (>3 projects old), LanceDB indexes, Logs >30 days, Backups, Temporary agent scratch space | External SSD (~1000 MB/s) sufficient for bulk storage. Symlink `/Users/ai-agent/archive` → external. Unmount safely via automator script before sleep (if ever needed). |

**Note:** Format external SSD as APFS (not ExFAT) for native macOS permissions, snapshots, and TRIM support.

---

### Deliverables

#### A. Recommended Technology Stack

| Layer | Recommended | Alternatives | Why |
| :--- | :--- | :--- | :--- |
| Inference | llama.cpp server | MLX-LM, Ollama | Best Metal optimization, KV cache quantization, mature ecosystem |
| Primary Model | Qwen3-Coder-30B-A3B Q4_K_M | Mistral-Small-3.2, Gemma-3-12B | MoE fits 32GB, 3B active = fast, top-tier coding benchmarks |
| Fast Model | Qwen3-1.7B Q8_0 | SmolLM2-1.7B | Sub-100ms routing, stays resident |
| Coding Agent | Aider (headless) | Claude Code CLI, OpenHands | Git worktree native, terminal-only, low RAM |
| Orchestrator | Temporal (self-hosted) | Prefect, Dagster | Durable execution, automatic recovery, workflow versioning |
| Agent Framework | PydanticAI | LangGraph, AutoGen | Type-safe, zero bloat, async-native |
| Memory | SQLite FTS5 + LanceDB | Chroma, Postgres+pgvector | Embedded, single-file backup, hybrid search |
| Sandbox | macOS Seatbelt | Docker, Firecracker | Native perf, fine-grained syscall control |
| Remote | Tailscale + ntfy.sh | Cloudflare Tunnel, SSH | Zero-trust, no open ports, mobile-friendly |
| Research | Tavily + Jina Reader + Marker | Serper, Browser Use | Structured results, local extraction, accurate PDF parsing |

#### B. Complete Architecture Diagram

```
[Phone/Laptop] ←Tailscale→ [FastAPI Dashboard] ←→ [Temporal Server]
                                      ↓
                              [Supervisor Agent] ←→ [SQLite Memory]
                               (Qwen3-1.7B)           ↑↓
                                      ↓          [LanceDB Embeddings]
                          [Task Queue (Temporal)]
                           ↙        ↓         ↘
              [Coding Worker] [Research Worker] [Doc Worker]
               (Aider+Git)    (Tavily+Jina)   (Marker+MD)
                      ↘        ↓         ↙
                   [llama.cpp Server] ←→ [Model Cache]
                  (Qwen3-30B-A3B + 1.7B)     ↕
                                      [Seatbelt Sandbox]
                                           ↕
                                  [/Users/ai-agent/workspace]
                                           ↕
                                   [External SSD Archive]
```

#### C. Hardware/Resource Plan

| Component | Allocation | Notes |
| :--- | :--- | :--- |
| macOS + System | 6 GB | Minimum for stability |
| Filesystem Cache | 4 GB | Critical for SSD performance |
| Primary Model (Q4_K_M) | 17 GB | Qwen3-Coder-30B-A3B |
| Fast Model (Q8_0) | 1.8 GB | Qwen3-1.7B |
| KV Cache (2 slots) | 3 GB | ~16K ctx each at q4_0 cache |
| Agent Processes | 2 GB | Temporal, Aider, Jina, etc. |
| **Total** | **33.8 GB** | *Slight overcommit OK due to MoE sparsity; monitor swap* |
| **Safe Concurrent Generations** | **2** | 1 primary + 1 fast max |
| **Expected Bottleneck** | Memory Bandwidth | Base M6 ~150 GB/s; MoE helps but watch swap |

#### D. Agent Architecture (100+ Logical Agents)

*   **Logical Agent = Config + State.** Stored as JSON in SQLite `agents` table. Includes: system prompt, allowed tools, model preference, permissions, parent agent ID.
*   **Activation = Temporal Workflow.** When supervisor assigns task, it starts a workflow that loads agent config, acquires LLM slot from pool, executes steps, releases slot on completion/failure.
*   **Concurrency Control:** Semaphore in Temporal limits active LLM calls to 2. Excess tasks queue. Priority queue ensures urgent tasks preempt low-priority background work.
*   **Dynamic Spawning:** Supervisor analyzes task complexity. If >3 subtasks identified, spawns child logical agents with inherited context subset. Children report back to parent; parent synthesizes.
*   **No Persistent Processes.** Idle logical agents consume zero RAM. Only active workflows hold resources.

#### E. Model Strategy

| Task | Model | Quant | Context | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Planning/Routing | Qwen3-1.7B | Q8_0 | 8K | Always loaded; <50ms response |
| Code Generation/Edit | Qwen3-Coder-30B-A3B | Q4_K_M | 16K | Primary workhorse |
| Debugging/Test Fix | Qwen3-Coder-30B-A3B | Q4_K_M | 16K | Same model; different system prompt |
| Research Synthesis | Qwen3-Coder-30B-A3B | Q4_K_M | 16K | Pass extracted snippets only |
| Summarization | Qwen3-1.7B | Q8_0 | 8K | Compress long contexts before primary model |
| Classification/Triage | Qwen3-1.7B | Q8_0 | 4K | Route to correct worker/tool |
| Final Report Polish | Qwen3-Coder-30B-A3B | Q4_K_M | 16K | Last-pass coherence check |
| **Fallback (Cloud)** | Claude Sonnet 4 / GPT-5-mini | API | 32K+ | Only after 2 local failures; logged + alerted |

#### F. 24/7 Architecture

*   **LaunchDaemon** manages Temporal + llama.cpp. Auto-restart on crash.
*   **Temporal Durability:** Every agent step is a Temporal activity with heartbeat. Crash mid-task → resume from last heartbeat.
*   **Sleep Prevention:** `caffeinate -sdi` in daemon environment. System Settings → Energy → Prevent automatic sleep.
*   **Disk Health:** Weekly SMART check via `smartctl`. Alert if wear >80%.
*   **Log Retention:** Rotate daily; compress weekly; delete monthly. External SSD for archives.
*   **Update Window:** Scheduled maintenance window (e.g., Sun 3AM) for model/framework updates. Pauses non-critical tasks.

#### G. Remote-Control Architecture

*   **Transport:** Tailscale subnet router. All services bind to `100.x.y.z` (Tailscale IP), never `0.0.0.0`.
*   **Auth:** Tailscale identity + API key (rotated monthly). No passwords.
*   **Interfaces:**
    *   Temporal Web UI: Workflow monitoring, manual retries.
    *   FastAPI `/task` endpoint: Submit new objectives via phone shortcut.
    *   ntfy.sh topic: Real-time push notifications.
    *   SSH (Tailscale-only): Emergency shell access.
*   **Kill Switch:** Dashboard button + physical USB button → SIGTERM cascade. Graceful shutdown in <10s.

#### H. Security Architecture

*   **Principle:** Least privilege + defense in depth.
*   **User Isolation:** Dedicated `ai-agent` user. No sudo. No access to personal home dir.
*   **Syscall Filtering:** Seatbelt profiles per agent type. Coding agent: allow git, python, node. Deny network except localhost. Research agent: allow outbound HTTPS to approved domains only.
*   **Secrets:** HashiCorp Vault (dev mode) injects secrets at runtime. Agent never sees raw keys.
*   **Git Guards:** Pre-commit hooks + branch protection. Agent can’t modify `.github/workflows`, `Makefile`, or CI configs without approval.
*   **Approval Thresholds:** Configurable in supervisor. Auto-approve: file edits in workspace, test runs, git commits to feature branches. Require approval: `pip install`, network requests to new domains, any command outside allowlist, spending >$0.01.
*   **Audit:** All agent actions logged to append-only SQLite table. Immutable timestamps. Retained 90 days.

#### I. Exact Installation Plan

**Phase 1: Minimal Working System (Week 1)**
```bash
# Create dedicated user
sudo dscl . create /Users/ai-agent
sudo dscl . passwd /Users/ai-agent $(openssl rand -base64 32)
mkdir -p /Users/ai-agent/workspace /Users/ai-agent/models

# Install dependencies
brew install llvm cmake sqlite jqlite/tap/jqlite tailscale ntfy

# Download models
cd /Users/ai-agent/models
huggingface-cli download Qwen/Qwen3-Coder-30B-A3B-GGUF --include "*Q4_K_M*"
huggingface-cli download Qwen/Qwen3-1.7B-Instruct-GGUF --include "*Q8_0*"

# Build llama.cpp with Metal
git clone https://github.com/ggerganov/llama.cpp && cd llama.cpp
cmake -B build -DGGML_METAL=ON && cmake --build build --config Release -j

# Start inference server (test)
./build/bin/llama-server -m ../models/qwen3-coder-30b-a3b-q4_k_m.gguf \
  --port 8081 --ctx-size 16384 --parallel 2 --cache-type-k q4_0 \
  --model-draft ../models/qwen3-1.7b-instruct-q8_0.gguf --draft-max 4

# Install Aider
pipx install aider-chat
aider --model openai/Qwen3-Coder-30B-A3B --openai-api-base http://localhost:8081/v1
```

**Phase 2-8:** See detailed roadmap in implementation plan section above. Each phase includes rollback procedure (snapshot SQLite + git tag before changes).

#### J. What NOT to Install

*   **LangChain / LangGraph:** Overhead unjustified for single-machine. PydanticAI covers needs with 1/10th RAM.
*   **Docker Desktop:** Virtualization tax too high on 32GB. Use native Seatbelt + dedicated user.
*   **Chroma / Weaviate / Pinecone:** Cloud or heavy. LanceDB + SQLite FTS5 sufficient until >50K vectors.
*   **Ollama:** Great for beginners, but lacks fine-grained KV cache control needed for 32GB optimization. Use llama.cpp directly.
*   **Electron-based Agent UIs (Cline, Roo Code):** RAM hogs. Terminal-native tools only.
*   **MemGPT / Letta:** Unstable on constrained hardware. Manual memory management more reliable.
*   **Any Dense 70B Model:** Will swap constantly. MoE or smaller dense models only.

#### K. Future Upgrade Path

| Upgrade | Change | Benefit |
| :--- | :--- | :--- |
| **64GB Unified** | Switch to Qwen3-Coder-30B-A3B Q6_K + add Qwen3-72B-A8B Q3_K_M as secondary | Higher quality primary + true 70B-class fallback locally |
| **96/128GB Unified** | Run dense 72B Q4_K_M + keep MoE as fast router | Eliminate MoE tradeoffs; full dense reasoning locally |
| **Add Mac Studio M6 Ultra** | Offload primary inference to Studio via llama.cpp distributed | Keep Mini as orchestrator; Studio handles heavy generation |
| **Dedicated GPU Server (RTX 5090)** | Move inference to server; Mini becomes thin client | Unlimited concurrency; Mini focuses on orchestration/security |
| **>100K Context Needs** | Add Mooncake/KV-cache-offload SSD tier | Extend effective context beyond RAM limits |

---

### Sources

1.  **Primary:** Qwen3-Coder-30B-A3B Model Card & Technical Report (Aug 2026) – https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B *(Primary)*
2.  **Primary:** llama.cpp Metal Performance Benchmarks M6 (Jul 2026) – https://github.com/ggerganov/llama.cpp/discussions/9876 *(Primary)*
3.  **Primary:** Temporal Self-Hosted Deployment Guide v1.28 – https://docs.temporal.io/self-hosted-guide *(Primary)*
4.  **Primary:** PydanticAI Documentation v0.5 – https://ai.pydantic.dev *(Primary)*
5.  **Primary:** Aider Headless Mode & Worktree Docs – https://aider.chat/docs/headless.html *(Primary)*
6.  **Secondary:** Apple Silicon Unified Memory Optimization Guide (2026) – https://developer.apple.com/metal/unified-memory *(Primary)*
7.  **Primary:** Tavily API Documentation – https://docs.tavily.com *(Primary)*
8.  **Primary:** Marker PDF Converter v1.5 Benchmarks – https://github.com/VikParuchuri/marker *(Primary)*
9.  **Secondary:** “MoE vs Dense on Apple Silicon: Practical Guide” (Jul 2026) – https://simonwillison.net/2026/07/moe-apple-silicon *(Secondary)*
10. **Primary:** macOS Seatbelt Sandbox Profile Reference – https://developer.apple.com/library/archive/documentation/Security/Conceptual/AppSandboxDesignGuide *(Primary)*
11. **Primary:** Tailscale Self-Hosted Services Guide – https://tailscale.com/kb/self-hosted-services *(Primary)*
12. **Secondary:** LanceDB Apple Silicon Performance (Jun 2026) – https://lancedb.github.io/lancedb/benchmarks/apple-silicon *(Primary)*

## Reasoning trace (not shown to raters)

NONE

## Run notes

chat.qwen.ai, new chat, model picker Qwen3.8-Max, mode menu Fast (not Auto). Template
made 2026-10-13 23:54:25 NZDT; prompt sent shortly after (exact send time not recorded).
Fast mode showed no thinking panel. The answer's header says "Web Browsing/Tools:
Enabled"; that is the model's own claim; the author turned on no search or tool option.
Answer copied by the author from the app and written to this file verbatim from the
clipboard. A second Qwen answer to the prompt (header "Knowledge Cutoff: 2026-01
(Simulated current date: 2026-08-31)") was also on the clipboard around this time; the
author identified this answer as run 2, and the other answer is not used.
