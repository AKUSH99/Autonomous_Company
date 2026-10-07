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
    "glm-flash": "RCP-AIaaS/zai-org/GLM-5.3-Flash",            # schnellere GLM-Variante
}
EMBEDDING_MODELL = "RCP-AIaaS/Qwen/Qwen3-Embedding-8B"
# Ratenlimit der Plattform laut FAQ: unter 15 Anfragen pro Minute pro Nutzer (weitergeleitete Modelle)
ANFRAGEN_PRO_MINUTE = 14
# Zeitlimit pro Modell-Aufruf in Sekunden
ZEITLIMIT_SCHNELL = 60
ZEITLIMIT_DENKEN = 240


def daten_ordner() -> Path:
    return Path(os.environ.get("STUDIENASSISTENT_DATEN", "daten"))


_BETRIEB = None
_BETRIEB_SPERRE = __import__("threading").Lock()


def betrieb():
    """Gemeinsame Taktbremse und Statistik für alle Prozesse, die den Schlüssel nutzen (siehe betrieb.py)."""
    global _BETRIEB
    with _BETRIEB_SPERRE:
        if _BETRIEB is None:
            from .betrieb import Betrieb
            _BETRIEB = Betrieb(daten_ordner() / "betrieb.sqlite", ANFRAGEN_PRO_MINUTE)
        return _BETRIEB


def _rate_limiter():
    from langchain_core.rate_limiters import BaseRateLimiter

    class Fensterbremse(BaseRateLimiter):
        def acquire(self, *, blocking: bool = True) -> bool:
            import time
            while (w := betrieb().warten("chat")) > 0:
                if not blocking:
                    return False
                time.sleep(w)
            return True

        async def aacquire(self, *, blocking: bool = True) -> bool:
            import asyncio
            while (w := betrieb().warten("chat")) > 0:
                if not blocking:
                    return False
                await asyncio.sleep(w)
            return True

    return Fensterbremse()



def chat_modell(name: str = "deepseek", denken: bool = False):
    """LangChain-Chatmodell auf der Swiss AI Platform (OpenAI-kompatibel), mit Taktbremse fürs Ratenlimit."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=MODELLE.get(name, name),
        base_url=SWISSAI_URL,
        api_key=os.environ.get("SWISSAI_API_KEY", "fehlt"),
        temperature=0.2,
        max_tokens=32000 if denken else 3000,  # mit Reasoning das volle Denkbudget
        # Ohne Zeitlimit wartet ein hängender Aufruf ewig. Mit Reasoning darf eine Antwort lange denken.
        timeout=ZEITLIMIT_DENKEN if denken else ZEITLIMIT_SCHNELL,
        max_retries=2,
        rate_limiter=_rate_limiter(),
        # Denkmodus über die Chat-Vorlage (DeepSeek: thinking, Qwen/GLM: enable_thinking)
        extra_body={"chat_template_kwargs": {"thinking": denken, "enable_thinking": denken}},
    )
