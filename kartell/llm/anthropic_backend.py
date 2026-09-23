"""Claude über das offizielle Anthropic-SDK mit strukturierten Ausgaben (Pydantic)."""
from __future__ import annotations

import anthropic

from ..config import LLMSpec
from .base import MAX_WERKZEUG_RUNDEN, LLMAntwort, LLMFehler, T, Werkzeug, fuehre_werkzeug_aus

# Modelle, für die der serverseitige Refusal-Fallback empfohlen ist: lehnt das Modell eine Anfrage
# aus Sicherheitsgründen ab, rechnet die API sie im selben Aufruf mit einem passenden Modell neu.
_FALLBACK_MODELLE = {"claude-opus-5", "claude-fable-5-1"}
_FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicClient:
    def __init__(self, spec: LLMSpec, client: anthropic.Anthropic | None = None):
        self.spec = spec
        self.name = spec.kurzname
        # Zugangsdaten aus der Umgebung (ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN oder `ant auth login`)
        self.client = client or anthropic.Anthropic(max_retries=4)

    def strukturiert(self, system: str, nutzer: str, schema: type[T], werkzeuge: list[Werkzeug] | None = None) -> LLMAntwort[T]:
        messages: list[dict] = [{"role": "user", "content": nutzer}]
        kwargs: dict = dict(
            model=self.spec.model,
            max_tokens=self.spec.max_tokens,
            system=system,
            messages=messages,
            output_format=schema,
        )
        if werkzeuge:
            kwargs["tools"] = [{"name": w.name, "description": w.beschreibung, "input_schema": w.parameter.model_json_schema()}
                               for w in werkzeuge]
        if self.spec.effort:
            kwargs["output_config"] = {"effort": self.spec.effort}
        if self.spec.model in _FALLBACK_MODELLE:
            kwargs["betas"] = [_FALLBACK_BETA]
            kwargs["fallbacks"] = "default"
        tokens_in = tokens_out = 0
        protokoll: list[dict] = []
        for runde in range(MAX_WERKZEUG_RUNDEN + 1):
            if werkzeuge:
                # In der letzten Runde muss Claude antworten; die Werkzeug-Definitionen bleiben wegen der Historie gesetzt.
                kwargs["tool_choice"] = {"type": "auto"} if runde < MAX_WERKZEUG_RUNDEN else {"type": "none"}
            antwort = self._aufruf(kwargs)
            tokens_in += antwort.usage.input_tokens
            tokens_out += antwort.usage.output_tokens
            if antwort.stop_reason != "tool_use":
                break
            messages.append({"role": "assistant", "content": [
                {"type": "tool_use", "id": b.id, "name": b.name, "input": b.input} if b.type == "tool_use"
                else {"type": "text", "text": b.text} for b in antwort.content if b.type in ("tool_use", "text")]})
            ergebnisse = []
            for block in (b for b in antwort.content if b.type == "tool_use"):
                text, fehler = fuehre_werkzeug_aus(werkzeuge or [], block.name, block.input, protokoll)
                ergebnisse.append({"type": "tool_result", "tool_use_id": block.id, "content": text} | ({"is_error": True} if fehler else {}))
            messages.append({"role": "user", "content": ergebnisse})

        if antwort.stop_reason == "refusal":
            kategorie = antwort.stop_details.category if antwort.stop_details else None
            raise LLMFehler(f"Modell hat abgelehnt (Kategorie: {kategorie}).", tokens_in, tokens_out)
        if antwort.stop_reason == "max_tokens":
            raise LLMFehler("Antwort wurde bei max_tokens abgeschnitten.", tokens_in, tokens_out)
        if antwort.parsed_output is None:
            raise LLMFehler("Keine strukturierte Ausgabe erhalten.", tokens_in, tokens_out)
        return LLMAntwort(objekt=antwort.parsed_output, input_tokens=tokens_in, output_tokens=tokens_out,
                          modell=antwort.model, werkzeug_aufrufe=protokoll)

    def _aufruf(self, kwargs: dict):
        try:
            return self.client.beta.messages.parse(**kwargs)
        except anthropic.BadRequestError as e:
            raise LLMFehler(f"Ungültige Anfrage an {self.spec.model}: {e.message}") from e
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
            raise LLMFehler("Keine gültigen Anthropic-Zugangsdaten (ANTHROPIC_API_KEY setzen).") from e
        except anthropic.RateLimitError as e:
            raise LLMFehler("Rate-Limit erreicht, auch nach automatischen Wiederholungen.") from e
        except anthropic.APIStatusError as e:
            raise LLMFehler(f"API-Fehler {e.status_code}: {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise LLMFehler("Keine Verbindung zur Anthropic-API.") from e
