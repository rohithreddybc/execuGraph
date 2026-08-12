"""Paired Wilcoxon, McNemar, and bootstrap CIs over per-trial logs."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass
class PairedStat:
    n_pairs: int
    mean_diff: float
    wilcoxon_p: float
    mcnemar_p: float
    ci_lo: float
    ci_hi: float


def per_problem_passrate(records: list[dict[str, Any]]) -> dict[tuple[str, str], float]:
    """Return mean pass-rate per (problem_id, condition) over all trials."""
    bucket: dict[tuple[str, str], list[int]] = defaultdict(list)
    for r in records:
        bucket[(r["problem_id"], r["condition"])].append(int(bool(r["passed"])))
    return {k: (sum(v) / len(v)) for k, v in bucket.items()}


def paired_compare(
    records: list[dict[str, Any]],
    *,
    a: str,
    b: str,
    bootstrap_n: int = 2000,
    seed: int = 0,
) -> PairedStat:
    """Compare condition ``a`` (baseline) against ``b`` (treatment)."""
    import random

    pr = per_problem_passrate(records)
    pids_a = {pid for (pid, cond) in pr if cond == a}
    pids_b = {pid for (pid, cond) in pr if cond == b}
    common = sorted(pids_a & pids_b)
    diffs = [pr[(pid, b)] - pr[(pid, a)] for pid in common]
    n = len(diffs)
    if n == 0:
        return PairedStat(0, 0.0, 1.0, 1.0, 0.0, 0.0)

    # Wilcoxon signed-rank (scipy is in deps; fall back to mean-only if missing).
    try:
        from scipy.stats import wilcoxon  # type: ignore

        if all(d == 0 for d in diffs):
            wilc_p = 1.0
        else:
            _, wilc_p = wilcoxon(diffs, zero_method="wilcox", alternative="two-sided")
    except Exception:
        wilc_p = float("nan")

    # McNemar on per-problem outcome (a passed, b passed); use trial-majority.
    bin_a, bin_b = {}, {}
    for r in records:
        key = r["problem_id"]
        if r["condition"] == a:
            bin_a.setdefault(key, []).append(int(bool(r["passed"])))
        elif r["condition"] == b:
            bin_b.setdefault(key, []).append(int(bool(r["passed"])))
    b01 = b10 = 0
    for pid in common:
        ma = round(sum(bin_a[pid]) / len(bin_a[pid]))
        mb = round(sum(bin_b[pid]) / len(bin_b[pid]))
        if ma == 0 and mb == 1:
            b01 += 1
        elif ma == 1 and mb == 0:
            b10 += 1
    try:
        from scipy.stats import binomtest  # type: ignore

        if (b01 + b10) == 0:
            mcn_p = 1.0
        else:
            mcn_p = binomtest(min(b01, b10), b01 + b10, 0.5).pvalue
    except Exception:
        mcn_p = float("nan")

    rng = random.Random(seed)
    boot = []
    for _ in range(bootstrap_n):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boot.append(sum(sample) / n)
    boot.sort()
    lo = boot[int(0.025 * len(boot))]
    hi = boot[int(0.975 * len(boot)) - 1]
    return PairedStat(
        n_pairs=n,
        mean_diff=sum(diffs) / n,
        wilcoxon_p=float(wilc_p) if wilc_p == wilc_p else float("nan"),
        mcnemar_p=float(mcn_p) if mcn_p == mcn_p else float("nan"),
        ci_lo=lo,
        ci_hi=hi,
    )
