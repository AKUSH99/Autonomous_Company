"""Evaluation des Retrievals: Findet die Suche die richtigen Rechtsgrundlagen?

Testset `evaluation/retrieval_testset.jsonl`: Anfragen, wie sie der Compliance-Agent stellt (Nachrichten der Shops,
wörtlich, umschrieben, englisch, unbedenklich, dazu Rechtsfragen), je mit den Dokumenten, die dazu passen.
Kennzahlen pro Verfahren:
  Hit@k – Anteil der Anfragen mit mindestens einem passenden Dokument unter den ersten k Treffern
  MRR   – Mean Reciprocal Rank: 1 / Rang des ersten passenden Treffers, gemittelt (1.0 = immer zuoberst)
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def lade_testset(datei: str | Path) -> list[dict]:
    return [json.loads(z) for z in Path(datei).read_text(encoding="utf-8").splitlines() if z.strip()]


def bewerte(retriever, testset: list[dict], k: int = 3) -> dict:
    zeilen, gruppen = [], defaultdict(list)
    for fall in testset:
        treffer = [a.quelle for a, _ in retriever.suche(fall["anfrage"], max(k, 5))]
        rang = next((i + 1 for i, q in enumerate(treffer) if q in fall["relevant"]), None)
        zeile = {"anfrage": fall["anfrage"], "art": fall.get("art", ""), "rang": rang, "treffer": treffer[:k]}
        zeilen.append(zeile)
        gruppen[zeile["art"]].append(zeile)

    def kennzahlen(z: list[dict]) -> dict:
        n = len(z) or 1
        return {"n": len(z), "hit@1": round(sum(1 for x in z if x["rang"] == 1) / n, 3),
                f"hit@{k}": round(sum(1 for x in z if x["rang"] and x["rang"] <= k) / n, 3),
                "mrr": round(sum(1 / x["rang"] for x in z if x["rang"]) / n, 3)}

    return {"gesamt": kennzahlen(zeilen), "nach_art": {a: kennzahlen(z) for a, z in sorted(gruppen.items())},
            "verfehlt": [z for z in zeilen if not z["rang"] or z["rang"] > k], "faelle": zeilen}


def tabelle(ergebnisse: dict[str, dict], k: int = 3) -> str:
    kopf = f"| Verfahren | Hit@1 | Hit@{k} | MRR |"
    zeilen = [kopf, "|---|---|---|---|"]
    for name, e in ergebnisse.items():
        g = e["gesamt"]
        zeilen.append(f"| {name} | {g['hit@1']:.2f} | {g[f'hit@{k}']:.2f} | {g['mrr']:.2f} |")
    arten = sorted({a for e in ergebnisse.values() for a in e["nach_art"]})
    zeilen += ["", "MRR nach Art der Anfrage:", "| Art | n | " + " | ".join(ergebnisse) + " |",
               "|---|---|" + "---|" * len(ergebnisse)]
    for a in arten:
        n = next(e["nach_art"][a]["n"] for e in ergebnisse.values() if a in e["nach_art"])
        zeilen.append(f"| {a} | {n} | " + " | ".join(f"{e['nach_art'].get(a, {}).get('mrr', 0):.2f}" for e in ergebnisse.values()) + " |")
    return "\n".join(zeilen)
