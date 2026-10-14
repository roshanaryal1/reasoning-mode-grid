---
run_id: claude__reasoning__p1-v1__r3
set: main
family: claude
vendor: Anthropic
mode: reasoning
native_label: claude.ai, Sonnet 5.5, Effort High
channel: web
model_requested: Anthropic chat app, claude.ai, Sonnet 5.5, Effort High
model_returned: Sonnet 5.5 (app model menu, Effort High)
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 3
date_stamped: '2026-10-14T07:14:43+00:00'
date_run: '2026-10-14T07:14:43+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

Starting the research now. I'll check hardware specs first, then inference, harnesses, and the rest.

**Claude Sonnet 5.5 | knowledge cutoff: end of June 2026 | web search ON (31 searches, search-result snippets only, no full-page fetches, so most figures below are vendor-reported or secondary unless marked)**

Date note: your brief says Aug 31, 2026, but the session date is Oct 14, 2026, and the M6 mini only shipped on Sept 22. I used Oct 14.

Disclosure: I am made by Anthropic, and Claude Code is an Anthropic product. I discount my own preference accordingly and treat it as an A/B candidate, not a default.

---

## 0. Decisions at a glance

| Layer | Pick | Confidence |
|---|---|---|
| Inference server | **oMLX** (MLX, continuous batching, SSD prefix cache), with **llama.cpp `llama-server`** as fallback and for grammar-constrained output | ~60% over Rapid-MLX; settled by a conformance test in Phase 1 |
| Primary model | **Qwen3.8-27B**, 4-bit, text path, MTP drafting on | ~70% |
| Throughput mode (eval-gated) | **Qwen3.6-35B-A3B** 4-bit, batch phases only | ~50%, needs a soak test |
| Embeddings and rerank | jina-embeddings-v5-text-small (MLX) + a 0.6B reranker | ~75% |
| Worker harness | **OpenCode** in server mode, **Pi** as lean alternate, Claude Code A/B in Phase 2 | ~55% OpenCode over Claude Code |
| Orchestration | **Custom control plane ("Foreman")**: Python asyncio + SQLite WAL, no agent framework | ~80% |
| Model router | Custom ~300 LOC gateway with per-run token budgets and policy-gated cloud escalation | ~70% |
| Sandbox | Dedicated macOS user + **Apple `container` 1.0** microVMs + pf egress control + allowlist proxy | ~75% |
| Memory | Markdown in git (truth) + SQLite FTS5 + sqlite-vec (derived index) | ~85% |
| Research | Evidence-ledger pipeline, cite-by-ID, deterministic quote check, RefChecker-style reference resolution | ~85% |
| Always-on | LaunchDaemons with `UserName=agent`, sentinel watchdog, `pmset`, UPS | ~80% |
| Remote | **Tailscale** (tailnet only), tmux, web UI via `tailscale serve`, ntfy push | ~85% |
| Storage | Internal = hot (DBs, repos, active model, KV cache). External = cold (models, papers, backups) | ~85% |
| Cloud | Frontier API as capped, policy-gated escalation only; system works without it | n/a |

---

## Findings that change the design

