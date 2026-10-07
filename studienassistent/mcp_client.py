"""MCP-Client: Der Agent holt seine Werkzeuge über das Model Context Protocol statt sie direkt aufzurufen.

Verbunden wird mit dem eigenen MCP-Server (mcp_server.py) im selben Prozess, über den In-Memory-Transport des
MCP-SDK: gleiches Protokoll (Werkzeugliste, Aufrufe, Fehler als JSON-RPC), aber ohne Netz und ohne die Unterlagen
ein zweites Mal zu laden. Jedes MCP-Werkzeug wird zu einem LangChain-Werkzeug, das LangGraph wie gewohnt aufruft.

Das MCP-SDK arbeitet asynchron, der Agent synchron: Die Verbindung lebt deshalb in einer eigenen Ereignisschleife
in einem Hintergrund-Thread, die Aufrufe werden dorthin übergeben (auch aus mehreren Chat-Sitzungen gleichzeitig).
"""
from __future__ import annotations

import asyncio
import threading

from langchain_core.tools import StructuredTool

ZEITLIMIT_SEKUNDEN = 120


class MCPWerkzeuge:
    def __init__(self, server):
        self._schleife = asyncio.new_event_loop()
        threading.Thread(target=self._schleife.run_forever, name="mcp-client", daemon=True).start()
        bereit = threading.Event()
        # Öffnen und Schliessen der Verbindung müssen in derselben Aufgabe passieren (anyio): sie lebt in _halten
        self._verbindung = asyncio.run_coroutine_threadsafe(self._halten(server, bereit), self._schleife)
        if not bereit.wait(ZEITLIMIT_SEKUNDEN):
            raise TimeoutError("MCP-Server antwortet nicht")
        if self._verbindung.done():
            self._verbindung.result()  # Fehler beim Verbinden sichtbar machen
        self.werkzeuge = [self._als_langchain(t) for t in self._ausfuehren(self._client.list_tools()).tools]

    async def _halten(self, server, bereit: threading.Event) -> None:
        from mcp import Client
        self._ende = asyncio.Event()
        try:
            async with Client(server) as client:
                self._client = client
                bereit.set()
                await self._ende.wait()
        finally:
            bereit.set()

    def _ausfuehren(self, koroutine):
        return asyncio.run_coroutine_threadsafe(koroutine, self._schleife).result(timeout=ZEITLIMIT_SEKUNDEN)

    def _als_langchain(self, werkzeug) -> StructuredTool:
        def aufrufen(**argumente) -> str:
            ergebnis = self._ausfuehren(self._client.call_tool(werkzeug.name, argumente))
            text = "\n".join(t for t in (getattr(c, "text", None) for c in ergebnis.content) if t)
            return f"Fehler im Werkzeug {werkzeug.name}: {text}" if ergebnis.is_error else text

        return StructuredTool.from_function(func=aufrufen, name=werkzeug.name, description=werkzeug.description or "",
                                            args_schema=werkzeug.input_schema)

    def schliessen(self) -> None:
        self._schleife.call_soon_threadsafe(self._ende.set)
        self._verbindung.result(timeout=ZEITLIMIT_SEKUNDEN)
        self._schleife.call_soon_threadsafe(self._schleife.stop)
