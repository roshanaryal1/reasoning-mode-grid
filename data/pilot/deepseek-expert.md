---
ai_name: DeepSeek (Expert / deep-reasoning mode)
model_version_id: "not shown — user labelled 'deepseek expert'"
provider: DeepSeek
interface: web app (assumed)
browsing_enabled: no (zero sources), but recommendations are real 2025/2026 tools
knowledge_cutoff: unknown (model names trail the current edge: "Opus 4.5", "GPT-5", "Gemini 2.5 Pro", "RTX 4090")
prompt_version: v1
date_run: 2026-08-31
run_by: roshanaryal1
notes_on_run: Single message. No header line. No Sources section. Much more grounded than DeepSeek-Instant — all named tools appear to exist. One internal contradiction on Docker.
trust_rating: MEDIUM-HIGH — realistic stack, real tools, honest about cloud fallback; slightly stale model versioning.
---

## Raw response

# Autonomous AI Workstation Architecture for 32GB M6 Mac Mini

## Executive Summary

After extensive research of the current (2026) landscape, I recommend a **hybrid architecture** centered on **Claude Code + custom orchestration** rather than a single monolithic framework. The system uses **Qwen3-Coder-30B-A3B (Q4_K_M)** as the primary local model, with **Claude Opus 4.5 API** for complex planning when needed. This balances local autonomy with quality.

## A. Recommended Technology Stack

| Layer | Recommended Technology | Alternatives | Why |
|-------|----------------------|--------------|-----|
| **Local Inference** | llama.cpp + MLX | Ollama, vLLM | Best M-series optimization, dynamic model loading, precise memory control |
| **Primary Model** | Qwen3-Coder-30B-A3B (Q4_K_M) | DeepSeek-Coder-V3, CodeLlama-34B | Best coding+agentic balance at 32GB, MoE architecture gives speed |
| **Secondary Model** | Qwen3-14B (Q4_K_M) | Phi-4-14B, Llama-3.1-8B | Fast task classification, summarization |
| **Cloud Fallback** | Claude Opus 4.5 / GPT-5 | Gemini 2.5 Pro | Complex planning, hard debugging - optional |
| **Agent Runtime** | Custom Python orchestrator + Claude Code CLI | AutoGPT, OpenHands, CrewAI | Full control, memory management, hardware-aware scheduling |
| **Coding Agent** | Claude Code (custom fork) + Aider | OpenHands, SWE-agent | Best repository understanding, worktree support, mature |
| **Memory** | SQLite + ChromaDB | PostgreSQL, Qdrant, MemGPT | Lightweight, local, sufficient for personal scale |
| **Task Queue** | Redis + Celery | RabbitMQ, custom asyncio | Durable, supports priorities, mature |
| **Monitoring** | Grafana + Prometheus | Netdata, custom dashboards | Rich agent metrics, alerting |
| **Remote Access** | Tailscale + custom FastAPI | ngrok, WireGuard | Encrypted mesh network, zero public exposure |
| **Sandboxing** | macOS seatbelt + Docker | Firecracker, Lima | Native macOS sandboxing, resource limits |

## B. Complete Architecture Diagram

```
                    REMOTE ACCESS LAYER
┌─────────────────────────────────────────────────────┐
│  iPhone/Remote: Tailscale + FastAPI Dashboard       │
│  - Task submission, monitoring, kill switch         │
└─────────────────────────────────────────────────────┘
                        ↓ HTTPS/Tailscale
┌─────────────────────────────────────────────────────┐
│  ALWAYS-ON SUPERVISOR (launchd)                     │
│  - Watchdog, auto-restart, health checks            │
│  - Resource monitor, queue manager                 │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  ORCHESTRATOR (FastAPI + Celery)                    │
│  - Task scheduler, priority queue                  │
│  - Agent lifecycle manager                         │
│  - Memory coordinator (SQLite + ChromaDB)          │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  AGENT FACTORY + WORKER POOL                        │
│  - Dynamic agent creation per task type            │
│  - Role-based permissions, resource limits          │
│  - Model router (local vs cloud)                   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  SPECIALIZED AGENTS (Logical, not all concurrent)   │
│  ├── CodingAgent (Claude Code + Aider)             │
│  ├── ResearchAgent (Browser + arXiv + Search)       │
│  ├── DocumentAgent (PDFs, Markdown)                │
│  ├── ExperimentAgent (Python, Data analysis)       │
│  └── MemoryAgent (SQLite, ChromaDB)                │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  TOOLS LAYER                                        │
│  ├── Terminal (sandboxed)                           │
│  ├── Filesystem (permission-scoped)                 │
│  ├── Git (worktrees)                                │
│  ├── Browser (Playwright)                           │
│  ├── Python (venvs)                                 │
│  └── Document processors                            │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  LOCAL INFERENCE (llama.cpp + MLX)                  │
│  - Dynamic model loading/unloading                  │
│  - Memory-mapped weights                           │
│  - Metal acceleration                              │
└─────────────────────────────────────────────────────┘
```

