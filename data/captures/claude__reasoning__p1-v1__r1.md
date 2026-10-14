---
run_id: claude__reasoning__p1-v1__r1
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
replicate: 1
date_stamped: '2026-10-14T02:40:55+00:00'
date_run: '2026-10-14T02:40:55+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

Model: Claude Sonnet 5.5. Knowledge cutoff: end of June 2026. Web search: on, and I'm researching now. One discrepancy to flag: your brief says today is 31 Aug 2026, but my session date is 14 Oct 2026. I'm treating 14 Oct 2026 as current.

**Model:** Claude Sonnet 5.5 (Anthropic) | **Knowledge cutoff:** end of June 2026, so everything after that comes from live search | **Web browsing:** ON (about 60 searches and fetches on 14 Oct 2026)

**Caveats**
- Your brief says today is 31 Aug 2026, but my session clock says 14 Oct 2026. I used 14 Oct.
- I am an Anthropic model. Claude appears only in the optional cloud tier below, and DeepSeek is cheaper. Treat my cloud ordering as unproven until you run your own evals.
- Evidence tags: **[P]** primary or vendor-reported, **[C]** community measurement, **[S]** secondary or SEO-prone, **[D]** derived by me from cited inputs.
- I found no independent M6 benchmarks. All speed figures are bandwidth arithmetic, scaled from M4/M5-class community data. Day-1 measurement is a gating step (section I, Phase 1).

---

## 0. Decisions at a glance

| Layer | Pick | Confidence |
|---|---|---|
| Binding constraint | Memory bandwidth (170 GB/s), not capacity | High |
| Inference engine | oMLX (MLX) primary, llama.cpp `llama-server` fallback | Medium |
| Bulk worker model | Qwen3.6-35B-A3B, about 3.5-bit mixed MLX, resident | Medium |
| Hard-task model | Qwen3.8-27B dense, 4-bit mixed with MTP head, loaded on demand | Medium-high |
| Embeddings | jina-embeddings-v5-text-small (0.6B, MLX), reranker optional | Medium |
| Orchestrator | Custom thin "conductor" on DBOS + SQLite | High |
| Coding harness | OpenCode (headless server), Pi for tiny workers | Medium |
| Research | Custom evidence-ledger pipeline, SearXNG + OpenAlex/S2/Crossref/arXiv, Docling | High (design) |
| Memory | Markdown + one SQLite file (FTS5 + sqlite-vec) | High |
| Isolation | Dedicated macOS user, Apple `container` VMs, egress allowlist, credential broker | High |
| Always-on | LaunchDaemons with `UserName=agent`, pmset, FileVault OFF (explicit trade-off) | High |
| Remote | Tailscale, tailnet-only dashboard, self-hosted ntfy approvals | High |
| Cloud | Off by default, per-project opt-in, cheap tier first | Medium |

**Market matrix** (best overall / your hardware / open-source / lightweight / mature / cutting-edge / what you should use)

| Category | Best overall | Best for M6-32GB | OSS | Lightweight | Mature | Cutting-edge | Use |
|---|---|---|---|---|---|---|---|
| Inference engine | oMLX | oMLX | oMLX, llama.cpp | Ollama | llama.cpp | MTPLX, dflash-mlx | oMLX + llama.cpp fallback |
| Models | Qwen3.8-27B | Qwen3.6-35B-A3B | Qwen family | Gemma 4 E4B | Qwen3.6 | Qwen3.8 | 35B-A3B + 27B |
| Harness | No independent head-to-head found | OpenCode | OpenCode | Pi | OpenCode | Hermes | OpenCode under custom conductor |
| Durable execution | Temporal (scale) | DBOS on SQLite | DBOS | SQLite + own loop | Temporal | Restate | DBOS |
| Memory | Markdown + SQLite | same | same | flat files | SQLite | temporal KG | SQLite |
| Sandbox | microVM per task | Apple `container` | Lima, apple/container | Seatbelt | Docker Sandboxes | drydock/sand wrappers | Apple `container` + Seatbelt |
| Remote | Tailscale | Tailscale | Tailscale client, Headscale | SSH | Tailscale | n/a | Tailscale + ntfy |

---

## 1. Local inference

**Hardware facts.**
- The M6 Mac mini has a 12-core CPU and 12-core GPU with Neural Accelerators in each GPU core. Memory is 16GB base, configurable to 32GB, with bandwidth up to 170GB/s, up from 153GB/s.
- It keeps Thunderbolt 4 and cannot be clustered.
- It was announced 25 Aug 2026, with sales from 22 Sept.
- The 170GB/s figure applies only to the 24GB and 32GB builds, and the GPU can by default use about two-thirds of RAM on Macs with 32GB or less.

**The governing equation [D].**
- Decode tok/s is roughly bandwidth divided by bytes read per token, times 50 to 80% efficiency.
- A 27B dense 4-bit model is 15 to 17 GB, so the ceiling is about 10 to 11 tok/s. An independent analysis reached the same figure, about 10 tok/s as the theoretical maximum for 27B at 4-bit on M6. Expect 6 to 9 real.
- A 3B-active MoE reads about 1.5 to 2 GB per token, so the ceiling is above 80 tok/s.
- Prefill is compute-bound, and M6's Neural Accelerators help there. One secondary test reports 742 tok/s prompt processing versus 210 on M4 for a 9B model, but only 18 to 27 tok/s generation. That source is SEO-ish, so treat the figures as indicative.

**Engines.**

| Engine | Verdict |
|---|---|
| **oMLX** | MLX server with continuous batching, a paged SSD KV cache, and both OpenAI and Anthropic-compatible endpoints. It requires macOS 15+ and supports LLMs, VLMs, embeddings and rerankers. Young (v0.6.x era) but purpose-built for agent loops that invalidate KV caches. **Pick.** |
| llama.cpp `llama-server` | Most mature. Grammar-constrained JSON, widest model coverage. MLX is reported 15 to 40% faster at 4-bit decode on M4/M5. GPT-OSS-20B is the notable exception, where llama.cpp wins. **Fallback.** |
| Ollama 0.34.x | The engine is chosen by file format: safetensors go to MLX, GGUF stays on llama.cpp. Easiest, least control over the cache. |
| LM Studio | One practitioner reports its bundled MLX runtime did not recognise Qwen3.6's MTP layers. Skip for the server role. |
| vLLM / SGLang / TokenSpeed | Qwen's card recommends them for production, but they target CUDA. Not for this machine. |

