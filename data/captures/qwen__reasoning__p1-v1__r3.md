---
run_id: qwen__reasoning__p1-v1__r3
set: main
family: qwen
vendor: Alibaba
mode: reasoning
native_label: chat.qwen.ai, Qwen3.8-Max, Thinking
channel: web
model_requested: Alibaba chat app, chat.qwen.ai, Qwen3.8-Max, Thinking
model_returned: Qwen3.8-Max (app model picker)
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 3
date_stamped: '2026-10-13T23:33:55+00:00'
date_run: 2026-10-13T23:21:30+00:00/2026-10-13T23:33:50+00:00
date_note: >-
  Sent on 14 Oct 2026 NZDT before this template was made; exact send time not
  recorded. The interval runs from the run 8 answer being read from the clipboard
  (12:21:30 NZDT; run 9 follows run 8) to this answer being read from the clipboard
  (12:33:50 NZDT). Template made afterwards (date_stamped).
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

**Model:** Qwen3.8 (no build hash exposed in this session) · **Knowledge cutoff:** not disclosed to me; reliable, checkable recall extends roughly through 2025 · **Web browsing / tools:** **OFF** — no search, browser, shell, or file tools were available.

> ## Evidence status — read this first
>
> I could not perform the live research you requested. I cannot verify August 2026 releases, M6 memory bandwidth, current llama.cpp/MLX flag names, or today's model leaderboard. **I will not name a "best model of August 2026" or cite a 2026 benchmark I did not retrieve. Doing so would be fabrication.**
>
> What follows is therefore an **evidence-bounded architecture specification**: decisions grounded in hardware arithmetic, protocol constraints, and failure-mode analysis, with a **Phase 0 script that gathers the missing primary evidence on your machine in ~20 minutes** and explicit **falsification gates** that change each decision. Every URL in Sources is marked as *not fetched in this session*. Treat version strings and model names below as **candidates to pin**, not as verified current releases.
>
> The architecture is deliberately robust to this uncertainty: the control plane, queue, memory, security, and recovery layers do not change when the model or executor changes.

---

## Decisions at a glance

| Layer | Final pick | Decisive reason |
|---|---|---|
| Inference server | **llama.cpp, Metal, one slot** | Mature constrained decoding + tool-call parsers + GGUF quant granularity. MLX is the benchmark challenger, not a co-resident second engine. |
| Workhorse model | **~30B-total / ~3–4B-active MoE, 4-bit, 24K context** | Active-parameter bandwidth is the scaling axis on unified memory. Dense 32B is the wrong shape here. |
| Second model | **None in v1** | Deterministic routing + FTS5 replaces a classifier LLM. A second large model guarantees memory pressure. |
| Coding executor | **Codex CLI against a local OpenAI-compatible endpoint, behind an adapter** | Existing sandbox + patch + exec loop. Native ~400-line loop is the fallback if local tool-call parsing fails. |
| General/research executor | **Small native loop with 10 fixed tools** | Browser-agent frameworks burn LLM turns per click. Deterministic tools are cheaper and more auditable. |
| Control plane | **Custom: SQLite state machine + launchd** | No off-the-shelf harness gives durable, cross-project, permission-scoped, budgeted orchestration. This is the part you own. |
| Queue | **SQLite WAL + leased tasks** | One inference consumer. A broker is pure overhead. |
| Memory | **Git-versioned Markdown + SQLite/FTS5**; `sqlite-vec` later | Provenance and diffability first. Vector search is an index, not a memory system. |
| Research sources | **OpenAlex + arXiv + Crossref + PyMuPDF + trafilatura** | Literature research does not need a general search engine or an API key. |
| Anti-hallucination | **Claim → evidence-ID → verbatim span, enforced in code** | The model never writes a bibliography. The renderer does. |
| Sandbox | **Dedicated macOS UID + per-task worktree + path jail**; Lima VM for untrusted code | Docker Desktop's VM RAM tax is unaffordable at 32 GB. |
| Secrets | **Separate root-owned broker daemon; secrets never enter model context** | The executor must be unable to read credentials even if fully compromised. |
| Remote | **Tailscale + Tailscale Serve + PWA + redacted alerts** | No public ports. Approvals bound to a diff hash and single-use nonce. |
| Supervision | **launchd daemon + independent watchdog + lease reclamation + caffeinate** | Recovery is a state-machine property, not a cron job. |
| GUI/computer-use | **Not in v1** | Terminal + fs + browser covers the requirement set without Accessibility/Screen Recording grants. |
| Cloud | **Optional, capped, redacted escalation. Never required.** | The lab must function with zero API keys. |

---

## Market comparison matrix

Legend: **O**=best overall · **M**=best for this Mac · **OS**=best open source · **L**=best lightweight · **S**=most mature · **C**=most cutting-edge · **U**=what you should actually run. Entries are candidates under the evidence caveat above.

| Category | O | M | OS | L | S | C | **U** |
|---|---|---|---|---|---|---|---|
| Inference engine | llama.cpp | MLX | llama.cpp | Ollama | llama.cpp | MLX + speculative decode | **llama.cpp** |
| Workhorse weights | strongest open agentic model that fits | 30B-A3B-class MoE Q4 | same | 14B dense Q4 | Qwen-Coder lineage | newest MoE passing your gate | **30B-A3B-class Q4, 24K** |
| Coding harness | Claude Code | Codex CLI (local provider) | Codex CLI / Aider | Aider | Aider | Codex CLI | **Codex CLI via adapter** |
| General agent harness | — | Goose | Goose | native loop | Goose | — | **native loop** |
| Orchestration | — | custom SQLite plane | custom / LangGraph | custom | custom | durable graph checkpointing | **custom SQLite plane** |
| Memory | — | fs + SQLite | sqlite-vec / FTS5 | SQLite | SQLite + Git | hybrid RRF retrieval | **fs + SQLite/FTS5** |
| Literature retrieval | — | OpenAlex + arXiv | same | arXiv only | Crossref | Semantic Scholar graph | **OpenAlex + arXiv + Crossref** |
| Web search | — | SearXNG (on demand) | SearXNG | direct fetch | Brave API | — | **direct fetch first; SearXNG later** |
| Sandbox | — | UID + Seatbelt | Lima / vz | UID only | macOS users | macOS native containers | **UID + worktree; Lima for untrusted** |
| Remote | — | Tailscale Serve | WireGuard | SSH | SSH | Tailscale identity-aware serve | **Tailscale Serve** |

**Close tradeoffs, resolved:**

- **MLX vs llama.cpp.** MLX is the more Apple-native code path and often wins prefill. llama.cpp wins on *agentic reliability*: GBNF/JSON constrained decoding, mature chat templates (`--jinja`), slot persistence, and a stable server contract. On a single-user lab, a 10% tool-call parse failure costs far more than a 20% token-rate gain. **Choose llama.cpp; switch if the Phase 0 gate says otherwise.**
- **Claude Code vs Codex CLI.** Claude Code is a stronger harness in my prior, but it is closed and Anthropic-oriented; local-model operation depends on a translation proxy you would have to maintain. Codex CLI is open source and has a documented custom-provider path. **Choose Codex CLI for the local default; treat Claude Code as an optional cloud executor, not infrastructure.**
- **Custom plane vs LangGraph.** LangGraph's durable checkpointing and human-in-the-loop interrupts are genuinely useful. But your hard requirements — cross-project worktrees, per-path write ownership, budget ledgers, approval-bound diffs, UID isolation — are *policy*, and policy wants to live in ~1,500 lines you fully control rather than inside a framework's graph semantics. **Choose custom. If you refuse to build, LangGraph + SQLite checkpointer is the one framework I would endorse.**

---

# 1. Local inference

### The binding constraint is bandwidth, not parameters

On Apple Silicon there is no discrete VRAM. Weights, KV cache, macOS, Chromium, and your build tools all draw from the same 32 GB and the same memory bus. Two consequences:

1. **Concurrency does not create throughput.** Two LLM workers share one bus. They halve each other's token rate while doubling KV memory. On this machine, parallel LLM workers are a *latency* feature for multi-user serving, which you are not.
2. **Swap is catastrophic, not a slowdown.** Once unified memory is exhausted, macOS compresses and pages to SSD. Inference latency can degrade by an order of magnitude. Admission control must prevent this, not recover from it.

### Why MoE is the right shape here

Arithmetic using the Qwen3-30B-A3B-class architecture (48 layers, 32 query heads, **4 KV heads**, head_dim 128, ~3B active parameters):

| Quantity | 30B-A3B MoE, Q4 | 32B dense, Q4 |
|---|---|---|
| Resident weights | ~16–18 GB | ~18–20 GB |
| Bytes read per decoded token | ~1.8–2.2 GB (active experts + attention) | ~16–18 GB |
| KV per token, FP16 | 48 × 4 × 128 × 2 × 2 = **96 KiB** | 64 × 8 × 128 × 2 × 2 = **256 KiB** |
| KV at 24K tokens | **~2.25 GiB** | **~6 GiB** |
| KV at 32K tokens | ~3 GiB | ~8 GiB |

At an *assumed* 150 GB/s bus (M6 base bandwidth is **unverified**), ideal decode ceilings are roughly ~75 tok/s for the MoE versus ~9 tok/s for the dense model. Real numbers are lower — kernel overhead, KV reads, prefill, expert gather inefficiency on Metal. **Do not treat these as predictions.** The *ratio* is the robust finding: a MoE with a small active set can be several times faster than a dense model of similar resident size, while GQA keeps the KV cache small enough to afford a useful context.

This is why "install the biggest model that fits" is wrong here. A 70B dense Q4 fits in 32 GB only by starving everything else, and decodes at a crawl.

### Model shortlist — pin via Phase 0, do not trust this list as current

| Candidate family | Role | Why | Risk |
|---|---|---|---|
| **Qwen3-Coder-30B-A3B-Instruct** (4-bit) | Default workhorse | Agentic-coding-oriented, long-context training, MoE bandwidth profile, small GQA KV | Metal MoE kernel efficiency varies by build |
| **Qwen3-30B-A3B** / instruct variant | Fallback if Coder-specific build unavailable | Same shape, general reasoning | Weaker tool-call adherence |
| **Qwen3-32B** (4-bit) | Quality reference only | Strong dense reasoning | 256 KiB/token KV; slow decode. **Not the default.** |
| **~14–20B dense instruct/coder** (Q4) | Memory fallback / fast worker | ~8–12 GB, leaves room for 64K context and a browser | Meaningfully worse long-horizon reliability |
| **gpt-oss-20b-class** | Cutting-edge challenger | Small active MoE, reasoning + tool use | Verify Metal path and tool-call format support |
| **Gemma-27B-class / Mistral-Small-24B-class** | Generalist alternates | Good prose and synthesis | Historically weaker agentic tool adherence |

**Decision:** run one **~30B-total / ~3B-active, 4-bit** model. If it does not fit the 20.5 GB inference budget in Section C, apply the trimming ladder there *before* considering a smaller family.

### Quantization and context

- **Q4_K_M or IQ4_XS** for GGUF. Avoid Q2/Q3 for the primary coding model: tool-call syntax and long-range instruction adherence degrade faster than prose quality.
- **Resident context 24K; working context 16–20K; compact at ~18K.** Do not provision 128K. Three reasons: KV memory, degraded small-model behavior in long contexts, and the fact that **long horizons are achieved by compaction + external memory, not by a larger window.**
- Keep the **system prompt and project brief as a stable prefix**; vary only the task suffix. Enable prefix/cache reuse. On a prefill-heavy agentic workload this is one of the cheapest real speedups available.
- **Never use partial CPU layer offload to "make it fit."** Offloading MoE experts to CPU destroys the bandwidth advantage. Either the whole model fits on Metal or you pick a smaller model.

### Engine operational choices

- One server process, **bound to 127.0.0.1**, `--parallel 1`.
- **Keep it resident across tasks.** Reload cost for a ~17 GB file is seconds to tens of seconds depending on the drive; per-task reloading is pure waste.
- Use per-task **sessions/slot state**, not per-task processes.
- Restart the server on a schedule or on degraded health (leaking RSS, rising p95 latency), not on every task.

---

# 2. Agent runtimes / harnesses

### The market splits into three things people confuse

1. **Executor** — runs one task in one directory: reads files, edits, runs tests, iterates. (Codex CLI, Claude Code, Aider, Goose, Cline.)
2. **Platform** — adds a UI, sandbox runtime, session store, sometimes multi-agent. (OpenHands, SWE-agent, various hosted agent products.)
3. **Control plane** — owns the durable task queue, budgets, permissions, scheduling, recovery, and cross-project routing.

**Almost every product is a 1 or a 2. Almost none is a 3 that fits your requirements.** A coding CLI tied to a cwd is not a cross-project autonomous operator. A platform tied to a Docker VM is not a good fit for 32 GB unified memory.

### Recommendation: own the control plane, rent the executor

```
Your code (durable, auditable, ~1.5k LOC):
  queue + leases + budgets + policy + role synthesis + recovery + memory

Rentable / swappable:
  executor that implements run(task, context, on_tool) -> result
```

The **adapter boundary** is what makes this robust to 2026 churn. Three adapters:

| Adapter | Implementation | Used for |
|---|---|---|
| `codex` | Codex CLI in `exec`/non-interactive mode, local provider, structured event capture | Coding, debugging, refactors |
| `native` | ~400-line loop: 10 fixed tools, strict JSON tool schema, diff-based edits | Research, documentation, orchestration subtasks |
| `batch` | No LLM. Deterministic script + verifier | Test runs, PDF extraction, dataset analysis, git operations |

**Do not give the model 40 MCP tool schemas.** Small and mid-size local models degrade sharply as tool count grows. Ten well-named, narrowly-scoped tools outperform forty generic ones. Add MCP later only for a capability you cannot implement in 50 lines.

### Why not OpenHands / SWE-agent as the core

- **OpenHands** assumes a container runtime. On macOS that means a Linux VM whose RAM comes out of your 32 GB, plus a filesystem hop. Its strengths (browser GUI, hosted runtime, multi-agent events) are not your bottleneck.
- **SWE-agent** is an excellent *benchmark* agent with a carefully designed action interface. It is not a 24/7 cross-project operator with a task queue and an approval system.
- **Aider** is mature and git-native, but it is an edit loop, not an orchestrator. **Use its repo-map idea as a deterministic tool, not Aider as your brain.**

---

# 3. Multi-agent architecture

### Terminology, precisely

| Term | What it actually is on this machine |
|---|---|
| Agent **definition** | A row of data: role charter, allowed tools, model class, budget, termination condition |
| Agent **instance** | A row in SQLite: id, role, task, state, context reference, spend |
| **Worker** | An OS process that leases an instance and calls the model |
| **Slot** | A concurrency permit for the inference server |
| **Logical agent** | An instance that may be parked, blocked, awaiting approval, or archived |
| **Swarm** | Peer-to-peer agents negotiating shared state — **rejected here** |
| **Coordinator/worker** | Hub-and-spoke over a durable blackboard — **chosen** |

