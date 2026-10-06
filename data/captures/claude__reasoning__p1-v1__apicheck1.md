---
run_id: claude__reasoning__p1-v1__apicheck1
set: api_check
family: claude
vendor: Anthropic
mode: reasoning
native_label: adaptive thinking, effort high
channel: api
model_requested: claude-sonnet-5-5
model_returned: claude-sonnet-5-5
params:
  thinking:
    type: adaptive
  output_config:
    effort: high
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 1
date_run: '2026-10-06T09:06:38+00:00'
run_by: roshanaryal
finish_reason: max_tokens
usage:
  input_tokens: 4096
  output_tokens: 32000
  reasoning_tokens: 14864
latency_s: 250.1
harness_version: 0.1.0
---

## Final answer

# Header

- **Model:** Claude (Anthropic). I don't know my exact version string.
- **Knowledge cutoff:** reliable through roughly mid-2025, patchy and lower-confidence into early 2026, and I have nothing for the months up to 31 Aug 2026.
- **Browsing/tools:** **OFF.** I did no live research, fetched no pages, and checked no versions. Everything below comes from training knowledge. Items I'm unsure of are tagged **[VERIFY]**.
- **Not verifiable by me:**
  - The "M6" chip, its memory bandwidth, and its GPU/neural-accelerator specs. I assume it is at least M5-class. I recall the M5 as roughly 150 GB/s on the base chip with per-GPU-core neural accelerators, which is **[VERIFY]**.
  - Any model released after about early 2026.
  - Current version numbers of every tool.
- **How I compensate:** I give selection logic that survives model churn, plus a Day-0 verification and bake-off procedure (§I, Step 1) that replaces the research I couldn't do. Treat my model names as candidates, not facts. The architecture is built so models are swappable config.

---

# Decisions at a glance

| Layer | Final pick | Confidence |
|---|---|---|
| Hardware role | Dedicated agent box; the agent runs as a separate non-admin macOS user | High |
| Inference engine | **llama.cpp `llama-server` (Metal)**, with **llama-swap** as the model residency/swap proxy. MLX (`mlx-lm`) is A/B-tested in Phase 8 | Medium-high |
| Main local models (candidates) | Coder: **Qwen3-Coder-30B-A3B** (Q4, ~17–19 GB). Generalist/reasoner/tool-user: **gpt-oss-20b** (MXFP4, ~12–13 GB). Newer equivalents win if the bake-off says so | Medium |
| Aux models (always resident) | ~4B instruct (classifier/summarizer, e.g. Qwen3-4B-Instruct-2507) + Qwen3-Embedding-0.6B | Medium-high |
| Coding harness | **OpenCode** (primary, headless/server mode); **Codex CLI** (secondary, best built-in sandbox); **mini-swe-agent** (fallback and eval baseline); Claude Code or Codex with cloud models only as budgeted escalation | Medium |
| Orchestration | **Custom thin Python daemon (`agentd`)**: SQLite task queue, leases, state machine, deterministic supervisor. No LangGraph/CrewAI/AutoGen | High |
| Durable-workflow upgrade | DBOS or Temporal only if SQLite leases prove insufficient | Medium |
| Agent definitions | YAML/Markdown specs (AGENTS.md, SKILL.md, MCP tool bundles) instantiated as short-lived, stateless runs | High |
| Model routing | Static rules table + escalation ladder inside `agentd`; LiteLLM only as optional cloud gateway/budget cap | High |
| Memory (initial) | Markdown vault in git (curated) + one SQLite DB (FTS5 + sqlite-vec) for events, evidence, tasks | High |
| Memory (later) | DuckDB for datasets; Graphiti/Neo4j only if relational queries hurt | Medium |
| Research stack | SearXNG + OpenAlex/Semantic Scholar/arXiv/Crossref/Unpaywall + Docling/PyMuPDF + **Evidence Ledger with mechanical quote/DOI verification** | High |
| Sandbox | Tier 0: dedicated user + Seatbelt (via harness) + pf egress rules. Tier 1: Linux containers (Apple `container` or Colima/OrbStack). Tier 2: Tart macOS VM for GUI use only | Medium-high |
| Remote access | **Tailscale** (tailnet-only, ACL tags) + SSH + tailnet-only web dashboard; **ntfy** for push and approvals | High |
| Always-on | LaunchDaemons (`KeepAlive`) under the agent user, `pmset`, external dead-man's-switch ping, UPS | High |
| Storage | Internal: OS, hot models, DBs, worktrees. External: cold models, papers, datasets, archives, restic backups | High |

---

# 1. Local inference (32 GB unified memory)

## Physics that drives every decision

- **Decode is memory-bandwidth-bound.** Tokens/s is roughly bandwidth ÷ bytes of active weights read per token.
  - Assuming about 120–150 GB/s (M4-base to M5-base class):
    - A 30B-A3B MoE at 4-bit reads about 1.7–2 GB per token. The ceiling is about 60–70 tok/s and real-world is plausibly 25–50.
    - A dense 24B at 4-bit reads about 13 GB per token. The ceiling is about 9–11 tok/s.
  - These are my arithmetic estimates, not benchmarks. Measure with `llama-bench`.
- **MoE with ~3B active parameters is the correct class** for this machine. A dense 24–32B model is 4–6× slower per token for modest quality gains, which is the wrong trade for "useful work per hour."
- **Prefill is compute-bound and is the real bottleneck on a base chip.** Agent harnesses re-send long system prompts, tool schemas, and file contents.
  - Mitigations: prefix/KV reuse, short contexts, truncated tool output, lean harness prompts, and context compaction.
  - If the M6 inherits M5-style GPU neural accelerators, prefill may improve a lot **[VERIFY]**, but only for engines that use them (MLX first).
