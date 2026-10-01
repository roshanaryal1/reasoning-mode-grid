---
ai_name: DeepSeek (Instant + DeepThink)
model_version_id: "chat.deepseek.com free tier — DeepSeek-V4-Pro (default, GA 2026-04-24) with DeepThink reasoning toggle ON; not disclosed in-answer"
provider: DeepSeek
interface: web app (free tier, DeepThink mode)
browsing_enabled: no (states 'Research Date: August 31, 2026' but cites nothing; invents 2026 tool/model names)
knowledge_cutoff: unknown (DeepSeek-V4 has a 2026 cutoff, yet output is heavily confabulated)
prompt_version: v1
date_run: 2026-08-31
run_by: roshanaryal1
notes_on_run: >
  Same provider as data/responses/deepseek-instant.md and deepseek-expert.md but a THIRD distinct
  run — user labelled it "deepseek instant deepthink". Underlying model is almost certainly
  DeepSeek-V4-Pro (the free chat default since April 2026) with the DeepThink reasoning mode on.
  Despite a real 2026-capable base model, the answer fabricates more tool and model names than any
  other response in the corpus.
trust_rating: LOW — highest fabrication rate so far (Ornith-1.0-9B, Qwen3.5-35B-A3B, WhipDesk, Cloak, Helmrig, DiffResearch, LightAgent, and more); also advises memory oversubscription.
---

## Raw response

# Complete Architecture for a 24/7 Autonomous AI Workstation on M6 Mac mini (32GB)

> **Research Date**: August 31, 2026. All recommendations are based on current 2026 technology.

## Executive Summary

For your 32GB M6 Mac mini, the optimal architecture is:

- **Inference Engine**: Ollama with MLX backend (switched March 2026) — ~1.4–3× faster than llama.cpp on Apple Silicon
- **Primary Model**: Qwen3.5-35B-A3B (Q4_K_M) — ~22GB, MoE with 3B active params, 256K context
- **Coding Agent**: Aider (model-agnostic, auto-commit, 41K GitHub stars) + Ornith-1.0-9B for lightweight tasks
- **Orchestration**: Custom lightweight Python layer using Smolagents or LightAgent — not LangGraph/CrewAI (overhead too high for 32GB)
- **Memory**: SQLite + embeddings (Chroma/Qdrant) initially; Mem0 for hybrid memory later
- **24/7**: macOS launchd daemons with auto-restart
- **Remote**: Tailscale + WhipDesk or Cloak (end-to-end encrypted)
- **Sandboxing**: Lima VM + macOS Seatbelt profiles

## A. Recommended Technology Stack

| Layer | Recommended Technology | Alternatives | Why |
|-------|----------------------|--------------|-----|
| **Inference Engine** | Ollama (v0.19+, MLX backend) | LM Studio, mlx-lm, llama.cpp | Ollama switched to MLX in March 2026 — +93% decode gain on M-series; simplest API; auto-Metal acceleration |
| **Primary Model** | Qwen3.5-35B-A3B (Q4_K_M) | Qwen2.5-Coder-32B, Ornith-1.0-9B | ~22GB fits 32GB with room for KV cache; MoE = 3B active params = fast inference; 256K context; Apache 2.0 |
| **Lightning Model** | Ornith-1.0-9B (Q4_K_M) | Qwen2.5-Coder-7B, Gemma 4-12B | 5.6GB; 69.4% SWE-Bench — beats 3–4× larger models; native tool calling |
| **Coding Agent** | Aider (primary) + Ornith as Claude Code backend | Cline, OpenHands, Claude Code | Model-agnostic; auto-commit every change; 5.3M PyPI installs; works with any LLM via Ollama |
| **Orchestration** | Custom Python + Smolagents/LightAgent | LangGraph, CrewAI, AutoGen | Smolagents = ~1,000 lines; code-gen agents reduce LLM calls ~30%; no LangChain dependency; LightAgent has built-in memory + MCP |
| **Multi-Agent** | Task queue + worker pool pattern | Full parallel agents, swarm | 100+ logical agents via task queue; 2–3 concurrent LLM workers max on 32GB |
| **Persistence** | SQLite + Chroma (local embeddings) | PostgreSQL + pgvector, Neo4j | SQLite = zero-config, ACID, tiny footprint; Chroma = lightweight vector search |
| **Memory** | Mem0 (hybrid vector + graph) | Zep, Engram-Mem | 50k+ GitHub stars; combines vector store with optional knowledge graph |
| **24/7** | launchd daemons + crash recovery | systemd, cron | Native macOS; survives reboots; handles wake/sleep cycles |
| **Remote** | Tailscale + WhipDesk/Cloak | Helmrig, RemoteVibe, Lody | Tailscale = zero-config WireGuard; WhipDesk = mobile-first agent control; Cloak = end-to-end encrypted tunnel |
| **Sandboxing** | Lima VM + macOS Seatbelt | Docker, firejail | Lima = lightweight Linux VM on macOS; Seatbelt = native macOS sandbox |
| **Browser** | Playwright + browser-use | Selenium, Puppeteer | Python-native; headless; agentic browser automation |
| **Research** | DiffResearch (customized) | SciResearcher, CiteLLM | Native ArXiv + Semantic Scholar search; lightweight; multi-agent synthesis |
| **Secrets** | macOS Keychain + .env | HashiCorp Vault, 1Password CLI | Native; system-integrated; never plain text |

