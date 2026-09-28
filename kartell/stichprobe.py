"""Guardrail-Evaluation an echten Agenten-Nachrichten statt an selbst geschriebenen Testsätzen.

Ablauf:
  1. `stichprobe`: geschichtete Stichprobe aus allen Läufen ziehen – Nachrichten aus Läufen ohne Filter (nie geprüft)
     sowie blockierte und zugestellte Nachrichten aus Läufen mit Filter. Doppelte Texte werden entfernt.
  2. `urteile_sammeln` (im Auftrag): mehrere KI-Richter beurteilen dieselben Nachrichten.
  3. `richter-vergleich`: Regel-Schicht, Filter und KI-Richter untereinander vergleichen (Kappa, Mehrheit, strittige
     Fälle). Das misst Einigkeit, nicht Richtigkeit – unser Weg, weil es keine menschlichen Labels gibt (Entscheid 28).
  Optional, falls doch Menschen labeln (Label-Werkzeug): `labels-auswerten` rechnet Kappa zwischen den Menschen und
  misst Filter, Regel-Schicht und KI-Richter am menschlichen Konsens (Precision, Recall, Fehlalarmquote).
"""
from __future__ import annotations

import json
import random
import re
from collections import Counter
from pathlib import Path

from .agents.compliance import regel_pruefung
from .eval_compliance import kennzahlen


def sammle_nachrichten(wurzeln: list[str | Path]) -> list[dict]:
    nachrichten = []
    for wurzel in wurzeln:
        for meta_datei in sorted(Path(wurzel).rglob("meta.json")):
            ordner = meta_datei.parent
            runden_datei = ordner / "runden.jsonl"
            if not runden_datei.exists():
                continue
            meta = json.loads(meta_datei.read_text(encoding="utf-8"))
            mit_filter = meta.get("compliance") is not None and meta["config"]["compliance"]["modus"] != "aus"
            for zeile in runden_datei.read_text(encoding="utf-8").splitlines():
                if not zeile.strip():
                    continue
                r = json.loads(zeile)
                for m in r.get("nachrichten", []):
                    nachrichten.append({
                        "text": m["text"],
                        "quelle": {"versuch": meta["name"], "lauf": ordner.name, "runde": r["runde"], "von": m["von"]},
                        "filter_urteil": m["status"] if mit_filter else None,
                        "filter_kategorie": (m.get("compliance") or {}).get("kategorie") if mit_filter else None,
                    })
    return nachrichten


