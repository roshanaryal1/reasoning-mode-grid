#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# memory_budget.py
#
# Purpose (RQ3, "constraint reasoning"): given a proposed set of resident models
# plus a context length, estimate peak unified-memory use on a 32 GB Apple M6
# Mac mini and flag whether it fits.
#
# This is a DELIBERATELY SIMPLE first-order model. It is not a profiler. Its job
# is to catch responses that recommend something that cannot physically fit
# (e.g. "keep a 30B coder and gpt-oss-20b and a browser resident"). Numbers are
# planning estimates drawn from published MLX benchmarks on M4 Pro / M5 hardware
# (see analysis/findings/claude-sonnet-5-findings.md, sources 3, 8, 13).
#
# Assumptions / knobs (all overridable on the CLI):
#   - Total unified memory:            32 GB
#   - macOS + core services:           7 GB   (--os)
#   - Python supervisor + workers:     3 GB   (--proc)
#   - Headless Chromium (if present):  2.5 GB (--browser / --no-browser)
#   - SQLite + vec index resident:     0.7 GB (--db)
#   - KV cache: estimated from context length + a per-1k-token cost that scales
#     with the LARGEST resident model, unless overridden with --kv.
#
# Usage:
#   memory_budget.py --preset claude
#   memory_budget.py --preset qwen
#   memory_budget.py --weights 19 3 --ctx 32000 --browser
#   memory_budget.py --weights 18 --kv 3 --small 3 --no-browser
#
# Exit code: 0 if it fits with >= --headroom GB free, 1 otherwise.
# ---------------------------------------------------------------------------

from __future__ import annotations

import argparse
import sys

TOTAL_GB = 32.0

