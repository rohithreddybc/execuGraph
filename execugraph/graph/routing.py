"""Workflow decision routing — kept in its own module so tests can
exercise the predicate without importing langgraph."""

from __future__ import annotations

from typing import Any


def route_after_decision(state: dict[str, Any]) -> str:
    if state.get("passed") and not state.get("optimized") and state.get("enable_optimizer", True):
        return "optimize"
    if state.get("passed") or int(state.get("retries", 0)) >= int(state.get("retry_budget", 0)):
        return "explain"
    return "generate"
