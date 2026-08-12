"""Baseline 1: single-agent, single-pass generation; no planner, no review, no retries."""

from __future__ import annotations

from typing import Any

from ..agents.evaluator import run_evaluator
from ..agents.generator import run_generator
from ..benchmarks.base import Problem
from ..graph.workflow import WorkflowDeps
from ..llm.base import CostAccumulator


def run_single_oneshot(
    problem: Problem,
    deps: WorkflowDeps,
    *,
    seed: int | None = None,
) -> dict[str, Any]:
    deps.cost = CostAccumulator()
    code = run_generator(
        problem=problem.statement,
        plan="",
        backend=deps.generator_llm,
        cost=deps.cost,
        seed=seed,
    )
    res = run_evaluator(
        problem=problem,
        code=code,
        backend=deps.reviewer_llm,
        cost=deps.cost,
        seed=seed,
        timeout_s=deps.timeout_s,
    )
    return {
        "problem": problem.statement,
        "code": code,
        "evaluation": {
            "passed": res.passed,
            "test_results": res.test_results,
            "error_class": res.error_class,
            "stderr": res.stderr,
            "tests_total": res.tests_total,
            "tests_passed": res.tests_passed,
            "test_source": res.test_source,
        },
        "passed": res.passed,
        "retries": 0,
        "cost": deps.cost.to_dict(),
    }
