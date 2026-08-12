"""End-to-end smoke test for the multi-agent pipeline using a stub LLM.

No Ollama, no HF token, no internet. Verifies that the entire workflow
(planner -> generator -> reviewer -> evaluator -> optimizer -> explainer)
runs to completion on a single problem and produces the expected
artifacts in the terminal state.
"""

from __future__ import annotations

import pytest

from execugraph.benchmarks.internal30 import load_internal30
from execugraph.graph.workflow import WorkflowDeps
from execugraph.llm.base import CostAccumulator
from execugraph.llm.stub_backend import fib_solver_stub
from execugraph.pipelines import run_multi_agent, run_single_oneshot, run_single_with_retry


def _fib_problem():
    for p in load_internal30():
        if p.id == "fib":
            return p
    raise AssertionError("fib problem missing from internal30")


def _deps_with_stub() -> WorkflowDeps:
    stub = fib_solver_stub()
    return WorkflowDeps(
        planner_llm=stub,
        generator_llm=stub,
        reviewer_llm=stub,
        optimizer_llm=stub,
        explainer_llm=stub,
        cost=CostAccumulator(),
        timeout_s=4.0,
    )


@pytest.mark.integration
def test_single_oneshot_with_stub() -> None:
    out = run_single_oneshot(_fib_problem(), _deps_with_stub(), seed=0)
    assert out["passed"], out["evaluation"]
    assert out["evaluation"]["tests_passed"] == out["evaluation"]["tests_total"]
    assert out["cost"]["calls"] >= 1


@pytest.mark.integration
def test_single_with_retry_converges() -> None:
    out = run_single_with_retry(_fib_problem(), _deps_with_stub(), retry_budget=1, seed=0)
    assert out["passed"]


@pytest.mark.integration
def test_multi_agent_full_path() -> None:
    out = run_multi_agent(_fib_problem(), _deps_with_stub(), retry_budget=1, seed=0)
    assert out["passed"]
    assert out["evaluation"]["passed"]
    # Multi-agent path should hit at least planner + generator + evaluator + explainer.
    assert out["cost"]["calls"] >= 3
    assert out.get("plan"), "planner output missing"
    assert out.get("explanation"), "explainer output missing"


@pytest.mark.integration
def test_multi_agent_no_planner_ablation() -> None:
    out = run_multi_agent(
        _fib_problem(),
        _deps_with_stub(),
        retry_budget=1,
        seed=0,
        enable_planner=False,
    )
    assert out["passed"]
    assert out["plan"] == "(planner disabled)"
