from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

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


class LLMClient(Protocol):
    name: str

    def strukturiert(self, system: str, nutzer: str, schema: type[T]) -> LLMAntwort[T]:
        """Schickt System- und Nutzer-Prompt und liefert eine validierte Instanz von `schema`."""
        ...
