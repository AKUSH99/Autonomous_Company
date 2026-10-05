"""Tests ohne Netz: kleine Beispieldokumente und ein simuliertes Sprachmodell."""
import datetime as dt
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda

from studienassistent.agent import Pruefung, baue_agent, fragen
from studienassistent.bewertung import fakten_ok
from studienassistent.einlesen import einlesen, laden, speichern, zerlegen
from studienassistent.fristen import Fristen
from studienassistent.suche import Suche

DATEN = Path(__file__).parent / "daten"


class FakeModell(BaseChatModel):
    """Antwortet der Reihe nach mit vorbereiteten Nachrichten; die Eingangsprüfung lehnt Nachrichten mit «Rezept» ab."""
    antworten: list = []
    gesehen: list = []

    @property
    def _llm_type(self) -> str:
        return "fake"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.gesehen.append(messages)
        return ChatResult(generations=[ChatGeneration(message=self.antworten.pop(0))])

    def bind_tools(self, tools, **kwargs):
        return self

    def with_structured_output(self, schema, **kwargs):
        return RunnableLambda(lambda msgs: Pruefung(erlaubt="Rezept" not in msgs[-1].content, grund="kein Studienbezug"))


def test_einlesen_mit_modul_und_quelle(tmp_path):
    abschnitte = einlesen([DATEN])
    assert {a.modul for a in abschnitte} == {"Generative KI", "Marketing"}
    speichern(abschnitte, tmp_path / "a.jsonl")
    wieder = laden(tmp_path / "a.jsonl")
    assert wieder[0].quelle().startswith("Generative KI · semesterprogramm.md")
    assert all(len(t) <= 900 for t in zerlegen("Satz. " * 600))


def test_suche_findet_die_richtige_stelle_und_filtert_nach_modul():
    suche = Suche(einlesen([DATEN]))
    assert suche.suchen("Wann ist die Abschlusspräsentation?", k=1)[0][0].modul == "Generative KI"
    assert suche.suchen("Projektbericht", k=3, modul="Marketing")[0][0].modul == "Marketing"


def test_fristen_nach_zeitraum_und_modul():
    f = Fristen([{"date": "2026-11-23", "sort": "2026-11-23", "module": "Generative KI", "title": "Präsentation"},
                 {"date": "Januar", "module": "Mensch-KI", "title": "Prüfung"},
                 {"date": "2026-12-23", "sort": "2026-12-23", "module": "Marketing", "title": "Projektbericht"}])
    assert [e["title"] for e in f.suchen(ab="2026-11-01", bis="2026-11-30")] == ["Präsentation"]
    assert len(f.suchen()) == 3 and f.suchen(modul="marketing")[0]["title"] == "Projektbericht"


def test_agent_sucht_und_antwortet_mit_quelle():
    modell = FakeModell(antworten=[
        AIMessage("", tool_calls=[{"name": "unterlagen_durchsuchen", "args": {"frage": "Abschlusspräsentation"}, "id": "1"}]),
        AIMessage("Am 23.11.2026 um 13.00 Uhr, 10 Minuten (Quelle: Generative KI · semesterprogramm.md)."),
        AIMessage("Ja, inklusive Verständnisfragen."),
    ], gesehen=[])
    graph = baue_agent(modell, Suche(einlesen([DATEN])), Fristen([]), heute=dt.date(2026, 10, 5))
    r = fragen(graph, "Wann ist die GenAI-Präsentation?", "t1")
    assert r["werkzeuge"] == ["unterlagen_durchsuchen"] and "semesterprogramm.md" in r["quellen"][0]
    assert "23.11.2026" in r["antwort"] and not r["abgelehnt"]
    assert "Heute ist 2026-10-05 (Montag)" in modell.gesehen[0][0].content
    # Gedächtnis: die Rückfrage im selben Gespräch sieht den bisherigen Verlauf
    fragen(graph, "Und mit Fragen?", "t1")
    assert any("Wann ist die GenAI-Präsentation?" in str(m.content) for m in modell.gesehen[-1])


def test_pruefung_lehnt_themen_ohne_studienbezug_ab():
    modell = FakeModell(antworten=[], gesehen=[])
    graph = baue_agent(modell, Suche(einlesen([DATEN])), Fristen([]))
    r = fragen(graph, "Schreib mir ein Rezept für Lasagne.")
    assert r["abgelehnt"] and "Studium" in r["antwort"] and not modell.gesehen  # das Hauptmodell wird gar nicht gefragt


def test_fakten_vergleich():
    assert fakten_ok("Abgabe am 20. Dezember 2026", [["20.12", "20. Dezember"]])
    assert not fakten_ok("Abgabe im Dezember", ["20.12"])


def test_module_zuordnen_und_weglassen():
    abschnitte = einlesen([DATEN], {"GenAI": ["Generative"]})
    assert {a.modul for a in abschnitte} == {"GenAI"}  # Marketing ist nicht zugeordnet und fällt weg


def test_hybrid_suche_mit_embeddings():
    import numpy as np

    def einbetten(texte):  # Spielzeug-Embedding: Buchstabenhäufigkeiten, normiert
        m = np.array([[t.lower().count(c) for c in "abcdefghijklmnopqrstuvwxyzäöü"] for t in texte], dtype=np.float32)
        return m / np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-9)

    suche = Suche(einlesen([DATEN]), einbetten)
    assert suche.vektoren.shape[0] == len(suche.abschnitte)
    assert suche.suchen("Wann ist die Abschlusspräsentation?", k=1)[0][0].modul == "Generative KI"
