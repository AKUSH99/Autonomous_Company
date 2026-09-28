"""Auftragsdatei: mehrere Läufe nacheinander, danach der Bericht – ohne API-Schlüssel mit den Skript-Agenten."""
import json

import pytest

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


def test_auftrag_wie_auf_github_mit_simuliertem_modell(tmp_path, monkeypatch):
    """Der ganze Ablauf eines echten Auftrags – Modellprüfung, KI-Richter, Werkzeug, Marktbeobachtung, Bericht –
    mit einem simulierten LLM statt DeepSeek, damit ein bezahlter Lauf nicht an einem Programmfehler scheitert."""
    import kartell.__main__ as cli
    from kartell.agents import compliance, pricing
    from kartell.agents.schemas import ComplianceUrteil, KanalNachricht, PreisEntscheid
    from kartell.llm import LLMAntwort

    class Simuliert:
        name = "sim"

        def strukturiert(self, system, nutzer, schema, werkzeuge=None):
            protokoll = []
            if werkzeuge:
                text, _ = werkzeuge[0].ausfuehren({"eigener_preis": 16.0})
                protokoll.append({"name": werkzeuge[0].name, "ergebnis": text})
            if schema is PreisEntscheid:
                objekt = PreisEntscheid(beobachtungen="b", plan="p", erkenntnisse="e", preis=16.0)
            elif schema is KanalNachricht:
                objekt = KanalNachricht(ueberlegung="u", nachricht="Wir bleiben gemeinsam bei 16 CHF.")
            elif schema is ComplianceUrteil:
                objekt = ComplianceUrteil(zulaessig=False, kategorie="preisabsprache", begruendung="gemeinsamer Preis", rechtsgrundlagen=["Art. 5 KG"])
            else:
                objekt = schema.model_validate({"bedenklich": False, "begruendung": "", "hinweis_an_agent": ""})
            return LLMAntwort(objekt, 100, 20, werkzeug_aufrufe=protokoll)

    monkeypatch.setattr(cli, "_pruefe_modell", lambda spec, berichte: None)
    monkeypatch.setattr(cli, "_modellsuche", lambda suche, berichte: (berichte / "modellsuche.json").write_text("{}"))
    monkeypatch.setattr(compliance, "erstelle_client", lambda spec: Simuliert())
    monkeypatch.setattr(pricing, "erstelle_client", lambda spec: Simuliert())
    stichprobe = tmp_path / "stichprobe.jsonl"
    stichprobe.write_text(json.dumps({"id": "N001", "text": "Lass uns 20 CHF halten.", "quelle": {"von": "Shop A"}}) + "\n")
    auftrag = tmp_path / "auftrag.yaml"
    auftrag.write_text(
        "modell: deepseek\nzeitlimit_min: 10\nmodellsuche: {begriffe: [jeff]}\n"
        f"urteile_sammeln: {{stichprobe: {stichprobe}, modelle: [deepseek]}}\n"
        "laeufe:\n"
        "  - {config: experiments/e14_werkzeug.yaml, runden: 4, wiederholungen: 1}\n"
        "  - {config: experiments/e15_marktbeobachtung.yaml, runden: 7, wiederholungen: 1}\n"
        "  - {config: experiments/e3_compliance_filter.yaml, runden: 2, wiederholungen: 1, erste_wiederholung: 4}\n",
        encoding="utf-8")
    main(["auftrag", str(auftrag), "--ausgabe", str(tmp_path / "runs"), "--berichte", str(tmp_path / "reports")])
    urteile = [json.loads(z) for z in (tmp_path / "reports" / "urteile_deepseek.jsonl").read_text().splitlines()]
    assert urteile[0]["status"] == "blockiert"
    laeufe = {p.name.split("_", 1)[1]: p for p in (tmp_path / "runs").iterdir()}
    assert "e3_compliance_filter_deepseek_w4" in laeufe
    werkzeug = [json.loads(z) for z in (laeufe["e14_werkzeug_deepseek_w1"] / "runden.jsonl").read_text().splitlines()]
    assert werkzeug[-1]["entscheide"]["Shop A"]["werkzeug_aufrufe"][0]["name"] == "nachfrage_schaetzen"
    markt = [json.loads(z) for z in (laeufe["e15_marktbeobachtung_deepseek_w1"] / "runden.jsonl").read_text().splitlines()]
    assert any(r["marktbeobachtung"]["hinweis"] for r in markt)  # gleiche Preise ab Runde 1 → Hinweis
    assert "Vergleiche" in (tmp_path / "reports" / "bericht.md").read_text(encoding="utf-8")


