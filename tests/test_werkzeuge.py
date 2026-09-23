"""Tool-Use: Nachfrage-Schätzer und Werkzeug-Schleifen beider Backends (gegen simulierte Server, ohne API-Schlüssel)."""
import json

import anthropic
import httpx2
import openai

from kartell.agents.pricing import LLMPreisAgent
from kartell.agents.schemas import PreisEntscheid
from kartell.agents.werkzeuge import nachfrage_schaetzer
from kartell.config import AgentSpec, ExperimentConfig, LLMSpec
from kartell.graph import Simulation
from kartell.llm import LLMAntwort
from kartell.llm.anthropic_backend import AnthropicClient
from kartell.llm.openai_compat import OpenAICompatClient
from kartell.market import LogitMarkt, MarktParameter

ANTWORT = {"beobachtungen": "b", "plan": "p", "erkenntnisse": "e", "preis": 16.0}


def _verlauf(preise_a, preise_b):
    markt = LogitMarkt(MarktParameter(firmen=2, alpha=10, beta=100))
    return [{"preise": {"Shop A": a, "Shop B": b}, "mengen": dict(zip(["Shop A", "Shop B"], markt.mengen([a, b])))}
            for a, b in zip(preise_a, preise_b)]


def test_schaetzer_nutzt_nur_eigene_historie_und_trifft_die_richtung():
    w = nachfrage_schaetzer(_verlauf([15, 16, 17, 18, 16.5, 15.5], [16, 15, 17.5, 16.5, 18, 15]), "Shop A", 10.0)
    billig, _ = w.ausfuehren({"eigener_preis": 15.0})
    teuer, _ = w.ausfuehren({"eigener_preis": 18.0})
    billig, teuer = json.loads(billig), json.loads(teuer)
    assert billig["geschaetzte_menge"] > teuer["geschaetzte_menge"] and billig["r2"] > 0.9
    wahr = LogitMarkt(MarktParameter(firmen=2, alpha=10, beta=100)).mengen([15.0, billig["angenommener_konkurrenzpreis"]])[0]
    assert abs(billig["geschaetzte_menge"] - wahr) / wahr < 0.1
    zu_wenig, _ = nachfrage_schaetzer(_verlauf([15], [16]), "Shop A", 10.0).ausfuehren({"eigener_preis": 15})
    assert "Zu wenige Runden" in zu_wenig
    fehler_text, fehler = w.ausfuehren({"eigener_preis": "viel"})
    assert fehler and fehler_text.startswith("Fehler")


def test_openai_compat_werkzeug_schleife():
    aufrufe = []

    def handler(request):
        body = json.loads(request.content)
        aufrufe.append(body)
        if len(aufrufe) == 1:
            nachricht = {"role": "assistant", "content": None, "tool_calls": [{"id": "t1", "type": "function",
                         "function": {"name": "nachfrage_schaetzen", "arguments": json.dumps({"eigener_preis": 16})}}]}
            grund = "tool_calls"
        else:
            nachricht, grund = {"role": "assistant", "content": json.dumps(ANTWORT)}, "stop"
        return httpx2.Response(200, json={"id": "c", "object": "chat.completion", "created": 0, "model": "m",
                                           "choices": [{"index": 0, "finish_reason": grund, "message": nachricht}],
                                           "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}})

    client = openai.OpenAI(api_key="x", base_url="http://test/v1", max_retries=0,
                           http_client=openai.DefaultHttpxClient(transport=httpx2.MockTransport(handler)))
    w = nachfrage_schaetzer(_verlauf([15, 16, 17, 18], [16, 15, 17.5, 16.5]), "Shop A", 10.0)
    a = OpenAICompatClient(LLMSpec(provider="openai_compat", model="m", base_url="http://test/v1"), client=client) \
        .strukturiert("S", "N", PreisEntscheid, [w])
    assert a.objekt.preis == 16.0 and a.input_tokens == 200
    assert aufrufe[0]["tools"][0]["function"]["name"] == "nachfrage_schaetzen" and "response_format" not in aufrufe[0]
    werkzeug_antwort = aufrufe[1]["messages"][-1]
    assert werkzeug_antwort["role"] == "tool" and werkzeug_antwort["tool_call_id"] == "t1"
    assert "geschaetzte_menge" in werkzeug_antwort["content"] and a.werkzeug_aufrufe[0]["name"] == "nachfrage_schaetzen"


def test_anthropic_werkzeug_schleife():
    aufrufe = []

    def handler(request):
        body = json.loads(request.content)
        aufrufe.append(body)
        if len(aufrufe) == 1:
            inhalt, grund = [{"type": "tool_use", "id": "toolu_1", "name": "nachfrage_schaetzen", "input": {"eigener_preis": 17}}], "tool_use"
        else:
            inhalt, grund = [{"type": "text", "text": json.dumps(ANTWORT)}], "end_turn"
        return httpx2.Response(200, json={"id": "msg", "type": "message", "role": "assistant", "model": "claude-opus-5",
                                           "content": inhalt, "stop_reason": grund, "stop_sequence": None,
                                           "usage": {"input_tokens": 300, "output_tokens": 40}})

    client = anthropic.Anthropic(api_key="test", http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)))
    w = nachfrage_schaetzer(_verlauf([15, 16, 17, 18], [16, 15, 17.5, 16.5]), "Shop A", 10.0)
    a = AnthropicClient(LLMSpec(provider="anthropic", model="claude-opus-5"), client=client).strukturiert("S", "N", PreisEntscheid, [w])
    assert a.objekt.preis == 16.0 and (a.input_tokens, a.output_tokens) == (600, 80)
    assert aufrufe[0]["tools"][0]["name"] == "nachfrage_schaetzen" and aufrufe[0]["tool_choice"] == {"type": "auto"}
    ergebnis = aufrufe[1]["messages"][-1]["content"][0]
    assert ergebnis["type"] == "tool_result" and ergebnis["tool_use_id"] == "toolu_1" and "geschaetzte_menge" in ergebnis["content"]
    assert aufrufe[1]["messages"][1]["content"][0]["type"] == "tool_use"


def test_preisagent_bekommt_werkzeug_nur_wenn_konfiguriert():
    class Merker:
        name = "fake"

        def __init__(self):
            self.werkzeuge = []

        def strukturiert(self, system, nutzer, schema, werkzeuge=None):
            self.werkzeuge.append([w.name for w in werkzeuge or []])
            return LLMAntwort(PreisEntscheid(**ANTWORT), 10, 5, werkzeug_aufrufe=[{"name": "nachfrage_schaetzen"}] if werkzeuge else [])

    for werkzeuge, erwartet in (([], []), (["nachfrage_schaetzen"], ["nachfrage_schaetzen"])):
        cfg = ExperimentConfig(name="t", runden=2, agenten={"werkzeuge": werkzeuge})
        llm = Merker()
        agenten = [LLMPreisAgent(AgentSpec(name=n, llm=LLMSpec()), cfg, llm, 10.0) for n in ("Shop A", "Shop B")]
        verlauf = Simulation(cfg, agenten=agenten).starte()
        assert llm.werkzeuge[0] == erwartet
        assert ("werkzeug_aufrufe" in verlauf[0]["entscheide"]["Shop A"]) == bool(werkzeuge)
        assert ("nachfrage_schaetzen" in agenten[0].system) == bool(werkzeuge)
