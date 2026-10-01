# Canonical Prompt — v1 (FROZEN 2026-08-31)

> This is the study instrument. Do not edit after freezing. Paraphrases live in `prompt-v2.md`, `prompt-v3.md`.
> Paste everything between the `=== PROMPT START ===` and `=== PROMPT END ===` markers into each AI.
> The header block below the markers is part of the prompt — keep it.

=== PROMPT START ===

**Context for you, the responding model:**
- Today's date is **31 August 2026**. Research and cite the current state of the ecosystem as of this date.
- If you have web/tool access, use it and cite primary sources. If you do not, answer from knowledge and say so explicitly.
- This response will be compared side-by-side with responses from ~10 other AI systems, then synthesized into a research paper and used as a build specification. Be concrete, evidence-based, and decisive.
- At the very top of your response, state: your model name and version, your knowledge cutoff (if known), and whether web browsing/tools were enabled for this answer.

---

I want you to act as a senior AI infrastructure architect and researcher. I am building a fully local, always-on autonomous AI workstation and want you to research the latest technology available as of today and determine the best architecture and tools for my specific hardware and requirements.

## My hardware

- Apple Mac mini
- M6 chip (base M6, not Pro/Max)
- 32 GB unified memory
- 512 GB internal SSD
- 1 TB external SSD
- The machine can remain powered on 24/7
- I want the system to continue working when I am away from home or sleeping.

## What I want to build

A personal autonomous AI system that can:

1. Work continuously for many hours without me supervising it.
2. Continue working overnight while I sleep.
3. Be remotely controllable from my phone/laptop when I am away.
4. Work across any project or directory on my computer, rather than being tied to one repository.
5. Perform serious software development: understand existing repositories, plan features, write code, modify files, run commands, run tests, debug, review code, use Git, create branches/worktrees, iterate until a task is completed.
6. Perform autonomous research: web research, literature research, find and compare papers, collect evidence, verify claims, identify contradictions, synthesize findings, produce research reports.
7. Work with documents, PDFs, datasets, Markdown, code, and other files.
8. Run experiments and analyze results.
9. Create documentation automatically.
10. Maintain persistent memory about projects, decisions, research, experiments, and previous work.
11. Spawn or coordinate many specialized subagents.
12. Potentially manage 100+ logical subagents, while intelligently limiting the number of simultaneous LLM inference processes according to my hardware.
13. Dynamically create specialized agents when a task requires them rather than requiring me to manually configure every agent.
14. Allow different agents to have different roles, tools, permissions, context, and objectives.
15. Automatically decide which model is appropriate for each task.
16. Prefer local/private processing wherever practical.
17. Be able to use external web resources when necessary for research.
18. Operate the computer autonomously, while maintaining sensible security boundaries around sensitive personal data, credentials, financial information, and destructive system operations.

## The most important requirement

I do NOT want a chatbot or coding autocomplete. I want an agentic operating environment capable of:

planning → delegating → executing → observing → verifying → correcting → documenting → continuing

with minimal human intervention. The system should wake up, inspect its task queue, decide what needs to be done, execute work, evaluate the results, create follow-up tasks, and continue until the objective or predefined stopping conditions are reached.

## Research requirements

Do NOT assume that any particular existing product, framework, model, agent platform, inference engine, orchestration framework, or protocol is the correct answer. Do not recommend tools because they are popular. Search the current ecosystem broadly and identify the best technologies available right now. Prioritize primary sources: official documentation, GitHub repositories, release notes, technical benchmarks, model cards, developer documentation, current community discussions, recent technical articles, independent benchmarks. Look beyond technologies commonly mentioned on Reddit or YouTube.

Investigate specifically:

1. **Local inference.** Compare the strongest practical local inference options for a 32 GB unified-memory Apple Silicon machine. Consider model quality, coding ability, reasoning ability, agentic/tool-use ability, context length, quantization, memory requirements, inference speed, concurrency, Apple Silicon optimization, Metal acceleration, model loading/unloading, multiple-model operation, stability, maturity. Determine which models I should actually run locally. Do not simply choose the largest model that technically fits. Optimize for useful work per hour, not parameter count.

2. **Agent runtimes / harnesses.** Research the latest agent runtimes/harnesses. Compare systems providing: autonomous loops, tool use, terminal access, filesystem access, browser access, code execution, sandboxing, persistent sessions, subagents, agent spawning, task delegation, retries, state management, long-running tasks, background execution, scheduling, observability, permissions, remote control. Determine whether I should use one existing agent harness, multiple complementary systems, or build a custom orchestration layer on top of existing technology.

3. **Multi-agent architecture.** Research the best current approach for running many agents on limited hardware. Explain the difference between: 100 actual simultaneous model instances, 100 logical agents, agent definitions, task queues, worker pools, dynamic subagents, sequential execution, parallel execution, model routing, hierarchical agents, swarm architectures, coordinator/worker architectures. Design the architecture that gives the highest useful throughput on 32 GB unified memory.

4. **Coding agents.** Compare the best current autonomous coding systems. Evaluate: repository understanding, terminal execution, code editing, test execution, debugging, Git integration, worktrees, long-running tasks, autonomous iteration, code review, context management, local model support, sandboxing. Determine which is best for my machine and requirements.