**100+ logical agents is trivial. 100 concurrent LLM instances is physically impossible on 32 GB and would be counterproductive if it weren't.** Reframe the requirement as: *100+ concurrent logical agents, 1 concurrent inference slot, 4–8 concurrent I/O slots.*

### The design that maximizes useful throughput

- **12 role templates, not 100.** Planner, repo-scout, implementer, test-author, debugger, reviewer, research-scout, source-verifier, synthesist, doc-writer, experiment-runner, memory-curator.
- **Dynamic specialization = charter synthesis, not new code.** The planner generates `{objective, success_test, allowed_tools, budget, termination}` from a template. The policy engine validates it. An agent can never grant itself a tool.
- **Pipeline parallelism, not model parallelism.**

  ```
  plan[LLM] → retrieve[IO] → edit[LLM] → test[IO] → review[LLM] → commit[IO]
  ```

  While the LLM stage runs, the *next* task's retrieval and the *previous* task's tests run in the I/O pool. Only LLM stages contend. This is where the real overnight throughput comes from.
- **Path-ownership locks.** Each writing instance owns an explicit set of paths. The supervisor rejects edits outside them. This prevents the classic multi-agent clobbering failure far more reliably than "merge and hope."
- **Git worktrees per writing task.** Useful for dirty-state isolation and for overlapping sequential tasks. **Do not pretend worktrees create LLM parallelism** — they don't.
- **Verifier ≠ author.** The reviewer sees the diff, the spec, and the test output. It does not see the author's reasoning. Deterministic gates (tests, typecheck, lint) take precedence; an LLM reviewer may add findings but cannot overturn a passing deterministic gate without a recorded rationale.
- **Best-of-N only for hard, verifiable tasks.** Generate 2–3 candidate solutions sequentially, select with the test suite. This often beats three retries of one trajectory, because verification is cheap and the failure modes are uncorrelated. Never use vote-counting as a truth mechanism for research claims.

---

# 4. Coding agents

### Evaluation against your actual requirements

| Requirement | Codex CLI | Claude Code | Aider | Goose | Native loop |
|---|---|---|---|---|---|
| Headless / non-interactive | yes | yes | yes | yes | yes |
| Local OpenAI-compatible endpoint | documented provider config | proxy-dependent | yes | yes | direct |
| Built-in macOS sandbox | yes (Seatbelt-based) | vendor-managed | no | partial | you build it |
| Worktree-aware | via cwd + your supervisor | via cwd | git-native | via cwd | you build it |
| Subagents / delegation | harness-specific | strong | no | recipe-based | **your control plane** |
| Long-running durable tasks | **your control plane** | **your control plane** | no | **your control plane** | **your control plane** |
| Local/private by default | yes | no | yes | yes | yes |
| Auditability of tool calls | moderate | low (closed) | high | moderate | **total** |

**Decision: Codex CLI as the coding executor, behind your adapter.** The durable queue, cross-project routing, worktree lifecycle, budgets, and approvals live in *your* layer regardless of which executor you pick. That is the correct separation.

### Hard compatibility gate (Phase 0/2)

Local models frequently fail at the exact tool-call serialization a harness expects. Before committing:

1. Run **30 fixed coding tasks** through the adapter.
2. Measure: tool-call parse failure rate, edit-application failure rate, tasks passing tests unaided, tokens/task, wall-clock/task.
3. **Acceptance: <5% tool-call parse failures and ≥60% unaided pass rate on your task set.** These are *your* thresholds, not published benchmarks.
4. If it fails: switch to the native loop with a stricter, smaller tool schema. **The architecture does not change.**

### Repository understanding without an LLM

Build a deterministic **repo map** with tree-sitter tags + `ripgrep` + a dependency/import graph. Feed the worker a compact map plus the 5–10 most relevant files, not a repo dump. This is cheaper, more reliable, and more reproducible than "let the model explore for 20 minutes."

---

# 5. Research agents

### Retrieval stack, in order of need

| Need | Tool | Cost | Notes |
|---|---|---|---|
| Scholarly discovery + citation graph | **OpenAlex** | free, no key for modest use | Best open baseline; entities, concepts, citations |
| Preprints + full text | **arXiv API** | free | Official, stable, rate-limited politely |
| DOI / metadata / retraction signals | **Crossref** | free | Resolve and normalize citations |
| Semantic / citation-context search | **Semantic Scholar Graph API** | free tier, key | Add after OpenAlex proves insufficient |
| General web | **direct `fetch(url)`** first | free | Most research starts from a known URL |
| General web discovery | **SearXNG** in a small Lima VM, on demand | free | ~0.5 GB service + VM RAM; start only when needed |
| HTML → clean text | **trafilatura** | free, light | Deterministic, fast |
| PDF → text + spans | **PyMuPDF** | free, light | Keeps page/offset provenance |
| OCR fallback | **Apple Vision** via `pyobjc` | free, on-device | Better than tesseract for mixed layouts |
| Browser interaction | **Playwright**, headless, dedicated profile | free | Deterministic actions, not an LLM-per-click agent |

**Avoid heavy PDF stacks (marker, MinerU, docling) as a default.** They pull in PyTorch and multi-GB memory for gains you do not need on text-based papers. Add **Grobid** later only if you need citation-level structuring across a large corpus.

### The anti-hallucinated-citation architecture

This is the most important design element in the research subsystem. **The model never writes a bibliography.**

```
1 DISCOVER  → source row {source_id, doi/arxiv_id, url, retrieved_at, content_hash}
2 ACQUIRE   → raw bytes on external SSD; extracted text with page + span offsets
3 GROUND    → evidence row {evidence_id, source_id, page, span, verbatim_quote}
              CODE CHECK: normalized quote must exist in extracted text. Else reject.
4 EXTRACT   → claim row {claim_id, text, evidence_ids[], status}
              CODE CHECK: every claim must reference ≥1 existing evidence_id. Else reject.
5 VERIFY    → separate pass, context = claim + quoted evidence ONLY. No web.
              Output: supported | unsupported | contradicted | insufficient
6 CHALLENGE → for high-stakes claims, run a disconfirming query.
              Record "no counter-evidence found" — which is NOT "true".
7 CONTRADICT→ cluster claims across sources; surface opposing pairs. Do not auto-resolve.
8 SYNTHESIZE→ model writes prose with [[evidence_id]] placeholders.
9 RENDER    → renderer resolves placeholders from SQLite and generates citations.
              Any unresolved placeholder → report build FAILS. No report emitted.
```

Additional controls:

- **Provenance tiers** stored on every source: peer-reviewed primary / preprint / secondary / blog / social. The renderer surfaces tier alongside citation.
- **Retraction and version checks** via Crossref/OpenAlex before citing a paper.
- **Claim persistence** with supersession: a new finding does not overwrite an old one; it links as `supersedes` with a reason.
- **Two-context verification.** The verifier must not see the synthesist's narrative. Otherwise it confirms the story instead of checking the evidence.

This converts "the agent hallucinated a citation" from an inevitable failure into a **schema violation that cannot pass the build**.

---

# 6. Persistent memory

### Layers, and when to add them

| Layer | Store | When | Why |
|---|---|---|---|
| **Artifacts** | Filesystem, Git-versioned | Day 1 | Reports, code, diffs, notes. Diffable, reviewable, backuppable. |
| **Episodic** | SQLite `events` (append-only) + run summaries | Day 1 | Every tool call, output hash, decision, failure. The recovery and audit substrate. |
| **Semantic / project** | `memory/projects/<slug>/{PROJECT,DECISIONS,FINDINGS}.md` | Day 1 | Human-readable, model-readable, Git-diffable. ADRs for decisions. |
| **Retrieval index** | SQLite **FTS5** (BM25) | Week 1 | Zero infrastructure. Surprisingly strong for code, names, error strings, exact phrases. |
| **Hybrid retrieval** | `sqlite-vec` + small embedding model + Reciprocal Rank Fusion | Month 1+, only if FTS5 recall disappoints | In-process extension. No server. No new service to operate. |
| **Relations** | SQLite `entities` / `relations` tables | Only when multi-hop queries become real | Not Neo4j. |
| **Global memory** | `memory/global/`, explicitly promoted | Month 2+ | Project-local facts must not silently become global truth. |

### Rules that matter more than the store choice

1. **Filesystem is the worker's source of truth. SQLite is the control plane's source of truth.** Do not try to mirror them.
2. **Semantic memory is written by a curator, not by every agent.** A scheduled job proposes memory edits; a verification pass accepts them. Unchecked self-written "facts" poison a lab faster than any model weakness.
3. **Every semantic fact carries provenance** (source task, evidence IDs, date, confidence, superseded-by).
4. **Compact, don't accumulate.** A task receives a curated brief + top-k retrieved context, never the full project history.
5. **Embeddings are optional.** FTS5 + a good repo map + structured task state solves most personal-lab retrieval. Add vectors only against a measured recall gap.

**Do not install a "memory layer" product that auto-writes facts.** Provenance loss is the hidden cost.

---

# 7. Computer control

### Capability ladder, safest first

| Level | Mechanism | Autonomy | Boundary |
|---|---|---|---|
| 1 | **Typed tools** (`read_file`, `apply_patch`, `git`, `run_test`, `fetch`, `cite`) | High | Path canonicalization + policy per call |
| 2 | Scoped shell (allowlisted command families) | Higher | Parser + allowlist, not regex blacklist |
| 3 | General shell as dedicated UID | High | FS ACLs + TCC + no credentials |
| 4 | General shell inside Seatbelt profile | High | Adds a syscall/file/network fence |
| 5 | General shell inside a Lima/vz Linux VM | High, untrusted-safe | Separate kernel; 4–6 GB RAM; on demand only |
| 6 | Browser, dedicated headless profile | High | Egress allowlist, no personal cookies, SSRF guards |
| 7 | AppleScript / JXA for specific apps | Moderate | Per-app, explicitly granted |
| 8 | GUI control (Accessibility + Screen Recording) | Highest | **Rejected for v1** |

### The highest-leverage security decision

**Do not give the agent a general `shell` tool in v1.** Give it ten typed tools. This simultaneously:

- makes policy enforceable (you can validate `git(op, args)`; you cannot reliably validate an arbitrary bash string),
- eliminates an entire class of prompt-injection-driven destruction,
- and *improves* small-model reliability, because the action space is legible.

Add general shell at Phase 5, behind UID isolation + Seatbelt + approval gates.

### Isolation model

- **Dedicated standard macOS user `aiworker`**, no admin group, own home, own Git identity, own SSH keys.
- **No TCC grants** for Documents, Desktop, Downloads, Photos, Messages, Screen Recording, Accessibility, or Full Disk Access.
- Your personal home set to `mode 700`. (macOS users commonly share the `staff` group, so default home permissions are not a sufficient boundary — verify this on your install.)
- **Per-task git worktree**, one branch per task, owned paths only.
- **Secrets broker**: a separate **root-owned** launchd daemon holding a dedicated Keychain, exposing a Unix domain socket, authenticating by peer UID, and performing only a fixed allowlist of operations. The agent requests *"push this commit to this allowed remote"*; it never receives the key.
- **No credentials in the worker environment.** The supervisor constructs a minimal env per subprocess.

### Browser safety

Dedicated profile, no personal logins, egress allowlist, downloads into task scratch only. **Explicitly block `file://`, loopback except the inference port, link-local, and private LAN ranges** — otherwise a fetched web page becomes an SSRF pivot into your router or Tailscale host.

### GUI

Terminal + filesystem + browser covers software development and research. GUI control requires OS-wide permissions that materially widen the boundary. If you later need it, do it in a **separate agent-dedicated session or VM**, never in your personal desktop session.

---

# 8. Always-on operation

### macOS specifics that actually matter

| Concern | Mechanism |
|---|---|
| Start at boot, no login required | **LaunchDaemon** with `UserName=aiworker` (not a LaunchAgent, which needs a login session) |
| Crash restart | `KeepAlive`, `RunAtLoad`, `ThrottleInterval`, `ExitTimeOut` |
| Sleep prevention | Supervisor holds `caffeinate -dims`; plus `pmset -a sleep 0 autopoweroff 0` |
| Power-return recovery | `pmset -a autorestart 1` |
| Hung supervisor | **Independent watchdog daemon** checks heartbeat file mtime; kills and restarts the process group |
| Task persistence | SQLite WAL + leases + checkpoints; reclaim expired leases on startup |
| Overnight approval deadlock | `blocked_approval` is a parked state; planner prefers unattended-safe work and batches approvals for morning |
| Model health | Nightly 1-turn smoke test; restart on RSS growth or p95 latency regression |
| Log growth | Rotating JSONL internal; daily rotation to external cold storage |

### The FileVault / auto-login conflict — a real residual risk

**macOS FileVault and unattended auto-login are mutually exclusive.** Do not let anyone sell you a "24/7 Mac" design that ignores this.

Chosen resolution:

- **Keep FileVault on.** Security wins.
- Run the supervisor as a **LaunchDaemon**, which does not require a login session.
- Secrets live in a **dedicated keychain** managed by the root broker, not your login keychain.
- **After a cold power loss or a cold boot, the machine needs one manual/FileVault unlock.** Tailscale cannot unlock FileVault pre-boot. Design for *warm* restarts (which are the common case) and accept this documented residual risk.

If unattended cold-boot recovery is an absolute requirement, the alternative is an unencrypted agent-only data volume plus an encrypted system volume — a deliberate, documented security trade, not a default.

### Recovery semantics

- Every task has an **idempotency key**.
- Every side effect is recorded before/after execution.
- On recovery, **inspect actual state** (git status, worktree contents, DB rows) rather than blindly replaying.
- Checkpoint after each successful tool batch: task state + compacted context + worktree commit. Resume from the checkpoint, not from a 200K-token transcript.

---

# 9. Remote access

```
Phone / laptop
   │  WireGuard (Tailscale) — no public inbound ports
   ▼
Mac mini, Tailscale interface only
   ├── Tailscale Serve → HTTPS → 127.0.0.1:8765 (dashboard + API)
   ├── SSH over Tailscale (key auth, password auth off)
   └── Redacted alert channel (optional)
```

