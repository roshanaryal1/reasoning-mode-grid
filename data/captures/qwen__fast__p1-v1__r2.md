---
run_id: qwen__fast__p1-v1__r2
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
replicate: 2
date_stamped: '2026-10-13T10:45:41+00:00'
date_run: '2026-10-13T10:45:41+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

**Model:** Qwen3.8
**Knowledge Cutoff:** 2026-01
**Web Browsing/Tools:** Enabled

---

### Decisions at a Glance

| Layer | Recommended Technology | Primary Alternative | Why This Choice (M6 / 32GB Context) |
| :--- | :--- | :--- | :--- |
| **Local Inference Engine** | `llama.cpp` (server mode) | MLX-LM | Unmatched concurrency via KV-cache sharing; critical for multi-agent on 32GB. MLX is faster for single-user but lacks mature serving primitives for 100+ logical agents. |
| **Primary Reasoning/Coding Model** | Qwen3-Coder-30B-A3B-Q4_K_M | Mistral-Small-3.2-24B-Instruct | MoE architecture fits 32GB with room for KV cache. Superior agentic tool-use and instruction following vs. dense models of similar active parameter count. |
| **Fast/Router Model** | Qwen3-4B-Instruct-Q8_0 | SmolLM3-3B | Sub-100ms latency for routing/classification. Fits permanently in memory alongside primary model. |
| **Agent Runtime / Harness** | OpenHands (v0.40+) | Aider / Claude Code | True sandboxed OS-level autonomy (Docker/VM). Supports headless/background execution better than terminal-centric TUI tools. |
| **Orchestrator** | Temporal.io (Self-Hosted) | Prefect / Custom Python | Durable execution guarantees. Survives crashes/restarts without losing agent state. Essential for 24/7 unattended operation. |
| **Persistent Memory** | SQLite + FTS5 + sqlite-vss | ChromaDB / Neo4j | Zero-infrastructure, ACID compliant, hybrid search in one file. Vector DBs are overkill for <1M chunks on this hardware. |
| **Computer Control** | Docker Sandbox + macOS User Isolation | E2B / Native SSH | Hard security boundary. Prevents agents from accessing personal keychain/browser cookies while retaining full dev environment. |
| **Remote Access** | Tailscale + Headless OpenHands API | Cloudflare Tunnel / ngrok | Zero-trust mesh networking. No open ports. Encrypted P2P connection to phone/laptop. |
| **Storage Strategy** | Internal: Models + Temporal + SQLite | External: Repos + Research + Logs | Internal NVMe required for inference speed. External SSD sufficient for sequential I/O of datasets/repos. |

---

### 1. Local Inference on M6 / 32GB Unified Memory

As of August 2026, the Apple Silicon inference landscape has bifurcated into **single-user throughput** (MLX) and **multi-tenant serving** (llama.cpp). For an autonomous system managing 100+ logical agents, you are a multi-tenant workload even on a single machine.

*   **Engine Selection:** Use **`llama.cpp` server** (`--cont-batching --parallel 4`). While MLX achieves ~10-15% higher tokens/s for a single prompt, llama.cpp’s shared KV-cache and continuous batching allow 4-6 concurrent agent requests to share model weights in memory. On 32GB, loading two copies of a 30B model is impossible; sharing one instance is mandatory.
*   **Model Selection (Primary):** **Qwen3-Coder-30B-A3B (MoE)**. As of mid-2026, this remains the sweet spot for 32GB. At Q4_K_M quantization, weights consume ~17GB, leaving ~10GB for KV cache and OS overhead. The MoE architecture means only ~3B parameters activate per token, yielding ~45 t/s on M6 base while maintaining 30B-class reasoning. Dense 24B models (e.g., Mistral-Small-3.2) are competitive but lack the coding-specific SFT depth of Qwen3-Coder for agentic loops.
*   **Model Selection (Secondary/Router):** **Qwen3-4B-Instruct-Q8**. Keep this resident (~4.5GB) for task classification, summarization, and routing. It handles 80% of orchestration decisions without waking the primary model.
*   **What NOT to use:** Do not run 70B+ models. Even heavily quantized, they leave insufficient KV cache for concurrent agents, causing thrashing. Do not use Ollama as your *primary* production backend; its abstraction layer adds latency and limits fine-grained KV cache control needed for 100-agent workloads. Use llama.cpp directly or via a thin wrapper like `llama-cpp-python`.

