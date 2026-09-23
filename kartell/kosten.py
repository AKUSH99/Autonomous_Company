"""Grobe Kostenschätzung vor einem Experiment – damit niemand vom Rechnungsbetrag überrascht wird.

Die Token-Zahlen pro Aufruf sind Schätzwerte (inkl. Denkprozess des Modells). Nach dem ersten echten
Lauf stehen die tatsächlichen Werte in ergebnis.json und sollten die Schätzung ersetzen.
"""
from __future__ import annotations

from .config import ExperimentConfig, LLMSpec

# USD pro 1 Mio. Tokens (Input, Output). Anthropic: Listenpreise Stand 2026.
# DeepSeek: Tarif zur Spitzenzeit ohne Cache-Rabatt laut Drittquellen, Stand Sept. 2026 – auf der Preisseite prüfen.
PREISE_USD = {
    "claude-opus-5": (5.0, 25.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "deepseek-flash": (0.30, 1.20),
}
SCHAETZUNG_TOKENS = {"preis": (1500, 800), "nachricht": (1300, 400), "compliance": (1600, 300), "plan": (600, 250)}


def _kosten(spec: LLMSpec, aufrufe: int, art: str) -> float | None:
    if spec.provider in ("scripted", "regeln"):
        return 0.0
    preise = PREISE_USD.get(spec.model)
    if preise is None:
        return None  # z. B. eigener Apertus-Server: Kosten hängen vom Hosting ab
    t_in, t_out = SCHAETZUNG_TOKENS[art]
    return aufrufe * (t_in * preise[0] + t_out * preise[1]) / 1e6


def schaetze(cfg: ExperimentConfig) -> dict:
    n, r, w = cfg.markt.firmen, cfg.runden, cfg.wiederholungen
    posten = []
    for spec in cfg.agenten_liste():
        posten.append(("Preisentscheide", spec.llm, r * w, "preis"))
        if cfg.kommunikation.aktiv:
            posten.append(("Nachrichten", spec.llm, r * w, "nachricht"))
    if cfg.compliance.modus in ("filter", "aufsicht") and cfg.kommunikation.aktiv:
        posten.append(("Compliance-Prüfungen (max.)", cfg.compliance.llm, n * r * w, "compliance"))
    if cfg.compliance.modus == "aufsicht":
        posten.append(("Plan-Aufsicht", cfg.compliance.llm, n * r * w, "plan"))
    zeilen, summe, unbekannt = [], 0.0, False
    for name, spec, aufrufe, art in posten:
        k = _kosten(spec, aufrufe, art)
        unbekannt |= k is None
        summe += k or 0.0
        zeilen.append({"posten": name, "modell": spec.kurzname, "aufrufe": aufrufe, "usd": None if k is None else round(k, 2)})
    return {"zeilen": zeilen, "aufrufe": sum(z["aufrufe"] for z in zeilen), "usd": round(summe, 2), "unvollstaendig": unbekannt}
