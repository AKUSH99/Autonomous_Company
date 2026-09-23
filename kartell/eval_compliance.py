"""Evaluation des Guardrails: Wie gut erkennt die Compliance-Abteilung Absprachen?

Testdatensatz: evaluation/compliance_testset.jsonl – Nachrichten mit Label (zulaessig true/false).
Gemessen werden Precision, Recall und F1 für die Klasse „unzulässig" sowie die Fehlalarmquote,
getrennt für Regel-Schicht, LLM-Schicht (mit RAG) und die Kombination.
"""
from __future__ import annotations

import json
from pathlib import Path

from .agents.compliance import ComplianceAbteilung, regel_pruefung
from .config import ComplianceConfig


def lade_testset(pfad: str | Path = "evaluation/compliance_testset.jsonl") -> list[dict]:
    return [json.loads(z) for z in Path(pfad).read_text(encoding="utf-8").splitlines() if z.strip()]


def kennzahlen(labels: list[bool], vorhersagen: list[bool]) -> dict:
    """labels/vorhersagen: True = unzulässig (positive Klasse)."""
    tp = sum(l and v for l, v in zip(labels, vorhersagen))
    fp = sum((not l) and v for l, v in zip(labels, vorhersagen))
    fn = sum(l and (not v) for l, v in zip(labels, vorhersagen))
    tn = sum((not l) and (not v) for l, v in zip(labels, vorhersagen))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": round(precision, 3), "recall": round(recall, 3),
            "f1": round(f1, 3), "fehlalarmquote": round(fp / (fp + tn), 3) if fp + tn else 0.0}


def evaluiere(cfg: ComplianceConfig | None, testset: list[dict]) -> dict:
    labels = [not t["zulaessig"] for t in testset]
    ergebnisse = {"regel_schicht": kennzahlen(labels, [regel_pruefung(t["text"]).verdacht for t in testset])}
    fehler = []
    if cfg is not None and cfg.llm.provider != "regeln":
        abteilung = ComplianceAbteilung(cfg)
        vorhersagen, llm_fehler = [], 0
        for t in testset:
            p = abteilung.pruefe_nachricht("Shop X", t["text"])
            llm_fehler += p["fehler"] is not None
            vorhersagen.append(p["status"] == "blockiert")
            if (p["status"] == "blockiert") != (not t["zulaessig"]):
                fehler.append({"text": t["text"], "label_zulaessig": t["zulaessig"], "urteil": p["status"],
                               "begruendung": p["begruendung"]})
        ergebnisse["regeln_plus_llm"] = kennzahlen(labels, vorhersagen) | {"llm_fehler": llm_fehler}
    return {"anzahl": len(testset), "unzulaessig": sum(labels), "ergebnisse": ergebnisse, "fehlklassifikationen": fehler}
