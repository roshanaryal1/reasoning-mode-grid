---
run_id: grok__fast__p1-v1__r2
set: main
family: grok
vendor: xAI
mode: fast
native_label: grok.com, Fast
channel: web
model_requested: xAI chat app, grok.com, Fast
model_returned: not shown (the app shows only the mode; the answer's own header says Grok 4.7)
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 2
date_stamped: '2026-10-14T02:01:52+00:00'
date_run: '2026-10-14T02:01:52+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

**Grok 4.7 | knowledge cutoff mid-2024 (tools used for current research) | browsing/tools enabled**

### Decisions at a glance

| Layer | Recommended | Why for this hardware |
|-------|-------------|-----------------------|
| Inference | Ollama 0.40+ (MLX default) + oMLX for agentic sessions | Best balance of ease, MLX speed, and SSD KV cache persistence on 32 GB M6 |
| Primary model | Qwen3.6-35B-A3B (4-bit / NVFP4) | Strongest practical agentic/coding MoE that fits with usable context; ~64 tok/s measured on M6 32 GB |
| Coding harness | OpenHands (self-hosted, local models) | Mature autonomous loop, sandboxing, Git, tests, browser, local model support |
| Orchestration | Custom lightweight supervisor (Python + SQLite task queue) + OpenHands/Goose workers | Avoids heavy multi-agent frameworks that burn memory |
| Memory | Filesystem + SQLite (+ optional local embeddings) | Minimal, reliable, no extra services initially |
| Remote | Tailscale + SSH + simple status dashboard | No public ports, encrypted, works from phone |
| Always-on | launchd + pmset + dedicated non-admin user | Proven macOS pattern |

---

## 1. Local inference

As of October 2026, community measurements on a 32 GB Mac mini M6 show Qwen 3.6-35B-A3B (MoE, ~3B active) at ~64 tok/s and Gemma 4 26B-A4B at ~48 tok/s (LM Studio, median of three runs). Dense models in the 27–31B class run ~8 tok/s. M6 bandwidth is 170 GB/s on the 32 GB configuration.

**Practical ranking for this machine:**
- **Best overall for agentic work**: Qwen3.6-35B-A3B (Apache 2.0, 262K native context, strong SWE-bench Verified ~73.4, Terminal-Bench 2.0 ~51.5, MCP-Atlas ~62.8).
- **Best dense**: Qwen3.8-27B.
- **Fast routing/summarization**: Qwen3.5-9B or Gemma 4 12B.
- **Avoid** 70B dense or larger MoEs that do not fit cleanly.

Ollama 0.40+ defaults to MLX on Apple Silicon for supported architectures (Qwen 3.x family, Gemma 4, etc.), delivering large gains in decode and especially prefill versus the older Metal/llama.cpp path. oMLX is the stronger choice for long agent sessions because it pages KV cache blocks to SSD, so prefix reuse across tool calls and context shifts is nearly free instead of 30–90 s recomputes.

**Recommendation**: Run Ollama as the primary always-on server (easy model management, OpenAI-compatible API). Use oMLX for heavy coding/research sessions that involve long contexts and frequent tool calls. Quantization: 4-bit / NVFP4. Keep one large model resident; swap only when necessary.

## 2. Agent runtimes / harnesses

OpenHands (formerly OpenDevin) is the strongest mature open-source autonomous coding agent as of October 2026 (~90k+ stars, active releases, SWE-bench Verified results in the 70% range with strong models). It supports local models via LM Studio/Ollama, Docker sandboxing, terminal, browser, Git, multi-agent, and scheduled workflows. Goose is lighter and excellent for general local automation (Rust, desktop + CLI, 70+ extensions). Aider remains excellent for git-native, human-in-the-loop editing but is less autonomous.

**Recommendation**: OpenHands as the primary coding harness (run with local models). Goose or a thin custom Python loop for general research/orchestration tasks. Do not start with heavy multi-agent frameworks (CrewAI, AutoGen, etc.) — they add overhead without proportional benefit on 32 GB.

## 3. Multi-agent architecture

100 simultaneous model instances is impossible. 100 logical agents is trivial if implemented as:
- Agent definitions (role, tools, system prompt, model preference) stored as files or DB rows.
- A task queue (SQLite).
- A small worker pool (1–2 concurrent large-model inferences).
- Hierarchical coordinator that routes tasks to specialized workers or subagents.

Sequential execution with intelligent queuing + occasional small-model parallel classification gives the highest useful throughput. Dynamic subagent spawning is fine as long as they share the model server and do not each load their own weights.

## 4. Coding agents

OpenHands is the best match for autonomous, long-running, multi-step coding with terminal, tests, Git, and local model support. Pair it with Qwen3.6-35B-A3B. Use worktrees for isolation. Aider is the fallback for simpler git-centric tasks.

## 5. Research agents

Use OpenHands or a custom LangGraph/Python loop with:
- Local or SearXNG web search.
- Firecrawl or Brave Search MCP for extraction (optional paid).
- PDF tools (Docling or local RAG MCP).
- Strict citation requirement in the system prompt + verification pass.

Prevent hallucinations by requiring every claim to cite a retrieved source ID and by running a separate verification agent on the final report.

## 6. Persistent memory

Start with:
- Project-specific Markdown + SQLite (decisions, experiments, task history).
- Optional local embeddings (via Ollama or oMLX) + simple cosine search in SQLite or a lightweight library.

Add Mem0 (self-hosted) or Letta later only if pure filesystem memory becomes insufficient. Avoid heavy vector databases initially.

## 7. Computer control

Dedicated non-admin user account + Docker (or OrbStack) sandboxes for untrusted code execution. OpenHands already provides strong sandboxing. Restrict the agent user’s home and mount only explicit workspaces. Never give the agent the main user’s Keychain or Documents by default.

## 8. Always-on operation

```bash
sudo pmset -a sleep 0 disksleep 0 hibernatemode 0 standby 0 autorestart 1
```
Use LaunchAgents for Ollama and the supervisor. External SSD for workspaces and logs. Automatic restart on crash via KeepAlive.

## 9. Remote access

Tailscale (CLI/tailscaled version for headless reliability) + SSH. Simple status endpoint or OpenHands Canvas UI bound to the Tailscale IP. No public ports.

## 10. Storage architecture

- **Internal 512 GB**: macOS, models (Ollama/oMLX), SQLite, active caches.
- **External 1 TB**: Git repos, research papers, datasets, agent workspaces, logs, backups, cold KV cache.

---

### A. Recommended technology stack

| Layer | Recommended | Alternatives | Why |
|-------|-------------|--------------|-----|
| Inference server | Ollama 0.40+ (MLX) + oMLX | llama.cpp server, LM Studio | Ease + MLX speed + SSD KV cache |
| Primary model | Qwen3.6-35B-A3B | Qwen3.8-27B, Gemma 4 26B-A4B | Best agentic quality that fits |
| Coding harness | OpenHands | Goose, Aider | Mature autonomy + sandbox + local models |
| Orchestrator | Custom Python + SQLite queue | LangGraph, simple scripts | Minimal memory, full control |
| Memory | Filesystem + SQLite | Mem0, Letta | Starts simple, grows later |
| Remote | Tailscale + SSH | Cloudflare Tunnel | Zero public ports, works from phone |
| Sandbox | Docker / OrbStack + dedicated user | None | Required for safe autonomy |

### B. Architecture diagram (textual)

```
Phone/Laptop (Tailscale)
        │
        ▼
Supervisor (launchd, dedicated user)
  ├── Task Queue (SQLite)
  ├── Model Router
  │     ├── Large model worker (Qwen3.6-35B-A3B via Ollama/oMLX)
  │     └── Small model workers (9B class, optional)
  ├── OpenHands Coding Agents (Docker sandboxes)
  ├── Research Agents (Python loops + tools)
  ├── Memory Layer (FS + SQLite + optional embeddings)
  └── Tools (terminal, Git, browser, PDF, web search)
        │
        ▼
Workspaces (external SSD) + Models (internal SSD)
```

### C. Hardware/resource plan

- macOS + system: ~4–6 GB
- Large model weights + KV: ~18–22 GB (Qwen3.6-35B-A3B 4-bit)
- Agent processes + Docker: 2–4 GB
- SQLite / caches / browser: 1–2 GB
- Remaining: filesystem cache and headroom

**Ideal**: 1 concurrent large-model worker, 0–1 small-model workers. Context 32k–64k practical. Model swapping is worthwhile only between sessions, not mid-task. Bottleneck is memory capacity and bandwidth, not CPU.

### D. Agent architecture

100+ logical agents = definitions + queue. Concurrent LLM inferences limited to 1–2. Coordinator decides routing. Subagents are short-lived tasks that share the model server.

### E. Model strategy

- Planning / hard coding / research synthesis: Qwen3.6-35B-A3B
- Debugging / code review: same
- Summarization / classification / routing: Qwen3.5-9B or Gemma 4 12B
- Final synthesis: large model with verification pass

### F. 24/7 architecture

pmset + LaunchAgents (KeepAlive) + dedicated user + external SSD workspaces + automatic queue resume on restart.

### G. Remote-control architecture

Tailscale SSH + OpenHands Canvas or simple status page bound to Tailscale IP. Phone clients (Termius, browser).

### H. Security architecture

Dedicated non-admin user. Explicit workspace mounts only. Docker sandboxes for code execution. Approval required for: package installs outside sandbox, network changes, deletion of files outside workspace, credential access. Emergency kill via `launchctl` or process group. Full audit logs.

### I. Exact installation plan (minimal working system)

1. Create dedicated user `ai-agent`.
2. `brew install ollama tailscale`
3. Configure pmset and LaunchAgent for Ollama.
4. `ollama pull qwen3.6:35b-a3b` (or equivalent MLX tag).
5. Install OpenHands per official docs (Docker recommended).
6. Point OpenHands at `http://localhost:11434/v1`.
7. Create SQLite task queue and simple supervisor script.
8. Test with a small coding task.

### J. What NOT to install

Heavy multi-agent frameworks (CrewAI, AutoGen) as the primary layer, 70B models, full desktop environments for the agent user, any public-facing reverse proxy without Tailscale.

### K. Future upgrade path

64 GB → 70B-class or larger MoEs + multiple concurrent models. 128 GB+ or external GPU → true multi-model serving and longer contexts. Add dedicated GPU server later for heavy research.

---

**Sources** (primary marked):
- LLMCheck state of local LLMs Oct 2026 (measured M6 benchmarks) — secondary/community [web:0]
- OpenHands official docs (local LLMs, setup) — primary [web:40]
- oMLX GitHub and site (SSD KV cache) — primary [web:64, web:67]
- Qwen3.6-35B-A3B model card / benchmarks — primary [web:77]
- Tailscale + macOS always-on patterns — secondary [web:69]
- Multiple 2026 comparisons of OpenHands, Goose, Aider — secondary

This architecture is practical, mostly free/local, and optimized for useful work per hour on exactly your hardware rather than parameter count. Start with Phase 1 (Ollama + OpenHands + basic supervisor) and expand.

## Reasoning trace (not shown to raters)

Worked for 26s
Researching local AI workstation architecture
Ran 13 searches
Synthesizing local AI architecture
Structuring the final response

## Run notes

grok.com, new chat, mode menu Fast (never Auto, Heavy or Build); the menu showed "Fast".
Send time 2026-10-14T02:01:55.490Z (browser clock, read right after sending). Chat: https://grok.com/c/3c0d77ae-5d83-4105-b817-ade444c991be
Operated by the assistant (Claude, via the Claude in Chrome extension) in the author's signed-in
browser, at the author's request; the ten runs were opened in separate tabs and sent in
manifest order, a few seconds to minutes apart, without waiting for earlier answers.
The study prompt was pasted from the clipboard and checked (1,782 words, first and last
lines) before sending. DeepSearch was not used and no files were attached; Grok ran web
searches by itself, and the app offers no switch to turn search off. The panel above the
answer ("Worked for ...") is recorded as the reasoning trace. Answer copied with the app's
"Copy response" button and written verbatim from the clipboard.