- **Bind the control API to 127.0.0.1.** Reach it via **Tailscale Serve**, which provides HTTPS and identity-aware access without exposing a port. Do not use Funnel or port forwarding.
- **Auth:** Tailscale identity + local bearer token + per-device session. Approvals are separate from authentication.
- **Approval binding:** an approval is valid for exactly `(task_id, action_hash, policy_version, nonce, expires_at)`, single-use. Approving "commit diff X" cannot be replayed to authorize "commit diff Y."
- **Phone UX:** show the diff, the test results, the risk class, and the budget. Buttons: Approve / Reject / Approve-with-narrower-scope. **Never a blind "yes."**
- **Notifications:** redacted only — task ID, status, duration, budget consumed. **No code, no document excerpts, no filenames that reveal personal projects.**
  - Primary: open the dashboard over Tailscale (zero third-party data).
  - Optional push: Telegram bot or ntfy, with a strict redaction filter. Understand that this leaks *metadata* to a third party. If that is unacceptable, use pull-based dashboard polling only.
- **Emergency stop must not depend on the supervisor being alive:** a flag file in a root-owned directory, checked by both the supervisor before every tool call and by an independent watchdog that kills the process group.

---

# 10. Storage architecture

| Data | Location | Rationale |
|---|---|---|
| macOS + apps | Internal | — |
| **Active workhorse model** | **Internal** | Fast cold start; no external-drive sleep/unmount dependency |
| One fallback model (optional) | Internal | Only if budget allows |
| Model archive (all other quants/families) | **External** | Cold; loaded rarely |
| Canonical Git repos + active worktrees | **Internal** | High small-file I/O; git ops are latency-sensitive |
| SQLite queue + events + FTS index | **Internal** | WAL writes; **never the only copy on an external disk** |
| Agent venvs, build caches, npm/pip caches | Internal, size-capped | Rebuild cost vs. capacity |
| Research PDFs, HTML corpus, datasets | **External** | Bulk sequential reads; large |
| Experiment artifacts, model outputs, reports | External, with internal pointers | — |
| Hot logs (7–14 days) | Internal, rotating | — |
| Cold logs, audit archive | **External** | Append-only, hash-chained |
| Backups | **External + one off-machine copy** | See below |

### Capacity plan (512 GB internal)

Approximate targets: OS/apps 60 GB · active models 25–40 GB · repos + worktrees 40–80 GB · caches/venvs 30–50 GB · DB + memory 2–5 GB · logs 5–10 GB · **free headroom ≥60 GB**. APFS snapshots and macOS swap both need room. **Do not run the internal SSD near full.**

### External 1 TB

Model archive 200–300 GB · corpus 150–300 GB · datasets/artifacts 100–200 GB · backups 100–150 GB. **Do not archive ten models you will never run.** One active + one fallback is enough.

### Reliability rules

- Consumer external SSDs sleep, unmount, and develop firmware issues. **The supervisor must verify the mount and a write probe at startup and before any corpus operation.**
- **Never put the only copy of the queue DB or the active model on the external drive.**
- Back up SQLite with **`VACUUM INTO` or the `.backup` API**, never by copying the `.sqlite` file while WAL is active.
- Minimum viable backup: Git push to a private remote + daily encrypted archive of `state/` + `memory/` to external + **weekly off-machine encrypted copy**. Two internal/external SSDs in one room are not a backup strategy.

---

# A. Recommended technology stack

| Layer | Recommended | Alternatives | Why |
|---|---|---|---|
| Interface | Tailscale Serve + small PWA + SSH | Telegram bot, Open WebUI | No public exposure; approval UX you control |
| Supervisor | Python + launchd LaunchDaemon | systemd (not macOS), tmux+cron | Durable leases, crash recovery, budget enforcement |
| Orchestrator | Custom planner/decomposer over SQLite | LangGraph + SQLite checkpointer | Policy lives in code you own |
| Task queue | **SQLite WAL, leased rows** | Redis, NATS, Celery | One inference consumer; a broker is overhead |
| Executors | Codex CLI (coding) + native loop (research) | Goose, Aider, Claude Code (cloud only) | Swap-safe adapter boundary |
| Model router | In-process deterministic class→config map | LiteLLM | One resident model; routing is context/budget/role, not weights |
| Inference | **llama.cpp Metal server, 1 slot** | MLX, Ollama | Constrained decoding + tool parsers + quant control |
| Weights | ~30B-A3B MoE Q4, 24K ctx | 14–20B dense Q4 | Best useful-work-per-bandwidth profile |
| Tools | 10 typed native tools | MCP server fleet | Legible action space; enforceable policy |
| Retrieval | FTS5 BM25; `sqlite-vec` later | Qdrant, Chroma, Milvus | Zero services at personal scale |
| Memory | Git Markdown + SQLite | Letta, Mem0, Zep | Provenance and diffability |
| Research | OpenAlex + arXiv + Crossref + PyMuPDF + trafilatura | SearXNG, Semantic Scholar, Grobid | Free, keyless, primary-source-oriented |
| Browser | Playwright, dedicated headless profile | browser-use, Firecrawl | Deterministic actions, no LLM-per-click |
| Sandbox | Dedicated UID + worktree + path jail; Seatbelt; Lima for untrusted | Docker Desktop, vz directly | No always-on VM RAM tax |
| Secrets | Root-owned broker daemon + dedicated Keychain | env vars, `.env` files | Executor cannot read credentials even if compromised |
| Remote | Tailscale + Serve | WireGuard self-hosted, Cloudflare Tunnel | Identity-aware, no inbound ports |
| Observability | JSONL + SQLite events + a status page | Prometheus/Grafana | You need task-level audit, not a metrics platform |
| Backup | `VACUUM INTO` + restic or encrypted tar + private Git remote | Time Machine alone | WAL-safe, off-machine, restorable |

---

# B. Complete architecture diagram

```
                         ┌──────────────────────────────────────┐
                         │  PHONE / LAPTOP (off-site)           │
                         └───────────────┬──────────────────────┘
                                         │ WireGuard / Tailscale
                                         │ NO public inbound ports
                         ┌───────────────▼──────────────────────┐
                         │ Tailscale Serve → HTTPS              │
                         │ 127.0.0.1:8765                       │
                         │ dashboard · submit · approve · kill  │
                         └───────────────┬──────────────────────┘
                                         │
        ┌────────────────────────────────▼─────────────────────────────────┐
        │ SUPERVISOR  (launchd, UserName=aiworker, single process)          │
        │  scheduler · lease reclaimer · budget ledger · watchdog heartbeat │
        │                                                                 │
        │  ┌─────────────────── POLICY GATE (cross-cutting) ─────────────┐  │
        │  │ typed-tool validation · path jail · risk class · approvals │  │
        │  │ hard denies · resource/time/token caps · audit hash chain  │  │
        │  └────────────────────────────────────────────────────────────┘  │
        └───────────────┬─────────────────────────────────┬────────────────┘
                        │                                 │
        ┌───────────────▼──────────────┐   ┌──────────────▼─────────────────┐
        │ SQLITE  (WAL)                │   │ ROOT SECRETS BROKER            │
        │ tasks · leases · agents      │   │ separate daemon, Unix socket   │
        │ events · budgets · claims    │   │ peer-UID auth · scoped ops     │
        │ sources · evidence           │   │ agent NEVER sees key material  │
        └───────────────┬──────────────┘   └────────────────────────────────┘
                        │
        ┌───────────────▼──────────────────────────────────────────────────┐
        │ ORCHESTRATOR                                                     │
        │ planner → decompose → synthesize role charters → accept/reject   │
        │ blackboard: project facts · decisions · open questions · locks   │
        └───────────────┬──────────────────────────────────────────────────┘
                        │  leases one LLM task at a time
        ┌───────────────▼──────────────────────────────────────────────────┐
        │ WORKER POOL                                                      │
        │  LLM slot = 1                 I/O pool = 4–8 (no LLM)             │
        │  ┌─────────────┐ ┌──────────┐  ┌──────────┐ ┌────────────────   │
        │  │ coding      │ │ research │  │ tests /  │ │ fetch / PDF /  │   │
        │  │ (worktree)  │ │ / synth  │  │ builds   │ │ dataset / git  │   │
        │  └──────┬──────┘ └─────────┘  └──────────┘ └────────────────┘   │
        │         └──────┬──────┘        ▲ runs concurrently with LLM      │
        └───────────────────────────────┴─────────────────────────────────┘
                         │
        ┌────────────────▼─────────────────────────────────────────────────┐
        │ MODEL ROUTER (in-process, deterministic)                         │
        │ role → context budget · thinking budget · tools · sampling       │
        │ optional redacted cloud escalation (OFF by default)              │
        └────────────────┬─────────────────────────────────────────────────┘
                         │ OpenAI-compatible, loopback only
        ┌────────────────▼─────────────────────────────────────────────────┐
        │ llama.cpp METAL SERVER · 127.0.0.1:8080 · parallel=1             │
        │ one resident ~30B-A3B Q4 model · 24K context · prefix cache      │
        └─────────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────▼─────────────────────────────────────────────────┐
        │ TYPED TOOLS (all pass through POLICY GATE)                       │
        │ read · patch · git · test · search · fetch · pdf · cite          │
        │ memory_query · spawn_task                                        │
        └─────────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────▼─────────────────────────────────────────────────┐
        │ MEMORY                                                           │
        │ Git Markdown (semantic/project/decisions)                        │
        │ SQLite + FTS5 (episodic/index)  →  sqlite-vec later              │
        │ Filesystem artifacts (internal hot / external cold)              │
        └──────────────────────────────────────────────────────────────────┘
```

---

# C. Hardware / resource plan

### Design budgets — **not measurements**

These are admission-control targets. Phase 0 replaces them with measured values.

| Consumer | Coding profile | Research profile |
|---|---:|---:|
| macOS + WindowServer + daemons | 4.5 GB | 4.5 GB |
| **Inference total** | **20.5 GB** | **20.5 GB** |
| — weights (~30B-A3B Q4) | 17.0 | 17.0 |
| — KV @ 24K (96 KiB/token) | 2.25 | 2.25 |
| — Metal buffers + allocator | 0.8 | 0.8 |
| — server runtime | 0.45 | 0.45 |
| Supervisor + SQLite + FTS | 0.4 | 0.4 |
| Worker + tool subprocesses | 1.2 | 0.8 |
| Dev toolchain (one active build/test) | 2.0 | — |
| Headless Chromium (2 tabs) | — | 2.0 |
| PDF/dataset extraction scratch | — | 0.8 |
| **Hard headroom** | **3.4 GB** | **3.0 GB** |
| **Total** | **32.0 GB** | **32.0 GB** |

**Profile switching, not model switching.** The supervisor does not run a browser and a build toolchain simultaneously at full size. It moves tasks between profiles so the inference budget stays constant.

### Concurrency decisions

| Resource | Decision |
|---|---|
| Concurrent large-model workers | **1** |
| Concurrent small-model workers | **0** in v1 |
| Concurrent I/O workers | **4–8** (bounded by task type) |
| Concurrent logical agents | **100–256 parked/running/blocked rows** |
| Model swapping | **No** in v1 |
| Multiple resident models | **No** in v1 |
| Context | **24K resident, 16–20K working, compact at ~18K** |
| Quantization | **Q4_K_M / IQ4_XS**; never Q2 for the workhorse |

### Trimming ladder (apply in order if the budget is exceeded)

1. Context 24K → 20K → 16K (KV drops 2.25 → 1.9 → 1.5 GiB).
2. Quant Q4_K_M → Q4_0 → IQ4_XS. **Re-run the agentic gate after each step**; prose quality is not the metric.
3. Stop the browser / defer builds (profile switch).
4. Reduce worker subprocess footprint; cap build parallelism (`-j2`, not `-j$(nproc)`).
5. Downsize to a 14–20B dense model with a larger context.
6. **Only then** consider a second small model.

### Admission control

Before granting an LLM lease, the supervisor checks `sysctl vm.swapusage` and `memory_pressure`. If swap use is above ~2 GB and growing, or available memory fraction is below ~10%, **pause leasing**. Park the task; keep running I/O work. This is more valuable than any tuning flag.

### Expected bottlenecks, ranked

1. **Unified memory capacity → swap** (fatal; prevented by admission control).
2. **Agentic reliability → retries** (often dominates wall-clock more than raw token rate).
3. **Memory bandwidth → prefill/decode rate.**
4. **Test/build latency** (mitigated by I/O pipelining).
5. **Research network latency** (mitigated by concurrent fetch).
6. SSD capacity.

**Planning assumption, not a benchmark:** budget roughly **1–3 nontrivial coding tasks per hour** for overnight planning, and measure your real number in Week 1. 100 logical agents does **not** mean 100 tasks per night.

---

# D. Agent architecture — 100+ logical agents, one LLM

### Role templates (12)

`planner`, `repo-scout`, `implementer`, `test-author`, `debugger`, `reviewer`, `research-scout`, `source-verifier`, `synthesist`, `doc-writer`, `experiment-runner`, `memory-curator`.

### A role is data

```yaml
# roles/implementer.yaml
id: implementer
charter_template: roles/implementer.md
allowed_tools: [read, patch, git, test, memory_query]
model_class: workhorse
context_budget: 18000
token_budget: 60000
wall_clock_seconds: 1800
max_children: 3
max_compactions: 2
termination:
  - success_test_passes
  - budget_exhausted
  - no_progress_count >= 3
approval_required: [git_push, merge, delete_outside_worktree]
```

### Dynamic specialization

The planner emits a **charter**, not a process:

```json
{
  "role": "implementer",
  "specialization": "migrate the rate limiter to token-bucket",
  "objective": "...",
  "success_test": "pytest tests/rate_limit -q",
  "owned_paths": ["src/rate_limit/", "tests/rate_limit/"],
  "budget": {"tokens": 40000, "seconds": 900},
  "termination": {"no_progress_count": 3}
}
```

The policy engine validates the charter against the template's **maximum** permission set. **A charter can narrow permissions, never widen them.**

### Lifecycle

```
proposed → admitted → leased → running → verifying
                                      ├→ accepted → archived
                                      ├→ retry (bounded)
                                      ├→ blocked_approval → (morning) → leased
                                      └→ failed → archived + follow-up task
```

### Anti-runaway controls

| Control | Value / mechanism |
|---|---|
| Per-task token budget | 20k–80k, set by role |
| Per-task wall clock | 15–30 min |
| Max children per task | 3 |
| Max total active instances | 256 rows, 1 LLM lease |
| No-progress detector | identical error hash 3× → escalate, stop retrying |
| Max context compactions | 2, then fail cleanly |
| Global daily budget | token + wall-clock + optional $ cap |
| Circuit breaker | repeated server errors → pause queue, alert |
| Global kill | root-owned flag file + independent watchdog |

### Why not a swarm

Peer-to-peer swarms on a single model server duplicate context, conflict on shared files, and have no natural stopping condition. A **coordinator + blackboard + path-ownership locks + deterministic verifier** gives you the same decomposition benefits with bounded cost and auditable state.

---

# E. Model strategy

