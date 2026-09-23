"""Experiment-Konfiguration (YAML -> Pydantic)."""
from __future__ import annotations

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

    @property
    def kurzname(self) -> str:
        return f"{self.provider}:{self.model}"


class AgentSpec(BaseModel):
    name: str
    llm: LLMSpec


class AgentenConfig(BaseModel):
    llm: LLMSpec = Field(default_factory=LLMSpec)
    namen: list[str] = Field(default_factory=lambda: ["Shop A", "Shop B", "Shop C", "Shop D", "Shop E"])
    abweichende_llm: dict[int, LLMSpec] = Field(default_factory=dict)  # z. B. {1: Apertus} für gemischte Märkte
    historie_runden: int = 10
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
VOREINSTELLUNGEN: dict[str, LLMSpec] = {
    "deepseek": LLMSpec(provider="openai_compat", model="deepseek-flash", base_url="https://api.deepseek.com",
                        api_key_env="DEEPSEEK_API_KEY", max_tokens=8000),
}


def mit_modell(cfg: ExperimentConfig, voreinstellung: str) -> ExperimentConfig:
    """Ersetzt alle Claude-Agenten und das Compliance-LLM durch eine Voreinstellung.

    Andere Modelle (z. B. Apertus in gemischten Märkten) und die reine Regel-Schicht bleiben unverändert.
    Der Versuchsname bekommt ein Suffix, damit der Bericht die Läufe getrennt auswertet.
    """
    spec = VOREINSTELLUNGEN[voreinstellung]
    neu = cfg.model_copy(deep=True)
    neu.name = f"{cfg.name}_{voreinstellung}"
    if neu.agenten.llm.provider == "anthropic":
        neu.agenten.llm = spec
    neu.agenten.abweichende_llm = {i: spec if s.provider == "anthropic" else s for i, s in neu.agenten.abweichende_llm.items()}
    if neu.compliance.llm.provider == "anthropic":
        neu.compliance.llm = spec
    return neu
