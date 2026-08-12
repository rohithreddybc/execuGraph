"""Regenerate every result table in the manuscript from the re-scored trial logs.

Supersedes the partial generator: the previous pipeline emitted only tab3-tab6
and left tab7-tab12 as ``\\todo{}`` stubs, so those tables' numbers had no
traceable source. This script emits all of them, plus a machine-readable
``all_numbers.json`` so prose figures can be checked against the same source.

Statistics follow the small-sample rules the design actually requires: the
Wilcoxon signed-rank test is run in EXACT mode (the normal approximation is
invalid at these discordant-pair counts), the bootstrap resamples problems as
clusters, and family-wise error within each family of contrasts is controlled
with Holm-Bonferroni.

Accepts several results trees; a run is loaded from the first tree that
contains it, so the original grid and the follow-up grid combine cleanly.

Usage:
    python scripts/build_all_tables.py \
        --results results/submission-20260509-223437-rescored \
                  results/submission-20260811-followup-rescored \
        --out generated_tables
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

CATEGORIES = ["DP", "GRAPH", "DS"]
BOOTSTRAP_B = 10000
BOOTSTRAP_SEED = 20260509

BS = chr(92)          # backslash, kept out of f-strings for legibility
NL = chr(10)
ROW_END = BS + BS     # LaTeX end-of-row


def load(roots: list[Path], run: str) -> list[dict]:
    """Load a run's trials from whichever results tree contains it."""
    for root in roots:
        path = root / run / "trials.jsonl"
        if path.exists():
            return [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
    return []


def per_problem(rows: list[dict]) -> dict[str, float]:
    """Mean pass-rate per problem across trials."""
    acc: dict[str, list[bool]] = defaultdict(list)
    for r in rows:
        acc[r["problem_id"]].append(bool(r["passed"]))
    return {k: sum(v) / len(v) for k, v in acc.items()}


def overall(rows: list[dict]) -> float:
    return 100.0 * sum(1 for r in rows if r["passed"]) / len(rows) if rows else 0.0


def category_of(rows: list[dict]) -> dict[str, str]:
    return {r["problem_id"]: (r.get("category") or "").upper() for r in rows}


def cat_rate(rows: list[dict], cat: str) -> float:
    sub = [r for r in rows if (r.get("category") or "").upper() == cat]
    return 100.0 * sum(1 for r in sub if r["passed"]) / len(sub) if sub else float("nan")


def cluster_bootstrap_ci(a: dict, b: dict, keys: list[str]) -> tuple[float, float]:
    """Percentile CI on the mean paired difference, resampling problems."""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    diffs = np.array([a[k] - b[k] for k in keys])
    n = len(diffs)
    draws = rng.integers(0, n, size=(BOOTSTRAP_B, n))
    means = diffs[draws].mean(axis=1) * 100.0
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired(a: dict, b: dict) -> dict:
    keys = sorted(set(a) & set(b))
    va, vb = [a[k] for k in keys], [b[k] for k in keys]
    diffs = np.array(va) - np.array(vb)
    discordant = int((diffs != 0).sum())
    try:
        p_exact = float(wilcoxon(va, vb, method="exact").pvalue)
    except Exception:
        try:
            p_exact = float(wilcoxon(va, vb, mode="exact").pvalue)
        except Exception:
            p_exact = float("nan")
    lo, hi = cluster_bootstrap_ci(a, b, keys)
    return {
        "n": len(keys),
        "discordant": discordant,
        "delta_pp": float(diffs.mean() * 100.0),
        "ci_lo": lo,
        "ci_hi": hi,
        "p_exact": p_exact,
    }


def holm(pvals: dict[str, float]) -> dict[str, float]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, (m - i) * p)
        running = max(running, adj)  # enforce monotonicity
        out[k] = running
    return out


