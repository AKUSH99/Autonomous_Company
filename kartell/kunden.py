"""Die Kundschaft: einzelne simulierte Kundinnen und Kunden und was ein Kartell sie kostet.

Die Logit-Nachfrage in market.py beschreibt genau eine Menge einzelner Kunden mit eigenen Vorlieben
(„Random-Utility-Modell“): Kundin k zieht aus dem Kauf bei Shop j den Nutzen
    u_kj = a - p_j/alpha + mu·ε_kj      und aus dem Nicht-Kauf   u_k0 = a0 + mu·ε_k0
mit zufälligen Vorlieben ε (Gumbel-verteilt). Jede Person wählt das Beste für sich; über viele Personen ergeben sich
genau die Marktanteile der Logit-Formel. Dieses Modul macht die Personen sichtbar – mit festen Vorlieben über alle
Runden (wer Shop A mag, mag ihn auch morgen) – und rechnet in Franken aus, was sie ein Kartell kostet.

Kundenschaden = Konsumentenrente bei Wettbewerbspreisen (Nash) minus Konsumentenrente bei den tatsächlichen Preisen.
Im Logit-Modell ist die erwartete Konsumentenrente pro Person  alpha·mu·ln(Σ_j exp(u_j/mu) + exp(a0/mu)) + Konstante;
die Konstante fällt in der Differenz weg.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .market import LogitMarkt, MarktParameter

VORNAMEN = ["Lena", "Marco", "Sara", "Luca", "Mia", "Noah", "Elena", "Jonas", "Lea", "David", "Nina", "Samuel", "Laura",
            "Elias", "Anna", "Tim", "Julia", "Nico", "Alina", "Leon", "Chiara", "Fabio", "Lara", "Dario", "Selina", "Jan",
            "Ronja", "Gian", "Aylin", "Milan"]


def konsumentenrente(markt: LogitMarkt, preise: Sequence[float]) -> float:
    """Erwartete Konsumentenrente pro Runde in CHF (für alle beta potenziellen Kunden, bis auf eine Konstante)."""
    p = markt.p
    nutzen = (p.a - np.asarray(preise, dtype=float) / p.alpha) / p.mu
    aussen = p.a0 / p.mu
    m = max(nutzen.max(), aussen)
    return float(p.beta * p.alpha * p.mu * (m + np.log(np.exp(nutzen - m).sum() + np.exp(aussen - m))))


def kundenschaden(runden: list[dict], parameter: MarktParameter, anteil_ende: float = 0.5) -> dict:
    """Was kosten die Preise der zweiten Hälfte die Kundschaft gegenüber Wettbewerbspreisen?

    schaden_pro_kunde: CHF pro potenzieller Kundin und Runde (positiv = Kunden zahlen drauf, negativ = sie sparen)
    schaden_prozent: Verlust an Konsumentenrente relativ zur Rente bei Wettbewerb, gemessen über dem Wert ohne Kauf
    ohne_kauf / ohne_kauf_nash: Anteil der Kundschaft, der gar nicht kauft
    """
    markt = LogitMarkt(parameter)
    nash = markt.nash_preis()
    shops = list(runden[0]["preise"])
    ende = runden[int(len(runden) * (1 - anteil_ende)):] or runden[-1:]
    rente_nash = konsumentenrente(markt, [nash] * len(shops))
    renten = [konsumentenrente(markt, [r["preise"][s] for s in shops]) for r in ende]
    # Rente relativ zum Nicht-Kauf (dort ist sie null): so wird der Prozentwert unabhängig von der Konstante
    null = parameter.beta * parameter.alpha * parameter.a0
    schaden = rente_nash - float(np.mean(renten))
    ohne = [1 - markt.anteile([r["preise"][s] for s in shops]).sum() for r in ende]
    return {
        "schaden_pro_runde": round(schaden, 2),
        "schaden_pro_kunde": round(schaden / parameter.beta, 3),
        "schaden_prozent": round(100 * schaden / (rente_nash - null), 1),
        "ohne_kauf": round(float(np.mean(ohne)), 3),
        "ohne_kauf_nash": round(float(1 - markt.anteile([nash] * len(shops)).sum()), 3),
    }


@dataclass
class Person:
    name: str
    zahlungsbereitschaft: list[float]  # je Shop: Preis in CHF, bis zu dem sich der Kauf dort lohnt (ohne Konkurrenz)
    ohne_kauf: float                   # Nutzen des Nicht-Kaufs in CHF (meist nahe 0)

    def waehle(self, preise: Sequence[float]) -> int | None:
        """Index des gewählten Shops oder None (kauft nicht)."""
        netto = [w - p for w, p in zip(self.zahlungsbereitschaft, preise)]
        beste = int(np.argmax(netto))
        return beste if netto[beste] > self.ohne_kauf else None

    def typ(self, shops: Sequence[str]) -> str:
        """Kurzbeschreibung aus den Vorlieben – für Menschen lesbar."""
        w = self.zahlungsbereitschaft
        reihen = sorted(range(len(w)), key=lambda i: -w[i])
        vorsprung = w[reihen[0]] - w[reihen[1]]
        grenze = w[reihen[0]] - self.ohne_kauf
        if vorsprung >= 2.0:
            art = f"Stammkundschaft von {shops[reihen[0]]} (zahlt dort bis {vorsprung:.2f} CHF mehr)"
        elif vorsprung < 0.5:
            art = "Schnäppchenjagd (kauft, wo es billiger ist)"
        else:
            art = f"leichte Vorliebe für {shops[reihen[0]]}"
        return f"{art}, kauft höchstens bis {grenze:.2f} CHF"


def kundschaft(parameter: MarktParameter, shops: Sequence[str], anzahl: int = 100, seed: int = 7) -> list[Person]:
    """Feste Gruppe simulierter Personen, deren Vorlieben genau der Logit-Nachfrage des Markts entsprechen."""
    rng = np.random.default_rng(seed)
    eps = rng.gumbel(size=(anzahl, len(shops) + 1))
    namen = [VORNAMEN[i % len(VORNAMEN)] + ("" if i < len(VORNAMEN) else f" {i // len(VORNAMEN) + 1}") for i in range(anzahl)]
    p = parameter
    return [Person(name=namen[k],
                   zahlungsbereitschaft=[round(p.alpha * (p.a + p.mu * eps[k, j]), 2) for j in range(len(shops))],
                   ohne_kauf=round(p.alpha * (p.a0 + p.mu * eps[k, -1]), 2))
            for k in range(anzahl)]
