"""Command-line entry point: `modegrid <command>`."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import getpass
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from . import DIMS, PRIMARY_MODES, __version__
from .agreement import exact_agreement, krippendorff_alpha
from .analyze import ALPHA_BAR, build_design, run_analysis, write_outputs
from .audit import PROBES, audit, concentration, write_audit
from .blind import build_packets, guess_accuracy
from .capture import Capture, check_capture, manual_template, read_capture, word_count, write_capture
from .cells import plot_cell_means, rank_agreement, write_cell_means, write_rank_agreement
from .config import load_grid, unready_families
from .ownvendor import own_vendor, write_own_vendor
from .plan import API_CHECK, MAIN, build_manifest, read_manifest, write_manifest
from .providers import adapter_for, with_retries
from .raterkit import build_kit, collect_rows
from .scores import consensus, disagreements, load_key, load_scores, unblind, write_scores
from .synthetic import Effect, power, synthetic_scores

DEFAULT_CONFIG = "configs/grid.yaml"
DEFAULT_MANIFEST = "data/manifest/runs.csv"
DEFAULT_CAPTURES = "data/captures"


def cmd_plan(args: argparse.Namespace) -> int:
    grid = load_grid(args.config)
    runs = build_manifest(grid)
    write_manifest(runs, args.manifest)
    cells = {(r.family, r.mode) for r in runs}
    print(f"wrote {len(runs)} runs ({len(cells)} cells) to {args.manifest}")
    unready = unready_families(grid)
    if unready:
        print(f"note: config placeholders still open for: {', '.join(unready)}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    grid = load_grid(args.config)
    runs = read_manifest(args.manifest)
    unready = set(unready_families(grid))
    done = {p.stem for p in Path(args.captures).glob("*.md")}
    todo = [r for r in runs if r.channel == "api" and r.run_id not in done]
    if args.family:
        todo = [r for r in todo if r.family in args.family]
    blocked = sorted({r.family for r in todo if r.family in unready})
    if blocked:
        print(f"refusing: FILL-ME/VERIFY placeholders remain for {blocked}. Fix configs/grid.yaml first.")
        return 2
    if args.limit:
        todo = todo[: args.limit]
    if args.dry_run:
        for r in todo:
            print(f"{r.run_id}  ({grid.api_check_model(r.family, r.mode, r.replicate)})")
        print(f"{len(todo)} run(s) would execute")
        return 0
    adapters = {}
    for r in todo:
        fam = grid.family(r.family)
        mode = fam.modes[r.mode]
        prompt = grid.prompt(r.prompt_id)
        if fam.id not in adapters:
            adapters[fam.id] = adapter_for(fam)
        text = prompt.text()
        print(f"[{r.order}] {r.run_id} ({grid.api_check_model(fam.id, mode.id, r.replicate)}) ...", flush=True)
        model = grid.api_check_model(fam.id, mode.id, r.replicate)
        adapter, params = adapters[fam.id], mode.params
        limit = fam.max_tokens or grid.max_tokens
        comp = with_retries(
            lambda a=adapter, t=text, m=model, p=params, limit=limit: a.complete(t, m, p, limit), attempts=args.retries
        )
        meta = {
            "run_id": r.run_id,
            "set": r.set,
            "family": fam.id,
            "vendor": fam.vendor,
            "mode": mode.id,
            "native_label": mode.native_label,
            "channel": "api",
            "model_requested": model,
            "model_returned": comp.model_returned,
            "params": json.loads(json.dumps(mode.params)),
            "max_tokens": limit,
            "prompt_id": prompt.id,
            "prompt_sha256": prompt.sha256,
            "replicate": r.replicate,
            "date_run": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "run_by": args.run_by,
            "finish_reason": comp.finish_reason,
            "usage": comp.usage,
            "latency_s": comp.latency_s,
            "harness_version": __version__,
        }
        notes = ""
        if comp.finish_reason not in {"end_turn", "stop", None}:
            notes = f"finish_reason={comp.finish_reason}. Check for truncation or refusal before scoring."
        write_capture(Capture(meta, comp.text, comp.reasoning or "NONE", notes), args.captures)
    print(f"done: {len(todo)} capture(s)")
    return 0


def cmd_new_capture(args: argparse.Namespace) -> int:
    grid = load_grid(args.config)
    runs = {r.run_id: r for r in read_manifest(args.manifest)}
    if args.run_id not in runs:
        print(f"unknown run_id {args.run_id}")
        return 2
    r = runs[args.run_id]
    fam = grid.family(r.family)
    prompt = grid.prompt(r.prompt_id)
    path = Path(args.captures) / f"{r.run_id}.md"
    if path.exists():
        print(f"{path} exists, captures are write-once")
        return 2
    if r.channel != "web":
        print(f"{r.run_id} is an API run. Use `modegrid run` for it.")
        return 2
    mode = fam.modes[r.mode]
    # time needed for the 48 h rule; date_stamped is never edited, date_run may be corrected with a date_note
    stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    meta = {
        "run_id": r.run_id,
        "set": r.set,
        "family": fam.id,
        "vendor": fam.vendor,
        "mode": r.mode,
        "native_label": mode.chat_label,
        "channel": "web",
        "model_requested": f"{fam.vendor} chat app, {mode.chat_label}",
        "model_returned": "FILL IN: the model name the app shows, or 'not shown'",
        "prompt_id": prompt.id,
        "prompt_sha256": prompt.sha256,
        "replicate": r.replicate,
        "date_stamped": stamp,
        "date_run": stamp,
        "run_by": args.run_by,
        "interface": "web app, fresh chat, signed in, no custom instructions, memory off",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manual_template(meta), encoding="utf-8")
    print(f"created {path}. Paste the answer verbatim, then run `modegrid validate`.")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    grid = load_grid(args.config)
    problems: list[str] = []
    for p in grid.prompts:
        try:
            p.text()
        except Exception as exc:
            problems.append(str(exc))
    runs = {r.run_id: r for r in read_manifest(args.manifest)} if Path(args.manifest).exists() else {}
    for path in sorted(Path(args.captures).glob("*.md")):
        try:
            cap = read_capture(path)
        except Exception as exc:
            problems.append(f"{path}: {exc}")
            continue
        problems += [f"{path}: {msg}" for msg in check_capture(cap)]
        if runs and cap.run_id not in runs:
            problems.append(f"{path}: run_id not in manifest")
        if cap.run_id != path.stem:
            problems.append(f"{path}: file name does not match run_id")
    for path in sorted(Path("data/scores").glob("*.csv")):
        try:
            # Rater and consensus sheets are keyed by blind_id; unblinded ones by run_id.
            with path.open(newline="", encoding="utf-8") as fh:
                header = next(csv.reader(fh), [])
            col = "run_id" if "run_id" in header else "blind_id"
            scores = load_scores(path, id_col=col)
        except Exception as exc:
            problems.append(f"{path}: {exc}")
            continue
        if path.name == "adjudicated.csv" and runs:
            main_ids = {rid for rid, r in runs.items() if r.set == MAIN}
            if set(scores) != main_ids:
                missing, extra = sorted(main_ids - set(scores)), sorted(set(scores) - main_ids)
                problems.append(f"{path}: {len(scores)} runs, missing {missing[:3]}, not in manifest {extra[:3]}")
    for msg in problems:
        print(f"ERROR {msg}")
    print("ok" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


def cmd_blind(args: argparse.Namespace) -> int:
    grid = load_grid(args.config)
    main_ids = {r.run_id for r in read_manifest(args.manifest) if r.set == MAIN}
    caps = [read_capture(p) for p in sorted(Path(args.captures).glob("*.md")) if p.stem in main_ids]
    caps = [c for c in caps if not check_capture(c)]
    terms = list(grid.global_redact_terms)
    for fam in grid.families:
        terms += [fam.vendor, fam.model, *fam.redact_terms]
    key = build_packets(caps, terms, args.out, args.key, grid.seed, args.raters)
    print(f"{len(key)} answers blinded into {args.out}. Key at {args.key} (keep away from raters).")
    return 0


def cmd_unblind(args: argparse.Namespace) -> int:
    key = load_key(args.key)
    scores = unblind(load_scores(args.scores), key)
    write_scores(scores, args.out)
    print(f"wrote {len(scores)} run-level rows to {args.out}")
    return 0


def cmd_consensus(args: argparse.Namespace) -> int:
    sheets = [load_scores(p) for p in args.files]
    merged = consensus(sheets)
    write_scores(merged, args.out, id_col="blind_id")
    print(f"median of {len(sheets)} raters for {len(merged)} answers -> {args.out}")
    return 0


def cmd_agreement(args: argparse.Namespace) -> int:
    sheets = [load_scores(p, allow_blank=True) for p in args.files]
    ids = sorted(set().union(*sheets))
    print(f"{len(args.files)} raters, {len(ids)} items. Pre-registered bar: alpha >= {ALPHA_BAR}\n")
    print(f"{'dim':<6}{'alpha_ordinal':>15}{'exact(1v2)':>12}  status")
    rows = []
    for d in DIMS:
        data = [[s.get(i, {}).get(d) for i in ids] for s in sheets]
        alpha = krippendorff_alpha(data, "ordinal")
        exact = exact_agreement(data[0], data[1]) if len(data) > 1 else float("nan")
        status = "ok" if alpha >= ALPHA_BAR else "BELOW BAR"
        rows.append((d, alpha, exact, status))
        print(f"{d:<6}{alpha:>15.3f}{exact:>12.2f}  {status}")
    # total score (sum of D1-D9) at interval level: H4's reliability gate
    totals = [
        [sum(s[i][d] for d in DIMS) if i in s and all(d in s[i] for d in DIMS) else None for i in ids] for s in sheets
    ]
    t_alpha = krippendorff_alpha(totals, "interval")
    t_exact = exact_agreement(totals[0], totals[1]) if len(totals) > 1 else float("nan")
    t_status = "ok" if t_alpha >= ALPHA_BAR else "BELOW BAR"
    rows.append(("total", t_alpha, t_exact, t_status))
    print(f"{'total':<6}{t_alpha:>15.3f}{t_exact:>12.2f}  {t_status}  (interval)")
    if args.out:
        # dimension,alpha is the format arch-spec-bench's `specbench gate --alpha` reads.
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["dimension", "alpha", "exact_agreement_1v2", "status"])
            for d, alpha, exact, status in rows:
                w.writerow([d, f"{alpha:.4f}", f"{exact:.4f}", status])
        print(f"\nwrote {out}")
    if len(sheets) >= 2:
        queue = disagreements(sheets[0], sheets[1])
        print(f"\nadjudication queue (rater 1 vs rater 2): {len(queue)} cell(s)")
        for uid, d, x, y in queue[: args.show]:
            print(f"  {uid} {d}: {x} vs {y}")
    return 0


def cmd_rater_kit(args: argparse.Namespace) -> int:
    """One file per answer per rater: fixed prompt, rubric, protocol, checker, one answer."""
    for rater in args.raters:
        files = build_kit(args.packets, rater, args.prompt, args.rubric, args.protocol, args.checker, args.out)
        print(f"{rater}: {len(files)} files in {Path(args.out) / rater}")
    return 0


def cmd_rater_rows(args: argparse.Namespace) -> int:
    """Collect returned CSV rows. The sheet goes to data/scores only once all answers are in."""
    sheet = Path(args.packets) / f"scoresheet-{args.rater}.csv"
    work = Path(args.packets) / "collected" / f"{args.rater}.csv"
    filled, missing = collect_rows(args.replies, sheet, work)
    print(f"{args.rater}: {filled} of {filled + len(missing)} scored; working sheet {work}")
    if missing:
        print(f"still to score: {' '.join(missing)}")
        return 0
    final = Path(args.final_dir) / f"{args.rater}.csv"
    final.parent.mkdir(parents=True, exist_ok=True)
    final.write_text(work.read_text(encoding="utf-8"), encoding="utf-8")
    load_scores(final)
    print(f"complete: wrote {final}")
    return 0


def cmd_blinding_check(args: argparse.Namespace) -> int:
    """Did raters guess family or mode better than chance? Reported in the paper."""
    key = load_key(args.key)
    runs = {r.run_id: (r.family, r.mode) for r in read_manifest(args.manifest) if r.set == MAIN}
    n_families = len({f for f, _ in runs.values()})
    print(f"chance: family 1/{n_families}, mode 1/2. Small p = rater beat chance = blinding leaked.\n")
    print(f"{'sheet':<28}{'guess':<14}{'guessed':>9}{'correct':>9}{'acc':>7}{'chance':>8}{'p':>8}")
    for sheet in args.files:
        res = guess_accuracy(sheet, key, runs, n_families)
        for field, r in res.items():
            print(
                f"{Path(sheet).name:<28}{field:<14}{int(r['guessed']):>6}/{int(r['items']):<2}"
                f"{int(r['correct']):>9}{r['accuracy']:>7.2f}{r['chance']:>8.2f}{r['p_value']:>8.3f}"
            )
    return 0


def cmd_blinding_audit(args: argparse.Namespace) -> int:
    """Before scoring: which family fingerprints survive in the packets? Exit 1 on a leak."""
    key = load_key(args.key)
    results = audit(Path(args.packets) / "answers", key)
    cells = sorted({"/".join(run.split("__")[:2]) for run in key.values()})
    leaks = 0
    print(f"{len(key)} packets. leak = should be 0 after blinding; style = the model's own text, reported.\n")
    print(f"{'probe':<18}{'kind':<7}{'packets':>8}  {'top family (share)':<22}cells")
    for p in PROBES:
        c = results[p.name]
        fam, share = concentration(c)
        top = f"{fam} ({share:.0%})" if fam else ""
        print(f"{p.name:<18}{p.kind:<7}{sum(c.values()):>8}  {top:<22}{dict(sorted(c.items()))}")
        if p.kind == "leak":
            leaks += sum(c.values())
    if args.out:
        print(f"\nwrote {write_audit(results, cells, args.out)}")
    print("\nno leak probes hit" if not leaks else f"\n{leaks} packet(s) hit a leak probe")
    return 1 if leaks else 0


def cmd_analyze(args: argparse.Namespace) -> int:
    runs = read_manifest(args.manifest)
    scores = load_scores(args.scores, id_col="run_id")
    # Answer length in words. Chat apps report no token counts, and words are
    # comparable across vendors whose tokenizers differ.
    lengths = None
    if args.captures and Path(args.captures).exists():
        lengths = {p.stem: float(word_count(read_capture(p).final_answer)) for p in Path(args.captures).glob("*.md")}
    families = [f.strip() for f in args.families.split(",") if f.strip()] if args.families else None
    design, rows = run_analysis(
        runs,
        scores,
        args.prompt,
        n_boot=args.boot,
        n_perm=args.perm,
        seed=args.seed,
        lengths=lengths,
        families=families,
    )
    alphas = None
    if args.agreement:
        with Path(args.agreement).open(newline="", encoding="utf-8") as fh:
            alphas = {r["dimension"]: float(r["alpha"]) for r in csv.DictReader(fh)}
    write_outputs(design, rows, args.out, note=args.note, alphas=alphas)
    print(Path(args.out, "variance_table.md").read_text(encoding="utf-8"))
    return 0


def cmd_cells(args: argparse.Namespace) -> int:
    """Cell means (the table view of Figure 1), and Figure 1 itself with --figure."""
    runs = read_manifest(args.manifest)
    if args.families:
        keep = {f.strip() for f in args.families.split(",") if f.strip()}
        runs = [r for r in runs if r.family in keep]
    design = build_design(runs, args.prompt)
    scores = load_scores(args.scores, id_col="run_id")
    out = write_cell_means(design, scores, Path(args.out) / "cell_means.csv")
    print(f"wrote {out}")
    if args.figure:
        fig = plot_cell_means(design, scores, Path(args.out) / args.figure, note=args.note)
        print(f"wrote {fig}")
    return 0


def cmd_rank_agreement(args: argparse.Namespace) -> int:
    """Do raters rank the 12 cells the same way? Kendall's tau-b per pair and W across all."""
    design = build_design(read_manifest(args.manifest), args.prompt)
    sheets = {Path(p).stem.removesuffix("-unblinded"): load_scores(p, id_col="run_id") for p in args.files}
    rows = rank_agreement(sheets, design)
    print(f"{'measure':<8}{'comparison':<26}{'statistic':<15}{'value':>7}")
    for r in rows:
        print(f"{r['measure']!s:<8}{r['comparison']!s:<26}{r['statistic']!s:<15}{float(r['value']):>7.3f}")
    if args.out:
        print(f"\nwrote {write_rank_agreement(rows, args.out)}")
    return 0


