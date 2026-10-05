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