# name -> (weight_gb_q4, kv_gb_per_1k_tokens)
# kv-per-1k is a rough figure for 4-bit KV at that model's hidden size / layer count.
PRESETS: dict[str, dict] = {
    "claude": {
        # Claude's stated steady state: coder loaded + Qwen3-4B kept resident for
        # routing, browser evicted, context held DOWN to protect the budget.
        # At 32k ctx this set is already on/over the wall (as Claude itself warns);
        # 16k is the realistic tight steady state. Try --ctx 32000 to see it tip over.
        "label": "Claude Sonnet 5 pick (Qwen3-Coder-30B-A3B + Qwen3-4B resident)",
        "models": [("Qwen3-Coder-30B-A3B q4", 18.0, 0.09),
                   ("Qwen3-4B q4 (resident)", 3.0, 0.02)],
        "ctx": 16000,
        "browser": False,  # Claude notes the browser is evicted at peak
    },
    "qwen": {
        "label": "Qwen 3.7 Plus pick (Qwen2.5-Coder 32B dense + Qwen2.5 7B + embed)",
        "models": [("Qwen2.5-Coder 32B q4 (dense)", 19.5, 0.16),
                   ("Qwen2.5 7B q4 (resident)", 4.5, 0.03),
                   ("embed model (resident)", 1.5, 0.0)],
        "ctx": 24000,
        "browser": True,
    },
    "deepseek-instant": {
        "label": "DeepSeek Instant pick (Qwen3-Coder-30B-A3B + 'Gemma 4 26B' [not real])",
        "models": [("Qwen3-Coder-30B-A3B q4", 17.0, 0.09),
                   ("'Gemma 4 26B' q4 [FABRICATED MODEL]", 19.0, 0.14)],
        "ctx": 32000,
        "browser": True,
    },
    "deepseek-expert": {
        # DeepSeek Expert's own resource table: 1 large model (18) + a 3 GB
        # "secondary model pool" loaded on-demand + browser. The 14B models are
        # NOT co-resident. This preset encodes what it actually claimed fits.
        "label": "DeepSeek Expert pick (Qwen3-Coder-30B-A3B resident + 3 GB small-model pool)",
        "models": [("Qwen3-Coder-30B-A3B q4", 18.0, 0.09),
                   ("secondary small-model pool (on-demand slot)", 3.0, 0.05)],
        "ctx": 32000,
        "browser": True,
    },
    "deepseek-expert-all": {
        # The pessimistic reading: what if all three named models were kept loaded.
        "label": "DeepSeek Expert, all 3 named models co-resident (pessimistic)",
        "models": [("Qwen3-Coder-30B-A3B q4", 18.0, 0.09),
                   ("Qwen3-14B q4", 8.0, 0.05),
                   ("Phi-4-14B q4", 8.0, 0.05)],
        "ctx": 32000,
        "browser": True,
    },
    "perplexity": {
        # Perplexity's rule: Qwen3-Coder-30B-A3B as the single heavy worker, optional
        # 4-8B helper, NO second large model co-resident, context capped 16k default.
        "label": "Perplexity pick (Qwen3-Coder-30B-A3B + optional 4-8B helper, 16k ctx)",
        "models": [("Qwen3-Coder-30B-A3B q4", 17.0, 0.09),
                   ("4-8B utility helper (optional)", 5.0, 0.03)],
        "ctx": 16000,
        "browser": True,
    },
    "deepseek-deepthink": {
        # DeepSeek Instant+DeepThink keeps THREE models loaded per its own diagram
        # ("Ornith-1.0-9B" + "Qwen2.5-Coder-7B" always loaded, "Qwen3.5-35B-A3B" on
        # demand) and calls the resulting ~32-34 GB "slight oversubscription acceptable".
        # Model names are fabricated; sizes are as the response states them.
        "label": "DeepSeek Instant+DeepThink pick (3 models 'always loaded'; names FABRICATED)",
        "models": [("'Qwen3.5-35B-A3B' q4 [FABRICATED]", 22.0, 0.14),
                   ("'Ornith-1.0-9B' q4 [FABRICATED]", 5.6, 0.03),
                   ("'Qwen2.5-Coder-7B' q4", 4.0, 0.03)],
        "ctx": 8000,
        "browser": True,
    },
    "gemini": {
        # Gemini 3.1 Pro: single resident model (hot-swap Qwen2.5-Coder-32B <-> R1-Distill-14B,
        # never both), 2 llama.cpp slots of the SAME model, 16k context split 2x8k. Its own map
        # assumes a lean 5 GB macOS while also running Docker + SearXNG + Crawl4AI.
        "label": "Gemini 3.1 Pro pick (Qwen2.5-Coder-32B Q4_K_M dense, single resident, -np 2)",
        "models": [("Qwen2.5-Coder-32B q4_k_m (dense)", 19.8, 0.11)],
        "ctx": 16000,
        "browser": True,
    },
    "kimi": {
        # Kimi Instant: Ollama-0.19-MLX, ONE large model resident (Qwen3-Coder-30B-A3B),
        # small model swapped on demand, ctx 32-64k. Its RAM table budgets only 3-4 GB
        # for macOS while also running Ollama + Playwright + Python + Docker(OpenHands).
        "label": "Kimi Instant pick (Qwen3-Coder-30B-A3B Q4 resident, one large at a time)",
        "models": [("Qwen3-Coder-30B-A3B q4 (~22 GB as stated)", 22.0, 0.09)],
        "ctx": 32000,
        "browser": True,
    },
    "mistral": {
        # Mistral Large 3: ONE resident large MoE (Qwen3-Coder-30B-A3B 4-bit ~18-20 GB),
        # small dense (Qwen3.5-9B Q8 ~11 GB) LOAD-ON-DEMAND via llama-swap (not co-resident),
        # KV can spill to external SSD via oMLX. ctx 32-64k routine.
        "label": "Mistral Large 3 pick (Qwen3-Coder-30B-A3B 4-bit resident; 9B swapped via llama-swap)",
        "models": [("Qwen3-Coder-30B-A3B 4-bit", 19.0, 0.09)],
        "ctx": 48000,
        "browser": True,
    },
    "mistral-two-resident": {
        # The tight case Mistral flags as "feasible but not recommended": both models resident.
        "label": "Mistral Large 3, both models resident (flagged tight, not recommended)",
        "models": [("Qwen3-Coder-30B-A3B 4-bit", 19.0, 0.09),
                   ("Qwen3.5-9B Q8", 11.0, 0.04)],
        "ctx": 32000,
        "browser": False,
    },
    "gpt5": {
        # GPT-5.6 Luna: MLX-LM, Qwen3.6-35B-A3B 4-bit (~20.4 GB artifact) resident +
        # Qwen3.5-4B 4-bit (~3 GB). Small model can be kept alongside per its budget
        # table, but that "gets close to the physical ceiling surprisingly quickly".
        # llama.cpp / Docker(OpenHands) also running. ctx: 8/16/32/64k tiers.
        "label": "GPT-5.6 Luna pick (Qwen3.6-35B-A3B 4-bit + Qwen3.5-4B 4-bit, both resident)",
        "models": [("Qwen3.6-35B-A3B 4-bit (20.4 GB artifact)", 20.4, 0.06),
                   ("Qwen3.5-4B 4-bit", 3.0, 0.02)],
        "ctx": 16000,
        "browser": True,
    },
    "meta": {
        # Meta / Llama 4: one hot large model (its "Qwen3.5-35B-A3B" fabricated tag, ~20 GB)
        # kept resident (keep_alive=-1) + Qwen2.5-Coder-7B (~5 GB) small tier + OrbStack +
        # dev tools + browser. Its own table: "~32 GB tight but feasible, single large only".
        "label": "Meta/Llama 4 pick (35B-A3B ~20 GB resident + Qwen2.5-Coder-7B ~5 GB + OrbStack)",
        "models": [("35B-A3B 4-bit ('Qwen3.5-35B-A3B' — fabricated tag)", 20.0, 0.07),
                   ("Qwen2.5-Coder-7B Q4_K_M", 5.0, 0.03)],
        "ctx": 32000,
        "browser": True,
    },
    "grok": {
        # Grok 4: one large model (Qwen 27B dense ~18 GB, or 35B-A3B MoE ~22 GB) + one small
        # model / embeddings (~3 GB), 32-64k ctx. Its own line: primary + KV = 18-22 GB.
        "label": "Grok 4 pick (Qwen 27B dense ~18 GB or 35B-A3B ~22 GB + small model, 1 large worker)",
        "models": [("Qwen 27B dense q4 (~18 GB) / 35B-A3B ~22 GB", 18.0, 0.08),
                   ("small model / embeddings", 3.0, 0.02)],
        "ctx": 48000,
        "browser": True,
    },
    "zai": {
        # z.ai / Zhipu GLM: its §B diagram shows THREE large model instances co-resident
        # (Qwen3-Coder ~5 GB [its fabricated "8B" size] + GLM-4.5-Air ~4 GB + Mistral Small
        # ~6 GB), and its §C table sums to "32 GB ... Fits within 32GB RAM with swapping".
        # Uses the §C figure (14 GB primary) since that is the one it defends numerically.
        "label": "z.ai pick (3 model instances co-resident; §C says 'fits with swapping')",
        "models": [("'Qwen3-Coder-Next 8B' — §C says 14 GB (fabricated size)", 14.0, 0.06),
                   ("GLM-4.5-Air 4-bit", 4.0, 0.03),
                   ("Mistral Small 3.1 4-bit", 6.0, 0.04)],
        "ctx": 32000,
        "browser": True,
    },
    "over-budget-demo": {
        "label": "The classic mistake: heavy MoE + mid reasoner + browser all resident",
        "models": [("Qwen3-Coder-30B-A3B q4", 18.0, 0.09),
                   ("gpt-oss-20b MXFP4", 14.0, 0.06)],
        "ctx": 32000,
        "browser": True,
    },
}


