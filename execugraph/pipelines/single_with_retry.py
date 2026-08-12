"""Baseline 2: single-agent + execution feedback retries (Reflexion-lite).

Same generator as single-oneshot, but on failure the prior stderr is
appended to the prompt and we regenerate up to ``retry_budget`` times.
This isolates the contribution of the multi-agent decomposition itself
from the contribution of execution feedback per se.
"""

from __future__ import annotations

from typing import Any

from ..agents.evaluator import run_evaluator
from ..agents.generator import run_generator
from ..benchmarks.base import Problem
from ..graph.workflow import WorkflowDeps
from ..llm.base import CostAccumulator


def run_single_with_retry(
    problem: Problem,
    deps: WorkflowDeps,
    *,
    retry_budget: int = 2,
    seed: int | None = None,
) -> dict[str, Any]:
    deps.cost = CostAccumulator()
    feedback: str | None = None
    last_eval = None
    code = ""
    attempt = 0
    for attempt in range(retry_budget + 1):  # noqa: B007 - attempt used after loop
        code = run_generator(
            problem=problem.statement,
            plan="",
            backend=deps.generator_llm,
            cost=deps.cost,
            seed=seed,
            feedback=feedback,
        )
        last_eval = run_evaluator(
            problem=problem,
            code=code,
            backend=deps.reviewer_llm,
            cost=deps.cost,
            seed=seed,
            timeout_s=deps.timeout_s,
        )
        if last_eval.passed:
            break
        feedback = (last_eval.stderr or last_eval.error_class or "")[:600]
    assert last_eval is not None
    return {
        "problem": problem.statement,
        "code": code,
        "evaluation": {
            "passed": last_eval.passed,
            "test_results": last_eval.test_results,
            "error_class": last_eval.error_class,
            "stderr": last_eval.stderr,
            "tests_total": last_eval.tests_total,
            "tests_passed": last_eval.tests_passed,
            "test_source": last_eval.test_source,
        },
        "passed": last_eval.passed,
        "retries": attempt,
        "cost": deps.cost.to_dict(),
    }
