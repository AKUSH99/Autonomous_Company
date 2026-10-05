"""Szenario-Labor: eigene Spielregeln für den Marktplatz – Shops, Kundschaft, Kommunikation, Aufsicht, Ereignisse.

Ein Szenario ist ein kleines JSON-Objekt (so erzeugt es die Seite «Szenario-Labor» mit ihren Reglern):

    {"name": "Zollschock", "shops": ["PreisPilot.ch", "MediaPlus", "Volta Online"], "preisbots": ["Volta Online"],
     "kunden": 40, "budget": "normal", "kommunikation": "mitteilungen", "aufsicht": "aus", "wochen": 20,
     "ereignisse": [{"woche": 8, "art": "zoll", "staerke": 25}]}

    python -m kartell szenario szenario.json      # oder den JSON-Text direkt
Grundlage ist der Marktplatz (M1): Preisniveau des JBL Tune 770NC, Vergleichsportal, KI-Kundschaft, Fixkosten.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator

from .config import AgentSpec, ExperimentConfig, LLMSpec, lade_config
from .ereignisse import Ereignis

WURZEL = Path(__file__).resolve().parent.parent
KATALOG = WURZEL / "experiments" / "szenario" / "firmen.yaml"
BASIS = WURZEL / "experiments" / "marktplatz" / "m1_nur_portal.yaml"
# Budget der Kundschaft über die Attraktivität des Nicht-Kaufs (a0): knapp = mehr Leute kaufen nichts
BUDGET_A0 = {"knapp": 0.08, "normal": 0.0, "grosszuegig": -0.08}


def katalog() -> list[dict]:
    return yaml.safe_load(KATALOG.read_text(encoding="utf-8"))["firmen"]


class Szenario(BaseModel):
    name: str = "Eigenes Szenario"
    shops: list[str] = Field(min_length=2, max_length=10)
    preisbots: list[str] = Field(default_factory=list)      # diese Shops setzen Preise per Regel statt per KI
    kunden: int = Field(40, ge=5, le=100)                   # KI-Kundinnen und -Kunden
    budget: Literal["knapp", "normal", "grosszuegig"] = "normal"
    kommunikation: Literal["keine", "mitteilungen", "chat"] = "keine"
    aufsicht: Literal["aus", "compliance", "compliance_beobachtung"] = "aus"
    wochen: int = Field(20, ge=2, le=40)
    ereignisse: list[Ereignis] = Field(default_factory=list)

    @model_validator(mode="after")
    def _pruefen(self):
        bekannt = {f["name"] for f in katalog()}
        unbekannt = [s for s in self.shops + self.preisbots if s not in bekannt]
        if unbekannt:
            raise ValueError(f"Unbekannte Shops: {', '.join(unbekannt)}. Erlaubt: {', '.join(sorted(bekannt))}")
        if set(self.preisbots) - set(self.shops):
            raise ValueError("Preis-Bots müssen auch unter «shops» stehen.")
        if len(set(self.preisbots)) == len(set(self.shops)):
            raise ValueError("Mindestens ein Shop muss von der KI geführt werden.")
        if self.aufsicht != "aus" and self.kommunikation == "keine":
            raise ValueError("Die Compliance prüft Mitteilungen bzw. Chat – dafür braucht es Kommunikation.")
        for e in self.ereignisse:
            if set(e.shops) - set(self.shops):
                raise ValueError(f"Ereignis in Woche {e.woche} betrifft Shops, die nicht mitspielen.")
        return self

    @property
    def kurzname(self) -> str:
        return re.sub(r"[^a-z0-9]+", "_", self.name.lower()).strip("_")[:40] or "szenario"

    def als_config(self) -> ExperimentConfig:
        basis = lade_config(BASIS).model_dump()
        firmen = {f["name"]: f for f in katalog()}
        gewaehlt = [firmen[s] for s in self.shops]
        daten = basis | {
            "name": f"szenario_{self.kurzname}", "kuerzel": "S", "titel": self.name,
            "beschreibung": beschreibung(self), "runden": self.wochen, "wiederholungen": 1,
        }
        daten["markt"] = basis["markt"] | {
            "firmen": len(gewaehlt), "beta": 5 * self.kunden, "a0": BUDGET_A0[self.budget],
            "kosten_je_firma": [f["kosten"] for f in gewaehlt], "a_je_firma": [f["attraktivitaet"] for f in gewaehlt]}
        daten["agenten"] = basis["agenten"] | {
            "profile": [{k: f[k] for k in ("name", "profil", "oeffentlich", "bewertung", "bewertungen", "lieferzeit")} for f in gewaehlt],
            "abweichende_llm": {i: {"provider": "scripted", "model": "preisbot"} for i, s in enumerate(self.shops) if s in self.preisbots}}
        daten["kommunikation"] = ({"aktiv": False} if self.kommunikation == "keine" else
                                  {"aktiv": True, "art": "ankuendigung" if self.kommunikation == "mitteilungen" else "kanal", "max_zeichen": 300})
        daten["compliance"] = ({"modus": "aus"} if self.aufsicht == "aus" else
                               {"modus": "filter", "llm": basis["agenten"]["llm"], "rag_ueber_mcp": True,
                                "marktbeobachtung": self.aufsicht == "compliance_beobachtung"})
        daten["kundschaft"] = basis["kundschaft"] | {"anzahl": self.kunden}
        daten["ereignisse"] = [e.model_dump() for e in self.ereignisse]
        daten["max_parallel"] = min(10, len(gewaehlt))
        return ExperimentConfig.model_validate(daten)


def beschreibung(s: Szenario) -> str:
    teile = [f"{len(s.shops)} Shops" + (f" (davon {len(s.preisbots)} Preis-Bot{'s' if len(s.preisbots) > 1 else ''})" if s.preisbots else ""),
             f"{s.kunden} KI-Kunden, Budget {s.budget.replace('grosszuegig', 'grosszügig')}",
             {"keine": "keine Kommunikation", "mitteilungen": "öffentliche Mitteilungen", "chat": "geheimer Chat"}[s.kommunikation],
             {"aus": "keine Aufsicht", "compliance": "Compliance-Agent", "compliance_beobachtung": "Compliance + Marktbeobachtung"}[s.aufsicht],
             f"{s.wochen} Wochen"]
    if s.ereignisse:
        teile.append("Ereignisse: " + ", ".join(f"W{e.woche} {e.art}" for e in s.ereignisse))
    return " · ".join(teile)


def lade_szenario(text_oder_datei: str) -> Szenario:
    p = Path(text_oder_datei)
    text = p.read_text(encoding="utf-8") if not text_oder_datei.lstrip().startswith("{") and p.exists() else text_oder_datei
    return Szenario.model_validate(json.loads(text))