def cmd_own_vendor(args: argparse.Namespace) -> int:
    """LLM raters on their own vendor's family, against the other raters (preregistration section 4)."""
    sheets = {Path(p).stem.removesuffix("-unblinded"): load_scores(p, id_col="run_id") for p in args.files}
    rows = []
    for pair in args.pair or ["llm-a=claude", "llm-b=gpt"]:
        rater, _, family = pair.partition("=")
        rows += own_vendor(sheets, rater.strip(), family.strip(), n_boot=args.boot, seed=args.seed)
    print("gap = this rater minus the mean of the other raters; self-preference = own-family gap - baseline gap\n")
    print(f"{'rater':<8}{'family':<9}{'measure':<8}{'own gap':>9}{'baseline':>10}{'self-pref':>11}  95% CI")
    for r in rows:
        print(
            f"{r['rater']!s:<8}{r['family']!s:<9}{r['measure']!s:<8}{float(r['own_gap']):>9.2f}"
            f"{float(r['baseline_gap']):>10.2f}{float(r['self_preference']):>11.2f}  "
            f"[{float(r['self_preference_ci_low']):.2f}, {float(r['self_preference_ci_high']):.2f}]"
        )
    if args.out:
        print(f"\nwrote {write_own_vendor(rows, args.out)}")
    return 0


