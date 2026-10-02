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


def test_versuche_sind_in_drei_kapitel_und_anhang_geordnet():
    from kartell.monitor import _reihenfolge, kapitel
    assert kapitel("e1_ohne_kommunikation_deepseek") == 1 and kapitel("e2_mit_kommunikation_deepseek") == 1
    assert kapitel("e16_abweichung_kanal_deepseek") == 2 and kapitel("e17_abweichung_ohne_kanal_deepseek") == 2
    assert kapitel("e3_compliance_filter_deepseek") == 3 and kapitel("e18_verbot_deepseek_replikation") == 3
    # Anhang: Vergleichsläufe und zweites Modell fürs Verbot, KI-Kundschaft, Varianten
    for name in ("e1_ohne_kommunikation_deepseek_replikation", "e18_verbot_nemotron-3-ultra-550b-a55b-free",
                 "e20_ki_kunden_nemotron-3-ultra-550b-a55b-free", "e7_drei_shops_deepseek"):
        assert kapitel(name) == 0, name
    namen = ["e7_drei_shops", "e18_verbot_deepseek_replikation", "e2_mit_kommunikation", "e16_abweichung_kanal",
             "e1_ohne_kommunikation"]
    assert sorted(namen, key=_reihenfolge) == [
        "e1_ohne_kommunikation", "e2_mit_kommunikation", "e16_abweichung_kanal", "e18_verbot_deepseek_replikation",
        "e7_drei_shops"]


def test_anhang_in_zeilen_und_kurze_knoepfe():
    from kartell.monitor import eindeutige_namen
    def versuch(name, kapitel, kurz, modell):
        return {"name": name, "kapitel": kapitel, "kurz": kurz, "durchgaenge": [{"modell": modell}]}
    nemotron = "nvidia/nemotron-3-ultra-550b-a55b:free"
    ergebnis = eindeutige_namen([
        versuch("e7_drei_shops_deepseek", 0, "E7 · drei Shops", "deepseek-flash"),
        versuch("e18_verbot_nemotron-3-ultra-550b-a55b-free", 0, "E18 · Verbot", nemotron),
        versuch("e18_verbot_deepseek_replikation", 3, "E18 · Verbot · Replikation", "deepseek-flash"),
        versuch("e1_ohne_kommunikation_deepseek_replikation", 0, "E1 · ohne Kanal · Replikation", "deepseek-flash")])
    assert [(v["kapitel"], v["zeile"], v["knopf"]) for v in ergebnis] == [
        (3, "", "E18 · Verbot"),
        (0, "Verbot: Vergleichsläufe (DeepSeek)", "E1 · ohne Kanal"),
        (0, "Verbot mit zweitem Modell (Nemotron)", "E18 · Verbot"),
        (0, "Weitere Varianten", "E7 · drei Shops")]
    assert ergebnis[0]["kurz"] == "E18 · Verbot · Replikation · DeepSeek"  # voller Name bleibt für den Anhang


def test_geschichte_zeigt_nur_woertliche_zitate(tmp_path, monkeypatch):
    import kartell.monitor as monitor
    cfg = lade_config("experiments/demo_absprache_ohne_aufsicht.yaml")
    cfg.runden = 6
    fuehre_lauf_aus(cfg, 1, tmp_path / "runs")
    ordner = next((tmp_path / "runs").iterdir())
    runden = [json.loads(z) for z in (ordner / "runden.jsonl").read_text(encoding="utf-8").splitlines() if z.strip()]
    echt = next((r["runde"], m["von"], m["text"]) for r in runden for m in r.get("nachrichten", []) if len(m["text"]) > 30)
    monkeypatch.setattr(monitor, "GESCHICHTE", [{
        "id": "test", "nummer": 1, "titel": "T", "frage": "F?", "antwort": "A.", "text": "", "fakten": [],
        "versuch": cfg.name, "wiederholung": 1, "von": 1, "bis": 6, "ruhe": 6,
        "momente": [
            {"runde": echt[0], "art": "kanal", "shop": echt[1], "text": f"{echt[2][:12]} […] {echt[2][-12:]}"},
            {"runde": echt[0], "art": "kanal", "shop": echt[1], "text": "Diesen Satz hat nie ein Agent geschrieben."},
            {"runde": 3, "art": "eingriff", "shop": echt[1], "text": "Eingriff ohne Abweichung in den Daten"},
        ]}])
    ausgabe = tmp_path / "monitor.html"
    monitor.baue([tmp_path / "runs"], ausgabe)
    daten = _daten(ausgabe.read_text(encoding="utf-8"))
    akt = daten["geschichte"][0]
    assert [m["text"][:12] for m in akt["momente"]] == [echt[2][:12]]  # nur das echte Zitat bleibt
    assert daten["versuche"][akt["versuch"]]["name"] == cfg.name and "_ordner" not in daten["versuche"][0]["durchgaenge"][0]
