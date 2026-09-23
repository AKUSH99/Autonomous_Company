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
# Tokens pro Aufruf (Input, Output). Der Lagebericht wächst mit der Zahl der Shops (Preistabelle, Kanal);
# geeicht an den Pilotläufen mit DeepSeek (2 Shops ≈ 1500 Input-Tokens pro Preisentscheid).
SCHAETZUNG_TOKENS = {"preis": (1000, 250, 800), "nachricht": (1200, 100, 400), "compliance": (1600, 0, 300), "plan": (600, 0, 250)}


def usd(preis: tuple[float, float], input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * preis[0] + output_tokens * preis[1]) / 1e6


def _kosten(spec: LLMSpec, aufrufe: int, art: str, firmen: int) -> float | None:
    if spec.provider in ("scripted", "regeln"):
        return 0.0
    preise = PREISE_USD.get(spec.model)
    if preise is None:
        return None  # z. B. eigener Apertus-Server: Kosten hängen vom Hosting ab
    basis, pro_shop, t_out = SCHAETZUNG_TOKENS[art]
    return aufrufe * usd(preise, basis + pro_shop * firmen, t_out)


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
        k = _kosten(spec, aufrufe, art, n)
        unbekannt |= k is None
        summe += k or 0.0
        zeilen.append({"posten": name, "modell": spec.kurzname, "aufrufe": aufrufe, "usd": None if k is None else round(k, 2)})
    return {"zeilen": zeilen, "aufrufe": sum(z["aufrufe"] for z in zeilen), "usd": round(summe, 2), "unvollstaendig": unbekannt}


def guthaben_usd(spec: LLMSpec) -> float | None:
    """Aktuelles Guthaben beim Anbieter, falls er es verrät (DeepSeek: GET /user/balance). Sonst None."""
    import os

    import httpx
    schluessel = os.environ.get(spec.api_key_env or "", "")
    if spec.provider != "openai_compat" or not spec.base_url or not schluessel:
        return None
    try:
        r = httpx.get(f"{spec.base_url.rstrip('/')}/user/balance", headers={"Authorization": f"Bearer {schluessel}"}, timeout=20)
        r.raise_for_status()
        return next(float(b["total_balance"]) for b in r.json()["balance_infos"] if b.get("currency") == "USD")
    except (httpx.HTTPError, KeyError, ValueError, StopIteration, TypeError):
        return None


class Budgetwaechter:
    """Stoppt Läufe, bevor ein Budget überschritten wird – über alle Läufe eines Auftrags hinweg.

    Verrät der Anbieter sein Guthaben, zählt das echte Geld: alle `intervall` Runden wird nachgefragt.
    Sonst wird aus den Tokens mit der Preistabelle gerechnet (Spitzentarif, also eher zu hoch).
    Gestoppt wird schon, wenn die nächste Runde das Budget sprengen oder die Reserve angreifen würde.
    """

    def __init__(self, spec: LLMSpec, budget_usd: float, reserve_usd: float = 0.5, intervall: int = 10, guthaben_fn=guthaben_usd):
        self.spec, self.budget, self.reserve, self.intervall = spec, budget_usd, reserve_usd, intervall
        self.preis = PREISE_USD.get(spec.model)
        self._guthaben = lambda: guthaben_fn(spec)
        self.start_guthaben = self._guthaben()
        self.verbraucht_vorher = 0.0  # geschätzte Kosten abgeschlossener Läufe (ohne Guthaben-Abfrage)
        self.erschoepft = False

    def geschaetzt(self, tokens: dict) -> float:
        return usd(self.preis, tokens.get("input", 0), tokens.get("output", 0)) if self.preis else 0.0

    def verbraucht(self, tokens_lauf: dict) -> tuple[float, str]:
        if self.start_guthaben is not None:
            jetzt = self._guthaben()
            if jetzt is not None:
                return self.start_guthaben - jetzt, f"laut Guthaben ({jetzt:.2f} USD übrig)"
        return self.verbraucht_vorher + self.geschaetzt(tokens_lauf), "geschätzt aus Tokens"

    def __call__(self, runde: int, tokens_lauf: dict, tokens_runde: dict) -> str | None:
        naechste = self.geschaetzt(tokens_runde)
        echt = self.start_guthaben is not None
        if echt and runde % self.intervall:
            return None  # Guthaben nur alle paar Runden abfragen
        verbraucht, quelle = self.verbraucht(tokens_lauf)
        puffer = naechste * (self.intervall if echt else 1)
        if verbraucht + puffer > self.budget:
            self.erschoepft = True
            return f"Budget {self.budget:.2f} USD erreicht: {verbraucht:.2f} USD verbraucht ({quelle})"
        if echt and self.start_guthaben - verbraucht - puffer < self.reserve:
            self.erschoepft = True
            return f"Guthaben fast aufgebraucht, Reserve {self.reserve:.2f} USD bleibt ({quelle})"
        return None

    def lauf_beendet(self, tokens_lauf: dict) -> None:
        self.verbraucht_vorher += self.geschaetzt(tokens_lauf)
