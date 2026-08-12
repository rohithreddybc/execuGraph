"""Strip non-code artifacts from raw LLM output.

The Generator is prompted to emit only Python code, but instruction-tuned
7B models occasionally violate this. We strip the most common artifacts:
markdown fences, polite preambles like "Here is the solution:", and
trailing chatter. We do **not** modify indentation or rewrite identifiers.
"""

from __future__ import annotations

import re

_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n?", re.IGNORECASE)
_PREAMBLE_RE = re.compile(
    r"^\s*(here(?:'s| is)|sure|certainly|the following is|solution|answer|let me)[^\n]*\n",
    re.IGNORECASE,
)


def sanitize_code(text: str) -> str:
    if not text:
        return ""
    s = _FENCE_RE.sub("", text)
    s = s.replace("```", "")
    while True:
        new = _PREAMBLE_RE.sub("", s, count=1)
        if new == s:
            break
        s = new
    return s.strip()


def extract_python_block(text: str) -> str:
    """If a fenced ```python``` block is present, return its body. Otherwise sanitize."""
    if not text:
        return ""
    m = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return sanitize_code(text)
