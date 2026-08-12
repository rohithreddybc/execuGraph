"""Generate result-side figures from per-trial JSONL logs.

Companion to ``build_tables.py``. Produces:
  fig_category_bar.pdf      per-category pass-rate by condition (grouped bar)
  fig_cost_accuracy.pdf     wallclock-vs-pass-rate scatter (1 point per condition)
  fig_retry_convergence.pdf cumulative pass-rate as retry budget increases

Usage::

    python -m execugraph.analysis.build_figures results/<run> --out paper/figures
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev


def _load_records(run_dir: Path) -> list[dict]:
    out: list[dict] = []
    for jsonl in run_dir.glob("**/trials.jsonl"):
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _category_bar(records: list[dict], out: Path) -> None:
    import matplotlib.pyplot as plt

    cats = sorted({r["category"] for r in records})
    conds = ["single-oneshot", "single-retry", "multi-full"]
    means: dict[tuple[str, str], float] = {}
    for cat in cats:
        for cond in conds:
            sub = [int(r["passed"]) for r in records if r["category"] == cat and r["condition"] == cond]
            means[(cat, cond)] = (sum(sub) / len(sub)) if sub else 0.0

    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    width = 0.27
    xs = list(range(len(cats)))
    for i, cond in enumerate(conds):
        ys = [100 * means[(c, cond)] for c in cats]
        ax.bar([x + (i - 1) * width for x in xs], ys, width=width, label=cond)
    ax.set_xticks(xs)
    ax.set_xticklabels([c.upper() for c in cats])
    ax.set_ylabel("Pass-rate (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Category-level pass-rate by condition")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, format="pdf")
    plt.close(fig)


def _cost_accuracy(records: list[dict], out: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    by_cond: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_cond[r["condition"]].append(r)
    for cond, sub in by_cond.items():
        if not sub:
            continue
        wc = mean([r["wallclock_s"] for r in sub])
        pr = 100 * mean([int(r["passed"]) for r in sub])
        ax.errorbar(
            wc, pr,
            xerr=pstdev([r["wallclock_s"] for r in sub]) / max(1, len(sub) ** 0.5),
            marker="o", markersize=8, label=cond, capsize=3,
        )
        ax.annotate(cond, (wc, pr), textcoords="offset points", xytext=(8, 4), fontsize=8)
    ax.set_xlabel("Mean wallclock per problem (s)")
    ax.set_ylabel("Pass-rate (%)")
    ax.set_title("Cost-correctness trade-off")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, format="pdf")
    plt.close(fig)


def _retry_convergence(records: list[dict], out: Path) -> None:
    """Cumulative pass-rate as a function of retries-used (budget axis).

    Bucketed: trials that passed at retry $r$ contribute to all $r' \\ge r$.
    """
    import matplotlib.pyplot as plt

    sub = [r for r in records if r["condition"] in {"single-retry", "multi-full"}]
    fig, ax = plt.subplots(figsize=(5.5, 3.0))
    for cond in ("single-retry", "multi-full"):
        cond_sub = [r for r in sub if r["condition"] == cond]
        if not cond_sub:
            continue
        max_b = max((r["retries_used"] for r in cond_sub), default=0)
        xs = list(range(0, max_b + 1))
        ys = []
        for x in xs:
            passed_within = [
                int(r["passed"] and r["retries_used"] <= x) for r in cond_sub
            ]
            ys.append(100 * mean(passed_within) if passed_within else 0.0)
        ax.plot(xs, ys, marker="o", label=cond)
    ax.set_xlabel("Retries used")
    ax.set_ylabel("Cumulative pass-rate (%)")
    ax.set_title("Retry convergence")
    ax.set_ylim(0, 105)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, format="pdf")
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    records = _load_records(args.run_dir)
    if not records:
        print(f"no records in {args.run_dir}; nothing to plot")
        return 0
    print(f"loaded {len(records)} records from {args.run_dir}")
    try:
        import matplotlib  # noqa
    except ImportError:
        print("matplotlib not installed; skipping figures.")
        return 0

    _category_bar(records, args.out / "fig_category_bar.pdf")
    _cost_accuracy(records, args.out / "fig_cost_accuracy.pdf")
    _retry_convergence(records, args.out / "fig_retry_convergence.pdf")
    print(f"wrote figures to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys
    sys.exit(main())
