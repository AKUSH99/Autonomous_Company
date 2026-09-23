"""Offene Modelle (z. B. Apertus) hinter einer OpenAI-kompatiblen Schnittstelle.

Funktioniert mit vLLM, Ollama, LM Studio oder Hosting-Anbietern, die eine /v1/chat/completions-
Schnittstelle anbieten. Nicht jeder Server unterstützt JSON-Schema-Ausgaben; deshalb wird die Antwort
zusätzlich tolerant geparst und bei Fehlern einmal mit Fehlerhinweis wiederholt.
"""
from __future__ import annotations

import json
import os
import re

import openai
from pydantic import ValidationError

from ..config import LLMSpec
from .base import LLMAntwort, LLMFehler, T


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


class OpenAICompatClient:
    def __init__(self, spec: LLMSpec, client: openai.OpenAI | None = None):
        if not spec.base_url and client is None:
            raise ValueError("openai_compat braucht eine base_url, z. B. http://localhost:8000/v1")
        self.spec = spec
        self.name = spec.kurzname
        api_key = os.environ.get(spec.api_key_env, "") if spec.api_key_env else "nicht-benoetigt"
        self.client = client or openai.OpenAI(base_url=spec.base_url, api_key=api_key or "nicht-benoetigt", max_retries=4)
        self._json_schema_ok = True

    def _anfrage(self, messages: list[dict], schema: type[T]):
        kwargs: dict = dict(model=self.spec.model, messages=messages, max_tokens=self.spec.max_tokens)
        if self.spec.temperature is not None:
            kwargs["temperature"] = self.spec.temperature
        if self.spec.extra_body:
            kwargs["extra_body"] = self.spec.extra_body
        if self._json_schema_ok:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()},
            }
        try:
            return self.client.chat.completions.create(**kwargs)
        except openai.BadRequestError:
            if not self._json_schema_ok:
                raise
            self._json_schema_ok = False  # Server kann kein JSON-Schema: ab jetzt nur noch per Prompt
            kwargs.pop("response_format")
            return self.client.chat.completions.create(**kwargs)

    def strukturiert(self, system: str, nutzer: str, schema: type[T]) -> LLMAntwort[T]:
        schema_text = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        messages = [
            {"role": "system", "content": f"{system}\n\nAntworte nur mit einem JSON-Objekt nach diesem Schema:\n{schema_text}"},
            {"role": "user", "content": nutzer},
        ]
        tokens_in = tokens_out = 0
        letzter_fehler = ""
        for versuch in range(2):
            try:
                antwort = self._anfrage(messages, schema)
            except openai.APIError as e:
                raise LLMFehler(f"{self.spec.model}: {e}", tokens_in, tokens_out) from e
            if antwort.usage:
                tokens_in += antwort.usage.prompt_tokens or 0
                tokens_out += antwort.usage.completion_tokens or 0
            wahl = antwort.choices[0]
            text = wahl.message.content or ""
            if wahl.finish_reason == "length":
                # Nochmals fragen hilft nicht: das Limit ist erreicht, bevor die Antwort fertig ist (oft ein langer Denkprozess).
                raise LLMFehler(f"{self.spec.model}: Antwort bei max_tokens={self.spec.max_tokens} abgeschnitten "
                                f"({antwort.usage.completion_tokens if antwort.usage else '?'} Output-Tokens).", tokens_in, tokens_out)
            try:
                objekt = schema.model_validate(_json_aus_text(text))
                return LLMAntwort(objekt=objekt, input_tokens=tokens_in, output_tokens=tokens_out, modell=self.spec.model)
            except (ValueError, ValidationError) as e:
                letzter_fehler = str(e)[:300]
                messages += [
                    {"role": "assistant", "content": text},
                    {"role": "user", "content": f"Die Antwort war kein gültiges JSON nach Schema ({letzter_fehler}). Bitte nur das JSON-Objekt."},
                ]
        raise LLMFehler(f"{self.spec.model} lieferte kein gültiges JSON: {letzter_fehler}", tokens_in, tokens_out)
