"""Read per-trial JSONL logs and emit the LaTeX table fragments
the paper \\input{}s.

Usage::

    python -m execugraph.analysis.build_tables results/<run> --out paper/tables
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from .stats import paired_compare, per_problem_passrate

TODO = r"\todo{}"


def _load_records(run_dir: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for jsonl in run_dir.glob("**/trials.jsonl"):
        run_tag = jsonl.parent.name  # e.g. "e1_mf", "e4_no_planner", "e7_xm_so"
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rec = json.loads(line)
                rec.setdefault("_run", run_tag)
                out.append(rec)
    return out


def _headline_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Records that constitute the headline internal-30 experiment.

    The ablation (e4_*), retry-sweep (e5_*), cross-model (e7_*) and
    supplementary (e9_*) runs all reuse the ``multi-full`` /
    ``single-oneshot`` condition labels but are NOT the headline grid.
    Pooling them silently inflates the trial count and blends models,
    so the per-problem / category / failure / cost / error-class tables
    must restrict to the canonical ``e1_*`` runs (primary backbone,
    5 trials per problem). External benchmarks (HumanEval/APPS) are
    excluded here by the category filter inside each table builder.
    """
    return [r for r in records if str(r.get("_run", "")).startswith("e1_")]


def _fmt_pct(x: float | None) -> str:
    return TODO if x is None else f"{100*x:.1f}"


def _fmt_p(x: float) -> str:
    if x != x:  # NaN
        return TODO
    if x < 0.001:
        return r"$<$0.001"
    return f"{x:.3f}"


def _condition_short(cond: str) -> str:
    return {
        "single-oneshot": "SO",
        "single-retry": "SR",
        "multi-full": "MF",
    }.get(cond, cond)


def _table_header_problem_level(records: list[dict[str, Any]]) -> str:
    # Only show internal-30 problems (exclude APPS-benchmark and HumanEval entries)
    _internal_cats = {"dp", "graph", "ds", "DP", "GRAPH", "DS"}
    records = [r for r in records if r.get("category", "").upper() in {"DP", "GRAPH", "DS"}]
    pr = per_problem_passrate(records)
    by_cond: dict[str, dict[str, float]] = defaultdict(dict)
    for (pid, cond), rate in pr.items():
        by_cond[cond][pid] = rate
    pid_meta: dict[str, dict[str, str]] = {}
    for r in records:
        pid_meta.setdefault(r["problem_id"], {"category": r["category"], "source": r["source"]})

    # Sort by category then problem id for a clean grouped layout
    def _sort_key(pid: str) -> tuple[str, str]:
        cat = pid_meta[pid]["category"].upper()
        order = {"DP": "0", "GRAPH": "1", "DS": "2"}
        return (order.get(cat, "9"), pid)

    rows = []
    prev_cat = None
    for pid in sorted(pid_meta, key=_sort_key):
        meta = pid_meta[pid]
        cat = meta["category"].upper()
        if cat != prev_cat and prev_cat is not None:
            rows.append(r"\midrule")
        prev_cat = cat
        src = meta["source"]
        src_tex = r"APPS$^\dagger$" if "apps" in src.lower() else "internal"
        row = [pid.replace("_", r"\_"), cat, src_tex]
        for cond in ("single-oneshot", "single-retry", "multi-full"):
            row.append(_fmt_pct(by_cond.get(cond, {}).get(pid)))
        rows.append(" & ".join(row) + r" \\")
    body = "\n".join(rows) if rows else (r"\multicolumn{6}{c}{" + TODO + r"} \\")
    return (
        r"\begin{tabular}{@{}llcrrr@{}}" "\n"
        r"\toprule" "\n"
        r"Problem & Cat & Src & SO\,\% & SR\,\% & MF\,\% \\" "\n"
        r"\midrule" "\n"
        f"{body}\n"
        r"\bottomrule" "\n"
        r"\end{tabular}" "\n"
    )


def _table_category(records: list[dict[str, Any]]) -> str:
    if not records:
        return _stub_one_col()
    cats = sorted({r["category"] for r in records})
    rows = []
    for cat in cats:
        cat_records = [r for r in records if r["category"] == cat]
        pr = per_problem_passrate(cat_records)
        means: dict[str, list[float]] = defaultdict(list)
        for (_, cond), rate in pr.items():
            means[cond].append(rate)
        cell_so = _fmt_pct(mean(means["single-oneshot"])) if means.get("single-oneshot") else TODO
        cell_sr = _fmt_pct(mean(means["single-retry"])) if means.get("single-retry") else TODO
        cell_mf = _fmt_pct(mean(means["multi-full"])) if means.get("multi-full") else TODO
        if means.get("single-oneshot") and means.get("multi-full"):
            stat_so_mf = paired_compare(cat_records, a="single-oneshot", b="multi-full")
            p_so_mf = _fmt_p(stat_so_mf.wilcoxon_p)
        else:
            p_so_mf = TODO
        if means.get("single-retry") and means.get("multi-full"):
            stat_sr_mf = paired_compare(cat_records, a="single-retry", b="multi-full")
            p_sr_mf = _fmt_p(stat_sr_mf.wilcoxon_p)
        else:
            p_sr_mf = TODO
        rows.append(
            f"{cat.upper()} & {cell_so} & {cell_sr} & {cell_mf} & {p_so_mf} & {p_sr_mf} " + r"\\"
        )
    body = "\n".join(rows)
    return (
        r"\begin{tabular}{@{}lrrrrr@{}}" "\n"
        r"\toprule" "\n"
        r"Category & SO & SR & MF & $p_{\text{SO}\!\to\!\text{MF}}$ & $p_{\text{SR}\!\to\!\text{MF}}$ \\" "\n"
        r"\midrule" "\n"
        f"{body}\n"
        r"\bottomrule" "\n"
        r"\end{tabular}" "\n"
    )


