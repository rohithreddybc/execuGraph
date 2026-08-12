"""Deterministic stub LLM backend for tests / smoke runs.

Returns hand-written canned responses keyed by prompt content. Lets the
multi-agent workflow be exercised end-to-end without needing Ollama or
HuggingFace credentials.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .base import LLMBackend, LLMResponse, time_call


@dataclass
class StubBackend(LLMBackend):
    """Stub backend that picks a response based on substrings in the prompt.

    ``responders`` is a list of (prompt_predicate, response_text) pairs.
    The first matching predicate wins. If none match, returns ``default``.
    """

    name: str = "stub"
    model: str = "stub-1"
    responders: list[tuple[Callable[[str], bool], str]] = field(default_factory=list)
    default: str = ""
    tokens_in_count: int = 0
    tokens_out_count: int = 0

    @time_call
    def invoke(
        self,
        prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        seed: int | None = None,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        text = self.default
        for pred, resp in self.responders:
            if pred(prompt):
                text = resp
                break
        return LLMResponse(
            content=text,
            tokens_in=max(1, len(prompt.split())),
            tokens_out=max(1, len(text.split())),
            raw={},
        )


def _has(*needles: str) -> Callable[[str], bool]:
    """Returns a predicate that matches a prompt containing all needles."""
    lower_needles = [n.lower() for n in needles]
    return lambda p: all(n in p.lower() for n in lower_needles)


def fib_solver_stub() -> StubBackend:
    """Stub that emits a correct ``fib`` solution for the Generator,
    a structured Reviewer JSON, a plan, and an explanation."""
    plan = (
        "Category: Dynamic Programming\n"
        "Algorithm: iterative Fibonacci\n"
        "Steps: track two values and iterate n-1 times.\n"
        "Edge: n in {0, 1}.\n"
        "Time O(n), Space O(1)."
    )
    code = (
        "def fib(n):\n"
        "    if n < 2:\n"
        "        return n\n"
        "    a, b = 0, 1\n"
        "    for _ in range(n - 1):\n"
        "        a, b = b, a + b\n"
        "    return b\n"
    )
    review_json = (
        '{"invariants": ["fib(0)=0", "fib(1)=1"], '
        '"potential_failures": [], "severity": "low"}'
    )
    explanation = "Iterative O(n) Fibonacci."
    return StubBackend(
        responders=[
            # Order matters: more specific predicates first.
            (_has("you are a senior algorithm planner"), plan),
            (_has("you are a code generation agent"), code),
            (_has("evaluator", "test"), '{"tests": []}'),
            (_has("review"), review_json),
            (_has("optimizer"), code),
            (_has("explain"), explanation),
        ],
        default="(stub: no responder matched)",
    )
