"""Fristen und Termine: eine Liste mit Datum, Modul, Titel und Beleg (z. B. aus dem Semesterprogramm).

Format (JSON-Liste), wie sie der Studien-Tagescheck erzeugt:
    [{"date": "2026-11-23", "time": "13:00", "module": "Generative KI", "title": "Abschlusspräsentation",
      "evidence": "Semesterprogramm S. 1", "sort": "2026-11-23"}, …]
Datei: <daten>/fristen.json (oder eigener Pfad).
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path


class Fristen:
    def __init__(self, eintraege: list[dict]):
        self.eintraege = eintraege

    @classmethod
    def laden(cls, datei: Path) -> "Fristen":
        if not datei.exists():
            return cls([])
        daten = json.loads(datei.read_text(encoding="utf-8"))
        return cls(daten if isinstance(daten, list) else daten.get("items", daten.get("deadlines", [])))

    def suchen(self, ab: str | None = None, bis: str | None = None, modul: str | None = None) -> list[dict]:
        """Termine im Zeitraum [ab, bis] (ISO-Daten), optional nur ein Modul. Ohne ISO-Datum (z. B. «Januar») nur ohne Zeitraum."""
        treffer = []
        for e in self.eintraege:
            if modul and modul.lower() not in str(e.get("module", "")).lower():
                continue
            sort = str(e.get("sort") or e.get("date") or "")[:10]
            hat_datum = len(sort) == 10 and sort[4] == "-"
            if (ab or bis) and not hat_datum:
                continue
            if ab and sort < ab or bis and sort > bis:
                continue
            treffer.append(e)
        return sorted(treffer, key=lambda e: str(e.get("sort") or e.get("date") or "9999"))

    @staticmethod
    def als_text(eintraege: list[dict]) -> str:
        if not eintraege:
            return "Keine Termine gefunden."
        zeilen = []
        for e in eintraege:
            zeit = f" {e['time']}" if e.get("time") else ""
            beleg = f" (Beleg: {e['evidence']})" if e.get("evidence") else ""
            zeilen.append(f"- {e.get('date', '?')}{zeit} · {e.get('module', '?')}: {e.get('title', '')}{beleg}")
        return "\n".join(zeilen)


def heute() -> str:
    return dt.date.today().isoformat()
