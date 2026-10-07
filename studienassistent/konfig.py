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


def daten_ordner() -> Path:
    return Path(os.environ.get("STUDIENASSISTENT_DATEN", "daten"))


class Taktbremse:
    """Höchstens n Anfragen in 60 Sekunden (gleitendes Fenster). Gewartet wird nur, wenn das Limit wirklich erreicht
    ist – einzelne Fragen laufen ohne Verzögerung durch. Ein gemeinsames Fenster für alle Modelle im Prozess."""

    def __init__(self, pro_minute: int = ANFRAGEN_PRO_MINUTE):
        import threading
        from collections import deque
        self.pro_minute, self.zeiten, self.sperre = pro_minute, deque(), threading.Lock()

    def warten(self) -> float:
        """Wie lange bis zur nächsten freien Anfrage; 0 = sofort (und die Anfrage ist dann gebucht)."""
        import time
        with self.sperre:
            jetzt = time.monotonic()
            while self.zeiten and jetzt - self.zeiten[0] >= 60:
                self.zeiten.popleft()
            if len(self.zeiten) < self.pro_minute:
                self.zeiten.append(jetzt)
                return 0.0
            return 60 - (jetzt - self.zeiten[0]) + 0.05


def _rate_limiter():
    from langchain_core.rate_limiters import BaseRateLimiter

    class Fensterbremse(BaseRateLimiter):
        def acquire(self, *, blocking: bool = True) -> bool:
            import time
            while (w := _BREMSE.warten()) > 0:
                if not blocking:
                    return False
                time.sleep(w)
            return True

        async def aacquire(self, *, blocking: bool = True) -> bool:
            import asyncio
            while (w := _BREMSE.warten()) > 0:
                if not blocking:
                    return False
                await asyncio.sleep(w)
            return True

    return Fensterbremse()


_BREMSE = Taktbremse()


def chat_modell(name: str = "deepseek", denken: bool = False):
    """LangChain-Chatmodell auf der Swiss AI Platform (OpenAI-kompatibel), mit Taktbremse fürs Ratenlimit."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=MODELLE.get(name, name),
        base_url=SWISSAI_URL,
        api_key=os.environ.get("SWISSAI_API_KEY", "fehlt"),
        temperature=0.2,
        max_tokens=32000 if denken else 3000,  # mit Reasoning das volle Denkbudget
        max_retries=4,
        rate_limiter=_rate_limiter(),
        # Denkmodus über die Chat-Vorlage (DeepSeek: thinking, Qwen/GLM: enable_thinking)
        extra_body={"chat_template_kwargs": {"thinking": denken, "enable_thinking": denken}},
    )
