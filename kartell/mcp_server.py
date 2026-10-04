"""MCP-Server: Kartellrecht-Wissensbasis und Regel-Prüfung als Werkzeuge für beliebige MCP-Clients.

Start (stdio):  python -m kartell mcp
Nutzen lässt er sich auf zwei Wegen:
  1. Im System selbst: Mit `compliance.rag_ueber_mcp: true` holt die Compliance-Abteilung ihr Rechtswissen
     über MCP statt direkt aus dem Index – Agent und Wissensbasis sind dann über ein Protokoll entkoppelt.
     Das Suchverfahren (BM25 oder Hybrid, `compliance.retrieval`) gibt der Agent dem Server beim Start mit.
  2. Von aussen: Claude Desktop, Claude Code oder ein anderer MCP-Client kann die Wissensbasis durchsuchen und
     Nachrichten prüfen lassen, z. B. live in der Präsentation.
"""
from __future__ import annotations

import asyncio
import atexit
import json
import sys
import threading
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

from .agents.compliance import regel_pruefung
from .rag import Abschnitt, erstelle_retriever

STANDARD_WISSENSBASIS = Path(__file__).resolve().parent.parent / "knowledge" / "wettbewerbsrecht"


class Fundstelle(BaseModel):
    quelle: str
    titel: str
    text: str
    score: float


class Suchergebnis(BaseModel):
    treffer: list[Fundstelle]


class Regelbefund(BaseModel):
    treffer: list[str]
    punkte: int
    verdacht: bool
    kategorie: str


def erstelle_server(wissensbasis: str | Path | None = None, retrieval=None) -> MCPServer:
    ordner = Path(wissensbasis) if wissensbasis else STANDARD_WISSENSBASIS
    retriever = erstelle_retriever(ordner, retrieval)
    verfahren = "BM25" if retrieval is None or retrieval.verfahren == "bm25" else "Hybrid: BM25 + Embeddings + Reranker"
    server = MCPServer(
        name="kartellrecht",
        instructions="Vereinfachte Zusammenfassungen zu Schweizer und EU-Wettbewerbsrecht (KG, AEUV, Behördenpraxis) "
                     "für die Prüfung von Nachrichten zwischen Konkurrenten. Keine Rechtsberatung.",
    )

    @server.tool(description=f"Durchsucht die Wissensbasis zum Wettbewerbsrecht ({verfahren}) und liefert die passendsten Abschnitte.")
    def suche_wettbewerbsrecht(anfrage: str, top_k: int = 3) -> Suchergebnis:
        treffer = retriever.suche(anfrage, max(1, min(top_k, 10)))
        return Suchergebnis(treffer=[Fundstelle(quelle=a.quelle, titel=a.titel, text=a.text, score=s) for a, s in treffer])

    @server.tool(description="Prüft eine Nachricht mit der transparenten Regel-Schicht auf typische Kartell-Signale.")
    def pruefe_nachricht_regeln(text: str) -> Regelbefund:
        befund = regel_pruefung(text)
        return Regelbefund(**befund.als_dict(), kategorie=befund.kategorie)

    @server.resource("kartellrecht://quellen", description="Liste der Dokumente in der Wissensbasis")
    def quellen() -> str:
        return "\n".join(sorted(p.name for p in ordner.glob("*.md")))

    return server


class MCPRetriever:
    """Gleiche Schnittstelle wie BM25Retriever.suche, aber über einen MCP-Server als Unterprozess (stdio).

    Die MCP-Sitzung läuft in einem eigenen Event-Loop-Thread; Aufrufe aus den Agenten-Threads werden serialisiert.
    """

    def __init__(self, wissensbasis: str | Path | None = None, retrieval=None):
        from mcp import Client, StdioServerParameters
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True, name="mcp-client").start()
        argumente = ["-m", "kartell", "mcp"] + (["--wissensbasis", str(Path(wissensbasis).resolve())] if wissensbasis else [])
        if retrieval is not None and retrieval.verfahren != "bm25":
            argumente += ["--retrieval", retrieval.model_dump_json()]
        self._client = Client(StdioServerParameters(command=sys.executable, args=argumente,
                                                    cwd=str(Path(__file__).resolve().parent.parent)))
        self._sperre = asyncio.Lock()
        self._ausfuehren(self._client.__aenter__())
        atexit.register(self.schliessen)

    def _ausfuehren(self, koroutine, timeout: float = 60):
        return asyncio.run_coroutine_threadsafe(koroutine, self._loop).result(timeout)

    async def _aufruf(self, name: str, argumente: dict) -> dict:
        async with self._sperre:
            ergebnis = await self._client.call_tool(name, argumente)
        if getattr(ergebnis, "is_error", False):
            raise RuntimeError(f"MCP-Werkzeug {name} meldet einen Fehler: {ergebnis.content}")
        strukturiert = getattr(ergebnis, "structured_content", None)
        return strukturiert if strukturiert is not None else json.loads(ergebnis.content[0].text)

    def suche(self, anfrage: str, top_k: int = 3) -> list[tuple[Abschnitt, float]]:
        daten = self._ausfuehren(self._aufruf("suche_wettbewerbsrecht", {"anfrage": anfrage, "top_k": top_k}))
        return [(Abschnitt(t["quelle"], t["titel"], t["text"]), t["score"]) for t in daten["treffer"]]

    def werkzeuge(self) -> list[str]:
        return [t.name for t in self._ausfuehren(self._client.list_tools()).tools]

    def schliessen(self) -> None:
        if self._loop.is_running():
            try:
                self._ausfuehren(self._client.__aexit__(None, None, None), timeout=10)
            except Exception:  # noqa: BLE001 – beim Beenden nur aufräumen
                pass
            self._loop.call_soon_threadsafe(self._loop.stop)
