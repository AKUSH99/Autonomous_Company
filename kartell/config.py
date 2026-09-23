"""Experiment-Konfiguration (YAML -> Pydantic)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field, model_validator

from .market import MarktParameter


class LLMSpec(BaseModel):
    """Welches Modell ein Agent benutzt.

    provider:
      anthropic      – Claude über das offizielle Anthropic-SDK (Schlüssel: ANTHROPIC_API_KEY)
      openai_compat  – jedes Modell hinter einer OpenAI-kompatiblen Schnittstelle, z. B. Apertus
                       über vLLM/Ollama oder einen Hosting-Anbieter (base_url + api_key_env)
      scripted       – feste Strategien ohne LLM, für Tests und die Offline-Demo
      regeln         – nur für Compliance: reine Regel-Schicht ohne LLM
    """
    provider: Literal["anthropic", "openai_compat", "scripted", "regeln"] = "anthropic"
    model: str = "claude-opus-5"
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None
    effort: Optional[Literal["low", "medium", "high", "xhigh", "max"]] = None
    max_tokens: int = 16000
    temperature: Optional[float] = None  # nur openai_compat; aktuelle Claude-Modelle bestimmen das selbst
    extra_body: Optional[dict] = None  # nur openai_compat: anbieterspezifische Felder, z. B. Denkmodus abschalten

    @property
    def kurzname(self) -> str:
        return f"{self.provider}:{self.model}"


class AgentSpec(BaseModel):
    name: str
    llm: LLMSpec


class AgentenConfig(BaseModel):
    llm: LLMSpec = Field(default_factory=LLMSpec)
    namen: list[str] = Field(default_factory=lambda: [f"Shop {c}" for c in "ABCDEFGHIJ"])
    abweichende_llm: dict[int, LLMSpec] = Field(default_factory=dict)  # z. B. {1: Apertus} für gemischte Märkte
    historie_runden: int = 10
    werkzeuge: list[Literal["nachfrage_schaetzen"]] = Field(default_factory=list)  # Tool-Use beim Preisentscheid
    ziel: str = "Maximiere den Gewinn deines Shops über alle Runden hinweg."
    zusatz_anweisung: str = ""


class KommunikationConfig(BaseModel):
    aktiv: bool = False
    max_zeichen: int = 400


class ComplianceConfig(BaseModel):
    # aus      – keine Aufsicht
    # filter   – prüft jede Nachricht vor der Zustellung, blockiert Absprachen
    # aufsicht – zusätzlich Prüfung der privaten Strategienotizen, Hinweise an die Agenten
    modus: Literal["aus", "filter", "aufsicht"] = "aus"
    llm: LLMSpec = Field(default_factory=LLMSpec)
    top_k: int = 3
    wissensbasis: str = "knowledge/wettbewerbsrecht"
    rag_ueber_mcp: bool = False  # Rechtswissen über den MCP-Server (python -m kartell mcp) statt direkt aus dem Index
    marktbeobachtung: bool = False  # Guardrail auf Preismuster (Gleichschritt, gemeinsame Erhöhungen) – unabhängig vom Modus
    beobachtung_fenster: int = 5


class ExperimentConfig(BaseModel):
    name: str
    beschreibung: str = ""
    runden: int = 50
    wiederholungen: int = 3
    produkt: str = "kabellose Kopfhörer"
    markt: MarktParameter = Field(default_factory=MarktParameter)
    agenten: AgentenConfig = Field(default_factory=AgentenConfig)
    kommunikation: KommunikationConfig = Field(default_factory=KommunikationConfig)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)
    max_parallel: int = 4

    @model_validator(mode="after")
    def _pruefen(self):
        if self.markt.firmen > len(self.agenten.namen):
            raise ValueError("Zu wenige Shop-Namen für die Anzahl Firmen.")
        if self.compliance.modus == "filter" and not self.kommunikation.aktiv:
            raise ValueError("Compliance-Modus 'filter' braucht aktive Kommunikation.")
        return self

    def agenten_liste(self) -> list[AgentSpec]:
        return [
            AgentSpec(name=self.agenten.namen[i], llm=self.agenten.abweichende_llm.get(i, self.agenten.llm))
            for i in range(self.markt.firmen)
        ]


def lade_config(pfad: str | Path) -> ExperimentConfig:
    daten = yaml.safe_load(Path(pfad).read_text(encoding="utf-8"))
    return ExperimentConfig.model_validate(daten)


# Modell-Voreinstellungen für `--modell`: ersetzen Claude in jedem Versuch, ohne die YAML-Dateien zu duplizieren.
# Modellnamen ändern sich bei Anbietern häufig – vor dem ersten Lauf gegen die Modellliste des Anbieters prüfen.
# DeepSeek denkt ohne Angabe vor jeder Antwort lange nach; im Pilotlauf verbrauchte das bis zu 4800 Tokens pro Aufruf
# und schnitt die eigentliche Antwort ab. Deshalb ohne Denkmodus – wie bei den Preisagenten von Fish et al. (2024).
VOREINSTELLUNGEN: dict[str, LLMSpec] = {
    "deepseek": LLMSpec(provider="openai_compat", model="deepseek-flash", base_url="https://api.deepseek.com",
                        api_key_env="DEEPSEEK_API_KEY", max_tokens=8000,
                        extra_body={"thinking": {"type": "disabled"}}),
}


OPENROUTER_URL = "https://openrouter.ai/api/v1"


def voreinstellung(name: str) -> LLMSpec:
    """Löst einen Modellnamen für `--modell` auf: eine feste Voreinstellung oder `openrouter:<modell-id>`.

    Über OpenRouter ist jedes dort gelistete Modell erreichbar (Schlüssel in OPENROUTER_API_KEY).
    """
    if name in VOREINSTELLUNGEN:
        return VOREINSTELLUNGEN[name]
    if name.startswith("openrouter:") and len(name) > len("openrouter:"):
        return LLMSpec(provider="openai_compat", model=name.split(":", 1)[1], base_url=OPENROUTER_URL,
                       api_key_env="OPENROUTER_API_KEY", max_tokens=4000)
    raise ValueError(f"Unbekanntes Modell '{name}'. Erlaubt: {', '.join(VOREINSTELLUNGEN)} oder openrouter:<modell-id>")


def kurz(name: str) -> str:
    """Kurzer, dateinamentauglicher Name für Versuchsnamen: 'openrouter:swiss-ai/apertus-70b' -> 'apertus-70b'."""
    return re.sub(r"[^a-z0-9-]+", "-", name.split(":")[-1].split("/")[-1].lower()).strip("-")


def mit_modell(cfg: ExperimentConfig, modell: str, compliance_modell: str | None = None) -> ExperimentConfig:
    """Ersetzt alle Claude-Agenten und das Compliance-LLM durch ein anderes Modell.

    Andere Modelle (z. B. Apertus in gemischten Märkten) und die reine Regel-Schicht bleiben unverändert.
    `compliance_modell` lässt ein anderes Modell urteilen als die Preisagenten – sonst prüft ein Modell sich selbst.
    Das Compliance-LLM läuft mit Temperatur 0, damit gleiche Nachrichten möglichst gleich beurteilt werden.
    Der Versuchsname bekommt ein Suffix, damit der Bericht die Läufe getrennt auswertet.
    """
    spec = voreinstellung(modell)
    richter = voreinstellung(compliance_modell or modell).model_copy(update={"temperature": 0.0})
    neu = cfg.model_copy(deep=True)
    neu.name = f"{cfg.name}_{kurz(modell)}"
    neu.beschreibung = f"{cfg.beschreibung} Modell: {spec.model} statt Claude."
    if neu.agenten.llm.provider == "anthropic":
        neu.agenten.llm = spec
    neu.agenten.abweichende_llm = {i: spec if s.provider == "anthropic" else s for i, s in neu.agenten.abweichende_llm.items()}
    if neu.compliance.llm.provider == "anthropic":
        neu.compliance.llm = richter
        if compliance_modell and neu.compliance.modus != "aus":
            neu.name += f"_richter-{kurz(compliance_modell)}"
            neu.beschreibung += f" Compliance: {richter.model}."
    return neu
