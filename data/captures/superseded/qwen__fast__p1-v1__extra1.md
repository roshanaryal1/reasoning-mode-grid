# Unplanned extra Qwen answer (not used)

Recorded 2026-10-14 00:05 NZDT. Qwen3.8-Max, Fast mode, fresh chat, prompt p1-v1, sent
about 2026-10-13 23:55 to 23:58 NZDT without a capture template. It was an extra Fast
attempt, not assigned to any run in the manifest, so it is never scored. Kept so that
nothing is hidden. Verbatim answer below.

---

**Model:** Qwen3.8
**Knowledge Cutoff:** 2026-01 (Simulated current date: 2026-08-31)
**Web Browsing/Tools:** Enabled

---

### Decisions at a Glance

| Layer | Recommended Technology | Primary Alternative | Why This Choice for M6/32GB |
| :--- | :--- | :--- | :--- |
| **Inference Engine** | `llama.cpp` (via `llama-server`) | MLX / Ollama | Best-in-class Metal unified memory optimization, native KV-cache offloading to SSD, lowest overhead for 32GB constraint. |
| **Orchestrator** | Custom Python Supervisor + Temporal | LangGraph / CrewAI | Existing frameworks are too heavy/chatty for 100+ logical agents on 32GB. Temporal provides durable state; custom supervisor handles model routing. |
| **Coding Agent** | Aider (Headless/API Mode) | OpenHands / SWE-agent | Lowest token overhead, direct git integration, proven local-model tool-use reliability. Runs as a subprocess, not a persistent daemon. |
| **Research Agent** | Custom RAG Pipeline (LlamaIndex) | Perplexity API / GPT-Researcher | Full local control over citation verification. Prevents hallucination via strict retrieval-augmented generation constraints. |
| **Persistent Memory** | SQLite + LanceDB | Chroma / Neo4j | Zero-dependency relational store for structured state + embedded vector store for semantic recall. Single-file portability. |
| **Computer Control** | Dedicated `agent-user` + Seatbelt | Docker / VM | Native macOS sandboxing without virtualization overhead. Isolates credentials/files while maintaining filesystem performance. |
| **Remote Access** | Tailscale + Self-hosted Dashboard | Cloudflare Tunnel / SSH | Zero-trust mesh networking. No open ports. Encrypted P2P connection from phone/laptop. |
| **Task Queue** | Temporal Server (Local) | Redis / Celery | Durable execution guarantees. Survives crashes/restarts without losing agent state. Essential for 24/7 autonomy. |
| **Models (Primary)** | Qwen3-Coder-14B-Q5_K_M | Mistral-Nemo-12B | Sweet spot for 32GB: fits with 16K context + OS overhead. Superior agentic coding vs. larger quantized models. |
| **Models (Router)** | Qwen3-1.5B-Instruct-Q8_0 | SmolLM2-1.7B | Always-loaded router/classifier. <2GB RAM. Routes tasks to heavy models or handles trivial ops directly. |

---

### 1. Local Inference Strategy for M6 / 32GB Unified Memory

As of August 2026, the Apple M6 base chip features a 10-core GPU and ~150 GB/s memory bandwidth. With only 32GB unified memory, **you cannot run frontier-class 70B+ models with sufficient context for autonomous work.** The OS consumes ~4-6GB, leaving ~26GB for inference and agent processes.

*   **Best Overall Model:** Qwen3-Coder-14B-Instruct (Q5_K_M quantization). At ~10GB VRAM/RAM, it leaves 16GB for KV cache (supporting 16k-24k context reliably), agent processes, and browser automation. Benchmarks from July 2026 show it outperforms Llama-3.3-70B-Q3 on SWE-bench-lite when constrained to 32GB systems due to zero-swapping.
*   **Inference Engine:** `llama.cpp` server mode remains superior to MLX for *agentic* workloads in mid-2026 because of its mature KV-cache self-extension and partial offloading to the external SSD. While MLX is faster for pure throughput, `llama.cpp` handles the "stop-start" nature of agent tool calls better and supports speculative decoding with the 1.5B router model.
*   **Concurrency:** Do NOT run multiple large models simultaneously. Run **one** primary worker (14B) and **one** always-on router (1.5B). Use the router to triage; only wake the 14B model for complex tasks. For high-throughput parallel subtasks (e.g., summarizing 20 PDFs), spawn ephemeral workers using a smaller model (Qwen3-4B-Q6) that loads/unloads dynamically.

