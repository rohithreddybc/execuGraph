"""Batch runner: iterate (problem x trial), append JSONL, write run summary."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..benchmarks.base import Problem
from ..graph.workflow import WorkflowDeps
from .trial_runner import append_jsonl, host_environment, run_one_trial


def run_batch(
    *,
    problems: Iterable[Problem],
    deps: WorkflowDeps,
    condition: str,
    n_trials: int,
    retry_budget: int = 2,
    output_dir: Path,
    config_meta: dict[str, Any],
    progress: bool = True,
    enable_planner: bool = True,
    enable_reviewer: bool = True,
    enable_optimizer: bool = True,
    enable_rag: bool = False,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl = output_dir / "trials.jsonl"
    meta = {
        "condition": condition,
        "n_trials": n_trials,
        "retry_budget": retry_budget,
        "config": config_meta,
        "host": host_environment(),
        "model_planner": getattr(deps.planner_llm, "model", ""),
        "model_generator": getattr(deps.generator_llm, "model", ""),
    }
    (output_dir / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    problems_list = list(problems)
    total = len(problems_list) * n_trials

    # Resume: load already-logged (problem_id, trial) pairs so a restart
    # after a system reboot does not re-run or duplicate completed trials.
    done_pairs: set[tuple[str, int]] = set()
    done = 0
    n_pass = 0
    if jsonl.exists():
        for _line in jsonl.read_text(encoding="utf-8").splitlines():
            if not _line.strip():
                continue
            try:
                _r = json.loads(_line)
                _key = (_r["problem_id"], int(_r["trial"]))
                if _key not in done_pairs:
                    done_pairs.add(_key)
                    done += 1
                    if _r.get("passed"):
                        n_pass += 1
            except (json.JSONDecodeError, KeyError):
                pass
        if done_pairs:
            print(
                f"[resume] {len(done_pairs)} trial(s) already logged — skipping.",
                flush=True,
            )

    for problem in problems_list:
        for trial in range(n_trials):
            seed = trial
            if (problem.id, trial) in done_pairs:
                continue  # already done; skip without re-running
            try:
                rec = run_one_trial(
                    problem=problem,
                    deps=deps,
                    condition=condition,
                    seed=seed,
                    trial=trial,
                    retry_budget=retry_budget,
                    enable_planner=enable_planner,
                    enable_reviewer=enable_reviewer,
                    enable_optimizer=enable_optimizer,
                    enable_rag=enable_rag,
                )
            except Exception as e:  # never let one trial kill the batch
                from .trial_runner import TrialRecord
                rec = TrialRecord(
                    problem_id=problem.id,
                    category=problem.category,
                    source=problem.source,
                    condition=condition,
                    model_planner=getattr(deps.planner_llm, "model", ""),
                    model_generator=getattr(deps.generator_llm, "model", ""),
                    seed=seed,
                    trial=trial,
                    retry_budget=retry_budget,
                    passed=False,
                    tests_total=0,
                    tests_passed=0,
                    retries_used=0,
                    error_class="harness_error",
                    test_source="none",
                    wallclock_s=0.0,
                    tokens_in=0,
                    tokens_out=0,
                    llm_calls=0,
                    code="",
                    stderr=f"{type(e).__name__}: {e}"[:600],
                    timestamp=0.0,
                )
            append_jsonl(rec, jsonl)
            done += 1
            if rec.passed:
                n_pass += 1
            if progress:
                print(
                    f"[{done}/{total}] {condition} {problem.id} t{trial} "
                    f"-> passed={rec.passed} err={rec.error_class} "
                    f"wc={rec.wallclock_s:.1f}s",
                    flush=True,
                )
    summary = {
        **meta,
        "trials_total": total,
        "trials_passed": n_pass,
        "pass_rate": (n_pass / total) if total else 0.0,
    }
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