**Speculative decoding is unresolved on Metal.**
- oMLX users report MTP taking decode from about 10 to 11.7-12.3 tok/s on an M1 Pro, and MTPLX claims 1.6 to 2.24x.
- Another measurement on an M2 Max found MTP and DFlash2 speculative decoding to be net losses on Metal, citing llama.cpp issues.
- Treat it as an A/B test on your box, not a default.

**Models.** Benchmarks below are vendor-reported unless marked.

| Model | Size at 4-bit | Evidence | Verdict |
|---|---|---|---|
| **Qwen3.8-27B** (dense, Apache-2.0) | about 15.3 to 16.8 GB | Model card: SWE-bench Pro 61.7, Terminal-Bench 2.1 73.0, DeepSWE 1.1 42.2 (vs 13.3 for Qwen3.6-27B), 262K native context, MTP head. One practitioner reports it is the first model they can leave alone for overnight tasks, and that 35B-A3B is lighter but less reliable. | Hard tier |
| **Qwen3.6-35B-A3B** (MoE, Apache-2.0) | about 15.8 GB (oQ3) to 20.2 GB (Q4_K_M) | SWE-bench Verified 73.4, Terminal-Bench 2.0 51.5. [C] on an M5 10-core 32GB: 57.8 tok/s decode, 1,149 tok/s prefill, 16.6 GB peak at 4k context (oQ3). | **Bulk tier** |
| Gemma 4 26B-A4B | about 16.8 GB | 25.2B total, 3.8B active, 256K context, native function calling. [C] M4 32GB: 37.7 tok/s, 355 tok/s prefill. | Generalist and summariser. Qwen's own table has it weak on SWE-bench, though NVIDIA's table differs, so harness-sensitive. |
| Muse Glimmer 30B | about 17 GB (NVFP4) | Apache-2.0, released 10 Aug 2026, SWE-bench Pro 51.2. Dense, 131K context. | Skip: dense speed with lower scores than Qwen3.8-27B |
| Nemotron 3.5 Lightning 30B-A3B | about 17 GB | NVIDIA's own table: SWE-bench Verified 51.6 and Terminal-Bench 2.1 24.6, versus 70.1 and 44.4 for Qwen3.6-35B-A3B. | Skip for coding |
| Laguna XS.2 33B-A3B | about 19 GB | Poolside reports SWE-bench Pro 44.5 and Terminal-Bench 2.0 30.1. | Skip (below Qwen3.6-35B-A3B) |
| 70B+ dense, or 100B+ MoE (gpt-oss-120b ~65 GB, Qwen3-Coder-Next 80B-A3B) | does not fit | n/a | Skip. SSD expert-streaming hacks run at about 1.5 to 5 tok/s. |

**What to actually run.**
- **Do not default to the 27B.** At 6 to 9 tok/s it yields roughly 0.2 to 0.35M decode tokens in 8 hours. The MoE yields roughly 1.4 to 3.0M. [D]
- Use a two-tier cascade: the MoE for bulk, the 27B for planning, review, and anything that failed verification twice.
- Qwen3.8's default reasoning effort is `xhigh`. Qwen warns that lower effort can cost more total time in multi-turn agent tasks because of retries. Default to `medium` and A/B it.

**Quantization.**
- 27B: 4-bit mixed with the MTP head preserved.
- 35B-A3B: about 3.5-bit mixed. A 20 GB Q4 leaves no headroom for sandboxes (section C).
- Avoid 2-bit and below for agent loops.
- Do not take MLX-vs-GGUF quality claims from small-model perplexity tables. Run your own eval.

**Context.**
- Model-card geometry gives 16 full-attention layers, 4 KV heads, head dimension 256. (Layout from the model card.)
- That is about 64 KiB/token at fp16 for the 27B [D], so 64K context is about 4 GiB and 262K is about 16 GiB.
- Cap working context at 64K with compaction at about 45K. Quantize the KV cache and measure, because community peak-memory deltas for the 35B-A3B imply roughly 0.1 MB/token fp16.

**GPU wired limit.** `sudo sysctl iogpu.wired_limit_mb=24576`. Sources describe this as worth doing to stabilise a 27B on 32GB Macs. The setting reverts on reboot, so persist it via a LaunchDaemon (section I).

---

## 2. Agent runtimes and harnesses

| Harness | Evidence | Fit |
|---|---|---|
| **OpenCode** (MIT) | About 200k stars, provider-agnostic, local models supported. Headless `opencode serve` HTTP API, ACP server, `--attach` to avoid MCP cold starts. Reported system prompt about 10k tokens. | **Primary** |
| **Pi** (MIT) | Minimal core, four modes (interactive, print/JSON, RPC, SDK), no subagents or plan mode in core. System prompt reported at about 2 to 3k tokens. Version 0.x. | Tiny workers. Prefill-friendly. |
| Hermes Agent (MIT) | Persistent memory, self-improving skills, built-in cron, Telegram/Slack/WhatsApp gateway. Roughly 20k-token system prompt. | Steal the ideas. Too large a surface for the unattended core. |
| OpenClaw | Critical RCE CVE-2026-25253 and 341 malicious ClawHub skills. Researchers also reported websites reaching local agents via localhost. | **Do not install** |
| Claude Code (commercial) | Works with local models via `ANTHROPIC_BASE_URL` (LM Studio documents it). Qwen evaluates its SWE-bench numbers in the Claude Code harness. Shim issues exist: mid-conversation system messages, a 200k context assumption. | Optional for interactive use. Conflict of interest noted. |
| Codex CLI, Goose, Aider, Crush, OpenHands | Not tested here | Not selected |

**Decision: build a custom conductor, and do not adopt a single monolithic harness.**
- Durability, a single-GPU lease scheduler, memory admission control, the hash-chained audit log and approvals are your product. No existing harness provides them for a 32 GB box.
- Workers should be replaceable harness processes driven over HTTP or RPC.
- Prefill is your weak axis. Prefer harnesses with small system prompts, plus oMLX's persistent SSD KV cache.

