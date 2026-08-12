"""Planner agent."""

from __future__ import annotations

from ..llm.base import CostAccumulator, LLMBackend
from .base import load_prompt


def run_planner(
    *,
    problem: str,
    backend: LLMBackend,
    techniques: list[str] | None = None,
    cost: CostAccumulator,
    seed: int | None = None,
) -> str:
    techniques_text = "\n".join(f"- {t}" for t in (techniques or [])) or "(none)"
    prompt = load_prompt("planner").format(problem=problem, techniques=techniques_text)
    resp = backend.invoke(prompt, temperature=0.2, max_tokens=768, seed=seed)
    cost.add(resp)
    return resp.content.strip()
