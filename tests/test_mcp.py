"""MCP-Server: dieselben Werkzeuge über das Protokoll aufrufen (im selben Prozess, ohne Netz)."""
import asyncio
from pathlib import Path

import pytest

pytest.importorskip("mcp.server.mcpserver")

from studienassistent.einlesen import einlesen  # noqa: E402
from studienassistent.fristen import Fristen  # noqa: E402
from studienassistent.mcp_server import erstelle_server  # noqa: E402
from studienassistent.suche import Suche  # noqa: E402

DATEN = Path(__file__).parent / "daten"


def test_werkzeuge_ueber_mcp():
    from mcp import Client
    server = erstelle_server(Suche(einlesen([DATEN])), Fristen([{"date": "2026-11-23", "sort": "2026-11-23",
                                                                  "module": "Generative KI", "title": "Präsentation"}]))

    async def ablauf():
        async with Client(server) as client:
            namen = {t.name for t in (await client.list_tools()).tools}
            suche = await client.call_tool("unterlagen_durchsuchen", {"frage": "Abschlusspräsentation"})
            fristen = await client.call_tool("fristen_anzeigen", {"ab": "2026-11-01"})
            return namen, suche.content[0].text, fristen.content[0].text

    namen, suche, fristen = asyncio.run(ablauf())
    assert namen == {"unterlagen_durchsuchen", "fristen_anzeigen", "module_auflisten"}
    assert "semesterprogramm.md" in suche and "Präsentation" in fristen


def test_agent_als_mcp_client():
    """Der Agent ruft seine Werkzeuge über das MCP-Protokoll auf und bekommt dieselben Treffer wie direkt."""
    from langchain_core.messages import AIMessage

    from studienassistent.agent import baue_agent, fragen
    from studienassistent.mcp_client import MCPWerkzeuge
    from test_studienassistent import FakeModell

    suche, fristen = Suche(einlesen([DATEN])), Fristen([])
    mcp = MCPWerkzeuge(erstelle_server(suche, fristen))
    try:
        assert {w.name for w in mcp.werkzeuge} == {"unterlagen_durchsuchen", "fristen_anzeigen", "module_auflisten"}
        modell = FakeModell(antworten=[
            AIMessage("", tool_calls=[{"name": "unterlagen_durchsuchen", "args": {"frage": "Abschlusspräsentation"}, "id": "1"}]),
            AIMessage("Am 23.11.2026 (Quelle: Generative KI · semesterprogramm.md)."),
        ], gesehen=[])
        r = fragen(baue_agent(modell, suche, fristen, werkzeuge=mcp.werkzeuge), "Wann ist die Präsentation?", "mcp")
        assert r["werkzeuge"] == ["unterlagen_durchsuchen"] and "semesterprogramm.md" in r["quellen"][0]
        direkt = next(w for w in __import__("studienassistent.werkzeuge", fromlist=["x"]).erstelle_werkzeuge(suche, fristen)
                      if w.name == "unterlagen_durchsuchen").invoke({"frage": "Abschlusspräsentation"})
        assert r["quellen"][0] == direkt  # über MCP kommt genau dasselbe an
    finally:
        mcp.schliessen()
