"""Marktplatz-Ansicht: ein Lauf als Preisvergleichsportal zum Durchblättern, Woche für Woche (eine HTML-Datei).

    python -m kartell marktplatz runs/ --ausgabe reports/marktplatz.html

Zeigt pro Woche die Rangliste wie im Portal (Preis, Bewertung, Lieferzeit, Mitteilung, verkaufte Menge, Gewinn), die
privaten Notizen jedes Shops, die Preiskurve mit Wettbewerbs- und Kartellpreis und die Entscheide der Kundschaft.
Gedacht für Läufe mit Portal (E26–E28); andere Läufe funktionieren auch, dann ohne Bewertungen und Lieferzeiten.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from .config import VERSUCHE, ExperimentConfig, anzeigename
from .market import LogitMarkt

VORLAGE = Path(__file__).resolve().parent / "vorlagen" / "marktplatz.html"
KOPF = ('<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')


def _kurz(text, n: int) -> str:
    text = str(text or "").strip()
    return text if len(text) <= n else text[:n].rstrip() + " …"


def lade_lauf(ordner: Path) -> dict | None:
    if not ((ordner / "meta.json").exists() and (ordner / "runden.jsonl").exists()):
        return None
    meta = json.loads((ordner / "meta.json").read_text(encoding="utf-8"))
    cfg = ExperimentConfig.model_validate(meta["config"])
    runden = [json.loads(z) for z in (ordner / "runden.jsonl").read_text(encoding="utf-8").splitlines() if z.strip()]
    if not runden:
        return None
    markt = LogitMarkt(cfg.markt)
    profile = {f.name: f for f in cfg.agenten.profile}
    shops = list(runden[0]["preise"])
    modelle = sorted(set(meta.get("agenten", {}).values()))
    daten = []
    for r in runden:
        preise = [r["preise"][s] for s in shops]
        anteile = markt.anteile(preise)
        eintrag = {
            "runde": r["runde"], "preise": r["preise"], "mengen": r["mengen"], "gewinne": r["gewinne"],
            "nachrichten": [{"von": m["von"], "text": m["text"], "status": m.get("status", "zugestellt"),
                             "begruendung": _kurz((m.get("compliance") or {}).get("begruendung"), 220)}
                            for m in r.get("nachrichten", [])],
            "entscheide": {s: {k: _kurz(e.get(k), 600) for k in ("beobachtungen", "plan", "erkenntnisse")}
                           | ({"erzwungen": True} if e.get("erzwungen") else {})
                           | ({"ausfall": True} if e.get("fehler") else {})
                           for s, e in r.get("entscheide", {}).items()},
            "anteile_formel": [round(float(a), 3) for a in anteile] + [round(float(1 - anteile.sum()), 3)],
            "ohne_kauf": round(float(1 - anteile.sum()), 3),
        }
        for k in ("ereignisse", "vergleich", "kosten"):
            if r.get(k):
                eintrag[k] = r[k]
        if r.get("kunden") and r["kunden"].get("anteile"):
            eintrag["kunden"] = {"anteile": r["kunden"]["anteile"],
                                 "entscheide": [{"name": e["name"], "kauf": e["kauf"], "grund": _kurz(e.get("grund"), 160)}
                                                for e in r["kunden"].get("entscheide", [])]}
        daten.append(eintrag)
    titel = anzeigename(meta["name"], meta.get("config", {}).get("titel", "") if meta["name"].startswith("szenario_") else "")
    # Aktuelle Beschreibung aus der Versuchsdatei (ältere Läufe tragen noch die alten Versuchsnummern im Text)
    beschreibung = cfg.beschreibung
    for datei in VERSUCHE.rglob("*.yaml"):
        versuch = yaml.safe_load(datei.read_text(encoding="utf-8"))
        if isinstance(versuch, dict) and versuch.get("name") and meta["name"].startswith(versuch["name"]) and versuch.get("beschreibung"):
            beschreibung = versuch["beschreibung"]
            break
    return {
        "titel": f"{titel} · Wiederholung {meta.get('wiederholung', 1)}",
        "beschreibung": beschreibung,
        "produkt": cfg.produkt,
        "portal": cfg.portal.name if cfg.portal.aktiv else "Preisvergleich.ch",
        "modell": ", ".join(m.split(":", 1)[-1].split("/")[-1] for m in modelle) or "?",
        "benchmarks": meta["benchmarks"],
        "shops": [{"name": s, "bewertung": getattr(profile.get(s), "bewertung", None),
                   "bewertungen": getattr(profile.get(s), "bewertungen", None),
                   "lieferzeit": getattr(profile.get(s), "lieferzeit", "") or "",
                   "bot": meta.get("agenten", {}).get(s, "").startswith("scripted:")} for s in shops],
        "runden": daten,
        "fuss": ("Simulation, keine echten Shops. Preisniveau kalibriert nach Toppreise.ch (JBL Tune 770NC, 04.10.2026). "
                 "Wettbewerbspreis = Nash-Gleichgewicht, Kartellpreis = Monopolpreis des Marktmodells. "
                 f"Lauf {ordner.name}."),
    }


def baue(ordner: list[Path], ausgabe: Path, artifact: bool = False) -> dict:
    """Sucht Läufe rekursiv, schreibt eine HTML-Datei. `artifact`: ohne <!doctype>/<head> (wird beim Veröffentlichen ergänzt)."""
    gefunden = []
    for wurzel in ordner:
        for meta in sorted(Path(wurzel).rglob("meta.json")):
            lauf = lade_lauf(meta.parent)
            if lauf:
                gefunden.append(lauf)
    if not gefunden:
        raise SystemExit("Keine Läufe gefunden (meta.json + runden.jsonl).")
    vorlage = VORLAGE.read_text(encoding="utf-8")
    json_text = json.dumps({"laeufe": gefunden}, ensure_ascii=False).replace("</", "<\\/")
    html = vorlage.replace('/*DATEN*/{"laeufe": []}/*ENDE*/', json_text)
    if not artifact:  # eigenständige Datei: Titel, Schriften und Stil in den <head>, der Rest in den <body>
        teil = html.index('<div class="wrap">')
        html = KOPF + html[:teil] + "</head>\n<body>\n" + html[teil:] + "\n</body>\n</html>\n"
    ausgabe.parent.mkdir(parents=True, exist_ok=True)
    ausgabe.write_text(html, encoding="utf-8")
    return {"datei": str(ausgabe), "laeufe": len(gefunden), "kb": round(len(html.encode()) / 1024)}