**Orchestration framework: DBOS.**
- DBOS uses SQLite by default, supports long-running and human-in-the-loop agents, and integrates with Pydantic AI and the OpenAI Agents SDK.
- Temporal and Restate are well funded, but they are server-class infrastructure. Temporal raised $550M in Sept 2026. That is overkill here.
- I did not verify DBOS's licence terms.

---

## 3. Multi-agent architecture

| Concept | Meaning here | Cost on this machine |
|---|---|---|
| 100 simultaneous model instances | 100 × 16 GB of weights | Impossible, and pointless on shared bandwidth |
| 100 logical agents | Rows in `agent_def` (role, tools, permissions, budget, prompt) | About 0 |
| Task queue | SQLite table, priority classes, leases | About 0 |
| Worker pool | 2 to 3 inference streams, ≤2 sandboxes, ≤1 browser | The real limit |
| Dynamic subagents | An LLM proposes an `AgentSpec` JSON. It is schema-validated, checked against allowlists, budget-capped, then compiled to harness config. | About 0 |
| Swarm | Kimi-style 100 to 300 sub-agent swarms assume cloud-scale inference. | Not viable locally |

**Design: coordinator/worker, depth ≤2, fan-out ≤4.**
- All streams share 170 GB/s. Batching amortises weight reads, but only for MoE.
- [C] On an M5 base chip, 4× batching of the 35B-A3B gave 1.70x aggregate. Another run gave 2.27x. Plan on 2 to 3 concurrent streams, about 100 tok/s aggregate.
- Do not batch the dense 27B. A 2-bit 27B on an M5 Air showed 0.75 to 0.87x aggregate with batching.

**Inference lease scheduler.**
- A priority queue with classes: interactive > foreground > background.
- Model affinity: drain all MoE tasks, swap once, drain the 27B queue. Use aging to avoid starvation.
- Memory admission control: refuse to spawn a VM or browser if free+inactive memory is under 4 GB.
- Preempt only at step boundaries.

---

## 4. Coding agents

**Loop.** Plan → create git worktree → implement → run tests **host-side deterministically** → on failure feed back (max N) → review by a different tier → commit to `agent/*` branch → publish a patch for approval. Never push unprompted.

**Escalation ladder.** Per-task attempts:
1. MoE, 2 attempts.
2. Dense 27B on the failing diff plus logs.
3. Optional cloud, only if the project is allowlisted.
4. Park for human.

Tests are the ground truth. Dense-vs-MoE reliability claims are anecdotal, so choose the default tier by measuring **accepted tasks per hour** on three of your own repositories over 3 days (section I, Phase 2).

**Why OpenCode.**
- It has a headless server, per-agent permissions and ACP.
- It has the largest independent OSS adoption of any harness I checked. Quality comparisons against Claude Code and Codex were not independently verified.
- A reviewer noted an older version sent the first message of a session to a hosted model for session titles unless a small model was configured. That was fixed in v1.2.23. Pin `small_model` to local anyway.

---

## 5. Research agents

**Principle: citations are database foreign keys, never generated text.**

```
Plan → Search (SearXNG + OpenAlex/S2/Crossref/arXiv) → Fetch → Parse (Docling)
→ Evidence ledger (SQLite: source, sha256, passage, char offsets)
→ Claim extraction (each claim anchored to evidence_id + exact quote span)
→ Verify (1) quote is a substring of the stored passage  [deterministic]
         (2) DOI/title resolves in Crossref/OpenAlex/S2  [deterministic]
         (3) NLI-style judge by a different model/tier   [LLM]
→ Contradiction pass → Synthesis constrained to evidence IDs
→ Lint: every cited sentence resolves; unsupported sentences dropped or flagged
→ Bibliography generated from the DB, not by the LLM
```

**Why this much machinery.**
- Over 100 hallucinated citations were found across at least 53 accepted NeurIPS 2025 papers.
- A cross-model audit used a CrossRef → OpenAlex → Semantic Scholar cascade with fuzzy title matching. That is the right first filter.
- HALLMARK reports that API-lookup tools top out around 27% detection on its harder hallucination types. Existence checks are necessary but not sufficient, so you need content-level verification (step 3).
- One survey notes that open models struggle to produce fully cited reports in one shot. The ledger design removes that burden.

**Parsing.**
- Docling (MIT).
- Docling's own benchmark claims competitive CPU and Apple Silicon speeds.
- Marker 2 scores 76.0% on olmOCR-bench in balanced mode. Its weights carry a paid-licence threshold above $5M revenue. That is fine for personal use but check before you commercialise.
- olmOCR-2 through llama.cpp took about 37 s/page on an M5 Pro. Reserve VLM OCR for scanned pages only.

**Frameworks.** GPT-Researcher, LangChain Open Deep Research and STORM exist, but they are different jobs, not clones. Mine their prompts. Do not adopt one wholesale, because none gives you the ledger and the lint.

---

## 6. Persistent memory

| Option | Verdict |
|---|---|
| Markdown files (`AGENTS.md` per repo, ADR decision log, curated global notes) | **Start here.** Human-readable, diffable, git-tracked. |
| SQLite + FTS5 | **Phase 4.** One file, BM25. |
| + `sqlite-vec` + embeddings, hybrid via RRF | **Phase 4.** Several local memory projects use exactly this stack. |
| Bitemporal facts table (`valid_from`/`valid_to`, provenance) | **Add when contradictions matter.** Handles "decision superseded". |
| Graph DB (Neo4j/Graphiti), Mem0, Letta, Cognee | **Not now.** One author found Graphiti/Zep needs Neo4j and heavy infra. Leaderboard claims are self-reported and contested. |

**Embeddings.** jina-embeddings-v5-text-small is 677M parameters, MTEB English 71.7, available in MLX. About 1 GB resident, served by oMLX.

**Write path.**
- Only the conductor writes memory, and only from verified outcomes (a green test, a verified claim).
- Each record carries provenance (task, commit sha, evidence_id).
- Web-derived text goes to a quarantine scope, so prompt injection cannot persist into trusted memory.

---

## 7. Computer control

