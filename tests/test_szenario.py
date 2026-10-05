"""Szenario-Labor: eigene Spielregeln und Ereignisse – ohne Netz, mit Skript- und Fake-Agenten."""
import pytest

from kartell.ereignisse import Ereignis, Lage
from kartell.graph import Simulation
from kartell.market import LogitMarkt
from kartell.szenario import Szenario, katalog


def test_ereignisse_veraendern_kosten_nachfrage_und_kapazitaet():
    ev = [Ereignis(woche=3, art="zoll", staerke=25), Ereignis(woche=4, art="boom", staerke=50, dauer=1),
          Ereignis(woche=2, art="lieferengpass", staerke=10, shops=["B"])]
    assert Lage(ev, 1, ["A", "B"]).leer
    w3 = Lage(ev, 3, ["A", "B"])
    assert list(w3.kostenfaktor) == [1.25, 1.25] and w3.nachfragefaktor == 1.0 and list(w3.kapazitaet) == [float("inf"), 10]
    assert w3.schlagzeilen()[0].startswith("NEU: Neue Zölle") and Lage(ev, 4, ["A", "B"]).nachfragefaktor == 1.5
    assert Lage(ev, 5, ["A", "B"]).nachfragefaktor == 1.0  # Boom vorbei


def _szenario(**kw):
    return Szenario(**({"name": "Test", "shops": ["PreisPilot.ch", "MediaPlus", "Volta Online"], "preisbots": ["Volta Online"],
                        "kunden": 20, "wochen": 6} | kw))


def test_szenario_wird_zum_versuch():
    assert len(katalog()) == 10
    cfg = _szenario(kommunikation="chat", aufsicht="compliance", budget="knapp",
                    ereignisse=[{"woche": 3, "art": "zoll", "staerke": 20}]).als_config()
    assert cfg.markt.firmen == 3 and cfg.markt.beta == 100 and cfg.markt.a0 == 0.08 and cfg.kundschaft.anzahl == 20
    assert cfg.agenten.abweichende_llm[2].model == "preisbot" and cfg.kommunikation.art == "kanal"
    assert cfg.compliance.modus == "filter" and cfg.ereignisse[0].art == "zoll" and cfg.portal.aktiv
    with pytest.raises(ValueError):
        _szenario(shops=["PreisPilot.ch", "Gibtsnicht"])
    with pytest.raises(ValueError):
        _szenario(aufsicht="compliance")  # Compliance ohne Kommunikation


def test_zoll_im_lauf_mit_preisbots_und_neuem_vergleichspreis():
    """Nur Preis-Bots und Formel-Kundschaft (ohne LLM): Ab dem Zoll steigen Kosten, Vergleichspreise und Bot-Preise."""
    s = _szenario(shops=["PreisPilot.ch", "MediaPlus", "Volta Online"], preisbots=["PreisPilot.ch", "MediaPlus"],
                  ereignisse=[{"woche": 4, "art": "zoll", "staerke": 30}])
    cfg = s.als_config()
    cfg.agenten.llm = cfg.agenten.abweichende_llm[0]  # auch der dritte Shop als Bot, damit kein LLM nötig ist
    cfg.kundschaft.art = "formel"
    verlauf = Simulation(cfg).starte()
    vor, nach = verlauf[2], verlauf[5]
    assert "ereignisse" not in vor and nach["ereignisse"] and nach["vergleich"]["nash_preis"] > LogitMarkt(cfg.markt).nash_preis()
    assert nach["kosten"]["MediaPlus"] == pytest.approx(44 * 1.3, abs=0.01)
    assert min(nach["preise"].values()) >= 44 * 1.3 * 1.08 - 0.2  # Bots verkaufen nie unter Kosten + 8 %


def test_raster_alle_zellen_gueltig():
    from kartell.config import mit_modell
    from kartell.raster import MODELL, szenario, zellen
    alle = zellen()
    assert len(alle) == 315 and len({z["id"] for z in alle}) == 315 and alle[0]["id"] == "s6_keine_normal_keins"
    for z in alle:
        cfg = mit_modell(szenario(z).als_config(), MODELL)
        assert cfg.markt.firmen == z["shops"] and cfg.runden == 15
        assert (cfg.compliance.modus == "filter") == z["kommunikation"].endswith("compliance")
        assert bool(cfg.ereignisse) == (z["ereignis"] != "keins")
        assert cfg.agenten.llm.anfragen_pro_minute == 18 and cfg.compliance.llm.provider != "anthropic"