**One resident model, many roles.** On 32 GB this is not a compromise — it is the correct design. "Model routing" here means routing **context budget, thinking budget, tool subset, sampling, and best-of-N**, not routing between weight sets that cannot coexist.

| Task | What actually runs | Configuration |
|---|---|---|
| **Planning / decomposition** | Workhorse | Highest thinking budget within role; 8–12K context; structured plan output with per-subtask budgets |
| **Coding** | Workhorse via Codex adapter | 16–18K working context; compact repo map; strict diff edits; test-driven loop |
| **Debugging** | Workhorse | Error trace + minimal reproducer + owned files; *not* the whole repo; best-of-2 on hard failures |
| **Research discovery** | **No LLM** — deterministic API queries | OpenAlex/arXiv/Crossref; LLM only to rank and select |
| **PDF / evidence extraction** | **No LLM** — PyMuPDF + trafilatura | Quoted spans stored with offsets |
| **Claim verification** | Workhorse, **separate context** | Claim + verbatim evidence only; no web; structured verdict |
| **Summarization / compaction** | Workhorse at low thinking budget | Small, bounded input; output schema enforced |
| **Classification / routing** | **No LLM** — rules + FTS5 + task metadata | A classifier LLM is a tax with no benefit at this scale |
| **Embeddings** (later) | Small embedding model, on demand | ~0.3–0.6 B class; not resident; not an LLM slot |
| **Final synthesis** | Workhorse, evidence-only context | Placeholder citations; renderer validates; optional redacted cloud escalation |
| **Adversarial review** | Workhorse, fresh context | Sees diff + tests + spec; never the author's rationale |

**When cloud is genuinely worth it:** hard long-horizon planning, a debugging session that has failed three local attempts, adversarial review of a security-sensitive change, synthesis over 100+ pages. Cap it, redact it, log it, and make it opt-in per task class.

**When local is better:** bulk edits, test-driven iteration, private repositories, high-volume summarization, anything repeated thousands of times, and all offline operation.

---

# F. 24/7 architecture

### Process topology

| Daemon | User | Restart |
|---|---|---|
| `lab.inference` | aiworker | KeepAlive, ThrottleInterval 10 |
| `lab.supervisor` | aiworker | KeepAlive, ThrottleInterval 10 |
| `lab.control` | aiworker | KeepAlive |
| `lab.watchdog` | **root** | KeepAlive; monitors supervisor heartbeat |
| `lab.broker` | **root** | KeepAlive; Unix socket only |
| `lab.searxng` (optional) | via Lima | **on demand**, not always-on |

### Overnight loop

```
00:00  health check → model smoke test → mount probe → budget reset
00:05  reclaim expired leases → reconcile worktrees → requeue interrupted tasks
00:10  planner inspects queue + project goals → admits unattended-safe tasks
       loop:
         lease → build context → execute → verify → checkpoint → document
         if approval needed: park in blocked_approval, pick another task
         if no safe work remains: run research/doc/memory curation
06:30  stop admitting new long tasks; finish or checkpoint the current one
07:00  write overnight report → queue approvals → send redacted alert
```

### Failure recovery matrix

| Failure | Detection | Recovery |
|---|---|---|
| Worker crash | lease heartbeat expires | reclaim lease, inspect worktree, resume from checkpoint |
| Supervisor crash | watchdog heartbeat mtime | launchd restarts; startup reclaims leases |
| Inference crash | health probe / connection error | launchd restarts; task retries with backoff |
| macOS reboot | LaunchDaemon RunAtLoad | same as supervisor crash; **FileVault cold-boot caveat applies** |
| Power loss | `pmset autorestart 1` | boot → unlock required → auto-recovery |
| External SSD unmounted | mount + write probe | pause corpus tasks; continue coding tasks |
| Runaway agent | budget / no-progress / wall clock | kill process group, mark failed, create follow-up |
| DB corruption | WAL + integrity check | restore last `VACUUM INTO` snapshot |
| Model quality regression | weekly fixed task suite | rollback model pin + quant pin |

### Sleep / power

```
sudo pmset -a sleep 0 autopoweroff 0 autorestart 1
# supervisor holds: caffeinate -dims
```

Defer macOS automatic reboots, but **do not design around updates never happening** — the recovery path must work regardless.

---

# G. Remote-control architecture

```
Phone
  └─ Tailscale (WireGuard)
       └─ https://lab.<your-tailnet>.ts.net   [Tailscale Serve]
            └─ 127.0.0.1:8765
                 ├─ GET  /status          → queue, active task, budgets, health
                 ├─ GET  /tasks/<id>/log  → streamed JSONL
                 ├─ GET  /tasks/<id>/diff → actual git diff
                 ├─ POST /tasks           → submit objective + budget + scope
                 ├─ POST /approve         → {task_id, action_hash, nonce}
                 ├─ POST /reject
                 └─ POST /kill            → global stop
```

**Security properties**

- No listener on a public or LAN interface. Only loopback + Tailscale.
- Tailscale ACLs restrict the dashboard to your own devices.
- Approval is **bound to the artifact hash**, single-use, short-TTL.
- `/kill` works even if the model server is hung: it sets a root-owned flag and signals the process group.
- SSH over Tailscale for deep debugging; key-only; password authentication disabled.

**Notification contract**

Allowed: `task_id`, `status`, `duration`, `tokens`, `approval_needed`.
Never allowed: source code, document text, file paths revealing personal projects, URLs of private resources.

**If you want zero third-party metadata leakage:** no push service. Use the dashboard over Tailscale, optionally with a periodic iOS Shortcut that polls it.

---

# H. Security architecture

### Enforcement is in code, never in the prompt

A Markdown instruction to "be careful" is not a security boundary. Every tool call passes through the supervisor's policy gate **before execution**.

```python
def gate(task, call):
    if call.tool not in roles[task.role].allowed_tools:
        return DENY("tool not in charter")
    if not path_jail.contains(task.worktree, call.paths):
        return DENY("path outside owned workspace")
    risk = classify(call)                      # allowlist-based, not regex blacklist
    if risk == HARD_DENY:
        audit.deny(task, call); alert(task); return DENY
    if risk == APPROVAL and not valid_approval(task, call):
        queue.park(task, "blocked_approval")
        raise NeedsApproval
    enforce_budgets(task, call)
    audit.append(task, call, risk)             # hash-chained, agent cannot write
    return execute(call)
```

### Approval matrix

| Fully autonomous | Pre-authorized (scoped, revocable) | Human approval every time | Hard deny |
|---|---|---|---|
| Read inside worktree | Dependency installation | `git push` / any remote write | Read broker key material |
| Edit inside owned paths | New network hosts | Merge / change to `main` | Disable audit or policy |
| `git status/diff/add/commit/branch/worktree` | Unlisted project scripts | `rm -rf`, `reset --hard`, `clean -fdx`, force-push | Modify own launchd unit / policy |
| Run declared tests, linters, builds | New role with new tools | sudo, `pmset`, firewall, ACLs | Reach LAN admin / metadata endpoints |
| Web fetch to allowlisted hosts | Budget increase | Read/export secrets; personal dirs; Keychain | Exfiltrate to unapproved endpoint |
| Write task memory namespace | Long runs (>30 min) | Email/message/publish to third parties | Spawn beyond budget |
| Spawn children within charter | | Spend money; install system software | Disable the watchdog |
| Generate documentation | | Access mail/messages/photos/personal browser | |

### Layered boundary

1. **Typed tools** — no general shell in v1.
2. **Path jail** — canonicalize, resolve symlinks, reject `..`, re-check after open.
3. **UID separation** — `aiworker` cannot read your home (`mode 700`) or your TCC-protected data.
4. **No TCC grants** — no Accessibility, Screen Recording, Full Disk Access, Messages, Photos.
5. **Worktree + path ownership** — no cross-task clobbering.
6. **Seatbelt profile** — additional file/network fence for subprocesses. *Deprecated API; treat as hardening, not the primary boundary, and test it against each toolchain.*
7. **Lima/vz VM** — separate kernel for untrusted repositories and dependency installation, 4–6 GB, started on demand.
8. **Secrets broker** — root-owned, peer-UID authenticated, fixed operation allowlist. No secret ever enters a model context or a worker env.
9. **Network egress allowlist** — proxy-enforced; block private ranges, loopback except inference, link-local.
10. **Audit** — append-only, hash-chained, written to a directory the agent UID cannot modify; rotated to external daily.

### Emergency stop

Three independent paths:
- Dashboard `/kill` → flag + SIGTERM to process group → SIGKILL after 5 s.
- **Root-owned flag file** checked before every tool call and every lease (works even if the model is stuck mid-generation).
- **Independent root watchdog** that kills the process group if the flag is set and the supervisor is unresponsive.

Offline fallback: revoke the device in Tailscale; physical power if necessary.

---

# I. Exact installation plan

> **Version discipline:** every pin below must be resolved by the Phase 0 probe. Flag names change between llama.cpp releases; always run `llama-server --help` on *your* build. Nothing below requires a cloud API key.

### Directory layout

```
/Users/aiworker/
  lab/
    supervisor/           # control plane
      pyproject.toml
      supervisor.py
      policy.toml
      roles/              # 12 YAML templates
      adapters/           # codex.py, native.py, batch.py
    state/
      lab.sqlite
      audit/              # agent UID cannot write
      checkpoints/
    work/                 # canonical repos
    worktrees/            # one per active task
    scratch/
    logs/
    memory/
      global/             # git
      projects/<slug>/    # PROJECT.md, DECISIONS.md, FINDINGS.md
      episodic/           # git
    models/active/        # ONE workhorse
    models/fallback/      # optional, only if budget allows
    vendor/
/Volumes/AgentVault/
  model-archive/  corpus/{pdf,datasets}/  research/  artifacts/  backups/  cold-logs/
```

---

### Phase 0 — Evidence and hardware baseline *(do this first)*

**Technologies:** system tools, `curl`, `jq`, Python.

```bash
# Hardware / OS baseline
sw_vers
sysctl -n machdep.cpu.brand_string
sysctl hw.memsize
df -h / /System/Volumes/Data
memory_pressure -Q | head -20
sysctl vm.swapusage

# Resolve CURRENT releases — this is the missing live research
for repo in ggml-org/llama.cpp ml-explore/mlx ml-explore/mlx-lm \
            openai/codex block/goose Aider-AI/aider \
            asg017/sqlite-vec lima-vm/lima SearXNG/SearXNG; do
  printf '%s\t' "$repo"
  curl -sS "https://api.github.com/repos/$repo/releases/latest" \
    | jq -r '[.tag_name, .published_at, .html_url] | @tsv'
done

# Resolve candidate model cards and quant artifacts
for m in Qwen/Qwen3-Coder-30B-A3B-Instruct \
         Qwen/Qwen3-30B-A3B \
         Qwen/Qwen3-32B; do
  curl -sS "https://huggingface.co/api/models/$m" \
    | jq '{id, lastModified, downloads, tags}'
done
```

**Then run the bake-off:**
1. One ~30B-A3B Q4 model via llama.cpp; the same family via MLX if available.
2. Measure: 24K-token prefill time, decode t/s, peak resident memory, tool-call parse success over 100 turns.
3. Run 30 fixed coding tasks through the candidate executor.

**Gate:** <5% tool-call parse failures; ≥60% unaided pass on your task set; no swap at peak.
**Test:** record the numbers in `lab/state/baseline.json`.
**Failure mode:** GitHub API rate limits → authenticate or space requests.
**Rollback:** none; this phase is read-only.

---

### Phase 1 — Minimal working system

```bash
brew install git ripgrep fd jq sqlite uv python@3.12 llama.cpp

# Dedicated non-admin user (store the generated password in YOUR keychain)
sudo sysadminctl -addUser aiworker -fullName "AI Worker" \
  -password "$(openssl rand -base64 24)"
sudo chmod 700 /Users/yourname          # verify your personal home is not group-readable

sudo mkdir -p /Users/aiworker
sudo chown aiworker:staff /Users/aiworker

# Become the agent user for all subsequent setup
sudo -u aiworker -i
mkdir -p ~/lab/{state/audit,state/checkpoints,work,worktrees,scratch,logs,models/active,vendor}
mkdir -p ~/lab/memory/{global,projects,episodic}
mkdir -p /Volumes/AgentVault/{model-archive,corpus/pdf,corpus/datasets,backups}

uv venv ~/lab/.venv
source ~/lab/.venv/bin/activate
uv pip install httpx pydantic pymupdf trafilatura

# Download ONE model. Pin the exact file from the Phase 0 probe.
uv pip install -U "huggingface_hub[cli]"
hf download <VERIFIED_MODEL_REPO> <VERIFIED_Q4_GGUF_FILE> \
  --local-dir ~/lab/models/active
```

Start the server (verify flags against your build):

```bash
llama-server \
  -m ~/lab/models/active/<VERIFIED_Q4_GGUF_FILE> \
  --host 127.0.0.1 --port 8080 \
  --ctx-size 24576 --parallel 1 --n-gpu-layers 99 \
  --jinja --flash-attn on --cache-reuse 4096
```

Smoke test:

```bash
curl -sS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"workhorse","messages":[{"role":"user","content":"Reply with exactly: OK"}],"stream":false}'
```

**Communications:** HTTP, loopback only.
**Test:** 20 turns with tool calls; watch `memory_pressure` and `vm.swapusage`.
**Failure modes:** OOM/swap → apply the Section C trimming ladder; tool-call malformation → adjust chat template/parser, not the prompt.
**Rollback:** delete the model file; stop the server. Nothing else depends on it yet.

---

### Phase 2 — Autonomous coding

```bash
# As aiworker, inside the venv
uv pip install tree-sitter tree-sitter-python tree-sitter-typescript

# Optional executor; verify the package name/version in Phase 0
npm install -g @openai/codex
```

`~/.codex/config.toml` (verify key names against your installed version):

```toml
model = "workhorse"
model_provider = "local"
sandbox_mode = "workspace-write"
approval_policy = "never"   # ONLY inside the supervisor's sandbox; policy lives upstream

[model_providers.local]
name = "local"
base_url = "http://127.0.0.1:8080/v1"
env_key = "LOCAL_API_KEY"
wire_api = "chat"
```

Supervisor-created worktree:

```bash
git -C ~/lab/work/proj worktree add \
  -b agent/task-0137 \
  ~/lab/worktrees/task-0137 main
```

**Control-plane core (the part you build):**

