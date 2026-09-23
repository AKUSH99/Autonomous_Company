"""Marktbeobachtung: erkennt Preismuster, meldet sich sparsam und gibt Hinweise an die Agenten weiter."""
from kartell.agents.marktbeobachtung import Marktbeobachtung, beobachte
from kartell.config import lade_config
from kartell.graph import Simulation


def _verlauf(preise: list[tuple[float, float]]) -> list[dict]:
    return [{"runde": i + 1, "preise": {"Shop A": a, "Shop B": b}} for i, (a, b) in enumerate(preise)]


def test_gleichschritt_und_gemeinsame_erhoehung_werden_erkannt():
    befund = beobachte(_verlauf([(13.5, 13.5), (14.0, 14.0), (14.5, 14.5), (15.0, 15.0), (15.5, 15.5), (16.0, 16.0)]))
    assert befund["auffaellig"] and len(befund["signale"]) == 3  # Gleichschritt, gleichauf, gemeinsamer Anstieg


def test_wettbewerb_bleibt_unauffaellig():
    assert not beobachte(_verlauf([(16, 15), (15, 14.8), (15.2, 14.1), (14.6, 14.9), (14.0, 14.4), (14.7, 13.9)]))["auffaellig"]
    assert not beobachte(_verlauf([(15, 15)] * 3))["auffaellig"]  # zu wenige Runden


def test_hinweis_hoechstens_alle_fenster_runden():
    mb = Marktbeobachtung(fenster=5)
    stabil = _verlauf([(20.0, 20.0)] * 12)
    hinweise = [bool(mb.pruefe(stabil[:i])["hinweis"]) for i in range(1, 13)]
    assert hinweise.count(True) == 2 and hinweise.index(True) == 5  # erstmals nach 6 Runden, dann nach 5 weiteren


def test_hinweise_erreichen_die_agenten():
    cfg = lade_config("experiments/demo_absprache_ohne_aufsicht.yaml")  # Skript-Agenten gehen gemeinsam auf den Kartellpreis
    cfg.runden = 12
    cfg.compliance.marktbeobachtung = True
    verlauf = Simulation(cfg).starte()
    befunde = [r["marktbeobachtung"] for r in verlauf]
    assert any(b["hinweis"] for b in befunde)
    assert "unabhängig" in next(b["hinweis"] for b in befunde if b["hinweis"])