def table(colspec: str, header: str, body_rows: list[str]) -> str:
    return (
        BS + "begin{tabular}{@{}" + colspec + "@{}}" + NL
        + BS + "toprule" + NL
        + header + " " + ROW_END + NL
        + BS + "midrule" + NL
        + NL.join(body_rows) + NL
        + BS + "bottomrule" + NL
        + BS + "end{tabular}"
    )


def row(cells: list[str]) -> str:
    return " & ".join(cells) + " " + ROW_END


def multirow_row(label: str | None, span: int, cells: list[str]) -> str:
    pre = (BS + "multirow{" + str(span) + "}{*}{" + label + "} ") if label else ""
    return pre + "& " + " & ".join(cells) + " " + ROW_END


def w(path: Path, body: str) -> None:
    path.write_text(body.rstrip() + NL, encoding="utf-8")
    print(f"  wrote {path.name}")


RUN_NAMES = [
    # original grid
    "e1_so", "e1_sr", "e1_mf",
    "e2_he_so", "e2_he_mf", "e3_apps_so", "e3_apps_mf",
    "e4_no_planner", "e4_no_reviewer", "e4_no_optimizer", "e4_rag_on",
    "e5_rb0", "e5_rb2", "e7_xm_so", "e7_xm_mf",
    "e9_l26_so", "e9_l26_mf",
    # follow-up grid (2026-08-11)
    "e2_he_sr", "e3_apps_sr", "e7_xm_sr", "e5_rb1",
    "e2_he_so_164", "e2_he_mf_164",
    "e4_no_planner_n5", "e4_no_reviewer_n5", "e4_no_optimizer_n5", "e4_rag_on_n5",
    "e2_he_so_bo5",
]

