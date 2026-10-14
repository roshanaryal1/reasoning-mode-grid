---
run_id: claude__reasoning__p1-v1__r2
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
replicate: 2
date_stamped: '2026-10-14T07:12:05+00:00'
date_run: '2026-10-14T07:12:05+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

I'll start by verifying the current state of the hardware and ecosystem before designing anything.

**Claude Sonnet 5.5 (Anthropic) | knowledge cutoff: end of June 2026 | web search: ON** (about 25 searches, no page fetches). Most findings below come from search snippets, not full-page reads.

**Date note:** your prompt says 31 Aug 2026, but the system clock says 14 Oct 2026. I used Oct 14. The M6 Mac mini only shipped Sept 22, so Aug 31 would predate your hardware.

**Evidence quality:** I could not retrieve Apple's newsroom or most primary model cards, so hardware specs come from retailers and press. Many benchmark pages are SEO-grade secondary sources, and the best M6 benchmark I found is secondary and covers one model. I mark everything as primary (P) or secondary (S) in Sources, and label my own estimates "est." I could not verify MLX or oMLX behavior on M6 silicon, so Phase 1 starts with a day-1 benchmark. Overall confidence in the stack is about 75%.

---

## Decisions at a glance

| Layer | Pick | Confidence |
|---|---|---|
| Inference server | oMLX (MLX, continuous batching, SSD KV cache); llama.cpp `llama-server` as fallback and A/B | 65% |
| Tier-0 model (resident) | Qwen3.6-35B-A3B, 4-bit | 75% |
| Tier-1 model (swap-in) | Qwen3.8-27B, 4-bit | 70% |
| Coding harness | OpenCode, run inside the sandbox, driven headless | 60% (bake-off decides) |
| Research | Custom evidence-ledger pipeline, not a free-form agent | 85% |
| Orchestrator | Custom thin layer: SQLite lease queue, Python, launchd | 85% |
| Memory | Markdown in git plus SQLite (FTS5), `sqlite-vec` later | 90% |
| Sandbox | Apple `container` Linux VM plus Seatbelt, dedicated macOS user | 75% |
| Remote | Tailscale (tailnet only), SSH+tmux, self-hosted ntfy, dashboard via `tailscale serve` | 85% |
| Cloud | Optional escalation behind a privacy gate; never required | n/a |

---

## 1. Local inference

**Hardware facts.** The M6 Mac mini ships with a 12-core CPU and a 12-core GPU with a Neural Accelerator in every GPU core, from September 22. Memory goes up to 32 GB at up to 170 GB/s. It has three Thunderbolt 4 ports, so no Thunderbolt 5. One source says the 170 GB/s figure applies only to the 24 GB and 32 GB builds. Your 32 GB/512 GB SKU is listed at a retailer.

**The physics governs everything.** Decode is memory-bandwidth-bound. At 170 GB/s, a 27B dense model at 4-bit has a theoretical ceiling of about 10 tok/s. The only M6 measurement I found (secondary, 9B Q4 via llama.cpp) shows prompt processing about 3.5x faster than M4 (742 vs 210 tok/s) but generation only 18 to 26.9 tok/s. The compute upgrade helps prefill far more than decode.

| Model class | Bytes read/token (est.) | Decode ceiling | Realistic decode (est.) |
|---|---|---|---|
| 27B dense, 4-bit (~16.5 GB) | 16.5 GB | ~10 tok/s | 8-9 (one index-based estimate: 8) [S] |
| 35B-A3B MoE, 4-bit (~20 GB resident) | ~1.8 GB active | ~90 tok/s | 30-40 |
| 9B dense, 4-bit | ~5.5 GB | ~31 tok/s | ~27 (measured, S) |

The MoE estimate comes from scaling a community benchmark. On an M2 Max 32GB, Qwen3.6-35B-A3B 4-bit ran at 86.9 tok/s decode in MLX versus 58.6 in llama.cpp. The M2 Max has about 400 GB/s, so scaling by 170/400 gives roughly 37 and 25 tok/s on M6. That is my projection, not a measurement.

**The same dataset shows a prefill reversal.** llama.cpp prefill was 685 tok/s versus MLX's 296 on that MoE. Agent loops are prefill-heavy, so MLX's decode advantage may not translate into useful work per hour. M6's Neural Accelerators may reshape this, but I have no data. This is the main reason for the day-1 benchmark below.

**Engine comparison**

| Engine | Verdict for this box |
|---|---|
| oMLX | Pick. Persists KV cache blocks to SSD so agent-invalidated prefixes restore without recompute, with continuous batching via mlx-lm. Serves LLM, embeddings and rerankers in one process with LRU eviction. Risks: about 2 months old, single maintainer, documented for M1-M4 only. |
| mlx-lm server | Apple's own, most conservative MLX option. No SSD KV tier. |
| llama.cpp `llama-server` | Most mature. Best prefill in the data above. MTP is supported. Use as fallback and A/B. |
| Ollama | Skip. Its MLX backend reportedly needs more than 32 GB [S], and it adds no value over the above. |
| LM Studio | Good for exploration, wrong for a headless service. |
| vllm-mlx | Adds continuous batching and KV reuse on MLX, but is research-grade. Revisit later. |

A peer-reviewed comparison found MLX gives the highest sustained throughput, llama.cpp suits lightweight single-stream use, and Ollama lags. That study ran on an M2 Ultra, so it is directional only.

**Models.** All are open-weight and Apache 2.0 unless noted.

- **Qwen3.6-35B-A3B:** released 2026-04-16, 35B total, about 3B active. Vendor-reported SWE-bench Verified is 73.4% versus 77.2% for Qwen3.6-27B. OpenHands' docs recommend it as the first local model to try.
- **Qwen3.8-27B:** published August 14, 2026 under Apache 2.0, native vision-language, and reported at 61.7% on SWE-bench Pro (vendor-reported). I found no Qwen3.8 small MoE.
- **Gemma 4 31B:** Qwen's own table puts it at 52.0% SWE-bench Verified. Use it for multimodal, not as the coding workhorse.
- **Bigger open models:** DeepSeek-V4.1, GLM-5.x and Kimi K2.x are server-scale. They do not fit 32 GB in any useful way.

