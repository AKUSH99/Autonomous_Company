"""Streamlit-Dashboard: startet ohne Fehler und zeigt Titel und erzwungene Abweichung (nur mit .[dashboard])."""
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")

from streamlit.testing.v1 import AppTest  # noqa: E402

from kartell.config import lade_config  # noqa: E402
from kartell.runner import fuehre_lauf_aus  # noqa: E402


def test_dashboard_zeigt_lauf_mit_abweichung(tmp_path):
    cfg = lade_config("experiments/demo/demo_absprache_ohne_aufsicht.yaml")
    cfg.runden = 16
    cfg.abweichung.aktiv, cfg.abweichung.ab_runde, cfg.abweichung.bis_runde = True, 8, 12
    fuehre_lauf_aus(cfg, 1, tmp_path / "laeufe" / "runs", ausgabe_konsole=False)
    at = AppTest.from_file(str(Path(__file__).parent.parent / "dashboard" / "app.py"), default_timeout=60)
    at.run()
    at.sidebar.text_input[0].set_value(str(tmp_path / "laeufe")).run()  # rekursiv: Läufe liegen eine Ebene tiefer
    assert not at.exception
    assert at.title[0].value == "Demo ohne Aufsicht"
    assert any("erzwungene Abweichung" in i.value for i in at.info)
