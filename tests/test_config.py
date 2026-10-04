"""Modell-Voreinstellungen (--modell) und Kostenschätzung."""
import pytest

from kartell.config import VOREINSTELLUNGEN, kurz, lade_config, mit_modell, voreinstellung
from kartell.kosten import schaetze


def test_deepseek_ersetzt_claude_bei_agenten_und_compliance():
    cfg = lade_config("experiments/e3_compliance_filter.yaml")
    neu = mit_modell(cfg, "deepseek")
    assert neu.name == "e3_compliance_filter_deepseek"
    assert all(a.llm == VOREINSTELLUNGEN["deepseek"] for a in neu.agenten_liste())
    assert neu.compliance.llm == VOREINSTELLUNGEN["deepseek"]  # unverändert: vergleichbar mit bisherigen Läufen
    streng = mit_modell(cfg, "deepseek", compliance_temperatur=0.0)
    assert streng.compliance.llm.temperature == 0.0 and streng.agenten.llm.temperature is None
    assert cfg.agenten.llm.provider == "anthropic"  # Original bleibt unverändert


def test_deepseek_laesst_andere_modelle_und_regeln_unveraendert():
    gemischt = mit_modell(lade_config("experiments/e6_gemischter_markt.yaml"), "deepseek")
    modelle = [a.llm.model for a in gemischt.agenten_liste()]
    assert modelle == ["deepseek-flash", "CSCS-Inference/swiss-ai/Apertus-v1.5-70B"]
    demo = mit_modell(lade_config("experiments/demo_absprache_mit_filter.yaml"), "deepseek")
    assert demo.compliance.llm.provider == "regeln"
    assert all(a.llm.provider == "scripted" for a in demo.agenten_liste())


def test_kostenschaetzung_deepseek_und_unbekannte_modelle():
    s = schaetze(mit_modell(lade_config("experiments/e2_mit_kommunikation.yaml"), "deepseek"))
    assert 0 < s["usd"] < 5 and not s["unvollstaendig"]
    assert schaetze(lade_config("experiments/e5_apertus.yaml"))["unvollstaendig"]  # eigener Server: Preis unbekannt
    assert schaetze(lade_config("experiments/demo_absprache_mit_filter.yaml"))["usd"] == 0


def test_openrouter_modelle_und_eigener_richter():
    spec = voreinstellung("openrouter:swiss-ai/apertus-70b-instruct")
    assert spec.base_url == "https://openrouter.ai/api/v1" and spec.api_key_env == "OPENROUTER_API_KEY"
    assert spec.model == "swiss-ai/apertus-70b-instruct" and kurz("openrouter:swiss-ai/apertus-70b-instruct") == "apertus-70b-instruct"
    neu = mit_modell(lade_config("experiments/e3_compliance_filter.yaml"), "deepseek", "openrouter:anbieter/richter-modell")
    assert neu.name == "e3_compliance_filter_deepseek_richter-richter-modell"
    assert neu.agenten.llm.model == "deepseek-flash" and neu.compliance.llm.model == "anbieter/richter-modell"
    ohne_filter = mit_modell(lade_config("experiments/e2_mit_kommunikation.yaml"), "deepseek", "openrouter:x/y")
    assert ohne_filter.name == "e2_mit_kommunikation_deepseek"  # ohne Compliance kein Richter-Suffix
    with pytest.raises(ValueError, match="openrouter:<modell-id>"):
        voreinstellung("jeff")


def test_plattformen_des_moduls(monkeypatch):
    """Swiss AI Research Platform und FHNW-LiteLLM (SW4) als OpenAI-kompatible Voreinstellungen."""
    swiss = voreinstellung("swissai:CSCS-Inference/swiss-ai/Apertus-v1.5-70B")
    assert swiss.extra_body["chat_template_kwargs"]["thinking"] is False and swiss.max_tokens == 16000
    assert swiss.provider == "openai_compat" and swiss.base_url == "https://api.swissai.svc.cscs.ch/v1"
    assert swiss.api_key_env == "SWISSAI_API_KEY" and swiss.model == "CSCS-Inference/swiss-ai/Apertus-v1.5-70B"
    assert voreinstellung("apertus").base_url == swiss.base_url and "Apertus" in VOREINSTELLUNGEN["apertus"].model

    monkeypatch.delenv("LITELLM_BASE_URL", raising=False)
    lite = voreinstellung("litellm:gpt-oss-120b")
    assert lite.base_url == "https://litellm.engines.aisl.science/v1" and lite.api_key_env == "LITELLM_API_KEY"
    monkeypatch.setenv("LITELLM_BASE_URL", "")  # leere Repository-Variable im Workflow
    assert voreinstellung("litellm:x").base_url == "https://litellm.engines.aisl.science/v1"
    monkeypatch.setenv("LITELLM_BASE_URL", "http://localhost:4000/v1")
    assert voreinstellung("litellm:x").base_url == "http://localhost:4000/v1"

    assert kurz("swissai:CSCS-Inference/swiss-ai/Apertus-v1.5-70B") == "apertus-v1-5-70b"
    assert kurz("apertus") == "apertus"
    with pytest.raises(ValueError):
        voreinstellung("swissai:")
