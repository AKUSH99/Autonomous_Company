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
from typing import Optional, Sequence

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
    # Unterschiedliche Stückkosten je Shop (in Einheiten von alpha), z. B. ein Discounter mit tieferen Kosten.
    # Ohne Angabe haben alle Shops dieselben Kosten `kosten`.
    kosten_je_firma: Optional[tuple[float, ...]] = None
    # Unterschiedliche Attraktivität je Shop (Service, Garantie, Lieferzeit, Bekanntheit) – ersetzt `a` pro Shop.
    a_je_firma: Optional[tuple[float, ...]] = None
    # Fixkosten pro Shop und Runde in CHF (Miete, Personal). Ändern Nash- und Monopolpreis nicht, aber den Gewinn:
    # Wer zu teuer ist und nichts verkauft, macht Verlust.
    fixkosten: float = 0.0


@dataclass(frozen=True)
class Benchmarks:
    nash_preis: float
    monopol_preis: float
    nash_gewinn: float      # Gewinn pro Shop im Nash-Gleichgewicht
    monopol_gewinn: float   # Gewinn pro Shop bei gemeinsamer Gewinnmaximierung
    grenzkosten: float
    # Bei unterschiedlichen Kosten: Preise je Shop; die Werte oben sind dann Durchschnitte über die Shops
    nash_preise: Optional[tuple[float, ...]] = None
    monopol_preise: Optional[tuple[float, ...]] = None

    def als_dict(self) -> dict:
        return {k: (round(v, 4) if isinstance(v, float) else [round(x, 4) for x in v])
                for k, v in self.__dict__.items() if v is not None}


class LogitMarkt:
    def __init__(self, parameter: MarktParameter):
        if parameter.firmen < 2:
            raise ValueError("Ein Markt braucht mindestens zwei Shops.")
        if parameter.kosten_je_firma is not None and len(parameter.kosten_je_firma) != parameter.firmen:
            raise ValueError("kosten_je_firma braucht genau einen Wert pro Shop.")
        if parameter.a_je_firma is not None and len(parameter.a_je_firma) != parameter.firmen:
            raise ValueError("a_je_firma braucht genau einen Wert pro Shop.")
        self.p = parameter

    @property
    def symmetrisch(self) -> bool:
        gleiche_kosten = self.p.kosten_je_firma is None or len(set(self.p.kosten_je_firma)) == 1
        gleiche_qualitaet = self.p.a_je_firma is None or len(set(self.p.a_je_firma)) == 1
        return gleiche_kosten and gleiche_qualitaet

    @property
    def attraktivitaet(self) -> np.ndarray:
        """Attraktivität a je Shop (ohne Angabe für alle gleich `a`)."""
        roh = self.p.a_je_firma if self.p.a_je_firma is not None else [self.p.a] * self.p.firmen
        return np.asarray(roh, dtype=float)

    @property
    def kostenvektor(self) -> np.ndarray:
        """Stückkosten je Shop in CHF."""
        roh = self.p.kosten_je_firma if self.p.kosten_je_firma is not None else [self.p.kosten] * self.p.firmen
        return np.asarray(roh, dtype=float) * self.p.alpha

    @property
    def grenzkosten(self) -> float:
        """Stückkosten in CHF (bei unterschiedlichen Kosten: Durchschnitt über die Shops)."""
        return float(self.kostenvektor.mean())

    def anteile(self, preise: Sequence[float]) -> np.ndarray:
        preise = np.asarray(preise, dtype=float)
        nutzen = (self.attraktivitaet - preise / self.p.alpha) / self.p.mu
        aussen = self.p.a0 / self.p.mu
        m = max(nutzen.max(), aussen)  # numerisch stabil
        e = np.exp(nutzen - m)
        return e / (e.sum() + np.exp(aussen - m))

    def mengen(self, preise: Sequence[float]) -> np.ndarray:
        return self.p.beta * self.anteile(preise)

    def gewinne(self, preise: Sequence[float]) -> np.ndarray:
        preise = np.asarray(preise, dtype=float)
        return (preise - self.kostenvektor) * self.mengen(preise) - self.p.fixkosten

    def _loese(self, aufschlag_von_anteil) -> float:
        """Löst p = c + aufschlag(p) für einen symmetrischen Preis per Bisektion.

        f(p) = p - c - aufschlag(p) ist monoton steigend (höherer Preis -> kleinerer Marktanteil ->
        kleinerer Aufschlag), negativ knapp über den Kosten und positiv bei sehr hohen Preisen.
        """
        c = float(self.kostenvektor[0])
        f = lambda p: p - c - aufschlag_von_anteil(self.anteile([p] * self.p.firmen))
        lo, hi = c, c + self.p.alpha * self.p.mu
        while f(hi) < 0:
            hi += self.p.alpha * self.p.mu * 4
        for _ in range(200):
            mitte = (lo + hi) / 2
            lo, hi = (mitte, hi) if f(mitte) < 0 else (lo, mitte)
        return float((lo + hi) / 2)

    def nash_preise(self) -> list[float]:
        """Nash-Preise je Shop. Bedingung erster Ordnung im Logit-Modell: p_i - c_i = alpha * mu / (1 - s_i)."""
        if self.symmetrisch:
            return [self._loese(lambda s: self.p.alpha * self.p.mu / (1 - s[0]))] * self.p.firmen
        c, preise = self.kostenvektor, self.kostenvektor + self.p.alpha * self.p.mu * 1.5
        for _ in range(5000):  # gedämpfte Fixpunkt-Iteration der besten Antworten
            neu = c + self.p.alpha * self.p.mu / (1 - self.anteile(preise))
            if np.abs(neu - preise).max() < 1e-10:
                break
            preise = 0.5 * preise + 0.5 * neu
        return [float(x) for x in preise]

    def monopol_preise(self) -> list[float]:
        """Preise je Shop bei gemeinsamer Gewinnmaximierung. Im Logit-Modell setzt ein Mehrprodukt-Monopolist auf alle
        Produkte denselben Aufschlag m = alpha * mu / (1 - Σ s_j) – auch bei unterschiedlichen Kosten."""
        if self.symmetrisch:
            return [self._loese(lambda s: self.p.alpha * self.p.mu / (1 - s.sum()))] * self.p.firmen
        c, am = self.kostenvektor, self.p.alpha * self.p.mu
        f = lambda m: m - am / (1 - self.anteile(c + m).sum())
        lo, hi = 0.0, am
        while f(hi) < 0:
            hi += am * 4
        for _ in range(200):
            mitte = (lo + hi) / 2
            lo, hi = (mitte, hi) if f(mitte) < 0 else (lo, mitte)
        return [float(x) for x in c + (lo + hi) / 2]

    def nash_preis(self) -> float:
        return float(np.mean(self.nash_preise()))

    def monopol_preis(self) -> float:
        return float(np.mean(self.monopol_preise()))

    def benchmarks(self) -> Benchmarks:
        pn, pm = self.nash_preise(), self.monopol_preise()
        return Benchmarks(
            nash_preis=float(np.mean(pn)),
            monopol_preis=float(np.mean(pm)),
            nash_gewinn=float(self.gewinne(pn).mean()),
            monopol_gewinn=float(self.gewinne(pm).mean()),
            grenzkosten=self.grenzkosten,
            nash_preise=None if self.symmetrisch else tuple(pn),
            monopol_preise=None if self.symmetrisch else tuple(pm),
        )
