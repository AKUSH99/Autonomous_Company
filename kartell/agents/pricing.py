"""Preisagenten: ein LLM entscheidet jede Runde über Nachricht und Preis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..config import AgentSpec, ExperimentConfig
from ..llm import LLMClient, LLMFehler, erstelle_client
from ..market import Benchmarks
from . import prompts
from .schemas import KanalNachricht, PreisEntscheid


@dataclass
class Kontext:
    """Alles, was ein Agent in einer Runde wissen darf."""
    runde: int
    name: str
    verlauf: list[dict]                     # bisherige Runden (Preise, Mengen, Gewinne aller Shops)
    kanal: list[dict] = field(default_factory=list)          # zugestellte Nachrichten dieser Runde
    kanal_verlauf: list[dict] = field(default_factory=list)  # zugestellte Nachrichten früherer Runden
    notizen: dict = field(default_factory=lambda: {"plan": "", "erkenntnisse": ""})
    hinweise: list[str] = field(default_factory=list)        # Compliance-Hinweise an diesen Agenten
    benchmarks: Benchmarks | None = None    # nur für Skript-Agenten; LLM-Agenten sehen das nie


@dataclass
class Schritt:
    """Ergebnis eines Agenten-Schritts inkl. Kosten und eventuellem Fehler."""
    daten: dict
    input_tokens: int = 0
    output_tokens: int = 0
    fehler: str | None = None


class PreisAgent(Protocol):
    name: str
    modell: str

    def nachricht(self, ctx: Kontext) -> Schritt: ...
    def preis(self, ctx: Kontext) -> Schritt: ...


class LLMPreisAgent:
    def __init__(self, spec: AgentSpec, cfg: ExperimentConfig, llm: LLMClient, grenzkosten: float):
        self.name = spec.name
        self.modell = spec.llm.kurzname
        self.cfg = cfg
        self.llm = llm
        self.grenzkosten = grenzkosten
        self.max_preis = grenzkosten * 5  # Guardrail gegen absurde Preise (Tippfehler, Einheitenfehler)
        self.system = prompts.PREIS_SYSTEM.format(
            name=spec.name,
            produkt=cfg.produkt,
            kosten=grenzkosten,
            konkurrenz=cfg.markt.firmen - 1,
            ziel=cfg.agenten.ziel,
            zusatz=cfg.agenten.zusatz_anweisung,
        ) + (prompts.KANAL_ZUSATZ if cfg.kommunikation.aktiv else "")

    def _lagebericht(self, ctx: Kontext, mit_kanal: bool) -> str:
        teile = [f"Runde {ctx.runde}", ""]
        teile.append("Deine Notizen aus der letzten Runde")
        teile.append(f"PLAN: {ctx.notizen.get('plan') or '(noch keine)'}")
        teile.append(f"ERKENNTNISSE: {ctx.notizen.get('erkenntnisse') or '(noch keine)'}")
        teile.append("")
        letzte = ctx.verlauf[-self.cfg.agenten.historie_runden:]
        if letzte:
            teile.append(f"Marktverlauf (letzte {len(letzte)} Runden, neueste zuletzt)")
            teile.append("Runde | dein Preis | verkaufte Menge | dein Gewinn | Preise der Konkurrenz")
            for r in letzte:
                konk = ", ".join(f"{n}: {p:.2f}" for n, p in r["preise"].items() if n != self.name)
                teile.append(f"{r['runde']} | {r['preise'][self.name]:.2f} | {r['mengen'][self.name]:.1f} | "
                             f"{r['gewinne'][self.name]:.2f} | {konk}")
        else:
            teile.append("Noch keine Marktdaten – dies ist die erste Runde.")
        if self.cfg.kommunikation.aktiv:
            frueher = ctx.kanal_verlauf[-6:]
            if frueher:
                teile += ["", "Frühere Nachrichten im Kanal"]
                teile += [f"Runde {m['runde']}, {m['von']}: „{m['text']}\"" for m in frueher]
            if mit_kanal:
                teile += ["", "Nachrichten im Kanal in dieser Runde"]
                teile += [f"{m['von']}: „{m['text']}\"" for m in ctx.kanal] or ["(keine)"]
        if ctx.hinweise:
            teile += ["", "Hinweise der Compliance-Abteilung"] + [f"- {h}" for h in ctx.hinweise]
        return "\n".join(teile)

    def nachricht(self, ctx: Kontext) -> Schritt:
        prompt = self._lagebericht(ctx, mit_kanal=False) + "\n\n" + prompts.KANAL_AUFTRAG
        try:
            a = self.llm.strukturiert(self.system, prompt, KanalNachricht)
        except LLMFehler as e:
            return Schritt({"nachricht": "", "ueberlegung": ""}, fehler=str(e))
        text = a.objekt.nachricht.strip()[: self.cfg.kommunikation.max_zeichen]
        return Schritt({"nachricht": text, "ueberlegung": a.objekt.ueberlegung}, a.input_tokens, a.output_tokens)

    def preis(self, ctx: Kontext) -> Schritt:
        prompt = self._lagebericht(ctx, mit_kanal=True) + "\n\n" + prompts.PREIS_AUFTRAG
        vorher = ctx.verlauf[-1]["preise"][self.name] if ctx.verlauf else self.grenzkosten * 1.5
        try:
            a = self.llm.strukturiert(self.system, prompt, PreisEntscheid)
        except LLMFehler as e:
            # Fällt das Modell aus, bleibt der Preis der Vorrunde – das Experiment läuft weiter.
            return Schritt({"preis": vorher, "preis_roh": None, "korrigiert": True, "plan": ctx.notizen.get("plan", ""),
                            "erkenntnisse": ctx.notizen.get("erkenntnisse", ""), "beobachtungen": ""}, fehler=str(e))
        e = a.objekt
        preis = min(max(e.preis, 0.0), self.max_preis)
        return Schritt(
            {"preis": round(preis, 2), "preis_roh": e.preis, "korrigiert": preis != e.preis,
             "plan": e.plan, "erkenntnisse": e.erkenntnisse, "beobachtungen": e.beobachtungen},
            a.input_tokens, a.output_tokens,
        )


def erstelle_preisagent(spec: AgentSpec, cfg: ExperimentConfig, grenzkosten: float, seed: int) -> PreisAgent:
    if spec.llm.provider == "scripted":
        from .scripted import SkriptAgent
        return SkriptAgent(spec.name, spec.llm.model, grenzkosten, seed)
    return LLMPreisAgent(spec, cfg, erstelle_client(spec.llm), grenzkosten)
