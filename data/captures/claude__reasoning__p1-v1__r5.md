---
run_id: claude__reasoning__p1-v1__r5
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
replicate: 5
date_stamped: '2026-10-14T07:13:27+00:00'
date_run: '2026-10-14T07:13:27+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

Starting with whether the hardware exists as specified, then the rest of the ecosystem.

**Claude Sonnet 5.5 (Anthropic) | knowledge cutoff: end of June 2026 | web search and fetch: ON** (about 45 queries and 1 page fetch; everything dated after June 2026 below comes from live sources).

**Date:** your prompt says 31 Aug 2026 but the system clock says 14 Oct 2026, so I used Oct 14. The M6 mini was announced Aug 25 and ships Sept 22, so Aug 31 would predate availability. **Disclosure:** I am an Anthropic model, so I scored Claude Code on the same criteria as the others and flag where that matters.

**Evidence legend:** [V] verified in a source I read this session. [EST] my derivation, not measured on an M6. [UNV] believed but not verified.

Three limits on the evidence:
- I found no independent M6 LLM benchmarks, only Apple's claims and one secondary 9B test. Every M6 tok/s figure below is an extrapolation from bandwidth.
- Nearly all coding scores are vendor-reported. Treat them as priors and gate them with your own evals.
- Several key projects (oMLX, Ornith, Pi) are new or single-maintainer. I pin versions and keep fallbacks.

---

## Decisions at a glance

| Layer | Pick | Confidence |
|---|---|---|
| Hardware reality | Decode is bandwidth-bound, so only MoE models give usable agent throughput. Dense 27B is a slow "deep thinking" tier. | high |
| Inference server | oMLX (MLX, continuous batching, RAM+SSD KV cache). Fallbacks: mlx-lm, Ollama, llama.cpp. | 65% |
| Workhorse model | Ornith-1.5-35B-A3B at ~4.5 bpw (MIT), promoted only if it beats Qwen3.6-35B-A3B on your gold tasks | 60% |
| Deep model | Qwen3.8-27B (Apache 2.0), loaded on demand, never co-resident with the workhorse | 80% |
| Sidecars | Qwen3-Embedding-0.6B + Qwen3-Reranker-0.6B. Task classification via embedding kNN, not an LLM. | 85% |
| Worker harness | OpenCode, headless, inside the sandbox. Pi as lean alternative. Claude Code only as optional cloud worker. | 70% |
| Orchestration | Custom thin control plane: Python + FastAPI + SQLite (WAL) lease queue. No Temporal, Postgres or LangGraph. | 80% |
| Structured pipelines | Pydantic AI for research and verifier pipelines | 60% |
| Memory | Git-tracked Markdown vault + SQLite (FTS5 + sqlite-vec) index | 90% |
| Sandbox | Apple `container` microVM per task, non-admin `agent` user, mitmproxy GET-only egress allowlist, host-side git and secret brokers | 70% |
| Always-on | LaunchDaemons + pmset + UPS + FileVault ON with SSH pre-boot unlock over Ethernet + off-box dead-man ping | 80% |
| Remote | Tailscale (tailnet only), `tailscale serve` PWA, ntfy push, passkey-gated approvals | 80% |
| Research | Evidence-ledger pipeline + multi-database citation resolver + SearXNG/OpenAlex/Semantic Scholar/arXiv/Crossref | 80% |
| Cloud | Optional escalation only: DeepSeek V4.1 Flash for non-sensitive bulk work, Opus 5.5 or GPT-6.1 Sol for hard planning and review | n/a |

### Market matrix

