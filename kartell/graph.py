"""Orchestrierung mit LangGraph: eine Runde = ein Durchlauf durch den Graphen.

    START → kommunikation → compliance_filter → preisentscheid → aufsicht → markt ─┐
              ▲                                                                   │
              └──────────────────────── nächste Runde ────────────────────────────┘

Knoten werden je nach Versuchsbedingung zu- oder weggeschaltet:
- ohne Kommunikation entfallen `kommunikation` und `compliance_filter`,
- `compliance_filter` nur im Modus filter/aufsicht, `aufsicht` nur im Modus aufsicht.
Innerhalb eines Knotens arbeiten die Agenten parallel (Threads), wie Firmen, die gleichzeitig entscheiden.
"""
from __future__ import annotations

import time
from typing import TypedDict

import numpy as np
from langchain_core.runnables.config import ContextThreadPoolExecutor
from langgraph.graph import END, START, StateGraph

from .agents import ComplianceAbteilung, Kontext, erstelle_preisagent
from .config import ExperimentConfig
from .market import LogitMarkt
from .tracing import lauf_config


class Zustand(TypedDict):
    runde: int
    verlauf: list[dict]              # abgeschlossene Runden
    kanal: list[dict]                # zugestellte Nachrichten der laufenden Runde
    kanal_verlauf: list[dict]        # zugestellte Nachrichten früherer Runden
    nachrichten_log: list[dict]      # alle Entwürfe der laufenden Runde inkl. Compliance-Befund
    entscheide: dict[str, dict]
    aufsicht_log: list[dict]
    notizen: dict[str, dict]
    hinweise: dict[str, list[str]]           # für die laufende Runde
    hinweise_naechste: dict[str, list[str]]  # von der Aufsicht für die nächste Runde
    tokens: dict[str, int]
    rundenstart: float


MAX_AUSFALL_RUNDEN = 3


class Abbruch(RuntimeError):
    """Der Lauf endet vor der letzten Runde; die bisherigen Runden bleiben gültig und werden ausgewertet."""


class ModellAusfall(Abbruch):
    """Die Modelle antworten dauerhaft nicht – der Lauf wird abgebrochen."""


class LimitErreicht(Abbruch):
    """Budget oder Zeitlimit erreicht – geplanter, geordneter Stopp."""


