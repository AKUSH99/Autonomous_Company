"""Einstellungen: Modelle der Swiss AI Research Platform und der Ordner für eingelesene Unterlagen.

Schlüssel: Umgebungsvariable SWISSAI_API_KEY (nach Login auf https://serving.swissai.svc.cscs.ch).
Daten: STUDIENASSISTENT_DATEN (Standard: ./daten) – dort liegen Index, Fristen und Embedding-Cache. Kursunterlagen der
FHNW gehören nicht ins öffentliche Repository; sie werden lokal eingelesen.
"""
from __future__ import annotations

import os
from pathlib import Path

SWISSAI_URL = "https://api.swissai.svc.cscs.ch/v1"
MODELLE = {
    "deepseek": "RCP-AIaaS/deepseek-ai/DeepSeek-V4.1-Flash",   # schnell, zuverlässiges Werkzeug-Aufrufen
    "apertus": "CSCS-Inference/swiss-ai/Apertus-v1.5-70B",     # das Schweizer Modell
    "glm": "CSCS-Inference/zai-org/GLM-5.3",                   # stärkstes Modell der Plattform
}
EMBEDDING_MODELL = "RCP-AIaaS/Qwen/Qwen3-Embedding-8B"
# Ratenlimit der Plattform laut FAQ: unter 15 Anfragen pro Minute pro Nutzer (weitergeleitete Modelle)
ANFRAGEN_PRO_MINUTE = 14


def daten_ordner() -> Path:
    return Path(os.environ.get("STUDIENASSISTENT_DATEN", "daten"))


def chat_modell(name: str = "deepseek", denken: bool = False):
    """LangChain-Chatmodell auf der Swiss AI Platform (OpenAI-kompatibel), mit Taktbremse fürs Ratenlimit."""
    from langchain_core.rate_limiters import InMemoryRateLimiter
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=MODELLE.get(name, name),
        base_url=SWISSAI_URL,
        api_key=os.environ.get("SWISSAI_API_KEY", "fehlt"),
        temperature=0.2,
        max_tokens=16000 if denken else 3000,
        max_retries=4,
        rate_limiter=InMemoryRateLimiter(requests_per_second=ANFRAGEN_PRO_MINUTE / 60, max_bucket_size=3),
        # Denkmodus über die Chat-Vorlage (DeepSeek: thinking, Qwen/GLM: enable_thinking)
        extra_body={"chat_template_kwargs": {"thinking": denken, "enable_thinking": denken}},
    )
