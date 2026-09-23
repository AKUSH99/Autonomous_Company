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
