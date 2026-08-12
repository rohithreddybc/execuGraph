"""Re-score archived trial artifacts against the corrected execution sandbox.

Why this exists
---------------
The sandbox shipped with the original experiment grid gated ``__import__``
against a flat allow-list. Importing an allow-listed pure-Python module
transitively imports its private C accelerator (``bisect`` -> ``_bisect``,
``heapq`` -> ``_heapq``, ``io`` -> ``_io``), whose root is not on the
allow-list, so the import was refused and the trial was recorded as
``error_class="sandbox_violation"``. Correct programs were scored as
failures, and the rate differed by condition because conditions that emit
more candidate programs had more opportunities to trip it.

Every trial record persists the candidate ``code`` it produced, so the
grid does not need to be regenerated: it needs to be *re-scored*. This
script replays each stored artifact through the corrected sandbox using
the same Evaluator code path as the original run, and writes a corrected
results tree alongside the original. No LLM is invoked.

Deduplication
-------------
Some runs were resumed and appended to their existing ``trials.jsonl``,
leaving duplicate ``(problem_id, trial)`` keys. The last occurrence wins
(it is the most recent execution) and the policy is applied uniformly to
every run, replacing the three inconsistent conventions used previously.

Usage
-----
    python scripts/rescore_trials.py \
        --in  results/submission-20260509-223437 \
        --out results/submission-20260509-223437-rescored
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

# Worker processes are spawned (not forked) on Windows and do not inherit
# the parent's sys.path, so the package root is added at import time.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_PROBLEMS: dict[str, object] = {}


def _load_problems() -> dict[str, object]:
    """Index every benchmark problem by id (all three suites are offline)."""
    global _PROBLEMS
    if _PROBLEMS:
        return _PROBLEMS
    from execugraph.benchmarks.apps_intro import load_apps_intro
    from execugraph.benchmarks.humaneval import load_humaneval
    from execugraph.benchmarks.internal30 import load_internal30

    index: dict[str, object] = {}
    for loader in (load_internal30, load_humaneval, load_apps_intro):
        for problem in loader():
            index[problem.id] = problem
    _PROBLEMS = index
    return index


def _rescore_one(record: dict) -> dict:
    """Replay one stored artifact through the corrected sandbox."""
    from execugraph.agents.evaluator import _evaluate_with_tests

    problems = _load_problems()
    problem = problems.get(record["problem_id"])
    out = dict(record)

    code = record.get("code") or ""
    if problem is None:
        out["rescore_status"] = "problem_not_found"
        return out
    if not code.strip():
        # Nothing was generated (e.g. an Ollama read-timeout). Preserve the
        # original harness failure rather than inventing an outcome.
        out["rescore_status"] = "no_code_artifact"
        out["error_class"] = record.get("error_class") or "harness_error"
        out["passed"] = False
        return out

    result = _evaluate_with_tests(
        code,
        list(problem.tests),
        problem.primary_function,
        list(problem.signature_aliases),
        timeout_s=float(problem.timeout_s or 5.0),
    )

    out["passed_original"] = bool(record.get("passed"))
    out["error_class_original"] = record.get("error_class")
    out["passed"] = bool(result.passed)
    out["error_class"] = result.error_class
    out["tests_passed"] = result.tests_passed
    out["tests_total"] = result.tests_total
    out["test_source"] = result.test_source
    out["stderr"] = result.stderr[:400]
    out["rescore_status"] = "rescored"
    return out


def _dedupe(records: list[dict]) -> list[dict]:
    """Keep the last occurrence of each (problem_id, trial) key."""
    keyed: dict[tuple, dict] = {}
    for record in records:
        keyed[(record.get("problem_id"), record.get("trial"))] = record
    return list(keyed.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="src", required=True)
    parser.add_argument("--out", dest="dst", required=True)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    args = parser.parse_args()

    src, dst = Path(args.src), Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)

    run_dirs = sorted(d for d in src.iterdir() if (d / "trials.jsonl").exists())
    print(f"re-scoring {len(run_dirs)} runs with {args.workers} workers\n")

    grand = {"runs": {}, "dedup_policy": "last-wins", "llm_invoked": False}

    for run_dir in run_dirs:
        raw = [
            json.loads(line)
            for line in (run_dir / "trials.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        records = _dedupe(raw)

        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            rescored = list(pool.map(_rescore_one, records, chunksize=4))

        out_dir = dst / run_dir.name
        out_dir.mkdir(parents=True, exist_ok=True)
        with (out_dir / "trials.jsonl").open("w", encoding="utf-8") as fh:
            for record in rescored:
                fh.write(json.dumps(record) + "\n")

        for name in ("run_meta.json", "run_summary.json"):
            if (run_dir / name).exists():
                (out_dir / name).write_text(
                    (run_dir / name).read_text(encoding="utf-8"), encoding="utf-8"
                )

        n = len(rescored)
        n_pass = sum(1 for r in rescored if r["passed"])
        was = sum(1 for r in rescored if r.get("passed_original"))
        flipped = sum(
            1
            for r in rescored
            if r.get("rescore_status") == "rescored"
            and bool(r.get("passed_original")) != bool(r["passed"])
        )
        summary = {
            "condition": run_dir.name,
            "trials_total": n,
            "raw_records": len(raw),
            "duplicates_dropped": len(raw) - n,
            "n_pass": n_pass,
            "pass_rate": round(n_pass / n, 6) if n else 0.0,
            "pass_rate_original": round(was / n, 6) if n else 0.0,
            "outcomes_flipped": flipped,
        }
        (out_dir / "run_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        grand["runs"][run_dir.name] = summary

        print(
            f"{run_dir.name:18s} {len(raw):4d} raw -> {n:4d} trials  "
            f"pass {100 * was / n:5.1f}% -> {100 * n_pass / n:5.1f}%  "
            f"({flipped} flipped)"
        )

    (dst / "rescore_summary.json").write_text(json.dumps(grand, indent=2), encoding="utf-8")
    print(f"\nwrote {dst / 'rescore_summary.json'}")


if __name__ == "__main__":
    main()
