"""Multi-full ExecuGraph pipeline."""

from __future__ import annotations

from typing import Any

from ..benchmarks.base import Problem
from ..graph.workflow import WorkflowDeps, build_graph
from ..llm.base import CostAccumulator


def run_multi_agent(
    problem: Problem,
    deps: WorkflowDeps,
    *,
    retry_budget: int = 2,
    enable_planner: bool = True,
    enable_reviewer: bool = True,
    enable_optimizer: bool = True,
    enable_rag: bool = False,
    seed: int | None = None,
) -> dict[str, Any]:
    """Run the full graph and return the terminal state."""
    deps.cost = CostAccumulator()
    app = build_graph(deps)
    state = {
        "problem": problem.statement,
        "problem_obj": problem,
        "retries": 0,
        "retry_budget": retry_budget,
        "passed": False,
        "optimized": False,
        "enable_planner": enable_planner,
        "enable_reviewer": enable_reviewer,
        "enable_optimizer": enable_optimizer,
        "enable_rag": enable_rag,
        "seed": seed,
        "logs": [],
    }
    final = app.invoke(state, {"recursion_limit": 50})
    final["cost"] = deps.cost.to_dict()
    return final
