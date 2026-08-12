"""Logical Reviewer agent.

Output is a structured advisory record. The framework does not gate on
this output (acceptance is execution-driven), but downstream tooling can
consume it.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..llm.base import CostAccumulator, LLMBackend
from .base import load_prompt

_REVIEW_SCHEMA_HINT = """
Return STRICT JSON (no prose, no markdown) with the schema:
{
  "invariants": [string, ...],          // properties the code should preserve
  "potential_failures": [string, ...],  // suspected bugs or edge-case gaps
  "severity": "low" | "medium" | "high"
}
""".strip()


def _parse_json(text: str) -> dict[str, Any] | None:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def run_reviewer(
    *,
    code: str,
    backend: LLMBackend,
    cost: CostAccumulator,
    seed: int | None = None,
) -> dict[str, Any]:
    base = load_prompt("review").format(code=code)
    prompt = f"{base}\n\n{_REVIEW_SCHEMA_HINT}"
    resp = backend.invoke(prompt, temperature=0.2, max_tokens=512, seed=seed)
    cost.add(resp)
    parsed = _parse_json(resp.content) or {
        "invariants": [],
        "potential_failures": [resp.content.strip()[:300]] if resp.content.strip() else [],
        "severity": "low",
    }
    parsed.setdefault("severity", "low")
    parsed.setdefault("invariants", [])
    parsed.setdefault("potential_failures", [])
    return parsed
