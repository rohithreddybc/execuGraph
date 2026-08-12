"""Construct an LLM backend from config."""

from __future__ import annotations

from typing import Any

from .base import LLMBackend
from .hf_backend import HFBackend
from .ollama_backend import OllamaBackend


def build_backend(cfg: dict[str, Any]) -> LLMBackend:
    """Return a backend per ``cfg``.

    Expected schema::

        provider: ollama | hf
        model: <model name>
        host: <ollama base url>          # ollama only
        timeout_s: <float>
    """
    provider = (cfg.get("provider") or "ollama").lower()
    model = cfg["model"]
    if provider == "ollama":
        return OllamaBackend(
            model=model,
            host=cfg.get("host", "http://localhost:11434"),
            timeout_s=cfg.get("timeout_s", 300.0),
        )
    if provider == "hf":
        return HFBackend(model=model, timeout_s=cfg.get("timeout_s", 300.0))
    raise ValueError(f"unknown LLM provider: {provider!r}")