```python
# supervisor.py — skeleton, ~1.5k LOC with policy + adapters
while not stop_flag():
    reclaim_expired_leases()
    t = queue.lease(policy=policy, budgets=budgets)
    if not t:
        time.sleep(1); continue
    try:
        ctx = memory.project_view(t.project, t.brief)
        res = adapters[t.kind].run(t, ctx, on_tool=policy.gate)
        verdict = verify(t, res)          # tests first, LLM review second
        queue.transition(t, verdict)
        checkpoint(t, res)
        spawn_followups(t, res)
    except NeedsApproval:
        queue.park(t, "blocked_approval")
    except Exception as e:
        queue.retry_or_fail(t, e)
    finally:
        queue.release(t)
```

**Adapter contract:**

```
run(task, context, on_tool) ->
  {status, diff, artifacts[], tests[], tokens, summary, followups[]}
events: tool_call | tool_result | checkpoint | error | done
```

**Test:** a repo with a failing test suite; the agent must produce a green branch without touching `main`.
**Failure modes:** local tool-call parse failures → switch adapter to `native`; dirty worktree on crash → reconcile from git state, never blind replay.
**Rollback:** `git worktree remove --force ...`; delete the task branch. `main` is never touched by a worker.

---

### Phase 3 — Research agents

```bash
uv pip install pymupdf trafilatura httpx
uv pip install playwright && playwright install chromium
```

SQLite evidence schema (the anti-hallucination substrate):

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE sources(
  id INTEGER PRIMARY KEY,
  url TEXT, doi TEXT, arxiv_id TEXT,
  retrieved_at TEXT, content_hash TEXT, tier TEXT
);
CREATE TABLE evidence(
  id INTEGER PRIMARY KEY,
  source_id INTEGER REFERENCES sources(id),
  page INTEGER, span_start INTEGER, span_end INTEGER,
  quote TEXT NOT NULL
);
CREATE TABLE claims(
  id INTEGER PRIMARY KEY,
  text TEXT NOT NULL,
  status TEXT CHECK(status IN ('supported','unsupported','contradicted','insufficient')),
  evidence_ids TEXT NOT NULL   -- JSON array; enforced non-empty in code
);
CREATE TABLE contradictions(
  claim_a INTEGER, claim_b INTEGER, rationale TEXT
);
```

**Enforced in code:**
- normalized `quote` must appear in the extracted source text;
- every claim must reference ≥1 existing evidence ID;
- report renderer resolves `[[evidence_id]]`; unresolved → **build fails**.

**Test:** a 10-paper research task with two deliberately contradictory sources. The report must surface the contradiction, not smooth it over.
**Failure modes:** paywalled PDFs → record as `insufficient`, never infer contents; rate limits → exponential backoff + on-disk cache.
**Rollback:** research is read-only outside its corpus directory; delete the task's corpus + claims rows.

---

### Phase 4 — Persistent memory

```bash
# Filesystem memory is Git-versioned
git -C ~/lab/memory init
git -C ~/lab/memory add . && git -C ~/lab/memory commit -m "memory seed"
```

SQLite FTS5:

```sql
CREATE VIRTUAL TABLE memory_fts USING fts5(
  body, project, kind, content='', tokenize='porter unicode64'
);
```

**Add later, only against a measured recall gap:**

```bash
uv pip install sqlite-vec
# small embedding model, loaded on demand, NOT resident
```

Hybrid retrieval = BM25 + vector, merged with Reciprocal Rank Fusion.

**Test:** 50 held-back questions about past projects; measure recall@5. Add vectors only if FTS5 < your target.
**Failure modes:** memory poisoning → curator-only writes + provenance + Git review.
**Rollback:** `git revert` the memory commit; rebuild the FTS index from Markdown.

---

### Phase 5 — Multi-agent orchestration

- Add the 12 role YAMLs + charter synthesis.
- Add path-ownership locks and the blackboard tables.
- Add the I/O pool (4–8 workers) decoupled from the single LLM lease.
- **Now** add scoped shell behind the policy gate.
- Add Seatbelt profiles; test each toolchain inside them.
- Add Lima for untrusted repositories:

```bash
brew install lima
limactl start --name=untrusted --memory=6 --cpus=4
# workspace: read-only inputs + writable task dir; no LAN bridge
# inference reached via a forwarded loopback port, not the host network
```

**Test:** two concurrent tasks editing overlapping files → the ownership lock must reject the second write.
**Failure modes:** context duplication → project views, not full history; runaway children → hard `max_children`.
**Rollback:** disable the I/O pool; return to sequential execution. Architecture unchanged.

---

### Phase 6 — 24/7 operation

`/Library/LaunchDaemons/com.lab.supervisor.plist` (verify with `man 5 launchd.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.lab.supervisor</string>
  <key>UserName</key><string>aiworker</string>
  <key>ProgramArguments</key><array>
    <string>/Users/aiworker/lab/.venv/bin/python</string>
    <string>/Users/aiworker/lab/supervisor/supervisor.py</string>
  </array>
  <key>WorkingDirectory</key><string>/Users/aiworker/lab</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
  <key>ThrottleInterval</key><integer>10</integer>
  <key>ExitTimeOut</key><integer>30</integer>
  <key>StandardOutPath</key><string>/Users/aiworker/lab/logs/supervisor.out</string>
  <key>StandardErrorPath</key><string>/Users/aiworker/lab/logs/supervisor.err</string>
</dict></plist>
```

```bash
sudo cp com.lab.supervisor.plist /Library/LaunchDaemons/
sudo launchctl bootstrap system /Library/LaunchDaemons/com.lab.supervisor.plist
sudo pmset -a sleep 0 autopoweroff 0 autorestart 1
```

Add a **root** watchdog daemon and the **root** secrets broker as separate units.

**Test:** `sudo launchctl kill SIGKILL system/com.lab.supervisor` → verify it restarts, reclaims the lease, and resumes from checkpoint. Then reboot and verify the same.
**Failure modes:** FileVault cold boot → documented manual-unlock requirement; log growth → rotation; TCC prompts in a daemon → do **not** grant Full Disk Access, redesign the tool.
**Rollback:** `sudo launchctl bootout system/com.lab.supervisor`.

---

### Phase 7 — Remote access

1. Install Tailscale for macOS from the official installer; log in with your own tailnet.
2. Restrict the tailnet ACL to your devices.
3. Bind the control API to `127.0.0.1:8765`.
4. Enable **Tailscale Serve** for that local port (verify the current CLI syntax in your installed version).
5. Add approval binding + redacted alert filter.
6. SSH: key-only, password auth off, reachable only over Tailscale.

**Test:** from a phone on cellular, submit a task, approve a diff, hit `/kill`. Verify no listener is reachable from a non-tailnet network.
**Failure modes:** Tailscale daemon down → local operation continues; phone lost → revoke device in the admin console.
**Rollback:** disable Serve; the lab remains fully usable locally and over SSH.

---

### Phase 8 — Advanced optimization

Only after Weeks 1–4 of measured operation:

1. **MLX bake-off** — switch engines only if >1.5× prefill advantage *and* the tool-call gate still passes.
2. **Speculative decoding** — a ~0.5–1.5 B draft model is the *one* legitimate second resident model on 32 GB. Measure acceptance rate; disable if it does not win.
3. **Prefix caching tuning** — stable system + project prefix across tasks.
4. **Best-of-N selection** for hard, test-verifiable tasks.
5. **LoRA distillation** — collect successful tool-call traces; fine-tune a small specialist with MLX-LoRA; serve it for drafting/classification. Advanced, optional, not v1.
6. **Hybrid retrieval** if the recall gate demands it.

**Rollback:** every optimization is a config flag or an adapter choice. None is architectural.

---

# J. What NOT to install

| Technology | Why not here |
|---|---|
| **Docker Desktop / Kubernetes / k3s** | A always-on Linux VM carves RAM out of your 32 GB. Use Lima **on demand** for untrusted code only. |
| **vLLM / TensorRT-LLM / SGLang** | NVIDIA-oriented; no first-class Apple Silicon path in my reliable knowledge. Verify before assuming, but do not build your lab on an experimental Metal port. |
| **A second inference engine running concurrently** | Doubles memory, shares one bus. Strictly negative. |
| **Qdrant / Milvus / Weaviate / Chroma / Pinecone** | `sqlite-vec` + FTS5 is sufficient at personal scale. A vector server is an operator burden with no throughput benefit here. |
| **Neo4j / Memgraph** | SQLite relation tables until you have a genuine multi-hop query workload. |
| **Redis / RabbitMQ / NATS / Celery** | One inference consumer. SQLite leases give you durability, recovery, and queries with zero services. |
| **LangChain / CrewAI / AutoGen** | Abstraction over a small state machine; opaque context management and dependency churn. **LangGraph is the defensible exception** if you refuse to build the plane yourself. |
| **Letta / Mem0 / Zep-style auto-memory** | Unchecked fact writes destroy provenance. Curate memory explicitly. |
| **OpenHands / SWE-agent as the core** | Container-assumed / benchmark-oriented. Wrong shape for a cross-project 24/7 operator. |
| **MCP server fleet by default** | Tool-schema bloat degrades mid-size local models; each server is a process and a supply-chain surface. Ten typed native tools first. |
| **browser-use / LLM-per-click browser agents** | Orders of magnitude more LLM turns than deterministic Playwright actions. |
| **marker / MinerU / docling as default PDF stack** | PyTorch + multi-GB memory for gains you do not need on text papers. PyMuPDF first. |
| **70B+ dense models at aggressive quants** | "It fits" is not "it works." Q2 tool-call reliability plus swap = a slow, broken lab. |
| **LiteLLM / a proxy layer** | One local endpoint + optional cloud. A ~100-line in-process router is simpler. Revisit at >3 providers. |
| **Electron agent IDEs as the supervisor** | GUI dependency, memory tax, not headless. |
| **Accessibility / Screen Recording / Full Disk Access for the agent** | Unnecessary for the stated requirements and catastrophically broad. |
| **cron + shell scripts as the only orchestrator** | No leases, no budgets, no recovery, no approvals. |
| **A public dashboard / Funnel / port forwarding** | Tailscale Serve gives you the same UX with no inbound attack surface. |

---

# K. Future upgrade path

### Upgrade order matters

**1. Harness. 2. Bandwidth. 3. Capacity. 4. Dedicated accelerator.**

Most personal-lab throughput is lost to retries, verification gaps, and context bloat — not to raw token rate. Fix those before buying hardware.

| Target | What changes | What does not |
|---|---|---|
| **64 GB unified** | Context 24K → 64–128K; optionally a second *resident* model (e.g., a dense reasoner + a fast worker); 2 LLM workers **only if measured throughput improves** | Queue, policy, memory, adapter boundary, security model |
| **96–128 GB unified** | 70B-class dense Q4 or larger MoE; resident embedding + reranker; a small VM pool; 3–4 workers | Control plane unchanged |
| **Higher-bandwidth Silicon (Pro/Max/Ultra-class)** | Often the biggest real win: decode and prefill scale with bus bandwidth, not core count. A bigger model on a narrow bus can be slower than a smaller model on a wide one | Everything software-side |
| **Dedicated NVIDIA GPU server (24–48 GB VRAM)** | Move inference off the Mac; Mac becomes supervisor + tool host. GPU batch throughput per dollar usually beats Silicon for a lab that runs all night | Adapter contract stays OpenAI-compatible; add auth + LAN/Tailscale transport |
| **Second Mac / cluster** | **Not recommended.** Coordination and context-splitting overhead exceeds the benefit for a single-user lab | — |

### At each step

- Re-run the **same fixed task suite** — never upgrade on a leaderboard.
- Keep the previous model + engine pin rollback-ready.
- Raise context only after measuring long-context reliability on *your* tasks.
- Add concurrency only after measuring that it improves **useful completed tasks/hour**, not token/s.

---

## What would change my answer (falsification gates)

| If this is true… | Then change… |
|---|---|
| A 2026 open-weight ~20B model beats the chosen workhorse by >20% on your agentic task suite | **Weights only.** Architecture unchanged. |
| MLX shows >1.5× prefill on your 24K prompt **and** passes the tool-call gate | **Engine only.** |
| Codex CLI's local-provider tool-call failures exceed 5% | **Executor adapter → native loop.** |
| The 30B-A3B budget causes swap at peak on your M6 | **Downsize/requantize before any other optimization.** |
| A mature low-RAM macOS-native container runtime exists in 2026 | **Replace UID+Seatbelt as the primary boundary.** |
| FTS5 recall@5 exceeds your target on the held-back memory suite | **Never add vectors.** |
| Two LLM workers measurably increase completed tasks/hour | **Allow a second slot.** (My prior: they will not.) |

---

## Sources

**All URLs below are known primary locations from my training. None were fetched or verified in this session. Each is a Phase 0 verification target, not a claim about its current contents.**

### Inference engines and model formats — primary
1. https://github.com/ggml-org/llama.cpp — engine, Metal support, release history.
2. https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md — server flags, slots, context, cache reuse.
3. https://github.com/ggml-org/llama.cpp/blob/master/gguf.md — quantization format and metadata.
4. https://github.com/ml-explore/mlx — Apple Silicon array framework.
5. https://github.com/ml-explore/mlx-lm — MLX inference, serving, LoRA.
6. https://huggingface.co/docs/hub/en/gguf — GGUF ecosystem.

### Models — primary
7. https://github.com/QwenLM/Qwen3 — architecture, context, licensing.
8. https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct — candidate workhorse card.
9. https://huggingface.co/Qwen/Qwen3-30B-A3B — MoE shape / active-parameter reference.
10. https://huggingface.co/Qwen/Qwen3-32B — dense comparison point.

### Executors and orchestration — primary
11. https://github.com/openai/codex — CLI, provider configuration, sandbox behavior.
12. https://github.com/block/goose — general-purpose open agent harness.
13. https://github.com/Aider-AI/aider — git-native edit loop, repo map.
14. https://github.com/All-Hands-AI/OpenHands — platform/runtime design.
15. https://github.com/SWE-agent/SWE-agent — action-interface design.
16. https://github.com/langchain-ai/langgraph — durable checkpointing alternative.
17. https://modelcontextprotocol.io/ — protocol spec; evaluate tool-schema cost.

### Memory and retrieval — primary
18. https://www.sqlite.org/fts5.html — FTS5 / BM25.
19. https://www.sqlite.org/wal.html — WAL semantics and durability.
20. https://www.sqlite.org/backup.html — safe online backup (`VACUUM INTO` / backup API).
21. https://github.com/asg017/sqlite-vec — in-process vector extension.

### Research tooling — primary
22. https://docs.openalex.org/ — scholarly metadata + citation graph API.
23. https://info.arxiv.org/help/ — arXiv API and usage policy.
24. https://www.crossref.org/documentation/retrieval/rest-api/ — DOI/metadata retrieval.
25. https://www.semanticscholar.org/product/api — citation context / graph API.
26. https://github.com/pymupdf/PyMuPDF — PDF text + span extraction.
27. https://github.com/adbar/trafilatura — HTML content extraction.
28. https://playwright.dev/python/docs/intro — browser automation.
29. https://github.com/SearXNG/SearXNG — self-hosted metasearch.

### macOS operation, sandboxing, remote — primary
30. https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html — launchd job design.
31. https://developer.apple.com/documentation/virtualization — Apple Virtualization.framework.
32. https://developer.apple.com/documentation/metal — Metal compute.
33. https://github.com/lima-vm/lima — on-demand Linux VMs on macOS.
34. https://tailscale.com/kb/ — Serve, ACLs, identity-aware access.

### Live data endpoints for Phase 0 — primary
35. `https://api.github.com/repos/{owner}/{repo}/releases/latest` — current version + publish date.
36. `https://huggingface.co/api/models/{repo}` — current model metadata + last modified.

