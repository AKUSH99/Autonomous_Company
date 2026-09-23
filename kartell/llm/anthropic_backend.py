"""Claude über das offizielle Anthropic-SDK mit strukturierten Ausgaben (Pydantic)."""
from __future__ import annotations

import anthropic

from ..config import LLMSpec
from .base import LLMAntwort, LLMFehler, T

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

    def strukturiert(self, system: str, nutzer: str, schema: type[T]) -> LLMAntwort[T]:
        kwargs: dict = dict(
            model=self.spec.model,
            max_tokens=self.spec.max_tokens,
            system=system,
            messages=[{"role": "user", "content": nutzer}],
            output_format=schema,
        )
        if self.spec.effort:
            kwargs["output_config"] = {"effort": self.spec.effort}
        if self.spec.model in _FALLBACK_MODELLE:
            kwargs["betas"] = [_FALLBACK_BETA]
            kwargs["fallbacks"] = "default"
        try:
            antwort = self.client.beta.messages.parse(**kwargs)
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

        if antwort.stop_reason == "refusal":
            kategorie = antwort.stop_details.category if antwort.stop_details else None
            raise LLMFehler(f"Modell hat abgelehnt (Kategorie: {kategorie}).")
        if antwort.stop_reason == "max_tokens":
            raise LLMFehler("Antwort wurde bei max_tokens abgeschnitten.")
        if antwort.parsed_output is None:
            raise LLMFehler("Keine strukturierte Ausgabe erhalten.")
        return LLMAntwort(
            objekt=antwort.parsed_output,
            input_tokens=antwort.usage.input_tokens,
            output_tokens=antwort.usage.output_tokens,
            modell=antwort.model,
        )
