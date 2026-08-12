"""Code Generator agent."""

from __future__ import annotations

from ..execution.code_sanitize import extract_python_block
from ..llm.base import CostAccumulator, LLMBackend
from .base import load_prompt


def run_generator(
    *,
    problem: str,
    plan: str,
    backend: LLMBackend,
    cost: CostAccumulator,
    seed: int | None = None,
    feedback: str | None = None,
) -> str:
    """Plan-conditioned code generation.

    ``feedback`` (optional) is appended when called by single-with-retry to
    feed the prior failure's stderr back into the next attempt.
    """
    base = load_prompt("generate").format(problem=problem, plan=plan or "(no plan provided)")
    if feedback:
        base += f"\n\nPRIOR ATTEMPT FAILED WITH:\n{feedback.strip()}\n\nFix it. Output code only."
    resp = backend.invoke(base, temperature=0.0, max_tokens=1024, seed=seed)
    cost.add(resp)
    return extract_python_block(resp.content)