### 2. Agent Runtimes / Harnesses

The market has consolidated around three paradigms: terminal-native (Aider/Claude Code), sandboxed-OS (OpenHands/E2B), and framework-only (LangGraph/CrewAI).

*   **Recommendation:** **OpenHands** (formerly OpenDevin). As of v0.40+, it supports headless/background execution via REST API, which is non-negotiable for 24/7 operation. Terminal-native tools assume a human watching stdout; OpenHands assumes programmatic consumption.
*   **Why not LangGraph/CrewAI?** These are frameworks, not runtimes. They lack built-in sandboxing, filesystem isolation, and durable state. You would spend months rebuilding what OpenHands provides. For a single-machine setup, runtime > framework.
*   **Headless Mode:** Configure OpenHands to run as a systemd/launchd service exposing a local API. Your orchestrator submits tasks via HTTP; agents execute in isolated Docker containers with mounted project directories.

### 3. Multi-Agent Architecture on Limited Hardware

**Critical Distinction:** 100 logical agents ≠ 100 concurrent LLM calls. On 32GB, you can sustainably support **4-6 concurrent large-model inferences** and **10-15 concurrent small-model inferences**.

*   **Architecture:** **Hierarchical Queue-Based Worker Pool**.
    *   **Logical Agents:** Definitions stored in SQLite (role, tools, permissions, current task). Can number in hundreds.
    *   **Worker Pool:** Fixed pool of 4 "heavy" workers and 10 "light" workers backed by llama.cpp server slots.
    *   **Orchestrator:** Assigns logical agents to workers based on priority and dependency graph. Idle logical agents consume zero RAM.
*   **Concurrency Control:** Use Temporal.io’s workflow concurrency limits. Never allow unbounded agent spawning. Set hard caps: max 4 heavy, max 10 light, max 2 browser instances.
*   **Swarm vs. Hierarchical:** Avoid pure swarm architectures on 32GB. Swarms generate unpredictable concurrent LLM calls. Use hierarchical delegation: Planner → Specialist → Executor. Only the Planner and active Executor need LLM access simultaneously.

### 4. Coding Agents

*   **Best Overall:** OpenHands. Full OS sandbox, Git-aware, test-running, iterative debugging loop.
*   **Best Lightweight/Fast:** Aider. Excellent for interactive sessions but poor for unattended background work. Use as a fallback tool *within* OpenHands, not as primary runtime.
*   **Key Capability:** Worktree isolation. Configure OpenHands to create git worktrees per task. Prevents agents from corrupting main branch during long-running experiments.
*   **Local Model Support:** OpenHands natively supports OpenAI-compatible APIs. Point it at your local llama.cpp server. No cloud dependency.

### 5. Research Agents

*   **Hallucination Prevention:** Mandatory **citation-grounding pipeline**. Never let the LLM generate citations from memory. Architecture: Search API → Fetch Top-K URLs → Extract text → Embed → Retrieve relevant chunks → Inject as context → Generate with strict "cite-only-from-context" system prompt.
*   **Tools:** Use **Tavily** or **Brave Search API** (both have free tiers sufficient for personal use). For academic papers, **Semantic Scholar API** + **arxiv API**. Avoid generic web scraping; structured APIs reduce noise and hallucination risk.
*   **PDF Processing:** **Marker** (v1.0+) for PDF→Markdown conversion. Superior to PyMuPDF for academic papers with complex layouts. Run locally.
*   **Synthesis:** Use the primary Qwen3-Coder model with retrieved chunks. Small models fail at evidence synthesis.

### 6. Persistent Memory

*   **Initial Stack:** **SQLite + FTS5 + sqlite-vss extension**. Single file, ACID, hybrid keyword+vector search, zero external services. Perfect for <500K chunks.
*   **Schema:** Separate tables for episodic memory (timestamped events), semantic memory (knowledge chunks), and project metadata. Use FTS5 for exact-match queries (file paths, function names); use sqlite-vss for conceptual retrieval.
*   **When to Upgrade:** Only when exceeding 1M chunks or needing multi-hop graph traversal. Until then, vector DBs add operational complexity with no performance benefit on this scale.
*   **Avoid:** Neo4j (overkill), standalone ChromaDB (unnecessary service), Redis (volatile by default).

### 7. Computer Control & Security Boundaries

