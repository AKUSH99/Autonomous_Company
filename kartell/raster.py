"""Vorgerechnetes Raster für den Marktplatz: jede Regler-Kombination ein fertiger Lauf.

Das Verhalten der KI-Shops lässt sich nicht ausrechnen, nur beobachten – darum wird jede Kombination der Regler
vorab einmal gerechnet. Die Seite zeigt dann beim Verstellen sofort den passenden Lauf.

    python -m kartell raster --liste                          # alle Zellen
    python -m kartell raster --rechne --fertig fertig.txt --minuten 320 --ausgabe raster_runs

Die Zellen kommen in einer festen Reihenfolge (zuerst 6 Shops ohne Ereignis, dann der Rest), fertige werden
übersprungen. So kann der GitHub-Workflow «Raster rechnen» in mehreren Etappen weitermachen.
"""
from __future__ import annotations

import itertools
import time
from pathlib import Path

from .ereignisse import Ereignis
from .szenario import Szenario, katalog

SHOPS = (6, 2, 10)
KOMMUNIKATION = {  # Kürzel -> (Kommunikation, Aufsicht)
    "keine": ("keine", "aus"),
    "mitteilungen": ("mitteilungen", "aus"),
    "mitteilungen-compliance": ("mitteilungen", "compliance"),
    "chat": ("chat", "aus"),
    "chat-compliance": ("chat", "compliance"),
}
BUDGET = ("normal", "knapp", "grosszuegig")
EREIGNIS = ("keins", "zoll")
WOCHEN = 15
ZOLL = {"woche": 6, "art": "zoll", "staerke": 25}
MODELL = "swissai:RCP-AIaaS/deepseek-ai/DeepSeek-V4.1-Flash"


def zellen() -> list[dict]:
    """Alle Kombinationen, wichtigste zuerst (ohne Ereignis vor Zoll, 6 Shops vor 2 und 10)."""
    alle = []
    for ereignis, shops, komm, budget in itertools.product(EREIGNIS, SHOPS, KOMMUNIKATION, BUDGET):
        alle.append({"id": f"s{shops}_{komm}_{budget}_{ereignis}", "shops": shops, "kommunikation": komm,
                     "budget": budget, "ereignis": ereignis})
    return alle


def szenario(zelle: dict) -> Szenario:
    kommunikation, aufsicht = KOMMUNIKATION[zelle["kommunikation"]]
    namen = [f["name"] for f in katalog()][: zelle["shops"]]
    return Szenario(name=f"Raster {zelle['id']}", shops=namen, kunden=40, budget=zelle["budget"],
                    kommunikation=kommunikation, aufsicht=aufsicht, wochen=WOCHEN,
                    ereignisse=[Ereignis(**ZOLL)] if zelle["ereignis"] == "zoll" else [])


def rechne(fertig: set[str], minuten: float, ausgabe: str | Path, modell: str = MODELL) -> list[str]:
    """Rechnet offene Zellen, bis die Zeit fast um ist. Jede Zelle landet in <ausgabe>/<id>/. Gibt die neuen IDs zurück."""
    from .config import mit_modell
    from .runner import fuehre_experiment_aus
    start, neu = time.time(), []
    offen = [z for z in zellen() if z["id"] not in fertig]
    print(f"Raster: {len(fertig)} fertig, {len(offen)} offen, Zeitbudget {minuten:.0f} Min.")
    for z in offen:
        verbraucht = (time.time() - start) / 60
        # grob geschätzte Dauer der Zelle: Anfragen pro Woche / 14 pro Minute, plus Reserve
        ki = z["shops"]
        anfragen = ki * (1 if z["kommunikation"] == "keine" else 2) + 1 + (ki if z["kommunikation"].endswith("compliance") else 0)
        schaetzung = WOCHEN * anfragen / 14 * 1.3 + 2
        if verbraucht + schaetzung > minuten:
            print(f"Zeitbudget reicht nicht mehr für {z['id']} (~{schaetzung:.0f} Min.) – nächste Etappe.")
            break
        cfg = mit_modell(szenario(z).als_config(), modell)
        cfg.name = f"raster_{z['id']}"
        print(f"▶ {z['id']} (~{schaetzung:.0f} Min.)")
        try:
            fuehre_experiment_aus(cfg, ausgabe=Path(ausgabe) / z["id"], zeitlimit_min=schaetzung * 2)
            neu.append(z["id"])
        except Exception as e:  # noqa: BLE001 – eine Zelle darf das Raster nicht stoppen
            print(f"  Zelle {z['id']} fehlgeschlagen: {e}")
    return neu
