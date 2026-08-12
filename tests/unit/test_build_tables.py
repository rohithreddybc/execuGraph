"""End-to-end smoke for the table generator with synthetic records.

Verifies the table-building path doesn't throw on a small fake dataset
and that the emitted .tex fragments are valid LaTeX (parseable booktabs).
"""

from __future__ import annotations

import json
from pathlib import Path

from execugraph.analysis.build_tables import main as build_main


def _record(pid: str, cat: str, cond: str, passed: bool, *, trial: int = 0, err: str = "none") -> dict:
    return {
        "problem_id": pid,
        "category": cat,
        "source": "internal",
        "condition": cond,
        "model_planner": "test",
        "model_generator": "test",
        "seed": 0,
        "trial": trial,
        "retry_budget": 2,
        "passed": passed,
        "tests_total": 5,
        "tests_passed": 5 if passed else 0,
        "retries_used": 0 if passed else 2,
        "error_class": "none" if passed else err,
        "test_source": "deterministic",
        "wallclock_s": 1.0 if passed else 3.0,
        "tokens_in": 100,
        "tokens_out": 50,
        "llm_calls": 1 if cond == "single-oneshot" else 4,
        "code": "",
        "stderr": "",
        "timestamp": 0.0,
    }


def test_build_tables_smoke(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    (run_dir / "sub").mkdir(parents=True)
    jsonl = run_dir / "sub" / "trials.jsonl"
    records = []
    # Three problems x three conditions; multi-full beats single-oneshot.
    for cat, pid in [("dp", "fib"), ("graph", "topo"), ("ds", "lru")]:
        records.append(_record(pid, cat, "single-oneshot", passed=False, err="wrong_answer"))
        records.append(_record(pid, cat, "single-retry", passed=True))
        records.append(_record(pid, cat, "multi-full", passed=True))
    with jsonl.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    out = tmp_path / "tables"
    rc = build_main([str(run_dir), "--out", str(out)])
    assert rc == 0
    expected = [
        "tab3_problem_level.tex",
        "tab4_category.tex",
        "tab5_failure.tex",
        "tab6_cost.tex",
        "tab11_errortax.tex",
    ]
    for name in expected:
        contents = (out / name).read_text(encoding="utf-8")
        assert r"\begin{tabular}" in contents
        assert r"\end{tabular}" in contents
        assert r"\bottomrule" in contents
