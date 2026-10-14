---
run_id: claude__fast__p1-v1__r1
set: main
family: claude
vendor: Anthropic
mode: fast
native_label: claude.ai, Sonnet 5.5, Effort Low
channel: web
model_requested: Anthropic chat app, claude.ai, Sonnet 5.5, Effort Low
model_returned: Sonnet 5.5 (app model menu, Effort Low)
prompt_id: p1-v1
prompt_sha256: ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0
replicate: 1
date_stamped: '2026-10-14T02:41:35+00:00'
date_run: '2026-10-14T02:41:35+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

I'll check the current state of the hardware and ecosystem first, starting with whether the M6 Mac mini and its specs are verifiable.

Hardware verified: M6 at 170 GB/s, 32 GB max, macOS 27. Now the model and runtime landscape.

**Model:** Claude Sonnet 5.5. **Knowledge cutoff:** end of June 2026. **Browsing:** ON, but limited to 3 searches (hardware, local models, harnesses) with no page fetches. Memory, research tooling, sandboxing, remote access, and always-on operation were **not** researched this session. Those sections come from my training and are marked *[unverified]*. I'm an Anthropic model, so discount my view of Claude Code accordingly.

**Date conflict:** your prompt says 31 Aug 2026, my session clock says 14 Oct 2026. I used Oct 14, which matches the search results.

## Decisions at a glance

| Layer | Pick |
|---|---|
| Inference engine | MLX-based server (benchmark Rapid-MLX against `llama-server`), one resident process |
| Primary model | Qwen3.8 27B dense, 4-bit MLX, 2 slots at 32K |
| Bulk/cheap model | Benchmark a ~9B (Ornith-1.0-9B) and a MoE (Qwen 3.6 35B-A3B) against the 27B on your own tasks |
| Coding harness | OpenCode (MIT), headless server mode |
| Orchestrator | Thin custom Python supervisor over a SQLite queue |
| Memory | Markdown in git, plus one SQLite file (FTS5 + sqlite-vec) |
| Research | Custom claim-ledger pipeline with API-verified citations |
| Isolation | Dedicated non-admin macOS user, per-task git worktrees, egress allowlist, VM for risky work |
| Remote | Tailscale, ntfy push, small tailnet-only dashboard |
| Always-on | `launchd` LaunchDaemons, `pmset`, UPS |
| Cloud | Optional, capped: hard planning and review only |

## 1. Local inference

