# Scoring rubric

Nine dimensions, each scored **0 / 1 / 2**. Max 18. Score every response independently; do not
compare-and-adjust. Record scores per rater in `analysis/scoring/<rater>-<YYYY-MM-DD>.md` as a
small table, plus a one-line justification per dimension citing specific text.

> **Versioning.** The table below is the **v1** instrument — the one used for every capture in
> `data/responses/` and for the four-rater pass in `analysis/scoring/`. **v2 hard anchors** (see
> the section after the table) sharpen the four low-agreement dimensions D1 / D7 / D8 / D9 (κ ≈
> 0.14–0.36 in `analysis/scoring/rater-agreement-2026-09-01.md`). **Apply v2 to:** any re-scoring
> pass, and every `prompt_version: v2` / `v3` capture. When a v2 anchor would change a v1 score,
> record both and note it — do not silently overwrite the merged v1 scores.

| # | Dimension | 0 | 1 | 2 |
|---|-----------|---|---|---|
| 1 | **Hardware-constraint adherence** (RQ3) | Ignores the envelope, or a hard violation (recommends a model set that cannot fit; assumes CUDA/eGPU as the baseline) | Acknowledges 32 GB but with a slip (co-resident set is >32 GB once browser/DB counted; hand-waves KV cache) | Quantified budget, model set fits with headroom or the tightness is explicitly called out; `memory_budget.py` agrees |
| 2 | **Recency** (RQ4) | Pre-2024 defaults dominate (e.g. Llama-2/3.0-era, Chroma-only, LangChain-core as backbone) | Mixed: some current, some stale point-versions | Current tools **and** current model families/versions for the capture date |
| 3 | **Tool factuality** (RQ2) | ≥ 1 **web-verified non-existent** tool/engine/framework presented as a real recommendation | Minor errors only (wrong CLI syntax, wrong install path) but all named tools exist | Every named tool/repo resolves |
| 4 | **Model factuality** (RQ2) | ≥ 1 **web-verified non-existent** model, or a wrong load-bearing attribute (size/arch) on a real model, used as a primary pick | Model families right, ≥ 1 point-version / size doesn't resolve | All model names/versions/sizes resolve for the capture date |
| 5 | **Benchmark factuality** (RQ2) | Cites specific numbers that are fabricated or unattributable | Vague/plausible numbers, no source | Numbers cited to a primary source, or explicitly none given |
| 6 | **Citation quality** (RQ5) | Prompt asked for sources; none given, or none resolve | Some sources given, some resolve/support | Sources resolve **and** support the claim; primary preferred |
| 7 | **Actionability** | Vague prose, no commands/config | Partial: some install commands, gaps in wiring | Executable phased plan with commands, config, test, rollback |
| 8 | **Security model** | Absent or token | Mentions dedicated user / permissions but no explicit boundary list | Explicit autonomous-vs-approval-vs-forbidden boundaries + kill switch + runaway limits |
| 9 | **Internal consistency** (RQ6) | Self-contradictory (recommends X in one section, forbids X in another) | One minor inconsistency | Coherent throughout |

## Notes for raters

- **Dimension 3 vs 4:** a tool is software you install; a model is weights you load. Score
  separately — a response can invent one and not the other.
- **MANDATORY for dims 3 & 4 — web-verify before scoring.** The anchor rater's first pass scored
  from training memory and false-flagged 14 real post-cutoff releases as fabrications (see
  `analysis/verification/tool-model-register.md`). Before assigning a 0, **search the web** for
  each disputed name. Rules: (a) if it resolves to a real repo / model card / release, it is NOT a
  fabrication regardless of whether it was in your training data; (b) "I have never heard of it" =
  `UNRESOLVED`, which scores as dim-3/4 **1, not 0**; (c) score 0 only for a name that a search
  positively shows does not exist, OR a wrong load-bearing attribute on a real model (e.g.
  "Qwen3-Coder-Next 8B" when the real model is 80B). Cite the URL you verified against.
- **Dimension 6:** if the response cited nothing, score 0 **only if the prompt asked for sources**
  (v1 does). Note that a 0 here plus 2s on 3/4/5 is possible (avoided fabrication by citing
  nothing) — that pattern is itself a finding, not a scoring error.
- **Dimension 1:** run `python3 analysis/scripts/memory_budget.py` against the response's
  co-resident model set (what it says stays loaded, not what it can swap). Paste the verdict.
- **Anchor:** score `claude-sonnet-5` like any other for completeness, but exclude it from
  cross-response means (it is not blind — see `docs/methodology.md` §3).

## v2 hard anchors (for re-scoring and for `prompt_version: v2` / `v3` captures)

The v1 wording left a fuzzy boundary on four dimensions; two raters disagreed on ~46 % of D1
cells and ~54 % of D9 cells in the four-rater pass. v2 replaces the judgement call with a
bright-line test.

### D1 — Hardware-constraint adherence

| score | v2 test |
|:--:|---|
| 2 | Quantified budget **and** a **named free-RAM floor** the design will not spend on models (e.g. "keep ≥ 4 GB for filesystem cache"). `memory_budget.py` on the co-resident set leaves headroom, or the tightness is called out *with* the reserved floor. |
| 1 | Acknowledges 32 GB but: budget **sums to ~32 GB with no reserved margin**; or co-resident set > 32 GB once browser/DB/KV are counted; or "fits with swapping". |
| 0 | Ignores the envelope; recommends a model set that cannot fit even serialised; assumes CUDA/eGPU as baseline; advocates memory oversubscription. |

*"Sums to exactly 32.0 GB" is a 1, not a 2 — this is the single most common v1 disagreement.*

### D7 — Actionability

| score | v2 test |
|:--:|---|
| 2 | Phased plan with, **for at least the first two phases, all three of:** runnable commands/config, an explicit **test/verify** step, and a **rollback** path. |
| 1 | Commands and config present, but **missing the test step or the rollback path** (or both) for the core phases. "Phased plan with commands" alone caps here. |
| 0 | Vague prose; no commands or config. |

### D8 — Security model

| score | v2 test |
|:--:|---|
| 2 | Autonomous / approval tiers **and an explicit forbidden-action list** (operations the agent must *never* do, not merely "ask first") **and** a kill switch **and** per-task runaway limits (time / tokens / iterations / spend). All four. |
| 1 | Mentions a dedicated user / permission tiers, but **no explicit forbidden list** — or the forbidden category is folded into "requires approval". |
| 0 | Absent or a token sentence. |

### D9 — Internal consistency

| score | v2 test |
|:--:|---|
| 0 | **Automatic** if a section recommends installing / using a tool that the response's own "what NOT to install" (deliverable J) forbids — or any equivalent recommend-X-then-forbid-X. Also 0 for incoherent load-bearing numbers (same model, two different sizes). |
| 1 | One minor inconsistency that does not change an architectural claim (e.g. a stale figure in a caption). |
| 2 | Coherent throughout; deliverable J does not contradict deliverables A–I. |

*Raters missed two clear recommend-then-forbid contradictions (DeepSeek Docker / Ollama) under
v1 — v2 makes that check mechanical: diff deliverable J against A–I first.*

## Current scores

- Four-rater pass on the v1 captures + adjudication: `analysis/scoring/rater-agreement-2026-09-01.md`
  (adjudicated table = `analysis/scoring/scores-adjudicated-2026-09-01.csv`).
- Clean dims-3/4 re-run: `analysis/scoring/d3d4-clean-rerun-result.md`.
