"""Die Werkzeuge des Agenten (Function Calling). Jedes liefert Text mit Quellenangaben zurück."""
from __future__ import annotations

from langchain_core.tools import tool

from .fristen import Fristen
from .suche import Suche


def erstelle_werkzeuge(suche: Suche, fristen: Fristen) -> list:
    @tool
    def unterlagen_durchsuchen(frage: str, modul: str = "") -> str:
        """Durchsucht die Kursunterlagen (Folien, Semesterprogramme, Projektbeschriebe, Aufgaben) und liefert die
        passendsten Stellen mit Quelle. `modul`: optional ein Teil des Modulnamens, z. B. «Marketing» oder «Generative»."""
        treffer = suche.suchen(frage, k=5, modul=modul or None)
        if not treffer:
            return "Keine passende Stelle in den Unterlagen gefunden."
        return "\n\n".join(f"[{i}] {a.quelle()}\n{a.text[:700]}" for i, (a, _) in enumerate(treffer, 1))

    @tool
    def fristen_anzeigen(ab: str = "", bis: str = "", modul: str = "") -> str:
        """Listet Fristen, Abgaben, Prüfungen und Pflichttermine. `ab`/`bis` als Datum JJJJ-MM-TT (leer = alle),
        `modul` optional ein Teil des Modulnamens."""
        return Fristen.als_text(fristen.suchen(ab or None, bis or None, modul or None))

    @tool
    def module_auflisten() -> str:
        """Listet die Module, zu denen Unterlagen vorhanden sind."""
        return "\n".join(f"- {m}" for m in suche.module())

    return [unterlagen_durchsuchen, fristen_anzeigen, module_auflisten]
