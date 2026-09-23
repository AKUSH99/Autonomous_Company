"""Modell-Voreinstellungen (--modell) und Kostenschätzung."""
from kartell.config import VOREINSTELLUNGEN, lade_config, mit_modell
from kartell.kosten import schaetze


def test_deepseek_ersetzt_claude_bei_agenten_und_compliance():
    cfg = lade_config("experiments/e3_compliance_filter.yaml")
    neu = mit_modell(cfg, "deepseek")
    assert neu.name == "e3_compliance_filter_deepseek"
    assert all(a.llm == VOREINSTELLUNGEN["deepseek"] for a in neu.agenten_liste())
    assert neu.compliance.llm == VOREINSTELLUNGEN["deepseek"]
    assert cfg.agenten.llm.provider == "anthropic"  # Original bleibt unverändert


def test_deepseek_laesst_andere_modelle_und_regeln_unveraendert():
    gemischt = mit_modell(lade_config("experiments/e6_gemischter_markt.yaml"), "deepseek")
    modelle = [a.llm.model for a in gemischt.agenten_liste()]
    assert modelle == ["deepseek-flash", "swiss-ai/Apertus-8B-Instruct-2509"]
    demo = mit_modell(lade_config("experiments/demo_absprache_mit_filter.yaml"), "deepseek")
    assert demo.compliance.llm.provider == "regeln"
    assert all(a.llm.provider == "scripted" for a in demo.agenten_liste())


def test_kostenschaetzung_deepseek_und_unbekannte_modelle():
    s = schaetze(mit_modell(lade_config("experiments/e2_mit_kommunikation.yaml"), "deepseek"))
    assert 0 < s["usd"] < 5 and not s["unvollstaendig"]
    assert schaetze(lade_config("experiments/e5_apertus.yaml"))["unvollstaendig"]  # eigener Server: Preis unbekannt
    assert schaetze(lade_config("experiments/demo_absprache_mit_filter.yaml"))["usd"] == 0