**Secondary sources: none cited.** I did not retrieve any independent 2026 benchmark, community discussion, or technical article, and I will not imply otherwise. All performance figures in this document are either explicit arithmetic from architecture parameters or clearly labeled design budgets and planning assumptions.

---

### Bottom line

Build **a durable SQLite control plane with a policy gate**, run **one resident ~30B-active-3B MoE at 4-bit through llama.cpp on Metal**, rent the coding executor through a **swap-safe adapter**, and implement research as a **claim→evidence→verification pipeline where the model cannot write a citation**. Isolate the executor by **UID, worktree, path ownership, and credential absence** — not by prompt instructions. Reach it only through **Tailscale**, with **hash-bound, single-use approvals**.

That design gives you 100+ logical agents, genuine overnight autonomy, and full offline operation on 32 GB. It does not give you 100 simultaneous LLMs — and on this hardware, wanting them would be the mistake.

**Run Phase 0 before installing anything else.** The missing 2026 evidence is the only part of this specification I could not obtain, and it is obtainable on your machine in twenty minutes.

## Reasoning trace (not shown to raters)

Thinking and Search


Assessing the response strategy regarding temporal and capability constraints.
I recognize the need to clarify my knowledge cutoff while adhering to the provided system date.
I intend to maintain honesty about the absence of real-time browsing tools in this environment.
The goal is to formulate a direct and transparent answer without revealing internal instructions or parameters.

Acknowledge current operational parameters and constraints
I am identifying my identity as Qwen3.8 while recognizing the absence of external browsing capabilities due to the lack of available tools. I acknowledge that my knowledge is static and cannot verify real-time data beyond my training cutoff, necessitating a reliance on established principles rather than live research. Consequently, I will approach the inquiry by formulating an evidence-based design specification that includes clear verification steps instead of claiming up-to-the-minute factual accuracy. This ensures the response remains grounded in verifiable logic while transparently addressing the limitations of my current environment.

Maintain strict adherence to knowledge cutoff boundaries by explicitly disclaiming real-time browsing capabilities.
I will clearly state that I cannot verify current versions or perform live searches, ensuring no fabricated citations or post-cutoff facts are presented.
All referenced materials will be marked as derived from prior knowledge and unverified as of the current date to prevent misleading assertions.
This approach ensures a decisive yet calibrated response that respects factual limitations while avoiding any exposure of internal instructions or technical parameters.

Assessing knowledge boundaries and hardware constraints
I recognize that my training cutoff is not explicitly defined in this session, so I will frame my factual recall as extending roughly to mid-2025 while acknowledging the uncertainty regarding 2026 developments. I am carefully avoiding overclaims about specific future hardware specifications, such as the M6 Mac mini's memory bandwidth or feature sets, which remain unverified. Instead, I intend to design my response around invariant principles that hold true regardless of specific hardware uncertainties. This approach ensures accuracy by focusing on established architectural concepts rather than speculative details.

Refining the architectural strategy for resource-constrained environments
I prioritize delivering high-value, concrete technical specifications while strictly adhering to memory limitations. I recognize that concurrent processing is inefficient under these constraints and instead focus on optimizing a minimal worker pool with durable state management. My goal is to provide a robust, first-principles-based design that maximizes utility without exceeding system boundaries. This approach ensures the solution remains practical, secure, and verifiable within the specified hardware parameters.

Evaluate optimal model selection for resource-constrained environments
I am analyzing the trade-offs between rule-based classification and lightweight models to minimize infrastructure complexity. I compare specific large language models based on their memory footprint, context window, and agentic capabilities on limited hardware. My goal is to identify a single efficient model that balances performance with the constraints of available system resources. This assessment ensures the solution remains practical while maintaining high utility for coding tasks.

Synthesizing hardware constraints and model capabilities to identify optimal local inference solutions.
I evaluate the trade-offs between sparse mixture-of-experts architectures and unified memory systems, prioritizing efficient bandwidth usage while ensuring all parameters fit within available RAM. I filter out models that exceed capacity limits or lack sufficient quantization support, focusing on those with proven performance in agentic tasks and tool use. Finally, I cross-reference release dates and technical specifications to recommend models that balance reasoning depth with practical deployment feasibility on consumer-grade silicon.

I am evaluating recent large language models to identify the most suitable option for my specific hardware constraints.
I consider several high-performance candidates, weighing their memory requirements against their reasoning and tool-use capabilities.
To ensure reliability, I prioritize a structured selection process over claiming an unverified state-of-the-art status.
My approach involves defining a shortlist of proven architectures and establishing clear criteria for final validation on this device.

Evaluating optimal model configurations for constrained memory environments
I am analyzing hardware limitations to determine the most efficient large language model architecture, weighing dense versus mixture-of-experts designs. My focus is on balancing parameter precision and context window size against available system resources to ensure stable operation. I am carefully calculating memory overheads to identify a configuration that maximizes performance without exceeding physical capacity constraints.

Evaluating optimal model configuration for constrained memory environments
I am analyzing the trade-offs between computational resources and inference capabilities to determine the most efficient architecture. I compare a smaller dense model with ample headroom against a larger mixture-of-experts variant that offers superior quality but demands stricter resource management. My assessment focuses on balancing agentic reliability and context length against the available memory after accounting for system overheads. Ultimately, I aim to identify a solution that maximizes performance without compromising stability or requiring excessive hardware constraints.

Analyze the performance trade-offs between sparse and dense architectures under memory bandwidth constraints.
Compare theoretical throughput rates by evaluating active parameter counts against hardware transfer capabilities.
Highlight the efficiency advantages of selective weight loading for specific computational workloads.
Conclude that reduced data movement significantly enhances inference speed while maintaining output quality.

Formulate a rigorous architectural argument for performance gains by quantifying memory efficiency.
Derive the KV cache footprint for specific model configurations using explicit arithmetic and known hyperparameters.
Compare the total memory requirements of competing models to highlight superior resource utilization.
Structure the presentation as a defensible measurement procedure with clearly defined variables.

Identify the optimal large language model configuration for agentic coding tasks within strict memory constraints.
I evaluate various quantization levels and architectural designs to balance model capacity with available system resources, ensuring stable operation without excessive swapping.
After analyzing parameter sizes and overheads, I determine that a specific mixture-of-experts variant offers the best trade-off between performance and efficiency for complex coding workflows.
This selection aligns with verified benchmarks for software engineering tasks while maintaining a manageable context window to preserve system responsiveness.

Evaluating local inference architectures and deployment strategies.
I am weighing the trade-offs between self-hosted solutions and optional cloud escalation to balance privacy with planning capabilities.
My focus is on ensuring that stronger models are used selectively for high-level reasoning while maintaining a robust local foundation for execution.
I aim to prioritize verification mechanisms over raw model size to ensure reliability in complex, long-horizon tasks.

Synthesizing a comparative analysis of local inference frameworks.
I evaluate each option by weighing architectural efficiency, structured output capabilities, and ecosystem maturity against specific use cases.
I prioritize solutions that offer robust constraint handling and stability for complex tasks while acknowledging the performance benefits of native hardware optimization.
Finally, I assess convenience-focused tools to determine their suitability for lightweight or casual deployment scenarios.

I am evaluating the most suitable inference engine for a persistent, headless agent deployment on Apple Silicon.
I systematically filter out options that are either closed-source, lack native hardware acceleration, or are designed for different architectures.
I prioritize solutions that offer robust structured output handling and reliable streaming capabilities to ensure agentic stability.
My current strategy involves conducting a comparative benchmark between the top contenders to make a final decision based on performance and reliability metrics.

Refine the inference strategy by prioritizing structural reliability over raw prefill speed.
I initially considered switching to MLX due to its superior prefill performance on Apple Silicon for long-context scenarios.
However, I concluded that agentic workflows demand robust tool-call parsing and structured decoding, which are more mature in the primary option.
Therefore, I settled on a solution that balances memory efficiency with the stability required for complex multi-turn interactions.

Evaluating inference frameworks to balance performance with operational simplicity.
I am comparing established tools against emerging alternatives to identify the most robust solution for my specific hardware constraints.
The analysis weighs the trade-offs between single-engine stability and multi-engine flexibility while prioritizing ease of maintenance.
This process aims to establish a clear, defensible decision matrix based on empirical benchmarks and practical deployment needs.

Analyze and compare coding assistant capabilities
I am evaluating open-source alternatives that support local model deployment through custom endpoints or specific flags. I weigh the trade-offs between proprietary services requiring external APIs and fully self-hosted options with varying degrees of sandboxing and orchestration maturity. My goal is to identify tools that balance privacy, autonomy, and ease of configuration for private development workflows.

Evaluating autonomous coding agents for suitability as a backend tool rather than a supervisory layer.
I assess various platforms by weighing their architectural strengths against specific hardware constraints and operational requirements.
While some solutions offer comprehensive sandboxing, they may introduce performance overhead on limited memory systems.
Conversely, lightweight alternatives provide efficient local execution with native protocol support, making them more practical for headless integration.

Assessing the viability of existing personal assistant gateways against specific architectural requirements.
Recognizing that relying on unverified or potentially fabricated product names compromises the integrity of the response.
Determining that constructing a custom supervisor layer over proven primitives offers a more robust and defensible solution than adopting monolithic platforms.
Concluding that this approach better addresses the need for dynamic roles, persistent queuing, and security boundaries inherent in the user's complex scenario.

Analyzing architectural constraints for resource-constrained orchestration
I am evaluating a hybrid system design that separates lightweight execution workers from a custom, durable control plane to maximize efficiency on limited hardware. I am assessing the trade-offs between local macOS sandboxing and virtualized environments, specifically noting the memory overhead and hardware access limitations inherent in containerized solutions. My focus is on structuring a solution that leverages native capabilities while maintaining strict security boundaries and state management without relying on external infrastructure.

Evaluating secure execution environments for host inference
I weigh the trade-offs between lightweight macOS-native sandboxing and heavier virtual machine solutions to balance performance with security. I consider combining native isolation techniques with dedicated user accounts while reserving Linux virtualization specifically for untrusted tasks. I plan to verify recent platform updates and prioritize mature, open-source options over convenient but resource-intensive commercial tools. My goal is to identify a configuration that maximizes operational autonomy without compromising system integrity.

Establishing a secure, isolated execution environment for autonomous tasks
I am designing a sandboxed architecture where the agent operates under a dedicated system account with strictly limited file system and network permissions.
Sensitive credentials are managed exclusively by a privileged supervisor process, ensuring they never reside within the agent's accessible memory or workspace.
All external communications and data access are mediated through a centralized approval gate that enforces strict policy compliance before any action is executed.

Formulate a secure and resilient autonomous operation framework for macOS
I am designing a robust access control mechanism that leverages policy-based filtering to restrict high-risk actions, requiring explicit human verification via phone for critical operations. I am architecting a reliable emergency shutdown protocol that combines system-level process termination with user-accessible shortcuts to ensure immediate containment of any malfunction. I am configuring the background service using native macOS daemon management tools to guarantee persistent execution as a dedicated user while optimizing process attributes for low-latency responsiveness. I am implementing sleep prevention strategies tailored for headless hardware to maintain continuous availability without relying on display-specific power settings.

Analyze system configuration and security constraints for 24/7 availability.
Evaluate power management settings to prevent unintended reboots while ensuring resilience against power failures.
Assess the impact of full-disk encryption on post-crash accessibility and identify potential operational blockers.
Recommend maintaining high-security standards while acknowledging necessary manual intervention steps after critical events.

Refine the technical recommendation by balancing security with operational continuity.
I evaluate macOS specific mechanisms to identify residual risks and prioritize robust security measures over convenience.
To ensure reliable access while maintaining isolation, I propose configuring a dedicated user session with minimal privileges rather than exposing personal credentials.
This approach allows for automated background operations without compromising the integrity of the primary account or requiring insecure workarounds.

Resolve the conflict between disk encryption and automatic login by prioritizing security through a daemon-based architecture.
I recognize that enabling full-disk encryption inherently prevents unattended user authentication, creating a fundamental operational constraint.
To maintain data protection while allowing background execution, I propose running the agent as a system-level service rather than a logged-in user.
This approach isolates sensitive credentials from the untrusted model-driven code using root-managed secrets, effectively mitigating local compromise risks without sacrificing encryption integrity.

Refining the architectural strategy for secure credential management and network connectivity.
I am evaluating a phased approach that initially restricts the agent to local operations while deferring complex privilege separation mechanisms to later stages. This ensures a simpler starting point before implementing a dedicated broker to handle sensitive data securely. I am also comparing various private networking solutions to establish safe remote access without exposing public ports.

Synthesizing a secure remote access and notification architecture
I evaluate network tunneling options balancing convenience against strict self-hosting requirements, ultimately favoring a managed solution with robust identity features. I analyze various notification channels weighing the trade-offs between ease of use and data privacy, noting that public services may expose sensitive metadata. I consider implementing a private dashboard accessible through the secure tunnel as the primary interface to minimize reliance on external push infrastructure. This approach prioritizes user control and security while maintaining accessibility for terminal management and status monitoring.

Evaluating notification and search infrastructure options
I am assessing secure alerting mechanisms that prioritize privacy by limiting data exposure to essential metadata. I am comparing local and external research tools to identify the most efficient and cost-effective solutions for information retrieval. I am weighing the trade-offs between self-hosted private services and specialized APIs to ensure reliable access without compromising user data. My goal is to recommend a balanced architecture that maximizes utility while maintaining strict security standards.

Establishing a robust and efficient evidence extraction pipeline
I prioritize lightweight, high-performance tools for text and layout analysis while reserving specialized solutions for complex structural requirements. To ensure rigorous verification, I construct a structured claim-evidence graph within a database rather than relying on unstructured summaries. This approach mandates that every assertion is linked to specific source details, verbatim quotes, and verification status. Such a design prevents the generation of unsupported citations and maintains strict traceability throughout the reasoning process.

