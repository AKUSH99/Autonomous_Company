"""Retrieval über die Wissensbasis zum Wettbewerbsrecht (BM25, ohne externe Dienste).

Warum BM25 statt Embeddings? Die Wissensbasis ist klein (wenige Seiten), Rechtsbegriffe wie
„Preisabsprache" oder „Mindestpreis" sollen exakt treffen, und das Verfahren ist vollständig
nachvollziehbar. Ein Vergleich mit Embedding-Retrieval ist eine mögliche Erweiterung.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

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