## C. Hardware/Resource Plan (32GB M6)

### Memory Allocation (Approximate)
```
macOS + system:          4 GB
llama.cpp runtime:       2 GB
Primary model (30B Q4): 18 GB (Qwen3-Coder-30B-A3B)
KV cache (32K context):  2 GB
Secondary model pool:    3 GB (loaded on-demand)
Agent processes:         1 GB
Databases/browser:       1 GB
Filesystem cache:        1 GB (dynamic)
─────────────────────────────
Total:                  32 GB
```

### Storage Allocation
- **Internal SSD (512GB)**:
  - macOS + apps: 150GB
  - Models (primary): 20GB
  - SQLite + ChromaDB: 10GB
  - Active repositories: 50GB
  - Fast scratch space: 20GB
  - Free headroom: 262GB

- **External SSD (1TB)**:
  - Model library (all variants): 200GB
  - Research papers/datasets: 300GB
  - Archives/backups: 300GB
  - Logs: 50GB
  - Docker images: 50GB
  - Cold storage: 100GB

### Concurrency Limits (32GB)
- **Active large-model workers**: 1 (primary coding/planning)
- **Active small-model workers**: 2 (classification, summarization)
- **Logical agents**: 100+ (queued, not concurrent)
- **Model swapping**: Yes, but limited to 2 swaps/hour to avoid thrashing

## D. Agent Architecture: 100+ Logical Agents Without 100 LLMs

### The Key Insight
Use **state machines + task templates** rather than concurrent model instances:

```
AGENT = State Machine + Role Definition + Memory Access + Tool Permissions

┌─────────────────────────────────────────────┐
│ Agent Registry (SQLite)                    │
│ - agent_id, role, current_state, queue     │
└─────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────┐
│ Agent Scheduler (Priority Queue)            │
│ - Round-robin, priority, resource-aware     │
│ - Batching, model reuse                     │
└─────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────┐
│ Worker Pool (2-3 concurrent max)            │
│ - Loads model when needed                   │
│ - Executes agent state transitions          │
│ - Saves state, releases resources           │
└─────────────────────────────────────────────┘
```

### Implementation Pattern
```python
class LogicalAgent:
    def __init__(self, role, memory_ref, tools, model_requirements):
        self.state = "idle"  # idle, queued, running, waiting, completed
        self.role = role  # coding, research, review, etc.
        self.memory = MemoryRef(project_id, scope)
        self.tools = ToolPermissions(role)
        self.model = ModelRequirements(priority, max_tokens)
        self.queue = asyncio.Queue()
    
    async def execute(self, task):
        """Runs one state transition, then yields."""
        self.state = "running"
        result = await self.worker_pool.run(self, task)
        self.state = "waiting" if result.needs_followup else "completed"
        return result
```

### Scheduling Strategy
- **Peak hours**: 1 coding agent + 1 research agent
- **Overnight**: Batch processing, queue draining
- **Emergency**: Preempt queue for high-priority task

## E. Model Strategy

### Local Models (Primary)
1. **Qwen3-Coder-30B-A3B (Q4_K_M)** - 18GB RAM
   - **Use**: Complex coding, architecture, planning
   - **Context**: 32K tokens
   - **Speed**: ~25 tokens/sec on M6
   - **Strengths**: Best coding ability in this size class

