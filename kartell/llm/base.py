from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable, Generic, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class LLMFehler(RuntimeError):
    """Das Modell hat keine gültige Antwort geliefert (Ablehnung, Abbruch, ungültiges JSON).

    Trägt die bis dahin verbrauchten Tokens mit – auch gescheiterte Aufrufe kosten Geld.
    """

    def __init__(self, meldung: str, input_tokens: int = 0, output_tokens: int = 0):
        super().__init__(meldung)
        self.input_tokens, self.output_tokens = input_tokens, output_tokens


@dataclass
class LLMAntwort(Generic[T]):
    objekt: T
    input_tokens: int = 0
    output_tokens: int = 0
    modell: str = ""
    werkzeug_aufrufe: list[dict] = field(default_factory=list)  # Protokoll: Name, Argumente, Ergebnis


MAX_WERKZEUG_RUNDEN = 3  # danach muss das Modell antworten, ohne weitere Werkzeuge aufzurufen


@dataclass
class Werkzeug:
    """Ein Werkzeug, das ein Agent während einer Antwort aufrufen kann (Tool-Use), backend-unabhängig beschrieben."""
    name: str
    beschreibung: str
    parameter: type[BaseModel]
    funktion: Callable[[BaseModel], dict]

    def ausfuehren(self, argumente: dict) -> tuple[str, bool]:
        """Liefert (Ergebnis als JSON-Text, ist_fehler). Fehler gehen als Hinweis ans Modell zurück, nicht als Absturz."""
        try:
            return json.dumps(self.funktion(self.parameter.model_validate(argumente)), ensure_ascii=False), False
        except (ValidationError, ValueError, TypeError) as e:
            return f"Fehler: {e}", True


def fuehre_werkzeug_aus(werkzeuge: list[Werkzeug], name: str, argumente: dict, protokoll: list[dict]) -> tuple[str, bool]:
    werkzeug = next((w for w in werkzeuge if w.name == name), None)
    text, fehler = werkzeug.ausfuehren(argumente) if werkzeug else (f"Fehler: unbekanntes Werkzeug {name}", True)
    protokoll.append({"name": name, "argumente": argumente, "ergebnis": text[:500], "fehler": fehler})
    return text, fehler


class LLMClient(Protocol):
    name: str

    def strukturiert(self, system: str, nutzer: str, schema: type[T], werkzeuge: list[Werkzeug] | None = None) -> LLMAntwort[T]:
        """Schickt System- und Nutzer-Prompt und liefert eine validierte Instanz von `schema`.

        Mit `werkzeuge` darf das Modell vorher bis zu MAX_WERKZEUG_RUNDEN Mal Werkzeuge aufrufen.
        """
        ...