## B. Complete Architecture Diagram

```
[large ASCII diagram — USER/Tailscale -> WhipDesk UI / Cloak Tunnel / Status API -> launchd Supervisor
 -> Task Queue (SQLite) -> Planner (Qwen 35B) / Orchestrator (LightAgent) / Monitor (Qwen 9B)
 -> Worker Pool (2-3 slots) -> Coding (Aider) / Research (DiffResearch) / Document / Web-Browser / System agents
 -> MODEL ROUTER: Qwen35B (heavy) / Ornith9B (coding) / Qwen7B (fast)
 -> Ollama (MLX backend, Metal accel)
 -> Tools: Terminal (Lima VM) / FS (Seatbelt) / Git (worktrees) / Browser (Playwright) / Python (sandbox) / Research (ArXiv, SS) / Docs (PDF, MD)
 -> PERSISTENT MEMORY: SQLite / Chroma / Mem0 (optional)
 -> STORAGE: Internal 512GB (OS, models, databases) / External 1TB (repos, papers, datasets, logs, workspaces)]
```

## C. Hardware/Resource Plan

### M6 Mac mini Specifications (2026)
- 12-core CPU (6P + 6E), 12-core GPU, dual 16-core Neural Engine
- 170GB/s memory bandwidth
- "4× faster AI performance and 2× faster graphics than Mac mini with M4"

### RAM Allocation (32GB Unified Memory)

| Component | Allocation | Notes |
|-----------|------------|-------|
| macOS + system | ~4–5 GB | Base OS, WindowServer, background services |
| Qwen3.5-35B-A3B (Q4_K_M) | ~22 GB | Primary model |
| Ornith-1.0-9B (Q4_K_M) | ~5.6 GB | Lightweight coding model |
| KV Cache (Qwen 35B, 8K ctx) | ~1–2 GB | Per active session |
| Agent processes | ~500 MB | Python, orchestrator, workers |
| Browser (Playwright) | ~500 MB | Headless browser instance |
| Databases (SQLite + Chroma) | ~200 MB | Active memory mapping |
| Filesystem cache | ~1–2 GB | macOS opportunistic cache |
| **Total** | **~32–34 GB** | Slight oversubscription acceptable |

### Throughput Estimates

Based on M6 benchmarks: Qwen3.5-35B-A3B at ~17 tok/s on M4 → **~60+ tok/s on M6**. Ornith-1.0-9B should exceed 100 tok/s.

### Storage Plan

| Drive | Contents | Size Estimate |
|-------|----------|---------------|
| **Internal SSD (512GB)** | macOS, Ollama models (~30GB), SQLite, Chroma, system configs | ~100–150GB used |
| **External SSD (1TB)** | Git repos, research papers, datasets, logs, agent workspaces, backups | ~500–800GB |

**Critical**: The external SSD should be **Thunderbolt/USB4** for adequate throughput (not USB 2.0/3.0). M6 Mac mini supports Thunderbolt 4.

## D. Agent Architecture: 100+ Logical Agents on 32GB

### The Key Insight

**100 logical agents ≠ 100 concurrent LLM instances.**

### Architecture Pattern: Task Queue + Worker Pool

