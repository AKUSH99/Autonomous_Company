"""Auftragsdatei: mehrere Läufe nacheinander, danach der Bericht – ohne API-Schlüssel mit den Skript-Agenten."""
import json

from kartell.__main__ import main


def test_auftrag_fuehrt_laeufe_aus_und_schreibt_bericht(tmp_path):
    auftrag = tmp_path / "auftrag.yaml"
    auftrag.write_text(
        "laeufe:\n"
        "  - {config: experiments/demo_absprache_ohne_aufsicht.yaml, runden: 4, wiederholungen: 2}\n"
        "  - {config: experiments/demo_absprache_mit_filter.yaml, runden: 4, wiederholungen: 1}\n",
        encoding="utf-8")
    main(["auftrag", str(auftrag), "--ausgabe", str(tmp_path / "runs"), "--berichte", str(tmp_path / "reports")])
    ergebnisse = [json.loads(p.read_text()) for p in (tmp_path / "runs").glob("*/ergebnis.json")]
    assert len(ergebnisse) == 3 and all(e["runden"] == 4 and e["modellfehler"] == 0 for e in ergebnisse)
    bericht = (tmp_path / "reports" / "bericht.md").read_text(encoding="utf-8")
    assert "demo_absprache_ohne_aufsicht" in bericht and "demo_absprache_mit_filter" in bericht
