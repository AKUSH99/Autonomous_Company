"""Prüft, dass die Backends korrekte Anfragen bauen – gegen einen simulierten HTTP-Server, ohne API-Schlüssel."""
import json

import anthropic
import httpx2
import openai

from kartell.agents.schemas import PreisEntscheid
from kartell.config import LLMSpec
from kartell.llm.anthropic_backend import AnthropicClient
from kartell.llm.openai_compat import OpenAICompatClient

ANTWORT = {"beobachtungen": "stabil", "plan": "halten", "erkenntnisse": "keine", "preis": 17.5}


def _anthropic_mit(aufnahme: list):
    def handler(request):
        aufnahme.append({"url": str(request.url), "headers": dict(request.headers), "body": json.loads(request.content)})
        return httpx2.Response(200, json={
            "id": "msg_test", "type": "message", "role": "assistant", "model": "claude-opus-5",
            "content": [{"type": "text", "text": json.dumps(ANTWORT)}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 120, "output_tokens": 30},
        })
    return anthropic.Anthropic(api_key="test", http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)))


def test_anthropic_strukturierte_ausgabe_und_refusal_fallback():
    aufnahme = []
    c = AnthropicClient(LLMSpec(provider="anthropic", model="claude-opus-5"), client=_anthropic_mit(aufnahme))
    a = c.strukturiert("System", "Nutzer", PreisEntscheid)
    assert a.objekt.preis == 17.5 and a.input_tokens == 120
    body, headers = aufnahme[0]["body"], aufnahme[0]["headers"]
    assert body["model"] == "claude-opus-5" and body["system"] == "System"
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert body["fallbacks"] == "default" and "server-side-fallback-2026-07-01" in headers["anthropic-beta"]


def test_anthropic_effort_und_format_gemeinsam():
    aufnahme = []
    c = AnthropicClient(LLMSpec(provider="anthropic", model="claude-opus-5", effort="medium"), client=_anthropic_mit(aufnahme))
    c.strukturiert("S", "N", PreisEntscheid)
    oc = aufnahme[0]["body"]["output_config"]
    assert oc["effort"] == "medium" and oc["format"]["type"] == "json_schema"


def test_anthropic_ohne_fallback_fuer_andere_modelle():
    aufnahme = []
    c = AnthropicClient(LLMSpec(provider="anthropic", model="claude-haiku-4-5", effort=None), client=_anthropic_mit(aufnahme))
    c.strukturiert("S", "N", PreisEntscheid)
    assert "fallbacks" not in aufnahme[0]["body"]


def test_openai_compat_parst_json_auch_ohne_schema_support():
    aufrufe = []

    def handler(request):
        body = json.loads(request.content)
        aufrufe.append(body)
        if "response_format" in body:  # Server ohne JSON-Schema-Unterstützung
            return httpx2.Response(400, json={"error": {"message": "response_format not supported"}})
        text = "Hier mein Entscheid:\n```json\n" + json.dumps(ANTWORT) + "\n```"
        return httpx2.Response(200, json={
            "id": "c1", "object": "chat.completion", "created": 0, "model": "apertus",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": text}}],
            "usage": {"prompt_tokens": 90, "completion_tokens": 25, "total_tokens": 115},
        })

    client = openai.OpenAI(api_key="x", base_url="http://test/v1", max_retries=0,
                           http_client=openai.DefaultHttpxClient(transport=httpx2.MockTransport(handler)))
    c = OpenAICompatClient(LLMSpec(provider="openai_compat", model="apertus", base_url="http://test/v1"), client=client)
    a = c.strukturiert("S", "N", PreisEntscheid)
    assert a.objekt.preis == 17.5
    assert "response_format" in aufrufe[0] and "response_format" not in aufrufe[1]


def test_openai_compat_uebernimmt_modell_und_max_tokens_der_voreinstellung():
    from kartell.config import VOREINSTELLUNGEN
    aufrufe = []

    def handler(request):
        aufrufe.append(json.loads(request.content))
        return httpx2.Response(200, json={
            "id": "c1", "object": "chat.completion", "created": 0, "model": "deepseek-flash",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps(ANTWORT)}}],
            "usage": {"prompt_tokens": 90, "completion_tokens": 25, "total_tokens": 115},
        })

    client = openai.OpenAI(api_key="x", base_url="http://test/v1", max_retries=0,
                           http_client=openai.DefaultHttpxClient(transport=httpx2.MockTransport(handler)))
    a = OpenAICompatClient(VOREINSTELLUNGEN["deepseek"], client=client).strukturiert("S", "N", PreisEntscheid)
    assert a.objekt.preis == 17.5 and a.input_tokens == 90
    assert aufrufe[0]["model"] == "deepseek-flash" and aufrufe[0]["max_tokens"] == 8000
    assert aufrufe[0]["response_format"]["type"] == "json_schema"
    assert aufrufe[0]["thinking"] == {"type": "disabled"}  # DeepSeek-Denkmodus aus (extra_body)