def cmd_check_modes(args: argparse.Namespace) -> int:
    """Summarise the API-check runs: did each mode switch do what the registry claims?"""
    runs = [r for r in read_manifest(args.manifest) if r.set == API_CHECK]
    caps = {p.stem: read_capture(p) for p in Path(args.captures).glob("*.md")}
    rows = []
    # One row per family and API-check replicate: each replicate past the first calls a
    # different model (api_check_models), and averaging two models would hide both.
    for fam, rep in sorted({(r.family, r.replicate) for r in runs}):
        label = fam if rep == 1 else f"{fam} (check {rep})"
        cells = {}
        for mode in PRIMARY_MODES:
            ids = [r.run_id for r in runs if r.family == fam and r.mode == mode and r.replicate == rep]
            cells[mode] = [caps[i] for i in ids if i in caps]
        if not cells["fast"] and not cells["reasoning"] and rep > 1:
            rows.append((label, "-", "-", "-", "-", "-", "not run yet"))
            continue
        if not cells["fast"] or not cells["reasoning"]:
            rows.append((label, "-", "-", "-", "-", "-", "missing capture(s)"))
            continue

        def stats(capset: list[Capture]) -> tuple[float, float | None, str]:
            words = sum(word_count(c.final_answer) for c in capset) / len(capset)
            rt = [(c.meta.get("usage") or {}).get("reasoning_tokens") for c in capset]
            rt_num = [x for x in rt if isinstance(x, int)]
            reasoning = sum(rt_num) / len(rt_num) if rt_num else None
            models = ",".join(sorted({str(c.meta.get("model_returned")) for c in capset}))
            return words, reasoning, models

        fw, fr, fm = stats(cells["fast"])
        rw, rr, rm = stats(cells["reasoning"])
        has_trace = any(c.reasoning_trace not in {"", "NONE"} for c in cells["reasoning"])
        if fr is not None and rr is not None:
            if fr == 0 and rr > 0:
                verdict = "switch confirmed"
            elif 0 < fr < rr:
                # vendors that cannot disable reasoning: fast is the lowest available level
                verdict = "lowest available: fast reasons less, not zero; record both counts"
            else:
                verdict = "CHECK: reasoning tokens do not separate the modes"
        elif has_trace:
            verdict = "trace present in reasoning mode, confirm fast mode by hand"
        else:
            verdict = "no reasoning token count, confirm from vendor console"
        if fm != rm:
            verdict += f"; models differ ({fm} vs {rm}), confirm same weights"
        rows.append((label, f"{fw:.0f}", f"{rw:.0f}", _n(fr), _n(rr), fm if fm == rm else f"{fm} / {rm}", verdict))

    lines = [
        "# Mode check (API)",
        "",
        "One API call per family and mode. Evidence that each mode switch works. Not scored.",
        "",
        "| Family | Words fast | Words reasoning | Reasoning tokens fast | Reasoning tokens reasoning "
        "| Model returned | Verdict |",
        "|---|---|---|---|---|---|---|",
        *[f"| {' | '.join(row)} |" for row in rows],
    ]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


