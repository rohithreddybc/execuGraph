"""Optimizer agent. Runs only after a passing evaluation."""

from __future__ import annotations

from ..execution.code_sanitize import extract_python_block
from ..llm.base import CostAccumulator, LLMBackend
from .base import load_prompt


def run_optimizer(
    *,
    code: str,
    backend: LLMBackend,
    cost: CostAccumulator,
    seed: int | None = None,
) -> str:
    prompt = load_prompt("optimizer").format(code=code)
    resp = backend.invoke(prompt, temperature=0.0, max_tokens=1024, seed=seed)
    cost.add(resp)
    return extract_python_block(resp.content) or code
