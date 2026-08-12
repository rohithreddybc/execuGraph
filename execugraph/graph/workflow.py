"""Compiled multi-agent workflow.

The workflow is parameterized: per-agent enable toggles, retry budget,
and the LLM backends are passed in via :class:`WorkflowDeps` so the same
graph can be configured as the multi-full ExecuGraph or reduced to either
of the two single-agent baselines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from ..agents.evaluator import EvaluationResult, run_evaluator
from ..agents.explainer import run_explainer
from ..agents.generator import run_generator
from ..agents.optimizer import run_optimizer
from ..agents.planner import run_planner
from ..agents.reviewer import run_reviewer
from ..benchmarks.base import Problem
from ..llm.base import CostAccumulator, LLMBackend


class GraphState(TypedDict, total=False):
    problem: str
    problem_obj: Problem
    plan: str
    code: str
    review: dict[str, Any]
    evaluation: dict[str, Any]
    explanation: str
    retries: int
    retry_budget: int
    passed: bool
    optimized: bool
    enable_planner: bool
    enable_reviewer: bool
    enable_optimizer: bool
    enable_rag: bool
    retrieved_techniques: list[str]
    cost: dict[str, Any]
    seed: int
    logs: list[str]
    last_stderr: str
    test_source: str


@dataclass
class WorkflowDeps:
    planner_llm: LLMBackend
    generator_llm: LLMBackend
    reviewer_llm: LLMBackend
    optimizer_llm: LLMBackend
    explainer_llm: LLMBackend
    cost: CostAccumulator
    timeout_s: float = 5.0
    rag_retriever: Any | None = None
    seed: int | None = None


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------


def _planner_node(state: GraphState, deps: WorkflowDeps) -> GraphState:
    state.setdefault("logs", []).append("[PLANNER]")
    if not state.get("enable_planner", True):
        return {"plan": "(planner disabled)"}
    techniques: list[str] = []
    if state.get("enable_rag") and deps.rag_retriever is not None:
        try:
            techniques = deps.rag_retriever.retrieve(state["problem"])
        except Exception:
            techniques = []
    plan = run_planner(
        problem=state["problem"],
        backend=deps.planner_llm,
        techniques=techniques,
        cost=deps.cost,
        seed=state.get("seed", deps.seed),
    )
    return {"plan": plan, "retrieved_techniques": techniques}


def _generator_node(state: GraphState, deps: WorkflowDeps) -> GraphState:
    state.setdefault("logs", []).append("[GENERATOR]")
    code = run_generator(
        problem=state["problem"],
        plan=state.get("plan", ""),
        backend=deps.generator_llm,
        cost=deps.cost,
        seed=state.get("seed", deps.seed),
        feedback=state.get("last_stderr"),
    )
    return {"code": code}


def _reviewer_node(state: GraphState, deps: WorkflowDeps) -> GraphState:
    state.setdefault("logs", []).append("[REVIEWER]")
    if not state.get("enable_reviewer", True):
        return {"review": {"invariants": [], "potential_failures": [], "severity": "low"}}
    review = run_reviewer(
        code=state.get("code", ""),
        backend=deps.reviewer_llm,
        cost=deps.cost,
        seed=state.get("seed", deps.seed),
    )
    return {"review": review}


def _evaluator_node(state: GraphState, deps: WorkflowDeps) -> GraphState:
    state.setdefault("logs", []).append("[EVALUATOR]")
    res: EvaluationResult = run_evaluator(
        problem=state["problem_obj"],
        code=state.get("code", ""),
        backend=deps.reviewer_llm,
        cost=deps.cost,
        seed=state.get("seed", deps.seed),
        timeout_s=deps.timeout_s,
    )
    return {
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
        "test_source": res.test_source,
        "last_stderr": "" if res.passed else (res.stderr or res.error_class),
    }


def _decision_node(state: GraphState, deps: WorkflowDeps) -> GraphState:
    if state.get("passed"):
        state.setdefault("logs", []).append("[DECISION] passed")
        return {}
    retries = int(state.get("retries", 0))
    budget = int(state.get("retry_budget", 0))
    if retries < budget:
        state.setdefault("logs", []).append(f"[DECISION] retry {retries + 1}/{budget}")
        return {"retries": retries + 1}
    state.setdefault("logs", []).append("[DECISION] budget exhausted")
    return {}


def _optimizer_node(state: GraphState, deps: WorkflowDeps) -> GraphState:
    state.setdefault("logs", []).append("[OPTIMIZER]")
    if not state.get("enable_optimizer", True):
        return {"optimized": True}
    original = state.get("code", "")
    new_code = run_optimizer(
        code=original,
        backend=deps.optimizer_llm,
        cost=deps.cost,
        seed=state.get("seed", deps.seed),
    )
    if new_code and new_code.strip() and new_code != original:
        # Re-validate before accepting (peer-review T1).
        re_eval = run_evaluator(
            problem=state["problem_obj"],
            code=new_code,
            backend=deps.reviewer_llm,
            cost=deps.cost,
            seed=state.get("seed", deps.seed),
            timeout_s=deps.timeout_s,
        )
        if re_eval.passed:
            return {"code": new_code, "optimized": True}
        state["logs"].append("[OPTIMIZER] regression suppressed")
    return {"optimized": True}


def _explainer_node(state: GraphState, deps: WorkflowDeps) -> GraphState:
    state.setdefault("logs", []).append("[EXPLAINER]")
    explanation = run_explainer(
        problem=state["problem"],
        code=state.get("code", ""),
        plan=state.get("plan", ""),
        backend=deps.explainer_llm,
        cost=deps.cost,
        seed=state.get("seed", deps.seed),
    )
    return {"explanation": explanation, "cost": deps.cost.to_dict()}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


from .routing import route_after_decision as _route_after_decision  # noqa: E402

# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_graph(deps: WorkflowDeps):
    g = StateGraph(GraphState)

    g.add_node("planner", lambda s: _planner_node(s, deps))
    g.add_node("generate", lambda s: _generator_node(s, deps))
    g.add_node("review", lambda s: _reviewer_node(s, deps))
    g.add_node("evaluate", lambda s: _evaluator_node(s, deps))
    g.add_node("decide", lambda s: _decision_node(s, deps))
    g.add_node("optimize", lambda s: _optimizer_node(s, deps))
    g.add_node("explain", lambda s: _explainer_node(s, deps))

    g.add_edge(START, "planner")
    g.add_edge("planner", "generate")
    g.add_edge("generate", "review")
    g.add_edge("review", "evaluate")
    g.add_edge("evaluate", "decide")
    g.add_conditional_edges(
        "decide",
        _route_after_decision,
        {"generate": "generate", "optimize": "optimize", "explain": "explain"},
    )
    g.add_edge("optimize", "explain")
    g.add_edge("explain", END)

    return g.compile()