def _n(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.0f}"


def cmd_demo(args: argparse.Namespace) -> int:
    """Synthetic end-to-end run. Proves the pipeline works before any spend."""
    grid = load_grid(args.config)
    runs = build_manifest(grid)
    prompt_id = grid.prompts[0].id
    fams = sorted({r.family for r in runs})
    scores = synthetic_scores(fams, grid.replicates, prompt_id, seed=args.seed)
    out = Path(args.out or tempfile.mkdtemp(prefix="modegrid-demo-"))
    write_scores(scores, out / "adjudicated-synthetic.csv")
    design, rows = run_analysis(runs, scores, prompt_id, n_boot=args.boot, n_perm=args.boot, seed=args.seed)
    write_outputs(design, rows, out, note="**SYNTHETIC DATA. Pipeline demo only. Not a result.**")
    print(Path(out, "variance_table.md").read_text(encoding="utf-8"))
    print(f"demo outputs in {out}")
    return 0


def cmd_power(args: argparse.Namespace) -> int:
    effect = Effect(args.family_sd, args.mode_shift, args.noise_sd)
    print(f"effect: family_sd={effect.family_sd} mode_shift={effect.mode_shift} noise_sd={effect.noise_sd}")
    print(f"{'families':>9}{'replicates':>11}{'runs':>6}{'delta only':>12}{'H4 rule':>9}")
    for a in args.families:
        for n in args.replicates:
            p = power(effect, a, n, sims=args.sims, seed=args.seed)
            p_dir = power(effect, a, n, sims=args.sims, seed=args.seed, direction=True)
            print(f"{a:>9}{n:>11}{a * 2 * n:>6}{p:>12.2f}{p_dir:>9.2f}")
    return 0