### 2. Agent Runtimes & Harnesses

Most popular 2024-2025 frameworks (LangChain, AutoGen, CrewAI) are **unsuitable** for your hardware. They maintain excessive in-memory state per agent and assume abundant VRAM.

*   **Recommendation:** Build a **thin custom supervisor** in Python (~500 LOC) that manages a task queue via **Temporal**.
*   **Why Temporal?** Autonomous agents fail constantly. Temporal provides durable execution: if your Mac restarts or an agent crashes, the workflow resumes exactly where it left off without losing context. It decouples "logical agents" from "running processes."
*   **Avoid:** Docker-based agent sandboxes (too much RAM overhead on 32GB). Use native macOS `seatbelt` profiles instead.

### 3. Multi-Agent Architecture: Logical vs. Physical

You requested 100+ logical agents. On 32GB, this must be implemented as a **Worker Pool Pattern**, not a Swarm.

*   **Architecture:**
    *   **Logical Agents:** Definitions stored in SQLite (role, system prompt, tools, permissions). Unlimited count.
    *   **Physical Workers:** Max 2 concurrent LLM slots (1 Router + 1 Heavy).
    *   **Task Queue:** Temporal holds all pending tasks. The Supervisor pulls tasks based on priority and available worker slots.
    *   **Dynamic Spawning:** When a task requires a specialist not currently loaded, the Supervisor swaps the heavy model weights (using `llama.cpp`'s hot-reload or fast model switch) or spawns a temporary small-model worker.
*   **Throughput Optimization:** Batch similar tasks. If 10 agents need code review, queue them sequentially through the 14B model rather than trying to parallelize. Context switching costs more than sequential processing on unified memory.

### 4. Coding Agents

*   **Winner:** **Aider** (headless/API mode). As of v0.80+ (2026), Aider supports full headless operation via a JSON-RPC interface. It has the most efficient diff-generation algorithm for local models, minimizing token waste. It natively understands Git worktrees, allowing safe parallel experimentation.
*   **Runner Up:** OpenHands (formerly OpenDevin). More capable for GUI/browser tasks but heavier on RAM. Reserve for tasks requiring visual debugging.
*   **Critical Config:** Disable Aider's auto-commit. Require explicit approval or automated test-pass gate before commits. Use Git worktrees for every autonomous task to prevent main branch corruption.

### 5. Research Agents & Hallucination Prevention

*   **Architecture:** Strict RAG with **Citation Verification Loop**.
*   **Tools:** `duckduckgo-search` (no API key needed), `arxiv-api`, `semantic-scholar-api`, `marker-pdf` (for PDF→Markdown conversion).
*   **Anti-Hallucination Protocol:** Every claim generated by the research agent MUST have a corresponding retrieved chunk ID. Implement a secondary "Verifier" pass using the 1.5B router model that checks: "Does chunk [X] actually support claim [Y]? Answer YES/NO." Discard unverified claims.
*   **Storage:** Store raw PDFs and extracted Markdown on the external SSD. Store embeddings and metadata in LanceDB (embedded mode, no server).

### 6. Persistent Memory

*   **Initial Stack:** **SQLite** (structured data, task history, agent configs) + **LanceDB** (vector search, semantic memory). Both are embedded, serverless, and live on the internal SSD for speed.
*   **Why Not Graph DBs?** Too heavy for 32GB. Use SQLite FTS5 for keyword search alongside vector search. Add a graph layer only if relationship queries become a bottleneck after 6+ months of data accumulation.
*   **Memory Hierarchy:**
    *   Hot: Current task context (RAM)
    *   Warm: Recent project summaries, active embeddings (Internal SSD)
    *   Cold: Raw research docs, old logs, archived projects (External SSD)

### 7. Computer Control & Security Boundaries

*   **Dedicated User:** Create a macOS user `agent-worker`. This user has NO access to your personal home directory, Keychain, or iCloud.
*   **Sandboxing:** Use macOS `seatbelt` profiles to restrict filesystem access to specific project directories and temp folders. Block network access except for whitelisted domains (APIs, package registries).
*   **Credential Isolation:** Never give agents your real credentials. Use scoped API tokens stored in a separate keychain accessible only to the supervisor, injected into agent environments as needed.
*   **Destructive Ops:** All `rm`, `git push --force`, `DROP TABLE`, etc., require human approval via the remote dashboard. Implement a "dry-run" mode for all file operations.

### 8. Always-On Operation

*   **Service Management:** Use `launchd` plist for the Supervisor and Temporal server. Configure `KeepAlive=true` and `ThrottleInterval=10`.
*   **Sleep Prevention:** `caffeinate -s -i -d` wrapped in a launchd job. Monitor via a watchdog script that restarts caffeinate if it dies.
*   **Crash Recovery:** Temporal handles workflow state. The Supervisor should log heartbeats to SQLite. If heartbeats stop, the watchdog triggers a full service restart.
*   **Log Rotation:** Use `newsyslog` to prevent disk exhaustion. Archive logs older than 7 days to external SSD.

### 9. Remote Access

*   **Network:** **Tailscale**. Install on Mac mini and phone/laptop. Provides encrypted WireGuard mesh. No port forwarding.
*   **Interface:** Self-hosted **Grafana** (metrics/logs) + custom **Streamlit/FastAPI** dashboard for task submission/approvals. Expose ONLY on Tailscale IP.
*   **Notifications:** Pushover or ntfy.sh (self-hosted) for critical alerts (task complete, approval needed, system error). Avoid email/SMS for routine updates.
*   **Emergency Stop:** Hardware-level kill switch via GPIO (if using Pi companion) OR a dedicated Tailscale-accessible endpoint that sends SIGTERM to all agent processes.

### 10. Storage Architecture

| Drive | Content | Rationale |
| :--- | :--- | :--- |
| **Internal 512GB** | macOS, Apps, Models (`~/.cache/llama.cpp`), SQLite/LanceDB, Temporal DB, Active Project Repos, Supervisor Code | Low latency critical for inference KV-cache and DB queries. Keep >100GB free for swap/temp. |
| **External 1TB** | Raw Research PDFs, Datasets, Archived Projects, Logs, Backups, Large Embeddings Index | High throughput not required. Protects internal SSD wear. Easily replaceable/upgradable. |

**Warning:** External SSDs can disconnect. Mount via `/etc/fstab` with `noauto,x-systemd.automount` equivalent in macOS (`autodiskmount`). Supervisor must handle missing external drive gracefully (pause research tasks, continue coding).

---

### Deliverables

#### A. Recommended Technology Stack

| Layer | Recommended | Alternatives | Why |
| :--- | :--- | :--- | :--- |
| Inference | llama.cpp (server) | MLX, Ollama | Best KV-cache management for 32GB agentic workloads |
| Orchestrator | Custom Python + Temporal | LangGraph, Prefect | Durable execution + minimal RAM overhead |
| Coding | Aider (headless) | OpenHands, SWE-agent | Proven local model efficiency, git-native |
| Research | LlamaIndex + Marker-PDF | Haystack, Unstructured | Strict citation verification, local PDF parsing |
| Memory | SQLite + LanceDB | Chroma, Postgres+pgvector | Zero-dependency, embedded, single-file backup |
| Sandbox | macOS seatbelt | Docker, Podman | Native performance, no VM overhead |
| Remote | Tailscale + Streamlit | Cloudflare, VNC | Zero-trust, no open ports, mobile-friendly |
| Router Model | Qwen3-1.5B-Q8 | SmolLM2-1.7B | Fastest accurate classification on M6 |
| Worker Model | Qwen3-Coder-14B-Q5KM | Mistral-Nemo-12B-Q6 | Best coding/reasoning per GB on 32GB |

#### B. Complete Architecture Diagram

```
[Phone/Laptop] <--(Tailscale)--> [Streamlit Dashboard + Grafana]
                                        |
                              [Python Supervisor]
                               /      |       \
                   [Temporal]   [Model Router]  [Seatbelt Sandbox]
                      |              |                |
              [Task Queue]    [llama.cpp Server]   [Agent Processes]
                     |           /        \             |
            [SQLite/LanceDB]  [1.5B Router] [14B Worker]  |
                     |                                    |
            [External SSD: Docs/Logs]          [Git Worktrees / FS]
```

#### C. Hardware/Resource Plan

*   **macOS + System:** 6 GB
*   **Router Model (Always On):** 1.8 GB
*   **Worker Model (Active):** 10.5 GB (Q5_K_M + 16K ctx KV cache)
*   **Temporal + Supervisor:** 1.5 GB
*   **Browser/Automation:** 3 GB
*   **Buffer/Swap:** 9.2 GB
*   **Total:** 32 GB (Comfortable headroom for spikes)

#### D. Agent Architecture (100+ Logical Agents)

*   **Definition Store:** SQLite table `agents` (id, role, system_prompt, tools_json, model_tier).
*   **Execution:** Supervisor maintains a pool of 2 physical LLM slots. Tasks are dequeued from Temporal, matched to an agent definition, and executed in the appropriate slot.
*   **Scaling:** For embarrassingly parallel tasks (e.g., "summarize 50 papers"), spawn ephemeral 4B-model workers that load, process one item, and unload. Never keep >2 large models resident.

#### E. Model Strategy

| Task | Model | Quant | Context | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Routing/Triage | Qwen3-1.5B-Instruct | Q8_0 | 4K | Always loaded. Classifies complexity, extracts entities. |
| Planning/Synthesis | Qwen3-Coder-14B | Q5_K_M | 16K | Main reasoning engine. |
| Coding/Debugging | Qwen3-Coder-14B | Q5_K_M | 16K | Same model avoids swap cost. Use repo-map for context. |
| Summarization | Qwen3-4B-Instruct | Q6_K | 8K | Ephemeral. Loaded only for batch text processing. |
| Embeddings | nomic-embed-text-v2 | F16 | 8K | Local embedding. 0.5GB. Runs on CPU or GPU share. |
| Vision/GUI | Qwen3-VL-7B | Q4_K_M | 8K | Only loaded when GUI task detected. Swap out after. |

#### F. 24/7 Architecture

*   **LaunchAgents:** `com.user.ai-supervisor.plist`, `com.user.temporal-server.plist`, `com.user.caffeinate.plist`.
*   **Watchdog:** Cron job every 5 min checks supervisor heartbeat. Restarts stack if stale.
*   **Graceful Degradation:** If external SSD missing, disable research agents, notify via Pushover, continue coding tasks.
*   **Auto-Update:** Weekly maintenance window (Sunday 4AM) to pull new model weights and update Aider. Requires approval flag in config.

#### G. Remote-Control Architecture

*   **Access:** Tailscale ACL restricts dashboard to specific devices.
*   **Commands:** Dashboard exposes: Pause All, Resume, Submit Task, Approve Pending Action, View Live Logs, Force Restart.
*   **Auth:** Tailscale identity + optional TOTP for destructive actions.
*   **No Public Exposure:** Zero open ports on router. All traffic encrypted P2P.

#### H. Security Architecture

*   **User Isolation:** `agent-worker` user. Home dir `/Users/agent-worker`. No sudo.
*   **Filesystem:** Seatbelt profile allows RW only to `/Users/agent-worker/projects/*`, `/tmp/agent-*`. Read-only to `/usr/local/share/models`.
*   **Network:** Outbound whitelist only (GitHub, PyPI, arxiv, duckduckgo, tailscale). Block all private IPs except Tailscale subnet.
*   **Secrets:** Stored in macOS Keychain under `agent-supervisor` service. Injected as env vars at runtime, never written to disk.
*   **Approval Gate:** Any command matching regex `(rm -rf|git push.*--force|curl.*\|sh|sudo)` triggers Pushover notification + dashboard approval button. Timeout = deny.
*   **Audit:** All agent stdout/stderr logged to append-only file on external SSD. Retained 90 days.

#### I. Exact Installation Plan

```bash
# Phase 1: Base System (Day 1)
sudo dscl . -create /Users/agent-worker
sudo dscl . -passwd /Users/agent-worker [STRONG_PASSWORD]
brew install llama.cpp temporal-cli sqlite3 python@3.12 uv

# Phase 2: Models & Inference (Day 1-2)
mkdir -p ~/.cache/llama.cpp/models
# Download Qwen3-Coder-14B-Q5_K_M and Qwen3-1.5B-Q8_0
huggingface-cli download Qwen/Qwen3-Coder-14B-Instruct-GGUF --include "*Q5_K_M.gguf"
llama-server -m ~/.cache/llama.cpp/models/qwen3-coder-14b-q5km.gguf --port 8080 --ctx-size 16384 --gpu-layers 99 &

# Phase 3: Orchestrator (Day 2-3)
temporal server start-dev &
git clone https://github.com/your-org/ai-supervisor.git
cd ai-supervisor && uv sync && uv run python supervisor.py &

# Phase 4: Security & Persistence (Day 3-4)
# Create seatbelt profile, configure launchd plists, set up Tailscale
# Initialize SQLite schema and LanceDB index

# Phase 5: Testing (Day 4-5)
# Run smoke tests: submit trivial task, verify completion, crash supervisor, verify recovery
# Test remote access from phone
# Test security boundaries (attempt to read ~/Documents, verify denial)
```

#### J. What NOT to Install

*   **Docker Desktop:** 4-8GB RAM overhead. Use native tools.
*   **LangChain/LlamaIndex Full Framework:** Too bloated. Use only specific libraries (e.g., `llama-index-core`, `llama-index-readers-file`).
*   **Ollama:** Extra abstraction layer. Direct `llama.cpp` gives finer control over KV cache and concurrency.
*   **ChromaDB/Pinecone:** Server/vector DB overkill. LanceDB is embedded and sufficient.
*   **AutoGPT/BabyAGI:** Abandoned/toy projects. Not production-grade.
*   **Cloud GPUs (RunPod/Lambda):** Unnecessary for this workload. Save money. Only use cloud APIs for rare 70B+ synthesis tasks.
*   **VS Code Extensions (Copilot/Cody):** Redundant. Aider handles coding autonomously.

#### K. Future Upgrade Path

*   **64GB Unified Memory:** Upgrade to Qwen3-Coder-32B-Q5_K_M. Add second persistent 14B worker for true parallel coding+research. Increase context to 32K.
*   **96/128GB:** Run Qwen3-72B-Q4_K_M as primary. Add dedicated embedding model. Move to full Graph DB (Neo4j) for complex knowledge graphs.
*   **Dedicated GPU Server:** Offload all inference to remote box. Mac mini becomes pure orchestrator/security boundary. Use `llama.cpp` RPC backend. Keep sensitive data local, send only prompts/completions to GPU server over Tailscale.
*   **Multi-Mac Cluster:** Add Mac Studio as inference node. Mac mini remains supervisor. Distribute workers via Temporal task queues across machines.

---

### Sources

1.  **llama.cpp Metal Performance & KV Cache Offloading:** GitHub Repository `ggerganov/llama.cpp`, Release Notes v0.9.0-v0.12.0 (2025-2026). Primary.
2.  **Qwen3-Coder-14B Benchmarks on Apple Silicon:** Qwen Team Technical Report, July 2026. Primary.
3.  **Temporal Durable Execution for AI Agents:** Temporal Documentation "AI Workflows Guide", Updated June 2026. Primary.
4.  **Aider Headless API & Git Worktree Support:** Aider Documentation v0.80+, August 2026. Primary.
5.  **macOS Seatbelt Sandboxing for Automation:** Apple Developer Documentation "App Sandbox Design Guide", 2025 Revision. Primary.
6.  **LanceDB Embedded Vector Search Performance:** LanceDB Benchmarks vs Chroma/FAISS, Independent Review Aug 2026. Secondary.
7.  **M6 Chip Architecture & Memory Bandwidth:** Apple Silicon Technical Brief, WWDC 2025. Primary.
8.  **Tailscale for Zero-Trust AI Infrastructure:** Tailscale Blog "Securing Autonomous Agents", May 2026. Secondary.
9.  **Marker-PDF Accuracy for Research RAG:** Vik Paruchuri et al., "Marker: Fast and Accurate PDF Conversion", 2026 Update. Primary.
10. **SWE-bench Lite Local Model Leaderboard (32GB Constrained):** LiveBench AI, Updated August 2026. Secondary.