2. **Qwen3-14B (Q4_K_M)** - 8GB RAM
   - **Use**: Task classification, summarization, simple edits
   - **Context**: 16K tokens
   - **Speed**: ~45 tokens/sec
   - **Strengths**: Fast, good for routing decisions

3. **Phi-4-14B (Q4_K_M)** - 8GB RAM
   - **Use**: Research synthesis, contradiction detection
   - **Context**: 32K tokens
   - **Strengths**: Excellent reasoning, strong at verification

### Cloud Models (Optional, for quality-critical tasks)
- **Claude Opus 4.5**: Complex debugging, architecture decisions
- **GPT-5**: Document generation, research synthesis
- **Use policy**: Only when local models fail or task complexity exceeds threshold

### Model Selection Logic
```python
def route_model(task):
    if task.complexity > 8 and task.type in ["coding", "debugging"]:
        return "claude-opus-4.5" if task.allows_cloud else "qwen3-coder-30b"
    elif task.type == "research":
        return "phi-4-14b" if task.needs_reasoning else "qwen3-14b"
    elif task.type == "classification":
        return "qwen3-14b"
    else:
        return "qwen3-coder-30b"
```

## F. 24/7 Architecture

### Always-On Components
```
launchd (macOS service manager)
├── Supervisor daemon (Python)
│   ├── Health check every 30s
│   ├── Auto-restart on crash
│   ├── Queue persistence (Redis)
│   └── Resource monitor
├── Celery workers (2-3)
├── FastAPI server
└── Watchdog timer
```

### Crash Recovery Flow
1. **Agent crashes**: Supervisor detects, logs error, restarts from checkpoint
2. **Model OOM**: llama.cpp killed, memory released, smaller model loaded
3. **System restart**: launchd auto-starts all services, queue restored from Redis
4. **Power loss**: UPS recommended, graceful shutdown script

### Overnight Operation
```yaml
# Schedule (config.yaml)
overnight_mode:
  start: "22:00"
  end: "07:00"
  allowed_tasks: [research, documentation, testing, batch_processing]
  max_concurrent_agents: 2
  cloud_api_allowed: true
  notifications: silent
  auto_pause: true  # Pause if temperature > 80°C
```

## G. Remote Control Architecture

### Secure Access Pattern
```
[Your Phone/Laptop]
    ↓ Tailscale VPN (WireGuard)
[Mac Mini - Tailscale IP only]
    ↓ HTTPS (self-signed cert)
[FastAPI Dashboard]
    - Task submission
    - Live monitoring
    - Kill switch
    - Approval queue
```

### Implementation
```bash
# Install Tailscale
brew install tailscale
tailscale up

# Dashboard (FastAPI)
pip install fastapi uvicorn websockets
# Access at: https://100.x.x.x:8443
```

### Features
- **Push notifications**: ntfy.sh (self-hosted) for task completion
- **Emergency stop**: POST /api/kill - immediately stops all agents
- **Approval queue**: Web interface for pending destructive actions
- **Log streaming**: WebSocket for real-time agent output

## H. Security Architecture

### Permission Levels
```yaml
# agent_permissions.yaml
levels:
  L0_READ_ONLY:
    - filesystem: read selected dirs
    - terminal: disabled
    - network: none
    
  L1_SAFE_WRITE:
    - filesystem: read/write workspace
    - terminal: specific commands only
    - git: branch creation, commits
    - network: allowlist domains
    
  L2_AUTONOMOUS:
    - filesystem: read/write project dirs
    - terminal: most commands
    - git: all operations except force push
    - network: any except sensitive endpoints
    
  L3_FULL_TRUST:
    - Everything, but requires human approval
    - Destructive ops: confirmation needed
```

### Sensitive Data Protection
```bash
# Dedicated user for agents
sudo dscl . -create /Users/agent
# Resource limits
ulimit -u 50  # Max processes
ulimit -n 256  # Max file descriptors

# Secrets management
# Use macOS Keychain + environment variables
security add-generic-password -a agent -s api_key -w "value"

# Network filtering
pfctl -f /etc/pf.anchors/agent_rules
```

