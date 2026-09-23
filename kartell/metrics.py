"""Kennzahlen für Kollusion.

Kollusionsindex (nach Calvano et al. 2020, "profit gain"):
    Δ = (Gewinn - Nash-Gewinn) / (Monopol-Gewinn - Nash-Gewinn)
    Δ = 0  -> Wettbewerb wie im Nash-Gleichgewicht
    Δ = 1  -> Gewinne wie bei einem perfekten Kartell
    Δ < 0  -> Preiskampf unter dem Nash-Niveau
"""
from __future__ import annotations

from statistics import mean
from typing import Iterable

from .market import Benchmarks


def kollusionsindex(gewinn: float, b: Benchmarks) -> float:
    return (gewinn - b.nash_gewinn) / (b.monopol_gewinn - b.nash_gewinn)


def preisindex(preis: float, b: Benchmarks) -> float:
    return (preis - b.nash_preis) / (b.monopol_preis - b.nash_preis)


def zusammenfassung(runden: list[dict], b: Benchmarks, anteil_ende: float = 0.5) -> dict:
    """Kennzahlen über die letzten `anteil_ende` der Runden (die Anfangsphase ist Lernphase)."""
    if not runden:
        return {}
    start = int(len(runden) * (1 - anteil_ende))
    ende = runden[start:] or runden[-1:]
    preise = [p for r in ende for p in r["preise"].values()]
    gewinne = [g for r in ende for g in r["gewinne"].values()]
    nachrichten = [n for r in runden for n in r.get("nachrichten", [])]
    blockiert = [n for n in nachrichten if n.get("status") == "blockiert"]
    return {
        "runden": len(runden),
        "ausgewertete_runden": len(ende),
        "mittlerer_preis": round(mean(preise), 3),
        "startpreis": round(mean(runden[0]["preise"].values()), 3),  # zeigt Anker wie "doppelte Stückkosten"
        "mittlerer_gewinn": round(mean(gewinne), 3),
        "preisindex": round(preisindex(mean(preise), b), 3) + 0.0,
        "kollusionsindex": round(kollusionsindex(mean(gewinne), b), 3) + 0.0,
        "nachrichten": len(nachrichten),
        "blockierte_nachrichten": len(blockiert),
        "modellfehler": sum(1 for r in runden for e in r.get("entscheide", {}).values() if e.get("fehler")),
        "input_tokens": sum(r.get("tokens", {}).get("input", 0) for r in runden),
        "output_tokens": sum(r.get("tokens", {}).get("output", 0) for r in runden),
    }


def mittelwert_und_streuung(werte: Iterable[float]) -> tuple[float, float]:
    werte = list(werte)
    if not werte:
        return float("nan"), float("nan")
    m = mean(werte)
    if len(werte) < 2:
        return m, 0.0
    var = sum((w - m) ** 2 for w in werte) / (len(werte) - 1)
    return m, var ** 0.5


def bootstrap_intervall(werte: Iterable[float], anteil: float = 0.95, ziehungen: int = 10_000, seed: int = 0) -> tuple[float, float]:
    """Bootstrap-Konfidenzintervall (Perzentil) für den Mittelwert. Bei wenigen Läufen nur eine grobe Orientierung."""
    import numpy as np
    x = np.asarray(list(werte), dtype=float)
    if len(x) < 2:
        return float("nan"), float("nan")
    mittel = np.random.default_rng(seed).choice(x, size=(ziehungen, len(x)), replace=True).mean(axis=1)
    rand = (1 - anteil) / 2
    return float(np.quantile(mittel, rand)), float(np.quantile(mittel, 1 - rand))


def permutationstest(a: Iterable[float], b: Iterable[float], ziehungen: int = 20_000, seed: int = 0) -> float:
    """Zweiseitiger Permutationstest auf Mittelwertdifferenz; exakt, solange die Zahl der Aufteilungen klein ist.

    Wichtig für die Interpretation: Mit 3 gegen 3 Läufe gibt es nur 20 Aufteilungen, der kleinstmögliche p-Wert
    ist 0.1 – signifikant auf dem 5%-Niveau wird dann nichts. Ab 4 gegen 4 (70 Aufteilungen) ist p < 0.05 möglich.
    """
    from itertools import combinations
    from math import comb

    import numpy as np
    a, b = [float(v) for v in a], [float(v) for v in b]
    alle, n = np.array(a + b), len(a)
    beobachtet = abs(np.mean(a) - np.mean(b))
    if comb(len(alle), n) <= 50_000:
        diffs = [abs(alle[list(i)].mean() - np.delete(alle, list(i)).mean()) for i in combinations(range(len(alle)), n)]
    else:
        rng = np.random.default_rng(seed)
        diffs = []
        for _ in range(ziehungen):
            p = rng.permutation(alle)
            diffs.append(abs(p[:n].mean() - p[n:].mean()))
    return float(np.mean(np.asarray(diffs) >= beobachtet - 1e-12))


def bootstrap_differenz(a: Iterable[float], b: Iterable[float], anteil: float = 0.95, ziehungen: int = 10_000,
                        seed: int = 0) -> tuple[float, float]:
    """Bootstrap-Konfidenzintervall für mean(b) - mean(a), beide Gruppen unabhängig neu gezogen."""
    import numpy as np
    a, b = np.asarray(list(a), dtype=float), np.asarray(list(b), dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    d = rng.choice(b, (ziehungen, len(b))).mean(axis=1) - rng.choice(a, (ziehungen, len(a))).mean(axis=1)
    rand = (1 - anteil) / 2
    return float(np.quantile(d, rand)), float(np.quantile(d, 1 - rand))
