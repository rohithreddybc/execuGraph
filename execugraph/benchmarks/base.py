"""Common types for benchmark loaders."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TestCase:
    args: tuple = ()
    expected: Any = None
    description: str = ""
    # Either an expression string ``call`` (preferred for richer signatures)
    # or ``args`` will be turned into a call against the primary function.
    call: str | None = None
    judge: Callable[[Any], bool] | None = None  # custom equality (e.g. topo-order)
    kind: str = "deterministic"  # deterministic | edge | stress | llm


@dataclass
class Problem:
    id: str
    category: str  # dp | graph | ds
    source: str  # internal | apps-<id> | humaneval/<id>
    statement: str
    primary_function: str
    signature_aliases: list[str] = field(default_factory=list)
    tests: list[TestCase] = field(default_factory=list)
    selection_rationale: str = ""
    difficulty: str = "easy"  # easy | medium | hard
    timeout_s: float = 5.0