def _table_failure(records: list[dict[str, Any]]) -> str:
    if not records:
        return _stub_one_col()
    cats = sorted({r["category"] for r in records})
    bucket: dict[tuple[str, str], list[int]] = defaultdict(list)
    for r in records:
        crashed = int(r["error_class"] not in {"none", "wrong_answer"})
        bucket[(r["category"], r["condition"])].append(crashed)
    rows = []
    for cat in cats:
        cells = []
        for cond in ("single-oneshot", "single-retry", "multi-full"):
            v = bucket.get((cat, cond))
            cells.append(_fmt_pct(mean(v)) if v else TODO)
        rows.append(f"{cat.upper()} & {' & '.join(cells)} " + r"\\")
    body = "\n".join(rows)
    return (
        r"\begin{tabular}{@{}lrrr@{}}" "\n"
        r"\toprule" "\n"
        r"Category & SO & SR & MF \\" "\n"
        r"\midrule" "\n"
        f"{body}\n"
        r"\bottomrule" "\n"
        r"\end{tabular}" "\n"
    )


def _table_cost(records: list[dict[str, Any]]) -> str:
    if not records:
        return _stub_one_col()
    rows = []
    for cond in ("single-oneshot", "single-retry", "multi-full"):
        sub = [r for r in records if r["condition"] == cond]
        if not sub:
            rows.append(f"{cond} & {TODO} & {TODO} & {TODO} " + r"\\")
            continue
        wc = [r["wallclock_s"] for r in sub]
        tk = [r["tokens_in"] + r["tokens_out"] for r in sub]
        cl = [r["llm_calls"] for r in sub]
        rows.append(
            f"{cond} & "
            f"{mean(wc):.1f}$\\pm${pstdev(wc):.1f} & "
            f"{mean(tk):.0f}$\\pm${pstdev(tk):.0f} & "
            f"{mean(cl):.1f}$\\pm${pstdev(cl):.1f} " + r"\\"
        )
    body = "\n".join(rows)
    return (
        r"\begin{tabular}{@{}lrrr@{}}" "\n"
        r"\toprule" "\n"
        r"Condition & Wallclock (s) & Tokens & LLM calls \\" "\n"
        r"\midrule" "\n"
        f"{body}\n"
        r"\bottomrule" "\n"
        r"\end{tabular}" "\n"
    )


def _stub_one_col() -> str:
    return (
        r"\begin{tabular}{@{}c@{}}" "\n"
        r"\toprule" "\n"
        r"Status \\" "\n"
        r"\midrule" "\n"
        f"{TODO} \\\\\n"
        r"\bottomrule" "\n"
        r"\end{tabular}" "\n"
    )


def _table_errortax(records: list[dict[str, Any]]) -> str:
    if not records:
        return _stub_one_col()
    classes = ["syntax", "runtime", "timeout", "wrong_answer", "sandbox_violation", "harness_error"]
    bucket: dict[tuple[str, str], int] = defaultdict(int)
    totals: dict[str, int] = defaultdict(int)
    for r in records:
        if r["passed"]:
            continue
        cond = r["condition"]
        bucket[(cond, r["error_class"])] += 1
        totals[cond] += 1
    header = " & ".join([r"Class"] + ["SO", "SR", "MF"]) + r" \\"
    rows = [header, r"\midrule"]
    for cls in classes:
        cells = []
        for cond in ("single-oneshot", "single-retry", "multi-full"):
            tot = totals.get(cond, 0)
            cnt = bucket.get((cond, cls), 0)
            cells.append(f"{(100*cnt/tot):.1f}" if tot else TODO)
        cls_tex = cls.replace("_", r"\_")
        rows.append(f"{cls_tex} & {' & '.join(cells)} " + r"\\")
    body = "\n".join(rows)
    return (
        r"\begin{tabular}{@{}lrrr@{}}" "\n"
        r"\toprule" "\n"
        f"{body}\n"
        r"\bottomrule" "\n"
        r"\end{tabular}" "\n"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    records = _load_records(args.run_dir)
    # Headline internal-30 tables use only the canonical e1_* runs so that
    # ablation/retry-sweep/cross-model/supplementary runs (which reuse the
    # same condition labels) do not contaminate the primary-backbone numbers.
    headline = _headline_records(records) or records
    print(
        f"loaded {len(records)} trial records from {args.run_dir} "
        f"({len(headline)} in the headline e1_* grid)"
    )

    (args.out / "tab3_problem_level.tex").write_text(_table_header_problem_level(headline), encoding="utf-8")
    (args.out / "tab4_category.tex").write_text(_table_category(headline), encoding="utf-8")
    (args.out / "tab5_failure.tex").write_text(_table_failure(headline), encoding="utf-8")
    (args.out / "tab6_cost.tex").write_text(_table_cost(headline), encoding="utf-8")
    (args.out / "tab11_errortax.tex").write_text(_table_errortax(headline), encoding="utf-8")
    # The remaining ablation / retry-sweep / external / cross-model / test-source tables
    # are populated by hand from specialized run directories (e4_*, e5_*, e7_*, etc.).
    # Only emit a stub when the file is missing — never overwrite existing real data.
    for stub in ("tab7_ablation", "tab8_retry_sweep", "tab9_external", "tab10_crossmodel", "tab12_testsource"):
        stub_path = args.out / f"{stub}.tex"
        if not stub_path.exists():
            stub_path.write_text(_stub_one_col(), encoding="utf-8")
    print(f"wrote tables to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys
    sys.exit(main())
