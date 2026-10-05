"""Der Agent als LangGraph-Graph.

    START → pruefen ──(erlaubt)──▶ agent ⇄ werkzeuge
              │                      │
              └──(nicht erlaubt)──▶ END ◀── (fertige Antwort)

- pruefen: Guardrail – Manipulationsversuche, Themen ohne Studienbezug und «schreib meine Abgabe» werden abgelehnt.
- agent: das Sprachmodell mit drei Werkzeugen (Unterlagen durchsuchen, Fristen, Module); es entscheidet selbst, welches
  Werkzeug es braucht, und kann mehrmals suchen.
- werkzeuge: führt die Aufrufe aus und gibt die Treffer mit Quellen zurück.
Gedächtnis: Der Checkpointer speichert den Gesprächsverlauf pro `thread_id`, so funktionieren Rückfragen.
"""
from __future__ import annotations

import datetime as dt

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

from . import prompts
from .fristen import Fristen
from .suche import Suche
from .werkzeuge import erstelle_werkzeuge

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


class Pruefung(BaseModel):
    erlaubt: bool = Field(description="True, wenn der Assistent auf die Nachricht eingehen darf")
    grund: str = Field(description="kurze Begründung, ein Satz")


class Zustand(MessagesState):
    erlaubt: bool


def baue_agent(modell, suche: Suche, fristen: Fristen, heute: dt.date | None = None, gedaechtnis=None):
    """Kompilierter Graph. `modell`: ein LangChain-Chatmodell mit Werkzeug-Unterstützung (z. B. konfig.chat_modell())."""
    werkzeuge = erstelle_werkzeuge(suche, fristen)
    mit_werkzeugen = modell.bind_tools(werkzeuge)
    pruefer = modell.with_structured_output(Pruefung)

    def system() -> SystemMessage:
        tag = heute or dt.date.today()
        return SystemMessage(prompts.SYSTEM.format(heute=tag.isoformat(), wochentag=WOCHENTAGE[tag.weekday()],
                                                   module=", ".join(suche.module())))

    def pruefen(zustand: Zustand) -> dict:
        try:
            ergebnis = pruefer.invoke([SystemMessage(prompts.PRUEFEN), zustand["messages"][-1]])
        except Exception:  # noqa: BLE001 – fällt die Prüfung aus, entscheidet der Agent mit seinen eigenen Regeln
            return {"erlaubt": True}
        if ergebnis.erlaubt:
            return {"erlaubt": True}
        return {"erlaubt": False, "messages": [AIMessage(prompts.ABLEHNUNG.format(grund=ergebnis.grund))]}

    def agent(zustand: Zustand) -> dict:
        return {"messages": [mit_werkzeugen.invoke([system()] + zustand["messages"])]}

    g = StateGraph(Zustand)
    g.add_node("pruefen", pruefen)
    g.add_node("agent", agent)
    g.add_node("werkzeuge", ToolNode(werkzeuge))
    g.add_edge(START, "pruefen")
    g.add_conditional_edges("pruefen", lambda z: "agent" if z["erlaubt"] else END, ["agent", END])
    g.add_conditional_edges("agent", tools_condition, {"tools": "werkzeuge", END: END})
    g.add_edge("werkzeuge", "agent")
    return g.compile(checkpointer=gedaechtnis or MemorySaver())


def fragen(graph, text: str, thread_id: str = "standard") -> dict:
    """Eine Frage stellen; gibt Antwort und die genutzten Quellen-Auszüge zurück."""
    vorher = len(graph.get_state({"configurable": {"thread_id": thread_id}}).values.get("messages", []))
    ende = graph.invoke({"messages": [("user", text)]}, config={"configurable": {"thread_id": thread_id}, "recursion_limit": 12})
    neu = ende["messages"][vorher:]
    quellen = [m.content for m in neu if getattr(m, "type", "") == "tool"]
    aufrufe = [c["name"] for m in neu if getattr(m, "tool_calls", None) for c in m.tool_calls]
    return {"antwort": ende["messages"][-1].content, "quellen": quellen, "werkzeuge": aufrufe,
            "abgelehnt": not ende.get("erlaubt", True)}
