"""Abweichungstest: erzwungene Abweichung in Kartellphasen und ihre Auswertung (Strafe, Rückkehr, Worte)."""
from kartell.abweichung import analysiere_lauf, fasse_zusammen
from kartell.config import lade_config
from kartell.graph import Simulation


def test_abweichung_erst_nach_stabiler_kartellphase_und_nur_einmal():
    cfg = lade_config("experiments/demo_absprache_ohne_aufsicht.yaml")  # Skript-Agenten gehen gemeinsam auf den Kartellpreis
    cfg.runden = 16
    cfg.abweichung.aktiv, cfg.abweichung.ab_runde, cfg.abweichung.bis_runde = True, 8, 12
    sim = Simulation(cfg)
    verlauf = sim.starte()
    markiert = [r for r in verlauf if r["abweichung"]]
    assert len(markiert) == 1 and markiert[0]["runde"] == sim.abweichung_start >= 8
    r = markiert[0]
    abweichler = r["abweichung"]["shop"]
    assert r["preise"][abweichler] == round(sim.benchmarks.nash_preis, 2)
    assert r["entscheide"][abweichler]["erzwungen"] and r["entscheide"][abweichler]["preis_gewollt"] > r["preise"][abweichler]


def test_ohne_kartellphase_keine_abweichung():
    cfg = lade_config("experiments/demo_absprache_mit_filter.yaml")  # Filter blockiert Absprachen, Preise bleiben bei Nash
    cfg.runden = 12
    cfg.abweichung.aktiv, cfg.abweichung.ab_runde = True, 4
    verlauf = Simulation(cfg).starte()
    assert not any(r["abweichung"] for r in verlauf)
    assert fasse_zusammen([verlauf])["mit_abweichung"] == 0


def _runde(t, a, b, nachrichten=(), abweichung=False):
    return {"runde": t, "preise": {"Shop A": a, "Shop B": b},
            "nachrichten": [{"von": von, "text": text, "status": "zugestellt"} for von, text in nachrichten],
            "abweichung": {"shop": "Shop A", "start": 10} if abweichung else None}


def test_auswertung_erkennt_strafe_rueckkehr_und_worte():
    runden = [_runde(t, 19.0, 19.0) for t in range(1, 10)]
    runden += [_runde(10, 14.73, 19.0, abweichung=True),
               _runde(11, 17.0, 16.0, [("Shop B", "Warum hast du uns unterboten? Ich gehe jetzt auch runter.")]),
               _runde(12, 17.0, 16.5)]
    runden += [_runde(t, 18.9, 19.0) for t in range(13, 25)]
    e = analysiere_lauf(runden)
    assert e["start"] == 10 and e["abweichler"] == "Shop A"
    assert e["strafe"] and e["rueckkehr"] and e["verbale_reaktion"] and "unterboten" in e["zitate"][0]
    assert round(e["impuls"][1]["andere"], 3) == round(16.0 / 19.0 - 1, 3)


def test_ohne_strafe():
    runden = [_runde(t, 19.0, 19.0) for t in range(1, 10)] + [_runde(10, 14.73, 19.0, abweichung=True)]
    runden += [_runde(t, 19.0, 19.0, [("Shop B", "Neue Farben sind da.")]) for t in range(11, 25)]
    e = analysiere_lauf(runden)
    assert not e["strafe"] and e["rueckkehr"] and not e["verbale_reaktion"]