def test_openai_compat_abgeschnittene_antwort_meldet_ursache_und_tokens():
    import pytest

    from kartell.llm import LLMFehler
    aufrufe = []

    def handler(request):
        aufrufe.append(json.loads(request.content))
        return httpx2.Response(200, json={
            "id": "c1", "object": "chat.completion", "created": 0, "model": "m",
            "choices": [{"index": 0, "finish_reason": "length", "message": {"role": "assistant", "content": ""}}],
            "usage": {"prompt_tokens": 900, "completion_tokens": 4000, "total_tokens": 4900},
        })

    client = openai.OpenAI(api_key="x", base_url="http://test/v1", max_retries=0,
                           http_client=openai.DefaultHttpxClient(transport=httpx2.MockTransport(handler)))
    c = OpenAICompatClient(LLMSpec(provider="openai_compat", model="m", base_url="http://test/v1", max_tokens=4000), client=client)
    with pytest.raises(LLMFehler, match="abgeschnitten") as fehler:
        c.strukturiert("S", "N", PreisEntscheid)
    assert len(aufrufe) == 1  # keine sinnlose Wiederholung
    assert (fehler.value.input_tokens, fehler.value.output_tokens) == (900, 4000)  # Kosten bleiben sichtbar


def test_taktbremse_haelt_abstand(monkeypatch):
    from kartell.llm import openai_compat
    wartezeiten = []
    monkeypatch.setattr(openai_compat.time, "sleep", lambda s: wartezeiten.append(round(s, 1)))
    monkeypatch.setattr(openai_compat.time, "monotonic", lambda: 100.0)
    openai_compat._NAECHSTE_ANFRAGE.clear()
    for _ in range(3):
        openai_compat._warte_auf_takt("https://openrouter.ai/api/v1", 20)
    assert wartezeiten == [3.0, 6.0]  # erste Anfrage sofort, dann je 3 s Abstand


def test_gratismodelle_bekommen_taktbremse():
    from kartell.config import voreinstellung
    assert voreinstellung("openrouter:meta-llama/llama-3.3-70b-instruct:free").anfragen_pro_minute == 16
    assert voreinstellung("openrouter:meta-llama/llama-3.3-70b-instruct").anfragen_pro_minute is None
    assert voreinstellung("deepseek").anfragen_pro_minute is None


def _gratis_client(antworten, aufrufe):
    antworten = iter(antworten)

    def handler(request):
        aufrufe.append(json.loads(request.content))
        status, koerper = next(antworten)
        return httpx2.Response(status, json=koerper)

    client = openai.OpenAI(api_key="x", base_url="http://test/v1", max_retries=0,
                           http_client=openai.DefaultHttpxClient(transport=httpx2.MockTransport(handler)))
    return OpenAICompatClient(LLMSpec(provider="openai_compat", model="m:free", base_url="http://test/v1", anfragen_pro_minute=600),
                              client=client)


_GUELTIG = {"id": "c1", "object": "chat.completion", "created": 0, "model": "m", "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": '{"beobachtungen": "b", "plan": "p", "erkenntnisse": "e", "preis": 17.5}'}}]}
_UEBERLASTET = {"error": {"message": "m:free is temporarily rate-limited upstream. Please retry shortly", "code": 429}}


def test_gratismodell_wartet_bei_ueberlastung(monkeypatch):
    from kartell.llm import openai_compat
    pausen, aufrufe = [], []
    monkeypatch.setattr(openai_compat.time, "sleep", lambda s: pausen.append(s))
    c = _gratis_client([(429, _UEBERLASTET), (429, _UEBERLASTET), (200, _GUELTIG)], aufrufe)
    assert c.strukturiert("S", "N", PreisEntscheid).objekt.preis == 17.5
    assert len(aufrufe) == 3 and [p for p in pausen if p >= 1] == [20, 45]


def test_gratismodell_tageslimit_und_leere_antwort(monkeypatch):
    import pytest

    from kartell.llm import LLMFehler, openai_compat
    monkeypatch.setattr(openai_compat.time, "sleep", lambda s: None)
    aufrufe = []
    tageslimit = {"error": {"message": "Rate limit exceeded: free-models-per-day", "code": 429}}
    with pytest.raises(LLMFehler, match="per-day"):
        _gratis_client([(429, tageslimit)], aufrufe).strukturiert("S", "N", PreisEntscheid)
    assert len(aufrufe) == 1  # Tageslimit: sofort aufgeben, keine weiteren Anfragen verbrennen
    leer = {"id": "c1", "object": "chat.completion", "created": 0, "model": "m", "choices": None, "error": {"message": "kaputt"}}
    aufrufe = []
    assert _gratis_client([(200, leer), (200, _GUELTIG)], aufrufe).strukturiert("S", "N", PreisEntscheid).objekt.preis == 17.5
    assert len(aufrufe) == 2  # leere Antwort: einmal wiederholt
    with pytest.raises(LLMFehler, match="leere Antwort"):
        _gratis_client([(200, leer), (200, leer)], []).strukturiert("S", "N", PreisEntscheid)


def test_denkmodus_je_lauf():
    import pytest

    from kartell.config import lade_config, mit_denken, mit_modell
    cfg = mit_modell(lade_config("experiments/e2_mit_kommunikation.yaml"), "deepseek")
    aus = mit_denken(cfg, "aus")
    assert aus.agenten.llm.extra_body == {"thinking": {"type": "disabled"}, "reasoning": {"enabled": False}}
    assert mit_denken(aus, "standard").agenten.llm.extra_body == {"thinking": {"type": "disabled"}}
    assert mit_denken(cfg, "niedrig").agenten.llm.extra_body["reasoning"] == {"effort": "low"}
    with pytest.raises(ValueError):
        mit_denken(cfg, "maximal")