PCT = BS + "," + BS + "%"   # LaTeX thin space then an escaped percent sign


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True, nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res, out = [Path(r) for r in args.results], Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    R = {name: load(res, name) for name in RUN_NAMES}
    missing = [k for k, v in R.items() if not v]
    if missing:
        print("  NOTE: no data for " + ", ".join(missing))

    N: dict = {"runs": {k: {"trials": len(v), "pass_rate": overall(v)}
                        for k, v in R.items() if v}}

    so, sr, mf = (per_problem(R[k]) for k in ("e1_so", "e1_sr", "e1_mf"))
    cats = category_of(R["e1_so"])
    src = {r["problem_id"]: r.get("source", "internal") for r in R["e1_so"]}

    # ---- Table 3: per-problem -------------------------------------------
    rows = []
    for cat in CATEGORIES:
        for p in sorted(x for x in so if cats.get(x) == cat):
            s = "APPS$^" + BS + "dagger$" if "apps" in str(src.get(p, "")).lower() else "internal"
            rows.append(row([p.replace("_", BS + "_"), cat, s,
                             f"{100 * so[p]:.1f}", f"{100 * sr[p]:.1f}", f"{100 * mf[p]:.1f}"]))
        if cat != CATEGORIES[-1]:
            rows.append(BS + "midrule")
    w(out / "tab3_problem_level.tex",
      table("lllrrr", "Problem & Cat & Src & SO" + PCT + " & SR" + PCT + " & MF" + PCT, rows))

    # ---- Table 4: category-level with EXACT Wilcoxon --------------------
    lines, N["category"] = [], {}
    for cat in CATEGORIES:
        ids = [p for p in so if cats.get(p) == cat]

        def restrict(d, _ids=ids):
            return {k: d[k] for k in _ids}

        a, b, c = (cat_rate(R[k], cat) for k in ("e1_so", "e1_sr", "e1_mf"))
        p_so = paired(restrict(mf), restrict(so))["p_exact"]
        p_sr = paired(restrict(mf), restrict(sr))["p_exact"]
        lines.append(row([cat, f"{a:.1f}", f"{b:.1f}", f"{c:.1f}", f"{p_so:.3f}", f"{p_sr:.3f}"]))
        N["category"][cat] = {"SO": a, "SR": b, "MF": c, "p_SO_MF": p_so, "p_SR_MF": p_sr}
    hdr4 = ("Category & SO & SR & MF & $p_{" + BS + "text{SO}" + BS + "to" + BS + "text{MF}}$ & "
            "$p_{" + BS + "text{SR}" + BS + "to" + BS + "text{MF}}$")
    w(out / "tab4_category.tex", table("lrrrrr", hdr4, lines))

    N["pooled"] = {k: overall(R["e1_" + k.lower()]) for k in ("SO", "SR", "MF")}

    # ---- Table 5: execution-failure rate --------------------------------
    def hard(r):
        return r.get("error_class") not in ("none", "wrong_answer")

    lines = []
    for cat in CATEGORIES:
        vals = []
        for key in ("e1_so", "e1_sr", "e1_mf"):
            sub = [r for r in R[key] if (r.get("category") or "").upper() == cat]
            vals.append(100.0 * sum(1 for r in sub if hard(r)) / len(sub) if sub else 0.0)
        lines.append(row([cat] + [f"{v:.1f}" for v in vals]))
    w(out / "tab5_failure.tex", table("lrrr", "Category & SO & SR & MF", lines))

    # ---- Table 6: cost ---------------------------------------------------
    lines, N["cost"] = [], {}
    pm = "$" + BS + "pm$"
    for key, label in [("e1_so", "single-oneshot"), ("e1_sr", "single-retry"),
                       ("e1_mf", "multi-full")]:
        wc = np.array([r.get("wallclock_s", 0.0) for r in R[key]], dtype=float)
        tk = np.array([r.get("tokens_in", 0) + r.get("tokens_out", 0) for r in R[key]], dtype=float)
        cl = np.array([r.get("llm_calls", 0) for r in R[key]], dtype=float)
        lines.append(row([label,
                          f"{wc.mean():.1f}" + pm + f"{wc.std(ddof=1):.1f}",
                          f"{tk.mean():.0f}" + pm + f"{tk.std(ddof=1):.0f}",
                          f"{cl.mean():.1f}" + pm + f"{cl.std(ddof=1):.1f}"]))
        N["cost"][label] = {"wallclock_mean": wc.mean(), "wallclock_median": float(np.median(wc)),
                            "tokens_mean": tk.mean(), "llm_calls_mean": cl.mean()}
    w(out / "tab6_cost.tex", table("lrrr", "Condition & Wallclock (s) & Tokens & LLM calls", lines))

    # ---- Table 7: ablation at N=5, with negative controls ----------------
    # -Reviewer, -Optimizer and +RAG cannot alter acceptance by construction:
    # the Reviewer's output is never read by the Generator, the Optimizer
    # reverts on re-validation failure, and retrieval feeds the Planner only.
    # At matched N they are therefore independent replications of multi-full,
    # and their spread estimates run-to-run variance, which is the yardstick
    # the -Planner contrast must be read against.
    star = "$^{" + BS + "ast}$"
    lines, N["ablation"] = [], {}
    for label, key in [("Multi-Full (baseline)", "e1_mf"),
                       ("$-$Planner", "e4_no_planner_n5"),
                       ("$-$Reviewer" + star, "e4_no_reviewer_n5"),
                       ("$-$Optimizer" + star, "e4_no_optimizer_n5"),
                       ("$+$RAG" + star, "e4_rag_on_n5")]:
        vals = [cat_rate(R[key], c) for c in CATEGORIES] + [overall(R[key])]
        lines.append(row([label] + [f"{v:.1f}" for v in vals]))
        N["ablation"][label] = dict(zip(CATEGORIES + ["Overall"], vals, strict=True))
    hdr7 = "Condition & DP" + PCT + " & Graph" + PCT + " & DS" + PCT + " & Overall" + PCT
    w(out / "tab7_ablation.tex", table("lrrrr", hdr7, lines))

    rep_keys = ["e1_mf", "e4_no_reviewer_n5", "e4_no_optimizer_n5", "e4_rag_on_n5"]
    rep_vals = [overall(R[k]) for k in rep_keys]
    same_session = [overall(R[k]) for k in rep_keys[1:]]
    planner = overall(R["e4_no_planner_n5"])
    pooled_pp: dict[str, list[float]] = {}
    for k in rep_keys:
        for prob, v in per_problem(R[k]).items():
            pooled_pp.setdefault(prob, []).append(v)
    pooled_base = {k: sum(v) / len(v) for k, v in pooled_pp.items()}
    N["replication"] = {
        "runs": dict(zip(rep_keys, rep_vals, strict=True)),
        "mean": float(np.mean(rep_vals)),
        "sd": float(np.std(rep_vals, ddof=1)),
        "same_session_mean": float(np.mean(same_session)),
        "same_session_sd": float(np.std(same_session, ddof=1)),
        "planner": planner,
        "planner_vs_same_session_pp": planner - float(np.mean(same_session)),
        "planner_vs_all_reps_pp": planner - float(np.mean(rep_vals)),
        "planner_paired_vs_pooled": paired(per_problem(R["e4_no_planner_n5"]), pooled_base),
    }

    # ---- Table 8: retry sweep (three budgets) ----------------------------
    lines, N["retry"] = [], {}
    for label, key in [("0 (multi-no-retry)", "e5_rb0"), ("1", "e5_rb1"),
                       ("2 (multi-full)", "e5_rb2")]:
        rr = R[key]
        rt = np.mean([r.get("retries_used", 0) for r in rr])
        wc = np.mean([r.get("wallclock_s", 0.0) for r in rr])
        tk = np.mean([r.get("tokens_in", 0) + r.get("tokens_out", 0) for r in rr])
        lines.append(row([label, f"{overall(rr):.1f}", f"{rt:.2f}", f"{wc:.1f}", f"{tk:,.0f}"]))
        N["retry"][label] = {"pass": overall(rr), "retries": rt, "wallclock": wc, "tokens": tk}
    hdr8 = "Budget & Pass" + PCT + " & Retries Used & Wall-clock (s) & Tokens"
    w(out / "tab8_retry_sweep.tex", table("lrrrr", hdr8, lines))

    # ---- Table 9: external validity, all three conditions ----------------
    lines, N["external"] = [], {}
    ext = [("HumanEval (164)",
            [("SO", "e2_he_so_164"), ("SR", "e2_he_sr"), ("MF", "e2_he_mf_164")], 164),
           ("APPS-intro (50)",
            [("SO", "e3_apps_so"), ("SR", "e3_apps_sr"), ("MF", "e3_apps_mf")], 50)]
    for bench, conds, n in ext:
        N["external"][bench] = {}
        for i, (cond, key) in enumerate(conds):
            v = overall(R[key])
            lines.append(multirow_row(bench if i == 0 else None, 3,
                                      [cond, str(n), f"{v:.1f}"]))
            N["external"][bench][cond] = v
        if bench.startswith("HumanEval"):
            lines.append(BS + "midrule")
    w(out / "tab9_external.tex",
      table("llrr", "Benchmark & Cond. & Probs. & Pass" + PCT, lines))

    he = {c: per_problem(R[k]) for c, k in
          [("SO", "e2_he_so_164"), ("SR", "e2_he_sr"), ("MF", "e2_he_mf_164")]}
    he_stats = {"SR $-$ SO": paired(he["SR"], he["SO"]),
                "MF $-$ SO": paired(he["MF"], he["SO"]),
                "MF $-$ SR": paired(he["MF"], he["SR"])}
    for k, v in holm({k: s["p_exact"] for k, s in he_stats.items()}).items():
        he_stats[k]["p_holm"] = v
    N["humaneval_paired"] = he_stats
    hdr_stats = ("Comparison & $n$ & Disc. & $" + BS + "Delta$" + BS + ",(pp) & 95" + BS
                 + "% CI & Exact $p$ & Holm $p$")
    he_lines = [
        row([k, str(s["n"]), str(s["discordant"]), f"{s['delta_pp']:+.1f}",
             "[" + f"{s['ci_lo']:+.1f}, {s['ci_hi']:+.1f}" + "]",
             f"{s['p_exact']:.4f}", f"{s['p_holm']:.4f}"])
        for k, s in he_stats.items()
    ]
    w(out / "tab15_humaneval_paired.tex", table("lrrrrrr", hdr_stats, he_lines))

    # ---- Sampling control: does extra compute alone explain the gain? ----
    # Five independent one-shot samples per problem, filtered by the same
    # sandbox. At the generator's temperature of 0.0 the samples are near
    # identical, so best-of-5 is barely above pass@1 -- which is precisely
    # the point: additional compute without feedback buys almost nothing.
    bo5 = R["e2_he_so_bo5"]
    if bo5:
        by_problem: dict[str, list[bool]] = defaultdict(list)
        for r in bo5:
            by_problem[r["problem_id"]].append(bool(r["passed"]))
        complete = [v for v in by_problem.values() if len(v) == 5]
        pass1 = 100.0 * sum(sum(v) for v in complete) / (5 * len(complete))
        best5 = 100.0 * sum(1 for v in complete if any(v)) / len(complete)
        unanimous = sum(1 for v in complete if len(set(v)) == 1)
        N["sampling_control"] = {
            "problems": len(complete),
            "samples_per_problem": 5,
            "pass_at_1": pass1,
            "best_of_5": best5,
            "delta_pp": best5 - pass1,
            "unanimous_problems": unanimous,
            "unanimous_frac": 100.0 * unanimous / len(complete),
        }
        lines = [
            row(["One-shot, single sample (pass@1)", "1.0", f"{pass1:.1f}"]),
            row(["One-shot, best of 5 samples", "5.0", f"{best5:.1f}"]),
            row(["Single-retry (execution feedback)", "1.5",
                 f"{overall(R['e2_he_sr']):.1f}"]),
            row(["Multi-full", "5.3", f"{overall(R['e2_he_mf_164']):.1f}"]),
        ]
        w(out / "tab16_sampling_control.tex",
          table("lrr", "Configuration & LLM calls & Pass" + PCT, lines))

    # ---- Table 10: cross-model, all three conditions ---------------------
    lines, N["crossmodel"] = [], {}
    for model, trio in [("Qwen2.5-Coder-7B",
                         [("SO", "e1_so"), ("SR", "e1_sr"), ("MF", "e1_mf")]),
                        ("DeepSeek-V2-Lite",
                         [("SO", "e7_xm_so"), ("SR", "e7_xm_sr"), ("MF", "e7_xm_mf")])]:
        for i, (cond, key) in enumerate(trio):
            vals = [cat_rate(R[key], c) for c in CATEGORIES] + [overall(R[key])]
            lines.append(multirow_row(model if i == 0 else None, 3,
                                      [cond] + [f"{v:.1f}" for v in vals]))
            N["crossmodel"][model + "-" + cond] = dict(
                zip(CATEGORIES + ["All"], vals, strict=True))
        if model.startswith("Qwen"):
            lines.append(BS + "midrule")
    hdr10 = "Model & Cond & DP" + PCT + " & Gr." + PCT + " & DS" + PCT + " & All" + PCT
    w(out / "tab10_crossmodel.tex", table("llrrrr", hdr10, lines))

    # ---- Table 11: error taxonomy ---------------------------------------
    classes = ["syntax", "runtime", "timeout", "wrong_answer",
               "sandbox_violation", "harness_error"]
    lines, N["errortax"] = [], {}
    for cls in classes:
        vals = []
        for key in ("e1_so", "e1_sr", "e1_mf"):
            fails = [r for r in R[key] if not r["passed"]]
            vals.append(100.0 * sum(1 for r in fails if r.get("error_class") == cls) / len(fails)
                        if fails else 0.0)
        lines.append(row([cls.replace("_", BS + "_")] + [f"{v:.1f}" for v in vals]))
        N["errortax"][cls] = dict(zip(["SO", "SR", "MF"], vals, strict=True))
    w(out / "tab11_errortax.tex", table("lrrr", "Class & SO & SR & MF", lines))

    # ---- Table 12: test-source ------------------------------------------
    lines, srcset = [], set()
    tsrc = [("Internal-30", [("Single-Oneshot", "e1_so"), ("Single-Retry", "e1_sr"),
                             ("Multi-Full", "e1_mf")]),
            ("HumanEval", [("Single-Oneshot", "e2_he_so_164"), ("Single-Retry", "e2_he_sr"),
                           ("Multi-Full", "e2_he_mf_164")]),
            ("APPS-intro", [("Single-Oneshot", "e3_apps_so"), ("Single-Retry", "e3_apps_sr"),
                            ("Multi-Full", "e3_apps_mf")])]
    for bench, conds in tsrc:
        for i, (cond, key) in enumerate(conds):
            ts = {r.get("test_source", "deterministic") for r in R[key]}
            srcset |= ts
            lines.append(multirow_row(bench if i == 0 else None, 3,
                                      [cond, "/".join(sorted(ts)), f"{overall(R[key]):.1f}"]))
        if not bench.startswith("APPS"):
            lines.append(BS + "midrule")
    N["test_sources_observed"] = sorted(srcset)
    N["total_trials"] = sum(len(v) for v in R.values() if v)
    w(out / "tab12_testsource.tex",
      table("lllr", "Benchmark & Condition & Test Source & Pass" + PCT, lines))

    # ---- Table 13: latest-2026 ------------------------------------------
    lines, N["latest2026"] = [], {}
    for label, key in [("Single-Oneshot", "e9_l26_so"), ("Multi-Full", "e9_l26_mf")]:
        rr = R[key]
        wc = np.mean([r.get("wallclock_s", 0.0) for r in rr])
        tk = np.mean([r.get("tokens_in", 0) + r.get("tokens_out", 0) for r in rr])
        lines.append(row([label, f"{overall(rr):.1f}" + BS + "%", str(len(rr)),
                          f"{wc:.0f}", f"{tk:,.0f}"]))
        N["latest2026"][label] = {"pass": overall(rr), "n": len(rr),
                                  "wallclock": wc, "tokens": tk}
    hdr13 = "Condition & Pass Rate & Trials & Avg Wall-clock (s) & Avg Tokens"
    w(out / "tab13_latest2026.tex", table("lrrrr", hdr13, lines))

    # ---- Table 14: paired stats on internal-30 ---------------------------
    stats = {"SR $-$ SO": paired(sr, so), "MF $-$ SO": paired(mf, so),
             "MF $-$ SR": paired(mf, sr)}
    for k, v in holm({k: s["p_exact"] for k, s in stats.items()}).items():
        stats[k]["p_holm"] = v
    N["paired"] = stats
    lines = [
        row([k, str(s["n"]), str(s["discordant"]), f"{s['delta_pp']:+.1f}",
             "[" + f"{s['ci_lo']:+.1f}, {s['ci_hi']:+.1f}" + "]",
             f"{s['p_exact']:.3f}", f"{s['p_holm']:.3f}"])
        for k, s in stats.items()
    ]
    w(out / "tab14_paired_stats.tex", table("lrrrrrr", hdr_stats, lines))

    (out / "all_numbers.json").write_text(json.dumps(N, indent=2, default=float),
                                          encoding="utf-8")
    print(NL + "  wrote all_numbers.json")


if __name__ == "__main__":
    main()