def cmd_hash(args: argparse.Namespace) -> int:
    print(hashlib.sha256(Path(args.path).read_bytes()).hexdigest())
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="modegrid", description=__doc__)
    p.add_argument("--version", action="version", version=f"modegrid {__version__}")
    p.add_argument("--config", default=DEFAULT_CONFIG)
    p.add_argument("--manifest", default=DEFAULT_MANIFEST)
    p.add_argument("--captures", default=DEFAULT_CAPTURES)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("plan", help="expand the grid into data/manifest/runs.csv").set_defaults(func=cmd_plan)

    r = sub.add_parser("run", help="execute API runs that have no capture yet")
    r.add_argument("--family", action="append", help="only this family (repeatable)")
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--retries", type=int, default=4, help="attempts per call; 1 = never re-send")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--run-by", default=getpass.getuser())
    r.set_defaults(func=cmd_run)

    n = sub.add_parser("new-capture", help="create a template for a web-UI run")
    n.add_argument("run_id")
    n.add_argument("--run-by", default=getpass.getuser())
    n.set_defaults(func=cmd_new_capture)

    k = sub.add_parser("check-modes", help="summarise the API mode-check runs")
    k.add_argument("--out", default="results/mode_check.md")
    k.set_defaults(func=cmd_check_modes)

    sub.add_parser("validate", help="check config, prompts, captures and score files").set_defaults(func=cmd_validate)

    b = sub.add_parser("blind", help="build blinded rater packets")
    b.add_argument("--out", default="packets")
    b.add_argument("--key", default="data/blinding/key.csv")
    b.add_argument("--raters", nargs="+", default=["rater1", "rater2"])
    b.set_defaults(func=cmd_blind)

    u = sub.add_parser("unblind", help="map an adjudicated blind score sheet back to run ids")
    u.add_argument("scores")
    u.add_argument("--key", default="data/blinding/key.csv")
    u.add_argument("--out", default="data/scores/adjudicated.csv")
    u.set_defaults(func=cmd_unblind)

    a = sub.add_parser("agreement", help="Krippendorff's alpha per dimension")
    a.add_argument("files", nargs="+")
    a.add_argument("--show", type=int, default=30)
    a.add_argument("--out", default="", help="also write dimension,alpha CSV (input for specbench gate)")
    a.set_defaults(func=cmd_agreement)

    cs = sub.add_parser("consensus", help="median of an odd number of blind rater sheets")
    cs.add_argument("files", nargs="+")
    cs.add_argument("--out", default="data/scores/adjudicated-blind.csv")
    cs.set_defaults(func=cmd_consensus)

    rk = sub.add_parser("rater-kit", help="one self-contained file per answer for each rater")
    rk.add_argument("--raters", nargs="+", required=True)
    rk.add_argument("--packets", default="packets")
    rk.add_argument("--prompt", default="docs/rater-prompt.md")
    rk.add_argument("--rubric", default="vendor/llm-architects/docs/rubric.md")
    rk.add_argument("--protocol", default="docs/scoring.md")
    rk.add_argument("--checker", default="vendor/llm-architects/scripts/memory_budget.py")
    rk.add_argument("--out", default="packets/kit")
    rk.set_defaults(func=cmd_rater_kit)

    rr = sub.add_parser("rater-rows", help="collect CSV rows returned by a rater into their sheet")
    rr.add_argument("rater")
    rr.add_argument("replies", nargs="+", help="text files holding pasted rater replies")
    rr.add_argument("--packets", default="packets")
    rr.add_argument("--final-dir", default="data/scores")
    rr.set_defaults(func=cmd_rater_rows)

    bc = sub.add_parser("blinding-check", help="rater guess accuracy vs chance")
    bc.add_argument("files", nargs="+", help="rater score sheets with guess_family / guess_mode filled")
    bc.add_argument("--key", default="data/blinding/key.csv")
    bc.set_defaults(func=cmd_blinding_check)

    ba = sub.add_parser("blinding-audit", help="before scoring: family fingerprints left in the packets")
    ba.add_argument("--packets", default="packets")
    ba.add_argument("--key", default="data/blinding/key.csv")
    ba.add_argument("--out", default="results/blinding_audit.csv")
    ba.set_defaults(func=cmd_blinding_audit)

    z = sub.add_parser("analyze", help="variance decomposition table")
    z.add_argument("--scores", default="data/scores/adjudicated.csv")
    z.add_argument("--prompt", default="p1-v1")
    z.add_argument("--out", default="results")
    z.add_argument("--boot", type=int, default=5000)
    z.add_argument("--perm", type=int, default=5000)
    z.add_argument("--seed", type=int, default=20261001)
    z.add_argument("--note", default="")
    z.add_argument("--families", default="", help="comma-separated subset, e.g. gpt,qwen,deepseek")
    z.add_argument("--agreement", default="", help="agreement CSV; dimensions below the alpha bar become exploratory")
    z.set_defaults(func=cmd_analyze)

    ce = sub.add_parser("cells", help="cell means per family x mode, and Figure 1")
    ce.add_argument("--scores", default="data/scores/adjudicated.csv")
    ce.add_argument("--prompt", default="p1-v1")
    ce.add_argument("--out", default="results")
    ce.add_argument("--figure", default="", help="file name under --out, e.g. figure1.pdf (needs the paper extra)")
    ce.add_argument("--families", default="", help="comma-separated subset, e.g. gpt,qwen,deepseek")
    ce.add_argument("--note", default="", help="caption line printed on the figure")
    ce.set_defaults(func=cmd_cells)

    ra = sub.add_parser("rank-agreement", help="do raters rank the cells the same way (Kendall tau-b, W)")
    ra.add_argument("files", nargs="+", help="unblinded run-level sheets, one per rater")
    ra.add_argument("--prompt", default="p1-v1")
    ra.add_argument("--out", default="results/cell_rank_agreement.csv")
    ra.set_defaults(func=cmd_rank_agreement)

    ov = sub.add_parser("own-vendor", help="LLM raters' scores for their own vendor's family, reported separately")
    ov.add_argument("files", nargs="+", help="unblinded run-level sheets, one per rater (name-unblinded.csv)")
    ov.add_argument("--pair", action="append", default=None, help="rater=family, default llm-a=claude and llm-b=gpt")
    ov.add_argument("--out", default="results/own_vendor.csv")
    ov.add_argument("--boot", type=int, default=5000)
    ov.add_argument("--seed", type=int, default=20261001)
    ov.set_defaults(func=cmd_own_vendor)

    d = sub.add_parser("demo", help="synthetic end-to-end dry run")
    d.add_argument("--out", default="")
    d.add_argument("--boot", type=int, default=2000)
    d.add_argument("--seed", type=int, default=7)
    d.set_defaults(func=cmd_demo)

    w = sub.add_parser("power", help="simulated power for the primary statistic")
    w.add_argument("--families", type=int, nargs="+", default=[5, 6, 8])
    w.add_argument("--replicates", type=int, nargs="+", default=[3, 5])
    w.add_argument("--mode-shift", type=float, default=1.0)
    w.add_argument("--family-sd", type=float, default=0.5)
    w.add_argument("--noise-sd", type=float, default=0.6)
    w.add_argument("--sims", type=int, default=200)
    w.add_argument("--seed", type=int, default=1)
    w.set_defaults(func=cmd_power)

    h = sub.add_parser("hash", help="sha256 of a file (for freezing a new prompt)")
    h.add_argument("path")
    h.set_defaults(func=cmd_hash)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
