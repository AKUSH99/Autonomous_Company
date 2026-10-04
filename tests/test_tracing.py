"""LangSmith-Tracing: Läufe landen als Baum Graph → Knoten → LLM/Werkzeug, ohne dass etwas ins Netz geht."""
import json
from unittest import mock

import langsmith
from langsmith.run_helpers import tracing_context

from kartell.agents.pricing import LLMPreisAgent
from kartell.agents.schemas import KanalNachricht, PreisEntscheid
from kartell.config import AgentSpec, ExperimentConfig, LLMSpec
from kartell.graph import Simulation
from kartell.llm import LLMAntwort
from kartell.llm.base import fuehre_werkzeug_aus
from kartell.tracing import mit_tracing


class _SkriptLLM:
    name = "fake"

    def strukturiert(self, system, nutzer, schema, werkzeuge=None):
        if schema is PreisEntscheid:
            fuehre_werkzeug_aus([], "nachfrage_schaetzen", {"preis": 17.0}, [])
            return LLMAntwort(PreisEntscheid(beobachtungen="b", plan="p", erkenntnisse="e", preis=17.0), 50, 10)
        return LLMAntwort(KanalNachricht(ueberlegung="u", nachricht="Hallo"), 40, 5)


def _gesendete_laeufe(session: mock.MagicMock) -> dict[str, dict]:
    """Sammelt alle an LangSmith geschickten Läufe (POST anlegen, PATCH abschliessen) nach ID."""
    laeufe: dict[str, dict] = {}
    for aufruf in session.request.call_args_list:
        methode, url = aufruf.args[:2]
        daten = aufruf.kwargs.get("data")
        if "/runs" not in url or not daten:
            continue
        lauf = json.loads(daten)
        laeufe.setdefault(lauf.get("id") or url.rsplit("/", 1)[-1], {}).update(lauf)
    return laeufe


def test_ohne_tracing_bleibt_alles_lokal():
    session = mock.MagicMock()
    client = langsmith.Client(api_url="http://ls.test", api_key="x", session=session, auto_batch_tracing=False)
    with tracing_context(enabled=False, client=client):
        llm = mit_tracing(_SkriptLLM(), LLMSpec(model="m"))
        assert llm.strukturiert("s", "n", KanalNachricht).objekt.nachricht == "Hallo"
    assert not _gesendete_laeufe(session)


def test_llm_aufrufe_haengen_unter_ihrem_graph_knoten():
    session = mock.MagicMock()
    session.request.return_value.status_code = 200
    client = langsmith.Client(api_url="http://ls.test", api_key="x", session=session, auto_batch_tracing=False)
    cfg = ExperimentConfig(name="e2_test", runden=2, kommunikation={"aktiv": True})
    spec = LLMSpec(model="claude-test")
    agenten = [LLMPreisAgent(AgentSpec(name=n, llm=spec), cfg, mit_tracing(_SkriptLLM(), spec), 10.0)
               for n in ["Shop A", "Shop B"]]

    with tracing_context(enabled=True, client=client, project_name="test"):
        Simulation(cfg, seed=7, agenten=agenten).starte()
    client.flush()

    laeufe = _gesendete_laeufe(session)
    wurzel = [l for l in laeufe.values() if l.get("name") == "e2_test · seed 7"]
    assert len(wurzel) == 1 and "e2_test" in wurzel[0]["tags"]
    nach_name = lambda name: [l for l in laeufe.values() if l.get("name") == name]
    llm_laeufe = nach_name("llm:fake")
    assert len(llm_laeufe) == 2 * 2 * 2  # 2 Runden × 2 Shops × (Nachricht + Preis)
    knoten = {l["id"]: l["name"] for l in laeufe.values() if l.get("name") in ("kommunikation", "preisentscheid")}
    assert {knoten.get(l["parent_run_id"]) for l in llm_laeufe} == {"kommunikation", "preisentscheid"}
    preis = next(l for l in llm_laeufe if knoten[l["parent_run_id"]] == "preisentscheid" and l.get("outputs"))
    assert preis["outputs"]["usage_metadata"]["input_tokens"] == 50
    assert preis["extra"]["metadata"]["ls_model_name"] == "claude-test"
    werkzeug = nach_name("werkzeug:nachfrage_schaetzen")
    assert werkzeug and all(knoten.get(laeufe[w["parent_run_id"]]["parent_run_id"]) == "preisentscheid" for w in werkzeug)
