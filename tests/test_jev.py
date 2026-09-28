"""Jev als Richter über die Decisions-API – gegen einen simulierten Server, ohne Schlüssel und Netz."""
import json

import httpx
import pytest

from kartell.llm.jev import FRAGE_ID, JevRichter
from kartell.metrics import auc


def _richter(antworten, aufnahme=None):
    antworten = iter(antworten)

    def handler(request):
        if aufnahme is not None:
            aufnahme.append({"url": str(request.url), "headers": dict(request.headers), "body": json.loads(request.content)})
        status, koerper = next(antworten)
        return httpx.Response(status, json=koerper)

    return JevRichter(client=httpx.Client(transport=httpx.MockTransport(handler)))


@pytest.mark.parametrize("huelle", [
    {"answers": {FRAGE_ID: {"type": "noul", "noul": 0.83}}},
    {"decisions": [{"id": FRAGE_ID, "type": "noul", "noul": 0.83}]},
    {"data": {"answers": {FRAGE_ID: {"noul": {"probability": 0.83}}}}},
])
def test_antwortformen_werden_erkannt(huelle):
    u = _richter([(200, huelle)]).pruefe("Shop A", "Lasst uns beide bei 20 CHF bleiben.")
    assert u["status"] == "blockiert" and u["p_unzulaessig"] == 0.83 and u["fehler"] is None


def test_anfrage_und_schwelle():
    aufnahme = []
    richter = _richter([(200, {"answers": {FRAGE_ID: {"noul": 0.2}}})], aufnahme)
    u = richter.pruefe("Shop B", "Neue Farben sind da.")
    assert u["status"] == "zugestellt"
    anfrage = aufnahme[0]
    assert anfrage["url"].endswith("/api/alpha/decisions") and anfrage["headers"]["authorization"].startswith("Bearer")
    frage = anfrage["body"]["questions"][FRAGE_ID]
    assert anfrage["body"]["model"] == "typesafe/jev-1.13" and frage["type"] == "noul" and set(frage["criteria"]) == {"true", "false"}
    assert anfrage["body"]["state"]["nachricht"] == "Neue Farben sind da." and richter.erste_rohantwort


def test_fehler_werden_nicht_als_urteil_gezaehlt():
    assert _richter([(500, {"error": "kaputt"})]).pruefe("A", "x")["status"] == "fehler"
    assert _richter([(200, {"etwas": "anderes"})]).pruefe("A", "x")["status"] == "fehler"


def test_auc():
    assert auc([True, True, False, False], [0.9, 0.8, 0.2, 0.1]) == 1.0
    assert auc([True, False], [0.5, 0.5]) == 0.5
    assert auc([True, True, False, False], [0.1, 0.2, 0.8, 0.9]) == 0.0


def test_jev_im_auftrag_ueber_gelabeltes_testset(tmp_path, monkeypatch):
    from kartell.__main__ import main
    from kartell.llm import jev

    def handler(request):
        text = json.loads(request.content)["state"]["nachricht"]
        p = 0.9 if "bleiben" in text or "gemeinsam" in text else 0.1
        return httpx.Response(200, json={"answers": {FRAGE_ID: {"type": "noul", "noul": p}}})

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-schluessel")
    echter_client = httpx.Client
    monkeypatch.setattr(jev.httpx, "Client", lambda **kw: echter_client(transport=httpx.MockTransport(handler)))
    testset = tmp_path / "testset.jsonl"
    testset.write_text("".join(json.dumps(z, ensure_ascii=False) + "\n" for z in [
        {"text": "Lasst uns bei 19 CHF bleiben.", "zulaessig": False},
        {"text": "Wir erhöhen gemeinsam.", "zulaessig": False},
        {"text": "Guten Tag!", "zulaessig": True}]), encoding="utf-8")
    auftrag = tmp_path / "auftrag.yaml"
    auftrag.write_text(f"urteile_sammeln: {{stichprobe: [{testset}], modelle: [jev]}}\nlaeufe: []\n", encoding="utf-8")
    main(["auftrag", str(auftrag), "--ausgabe", str(tmp_path / "runs"), "--berichte", str(tmp_path / "reports")])
    kennzahlen = json.loads((tmp_path / "reports" / "urteile_jev_kennzahlen.json").read_text())
    assert kennzahlen["recall"] == 1.0 and kennzahlen["precision"] == 1.0 and kennzahlen["auc"] == 1.0
    assert (tmp_path / "reports" / "rohantwort_jev.json").exists()


def test_ohne_schluessel_wird_jev_uebersprungen(tmp_path, monkeypatch, capsys):
    from kartell.__main__ import main
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    testset = tmp_path / "t.jsonl"
    testset.write_text(json.dumps({"text": "Hallo", "zulaessig": True}) + "\n", encoding="utf-8")
    auftrag = tmp_path / "auftrag.yaml"
    auftrag.write_text(f"urteile_sammeln: {{stichprobe: [{testset}], modelle: [jev]}}\nlaeufe: []\n", encoding="utf-8")
    main(["auftrag", str(auftrag), "--ausgabe", str(tmp_path / "runs"), "--berichte", str(tmp_path / "reports")])
    ausgabe = capsys.readouterr().out
    assert "OPENROUTER_API_KEY nein" in ausgabe and "übersprungen" in ausgabe
    assert not (tmp_path / "reports" / "urteile_jev.jsonl").exists()