**Layers, outermost first.**
1. **Dedicated standard macOS user `agent`.** No admin, no Full Disk Access, separate Keychain. Never run agents as your own user.
2. **Apple `container` VMs.** One lightweight VM per container with a dedicated kernel, Apple Silicon and macOS 26+ only. It reached 1.0.0 on 9 June 2026. Alternatives: Docker Sandboxes (microVM, launched March 2026) and Lima. Mount a throwaway worktree copy, not your home directory.
3. **Egress allowlist** via a host-side proxy. Deny by default. This is where you stop exfiltration.
4. **Credential broker.** Secrets never enter the VM. A host proxy injects tokens only for allowlisted hosts.
5. **Seatbelt (`sandbox-exec`)** on host-side harness processes. Apple marks it deprecated, but Anthropic's sandbox runtime and Codex still use it. Use it as an extra layer, not the main one.

**The lethal trifecta rule.** No single agent may combine private data, untrusted content and an exfiltration channel.
- Research agents: web yes, private data no.
- Coding agents: private repos yes, egress only to allowlisted hosts.

**Apple's direction.** Apple announced on 2 Oct 2026 that it will add controls to Full Disk Access because of AI agents. It gave no version, date or mechanism. Do not rely on it. Never grant Full Disk Access to any agent.

**Browser.**
- Playwright CLI or MCP, headless and `--isolated`, inside the sandbox. The Playwright README says the CLI is more token-efficient for coding agents.
- Chrome DevTools MCP only against localhost, for debugging.
- Chrome warns that DevTools for agents exposes browser content and can act through an authenticated session. Never attach to your daily profile. Extensions that reuse your logged-in session are out.

**GUI computer-use.**
- Qwen3.8-27B reports OSWorld-Verified 84.3. That is a vendor number for a 27B model, so treat it as unproven.
- Phase 8 only, inside a disposable macOS VM (Tart), never on the host.

---

## 8. Always-on operation

**Four properties must stack.** Power returns, the disk unlocks, a session opens (if needed), and the service starts.

- `sudo pmset -a sleep 0 disksleep 0 womp 1 autorestart 1`. On Apple Silicon headless, `displaysleep 0` alone does not stop display parking. A `caffeinate -d` LaunchDaemon does. This only matters for GUI work (use an HDMI dummy plug).
- Services run as **LaunchDaemons with `UserName=agent`**. A daemon runs at boot, before any login. A LaunchAgent (what non-root `brew services` creates) waits for a GUI session.
- **FileVault decision.** FileVault blocks automatic login, so encryption versus unattended restart is a deliberate trade-off. I recommend FileVault OFF, because an unattended reboot after a power cut is a hard requirement and no remote pre-boot unlock exists. Compensate by keeping crown-jewel personal data off this machine, and put a UPS in front of it.
- Disable automatic macOS update installs, since they reboot at night. macOS 27.0.1 shipped 28 Sept and 27.2 is in beta, so pin the version and update deliberately.

**Failure matrix.**

| Failure | Detection | Recovery |
|---|---|---|
| Harness crash | Heartbeat row stale | launchd `KeepAlive`, DBOS replays from the last checkpoint |
| oMLX crash or OOM kill | Watchdog `/health` poll | Restart, scheduler retries the leased step |
| Memory pressure | `memory_pressure`, swap > 1 GB | Pause new VMs, unload model, shed to the smaller tier |
| External SSD drops | Mount check each tick | Forum reports show random disconnects on M4 minis with some TB enclosures. Pause the queue. Nothing irreplaceable lives there. |
| Power loss | `autorestart` | Boots, daemons start, DBOS resumes |
| Runaway loop | Repeated-action hash, no-progress detector | Kill task, park, notify |
| Network loss | Probe failure | Local-only work continues. Research tasks defer. |

**Stop conditions per task.** Wall-clock, tokens, step count, repeated tool-call hash (last 6 identical), no `git diff` or test delta in K steps, disk quota, cloud spend.

---

## 9. Remote access

- **Transport:** Tailscale. It meshes devices through NAT with no public ports. Nothing is exposed to the internet.
- **Dashboard:** `tailscale serve` proxying a localhost-only status and approval app. Serve keeps services on localhost and proxies them through your authenticated tailnet.
- **Shell:** key-only sshd restricted to the tailnet. Tailscale SSH can replace sshd. I did not verify which macOS Tailscale builds include the SSH server.
- **Notifications and approvals:** self-hosted ntfy. Existing agent-box tooling uses ntfy for tap-to-approve on risky actions. iOS web push does not render action buttons. A tap opens the tailnet-only approve page.
- **Contents rule:** pushes carry only a task ID and a short title, never data.
- **Approval hygiene:** each approval has a nonce and a 10-minute expiry. A timeout means deny.
- **Emergency stop ladder:**
  1. Phone button POSTs to the conductor to pause the queue.
  2. A `~/lab/STOP` file is checked every step.
  3. Admin SSH runs `sudo pkill -u agent`.
  4. Tailscale ACL cut.
  5. `sudo shutdown`.

---

## 10. Storage

| Item | Internal 512 GB | External 1 TB | Reason |
|---|---|---|---|
| macOS, apps, toolchains | ✓ | | |
| Hot models (35B-A3B, 27B, embed: about 35 GB) | ✓ | cold copies | Load speed |
| `agent.db` (SQLite WAL) and git repositories of record | ✓ | | State must survive the drive vanishing |
| Active worktrees | ✓ | | Many small files |
| **oMLX SSD KV cache** | | ✓ | Write-heavy. The Mac's internal SSD is soldered, the external is replaceable. |
| VM disk images, logs, scratch | | ✓ | Same wear logic |
| Papers, datasets, embedding index | | ✓ | Rebuildable |
| Backups | | **not a backup** | Same enclosure |

**Backup rule.** `sqlite3 .backup` and `git bundle`, then encrypted `restic` to an off-box target (laptop over Tailscale or object storage).

**Format and drive.** APFS. Users report no sleep or mount issues with external SSDs on Apple Silicon Mac minis. Other reports differ, so buy a reputable TB4 enclosure and set `disksleep 0`.

---

# Deliverables A to K

## A. Technology stack

