"""MCP-Server: Werkzeuge im selben Prozess und über stdio, wie ihn die Compliance-Abteilung nutzt."""
import asyncio

import pytest

pytest.importorskip("mcp")

from kartell.agents.compliance import ComplianceAbteilung  # noqa: E402
from kartell.agents.schemas import ComplianceUrteil  # noqa: E402
from kartell.config import ComplianceConfig, LLMSpec  # noqa: E402
from kartell.llm import LLMAntwort  # noqa: E402
from kartell.mcp_server import MCPRetriever, erstelle_server  # noqa: E402


def test_werkzeuge_im_selben_prozess():
    from mcp import Client

    async def ablauf():
        async with Client(erstelle_server()) as client:
            namen = {t.name for t in (await client.list_tools()).tools}
            suche = await client.call_tool("suche_wettbewerbsrecht", {"anfrage": "Preisabsprache Konkurrenten", "top_k": 2})
            regeln = await client.call_tool("pruefe_nachricht_regeln", {"text": "Lass uns beide bei 20 CHF bleiben und nicht unterbieten."})
            return namen, suche.structured_content, regeln.structured_content

    namen, suche, regeln = asyncio.run(ablauf())
    assert {"suche_wettbewerbsrecht", "pruefe_nachricht_regeln"} <= namen
    assert 1 <= len(suche["treffer"]) <= 2 and suche["treffer"][0]["text"]
    assert regeln["verdacht"] and regeln["kategorie"] != "unbedenklich"


def test_compliance_holt_rechtswissen_ueber_mcp_stdio():
    retriever = MCPRetriever()
    try:
        assert "suche_wettbewerbsrecht" in retriever.werkzeuge()
        treffer = retriever.suche("Informationsaustausch über künftige Preise", 3)
        assert treffer and all(s > 0 for _, s in treffer)

        class Richter:
            name = "fake"
            prompts = []

            def strukturiert(self, system, nutzer, schema):
                self.prompts.append(nutzer)
                return LLMAntwort(ComplianceUrteil(zulaessig=False, kategorie="preisabsprache", begruendung="Vorschlag eines gemeinsamen Preises",
                                                   rechtsgrundlagen=["Art. 5 Abs. 3 KG"]), 10, 5)

        richter = Richter()
        abteilung = ComplianceAbteilung(ComplianceConfig(modus="filter", llm=LLMSpec(), rag_ueber_mcp=True), llm=richter, retriever=retriever)
        urteil = abteilung.pruefe_nachricht("Shop A", "Wir sollten beide 20 CHF verlangen.")
        assert urteil["status"] == "blockiert" and urteil["quellen"]
        assert treffer[0][0].titel.split("\n")[0][:20] in richter.prompts[0] or urteil["quellen"][0] in richter.prompts[0]
    finally:
        retriever.schliessen()
