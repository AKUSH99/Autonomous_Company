"""Budgetwächter und Zeitlimit: Läufe stoppen geordnet, die bisherigen Runden bleiben ausgewertet."""
import json

from kartell.bericht import erstelle_bericht
from kartell.config import LLMSpec, lade_config
from kartell.graph import LimitErreicht, Simulation
from kartell.kosten import Budgetwaechter
from kartell.runner import fuehre_experiment_aus

DEEPSEEK = LLMSpec(provider="openai_compat", model="deepseek-flash", base_url="http://test", api_key_env="X")
RUNDE = {"input": 50_000, "output": 7_000}  # ≈ 0.023 USD zum Spitzentarif


def test_budget_nach_echtem_guthaben_mit_puffer_fuer_die_naechsten_runden():
    guthaben = iter([8.0, 7.0, 3.6])  # Start, nach Runde 10, nach Runde 20
    w = Budgetwaechter(DEEPSEEK, budget_usd=4.5, reserve_usd=0.5, guthaben_fn=lambda spec: next(guthaben))
    assert w(5, {}, RUNDE) is None  # zwischen den Abfragen keine Prüfung
    assert w(10, {}, RUNDE) is None  # 1.00 USD verbraucht
    grund = w(20, {}, RUNDE)  # 4.40 USD verbraucht + Puffer für 10 Runden > 4.50
    assert grund and "laut Guthaben" in grund and w.erschoepft


def test_reserve_bleibt_auf_dem_konto():
    guthaben = iter([2.0, 0.7])
    w = Budgetwaechter(DEEPSEEK, budget_usd=10, reserve_usd=0.5, guthaben_fn=lambda spec: next(guthaben))
    assert "Reserve" in w(10, {}, RUNDE)


def test_ohne_guthaben_abfrage_zaehlen_die_tokens_ueber_alle_laeufe():
    w = Budgetwaechter(DEEPSEEK, budget_usd=0.06, guthaben_fn=lambda spec: None)
    w.lauf_beendet({"input": 60_000, "output": 8_000})  # erster Lauf ≈ 0.028 USD
    assert w(1, {"input": 0, "output": 0}, RUNDE) is None
    assert "geschätzt aus Tokens" in w(2, RUNDE, RUNDE)


def test_limit_stoppt_lauf_und_speichert_teilergebnis(tmp_path):
    cfg = lade_config("experiments/demo_absprache_ohne_aufsicht.yaml")
    cfg.runden, cfg.wiederholungen = 10, 3

    class NachDreiRunden:
        erschoepft = False

        def __call__(self, runde, tokens_lauf, tokens_runde):
            if runde == 3:
                self.erschoepft = True
                return "Budget erreicht"

        def lauf_beendet(self, tokens):
            pass

    ergebnisse = fuehre_experiment_aus(cfg, tmp_path, waechter=NachDreiRunden())
    assert len(ergebnisse) == 1  # weitere Wiederholungen entfallen
    e = ergebnisse[0]
    assert e["runden"] == 3 and e["abbruch"]["art"] == "LimitErreicht"
    gespeichert = json.loads(next(tmp_path.glob("*/ergebnis.json")).read_text())
    assert gespeichert["abbruch"]["grund"].startswith("Budget erreicht")
    bericht = erstelle_bericht(tmp_path, tmp_path / "reports").read_text(encoding="utf-8")
    assert "Vorzeitig beendete Läufe" in bericht and "nach 3 Runden" in bericht


def test_zeitlimit():
    import pytest
    cfg = lade_config("experiments/demo_absprache_ohne_aufsicht.yaml")
    cfg.runden = 5
    sim = Simulation(cfg, zeitlimit_s=1e-9)
    with pytest.raises(LimitErreicht, match="Zeitlimit"):
        sim.starte()
    assert len(sim.verlauf_bisher) == 1


def test_permutationstest_und_bootstrap():
    from kartell.metrics import bootstrap_differenz, permutationstest
    assert permutationstest([1, 1.1, 1.2], [0, 0.1, 0.2]) == 0.1  # 3 gegen 3: kleinstmöglicher p-Wert
    assert permutationstest([1, 1.1, 1.2, 1.3], [0, 0.1, 0.2, 0.3]) < 0.05
    assert permutationstest([0.5, 0.2, 0.8], [0.4, 0.6, 0.3]) > 0.5
    lo, hi = bootstrap_differenz([0.6, 0.7, 0.8], [0.1, 0.2, 0.3])
    assert lo < -0.4 < -0.5 + 0.2 and hi < 0


def test_wiederholungen_fortsetzen(tmp_path):
    cfg = lade_config("experiments/demo_absprache_ohne_aufsicht.yaml")
    cfg.runden, cfg.wiederholungen = 2, 2
    fuehre_experiment_aus(cfg, tmp_path, erste_wiederholung=4)
    assert sorted(p.name[-2:] for p in tmp_path.iterdir()) == ["w4", "w5"]
