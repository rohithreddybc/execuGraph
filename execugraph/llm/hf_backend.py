"""HuggingFace Inference API fallback backend.

Used when no GPU is available locally. Requires the
``HUGGINGFACEHUB_API_TOKEN`` environment variable. Cost fields are
best-effort: HF Inference API does not always return token counts, so
we fall back to whitespace counts when missing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import requests

from .base import LLMBackend, LLMResponse, time_call


def _approx_tokens(text: str) -> int:
    return max(1, len(text.split()))


@dataclass
class HFBackend(LLMBackend):
    model: str
    name: str = "hf"
    timeout_s: float = 300.0
    api_url_template: str = "https://api-inference.huggingface.co/models/{model}"

    def __post_init__(self) -> None:
        token = os.environ.get("HUGGINGFACEHUB_API_TOKEN")
        if not token:
            raise RuntimeError(
                "HFBackend requires HUGGINGFACEHUB_API_TOKEN env var; "
                "use OllamaBackend instead for local-only operation."
            )
        self._headers = {"Authorization": f"Bearer {token}"}

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
        url = self.api_url_template.format(model=self.model)
        body = {
            "inputs": prompt,
            "parameters": {
                "temperature": max(temperature, 1e-3),
                "max_new_tokens": max_tokens,
                "return_full_text": False,
            },
            "options": {"wait_for_model": True},
        }
        if seed is not None:
            body["parameters"]["seed"] = int(seed)
        r = requests.post(url, json=body, headers=self._headers, timeout=self.timeout_s)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data and "generated_text" in data[0]:
            content = data[0]["generated_text"]
        elif isinstance(data, dict) and "generated_text" in data:
            content = data["generated_text"]
        else:
            content = str(data)
        return LLMResponse(
            content=content,
            tokens_in=_approx_tokens(prompt),
            tokens_out=_approx_tokens(content),
            raw=data if isinstance(data, dict) else {"raw": data},
        )