- **Batching is nearly free throughput.** Because decode is bandwidth-bound, N concurrent sequences on one resident model share one weight read per step. Aggregate tok/s rises substantially (my guess is 1.8–3× at 3–4 streams; measure). One server with parallel slots beats several model instances.

## Engine comparison

| Engine | Strengths | Weaknesses | Verdict |
|---|---|---|---|
| **llama.cpp / llama-server** | Mature; Metal; GGUF ecosystem; continuous batching (`-np`); KV-cache quantization; prompt-cache reuse and slot save/restore; grammar/JSON-schema constraints; speculative decoding; fast support for new architectures; gpt-oss/harmony handling via `--jinja` | Sometimes 10–30% slower decode than MLX on some models; flags change between releases | **Primary** |
| **MLX / mlx-lm** (Apple) | Best-tuned for Apple GPUs; likely first to use M5+ neural accelerators; quantization options (3/4/6/8-bit, mixed) | Server batching/prompt caching historically less mature; fewer sampling/constraint features | **A/B candidate** (Phase 8) |
| **Ollama** | Easiest; auto load/unload; `OLLAMA_NUM_PARALLEL`, `OLLAMA_MAX_LOADED_MODELS`, `keep_alive` | Less control over KV, slots, and flags; abstraction hides regressions | Fine for convenience, not for tuning |
| **LM Studio / `lms` / llmster headless** | MLX + llama.cpp in one; JIT load and TTL unload; newer builds reportedly add parallel requests with continuous batching **[VERIFY]** | Closed-source app/daemon; less scriptable | Best "no-fuss" alternative |
| **vllm-mlx / vLLM-Metal plugins, other community MLX servers** | Real batching on MLX | Young; stability unknown **[VERIFY]** | Watch, don't depend |
| **exo** | Multi-Mac clustering | Irrelevant on one machine | Future (§K) |

**Pick:** llama-server for explicit control of context, slots, KV type, and memory. **llama-swap** (mostlygeek) fronts it as one OpenAI-compatible endpoint that swaps models by name, with groups for persistent versus exclusive models. It also supports MLX or other backends later without touching clients.

## Which models

Selection criteria, in order: agentic tool-call reliability, then coding/SWE performance, then active parameters (speed), then footprint (headroom), then licence.

| Role | Candidate | Footprint | Why |
|---|---|---|---|
| **Coder (swap-in)** | Qwen3-Coder-30B-A3B-Instruct, Q4_K_M or Unsloth UD-Q4 | ~17–19 GB | Purpose-built for agentic coding; 3B active; native tool-call format. KV is about 96 KiB/token at fp16 (48 layers × 4 KV heads × 128 dim), about 48 KiB at q8_0 |
| **Generalist, planner, researcher, tool-user (swap-in)** | gpt-oss-20b (MXFP4, Apache-2.0) | ~12–13 GB | Strong reasoning and tool use for its size; adjustable reasoning effort; alternating sliding-window attention gives a small KV; leaves RAM headroom. It reports competitive SWE-bench numbers, but settings differ between vendors, so don't compare across charts |
| **Fast/aux (resident)** | Qwen3-4B-Instruct-2507 Q4 (or a Gemma-3 4B/QAT) | ~2.5–3 GB | Classification, routing, summarizing tool output, titles, dedupe. About 100+ tok/s class |
| **Embeddings (resident)** | Qwen3-Embedding-0.6B (Q8) or EmbeddingGemma-300M | ~0.3–0.7 GB | Cheap, multilingual, good retrieval quality |
| **Reranker (on demand)** | Qwen3-Reranker-0.6B | <1 GB | Improves RAG precision |
| **Vision/PDF-OCR (on demand)** | A Qwen-VL or Gemma-3 multimodal at 4-bit; Docling's own models first | 3–8 GB | Only when layout parsing fails |

**Do not run locally on 32 GB:**
- Dense 70B models.
- gpt-oss-120b (~60+ GB).
- Qwen3-Next-80B-A3B (~45 GB at 4-bit).
- GLM-4.5-Air-class (~60 GB).

They don't fit alongside an OS and tools.

**Newer models [VERIFY]:** Between my cutoff and today, newer Qwen, GLM-Flash-class, Devstral-Small-class, and Gemma generations likely appeared. The slots (30B-A3B coder, ~20B reasoner, 4B fast) stay the same. Re-run the bake-off and swap the GGUF path.

**Quantization:** Q4_K_M / UD-Q4 for the coder (Q5 only if headroom allows and the bake-off shows a gain). MXFP4 as shipped for gpt-oss. KV cache q8_0 (requires flash attention). Avoid Q2/Q3 for agentic work, because tool-call syntax degrades first.

**Context:** run **24k tokens per slot** by default, not 128k. Long documents go through retrieval and chunked map-reduce, not giant prompts. A rare 64k "long-context" mode runs with a single slot.

**Swapping is worthwhile** when batched. Loading an 18 GB GGUF from internal NVMe takes about 10–30 s, which is trivial against multi-minute tasks. The scheduler therefore uses **model-affinity batching**: drain all coding tasks while the coder is loaded, then switch to research tasks on the generalist. Never thrash per request.

---

# 2. Agent runtimes / harnesses