**Hardware (verified).** The M6 has a 12-core CPU and 12-core GPU, with a Neural Accelerator in every GPU core (per Apple's launch coverage). Base memory is 16 GB, configurable to 32 GB, at up to 170 GB/s (per a launch report). Apple claims prompt processing in LM Studio is up to 4.8x faster than on the M4 (per a launch report). That is a vendor claim, but it matters because agentic coding is prefill-heavy.

**The bandwidth ceiling.** Decode is memory-bound.
- Qwen3.8 27B is dense and about 16-19 GB at 4-bit (per a self-hosting guide).
- That gives a theoretical single-stream ceiling of 170/18.3, about 9 tok/s. Expect roughly 6-7 in practice. This is my arithmetic, not a benchmark, so measure it.
- Overnight, one dense stream yields only about 200K output tokens over 8 hours.
- The levers are continuous batching, which amortizes weight reads across slots, and smaller or sparse models.

**Model candidates.**
- **Qwen3.8 27B** is the consensus pick for 32 GB. Several October 2026 roundups name it first (one lists it for 32 GB+ Macs). It is Apache 2.0 and has an MLX build (same guide). A 4-bit build at 32K context is 18.29 GB (per one measurement).
- **Context:** Qwen 3.6 27B on 32 GB was reported to reach about 128K, with the full 262K needing 48 GB (a Kilo comparison). I would cap at 32-48K per slot anyway.
- **Does not fit:** Qwen3.8-Flash-Next (125B, 6B active) needs 96-114 GB at 4-bit (same guide).
- **Candidate worker model:** Ornith-1.0-9B is reported at 69.4% on SWE-Bench Verified in a 5.6 GB Q4 build (a single Hugging Face card from a third-party tune). Treat that as an unverified claim and test it on your own tasks. If it holds, its bandwidth ceiling is about 3x the 27B's.
- **MoE alternative:** Qwen 3.6 35B-A3B fits 32 GB (per the same Kilo comparison). With about 3B active parameters, its decode ceiling is several times the dense model's. I couldn't verify a Qwen3.8 MoE that fits.

**Engine.** Community sources report MLX is about 2x faster than Ollama on Mac (secondary). MLX-LM's built-in server is described as very limited, while llama.cpp has broader model support (per a Mac local-AI guide). Rapid-MLX advertises a local backend for agents including OpenCode and Claude Code (its README, a vendor claim). I could not verify its batching behavior or maturity.
- **Decision:** Run a 2-hour bake-off between Rapid-MLX and `llama-server -np 2` on your task set. The metrics are aggregate tok/s at 2 concurrent streams, prefill latency with a warm cache, and crash count. Ship the winner.
- **Prefix caching:** OpenCode-derived tools warn that local setups often lack prompt caching (per Kilo's local-model docs). Choose an engine that has it, because re-prefilling a 20K system and repo context every turn will dominate your latency.

## 2. Agent runtimes

OpenCode is MIT-licensed, provider-agnostic across 75+ providers, and had 212k stars at v1.19.0 on Oct 11 (per a roundup). The repo moved to `anomalyco/opencode`, which breaks old `sst/opencode` references (same source).
- Per-agent model and permission config is defined in markdown or JSON, with MCP, AGENTS.md, and the shared SKILL.md standard (per Firecrawl).
- It documents three local paths: Ollama, LM Studio, and `llama-server`, with `build` (full access) and `plan` (read-only) built-in agents (per MarkTechPost).

Claude Code has the deepest hook system and fleet tooling, but it is closed source (per ExplainX) and Claude-only (per Morph). It cannot be your offline default.

**Decision:** Use OpenCode as the per-task worker. Write your own supervisor around it, because none of the harnesses I surveyed give you a durable queue, budget enforcement, and a global inference scheduler in one place. Don't adopt a general multi-agent framework. LangGraph, CrewAI, and AutoGen overlap with your supervisor and add state you'd have to reconcile *[unverified, from priors]*.

## 3. Multi-agent architecture

Separate four things:
- **Logical agent:** a row in `agent_defs` (role prompt, tool allowlist, model tier, budgets, permissions). Cost: zero RAM.
- **Task:** a row in the queue, with status, dependencies, a budget, and a workspace.
- **Runner:** an OpenCode session process (budget about 0.25 GB each, unverified), alive only while a task runs.
- **Inference slot:** the scarce resource, 2 slots on the 27B.

So 100+ agents are just definitions, and concurrency is governed by semaphores. Planning is local, so it occupies a slot. Suggested limits:
- LLM slots: 2
- Tool slots (builds, tests): 3
- Browser: 1
- Hard cap on concurrent runner processes: 4

Runners mostly wait on tools or slots. **Hierarchy:** use coordinator/worker with depth limited to 2. Swarm-style peer chatter burns tokens you don't have.

**Dynamic spawning.** A planner emits an `AgentSpec` JSON. The supervisor validates it against a schema, and the spec can only pick from a fixed tool catalog. A child's permissions must be a subset of its parent's (capability attenuation). Anything requesting new tool scope goes to approval.

## 4. Coding agents

OpenCode on Qwen3.8 27B is the default. Expect model quality to be the bottleneck, not the harness. Each task gets its own git worktree and runs plan → implement → test → self-review in loops. A coding task is "done" only when the supervisor's own test command exits 0, never when the agent says so. For the hardest 10-20% of tasks, escalate to a cloud model through the same harness. It is a one-line provider switch in OpenCode.

## 5. Research agents *[unverified, from priors]*

The architecture does the work, not a product:
1. **Discovery:** OpenAlex, Semantic Scholar, arXiv, and Crossref APIs (free), plus a web search API for non-academic sources.
2. **Ingest:** store PDFs on the external SSD, extract text (PyMuPDF-class tooling), and chunk with page and offset spans.
3. **Claim ledger (SQLite):** `claim`, `evidence(source_id, span_start, span_end, verbatim_text)`, `verdict`.
4. **Hard invariant:** a claim reaches a report only if every cited span exists in stored source text (exact or normalized substring match) and the DOI/arXiv ID resolves via API to matching title and authors. Fabricated citations then fail mechanically instead of relying on the model's honesty.
5. **Verification pass:** a separate agent attempts to refute each claim using only retrieved text. Contradiction detection is pairwise NLI-style prompting over claims sharing entities.
6. **Reports:** generated from the ledger, never free-written.

## 6. Persistent memory

**Start with:** Markdown files in a git repo (`memory/global/`, `memory/projects/<name>/`: decisions, ADRs, run logs) plus one SQLite file with FTS5 and `sqlite-vec`. That covers episodic (run logs), semantic (notes with embeddings), and project and global scopes.

**Add later, only on evidence:** a reranker if retrieval precision is poor. A knowledge graph only if you hit multi-hop queries FTS plus vectors can't answer. Skip Postgres and dedicated vector DBs. At this scale they are pure operational cost.

## 7. Computer control and security

**Isolation tiers.**
- **Tier 0, default:** a dedicated standard macOS user `agent` with no admin rights, its own home, and an empty keychain. Your personal data stays in your own account with `chmod 700` and no ACLs for `agent`.
- **Tier 1, per task:** a git worktree under `/Users/agent/work`, with the repo cloned from a local bare mirror.
- **Tier 2, risky:** untrusted code, dependency installs, and browser automation inside a Linux VM or container. Candidates are Lima or Apple's container tooling. I did not verify their status on macOS 27.
- **Network:** per-user egress allowlist via a local proxy plus `pf` rules. Default deny except the inference loopback, package registries, git remote, and search APIs. Prompt-injection from fetched pages is the main threat, and egress control is the mitigation that still works when the model is fooled.

**Secrets:** none ambient. Use per-task scoped tokens (fine-grained, repo-limited, expiring) injected via environment into one process. Never grant a general GitHub token, SSH key, cloud credential, or financial account.

**Approval matrix.**

| Fully autonomous | Requires approval | Never allowed |
|---|---|---|
| Read/write inside the task worktree; run tests, builds, linters; branch/commit/push to `agent/*`; read-only web; allowlisted package installs in a VM | Merge to main or tag; touching files outside the worktree; new network domains; new dependencies with install scripts on host; spawning agents with new tool scope; spend over budget; GUI/computer-use outside the sandbox | `sudo`; force-push; `rm -rf` outside the workspace; reading your home, keychain, or browser profiles; credential changes; sending email or messages as you; financial sites; modifying the supervisor, its config, or its own permissions |

**Git safeguards:** server-side branch protection on main; agents push only to `agent/*`; reflog and a nightly bundle backup.

**Runaway protection:** per-task wall-clock limit (default 2h), token limit, tool-call limit, and a repeat-loop detector (same tool call plus same output hash 3x aborts). Add a global daily token and spend cap, with `ulimit` and a RAM watchdog. Every tool call is logged to an append-only JSONL audit file the agent can't write.

**Kill switch:** the supervisor checks `/var/agent/KILL` before every dequeue and every tool call. A phone button creates it and runs `launchctl bootout` on the agent services.

## 8. Always-on *[unverified on macOS 27]*

- **Services:** LaunchDaemons with `UserName=agent`, `KeepAlive=true`, and `ThrottleInterval`. Run `inference`, `supervisor`, `dashboard`, and `watchdog` as separate jobs. LaunchAgents only run with a logged-in session, and you don't need a GUI session for headless work.
- **Power:** `sudo pmset -a sleep 0 disablesleep 1 autorestart 1 womp 1`, plus `caffeinate -s` inside the supervisor as a belt-and-suspenders measure. Put the Mac on a UPS.
- **FileVault tradeoff:** with FileVault on, an unattended reboot after a power loss stops at the unlock screen. My recommendation is to keep FileVault on and use the UPS. Verify whether macOS 27 supports remote unlock before relying on it.
- **Crash recovery:** the task queue is the source of truth. On start, the supervisor requeues any `running` task whose heartbeat is older than 90 s, resuming from the last checkpoint (the git commit plus a notes file in the worktree).
- **Watchdog:** a 60 s cron job checks inference health (a 1-token completion), memory pressure, and disk. It restarts the engine and alerts via ntfy.

## 9. Remote access *[unverified]*

Tailscale (SSH enabled, ACL-restricted to your phone and laptop) plus no public ports at all. Run a small FastAPI/htmx dashboard bound to the tailnet interface only, for queue, logs, approvals, and a kill button. Use ntfy (self-hosted or hosted) for push notifications, with approval buttons whose actions carry signed single-use tokens. Authentication relies on tailnet identity plus a second factor on approvals.

## 10. Storage

| Internal 512 GB | External 1 TB |
|---|---|
| OS, apps, ~50 GB active models, SQLite DBs and queue, active worktrees, build caches, logs (7-day) | Model library (cold), papers/PDFs, datasets, log archive, backups |

The M6's internal SSD is claimed to be up to 2x faster than the prior generation (per a retailer listing quoting Apple). Keep anything latency-sensitive or write-heavy off the external drive, because a USB or Thunderbolt dropout mid-write corrupts SQLite and git state. The external drive is a single failure domain next to the Mac. Add an encrypted offsite copy (restic) of `memory/` and the DBs if the work matters.

## Market comparison (compact)

| Category | Best overall | Best for this Mac | OSS | Lightest | Most stable | Cutting edge | **Use** |
|---|---|---|---|---|---|---|---|
| Inference | llama.cpp / MLX | MLX | both | llama.cpp | llama.cpp | Rapid-MLX | Bake-off, then pick |
| Harness | Claude Code | OpenCode | OpenCode | Pi/Aider | Aider / OpenCode | Claude Code | OpenCode |
| Orchestration | custom | custom | custom | SQLite queue | SQLite | none | Custom |
| Memory | SQLite+git | same | same | files | SQLite | graph | SQLite+git |
| Remote | Tailscale | Tailscale | WireGuard | SSH | Tailscale | none | Tailscale+ntfy |

These rankings rest on partial verification and secondary sources, so treat them as hypotheses until your bake-off.

## A. Stack

| Layer | Recommended | Alternatives | Why |
|---|---|---|---|
| Models | Qwen3.8 27B 4-bit | 9B worker, MoE, Gemma 4 12B | Best reported quality that fits |
| Engine | Rapid-MLX or llama-server | LM Studio, Ollama | Batching and prefix cache decide it |
| Harness | OpenCode | Claude Code (cloud), Pi, Goose | Local, MIT, per-agent models/permissions |
| Queue | SQLite WAL | Redis, Temporal | No extra daemons |
| Memory | git + SQLite FTS5/vec | Postgres, graph DB | Minimal infrastructure |
| Remote | Tailscale + ntfy | Cloudflare Tunnel | No public ports |
| Isolation | user + worktree + VM | Docker | Cheap, strong boundaries |

## B. Architecture

```
 Phone/Laptop --(Tailscale)--> Dashboard + ntfy + SSH
                                     |
                         [Supervisor daemon (launchd)]
                          budgets | KILL | audit log
                                     |
              [Orchestrator/Planner] --> SQLite task queue (WAL)
                                     |
              [Worker pool: <=4 OpenCode runners, semaphores]
                 |            |             |
          git worktrees   VM sandbox   research pipeline
                 \            |             /
                  [Model router: tier -> endpoint]
                     |                  |
          [Local MLX/llama server]   [Optional cloud, capped]
           27B (2 slots) + embedder
                                     |
              [Memory: markdown+git, SQLite FTS5/vec]
```

## C. Resources (32 GB)

| Item | GB |
|---|---|
| macOS + daemons | 5-6 |
| Qwen3.8 27B 4-bit weights | ~18.3 |
| KV cache, 2 x 32K | 2-4 (measure) |
| Embedder | ~0.6 |
| Supervisor, DB, runners | ~1.5 |
| Headroom (builds, browser, cache) | ~2-3 |

This is tight. The macOS GPU wired-memory limit may need raising via `iogpu.wired_limit_mb` *[unverified default]*. Storage: internal about 150 GB used, external about 200 GB at first.

## D. 100+ logical agents

See section 3. The key mechanics are definitions as data, a 2-slot LLM semaphore, short-lived runners, and queue-driven scheduling. Sequential execution is the right default for anything that touches the same repo.

## E. Model strategy

| Task | Model |
|---|---|
| Planning | Local 27B in thinking mode; cloud for ambiguous, high-stakes plans |
| Coding / debugging | 27B (thinking on for debugging) |
| Research / synthesis | 27B over retrieved spans; cloud optional for final polish |
| Summarization / classification | 9B or small model if the bake-off supports it, else 27B with short outputs |
| Embeddings | Small dedicated embedder (verify current options) |

## F. 24/7

See section 8. Durable queue, heartbeats, requeue-on-stale, watchdog, UPS, and a morning digest pushed via ntfy.

## G. Remote control

See section 9. Verbs: `submit`, `status`, `logs`, `approve/deny`, `pause`, `kill`.

## H. Security

See section 7. Broad capability comes from a sandboxed user and VM, while secrets and your personal data simply aren't reachable.

## I. Installation

Commands marked ✓ were seen in search results. The rest are from training, so verify them.

```bash
# Phase 1: minimal system
brew install uv git gh sqlite
brew install rapid-mlx                      # ✓ from the Rapid-MLX README
ollama launch opencode --model qwen3.8:27b  # ✓ from a self-hosting guide; the qwen3.8:27b-mlx tag runs on MLX
# Phase 6/7
sudo pmset -a sleep 0 disablesleep 1 autorestart 1
brew install --cask tailscale
sudo sysadminctl -addUser agent -password - -home /Users/agent   # standard user, no admin
```

**Roadmap with tests and rollback:**
1. **Minimal:** the engine serving the 27B, OpenCode pointed at it. Test: one repo task that ends with a green test run. Rollback: stop the service.
2. **Autonomous coding:** worktrees plus the supervisor's test gate. Test: 10 benchmark tasks, pass rate recorded. Failure modes: false "done" claims, loops.
3. **Research:** claim ledger and citation verifier. Test: seeded fake citations must be rejected 100%.
4. **Memory:** git plus SQLite, with retrieval evals on past decisions.
5. **Multi-agent:** semaphores and AgentSpec validation. Test: 20 queued tasks, RAM stays flat.
6. **24/7:** LaunchDaemons. Test: `kill -9` the engine and pull the power, confirm recovery.
7. **Remote:** Tailscale, ntfy, dashboard. Test: approve and kill from cellular.
8. **Optimization:** the model bake-off, prefix caching, and the 9B-worker profile.

Directory layout: `/Users/agent/{work,memory,queue.db,logs}`, with the model library and archives on the external drive.

## J. What not to install

- Kubernetes, Redis, Celery, Temporal: more daemons than you can afford in 32 GB.
- Postgres or dedicated vector DBs: SQLite suffices.
- General multi-agent frameworks as the core: they duplicate the supervisor.
- Running Ollama and a second engine side by side: pick one engine.
- Claude Code as the offline default: closed source and Claude-only.
- Unvetted community MLX "abliterated" or custom tunes as primary models: your own evals decide.

## K. Upgrade path

- **64 GB:** 8-bit 27B or a stronger quantized model, more slots, and a resident second model. The M5 Pro Mac mini goes to 64 GB at 307 GB/s (per a launch report), which roughly doubles decode ceilings.
- **96-128 GB:** Qwen3.8-Flash-Next at 4-bit (96-114 GB) becomes feasible.
- **Dedicated GPU/server:** move inference off the Mac and keep it as the supervisor and tool host. The router and OpenAI-compatible endpoints make that a config change.

## Sources

Primary-source verification is weak here, so please read these as secondary.
- https://www.ldlc.com/en/product/PB00751971.html (secondary, retailer quoting Apple)
- https://guru3d.com/story/apple-m6-2nm-processor-debuts-with-12core-cpu-12core-gpu-and-dual-neural-engines/ (secondary)
- https://fstoppers.com/gear/apples-new-mac-mini-gets-m6-m5-pro-and-genlock-video-work-904276 (secondary)
- https://t2online.in/tech/tech-news/apple-mac-mini-launches-with-m6--m5-pro-chips/2007528 (secondary)
- https://www.igeeksblog.com/mac-mini-m6-m5-pro-price-specs-release-date/ (secondary)
- https://pinggy.io/blog/best_open_source_self_hosted_llms_for_coding/ (secondary)
- https://www.microcenter.com/site/mc-news/article/best-local-llms-8gb-16gb-32gb-memory-guide.aspx (secondary)
- https://www.developersdigest.tech/best/local-models (secondary)
- https://blog.kilo.ai/p/the-best-local-coding-models-for (secondary)
- https://huggingface.co/rafw007/ornith-1.0-9b-claude-coder (secondary, third-party model card)
- https://github.com/chethanuk/Rapid-MLX (primary repo README, vendor claims unverified)
- https://github.com/dmitryryabkov/local-ai-mac (secondary)
- https://github.com/msb-msb/awesome-local-ai (secondary)
- https://pinggy.io/blog/top_cli_based_ai_coding_agents/ (secondary)
- https://www.marktechpost.com/2026/09/18/best-open-source-agent-harnesses-for-local-llms-in-2026/ (secondary)
- https://www.firecrawl.dev/blog/best-ai-coding-agents (secondary)
- https://www.morphllm.com/comparisons/opencode-vs-claude-code (secondary)
- https://explainx.ai/blog/top-10-open-closed-source-agent-harnesses-2026 (secondary)

**Biggest gaps before you build from this:**
1. No official Apple spec page, OpenCode docs, or MLX/llama.cpp release notes were read.
2. All throughput figures are my bandwidth arithmetic or vendor claims. Only your bake-off gives real numbers.
3. Sandboxing, `launchd`, FileVault, and Tailscale details were not verified on macOS 27.

I can run a second research pass on those three if you want it.

## Reasoning trace (not shown to raters)

Claude responded: I'll check the current state of the hardware and ecosystem first, starting with whether the M6 Mac mini and its specs are verifiable.
Preparing a large research report amid a date discrepancy.
Preparing a large research report amid a date discrepancy.

I’ll check the current state of the hardware and ecosystem first, starting with whether the M6 Mac mini and its specs are verifiable.

Searched the web

Searched the web






4 hours ago

## Run notes

claude.ai incognito chat (no history or memory), model menu Sonnet 5.5, Effort Low; the menu showed
"Sonnet 5.5 Low". Connectors were switched off in the composer menu; the composer has no web-search
switch, and Claude searched the web by itself. Send time 2026-10-14T02:41:38.516Z (browser clock, read right after
sending). Chat: https://claude.ai/chat/d5bde6a7-bc48-4044-bf83-59f999046fe0?incognito (incognito chats are not kept in history).
Operated by the assistant (Claude, via the Claude in Chrome extension) in the author's signed-in browser,
at the author's request; the runs were opened in separate tabs and sent in manifest order without waiting
for earlier answers. The app turns long pastes into an attachment, so the prompt was inserted as plain
text in eight line-aligned pieces from one clipboard paste and checked against the original (1,782 words,
same text) before sending. Answer copied with the app's Copy button (it includes any short lines the model
wrote before its searches) and written verbatim from the clipboard; the reasoning trace is the visible
process panel (step summaries and search queries) copied from the page text.