1. **Memory bandwidth is the binding constraint, not RAM size.** Apple lists the M6 mini at up to 170 GB/s with 32 GB configurable, 12 CPU cores, and a Neural Accelerator in each of 12 GPU cores (Apple's launch details). One measurement put real STREAM bandwidth at roughly 143-144 GB/s. The same test showed 9B prompt processing at 742 tok/s versus 210 on the M4, while generation only rose from 18 to about 27 tok/s (mindstudio measurement). The M6 helps prefill far more than decode.
2. **Measured decode on 32 GB M6:** Qwen3.6-35B-A3B reached about 64 tok/s while Qwen3.8-27B ran about 11-12 tok/s in normal mode. Another report had plain MLX at 8-9 tok/s on the 27B dense 4-bit, rising to 16-19 with multi-token prediction. These are secondary sources and a YouTube-derived summary, but they match the bandwidth roofline (~143 GB/s ÷ ~15 GB of weights ≈ 9-10 tok/s).
3. **The 32 GB wall is real.** macOS lets the GPU address only about 22 GB of a 32 GB Mac by default, and one guide advises leaving roughly 6 GB for macOS on this tier. A 32 GB M5 tester found that pushing a 30B coder with multi-file tools caused swap spikes and a dead session.
4. **Qwen3.8 is a hybrid architecture.** Qwen3.8-27B has 16 full-attention layers and 48 Gated-DeltaNet layers. Recurrent state cannot be rolled back like a KV cache, so ordinary prefix caching fails and exact checkpoints are required. This matters because agent loops re-read context every turn. oMLX 0.6.3 now ships first-class Qwen3.8 support with continuous batching, prefix-cache state preservation, and Lightning MTP, and restored prefix reuse in long Claude Code sessions. Earlier, prompt-cache failures on Qwen3-Next hybrids (mlx-lm #1162) and tool-parser mismatches were the top failure modes, so the cache and parser must be tested before trusting them.
5. **The popular "personal agent" platforms are a poor trust root.** OpenClaw had a critical RCE (CVE-2026-25253) and 341 malicious skills on ClawHub. A review of Hermes Agent reports an independent audit with 4 critical and 9 high findings in default config, and 44 CVEs tracked as of Sept 2026 including a CVSS 8.8 RCE. I have not verified these against NVD or OpenCVE directly.
6. **Vendors evaluate with Claude Code-style harnesses.** Qwen states its SWE-bench Pro runs for 3.8-27B use Claude Code with a refined task set. A third-party quant card also reports Terminal-Bench 2.1 with Claude Code 2.1.228. Harness and model are co-adapted, so you need your own bake-off.
7. **macOS unattended-boot rules:** FileVault blocks automatic login, so encryption and unattended restart are a deliberate trade-off. Per-user LaunchAgents do not auto-load on headless Macs, and an external APFS volume does not mount before login.

**Realistic capacity, derived from those numbers (estimates, not benchmarks):**

| Mode | Single-stream decode | Output tokens/hour |
|---|---|---|
| Q (27B dense) | ~10 tok/s, ~16-19 with MTP | 36K single-stream; ~0.1M aggregate if batching gives ~2.5x (hypothesis) |
| T (35B-A3B) | ~64 tok/s | ~0.23M |

A 100-turn coding task at ~2K output tokens per turn is ~200K tokens. That is roughly 2 hours in Mode Q and under 1 hour in Mode T, before prefill and tool time. An 8-hour night therefore yields about 4-8 substantial tasks in Q or 15-30 in T. Thinking-token budgets are the main lever on throughput.

---

## 1. Local inference

**Engines.** One tracker reports MLX decode 15-40% faster than llama.cpp on M4/M5 for most modern architectures. On an M2 Max test, MLX generated 1.5x faster but prefilled 2.3x slower than llama.cpp. The M2 Max has no neural accelerators, and Apple says MLX targets the M5 Neural Accelerators automatically with no code changes, so the prefill gap should shrink on M6. Re-measure on your machine.

llama.cpp still has two advantages. MLX lacks schema-level JSON constrained decoding, and llama.cpp is better when a model does not fit and needs layer splitting. Ollama adds a layer without adding capability here: GGUF routes to llama.cpp, safetensors to MLX.

**Servers.** oMLX provides continuous batching, a two-tier KV cache (RAM plus SSD) that survives restarts, and multi-model serving with LRU eviction, pinning, and per-model TTL. That is the right feature set for crash recovery and for batching several agent streams on one model. The risk is maturity: the project was created about two months before that snapshot and moves fast, so pin versions. Rapid-MLX reports 17 tool parsers and is described as the strongest Mac backend for tool-calling reliability. Apple's own reference path is MLX-LM Server, which any agent framework can use.

**Models for 32 GB:**

| Model | Fit at 4-bit | Evidence | Verdict |
|---|---|---|---|
| **Qwen3.8-27B** (Apache-2.0, Aug 14) | 17-19 GB total per Unsloth | Vendor card: SWE-bench Pro 61.7 vs 53.5 for 3.6-27B, Terminal-Bench 2.1 63.4 to 73.0, DeepSWE 13.3 to 42.2. Independent replication pending | **Primary** |
| Qwen3.6-35B-A3B | ~20 GB weights; ~64 tok/s on M6 32GB | SWE-bench Verified 73.4, Pro 49.5 | **Throughput mode**, eval-gated, at the memory wall |
| Qwen3.6-27B | ~16 GB | 77.2 Verified, 53.5 Pro | Superseded |
| Ornith-1.0-9B (MIT) | 5.6 GB Q4_K_M at 64K (community card) | 69.4 Verified, self-reported, with the team's public track record described as thin | Eval candidate for a fast bulk tier |
| Gemma 4 12B QAT | ~6.7 GB at Q4_0 | Released June 3, 256K context | Small-tier candidate, not default |
| Gemma 4 26B-A4B / 31B | 14-18 GB | Qwen's table shows 17.4 for 26B-A4B on SWE-bench Verified, a competitor's scaffold, so discount it | Skip for coding |
| Muse Glimmer 30B (Apache-2.0, dense) | under 20 GB at 4-bit | Meta claims it beats Qwen3.6-27B; Qwen's 3.8 table lists it at 51.2 on SWE-bench Pro vs 61.7 | Skip |

**Quantization caution.** One small-model test found llama.cpp Q4_K_M kept near-8-bit quality while MLX 4-bit cost about 4 perplexity points, though MLX generated ~80% faster. That was a 0.5B-class model, so it does not transfer directly. Prefer mixed-precision MLX builds (oQ-style, MTP head and GDN gates kept at BF16) and validate against your own eval.

---

## 2. Agent runtimes and harnesses

| Candidate | Strengths | Disqualifiers | Role |
|---|---|---|---|
| **OpenCode** (MIT) | 75+ providers, client/server design, 156K stars; headless `opencode serve` with OpenAPI 3.1 and an SDK; custom agents with their own model and permissions | Permissions are a workflow safeguard, not a sandbox; the headless server needs a password (OPENCODE_SERVER_PASSWORD, never unauthenticated) | **Default worker** |
| **Pi** (MIT) | Four tools and a system prompt under 1,000 tokens, which leaves more of a 64K local context for work; RPC mode | Minimal guardrails, so sandbox externally | Lean worker |
| Claude Code | OS-level sandbox plus permissions as defense in depth; talks to local servers via ANTHROPIC_BASE_URL | Proprietary. Remote Control drives the session from claude.ai or the mobile app, which is a cloud dependency | A/B candidate, optional cloud worker |
| Codex CLI | Apache-2.0, sandboxing is its clearest advantage | Reported OpenAI-only; one source says `--oss` enables local models, and the sources conflict | Skip |
| Hermes Agent | Cron, self-authored skills, seven terminal backends | See finding 5; small local models may claim a save without calling the tool | Do not deploy; borrow the skills-as-procedural-memory idea |
| OpenClaw | Viral, Mac-centric | See finding 5 | Do not deploy |

I did not evaluate Aider, OpenHands, Goose, Cline, or Qwen Code beyond star counts.

**Decision: build a thin control plane and use existing harnesses as workers.** Four reasons:
- **Durable state:** the thing that must survive crashes is the queue, leases, budgets, approvals, and audit log. Harnesses do not own that.
- **Privilege separation:** the component that gates actions must not be controllable by the component being gated.
- **Model-aware scheduling:** one resident model on 32 GB needs scheduling that no agent framework provides.
- **Small surface:** the Foreman is ~1.5-2K LOC with one SQLite file. I did not research LangGraph or Temporal this session, so I am not claiming they are worse. They add infrastructure you do not need yet.

---

## 3. Multi-agent architecture

| Concept | Meaning | Cost on 32 GB |
|---|---|---|
| 100 model instances | 100 copies of weights | 100 × ~16 GB: impossible |
| 100 logical agents | Rows in `agents`: role, prompt, tool scope, budget, memory namespace | KBs |
| Active agent | A harness process plus a KV/state slice | ~0.3 GB process (my estimate) + ~1-2 GB state (assumption, measure) |
| Worker pool / slots | Concurrent LLM streams batched on **one** resident model | 2-3 |
| Dynamic subagents | Planner emits a validated `AgentSpec`; child capabilities ⊆ parent | free |

Decode is bandwidth-bound, and a batched decode step reads the weights once for N sequences. So the right shape is **many logical agents, one model, 2-3 batched streams**. Most agent time is tool waits (tests, builds, fetches), so an agent that is waiting yields its slot. Cap hierarchy depth at 2 (coordinator → worker, with a reviewer as a sibling). Free-form swarms burn tokens you do not have.

I would not run separate instances of the same model. Batching is strictly better, though the 2-3x aggregate gain is an assumption you must measure. Dense models batch well. The MoE gains less because different sequences touch different experts.

---

## 4. Coding agents

Model quality dominates harness quality, but the harness must match how the model was trained, per finding 6. Required behaviors: worktree per task, two-phase container execution (online setup, offline test), hard verification gates, loop detection, and branch-only output.

**Bake-off in Phase 2:** 30 tasks from your own repos (issue → hidden tests), run for OpenCode, Pi, and Claude Code against the same local endpoint. Record pass@1, turns, tokens, wall time, and tool-call error rate. Switch the default only if a harness wins by ≥10% relative on pass@1 at ≤1.3x tokens. My prior is about 60/40 that Claude Code's harness beats OpenCode with Qwen3.8, given the vendor evals. OpenCode wins on openness and on needing no vendor account. The Foreman adapter is harness-agnostic, so this is a config switch.

---

## 5. Research agents

**The failure mode is real.** One study found 13 LLMs hallucinated citations at rates from 14.23% to 94.93%. Hallucinated references also survive peer review at top conferences. Reference-level checking is tractable: RefChecker resolves entries against multiple bibliographic sources, costing about $0.04 per paper in one venue scan. The CiteAudit design splits checking into claim extraction, evidence retrieval, passage matching, contextual reasoning, and calibrated judgment.

**Architecture (the model never types a citation):**
1. **Discover:** arXiv, OpenAlex, Crossref, Semantic Scholar, Unpaywall APIs plus self-hosted SearXNG. Local Deep Research (MIT, ~9.1K stars) already integrates these sources and is a reasonable component. PaperQA reports performance comparable to expert humans on LitQA (with a GPT-4-turbo agent, so transfer to a local 27B is unverified).
2. **Snapshot:** fetch each source, store text plus SHA-256, and parse PDFs with offsets.
3. **Evidence cards:** `{claim, verbatim quote, page, char_start, char_end, snapshot_sha}` in SQLite. The quote must be a **literal substring** of the snapshot, checked deterministically with no LLM.
4. **Write:** the writer sees only evidence IDs and emits `[ev:123]` markers.
5. **Render:** bibliography is built from Crossref/OpenAlex metadata for the cited source IDs. The model never writes authors, titles, or DOIs.
6. **Verify:** per sentence, a verifier (ideally a different model or prompt from the writer) judges entailment against the quote span. Unsupported sentences are deleted or flagged `[unsupported]`.
7. **Contradictions:** cluster cards by entity and predicate, flag opposing stance across sources, and surface both in the report.

Research agents have **no access to private repos and no write tools**. That is the lethal-trifecta control in section 7.

---

## 6. Persistent memory

| Option | Verdict |
|---|---|
| Markdown in git (truth) | **Phase 1.** Reviewable, diffable, rollback is `git revert` |
| SQLite FTS5 | **Phase 1.** Exact matches on symbols, error strings, paths |
| sqlite-vec | **Phase 4.** One file, the index is a derived cache rebuildable from the Markdown |
| Hybrid BM25 + vector with RRF | **Phase 4.** One builder reports pure vector search missed exact technical terms (single-author anecdote) |
| Vector DB server, graph DB, Postgres | Defer. Revisit above ~1M chunks, multi-writer contention, or demonstrated multi-hop failures |
| Letta / Mem0 / Zep-Graphiti | Not evaluated |

Embeddings: jina-embeddings-v5-text-small is 0.6B, scored 67.0 on MMTEB (vendor-reported), and ships MLX weights. Qwen3-Embedding-0.6B is the alternative.

**Write gating:** only the Foreman writes to global memory, and agents submit proposals. Web-derived memory is tagged `untrusted` and expires. Scopes are global, per-project, per-agent, and per-run scratch.

---

## 7. Computer control and sandboxing

**The core security idea is the lethal trifecta:** private data + untrusted content + external egress. A CSA note reports 98% of 100 assessed agents had all three. The fix is architectural: remove at least one leg from every execution path, using patterns like dual-LLM and plan-then-execute.

| Agent class | Private data | Untrusted content | Egress |
|---|---|---|---|
| Coding | yes (repos) | only via deps/issues | **none** at execution; allowlisted registries during setup only |
| Research | **no** | yes | allowlisted domains via proxy |
| Reader/extractor | no | yes | none; emits schema-validated JSON only |

**Mechanisms:**

| Mechanism | Use |
|---|---|
| Dedicated non-admin macOS user | Mandatory baseline |
| **Apple `container` 1.0 microVMs** | Released June 9, 2026; each container gets its own micro-VM and consumes OCI images. No Compose support. Per-VM isolation costs slower startup than a shared VM |
| pf rules | Per-user for host processes; per-subnet on the vmnet bridge for microVMs (needs validation, confidence ~65%) |
| Harness built-in sandboxes | Defense in depth only |
| Host GUI/computer-use | **Off by default.** Use headless Playwright in a container with a fresh profile |
| macOS VM | Only for Xcode/Swift builds (not researched here) |

The `vvbox` pattern is a good reference: snapshot a git worktree, run in an isolated container, produce a reviewable patch instead of touching the repo.

---

## 8. Always-on operation

Use LaunchDaemons with `UserName`, not LaunchAgents, for headless boot (finding 7). One Apple forum answer is blunt: there is no solution that works with FileVault, since its whole point is to protect data at rest. Details are in deliverable F.

## 9. Remote access

Tailscale gives a tailnet-only mesh with no public ports. On a headless mini, the GUI app's daemon needs a logged-in user session, so use the Homebrew daemon. Tailscale SSH is not OpenSSH, and mosh cannot bootstrap through it. A tag:agent ACL model plus Tailscale Lock is a documented pattern. Details are in deliverable G.

## 10. Storage

Hot and latency-sensitive data lives on internal storage, and cold data on external. Numbers are in deliverable C. The M6 has three Thunderbolt 4 ports, so the external SSD is far slower than internal and must never hold databases.

---

## Market comparison by category

| Category | Best overall | Best for this HW | Best OSS | Lightest | Most mature | Cutting edge | **Use** |
|---|---|---|---|---|---|---|---|
| Inference | vLLM/SGLang (SGLang had day-0 Qwen3.8 support; not Apple) | oMLX | mlx-lm / llama.cpp | llama.cpp | llama.cpp | oMLX 0.6.x, vMLX, Rapid-MLX (MTP) | **oMLX + llama-server** |
| Local model | Ornith-397B / Qwen3.8-2.4T (cannot run) | Qwen3.8-27B | Qwen3.8-27B (Apache-2.0) | Ornith-9B | Qwen3.6-27B/35B | Qwen3.8-27B + MTP | **Qwen3.8-27B** |
| Harness | Claude Code (bias flagged) | OpenCode / Pi | OpenCode | Pi | Claude Code, Codex CLI, Aider | Hermes (unsafe) | **OpenCode, A/B** |
| Orchestration | Temporal (prior knowledge, unverified) | SQLite + asyncio | same | SQLite | Temporal/Celery (prior) | n/a | **Foreman** |
| Memory | Postgres + pgvector (prior) | MD + SQLite hybrid | same | Markdown + ripgrep | SQLite FTS5 | graph/temporal memory (not evaluated) | **MD + SQLite** |
| Sandbox | Firecracker-class microVMs (prior) | Apple container | Apple container | Seatbelt | Docker/VMs | Apple container machines | **container + pf + user** |
| Remote | Tailscale | Tailscale | WireGuard | plain WireGuard | Tailscale | n/a | **Tailscale** |
| Research | closed deep-research products (not evaluated) | custom ledger | PaperQA2, Local Deep Research | Local Deep Research | PaperQA2 | CiteAudit/RefChecker-style | **Custom ledger** |

---

## A. Technology stack

| Layer | Technology | Alternatives | Why |
|---|---|---|---|
| Interface | Web UI via `tailscale serve` + `agentctl` CLI + ntfy | Telegram bot, Moshi | No third party sees content |
| Supervisor | `sentinel` LaunchDaemon (root-launched, `_foreman` user) | monit | Independent of the thing it watches |
| Orchestrator + queue | Foreman: Python 3.12, asyncio, SQLite WAL | Temporal, LangGraph | Durable, tiny, auditable |
| Agent definitions | Markdown/JSON `AgentSpec` in a config git repo | OpenCode `.opencode/agents/*.md` | Versioned, diffable |
| Model router | Custom gateway (OpenAI + Anthropic-compatible) | LiteLLM | Per-run budgets, policy-gated cloud |
| Inference | oMLX → Qwen3.8-27B (Q), Qwen3.6-35B-A3B (T) | Rapid-MLX, llama-server | See section 1 |
| Workers | OpenCode server / Pi RPC in microVMs | Claude Code | See sections 2 and 4 |
| Tools | git worktrees, container runner, SearXNG, Playwright (container), MCP (own servers only) | n/a | Minimal supply chain |
| Memory | Markdown + SQLite FTS5 + sqlite-vec | pgvector | Rebuildable, diffable |
| Evals | Own 30-task harness + citation verifier | SWE-bench | Vendor benchmarks are self-reported |
| Remote | Tailscale, ntfy, tmux | WireGuard | See section 9 |

## B. Architecture diagram

I changed the requested layer shape. Supervisor, orchestrator, and queue collapse into one control plane that runs as a **separate OS user** from workers, and "specialized agents" are data rows, not processes.

```
 Phone/Laptop ── Tailscale (tailnet only) ──┐        ntfy push (metadata only)
                                            ▼
┌───────────────────────── Mac mini M6, 32 GB ─────────────────────────────┐
│ roshan (admin, personal data)            ── no agent access              │
│                                                                          │
│ _foreman (no shell)                                                      │
│  ├ Web/API (unix socket + tailscale serve): approvals, status, STOP      │
│  ├ Scheduler/Leaser (SQLite WAL): queue, leases, budgets, stop rules     │
│  ├ Agent factory: AgentSpec validation, capability attenuation           │
│  ├ Sentinel: health, memory governor, heartbeat, kill switch             │
│  └ Secrets: git deploy key, cloud API keys (workers never see them)      │
│                    │ unix socket                                         │
│ agent (unprivileged)                                                     │
│  ├ Model Gateway :8000 ── per-run token, budget, routing, retries        │
│  │     ├ oMLX :8001 ─ Qwen3.8-27B | Qwen3.6-35B-A3B | embed+rerank       │
│  │     └ cloud frontier (policy-gated, capped)                           │
│  ├ Worker slots (2-3 LLM streams): OpenCode/Pi inside container microVM  │
│  │     worktree rw, net=none after setup                                 │
│  ├ Research microVM: egress proxy allowlist, NO private repos            │
│  └ Memory: Markdown(git) + SQLite FTS5/sqlite-vec                        │
│ pf: agent → gateway + proxy only; VM subnet → host ports 8000/8888 only  │
└──────────────────────────────────────────────────────────────────────────┘
 Internal NVMe: DBs, repos, worktrees, hot model, KV cache | External: cold
```

## C. Hardware and resource plan

**RAM, Mode Q** (`iogpu.wired_limit_mb=24576`; this resets on reboot, so persist it via a LaunchDaemon, and Apple's general guidance is no more than ~70% of RAM):

| Consumer | GB |
|---|---|
| macOS + system | 5.0 |
| Foreman, gateway, SQLite, Tailscale, proxy | 1.0 |
| GPU pool: weights 15.5 + 2 streams' state 2.5 + embed/rerank 1.0 + Metal/MTP overhead 1.5 | 20.5 |
| 2 microVMs × ~1.25 | 2.5 |
| Harness processes | 0.8 |
| Page cache / headroom | 2.2 |
| **Total** | **32** |

The 15.5 GB weights figure is a plan value. Published numbers range from 14.95 GiB weights with 16.16 GiB peak to 21.8 GB in one 4K-context run (machine unspecified). Per-stream state is an assumption: 16 of 64 layers keep a KV cache, but the DeltaNet state is what dominates. Measure with `mx.get_peak_memory()`.

**Mode T** (35B-A3B, ~20.2 GB at 4-bit) needs a ~25 GB wired limit, one microVM, and one stream, with embeddings unloaded. That is at the wall, so adopt it only if an 8-hour soak shows zero swapouts and green `memory_pressure`.

**Answers to your sizing questions:**
- **Ideal size:** 27B dense at 4-bit. Do not run 6-bit; one build measured 29.5 GB at 6-bit.
- **Context:** 64K per stream by default, 128K for a single long job, harness compaction at ~48K. The SSD prefix cache makes re-prefill cheap.
- **Concurrent large-model workers:** 1 instance, 2 batched streams (3 after a soak). **Small-model workers:** only embed and rerank stay resident.
- **Swapping:** worthwhile at phase granularity (a few times a night, ~10-30s each, my estimate), never per request. The dispatcher drains one tier's queue before swapping.
- **Two big models resident:** no. 16 + 20 GB exceeds the wired pool.
- **Bottlenecks, in order:** decode bandwidth, memory capacity, prefill on long cold contexts, SSD write volume from KV spill.

**Storage (my estimates):**

| Internal 512 GB | GB | External 1 TB | GB |
|---|---|---|---|
| macOS + apps | 40 | Cold model library | 300 |
| Repos + worktrees | 60 | HF cache | 50 |
| Hot models | 38 | Paper corpus | 150 |
| SSD KV cache, **capped** (one user's setup pre-allocated ~100GB) | 60 | Datasets | 200 |
| DBs, memory, logs | 10 | Backups (restic of DBs, memory, git bundles) | 250 |
| Container images | 20 | | |
| Free reserve | ≥100 | | |

If an external drive vanishes, only cold models and corpora are affected, and the Foreman degrades gracefully.

## D. Agent architecture

```json
{"id":"agt_reviewer","role":"reviewer","tier":"Q","thinking":"low",
 "tools":["fs.read","git.diff","sandbox.run:test"],"fs_scope":["worktree:ro"],
 "net":"none","budget":{"tokens":150000,"wall_s":1800,"iterations":25},
 "memory":{"read":["project","global:decisions"],"write":["proposals"]},
 "parent":"agt_planner","ttl_s":86400}
```

```sql
CREATE TABLE agents(id TEXT PRIMARY KEY, spec JSON NOT NULL, parent TEXT, created_at INT, ttl_s INT);
CREATE TABLE tasks(id TEXT PRIMARY KEY, project TEXT, goal TEXT,
  state TEXT CHECK(state IN ('queued','leased','running','verifying','needs_approval',
                             'blocked','done','failed','quarantined')),
  tier TEXT, priority INT, agent_id TEXT, parent_task TEXT, attempts INT DEFAULT 0,
  lease_owner TEXT, lease_expires INT, budget JSON, created_at INT, updated_at INT);
CREATE TABLE runs(id TEXT PRIMARY KEY, task_id TEXT, model TEXT, harness TEXT, config_sha TEXT,
  tokens_in INT, tokens_out INT, wall_s INT, exit TEXT, worktree TEXT, started INT, ended INT);
CREATE TABLE events(seq INTEGER PRIMARY KEY AUTOINCREMENT, ts INT, run_id TEXT, kind TEXT,
  payload JSON, prev_hash TEXT, hash TEXT);               -- hash-chained audit log
CREATE TABLE approvals(id TEXT PRIMARY KEY, task_id TEXT, action JSON, action_hash TEXT,
  tier INT, state TEXT, expires INT, decided_by TEXT);
CREATE TABLE evidence(id TEXT PRIMARY KEY, source_id TEXT, quote TEXT, page INT,
  char_start INT, char_end INT, snapshot_sha TEXT, retrieved_at INT);
```

**Dynamic creation:** the planner proposes an `AgentSpec`, and the Foreman validates it against the schema. Child tools, filesystem scope, network, and budget must be subsets of the parent's (capability attenuation). Specs are ephemeral by default. Recurring specs are promoted into the config repo by a human.

**Scheduler policy:**
- Slots = 2.
- Order by priority plus aging, with per-project fairness.
- Prefer tasks matching the loaded model tier.
- Yield a slot during tool waits.
- Preempt only at turn boundaries.
- Pause new leases when the memory governor trips.

**Stop conditions (any one halts the run):**
- Wall, token, or iteration budget exhausted.
- The same failing-test hash 3 times, or an identical tool call 3 times.
- Diff exceeds budget.
- 3 consecutive harness errors.
- Daily token/$ cap reached.
- STOP flag set.

**Definition of done:** tests pass in a clean container from committed state, lint and typecheck pass, the diff is in budget, a different-prompt reviewer approves, and docs are updated. Output is a branch only.

## E. Model strategy

| Task | Model | Notes |
|---|---|---|
| Planning | Qwen3.8-27B, thinking, capped (2-4K thinking tokens) | Escalate to frontier for architecture-level plans if data class permits |
| Coding (edit-test loops) | 27B non-thinking/low; 35B-A3B for bulk mechanical work (refactors, tests, docs) | T is eval-gated |
| Debugging | 27B thinking | Escalate after 2 failed hypotheses |
| Code review | **Other tier than the author** | Reduces correlated errors |
| Research extraction | 27B non-thinking, schema-validated output | MLX has no schema enforcement, so validate and retry, or route through llama-server grammar |
| Summarization | 27B, or 35B-A3B in T phases | A 12B small tier only if profiling shows it pays |
| Classification/routing | Deterministic rules first, then 27B with short constrained outputs | Not worth a resident small model |
| Final synthesis | 27B thinking + deterministic citation verifier | Optional frontier pass on non-sensitive topics |
| Embeddings / rerank | jina-embeddings-v5-text-small / 0.6B reranker | Keep both resident |

**Cloud policy:** local first. Escalate after K failed iterations or on a `needs_frontier` tag, only for repos classified non-sensitive, under a hard daily dollar cap enforced in the gateway. I did not verify current pricing, so check it before setting caps. Candidates are Claude Opus/Sonnet/Haiku 5.5 (disclosure above) and the GPT-5.6, DeepSeek V4, and hosted Qwen3.8-Max models seen in sources. Local is strictly better for private code, bulk token volume, and anything touching sensitive data. Cloud is worth it for hard planning, last-mile debugging, and final review, because local throughput is ~0.1-0.25M tokens/hour.

## F. 24/7 architecture

- **Boot:** `pmset -a sleep 0 displaysleep 0 disksleep 0 autorestart 1`, plus a UPS. One guide notes auto power-on after outage arrived in Tahoe 26.5.
- **Services:** LaunchDaemons for oMLX, gateway, Foreman, sentinel, and Tailscale, each with `UserName`, `KeepAlive`, and `ThrottleInterval`. Metal under a daemon context is untested by me, so test it in Phase 6. If it fails, use a LaunchAgent for the inference service plus auto-login of the `agent` user.
- **External volume:** a boot-time automount LaunchDaemon (the same pattern someone used for a headless build mini).
- **Updates:** disable automatic macOS install, because major updates can reset privacy grants and reportedly re-enable FileVault.
- **FileVault decision:** on a dedicated agent box with personal data kept off it, I would ship FileVault **off**. Otherwise ship it **on**, buy the UPS, and accept a LAN-side unlock after unplanned power loss. One source notes macOS 26 permits pre-boot unlock over SSH when Remote Login is enabled, but that only works on the LAN, not over Tailscale.

| Failure | Detection | Action |
|---|---|---|
| Inference crash | Sentinel: `/v1/models` plus 1-token generate every 45s | `launchctl kickstart -k`; the SSD cache survives |
| Foreman crash | launchd KeepAlive | Expired leases requeue with `attempts+1` |
| Worker hang | No events for N minutes | Kill the microVM; resume from the branch plus a handoff-notes file |
| Memory pressure / swapouts rising | `memory_pressure`, `vm_stat` | Pause leases, kill the largest worker, fall back from T to Q |
| Poison task | `attempts>=3` | Quarantine plus notify |
| Power loss | Boot | Daemons restart; run the reboot test below |
| Mac fully dead | External heartbeat missed (a free healthchecks-style service, not verified) | Push to your phone |

**Reboot test (the acceptance criterion):** pull power mid-task, then confirm the queue resumes, the model serves, and Tailscale is reachable, all with no console login.

## G. Remote-control architecture

- **Transport:** Tailscale only, with a `tag:agent` ACL where only your phone and laptop reach the mini. Disable key expiry on the mini. Consider Tailscale Lock. Nothing listens publicly.
- **Shell:** Tailscale SSH plus tmux from a phone SSH client. Turn off macOS Remote Login so there is a single door. Break-glass is Screen Sharing on the LAN.
- **Dashboard and approvals:** web UI via `tailscale serve`, HTTPS, tailnet identity plus an app token. It shows queue, active runs, tok/s, memory pressure, spend, and approval cards with diff, test results, and risk.
- **Push:** ntfy carries metadata only ("T-0042 needs approval"), never content.
- **Approvals:** bound to `action_hash`, so an approved action cannot be swapped. They expire after 12h and default to deny.
- **Emergency stop** (`agentctl stop --hard`, also available as a button):
  1. Set the STOP flag.
  2. `pkill -KILL -u agent`.
  3. Stop all containers.
  4. Load the pf block-all anchor.
  5. Revoke gateway tokens.
  
  Nuclear remote option: remove the node from the tailnet in the admin console.
- **Autonomy lease:** autonomy above T0 pauses if you have not acknowledged the dashboard for 7 days.

## H. Security architecture

**Principals:** `roshan` (admin, personal), `_foreman` (control plane, owns the DB, approvals, and all secrets), `agent` (unprivileged, no Keychain, no access to `/Users/roshan`).

**Secrets:** workers never hold long-lived credentials. The gateway holds cloud keys, and workers get short-lived per-run tokens. Git pushes are performed by the Foreman with a deploy key after approval. The remote token is fine-grained, with branch protection forbidding pushes to `main`.

**"Any directory":** projects live in an allowlisted registry under `/Users/agent/work`. Anything else needs `agentctl grant <path> --ro|--rw --ttl 24h`, which is a T2 approval and a mount into the container, not host access.

| Tier | Policy | Operations |
|---|---|---|
| **T0** | Fully autonomous | Read inside granted workspaces; edit inside the task worktree; run tests/lint/builds in container; commit to `agent/*` branches; fetch allowlisted domains via proxy; write agent-scoped memory proposals; spawn subagents within budget |
| **T1** | Autonomous, logged, rate-limited, reviewed after the fact | New dependencies (lockfile, registry allowlist, install scripts off by default); diffs above N lines; file downloads; running generated scripts in container with net off |
| **T2** | Needs approval (default deny on timeout) | `git push`, PRs, merges; anything outside granted workspaces; deleting more than N files; touching dotfiles, launchd, SSH config; using credentials; any outbound POST to a non-allowlisted domain; cloud spend above cap; **editing the agents' own prompts, skills, or policies**; mass memory deletion; host `brew install` |
| **T3** | Never (OS-enforced, not model-enforced) | Personal home, Keychain, password manager, browser profiles, mail/messages, financial apps/sites; `sudo`; disabling pf, the kill switch, FileVault, or SIP; force-push to protected branches |

**Other controls:**
- **Injection:** web content is data. Use a quarantined reader that emits schema-validated JSON, and let the privileged agent see only validated fields. Plan before reading untrusted content.
- **Supply chain:** pin model weights by commit hash, use safetensors only, and verify checksums. Prefer converting official Qwen weights yourself over community MLX builds. Skills are code, and ClawHub's 341 malicious skills show why: only your own repo, no third-party MCP servers without review.
- **Resource limits per run:** tokens, wall time, iterations, container `--cpus/--memory`, a sparse-image disk quota, `ulimit -u`, and proxy byte caps.
- **Audit:** the hash-chained `events` table, written only by `_foreman`.
- **Git safeguards:** worktree per task, branch only, never operate on the primary checkout.

## I. Installation plan

Verify flags with `--help`, since projects here move weekly. Sources are cited above.

**Phase 0: prep (admin)**
```bash
sudo sysadminctl -addUser agent -fullName "Agent" -password -   # standard user, NOT -admin
sudo pmset -a sleep 0 displaysleep 0 disksleep 0 autorestart 1
sudo sysctl iogpu.wired_limit_mb=24576     # persist via LaunchDaemon (resets on reboot)
sudo mkdir -p /var/foreman && sudo chown _foreman /var/foreman   # create _foreman first
# dirs: /Users/agent/{work,worktrees,models,logs,memory}  /Volumes/AGENT-EXT/{models,papers,datasets,backups}
```

**Phase 1: minimal working system**
```bash
brew install uv node jq sqlite git
brew tap jundot/omlx https://github.com/jundot/omlx && brew install omlx
uv tool install huggingface_hub
# Pin by revision hash. Prefer converting official Qwen weights with mlx_lm.convert.
omlx serve --model-dir /Users/agent/models      # bind 127.0.0.1; set an API key
brew install anomalyco/tap/opencode
OPENCODE_SERVER_PASSWORD=<secret> opencode serve --hostname 127.0.0.1 --port 4096
# Pi (documented models.json shape for a local mlx-lm server):
#  ~/.pi/agent/models.json -> {"providers":{"mlx-lm":{"baseUrl":"http://localhost:8001/v1",
#   "api":"openai-completions","apiKey":"none","models":[{"id":"<model>"}]}}}
# Claude Code against local (for the A/B):
ANTHROPIC_BASE_URL=http://127.0.0.1:8001 ANTHROPIC_AUTH_TOKEN=local claude --model <id>
```
- **Test:** 20 scripted tool-calling turns (≥19/20 valid), and a 40K-token conversation where turn-20 TTFT shows a cache hit.
- **Failure modes:** parser mismatch, hybrid prefix-cache miss, OOM.
- **Rollback:** serve the GGUF via `llama-server`.

**Phase 2: autonomous coding**
```bash
git worktree add -b agent/T-0042 /Users/agent/worktrees/T-0042 main
container system start
container run --rm -v /Users/agent/worktrees/T-0042:/work -w /work <image> sh -lc "<test cmd>"
```
- Implement the Foreman v0: leases, worktrees, two-phase containers, verification gates, stop rules.
- Run the 30-task bake-off.
- **Test:** 5 tasks end to end overnight with zero manual steps.
- **Failure modes:** infinite fix loops, flaky tests (rerun 2x before counting a failure), disk growth from stale worktrees.
- **Rollback:** `git worktree remove`; branches are disposable.

**Phase 3: research**
```bash
uv pip install paper-qa local-deep-research          # components, not the system
git clone https://github.com/markrussinovich/refchecker  # reference-resolution component
# SearXNG in its own container with its own egress policy
```
- Build the evidence ledger, quote check, ID-only writer, and verifier.
- **Test:** 20 seeded fake citations plus 20 real ones. Pass bar is 100% of fakes flagged and 0 unresolved real references.
- **Failure modes:** PDF parse errors, paywalled sources, snapshots drifting.
- **Rollback:** reports are regenerated from the ledger.

**Phase 4: memory**
```bash
uv pip install sqlite-vec
# Markdown in git: ~/memory/{global,projects/<p>,agents/<id>}; FTS5 index first, vec + RRF after
```
- **Test:** recall@5 on 50 questions about past decisions.
- **Failure modes:** stale facts, injected memories (tag untrusted).
- **Rollback:** `git revert`, then rebuild the index.

**Phase 5: multi-agent**
- `AgentSpec` validator, tier-affinity scheduler, reviewer cross-tier rule.
- **Test:** a planner spawns 3 workers and a reviewer within budget, and a spec requesting more than its parent is rejected.
- **Failure modes:** token blowup, infinite spawning (depth cap 2).
- **Rollback:** disable the factory flag.

**Phase 6: 24/7**
```bash
sudo cp ai.local.omlx.plist /Library/LaunchDaemons/   # Label, UserName=agent, RunAtLoad, KeepAlive, ThrottleInterval
sudo launchctl bootstrap system /Library/LaunchDaemons/ai.local.omlx.plist
```
- Add daemons for the gateway, Foreman, sentinel, the wired-limit sysctl, and the external-volume automount.
- **Test:** the reboot test in section F, and an 8-hour soak watching swapouts.
- **Failure modes:** Metal unavailable in daemon context (fall back to LaunchAgent + auto-login), the external drive not mounted, a macOS update altering settings.
- **Rollback:** `launchctl bootout`.

**Phase 7: remote**
```bash
brew install tailscale && sudo brew services start tailscale
sudo tailscale up --ssh --advertise-tags=tag:agent     # needs tagOwners in your ACL
tailscale serve --bg 8443 http://127.0.0.1:9000        # verify syntax for your Tailscale version
```
- **Test:** from cellular, run SSH, the approval flow, and the kill switch.
- **Failure modes:** tailscaled not running headless, key expiry.
- **Rollback:** `tailscale down`; use the LAN.

**Phase 8: optimization**
- Enable MTP drafting and measure its acceptance rate.
- Run the Mode T soak.
- Cap thinking budgets and tune the batch size.
- Add a small-model tier only if profiling shows low-complexity work is a large share of GPU time.

## J. What NOT to install

- **OpenClaw and Hermes Agent** as the supervisor (finding 5).
- **Ollama** as the server, since it adds a layer over what oMLX and llama.cpp already do.
- **A vector DB server** (Qdrant, Chroma, Weaviate), graph DBs, Langfuse (Postgres + ClickHouse), and Kubernetes. All are unnecessary at this scale.
- **Third-party skills and MCP servers** from marketplaces.
- **Host-level GUI computer-use agents.**
- **Community MLX conversions** pulled by tag instead of pinned hash.
- **Docker Desktop**, which duplicates Apple `container` and shares one VM kernel.
- **Llama 4-class and 70B models.** They do not fit or run usefully on this tier.
- **Multiple simultaneous model instances.**

## K. Upgrade path

Figures come from Apple's launch coverage and a few reports, mostly unverified.
- **64 GB (M5 Pro mini):** up to 64 GB and 307 GB/s, so decode is roughly double. Run Qwen3.8-27B at 8-bit and 35B-A3B co-resident, which removes tier swapping.
- **96-128 GB (Mac Studio M5 Max):** up to 128 GB, with a 512 GB option arriving late October. 100B+ MoE models become practical. Raise slots to 4-6.
- **Clustering:** the M6 mini has Thunderbolt 4, while Apple's RDMA clustering demo used Thunderbolt for up to 3x speedup across four machines. Treat it as a Studio-class feature.
- **Dedicated GPU box:** put vLLM or SGLang on a Linux/NVIDIA machine for batch throughput. The gateway abstracts the backend, so it is a URL change. Keep the Mac as the control plane.
- **Unchanged across upgrades:** the Foreman, the schema, the security tiers, and the evidence ledger. Only the tiers and the concurrency settings change.

---

## Unverified items (flag once)

1. No independent benchmark of Qwen3.8-27B in agent loops on M6 exists in my sources. The vendor numbers are self-reported on refined task sets. Build your own eval before trusting any figure above.
2. MTP speedup and batching gain on MLX are second-hand or hypotheses.
3. Hybrid prefix-cache correctness in oMLX is claimed by the maintainers, and earlier mlx-lm issues existed. Test it before overnight runs.
4. pf rules for vmnet-bridged microVMs, Metal under a LaunchDaemon, and `tailscale serve` syntax are from prior knowledge, not tested this session.
5. Hermes and OpenClaw CVE counts come from secondary sources, apart from one NVD entry.
6. I did not research LangGraph, Temporal, Letta, Mem0, Zep, OpenHands, Goose, or Cline in depth.

## Sources (P = primary, S = secondary or mirror)

- Apple WWDC26, run local agentic AI with MLX: https://developer.apple.com/videos/play/wwdc2026/232/ (P)
- Qwen3.8 repo: https://github.com/QwenLM/Qwen3.8 (P)
- Qwen3.6-27B card (mirror): https://huggingface.co/Prince-1/Qwen3.6-27B (S)
- Qwen3.6-35B-A3B card (mirror): https://huggingface.co/qqceqqq/Qwen3.6-35B-A3B (S)
- Qwen3.8-27B specs/benchmarks: https://kingy.ai/blog/qwen3-8-27b-specs-benchmarks-local-hardware/ (S)
- Qwen3.8-27B release summary: https://www.yottalabs.ai/post/qwen-3-8-27b-specs-hardware-requirements-how-to-run-2026 (S)
- Qwen3.8-27B 8-bit MLX conversion with card text: https://huggingface.co/ggh5454/Qwen3.8-27B-MLX-8bit (S)
- Qwen3.8-27B MLX 4/6/8-bit memory table: https://huggingface.co/PocketAiHub/Qwen3.8-27B-MLX (S)
- Qwen3.8-27B hybrid layer counts, MTP acceptance: https://friendli.ai/models/Twu31/Qwen3.8-27B-AWQ-INT4-ZhChat-MTP (S)
- Hybrid prefix cache: https://pypi.org/project/yunshu/ (S)
- Unsloth Qwen3.8-27B: https://www.unsloth.ai/models/qwen3.8-27b (S)
- NVFP4 card with Claude Code Terminal-Bench run: https://huggingface.co/RadixArk/Qwen3.8-27B-NVFP4 (S)
- SGLang Qwen3.8 day-0: https://lmsys.org/blog/2026-08-12-qwen3-8-day0-support/ (P)
- oMLX: https://github.com/jundot/omlx (P); v0.6.3: https://github.com/jundot/omlx/releases/tag/v0.6.3 (P)
- Rapid-MLX: https://github.com/raullenchai/Rapid-MLX/releases/tag/v0.13.4 (P)
- Hermes + MLX megathread: https://r.datuan.dev/r/hermesagent/comments/1uc7rw5/ (S)
- M6 mini launch: https://t2online.in/tech/tech-news/apple-mac-mini-launches-with-m6--m5-pro-chips/2007528 (S); https://www.mactrast.com/?p=173149 (S)
- M6 AI measurements: https://www.mindstudio.ai/blog/m6-mac-mini-local-ai-performance (S); https://note.com/thegadget/n/ne16cddf6d40d?hl=en (S); https://daily.dev/posts/mac-mini-m6-first-look-qwen3-8-27b-hits-53-tps-locally-eqglitifc (S)
- MLX vs llama.cpp: https://bestllmfor.com/guides/mlx-local-llm-apple-silicon/ (S); https://huggingface.co/datasets/RaynarDM/apple-silicon-llm-benchmarks (S); https://www.emergentmind.com/topics/mlx (S); https://blog.starmorph.com/blog/apple-silicon-llm-inference-optimization-guide (S); https://pypi.org/project/silicon-eval/ (S)
- Ollama MLX routing: https://levelup.gitconnected.com/ollama-mlx-nearly-doubles-llm-speed-on-your-mac-58-to-112-tok-s-and-your-old-models-get-none-of-fd1a9ec531fb (S)
- GPU wired limit: https://localaimaster.com/mac/best-llm-32gb-mac (S); https://localaimaster.com/blog/mac-memory-pressure-local-llm (S); https://medium.com/@michael.hannecke/tuning-llama-cpp-on-apple-silicon-843f37a6c3dc (S)
- 32 GB M5 coding report: https://reddit.sentinel-team.org/posts/1uw2hir/snapshots/2026-07-17T18%3A53%3A30.39359Z (S)
- Ornith-1.0: https://letsdatascience.com/news/deepreinforce-releases-ornith-10-agentic-coding-models-ab5849e1 (S); https://huggingface.co/rafw007/ornith-1.0-9b-claude-coder (S, community fine-tune)
- Gemma 4 sizes: https://ai.google.dev/gemma/docs/core?authuser=0&hl=tr (P); https://gemma4all.com/blog/gemma-4-hardware-requirements (S)
- Muse Glimmer: https://aiweekly.co/node/9642 (S); https://runtimewire.com/article/meta-open-sources-muse-glimmer-agent-model-under-apache-2-0 (S)
- Harness comparisons: https://techstackups.com/comparisons/coding-agent-harness-comparison-2026/ (S); https://pinggy.io/blog/best_open_source_cli_coding_agents/ (S); https://enter.converge.ai/page/en-US/blog/codex-cli-vs-opencode-2026 (S); https://codex.danielvaughan.com/2026/04/09/opencode-vs-codex-cli/ (S)
- OpenCode server: https://www.analyticsvidhya.com/blog/2026/09/opencode-ai-explained/ (S); https://github.com/pradhankukiran/codex-opencode-executor (S)
- Pi: https://agentic-ai.readthedocs.io/en/latest/AgentHarness/pi-dev/ (S)
- Claude Code: https://code.claude.com/docs/en/changelog.md (P); https://docsearch.algolia.com/mcp/docs/website/code.claude.com (S); https://www.kdnuggets.com/pairing-claude-code-with-local-models (S)
- Hermes: https://github.com/hjlebbink/hermes-agent (S, README mirror); https://www.promptquorum.com/power-local-llm/hermes-agent-review (S); https://bestllmfor.com/guides/hermes-agent-local-models/ (S)
- OpenClaw: https://www.techradar.com/pro/best-hardware-options-for-deploying-openclaw (S); https://nvd.nist.gov/vuln/detail/cve-2026-27487 (P); https://letsdatascience.com/news/openclaw-faces-security-risks-despite-ecosystem-growth-e0b69cf2 (S)
- Apple container: https://www.opensourceforu.com/2026/06/apple-launches-container-to-run-linux-containers-inside-micro-vms-on-mac/ (S); https://www.infoq.com/news/2025/06/apple-container-linux (S); https://docs.rs/crate/vvbox/latest/source/docs/overview.md (S)
- Always-on: https://hometechops.com/mac/mac-mini-home-server-setup (S); https://developer.apple.com/forums/thread/737381 (P, forum); https://github.com/smartwatermelon/mac-dev-server-setup/pull/44 (S); https://clawhub.ai/alexbloch-ia/skills/mac-mini (S)
- Remote: https://lobster.shahine.com/guides/remote-access/ (S); https://claudskills.com/skills/tailscale-mosh-recover/SKILL.md (S); https://getmoshi.app/guides/tailscale (S)
- Citation integrity: https://arxiv.org/abs/2602.06718 (P); https://arxiv.org/html/2602.23452 (P); https://sotaverified.org/papers/260700738 (S); https://www.alphaxiv.org/abs/2605.27700 (S); https://arxiv.org/pdf/2312.07559 (P); https://www.promptquorum.com/power-local-llm/local-deep-research-review (S)
- Memory: https://pypi.org/project/memweave/0.1.1/ (S); https://blakecrosley.com/blog/ai-agent-memory-architecture (S); https://jina.ai/models/jina-embeddings-v5-text-small/ (P, vendor)
- Lethal trifecta: https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-agent-lethal-trifecta-capability-securi (S); https://agentpatterns.ai/security/lethal-trifecta-threat-model/ (S); https://www.stride.build/blog/security-risks-of-ai-coding-agents (S)
- Expert streaming (experimental, not recommended): https://github.com/manjunathshiva/turboquant-mlx (S)

## Reasoning trace (not shown to raters)

Claude responded: Starting the research now.
Preparing an in-depth research response for the request.
Preparing an in-depth research response for the request.

Starting the research now. I’ll check hardware specs first, then inference, harnesses, and the rest.

Searched the web

Searched the web





11 minutes ago

## Run notes

claude.ai incognito chat (no history or memory), model menu Sonnet 5.5, Effort High; the menu showed
"Sonnet 5.5 High". Connectors were switched off in the composer menu; the composer has no web-search
switch, and Claude searched the web by itself. Send time 2026-10-14T07:14:48.544Z (browser clock, read right after
sending). Chat: https://claude.ai/chat/e0862bd2-6f48-4cc2-9d4f-e8d021928c5a?incognito (incognito chats are not kept in history).
Operated by the assistant (Claude, via the Claude in Chrome extension) in the author's signed-in browser,
at the author's request; the runs were opened in separate tabs and sent in manifest order without waiting
for earlier answers. The app turns long pastes into an attachment, so the prompt was inserted as plain
text in eight line-aligned pieces from one clipboard paste and checked against the original (1,782 words,
same text) before sending. Answer copied with the app's Copy button (it includes any short lines the model
wrote before its searches) and written verbatim from the clipboard; the reasoning trace is the visible
process panel (step summaries and search queries) copied from the page text.
Replacement for this run: attempt 1 was stopped by the author's claude.ai usage limit and is in
superseded/. Sent after the limit reset, with at most three chats generating at once.
