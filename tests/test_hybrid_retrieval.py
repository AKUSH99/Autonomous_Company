"""Hybrid Retrieval (BM25 + Embeddings + Reranker) und die Retrieval-Evaluation – ohne Netz, mit Fake-Einbetter."""
from kartell.config import ComplianceConfig, RetrievalConfig
from kartell.eval_retrieval import bewerte, lade_testset, tabelle
from kartell.rag import Abschnitt, BM25Retriever, HybridRetriever, erstelle_retriever, lade_abschnitte

WISSEN = "knowledge/wettbewerbsrecht"
THEMEN = ["preis", "kunde", "busse", "algorithmus"]


def fake_einbetten(texte):
    """Bag-of-themes: ein Vektor pro Thema, damit Umschreibungen ohne gemeinsame Wörter ähnlich werden."""
    synonyme = {"preis": ["preis", "price", "niveau", "chf", "marge"], "kunde": ["kund", "region", "zürich"],
                "busse": ["busse", "sanktion", "umsatz"], "algorithmus": ["algorithm", "software", "automat"]}
    return [[sum(t.lower().count(w) for w in synonyme[th]) + 0.01 for th in THEMEN] for t in texte]


ABSCHNITTE = [Abschnitt("a.md", "Preise", "Gemeinsame Preise und Mindestpreise sind verboten."),
              Abschnitt("b.md", "Sanktionen", "Die Busse beträgt bis zu 10 Prozent vom Umsatz."),
              Abschnitt("c.md", "Algorithmen", "Wer Software einsetzt, haftet für sie.")]


def test_hybrid_findet_umschreibung_die_bm25_verfehlt():
    anfrage = "Let's keep our price level"
    assert BM25Retriever(ABSCHNITTE).suche(anfrage, 1) == []  # kein gemeinsames Wort
    treffer = HybridRetriever(ABSCHNITTE, fake_einbetten).suche(anfrage, 1)
    assert treffer[0][0].quelle == "a.md"


def test_reranker_sortiert_neu_und_faellt_sicher_aus():
    retriever = HybridRetriever(ABSCHNITTE, fake_einbetten, reranker=lambda q, texte: [1.0 if "Software" in t else 0.0 for t in texte])
    assert retriever.suche("Preise", 1)[0][0].quelle == "c.md"

    def kaputt(q, texte):
        raise RuntimeError("503")

    retriever = HybridRetriever(ABSCHNITTE, fake_einbetten, reranker=kaputt)
    assert retriever.suche("Mindestpreise", 1)[0][0].quelle == "a.md"
    assert retriever.reranker_fehler == "503"


def test_standard_bleibt_bm25():
    assert ComplianceConfig().retrieval.verfahren == "bm25"
    assert isinstance(erstelle_retriever(WISSEN), BM25Retriever)
    assert isinstance(erstelle_retriever(WISSEN, RetrievalConfig()), BM25Retriever)


def test_evaluation_auf_dem_testset():
    testset = lade_testset("evaluation/retrieval_testset.jsonl")
    quellen = {a.quelle for a in lade_abschnitte(WISSEN)}
    assert len(testset) >= 20 and all(set(f["relevant"]) <= quellen for f in testset)
    bm25 = bewerte(BM25Retriever.aus_ordner(WISSEN), testset)
    hybrid = bewerte(HybridRetriever(lade_abschnitte(WISSEN), fake_einbetten), testset)
    for e in (bm25, hybrid):
        assert 0 <= e["gesamt"]["hit@1"] <= e["gesamt"]["hit@3"] <= 1 and e["gesamt"]["n"] == len(testset)
    assert bm25["nach_art"]["wörtlich"]["hit@3"] == 1.0  # exakte Begriffe: BM25-Stärke
    assert "| BM25 |" in tabelle({"BM25": bm25, "Hybrid": hybrid})
