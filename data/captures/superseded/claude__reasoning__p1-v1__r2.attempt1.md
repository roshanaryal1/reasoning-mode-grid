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
date_stamped: '2026-10-14T02:39:03+00:00'
date_run: '2026-10-14T02:39:03+00:00'
run_by: Roshan Aryal
interface: web app, fresh chat, signed in, no custom instructions, memory off
---

## Final answer

STOPPED BY USAGE LIMIT. The app stopped this answer with "Stopped by a usage limit" (the
author's claude.ai 5-hour limit was reached while ten chats ran at once). The partial page text
as shown, including process lines, is kept below for the record.

Claude responded: I'll start by verifying the hardware and the current ecosystem state before designing anything.
Resolving a date discrepancy before starting the research.
Resolving a date discrepancy before starting the research.

I’ll start by verifying the hardware and the current ecosystem state before designing anything.

Searched the web

Searched the web

Model: Claude Sonnet 5.5 (Anthropic)
Knowledge cutoff: end of June 2026
Browsing: ON (about 35 searches this session, no page fetches)

Three caveats first:

Date: your note says 31 Aug 2026, but the system date is 14 Oct 2026. I used 14 Oct, since the M6 mini only opened for pre-order with delivery from 22 September. 
t2online
Evidence quality: most local-performance numbers are secondary (community posts, review summaries). Benchmark scores for new models are vendor-reported. I tag my own extrapolations [E] and items to confirm at install [V]. Where I found no source, I say so.
Disclosure: I’m made by Anthropic. I still rank Claude Code below OpenCode as your primary harness, for technical reasons given in section 2. Weigh that accordingly.
Decisions at a glance
Layer	Pick	Runner-up	Confidence
Inference server	oMLX (pinned version, prebuilt kernels)	mlx-lm server, llama.cpp Metal	75%
Resident heavy model	Qwen3.8-27B, 4-bit mixed, MTP head kept	Qwen3.6-27B (stability fallback)	70%
Batch-window model	Qwen3.6-35B-A3B, 4-bit (swapped in off-hours)	Gemma 4 26B-A4B	55%
Small/utility model	Qwen3.5-4B or 9B, 4-bit; Qwen3-Embedding-0.6B [V]	none	65%
Coding harness	OpenCode (headless), bake-off against Pi, Codex CLI, Qwen Code	Pi	60%
Orchestrator	Custom thin supervisor: Python, SQLite WAL queue, launchd	Temporal (only if multi-node)	80%
Always-on assistant runtime	None in Phase 1. Hermes Agent only as an optional gateway after review. Avoid OpenClaw.		70%
Sandbox	Apple container (one lightweight VM per container)	Lima or vibe VMs	75%
Memory	Markdown files and SQLite FTS5, then sqlite-vec, then temporal columns	Graphiti, much later	85%
Research	Claims ledger with an identifier resolver (Crossref, OpenAlex, Semantic Scholar, arXiv), self-hosted SearXNG		80%
Remote	Tailscale (SSH and Serve), ntfy for push		85%
Cloud	Optional escalation lane, off by default, never for private data		80%
1. Local inference

Hardware facts.

The M6 mini has a 12-core CPU, 12-core GPU and 170GB/s memory bandwidth. 
smartprix
The GPU has Neural Accelerators, and the 32GB ceiling limits which models run locally. 
macstories
The 170GB/s figure applies to the 24GB and 32GB configurations; the 16GB model gets 153GB/s. 
9to5Mac
It has Thunderbolt 4, not 5, so Apple’s Thunderbolt 5 clustering is unavailable. 
camerajabber

Decode versus prefill.

Decode is bandwidth-bound: tokens per second is at most bandwidth divided by bytes read per token.
Prefill is compute-bound. A 9B Q4 llama.cpp test showed prefill of 742 tok/s on M6 versus 210 on M4, but generation only rose from 18 to about 27 tok/s [S]. 
mindstudio
Apple’s own claim is up to 4.8x faster LLM prompt processing in LM Studio versus M4. 
camerajabber
Whether oMLX and mlx-lm exploit the neural accelerators equally is unverified. This is a Phase 1 gate.

Decode ceilings for your machine.

A dense 27B at 4-bit is about 15 GiB, so the ceiling is roughly 170/16, about 10.6 tok/s.
A review of the M6 mini measured about 8-9 tok/s on Qwen3.8-27B 4-bit with plain MLX, and 16-19 tok/s with MTP [S, video-review summary]. That review also claims 26-56 tok/s from a separate engine. I don’t trust that figure. 
daily
The 8-9 tok/s result is consistent with an M5 Max table where dense 27B 4-bit decodes about 33 tok/s and the 35B-A3B MoE about 138 tok/s, scaled by the bandwidth ratio. 
github
By the same scaling, the 3B-active MoE should decode at roughly 35-45 tok/s on M6 [E].

Model candidates for 32 GB.

Model	Facts	Verdict
Qwen3.8-27B (dense VLM)	Apache 2.0, vision encoder, 262k native context, released mid-August. Vendor-reported Terminal-Bench 2.1 of 73.0 and SWE-bench Pro of 61.7, up from 63.4 and 53.5 on Qwen3.6-27B, plus selectable reasoning-effort levels. All headline numbers are Alibaba’s own, and the coding runs used the Claude Code harness. It is a hybrid Gated DeltaNet plus full-attention design, so KV cache growth is modest. It answered the same prompts in about 1,000 tokens versus 2,000-3,300 for 3.6. Testers report much better tool-call reliability than 3.6.	Primary
Qwen3.6-35B-A3B	35B total, 3B active. SWE-bench Pro 49.5 versus 61.7 for Qwen3.8-27B. Tool-call reliability reported as mixed versus strong for the dense 27B. About 22GB for the nvfp4 MLX build.	Batch windows only. At about 20-22 GB it cannot coexist with the 27B.
Gemma 4 26B-A4B	3.8B active; claimed 40-75 tok/s on 32GB Macs (older chips, so an upper bound). Needs llama.cpp with --jinja for reliable tool calls; Ollama had parser bugs.	Alternate batch model, bake-off only
Laguna-XS.2 33B	3-bit, 13.8 GB, 46.8 tok/s on a 32GB Mac, passed an OpenCode check. Quality and license are unverified.	Add to bake-off
Doesn’t fit	Qwen3.8-Flash-Next is 125B total, 6B active, plus a 51B n-gram component. MiMo-V2.6-Pro and DeepSeek-V4.1-Flash don’t fit one GPU.	Cloud only 
Qwen 3.8 27B: Specs, Hardware Requirements, and How to Run It (2026) +14

Engines.

oMLX: it provides continuous batching, a RAM+SSD tiered KV cache, multi-model serving with pin and evict, OpenAI and Anthropic APIs, embeddings and rerankers. This matters because coding agents invalidate caches constantly, and oMLX persists KV blocks to SSD so earlier prefixes can be restored. 
sourceforge
omlx
oMLX maturity: the project dates from 2026-02-13 and ships fast (0.6.3rc3 on Aug 24). Pin versions. 
jimmysong
github
oMLX operational traps:
Source installs without full Xcode silently skip the fast kernels, giving up to 30x slower prefill. Use the DMG, brew or pip wheels, and check /api/status. 
github
A hard-killed process holding a large wired model can leak wired memory until reboot, and launchd KeepAlive turns that into a jetsam crash loop. See F. 
github
Disable the experimental ANE prefill. It costs about 7 GB peak memory. 
github
mlx-lm MTP: the server uses MTP for solo requests and switches to BatchGenerator for concurrent ones. MTP and batching are alternatives. Under load you get batching throughput, not MTP speed. 
github
llama.cpp: Metal is the fallback and the best tool-call parser for Gemma 4. One test found it faster than mlx-lm on Qwen3.6, so benchmark both. 
quesma
Ollama: skip it. Open issues report /v1/chat/completions hanging for qwen3.8:27b, and it has no SSD KV tier. 
betterclaw

Required config.

Lower temperatures degrade agentic behavior on this family, so use Qwen’s recommended sampling. 
regolo
Preserve reasoning between turns. Without the right field, OpenCode silently drops reasoning. 
regolo
Cold prefill on the 27B will likely be about 100-250 tok/s [E]. One M4 Pro 64GB test read prompts at about 90 tok/s, and I scaled it. A cold 32K context therefore costs 2-5 minutes. Optimise for prefix-cache hit rate: append-only context, stable system prompt, small harness prompts. One user had to patch the chat template to keep prefix caching with Claude Code. 
huggingface
github
2. Agent runtimes and harnesses

Evidence.

OpenCode is MIT, provider-agnostic, local-model friendly (about 202k stars); Pi is MIT with local models; Codex is Apache-2.0 and sandboxed. 
pinggy
A community test estimated Claude Code’s prompt and tool schemas at about 33,000 tokens versus about 6,900 for OpenCode [S]. At 100-250 tok/s prefill, that difference is the whole game. 
tensorlake
The same review found Codex safest but slow, and Pi the benchmark surprise with almost no guardrails. 
tensorlake
Pi documents RPC, JSON events and an SDK, and added MCP support in September; OpenCode supports subagents and project rules. 
jock
Claude Code Remote Control requires a Claude.ai subscription and login, and depends on the local process staying alive. It also routes traffic through the Anthropic API. That conflicts with local-first, so it is an optional lane at most. 
seawork
letsdatascience
Hermes Agent: MIT, agent-curated persistent memory, natural-language cron, isolated subagents, a messaging gateway. It is v0.15.x, and coverage flags oversight questions around autonomous memory and scheduling. I found no independent security audit. 
github
it
OpenClaw: an audit found 512 vulnerabilities, 8 critical, with 138 flaws in 63 days, and instances found exposed on the open internet. Do not use it. 
Don’t get pinched: the OpenClaw vulnerabilities +2

Decision: a layered build, not one monolith.

No product I found gives you all three of: model-affinity scheduling over one shared GPU pool, per-task sandbox and credential policy, and acceptance-test verification gates. Those three determine useful work per hour.
Build a roughly 1-2 KLOC supervisor and run existing harnesses as stateless headless workers inside sandboxes.
Evaluate Hermes in Phase 5 as a messaging and cron front end, read-only and sandboxed, after its own review.

Bake-off protocol (Phase 2 gate).

Take 20 tasks from your own repos (failing test to fix, hidden acceptance tests).
Run OpenCode, Pi, Qwen Code, Codex CLI (local provider) and Claude Code (local Anthropic-compatible endpoint) on the same Qwen3.8-27B.
Measure pass@1, wall-clock, uncached prefill tokens, tool-error rate and loop rate. Rank by tasks passed per hour.
My prior is OpenCode and Pi above Codex and Qwen Code, with Claude Code last on this hardware [E]. Run the test anyway.
3. Multi-agent architecture

Terms:

Simultaneous model instances: impossible at scale. 100 times 15 GiB does not fit, and instances would contend for the same 170 GB/s.
Logical agent: a versioned definition (role prompt, tool allowlist, model tier, effort, budgets, memory scope). Rows or files, costing about 0 RAM.
Run: an ephemeral instantiation of a logical agent on one task.
Inference slot: a row in the engine’s continuous batch.
Worker: a sandboxed process executing tools (tests, builds, browser).

Why this works on your box:

Decode reads the weights once per step regardless of batch size, so 3-4 concurrent sequences yield roughly 2.5-3.5x aggregate decode throughput [E]. oMLX’s own docs claim up to 4x generation speedup at high concurrency. 
toolradar
KV capacity caps the batch at about 3 long contexts. Prefill is the real serialization point.
Agents spend much of their wall time waiting on tools. Many runs can be in flight while only about 3 are decoding.

Design:

Coordinator/worker over a shared task table (blackboard). No swarm chat: token cost grows with the number of participants and your decode is the scarcest resource.
Hierarchy depth at most 3.
Parallelism only across independent tasks, each with its own git worktree.
Group queued tasks by model tier and swap models at window boundaries, not per task. Details are in D.
4. Coding agents
Axis	Claude Code	Codex CLI	OpenCode	Pi
Local-model support	Hacky (Anthropic-compatible endpoint)	Yes (Ollama, LM Studio, shims)	First-class	First-class
Prompt overhead (community figure)	about 33K tokens	not measured	about 6.9K	smallest (about 4 tools)
Sandboxing	Seatbelt option	Strongest	None built in	None (“almost no guardrails”)
Headless/SDK	Strong	codex exec	Server + SDK	RPC, JSON events, SDK
Subagents	Yes	Limited	Yes	Via extensions
Best overall (cloud model): Claude Code, per one two-week test [S].
Best sandbox: Codex.
Best OSS: OpenCode.
Lightest: Pi.
For your machine: OpenCode, in a Linux VM sandbox that you control, with Pi as the first alternate.
Qwen Code (Alibaba’s CLI) and OpenHands are in the bake-off list. I did not evaluate them beyond listings.
5. Research agents

Evidence on the problem.

An analysis of 4,000-plus NeurIPS 2025 papers found over 100 hallucinated citations across at least 53 papers. 
arxiv
A real citation often still fails the support test: the cited source frequently doesn’t back the claim. 
intuitionlabs
Existing open tools check existence against several databases. RefChecker uses Semantic Scholar, OpenAlex, Crossref, DBLP and ACL Anthology. A cascade design goes DOI/URL fetch, then scholar connectors, then web search. 
emergentmind
alphaxiv
Semantic Scholar’s free tier rate-limits at about 100 requests per 5 minutes. Cache everything. 
skillselion

Architecture: a claims ledger. Hallucinated citations become structurally impossible.

Discover: SearXNG (self-hosted) plus OpenAlex, Crossref, Semantic Scholar, arXiv, Unpaywall and PubMed E-utilities.
Fetch and extract: HTTP fetch, readability extraction, PDF to text. Docling or PyMuPDF4LLM are candidates [V]. Qwen3.8’s native vision handles figures.
Ledger: every claim is a row of claim_text, source_id, locator, verbatim_span, span_sha256, confidence. Only the extractor can write rows.
Deterministic gates:
The identifier (DOI or arXiv ID) must resolve, and Crossref/OpenAlex metadata must match title, year and authors.
The verbatim span must appear as an exact substring of the stored fetched text.
Entailment pass: a separate verifier call, given span and claim only, outputs supported / partial / unsupported / contradicts. Use a different prompt, and ideally a different model than the extractor (35B-A3B in batch windows, or the cloud lane for public material).
Contradiction pass: cluster claims by embedding, then run pairwise entailment inside clusters.
Writer: it may cite only ledger IDs. A post-processor rejects any citation key not in the ledger, and unsupported claims render with a visible flag.
Audit: run RefChecker or an equivalent on every final report and log the results.

Local models are weaker at step 5, so treat its output as a filter, not a proof. High-stakes claims go to human review.

6. Persistent memory
Option	Verdict	When
Markdown files (AGENTS.md, project notes, decision log)	Use	Day 1
SQLite (tasks, runs, events, claims) with FTS5	Use	Day 1
sqlite-vec with FTS5 fused by RRF	Add	Phase 4. Local projects such as Engram and memori already do hybrid search in one SQLite file.
Temporal validity (valid_from, valid_to)	Add	Phase 4. MemFabric does Graphiti-style invalidation in plain SQLite.
Knowledge graph (Graphiti, Kuzu)	Defer	Only when multi-hop relational queries demonstrably fail on hybrid search
Postgres, Qdrant, Neo4j, Mem0 and Letta servers	Skip	None of them earns its RAM or ops cost at this scale 
A lightweight, standalone, framework-agnostic agent memory library — the SQLite of agent memory +2
LLM-driven memory extraction costs decode time you don’t have. Run consolidation (dedupe, promote, prune) in the 05:00 idle window, not inline.
Agents propose memories. Only the supervisor commits “facts”, with provenance (task_id, source, confidence). This blunts memory poisoning through prompt injection.
Scopes: global, project, task, agent. Retrieval by scope first, then hybrid search.
7. Computer control
Technology	Isolation	Verdict
Dedicated macOS user	Weak alone	Mandatory baseline
sandbox-exec (Seatbelt)	Medium, with escape history. Claude Code and Codex rely on it, and macOS won’t nest sandboxes	Not as the primary boundary
Linux containers in a shared VM	Weak. Containers aren’t security boundaries	No
Apple container	Strong. Each container gets its own lightweight VM via the Virtualization framework; needs macOS 26+, so macOS 27 qualifies	Use
Lima or vibe VM	Strong. vibe spins a zero-config Linux VM to sandbox agents	Fallback
macOS guest VM for GUI computer use	Strong, but needs 4-8 GB RAM you can’t spare	Off by default
Host-level GUI agent	None	Never 
github.com +3

Decision: all agent code execution happens in Apple container VMs with no host mounts except the task worktree. Browser automation uses Playwright inside the VM. Full spec is in H.

8. Always-on operation

Full design is in F. Two findings drive it:

FileVault: with FileVault on, a cold boot waits for a password. On macOS 26 and later with Remote Login enabled, you can SSH in before login to unlock the volume, and it worked over Wi-Fi as of 26.5. A power-loss reboot is therefore recoverable, but not unattended. The unattended alternative is turning FileVault off. 
jeffgeerling
astropad
Crash loops: the oMLX KeepAlive leak (see section 1) means restarting a hard-killed model server can make things worse. Restarts need throttling, an escalation ladder, and a root-level guardian outside the agent’s control.
9. Remote access
Tailscale: default-deny ACLs, Tailscale SSH, Serve for internal services, Funnel for public exposure. Use SSH and Serve. Never use Funnel. 
starmorph
A headless-mini pattern already exists: Tailscale Serve for tailnet-only HTTPS dashboards plus Tailscale SSH. 
github
Notifications: self-hosted ntfy, reachable over the tailnet.
Approvals and kill switch: see G.
10. Storage
Item	Location	Reason
macOS, tools, hot models (27B 16 GB, 4B 2.5 GB, embedder)	Internal	Fastest load, boot-critical
Active clones and worktrees	Internal	Small-file I/O
SQLite DBs (WAL) and memory files	Internal	Never put a WAL DB on a detachable drive
Batch model (35B-A3B) and other cold weights	External (copy to internal before a window)	Rarely used
oMLX cold KV cache	External, capped at about 100 GB	Protects internal SSD endurance. Restoring about 2 GB blocks at TB4 speeds is under a second [E].
Papers, datasets, artifacts, log archive	External	Rebuildable or re-downloadable
Backups	External plus optional off-site	Nightly sqlite3 .backup and restic

External drive rules:

Use a Thunderbolt NVMe enclosure.
Run pmset disksleep 0.
Mount it at boot.
Treat everything on it as rebuildable.
Give oMLX a fallback cache path on internal disk so a detach doesn’t kill serving.
A. Recommended technology stack
Layer	Recommended	Alternatives	Why
Interface	SSH + tmux, tailnet web dashboard, ntfy	Hermes gateway (later)	No public ports
Supervisor	launchd units plus a Python supervisor, root guardian daemon	systemd-style tools (n/a on macOS)	Native recovery, minimal parts
Orchestrator and queue	Python asyncio plus SQLite WAL	Temporal, Celery	Single node, durable, zero services
Agents	AgentSpec YAML plus headless OpenCode workers	Pi, Codex exec	Small prompts, SDK/server mode
Model router	Rule table (role to tier, effort, sensitivity) in the supervisor	LiteLLM-style proxy	Deterministic, auditable
Local inference	oMLX, Qwen3.8-27B resident	mlx-lm, llama.cpp	Batching and SSD prefix cache
Tools	MCP servers (fetch, search, ledger, git broker) behind the policy broker		Single choke point
Sandbox	Apple container VMs	Lima, vibe	VM-grade isolation
Memory	Files, SQLite FTS5, sqlite-vec	Graphiti later	No extra services
Remote	Tailscale, ntfy	WireGuard, Headscale	Identity-based ACLs

A2. Market map

Category	Best overall	Best for this HW	Best OSS	Lightest	Most mature	Cutting edge	Use
Inference engine	vLLM/SGLang on NVIDIA (from memory)	oMLX	oMLX / llama.cpp	llama.cpp	llama.cpp	oMLX (SSD KV, MTP)	oMLX, llama.cpp fallback
Local coding model (32 GB)	Qwen3.8-27B	Qwen3.8-27B (quality), 3.6-35B-A3B (speed)	Same (Apache-2.0)	Qwen3.5-9B	Qwen3.6-27B	Qwen3.8 with MTP	Qwen3.8-27B
Coding harness	Claude Code	OpenCode / Pi	OpenCode	Pi	Claude Code, Codex	Pi ecosystem	OpenCode
Always-on runtime	Hermes (features)	none	Hermes (MIT)	custom	none (all young)	Hermes	custom supervisor
Orchestrator	Temporal	SQLite queue	Temporal	SQLite	Temporal	n/a	SQLite plus Python
Sandbox	Firecracker/gVisor on Linux (from memory, not researched)	Apple container	Apple container, Lima	Seatbelt	Docker	Apple container	Apple container
Memory	Postgres plus pgvector or Graphiti	SQLite stack	SQLite stack	Markdown	Postgres	Temporal graph	Files plus SQLite
Remote	Tailscale	Tailscale	Headscale, WireGuard	SSH over Tailscale	WireGuard/SSH	Tailscale Serve	Tailscale
B. Architecture diagram

Five tiers, with trust boundaries shown by color: the host control plane is trusted, the VM workers are not.


Stopped by a usage limit. You can try again now.
Try again



4 hours ago

## Reasoning trace (not shown to raters)

NONE

## Run notes

claude.ai incognito chat, Sonnet 5.5, Effort High. Send time 2026-10-14T02:39:12.772Z (browser clock). Chat: https://claude.ai/chat/7a66366d-6aeb-4d19-9deb-f05755ab02c6?incognito
Operated by the assistant (Claude, via Claude in Chrome) at the author's request.
Not scored. Treated as app downtime under preregistration section 7 (the block waits until the app
works again), per the author's decision; redone with the same run id.
