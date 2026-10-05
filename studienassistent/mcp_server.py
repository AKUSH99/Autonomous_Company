"""MCP-Server: die Werkzeuge des Studienassistenten für beliebige MCP-Clients (Claude Desktop, Claude Code, …).

    python -m studienassistent mcp

Der Server nutzt dieselben Werkzeuge wie der Agent – wer einen anderen Client oder ein anderes Modell verwenden will,
bekommt Suche, Fristen und Modulliste über ein Standardprotokoll, ohne den Code zu kennen.
"""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from .fristen import Fristen
from .suche import Suche
from .werkzeuge import erstelle_werkzeuge


def erstelle_server(suche: Suche, fristen: Fristen) -> MCPServer:
    server = MCPServer(name="studienassistent",
                       instructions="Kursunterlagen, Fristen und Module des BAI-Studiums an der FHNW (HS 2026). "
                                    "Antworten immer mit der gelieferten Quelle belegen.")
    for werkzeug in erstelle_werkzeuge(suche, fristen):
        server.add_tool(werkzeug.func, name=werkzeug.name, description=werkzeug.description)

    @server.resource("studienassistent://module", description="Module mit eingelesenen Unterlagen")
    def module() -> str:
        return "\n".join(suche.module())

    return server