| System | Autonomy loop | Local-model fit | Sandbox | Subagents | Headless/remote | Notes |
|---|---|---|---|---|---|---|
| **OpenCode** (opencode.ai, MIT) | Yes | Provider-agnostic, good | Permission rules (allow/ask/deny per command pattern); no strong OS sandbox of its own | Yes (markdown-defined agents) | `opencode run` and `opencode serve` (HTTP server + SDK) | Best fit as an embeddable worker **[VERIFY repo/org naming]** |
| **Codex CLI** (OpenAI, Apache-2.0, Rust) | Yes | `--oss` with local servers; tuned for gpt-oss | **Seatbelt sandbox on macOS built in**, approval modes | Limited | `codex exec`; MCP; AGENTS.md | Best built-in sandbox |
| **Claude Code** | Best-in-class loop | Cloud models; local only via Anthropic-API-compatible proxy | Seatbelt sandbox, hooks, permissions | Strong subagents, skills, hooks | `claude -p`, Agent SDK | **Large system prompt (~10k+ tokens) is a poor fit for local prefill-limited inference** |
| **Goose** (Block → Linux Foundation AAIF) | Yes | OK | Weak | Recipes | CLI, scheduling | MCP-native; decent, not distinctive |
| **OpenHands** | Yes | Works; heavy | **Docker runtime** | Yes | Headless, SDK | Strong for isolation, heavy on 32 GB |
| **mini-swe-agent / SWE-agent** | Minimal bash-only loop (~100 lines) | Excellent (tiny prompt) | Whatever you wrap it in | No | Trivial to script | Great baseline and fallback; robust with weaker models |
| **Aider** | Edit-and-commit loop, weaker autonomy | Excellent | None | No | CLI | Mature; git-native; not an agent OS |
| **Cline / Roo / Kilo** | Yes | Good | IDE-bound | Some | VS Code-bound | Wrong shape for headless 24/7 |
| **Qwen Code, Gemini CLI, Crush, Droid, Amp** | Yes | Qwen Code is tuned for Qwen3-Coder | Varies | Varies | CLI | Alternates; not needed |
| **OpenClaw (ex-Clawdbot/Moltbot), "personal agent gateways"** | Heartbeats, cron, chat-app gateways | Any | **Poor default security record** (exposed gateways, malicious skills, prompt injection) **[VERIFY details]** | Some | Via chat apps | Borrow ideas (heartbeat, channel gateway); do not run as the core with broad host access |

**Decision: complementary systems under a custom orchestrator.** No single harness provides all of the following:
- a durable queue,
- policy-enforced permissions,
- model-affinity scheduling,
- an evidence ledger,
- budgets and kill switches.

Harnesses are therefore **workers**, and `agentd` owns the loop, state, and policy. A harness is invoked as a bounded subprocess per task (`opencode run …` or `codex exec …`) inside a sandbox, in a git worktree, with a timeout and a token budget.

**Protocols:**
- **MCP** for tools (adopt).
- **AGENTS.md** for per-repo instructions (adopt).
- **SKILL.md-style "Agent Skills"** for reusable procedures (adopt).
- **A2A**: skip. It solves cross-vendor agent federation, not your problem.

---

# 3. Multi-agent architecture on limited hardware

**Definitions**
- **100 simultaneous model instances:** impossible and useless. The weights are shared, the GPU is one device, and 100 copies would take 1.8 TB.
- **Logical agent:** a *definition* (row or file) of role prompt, model class, tool allowlist, permission profile, memory scope, and budgets. 100+ of these cost kilobytes.
- **Agent run:** a short-lived execution (one harness invocation or one LLM-call loop) of a definition against a task. All state lives in SQLite, so an agent never "sits" in memory.
- **Worker pool:** bounded semaphores per scarce resource.
- **Dynamic subagent:** a definition instantiated on demand by the planner from an archetype template, with permissions attenuated from the parent.

**Concurrency limits for 32 GB (starting values, tuned by measurement)**

| Resource | Limit |
|---|---|
| LLM decode streams on the resident main model | 3 (slots) |
| Aux-model streams | 4–8 (small and cheap) |
| Concurrent harness processes (mostly idle waiting on tools) | 4 |
| Linux containers for tests/builds | 2 (≤3 GB each) |
| Headless browsers | 1–2 |
| CPU-heavy jobs (builds/tests/experiments) | 2–3 |
| Tart macOS VM (GUI) | 0–1, on demand only |

**Design rules (evidence-informed)**
1. **Coordinator/worker, depth ≤ 2.** Anthropic's multi-agent research write-up reports large gains from orchestrator-worker research (at roughly 15× token cost). Cognition's "don't build multi-agents" argues that parallel *writers* with fragmented context conflict. Reconcile them: **parallelize read-only, independent work** (search, paper reading, review, test running, per-file analysis) and keep **one writer per worktree**.
2. **Swarm/peer-to-peer topologies: skip.** They burn tokens, which on local hardware means scarce prefill and decode, and add nondeterminism.
3. **The supervisor is deterministic code, not an LLM.** LLMs propose; code disposes. Policy gates cap tree depth (≤3), fan-out (≤8 per task), the total open-task backlog, and duplicate-task hashes.
4. **Model-affinity scheduling** (§1). Tasks carry `model_class`. The scheduler picks the next batch to keep the loaded model busy.
5. **Escalation ladder:** fast model → main local model → (if allowed by sensitivity label and budget) cloud model. Escalate on verifier failure or repeated failure, not on a guess.
6. **Definition of done is machine-checkable:** tests pass, lint and type-check pass, the evidence verifier passes, diff size is within bounds. "The LLM says it's done" is never terminal.