| Layer | Recommended | Alternatives | Why |
|---|---|---|---|
| Interface | Tailnet web dashboard + ntfy | Telegram bot | No public ports |
| Supervisor | launchd + watchdog daemon | `supervisord` | Native, boots without login |
| Orchestrator | Conductor on DBOS (SQLite) | Temporal, Restate | Durable, tiny |
| Queue | SQLite `task` table + leases | Redis | One file, crash-safe |
| Agents | Rows in `agent_def` + OpenCode/Pi workers | Hermes | Logical agents are cheap |
| Router | Policy code in conductor | LiteLLM, Bifrost | LiteLLM suffered a March 2026 PyPI supply-chain compromise |
| Inference | oMLX | llama.cpp, Ollama | KV cache + batching |
| Tools | Playwright, git, test runners in VMs | MCP registry servers | Reviewed only |
| Memory | Markdown + SQLite FTS5 + sqlite-vec | Graph DB | Avoid infrastructure |
| Search | SearXNG (container) + scholarly APIs | Brave/Tavily | Local-first |
| Parsing | Docling | Marker 2, MinerU | MIT |

## B. Architecture diagram

```
 PHONE / LAPTOP
   │  Tailscale (WireGuard, identity + ACL)         ntfy push (id + title only)
   ▼                                                      ▲
┌───────────────────────── Mac mini M6 (32 GB) ──────────┼──────────────────┐
│ launchd (LaunchDaemons, KeepAlive) ◄── watchdog ───────┘                  │
│                                                                           │
│  tailscale serve ──► DASHBOARD / APPROVALS  (localhost only)              │
│                           │                                               │
│  ┌────────────────────────▼───────────────────────────────────────────┐   │
│  │ CONDUCTOR (user: agent)  DBOS workflows on agent.db (SQLite)       │   │
│  │  task queue │ lease scheduler │ policy engine │ audit chain        │   │
│  │  agent_def registry │ budgets │ stop-conditions │ memory writer    │   │
│  └───────┬──────────────────────────┬─────────────────────────┬───────┘  │
│          │ HTTP/RPC                  │ model API               │ tools   │
│  ┌───────▼────────┐        ┌────────▼─────────┐     ┌─────────▼───────┐   │
│  │ OpenCode / Pi  │───────►│ oMLX :8000       │     │ Apple container │   │
│  │ workers (≤3)   │        │ 35B-A3B ⇄ 27B    │     │ VMs (≤2)        │   │
│  └───────┬────────┘        │ embed 0.6B       │     │  egress proxy ──┼─► allowlisted
│          └── commands ────►│ SSD KV → ext SSD │     │  cred broker    │   hosts only
│                            └──────────────────┘     │  SearXNG, PW    │   │
│  agent.db (internal) │ memory/*.md (git) │ evidence ledger │ audit log    │
└───────────────────────────────────────────────────────────────────────────┘
 External SSD: KV cache, VM images, logs, papers, datasets, restic staging
```

## C. Hardware and resource plan

Estimates. Measure in Phase 1.

| Component (MoE profile) | GB |
|---|---|
| macOS + daemons, headless | 4.5 to 5.5 |
| 35B-A3B weights (~3.5-bit) | 15.5 to 16.5 |
| KV and state, 2 streams ≤32K, quantized KV | 2 to 4 |
| Embedding model | 0.7 to 1.2 |
| Conductor, SQLite, OpenCode servers, MCP | 1.5 to 2.5 |
| Sandbox VMs (≤2 GB each) | 2 to 4 |
| Headless browser (research only) | 0.8 to 1.5 |
| **Total** | **27 to 31** |

This is oversubscribed if everything runs at once. Enforce admission control (section 3).

**Heavy builds.** Rust, C++ or Xcode builds cannot fit in a 2 GB VM. They run in an exclusive slot: the scheduler pauses inference streams and gives the VM 8 to 12 GB.

| Profile | Decode (est., M6) | Prefill (est.) | Overnight decode |
|---|---|---|---|
| 35B-A3B, one stream | 48 to 66 tok/s | 900 to 1,400 tok/s | 1.4 to 1.9M tokens |
| 35B-A3B, 3 to 4 streams | about 100 tok/s aggregate | same | up to about 2.9M |
| 27B, no MTP | 6 to 9 tok/s | 150 to 350 tok/s | 0.17 to 0.26M |
| 27B, MTP (if it wins) | 8 to 12 tok/s | same | 0.23 to 0.35M |

Wired limit 24 GB. Load takes seconds to low tens of seconds, so swap per epoch, not per task.

## D. Agent architecture (100+ logical agents, 1 inference process)

```sql
CREATE TABLE agent_def(id TEXT PRIMARY KEY, version INT, role TEXT, model_tier TEXT,
  tools JSON, perms JSON, budget JSON, prompt_ref TEXT, created_by TEXT, approved INT);
CREATE TABLE task(id INTEGER PRIMARY KEY, parent_id INT, project TEXT, kind TEXT,
  agent_id TEXT, tier TEXT, state TEXT, priority INT, spec JSON, budget JSON,
  spent JSON, attempts INT, lease_until REAL, created REAL, updated REAL);
CREATE TABLE event(id INTEGER PRIMARY KEY, task_id INT, ts REAL, kind TEXT,
  payload JSON, prev_hash TEXT, hash TEXT);          -- hash-chained audit
CREATE TABLE evidence(id TEXT PRIMARY KEY, source_url TEXT, doi TEXT, sha256 TEXT,
  passage TEXT, char_start INT, char_end INT, fetched REAL, verified INT);
CREATE TABLE memory(id INTEGER PRIMARY KEY, scope TEXT, kind TEXT, body TEXT,
  provenance JSON, valid_from REAL, valid_to REAL, confidence REAL);
```

**Dynamic agent creation.**
1. A planner emits an `AgentSpec`.
2. A validator checks the schema, then checks tools and permissions against the project policy (an agent can never request more than its parent holds).
3. A budget cap is applied.
4. It is stored with `approved=0` and auto-approved only for the read-only class. Anything with write, network or credential scope goes to the phone.
5. The agent is instantiated as a task. It takes a lease and exits.

## E. Model strategy

| Role | Model and setting |
|---|---|
| Classification and routing | 35B-A3B non-thinking, JSON-schema constrained. A resident tiny model costs 4 to 5 GB, which is about the KV budget. Add it only if measurements justify it. |
| Summarisation | 35B-A3B non-thinking |
| Planning | 27B, `reasoning_effort=medium` |
| Coding (default) | 35B-A3B. Escalate to 27B after 2 failed verify cycles. |
| Debugging | 35B-A3B first, then 27B on the failing diff and logs |
| Research reading and extraction | 35B-A3B |
| Claim verification and contradiction | 27B (a different model from the extractor) |
| Final synthesis | 27B, optionally cloud for public-source research |
| Embedding and rerank | jina v5 small, jina-reranker-v3.5 optional |