| Category | Best overall | Best for this HW | Best OSS | Lightweight | Mature/stable | Cutting-edge | **Use** |
|---|---|---|---|---|---|---|---|
| Inference engine | MLX-based | oMLX | oMLX / llama.cpp | llama.cpp | Ollama / llama.cpp | oMLX + MTP | **oMLX** (fallback Ollama) |
| Coding model | frontier cloud (Opus 5.5); open: MiMo-V2.6-Pro (won't fit) | Ornith-1.5-35B-A3B | Ornith / Qwen3.8-27B | Qwen3.5-9B class | Qwen3.6-35B-A3B | Ornith 1.5 | **Ornith + Qwen3.8-27B** |
| Coding harness | Claude Code with Claude models | Pi / OpenCode | OpenCode | Pi | OpenCode | Pi extensions, Hermes | **OpenCode** |
| Orchestration | Temporal | SQLite lease queue | DBOS / Temporal | SQLite | Temporal | DBOS + Pydantic AI | **SQLite lease queue** |
| Memory | Postgres + pgvector | SQLite FTS5 + sqlite-vec | same | Markdown + ripgrep | Postgres | temporal KG | **Markdown + SQLite** |
| Sandbox | per-task microVM | Apple `container` | Lima / Apple `container` | Seatbelt | Docker / Lima | Apple `container` | **Apple `container`** |
| Remote | Tailscale | Tailscale | WireGuard / Headscale | SSH over WireGuard | Tailscale | n/a | **Tailscale** |

---

## 1. Local inference

**What the chip gives you.** The M6 has a 12-core CPU and a 12-core GPU with a Neural Accelerator in every GPU core. Memory tops out at 32GB with up to 170GB/s of bandwidth. The M6 Mac mini has a 12-core GPU with Neural Accelerators in each core, ships with 16GB configurable to 32GB, and has up to 170GB/s memory bandwidth. Apple claims LM Studio prompt processing is up to 4.8x faster than on the M4 mini. One secondary test of a 9B Q4 GGUF in llama.cpp measured prompt processing at 742 tok/s versus 210 on the M4, and generation at 26.9 versus 18 tok/s. Prefill gained 3.5x and decode only 1.5x, which is the shape you expect: prefill is compute-bound, decode is bandwidth-bound, and at 170GB/s a 4-bit 27B dense model tops out around 10 tok/s.

My decode estimates for M6 [EST]:

| Model class | Bandwidth ceiling | Realistic |
|---|---|---|
| 35B-A3B MoE, ~2GB read per token | ~80 tok/s | 40-50 tok/s |
| 27B dense, ~16GB read per token | ~10 tok/s | 10-14 tok/s (more with MTP speculation, unverified) |

Sanity check: the 9B measurement above is 87% of its bandwidth ceiling. A Reddit report on a 32GB M5 base machine shows about 40 tok/s on Qwen3.6 35B-A3B MLX versus 10 to 16 tok/s on Qwen3.8 27B. That chip has roughly 10% less bandwidth than the M6 [UNV: from my training data].

**GPU memory cap (this will bite you).** Metal exposes about 75% of RAM to the GPU by default, and `iogpu.wired_limit_mb` can raise it. That is about 24GB on your machine. MLX documents `max_recommended_working_set_size` as the system wired limit and refuses a larger request. Wired memory cannot swap. A mlx-lm issue reports `mlx_lm.server` wiring 75% of RAM by default, and a failed GPU allocation caused a kernel panic rather than a clean exit. Consequences:
- Budget the model, KV cache and scratch against about 25GB (set `iogpu.wired_limit_mb=25600`).
- Cap the server's memory explicitly.
- A panic with FileVault on means the box stays down until you unlock it (see §8).

**Engines**

| Engine | Strengths | Weaknesses | Verdict |
|---|---|---|---|
| oMLX | Continuous batching, hot RAM plus cold SSD KV tiers with prefix sharing, OpenAI and Anthropic APIs, VLM, embeddings and rerankers in one server. Lists M5 support. | Single maintainer, v0.x. M6 not explicitly listed [UNV]. | **Primary** |
| mlx-lm server | Apple reference implementation | Wires 75% of RAM by default (above). Fewer serving features. | Baseline and fallback |
| Ollama 0.32.x | MLX backend since 0.19; its own benchmark on Qwen3.5-35B-A3B went from 58 to 112 tok/s decode on an M5 Max. One-command pulls. | The `qwen3.8:27b-mlx` build rejects the "developer" role on `/v1/responses`, breaking `ollama launch codex`. A reported memory-growth bug on an MLX runner (Aug 2026). | Convenience fallback |
| llama.cpp | GGUF, GBNF grammars for guaranteed JSON, widest architecture coverage. MLX does not enforce schema-level structured output. | A recent paper reports its prefill trailing MLX on M5 Pro MoE models. | Sidecar for strict-JSON tasks |
| LM Studio | GUI, MLX runtime | A user's config notes its bundled MLX runtime did not recognize Qwen3.6 MTP layers. GUI-centric. | Not for a daemon |
| BaseRT, MLC, vLLM ports | Research or young | Not production for you | Skip |

**Models (vendor numbers are priors, not facts)**

| Model | Facts | Fit on 32GB |
|---|---|---|
| **Ornith-1.5-35B-A3B** | Released Aug 18, MIT, 262K context, MLX and GGUF builds published. Vendor card: SWE-bench Verified 79, Pro 59.6 (OpenHands harness, 5-run average), versus 73.4 and 49.5 for Qwen3.6-35B-A3B. I found no independent evaluation. | 4-bit MLX ≈ 19.5-21GB. The 1.0 MLX 4-bit used 21.2GB peak in one run. |
| **Qwen3.6-35B-A3B** | Released Apr 15, SWE-bench Verified 73.4. About 20.5GB, Terminal-Bench 51.5%. Most field-tested. | ≈ 20GB at Q4 |
| **Qwen3.8-27B** | Dense multimodal, Apache 2.0, 262K context; vendor reports SWE-bench Pro 61.7 and OSWorld-Verified 84.3. Artificial Analysis index 34, first of 142 models in its size class, but verbose: it took about six times longer to finish the index than a fast MoE. Scores come from the vendor's own runs. | 16-19GB at 4-bit |
| Gemma 4 26B-A4B / 31B | Apache 2.0, released Apr 2. Weak coding (31B: SWE-bench Pro 35.7 on Ornith's table). Useful as an independent-lineage verifier [UNV]. | ~15-17GB |
| Qwen3.8-Flash-Next 125B-A6B | Needs 96-114GB at 4-bit; AA index 40. | No |
| Nemotron 3.5 Lightning, Muse Glimmer 30B | AA 13 and 17 per the same source | Skip |

Not released: community requests for Qwen3.8-35B-A3B are open on the Qwen3.8-27B repo. A Reddit comment says it is coming [UNV]. Re-check weekly. If it ships, it likely replaces Qwen3.6 as the fallback.

**What you should actually run**
- **Workhorse:** Ornith-1.5-35B-A3B MoE at 4.0-4.5 bpw. Fallback: Qwen3.6-35B-A3B.
- **Deep tier:** Qwen3.8-27B at ~4.25 bpw, loaded only when the router asks for it.
- **Quantization:** 4.5 bpw (~19.5GB) with 2 streams, or 3.8-4.0 bpw (~17GB) with 3-4 streams. Choose by eval, not by taste.
- **Context:** working window 32-48K, hard cap 96K. The 262K native window is a trap here: KV is affordable [EST, below], but cold prefill is not. 64K cold at an EST 500-1,000 tok/s is 1-2 minutes.
- **KV size [EST]:** Qwen3.5-architecture models keep full attention in only 1 of 4 layers. The Ornith card describes 40 hybrid layers with 2 KV heads. At head_dim 256 that is ≈ 20KB per token, so 2 streams × 48K ≈ 1.9GB. Qwen3.8-27B (16 attention layers) is ≈ 65KB per token if it has 4 KV heads, so 2 × 48K ≈ 6GB. Check `config.json` for the real numbers.
- **Concurrency:** one server, 2-4 batched streams. Never several copies of a model.
- **Swapping:** worth it, because both models can't be co-resident (≈ 36GB against a 25GB cap). Loading ~17GB from internal SSD takes seconds. Schedule in model epochs of at least 10 minutes to avoid thrash.
- **Bottlenecks, in order:**
  1. Cold prefill on long agent contexts. Mitigate with the oMLX SSD prefix cache.
  2. Decode bandwidth on the dense tier.
  3. The wired-memory ceiling.
  4. CPU contention from builds starving the inference feeder.
  5. Thinking-token verbosity. Use `reasoning_effort` low or medium for edit loops.
  6. MLX lacked chunked prefill as of a March 2026 article, so one long prefill stalls other streams. Don't start cold giants while others decode. Re-test on oMLX.
- **Batching caveat:** An oMLX community run on an M2 24GB showed 4 concurrent requests scaling 4.0x. That is almost certainly an artifact of identical prompts hitting identical experts. Plan on 1.5-2.5x aggregate at 4 heterogeneous streams for the MoE [EST], and measure.

---

## 2. Agent runtimes and harnesses

| Runtime | What I verified | Gap for your spec | Verdict |
|---|---|---|---|
| **Claude Code** (closed) | Worktrees, subagents in their own worktrees, and a Remote Control server mode with `--spawn worktree --capacity N`. Very active release cadence (v2.1.260). Local models work via an Anthropic-compatible endpoint. | Tuned for Claude models. A January 2026 report found local-model use impractical then (stale, pre-Qwen3.6). Remote Control appears to depend on Anthropic's relay and an account [UNV], which breaks "useful with no cloud". | Optional cloud-escalation worker |
| **OpenCode** (MIT) | A fleet operator reports it is the one that gets open-weight models doing useful work on their own hardware. 75+ providers, LSP, build and plan agents, SDK. Roughly 200k stars (an activity signal only). | No hard permission model. Provide it via the sandbox. | **Primary worker** |
| **Pi** (MIT) | Four tools and a system prompt under 1,000 tokens. No built-in MCP, subagents, permission popups or plan mode, by design; 2,143 packages; owned by Earendil since April. | Everything else is an extension you vet. | Lean alternative. Best prefill economy. |
| **Codex CLI** (Apache-2.0) | `--oss` local mode, sandboxed by default | OpenAI-tuned. The `/v1/responses` bug above on Ollama MLX. | Skip for local |
| **Hermes Agent** (MIT) | Cron scheduler, isolated subagents, persistent memory, a Skills Hub, and a default "local" backend that runs commands directly on your machine. | Self-writing skills are a persistence vector for prompt injection. | Not the core. Maybe a chat front-end later, in its own sandbox. |
| **OpenClaw** | Rapid growth with security headaches, and academic papers use it as a vulnerability case study. A reported inbox agent deleted messages unexpectedly. | Broad default access | No |
| Goose, OpenHands, Aider, Qwen Code | Qwen Code is best for Qwen models and worst for anything else. | Redundant | No |

**Decision: custom thin control plane with an existing harness as the worker.** I found no product combining all of:
- a lease-based durable queue
- per-task sandbox with allowlisted egress
- tiered approvals from a phone
- model-tier routing with escalation
- an append-only audit chain

Claude Code's server mode and Hermes each cover a subset and couple you to their own state and security model. The control plane is roughly 2-3k lines. The hard parts (agent loop, edit tools, LSP) come from OpenCode. Keep the interface narrow so the harness is swappable: `run(task_spec, sandbox, model_endpoint) -> event stream + exit code`.

---

## 3. Multi-agent architecture

| Concept | Meaning | Cost here | Verdict |
|---|---|---|---|
| 100 simultaneous model instances | 100 copies of weights | 100 × ≥17GB: impossible | No |
| 100 logical agents | 100 rows in `agent_defs` (role, tools, permissions, tier, budgets) | ~0 RAM idle | **Yes** |
| Agent run | A leased task executing a spec in a sandbox, calling the shared inference server | 1 VM + 1 stream | Unit of work |
| Worker pool | N slots per resource class (GPU streams, VMs, browser, cloud) | Bounded by hardware | **Yes** |
| Dynamic subagents | A parent calls `spawn(spec)` on the control plane. Policy validates: tools ⊆ parent's, egress ⊆ parent's, budget ≤ parent's remainder. | Central enforcement | **Yes**, never via harness-internal subagents |
| Hierarchical coordinator/worker | Planner emits a task DAG, workers run leaves, verifier runs separately. Coordinate via artifacts (git, SQLite), not chat. | Cheap | **Yes** |
| Swarm / peer chat | Agents talking to each other | Tokens are the scarce resource at ~45 tok/s | No |
| Sequential vs parallel | Parallelize only unsaturated resources | | Mostly sequential per repo |

**Scheduler lanes**

| Lane | Capacity | Why |
|---|---|---|
| `gpu_stream` | 3 (2 in the 4.5 bpw profile) | Batched on one server |
| `vm` | 2 | 2GB each, 4 cores max |
| `browser` | 1 | 1GB, research profile only |
| `cloud` | 2 | Budget-capped |
| CPU build/test jobs | ≤ 2 concurrent | Keep ~2 cores free for the inference feeder. Run tests under `taskpolicy -b`. |

Each task requests lanes via `resource_class`. The scheduler groups by model epoch, applies priority then FIFO, and backpressures when memory pressure is yellow.

**Throughput [EST]**
- One MoE stream: about 3K tokens of tool output prefilled in ~4s plus ~800 decoded tokens in ~18s, so ~25s per step and ~140 steps/hour.
- 2-3 streams: ~250-350 steps/hour aggregate.
- Overnight (8h): ~2,000-2,800 steps. At 40-80 steps per medium task including retries, that is ~25-70 tasks per night if specs are crisp.
- The dense tier does ~50 steps/hour, so use it for planning, review and hard debugging only.

**Stop conditions (enforced by the control plane, not the model)**
- Token, step and wall-clock budgets per task and per day.
- Loop detector: hash of the last 6 tool calls and diffs.
- No-progress detector: the same failing-test signature 3 times.
- Max spawn depth 3, max fan-out 8.
- Explicit success predicate (tests green plus review pass).

---

## 4. Coding agents

| Axis | OpenCode | Pi | Claude Code | Codex CLI |
|---|---|---|---|---|
| Repo understanding | LSP integration | grep/read only | strong | good |
| Terminal and edits | yes | yes (4 tools) | yes | yes |
| Test/debug loop | model-driven | model-driven | model-driven plus hooks | model-driven |
| Git and worktrees | manual | manual | native worktrees | manual |
| Long tasks | sessions, server mode | extensions | background and Remote Control | cloud mode |
| Code review | agent config | extension | `/code-review` | built in |
| Context management | compaction | minimal prompt | compaction | compaction |
| Local models | first-class | yes | via endpoint | `--oss` |
| Sandbox | external | none by design | opt-in OS sandbox | Seatbelt default |

**Pick:** OpenCode inside the microVM as the default worker. Pi is the lean variant if prefill cost dominates (run both on the gold set in Phase 2 and keep the winner). Claude Code with Opus 5.5 is the cloud escalation target, because the harness and model pairing is strongest there (my judgment, and I am not neutral).

**Workflow**
1. Planner emits a task spec: goal, acceptance tests, files in scope, budget.
2. The control plane makes a **fresh clone** (`git clone --local`) per task, not a worktree. Worktrees share `.git`, so a hostile agent can plant hooks or config there. One example is `core.fsmonitor` in a cloned repo's git config, which git runs outside the sandbox with no prompt.
3. The worker loops until the deterministic gates pass: tests, lint, types, secret scan, diff-size limit, forbidden-path check.
4. A separate read-only reviewer runs on the deep tier with a fresh context.
5. The host-side broker fetches only the `agent/<task>` branch. Objects and refs only, never config or hooks. You approve the merge from your phone.

Rules: never run host-side git inside an agent clone without `-c core.hooksPath=/dev/null -c core.fsmonitor=false`. Never rely on harness approval classifiers as the security boundary: Anthropic described its auto mode as a best-effort classifier rather than a guarantee, and a researcher reported 60 to 80 percent attack success against it.

---

## 5. Research agents

Preventing hallucinated citations is an architecture property, not a tool. A 2026 study measured 5-18% non-resolving and 3-13% hallucinated citation URLs from commercial LLMs and deep-research agents.

**Pipeline**
1. **Decompose** the question (worker tier).
2. **Discover** via self-hosted SearXNG plus OpenAlex, Semantic Scholar, arXiv, Crossref and PubMed APIs. Dedupe by DOI, arXiv ID or title hash.
3. **Acquire.** A deterministic fetcher stores raw bytes, extracted text, sha256 and `retrieved_at`. The model never creates source records.
4. **Extract.** The LLM proposes `(claim, quote, char_range)`. Code checks the quote is a verbatim substring of the stored text and rejects it otherwise.
5. **Verify.** Entailment check (does this span support this claim?) on a different tier. Optionally add a different model lineage such as Gemma 4. Re-check numeric claims against tables.
6. **Contradiction audit.** Cluster claims by normalized proposition, compare polarity across sources, and emit conflict sets.
7. **Write** under closed-world citation. The writer may only emit `[@ev:ID]` tokens. A renderer resolves them. Any sentence without an ID must be tagged "inference" or dropped. A linter enforces this.
8. **Reference audit** on the final bibliography. RefChecker checks references against Semantic Scholar, OpenAlex, CrossRef, DBLP and ACL Anthology, and uses LLM-driven web search to flag likely fabrications, with retraction screening via OpenAlex. Its authors audited 221,281 references across 3,703 papers for about $157. CiteTracer uses a cascade of local cache, direct URL fetch, scholar databases and then web search. Borrow the design, and check RefChecker's license before depending on it [UNV].

PDF parsing: PyMuPDF for born-digital files. Use the Qwen3.8-27B vision path for scans and figures. I did not verify Docling or other parsers, so bake them off on 20 of your own PDFs.

I did not verify the current state of GPT-Researcher, STORM, PaperQA or LangChain open_deep_research. I would not build on them unreviewed, because none gives you the ledger guarantee above.

**Local vs cloud:** run private-document research fully local. For public-web research, local is fine. Optionally send only verified evidence snippets (never private files) to a cloud model for final prose.

---

## 6. Persistent memory

| Store | Use | When |
|---|---|---|
| Markdown vault (git) | Canonical. Decisions (ADRs), lessons, project notes, `AGENTS.md` per repo. | **Day 1** |
| SQLite events table | Episodic log: every task, tool call and outcome | **Day 1** |
| SQLite FTS5 + sqlite-vec | Hybrid retrieval with reciprocal-rank fusion, rebuildable from the Markdown | **Phase 4** |
| Embeddings | Qwen3-Embedding-0.6B 4-bit (~600MB, ~50ms per embed) + 0.6B reranker, served by oMLX. A local project (memo) already combines MLX embeddings, sqlite-vec, FTS5 and a reranker. Copy the design, don't depend on it. | Phase 4 |
| Knowledge graph | Plain SQLite `nodes` and `edges` tables | Only when multi-hop recall tests fail |
| Postgres + pgvector, Qdrant, Neo4j | | Only past ~5M chunks or multiple writer processes |

**Scoping:** project memory lives in `<repo>/.agent/` and the vault's `projects/<name>/`. Global memory is `~/memory/global/`.

**Write policy (anti-poisoning)**
- Agents propose memory items. A curator job dedupes and validates them.
- Items derived from web or untrusted content get a `provenance: untrusted` tag. They are never promoted into instructions and are always injected as data.
- Items carry TTL and `supersedes`.
- Store negative experiment results explicitly.

---

## 7. Computer control

**Capability ladder (stop at the lowest rung that works)**
1. Terminal and filesystem in a per-task microVM (default).
2. Headless Chromium or Playwright in a microVM with a throwaway profile, no cookies, research egress profile.
3. A disposable macOS guest VM for Mac-only GUI work (Xcode, native apps). Phase 8 only.
4. The host desktop: **never**.

**Isolation options**

| Option | Verdict |
|---|---|
| Docker Desktop | Skip. One shared VM, heavier. |
| Lima | Solid fallback |
| **Apple `container`** | On macOS 26, each container runs in its own lightweight VM. A third-party sandbox tool reports its Apple-container backend is 10-20x faster than Lima and uses about a third of the RAM per sandbox (experimental, unaudited). **Pick.** |
| Seatbelt tools (nono, ai-jail) | Exist for macOS. Useful for host-side tools. |
| Separate Mac | Ideal but expensive |

Linux ARM64 microVMs cover most dev work. They cannot build Apple-platform software.

**Layers**
- **Users:** `roshan` (you, untouched), `agent` (standard, non-admin, runs control plane, inference and sandboxes), `broker` (holds deploy keys and cloud API keys, serves local sockets with policy).
- **Network:** microVMs have no direct internet. Egress goes through a mitmproxy addon (domain allowlist, GET/HEAD only, logging), enforced by `pf` rules on the host. An allowlisted `github.com` over a bare CONNECT proxy is an exfiltration channel, which is why I want method filtering via MITM.
- **Secrets:** none in the sandbox. The git broker pushes only `agent/*`. The cloud gateway lives in `broker`, redacts, applies sensitivity labels and enforces budgets.
- **Split the lethal trifecta.** The trifecta is private data, untrusted content and external communication, and coding agents satisfy it by default. Coding agents get private code and exec, but only a package-registry allowlist and no open web. Research agents get the open web, but no private repos and no exec beyond a parser. Google's April 2026 study of Common Crawl found malicious prompt injections in public pages up 32% from Nov 2025 to Feb 2026.

**Honest risks:**
- Apple `container` is young.
- I could not verify it running as a non-GUI user. Test in Phase 0, with Lima in a LaunchDaemon as the fallback.
- `pf` egress enforcement is DIY and must be tested.

---

## 8. Always-on operation

- **Sleep:** `pmset -a sleep 0 disksleep 0 displaysleep 0 autorestart 1 womp 1`. Wrap long jobs in `caffeinate -s` as belt and suspenders. Turn off auto-install of macOS updates and apply them weekly with `fdesetup authrestart`.
- **Services:** LaunchDaemons in `/Library/LaunchDaemons` with `UserName=agent`, `KeepAlive`, `ThrottleInterval`. They start at boot with no login.
- **FileVault, decided:** ON, on wired Ethernet. Apple documents that on Apple silicon with macOS 26 or later, FileVault can be unlocked over SSH after a restart if Remote Login is on and the network is available. One user tested it and found it worked on Ethernet, and on Wi-Fi only from 26.5. Buy a UPS. Limits:
  - After a power cut or kernel panic the Mac sits at the pre-boot screen until you unlock it.
  - Tailscale is not up yet, because the data volume is locked. Unlocking needs LAN reachability, so put WireGuard on your router (or another always-on box) [my reasoning, UNV].
  - If you will be away for weeks with no router VPN, the alternative is FileVault OFF with auto-login of `agent`. Do that only if the machine holds nothing sensitive.
- **Recovery matrix:**

| Failure | Detection | Automatic response |
|---|---|---|
| Harness crash | missed heartbeat (30s) | lease expires, task requeued attempt+1, fresh sandbox from last checkpoint branch |
| Inference hang or crash | 60s probe, 3 fails | `launchctl kickstart -k`. After 3 restarts in 15 min, drop to the 3.9 bpw single-stream profile and alert. |
| Control plane crash | launchd | restart, reconcile leases |
| External SSD gone | mount watchdog | pause VM lane, mark infra failure (no attempt burned), alert |
| Disk <10% free | watchdog | pause intake, GC workspaces and caches |
| Runaway agent | budgets or loop detector | kill microVM, fail with `budget`, auto-create a postmortem task |
| Power or panic | dead-man ping stops | UPS covers short outages. Alert you. SSH unlock. |

- **Off-box dead-man switch:** the mini pings a healthchecks-style endpoint every minute. If pings stop, your phone alerts. It sees only liveness.
- **Checkpointing:** the agent maintains `PROGRESS.md` in its clone, and the step log lives in SQLite. A 150-line SQLite event log plus a step wrapper gives resumable runs. Temporal or DBOS only when you hit a problem this can't solve. DBOS is described as a Postgres-backed library.

---

## 9. Remote access

| Need | Mechanism |
|---|---|
| Transport | Tailscale (WireGuard mesh). Nothing exposed to the public internet. Alternative with no vendor control plane: WireGuard or Headscale. |
| Shell | Tailscale SSH in check mode (periodic re-auth). Phone client: Blink or Termius. |
| Dashboard | FastAPI on 127.0.0.1, published via `tailscale serve`. Mobile-friendly PWA for status, queue, logs, approvals and the emergency stop. |
| Notifications | ntfy (self-hosted, ACL'd) or Pushover. The payload is only an approval ID plus a summary. |
| Approvals | The notification opens an approval page showing the full action and diff. A **WebAuthn passkey** confirms Tier-2 actions, so a forged notification or stolen tailnet session isn't enough. Unapproved tasks park, not fail, and expire after 24h. |
| Emergency stop | Big button in the PWA, plus `ssh lab agentctl panic`. |
| Auth | Tailnet identity ACL (phone and laptop tags only), app-level passkey for approvals, rate limits |

Skip Claude Code Remote Control as core infrastructure: it ties remote control to a vendor relay. Cloudflare Tunnel is possible but adds a public edge you don't need.

---

## 10. Storage

| Item | Location | Reason |
|---|---|---|
| macOS, tools, `agent` home | Internal | |
| SQLite control DB (WAL), audit shadow | Internal | fsync latency, small writes |
| Served model weights (~50-60GB) | Internal | An external disconnect would crash inference |
| oMLX cold KV cache | Internal, 40GB cap, monitor writes | Restoring a 20K-token prefix (≈0.4GB) takes ~0.2s versus tens of seconds to recompute |
| Container images and VM disks | Internal | |
| Per-task clones and workspaces | **External** (case-sensitive APFS) | Disposable, churny, size-hungry |
| Build and package caches (uv, npm, cargo, HF) | **External** | Write-heavy |
| Research corpus (PDFs, extracted text), datasets, experiment outputs | **External** | Bulk |
| Logs older than 7 days | **External** | |
| Backups | **External** + encrypted offsite (restic) | The external disk is not a backup of itself |

- **Internal SSD is soldered.** The M6 mini's internal SSD is not replaceable, and Apple exposes limited wear telemetry. Treat write volume as a budget and keep churn on the external drive. If KV cold-tier writes exceed ~100GB/day, move it to the external SSD.
- **External throughput:** the M6 has Thunderbolt 4 (three TB4 ports on the M6 model). Expect ~2.5GB/s sequential from a good NVMe enclosure [EST]. Use one with active cooling. Set `pmset disksleep 0`.
- **Format:** `diskutil apfs addVolume <disk> "Case-sensitive APFS" Work`.
- **Mount watchdog:** run it before every VM lease.
- Keep ≥20% free internally.

---

## A. Recommended technology stack

| Layer | Recommended | Alternatives | Why |
|---|---|---|---|
| Interface | `tailscale serve` + FastAPI PWA + ntfy | Telegram bot, Hermes gateway | Tailnet-only, passkey approvals |
| Supervisor | launchd (LaunchDaemons) + watchdog + dead-man ping | pm2, supervisord | Native, boot-time, no login needed |
| Control plane | Python 3.12, FastAPI, SQLite WAL, lease queue | Temporal, DBOS, LangGraph | No cluster, no Postgres, ~2-3k LOC |
| Pipelines | Pydantic AI | LangGraph | Typed outputs and retries; weak constrained decoding on MLX means validate-and-retry |
| Workers | OpenCode headless in microVM | Pi, Claude Code, Codex | Provider-agnostic, local-first |
| Router | Rule ladder plus embedding kNN classifier, learned later | LLM router | Zero tokens spent on routing |
| Inference | oMLX (MLX) | mlx-lm, Ollama, llama.cpp | Batching and SSD prefix cache |
| Models | Ornith-1.5-35B-A3B; Qwen3.8-27B; Qwen3-Embedding/Reranker 0.6B | Qwen3.6-35B-A3B, Gemma 4 | See §1 |
| Tools | Shell, files, git broker, Playwright, MCP (vetted) | | |
| Memory | Markdown (git) + SQLite FTS5/sqlite-vec | pgvector, KG | No infra |
| Sandbox | Apple `container`, dedicated users, mitmproxy, pf | Lima, Seatbelt | Per-task VM |
| Observability | SQLite events + hash-chained audit + dashboard | Grafana, Langfuse | Add later |
| Remote | Tailscale, ntfy, WebAuthn | WireGuard, Cloudflare Tunnel | |

## B. Architecture diagram

```
 PHONE / LAPTOP --(Tailscale, SSH check mode, PWA, ntfy, passkey approvals)--+
                                                                              v
+------------------------------- Mac mini M6 (32GB) --------------------------------+
| user `roshan` (personal; agents have no access)                                    |
|                                                                                    |
| user `agent` (standard, non-admin)                                                 |
|  [Interface] tailscale serve -> FastAPI 127.0.0.1:8765                             |
|       |                                                                            |
|  [Supervisor] launchd KeepAlive | watchdog | panic switch | dead-man ping          |
|       |                                                                            |
|  [Control plane] scheduler | policy engine | approvals | router | audit client    |
|       |          SQLite WAL: tasks, leases, events, approvals, evidence, mem index |
|  [Worker pool] lanes: gpu_stream x3 | vm x2 | browser x1 | cloud x2                |
|       |                                                                            |
|  +----v--------- microVM per task (Apple container) -----------+                  |
|  | OpenCode / Pi / pipeline code on a fresh git clone, no secrets|                 |
|  +--+-------------------+--------------------+------------------+                 |
|     | model API (key)   | egress             | git                                 |
|     v                   v                    v                                     |
|  [Model router]     [mitmproxy+pf]       [git broker] (user `broker`)              |
|     |                allowlist, GET-only      pushes agent/* only                   |
|  oMLX :8000 (MLX/Metal, GPU wired cap 25GB)  [cloud gateway] redact+budget         |
|    worker | deep | embed | rerank                 |                                |
|                                                   v   optional cloud LLMs         |
|  [Memory] Markdown vault (git) + SQLite FTS5/vec    [auditd, root, append-only]    |
+------------------------------------------------------------------------------------+
 Internal SSD: OS, models, DBs, KV cache, images      External TB4 SSD: workspaces, caches, corpus, backups
```

## C. Hardware and resource plan

**32GB split [EST]**

| Component | GB |
|---|---|
| GPU-wired pool (hard cap 25 via sysctl): weights 19.5 (4.5 bpw) + KV/state 1.9 (2 × 48K) + scratch 1.2 + embed/rerank 1.3 | ≈ 23.9 |
| macOS headless + daemons | 3.0 |
| Control plane, proxy, dashboard | 0.7 |
| Harness processes (2) | 0.6 |
| 1 active microVM | 2.0 |
| **Total** | **≈ 30.2** |
| Browser VM adds | +1.0 |

This is tight, with ~1.5-2GB headroom. Buy margin with the quant ladder: 3.9 bpw frees ~2GB and allows 3 streams. Watchdog rule: if `memory_pressure` shows <15% free for 2 minutes, stop leasing VMs. If swap exceeds 2GB, restart inference on the smaller profile.

**Deep profile (swap in):** Qwen3.8-27B ≈ 15.5GB + vision + KV 6GB (2 × 48K) + scratch 1.5 ≈ 23-24GB. One VM only.

**Storage:** ≈ 300GB internal planned use, with ≥ 200GB free. External: workspaces ≤ 300GB, corpus ≤ 300GB, caches ≤ 150GB, backups ≤ 150GB. (This leaves ~100GB slack on 1TB.)

**CPU:** 12 cores. Reserve 2 for inference feeding, cap concurrent build/test jobs at 2 × 4 cores.

## D. Agent architecture (100+ logical agents without 100 LLMs)

An agent is a versioned YAML file. A run is a leased task. The only things that consume RAM are the lanes.

```yaml
name: py-refactorer
version: 3
extends: coder-base          # inherits tools, sandbox, policy
role: "Refactor Python modules without behavior change; add tests first."
model_tier: worker           # worker | deep | cloud-approved
tools: [read, edit, bash, grep, git-local]   # must be subset of parent's
sandbox: {profile: code-offline, cpus: 4, mem: 4g, wall: 90m}
egress: [pypi.org, files.pythonhosted.org]   # must be subset of parent's
budgets: {tokens: 600000, steps: 120}
verify: ["pytest -x", "ruff check", "mypy ."]
stop_when: [tests_green, no_progress(3), budget]
```

Dynamic creation: a planner submits `spawn(spec)`. The policy engine validates the schema, checks each field is ≤ the parent's, and rejects new credentials. Specs are ephemeral by default and promoted into `agents/` (git) after N successful runs and an eval pass.

```sql
CREATE TABLE tasks(
  id TEXT PRIMARY KEY, parent_id TEXT, project TEXT, kind TEXT, spec_json TEXT,
  state TEXT CHECK(state IN ('queued','leased','running','verifying',
                             'needs_approval','done','failed','cancelled')),
  priority INT DEFAULT 50, model_tier TEXT, resource_class TEXT,
  attempts INT DEFAULT 0, max_attempts INT DEFAULT 3,
  lease_owner TEXT, lease_expires_at INT,
  budget_tokens INT, spent_tokens INT DEFAULT 0, deadline_at INT, sensitivity TEXT,
  created_at INT, updated_at INT);
CREATE TABLE events(id INTEGER PRIMARY KEY, task_id TEXT, ts INT, kind TEXT,
  payload_json TEXT, prev_hash TEXT, hash TEXT);        -- hash-chained
CREATE TABLE approvals(id TEXT PRIMARY KEY, task_id TEXT, tier INT, action_json TEXT,
  state TEXT, requested_at INT, decided_at INT, decided_by TEXT);
-- lease (SQLite >= 3.35)
UPDATE tasks SET state='leased', lease_owner=:w, lease_expires_at=:exp, attempts=attempts+1
 WHERE id=(SELECT id FROM tasks WHERE state='queued' AND resource_class=:rc
           ORDER BY priority DESC, created_at LIMIT 1) RETURNING *;
```

Scheduler loop (pseudocode):
```
every 2s:
  reap expired leases -> queued (or failed if attempts>=max)
  if panic_flag: stop leasing
  for lane in lanes: while lane.has_capacity() and memory_ok():
      t = lease(next task whose model_tier == current_epoch_model or epoch can switch)
      dispatch(t)  # create clone -> start microVM -> run harness -> stream events
  epoch switch only if current model idle>=60s AND (>=10 min since last switch OR no queued work for it)
```

**Router ladder:** classify by embedding kNN (task kind, estimated context, repo size, prior failures, sensitivity label). Default `worker`. Escalate to `deep` after 2 failed verification cycles, for planning or review, or when more than ~60K context is needed. Escalate to `cloud` only after `deep` fails, only for labels `public` or `internal`, only under budget. Label `private` needs approval. Label `secret` never leaves.

## E. Model strategy

| Role | Model | Settings |
|---|---|---|
| Planning (routine) | Qwen3.8-27B | reasoning high |
| Planning (large/ambiguous) | Cloud: Opus 5.5 or GPT-6.1 Sol, approved | |
| Coding loop | Ornith-1.5-35B-A3B (fallback Qwen3.6-35B-A3B) | temp 0.6, top_p 0.95, top_k 20 (the Ornith card's general values) |
| Debugging | Worker with thinking, then Qwen3.8-27B after 2 failures, then cloud | feed failing test output and diff |
| Research extraction and triage | Worker (MoE) with schema | low reasoning |
| Claim verification | Qwen3.8-27B; optionally Gemma 4 for lineage diversity | |
| Summarization | Worker, low reasoning | |
| Classification / routing | Embedding kNN, or ≤4B sidecar with GBNF via llama.cpp | |
| Final synthesis | Qwen3.8-27B routine; cloud for publication-grade, verified snippets only | |
| Vision, OCR, GUI | Qwen3.8-27B | |
| Embeddings | Qwen3-Embedding-0.6B (+ reranker) | |

**Promotion gate:** 30-50 gold tasks from your own repos (pinned commit, failing test, known fix) plus 10 research tasks with known sources. Promote a model, quant or harness only if it matches or beats the incumbent on pass@1, steps and wall-clock.

**Cloud (optional, the system works without it)**
- DeepSeek V4.1 Flash lists at $0.15 per million input and $0.60 output off-peak, with cache hits at $0.003. Peak rates are double, on weekday windows (01:00-04:00 and 06:00-10:00 UTC). It is China-hosted: use it only for `public`-labelled bulk work.
- Claude Opus 5.5 is $4 input / $20 output per million tokens, with cache reads at $0.20. GPT-6 Sol is $2 / $10. Sol's price steps up past 272K context.
- Quality context: On Artificial Analysis v4.3.2 Opus 5.5 scores 58, the best open weight (MiMo-V2.6-Pro) 46, Qwen3.8-27B 34. So local is the right default for high-volume, well-specified work, and frontier is worth buying for the few hard planning and review tasks per week.
- Local always wins on privacy, cost per token and availability. Cloud wins on hard reasoning and long-context synthesis.

## F. 24/7 architecture

Covered in §8. The remaining pieces are below.

Inference daemon `/Library/LaunchDaemons/com.lab.inference.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.lab.inference</string>
  <key>UserName</key><string>agent</string>
  <key>ProgramArguments</key><array>
    <string>/Users/agent/lab/bin/run-inference.sh</string></array>   <!-- reads key from a 0600 file -->
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>StandardOutPath</key><string>/Users/agent/var/logs/inference.out</string>
  <key>StandardErrorPath</key><string>/Users/agent/var/logs/inference.err</string>
</dict></plist>
```
A second daemon `com.lab.wired` runs `/usr/sbin/sysctl iogpu.wired_limit_mb=25600` at load (I did not verify that `/etc/sysctl.conf` is honored on macOS 27). Watchdog (`StartInterval 60`): inference 1-token probe, control-plane heartbeat, mount check, disk %, `memory_pressure`, thermals, Tailscale status, dead-man ping.

## G. Remote-control architecture

Phone → Tailscale → (a) PWA via `tailscale serve` for status, queue, logs, submit task, approve or deny, panic; (b) SSH (check mode) for debugging. Push via ntfy carries only an ID and summary. Approvals require a passkey on the phone. Pre-boot unlock needs LAN or router VPN, not Tailscale.

## H. Security architecture

| Operation | Tier | Enforced by |
|---|---|---|
| Read, write and exec inside the task clone and artifacts dir | Autonomous | microVM |
| Tests, builds, lint; installs from allowlisted registries | Autonomous | proxy (GET-only), lockfile diff logged |
| Web research GET (research profile, no credentials) | Autonomous | research VM, separate from code VMs |
| Commit to `agent/<task>` in the clone; host fetches the branch | Autonomous | git broker |
| Local inference and embeddings | Autonomous | token budgets |
| Spawn child agents within the parent's budget and tool subset | Autonomous | policy engine |
| Write memory (tagged untrusted if web-derived) | Autonomous | curator |
| Merge to default branch; push anywhere except `agent/*`; PR to an external repo | **Approval** | broker + passkey |
| New dependency with install scripts or from a non-allowlisted source | **Approval** | policy engine |
| Edit CI, git hooks, Dockerfiles, `.env*`, policy files, launch configs | **Approval** | path policy |
| Egress to a non-allowlisted domain | **Approval** (one-time) | proxy |
| Cloud inference with `private` content | **Approval**; `internal` under budget autonomous | cloud gateway |
| Any write outside clone or artifacts (e.g. your real working copy) | **Approval** | broker |
| Budget overrun (tokens, time, dollars) | **Approval** | control plane |
| New AgentSpec exceeding its parent | **Approval** | policy engine |
| Outbound message (email, Slack) | **Approval** | broker |
| Use of any credential | **Approval** (scoped, per session) | broker |
| Access to `roshan` home, Keychain, browser profiles, iCloud, Messages, banking, password managers | **Forbidden** | user separation, TCC |
| `sudo`; disabling the sandbox, proxy or `pf`; editing LaunchDaemons, control-plane code or policies from inside a task | **Forbidden** | permissions, read-only mounts |
| `git push --force`, remote branch deletion, rewriting protected history | **Forbidden** | broker |
| Destructive disk operations or touching backups | **Forbidden** | permissions |
| GUI control of the host desktop | **Forbidden** | not enabled |
| Public skill or extension hubs installed without review | **Forbidden** | supply-chain rule |

**Kill switch (`agentctl panic`):**
1. Set the PANIC flag in SQLite.
2. Flip the egress proxy to deny-all.
3. Stop all microVMs.
4. `launchctl bootout` the control plane and inference.
5. Optionally revoke the phone's tailnet ACL tag.

A separate drain-stop `agentctl stop` lets running tasks finish.

**Audit:** hash-chained events written through a root-owned `auditd` over a Unix socket. The `agent` user can append but not edit. Log the full tool-call stream, approvals and policy decisions.

**Limits:**
- Per-task wall (default 90 min), per-tool timeout (10 min), token and step budgets, loop detector.
- Per-VM CPU and memory caps, log and output size caps, workspace disk watcher.
- Daily cloud dollar cap.
- Sampling at temperature ≤ 1.0 only.

**Prompt injection:** assume it works against you. Control what a hijacked agent can reach (process, egress, credentials), not what it is told. A sandboxed agent that legitimately holds secrets and has internet access can still leak them, so give agents neither.

## I. Exact installation plan

### Directory layout
```
/Users/agent/lab/{controlplane,agents,policies,prompts,eval,bin}   (git)
/Users/agent/memory/{global,projects/<name>}                       (git)
/Users/agent/models/   /Users/agent/var/{lab.db,logs}   /Users/agent/.omlx/cache
/Volumes/Work/{workspaces/<task>,caches/{uv,npm,cargo,hf},corpus/{papers,text},artifacts/<task>,backups}
```

### Phase 0: OS, hardware, benchmarks (day 1)
```bash
# admin user, wired Ethernet, FileVault ON (store recovery key offline)
sudo systemsetup -setremotelogin on        # Terminal needs Full Disk Access
sudo pmset -a sleep 0 disksleep 0 displaysleep 0 autorestart 1 womp 1
# disable auto-install of macOS updates in System Settings
sudo sysadminctl -addUser agent -fullName "Agent" -password -    # standard user (not admin)
sudo sysadminctl -addUser broker -fullName "Broker" -password -
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git uv node sqlite jq tailscale mitmproxy
sudo brew services start tailscale && sudo tailscale up --ssh --hostname=lab-mini
sudo sysctl iogpu.wired_limit_mb=25600; sysctl iogpu.wired_limit_mb   # then persist via LaunchDaemon
```
Test: reboot and SSH in with no GUI login, then confirm the pre-boot SSH unlock works. Run the benchmark (below). Failure modes: unlock fails on Wi-Fi (use Ethernet), `sysctl` key absent or changed on macOS 27. Rollback: `pmset -a` defaults, delete users.

Benchmark script (run against any OpenAI-compatible endpoint; randomize prompts to defeat caching):
```python
import asyncio, time, httpx, json, sys, uuid
KEY, MODEL = sys.argv[1], sys.argv[2]
URL = "http://127.0.0.1:8000/v1/chat/completions"
async def one(c, words):
    body = {"model": MODEL, "stream": True, "max_tokens": 256,
            "stream_options": {"include_usage": True},
            "messages": [{"role": "user", "content": f"{uuid.uuid4()} " + "lorem ipsum " * words + "\nSummarize."}]}
    t0, tf, usage = time.perf_counter(), None, None
    async with c.stream("POST", URL, json=body, headers={"Authorization": f"Bearer {KEY}"}, timeout=900) as r:
        async for line in r.aiter_lines():
            if not line.startswith("data: ") or line.endswith("[DONE]"): continue
            d = json.loads(line[6:]); usage = d.get("usage") or usage
            if d["choices"]:
                dl = d["choices"][0]["delta"]
                if tf is None and (dl.get("content") or dl.get("reasoning_content")): tf = time.perf_counter()
    t1 = time.perf_counter()
    return usage["prompt_tokens"]/(tf-t0), usage["completion_tokens"]/(t1-tf)
async def main():
    async with httpx.AsyncClient() as c:
        for words, n in [(2000,1),(8000,1),(2000,2),(2000,4)]:
            r = await asyncio.gather(*[one(c, words) for _ in range(n)])
            print(words, n, "PP/s", [round(x[0]) for x in r], "TG/s", [round(x[1],1) for x in r])
asyncio.run(main())
```

### Phase 1: minimal working system (days 2-3)
```bash
# as agent
brew tap jundot/omlx https://github.com/jundot/omlx && brew install omlx   # install form inferred from README; verify
uv tool install "huggingface_hub[cli]"
hf download <vendor-or-mlx-community 4-bit Ornith-1.5-35B-A3B repo> --revision <PINNED_SHA> --local-dir ~/models/ornith-1.5-35b-a3b
hf download <mlx-community Qwen3.8-27B 4-bit repo> --revision <PINNED_SHA> --local-dir ~/models/qwen3.8-27b
omlx serve --model-dir ~/models --paged-ssd-cache-dir ~/.omlx/cache --hot-cache-max-size 10% --api-key "$(cat ~/.secrets/omlx.key)"
curl -s localhost:8000/v1/models -H "Authorization: Bearer $(cat ~/.secrets/omlx.key)"
```
Use the vendor's MLX build if it exists; else mlx-community. A community quant such as `LookUpMark/Ornith-1.5-35B-A3B-oQ4e-mtp` is acceptable only pinned, safetensors-only, no `trust_remote_code`. Converting bf16 yourself needs ~70GB, so don't on 32GB. Check the listening address with `lsof -iTCP -sTCP:LISTEN`. Fallback: `ollama pull qwen3.8:27b-mlx`. Test with the benchmark. Failure modes: wired-memory panic, Metal OOM on large context, MTP not recognized. Rollback: revert the model alias.

### Phase 2: autonomous coding
```bash
curl -fsSL https://opencode.ai/install | bash
```
Config `opencode.json` (OpenAI-compatible provider pointing at the host gateway, as in the Pinggy example):
```json
{"$schema":"https://opencode.ai/config.json","provider":{"local":{"npm":"@ai-sdk/openai-compatible","name":"oMLX",
 "options":{"baseURL":"http://<host-gateway>:8000/v1","apiKey":"{env:OMLX_KEY}"},
 "models":{"ornith-1.5-35b-a3b":{"name":"Ornith 1.5 35B-A3B"}}}}}
```
Apple container (download the signed `.pkg` from github.com/apple/container releases):
```bash
sudo installer -pkg container-installer-signed.pkg -target / && container system start
container run --rm -it --cpus 4 --memory 4g -v /Volumes/Work/workspaces/T1:/work -w /work <your-base-image> bash   # verify flags with --help
```
Build the gold-task eval and the sandbox egress layer:
```python
# allowlist.py  (mitmdump -s allowlist.py --listen-host <bridge-ip> --listen-port 3128)
from mitmproxy import http
ALLOW = {"pypi.org","files.pythonhosted.org","registry.npmjs.org","crates.io","static.crates.io","index.crates.io"}
def request(flow: http.HTTPFlow):
    h = flow.request.pretty_host
    if flow.request.method not in ("GET","HEAD") or not any(h == d or h.endswith("."+d) for d in ALLOW):
        flow.response = http.Response.make(403, b"blocked by lab egress policy")
```
```
# pf anchor sketch (verify bridge name and subnet with ifconfig): pass first, then block
pass quick on bridge100 proto tcp from 192.168.64.0/24 to 192.168.64.1 port {3128, 8000, 8765}
block drop quick on bridge100 from 192.168.64.0/24 to any
```
Test: from inside a VM, `curl https://example.com` must fail while `pip install` through the proxy works. Failure modes: tools that pin certificates, DNS leaks, container networking quirks. Rollback: `container system stop`, remove the pf anchor.

### Phase 3: research agents
Run SearXNG in its own microVM exposed host-only. Build the ledger pipeline: tables `sources`, `evidence`, `claims`, `edges`. Add a citation resolver (RefChecker-style) and the linter. Test: 20 known-answer research tasks plus 10 planted fake citations that must all be caught. Failure modes: rate limits from scholarly APIs (use the polite pool with an email, cache aggressively), PDF parsing errors. Rollback: disable the writer, keep the ledger.

### Phase 4: persistent memory
`uv add sqlite-vec`. Serve embeddings and reranking from oMLX. Build the curator job. Test: recall@10 on 50 queries over your own notes. Failure modes: poisoned memories, stale facts (use `supersedes`). Rollback: rebuild the index from Markdown (`git revert` the vault).

### Phase 5: multi-agent orchestration
Implement the control plane per §D: scheduler, lanes, policy engine, spawn API, router. Test: 20 queued tasks, kill the inference server and the control plane mid-run, and confirm all tasks complete with no duplicates. Failure modes: lease races, runaway spawn. Rollback: `agentctl stop`, restore the SQLite snapshot (`sqlite3 lab.db ".backup"` taken nightly).

### Phase 6: 24/7 operation
Install the LaunchDaemons (`sudo launchctl bootstrap system /Library/LaunchDaemons/<plist>`; `launchctl print system/<label>`), the watchdog, UPS with graceful-shutdown signaling, and the dead-man ping. Test: pull the plug, `kill -9` each daemon, unplug the external SSD. Rollback: `launchctl bootout`.

### Phase 7: remote access
```bash
tailscale serve --bg 8765     # syntax varies by version; check `tailscale serve --help`
```
Set tailnet ACLs (phone and laptop tags only, SSH `check` action). Install ntfy and the passkey approval flow. Test: approve and deny from a phone on cellular, press the panic button, confirm it halts everything within 10 seconds. Failure modes: ACL lockout (keep a local console path), notification delivery delay. Rollback: remove the `serve` config.

### Phase 8: optimization
MTP/speculative decoding, KV quantization, SSD cache tuning, learned router from the event log, a Gemma 4 verifier, a disposable macOS VM for GUI tasks, and chunked-prefill scheduling if oMLX supports it. Each change is gated by the eval.

## J. What NOT to install

| Technology | Why not |
|---|---|
| OpenClaw as core | Security record, heartbeat cost, broad default access |
| Hermes as core | Self-writing skills and local-by-default execution conflict with the isolation model |
| Temporal, Kubernetes, Postgres, Qdrant, Neo4j | Infrastructure beyond what one machine needs |
| LangGraph as the backbone | A durable-execution comparison argues none of the agent frameworks is itself a durable execution engine. |
| Docker Desktop | Heavier than per-task microVMs |
| LM Studio as a daemon | GUI-centric; MTP gap above |
| vLLM Apple ports, MLC, BaseRT | Young or research-grade for this use |
| 70B+ dense or 100B+ MoE models | Don't fit the 25GB GPU cap |
| Unpinned community quants, `trust_remote_code` | Supply-chain risk |
| Public skill and extension hubs (Pi packages, Hermes skills) without review | Persistence vector |
| Host-desktop computer-use, agents on your personal browser profile | Violates credential isolation |
| Harness "auto" approval modes as a security boundary | Best-effort classifiers only |
| FileVault OFF with personal data on the box | Only if the box holds nothing sensitive |

## K. Future upgrade path

| Hardware | Change |
|---|---|
| **64GB M5 Pro mini** (up to 64GB and 307GB/s, ~1.8x the bandwidth) | Keep both models resident: 35B-A3B at ~4.5 bpw (20GB) + 27B at ~6 bpw (23GB) + KV. Dense tier ceiling roughly 18 tok/s. No more epoch swapping. |
| **96-128GB** (Studio / MacBook Max) | Qwen3.8-Flash-Next at 4-bit (96-114GB, AA index 40). Mind its license for any AI-coding product. Internal use is exempt per the same source. |
| **256GB+** | GLM-5.3-Flash at 4-bit (162-210GB, MIT, AA index 42) |
| **Dedicated GPU box** | Run Qwen3.8-27B FP8 (≈ 28-31GB) on a 32GB card with vLLM. Point the router at the new endpoint. |
| **Multiple Macs** | Apple promotes Thunderbolt 5 clustering of M5 Pro minis; I did not verify performance |

The control plane, memory, sandbox and policy layers don't change. Only the inference endpoints and tier definitions do.

---

## Sources

**Primary**
- Apple Platform Deployment, FileVault SSH unlock: https://support.apple.com/guide/deployment/dep82064ec40
- MLX docs, `set_wired_limit`: https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.set_wired_limit.html
- mlx-lm issue #883 (wired memory panic): https://github.com/ml-explore/mlx-lm/issues/883
- Claude Code docs, worktrees: https://code.claude.com/docs/en/worktrees
- Claude Code release notes: https://github.com/anthropics/claude-code/releases/tag/v2.1.260
- Ornith-1.5-35B-A3B model card: https://huggingface.co/ornith-ai/Ornith-1.5-35B
- Qwen3.8 repo: https://github.com/QwenLM/Qwen3.8 and Qwen3.8-27B-FP8 card: https://huggingface.co/qwen/qwen3.8-27b-fp8
- oMLX: https://github.com/jundot/omlx
- Hermes Agent: https://github.com/NousResearch/hermes-agent
- RefChecker: https://github.com/markrussinovich/refchecker
- arXiv 2604.03173 (reference hallucination): https://arxiv.org/html/2604.03173v1
- arXiv 2607.00738 (Phantom References): https://arxiv.org/html/2607.00738v1
- arXiv 2607.19438 (BaseRT): https://arxiv.org/pdf/2607.19438
- DeepSeek API pricing (read via aggregators, not fetched directly): https://api-docs.deepseek.com/quick_start/pricing
- Anthropic pricing (read via aggregators, not fetched directly): https://platform.claude.com/docs/en/about-claude/pricing

**Secondary**
- Mac mini M6 launch coverage: https://t2online.in/tech/tech-news/apple-mac-mini-launches-with-m6--m5-pro/2007528 ; https://www.igeeksblog.com/mac-mini-m6-m5-pro-price-specs-release-date/ ; https://www.mactech.com/2026/08/25/apple-unveils-a-new-mac-mini-with-m6-and-m5-pro-chips/ ; https://fstoppers.com/gear/apples-new-mac-mini-gets-m6-m5-pro-and-genlock-video-work-904276
- M6 9B local test: https://www.mindstudio.ai/blog/m6-mac-mini-local-ai-performance
- Bandwidth analysis: https://levelup.gitconnected.com/apple-says-the-mac-mini-m6-is-4-8x-faster-at-ai-the-number-that-actually-matters-went-up-42-6aa2a8be9b50
- Pinggy, open-weight coding models (AA index figures): https://pinggy.io/blog/best_open_source_self_hosted_llms_for_coding/
- Qwen3.8-27B coverage: https://venturebeat.com/technology/qwen3-8-27b-runs-frontier-class-coding-agents-and-reasoning-locally-no-cloud-api-required ; https://www.nxcode.io/resources/news/qwen3-8-27b-local-agent-model-2026
- Ornith 1.5 coverage: https://www.mindstudio.ai/blog/ornith-1-5-35b-a3b-benchmarks ; https://ai-tldr.dev/models/ornith-1-5-35b-a3b/
- Ollama MLX: https://lilting.ch/en/articles/ollama-mlx-apple-silicon-preview ; Qwen3.8 MLX tag notes: https://www.orcarouter.ai/blog/qwen-3-8-27b-mlx
- Reddit snapshot (M5 32GB tok/s): https://reddit.sentinel-team.org/posts/1w4n0ri/snapshots/2026-09-04T21%3A20%3A12.3645Z
- oMLX community benchmark: https://omlx.ai/benchmarks/7habyabx
- Harness comparisons: https://pinggy.io/blog/best_open_source_cli_coding_agents/ ; https://winder.ai/ai-agent-harness-comparison/ ; Pi: https://www.implicator.ai/pi-is-not-a-claude-code-rival-it-is-a-harness-rebellion/ ; OpenClaw/Hermes: https://www.websiterating.com/tools/hermes-agent-vs-openclaw-comparison/
- Claude Code with local models: https://www.kdnuggets.com/pairing-claude-code-with-local-models ; https://dev.classmethod.jp/en/articles/claude-code-ollama-local/
- Sandboxing: https://pypi.org/project/agentcage/0.22.11/ ; https://github.com/fishman/awesome-agent-sandbox ; https://www.sophos.com/blog/inside-the-lethal-trifecta-blast-radius-reduction-in-ai-agent-deployments ; https://stevekinney.com/courses/ai-development-setup/blast-radius/llms.txt
- FileVault remote unlock: https://www.jeffgeerling.com/blog/2025/you-can-finally-manage-macs-filevault-remotely-tahoe/
- Wired limit guides: https://bestllmfor.com/guide/qwen3-32b-local-mac-m1-m2/ ; https://localaimaster.com/blog/mac-memory-pressure-local-llm
- Durable execution: https://hackernoon.com/you-dont-need-temporal-yet-durable-execution-for-ai-agents-in-150-lines ; https://www.beri.net/article/langchain-alternatives-durable-execution-migration-2026
- Memory design reference: https://github.com/jagoff/memo
- Pricing aggregators: https://www.orcarouter.ai/blog/deepseek-v4-1-flash-pricing ; https://www.eesel.ai/blog/claude-opus-5-5-pricing ; https://www.mindstudio.ai/blog/gpt-6-soul-opus-5-5-pricing

**Not verified this session:** Apple `container` running as a non-GUI user, M6 behavior of oMLX and MLX, the `iogpu.wired_limit_mb` key on macOS 27, Tailscale and ntfy install specifics, Docling versus PyMuPDF, any independent evaluation of Ornith 1.5, and the current state of GPT-Researcher, STORM and PaperQA.

## Reasoning trace (not shown to raters)

Claude responded: Starting with whether the hardware exists as specified, then the rest of the ecosystem.
Sorting out a date mismatch before starting the research.
Sorting out a date mismatch before starting the research.

Starting with whether the hardware exists as specified, then the rest of the ecosystem.

Searched the web, read a page

Searched the web, read a page






12 minutes ago

## Run notes

claude.ai incognito chat (no history or memory), model menu Sonnet 5.5, Effort High; the menu showed
"Sonnet 5.5 High". Connectors were switched off in the composer menu; the composer has no web-search
switch, and Claude searched the web by itself. Send time 2026-10-14T07:13:30.451Z (browser clock, read right after
sending). Chat: https://claude.ai/chat/b008a1b4-adbc-4cf1-a001-2a9c37c6a6aa?incognito (incognito chats are not kept in history).
Operated by the assistant (Claude, via the Claude in Chrome extension) in the author's signed-in browser,
at the author's request; the runs were opened in separate tabs and sent in manifest order without waiting
for earlier answers. The app turns long pastes into an attachment, so the prompt was inserted as plain
text in eight line-aligned pieces from one clipboard paste and checked against the original (1,782 words,
same text) before sending. Answer copied with the app's Copy button (it includes any short lines the model
wrote before its searches) and written verbatim from the clipboard; the reasoning trace is the visible
process panel (step summaries and search queries) copied from the page text.
Replacement for this run: attempt 1 was stopped by the author's claude.ai usage limit and is in
superseded/. Sent after the limit reset, with at most three chats generating at once.
