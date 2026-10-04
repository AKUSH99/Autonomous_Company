"""Kommandozeile: python -m kartell <befehl> ..."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import DENKEN, DENKEN_MAXIMAL_ERSATZ, OPENROUTER_URL, ComplianceConfig, LLMSpec, kurz, lade_config, mit_denken, mit_modell, voreinstellung


def _lade(args):
    cfg = lade_config(args.config)
    return mit_modell(cfg, args.modell, getattr(args, "compliance_modell", None)) if getattr(args, "modell", None) else cfg


def _benchmark(args) -> None:
    from .market import LogitMarkt
    cfg = lade_config(args.config)
    b = LogitMarkt(cfg.markt).benchmarks()
    print(f"{cfg.name}: {cfg.markt.firmen} Shops, Stückkosten {b.grenzkosten:.2f} CHF")
    print(f"  Nash-Preis    {b.nash_preis:6.2f} CHF   Gewinn pro Shop {b.nash_gewinn:8.2f}")
    print(f"  Monopolpreis  {b.monopol_preis:6.2f} CHF   Gewinn pro Shop {b.monopol_gewinn:8.2f}")


def _schaetzung(args) -> dict:
    return _zeige_schaetzung(_lade(args))


def _zeige_schaetzung(cfg) -> dict:
    from .kosten import schaetze
    s = schaetze(cfg)
    print(f"Kostenschätzung {cfg.name}: {cfg.runden} Runden × {cfg.wiederholungen} Wiederholungen")
    for z in s["zeilen"]:
        usd = "unbekannt" if z["usd"] is None else f"{z['usd']:.2f} USD"
        print(f"  {z['posten']:<28} {z['modell']:<40} {z['aufrufe']:>6} Aufrufe  {usd}")
    print(f"  Summe ≈ {s['usd']:.2f} USD{' (ohne Posten mit unbekanntem Preis)' if s['unvollstaendig'] else ''}")
    return s


def _lauf(args) -> None:
    from .runner import fuehre_experiment_aus
    cfg = _lade(args)
    if args.runden:
        cfg.runden = args.runden
    if args.wiederholungen:
        cfg.wiederholungen = args.wiederholungen
    s = _zeige_schaetzung(cfg) if not args.ja else None  # nach --runden/--wiederholungen: tatsächlicher Umfang
    if s and s["usd"] > 0 and input("Starten? [j/N] ").strip().lower() not in ("j", "ja", "y", "yes"):
        print("Abgebrochen.")
        return
    fuehre_experiment_aus(cfg, args.ausgabe)


def _demo(args) -> None:
    from .runner import fuehre_lauf_aus
    print("Offline-Demo mit festen Skript-Strategien (kein LLM, kein API-Schlüssel nötig).\n")
    for datei in ("experiments/demo_absprache_ohne_aufsicht.yaml", "experiments/demo_absprache_mit_filter.yaml"):
        fuehre_lauf_aus(lade_config(datei), 1, args.ausgabe)


def _eval_compliance(args) -> None:
    from .eval_compliance import evaluiere, lade_testset
    cfg = None
    if not args.nur_regeln:
        if args.config:
            cfg = _lade(args).compliance
        else:
            name = args.compliance_modell or args.modell
            cfg = ComplianceConfig(llm=voreinstellung(name).model_copy(update={"temperature": 0.0}) if name else LLMSpec())
    r = evaluiere(cfg, lade_testset(args.testset))
    print(json.dumps(r, ensure_ascii=False, indent=2))


def _pruefe_modell(spec: LLMSpec, berichte) -> None:
    """Vor langen Läufen: Schlüssel gültig und Modellname beim Anbieter vorhanden? Schreibt die Modellliste mit."""
    import os

    import openai
    if spec.provider != "openai_compat":
        return
    if spec.api_key_env and not os.environ.get(spec.api_key_env):
        raise SystemExit(f"Umgebungsvariable {spec.api_key_env} fehlt – ohne Schlüssel kein Lauf.")
    client = openai.OpenAI(base_url=spec.base_url, api_key=os.environ.get(spec.api_key_env or "", "") or "nicht-benoetigt")
    try:
        ids = sorted(m.id for m in client.models.list())
    except openai.AuthenticationError as e:
        raise SystemExit(f"Schlüssel in {spec.api_key_env} wird abgelehnt: {e}") from e
    except openai.APIError as e:
        print(f"Hinweis: Modellliste nicht abrufbar ({e}), fahre ohne Prüfung fort.")
        return
    (berichte / f"modelle_{kurz(spec.base_url.split('//')[-1].split('/')[0])}.txt").write_text("\n".join(ids) + "\n", encoding="utf-8")
    print(f"{len(ids)} Modelle bei {spec.base_url}" + (f": {', '.join(ids)}" if len(ids) <= 20 else ""))
    if spec.model not in ids:
        raise SystemExit(f"Modell {spec.model} ist bei {spec.base_url} nicht verfügbar – Modellnamen prüfen (siehe modelle.txt).")


def preise_openrouter(modell: str, modelle: list[dict]) -> dict | None:
    """Preisangaben eines Modells aus OpenRouters Modellliste (GET /models), oder None, wenn es fehlt."""
    eintrag = next((m for m in modelle if m.get("id") == modell), None)
    return None if eintrag is None else (eintrag.get("pricing") or {})


def ist_gratis(preise: dict | None) -> bool:
    """Nur wenn alle Preisfelder genau 0 sind. Fehlt die Angabe, gilt das Modell nicht als gratis."""
    if not preise:
        return False
    try:
        return all(float(v) == 0 for v in preise.values() if v not in (None, ""))
    except (TypeError, ValueError):
        return False


def _pruefe_gratis(spec: LLMSpec, berichte) -> None:
    """Sicherung vor Läufen mit `nur_gratis: true`: Kostet das Modell bei OpenRouter etwas, startet kein Lauf."""
    import urllib.request
    if spec.provider != "openai_compat" or not (spec.base_url or "").startswith(OPENROUTER_URL):
        raise SystemExit(f"nur_gratis: {spec.kurzname} läuft nicht über OpenRouter – Preis nicht prüfbar, kein Lauf.")
    with urllib.request.urlopen(f"{OPENROUTER_URL}/models", timeout=30) as antwort:
        modelle = json.load(antwort).get("data", [])
    preise = preise_openrouter(spec.model, modelle)
    (berichte / f"preise_{kurz(spec.model)}.json").write_text(json.dumps(preise, indent=2), encoding="utf-8")
    if not ist_gratis(preise):
        raise SystemExit(f"nur_gratis: {spec.model} ist nicht gratis ({preise}) – kein Lauf gestartet, nichts ausgegeben.")
    print(f"Preis geprüft: {spec.model} ist gratis ({preise}).")


def _denkstufe_pruefen(spec: LLMSpec) -> str:
    """Für denken: maximal – eine Probe-Anfrage mit der höchsten Stufe; lehnt das Modell sie ab, die nächsttiefere."""
    import os

    import openai
    client = openai.OpenAI(base_url=spec.base_url, api_key=os.environ.get(spec.api_key_env or "", "") or "nicht-benoetigt")
    for stufe in DENKEN_MAXIMAL_ERSATZ:
        try:
            client.chat.completions.create(model=spec.model, messages=[{"role": "user", "content": "Antworte nur mit OK."}],
                                           max_tokens=2000, extra_body={"reasoning": {"effort": stufe}})
            print(f"Denkstufe maximal: Modell akzeptiert effort={stufe}.")
            return stufe
        except openai.BadRequestError as e:
            print(f"Denkstufe effort={stufe} abgelehnt ({str(e)[:160]}) – versuche die nächste.")
    return DENKEN_MAXIMAL_ERSATZ[-1]


def _modellsuche(suche: dict, berichte) -> None:
    """Sucht in der Modellliste eines Anbieters (Standard: OpenRouter) nach Begriffen und speichert die Treffer."""
    import os

    import openai
    base_url = suche.get("base_url", OPENROUTER_URL)
    schluessel = os.environ.get(suche.get("api_key_env", "OPENROUTER_API_KEY"), "") or "nicht-benoetigt"
    try:
        modelle = [m.model_dump() for m in openai.OpenAI(base_url=base_url, api_key=schluessel).models.list()]
    except openai.APIError as e:
        print(f"Modellsuche bei {base_url} fehlgeschlagen: {e}")
        return
    treffer = {b: [{k: m.get(k) for k in ("id", "name", "context_length", "pricing", "description")}
                   for m in modelle if b.lower() in f"{m.get('id', '')} {m.get('name', '')}".lower()]
               for b in suche.get("begriffe", [])}
    (berichte / "modellsuche.json").write_text(json.dumps({"base_url": base_url, "anzahl_modelle": len(modelle), "treffer": treffer},
                                                          ensure_ascii=False, indent=2), encoding="utf-8")
    for begriff, liste in treffer.items():
        print(f"Modellsuche '{begriff}': " + (", ".join(m["id"] for m in liste) if liste else "keine Treffer"))


def _stichprobe(args) -> None:
    from pathlib import Path

    from .stichprobe import sammle_nachrichten, ziehe_stichprobe
    alle = sammle_nachrichten(args.laeufe)
    stichprobe = ziehe_stichprobe(alle, args.anzahl, args.seed)
    Path(args.ausgabe).write_text("".join(json.dumps(n, ensure_ascii=False) + "\n" for n in stichprobe), encoding="utf-8")
    print(f"{len(stichprobe)} von {len(alle)} Nachrichten → {args.ausgabe}")


def _urteile_sammeln(auftrag: dict, berichte) -> None:
    """Richter beurteilen Nachrichten – ohne menschliche Labels zu kennen.

    `stichprobe`: eine Datei oder eine Liste. Einträge ohne `id` bekommen T001, T002, ...; tragen sie ein Label
    (`zulaessig`, wie im selbst geschriebenen Testset), werden Kennzahlen gleich mitgerechnet.
    `modelle`: Voreinstellungen (`deepseek`, `openrouter:<id>`) als LLM-Compliance-Abteilung (Regeln + RAG + LLM) oder
    `jev` / `jev:<modell-id>` für Jev über die Decisions-API (liefert eine Wahrscheinlichkeit statt einer Begründung).
    """
    from .agents.compliance import ComplianceAbteilung
    from .eval_compliance import kennzahlen
    from .llm.jev import STANDARD_MODELL, JevRichter
    from .metrics import auc
    from .stichprobe import lade_jsonl
    dateien = auftrag["stichprobe"] if isinstance(auftrag["stichprobe"], list) else [auftrag["stichprobe"]]
    for name in auftrag.get("modelle", []):
        if name == "jev" or name.startswith("jev:"):
            import os
            if not os.environ.get("OPENROUTER_API_KEY"):
                print(f"Richter {name} übersprungen: OPENROUTER_API_KEY ist leer (Repository-Secret genau so benennen).")
                continue
            richter = JevRichter(name.split(":", 1)[1] if ":" in name else STANDARD_MODELL)
            pruefe = richter.pruefe
        else:
            spec = voreinstellung(name).model_copy(update={"temperature": 0.0})
            if auftrag.get("denken"):
                zusatz = DENKEN[auftrag["denken"]] or {}
                spec = spec.model_copy(update={"extra_body": ({k: v for k, v in (spec.extra_body or {}).items() if k != "reasoning"} | zusatz) or None})
            try:
                _pruefe_modell(spec, berichte)
            except SystemExit as e:  # ein ausgefallener Richter soll die anderen nicht verhindern
                print(f"Richter {name} übersprungen: {e}")
                continue
            richter, pruefe = None, ComplianceAbteilung(ComplianceConfig(modus="filter", llm=spec)).pruefe_nachricht
        for datei_pfad in dateien:
            eintraege = lade_jsonl(datei_pfad)
            zeilen, fehler_in_folge = [], 0
            for i, n in enumerate(eintraege, 1):
                if fehler_in_folge >= 5:  # z. B. Tageslimit erreicht: keine Anfragen mehr verbrennen
                    u = {"status": "fehler", "fehler": "übersprungen nach 5 Fehlern in Folge"}
                else:
                    u = pruefe((n.get("quelle") or {}).get("von", "Shop X"), n["text"])
                # Springt bei einem LLM-Fehler die Regel-Schicht ein, ist das kein Urteil dieses Richters.
                status = "fehler" if u.get("fehler") else u["status"]
                fehler_in_folge = fehler_in_folge + 1 if status == "fehler" else 0
                zeilen.append({"id": n.get("id", f"T{i:03d}"), "status": status, "kategorie": u.get("kategorie"),
                               "begruendung": u.get("begruendung"), "p_unzulaessig": u.get("p_unzulaessig"),
                               "fehler": u.get("fehler")})
            stamm = Path(datei_pfad).stem
            ziel = berichte / (f"urteile_{kurz(name)}.jsonl" if datei_pfad == dateien[0] else f"urteile_{kurz(name)}_{stamm}.jsonl")
            ziel.write_text("".join(json.dumps(z, ensure_ascii=False) + "\n" for z in zeilen), encoding="utf-8")
            gueltig = [(n, z) for n, z in zip(eintraege, zeilen) if z["status"] != "fehler"]
            zusammenfassung = {"nachrichten": len(zeilen), "fehler": len(zeilen) - len(gueltig),
                               "blockiert": sum(z["status"] == "blockiert" for _, z in gueltig)}
            if gueltig and all("zulaessig" in n for n, _ in gueltig):  # gelabeltes Testset: gleich auswerten
                labels = [not n["zulaessig"] for n, _ in gueltig]
                zusammenfassung |= kennzahlen(labels, [z["status"] == "blockiert" for _, z in gueltig])
                if all(z["p_unzulaessig"] is not None for _, z in gueltig):
                    zusammenfassung["auc"] = round(auc(labels, [z["p_unzulaessig"] for _, z in gueltig]), 3)
            (berichte / f"{ziel.stem}_kennzahlen.json").write_text(json.dumps(zusammenfassung, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Urteile {name} über {stamm}: {json.dumps(zusammenfassung, ensure_ascii=False)} → {ziel}")
        if richter is not None and richter.erste_rohantwort is not None:
            (berichte / f"rohantwort_{kurz(name)}.json").write_text(json.dumps(richter.erste_rohantwort, ensure_ascii=False, indent=2), encoding="utf-8")


def _richter_vergleich(args) -> None:
    from pathlib import Path

    from .stichprobe import lade_jsonl, vergleiche_richter

    def lies(angaben):  # "name=pfad" oder nur "pfad" (Name aus dem Dateinamen)
        paare = [a.split("=", 1) if "=" in a else (Path(a).stem.removeprefix("urteile_"), a) for a in angaben or []]
        return {name: lade_jsonl(pfad) for name, pfad in paare}
    r = vergleiche_richter(lade_jsonl(args.stichprobe), lies(args.urteile), lies(args.wiederholung))
    print(json.dumps({k: v for k, v in r.items() if k != "strittig"}, ensure_ascii=False, indent=2))
    print(f"{len(r.get('strittig', []))} strittige Nachrichten (vollständig in der Ausgabedatei)")
    if args.ausgabe:
        Path(args.ausgabe).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")


def _verbot_auswerten(args) -> None:
    from pathlib import Path

    from .verbot import als_text, lade_handcodierung, lade_verbotslaeufe, werte_aus
    messungen = lade_verbotslaeufe(args.laeufe, args.modell)
    r = werte_aus(messungen, lade_handcodierung(args.handcodierung))
    print(als_text(messungen, r))
    if args.ausgabe:
        Path(args.ausgabe).write_text(json.dumps({"auswertung": r, "laeufe": messungen}, ensure_ascii=False, indent=2),
                                      encoding="utf-8")


def _labels_auswerten(args) -> None:
    from pathlib import Path

    from .stichprobe import lade_jsonl, lade_labels, werte_labels_aus
    urteile = {Path(p).stem.removeprefix("urteile_"): lade_jsonl(p) for p in args.urteile or []}
    r = werte_labels_aus(lade_jsonl(args.stichprobe), lade_labels(args.labels), urteile)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if args.ausgabe:
        Path(args.ausgabe).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")


def _auftrag(args) -> None:
    """Arbeitet eine Auftragsdatei ab: mehrere Läufe, optional Guardrail-Evaluation, danach der Bericht.

    Gedacht für lange Versuchsreihen ohne Aufsicht, z. B. in GitHub Actions. Optionale Felder:
    budget_usd / reserve_usd (Budgetwächter über alle Läufe), zeitlimit_min (pro Lauf).
    """
    from pathlib import Path

    import yaml

    from .bericht import erstelle_bericht
    from .eval_compliance import evaluiere, lade_testset
    from .kosten import Budgetwaechter, guthaben_usd, openrouter_konto
    from .runner import fuehre_experiment_aus
    import os
    auftrag = yaml.safe_load(Path(args.datei).read_text(encoding="utf-8"))
    print("Schlüssel vorhanden: " + ", ".join(f"{n} {'ja' if os.environ.get(n) else 'nein'}"
                                              for n in ("DEEPSEEK_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY")))
    modell, richter = auftrag.get("modell"), auftrag.get("compliance_modell")
    berichte = Path(args.berichte)
    berichte.mkdir(parents=True, exist_ok=True)
    konto = openrouter_konto()
    if konto:
        (berichte / "openrouter_konto.json").write_text(json.dumps(konto, indent=2), encoding="utf-8")
        print(f"OpenRouter-Konto: {konto['gratis_anfragen_pro_tag']} Anfragen pro Tag an Gratismodelle "
              f"({'nie Guthaben gekauft' if konto.get('is_free_tier') else 'Guthaben schon einmal gekauft'}); {json.dumps(konto)}")
    elif os.environ.get("OPENROUTER_API_KEY"):
        print("OpenRouter-Konto: Abfrage fehlgeschlagen – Schlüssel ungültig oder OpenRouter nicht erreichbar.")
    if auftrag.get("modellsuche"):
        _modellsuche(auftrag["modellsuche"], berichte)
    spec = voreinstellung(modell) if modell else LLMSpec()
    richter_spec = voreinstellung(richter).model_copy(update={"temperature": 0.0}) if richter else spec
    zu_pruefen = {spec.kurzname: spec, richter_spec.kurzname: richter_spec}
    for eintrag in auftrag.get("laeufe", []):  # einzelne Läufe dürfen ein anderes Modell nutzen (z. B. Probelauf mehrerer Modelle)
        if eintrag.get("modell"):
            s = voreinstellung(eintrag["modell"])
            zu_pruefen[s.kurzname] = s
    for s in zu_pruefen.values():
        _pruefe_modell(s, berichte)
        if auftrag.get("nur_gratis"):
            _pruefe_gratis(s, berichte)
    stufen = {e.get("denken", auftrag.get("denken")) for e in auftrag.get("laeufe", [])} | {auftrag.get("denken")}
    if "maximal" in stufen:
        DENKEN["maximal"] = {"reasoning": {"effort": _denkstufe_pruefen(spec)}}
    waechter = None
    if auftrag.get("budget_usd"):
        waechter = Budgetwaechter(spec, float(auftrag["budget_usd"]), float(auftrag.get("reserve_usd", 0.5)))
        quelle = f"Guthaben {waechter.start_guthaben:.2f} USD" if waechter.start_guthaben is not None else "ohne Guthaben-Abfrage"
        print(f"Budget {waechter.budget:.2f} USD ({quelle})")
    if auftrag.get("urteile_sammeln"):  # zuerst: kostet wenig und soll nicht am Budget der Läufe scheitern
        _urteile_sammeln(auftrag["urteile_sammeln"], berichte)
    ergebnisse, ausgefallen = [], set()
    for eintrag in auftrag.get("laeufe", []):
        eintrag_modell = eintrag.get("modell", modell)
        if waechter and waechter.erschoepft:
            print(f"Budget erschöpft – {eintrag['config']} entfällt.")
            continue
        if eintrag_modell in ausgefallen:
            # Z. B. Tageslimit eines Gratismodells erreicht: weitere Läufe würden nur weitere Anfragen verbrennen.
            print(f"Modell {eintrag_modell} ausgefallen – {eintrag['config']} entfällt (später erneut starten).")
            continue
        cfg = lade_config(eintrag["config"])
        temperatur = eintrag.get("compliance_temperatur", auftrag.get("compliance_temperatur"))
        cfg = mit_modell(cfg, eintrag_modell, eintrag.get("compliance_modell", richter), temperatur) if eintrag_modell else cfg
        if eintrag.get("denken", auftrag.get("denken")):
            cfg = mit_denken(cfg, eintrag.get("denken", auftrag.get("denken")))
        cfg.runden = eintrag.get("runden", cfg.runden)
        cfg.wiederholungen = eintrag.get("wiederholungen", cfg.wiederholungen)
        if zusatz := eintrag.get("zusatz", auftrag.get("zusatz")):
            # z. B. eine Replikation mit anderer Rundenzahl: eigener Versuchsname, damit sie sich nicht mit älteren Läufen mischt
            cfg.name = f"{cfg.name}_{zusatz}"
            cfg.titel = f"{cfg.titel} · {zusatz.capitalize()}" if cfg.titel else cfg.titel
        neu = fuehre_experiment_aus(cfg, args.ausgabe, waechter, eintrag.get("zeitlimit_min", auftrag.get("zeitlimit_min")),
                                    eintrag.get("erste_wiederholung", 1))
        if any((e.get("abbruch") or {}).get("art") == "ModellAusfall" for e in neu):
            ausgefallen.add(eintrag_modell)
        ergebnisse += neu
    if auftrag.get("guardrail_evaluation") and not (waechter and waechter.erschoepft):
        testset = auftrag.get("guardrail_testset", "evaluation/compliance_testset.jsonl")
        r = evaluiere(ComplianceConfig(llm=richter_spec.model_copy(update={"temperature": 0.0})), lade_testset(testset))
        datei = berichte / f"guardrail_{Path(testset).stem}_{kurz(richter or modell or spec.model)}.json"
        datei.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Guardrail-Evaluation: {json.dumps(r['ergebnisse'], ensure_ascii=False)} → {datei}")
    kosten = {"geschaetzt_usd": round(sum(e.get("kosten_usd_geschaetzt") or 0 for e in ergebnisse), 4)}
    if waechter and waechter.start_guthaben is not None:
        danach = guthaben_usd(spec)
        kosten |= {"guthaben_vorher_usd": waechter.start_guthaben, "guthaben_nachher_usd": danach,
                   "verbraucht_usd": None if danach is None else round(waechter.start_guthaben - danach, 4)}
    (berichte / "kosten.json").write_text(json.dumps(kosten, indent=2), encoding="utf-8")
    print(f"Kosten: {json.dumps(kosten)}")
    if any(Path(args.ausgabe).glob("*/runden.jsonl")):
        print(f"Bericht geschrieben: {erstelle_bericht(args.ausgabe, berichte)}")
    ausfaelle = [e for e in ergebnisse if (e.get("abbruch") or {}).get("art") == "ModellAusfall"]
    if ausfaelle:
        raise SystemExit(f"{len(ausfaelle)} Lauf/Läufe wegen Modellausfall abgebrochen – Protokoll prüfen.")


def _eval_retrieval(args) -> None:
    """Vergleicht Suchverfahren auf evaluation/retrieval_testset.jsonl (Hit@k, MRR) und schreibt reports/retrieval.json."""
    from .config import RetrievalConfig
    from .eval_retrieval import bewerte, lade_testset, tabelle
    from .rag import erstelle_retriever
    testset = lade_testset(args.testset)
    varianten = {"BM25": None}
    if "hybrid" in args.verfahren:
        varianten["Hybrid (BM25 + Embeddings)"] = RetrievalConfig(verfahren="hybrid", reranker_modell=None)
        if not args.ohne_reranker:
            varianten["Hybrid + Reranker"] = RetrievalConfig(verfahren="hybrid")
    ergebnisse = {}
    for name, cfg in varianten.items():
        retriever = erstelle_retriever(args.wissensbasis, cfg)
        ergebnisse[name] = bewerte(retriever, testset, args.k)
        if getattr(retriever, "reranker_fehler", None):
            print(f"Hinweis: Reranker nicht verfügbar ({retriever.reranker_fehler}) – {name} entspricht der Fusion ohne Reranker.")
    berichte = Path("reports")
    berichte.mkdir(exist_ok=True)
    (berichte / "retrieval.json").write_text(json.dumps(ergebnisse, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(testset)} Anfragen, Wissensbasis {args.wissensbasis}\n")
    print(tabelle(ergebnisse, args.k))
    for name, e in ergebnisse.items():
        for z in e["verfehlt"]:
            print(f"  verfehlt ({name}): {z['anfrage']} → {', '.join(z['treffer'])}")


def _mcp(args) -> None:
    from .mcp_server import erstelle_server
    from .config import RetrievalConfig
    retrieval = RetrievalConfig.model_validate_json(args.retrieval) if args.retrieval else None
    erstelle_server(args.wissensbasis, retrieval).run("stdio")


def _monitor(args) -> None:
    from .monitor import baue
    r = baue([Path(o) for o in args.laeufe], Path(args.ausgabe))
    print(f"Monitor geschrieben: {r['datei']} ({r['versuche']} Versuche, {r['laeufe']} Läufe, {r['kb']} KB) – im Browser öffnen")


def _highlights(args) -> None:
    from .highlights import als_text, firmen, kanal_art, kundenstimmen
    laeufe = []
    for meta_datei in sorted(Path(args.laeufe).rglob("meta.json")):
        meta = json.loads(meta_datei.read_text(encoding="utf-8"))
        profile = (meta["config"].get("agenten") or {}).get("profile") or []
        datei = meta_datei.parent / "runden.jsonl"
        if not profile or not datei.exists():
            continue
        roh = [json.loads(z) for z in datei.read_text(encoding="utf-8").splitlines() if z.strip()]
        if roh:
            laeufe.append({"name": meta["name"], "wiederholung": meta["wiederholung"],
                           "firmen": firmen(roh, profile, meta["benchmarks"]), "kunden": kundenstimmen(roh), "kanal": kanal_art(roh)})
    text = als_text(laeufe) if laeufe else "Keine Läufe mit Firmenprofilen gefunden."
    if args.ausgabe:
        Path(args.ausgabe).write_text(text, encoding="utf-8")
    print(text)


def _bericht(args) -> None:
    from .bericht import erstelle_bericht
    print(f"Bericht geschrieben: {erstelle_bericht(args.laeufe, args.ausgabe)}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="python -m kartell", description="KI-Kartell: Preisagenten im simulierten Markt")
    sub = p.add_subparsers(dest="befehl", required=True)

    s = sub.add_parser("benchmark", help="Nash- und Monopolpreis für eine Konfiguration berechnen")
    s.add_argument("config")
    s.set_defaults(fn=_benchmark)

    s = sub.add_parser("schaetzung", help="Kosten eines Experiments schätzen")
    s.add_argument("config")
    s.add_argument("--modell", help="Claude ersetzen: deepseek, apertus, openrouter:<id>, swissai:<id> oder litellm:<id>")
    s.add_argument("--compliance-modell", help="anderes Modell für die Compliance-Abteilung (Standard: wie --modell)")
    s.set_defaults(fn=_schaetzung)

    s = sub.add_parser("lauf", help="Experiment ausführen")
    s.add_argument("config")
    s.add_argument("--runden", type=int)
    s.add_argument("--wiederholungen", type=int)
    s.add_argument("--ausgabe", default="runs")
    s.add_argument("--ja", action="store_true", help="ohne Rückfrage zur Kostenschätzung starten")
    s.add_argument("--modell", help="Claude ersetzen: deepseek, apertus, openrouter:<id>, swissai:<id> oder litellm:<id>")
    s.add_argument("--compliance-modell", help="anderes Modell für die Compliance-Abteilung (Standard: wie --modell)")
    s.set_defaults(fn=_lauf)

    s = sub.add_parser("demo", help="Offline-Demo ohne API-Schlüssel")
    s.add_argument("--ausgabe", default="runs")
    s.set_defaults(fn=_demo)

    s = sub.add_parser("eval-compliance", help="Guardrail gegen den Testdatensatz evaluieren")
    s.add_argument("--config", help="Experiment-Config, deren Compliance-Einstellungen verwendet werden")
    s.add_argument("--testset", default="evaluation/compliance_testset.jsonl")
    s.add_argument("--nur-regeln", action="store_true", help="nur die Regel-Schicht (ohne LLM) auswerten")
    s.add_argument("--modell", help="Claude ersetzen: deepseek, apertus, openrouter:<id>, swissai:<id> oder litellm:<id>")
    s.add_argument("--compliance-modell", help="anderes Modell für die Compliance-Abteilung (Standard: wie --modell)")
    s.set_defaults(fn=_eval_compliance)

    s = sub.add_parser("auftrag", help="Mehrere Läufe aus einer Auftragsdatei abarbeiten (z. B. in GitHub Actions)")
    s.add_argument("datei")
    s.add_argument("--ausgabe", default="runs")
    s.add_argument("--berichte", default="reports")
    s.set_defaults(fn=_auftrag)

    s = sub.add_parser("stichprobe", help="Stichprobe echter Agenten-Nachrichten für die Guardrail-Evaluation ziehen")
    s.add_argument("laeufe", nargs="+", help="Ordner mit Läufen (werden rekursiv durchsucht)")
    s.add_argument("--anzahl", type=int, default=120)
    s.add_argument("--seed", type=int, default=7)
    s.add_argument("--ausgabe", default="evaluation/echte_nachrichten.jsonl")
    s.set_defaults(fn=_stichprobe)

    s = sub.add_parser("labels-auswerten", help="Menschliche Labels auswerten: Kappa, Filter, Regeln und LLM-Richter")
    s.add_argument("--stichprobe", default="evaluation/echte_nachrichten.jsonl")
    s.add_argument("--labels", default="evaluation/echte_nachrichten_labels.json",
                   help="Export aus dem Label-Werkzeug (JSON) oder JSONL mit id, rater, urteil")
    s.add_argument("--urteile", nargs="*", help="urteile_<modell>.jsonl aus einem Auftrag")
    s.add_argument("--ausgabe", help="Ergebnis zusätzlich als JSON speichern")
    s.set_defaults(fn=_labels_auswerten)

    s = sub.add_parser("richter-vergleich", help="Ohne menschliche Labels: Regel-Schicht, Filter und KI-Richter untereinander vergleichen")
    s.add_argument("--stichprobe", default="evaluation/echte_nachrichten.jsonl")
    s.add_argument("--urteile", nargs="+", required=True, help="urteile_<modell>.jsonl oder name=pfad, je ein Modell")
    s.add_argument("--wiederholung", nargs="*", help="zweiter Durchgang eines Modells als name=pfad (nur Beständigkeit)")
    s.add_argument("--ausgabe", help="Ergebnis inkl. strittiger Nachrichten als JSON speichern")
    s.set_defaults(fn=_richter_vergleich)

    s = sub.add_parser("verbot-auswerten", help="Verbots-Experiment genau nach der Vorregistrierung auswerten (M1–M6, Regeln 1–4)")
    s.add_argument("laeufe", nargs="+", help="Ordner mit Läufen (werden rekursiv durchsucht)")
    s.add_argument("--modell", default="nemotron-3-ultra", help="nur Läufe dieses Modells (Teil des Ordnernamens)")
    s.add_argument("--handcodierung", default="evaluation/verbot_m6_handcodierung.json")
    s.add_argument("--ausgabe", help="Ergebnis inkl. M6-Kandidaten als JSON speichern")
    s.set_defaults(fn=_verbot_auswerten)

    s = sub.add_parser("eval-retrieval", help="Suchverfahren vergleichen: BM25 gegen Hybrid (Embeddings + Reranker)")
    s.add_argument("--testset", default="evaluation/retrieval_testset.jsonl")
    s.add_argument("--wissensbasis", default="knowledge/wettbewerbsrecht")
    s.add_argument("--verfahren", nargs="+", default=["bm25", "hybrid"], choices=["bm25", "hybrid"])
    s.add_argument("--ohne-reranker", action="store_true", help="nur BM25 und Fusion, ohne Reranker")
    s.add_argument("-k", type=int, default=3)
    s.set_defaults(fn=_eval_retrieval)

    s = sub.add_parser("mcp", help="MCP-Server mit Wissensbasis und Regel-Prüfung starten (stdio)")
    s.add_argument("--wissensbasis", help="Ordner mit Markdown-Dateien (Standard: knowledge/wettbewerbsrecht)")
    s.add_argument("--retrieval", help='Suchverfahren als JSON, z. B. {"verfahren": "hybrid"} (Standard: BM25)')
    s.set_defaults(fn=_mcp)

    s = sub.add_parser("monitor", help="Kartell-Monitor bauen: eine HTML-Seite, die die Läufe Runde für Runde abspielt")
    s.add_argument("laeufe", nargs="+", help="Ordner mit Läufen (werden rekursiv durchsucht)")
    s.add_argument("--ausgabe", default="reports/monitor.html")
    s.set_defaults(fn=_monitor)

    s = sub.add_parser("highlights", help="Beste Momente aus Läufen mit echten Firmen: Zitate je Firma, Stimmen der Kundschaft")
    s.add_argument("laeufe", help="Ordner mit Läufen (wird rekursiv durchsucht)")
    s.add_argument("--ausgabe", help="Ergebnis zusätzlich als Markdown speichern")
    s.set_defaults(fn=_highlights)

    s = sub.add_parser("bericht", help="Auswertung über alle Läufe erstellen")
    s.add_argument("laeufe", nargs="?", default="runs")
    s.add_argument("--ausgabe", default="reports")
    s.set_defaults(fn=_bericht)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