Use the Qwen sampler settings from the model card.

## F. 24/7 architecture

Wake via a LaunchDaemon, not a login item. The conductor loop runs: inspect the queue → lease task → run workflow (DBOS-checkpointed steps) → verify → emit follow-up tasks → check stop conditions → sleep or continue. Failure handling is in section 8.

**Quiet-hours policy.** Overnight, only auto-approve the "autonomous" operations in section H. Any approval request is queued and the task parks until morning, unless the task is flagged urgent.

## G. Remote control

Section 9. One addition: a daily 07:00 digest is pushed as one ntfy message containing counts (done, parked, failed), not content, with a link to the dashboard.

## H. Security architecture

**Operation tiers.**

| Tier | Operations |
|---|---|
| **Autonomous** | Read and write inside the task worktree. Run tests and builds in a VM. Commit to `agent/*` branches. Web GET and search on allowlist. Package install in VM from lockfiles with lifecycle scripts disabled. |
| **Notify after** | Creating new worktrees. Large refactors. Dependency bumps inside allowlisted registries. |
| **Approve before** | `git push` anywhere. PR creation. New network domain. New dependency or lifecycle script. Writes outside the workspace. Any credential use. Cloud spend above budget. Deleting more than N files or X MB. Changing agent policy, schemas or the allowlists. Installing any skill or MCP server. Sending email or messages. GUI control of any app. |
| **Forbidden** | `sudo`. Editing LaunchDaemons. Reading `~/.ssh`, Keychain, browser profiles, Mail or Messages stores. Financial sites. Force-push to protected branches. Disabling or truncating logs. Egress to a non-allowlisted host. |

