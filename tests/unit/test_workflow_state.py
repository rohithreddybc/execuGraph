"""Sanity test on the workflow state schema + decision routing."""

from __future__ import annotations

from execugraph.graph.routing import route_after_decision as _route_after_decision


def test_route_passed_runs_optimizer() -> None:
    state = {"passed": True, "optimized": False, "enable_optimizer": True, "retries": 0, "retry_budget": 2}
    assert _route_after_decision(state) == "optimize"


def test_route_passed_optimized_explains() -> None:
    state = {"passed": True, "optimized": True, "enable_optimizer": True, "retries": 0, "retry_budget": 2}
    assert _route_after_decision(state) == "explain"


def test_route_optimizer_disabled_skips() -> None:
    state = {"passed": True, "optimized": False, "enable_optimizer": False, "retries": 0, "retry_budget": 2}
    # When optimizer is disabled, we don't take the optimize branch
    assert _route_after_decision(state) == "explain"


def test_route_failure_within_budget_retries() -> None:
    state = {"passed": False, "optimized": False, "retries": 1, "retry_budget": 2}
    assert _route_after_decision(state) == "generate"


def test_route_failure_exhausted_explains() -> None:
    state = {"passed": False, "optimized": False, "retries": 2, "retry_budget": 2}
    assert _route_after_decision(state) == "explain"