**Realistic throughput expectation (my estimate):** one night (8 h) is about 29k seconds. At an aggregate 60–100 tok/s with batching, that is about 2–3M generated tokens. Prefill is likely the tighter constraint. That is enough for dozens of small-to-medium, well-specified coding tasks or several literature surveys, but not enough for hard, ambiguous, large-repo work, which is where cloud escalation earns its cost.

---

# 4. Coding agents

Evaluated on the 13 sub-criteria you listed (repository understanding, terminal, editing, tests, debugging, git, worktrees, long tasks, iteration, review, context, local support, sandbox):

- **Quality ceiling** (cloud models): Claude Code and Codex lead on long-horizon autonomy and context management. I can't verify the August 2026 leaderboard, so check SWE-bench Verified/Pro, Terminal-Bench, and Aider polyglot.
- **Local-model suitability:** OpenCode, Codex `--oss`, mini-swe-agent, and Aider have lean prompts. Claude Code's heavy prompt is poor for prefill-limited hardware.
- **Sandboxing:** Codex (built-in Seatbelt) is best; Claude Code is good with its sandbox runtime. For OpenCode, wrap it in your own sandbox.

**Choice**
- **Primary:** OpenCode driven by `agentd` through its server/headless mode, pointed at llama-swap (`coder` model), with project `AGENTS.md`.
- **Secondary:** Codex CLI with `--oss`/custom provider, using gpt-oss-20b for review and debugging passes. Its sandbox is reused.
- **Fallback and eval baseline:** mini-swe-agent. If the harness tool-calling breaks with a new local model, this is the control group.
- **Escalation (optional, paid):** Claude Code or Codex with a cloud model, for tasks flagged hard or after N local failures, only on `public-ok` or explicitly approved repos.

**Git protocol (enforced by `agentd`, not the harness)**
- One bare "agent remote" and a worktree per task: `git worktree add /Users/agent/work/<proj>/<task-id> -b agent/<task-id>`.
- Agents commit to `agent/*` only. Merge to main is human-approved (or auto-merge only for low-risk labels once trust is earned).
- Pre-task: clean tree check. Post-task: run the project's test command in a container, store logs, and produce a diff summary and review by a *different* model or prompt than the author.

---

# 5. Research agents

**Existing tools surveyed:** GPT-Researcher, LangChain open_deep_research, Stanford STORM, **PaperQA2** (FutureHouse; the strongest open citation-grounded scientific QA, supports local models), OpenScholar (Ai2), Khoj, plus paid Elicit/Consensus/Perplexity-class products. None enforces citation integrity at the data-model level, which is the property you care about.

**Architecture: an Evidence Ledger, with citation-by-reference.**

```
question → plan (sub-questions)
 → discover: SearXNG (self-hosted metasearch), OpenAlex, Semantic Scholar, arXiv, Crossref, Unpaywall, Europe PMC
 → fetch: HTTP (trafilatura) → Playwright fallback → store raw bytes + sha256 + URL + timestamp
 → parse: PDFs via Docling / PyMuPDF4LLM (GROBID for reference lists; OCR fallback)
 → chunk with stable span IDs (doc_id, page, char_start, char_end)
 → extract claims: LLM emits {claim, quote, span_id}      ← LLM never writes citations freehand
 → MECHANICAL verification:
     1. quote ⊂ source text (normalized exact/fuzzy match ≥ threshold) 
     2. DOI/ID resolves via Crossref/OpenAlex; title/author/year match metadata
     3. NLI/entailment check by a different model/prompt: does quote support claim?
 → ledger rows: verified | unsupported | contradicted | unresolved
 → contradiction detector: cluster claims by entity/question; cross-NLI inside clusters; surface conflicts with both sources
 → report writer: can only cite ledger IDs [E123]; sees verified claims only
 → post-processor: renders bibliography from the ledger; strips/flags any citation not in the ledger; flags any sentence with no ledger reference as "uncited opinion"
```

- **Injection defense:** the fetch/extract stage is a **quarantined** worker. It sees untrusted web text, has no private-data access, and returns only structured JSON (a dual-LLM/CaMeL-style separation). The report writer sees the structured claims, not raw pages.
- **Model split:** the 4B aux model handles dedupe, filtering, and snippet summarization. gpt-oss-20b handles planning and claim extraction and synthesis. A *different* model/prompt (the coder or the 4B) handles the verifier role. For final synthesis of non-private work, optionally use a cloud model reading only ledger-verified claims.
- **Known limits:** local 20–30B models are weaker at long, multi-document synthesis, so chunk it and map-reduce with a ledger. Paywalled PDFs are inaccessible. Search quality is bounded by SearXNG/engine blocking, so keep a Brave Search API key as an optional paid fallback.

---

# 6. Persistent memory

| Option | Verdict |
|---|---|
| Filesystem Markdown (Obsidian-compatible vault, in git) | **Initial: curated project/decision/research memory.** Human-readable, diffable, rollbackable |
| SQLite (+FTS5, +sqlite-vec) | **Initial: events, episodic log, tasks, evidence ledger, embeddings, hybrid search.** One file, WAL mode, zero ops |
| Postgres + pgvector | Later, only for multi-writer or remote access needs |
| Dedicated vector DBs (Qdrant, LanceDB, Chroma) | Unnecessary below ~millions of chunks |
| Knowledge graph (Graphiti/Zep, Neo4j, Cognee, Mem0, Letta) | Defer. Add if multi-hop entity queries repeatedly fail on relational and FTS search |
| DuckDB | Add in Phase 8 for datasets and experiment results (analytical queries over Parquet) |

