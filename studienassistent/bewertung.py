"""Evaluation: Findet der Assistent die richtige Quelle, stimmt die Antwort, lehnt er das Richtige ab?

Testset (JSON Lines), je Zeile:
    {"frage": "...", "quelle": "Teil von Modul oder Dateiname",           # erwartete Fundstelle (optional)
     "fakten": ["10 Min", ["20.12", "20. Dezember"]],                      # müssen in der Antwort stehen; Liste = eine davon
     "ablehnen": false}                                                    # soll die Prüfung die Frage abweisen?
Kennzahlen:
    Quelle in Top 5   – Anteil der Fragen, bei denen die Suche eine passende Stelle unter den ersten 5 findet
    Fakten richtig    – Anteil der Antworten, die alle erwarteten Fakten enthalten
    Ablehnung richtig – Anteil, bei dem abgelehnt bzw. beantwortet wurde wie erwartet
    Quelle genannt    – Anteil der beantworteten Studienfragen, deren Antwort eine «(Quelle: …)»-Angabe enthält
    Antwortzeit       – Median und Anteil unter ZIEL_SEKUNDEN, gemessen von der Frage bis zur fertigen Antwort
"""
from __future__ import annotations

import json
import re
import statistics
import time
import uuid
from pathlib import Path


ZIEL_SEKUNDEN = 20
_QUELLE = re.compile(r"\(\s*Quelle", re.IGNORECASE)


def quelle_genannt(antwort: str) -> bool:
    return bool(_QUELLE.search(antwort))


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace(" ", " "))


def fakten_ok(antwort: str, fakten: list) -> bool:
    a = _norm(antwort)
    return all(any(_norm(f) in a for f in (fakt if isinstance(fakt, list) else [fakt])) for fakt in fakten)


def bewerte(graph, suche, testset: Path, nur_suche: bool = False) -> dict:
    from .agent import fragen
    faelle = [json.loads(z) for z in testset.read_text(encoding="utf-8").splitlines() if z.strip()]
    zeilen = []
    for fall in faelle:
        z = {"frage": fall["frage"], "quelle_ok": None, "fakten_ok": None, "ablehnung_ok": None, "quelle_genannt": None,
             "sekunden": None}
        if fall.get("quelle"):
            treffer = suche.suchen(fall["frage"], k=5)
            z["quelle_ok"] = any(fall["quelle"].lower() in f"{a.modul} {a.datei}".lower() for a, _ in treffer)
        if not nur_suche:
            start = time.time()
            r = fragen(graph, fall["frage"], thread_id=str(uuid.uuid4()))
            z["sekunden"] = round(time.time() - start, 1)
            z["antwort"] = r["antwort"]
            z["ablehnung_ok"] = r["abgelehnt"] == bool(fall.get("ablehnen"))
            if not fall.get("ablehnen") and not r["abgelehnt"]:
                z["quelle_genannt"] = quelle_genannt(r["antwort"])
            if fall.get("fakten") and not fall.get("ablehnen"):
                z["fakten_ok"] = fakten_ok(r["antwort"], fall["fakten"])
        zeilen.append(z)

    def anteil(feld):
        werte = [z[feld] for z in zeilen if z[feld] is not None]
        return (sum(werte) / len(werte), len(werte)) if werte else (None, 0)

    zeiten = [z["sekunden"] for z in zeilen if z["sekunden"] is not None]
    zeit = {"median": statistics.median(zeiten), "max": max(zeiten),
            "unter_ziel": sum(s < ZIEL_SEKUNDEN for s in zeiten) / len(zeiten)} if zeiten else None
    return {"quelle": anteil("quelle_ok"), "fakten": anteil("fakten_ok"), "ablehnung": anteil("ablehnung_ok"),
            "quelle_genannt": anteil("quelle_genannt"), "zeit": zeit, "faelle": zeilen}


def ohne_antworten(e: dict) -> dict:
    """Für das öffentliche Repository: Kennzahlen und Ergebnis je Frage, aber keine Antworttexte (sie zitieren
    Kursunterlagen)."""
    return e | {"faelle": [{k: v for k, v in z.items() if k != "antwort"} for z in e["faelle"]]}


def tabelle(e: dict) -> str:
    zeilen = ["| Kennzahl | Wert | Fragen |", "|---|---|---|"]
    for name, key in (("Quelle in Top 5", "quelle"), ("Fakten richtig", "fakten"), ("Ablehnung richtig", "ablehnung"),
                      ("Quelle genannt", "quelle_genannt")):
        wert, n = e[key]
        zeilen.append(f"| {name} | {'–' if wert is None else f'{wert:.0%}'} | {n} |")
    if e.get("zeit"):
        z = e["zeit"]
        zeilen.append(f"| Antwortzeit (Median, max) | {z['median']:.0f} s, {z['max']:.0f} s | {len([f for f in e['faelle'] if f['sekunden']])} |")
        zeilen.append(f"| Antwort unter {ZIEL_SEKUNDEN} s | {z['unter_ziel']:.0%} | |")
    fehler = [z for z in e["faelle"] if False in (z["quelle_ok"], z["fakten_ok"], z["ablehnung_ok"])]
    if fehler:
        zeilen += ["", "Nicht bestanden:"] + [f"- {z['frage']}" + (f" → {z.get('antwort', '')[:160]!r}" if z.get("antwort") else "")
                                             for z in fehler]
    return "\n".join(zeilen)