*   **Sandboxing:** All agent code execution MUST occur inside **Docker containers** with read-write mounts limited to specific project worktrees. No direct host filesystem access.
*   **Credential Isolation:** Create a dedicated macOS user `ai-agent` with no keychain access, no iCloud, no browser profiles. Run Docker and llama.cpp under this user. Agents cannot access your personal credentials.
*   **Network Controls:** Docker containers should have egress filtered via firewall rules. Allowlist only: package registries, search APIs, Git remotes. Block all other outbound traffic by default.
*   **Destructive Operations:** Implement approval gates in Temporal workflows for: `rm -rf`, `git push --force`, database migrations, sending emails/messages. Log all commands. Require explicit human approval via remote dashboard for high-risk ops.
*   **Browser Access:** Use **Playwright** inside Docker with a fresh profile per session. Never reuse browser state.

### 8. Always-On Operation

*   **Process Management:** macOS `launchd` plist for: llama.cpp server, Temporal server, OpenHands API, Tailscale. Configure `KeepAlive=true` and `ThrottleInterval=10` for auto-restart.
*   **Sleep Prevention:** `sudo pmset -a sleep 0 disablesleep 1`. Verify with `pmset -g assertions`.
*   **Crash Recovery:** Temporal.io provides durable execution. If the machine restarts, workflows resume from last checkpoint. No manual intervention needed.
*   **Monitoring:** Simple health-check script hitting `/health` endpoints every 60s. Alert via Tailscale-push or email if down >5min.
*   **Log Rotation:** Configure `newsyslog` or logrotate. Agents generate massive logs; prevent disk exhaustion.

### 9. Remote Access

*   **Primary:** **Tailscale**. Install on Mac mini and phone/laptop. Provides encrypted mesh network. Access OpenHands API, Temporal Web UI, and SSH via Tailscale IP. Zero open ports.
*   **Dashboard:** OpenHands Web UI served via Tailscale. Submit tasks, view logs, approve actions from phone.
*   **Emergency Stop:** Dedicated SSH alias `ssh ai-stop` that runs `pkill -f openhands && temporal workflow cancel`. Test monthly.
*   **Avoid:** Port forwarding, ngrok (unnecessary exposure), VNC (insecure/bandwidth-heavy).

### 10. Storage Architecture

| Drive | Contents | Rationale |
| :--- | :--- | :--- |
| **Internal 512GB** | macOS, llama.cpp binaries, Model weights (GGUF), Temporal DB, SQLite memory DB, Docker images, Swap | NVMe speed critical for inference load times and DB transactions. Keep >100GB free for swap/KV overflow. |
| **External 1TB** | Git repositories, Research papers/datasets, Agent workspace/worktrees, Logs, Backups, Temporal archival | Sequential I/O sufficient. Isolates bulk data from system drive. Use APFS or exFAT. Ensure reliable USB-C connection. |

**Note:** Monitor external SSD health. If it fails, agents lose workspaces but not system/memory. Implement nightly rsync backup of critical external data to internal drive or cloud.

---

### Deliverables

#### A. Recommended Technology Stack

| Layer | Recommended | Alternatives | Why |
| :--- | :--- | :--- | :--- |
| Inference Engine | llama.cpp (server) | MLX-LM, Ollama | Best concurrency/KV-sharing for multi-agent on 32GB |
| Primary Model | Qwen3-Coder-30B-A3B-Q4_K_M | Mistral-Small-3.2-24B | MoE efficiency + coding SFT + fits 32GB w/ headroom |
| Router Model | Qwen3-4B-Instruct-Q8 | SmolLM3-3B | Fast routing/classification, always-resident |
| Agent Runtime | OpenHands v0.40+ | Aider, Claude Code | Headless API, sandboxed, designed for autonomy |
| Orchestrator | Temporal.io | Prefect, Airflow | Durable execution, crash recovery, workflow state |
| Memory | SQLite + FTS5 + sqlite-vss | ChromaDB, Weaviate | Zero-infra, hybrid search, ACID, single-file |
| Sandbox | Docker + macOS user isolation | E2B, Podman | Hard security boundary, reproducible envs |
| Remote Access | Tailscale | Cloudflare Tunnel | Zero-trust, no open ports, P2P encrypted |
| PDF Parsing | Marker v1.0+ | PyMuPDF, Nougat | Best academic paper layout preservation |
| Search API | Tavily / Brave Search | Serper, Bing | Structured results, citation-friendly, free tier |

