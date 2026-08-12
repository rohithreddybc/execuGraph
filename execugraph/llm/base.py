"""Provider-agnostic LLM backend interface.

Every LLM call in ExecuGraph goes through ``LLMBackend.invoke``. Backends
must report cost (tokens in/out, wallclock, call count) so the runner can
record per-trial cost without each agent caring about the provider.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class LLMResponse:
    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    wallclock_s: float = 0.0
    raw: dict = field(default_factory=dict)


@dataclass
class CostAccumulator:
    tokens_in: int = 0
    tokens_out: int = 0
    wallclock_s: float = 0.0
    calls: int = 0

    def add(self, r: LLMResponse) -> None:
        self.tokens_in += r.tokens_in
        self.tokens_out += r.tokens_out
        self.wallclock_s += r.wallclock_s
        self.calls += 1

    def to_dict(self) -> dict:
        return {
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "wallclock_s": round(self.wallclock_s, 4),
            "calls": self.calls,
        }


class LLMBackend(Protocol):
    """A backend converts a single prompt into an :class:`LLMResponse`."""

    name: str
    model: str

    def invoke(
        self,
        prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        seed: int | None = None,
        stop: list[str] | None = None,
    ) -> LLMResponse: ...


def time_call(fn):
    """Decorator: wraps an LLM call so wallclock and (best-effort) tokens land in the response."""

    def wrapper(*args, **kwargs) -> LLMResponse:
        start = time.perf_counter()
        resp: LLMResponse = fn(*args, **kwargs)
        resp.wallclock_s = time.perf_counter() - start
        return resp

    return wrapper
