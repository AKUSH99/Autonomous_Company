"""Kartell-Monitor und lesbare Versuchsnamen – mit Offline-Läufen der Skript-Agenten."""
import base64
import gzip
import json
import re

from kartell.__main__ import main
from kartell.config import anzeigename, lade_config
from kartell.runner import fuehre_lauf_aus


def _daten(html: str) -> dict:
    gepackt = re.search(r'const DATEN_GZ = "([^"]+)"', html).group(1)
    return json.loads(gzip.decompress(base64.b64decode(gepackt)))


def test_anzeigename():
    assert anzeigename("e3_compliance_filter_deepseek") == "E3 · Compliance-Filter"
    assert anzeigename("e10_anker_tief_deepseek") == "E10 · Anker tief"  # nicht mit E1 verwechseln
    assert anzeigename("e3_compliance_filter_deepseek_richter-jev") == "E3 · Compliance-Filter · Richter jev"
    assert anzeigename("e99_neu", "Eigener Titel") == "E99 · Eigener Titel"
    assert anzeigename("unbekannt") == "unbekannt"


def test_alle_versuche_haben_einen_titel():
    from pathlib import Path
    for datei in Path("experiments").glob("*.yaml"):
        if datei.name != "auftrag.yaml":
            assert lade_config(datei).titel, datei.name


def test_monitor_mit_abweichung(tmp_path, capsys):
    cfg = lade_config("experiments/demo_absprache_ohne_aufsicht.yaml")
    cfg.runden = 16
    cfg.abweichung.aktiv, cfg.abweichung.ab_runde, cfg.abweichung.bis_runde = True, 8, 12
    fuehre_lauf_aus(cfg, 1, tmp_path / "runs")
    fuehre_lauf_aus(lade_config("experiments/demo_absprache_mit_filter.yaml"), 1, tmp_path / "runs")
    ausgabe = tmp_path / "monitor.html"
    main(["monitor", str(tmp_path / "runs"), "--ausgabe", str(ausgabe)])
    assert "2 Versuche, 2 Läufe" in capsys.readouterr().out
    html = ausgabe.read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>") and "/*__DATEN_GZ__*/" not in html
    daten = _daten(html)
    assert [v["kurz"] for v in daten["versuche"]] == ["Demo mit Filter", "Demo ohne Aufsicht"]
    runden = daten["versuche"][1]["durchgaenge"][0]["runden"]
    markiert = [r for r in runden if r["abweichung"]]
    assert len(markiert) == 1
    abweichler = markiert[0]["abweichung"]["shop"]
    assert markiert[0]["entscheide"][abweichler]["erzwungen"] and markiert[0]["entscheide"][abweichler]["preis_gewollt"]


def test_modellname():
    from kartell.monitor import modellname
    assert modellname("openai_compat:deepseek-flash") == "deepseek-flash"
    assert modellname("openai_compat:nvidia/nemotron-3-ultra-550b-a55b:free") == "nemotron-3-ultra-550b-a55b"


def test_gleicher_versuch_mit_zwei_modellen_bekommt_modell_im_namen():
    from kartell.monitor import eindeutige_namen
    versuche = [{"kurz": "E1 · ohne Kanal", "durchgaenge": [{"modell": "deepseek-flash"}]},
                {"kurz": "E1 · ohne Kanal", "durchgaenge": [{"modell": "nvidia/nemotron-3-ultra-550b-a55b:free"}]},
                {"kurz": "E3 · Compliance-Filter", "durchgaenge": [{"modell": "deepseek-flash"}]}]
    assert [v["kurz"] for v in eindeutige_namen(versuche)] == [
        "E1 · ohne Kanal · DeepSeek", "E1 · ohne Kanal · Nemotron", "E3 · Compliance-Filter"]