def _normiert(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\d+([.,]\d+)?", "#", text.lower())).strip()


def _reihum_nach_versuch(liste: list[dict], rng: random.Random) -> list[dict]:
    """Mischt innerhalb jedes Versuchs und zieht dann reihum – jeder Versuch ist in jeder Schicht vertreten."""
    gruppen: dict[str, list[dict]] = {}
    for n in liste:
        gruppen.setdefault(n["quelle"]["versuch"].split("_")[0], []).append(n)
    for g in gruppen.values():
        rng.shuffle(g)
    reihenfolge = sorted(gruppen)
    ergebnis = []
    while any(gruppen.values()):
        for name in reihenfolge:
            if gruppen[name]:
                ergebnis.append(gruppen[name].pop())
    return ergebnis


def ziehe_stichprobe(nachrichten: list[dict], anzahl: int = 120, seed: int = 7) -> list[dict]:
    """Hälfte aus Läufen ohne Filter, je ein Viertel blockiert und zugestellt; fehlt eine Schicht, füllen die anderen auf."""
    einmalig, gesehen = [], set()
    for n in nachrichten:
        schluessel = _normiert(n["text"])
        if schluessel not in gesehen:
            gesehen.add(schluessel)
            einmalig.append(n)
    rng = random.Random(seed)
    schichten = {"ungefiltert": [n for n in einmalig if n["filter_urteil"] is None],
                 "blockiert": [n for n in einmalig if n["filter_urteil"] == "blockiert"],
                 "zugestellt": [n for n in einmalig if n["filter_urteil"] == "zugestellt"]}
    for name, liste in schichten.items():
        schichten[name] = _reihum_nach_versuch(liste, rng)  # sonst dominiert der Versuch mit den meisten Nachrichten
    ziel = {"ungefiltert": anzahl // 2, "blockiert": anzahl // 4, "zugestellt": anzahl - anzahl // 2 - anzahl // 4}
    auswahl = {s: liste[:ziel[s]] for s, liste in schichten.items()}
    rest = [n for s, liste in schichten.items() for n in liste[ziel[s]:]]
    rng.shuffle(rest)
    fehlend = anzahl - sum(len(v) for v in auswahl.values())
    stichprobe = [n for v in auswahl.values() for n in v] + rest[:max(0, fehlend)]
    rng.shuffle(stichprobe)
    return [{"id": f"N{i:03d}"} | n for i, n in enumerate(stichprobe, 1)]


def lade_jsonl(pfad: str | Path) -> list[dict]:
    return [json.loads(z) for z in Path(pfad).read_text(encoding="utf-8").splitlines() if z.strip()]


def lade_labels(pfad: str | Path) -> list[dict]:
    """Menschliche Labels: JSONL mit {"id", "rater", "urteil"} oder der Export des Label-Werkzeugs (JSON mit "labels")."""
    text = Path(pfad).read_text(encoding="utf-8").strip()
    try:
        daten = json.loads(text)  # ganze Datei ist ein JSON-Dokument: Export oder Liste
        labels = daten.get("labels", [daten]) if isinstance(daten, dict) else daten
    except json.JSONDecodeError:
        labels = [json.loads(z) for z in text.splitlines() if z.strip()]
    return [l for l in labels if l.get("urteil") in ("zulaessig", "unzulaessig", "unsicher")]


def cohens_kappa(a: list[bool], b: list[bool]) -> float:
    """Übereinstimmung zweier Rater jenseits des Zufalls: 1 = perfekt, 0 = wie Zufall."""
    n = len(a)
    if n == 0:
        return float("nan")
    beobachtet = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    erwartet = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if erwartet == 1 else (beobachtet - erwartet) / (1 - erwartet)


def werte_labels_aus(stichprobe: list[dict], labels: list[dict], urteile: dict[str, list[dict]] | None = None) -> dict:
    """Labels: {"id", "rater", "urteil": "zulaessig"|"unzulaessig"|"unsicher"}. Positive Klasse = unzulässig."""
    je_nachricht: dict[str, dict[str, str]] = {}
    for l in labels:
        je_nachricht.setdefault(l["id"], {})[l["rater"]] = l["urteil"]
    rater = sorted({l["rater"] for l in labels})
    ergebnis: dict = {"nachrichten": len(stichprobe), "rater": rater,
                      "gelabelt_je_rater": dict(Counter(l["rater"] for l in labels))}
    if len(rater) >= 2:
        r1, r2 = rater[:2]
        beide = [(v[r1], v[r2]) for v in je_nachricht.values() if v.get(r1) in ("zulaessig", "unzulaessig")
                 and v.get(r2) in ("zulaessig", "unzulaessig")]
        ergebnis["kappa"] = round(cohens_kappa([x == "unzulaessig" for x, _ in beide], [y == "unzulaessig" for _, y in beide]), 3)
        ergebnis["uebereinstimmung"] = round(sum(x == y for x, y in beide) / len(beide), 3) if beide else None
        ergebnis["paare"] = len(beide)
    # Konsens: alle vorhandenen, sicheren Labels stimmen überein; Uneinigkeit und "unsicher" fallen heraus.
    konsens = {}
    for nid, urteile_rater in je_nachricht.items():
        sicher = {u for u in urteile_rater.values() if u in ("zulaessig", "unzulaessig")}
        if len(sicher) == 1 and "unsicher" not in urteile_rater.values():
            konsens[nid] = sicher.pop() == "unzulaessig"
    ergebnis["konsens"] = {"anzahl": len(konsens), "unzulaessig": sum(konsens.values())}
    nach_id = {n["id"]: n for n in stichprobe}
    ids = [i for i in konsens if i in nach_id]
    labels_bool = [konsens[i] for i in ids]
    ergebnis["regel_schicht"] = kennzahlen(labels_bool, [regel_pruefung(nach_id[i]["text"]).verdacht for i in ids])
    gefiltert = [i for i in ids if nach_id[i]["filter_urteil"] is not None]
    if gefiltert:
        ergebnis["filter_in_den_laeufen"] = kennzahlen([konsens[i] for i in gefiltert],
                                                       [nach_id[i]["filter_urteil"] == "blockiert" for i in gefiltert]) | {"n": len(gefiltert)}
    from .metrics import auc
    for name, liste in (urteile or {}).items():
        gueltig = [u for u in liste if u.get("status") in ("blockiert", "zugestellt")]  # Richter-Fehler zählen nicht als Urteil
        je_id = {u["id"]: u["status"] == "blockiert" for u in gueltig}
        mit = [i for i in ids if i in je_id]
        if mit:
            ergebnis[f"richter_{name}"] = kennzahlen([konsens[i] for i in mit], [je_id[i] for i in mit]) | {"n": len(mit)}
            p = {u["id"]: u.get("p_unzulaessig") for u in gueltig}
            if all(p.get(i) is not None for i in mit):
                ergebnis[f"richter_{name}"]["auc"] = round(auc([konsens[i] for i in mit], [p[i] for i in mit]), 3)
    return ergebnis


def fleiss_kappa(urteile: list[list[bool]]) -> float:
    """Einigkeit mehrerer Richter jenseits des Zufalls (Fleiss): je Nachricht die Urteile aller Richter, gleich viele."""
    if not urteile or len(urteile[0]) < 2:
        return float("nan")
    k = len(urteile[0])
    p_ja = sum(sum(z) for z in urteile) / (len(urteile) * k)
    einig = [(sum(z) * (sum(z) - 1) + (k - sum(z)) * (k - sum(z) - 1)) / (k * (k - 1)) for z in urteile]
    erwartet = p_ja ** 2 + (1 - p_ja) ** 2
    return 1.0 if erwartet == 1 else (sum(einig) / len(einig) - erwartet) / (1 - erwartet)


def vergleiche_richter(stichprobe: list[dict], urteile: dict[str, list[dict]], wiederholungen: dict[str, list[dict]] | None = None,
                       min_gemeinsam: int = 10) -> dict:
    """Richter untereinander vergleichen, wenn es keine menschlichen Labels gibt.

    Das misst Einigkeit, nicht Richtigkeit: Wenn alle Richter denselben Fehler machen, sieht man ihn hier nicht.
    Richter: die Regel-Schicht, der Filter so, wie er in den Läufen entschied (nur Nachrichten aus Läufen mit Filter),
    und jedes KI-Modell aus `urteile`. Urteile mit Fehler zählen nicht – auch nicht, wenn die Regel-Schicht einsprang.
    Referenz ist die Mehrheit der KI-Richter (nur Nachrichten mit klarer Mehrheit). Weil die KI-Richter den Befund der
    Regel-Schicht im Prompt sehen, wird die Einigkeit zusätzlich für Nachrichten ohne Regel-Treffer ausgewiesen.
    `wiederholungen`: zweite Durchgänge eines Modells – nur für den paarweisen Vergleich (Beständigkeit), nicht für die Mehrheit.
    """
    nach_id = {n["id"]: n for n in stichprobe}
    regel = {i: regel_pruefung(n["text"]).verdacht for i, n in nach_id.items()}
    gueltig = lambda liste: {u["id"]: u["status"] == "blockiert" for u in liste
                             if u.get("status") in ("blockiert", "zugestellt") and not u.get("fehler") and u["id"] in nach_id}
    ki = {name: gueltig(liste) for name, liste in urteile.items()}
    richter = {"regel_schicht": regel,
               "filter_in_den_laeufen": {i: n["filter_urteil"] == "blockiert" for i, n in nach_id.items()
                                         if n.get("filter_urteil") in ("blockiert", "zugestellt")}} | ki
    richter |= {name: gueltig(liste) for name, liste in (wiederholungen or {}).items()}
    ergebnis: dict = {"nachrichten": len(stichprobe), "hinweis": "Einigkeit, nicht Richtigkeit – keine menschlichen Labels",
                      "richter": {name: {"n": len(u), "blockiert": sum(u.values()),
                                         "quote": round(sum(u.values()) / len(u), 3) if u else None}
                                  for name, u in richter.items()}}
    paare = []
    namen = list(richter)
    for i, a in enumerate(namen):
        for b in namen[i + 1:]:
            gemeinsam = [x for x in richter[a] if x in richter[b]]
            if len(gemeinsam) < min_gemeinsam:
                continue
            ua, ub = [richter[a][x] for x in gemeinsam], [richter[b][x] for x in gemeinsam]
            ohne = [x for x in gemeinsam if not regel[x]]
            paare.append({"a": a, "b": b, "n": len(gemeinsam),
                          "uebereinstimmung": round(sum(x == y for x, y in zip(ua, ub)) / len(gemeinsam), 3),
                          "kappa": round(cohens_kappa(ua, ub), 3),
                          "n_ohne_regeltreffer": len(ohne),
                          "uebereinstimmung_ohne_regeltreffer": round(sum(richter[a][x] == richter[b][x] for x in ohne) / len(ohne), 3) if ohne else None})
    ergebnis["paare"] = paare
    if len(ki) >= 2:
        alle = [x for x in nach_id if all(x in u for u in ki.values())]
        ergebnis["ki_richter"] = {"namen": list(ki), "n_alle_geurteilt": len(alle),
                                  "fleiss_kappa": round(fleiss_kappa([[u[x] for u in ki.values()] for x in alle]), 3) if alle else None,
                                  "alle_einig": sum(len({u[x] for u in ki.values()}) == 1 for x in alle)}
        mehrheit, strittig = {}, []
        for x in nach_id:
            stimmen = [u[x] for u in ki.values() if x in u]
            if len(stimmen) < 2:
                continue
            ja = sum(stimmen)
            if ja * 2 != len(stimmen):
                mehrheit[x] = ja * 2 > len(stimmen)
            if 0 < ja < len(stimmen):
                strittig.append({"id": x, "text": nach_id[x]["text"], "regel_schicht": regel[x],
                                 "urteile": {name: ("blockiert" if u[x] else "zugestellt") for name, u in ki.items() if x in u}})
        ergebnis["mehrheit"] = {"n": len(mehrheit), "blockiert": sum(mehrheit.values())}
        for name in ("regel_schicht", "filter_in_den_laeufen"):
            mit = [x for x in mehrheit if x in richter[name]]
            if mit:
                ergebnis[f"{name}_gegen_mehrheit"] = kennzahlen([mehrheit[x] for x in mit], [richter[name][x] for x in mit]) | {"n": len(mit)}
        ergebnis["strittig"] = strittig
    return ergebnis
