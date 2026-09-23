"""LLM-Backends mit einheitlicher Schnittstelle: strukturierte JSON-Antworten als Pydantic-Objekte."""
from __future__ import annotations

from ..config import LLMSpec
from .base import LLMAntwort, LLMClient, LLMFehler


def erstelle_client(spec: LLMSpec) -> LLMClient:
    if spec.provider == "anthropic":
        from .anthropic_backend import AnthropicClient
        return AnthropicClient(spec)
    if spec.provider == "openai_compat":
        from .openai_compat import OpenAICompatClient
        return OpenAICompatClient(spec)
    raise ValueError(f"Provider '{spec.provider}' ist kein LLM-Backend (scripted/regeln werden in den Agenten behandelt).")


__all__ = ["LLMAntwort", "LLMClient", "LLMFehler", "erstelle_client"]
