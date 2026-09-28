"""Offene Modelle (z. B. Apertus) hinter einer OpenAI-kompatiblen Schnittstelle.

Funktioniert mit vLLM, Ollama, LM Studio oder Hosting-Anbietern, die eine /v1/chat/completions-
Schnittstelle anbieten. Nicht jeder Server unterstützt JSON-Schema-Ausgaben; deshalb wird die Antwort
zusätzlich tolerant geparst und bei Fehlern einmal mit Fehlerhinweis wiederholt.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time

import openai
from pydantic import ValidationError

from ..config import LLMSpec
from .base import MAX_WERKZEUG_RUNDEN, LLMAntwort, LLMFehler, T, Werkzeug, fuehre_werkzeug_aus


def _json_aus_text(text: str) -> dict:
    text = text.strip()
    block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if block:
        text = block.group(1)
    else:
        start, ende = text.find("{"), text.rfind("}")
        if start == -1 or ende == -1:
            raise ValueError("Kein JSON-Objekt in der Antwort.")
        text = text[start:ende + 1]
    return json.loads(text)


# Gratismodelle teilen sich beim Anbieter einen Pool; „temporarily rate-limited upstream“ ist dort normal.
# Mit Taktbremse (anfragen_pro_minute) wird deshalb geduldig wiederholt – nie aber beim Tageslimit.
GEDULD_S = (20, 45, 90)

_TAKT_SPERRE = threading.Lock()
_NAECHSTE_ANFRAGE: dict[str, float] = {}


def _warte_auf_takt(schluessel: str, pro_minute: int) -> None:
    """Hält Anfragen an denselben Anbieter mindestens 60/pro_minute Sekunden auseinander – auch über Threads hinweg."""
    with _TAKT_SPERRE:
        jetzt = time.monotonic()
        start = max(jetzt, _NAECHSTE_ANFRAGE.get(schluessel, jetzt))
        _NAECHSTE_ANFRAGE[schluessel] = start + 60 / pro_minute
    if start > jetzt:
        time.sleep(start - jetzt)


class OpenAICompatClient:
    def __init__(self, spec: LLMSpec, client: openai.OpenAI | None = None):
        if not spec.base_url and client is None:
            raise ValueError("openai_compat braucht eine base_url, z. B. http://localhost:8000/v1")
        self.spec = spec
        self.name = spec.kurzname
        api_key = os.environ.get(spec.api_key_env, "") if spec.api_key_env else "nicht-benoetigt"
        self.client = client or openai.OpenAI(base_url=spec.base_url, api_key=api_key or "nicht-benoetigt", max_retries=4)
        self._json_schema_ok = True

    def _anfrage(self, messages: list[dict], schema: type[T], werkzeug_kwargs: dict | None = None):
        kwargs: dict = dict(model=self.spec.model, messages=messages, max_tokens=self.spec.max_tokens)
        if self.spec.temperature is not None:
            kwargs["temperature"] = self.spec.temperature
        if self.spec.extra_body:
            kwargs["extra_body"] = self.spec.extra_body
        if werkzeug_kwargs:
            kwargs |= werkzeug_kwargs  # mit Werkzeugen kein JSON-Schema-Zwang: das Format kommt aus dem Prompt
        elif self._json_schema_ok:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()},
            }
        wartezeiten = list(GEDULD_S) if self.spec.anfragen_pro_minute else []
        while True:
            try:
                return self._erstelle(kwargs, werkzeug_kwargs)
            except openai.RateLimitError as e:
                if not wartezeiten or "per-day" in str(e):
                    raise
                time.sleep(wartezeiten.pop(0))

    def _erstelle(self, kwargs: dict, werkzeug_kwargs: dict | None):
        if self.spec.anfragen_pro_minute:
            _warte_auf_takt(self.spec.base_url or "", self.spec.anfragen_pro_minute)
        try:
            return self.client.chat.completions.create(**kwargs)
        except openai.BadRequestError:
            if not self._json_schema_ok or werkzeug_kwargs:
                raise  # ohne Schema abgelehnt oder Werkzeuge nicht unterstützt: Fehler sichtbar machen
            self._json_schema_ok = False  # Server kann kein JSON-Schema: ab jetzt nur noch per Prompt
            kwargs.pop("response_format")
            return self.client.chat.completions.create(**kwargs)

    def strukturiert(self, system: str, nutzer: str, schema: type[T], werkzeuge: list[Werkzeug] | None = None) -> LLMAntwort[T]:
        schema_text = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        messages = [
            {"role": "system", "content": f"{system}\n\nAntworte nur mit einem JSON-Objekt nach diesem Schema:\n{schema_text}"},
            {"role": "user", "content": nutzer},
        ]
        tokens_in = tokens_out = 0
        letzter_fehler = ""
        protokoll: list[dict] = []
        werkzeug_runden = json_versuche = 0
        definitionen = [{"type": "function", "function": {"name": w.name, "description": w.beschreibung,
                                                           "parameters": w.parameter.model_json_schema()}} for w in werkzeuge or []]
        while json_versuche < 2:
            werkzeug_kwargs = None
            if definitionen:
                werkzeug_kwargs = {"tools": definitionen, "tool_choice": "auto" if werkzeug_runden < MAX_WERKZEUG_RUNDEN else "none"}
            try:
                antwort = self._anfrage(messages, schema, werkzeug_kwargs)
            except openai.APIError as e:
                raise LLMFehler(f"{self.spec.model}: {e}", tokens_in, tokens_out) from e
            if getattr(antwort, "usage", None):
                tokens_in += antwort.usage.prompt_tokens or 0
                tokens_out += antwort.usage.completion_tokens or 0
            if not getattr(antwort, "choices", None):  # manche Anbieter melden Fehler als Antwort ohne choices
                raise LLMFehler(f"{self.spec.model}: leere Antwort ohne choices ({str(getattr(antwort, 'error', '') or '')[:200]})",
                                tokens_in, tokens_out)
            wahl = antwort.choices[0]
            aufrufe = getattr(wahl.message, "tool_calls", None) or []
            if aufrufe and werkzeug_runden < MAX_WERKZEUG_RUNDEN:
                werkzeug_runden += 1
                messages.append({"role": "assistant", "content": wahl.message.content or "", "tool_calls": [
                    {"id": a.id, "type": "function", "function": {"name": a.function.name, "arguments": a.function.arguments}}
                    for a in aufrufe]})
                for a in aufrufe:
                    try:
                        argumente = json.loads(a.function.arguments or "{}")
                    except json.JSONDecodeError:
                        argumente = {}
                    text, _ = fuehre_werkzeug_aus(werkzeuge or [], a.function.name, argumente, protokoll)
                    messages.append({"role": "tool", "tool_call_id": a.id, "content": text})
                continue
            json_versuche += 1
            text = wahl.message.content or ""
            if wahl.finish_reason == "length":
                # Nochmals fragen hilft nicht: das Limit ist erreicht, bevor die Antwort fertig ist (oft ein langer Denkprozess).
                raise LLMFehler(f"{self.spec.model}: Antwort bei max_tokens={self.spec.max_tokens} abgeschnitten "
                                f"({antwort.usage.completion_tokens if antwort.usage else '?'} Output-Tokens).", tokens_in, tokens_out)
            try:
                objekt = schema.model_validate(_json_aus_text(text))
                return LLMAntwort(objekt=objekt, input_tokens=tokens_in, output_tokens=tokens_out, modell=self.spec.model,
                                  werkzeug_aufrufe=protokoll)
            except (ValueError, ValidationError) as e:
                letzter_fehler = str(e)[:300]
                messages += [
                    {"role": "assistant", "content": text},
                    {"role": "user", "content": f"Die Antwort war kein gültiges JSON nach Schema ({letzter_fehler}). Bitte nur das JSON-Objekt."},
                ]
        raise LLMFehler(f"{self.spec.model} lieferte kein gültiges JSON: {letzter_fehler}", tokens_in, tokens_out)
