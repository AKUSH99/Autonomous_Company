"""Werkzeuge für die Preisagenten (Tool-Use).

Der Nachfrage-Schätzer rechnet nur mit Daten, die der Agent ohnehin sieht (eigene Preise und Mengen, Preise der
Konkurrenz). Er verrät weder die wahre Nachfragefunktion noch Wettbewerbs- oder Kartellpreis – sonst würde das
Werkzeug das Ergebnis vorgeben statt die Frage zu beantworten, ob analytische Hilfsmittel Kollusion verändern.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from pydantic import BaseModel, Field

from ..llm import Werkzeug

MIN_DATENPUNKTE = 3
FENSTER = 20  # jüngste Runden, aus denen geschätzt wird


class NachfrageAnfrage(BaseModel):
    eigener_preis: float = Field(description="Preis in CHF, den du prüfen möchtest")
    konkurrenzpreis: Optional[float] = Field(
        None, description="Angenommener Durchschnittspreis der Konkurrenz in CHF; leer = zuletzt beobachteter Wert")


def nachfrage_schaetzer(verlauf: list[dict], name: str, stueckkosten: float) -> Werkzeug:
    def schaetze(a: NachfrageAnfrage) -> dict:
        daten = [(r["preise"][name], float(np.mean([p for n, p in r["preise"].items() if n != name])), r["mengen"][name])
                 for r in verlauf[-FENSTER:]]
        if len(daten) < MIN_DATENPUNKTE:
            return {"hinweis": f"Zu wenige Runden für eine Schätzung (mindestens {MIN_DATENPUNKTE}, bisher {len(daten)})."}
        x = np.array([[1.0, p, k] for p, k, _ in daten])
        y = np.array([q for _, _, q in daten])
        koeff, *_ = np.linalg.lstsq(x, y, rcond=None)
        rest = y - x @ koeff
        streuung = float(((y - y.mean()) ** 2).sum())
        r2 = 1 - float((rest ** 2).sum()) / streuung if streuung > 0 else 0.0
        konkurrenz = a.konkurrenzpreis if a.konkurrenzpreis is not None else daten[-1][1]
        menge = max(0.0, float(koeff @ [1.0, a.eigener_preis, konkurrenz]))
        return {
            "eigener_preis": a.eigener_preis, "angenommener_konkurrenzpreis": round(konkurrenz, 2),
            "geschaetzte_menge": round(menge, 2), "geschaetzter_gewinn": round((a.eigener_preis - stueckkosten) * menge, 2),
            "datenpunkte": len(daten), "r2": round(r2, 3),
            "hinweis": "Lineare Schätzung aus deinen bisherigen Runden – je weiter der Preis von bisherigen Preisen weg liegt, "
                       "desto unsicherer. Keine Garantie.",
        }

    return Werkzeug(
        name="nachfrage_schaetzen",
        beschreibung="Schätzt aus deinen bisherigen Runden (eigener Preis, Konkurrenzpreis, verkaufte Menge), wie viel du bei "
                     "einem bestimmten Preis verkaufen würdest und welcher Gewinn daraus folgt. Kann mehrmals aufgerufen werden.",
        parameter=NachfrageAnfrage,
        funktion=schaetze,
    )


VERFUEGBAR = {"nachfrage_schaetzen": nachfrage_schaetzer}
