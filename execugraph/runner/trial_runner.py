"""One-trial runner: (problem, condition, model, seed, trial) -> JSON record."""

from __future__ import annotations

import json
import platform
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..benchmarks.base import Problem
from ..graph.workflow import WorkflowDeps
from ..pipelines import run_multi_agent, run_single_oneshot, run_single_with_retry


@dataclass
class TrialRecord:
    problem_id: str
    category: str
    source: str
    condition: str  # single-oneshot | single-retry | multi-full | multi-no-X | rag-on
    model_planner: str
    model_generator: str
    seed: int
    trial: int
    retry_budget: int
    passed: bool
    tests_total: int
    tests_passed: int
    retries_used: int
    error_class: str
    test_source: str
    wallclock_s: float
    tokens_in: int
    tokens_out: int
    llm_calls: int
    code: str
    stderr: str
    timestamp: float


def run_one_trial(
    *,
    problem: Problem,
    deps: WorkflowDeps,
    condition: str,
    seed: int,
    trial: int,
    retry_budget: int = 2,
    enable_planner: bool = True,
    enable_reviewer: bool = True,
    enable_optimizer: bool = True,
    enable_rag: bool = False,
) -> TrialRecord:
    t0 = time.perf_counter()
    if condition == "single-oneshot":
        out = run_single_oneshot(problem, deps, seed=seed)
    elif condition == "single-retry":
        out = run_single_with_retry(problem, deps, retry_budget=retry_budget, seed=seed)
    else:
        out = run_multi_agent(
            problem,
            deps,
            retry_budget=retry_budget,
            enable_planner=enable_planner,
            enable_reviewer=enable_reviewer,
            enable_optimizer=enable_optimizer,
            enable_rag=enable_rag,
            seed=seed,
        )
    wallclock = time.perf_counter() - t0
    ev = out.get("evaluation", {}) or {}
    cost = out.get("cost", {}) or {}
    return TrialRecord(
        problem_id=problem.id,
        category=problem.category,
        source=problem.source,
        condition=condition,
        model_planner=getattr(deps.planner_llm, "model", ""),
        model_generator=getattr(deps.generator_llm, "model", ""),
        seed=seed,
        trial=trial,
        retry_budget=retry_budget,
        passed=bool(ev.get("passed", out.get("passed", False))),
        tests_total=int(ev.get("tests_total", 0)),
        tests_passed=int(ev.get("tests_passed", 0)),
        retries_used=int(out.get("retries", 0)),
        error_class=str(ev.get("error_class", "none")),
        test_source=str(ev.get("test_source", "deterministic")),
        wallclock_s=round(wallclock, 4),
        tokens_in=int(cost.get("tokens_in", 0)),
        tokens_out=int(cost.get("tokens_out", 0)),
        llm_calls=int(cost.get("calls", 0)),
        code=(out.get("code") or "")[:4000],
        stderr=(ev.get("stderr") or "")[:600],
        timestamp=time.time(),
    )


def append_jsonl(record: TrialRecord, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(record)) + "\n")


def host_environment() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
