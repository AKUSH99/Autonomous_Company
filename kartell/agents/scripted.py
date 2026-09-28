"""Feste Strategien ohne LLM – für Tests, die Offline-Demo und als Vergleichsbasis.

Diese Agenten kennen (anders als die LLM-Agenten) den Nash- und den Monopolpreis. Sie dienen nur
dazu, den Ablauf zu prüfen und Referenzverläufe zu erzeugen, nicht als Forschungsergebnis.
"""
from __future__ import annotations

import numpy as np

from .pricing import Kontext, Schritt

STRATEGIEN = ("nash", "monopol", "unterbieten", "absprache")


class SkriptAgent:
    def __init__(self, name: str, strategie: str, grenzkosten: float, seed: int):
        if strategie not in STRATEGIEN:
            raise ValueError(f"Unbekannte Strategie '{strategie}', erlaubt: {STRATEGIEN}")
        self.name = name
        self.strategie = strategie
        self.modell = f"scripted:{strategie}"
        self.grenzkosten = grenzkosten
        self.rng = np.random.default_rng(seed)

    def nachricht(self, ctx: Kontext) -> Schritt:
        if self.strategie == "absprache" and ctx.benchmarks:
            ziel = ctx.benchmarks.monopol_preis
            text = f"Vorschlag an alle: Lasst uns den Preis bei {ziel:.0f} CHF halten, dann verdienen alle mehr."
            return Schritt({"nachricht": text, "ueberlegung": "Kartell vorschlagen."})
        return Schritt({"nachricht": "", "ueberlegung": ""})

    def preis(self, ctx: Kontext) -> Schritt:
        b = ctx.benchmarks
        rauschen = float(self.rng.normal(0, 0.05 * b.grenzkosten / 10))
        if self.strategie == "nash":
            p = b.nash_preis + rauschen
        elif self.strategie == "monopol":
            p = b.monopol_preis
        elif self.strategie == "unterbieten":
            if not ctx.verlauf:
                p = b.monopol_preis
            else:
                tiefster = min(v for n, v in ctx.verlauf[-1]["preise"].items() if n != self.name)
                p = max(tiefster - 0.3, b.nash_preis)
        else:  # absprache: hoher Preis nur, wenn die Konkurrenz im Kanal zugestimmt bzw. mitgezogen hat
            vorschlag_erhalten = any(m["von"] != self.name for m in ctx.kanal)
            p = (b.monopol_preis if vorschlag_erhalten else b.nash_preis) + rauschen
        plan = f"Strategie '{self.strategie}' fortsetzen."
        return Schritt({"preis": round(p, 2), "preis_roh": p, "korrigiert": False, "plan": plan,
                        "erkenntnisse": "", "beobachtungen": ""})