**Structure**
- **Global memory:** `vault/global/` (preferences, standing policies, tool notes).
- **Project memory:** `vault/projects/<name>/` containing `README.md`, `decisions/ADR-*.md`, `experiments/`, `status.md`.
- **Episodic:** the `events` table (append-only; every task, tool call summary, outcome).
- **Semantic:** `memory_items(id, scope, text, embedding, source_event, confidence, created, superseded_by)`.
- **Write path:** only a **Librarian** agent writes to long-term memory, always with provenance (`source_event`). Other agents *propose* memories. A nightly consolidation job dedupes, supersedes stale items, and writes `status.md` summaries.
- **Read path:** a "context pack" builder assembles the top-k hybrid hits (FTS5 + vector, reranked) under a token budget per task, rather than letting agents browse memory freely.

---

# 7. Computer control and sandboxing

**Principle:** autonomy comes from *capability scoping*, not trust. Break the "lethal trifecta" (private data + untrusted content + exfiltration channel): **no single agent profile holds all three.**

| Profile | Private data | Untrusted content | Network egress |
|---|---|---|---|
| `coder` | Project repo only | Docs/issues (low) | Allowlist: git remote, package registries |
| `researcher` | **None** | Yes (web) | Broad GET via filtering proxy |
| `analyst` | Datasets (granted) | Local files | **None** |
| `librarian` | Memory DB | Only structured proposals | None |
| `gui-operator` | VM-only data | Yes | Proxy, VM-restricted |

**Isolation tiers**
- **Tier 0: macOS user separation.**
  - A standard (non-admin) user `agent` has its own home and its own keychain. It has no sudo and no access to your login keychain, `~/.ssh`, browser profiles, or `~/Library`.
  - Grant access to your real project directories via a group (`labshare`) and explicit ACLs (`chmod +a`), read-only unless writable is needed. Agents work on worktrees or clones in `/Users/agent/work`, and results flow back as branches or patches.
  - Optionally add Seatbelt (`sandbox-exec` is deprecated but still used by Codex and Claude Code), via the harness's own sandbox or Anthropic's open-source sandbox-runtime.
