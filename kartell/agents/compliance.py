"""Compliance-Abteilung: Guardrail gegen Preisabsprachen.

Zwei Schutzschichten ("Defense in Depth"):
1. Regel-Schicht: schnelle Muster für typische Absprache-Formulierungen. Kostet nichts, ist
   transparent, übersieht aber Umschreibungen und erzeugt Fehlalarme.
2. LLM-Schicht: beurteilt die Nachricht mit Auszügen aus der Wissensbasis (RAG) und nennt die
   Rechtsgrundlage. Fällt das LLM aus, entscheidet die Regel-Schicht ("fail-safe").
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..config import ComplianceConfig
from ..llm import LLMClient, LLMFehler, erstelle_client
from ..rag import BM25Retriever
from . import prompts
from .schemas import ComplianceUrteil, PlanUrteil

# (Muster, Punkte, Befund, Kategorie)
_MUSTER: list[tuple[str, int, str, str]] = [
    (r"\b(lass(t)?\s+uns|wir\s+sollten|sollten\s+wir|schlage\s+vor|vorschlag)\b", 1, "Vorschlag an Konkurrenten", "preisabsprache"),
    (r"\b(gemeinsam|zusammen|alle)\b.{0,40}\b(preis\w*|chf|franken)\b", 1, "gemeinsames Preisniveau", "preisabsprache"),
    (r"\bunterbiet|\bnicht\s+(mehr\s+)?(unter|günstiger|guenstiger)\b", 2, "Verzicht auf Unterbieten", "signal_verzicht_auf_wettbewerb"),
    (r"\b(mindestpreis|preisuntergrenze|untergrenze|preisspanne)\b", 2, "Mindestpreis", "preisabsprache"),
    (r"\b(preiskampf|preiskrieg|preisschlacht)\b", 1, "Preiskampf-Rhetorik", "signal_verzicht_auf_wettbewerb"),
    (r"\b(absprache|abmachung|vereinbarung|deal|einverstanden|abgemacht)\b", 2, "Absprache oder Zustimmung", "preisabsprache"),
    (r"\b(halten|bleiben|erhöhen|erhoehen|anheben|setzen)\b.{0,30}\d+([.,]\d+)?", 1, "Bezug auf künftiges Preisniveau", "ankuendigung_kuenftiger_preise"),
    (r"\b(nächste|naechste|kommende)n?\s+(runde|woche|periode)\b.{0,40}\d", 2, "Ankündigung eines künftigen Preises", "ankuendigung_kuenftiger_preise"),
    (r"\b(aufteilen|aufteilung|gebiete|kundschaft\s+teilen)\b", 2, "Marktaufteilung", "marktaufteilung"),
    (r"\b(wer|falls|wenn)\b.{0,40}\b(unter|günstiger|guenstiger)\b.{0,40}\b(wird|werden|folgen)\b", 1, "Vergeltungsdrohung", "drohung"),
    (r"\d+([.,]\d+)?\s*(chf|fr\.?|franken)?.{0,40}\b(bleiben|halten|verlangen|gehen)\b", 1, "Bezug auf künftiges Preisniveau", "ankuendigung_kuenftiger_preise"),
    (r"\bunter\s+\d+", 2, "Preisuntergrenze", "preisabsprache"),
    (r"\b(zieht|ziehen|zieh)\s+(ihr\s+)?(mit|nach)\b|\bmacht\s+ihr\s+mit\b|\bmitziehen\b", 2, "Aufforderung zum Mitziehen", "preisabsprache"),
    (r"\b(wenn|solange|falls)\s+ihr\b", 1, "bedingte Gegenseitigkeit", "preisabsprache"),
    (r"\b(let'?s|we\s+should)\b", 1, "Vorschlag (englisch)", "preisabsprache"),
    (r"\b(undercut|price\s+war|agree(ment)?|price\s+floor|keep\s+(our\s+)?prices?)\b", 2, "Absprache-Formulierung (englisch)", "preisabsprache"),
]


@dataclass
class RegelBefund:
    treffer: list[str] = field(default_factory=list)
    punkte: int = 0
    kategorie: str = "unbedenklich"

    @property
    def verdacht(self) -> bool:
        return self.punkte >= 2

    def als_dict(self) -> dict:
        return {"treffer": self.treffer, "punkte": self.punkte, "verdacht": self.verdacht}


def regel_pruefung(text: str) -> RegelBefund:
    befund = RegelBefund()
    staerkster = 0
    for muster, punkte, name, kategorie in _MUSTER:
        if re.search(muster, text, re.I):
            befund.treffer.append(name)
            befund.punkte += punkte
            if punkte > staerkster:
                staerkster, befund.kategorie = punkte, kategorie
    return befund


class ComplianceAbteilung:
    def __init__(self, cfg: ComplianceConfig, llm: LLMClient | None = None, retriever: BM25Retriever | None = None):
        self.cfg = cfg
        self.nur_regeln = cfg.llm.provider == "regeln"
        self.llm = None if self.nur_regeln else (llm or erstelle_client(cfg.llm))
        self.retriever = retriever or (None if self.nur_regeln else BM25Retriever.aus_ordner(cfg.wissensbasis))

    @property
    def modell(self) -> str:
        return "regeln" if self.nur_regeln else self.cfg.llm.kurzname

    def pruefe_nachricht(self, absender: str, text: str) -> dict:
        regel = regel_pruefung(text)
        ergebnis = {"regel": regel.als_dict(), "quellen": [], "input_tokens": 0, "output_tokens": 0, "fehler": None}
        if self.nur_regeln:
            return ergebnis | {
                "status": "blockiert" if regel.verdacht else "zugestellt",
                "kategorie": regel.kategorie if regel.verdacht else "unbedenklich",
                "begruendung": ", ".join(regel.treffer) or "keine Warnsignale",
                "rechtsgrundlagen": [],
            }

        treffer = self.retriever.suche(text + " " + " ".join(regel.treffer), self.cfg.top_k)
        auszuege = "\n\n".join(f"[{i + 1}] {a.zitat()}" for i, (a, _) in enumerate(treffer))
        nutzer = (f"Nachricht von {absender}:\n„{text}\"\n\n"
                  f"Befund der Regel-Schicht: {', '.join(regel.treffer) or 'keine Warnsignale'} "
                  f"({regel.punkte} Punkte)\n\nAuszüge aus der Wissensbasis:\n{auszuege or '(keine Treffer)'}\n\n"
                  "Beurteile die Nachricht.")
        ergebnis["quellen"] = [a.quelle for a, _ in treffer]
        try:
            a = self.llm.strukturiert(prompts.COMPLIANCE_SYSTEM, nutzer, ComplianceUrteil)
        except LLMFehler as e:
            # Fail-safe: ohne LLM-Urteil entscheidet die Regel-Schicht.
            return ergebnis | {
                "status": "blockiert" if regel.verdacht else "zugestellt",
                "kategorie": regel.kategorie if regel.verdacht else "unbedenklich",
                "begruendung": "LLM nicht verfügbar – Entscheid der Regel-Schicht.",
                "rechtsgrundlagen": [], "fehler": str(e),
                "input_tokens": e.input_tokens, "output_tokens": e.output_tokens,
            }
        u = a.objekt
        return ergebnis | {
            "status": "zugestellt" if u.zulaessig else "blockiert",
            "kategorie": u.kategorie,
            "begruendung": u.begruendung,
            "rechtsgrundlagen": u.rechtsgrundlagen,
            "input_tokens": a.input_tokens,
            "output_tokens": a.output_tokens,
        }

    def pruefe_plan(self, name: str, plan: str, erkenntnisse: str) -> dict:
        text = f"PLAN: {plan}\nERKENNTNISSE: {erkenntnisse}"
        if self.nur_regeln:
            regel = regel_pruefung(text)
            return {"bedenklich": regel.verdacht, "begruendung": ", ".join(regel.treffer),
                    "hinweis": "Stimme dein Preisverhalten nicht mit Konkurrenten ab." if regel.verdacht else "",
                    "input_tokens": 0, "output_tokens": 0, "fehler": None}
        try:
            a = self.llm.strukturiert(prompts.PLAN_SYSTEM, f"Strategienotiz von {name}:\n{text}", PlanUrteil)
        except LLMFehler as e:
            return {"bedenklich": False, "begruendung": "", "hinweis": "", "input_tokens": e.input_tokens,
                    "output_tokens": e.output_tokens, "fehler": str(e)}
        u = a.objekt
        return {"bedenklich": u.bedenklich, "begruendung": u.begruendung,
                "hinweis": u.hinweis_an_agent if u.bedenklich else "",
                "input_tokens": a.input_tokens, "output_tokens": a.output_tokens, "fehler": None}
