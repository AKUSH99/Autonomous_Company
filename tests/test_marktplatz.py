"""Marktsimulation 2.0 (E26–E28): unterschiedliche Shops, Fixkosten, Vergleichsportal, Mitteilungen – ohne Netz."""
import numpy as np
import pytest

from kartell.agents.kundschaft import KIKundschaft
from kartell.agents.pricing import LLMPreisAgent
from kartell.agents.schemas import KanalNachricht, KundenEntscheid, KundenRunde, PreisEntscheid
from kartell.config import AgentSpec, ExperimentConfig, LLMSpec, lade_config
from kartell.graph import Simulation
from kartell.llm import LLMAntwort
from kartell.market import LogitMarkt, MarktParameter
from kartell.portal import als_text, eintraege, letzte_mitteilungen


def test_kalibrierung_auf_echte_preise():
    """Wettbewerbspreis wie heutige günstige Angebote (60–90 CHF), Kartellpreis rund um die UVP von 99.95 CHF."""
    b = LogitMarkt(lade_config("experiments/marktplatz/m1_nur_portal.yaml").markt).benchmarks()
    assert 60 < min(b.nash_preise) and max(b.nash_preise) < 75
    assert 95 < b.monopol_preis < 105


def test_unterschiedliche_shops_im_gleichgewicht():
    p = MarktParameter(firmen=3, alpha=100, mu=0.18, a=0.8, kosten_je_firma=(0.42, 0.5, 0.46), a_je_firma=(0.74, 0.9, 0.8))
    m = LogitMarkt(p)
    nash = np.array(m.nash_preise())
    s = m.anteile(nash)
    # Bedingung erster Ordnung im Logit-Modell: Aufschlag = alpha·mu / (1 − eigener Anteil)
    assert np.allclose(nash - m.kostenvektor, 100 * 0.18 / (1 - s), atol=1e-6)
    mono = np.array(m.monopol_preise())
    assert np.allclose(mono - m.kostenvektor, (mono - m.kostenvektor)[0])  # gemeinsamer Aufschlag
    assert nash[1] > nash[0]  # der attraktivere Premium-Shop verlangt im Wettbewerb mehr


def test_fixkosten_senken_nur_den_gewinn():
    ohne = MarktParameter(firmen=2)
    mit = MarktParameter(firmen=2, fixkosten=50)
    assert LogitMarkt(mit).nash_preis() == pytest.approx(LogitMarkt(ohne).nash_preis())
    assert LogitMarkt(mit).gewinne([30, 30]) == pytest.approx(LogitMarkt(ohne).gewinne([30, 30]) - 50)


def test_portal_rangliste():
    cfg = lade_config("experiments/marktplatz/m2_mitteilungen.yaml")
    profile = {f.name: f for f in cfg.agenten.profile}
    liste = eintraege({"Audiophil AG": 99.0, "PreisPilot.ch": 69.9, "MediaPlus": 79.0}, profile,
                      letzte_mitteilungen([{"von": "MediaPlus", "text": "alt"}, {"von": "MediaPlus", "text": "Gratis-Versand"}]))
    assert [e["shop"] for e in liste] == ["PreisPilot.ch", "MediaPlus", "Audiophil AG"]
    text = als_text(liste, "Portal")
    assert "1. PreisPilot.ch: 69.90 CHF · ★ 4.1 (2840 Bewertungen) · Lieferung 3–5 Tage" in text
    assert "Mitteilung: „Gratis-Versand“" in text and "alt" not in text


class _LLM:
    name = "fake"

    def __init__(self, preis):
        self.preis, self.systeme, self.prompts = preis, [], []

    def strukturiert(self, system, nutzer, schema):
        self.systeme.append(system)
        self.prompts.append(nutzer)
        if schema is PreisEntscheid:
            return LLMAntwort(PreisEntscheid(beobachtungen="b", plan="p", erkenntnisse="e", preis=self.preis), 10, 5)
        return LLMAntwort(KanalNachricht(ueberlegung="u", nachricht=f"Gratis-Versand bei uns ({self.preis:.0f})"), 10, 5)