**Controls.**
- Hash-chained audit log, written only by the conductor.
- VM CPU and memory caps (flags per `container run --help`).
- Per-task wall-clock, token and step limits.
- A dedicated APFS volume with a quota for agent scratch.
- Git safeguards: branch protection on the remote, no push credentials inside VMs, destructive commands matched by policy.
- **Treat all fetched content as untrusted data.** Never let it become instructions. Quarantine it from memory.
- **Supply chain.**
  - The LiteLLM compromise exfiltrated credentials via a malicious PyPI release.
  - Pin versions and hashes.
  - Install harnesses with lifecycle scripts disabled (Pi's own install command does this).
  - Review every MCP server.

## I. Installation plan

Commands are as I understand current docs. Flag names drift (OpenCode shows both `--auto` and `--dangerously-skip-permissions` across versions), so check `--help` first.

**Phase 0: host hardening** (as admin)
```bash
sudo sysadminctl -addUser agent -fullName "Agent" -password - -home /Users/agent   # standard user, NOT admin
sudo pmset -a sleep 0 disksleep 0 womp 1 autorestart 1
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install uv node jq sqlite tailscale
sudo brew services start tailscale && sudo tailscale up --hostname=mini
```
*Test:* reboot, confirm Tailscale and SSH return with no login. *Rollback:* `pmset -a restoredefaults`.

**Phase 1: minimal working system**
```bash
brew tap jundot/omlx https://github.com/jundot/omlx && brew install omlx
sudo sysctl iogpu.wired_limit_mb=24576
omlx serve --model-dir /Users/agent/models \
  --paged-ssd-cache-dir /Volumes/lab-ext/omlx-cache --hot-cache-max-size 8%
curl -s localhost:8000/v1/models
```
- Download an MLX 4-bit mixed Qwen3.8-27B with the MTP head kept, and an MLX ~3.5-bit Qwen3.6-35B-A3B, via oMLX's downloader. Verify exact repo IDs there.
- **Measurement gate.** On both models, record decode and prefill at 1K, 8K and 32K, peak memory, 1/2/4-stream batching, and MTP on versus off. Compare against section C. If the 35B-A3B delivers under 35 tok/s, reconsider the plan.
- *Failure modes:* thermal throttling (check `powermetrics`), model loads past the wired limit. *Rollback:* `brew uninstall omlx`.

**Phase 2: autonomous coding**
- Install OpenCode per opencode.ai, then `opencode serve --hostname 127.0.0.1 --port 4096` with `OPENCODE_SERVER_PASSWORD` set.
- `~/.config/opencode/opencode.json`: an OpenAI-compatible provider at `http://127.0.0.1:8000/v1`, `small_model` set to the local MoE, and `permission.bash` default-deny with explicit allows. Check the exact schema in the docs.
- Apple `container`: install the signed pkg from github.com/apple/container releases, then `container system start`. Run the harness inside a VM with a copy of the worktree and egress via the proxy only.
- Bake-off: 3 repos × 3 days, MoE-first versus 27B-first, metric is accepted tasks per hour.
- *Failure modes:* tool-call parse errors (try the llama.cpp fallback), KV cache thrash. *Rollback:* delete the worktrees.

**Phase 3: research agents**
```bash
container run -d --name searxng -p 127.0.0.1:8888:8080 docker.io/searxng/searxng
uv pip install docling
```
- Build the ledger and lint. Test with 20 seeded fake citations and require 100% to be flagged.
- *Failure modes:* scholarly API rate limits (Semantic Scholar's free tier is about 100 requests per 5 minutes), so cache aggressively.

**Phase 4: memory**
```bash
uv pip install sqlite-vec
```
- Serve embeddings from oMLX. Hybrid recall via RRF.
- *Test:* a retrieval eval with 50 questions drawn from your own notes. *Rollback:* memory is a table, so drop it.

**Phase 5: multi-agent orchestration**
```bash
uv pip install dbos
```
- Implement the lease scheduler, `agent_def`, dynamic `AgentSpec`, and model-epoch batching.
- *Failure mode:* model-swap thrash. *Test:* crash-inject mid-workflow and confirm replay.

**Phase 6: 24/7.** Install the plists (below), the watchdog, and pmset settings. Test by pulling power.

```xml
<!-- /Library/LaunchDaemons/lab.conductor.plist -->
<plist version="1.0"><dict>
 <key>Label</key><string>lab.conductor</string>
 <key>UserName</key><string>agent</string>
 <key>ProgramArguments</key><array>
   <string>/Users/agent/lab/.venv/bin/python</string><string>-m</string><string>conductor</string></array>
 <key>WorkingDirectory</key><string>/Users/agent/lab</string>
 <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
 <key>ThrottleInterval</key><integer>10</integer>
 <key>StandardOutPath</key><string>/Users/agent/lab/logs/conductor.out</string>
 <key>StandardErrorPath</key><string>/Users/agent/lab/logs/conductor.err</string>
</dict></plist>
```
Add the same shape for `omlx serve`, and one running `/usr/sbin/sysctl iogpu.wired_limit_mb=24576` at load. Logs go on internal storage so a missing external drive cannot stop boot.

**Phase 7: remote access.** `tailscale serve` the dashboard, self-host ntfy, wire approvals and the stop ladder. *Test:* approve and deny from a phone on cellular. Kill the conductor from the phone.

**Phase 8: optimisation.** A/B MTP and DFlash, KV quantization levels, cloud escalation, GUI control in a Tart VM.

**Directory layout**
```
/Users/agent/lab/{conductor/,agents/,memory/(git),logs/,policy/}
/Users/agent/{models/,worktrees/}
/Volumes/lab-ext/{omlx-cache/,vm/,papers/,datasets/,backups-staging/}
```

## J. What NOT to install

- **OpenClaw, ClawHub skills, and unreviewed MCP registry servers.** Security record above.
- **LiteLLM** as a gateway. Routing is about 100 lines of policy in the conductor.
- **LangGraph, CrewAI, AutoGen** as orchestrators. They add dependencies without durability or a single-GPU scheduler.
- **Neo4j, Graphiti, vector database servers, Redis, Kafka, Kubernetes, Temporal server.** No problem here needs them.
- **Docker Desktop.** Licence and VM overhead. Apple `container` covers it.
- **vLLM, SGLang, TokenSpeed.** CUDA-oriented.
- **Dense models above about 30B, or 100B+ MoE via SSD streaming.** Single-digit or lower tok/s.
- **2-bit quants for agent loops** and **uncensored fine-tunes** as the autonomous brain. Tool-call reliability is unproven.
- **Browser extensions that reuse your logged-in session.**
- **Full Disk Access for anything agentic.**
- **Hermes's self-installing skills** in the unattended core.

## K. Upgrade path

| Hardware | Change |
|---|---|
| **64 GB (M5 Pro mini, 307 GB/s)** | Up to 64GB and 307GB/s, three Thunderbolt 5 ports with clustering. Keep both Qwen models resident, run 8-bit, 128K context, 4 to 6 concurrent streams. Drop epoch swapping. |
| **96 to 128 GB+ (Mac Studio M5 Max/Ultra)** | The M5 Ultra offers up to 1.2TB/s. Larger MoE models (gpt-oss-120b class at about 65 GB, Qwen3-Coder-Next 80B-A3B). The dense 27B becomes fast. |
| **Dedicated GPU server** | vLLM/SGLang with Qwen3.8-27B FP8 and 10 to 50 streams. Keep the Mac as the control plane, sandbox host and memory store. The conductor already speaks HTTP, so only the endpoint changes. |

**Cloud tier (optional, section "Cost").**
- DeepSeek V4.1 Flash is $0.15/$0.60 per million tokens off-peak and open-weight (MIT).
- Claude Haiku 5.5 is $0.10/$0.50 up to 100K tokens, and Opus 5.5 is $4/$20 and Sonnet 5.5 $2/$10.
- Prices come from secondary aggregators. Confirm at platform.claude.com/docs/en/about-claude/pricing and DeepSeek's docs.
- Use cloud only for opted-in projects with redacted context, and cap spend per task.
- Local is better for private code, bulk loops and anything that runs overnight. Cloud is worth it for a hard bug after two failed local cycles, or for final synthesis on public-source research.

---

## What I could not verify
1. Any independent M6 benchmark. All speeds are projections.
2. MTP and DFlash behaviour on M6's GPU.
3. oMLX's stability over weeks of unattended running.
4. Qwen3.8's tool-parser behaviour inside oMLX versus llama.cpp. This is your first-week test.
5. The exact `container`, OpenCode permission and oMLX flags. Check `--help`.
6. DBOS's licence and which macOS Tailscale builds include the SSH server.
7. Whether Apple's Full Disk Access changes will affect agent CLIs, since no mechanism or date was given.

---

## Sources

**Hardware and platform**
- [S] https://daringfireball.net/linked/2026/08/25/m6-and-m5-ultra-chips
- [S] https://www.freepressjournal.in/amp/tech/apple-launches-new-mac-mini-with-m6-chip-days-before-iphone-18-pro-event
- [S] https://nextrift.com/?p=44146
- [S] https://levelup.gitconnected.com/apple-says-the-mac-mini-m6-is-4-8x-faster-at-ai-the-number-that-actually-matters-went-up-42-6aa2a8be9b50
- [S] https://www.mindstudio.ai/blog/m6-mac-mini-local-ai-performance
- [S] https://towardsai.net (via pub.towardsai.net/is-a-16gb-mac-mini-enough-for-local-llms-m6-2026-efd2a80ca3d1)
- [S] https://localaimaster.com/blog/mac-memory-pressure-local-llm
- [S] https://macrumors.com/2026/10/02/apple-announces-macos-full-disk-access-changes
- [S] https://blakecrosley.com/blog/macos-full-disk-access-ai-agents
- [S] https://www.it-connect.tech/apple-container-getting-started-with-macos-containers/

**Models**
- [P] https://huggingface.co/Qwen/Qwen3.8-27B
- [P] https://github.com/QwenLM/Qwen3.8
- [P, mirror] https://huggingface.co/Prince-1/Qwen3.6-27B, https://huggingface.co/qqceqqq/Qwen3.6-35B-A3B
- [P] https://www.deepmind.google/models/gemma/gemma-4
- [P] https://catalog.ngc.nvidia.com/orgs/nim/nvidia/models/nemotron-3.5-lightning
- [P] https://www.poolside.ai/blog/laguna-a-deeper-dive
- [S] https://aiweekly.co/node/9634, https://www.sebastianraschka.com/blog/2026/muse-glimmer-30b-architecture-notes.html
- [P] https://jina.ai/news/jina-embeddings-v5-text-distilling-4b-quality-into-sub-1b-multilingual-embeddings/

**Inference engines and benchmarks**
- [P] https://omlx.ai (and README mirrors on github.com/docxology/omlx)
- [C] https://omlx.ai/benchmarks/lljizegh, https://omlx.ai/benchmarks/txulyyft, https://omlx.ai/benchmarks/s3tk1giz, https://omlx.ai/benchmarks/tnnsywm9
- [C] https://huggingface.co/datasets/RaynarDM/apple-silicon-llm-benchmarks
- [C] https://github.com/jundot/omlx/discussions/2750
- [S] https://huggingface.co/npario/Qwen3.8-27B-MTPLX-Optimized-Quality
- [S] https://codepick.dev/en/guides/qwen3-27b-mac-local/
- [S] https://levelup.gitconnected.com/ollama-mlx-nearly-doubles-llm-speed-on-your-mac-58-to-112-tok-s-and-your-old-models-get-none-of-fd1a9ec531fb
- [S] https://bestllmfor.com/guides/mlx-local-llm-apple-silicon/
- [S] https://reddit.sentinel-team.org/posts/1w172j3/snapshots/2026-09-04T21%3A20%3A12.3645Z
- [S] https://github.com/chronicblondiee/pi-agent-config
- [S] https://github.com/bstnxbt/dflash-mlx/wiki

**Harnesses, security, ops**
- [P] https://opencode.ai/docs/cli/
- [P] https://github.com/NousResearch/hermes-agent
- [P] https://lmstudio.ai/blog/claudecode
- [S] https://pinggy.io/blog/best_open_source_cli_coding_agents/
- [S] https://www.tencentcloud.com/techpedia/147665 (system-prompt sizes)
- [S] https://winder.ai/ai-agent-harness-comparison/
- [S] https://innfactory.ai/en/ai-harness/pi/
- [S] https://www.techradar.com/pro/best-hardware-options-for-deploying-openclaw
- [S] https://vuln.today/cve/CVE-2026-27487
- [S] https://letsdatascience.com/news/openclaw-faces-security-risks-despite-ecosystem-growth-e0b69cf2
- [S] https://www.infralovers.com/blog/2026-02-15-sandboxing-claude-code-macos/
- [S] https://github.com/fishman/awesome-agent-sandbox
- [S] https://www.morphllm.com/docker-sandbox
- [S] https://hometechops.com/mac/mac-mini-home-server-setup, https://clawhub.ai/alexbloch-ia/skills/mac-mini, https://skillsmp.com/fr/creators/soulmachine/skills/mac-mini-as-headless-server
- [S] https://lobster.shahine.com/guides/remote-access/, https://github.com/Keeeeeeeks/opencode-dashboard
- [S] https://github.com/EfeDurmaz16/agentbox, https://github.com/Isco0819/push-bridge
- [S] https://www.testmuai.com/blog/playwright-mcp/, https://dev.to/ahab_indieseek/chrome-devtools-mcp-for-ai-coding-agents-a-practical-debugging-workflow-4m48
- [S] https://www.fredmiranda.com/forum/topic/1898118/0, https://forums.macrumors.com/threads/external-ssds-how-practical-are-they-in-reality.2488366/

**Research, memory, orchestration, cost**
- [P] https://arxiv.org/pdf/2603.03299, https://arxiv.org/abs/2602.15871, https://www.alphaxiv.org/abs/2607.18360.md
- [P] https://github.com/datalab-to/marker/releases
- [S] https://gmagazine.it.com/?p=566
- [S] https://www.digitalapplied.com/blog/open-source-deep-research-agents-2026-guide
- [P] https://docs.dbos.dev/ai/ai-quickstart
- [S] https://forkast.news/?p=131065
- [S] https://clawdocs.org/guides/memory-systems, https://pypi.org/project/memoirs/
- [S] https://www.respan.ai/blog/best-litellm-alternatives, https://vercel.com/i/litellm-alternatives
- [S] https://letsdatascience.com/blog/claude-haiku-5-5-cut-prices-90-prompts-over-100k-pay-5x (Anthropic pricing page cited there, not fetched by me: https://platform.claude.com/docs/en/about-claude/pricing)
- [S] https://www.yottalabs.ai/post/deepseek-v4-1-flash-pricing-specs-v4-pro-routing-2026, https://datanorth.ai/news/deepseek-releases-deepseek-v4-1-flash
- [S] https://en.wikipedia.org/wiki/Reasoning_model (Kimi agent swarm)

## Reasoning trace (not shown to raters)

Claude responded: Model: Claude Sonnet 5.5.
Checking the date reference before starting the research.
Checking the date reference before starting the research.

Model: Claude Sonnet 5.5. Knowledge cutoff: end of June 2026. Web search: on, and I’m researching now. One discrepancy to flag: your brief says today is 31 Aug 2026, but my session date is 14 Oct 2026. I’m treating 14 Oct 2026 as current.

Used Tried a tool that isn't available, searched the web, read 2 pages

Used Tried a tool that isn't available, searched the web, read 2 pages





5 hours ago

## Run notes

claude.ai incognito chat (no history or memory), model menu Sonnet 5.5, Effort High; the menu showed
"Sonnet 5.5 High". Connectors were switched off in the composer menu; the composer has no web-search
switch, and Claude searched the web by itself. Send time 2026-10-14T02:40:58.757Z (browser clock, read right after
sending). Chat: https://claude.ai/chat/57c2e3eb-c69b-43a6-913b-2e48dbfbc8c4?incognito (incognito chats are not kept in history).
Operated by the assistant (Claude, via the Claude in Chrome extension) in the author's signed-in browser,
at the author's request; the runs were opened in separate tabs and sent in manifest order without waiting
for earlier answers. The app turns long pastes into an attachment, so the prompt was inserted as plain
text in eight line-aligned pieces from one clipboard paste and checked against the original (1,782 words,
same text) before sending. Answer copied with the app's Copy button (it includes any short lines the model
wrote before its searches) and written verbatim from the clipboard; the reasoning trace is the visible
process panel (step summaries and search queries) copied from the page text.
During generation the app paused with "Claude wants to fetch a web page". The author chose "Allow
once" and the assistant clicked it about four hours later (the session had paused); the answer then
finished. The other runs read web pages without asking.