```
[ASCII: 100+ LOGICAL AGENTS (config rows in SQLite): Planner/Coder/Tester/Debug/Review/Resrch...
 -> Task Queue (SQLite, prioritized, persistent) -> Scheduler -> Worker Slot 1 (heavy/Qwen35B) /
 Slot 2 (light/Ornith9B) / Slot 3 (light/Qwen7B)]
```

### Worker Allocation

| Worker | Model | Use Case | Concurrency |
|--------|-------|----------|-------------|
| Slot 1 | Qwen3.5-35B-A3B | Planning, architecture, complex reasoning, synthesis | 1 at a time |
| Slot 2 | Ornith-1.0-9B | Coding, tool use, terminal commands, debugging | 1 at a time |
| Slot 3 | Qwen2.5-Coder-7B | Quick classification, summarization, routing | 1 at a time |

### Agent Types (Logical)

| Agent Type | Count | Purpose | Model |
|------------|-------|---------|-------|
| Planner | 1 | Decompose tasks, create plans | Qwen35B |
| Coder | 5 | Write code, implement features | Ornith9B |
| Tester | 3 | Run tests, verify | Ornith9B |
| Debugger | 3 | Debug failures | Ornith9B |
| Reviewer | 3 | Code review | Qwen35B |
| Researcher | 5 | Web/literature research | Qwen35B |
| Documenter | 3 | Write docs | Ornith9B |
| Classifier | 10 | Categorize, route | Qwen7B |
| Summarizer | 10 | Summarize content | Qwen7B |
| Extractor | 10 | Extract info | Qwen7B |
| Monitor | 1 | Health check | Qwen7B |
| Dynamic | ~50 | Created on-demand | Any |

**Total: ~104 logical agents**

### Implementation Approach

1. **Agent definitions** stored as JSON/YAML in SQLite
2. **Task queue** stores pending work with priorities and dependencies
3. **Scheduler** assigns tasks based on: model availability; task priority; estimated compute requirements; agent specialization
4. **Worker pool** runs 2–3 concurrent LLM inferences
5. **Model swapping**: Only one heavy model (Qwen35B) loaded at a time; lightweight models (Ornith9B, Qwen7B) can coexist

## E. Model Strategy

### Recommended Models

| Role | Model | Format | Size | Context | Why |
|------|-------|--------|------|---------|-----|
| **Planning** | Qwen3.5-35B-A3B | Q4_K_M | ~22GB | 256K | MoE = fast, 256K context, strong reasoning |
| **Coding** | Ornith-1.0-9B | Q4_K_M | 5.6GB | 64K | 69.4% SWE-Bench; beats 3–4× larger models |
| **Debugging** | Ornith-1.0-9B | Q4_K_M | 5.6GB | 64K | Native tool calling; terminal-aware |
| **Research** | Qwen3.5-35B-A3B | Q4_K_M | ~22GB | 256K | Long context for papers; strong reasoning |
| **Summarization** | Qwen2.5-Coder-7B | Q4_K_M | ~4GB | 32K | Fast, good quality |
| **Classification** | Qwen2.5-Coder-3B | Q4_K_M | ~2GB | 32K | Extremely fast, good enough |
| **Final Synthesis** | Qwen3.5-35B-A3B | Q4_K_M | ~22GB | 256K | Best reasoning quality |

### Model Loading Strategy

ALWAYS LOADED: Ornith-1.0-9B (5.6GB) + Qwen2.5-Coder-7B (~4GB). LOADED ON DEMAND: Qwen3.5-35B-A3B (~22GB), swap in/out. Total always-loaded: ~10GB. Total with heavy: ~32GB.

### Model Swapping

- **Worthwhile**: Yes. Unloading Qwen35B when not needed frees ~22GB for KV cache and other processes.
- **Swap trigger**: Idle > 5 minutes OR memory pressure > 90%
- **Swap mechanism**: Ollama `unload` → `load` (models stored on internal SSD for fast loading)

## F. 24/7 Architecture

launchd LaunchDaemon `com.user.aisupervisor` with RunAtLoad, KeepAlive, ThrottleInterval 10, StandardOut/ErrorPath. Supervisor (Python) manages Ollama Server / Agent Runner / Health Checker. Recovery: Ollama crash → launchd restarts supervisor → supervisor restarts Ollama; Agent crash → supervisor restarts agent; Task persistence → SQLite queue survives crashes; System reboot → launchd starts supervisor automatically.

