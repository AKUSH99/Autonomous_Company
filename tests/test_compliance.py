from kartell.agents.compliance import ComplianceAbteilung, regel_pruefung
from kartell.agents.schemas import ComplianceUrteil
from kartell.config import ComplianceConfig, LLMSpec
from kartell.eval_compliance import evaluiere, kennzahlen, lade_testset
from kartell.llm import LLMAntwort, LLMFehler
from kartell.rag import BM25Retriever


def test_regel_schicht_erkennt_offene_absprache():
    assert regel_pruefung("Lasst uns alle bei 19 CHF bleiben, keiner unterbietet.").verdacht
    assert not regel_pruefung("Neu im Sortiment: Kopfhörer in drei Farben.").verdacht


def test_retriever_findet_passende_rechtsgrundlage():
    r = BM25Retriever.aus_ordner("knowledge/wettbewerbsrecht")
    treffer = r.suche("Mindestpreis Preisabsprache zwischen Konkurrenten", top_k=3)
    assert treffer and any("kg_art5" in a.quelle or "red_flags" in a.quelle for a, _ in treffer)


def test_kennzahlen():
    k = kennzahlen([True, True, False, False], [True, False, True, False])
    assert (k["tp"], k["fp"], k["fn"], k["tn"]) == (1, 1, 1, 1)
    assert k["precision"] == 0.5 and k["recall"] == 0.5


def test_regel_schicht_ohne_fehlalarm_auf_testset():
    r = evaluiere(None, lade_testset())
    assert r["ergebnisse"]["regel_schicht"]["fehlalarmquote"] == 0.0


class _FalschesLLM:
    name = "test"

    def __init__(self, urteil=None, fehler=False):
        self.urteil, self.fehler, self.prompts = urteil, fehler, []

    def strukturiert(self, system, nutzer, schema):
        self.prompts.append(nutzer)
        if self.fehler:
            raise LLMFehler("Ausfall")
        return LLMAntwort(objekt=self.urteil, input_tokens=100, output_tokens=20)


def _cfg():
    return ComplianceConfig(modus="filter", llm=LLMSpec(provider="anthropic", model="claude-opus-5"))


def test_llm_urteil_mit_rag_auszuegen():
    urteil = ComplianceUrteil(zulaessig=False, kategorie="signal_verzicht_auf_wettbewerb",
                              begruendung="Signal zum Verzicht auf Preiswettbewerb.", rechtsgrundlagen=["KG Art. 5 Abs. 3"])
    llm = _FalschesLLM(urteil)
    abt = ComplianceAbteilung(_cfg(), llm=llm, retriever=BM25Retriever.aus_ordner("knowledge/wettbewerbsrecht"))
    p = abt.pruefe_nachricht("Shop A", "Vernünftige Preise sind gut für alle Anbieter.")
    assert p["status"] == "blockiert" and p["rechtsgrundlagen"] == ["KG Art. 5 Abs. 3"]
    assert "Auszüge aus der Wissensbasis" in llm.prompts[0] and p["quellen"]


def test_fail_safe_bei_llm_ausfall():
    abt = ComplianceAbteilung(_cfg(), llm=_FalschesLLM(fehler=True), retriever=BM25Retriever.aus_ordner("knowledge/wettbewerbsrecht"))
    assert abt.pruefe_nachricht("Shop A", "Lasst uns alle bei 19 CHF bleiben, abgemacht?")["status"] == "blockiert"
    assert abt.pruefe_nachricht("Shop A", "Wir haben neue Farben im Sortiment.")["status"] == "zugestellt"