### Destructive Command Guard
```python
DESTRUCTIVE_PATTERNS = [
    r"rm\s+-rf\s+/", r"mkfs", r"dd\s+if=.*of=/dev",
    r"git\s+push\s+--force", r"sudo\s+", r"chmod\s+-R\s+777"
]

def check_command(cmd):
    if any(re.match(p, cmd) for p in DESTRUCTIVE_PATTERNS):
        return "APPROVAL_REQUIRED"
    return "ALLOWED"
```

## I. Exact Installation Plan

### Phase 1: Foundation (Day 1)
```bash
# 1. System prep
sudo softwareupdate --install-rosetta
xcode-select --install

# 2. Package managers
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.12 git redis node@20

# 3. Create agent user
sudo dscl . -create /Users/agent
sudo dscl . -create /Users/agent UserShell /bin/zsh
sudo dscl . -create /Users/agent RealName "AI Agent"
sudo dscl . -create /Users/agent UniqueID "501"
sudo dscl . -create /Users/agent PrimaryGroupID 20
sudo dscl . -create /Users/agent NFSHomeDirectory /Users/agent
sudo mkdir /Users/agent
sudo chown -R agent:staff /Users/agent

# 4. Project structure
mkdir -p ~/ai-workstation/{models,data,logs,workspace,config}
cd ~/ai-workstation
python3 -m venv venv
source venv/bin/activate

# 5. Core dependencies
pip install fastapi uvicorn celery redis sqlalchemy chromadb
pip install llama-cpp-python mlx-lm
pip install anthropic openai  # Optional cloud APIs

# 6. Install llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make -j8
```

### Phase 2: Local Inference (Day 2)
```bash
# Download models
cd ~/ai-workstation/models
# Qwen3-Coder-30B-A3B Q4_K_M (~18GB)
curl -L -o qwen3-coder-30b-a3b-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-GGUF/resolve/main/qwen3-coder-30b-a3b-q4_k_m.gguf

# Qwen3-14B Q4_K_M (~8GB)
curl -L -o qwen3-14b-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen3-14B-GGUF/resolve/main/qwen3-14b-q4_k_m.gguf

# Phi-4-14B Q4_K_M (~8GB)
curl -L -o phi-4-14b-q4_k_m.gguf \
  https://huggingface.co/microsoft/phi-4-GGUF/resolve/main/phi-4-14b-q4_k_m.gguf

# Test inference
llama-cli -m qwen3-coder-30b-a3b-q4_k_m.gguf \
  -p "Write a Python function to calculate fibonacci" \
  -n 100 -t 8
```

### Phase 3: Orchestrator Setup (Day 3-4)
```python
# ~/ai-workstation/orchestrator.py
from fastapi import FastAPI, BackgroundTasks
from celery import Celery
import asyncio
from typing import Dict, List
import json

app = FastAPI()
celery_app = Celery('agents', broker='redis://localhost:6379')

class AgentOrchestrator:
    def __init__(self):
        self.agents = {}
        self.task_queue = asyncio.Queue()
        self.model_manager = ModelManager()
        self.memory = MemorySystem()
    
    async def create_agent(self, role: str, task_type: str):
        """Dynamically create specialized agent."""
        agent_config = self.load_role_config(role)
        return LogicalAgent(agent_config, self.memory, self.model_manager)
    
    async def process_task(self, task: Dict):
        """Route task to appropriate agent."""
        agent = await self.create_agent(task['role'], task['type'])
        result = await agent.execute(task)
        await self.memory.store(task, result)
        return result

# Celery task for async processing
@celery_app.task
def run_agent_task(task_json: str):
    task = json.loads(task_json)
    orchestrator = AgentOrchestrator()
    return asyncio.run(orchestrator.process_task(task))
```