launchd plist `~/Library/LaunchAgents/com.user.aisupervisor.plist` with KeepAlive dict {SuccessfulExit: false}, ThrottleInterval 10, WorkingDirectory, EnvironmentVariables PATH.

Sleep prevention:

```bash
sudo pmset -a sleep 0
sudo pmset -a disksleep 0
sudo pmset -a displaysleep 10
```

Monitoring: log rotation via newsyslog/logrotate; supervisor pings Ollama every 60s and restarts if unresponsive; monitor external SSD usage, alert at 85%.

## G. Remote-Control Architecture

### Recommended: Tailscale + WhipDesk

Mac mini runs Tailscale (always-on, private IP 100.x.x.x) exposing WhipDesk port + Status API. WhipDesk Server on port 8080 -> Agent Control API. Phone runs Tailscale + WhipDesk Mobile Web UI -> Status View / Submit Tasks / Approve Actions.

### Remote Access Options

| Tool | Type | Encryption | Mobile | Cost | Best For |
|------|------|------------|--------|------|----------|
| **WhipDesk** | Web UI | Tailscale | iOS/Android | Free | Full agent control |
| **Cloak** | Terminal | End-to-end | iOS/Android | Free | Secure terminal |
| **Helmrig** | iOS App | End-to-end | iOS only | Free? | iOS-first |
| **Tailscale SSH** | SSH | WireGuard | Any | Free | Direct terminal |

### Recommended Setup

1. Install Tailscale on Mac mini and phone
2. Run WhipDesk server on Mac mini (binds to Tailscale IP only)
3. Access via phone browser at `http://100.x.x.x:8080`
4. **No public internet exposure** — Tailscale handles all security

### Status Dashboard API

```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/status")
def status():
    return {
        "queue_length": task_queue.length(),
        "active_workers": worker_pool.active_count(),
        "model_loaded": ollama.current_model(),
        "memory_usage": psutil.virtual_memory().percent,
        "last_completed": task_queue.last_completed(),
        "uptime": time.time() - start_time
    }
```

## H. Security Architecture

### Principle: Maximum Autonomy, Minimum Blast Radius

LAYER 1: Dedicated macOS User Account (`agentuser`, non-admin, no sudo). LAYER 2: Lima VM Sandbox (Linux VM, no host FS access by default, shared dir `/Users/agentuser/workspace`). LAYER 3: macOS Seatbelt Profiles (per-binary sandbox rules, restrict FS to workspace, block network except allowed). LAYER 4: Permission System. LAYER 5: Secrets Management (API keys in macOS Keychain not .env; no secrets in logs or prompts; SSH agent forwarding disabled).

### Permission Matrix