Establishing a rigorous verification framework to ensure factual accuracy
I prioritize retrieving information before generating any content, ensuring that every claim is anchored to specific, verifiable evidence. I extract precise quotes from these sources and subject them to a dual-verification process where independent checks determine if the evidence supports or contradicts the assertions. To further mitigate errors, I actively seek out disconfirming data and strictly adhere to a hierarchy of source credibility, favoring primary academic works over less reliable media. This approach guarantees that all citations are grounded in stored, authentic references rather than potentially hallucinated text.

Establish a secure and efficient data ingestion pipeline
I prioritize lightweight, open-source text extraction tools to ensure speed and privacy while avoiding resource-heavy or external dependencies.
To mitigate security risks, I isolate the browsing environment by restricting network access and disabling sensitive features like password management.
For memory management, I implement a tiered approach starting with version-controlled markdown files for transparency and evolving into a local SQLite database for structured storage.
Finally, I integrate hybrid retrieval methods combining keyword search with local embeddings to enhance information recall without relying on external services.

I am designing a lightweight, self-contained memory architecture that prioritizes efficiency and security.
I plan to utilize in-process vector search and structured relational tables to eliminate the overhead of external database servers.
My approach distinguishes between raw event logs and verified semantic knowledge, ensuring that unverified information never contaminates the core memory.
I will manage context by retrieving only relevant summaries and structural maps rather than loading entire repositories, maintaining a focused and deterministic workflow.

Maintain strict separation between agent definitions and execution resources to ensure system stability
I distinguish between logical roles and physical inference slots, reserving limited computational capacity for the primary model while offloading I/O tasks to a separate pool. This approach prevents memory contention and swap-induced performance degradation by ensuring only one large model runs concurrently. By leveraging parallelism for non-LLM operations, I maximize throughput without overburdening the hardware. This strategy preserves resource integrity while supporting a high volume of concurrent logical agents.

Structuring the response architecture
I prioritize a staged pipeline to maximize throughput by overlapping computational and input-output phases while limiting resource contention. I adopt a hub-and-spoke coordination model with a central verification layer to prevent context redundancy and conflicting edits inherent in decentralized approaches. To ensure safety and precision, I dynamically generate constrained agent roles with strict permission boundaries and clear termination criteria. This design ensures efficient execution while maintaining rigorous control over tool access and operational scope.

Evaluating autonomous coding tools for local deployment
I am assessing safety mechanisms like token limits and error detection to ensure system stability during execution. I recognize that isolated workspaces primarily benefit sequential task management rather than increasing parallel processing speed on a single model. My focus is now on selecting a tool that supports custom inference providers while maintaining strict sandboxing and approval workflows. This approach ensures secure, headless operation with robust version control integration.

Synthesizing a strategic recommendation for local AI coding infrastructure
I evaluate the technical viability of various autonomous agents to identify the most robust solution for private, offline development workflows.
I prioritize open-source tools that natively support model-agnostic execution and non-interactive automation while ensuring compatibility with local inference engines.
I explicitly exclude proprietary cloud-based alternatives due to their inherent limitations regarding data sovereignty and architectural rigidity in local environments.
The final guidance emphasizes establishing a secure, self-hosted pipeline that balances advanced reasoning capabilities with strict privacy and operational control.

I am synthesizing a strategic plan for an autonomous coding architecture.
I evaluate various existing frameworks to determine their suitability for resource-constrained environments, ultimately dismissing those that are too heavy or benchmark-focused.
I propose constructing a custom control layer that leverages a specialized command-line interface as the primary execution engine while retaining a lightweight native loop as a robust fallback mechanism.
This approach prioritizes precise controllability and reliability over reliance on brittle third-party tools.

I am evaluating architectural strategies to balance reliability with local model compatibility for a continuous operation system.
I prioritize mature frameworks over custom loops to mitigate complexity, while establishing a benchmarking phase to objectively select the optimal toolset based on performance metrics.
I maintain a cautious stance regarding specific third-party tools due to potential version uncertainties, ensuring a robust fallback mechanism is integrated into the design.
The goal is to present a decisive yet flexible solution that guarantees operational continuity regardless of external tool availability.

Evaluate architectural resilience and tool integration strategies
I prioritize design stability by emphasizing the robustness of the control plane against component swaps through a standardized interface. I advise against adopting complex external protocols or databases initially to prevent performance degradation and security risks for smaller models. Instead, I recommend implementing a concise set of native tools directly within the supervisor process to ensure reliability and ease of maintenance. This approach avoids unnecessary complexity while maintaining the flexibility to add advanced integrations only when strictly necessary.

Refining the architectural hierarchy to prioritize the queue as the central spine
I am re-evaluating the system design to elevate the task queue from a peripheral component to the core structural element.
Simultaneously, I am treating policy enforcement as a pervasive control mechanism rather than a distinct sequential layer.
This adjustment aims to create a more cohesive and resilient architecture that better supports dynamic orchestration.

I am analyzing the architectural blueprint of an autonomous agent system.
This design outlines a hierarchical structure starting with secure interfaces and transitioning into a robust supervision layer that manages scheduling, task queuing, and policy enforcement.
The core orchestration mechanism dynamically synthesizes roles and maintains shared state to decompose complex objectives into manageable tasks for specialized workers.
Finally, the system employs intelligent routing to direct these tasks through various operational slots, ensuring efficient execution and verification within a controlled environment.

I am architecting a deterministic inference pipeline with strict resource allocation and security constraints.
I prioritize rule-based routing over probabilistic classification to minimize latency and computational overhead.
I design a layered memory system that distinguishes between persistent storage and dynamic indexing mechanisms.
I define precise hardware budgets to ensure stable operation within the limits of unified memory architecture.

Optimizing system memory allocation to ensure stable operation within hardware constraints
I recalculated the total resource requirements and identified an excess that necessitates trimming specific components. By adjusting model precision, reducing context window size, and minimizing overhead for auxiliary processes, I derived a more efficient configuration. This revised plan lowers the inference footprint and OS reserves while maintaining sufficient headroom for cache and unexpected spikes. The final estimate ensures the system remains well within the available memory limits without compromising core functionality.

Refine the memory allocation strategy by distinguishing between distinct usage profiles rather than relying on concurrent model loading.
I propose a coding profile optimized for inference and a research profile that accommodates browser overhead while disabling toolchains.
This approach allows the system to dynamically switch contexts by managing workload limits, ensuring efficient resource utilization within the fixed memory budget.
Finally, I determine the default configuration based on the optimal balance between model quality and bandwidth efficiency, offering a fallback option if the primary setup proves too demanding.

Evaluating model selection and memory constraints for optimal deployment.
I assess the trade-offs between dense and mixture-of-experts architectures, noting that smaller context windows significantly reduce key-value cache overhead. I calculate the precise memory footprint of the candidate models, identifying that standard quantization may exceed available resources while specialized formats offer a viable path. To ensure stability, I propose a tiered strategy that prioritizes reducing context length before applying more aggressive quantization techniques.

Analyze resource constraints and optimize inference efficiency.
I prioritize reducing parallel processing slots and downscaling the model to ensure stable performance on macOS hardware. I strictly advise against partial CPU offloading as it severely degrades throughput, emphasizing full GPU acceleration instead. To prevent latency spikes caused by memory swapping, I propose implementing strict admission controls based on real-time memory usage metrics. Finally, I outline a storage management strategy to accommodate the system and applications within limited internal capacity.

Formulate storage architecture strategy
I evaluate the distinct requirements for data access frequency and reliability to determine optimal placement within my system. I distinguish between active resources needing low-latency internal access and archival materials suitable for external cold storage. I prioritize system stability by ensuring critical operational data remains on high-performance drives while mitigating risks associated with external device connectivity. I establish clear boundaries for backup and recovery protocols to maintain integrity without compromising inference performance.

I am formulating a robust strategy for local AI deployment and data preservation.
I emphasize the necessity of strict storage management to handle model archives efficiently while ensuring system stability through proactive health checks.
I outline a comprehensive backup protocol that prioritizes data integrity by employing specialized database checkpointing rather than raw file copying.
Finally, I delineate a cost-effective architecture leveraging free open-source tools for core operations, reserving paid services only for specific escalation needs.

Maintaining a secure and autonomous operational framework
I prioritize local execution for routine tasks to ensure privacy and efficiency while reserving cloud resources only for complex, high-stakes scenarios. My design strictly avoids mandatory external dependencies by enabling full functionality without API keys through integrated research and memory systems. I operate with precise boundaries, autonomously managing files, version control, and project-specific validations within a defined workspace. This approach guarantees that all actions remain transparent, safe, and aligned with the core requirements of independence and security.

Maintaining operational boundaries while executing tasks
I initiate subtasks within established limits and generate necessary documentation to support the workflow. I defer actions requiring pre-authorization or human oversight, ensuring that sensitive operations involving system changes, remote updates, or security configurations remain under strict control. By adhering to these constraints, I prioritize safety and compliance in all autonomous activities. This approach guarantees that high-risk procedures are only executed with explicit permission or authorization.

Maintaining strict operational boundaries within a secure execution environment
I operate under a rigorous policy framework enforced by my supervisor to ensure system integrity and data safety. My capabilities are restricted to specific, pre-approved functions that facilitate task completion without exposing sensitive infrastructure or credentials. I strictly adhere to these constraints, recognizing that trust must be established through architectural safeguards rather than mere instructions. This approach guarantees that all actions remain transparent, auditable, and aligned with the highest standards of security and compliance.

Establishing a secure execution environment with rigorous access controls and tamper-evident logging
I am implementing robust input validation and path normalization to prevent traversal attacks while isolating the worker process under a distinct identity to restrict data access. I am designing an immutable audit trail using cryptographic hashing to ensure integrity and enable tamper detection across all operations. Additionally, I am defining a definitive emergency termination protocol that allows for immediate process cessation and task suspension through controlled system signals.

Designing a resilient autonomous agent architecture with robust fault tolerance mechanisms
I implement an out-of-band kill switch using file-based flags and system-level daemons to ensure immediate termination even if the primary supervisor fails.
The system operates continuously with automated restart policies and lease-based heartbeat monitoring to maintain state consistency and resume interrupted tasks seamlessly.
I enforce strict idempotency for all operations and integrate hardware-level revocation options to provide comprehensive control and safety guarantees.

Maintaining system stability and operational continuity
I ensure resilience by verifying the actual state during recovery rather than blindly replaying actions, while preserving a lightweight checkpoint of progress to facilitate efficient resumption. I actively monitor system health through independent watchdogs and keep the model ready for immediate response. To optimize resource usage and safety, I defer approval-gated tasks to daytime hours, focusing on unattended operations overnight. This strategy prevents idle waiting and ensures that critical decisions are made with appropriate oversight.

Formulating a secure and efficient remote access strategy for the Mac mini.
I am defining power management protocols to ensure stable operation during outages while maintaining low energy consumption.
I am designing an identity-aware network architecture that leverages private tunneling to expose services securely without exposing public ports.
I am establishing strict authentication mechanisms, including cryptographic verification and multi-factor approvals, to prevent replay attacks and unauthorized access.

Formulating a precise implementation strategy with executable verification steps.
Validating the availability of specific system tools and dependencies via package managers.
Resolving version constraints to ensure compatibility while acknowledging future uncertainty.
Structuring the response to provide actionable commands without exposing internal reasoning details.

Evaluating the optimal installation method for Tailscale on a headless macOS system.
I am weighing the trade-offs between the official graphical installer and the command-line interface to ensure robust operation without a display.
My reasoning focuses on verifying that the chosen approach supports background services and remote management effectively.
I aim to recommend a solution that balances ease of setup with reliable daemon functionality for an unattended environment.

Refining technical recommendations by prioritizing official installation methods and verified package dependencies.
I am discarding uncertain package manager commands to ensure accuracy and avoid potential configuration errors.
I am evaluating lightweight alternatives for search functionality to maintain system efficiency without relying on complex infrastructure.
My goal is to provide a robust, streamlined solution that avoids unnecessary complexity or deprecated tools.

Evaluating architectural strategies for research data acquisition and system configuration
I prioritize specialized academic APIs over fragile web scraping to ensure a robust and lightweight foundation for literature review. I plan to supplement this with on-demand general search capabilities only when necessary, maintaining a clean separation of concerns. Concurrently, I am managing version control workflows and system-level configurations to support the agent's operational environment. This approach balances technical precision with resource efficiency while adhering to security and structural constraints.

Evaluating methods to provision a dedicated service account.
I analyze the feasibility of built-in user creation commands and their associated flags.
I consider alternative approaches involving hidden accounts or secure credential management.
I conclude by selecting the most appropriate strategy for establishing a standard user identity.

Establishing a dedicated service account with strict isolation protocols
I generate a cryptographically secure password and configure the user environment to exclude administrative privileges and personal data access. I recognize that default group permissions may inadvertently allow traversal of private directories, prompting an adjustment to enforce stricter file system restrictions. To mitigate risks associated with system privacy frameworks, I explicitly withhold specific user consent permissions for sensitive areas such as documents and screen recording. This approach ensures that automated tasks operate within a minimal permission set while preserving the integrity of personal information.

Analyze the security implications of system-level permissions and sandboxing mechanisms for background processes.
Evaluate how attribute-based access controls interact with daemon execution contexts to ensure least-privilege principles are maintained.
Compare restrictive versus permissive isolation profiles to determine the optimal configuration for protecting sensitive user data and system integrity.
Formulate a recommendation that separates elevated privilege tasks from standard user operations to minimize potential attack surfaces.

Refining the security architecture strategy for untrusted execution environments
I recognize that relying solely on sandbox profiles is insufficient due to their complexity and limitations, so I prioritize a layered defense model centered on identity, filesystem permissions, and credential isolation.
I evaluate the trade-offs between lightweight process confinement and robust virtualization, concluding that dedicated VMs offer superior isolation despite higher resource costs.
To ensure honesty and correctness, I frame technical recommendations as hardening measures rather than absolute boundaries, emphasizing rigorous testing and minimal exposure surfaces.
My goal is to provide a balanced, pragmatic solution that acknowledges the inherent risks while offering clear guidance on secure toolchain deployment.

Refine the technical strategy by explicitly defining exclusions to prevent resource waste and architectural bloat.
I will identify specific heavy infrastructure and complex frameworks that are unnecessary for personal-scale operations.
This approach prioritizes lightweight, integrated solutions over distributed systems and opaque abstractions.
The goal is to maintain a lean, efficient environment suitable for untrusted or experimental contexts.

Evaluate agent architecture against efficiency and privacy constraints
I prioritize headless, resource-light solutions over GUI-dependent or cloud-hosted platforms to ensure offline capability and reduced overhead. I caution against complex memory layers and large models that offer diminishing returns due to provenance loss and computational waste. I advocate for deterministic tools and simple scripting over heavy browser automation to maintain cost-effectiveness and reliability. Finally, I recommend restricting system-level permissions and using targeted scripts only when specific interface interactions are absolutely necessary.