5. **Research agents.** Investigate the best current technology for autonomous research: web search, source discovery, academic literature discovery, PDF analysis, citation extraction, evidence tracking, claim verification, contradiction detection, synthesis, report generation. Determine the best architecture for preventing hallucinated citations and unsupported claims.

6. **Persistent memory.** Compare: filesystem memory, SQLite, relational databases, vector databases, knowledge graphs, embeddings, hybrid memory, episodic memory, semantic memory, project-specific memory, global memory. Determine what I should use initially and what to add later as the system grows. Avoid unnecessary infrastructure.

7. **Computer control.** Research the safest and most capable current technologies for giving an autonomous agent broad access to a computer: terminal control, filesystem control, browser control, GUI/computer-use, application control, process management, sandboxing, virtual machines, containers, dedicated OS users, permission systems, credential isolation, network isolation. I want maximum practical autonomy without giving an AI unrestricted access to sensitive personal information by default.

8. **Always-on operation.** Determine how to make the system operate 24/7: macOS background services, launch agents/daemons, automatic restart, crash recovery, task persistence, queues, scheduled jobs, monitoring, logging, watchdogs, sleep prevention, remote access, network security. The system should recover automatically if an agent crashes or the computer restarts.

9. **Remote access.** Best current approaches for: secure remote commands, status dashboards, notifications, task submission, logs, approvals, emergency stop, authentication, encrypted connections. Do not expose unnecessary services directly to the public internet.

10. **Storage architecture.** Given 512 GB internal + 1 TB external SSD, determine what should live on each drive: models, databases, embeddings, Git repositories, research papers, datasets, logs, temporary agent workspaces, backups, caches. Consider external SSD throughput and reliability.

## Required final architecture

After researching everything, design the best complete system for my exact machine. Give a concrete layered architecture (interface → supervisor → orchestrator → task queue → specialized agents → model router → local inference → tools → persistent memory), but do NOT assume that shape is correct — change it if your research shows a better design.

## Independently compare the market

For every major category identify: (1) best overall, (2) best for my specific hardware, (3) best open-source option, (4) best lightweight option, (5) best mature/stable option, (6) best cutting-edge option, (7) what I should actually use. Include alternatives I may not know about. If two technologies are close, explain the tradeoff and choose one for my use case.

## Hardware optimization

Calculate approximately how my 32 GB unified memory should be allocated. Account for: macOS, inference model weights, KV cache, context windows, agent processes, databases, browser, development tools, filesystem cache. Determine: ideal model size, ideal quantization, ideal context window, number of concurrent large-model workers, number of concurrent small-model workers, whether model swapping is worthwhile, whether multiple models should remain loaded, expected bottlenecks. Do not claim precise performance numbers unless supported by benchmarks.

## Cost

Prefer free/open-source/local technologies where practical. Identify: completely local/free components, optional paid components, cloud APIs genuinely worth using, situations where local inference is better, situations where cloud inference is worth temporarily using. The system must remain useful without mandatory cloud APIs.

## Security

Design a security model for autonomous operation. The agent should be highly autonomous but NOT blindly trusted. Include: permissions, sandboxing, dedicated user accounts, workspace isolation, Git safeguards, secrets management, network controls, destructive-command controls, human approval thresholds, emergency kill switch, audit logs, resource limits, time limits, token limits, runaway-agent protection. Explain exactly which operations should require approval and which can be fully autonomous.

## Implementation plan

Give a practical roadmap in phases: (1) minimal working system, (2) autonomous coding, (3) research agents, (4) persistent memory, (5) multi-agent orchestration, (6) 24/7 operation, (7) remote access, (8) advanced optimization. For every phase provide: exact technologies, installation commands where applicable, configuration, directory structure, architecture, how components communicate, how to test it, common failure modes, how to roll back.

## Final deliverables

Provide, clearly labeled:
- **A.** Recommended technology stack — table: Layer | Recommended technology | Alternatives | Why
- **B.** Complete architecture diagram — show how everything connects
- **C.** Hardware/resource plan — expected RAM/storage usage
- **D.** Agent architecture — how to have 100+ logical agents without running 100 LLMs simultaneously
- **E.** Model strategy — exactly which models for: planning, coding, debugging, research, summarization, classification, final synthesis
- **F.** 24/7 architecture — how the system continues overnight and recovers from failures
- **G.** Remote-control architecture — how to securely interact from a phone while away
- **H.** Security architecture — how to give broad computer capability without exposing personal secrets
- **I.** Exact installation plan — step-by-step, executable on the Mac
- **J.** What NOT to install — popular technologies that would be redundant, unnecessary, immature, or counterproductive here
- **K.** Future upgrade path — what to change when moving to 64/96/128+ GB unified memory or adding a dedicated GPU/server

## Most important instruction

Do the research first. Do not give a generic answer from existing knowledge. Verify current versions, capabilities, hardware support, and project activity as of today. Make decisions based on evidence and benchmarks, not brand popularity. The result should be a practical, production-quality architecture for a personal 24/7 autonomous AI research lab running primarily on a 32 GB M6 Mac mini.

## Response format (for comparability across models)

Please structure your answer as:
1. Header line: model name + version, knowledge cutoff, browsing on/off
2. Short "decisions at a glance" table (your final picks per layer)
3. Numbered sections 1–10 matching the investigation areas above
4. Lettered deliverables A–K
5. A "Sources" list with URLs, marking each primary or secondary

=== PROMPT END ===