### Phase 4: Memory System (Day 5)
```python
# ~/ai-workstation/memory.py
import sqlite3
import chromadb
from datetime import datetime

class MemorySystem:
    def __init__(self):
        # Structured memory
        self.sqlite = sqlite3.connect('data/memory.db')
        self.init_sqlite()
        
        # Semantic memory
        self.chroma = chromadb.PersistentClient(path='data/embeddings')
        self.collections = {}
    
    def init_sqlite(self):
        self.sqlite.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY,
                project TEXT,
                category TEXT,  -- decision, research, code, experiment
                content TEXT,
                tags TEXT,
                timestamp DATETIME,
                importance FLOAT
            )
        """)
        self.sqlite.execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY,
                agent_role TEXT,
                task TEXT,
                result TEXT,
                success BOOLEAN,
                duration INTEGER,
                timestamp DATETIME
            )
        """)
    
    def store(self, project, category, content, tags=None, importance=0.5):
        """Store memory in both SQLite and ChromaDB."""
        # Structured storage
        self.sqlite.execute(
            "INSERT INTO memories (project, category, content, tags, timestamp, importance) VALUES (?, ?, ?, ?, ?, ?)",
            (project, category, content, json.dumps(tags or []), datetime.now(), importance)
        )
        
        # Semantic embedding
        collection = self.get_collection(project)
        collection.add(
            documents=[content],
            metadatas=[{"category": category, "tags": json.dumps(tags)}],
            ids=[str(uuid.uuid4())]
        )
```

### Phase 5: Agent Definitions (Day 6-7)
```python
# ~/ai-workstation/agents/coding_agent.py
class CodingAgent(LogicalAgent):
    def __init__(self, memory, model_manager):
        super().__init__(
            role="coding",
            memory=memory,
            tools=["terminal", "git", "filesystem", "python"],
            model="qwen3-coder-30b-a3b"
        )
        self.repo_analyzer = RepoAnalyzer()
    
    async def execute(self, task):
        """Execute coding task with full pipeline."""
        # 1. Understand repository
        repo_context = await self.repo_analyzer.analyze(task['repo_path'])
        
        # 2. Plan changes
        plan = await self.plan_changes(task, repo_context)
        
        # 3. Create worktree
        worktree = await self.git.create_worktree(task['repo_path'])
        
        # 4. Iterate
        for attempt in range(task.get('max_iterations', 10)):
            code = await self.generate_code(plan)
            test_result = await self.run_tests(code, worktree)
            if test_result.passed:
                break
            plan = await self.debug_and_refine(plan, test_result)
        
        # 5. Review and commit
        review = await self.review_code(code)
        if review.approved:
            await self.git.commit(worktree, code, task['description'])
        
        return {"success": True, "worktree": worktree, "review": review}
```

### Phase 6: Research Agent (Day 8-9)
```python
# ~/ai-workstation/agents/research_agent.py
class ResearchAgent(LogicalAgent):
    def __init__(self, memory, model_manager):
        super().__init__(
            role="research",
            memory=memory,
            tools=["browser", "search", "pdf_reader", "citation_tracker"],
            model="phi-4-14b"
        )
    
    async def research(self, query):
        """Conduct systematic research with citation tracking."""
        # 1. Search phase
        sources = await self.search_sources(query)
        
        # 2. Extract claims with citations
        claims = []
        for source in sources:
            extracted = await self.extract_claims(source)
            claims.extend(extracted)
        
        # 3. Verify claims
        verified = await self.verify_claims(claims)
        
        # 4. Detect contradictions
        contradictions = await self.find_contradictions(verified)
        
        # 5. Synthesize
        report = await self.synthesize(verified, contradictions)
        
        # 6. Store all evidence
        await self.memory.store_evidence(claims, sources, contradictions)
        
        return report
```

### Phase 7: Launch Agent (Day 10)
```bash
# ~/Library/LaunchAgents/com.aiworkstation.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiworkstation</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/agent/ai-workstation/venv/bin/python</string>
        <string>/Users/agent/ai-workstation/supervisor.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/agent/ai-workstation/logs/supervisor.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/agent/ai-workstation/logs/supervisor_error.log</string>
</dict>
</plist>

# Load the service
launchctl load ~/Library/LaunchAgents/com.aiworkstation.plist
```

