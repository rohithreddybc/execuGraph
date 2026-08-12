"""Ollama HTTP backend.

Talks to a local ``ollama serve`` daemon over its REST API. We use the
raw HTTP API rather than the ``ollama`` Python package so that the only
runtime dependency is ``requests`` and so cost fields (eval_count,
prompt_eval_count) are available directly from the response.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import requests

from .base import LLMBackend, LLMResponse, time_call


@dataclass
class OllamaBackend(LLMBackend):
    model: str
    host: str = "http://localhost:11434"
    name: str = "ollama"
    timeout_s: float = 300.0

    def __post_init__(self) -> None:
        env_host = os.environ.get("OLLAMA_HOST")
        if env_host:
            self.host = env_host

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
        body = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if seed is not None:
            body["options"]["seed"] = int(seed)
        if stop:
            body["options"]["stop"] = stop
        r = requests.post(f"{self.host}/api/generate", json=body, timeout=self.timeout_s)
        r.raise_for_status()
        data = r.json()
        return LLMResponse(
            content=data.get("response", ""),
            tokens_in=int(data.get("prompt_eval_count", 0)),
            tokens_out=int(data.get("eval_count", 0)),
            raw=data,
        )

    def healthcheck(self) -> bool:
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=5)
            r.raise_for_status()
            tags = {m["name"] for m in r.json().get("models", [])}
            return self.model in tags
        except Exception:
            return False