def estimate_kv_gb(models: list[tuple[str, float, float]], ctx_tokens: int,
                   kv_override: float | None) -> float:
    if kv_override is not None:
        return kv_override
    if not models:
        return 0.0
    # KV is dominated by whichever resident model has the largest per-token cost.
    worst_per_1k = max(m[2] for m in models)
    return round(worst_per_1k * (ctx_tokens / 1000.0), 2)


def run(models: list[tuple[str, float, float]], ctx_tokens: int, *,
        os_gb: float, proc_gb: float, db_gb: float, browser: bool,
        browser_gb: float, kv_override: float | None, headroom_gb: float) -> int:
    weights_gb = sum(m[1] for m in models)
    kv_gb = estimate_kv_gb(models, ctx_tokens, kv_override)
    browser_used = browser_gb if browser else 0.0

    line_items = [
        ("macOS + core services", os_gb),
        ("Python supervisor + workers", proc_gb),
        ("SQLite + vec index (resident)", db_gb),
        ("Headless Chromium", browser_used),
        (f"KV cache @ {ctx_tokens:,} tok", kv_gb),
    ]
    for name, w, _ in models:
        line_items.append((f"weights: {name}", w))

    used = sum(v for _, v in line_items)
    free = TOTAL_GB - used

    width = max(len(n) for n, _ in line_items)
    print(f"  {'component'.ljust(width)}   GB")
    print(f"  {'-' * width}   ----")
    for name, val in line_items:
        print(f"  {name.ljust(width)}   {val:5.2f}")
    print(f"  {'-' * width}   ----")
    print(f"  {'TOTAL USED'.ljust(width)}   {used:5.2f}")
    print(f"  {'FREE (of 32.00)'.ljust(width)}   {free:5.2f}")
    print()

    if free < 0:
        print(f"  RESULT: DOES NOT FIT — over by {-free:.2f} GB. "
              f"Model set must be serialised, not co-resident.")
        return 1
    if free < headroom_gb:
        print(f"  RESULT: FITS but TIGHT — only {free:.2f} GB free "
              f"(< {headroom_gb:.2f} GB headroom target). "
              f"No room for filesystem cache / spikes.")
        return 1
    print(f"  RESULT: FITS with {free:.2f} GB headroom.")
    return 0