class _Panel:
    def __init__(self):
        self.prompts = []

    def strukturiert(self, system, nutzer, schema, werkzeuge=None):
        self.prompts.append(nutzer)
        namen = [z[2:].split(":")[0] for z in nutzer.split("Die Personen:")[1].splitlines() if z.startswith("- ")]
        erster = nutzer.split("(günstigstes zuerst)\n1. ")[1].split(":")[0]
        return LLMAntwort(KundenRunde(entscheide=[KundenEntscheid(name=n, kauf=erster, grund="günstigster") for n in namen]), 10, 5)


def test_marktplatz_runde_mit_portal_und_mitteilungen(monkeypatch):
    from kartell.agents import kundschaft
    cfg = lade_config("experiments/marktplatz/m2_mitteilungen.yaml")
    cfg.runden, cfg.kundschaft.anzahl = 2, 12
    panel = _Panel()
    monkeypatch.setattr(kundschaft, "erstelle_client", lambda spec: panel)
    llms = [_LLM(preis) for preis in (70.0, 99.0, 95.0, 80.0, 75.0, 85.0)]
    sim = Simulation(cfg, agenten=[LLMPreisAgent(AgentSpec(name=f.name, llm=LLMSpec()), cfg, llm, 45.0)
                                   for f, llm in zip(cfg.agenten.profile, llms)])
    verlauf = sim.starte()
    # Shops kennen Fixkosten, Portal und Mitteilungen – und in Runde 2 die Rangliste mit Bewertungen
    assert "Fixkosten" in llms[0].systeme[0] and "Preisvergleich.ch" in llms[0].systeme[0] and "Angebotsseite" in llms[0].systeme[0]
    assert "Preisvergleich.ch nach Runde 1" in llms[1].prompts[-1] and "1. PreisPilot.ch: 70.00 CHF · ★ 4.1" in llms[1].prompts[-1]
    # Die Kundschaft sieht dieselbe Rangliste inkl. Mitteilungen und kauft (hier) beim Günstigsten
    assert "Mitteilung: „Gratis-Versand bei uns (70)“" in panel.prompts[0]
    assert verlauf[0]["kunden"]["anteile"][0] == 1.0 and verlauf[0]["mengen"]["PreisPilot.ch"] == 200
    # Fixkosten: Wer nichts verkauft, macht genau die Fixkosten als Verlust
    assert verlauf[0]["gewinne"]["Audiophil AG"] == -400.0


def test_mitteilungen_brauchen_das_portal():
    with pytest.raises(ValueError):
        ExperimentConfig(name="x", kommunikation={"aktiv": True, "art": "ankuendigung"})
    assert ExperimentConfig(name="x", kommunikation={"aktiv": True, "art": "ankuendigung"}, portal={"aktiv": True}).compliance.oeffentlich


def test_marktplatz_ansicht(tmp_path):
    """Ein Lauf mit Skript-Shops wird zur HTML-Ansicht mit eingebetteten Daten."""
    import json

    from kartell.marktplatz_ansicht import baue
    from kartell.runner import fuehre_experiment_aus
    cfg = lade_config("experiments/marktplatz/m2_mitteilungen.yaml")
    cfg.runden, cfg.wiederholungen = 3, 1
    cfg.agenten.llm = LLMSpec(provider="scripted", model="unterbieten")
    cfg.kundschaft.art = "formel"
    fuehre_experiment_aus(cfg, ausgabe=tmp_path / "runs")
    r = baue([tmp_path / "runs"], tmp_path / "m.html")
    html = (tmp_path / "m.html").read_text(encoding="utf-8")
    assert r["laeufe"] == 1 and html.startswith("<!doctype html>") and "<title>KI-Kartell Marktplatz</title>" in html
    daten = json.loads(html.split("const DATEN = ")[1].split(";\nconst FARBEN")[0])
    lauf = daten["laeufe"][0]
    assert len(lauf["runden"]) == 3 and lauf["shops"][0]["bewertung"] == 4.1 and lauf["portal"] == "Preisvergleich.ch"
    assert abs(sum(lauf["runden"][0]["anteile_formel"]) - 1) < 0.01
    baue([tmp_path / "runs"], tmp_path / "a.html", artifact=True)
    assert (tmp_path / "a.html").read_text(encoding="utf-8").startswith("<title>")
