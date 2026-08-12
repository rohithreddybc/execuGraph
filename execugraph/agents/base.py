"""Shared utilities for the agent layer."""

from __future__ import annotations

from importlib import resources
from typing import Final

_PROMPT_PACKAGE: Final[str] = "execugraph.prompts"


def load_prompt(name: str) -> str:
    """Read ``execugraph/prompts/<name>.txt`` as a UTF-8 string."""
    return resources.files(_PROMPT_PACKAGE).joinpath(f"{name}.txt").read_text(encoding="utf-8")
