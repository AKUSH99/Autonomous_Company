"""Marktmodell: Bertrand-Wettbewerb mit Logit-Nachfrage.

Standardmodell der Forschung zu algorithmischer Kollusion (Calvano et al. 2020, Fish et al. 2024).
Jeder Shop i setzt einen Preis p_i. Die Kundschaft wählt zwischen den Shops und dem Nicht-Kauf
("Aussengut") nach einem Logit-Modell:

    s_i = exp((a - p_i/alpha) / mu) / ( Σ_j exp((a - p_j/alpha) / mu) + exp(a0 / mu) )
    q_i = beta * s_i
    Gewinn_i = (p_i - c) * q_i        mit c = kosten * alpha

Aus dem Modell lassen sich zwei Referenzpreise exakt berechnen:
- Nash-Preis: Kein Shop kann seinen Gewinn durch einseitige Preisänderung steigern (fairer Wettbewerb).
- Monopolpreis: Maximiert den gemeinsamen Gewinn aller Shops (perfektes Kartell).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class MarktParameter:
    firmen: int = 2
    a: float = 2.0        # Attraktivität der Produkte (gleich für alle Shops)
    a0: float = 0.0       # Attraktivität des Nicht-Kaufs
    mu: float = 0.25      # Produktdifferenzierung: klein = Kundschaft reagiert stark auf Preise
    kosten: float = 1.0   # Stückkosten in Einheiten von alpha
    alpha: float = 10.0   # Preisskala: alpha=10 ergibt Preise in einer CHF-Grössenordnung um 15
    beta: float = 100.0   # Mengenskala: potenzielle Kundschaft pro Runde


@dataclass(frozen=True)
class Benchmarks:
    nash_preis: float
    monopol_preis: float
    nash_gewinn: float      # Gewinn pro Shop im Nash-Gleichgewicht
    monopol_gewinn: float   # Gewinn pro Shop bei gemeinsamer Gewinnmaximierung
    grenzkosten: float

    def als_dict(self) -> dict:
        return {k: round(v, 4) for k, v in self.__dict__.items()}


class LogitMarkt:
    def __init__(self, parameter: MarktParameter):
        if parameter.firmen < 2:
            raise ValueError("Ein Markt braucht mindestens zwei Shops.")
        self.p = parameter

    @property
    def grenzkosten(self) -> float:
        return self.p.kosten * self.p.alpha

    def anteile(self, preise: Sequence[float]) -> np.ndarray:
        preise = np.asarray(preise, dtype=float)
        nutzen = (self.p.a - preise / self.p.alpha) / self.p.mu
        aussen = self.p.a0 / self.p.mu
        m = max(nutzen.max(), aussen)  # numerisch stabil
        e = np.exp(nutzen - m)
        return e / (e.sum() + np.exp(aussen - m))

    def mengen(self, preise: Sequence[float]) -> np.ndarray:
        return self.p.beta * self.anteile(preise)

    def gewinne(self, preise: Sequence[float]) -> np.ndarray:
        preise = np.asarray(preise, dtype=float)
        return (preise - self.grenzkosten) * self.mengen(preise)

    def _loese(self, aufschlag_von_anteil) -> float:
        """Löst p = c + aufschlag(p) für einen symmetrischen Preis per Bisektion.

        f(p) = p - c - aufschlag(p) ist monoton steigend (höherer Preis -> kleinerer Marktanteil ->
        kleinerer Aufschlag), negativ knapp über den Kosten und positiv bei sehr hohen Preisen.
        """
        f = lambda p: p - self.grenzkosten - aufschlag_von_anteil(self.anteile([p] * self.p.firmen))
        lo, hi = self.grenzkosten, self.grenzkosten + self.p.alpha * self.p.mu
        while f(hi) < 0:
            hi += self.p.alpha * self.p.mu * 4
        for _ in range(200):
            mitte = (lo + hi) / 2
            lo, hi = (mitte, hi) if f(mitte) < 0 else (lo, mitte)
        return float((lo + hi) / 2)

    def nash_preis(self) -> float:
        # Bedingung erster Ordnung im Logit-Modell: p - c = alpha * mu / (1 - s_i)
        return self._loese(lambda s: self.p.alpha * self.p.mu / (1 - s[0]))

    def monopol_preis(self) -> float:
        # Mehrprodukt-Monopolist: gleicher Aufschlag auf alle Produkte, p - c = alpha * mu / (1 - Σ s_j)
        return self._loese(lambda s: self.p.alpha * self.p.mu / (1 - s.sum()))

    def benchmarks(self) -> Benchmarks:
        pn, pm = self.nash_preis(), self.monopol_preis()
        n = self.p.firmen
        return Benchmarks(
            nash_preis=pn,
            monopol_preis=pm,
            nash_gewinn=float(self.gewinne([pn] * n)[0]),
            monopol_gewinn=float(self.gewinne([pm] * n)[0]),
            grenzkosten=self.grenzkosten,
        )