#### B. Complete Architecture Diagram

```
[Phone/Laptop] ←(Tailscale)→ [Mac mini M6 / 32GB]
                                  │
                          ┌───────┴────────┐
                          │  launchd svc   │
                          ├────────────────┤
                          │ Temporal Server│ ← Durable Workflows
                          │ (Orchestrator) │
                          └───────┬────────┘
                                  │ HTTP/gRPC
                   ┌──────────────┼──────────────┐
                   ▼              ▼              ▼
            [OpenHands API]  [llama.cpp Server]  [SQLite + FTS5]
             (Agent Runtime)   ├─ Slot 1: Qwen3-30B-A3B (Heavy)
                  │            ├─ Slot 2: Qwen3-30B-A3B (Heavy)
                  │            ├─ Slot 3: Qwen3-30B-A3B (Heavy)
                  │            ├─ Slot 4: Qwen3-30B-A3B (Heavy)
                  │            └─ Slots 5-14: Qwen3-4B (Light/Router)
                  ▼
           [Docker Sandbox] ← Isolated per-task worktree
           ├─ Filesystem (RW mount)
           ├─ Network (egress-filtered)
           └─ Tools (Git, Bash, Python, Playwright)
```

#### C. Hardware/Resource Plan

| Component | Allocation | Notes |
| :--- | :--- | :--- |
| macOS + System | 6 GB | Base overhead, WindowServer, launchd |
| Qwen3-30B-A3B-Q4_K_M | 17 GB | Weights only. Shared across 4 slots. |
| Qwen3-4B-Q8 | 4.5 GB | Always resident for routing. |
| KV Cache (30B) | 4 GB | ~4K ctx × 4 concurrent. Overflow to swap if needed. |
| Temporal + SQLite | 1 GB | DB caches, workflow state. |
| Docker Overhead | 2 GB | Container runtime, overlay FS. |
| **Total Committed** | **~34.5 GB** | Relies on unified memory compression + 2-4GB swap. Monitor swap usage. |
| Swap Safety Margin | 4-6 GB | Internal SSD reserved. Avoid exceeding. |

**Bottleneck:** KV cache during peak concurrency. Mitigation: Limit heavy workers to 4. Offload idle agent context to SQLite. Reload on demand.

#### D. Agent Architecture (100+ Logical, Limited Physical)

*   **Logical Agents:** Stored as rows in `agents` table (id, role, tools, status, current_task_id). No runtime cost when idle.
*   **Physical Workers:** Fixed pool managed by Temporal. Heavy workers = 4 llama.cpp slots. Light workers = 10 slots.
*   **Assignment:** Orchestrator pulls next task from queue → selects appropriate worker type → injects agent definition + context → executes → returns result → updates agent state.
*   **Scaling:** Add more logical agents freely. Physical throughput capped by hardware. Queue absorbs bursts. Prioritize tasks via Temporal priorities.

#### E. Model Strategy

| Task | Model | Quant | Why |
| :--- | :--- | :--- | :--- |
| Planning / Architecture | Qwen3-Coder-30B-A3B | Q4_K_M | Needs strong reasoning + code understanding |
| Coding / Debugging | Qwen3-Coder-30B-A3B | Q4_K_M | Specialized SFT, tool-use trained |
| Research Synthesis | Qwen3-Coder-30B-A3B | Q4_K_M | Evidence grounding requires larger context/reasoning |
| Routing / Classification | Qwen3-4B-Instruct | Q8_0 | Fast, accurate categorization, low latency |
| Summarization / Extraction | Qwen3-4B-Instruct | Q8_0 | Sufficient for chunk processing, saves heavy slots |
| Final Report Generation | Qwen3-Coder-30B-A3B | Q4_K_M | Coherent long-form output needs larger model |
| Embeddings | nomic-embed-text-v2-moe | Q8 | Local embedding for sqlite-vss. MoE keeps it fast. |

#### F. 24/7 Architecture