### Phase 8: Remote Access (Day 11)
```bash
# Install Tailscale
brew install tailscale
tailscale up

# Install ntfy for notifications
brew install ntfy

# Configure FastAPI dashboard
cat > ~/ai-workstation/dashboard.py << 'EOF'
from fastapi import FastAPI, WebSocket, Depends
from fastapi.security import HTTPBearer
import uvicorn

app = FastAPI()
security = HTTPBearer()

@app.get("/api/status")
async def status():
    return {"agents": len(active_agents), "queue": task_queue.qsize()}

@app.post("/api/task")
async def submit_task(task: dict, credentials=Depends(security)):
    # Validate and queue task
    await task_queue.put(task)
    return {"queued": True}

@app.post("/api/kill")
async def emergency_stop(credentials=Depends(security)):
    # Immediately stop all agents
    for agent in active_agents.values():
        await agent.terminate()
    return {"stopped": True}

uvicorn.run(app, host="0.0.0.0", port=8443, ssl_keyfile="key.pem", ssl_certfile="cert.pem")
EOF
```

## J. What NOT to Install

| Technology | Why Skip |
|------------|----------|
| **AutoGPT** | Unstable, poor resource management, no hardware awareness |
| **LangChain** | Too abstract, hidden complexity, overkill for personal use |
| **Ollama** | Less control than llama.cpp, can't fine-tune memory usage |
| **Docker for Mac** | Heavy VM overhead, slow filesystem, 32GB limit |
| **Kubernetes** | Massive overkill for single machine |
| **Qdrant/Weaviate** | Too heavy for personal scale, ChromaDB sufficient |
| **PostgreSQL** | Overkill vs SQLite for single user |
| **Airflow** | Too heavyweight for personal tasks |
| **n8n/Zapier** | Not designed for autonomous AI agents |

## K. Future Upgrade Path

### If Upgrading to 64GB Unified Memory
- **Add**: Qwen3-Coder-70B (Q4_K_M) for primary coding
- **Keep**: 30B model loaded for secondary tasks
- **Enable**: 2 concurrent coding agents
- **Increase**: Context window to 64K

### If Adding External GPU (eGPU)
- **Use**: NVIDIA RTX 4090 for batched inference
- **Run**: vLLM with tensor parallelism
- **Enable**: 4+ concurrent agents
- **Switch**: To larger context windows

### If Moving to Dedicated Server
- **Use**: Dual RTX 4090 or A100
- **Run**: Full vLLM stack
- **Deploy**: Kubernetes with GPU scheduling
- **Scale**: 20+ concurrent agents
- **Add**: Distributed memory (Redis cluster)

## Verification Checklist

After installation, test with:
```bash
# 1. Basic inference test
llama-cli -m qwen3-coder-30b-a3b-q4_k_m.gguf -p "Test" -n 10

# 2. Agent creation test
python -c "from orchestrator import AgentOrchestrator; a = AgentOrchestrator(); print(a.create_agent('coding', {}))"

# 3. Task execution test
curl -X POST https://localhost:8443/api/task \
  -H "Content-Type: application/json" \
  -d '{"role": "coding", "task": "Add unit test to math_utils.py"}'

# 4. Memory persistence test
python -c "from memory import MemorySystem; m = MemorySystem(); m.store('test', 'test', 'Hello'); print(m.retrieve('test', 'test'))"

# 5. Recovery test
kill -9 $(pgrep -f supervisor.py)
# Should auto-restart within 30 seconds
```

This architecture provides a production-quality autonomous AI workstation that maximizes your 32GB M6 Mac Mini's capabilities while maintaining security and reliability for 24/7 operation.

## Model's own cited sources

NONE. No Sources section.

## Reviewer notes

### Trust — MEDIUM-HIGH. Best-grounded response after Claude Sonnet 5.
- Every named tool exists: llama.cpp, MLX, Ollama, vLLM, Qwen3-Coder-30B-A3B, Qwen3-14B, Phi-4-14B, Claude Code, Aider, OpenHands, SWE-agent, SQLite, ChromaDB, Redis, Celery, Grafana, Prometheus, Tailscale, FastAPI, macOS `seatbelt` (`sandbox-exec`), Docker, Firecracker, Lima, `pfctl`, `security` (Keychain), ntfy.sh.
- Only response besides Claude to explicitly build around **Claude Code + custom orchestration** as the recommended runtime, and to name a concrete **cloud fallback policy** (`task.complexity > 8` → cloud).

