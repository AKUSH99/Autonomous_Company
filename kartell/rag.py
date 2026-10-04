"""Retrieval über die Wissensbasis zum Wettbewerbsrecht.

Standard ist BM25 ohne externe Dienste: Die Wissensbasis ist klein (wenige Seiten), Rechtsbegriffe wie
„Preisabsprache" oder „Mindestpreis" sollen exakt treffen, und das Verfahren ist vollständig nachvollziehbar.
Wahlweise Hybrid Retrieval (BM25 + Embeddings + Reranker, siehe unten); welches Verfahren besser findet, misst
`python -m kartell eval-retrieval` auf einem gelabelten Testset (evaluation/retrieval_testset.jsonl).
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

_STOPPWOERTER = set("""
der die das den dem des ein eine einer eines einem einen und oder aber nicht kein keine ist sind war
wird werden wurde zu zum zur im in am an auf aus bei mit von vor nach über unter für ohne um als wie
auch nur noch schon so sehr es er sie wir ihr ich du man sich dass wenn weil ob doch ja nein alle
the a an and or of to in on for with is are be we you they it this that let lets us
""".split())


def tokens(text: str) -> list[str]:
    woerter = [w for w in re.findall(r"[a-zäöüß0-9]+", text.lower()) if w not in _STOPPWOERTER and len(w) > 1]
    # Einfache Stammform-Näherung für deutsche Komposita und Flexion: Präfix aus 5 Zeichen zusätzlich
    return woerter + [w[:5] for w in woerter if len(w) > 6]


@dataclass(frozen=True)
class Abschnitt:
    quelle: str
    titel: str
    text: str

    def zitat(self, max_zeichen: int = 700) -> str:
        t = self.text if len(self.text) <= max_zeichen else self.text[:max_zeichen] + " …"
        return f"{self.titel}\n{t}"


def lade_abschnitte(ordner: str | Path) -> list[Abschnitt]:
    abschnitte: list[Abschnitt] = []
    for datei in sorted(Path(ordner).glob("*.md")):
        inhalt = datei.read_text(encoding="utf-8").strip()
        titel = inhalt.splitlines()[0].lstrip("# ").strip()
        absaetze = [a.strip() for a in inhalt.split("\n\n")[1:] if a.strip()]
        puffer = ""
        for absatz in absaetze:
            puffer = f"{puffer}\n{absatz}".strip()
            if len(puffer) >= 250:
                abschnitte.append(Abschnitt(datei.name, titel, puffer))
                puffer = ""
        if puffer:
            abschnitte.append(Abschnitt(datei.name, titel, puffer))
    return abschnitte


class BM25Retriever:
    def __init__(self, abschnitte: list[Abschnitt], k1: float = 1.5, b: float = 0.75):
        if not abschnitte:
            raise ValueError("Die Wissensbasis ist leer.")
        self.abschnitte = abschnitte
        self.k1, self.b = k1, b
        self.dok_tokens = [Counter(tokens(f"{a.titel} {a.text}")) for a in abschnitte]
        self.laengen = [sum(c.values()) for c in self.dok_tokens]
        self.mittel = sum(self.laengen) / len(self.laengen)
        df = Counter(t for c in self.dok_tokens for t in c)
        n = len(abschnitte)
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    @classmethod
    def aus_ordner(cls, ordner: str | Path) -> "BM25Retriever":
        return cls(lade_abschnitte(ordner))

    def suche(self, anfrage: str, top_k: int = 3) -> list[tuple[Abschnitt, float]]:
        q = tokens(anfrage)
        wertung = []
        for i, c in enumerate(self.dok_tokens):
            s = 0.0
            for t in q:
                if t not in c:
                    continue
                f = c[t]
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.laengen[i] / self.mittel))
            wertung.append((s, i))
        wertung.sort(reverse=True)
        return [(self.abschnitte[i], round(s, 3)) for s, i in wertung[:top_k] if s > 0]


# ---------------------------------------------------------------------------------------------------------------
# Hybrid Retrieval (SW7: Chunking und Hybrid Retrieval): BM25 + Embeddings, verbunden mit Reciprocal Rank Fusion,
# optional neu sortiert von einem Reranker. Embeddings und Reranker kommen standardmässig von der Swiss AI Research
# Platform (Qwen3-Embedding-8B, bge-reranker-v2-m3). Chunking: lade_abschnitte fasst Absätze zu Stücken von mindestens
# 250 Zeichen zusammen, jedes Stück behält den Titel seines Dokuments.
# ---------------------------------------------------------------------------------------------------------------
Einbetter = Callable[[list[str]], list[list[float]]]
Reranker = Callable[[str, list[str]], list[float]]


def _norm(v: list[float]) -> list[float]:
    laenge = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / laenge for x in v]


class EmbeddingRetriever:
    """Semantische Suche: Kosinus-Ähnlichkeit zwischen Anfrage und Abschnitten (Titel + Text)."""

    def __init__(self, abschnitte: list[Abschnitt], einbetten: Einbetter):
        if not abschnitte:
            raise ValueError("Die Wissensbasis ist leer.")
        self.abschnitte = abschnitte
        self.einbetten = einbetten
        self.vektoren = [_norm(v) for v in einbetten([f"{a.titel}\n{a.text}" for a in abschnitte])]

    def suche(self, anfrage: str, top_k: int = 3) -> list[tuple[Abschnitt, float]]:
        q = _norm(self.einbetten([anfrage])[0])
        wertung = sorted(((sum(a * b for a, b in zip(q, v)), i) for i, v in enumerate(self.vektoren)), reverse=True)
        return [(self.abschnitte[i], round(s, 3)) for s, i in wertung[:top_k]]


class HybridRetriever:
    """BM25 (exakte Rechtsbegriffe) + Embeddings (Umschreibungen wie „wir halten unser Niveau, wenn ihr eures haltet").

    Beide Listen werden mit Reciprocal Rank Fusion (Cormack et al. 2009) verbunden: score = Σ 1 / (k + Rang). RRF braucht
    keine vergleichbaren Skalen – BM25-Werte und Kosinus-Ähnlichkeiten lassen sich nicht direkt addieren. Ist ein
    Reranker gesetzt, sortiert er die `kandidaten` besten Treffer neu (Cross-Encoder: liest Anfrage und Abschnitt
    zusammen). Fällt der Reranker aus, bleibt die RRF-Reihenfolge (fail-safe wie beim Compliance-LLM).
    """

    def __init__(self, abschnitte: list[Abschnitt], einbetten: Einbetter, reranker: Reranker | None = None,
                 kandidaten: int = 8, rrf_k: int = 60):
        self.bm25 = BM25Retriever(abschnitte)
        self.semantisch = EmbeddingRetriever(abschnitte, einbetten)
        self.abschnitte = abschnitte
        self.reranker, self.kandidaten, self.rrf_k = reranker, kandidaten, rrf_k
        self.reranker_fehler: str | None = None

    def suche(self, anfrage: str, top_k: int = 3) -> list[tuple[Abschnitt, float]]:
        n = max(self.kandidaten, top_k)
        rrf: dict[int, float] = {}
        for liste in (self.bm25.suche(anfrage, n), self.semantisch.suche(anfrage, n)):
            for rang, (a, _) in enumerate(liste, 1):
                i = self.abschnitte.index(a)
                rrf[i] = rrf.get(i, 0.0) + 1.0 / (self.rrf_k + rang)
        reihenfolge = sorted(rrf, key=rrf.get, reverse=True)[:n]
        if self.reranker and reihenfolge:
            try:
                werte = self.reranker(anfrage, [f"{self.abschnitte[i].titel}\n{self.abschnitte[i].text}" for i in reihenfolge])
                neu = sorted(zip(werte, reihenfolge), reverse=True)
                return [(self.abschnitte[i], round(float(s), 3)) for s, i in neu[:top_k]]
            except Exception as e:  # noqa: BLE001 – Reranker ist optional
                self.reranker_fehler = str(e)
        return [(self.abschnitte[i], round(rrf[i], 4)) for i in reihenfolge[:top_k]]


def openai_einbetter(base_url: str, modell: str, api_key_env: str, cache: str | Path | None = None,
                     stapel: int = 32) -> Einbetter:
    """Embeddings über eine OpenAI-kompatible Schnittstelle (/v1/embeddings). Mit `cache` werden Vektoren pro Text
    gespeichert, damit die Wissensbasis nicht bei jedem Lauf neu eingebettet wird."""
    import hashlib
    import json
    import os

    import openai
    client = openai.OpenAI(base_url=base_url, api_key=os.environ.get(api_key_env, "") or "nicht-benoetigt", max_retries=4)
    datei = Path(cache) if cache else None
    gespeichert: dict[str, list[float]] = json.loads(datei.read_text(encoding="utf-8")) if datei and datei.exists() else {}

    def schluessel(t: str) -> str:
        return hashlib.sha1(f"{modell}\n{t}".encode("utf-8")).hexdigest()

    def einbetten(texte: list[str]) -> list[list[float]]:
        fehlend = [t for t in dict.fromkeys(texte) if schluessel(t) not in gespeichert]
        for start in range(0, len(fehlend), stapel):
            teil = fehlend[start:start + stapel]
            antwort = client.embeddings.create(model=modell, input=teil)
            for t, d in zip(teil, sorted(antwort.data, key=lambda d: d.index)):
                gespeichert[schluessel(t)] = d.embedding
        if fehlend and datei:
            datei.parent.mkdir(parents=True, exist_ok=True)
            datei.write_text(json.dumps(gespeichert), encoding="utf-8")
        return [gespeichert[schluessel(t)] for t in texte]

    return einbetten


def http_reranker(base_url: str, modell: str, api_key_env: str) -> Reranker:
    """Reranker über den /rerank-Endpunkt (Cohere/Jina-Format, so wie ihn vLLM und LiteLLM anbieten)."""
    import os

    import httpx
    kopf = {"Authorization": f"Bearer {os.environ.get(api_key_env, '')}"}

    def rerank(anfrage: str, texte: list[str]) -> list[float]:
        r = httpx.post(f"{base_url.rstrip('/')}/rerank", headers=kopf, timeout=60,
                       json={"model": modell, "query": anfrage, "documents": texte})
        r.raise_for_status()
        werte = [0.0] * len(texte)
        for e in r.json()["results"]:
            werte[e["index"]] = float(e["relevance_score"])
        return werte

    return rerank


def erstelle_retriever(ordner: str | Path, cfg=None):
    """BM25 (Standard, ohne externe Dienste) oder Hybrid nach `RetrievalConfig`."""
    abschnitte = lade_abschnitte(ordner)
    if cfg is None or cfg.verfahren == "bm25":
        return BM25Retriever(abschnitte)
    einbetten = openai_einbetter(cfg.base_url, cfg.embedding_modell, cfg.api_key_env, cache=cfg.cache)
    reranker = http_reranker(cfg.base_url, cfg.reranker_modell, cfg.api_key_env) if cfg.reranker_modell else None
    return HybridRetriever(abschnitte, einbetten, reranker, kandidaten=cfg.kandidaten)