- **Tier 1: Linux containers** for running untrusted or project code and tests. Options are Apple's open-source `container` CLI (Containerization framework, macOS 26+, each container in a lightweight VM), Colima/Lima, and OrbStack. I choose **Apple `container` if stable on your macOS, else Colima** (OSS, lighter than Docker Desktop). Cap RAM and CPU, use no host mounts except the worktree, and default to `--network none` plus an egress proxy where needed.
- **Tier 2: Tart macOS VM** (Virtualization.framework) for GUI/computer-use experiments only. Use a throwaway snapshot, no personal accounts, and 6–8 GB RAM. Apple limits macOS guests to 2 per host.
- **Egress control:** a local filtering proxy (e.g. mitmproxy or Squid) with a domain allowlist per profile, plus **pf rules keyed on the `agent` UID** that block all outbound except to the proxy and the local inference port. Optionally add LuLu or Little Snitch for visibility.
- **Browser:** Playwright headless Chromium in the agent user's profile or container, no persistent logins, and downloads quarantined.
- **GUI/computer-use:** lowest priority. Prefer API/CLI/MCP paths. Where GUI is unavoidable, use Tier 2 only. Small local VLMs are unreliable at GUI grounding; escalate to a cloud computer-use model for non-private tasks only.
- **Secrets:**
  - Agents never hold primary secrets.
  - Use a **bot GitHub account** or fine-grained PAT scoped to specific repos and `agent/*` branches, with branch protection on `main`.
  - Wrapper tools inject credentials (broker pattern, e.g. `op run` with a 1Password service account, or the agent's own keychain). The model sees tool results, never tokens.
  - Redact known secret patterns from logs.

---

# 8. Always-on operation (macOS)

- **Power:** `sudo pmset -a sleep 0 disksleep 0 displaysleep 0 powernap 0 womp 1 autorestart 1`. A UPS is cheap insurance. A headless mini may need an HDMI dummy plug for GUI/screen-sharing use.
- **FileVault trade-off (important):**
  - With FileVault ON, after an unplanned reboot the Mac waits at pre-boot for a password, so your services do not start.
  - Options: (a) keep FileVault ON and use `sudo fdesetup authrestart` for planned updates, accepting a manual unlock after power loss, with a UPS; macOS 26 reportedly allows remote FileVault unlock over SSH **[VERIFY]**; (b) FileVault OFF only if the machine is truly dedicated and holds no personal data.
  - I recommend (a) for a personal machine.
- **Services:** system **LaunchDaemons** in `/Library/LaunchDaemons/` with `UserName=agent`, `RunAtLoad`, `KeepAlive`, `ThrottleInterval`, and log paths. These run at boot without GUI login. Services: `llama-swap`, `agentd`, `agentd-dashboard`, the egress proxy, SearXNG, and the `iogpu.wired_limit_mb` setter (root).
- **GPU memory limit:** macOS by default lets the GPU wire only about 2/3 of RAM at this size. Raise it with `sudo sysctl iogpu.wired_limit_mb=24576` (a LaunchDaemon reapplies it at boot, since it resets). Keep at least 6–8 GB for everything else.
- **Crash recovery:** every task has a lease (`lease_expires`) and heartbeat. On `agentd` restart, expired leases return to `queued` with `attempt+1`. Worktrees are reset or recreated. Idempotent steps are marked in `events`. A poison-task quarantine kicks in after 3 failures.
- **Watchdogs:**
  - `agentd` self-checks inference health (`/health`), disk space, memory pressure (`memory_pressure`), and thermal state.
  - It pauses the queue on a RAM-pressure "critical" state, a full disk, or an unmounted external drive.
  - **External dead-man's switch:** ping healthchecks.io (or self-hosted Uptime Kuma on another device) every 5 minutes. A missed ping sends a phone alert. This is the only way to learn the whole box is down.
- **Scheduling:** a `schedules` table inside `agentd` (cron-like) instead of dozens of launchd jobs. Nightly: consolidation, backups, log rotation, an evals smoke-test, and a morning digest.
- **Updates:** pin versions (uv lockfiles, brew bundle). Update in a maintenance window, then run the smoke test, and roll back by pinned version if it fails.

---

# 9. Remote access

- **Network:** **Tailscale** with the open-source `tailscaled` as a system daemon (starts before login). Use ACL tags (`tag:lab`), deny-by-default, and your phone/laptop as the only allowed sources. **No port forwarding, no public exposure.** Alternatives: self-hosted WireGuard (more work), Cloudflare Tunnel + Access (public endpoint, I prefer to avoid it).
- **Shell:** SSH over the tailnet (key-only; Tailscale SSH where supported). From a phone use Termius or Blink Shell. `tmux` for persistence.
- **Dashboard:** a small FastAPI/htmx app (or Datasette over the SQLite DB plus a custom status page), served with `tailscale serve` (tailnet-only HTTPS). It shows the queue, running agents, token and time budgets, GPU memory, logs, diffs, and the evidence ledger.
- **Notifications and approvals:** **ntfy** (self-hosted on the mini, behind Tailscale, or ntfy.sh with a long random topic and content-free messages). Action buttons call a tailnet-only, signed-token endpoint: "Approve / Deny / Pause." Alternative: a Telegram bot (outbound-only, but message content transits Telegram) for convenience. Pushover is a $5 paid option.
- **Task submission:** `agentctl submit "…"` over SSH, a dashboard form, or an iOS Shortcut posting to the tailnet endpoint.
- **Emergency stop (layered):**
  1. `agentctl panic` (SSH or a dashboard button) creates `/var/lab/KILL`. Every worker polls it and `agentd` SIGTERMs, then SIGKILLs, all child process groups.
  2. `launchctl bootout system/com.lab.agentd`.
  3. A pf rule blocks the agent UID's egress.
  4. Tailscale ACL or `tailscale down` as a last resort.
  5. A smart plug is the physical backstop.

---

# 10. Storage architecture

External SSD throughput is fine for sequential reads, but it is a reliability and latency risk for fsync-heavy databases, because a disconnect or sleep can corrupt an open WAL. Keep hot and write-heavy data internal.

| Data | Location | Reason |
|---|---|---|
| macOS, apps, brew, uv envs | Internal | — |
| **Active models** (coder, generalist, aux ≈ 35–40 GB) | **Internal** `/Users/agent/models` | Mmapped; page faults over USB/TB under memory pressure stall inference |
| Cold model library | External `/Volumes/Lab/models` | Copy to internal when promoted |
| SQLite DBs, WAL, ledger, vector index | **Internal** | fsync latency, integrity |
| Git repos and worktrees (active) | **Internal** | Many small files; builds |
| `node_modules`, build dirs, container storage | Internal (cap ~60–80 GB) | Random IO |
| Temporary agent workspaces | Internal `/Users/agent/work`, with a TTL reaper | — |
| Papers/PDF corpus, parsed text | External | Large, mostly read-only |
| Datasets, experiment outputs, Parquet | External (hot subsets internal) | — |
| Logs | Internal 14 days, then compressed and archived externally | — |
| **Backups** | External restic repo **plus an offsite copy** (B2/S3 or another machine), encrypted | An external drive on the same machine is not a backup |
| Vault (Markdown memory) | Internal git repo, pushed to a private remote | — |

Rough internal budget: macOS and apps ~100 GB, models ~40 GB, repos and worktrees ~60 GB, containers ~40 GB, DBs and indices ~20 GB, caches and logs ~20 GB. That is ~280 GB, leaving more than 200 GB free. Keep at least 15% free, since SSD health and swap depend on it. Format the external drive APFS (encrypted) and have `agentd` verify the mount and pause the queue if it is absent.

---

# Market comparison (per category)

| Category | Best overall | Best for this HW | Best OSS | Lightest | Most mature | Cutting-edge | **Use** |
|---|---|---|---|---|---|---|---|
| Inference engine | llama.cpp / MLX (close) | llama.cpp now; MLX likely on M5+ accelerators | llama.cpp | llama.cpp (single binary) | llama.cpp | vLLM-Metal/MLX servers | **llama-server + llama-swap** |
| Model (coding) | Frontier cloud | Qwen3-Coder-30B-A3B-class | Qwen3-Coder | Qwen3-4B | Qwen2.5-Coder family | Newer 2026 Qwen/GLM-Flash **[VERIFY]** | **Qwen3-Coder-30B-A3B (bake-off)** |
| Model (reasoning/tools) | Frontier cloud | gpt-oss-20b | gpt-oss/Qwen3 | 4B-class | Qwen3 | 2026 releases **[VERIFY]** | **gpt-oss-20b** |
| Coding harness | Claude Code / Codex (cloud) | OpenCode, Codex `--oss` | OpenCode, Codex, mini-swe-agent | mini-swe-agent | Aider | OpenCode server mode | **OpenCode + Codex + mini-swe** |
| Orchestration | Temporal (durable) | Custom SQLite | Temporal/DBOS | SQLite+Python | Temporal | DBOS-style library durability | **Custom SQLite `agentd`** |
| Memory | Postgres+pgvector (scale) | SQLite+sqlite-vec | SQLite | Markdown files | Postgres | Graphiti/Zep temporal graphs | **Markdown + SQLite** |
| Research | PaperQA2 (science QA) | Custom ledger + PaperQA2 pieces | PaperQA2 / GPT-Researcher | SearXNG + scripts | GPT-Researcher | Ai2 OpenScholar/Asta-class | **Ledger pipeline** |
| Sandbox | VMs | Dedicated user + containers | Apple `container`/Colima/Tart | Seatbelt | Docker | Apple Containerization | **User + Seatbelt + container** |
| Remote | Tailscale | Tailscale | WireGuard/Headscale | WireGuard | Tailscale/SSH | — | **Tailscale** |
| Notifications | Pushover | ntfy | ntfy | ntfy | Pushover | — | **ntfy** |
| PDF parsing | Docling / Marker | Docling (CPU-viable) | Docling, MinerU | PyMuPDF4LLM | GROBID | olmOCR/VLM parsers | **Docling + PyMuPDF4LLM** |
| Search | Paid APIs (Brave/Exa/Tavily) | SearXNG | SearXNG | SearXNG | Brave API | Exa | **SearXNG + Brave fallback + OpenAlex** |

---

# Required architecture

I changed the requested layering in three ways:
- The supervisor and orchestrator merge into one deterministic `agentd` process. Splitting them adds failure modes without benefit at this scale.
- A **policy/approval gate** sits between orchestrator and tools, so permissions are enforced outside the model.
- A **verifier** layer is mandatory and separate from the authors.

---

# Deliverables

## A. Recommended technology stack

| Layer | Recommended | Alternatives | Why |
|---|---|---|---|
| Interface | SSH + `agentctl` CLI, tailnet web dashboard, ntfy | Telegram bot, Datasette | No public surface; phone-friendly |
| Supervisor and orchestrator | `agentd` (Python 3.12+, `uv`, asyncio, SQLite) | Temporal, DBOS, LangGraph | Deterministic, tiny, inspectable; can graduate to DBOS/Temporal |
| Queue | SQLite table with leases | Redis, Postgres, NATS | No extra daemon |
| Policy gate | Python module + YAML permission profiles | OPA | Enforced outside the LLM |
| Agent definitions | `agents/*.md` (front-matter YAML) + Skills + AGENTS.md | CrewAI/AutoGen | Plain files, versioned |
| Model router | Rules table + escalation ladder; optional LiteLLM | RouteLLM, Plano | Measured rules beat learned routers at this scale |
| Inference | llama-server ×N via llama-swap | MLX, Ollama, LM Studio | Control, batching, swap groups |
| Harness workers | OpenCode, Codex CLI, mini-swe-agent | Claude Code, Aider, Goose, OpenHands | Lean prompts, headless |
| Tools | MCP servers (filesystem-scoped, git, fetch, SQLite, search), Playwright | Custom tools | Standard, portable |
| Memory | Markdown vault (git) + SQLite (FTS5 + sqlite-vec) | Postgres, Qdrant, Graphiti | Minimal infra |
| Research | SearXNG, OpenAlex, S2, arXiv, Crossref, Docling, ledger | PaperQA2, GPT-Researcher | Mechanical citation integrity |
| Sandbox | Dedicated user, Seatbelt, pf, Apple `container`/Colima, Tart | Docker Desktop, OrbStack | Layered isolation |
| Secrets | Agent keychain or `op run`, scoped bot tokens | Vault | Broker pattern |
| Remote | Tailscale, ntfy, healthchecks | WireGuard, Cloudflare | No inbound |
| Observability | Structured JSONL + SQLite events + dashboard; OpenTelemetry later | Langfuse (self-host) | Enough |
| Backup | restic (encrypted) to external plus offsite | Time Machine | Verifiable, versioned |

## B. Architecture diagram

```
 PHONE / LAPTOP ──(Tailscale WireGuard, ACL tag:lab)──────────────────────────┐
   ntfy push ◄──────────────┐   SSH/tmux   Dashboard (tailscale serve)         │
                            │                                                  ▼
┌───────────────────────────┴────────────────── Mac mini (M6, 32 GB) ───────────────────────────┐
│ root/launchd: pmset, iogpu.wired_limit_mb, pf (agent UID egress → proxy only), tailscaled      │
│                                                                                               │
│ user "agent" (non-admin) ── LaunchDaemons (KeepAlive)                                          │
│                                                                                               │
│  agentd (supervisor+orchestrator, deterministic)                                               │
│   ├─ Task queue/state (SQLite WAL) ◄──► Memory: vault(git) + SQLite(FTS5,sqlite-vec,ledger)    │
│   ├─ Planner (LLM call) → proposes tasks/agent specs → POLICY GATE (depth, fan-out, perms,     │
│   │                                                      budgets, sensitivity labels)          │
│   ├─ Scheduler (model-affinity batching, semaphores: LLM 3 / ctr 2 / browser 2 / cpu 3)        │
│   ├─ Approval service ──► ntfy ◄── you         Kill switch (/var/lab/KILL, launchctl, pf)      │
│   └─ Verifier layer (tests, lint, quote-match, DOI resolve, NLI, diff-size)                    │
│          │                                                                                     │
│   Workers (short-lived, per task, own worktree + profile):                                     │
│     coder → OpenCode/Codex/mini-swe  ─┐   researcher (quarantined) → fetch/parse/extract       │
│     reviewer, debugger, analyst, librarian, doc-writer, dynamic specialists…                   │
│          │ tools via MCP / wrappers                    │                                       │
│          ▼                                             ▼                                       │
│   Seatbelt → Container (tests/builds, no net)    Filtering proxy (allowlist) → Internet        │
│   Tart VM (GUI, on demand)   Playwright browser   SearXNG (local)                              │
│          │ OpenAI-compatible HTTP (localhost only)                                             │
│          ▼                                                                                     │
│   llama-swap ─┬─ group main (exclusive swap): coder 30B-A3B | gpt-oss-20b   (-np 3, KV q8)     │
│               └─ group aux (persistent): 4B fast | embed 0.6B | (rerank on demand)             │
│   (optional) LiteLLM → cloud models only for tasks labelled public-ok and within spend cap     │
│                                                                                               │
│ Internal SSD: OS, hot models, DBs, worktrees, containers │ External SSD: cold models, papers,  │
│ datasets, archives, restic repo (+ offsite copy)                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
 healthchecks.io dead-man's switch ◄── ping /5 min
```

## C. Hardware/resource plan (estimates; verify with `vm_stat`, `memory_pressure`, Activity Monitor)

| Item | RAM |
|---|---|
| macOS + system daemons + Tailscale | 4.5 GB |
| Main model (Qwen3-Coder-30B-A3B Q4), **or** gpt-oss-20b (12.5 GB), one at a time | 18 GB (or 12.5) |
| KV: 3 slots × 24k tokens at q8_0 (≈48 KiB/token) | ~3.5 GB (gpt-oss: ~1 GB) |
| Aux 4B Q4 + KV | ~3 GB |
| Embedding 0.6B | ~0.7 GB |
| `agentd`, SQLite cache, proxy, SearXNG, dashboard | ~1.5 GB |
| Harness processes (3–4 × ~0.3–0.5 GB) | ~1.5 GB |
| Headless Chromium (1–2) | ~1.5 GB |
| Container VM (tests) | 2–3 GB |
| **Total with coder loaded** | **≈ 36–37 GB if everything is active, which does not fit** |

**Consequence:** with the 30B coder loaded, the box is *tight*.
- Run **one container, one browser, and 2 slots** during coding phases, and let page cache and swap absorb the rest.
- Better, drop the aux 4B to ~2 GB or run it on CPU-light duty.
- With **gpt-oss-20b** loaded (12.5 + 1 KV) the total is comfortably ~28–30 GB.

**Model-phase profiles:**
- **Coding phase:** coder + embedding; aux 4B optional; 2 slots; 1 container.
- **Research phase:** gpt-oss-20b + 4B + embed; 3 slots; 2 browsers.
- **GUI phase:** gpt-oss-20b only, plus the Tart VM (6–8 GB).

If the coder-versus-gpt-oss bake-off is close, **choose gpt-oss-20b as the single resident main** for the headroom. Headroom directly buys concurrency, which is useful throughput. This is the main hardware-driven decision, and it is yours to settle with the Day-0 bake-off.

**Expected bottlenecks (in order):** prefill speed with long agent contexts, then RAM pressure from sidecars, then memory bandwidth at higher concurrency, then thermals (mini cooling is decent but sustained load will throttle somewhat), then external-drive disconnects.

**Context:** 24k per slot default, 64k single-slot mode. **Concurrency:** 2–3 large-model streams, 4–8 small-model streams.

## D. Agent architecture: 100+ logical agents, ≤3 inference streams

1. **Registry:** `agents/<name>.md` with front-matter:
   ```yaml
   name: lit-reviewer
   archetype: researcher
   model_class: reasoner        # fast | reasoner | coder | cloud-optional
   profile: researcher          # perms: fs scope, net allowlist, tool bundle
   memory_scope: [global, project]
   budgets: {wall_s: 1800, tokens: 150000, tool_calls: 80, retries: 2}
   tools: [search, fetch, pdf_parse, ledger_write]
   done_when: ledger.verified_ratio >= 0.9
   ```
2. **Archetypes** (about 12 hand-written): planner, coder, debugger, reviewer, tester, researcher, verifier, summarizer, analyst, doc-writer, librarian, triager. Each is a template with tool bundles.
3. **Dynamic creation (Agent Forge):** the planner emits a spec as JSON. The policy gate validates the schema and enforces **capability attenuation** (child permissions ⊆ parent), a budget ceiling, and a whitelist of tools and models. Specs are ephemeral. After ≥N successes and passing evals, the Librarian promotes one to the registry for human review.
4. **Execution:** `task(agent_spec, inputs, context_pack)` runs as one harness subprocess or one bounded LLM loop. It is stateless, and state is checkpointed to SQLite after every step.
5. **Scheduling:** a priority queue ordered by (priority,

## Reasoning trace (not shown to raters)

NONE

## Run notes

finish_reason=max_tokens. Check for truncation or refusal before scoring.