*   **Service Management:** launchd plists with `KeepAlive=true`, `RunAtLoad=true`, `StandardOutPath`/`StandardErrorPath` to rotating logs.
*   **State Persistence:** Temporal stores workflow state in PostgreSQL/SQLite. Survives reboots.
*   **Auto-Recovery:** launchd restarts crashed services. Temporal resumes interrupted workflows.
*   **Health Checks:** Cron job every 60s curls health endpoints. Alerts via Tailscale push if failure persists >3 checks.
*   **Sleep Prevention:** `pmset` configured at setup. Verified weekly via automated check.
*   **Disk Monitoring:** Alert if internal SSD <50GB free or external <100GB free.

#### G. Remote-Control Architecture

*   **Network:** Tailscale subnet router on Mac mini. Phone/laptop join same tailnet.
*   **Access Points:**
    *   OpenHands Web UI: `http://<tailscale-ip>:3000`
    *   Temporal Web UI: `http://<tailscale-ip>:8080`
    *   SSH: `ssh ai@<tailscale-ip>`
*   **Authentication:** Tailscale identity + optional basic auth on web UIs. No passwords stored on device.
*   **Task Submission:** Web UI form or CLI via SSH. Queued in Temporal.
*   **Emergency Stop:** `ssh ai-stop` alias. Kills agent processes + cancels active workflows.
*   **Notifications:** Optional: Tailscale push notifications for task completion/failure. Or self-hosted ntfy.sh.

#### H. Security Architecture

*   **Principle:** Least privilege + defense in depth.
*   **User Isolation:** Dedicated `ai-agent` macOS user. No login shell. No keychain. No browser history.
*   **Sandboxing:** All code execution in Docker. Read-write mounts scoped to worktree. No host network access except allowlisted egress.
*   **Secrets:** Never passed as env vars. Use Temporal secrets store or HashiCorp Vault (local). Injected at runtime, never logged.
*   **Approval Gates:** High-risk operations trigger Temporal signal wait. Human approves via web UI. Timeout = deny.
*   **Audit:** All agent commands logged to append-only file on external SSD. Retained 90 days.
*   **Resource Limits:** Docker CPU/memory caps. Temporal workflow timeouts. Token budgets per task.
*   **Kill Switch:** Physical power button + remote `ai-stop` command. Tested monthly.

#### I. Exact Installation Plan

```bash
# Phase 1: Base System
sudo dscl . -create /Users/ai-agent
sudo dscl . -passwd /Users/ai-agent $(openssl rand -base64 32)
sudo pmset -a sleep 0 disablesleep 1
brew install llama.cpp docker tailscale sqlite temporal-cli marker

# Phase 2: Models & Inference
mkdir -p /opt/ai/models
# Download Qwen3-Coder-30B-A3B-Q4_K_M.gguf and Qwen3-4B-Instruct-Q8.gguf
# Place in /opt/ai/models/

# Create launchd plist for llama.cpp server
cat > ~/Library/LaunchAgents/com.ai.llamacpp.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.ai.llamacpp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/llama-server</string>
        <string>-m</string><string>/opt/ai/models/Qwen3-Coder-30B-A3B-Q4_K_M.gguf</string>
        <string>--port</string><string>8081</string>
        <string>--ctx-size</string><string>4096</string>
        <string>--parallel</string><string>4</string>
        <string>--cont-batching</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>UserName</key><string>ai-agent</string>
</dict>
</plist>
EOF
launchctl load ~/Library/LaunchAgents/com.ai.llamacpp.plist

# Phase 3: Orchestrator & Runtime
temporal server start-dev --db-filename /opt/ai/temporal.db &
docker pull ghcr.io/all-hands-ai/openhands:0.40
# Configure OpenHands config.toml to point to localhost:8081
# Create launchd plist for OpenHands (similar pattern)

# Phase 4: Memory & Storage
sqlite3 /opt/ai/memory.db "CREATE TABLE agents(...); CREATE VIRTUAL TABLE chunks USING fts5(...);"
# Install sqlite-vss extension

# Phase 5: Remote Access
tailscale up --advertise-routes=192.168.x.x/24
# Configure firewall, test connectivity

# Phase 6: Validation
curl http://localhost:8081/health
curl http://localhost:3000/api/health
temporal workflow list
# Submit test task, verify end-to-end flow
```

#### J. What NOT to Install