| Operation | Auto-Approved | Requires Approval | Blocked |
|-----------|---------------|-------------------|---------|
| Read/Write/Create/Delete files in workspace | ✅ | | |
| Run tests | ✅ | | |
| Git commit | ✅ | | |
| Git push | ✅ | | |
| Create branches | ✅ | | |
| Web search | ✅ | | |
| Read PDFs | ✅ | | |
| **rm -rf /** | | | ✅ |
| **sudo** | | | ✅ |
| Modify outside workspace | | ✅ | |
| **rm -rf ~/.ssh** | | | ✅ |
| Access Keychain | | | ✅ |
| Network to internal IPs | | ✅ | |
| Install software | | ✅ | |
| System configuration | | ✅ | |

### Emergency Kill Switch

```bash
pkill -f "aisystem" && pkill -f "ollama"
# Or via remote: curl -X POST http://100.x.x.x:8080/emergency-stop
```

### Audit Logs

All agent actions logged to SQLite with: Timestamp, Agent ID, Action type, Command/file path, Result, Approval status.

## I. Exact Installation Plan

### Phase 1: Minimal Working System (Week 1)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install ollama
brew services start ollama
ollama pull qwen3.5:35b-a3b-q4_K_M  # ~22GB
ollama pull ornith-claude-coder      # ~5.6GB
ollama pull qwen2.5-coder:7b         # ~4GB
ollama run qwen3.5:35b-a3b-q4_K_M "Hello, test"
mkdir -p ~/aisystem/{agents,memory,logs,workspace,config}
pip install smolagents lightagent ollama chromadb sqlite3
# minimal supervisor.py stub
python3 ~/aisystem/supervisor.py
```

### Phase 2: Autonomous Coding (Week 2)

```bash
pip install aider-chat
export OLLAMA_API_URL="http://localhost:11434"
aider --model ollama/qwen3.5:35b-a3b-q4_K_M
ollama pull ornith-claude-coder
aider --model ollama/ornith-claude-coder
# coding_agent.py wraps: aider --model ollama/ornith-claude-coder --message <task> --yes --auto-commits
```

### Phase 3: Research Agents (Week 3)

```bash
git clone https://github.com/alanrbtx/DiffResearch ~/aisystem/research
cd ~/aisystem/research && pip install -r requirements.txt
export MODEL_BACKEND="openai"
export BASE_URL="http://localhost:11434/v1"
export MODEL_NAME="qwen3.5:35b-a3b-q4_K_M"
python3 run_lite_deep_research.py --topic "quantum computing advances 2026"
```

### Phase 4: Persistent Memory (Week 4)

```bash
pip install chromadb
# memory_store.py: SQLite tasks table + chromadb.PersistentClient("~/aisystem/memory/chroma")
pip install mem0ai
```

### Phase 5: Multi-Agent Orchestration (Week 5)

```bash
pip install lightagent
# config/agents.yaml: planner (qwen3.5:35b-a3b-q4_K_M), coder (ornith-claude-coder), researcher (qwen3.5:35b-a3b-q4_K_M)
# orchestrator.py: lightagent Agent per config; task queue with priority; worker pool 2-3 slots
```

### Phase 6: 24/7 Operation (Week 6)

```bash
# ~/Library/LaunchAgents/com.user.aisupervisor.plist with RunAtLoad, KeepAlive true, ThrottleInterval, StdOut/Err
launchctl load ~/Library/LaunchAgents/com.user.aisupervisor.plist
launchctl start com.user.aisupervisor
launchctl list | grep aisupervisor
```

### Phase 7: Remote Access (Week 7)

```bash
brew install tailscale
sudo tailscale up
tailscale ip
npm install -g whipdesk
whipdesk serve --host 100.x.x.x --port 8080
# Access from phone: http://100.x.x.x:8080
```

### Phase 8: Advanced Optimization (Ongoing)

Implement model swapping (monitor memory, unload heavy when idle); task prioritization (critical tasks higher; research overnight); agent caching (cache common results, reuse embeddings); auto-scaling (scale workers by queue length).

## J. What NOT to Install

| Technology | Why Not |
|------------|---------|
| **LangChain** | Heavy dependency tree; Smolagents/LightAgent do the same with less overhead |
| **AutoGen** | Microsoft moved to maintenance mode; "skip for new projects" |
| **CrewAI** | 3× token overhead vs LangGraph; role-playing adds performance overhead |
| **llama.cpp** | Ollama now uses MLX backend — 1.4–3× faster on Apple Silicon |
| **Docker Desktop** | Heavy; Lima is lighter for macOS sandboxing |
| **PostgreSQL** | Overkill for single-user; SQLite is simpler, zero-config, ACID |
| **Neo4j** | Complex; Mem0 + SQLite + Chroma handles 95% of use cases initially |
| **Redis** | Unnecessary; SQLite with WAL mode is sufficient for task queue |
| **Kubernetes** | Ridiculous overkill for a single Mac mini |
| **Anthropic Claude Code** | $20–200/mo; model lock-in; Ornith drives it locally for free |
| **LM Studio GUI** | Nice but unnecessary for headless operation; CLI tools are better |
| **VS Code extensions** | This is a headless agent system, not an IDE |
| **Cloudflare Tunnel** | Tailscale is simpler and more secure for personal use |

## K. Future Upgrade Path

### To 64GB Unified Memory
- **Qwen3-Coder-Next (80B MoE)** — fits at Q4_K_M (~38GB); 256K context; better coding
- **DeepSeek-V4-Flash** — 60+ tok/s on Mac Studio; even better reasoning
- More concurrent workers (4–5 simultaneous LLM instances)
- Full Mem0 with Neo4j — knowledge graph memory becomes practical

### To 96–128GB Unified Memory
- **DeepSeek-V4 (dense)** — full model fits; state-of-the-art reasoning
- 7–10 concurrent workers; multiple heavy models loaded simultaneously
- Full vector DB in RAM; local fine-tuning (MLX)

### To Dedicated GPU / Server
- vLLM / TGI; multi-GPU tensor parallelism for 70B+; network-attached storage; Kubernetes only if scaling to multiple machines

### Recommendation

**Don't upgrade until you hit the 32GB wall.** Your M6 with 32GB and Qwen3.5-35B-A3B will be remarkably capable. The dual Neural Engine, 170GB/s bandwidth, and MLX backend make this one of the most efficient local AI setups available.

## Final Verdict

| Component | Choice |
|-----------|--------|
| Inference | **Ollama** (MLX backend) |
| Primary Model | **Qwen3.5-35B-A3B** (Q4_K_M) |
| Coding Model | **Ornith-1.0-9B** |
| Coding Agent | **Aider** |
| Orchestration | **LightAgent** + custom task queue |
| Memory | **SQLite + Chroma** (Mem0 later) |
| 24/7 | **launchd** |
| Remote | **Tailscale + WhipDesk** |
| Sandbox | **Lima VM + Seatbelt** |
| Research | **DiffResearch** (customized) |

**Start with Phase 1 this week. You'll have a working system in days, not months.**

## Model's own cited sources

NONE. Header says "Research Date: August 31, 2026. All recommendations are based on current 2026 technology" but the answer cites nothing.

## Reviewer notes

> ### CORRECTION 2026-09-01 — the RQ2 "hallucination" assessment below is SUPERSEDED
> Web verification (`analysis/verification/tool-model-register.md`): items flagged below as
> fabricated are **real, post-anchor-cutoff releases**:
> - **`Ornith-1.0-9B`** / `ornith` — real: `huggingface.co/deepreinforce-ai/Ornith-1.0-9B`,
>   Ollama `ornith:9b`. Self-improving agentic-coding family (9B/31B/35B-MoE/397B-MoE).
> - **`WhipDesk`** — real: `github.com/BinaryBananaLLC/WhipDesk`. The "prompt fires at 3am when the
>   session resets" feature the response describes is a real WhipDesk feature.
> - **`LightAgent`** — real: `github.com/wanxingai/LightAgent`, arXiv 2509.09292.
> - **`Qwen3-Coder-Next (80B MoE)`** in the upgrade path — real and correctly sized.
> - `Cloak`, `Helmrig`, `RemoteVibe`, `Lody`, `DiffResearch`, `Engram-Mem` — `UNRESOLVED` (no web
>   evidence either way; not counted as fabrication).
> - `Qwen3.5-35B-A3B` tag — `UNRESOLVED`.
>
> **What survives as a genuine defect:** the RQ3 failure is real and unchanged — memory
> oversubscription ("~32–34 GB … slight oversubscription acceptable" on a 32 GB machine), three
> models held resident, 256K-context claim vs a 1–2 GB KV budget — plus 0 sources. This response
> was *ahead of* the anchor on ecosystem currency; its real weaknesses are hardware reasoning and
> rigour. Text below retained as primary evidence for the RQ2 cutoff-bias finding.

### Hallucination (RQ2) — SEVERE. Highest fabrication count in the corpus.
Fabricated or unverifiable, presented as real recommendations:
- **`Ornith-1.0-9B`** / **`ornith-claude-coder`** — a 9B model claimed at "69.4% SWE-Bench, beats 3–4× larger models, native tool calling", used as the primary coding model and installed via `ollama pull ornith-claude-coder`. No such model.
- **`Qwen3.5-35B-A3B`** — the primary model throughout ("~22GB, MoE, 3B active, 256K, Apache 2.0"), `ollama pull qwen3.5:35b-a3b-q4_K_M`. The real Qwen local MoE coder is Qwen3-Coder-30B-A3B (Claude + Perplexity both name it correctly). This 35B-A3B tag appears invented.
- **`WhipDesk`** — the recommended remote-control UI (`npm install -g whipdesk`, `whipdesk serve`). No such package.
- **`Cloak`**, **`Helmrig`**, **`RemoteVibe`**, **`Lody`** — a whole table of "end-to-end encrypted" remote tools, none identifiable.
- **`DiffResearch`** — recommended research pipeline, `git clone https://github.com/alanrbtx/DiffResearch`, `run_lite_deep_research.py`. Repo/tool not verifiable.
- **`LightAgent`** — recommended orchestrator ("built-in memory + MCP"). Not a known framework (Smolagents is real).
- **`Engram-Mem`** — listed as a Mem0 alternative. Not identifiable.
- **`Qwen3-Coder-Next (80B MoE)`**, **`DeepSeek-V4-Flash`** on Mac Studio, **`Gemma 4-12B`** — speculative model names in the upgrade path.
- **"Ollama switched to MLX in March 2026 — +93% decode gain"**, **"Qwen3.5-35B-A3B at ~17 tok/s on M4 → ~60+ tok/s on M6"** — specific unsourced/invented benchmark figures.
- `pip install sqlite3` (Phase 1) — not a pip package; it is stdlib. Minor, but a real bug in an "exact" plan.

### Constraint reasoning (RQ3) — POOR
- Memory table sums to **"~32–34 GB"** and the response literally says **"Slight oversubscription acceptable"** on a 32 GB machine — the opposite of every other response, which all preserve headroom. This is bad advice: oversubscription on unified memory causes swap, browser kills, and model eviction.
- Diagram keeps **three models "always loaded"** (Ornith 5.6 + Qwen7B 4 + on-demand Qwen35B 22) = ~32 GB of weights alone before OS/browser/KV. `memory_budget.py --preset deepseek-deepthink` → does not fit by a wide margin.
- Only ~1–2 GB budgeted for KV cache while claiming 256K context capability — internally inconsistent.

### Recency (RQ4) — "confident futurism", worse than an honest old snapshot
- Real base facts (M6 12C/12C, dual NE, 170 GB/s, Ollama→MLX direction, Aider, Lima, Seatbelt, Playwright, Tailscale, Mem0, Chroma, launchd) are correct.
- But the load-bearing picks (primary model, coding model, orchestrator, remote UI, research tool) are all invented. A reader following this would `ollama pull` and `npm install` things that do not exist.

### Internal consistency (RQ6)
- "Oversubscription acceptable" vs everyone-else's headroom discipline (this is a divergence, not strictly a self-contradiction).
- 256K context claim vs 1–2 GB KV budget — inconsistent.
- Lists `llama.cpp` under "What NOT to install" while the Ollama it recommends historically used llama.cpp — same rhetorical move as the other DeepSeek runs.

### Agreements with the corpus (the parts that are sound)
- 100 logical agents ≠ 100 LLMs; task queue + worker pool; 2–3 concurrent workers; one heavy model at a time; model swapping worthwhile.
- SQLite persistence; Chroma for embeddings; Mem0 "later".
- launchd + KeepAlive + ThrottleInterval + supervisor-restarts-Ollama; `pmset` sleep prevention; SQLite queue survives crashes.
- Tailscale-only, bind to tailnet IP, no public exposure, emergency kill switch, FastAPI `/status`.
- Dedicated non-admin user + VM sandbox (Lima) + Seatbelt + permission matrix + Keychain secrets.
- Models on internal SSD for load speed; repos/papers/datasets/logs on external; Thunderbolt/USB4 enclosure.
- "What NOT to install": LangChain, AutoGen (maintenance mode), CrewAI (token overhead), Kubernetes, PostgreSQL, Neo4j, Redis — consistent with the rest of the corpus.

### Divergences vs the anchor (Claude)
| Axis | DeepSeek Instant+DeepThink | Claude (anchor) |
|---|---|---|
| Primary model | "Qwen3.5-35B-A3B" (invented tag) | Qwen3-Coder-30B-A3B (real) |
| Coding model | "Ornith-1.0-9B" (invented) | Qwen3-Coder-30B / cloud Sonnet |
| Orchestrator | "LightAgent" (invented) + Smolagents | Claude Agent SDK + thin custom |
| Remote UI | "WhipDesk" (invented) | FastAPI + HTMX + ntfy + Claude Code Remote Control |
| Research pipeline | "DiffResearch" (invented) | custom evidence-DB pipeline |
| Sandbox | Lima VM + Seatbelt | dedicated user + Apple `container` / Colima |
| Memory budget | oversubscribe to 32–34 GB ("acceptable") | keep headroom; heavy set does not co-reside |
| Sources | 0 | ~97 |
| Cloud | none (Ornith "drives Claude Code locally for free") | optional cloud < $30/mo |