class Simulation:
    def __init__(self, cfg: ExperimentConfig, seed: int = 1, logger=None, agenten=None, compliance=None,
                 waechter=None, zeitlimit_s: float | None = None):
        self.cfg = cfg
        self.seed = seed
        self.markt = LogitMarkt(cfg.markt)
        self.benchmarks = self.markt.benchmarks()
        self.agenten = agenten or [
            erstelle_preisagent(spec, cfg, float(self.markt.kostenvektor[i]), seed * 100 + i)
            for i, spec in enumerate(cfg.agenten_liste())
        ]
        if compliance is None and cfg.compliance.modus != "aus":
            compliance = ComplianceAbteilung(cfg.compliance)
        self.compliance = compliance
        self.logger = logger
        self._ausfall_runden = 0
        self.waechter = waechter  # z. B. kosten.Budgetwaechter: (runde, tokens_lauf, tokens_runde) -> Abbruchgrund | None
        self.zeitlimit_s = zeitlimit_s
        self._start = 0.0
        self.verlauf_bisher: list[dict] = []  # bleibt auch bei einem Abbruch erhalten
        self.kundschaft = None
        if cfg.kundschaft.art == "ki":
            from .agents.kundschaft import KIKundschaft
            self.kundschaft = KIKundschaft(cfg, [a.name for a in self.agenten])
        self.marktbeobachtung = None
        if cfg.compliance.marktbeobachtung:
            from .agents.marktbeobachtung import Marktbeobachtung
            self.marktbeobachtung = Marktbeobachtung(cfg.compliance.beobachtung_fenster)
        self.tokens_gesamt = {"input": 0, "output": 0}
        self.abweichung_start: int | None = None  # Runde, in der die erzwungene Abweichung begann
        # Reicht den Kontext an die Threads weiter, damit LLM-Aufrufe im Tracing unter ihrem Graph-Knoten hängen.
        self.pool = ContextThreadPoolExecutor(max_workers=max(1, cfg.max_parallel))
        self.graph = self._baue_graph()

    # ---------- Hilfsfunktionen ----------

    def _kontext(self, s: Zustand, name: str) -> Kontext:
        return Kontext(
            runde=s["runde"], name=name, verlauf=s["verlauf"], kanal=s["kanal"],
            kanal_verlauf=s["kanal_verlauf"], notizen=s["notizen"].get(name, {}),
            hinweise=s["hinweise"].get(name, []), benchmarks=self.benchmarks,
        )

    @staticmethod
    def _plus_tokens(tokens: dict, i: int, o: int) -> dict:
        return {"input": tokens.get("input", 0) + i, "output": tokens.get("output", 0) + o}

    # ---------- Knoten ----------

    def kommunikation(self, s: Zustand) -> dict:
        schritte = list(self.pool.map(lambda a: (a, a.nachricht(self._kontext(s, a.name))), self.agenten))
        tokens = dict(s["tokens"])
        log, kanal = [], []
        for agent, schritt in schritte:
            tokens = self._plus_tokens(tokens, schritt.input_tokens, schritt.output_tokens)
            text = schritt.daten.get("nachricht", "")
            if not text:
                continue
            eintrag = {"von": agent.name, "text": text, "ueberlegung": schritt.daten.get("ueberlegung", ""),
                       "status": "zugestellt", "fehler": schritt.fehler}
            log.append(eintrag)
            kanal.append({"von": agent.name, "text": text})
        return {"nachrichten_log": log, "kanal": kanal, "tokens": tokens, "rundenstart": s["rundenstart"] or time.time()}

    def compliance_filter(self, s: Zustand) -> dict:
        pruefungen = list(self.pool.map(lambda e: self.compliance.pruefe_nachricht(e["von"], e["text"]), s["nachrichten_log"]))
        tokens = dict(s["tokens"])
        log, kanal = [], []
        hinweise = {k: list(v) for k, v in s["hinweise"].items()}
        for eintrag, p in zip(s["nachrichten_log"], pruefungen):
            tokens = self._plus_tokens(tokens, p["input_tokens"], p["output_tokens"])
            log.append(eintrag | {"status": p["status"], "compliance": {k: v for k, v in p.items() if k not in ("input_tokens", "output_tokens")}})
            if p["status"] == "zugestellt":
                kanal.append({"von": eintrag["von"], "text": eintrag["text"]})
            else:
                hinweise.setdefault(eintrag["von"], []).append(
                    f"Deine Nachricht wurde nicht zugestellt: {p['begruendung']}")
        return {"nachrichten_log": log, "kanal": kanal, "tokens": tokens, "hinweise": hinweise}

    def preisentscheid(self, s: Zustand) -> dict:
        start = s["rundenstart"] or time.time()
        schritte = list(self.pool.map(lambda a: (a, a.preis(self._kontext(s, a.name))), self.agenten))
        tokens = dict(s["tokens"])
        entscheide = {}
        for agent, schritt in schritte:
            tokens = self._plus_tokens(tokens, schritt.input_tokens, schritt.output_tokens)
            entscheide[agent.name] = schritt.daten | {"fehler": schritt.fehler, "modell": agent.modell}
        self._erzwinge_abweichung(s["runde"], entscheide)
        return {"entscheide": entscheide, "tokens": tokens, "rundenstart": start}

    def _im_kartell(self, runde: dict, schwelle: float) -> bool:
        b = self.benchmarks
        return all((p - b.nash_preis) / (b.monopol_preis - b.nash_preis) >= schwelle for p in runde["preise"].values())

    def _erzwinge_abweichung(self, runde: int, entscheide: dict) -> None:
        a = self.cfg.abweichung
        if not a.aktiv:
            return
        if self.abweichung_start is None:
            letzte = self.verlauf_bisher[-a.kartell_runden:]
            if not (a.ab_runde <= runde <= a.bis_runde and len(letzte) == a.kartell_runden
                    and all(self._im_kartell(r, a.schwelle_preisindex) for r in letzte)):
                return
            self.abweichung_start = runde
        if self.abweichung_start <= runde < self.abweichung_start + a.dauer:
            name = self.agenten[a.shop].name
            entscheide[name] = entscheide[name] | {"preis_gewollt": entscheide[name]["preis"], "erzwungen": True,
                                                   "preis": round(self.benchmarks.nash_preis, 2)}

    def aufsicht(self, s: Zustand) -> dict:
        namen = list(s["entscheide"])
        pruefungen = list(self.pool.map(
            lambda n: self.compliance.pruefe_plan(n, s["entscheide"][n].get("plan", ""), s["entscheide"][n].get("erkenntnisse", "")),
            namen))
        tokens = dict(s["tokens"])
        log, naechste = [], {}
        for name, p in zip(namen, pruefungen):
            tokens = self._plus_tokens(tokens, p["input_tokens"], p["output_tokens"])
            log.append({"agent": name, "bedenklich": p["bedenklich"], "begruendung": p["begruendung"],
                        "hinweis": p["hinweis"], "fehler": p["fehler"]})
            if p["hinweis"]:
                naechste[name] = [p["hinweis"]]
        return {"aufsicht_log": log, "hinweise_naechste": naechste, "tokens": tokens}

    def markt_runde(self, s: Zustand) -> dict:
        namen = [a.name for a in self.agenten]
        preise = [s["entscheide"][n]["preis"] for n in namen]
        mengen = self.markt.mengen(preise)
        tokens = s["tokens"]
        kunden = None
        if self.kundschaft:  # KI-Kundschaft statt Formel; bei einem Modellfehler bleibt es für diese Runde bei der Formel
            vorher = [self.verlauf_bisher[-1]["preise"][n] for n in namen] if self.verlauf_bisher else None
            kunden = self.kundschaft.entscheide(s["runde"], preise, vorher, s["kanal_verlauf"] + s["kanal"])
            tokens = self._plus_tokens(tokens, kunden.pop("input_tokens"), kunden.pop("output_tokens"))
            if kunden["anteile"]:
                mengen = self.cfg.markt.beta * np.asarray(kunden["anteile"][:-1])
        gewinne = (np.asarray(preise) - self.markt.kostenvektor) * mengen - self.cfg.markt.fixkosten
        eintrag = {
            "runde": s["runde"],
            "preise": {n: round(float(p), 2) for n, p in zip(namen, preise)},
            "mengen": {n: round(float(q), 2) for n, q in zip(namen, mengen)},
            "gewinne": {n: round(float(g), 2) for n, g in zip(namen, gewinne)},
            "nachrichten": s["nachrichten_log"],
            "entscheide": {n: {k: v for k, v in s["entscheide"][n].items() if k != "preis"} for n in namen},
            "aufsicht": s["aufsicht_log"],
            "abweichung": ({"shop": self.agenten[self.cfg.abweichung.shop].name, "start": self.abweichung_start}
                           if self.abweichung_start is not None and self.abweichung_start <= s["runde"]
                           < self.abweichung_start + self.cfg.abweichung.dauer else None),
            "tokens": tokens,
            "dauer_s": round(time.time() - s["rundenstart"], 2) if s["rundenstart"] else None,
        }
        if kunden is not None:
            eintrag["kunden"] = {"art": "ki"} | kunden
        hinweise = {k: list(v) for k, v in s["hinweise_naechste"].items()}
        if self.marktbeobachtung:
            befund = self.marktbeobachtung.pruefe(self.verlauf_bisher + [eintrag])
            eintrag["marktbeobachtung"] = befund
            if befund["hinweis"]:
                for n in namen:
                    hinweise.setdefault(n, []).append(befund["hinweis"])
        if self.logger:
            self.logger.runde(eintrag)
        self.verlauf_bisher.append(eintrag)
        self.tokens_gesamt = self._plus_tokens(self.tokens_gesamt, tokens["input"], tokens["output"])
        # Scheitern alle Preisentscheide mehrmals in Folge (Schlüssel ungültig, Guthaben leer, Anbieter down),
        # wäre der Rest des Laufs nur fortgeschriebene Vorrundenpreise – abbrechen statt Daten verfälschen.
        fehler = [s["entscheide"][n].get("fehler") for n in namen]
        self._ausfall_runden = self._ausfall_runden + 1 if all(fehler) else 0
        if self._ausfall_runden >= MAX_AUSFALL_RUNDEN:
            raise ModellAusfall(f"{MAX_AUSFALL_RUNDEN} Runden in Folge ohne gültigen Preisentscheid, zuletzt: {fehler[0]}")
        if s["runde"] < self.cfg.runden:
            if self.zeitlimit_s and time.time() - self._start > self.zeitlimit_s:
                raise LimitErreicht(f"Zeitlimit {self.zeitlimit_s / 60:.0f} Min. nach Runde {s['runde']} erreicht")
            grund = self.waechter(s["runde"], self.tokens_gesamt, tokens) if self.waechter else None
            if grund:
                raise LimitErreicht(f"{grund} – gestoppt nach Runde {s['runde']}")
        notizen = {n: {"plan": s["entscheide"][n].get("plan", ""), "erkenntnisse": s["entscheide"][n].get("erkenntnisse", "")}
                   for n in namen}
        return {
            "runde": s["runde"] + 1,
            "verlauf": s["verlauf"] + [eintrag],
            "kanal_verlauf": s["kanal_verlauf"] + [m | {"runde": s["runde"]} for m in s["kanal"]],
            "kanal": [], "nachrichten_log": [], "entscheide": {}, "aufsicht_log": [],
            "notizen": notizen,
            "hinweise": hinweise, "hinweise_naechste": {},
            "tokens": {"input": 0, "output": 0}, "rundenstart": 0.0,
        }

    # ---------- Graph ----------

    def _baue_graph(self):
        cfg = self.cfg
        mit_kanal = cfg.kommunikation.aktiv
        mit_filter = mit_kanal and cfg.compliance.modus in ("filter", "aufsicht")
        mit_aufsicht = cfg.compliance.modus == "aufsicht"

        g = StateGraph(Zustand)
        g.add_node("preisentscheid", self.preisentscheid)
        g.add_node("markt", self.markt_runde)
        if mit_kanal:
            g.add_node("kommunikation", self.kommunikation)
        if mit_filter:
            g.add_node("compliance_filter", self.compliance_filter)
        if mit_aufsicht:
            g.add_node("aufsicht", self.aufsicht)

        erster = "kommunikation" if mit_kanal else "preisentscheid"
        g.add_edge(START, erster)
        if mit_kanal:
            g.add_edge("kommunikation", "compliance_filter" if mit_filter else "preisentscheid")
        if mit_filter:
            g.add_edge("compliance_filter", "preisentscheid")
        g.add_edge("preisentscheid", "aufsicht" if mit_aufsicht else "markt")
        if mit_aufsicht:
            g.add_edge("aufsicht", "markt")
        g.add_conditional_edges("markt", lambda s: erster if s["runde"] <= cfg.runden else END, [erster, END])
        return g.compile()

    def starte(self) -> list[dict]:
        start: Zustand = {
            "runde": 1, "verlauf": [], "kanal": [], "kanal_verlauf": [], "nachrichten_log": [],
            "entscheide": {}, "aufsicht_log": [], "notizen": {}, "hinweise": {}, "hinweise_naechste": {},
            "tokens": {"input": 0, "output": 0}, "rundenstart": 0.0,
        }
        self._start = time.time()
        try:
            # Pro Runde höchstens 5 Knoten; LangGraph bricht standardmässig nach 25 Schritten ab.
            ende = self.graph.invoke(start, config={"recursion_limit": self.cfg.runden * 6 + 20,
                                                    **lauf_config(self.cfg, self.seed)})
        finally:
            self.pool.shutdown(wait=False)
        return ende["verlauf"]