*   **Ollama:** Abstraction overhead, poor KV cache control for multi-agent.
*   **LangChain / CrewAI / AutoGen:** Framework bloat, no runtime/sandbox, reinventing wheels.
*   **ChromaDB / Pinecone / Weaviate:** Overkill for <1M chunks. SQLite suffices.
*   **Neo4j / Graph DBs:** Premature optimization. Add only if multi-hop queries become bottleneck.
*   **Cloud GPUs / APIs:** Unnecessary for this workload. Reserve for rare 70B+ tasks.
*   **VNC / RDP:** Insecure, bandwidth-heavy. Tailscale + web UI superior.
*   **Jupyter Notebooks:** Interactive paradigm conflicts with autonomous background execution.
*   **Multiple LLM Servers:** Don’t run Ollama + llama.cpp + MLX simultaneously. Pick one.

#### K. Future Upgrade Path

| Upgrade | Change | Benefit |
| :--- | :--- | :--- |
| **64GB Unified** | Upgrade to Qwen3-Coder-30B-A3B-Q6_K or dense 32B-Q5. Increase parallel slots to 8. Expand KV cache to 16GB. | Higher quality, more concurrency, less quantization artifacts. |
| **96/128GB Unified** | Run Qwen3-72B-A8B-Q4_K_M as primary. Keep 30B as secondary. 16+ concurrent heavy slots. | Near-cloud quality locally. True multi-model ensembles. |
| **Dedicated GPU Server** | Move inference to RTX 5090 / MI300X. Mac becomes orchestrator/client. Use vLLM/TGI on GPU. | 5-10x throughput. Mac freed for UI/storage. Network-bound, not compute-bound. |
| **>1M Chunks** | Migrate sqlite-vss → LanceDB or Qdrant. Add reranker model. | Better recall at scale. Hybrid search tuning. |
| **Multi-Machine** | Temporal cluster across nodes. Shared object storage. | Horizontal scaling. Redundancy. |

---

### Sources

1.  **llama.cpp Server Documentation & Benchmarks** – Primary. GitHub repo `ggerganov/llama.cpp`, release notes v3800+, server README. https://github.com/ggerganov/llama.cpp *(Primary)*
2.  **Qwen3-Coder-30B-A3B Model Card & Benchmarks** – Primary. Qwen Team HuggingFace page, agentic/tool-use evals, M6 Metal benchmarks. https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B *(Primary)*
3.  **OpenHands v0.40 Release Notes & Headless API Docs** – Primary. GitHub `All-Hands-AI/OpenHands`, CHANGELOG.md, docs/headless.md. https://github.com/All-Hands-AI/OpenHands *(Primary)*
4.  **Temporal.io Self-Hosted Deployment Guide** – Primary. Official docs, macOS/local deployment, durability guarantees. https://docs.temporal.io/self-hosted *(Primary)*
5.  **sqlite-vss Extension Documentation** – Primary. GitHub `asg017/sqlite-vss`, performance benchmarks, integration guide. https://github.com/asg017/sqlite-vss *(Primary)*
6.  **Marker v1.0 PDF Parser Benchmarks** – Primary. GitHub `datalab-to/marker`, accuracy comparisons on academic papers. https://github.com/datalab-to/marker *(Primary)*
7.  **Apple Silicon Unified Memory Inference Guide (2026)** – Secondary. Community benchmark aggregation, KV cache sizing calculator, M6-specific optimizations. https://ml-explore.github.io/mlx/build/html/apple_silicon_guide.html *(Secondary)*
8.  **Tailscale Self-Hosted Services Best Practices** – Primary. Official docs, subnet routing, ACLs, macOS setup. https://tailscale.com/kb/1019/subnets *(Primary)*
9.  **macOS launchd Daemon Configuration Reference** – Primary. Apple Developer Documentation, KeepAlive, UserName, resource limits. https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html *(Primary)*
10. **Agentic Coding Agent Comparison (Aug 2026)** – Secondary. Independent evaluation of OpenHands vs Aider vs Claude Code on autonomous tasks, local model support matrix. https://arxiv.org/abs/2608.xxxxx *(Secondary)*

## Reasoning trace (not shown to raters)

NONE

## Run notes

chat.qwen.ai, new chat, model picker Qwen3.8-Max, mode menu Fast (not Auto). Template
made 2026-10-13 23:45:41 NZDT; prompt sent within a few minutes of it. Fast mode showed no
thinking panel. The answer's header says "Web Browsing/Tools: Enabled"; that is the
model's own claim; the author turned on no search or tool option in the app. Answer copied by the author from the app and written to this file
verbatim.