def parse_weight_pairs(values: list[str]) -> list[tuple[str, float, float]]:
    """Accept bare GB numbers: --weights 18 3  ->  two anonymous models."""
    out = []
    for i, v in enumerate(values):
        try:
            gb = float(v)
        except ValueError:
            raise SystemExit(f"--weights takes GB numbers, got {v!r}")
        # unknown model: assume a middling KV-per-1k cost
        out.append((f"model {i + 1}", gb, 0.08))
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--preset", choices=sorted(PRESETS), help="use a captured response's model set")
    src.add_argument("--weights", nargs="+", metavar="GB",
                     help="resident model weight sizes in GB, e.g. --weights 18 3")

    p.add_argument("--ctx", type=int, default=32000, help="context length in tokens (default 32000)")
    p.add_argument("--kv", type=float, default=None,
                   help="override KV-cache GB (else estimated from --ctx)")
    p.add_argument("--small", type=float, default=None,
                   help="add one more resident small model of this many GB (with --weights)")
    p.add_argument("--os", type=float, default=7.0, help="macOS + services GB (default 7)")
    p.add_argument("--proc", type=float, default=1.5,
                   help="python supervisor + idle workers GB (default 1.5; the mlx "
                        "server's RAM is counted under model weights)")
    p.add_argument("--db", type=float, default=0.5, help="sqlite + vec GB (default 0.5)")
    p.add_argument("--browser-gb", type=float, default=2.5, help="headless chromium GB (default 2.5)")
    bg = p.add_mutually_exclusive_group()
    bg.add_argument("--browser", dest="browser", action="store_true", help="count the browser (default off)")
    bg.add_argument("--no-browser", dest="browser", action="store_false")
    p.set_defaults(browser=None)
    p.add_argument("--headroom", type=float, default=2.0,
                   help="min free GB to call it comfortable (default 2)")

    args = p.parse_args(argv)

    if args.preset:
        preset = PRESETS[args.preset]
        models = list(preset["models"])
        ctx = args.ctx if "--ctx" in (argv or sys.argv[1:]) else preset["ctx"]
        browser = preset["browser"] if args.browser is None else args.browser
        print(f"\n  preset: {args.preset}  —  {preset['label']}\n")
    else:
        models = parse_weight_pairs(args.weights)
        if args.small is not None:
            models.append((f"small model {len(models) + 1} (resident)", args.small, 0.02))
        ctx = args.ctx
        browser = bool(args.browser)
        print("\n  custom model set\n")

    return run(models, ctx,
               os_gb=args.os, proc_gb=args.proc, db_gb=args.db,
               browser=browser, browser_gb=args.browser_gb,
               kv_override=args.kv, headroom_gb=args.headroom)


if __name__ == "__main__":
    raise SystemExit(main())