Assessing system architecture and safety boundaries for agent deployment
I am evaluating the trade-offs between granting broad graphical interface permissions and maintaining strict isolation to prevent security risks. I recognize that while enhanced capabilities are possible with increased memory or dedicated hardware, introducing complex GUI controls in early stages poses significant stability and privacy challenges. Therefore, I prioritize a minimalist approach by excluding visual automation features initially to ensure a secure and stable foundation. Future scalability plans involve leveraging additional resources for specialized models only when they demonstrate clear operational value.

Formulate a comprehensive hardware and software strategy for local large language model deployment.
Evaluate the cost-effectiveness of Apple Silicon based on memory bandwidth constraints while dismissing distributed clusters for personal use cases.
Prioritize system upgrades by focusing on bandwidth enhancements and optimizing inference pipelines before acquiring new server infrastructure.
Curate a list of verifiable primary sources to ensure factual accuracy and prevent the fabrication of technical specifications or benchmarks.

Identifying relevant technical repositories and documentation for implementation reference
I am gathering information on core inference engines and server tools to understand the underlying infrastructure. I am also reviewing advanced AI agents and coding assistants to explore their architectures and capabilities. Additionally, I am consulting academic and data retrieval APIs to ensure comprehensive resource integration. Finally, I am examining document processing libraries to support efficient content parsing and analysis.

Verifying the authenticity and accessibility of referenced documentation sources.
I am cross-rechecking specific URLs to ensure they are valid and safe for citation.
I am evaluating whether certain optional tools are necessary for the proposed solution.
I am finalizing the list of reliable resources while discarding uncertain or redundant links.

I am refining my response strategy to ensure absolute transparency regarding evidence limitations.
I will explicitly state that no live benchmark data exists and classify all performance claims as theoretical or labeled priors.
I will structure the answer with clear status indicators for sources while avoiding any unverified assumptions about specific hardware models.
This approach guarantees rigor by prioritizing honest disclosure over speculative assertions.

Evaluating architectural alternatives to optimize the system design.
I weigh the trade-offs between building a custom interface versus leveraging existing gateways while maintaining control over the core logic.
I determine that a polling mechanism with file-based state management offers superior simplicity and native crash-safety compared to event-driven models or complex databases.
This approach ensures robust task orchestration without unnecessary complexity, aligning with the constraints of the current environment.

Refining architectural and algorithmic strategies for intelligent systems
I prioritize a distributed storage model where a lightweight relational database manages control logic while the file system retains worker artifacts, ensuring neither acts as a full mirror of the other. I consider leveraging versioned text for semantic memory alongside traditional databases to handle episodic data, while maintaining local processing capabilities with optional cloud assistance for complex planning. For resource-constrained environments, I advocate for speculative multi-candidate generation on verifiable tasks rather than redundant single-trajectory retries, optimizing for efficiency through deterministic selection. Finally, I distinguish between self-consistency voting and rigorous evidence checking, rejecting the former as a reliable truth mechanism in favor of substantive verification.

Synthesizing advanced inference optimizations
I evaluate strategies to enhance efficiency by distilling specialist models from broader traces and leveraging prompt caching mechanisms. I consider the practical implementation of these techniques, such as maintaining resident model servers to minimize prefill costs and ensuring stable system prefixes for seamless reuse. I also weigh the trade-offs between training overhead and operational speed, noting that certain optimizations are better suited for later development phases rather than initial releases. Ultimately, I aim to balance cutting-edge performance gains with the stability required for a robust first version.

Refining the response to address the specific constraints of single-slot hardware limitations.
I evaluate speculative decoding as a viable optimization strategy for increasing throughput on limited memory.
I clarify that model selection in this context relies on configuration and prompts rather than weight switching.
The final output will provide concrete, non-generic advice tailored to the user's hardware constraints.

Formulate a deterministic routing architecture prioritizing a single primary model with conditional specialist invocation.
I evaluate the latency costs of context switching to establish a threshold where swapping models yields tangible performance gains.
I refine the agent design by distinguishing between reusable role templates and specific task instances to optimize scalability.
This approach ensures efficient resource allocation while maintaining high throughput for routine operations.

Orchestrating a structured collaborative workflow to address the user's request
I dynamically assign specialized roles with clear objectives and constraints to ensure focused execution.
To maintain stability, I manage concurrent tasks while enforcing strict file ownership to prevent conflicts.
Finally, I employ independent verification mechanisms to validate outputs before archiving the results.

Assessing operational constraints and architectural priorities for autonomous coding agents.
I emphasize the necessity of deterministic verification gates to ensure reliability before engaging higher-level reasoning models.
I provide realistic throughput estimates that account for system latency, clarifying that theoretical speed does not translate directly to task completion rates.
Finally, I begin defining optimal context management parameters to balance memory efficiency with processing needs.

Formulating an optimized system architecture for efficient and reliable AI operation.
I prioritize a compact context window to mitigate memory constraints and prevent performance degradation in long sequences, relying instead on compaction strategies and external memory storage.
The primary model is configured with moderate quantization to balance resource usage with tool-call accuracy, while the embedding component remains high-precision to ensure robust semantic understanding.
Concurrent processing is structured around a single large worker supplemented by multiple I/O threads to maximize throughput without overloading system resources.

Formulate a transparent verification strategy that acknowledges current limitations while providing actionable alternatives.
I will structure the source list as a precise verification queue containing specific claims and corresponding evidence locations to ensure accountability.
Additionally, I will design an automated research script that enables users or agents to independently gather real-time data through standard interfaces.
This approach transforms the inability to browse directly into a robust framework for obtaining accurate, up-to-date information.

I am structuring a comprehensive technical response that compensates for limited real-time access by integrating locally executable data collection scripts.
I plan to include precise commands for gathering current release information and model metadata, alongside a framework for local performance evaluation.
The output will follow a strict hierarchical format to ensure clarity and completeness across all required sections.
This approach ensures the final deliverable remains actionable and evidence-based despite the absence of direct web browsing capabilities.

I am calibrating the scope and depth of my response to align with the extensive requirements.
I carefully weigh the need for comprehensiveness against readability to determine an optimal word count.
I resolve to target a substantial length that accommodates all specified deliverables without unnecessary padding.
My focus remains on delivering a dense, high-quality analysis while maintaining strict adherence to the requested structure.

Maintaining a strict boundary between evidence-based architectural specification and dynamic inquiry.
I am structuring the response to reflect a static, pre-defined system design rather than an active research process.
The focus remains on establishing a robust, localized infrastructure that prioritizes privacy and deterministic control over external dependencies.
This approach ensures the output serves as a definitive technical blueprint without engaging in speculative or live literature analysis.

Plan the structural organization of the comparative analysis to ensure clarity and readability.
Evaluate the trade-offs between tabular layouts and categorical groupings to determine the most effective presentation format.
Refine the output strategy to align with user requirements for concise, elegant language while maintaining technical precision.
Finalize the approach to deliver a comprehensive yet streamlined response that meets all specified constraints.

Structuring a comparative analysis of AI tooling ecosystems
I am designing a compact matrix to evaluate distinct software categories against key performance metrics.
I am refining the layout to balance brevity with comprehensive coverage by utilizing abbreviated headers and concise entries.
I am preparing to articulate the nuanced trade-offs inherent in each selection through detailed explanatory sections.

Analyzing resource allocation and performance constraints for large language model inference.
I evaluate memory budgets across different usage profiles to ensure system stability and efficiency.
I calculate key-value cache requirements for various model architectures to identify optimal configurations.
I assess bandwidth limitations to determine feasible throughput for dense models under specific quantization schemes.

I am analyzing hardware performance metrics and formulating a deployment strategy for an AI model.
I evaluate theoretical bandwidth limits against active memory requirements to establish realistic inference ceilings.
I design admission control mechanisms based on system resource thresholds to prevent overload during execution.
I outline a phased installation plan utilizing specific directory structures and external storage configurations.

Establishing a robust local inference environment
I am designing a streamlined setup process that prioritizes security and compatibility by leveraging standard package managers and isolated virtual environments. To ensure reliability, I am evaluating multiple methods for retrieving model weights, balancing the convenience of dedicated command-line tools with the universality of direct HTTP requests. My approach involves configuring the server with precise parameters to optimize performance while maintaining a clean and reproducible deployment structure. Finally, I plan to validate the system's functionality through automated testing to guarantee seamless operation from initialization to response generation.

Refining the configuration and verification strategy for the local inference service.
I am carefully evaluating command-line flags to ensure compatibility with the specific build while minimizing unnecessary parameters.
I plan to adjust memory allocation settings to optimize performance within constrained resources.
Finally, I will outline a structured workflow for autonomous coding tasks using isolated repositories.

Refining the strategic architecture for the user's request.
I am evaluating whether to prioritize an existing agent harness or a custom orchestration layer to ensure both flexibility and reliability.
After weighing the trade-offs between immediate execution capabilities and long-term maintainability, I have decided to adopt a hybrid approach that leverages established tools as executors while building a custom adapter for seamless integration.
This decision ensures that the solution remains robust and adaptable, allowing for future swaps without compromising the core system stability.

I am structuring a comprehensive, phased roadmap for an autonomous AI system.
This plan details the evolution from foundational data handling to complex multi-agent orchestration and continuous operation.
I organize each stage by specifying technical components, configuration strategies, and robust failure recovery mechanisms.
The architecture centers on a centralized supervisor managing diverse roles within a secure, version-controlled environment.

Establishing a comprehensive digital ecosystem for autonomous operations.
I am organizing persistent storage into distinct layers for active work, archival evidence, and long-term memory.
This structure ensures data integrity through append-only logs and version-controlled fact repositories.
The design supports modular task isolation while maintaining a unified global knowledge base.

Structuring the system architecture and data models to align with specified operational constraints.
Refining database schemas to ensure robust state management, lease mechanisms, and idempotency.
Designing visual representations of component interactions and agent lifecycle stages.
Formulating a unified model strategy that adapts capabilities across diverse functional roles.

I am structuring a comprehensive, cost-efficient AI deployment strategy tailored for constrained hardware environments.
I prioritize a deterministic classification layer and lightweight summarization to maximize performance on limited resources while reserving heavy lifting for final synthesis.
I plan to detail operational resilience, remote access security, and phased implementation steps alongside clear constraints and upgrade paths.
I will also define the specific evidence required to challenge these decisions, ensuring the approach remains rigorous and falsifiable.

Refining the architectural strategy to align with hardware constraints
I am evaluating conditional triggers for model and engine selection based on performance benchmarks and reliability metrics. I recognize that managing a large number of logical subagents requires distinguishing between concurrent inference capabilities and total agent count to ensure feasibility on limited resources. Consequently, I am redefining the system's scope to prioritize a single active inference thread while supporting extensive logical agent orchestration. This approach ensures optimal resource utilization without exceeding physical memory limitations.

Synthesize a rigorous verification pipeline for research claims.
I structure the process into distinct phases from source discovery to contradiction scanning, ensuring every claim is anchored to verifiable evidence.
By enforcing strict reference requirements and independent validation passes, I guarantee that conclusions are supported by concrete data rather than mere assertions.
This approach transforms raw information into trusted knowledge through systematic segmentation and cross-claim analysis.

Evaluating the necessity of providing executable code.
I am analyzing a robust anti-hallucination framework that prioritizes strict evidence citation, quote verification, and source quality assessment over generic retrieval methods.
The system emphasizes negative search capabilities to disprove high-stakes claims and prevents model-generated bibliographies by enforcing rigid structural validation.
I am currently deliberating on whether to include actual code implementations for this architecture in my response.

Synthesizing a concise technical specification to concretize the system architecture.
I construct a compact state-machine sketch that illustrates the core operational loop and policy enforcement mechanisms.
This approach transforms abstract concepts into tangible code structures while maintaining brevity and clarity.
The resulting output provides a direct, executable reference for the intended implementation logic.

Refining the technical specifications for the build architecture.
I am defining the core worker interface and event structure to ensure a robust implementation framework.
I have decided against using external routing proxies in favor of a simpler, in-process solution to minimize dependencies.
I am also evaluating lightweight model management options to balance ease of use with necessary control over system parameters.

I am refining the structure and tone of my response to ensure accuracy and elegance.
I will explicitly state that I cannot verify specific future product details to avoid fabrication.
I plan to categorize tools as experimental rather than production-ready dependencies.
Finally, I will organize the content into concise sections with clear evidence notices.

I am planning the structure and content of my response.
I intend to organize the output into research reasoning and concrete specifications to ensure clarity and avoid redundancy. I will carefully manage the length by cross-referencing information rather than repeating it. Additionally, I will define my knowledge boundaries accurately to maintain honesty about my capabilities.

Verifying the authenticity of provided source links.
I am cross-referencing repository URLs and documentation paths to ensure they are accurate and accessible.
This process involves confirming specific project locations and their current structural integrity.
The goal is to establish a reliable foundation for answering the user's inquiry based on verified information.

Verifying the validity and relevance of the provided resource links.
I confirm that each URL is active and correctly points to its intended documentation or repository.
For specific entries like the arXiv API, I evaluate alternative paths to ensure robustness and accuracy.
This process ensures that all referenced materials are reliable and accessible for future use.

Refining the reference strategy to prioritize verified primary sources while omitting unverifiable secondary citations.
I will designate known URLs as primary data points without claiming they were fetched in this session, ensuring transparency about verification status.
To maintain integrity, I will explicitly note the absence of independent benchmarks rather than fabricating or padding with unverified sources.
The final response will be structured with clear formatting and include specific API endpoints as foundational data for the proposed script.

Analyzing the memory bandwidth constraints to estimate decoding throughput.
I calculate the active parameter volume for the mixture-of-experts architecture by summing attention, routing, and expert weights.
This figure is compared against a dense model's load to determine the theoretical speedup ratio under ideal conditions.
Finally, I account for real-world hardware inefficiencies to provide a realistic performance expectation.

Refining memory allocation estimates for the specified model architecture.
I recalculated the key-value cache and weight sizes to adjust the inference budget upwards while maintaining the total system limit.
I established distinct operational profiles for different usage scenarios and defined optimal context window parameters based on these constraints.
Finally, I noted contingency plans for potential weight size variations to ensure stable performance.

Thinking completed

## Run notes

chat.qwen.ai, new chat, Qwen3.8-Max, mode menu Thinking. The thinking panel's heading
reads "Thinking and Search"; the answer itself says browsing/tools OFF, as in runs 5
to 8. Answer copied by the author from the app and written verbatim from the clipboard;
the thinking panel was pasted by the author into the session and written verbatim from
that.
