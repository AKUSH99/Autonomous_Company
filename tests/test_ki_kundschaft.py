"""KI-Kundschaft: ein LLM entscheidet für ein Panel simulierter Personen – hier mit einem simulierten Modell."""
from kartell.agents.kundschaft import KIKundschaft, beschreibung
from kartell.agents.schemas import KundenEntscheid, KundenRunde
from kartell.config import lade_config
from kartell.graph import Simulation
from kartell.llm import LLMAntwort, LLMFehler


class Panel:
    """Kauft beim billigsten Shop, über 30 CHF gar nicht; merkt sich die Prompts."""

    def __init__(self, fehler=False):
        self.prompts, self.fehler = [], fehler

    def strukturiert(self, system, nutzer, schema, werkzeuge=None):
        self.prompts.append(nutzer)
        if self.fehler:
            raise LLMFehler("429", 5, 0)
        preisteil = nutzer.split("Preise diese Runde:")[1].split("\n\n")[0]
        preise = {z.split(":")[0].strip("- "): float(z.split(":")[1].split("CHF")[0]) for z in preisteil.splitlines()
                  if z.startswith("- Shop")}
        billig = min(preise, key=preise.get)
        namen = [z[2:].split(":")[0] for z in nutzer.split("Die Personen:")[1].splitlines() if z.startswith("- ")]
        kauf = "nichts" if preise[billig] > 30 else billig
        return LLMAntwort(KundenRunde(entscheide=[KundenEntscheid(name=n, kauf=kauf, grund="Preis") for n in namen]), 50, 20)


def _cfg(sieht_kanal=False):
    cfg = lade_config("experiments/demo_absprache_ohne_aufsicht.yaml")
    cfg.runden = 3
    cfg.kundschaft.art, cfg.kundschaft.anzahl, cfg.kundschaft.sieht_kanal = "ki", 10, sieht_kanal
    return cfg


def test_panel_bestimmt_die_mengen(monkeypatch):
    from kartell.agents import kundschaft
    panel = Panel()
    monkeypatch.setattr(kundschaft, "erstelle_client", lambda spec: panel)
    verlauf = Simulation(_cfg()).starte()
    r = verlauf[-1]
    assert r["kunden"]["art"] == "ki" and r["kunden"]["fehler"] is None and len(r["kunden"]["entscheide"]) == 10
    billig = min(r["preise"], key=r["preise"].get)
    teuer = max(r["preise"], key=r["preise"].get)
    if r["preise"][billig] < r["preise"][teuer]:
        assert r["mengen"][billig] == 100.0 and r["mengen"][teuer] == 0.0  # beta · Anteil im Panel
    assert r["tokens"]["input"] >= 50  # Kosten der Kundschaft zählen mit
    assert "Öffentliche Nachrichten" not in panel.prompts[0]


def test_kanal_sichtbar_und_fehler_faellt_auf_formel_zurueck(monkeypatch):
    from kartell.agents import kundschaft
    panel = Panel()
    monkeypatch.setattr(kundschaft, "erstelle_client", lambda spec: panel)
    Simulation(_cfg(sieht_kanal=True)).starte()
    assert "Öffentliche Nachrichten der Shops" in panel.prompts[-1] and "Lasst uns" in panel.prompts[-1]
    monkeypatch.setattr(kundschaft, "erstelle_client", lambda spec: Panel(fehler=True))
    r = Simulation(_cfg()).starte()[-1]
    assert r["kunden"]["fehler"] and sum(r["mengen"].values()) > 0  # Formel übernimmt


def test_beschreibung_ohne_zahlen():
    cfg = _cfg()
    k = KIKundschaft(cfg, ["Shop A", "Shop B"], llm=Panel())
    assert len(k.personen) == 10
    text = beschreibung(k.personen[0], ["Shop A", "Shop B"])
    assert "Budget" in text and "CHF" not in text


def test_monitor_zeigt_ki_entscheide(tmp_path, monkeypatch):
    from kartell.agents import kundschaft
    from kartell.monitor import lade
    from kartell.runner import fuehre_lauf_aus
    monkeypatch.setattr(kundschaft, "erstelle_client", lambda spec: Panel())
    fuehre_lauf_aus(_cfg(), 1, tmp_path / "runs", ausgabe_konsole=False)
    lauf = lade(next((tmp_path / "runs").iterdir()))
    r = lauf["runden"][-1]
    assert r["kunden_ki"]["entscheide"] and r["kunden"]["anteile"] == r["kunden_ki"]["anteile"]


def test_bericht_zeigt_ki_kundschaft(tmp_path, monkeypatch):
    from kartell.agents import kundschaft
    from kartell.bericht import erstelle_bericht
    from kartell.runner import fuehre_lauf_aus
    monkeypatch.setattr(kundschaft, "erstelle_client", lambda spec: Panel())
    fuehre_lauf_aus(_cfg(sieht_kanal=True), 1, tmp_path / "runs", ausgabe_konsole=False)
    text = erstelle_bericht(tmp_path / "runs", tmp_path / "reports").read_text(encoding="utf-8")
    assert "KI-Kundschaft: Wie kauft ein KI-Panel?" in text
    zeile = next(z for z in text.splitlines() if z.startswith("| ") and "| ja |" in z)
    assert "0 von 30 Gründen" in zeile  # 10 Personen × 3 Runden, Grund „Preis“ erwähnt keine Absprache