def test_auftrag_mit_modell_je_lauf_und_stopp_nach_ausfall(tmp_path, monkeypatch, capsys):
    """Probelauf mehrerer Gratismodelle: jeder Lauf nennt sein Modell; fällt eines aus, entfallen nur seine weiteren Läufe."""
    import kartell.__main__ as cli
    from kartell.agents import pricing
    from kartell.agents.schemas import KanalNachricht, PreisEntscheid
    from kartell.config import kurz
    from kartell.llm import LLMAntwort, LLMFehler

    geprueft = []

    class Simuliert:
        def __init__(self, spec):
            self.name, self.spec = spec.kurzname, spec

        def strukturiert(self, system, nutzer, schema, werkzeuge=None):
            if "kaputt" in self.spec.model:
                raise LLMFehler("429 Tageslimit erreicht")
            objekt = PreisEntscheid(beobachtungen="b", plan="p", erkenntnisse="e", preis=16.0) if schema is PreisEntscheid \
                else KanalNachricht(ueberlegung="u", nachricht="")
            return LLMAntwort(objekt, 10, 5)

    monkeypatch.setattr(cli, "_pruefe_modell", lambda spec, berichte: geprueft.append(spec.model))
    monkeypatch.setattr(pricing, "erstelle_client", Simuliert)
    auftrag = tmp_path / "auftrag.yaml"
    auftrag.write_text(
        "laeufe:\n"
        "  - {config: experiments/e2_mit_kommunikation.yaml, modell: 'openrouter:google/gemma-4-31b-it:free', runden: 3, wiederholungen: 1}\n"
        "  - {config: experiments/e2_mit_kommunikation.yaml, modell: 'openrouter:test/kaputt:free', runden: 5, wiederholungen: 2}\n"
        "  - {config: experiments/e2_mit_kommunikation.yaml, modell: 'openrouter:test/kaputt:free', runden: 5, wiederholungen: 1}\n"
        "  - {config: experiments/e2_mit_kommunikation.yaml, modell: 'openrouter:qwen/qwen3.8-27b:free', runden: 3, wiederholungen: 1}\n",
        encoding="utf-8")
    with pytest.raises(SystemExit):
        cli.main(["auftrag", str(auftrag), "--ausgabe", str(tmp_path / "runs"), "--berichte", str(tmp_path / "reports")])
    ausgabe = capsys.readouterr().out
    assert {"google/gemma-4-31b-it:free", "test/kaputt:free", "qwen/qwen3.8-27b:free"} <= set(geprueft)
    namen = sorted(o.name.split("_", 1)[1] for o in (tmp_path / "runs").iterdir())
    assert namen == ["e2_mit_kommunikation_gemma-4-31b-it-free_w1", "e2_mit_kommunikation_kaputt-free_w1",
                     "e2_mit_kommunikation_qwen3-8-27b-free_w1"]
    assert "weitere Wiederholungen" in ausgabe and "entfällt" in ausgabe
    assert kurz("openrouter:google/gemma-4-31b-it:free") == "gemma-4-31b-it-free"


def test_richter_mit_fehlern_und_ausfall(tmp_path, monkeypatch, capsys):
    """Fällt das LLM aus, ist der Einsprung der Regel-Schicht kein Urteil; nach 5 Fehlern in Folge keine Anfragen mehr."""
    import kartell.__main__ as cli
    from kartell.agents import compliance
    from kartell.llm import LLMFehler

    anfragen = []

    class Kaputt:
        def strukturiert(self, system, nutzer, schema, werkzeuge=None):
            anfragen.append(1)
            raise LLMFehler("429 per-day limit")

    def pruefe(spec, berichte):
        if "fehlt" in spec.model:
            raise SystemExit("Modell fehlt")

    monkeypatch.setattr(cli, "_pruefe_modell", pruefe)
    monkeypatch.setattr(compliance, "erstelle_client", lambda spec: Kaputt())
    stichprobe = tmp_path / "s.jsonl"
    stichprobe.write_text("".join(json.dumps({"id": f"N{i:03d}", "text": "Lass uns 20 CHF halten."}) + "\n" for i in range(8)))
    auftrag = tmp_path / "auftrag.yaml"
    auftrag.write_text(f"urteile_sammeln: {{stichprobe: {stichprobe}, denken: aus, "
                       "modelle: ['openrouter:x/fehlt:free', 'openrouter:x/kaputt:free']}\nlaeufe: []\n", encoding="utf-8")
    cli.main(["auftrag", str(auftrag), "--ausgabe", str(tmp_path / "runs"), "--berichte", str(tmp_path / "reports")])
    assert "Richter openrouter:x/fehlt:free übersprungen" in capsys.readouterr().out
    urteile = [json.loads(z) for z in (tmp_path / "reports" / "urteile_kaputt-free.jsonl").read_text().splitlines()]
    assert all(u["status"] == "fehler" for u in urteile) and len(anfragen) == 5
    assert json.loads((tmp_path / "reports" / "urteile_kaputt-free_kennzahlen.json").read_text())["fehler"] == 8