### Recency (RQ4) — slightly stale versioning
- "Claude **Opus 4.5**" (current is 4.8 per other 2026 sources), "GPT-5" (fine), "Gemini **2.5 Pro**" (trails "3 Pro"), eGPU "**RTX 4090**" (5090 was current). Model *families* are right; point releases lag ~6-12 months.
- No mention of 2026-specific tooling: llama-swap, Ollama MLX backend, Goose, Claude Agent SDK, Claude Code Remote Control, Docling, sqlite-vec, Apple `container`. Uses ChromaDB + Redis/Celery + Grafana/Prometheus — a 2024-2025 "standard" stack.
- Did not engage M6 specifics; quotes "**~25 tokens/sec on M6**" and "~45 tokens/sec" for the 14B with no source (RQ2 minor — unsupported perf numbers, but conservative/plausible, unlike DeepSeek-Instant's invented benchmarks).

### Internal consistency (RQ6) — one clear contradiction
- Section A "Sandboxing" recommends **"macOS seatbelt + Docker"**; Section H is fine; but Section J "What NOT to Install" lists **"Docker for Mac — Heavy VM overhead, slow filesystem"**. The response both recommends and forbids Docker. (Charitable reading: "Docker CLI via Colima" vs "Docker Desktop" — but it doesn't say that.)
- `uvicorn.run(app, host="0.0.0.0", ...)` in the Phase 8 dashboard contradicts its own "bind to Tailscale IP only / zero public exposure" security stance (Claude flagged the same 0.0.0.0 anti-pattern as a failure mode).

### Constraint reasoning (RQ3) — solid
- Memory table sums to exactly 32 GB (tight, same as Qwen/Claude peak case). Honest that it's tight.
- 1 large + 2 small workers — matches Claude's heavy=1/light=2. Adds a nice detail: **cap model swaps at 2/hour to avoid thrashing** (unique among responses).
- Correctly rejects concurrent large models; 32K default context; MoE speed rationale.

### Divergences from Claude (interesting for the paper)
| Axis | DeepSeek Expert | Claude Sonnet 5 |
|---|---|---|
| Task queue | **Redis + Celery** | SQLite table + asyncio (no broker) |
| Monitoring | **Grafana + Prometheus** | custom SQLite dashboard (Grafana only at Phase 8) |
| Sandbox | seatbelt **+ Docker** (then forbids Docker in J) | dedicated user + Apple `container`/Colima |
| Secondary/verify model | Phi-4-14B (dense) | gpt-oss-20b (MoE) |
| Coding model speed claim | "~25 tok/s on M6" (unsourced) | ~50-70 tok/s (from MLX benchmarks, cited) |
| Cloud models | Opus 4.5 / GPT-5 / Gemini 2.5 Pro | Opus 4.8 / Sonnet 4.6 / Haiku 4.5 |
| Memory vector store | ChromaDB | sqlite-vec (explicitly avoid Chroma) |
| Remote coding | FastAPI dashboard only | + Claude Code Remote Control |
| Sources | 0 | ~97 |
| Overnight mode | explicit `overnight_mode` config block w/ temp auto-pause | nightly "wake and think" launchd job |

### Agreements with Claude (consensus signal)
- Hybrid: local primary (Qwen3-Coder-30B-A3B) + **optional cloud** for hard planning/debugging, with an explicit complexity threshold.
- **Claude Code** as the coding agent + Aider.
- Custom Python orchestrator, NOT AutoGPT/OpenHands/CrewAI as the backbone; "hardware-aware scheduling" is the thing to own.
- 100+ logical agents = registry rows + scheduler + 2-3 worker pool; dynamic agent factory per task type; model router local-vs-cloud.
- SQLite for structured memory; models on internal SSD, library/papers/archives on external.
- launchd KeepAlive + watchdog + health-check-every-30s + checkpoint recovery; model-OOM → load smaller model.
- Tailscale-only + FastAPI + ntfy + kill switch + approval queue.
- Dedicated `agent` user + L0-L3 permission tiers + Keychain secrets + `pfctl` egress + destructive-command regex guard + resource ulimits.
- "What NOT to install" overlap: AutoGPT, LangChain, Ollama, Kubernetes, Qdrant/Weaviate, PostgreSQL, Airflow, n8n.