**Decision:** a 4-point benchmark gap against a 3-4x decode advantage is not close. For useful work per hour, the MoE is the default. The 27B dense model is a swapped-in "deliberate" tier for planning, hard debugging and review.

**MTP (multi-token prediction).** Qwen3.5/3.6 checkpoints ship an MTP head, and mlx-lm has a reference implementation for native MTP speculative decoding. Results on other hardware: about 1.9x for the 27B dense on an RTX 3090 in llama.cpp, but marginal for MoE on M4 Pro. Enable it for the 27B tier only after verifying that Qwen3.8 ships an MTP head. I did not confirm that.

**Quantization and context.** Use 4-bit MLX (group size 64, or oMLX's mixed-precision quant) for both models. Do not go below 4-bit for coding without your own eval showing no loss. Cap context at 128K, run typically at 32-64K, and spill to the SSD KV tier beyond that. Qwen3.5/3.6 use hybrid linear attention, so KV grows slowly. From my recollection of the config (verify `config.json`), full-attention KV is about 20 KB/token at fp16, or roughly 2.6 GB at 128K.

**Day-1 acceptance benchmark (mandatory).** Run the same recorded OpenCode trace of about 20 turns and 40K tokens through oMLX and llama.cpp. Compare prefill tok/s, decode tok/s at 1/2/3 concurrent sequences, time-to-first-token with a warm cache, and peak memory pressure. Run `infer-check` (found in my search) to confirm the MLX server matches reference outputs at temperature 0. If llama.cpp wins on end-to-end task time, switch the primary. Both speak the OpenAI API, so the swap costs minutes.

---

## 2. Agent runtimes and harnesses

| Harness | Local-model fit | Unattended use | Subagents | Sandbox | Verdict |
|---|---|---|---|---|---|
| OpenCode (MIT, ~160K stars, v1.15) | Provider-agnostic including local models; agents defined as markdown files, background subagents | CLI/server mode | Yes | None built in | **Pick** |
| Codex CLI (Apache-2.0, Rust) | `--oss` path, but tuned for OpenAI models, local is the B-path | Strong | Limited | Built-in | Alternative |
| Claude Code (closed) | Weak local support [S]; large system prompt [S] | Strong (`-p` headless) | Best-in-class [S] | Seatbelt `srt` | Cloud escalation only |
| OpenHands SDK | Documented local path; one harness-fluency study reported malformed tool calls | Strong, built for it | Micro-agents plus explicit verification | Docker | Bake-off candidate |
| Pi | Minimal prompt, good for small context | Scriptable | Via your orchestrator | None | Bake-off candidate |
| Goose | Linux Foundation project | Moderate | Yes | None | Skip |
| Aider | Good local fit, git-native | Not an agent loop | No | None | Skip |
| Hermes Agent (MIT) | Local-first; SQLite memory and a self-improvement loop | Server-style | Some | Docker | Watch |
| OpenClaw | Local capable | Messaging-gateway design | Yes | Weak | **Do not use** |

On OpenClaw: its own community setup guide warns it runs with high privileges over shell, filesystem and credentials. A widely shared incident had an inbox-managing agent deleting messages unexpectedly. Its public skill marketplace is a supply-chain risk.

Two findings drive the decision.

1. **Harness choice changes outcomes materially.** A 2026 workshop paper evaluated three open-source harnesses (Goose, OpenCode, OpenHands-SDK) on the same models and treats harness as a hidden variable. Another found harness-specific fine-tuning moved one local model between about 23% and 35% on Terminal-Bench 2.0. Public leaderboards will not tell you which harness is best with a 35B-A3B on your tasks.
2. **Prefill is expensive locally.** Claude Code's system prompt is over 10,000 tokens. At a few hundred prefill tok/s, that is tens of seconds cold, so you want a small-prompt harness plus a stable prefix and SSD KV caching.

**Decision.** Do not write an agent loop; use one existing harness plus a custom orchestrator, with tasks in SQLite and OpenCode as the stateless worker. Research uses its own deterministic pipeline (Section 5), because citation integrity needs state-machine control, not a freeform loop. Before committing, run a 2-day bake-off of OpenCode vs Pi vs OpenHands SDK on 20 tasks from your own repos, and keep the winner.

---

## 3. Multi-agent architecture

Definitions that matter:

- **100 simultaneous model instances:** impossible. Weights are about 19 GB, and memory bandwidth is shared. Two instances would each run at half speed with no extra weights benefit.
- **100 logical agents:** rows in an `agents` table (role prompt, tool allowlist, model tier, permissions, budgets, version). They cost nothing until a task instantiates one.
- **Worker pool:** harness processes, each about 250 MB (est.), each pinned to one git worktree. Cap at 5 to 6.
- **Inference slots:** concurrent sequences inside one MLX process, capped at 3, or 2 when any context exceeds 64K.
- **Why more workers than slots:** an agent loop is idle on the GPU while tests, builds or fetches run, often 40-70% of wall time (my estimate). Five workers sharing three slots keep the GPU busy.
- **Batching returns are lower for MoE than dense.** Each token routes to 8 of 256 experts, so at batch 3 you read more distinct experts per step. I expect 1.3-2x aggregate throughput at 3 streams, versus the 2-3.4x scaling the starmorph blog reports for vllm-mlx (model not specified). The dense 27B batches better. Measure it.
- **Swarms and hierarchies:** keep depth at 2: a coordinator decomposes, workers execute, a verifier checks. Deeper trees multiply prefill cost with no throughput gain on one GPU.
- **Dynamic agent creation:** the planner emits an `AgentSpec` JSON. A validator enforces capability attenuation: a child's tools and permissions must be a subset of its parent's, and its budgets must be at most the parent's remainder. Specs start ephemeral. They are promoted to the registry only after passing the eval set.

**Throughput levers, in order of value:** (1) stable prompt prefixes with SSD KV reuse (tool definitions first, no timestamps, no reordering); (2) a small tool set per agent, ideally 15 or fewer, since each tool schema costs prefill and local models degrade with many tools; (3) context compaction at about 60% of the window; (4) non-thinking mode for classification and summarization; (5) phase scheduling to minimize model swaps (Section 1).

---

## 4. Coding agents

OpenCode runs inside the sandbox VM, driven by the orchestrator. Each task gets a git worktree on branch `agent/<task-id>`. The run loop:

```
plan (tier-1, thinking) → implement (tier-0) → run tests/lint in VM
→ on failure: 2 retries tier-0 → escalate: tier-1 debug with failure summary
→ completion gate (all must pass):
    - tests green, lint/typecheck clean
    - diff-size and touched-path policy
    - independent review pass by the *other* model tier
→ else mark needs-human with a written handoff
```

Stopping conditions per task (all configurable): max wall time 90 min, max 200 tool calls, max 3 consecutive identical errors, a no-diff-progress watchdog at 10 min, and a token budget. Each run writes a structured log and a Markdown report.

**Repo-agnostic access (your requirement 4).** `agentctl add-project <path>` makes a read-only bare mirror under the agent's area. Non-git directories are cloned with APFS `cp -c` into a scratch workspace. Results come back as branches or patch files for your review. The agent never writes in place in your real directories. This is the one place I trade your requirement 4 against security, deliberately.

For local models, your own eval beats public numbers. Hold out 30 to 50 tasks (repo at commit, failing test) and re-run them nightly against any change to model, quant, harness version or prompt.

---

## 5. Research agents

Hallucination evidence is bad enough to design around. One study of commercial LLMs and deep-research agents found even search-enabled systems fabricated 3 to 13% of citation URLs, and cited work with rates from 14% to 95% across domains for non-retrieval models. A real-world verification benchmark found detection falls well below benchmark accuracy on real data.

**Architecture: citations are pointers, not text.**

1. **Plan:** the MoE decomposes the question into sub-questions and queries.
2. **Discover:** OpenAlex, Semantic Scholar, arXiv and Crossref APIs, plus self-hosted SearXNG for the open web. OpenAlex now needs a key: a free key gives $1 of API usage per day, and heavier calls are metered. Bulk snapshot data is free.
3. **Acquire:** Unpaywall for open-access PDFs; store the raw file with a SHA-256.
4. **Parse:** PyMuPDF first, Docling when tables matter (run it off-peak; this is from my knowledge, not verified today).
5. **Ledger (SQLite):** `sources`, `passages(source_id, offset, text, hash)`, `claims`, `claim_evidence(claim_id, passage_id, quote_span, stance)`.
6. **Write:** the writer may cite only IDs in the ledger. It outputs `[claim → passage_id]`, never free-text references.
7. **Deterministic validation (no LLM):** the quote must string-match the stored passage, and the DOI must resolve. Title, authors, year and venue must all come from the same resolved record, which blocks "mashup" citations built from parts of different papers.
8. **Entailment check by a different model:** the verifier is the 27B, the writer is the MoE. A cited line of work found that same-source verification lets plausible fabrications pass, which is the reason for splitting them.
9. **Contradiction pass:** pairwise claim comparison among claims about the same entity or metric. Contradictions are reported in the output, not resolved silently.
10. **Report:** every sentence is tagged supported, partially supported, or unverified, with the evidence links.

For reference designs and benchmarks, see PaperQA2 and OpenScholar, plus CiteAudit's staged extract, memory lookup, search, scholar lookup and judge pipeline and the open citation-faithfulness kit. I would borrow ideas rather than adopt a framework, because the ledger schema is the core asset.

---

## 6. Persistent memory

| Tier | Tech | Contents | When |
|---|---|---|---|
| Semantic, human-readable | Markdown in a git repo (`memory/`) | Project notes, ADRs, decisions, glossary | Day 1 |
| Episodic | SQLite (WAL) plus FTS5 | Runs, tool calls, outcomes, research ledger | Day 1 |
| Embeddings | `sqlite-vec` plus a ~0.6B embedder served by oMLX | Semantic recall over notes and passages | Only when FTS recall misses, Phase 4 |
| Knowledge graph | Skip | | Likely never |
| Vector DB server | Skip | | Only multi-node |

Write discipline matters more than the store. Agents propose memories; a curator step deduplicates, requires a source link, and sets a TTL. Agents never edit global memory directly, which limits memory poisoning from injected content. Project memory lives in the project's notes; global memory holds preferences and cross-project lessons only.

---

## 7. Computer control

Isolation layers, outermost first:

1. **Separate macOS user** `agent` (standard, non-admin), with no access to your home directory.
2. **Linux VM** via Apple's Containerization framework (`container` CLI). Each container runs in its own lightweight VM. It needs macOS 26+, which the M6 mini's macOS 27 satisfies. A VM boundary is stronger than Seatbelt: the author of `vibe` argues virtualization is more secure against escapes than containers or the macOS sandbox framework.
3. **Per-task workspace** mounted as a disposable copy with diff-only output.
4. **Network:** the VM can only reach a host-side egress proxy (domain allowlist, logging). Enforce with a `pf` anchor on the host. I have not verified exact `pf` plus `container` networking on macOS 27, so test it. Look at `drydock`'s deny-by-default allowlist and diff-only output as a pattern, but note it is a small project.
5. **Secrets broker on the host:** the VM never holds tokens. The proxy injects scoped credentials for specific destinations.
6. **Seatbelt** (Anthropic's `sandbox-runtime` is the reference) for any host-side tool.
7. **Browser:** headless Chromium via Playwright inside the VM, clean profile, no logged-in sessions.
8. **GUI computer-use:** skip in v1. Screenshot loops through a local VLM are slow, and a GUI agent on a logged-in desktop breaks the isolation model.

**Principle:** an agent run should combine at most two of: untrusted input (web, PDFs, repo content), access to sensitive data, and ability to act externally. Research runs have untrusted input and no sensitive data. Coding runs touch repo content but cannot push. Anything combining all three goes through a human.

---

## 8. Always-on operation

- **Power:** `sudo pmset -a sleep 0 disksleep 0 womp 1 autorestart 1` keeps the machine awake, wakes on network access, and restarts after power loss.
- **Boot without a human:** with FileVault on, the Mac stalls at the pre-boot unlock after a power cut and no service starts. My decision: FileVault off, auto-login as `agent`, because this box holds no personal secrets by design. If you disagree, keep FileVault on and accept that unplanned reboots need you. I could not confirm whether macOS 27 supports remote FileVault unlock.
- **Services:** LaunchAgents in the `agent` session with `KeepAlive` and `ThrottleInterval`. Fall back to LaunchDaemons with `UserName` if GUI-session dependence causes trouble. I did not verify Metal access from daemons.
- **GPU limit at boot:** a root LaunchDaemon runs `sysctl iogpu.wired_limit_mb=24064`. macOS lets the GPU use about two-thirds of RAM by default on 32 GB Macs, and one source says the limit resets at reboot, so persist it. Check the default first with `sysctl iogpu.wired_limit_mb` (0 means default).
- **Task persistence:** every task state transition commits to SQLite. A worker that stops heartbeating has its lease expire, and the task requeues with the previous run's handoff notes.
- **Watchdog:** a separate tiny process monitors the orchestrator and inference endpoints, checks memory pressure and swap, and restarts stuck components. Alerts go through ntfy.
- **Schedule (Auckland time):** planning window 22:30 (tier-1), execution 23:00-06:30 (tier-0), review/synthesis 06:30 (tier-1), then idle for your day use.

---

## 9. Remote access

Tailscale only; nothing is exposed to the public internet.

- **Variant choice matters.** Tailscale's docs say the Standalone app cannot be a Tailscale SSH server; on macOS the SSH server requires the open-source `tailscaled` variant. That variant is also the only one that starts before login. So install the Homebrew `tailscale`, run it as a root daemon, then `tailscale up --ssh`. Tailscale itself says `tailscaled` is recommended only for unattended installs by experienced administrators, which is what you are building.
- **Known issue:** an open GitHub issue reports MagicDNS name resolution failing on macOS for both variants. Use `100.x` addresses in your SSH config until it is fixed.
- **ACLs:** tag the mini `tag:agentbox`; allow only your own devices to reach it, and the mini to reach nothing on your tailnet.
- **Control surface:** SSH+tmux from phone/laptop (Termius or Blink); a status/approval dashboard (FastAPI plus HTMX) bound to localhost and exposed with `tailscale serve` (tailnet-only, no Funnel); self-hosted ntfy for push. I could not verify whether ntfy's iOS relay leaks any content, so check that before relying on it. Telegram is the quick-start fallback, but it routes task summaries through a third party.
- **Approvals:** done on the tailnet web page, authenticated by Tailscale identity, with a TOTP step for destructive classes. Do not approve through push-notification buttons alone.
- **Emergency stop:** `agentctl stop` (also reachable from the dashboard) creates a STOP file that the supervisor checks every few seconds, SIGTERMs worker process groups, stops the VM, and flips the egress proxy to deny-all. Test it monthly.

---

## 10. Storage

| Item | Location | Reason |
|---|---|---|
| macOS, tools, apps | Internal | |
| Models (~45 GB) | Internal | Fast load, needed at boot |
| oMLX SSD KV cache (cap 60 GB) | Internal | Latency-sensitive; random access |
| Active repos and worktrees | Internal | |
| SQLite DBs, memory repo, logs (30-day rotation) | Internal | WAL needs reliable fast storage |
| Paper corpus, PDFs, datasets, long-term logs | External | Bulk, rarely read |
| Backups (Time Machine or restic of DBs and memory repo) | External | Plus an offsite encrypted copy |
| Scratch workspaces | Internal | Short-lived, APFS clones |

External throughput depends on the enclosure: roughly 2.5-3 GB/s over Thunderbolt 4 NVMe, about 1 GB/s over the 10 Gbps USB-C port (my knowledge, not tested). Nothing boot-critical goes on the external drive, and every launchd job must survive the volume being absent. The internal 512 GB budget: about 50 GB models, 60 GB KV cache, 100 GB repos and worktrees, 20 GB databases, 30 GB macOS, leaving roughly 250 GB headroom.

---

## A. Technology stack

| Layer | Recommended | Alternatives | Why |
|---|---|---|---|
| Interface | ntfy + tailnet web dashboard + SSH/tmux | Telegram bot, Pushover | No public ports; third-party content exposure is minimal |
| Supervisor | launchd + watchdog process | systemd-style supervisors (not on macOS) | Native, survives reboot |
| Orchestrator | Python service, SQLite lease queue | Temporal, Prefect, DBOS (unverified) | Single node; Temporal's server RAM and ops are unjustified |
| Workers | OpenCode in Apple `container` VM; research pipeline in Python | OpenHands SDK, Pi, Codex CLI | Local-first, small prompts, markdown agents |
| Inference gateway | Thin Python router (admission control, budgets, model-tier routing) in front of oMLX | LiteLLM (not evaluated) | Rules first; log outcomes to learn from |
| Inference | oMLX; llama.cpp fallback | mlx-lm server, vllm-mlx | SSD KV cache plus batching |
| Models | Qwen3.6-35B-A3B (T0), Qwen3.8-27B (T1) | Gemma 4, Qwen3.5-9B for light jobs | Section 1 |
| Memory | Markdown+git, SQLite FTS5, `sqlite-vec` later | Postgres+pgvector | No infrastructure to babysit |
| Research | Custom ledger; OpenAlex, Semantic Scholar, Crossref, arXiv, SearXNG | PaperQA2, OpenScholar | Verifiable citations |
| Sandbox | Apple `container` + pf + Seatbelt | Lima, vibe, Docker Sandboxes | Per-container VMs, no Docker Desktop RAM overhead |
| Remote | Tailscale (`tailscaled` variant) | WireGuard, Headscale | Identity-based ACLs |

### A2. Market comparison by category

| Category | Best overall | Best for this HW | Best OSS | Lightest | Most mature | Cutting-edge | **Use** |
|---|---|---|---|---|---|---|---|
| Inference | vLLM/SGLang (NVIDIA) | oMLX | llama.cpp | llama.cpp | llama.cpp | MTP + TurboQuant-MLX | oMLX, llama.cpp backup |
| Models | Server-scale GLM/DeepSeek class [S] | Qwen3.6-35B-A3B | Qwen (Apache 2.0) | Qwen3.5-9B / Gemma 4 E4B | Qwen3.6 | Qwen3.8-27B | T0 + T1 above |
| Harness | Claude Code / Codex | OpenCode | OpenCode | Pi | Aider | OpenHands SDK / Hermes | OpenCode |
| Queue | Temporal | SQLite | Temporal | SQLite | Temporal | DBOS-style | SQLite |
| Memory | Postgres hybrid | SQLite+FTS5 | same | Markdown | SQLite | Agent-curated skills | Markdown+SQLite |
| Sandbox | Firecracker | Apple `container` | Lima | Seatbelt | Docker | drydock | `container`+Seatbelt |
| Remote | Tailscale | Tailscale | WireGuard | SSH+tmux | WireGuard | Tailscale Serve | Tailscale |
| Research | PaperQA2-style | Custom ledger | PaperQA2 | API scripts | Zotero+Crossref | CiteAudit-style | Custom |

---

## B. Architecture diagram

```
 PHONE / LAPTOP ──tailnet (WireGuard)──┐
   ssh+tmux | dashboard | ntfy push    │
                                       ▼
┌─────────────────── Mac mini M6 (host) ──────────────────────────────┐
│ INTERFACE: tailscale serve → dashboard (approvals, logs, STOP)      │
│            ntfy (push)       agentctl CLI                           │
│                │                                                    │
│ SUPERVISOR: launchd + watchdog (health, memory pressure, restarts) │
│                │                                                    │
│ ORCHESTRATOR (Python)                                               │
│   SQLite: tasks(lease,state) agents runs budgets approvals          │
│   planner → decompose → AgentSpec validator → scheduler             │
│   policy engine: permissions, budgets, stop conditions              │
│        │                         │                                  │
│        ▼                         ▼                                  │
│ WORKER POOL (≤5)          RESEARCH PIPELINE (deterministic)         │
│  OpenCode sessions        discover→acquire→parse→ledger→write       │
│  one per git worktree     →validate→verify→report                   │
│        │ (inside Linux VM)       │                                  │
│        ├─────────────────────────┤                                  │
│        ▼                         ▼                                  │
│ EGRESS PROXY (allowlist, secret injection, logs; pf-enforced)       │
│        │                                                            │
│ INFERENCE GATEWAY: router + admission (≤3 slots) + token budgets    │
│        ▼                                                            │
│ oMLX  [T0 Qwen3.6-35B-A3B ⇄ T1 Qwen3.8-27B] + embedder              │
│   hot KV (RAM) ↔ cold KV (internal SSD)                             │
│                                                                     │
│ MEMORY: markdown repo (git) + SQLite FTS5 (+sqlite-vec later)       │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
                 EXTERNAL 1TB: corpus, datasets, backups
```

I changed one thing from your suggested shape: the model router is not a separate layer. It sits inside the inference gateway with admission control, because routing and memory-aware scheduling are the same decision.

---

## C. Hardware and resource plan

| Consumer | GB |
|---|---|
| macOS, sshd, tailscaled, launchd | 4.0 |
| MLX GPU-wired pool: weights ~19.5, hot KV ~2.5, embedder ~0.6, scratch ~0.9 | 23.5 |
| Harness workers (≤5 × ~250 MB) | 1.3 |
| Linux VM (builds, browser, tests) | 2.5 |
| Orchestrator, SQLite, SearXNG, ntfy, dashboard | 0.7 |
| Page cache / residual | ~0 |
| **Total** | **32** |

This is tight. Set `iogpu.wired_limit_mb=24064` (73% of RAM, slightly above the roughly 70% guidance one source cites) and watch memory pressure. If it goes yellow or red, or swap exceeds about 1 GB sustained, drop to 22.5 GB and shrink the hot KV tier; the SSD tier absorbs the difference. When the 27B is loaded (about 16.5 GB), roughly 6 GB frees for KV, enough for 128K contexts. A user on a 32GB M5 reported agentic runs with a ~30B coder and multi-file tools exhausted memory and killed the session (one anecdote), which is the failure this budget is designed to avoid.

Bottlenecks in order: decode bandwidth, prefill on long contexts, memory headroom, then external-drive latency. Concurrent large-model workers: one model, up to three sequences. Concurrent small-model workers: none. The MoE already runs at about 3B active, so a separate small LLM saves nothing and costs 2.5 GB. Swap models only at phase boundaries (a few times a day), never per request. Load time from internal SSD is unmeasured; expect seconds to tens of seconds.

**Night capacity (est.):** about 300-500K decode tokens per stream over 8 hours, or 0.6-1.2M with 2-3 streams. Treat these as order-of-magnitude until measured.

---

## D. Agent architecture (100+ logical agents)

**Data model (SQLite):**

```sql
CREATE TABLE agents(id TEXT PRIMARY KEY, version INT, role TEXT, system_prompt_hash TEXT,
  tools JSON, tier TEXT, perms JSON, budget JSON, parent_id TEXT, status TEXT); -- ephemeral|promoted|retired
CREATE TABLE tasks(id TEXT PRIMARY KEY, project TEXT, kind TEXT, priority INT, state TEXT,
  agent_id TEXT, lease_until INT, attempts INT DEFAULT 0, not_before INT, risk TEXT, handoff TEXT);
CREATE TABLE runs(id TEXT PRIMARY KEY, task_id TEXT, model TEXT, tokens_in INT, tokens_out INT,
  tool_calls INT, outcome TEXT, log_path TEXT, started INT, ended INT);
```

**Claim a task atomically** (SQLite 3.35+ `RETURNING`):

```sql
UPDATE tasks SET state='running', lease_until=:now+300 WHERE id=(
  SELECT id FROM tasks WHERE state='queued' AND not_before<=:now
  ORDER BY priority DESC LIMIT 1) RETURNING *;
```

Workers heartbeat every 60 seconds. Expired leases requeue with the last handoff note.

**Flow:** planner (T1) → tasks → scheduler picks tier-appropriate tasks per window → worker instantiates an agent from its spec → inference gateway admits at most 3 sequences → results go to the verifier → follow-up tasks enqueue. One hundred agent definitions cost a few kilobytes each.

---

## E. Model strategy

| Task | Model | Settings |
|---|---|---|
| Planning | Qwen3.8-27B (T1) | Thinking on; batched in planning window |
| Coding | Qwen3.6-35B-A3B (T0) | Thinking limited; 32-64K context |
| Debugging | T0 for 2 attempts, then T1 with a summarized failure transcript | Escalation ladder |
| Research reading/extraction | T0 | Structured JSON output, chunk-level |
| Summarization | T0 | Non-thinking |
| Classification / routing | Deterministic rules first, T0 for ambiguous cases | Constrained JSON, ≤50 tokens |
| Final synthesis and review | T1 writer; separate T1 verifier pass; cloud optional for >128K | Different prompt from writer |
| Embeddings | ~0.6B embedder (class not verified) | Served by oMLX |

Escalation ladder: T0 → retry with different prompt → T1 → optional cloud (privacy-gated) → human.

---

## F. 24/7 architecture

Covered in Section 8. Failure modes and recovery:

| Failure | Detection | Recovery |
|---|---|---|
| Worker crash or hang | Heartbeat expiry; no-progress watchdog | Lease expires, task requeues with handoff |
| oMLX crash or OOM | Health probe, memory pressure | launchd restart; SSD KV cache survives; fall back to llama.cpp after 3 failures |
| Power loss | Boot | `autorestart`; auto-login; LaunchAgents resume; queue state is in SQLite |
| External drive missing | Mount check | Pause research jobs, continue coding, alert |
| Runaway agent | Budget, loop and time limits | Kill process group, mark needs-human |
| Model regression after an update | Nightly eval | Auto-pin the previous version; alert |

---

## G. Remote control

Covered in Section 9. Phone workflow: ntfy push on task done or blocked → open tailnet dashboard → read the diff or report → approve with TOTP → or STOP.

---

## H. Security architecture

**Approval matrix**

| Operation | Policy |
|---|---|
| Read, write, and run tests inside the task worktree | Autonomous |
| Create branches, commit to `agent/*` | Autonomous |
| Web GET on allowlisted domains; scholarly API calls | Autonomous |
| Install dependencies from a lockfile via the proxy mirror | Autonomous, notify on additions |
| Write to memory (curated) | Autonomous |
| New egress domain | Queue for approval |
| Diff above 500 lines or touching CI/secrets/config paths | Approval |
| Push, open PR, merge | Approval (push to `agent/*` on private repos can be auto after a trial period) |
| Delete branches, `rm -rf` outside the worktree, any destructive git (reset --hard on shared refs, force push) | Blocked by default; manual only |
| Sending messages or email; spending money; using credentials | Approval |
| Sending content to a cloud model | Only for repos flagged `cloud_ok`; otherwise blocked |
| `sudo`, system config, launchd, installing system software | Never from the agent |
| Access to personal or financial directories | Not mounted; impossible |

**Controls:** dedicated macOS user; VM boundary; per-task disposable workspaces; no credentials in the VM; commit trailer `Agent-Task: <id>`; protected branches on the remote; append-only audit log (SQLite plus signed daily export); limits per task (time, tokens, tool calls) and per day (tasks, tokens); STOP file; quarterly kill-switch drill. Treat all fetched content as untrusted: strip it from system-prompt position, and never let fetched text alter agent permissions.

---

## I. Installation plan and phased roadmap

Commands assume macOS 27 and an admin account. Verify exact model repo IDs yourself (`hf search`), since I found one third-party Qwen3.8 MLX repo and unofficial mirrors exist. Placeholder repos appeared on Hugging Face before the real Qwen3.8 release, so prefer the Qwen org, `mlx-community`, or oMLX's own conversions, and check checksums.

**Phase 1: Minimal working system**

```bash
# power
sudo pmset -a sleep 0 disksleep 0 womp 1 autorestart 1
# agent user (standard, no admin)
sudo sysadminctl -addUser agent -fullName "Agent" -password -
# tools (admin)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew tap jundot/omlx && brew install omlx
brew install uv node
# models (as agent), repo IDs to be verified
uv tool install "huggingface_hub[cli]"
hf download <verified-qwen3.6-35b-a3b-mlx-4bit> --local-dir ~/models/qwen36-35b-a3b
hf download <verified-qwen3.8-27b-mlx-4bit>   --local-dir ~/models/qwen38-27b
omlx serve --model-dir ~/models --paged-ssd-cache-dir ~/.omlx/cache --hot-cache-max-size 10%
```

GPU limit at boot, as `/Library/LaunchDaemons/local.wired-limit.plist`, running `/usr/sbin/sysctl iogpu.wired_limit_mb=24064` with `RunAtLoad`. Activate with `sudo launchctl bootstrap system /Library/LaunchDaemons/local.wired-limit.plist`. Then install OpenCode (`npm i -g opencode-ai`; confirm the current method at opencode.ai) and point it at the local OpenAI-compatible endpoint:

```json
{ "$schema": "https://opencode.ai/config.json",
  "provider": { "local": { "npm": "@ai-sdk/openai-compatible", "name": "oMLX",
    "options": { "baseURL": "http://127.0.0.1:<omlx-port>/v1" },
    "models": { "qwen-moe": { "name": "Qwen3.6-35B-A3B", "limit": { "context": 131072, "output": 16384 } } } } },
  "model": "local/qwen-moe" }
```

- **Test:** the day-1 benchmark from Section 1, then one real bugfix on a scratch repo. Record memory pressure throughout.
- **Failure modes:** Metal allocation errors (raise the wired limit), garbled output (run `infer-check`), tool-call format errors (try the llama.cpp backend).
- **Rollback:** `launchctl bootout`; delete `~/.omlx`; remove the sysctl daemon.

**Phase 2: Autonomous coding.** Install Apple's `container` (signed pkg from the apple/container GitHub releases; `container system start`). Build an image with git, Node, Python, Playwright and OpenCode. Write the worktree manager and the completion gate. Add the pf egress rule and proxy.
- **Test:** 20-task eval set; a deliberate exfiltration attempt (the VM must fail to reach a non-allowlisted host); a task that deletes files outside the worktree (must be impossible).
- **Failure:** VM memory exhaustion (shrink concurrency); proxy breaks package installs (add a mirror).
- **Rollback:** stop and delete VMs; worktrees are disposable.

**Phase 3: Research agents.** Create the ledger schema and the pipeline stages. Register an OpenAlex key. Start SearXNG in the VM or the Linux container.
- **Test:** 10 questions where you know the literature; inject a fake DOI and a mashup citation. Both must be rejected by the validator.
- **Failure:** API budget exhaustion, PDF parse failures, SearXNG engines getting rate-limited.
- **Rollback:** drop ledger tables; they are derived data.

**Phase 4: Persistent memory.** Create the `memory/` git repo, FTS5 indexes and the curator. Add `sqlite-vec` and the embedder only if recall tests fail.
- **Test:** recall of five decisions from last week without prompting. **Failure:** memory bloat, stale notes. **Rollback:** `git revert`.

**Phase 5: Multi-agent orchestration.** Agent registry, AgentSpec validator, scheduler with tier windows and the inference gateway. **Test:** 20 mixed tasks overnight; verify no task exceeded budgets and the slot cap held. **Failure:** swap thrash (widen batching windows), starvation. **Rollback:** disable dynamic agents; run static specs only.

**Phase 6: 24/7 operation.** LaunchAgents for oMLX, orchestrator, proxy, SearXNG, ntfy and the watchdog. **Test:** pull the power cord mid-task; kill workers at random; unplug the external drive. All should recover with no data loss. **Failure:** auto-login not triggering, services starting before the volume mounts. **Rollback:** `launchctl bootout` each service.

**Phase 7: Remote access.**

```bash
brew install tailscale && sudo brew services start tailscale
sudo tailscale up --ssh --hostname=agentbox
tailscale serve --bg http://127.0.0.1:<dashboard-port>
```

Set ACLs, add TOTP approvals and the STOP path. **Test:** from cellular, run a task, approve a gated action, then STOP and confirm that workers, VM and proxy all halt within 30 seconds. **Failure:** DERP-relayed connections, MagicDNS issue (use IPs). **Rollback:** `tailscale down`.

**Phase 8: Advanced optimization.** Enable MTP on the 27B (after verifying the head exists); evaluate KV quantization and 8-bit KV; compare llama.cpp vs oMLX after each major MLX release; run the harness bake-off again after OpenCode updates; tune concurrency. Re-run the eval set after every change, and pin versions.

---

## J. What NOT to install

| Item | Why |
|---|---|
| OpenClaw | High-privilege gateway design, public skill marketplace, and documented destructive-behavior incidents [S] |
| Ollama / LM Studio as the production server | Redundant with oMLX; no SSD KV tier; MLX backend reportedly needs more than 32 GB [S] |
| Docker Desktop | RAM tax on a 32 GB box; Apple `container` does the job |
| Temporal, Redis, RabbitMQ, Kubernetes | Single node; none of it pays for its RAM |
| Qdrant, Chroma, Weaviate, Milvus, Neo4j, GraphRAG | LLM-heavy indexing is unaffordable at 30-40 tok/s; FTS5 plus `sqlite-vec` suffices |
| LangChain, LangGraph, CrewAI, AutoGen | Not evaluated in this window; judged on fit: your durable state belongs in SQLite, not a framework |
| Letta, mem0, Zep | Extra infrastructure; the write-discipline problem remains yours |
| Large MCP collections | Every schema costs prefill; keep ≤15 tools per agent |
| GUI computer-use agents | Slow with local VLMs and break isolation |
| 70B+ models, ≤3-bit quants of big MoEs | Do not fit or lose quality. Expert streaming from SSD exists (a 35B MoE running in under 4 GB RAM via paging) but costs speed and is community-grade |
| Gemini CLI, Roo Code | Gemini CLI retired June 18, 2026; Roo Code archived in May |
| Gemma 4 31B as the coder | Weaker agentic-coding numbers than Qwen per Qwen's own table; use only for multimodal |

---

## K. Upgrade path

- **64 GB (M5 Pro mini: up to 64 GB at 307 GB/s):** about 1.8x the decode bandwidth. Keep both tiers resident with no swapping, raise concurrency to 4-6 slots, and give the VM and browser real headroom. A 70B dense at 4-bit still tops out under 8 tok/s even at 307 GB/s, so stay with MoE.
- **96-128 GB:** 100B-class MoEs (for example GPT-OSS-120B at 65.8 GB in 4-bit) become practical, and the 27B can run at 8-bit. Mac Studio configurations reportedly go higher; I did not verify them.
- **Dedicated GPU or server:** put vLLM/SGLang on an NVIDIA box for batch throughput, and keep the Mac as the control plane. Everything speaks OpenAI-compatible APIs, so only the gateway endpoint changes. The Thunderbolt 5 Mac clustering Apple mentions needs the M5 Pro mini, not your M6.
- **Unchanged at any size:** the orchestrator, ledger, memory, sandbox and approval model.

---

## Sources

Primary (P) or secondary (S). Apple's newsroom and most vendor model cards were not retrieved.

1. Mac mini M6 32GB/512GB listing, release 22 Sep 2026 (S, retailer): https://www.ldlc.com/en/product/PB00751971.html
2. Mac mini M6/M5 Pro launch (S): https://www.igeeksblog.com/mac-mini-m6-m5-pro-price-specs-release-date/
3. Mac mini M6 specs and M5 Pro 64 GB (S): https://fstoppers.com/gear/apples-new-mac-mini-gets-m6-m5-pro-and-genlock-video-work-904276
4. Mac mini launch, Neural Accelerators, TB5 clustering (S): https://t2online.in/tech/tech-news/apple-mac-mini-launches-with-m6--m5-pro-chips/2007528
5. M6 2nm, dual Neural Engines (S): https://guru3d.com/story/apple-m6-2nm-processor-debuts-with-12core-cpu-12core-gpu-and-dual-neural-engines/
6. Bandwidth ceiling analysis (S): https://levelup.gitconnected.com/apple-says-the-mac-mini-m6-is-4-8x-faster-at-ai-the-number-that-actually-matters-went-up-42-6aa2a8be9b50
7. M6 9B llama.cpp measurements (S): https://www.mindstudio.ai/blog/m6-mac-mini-local-ai-performance
8. 16 GB M6 guide, GPU memory default (S): https://pub.towardsai.net/is-a-16gb-mac-mini-enough-for-local-llms-m6-2026-efd2a80ca3d1
9. M6 32 GB model rankings, index estimates (S): https://llmcheck.net/best-llm/mac-mini-m6-32gb/
10. Qwen3.8 / 3.6 / 3.5 repository (P): https://github.com/QwenLM/Qwen3.8
11. Qwen3.8-27B release details (S): https://www.orcarouter.ai/blog/qwen-3-8-27b-huggingface
12. Open LLM benchmark roundup (S): https://www.morphllm.com/best-open-source-llm
13. Apple Silicon benchmark dataset, M2 Max 32GB (S, community): https://huggingface.co/datasets/RaynarDM/apple-silicon-llm-benchmarks
14. mlx-lm MTP PR #990 (P): https://github.com/ml-explore/mlx-lm/pull/990
15. MTP in llama.cpp (S): https://mer.vin/2026/05/run-qwen-3-6-mtp-in-llama-cpp-faster-local-inference-with-built-in-speculative-decoding/?amp=1
16. oMLX project (P): https://omlx.ai and https://github.com/v7idea/omlx
17. vllm-mlx (S): https://www.emergentmind.com/topics/vllm-mlx
18. MLX vs llama.cpp study, arXiv 2511.05502 (P): https://huggingface.co/papers/2511.05502
19. TurboQuant-MLX (S, community): https://github.com/manjunathshiva/turboquant-mlx
20. OpenHands local LLM docs (P): https://docs.openhands.dev/usage/llms/local-llms
21. Harness scaffold effect, arXiv 2607.22585 (P): https://arxiv.org/pdf/2607.22585
22. Harness fluency study, Qwen3.6 27B (S, community): https://huggingface.co/blog/bytkim/qwen36-27b-reasoning
23. Open-source CLI agents survey (S): https://pinggy.io/blog/best_open_source_cli_coding_agents
24. Harness comparison (S): https://techstackups.com/comparisons/coding-agent-harness-comparison-2026/
25. OpenCode vs Codex CLI (S): https://morphllm.com/comparisons/opencode-vs-codex
26. OpenClaw vs Hermes (S): https://toolradar.com/blog/openclaw-vs-hermes-agent
27. OpenClaw security notice (S): https://github.com/Desu403/claw-local
28. Byte-Sized Intelligence on OpenClaw incidents (S): https://bytesizedintelligence.beehiiv.com/p/byte-sized-intelligence-march-12-2026
29. Agent sandbox survey (S): https://github.com/fishman/awesome-agent-sandbox
30. `vibe` VM sandbox (P, repo): https://github.com/lynaghk/vibe
31. Apple Containerization overview (S): https://glichstream.substack.com/p/apple-has-finally-solved-the-problem
32. Osaurus sandbox docs, macOS 26 requirement (S): https://docs.osaurus.ai/sandbox
33. Tailscale macOS variants (P): https://tailscale.com/docs/concepts/macos-variants.md
34. Tailscale SSH (P): https://tailscale.com/docs/features/tailscale-ssh.md
35. Tailscale MagicDNS macOS issue (P, repo): https://github.com/tailscale/tailscale/issues/19139
36. OpenAlex authentication and pricing (P): https://developers.openalex.org/api-reference/authentication
37. Reference hallucination in deep-research agents, arXiv 2604.03173 (P): https://arxiv.org/pdf/2604.03173
38. CiteAudit, arXiv 2602.23452 (P): https://arxiv.org/pdf/2602.23452
39. Citation faithfulness kit, arXiv 2607.20527 (P): https://arxiv.org/pdf/2607.20527
40. 32GB M5 local-coding anecdote (S, Reddit snapshot): https://reddit.sentinel-team.org/posts/1uw2hir/snapshots/2026-07-17T18%3A53%3A30.39359Z
41. mlx-lm wired-limit documentation (S, mirror): https://docsearch.algolia.com/mcp/docs/repo/ml-explore/mlx-lm
42. Same-source verification risk in an integrity-agent writeup (S): https://succubuns.com/naughty-bots/6e30e367-6eb0-4542-8938-6cf8977a487e?page=8

**What I could not verify:** Apple's own M6 numbers; oMLX on M6/macOS 27; whether Qwen3.8 ships an MTP head; Metal access from LaunchDaemons; `pf` egress enforcement with `container`; remote FileVault unlock on macOS 27; ntfy iOS relay privacy; and the Docling, GROBID, SearXNG, sqlite-vec and OpenCode install details I gave from prior knowledge.

## Reasoning trace (not shown to raters)

Claude responded: I'll start by verifying the current state of the hardware and ecosystem before designing anything.
Resolving a date discrepancy before starting the research.
Resolving a date discrepancy before starting the research.

I’ll start by verifying the current state of the hardware and ecosystem before designing anything.

Searched the web

Searched the web






6 minutes ago

## Run notes

claude.ai incognito chat (no history or memory), model menu Sonnet 5.5, Effort High; the menu showed
"Sonnet 5.5 High". Connectors were switched off in the composer menu; the composer has no web-search
switch, and Claude searched the web by itself. Send time 2026-10-14T07:12:13.220Z (browser clock, read right after
sending). Chat: https://claude.ai/chat/6aa84973-425a-406e-ad00-1311eb4877e9?incognito (incognito chats are not kept in history).
Operated by the assistant (Claude, via the Claude in Chrome extension) in the author's signed-in browser,
at the author's request; the runs were opened in separate tabs and sent in manifest order without waiting
for earlier answers. The app turns long pastes into an attachment, so the prompt was inserted as plain
text in eight line-aligned pieces from one clipboard paste and checked against the original (1,782 words,
same text) before sending. Answer copied with the app's Copy button (it includes any short lines the model
wrote before its searches) and written verbatim from the clipboard; the reasoning trace is the visible
process panel (step summaries and search queries) copied from the page text.
Replacement for this run: attempt 1 was stopped by the author's claude.ai usage limit and is in
superseded/. Sent after the limit reset, with at most three chats generating at once.
