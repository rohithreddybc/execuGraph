"""Explainer agent."""

from __future__ import annotations

from ..llm.base import CostAccumulator, LLMBackend
from .base import load_prompt


def run_explainer(
    *,
    problem: str,
    code: str,
    plan: str,
    backend: LLMBackend,
    cost: CostAccumulator,
    seed: int | None = None,
) -> str:
    prompt = load_prompt("explain").format(problem=problem, code=code, plan=plan or "(no plan)")
    resp = backend.invoke(prompt, temperature=0.2, max_tokens=512, seed=seed)
    cost.add(resp)
    return resp.content.strip()
