"""Kommandozeile: python -m kartell <befehl> ..."""
from __future__ import annotations

import argparse
import json
import sys

from .config import OPENROUTER_URL, ComplianceConfig, LLMSpec, kurz, lade_config, mit_modell, voreinstellung


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
    """LLM-Richter beurteilen die Stichprobe echter Nachrichten – ohne die menschlichen Labels zu kennen."""
    from .agents.compliance import ComplianceAbteilung
    from .stichprobe import lade_jsonl
    stichprobe = lade_jsonl(auftrag["stichprobe"])
    for name in auftrag.get("modelle", []):
        spec = voreinstellung(name).model_copy(update={"temperature": 0.0})
        _pruefe_modell(spec, berichte)
        abteilung = ComplianceAbteilung(ComplianceConfig(modus="filter", llm=spec))
        zeilen, fehler = [], 0
        for n in stichprobe:
            u = abteilung.pruefe_nachricht(n["quelle"]["von"], n["text"])
            fehler += u.get("fehler") is not None
            zeilen.append({"id": n["id"], "status": u["status"], "kategorie": u.get("kategorie"),
                           "begruendung": u.get("begruendung"), "fehler": u.get("fehler")})
        datei = berichte / f"urteile_{kurz(name)}.jsonl"
        datei.write_text("".join(json.dumps(z, ensure_ascii=False) + "\n" for z in zeilen), encoding="utf-8")
        blockiert = sum(z["status"] == "blockiert" for z in zeilen)
        print(f"Urteile {name}: {blockiert}/{len(zeilen)} blockiert, {fehler} LLM-Fehler → {datei}")


def _labels_auswerten(args) -> None:
    from pathlib import Path

    from .stichprobe import lade_jsonl, werte_labels_aus
    urteile = {Path(p).stem.removeprefix("urteile_"): lade_jsonl(p) for p in args.urteile or []}
    r = werte_labels_aus(lade_jsonl(args.stichprobe), lade_jsonl(args.labels), urteile)
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
    from .kosten import Budgetwaechter, guthaben_usd
    from .runner import fuehre_experiment_aus
    auftrag = yaml.safe_load(Path(args.datei).read_text(encoding="utf-8"))
    modell, richter = auftrag.get("modell"), auftrag.get("compliance_modell")
    berichte = Path(args.berichte)
    berichte.mkdir(parents=True, exist_ok=True)
    if auftrag.get("modellsuche"):
        _modellsuche(auftrag["modellsuche"], berichte)
    spec = voreinstellung(modell) if modell else LLMSpec()
    richter_spec = voreinstellung(richter).model_copy(update={"temperature": 0.0}) if richter else spec
    for s in {spec.kurzname: spec, richter_spec.kurzname: richter_spec}.values():
        _pruefe_modell(s, berichte)
    waechter = None
    if auftrag.get("budget_usd"):
        waechter = Budgetwaechter(spec, float(auftrag["budget_usd"]), float(auftrag.get("reserve_usd", 0.5)))
        quelle = f"Guthaben {waechter.start_guthaben:.2f} USD" if waechter.start_guthaben is not None else "ohne Guthaben-Abfrage"
        print(f"Budget {waechter.budget:.2f} USD ({quelle})")
    if auftrag.get("urteile_sammeln"):  # zuerst: kostet wenig und soll nicht am Budget der Läufe scheitern
        _urteile_sammeln(auftrag["urteile_sammeln"], berichte)
    ergebnisse = []
    for eintrag in auftrag.get("laeufe", []):
        if waechter and waechter.erschoepft:
            print(f"Budget erschöpft – {eintrag['config']} entfällt.")
            continue
        cfg = lade_config(eintrag["config"])
        temperatur = eintrag.get("compliance_temperatur", auftrag.get("compliance_temperatur"))
        cfg = mit_modell(cfg, modell, richter, temperatur) if modell else cfg
        cfg.runden = eintrag.get("runden", cfg.runden)
        cfg.wiederholungen = eintrag.get("wiederholungen", cfg.wiederholungen)
        ergebnisse += fuehre_experiment_aus(cfg, args.ausgabe, waechter, eintrag.get("zeitlimit_min", auftrag.get("zeitlimit_min")),
                                            eintrag.get("erste_wiederholung", 1))
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


def _mcp(args) -> None:
    from .mcp_server import erstelle_server
    erstelle_server(args.wissensbasis).run("stdio")


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
    s.add_argument("--modell", help="Claude ersetzen: deepseek oder openrouter:<modell-id>")
    s.add_argument("--compliance-modell", help="anderes Modell für die Compliance-Abteilung (Standard: wie --modell)")
    s.set_defaults(fn=_schaetzung)

    s = sub.add_parser("lauf", help="Experiment ausführen")
    s.add_argument("config")
    s.add_argument("--runden", type=int)
    s.add_argument("--wiederholungen", type=int)
    s.add_argument("--ausgabe", default="runs")
    s.add_argument("--ja", action="store_true", help="ohne Rückfrage zur Kostenschätzung starten")
    s.add_argument("--modell", help="Claude ersetzen: deepseek oder openrouter:<modell-id>")
    s.add_argument("--compliance-modell", help="anderes Modell für die Compliance-Abteilung (Standard: wie --modell)")
    s.set_defaults(fn=_lauf)

    s = sub.add_parser("demo", help="Offline-Demo ohne API-Schlüssel")
    s.add_argument("--ausgabe", default="runs")
    s.set_defaults(fn=_demo)

    s = sub.add_parser("eval-compliance", help="Guardrail gegen den Testdatensatz evaluieren")
    s.add_argument("--config", help="Experiment-Config, deren Compliance-Einstellungen verwendet werden")
    s.add_argument("--testset", default="evaluation/compliance_testset.jsonl")
    s.add_argument("--nur-regeln", action="store_true", help="nur die Regel-Schicht (ohne LLM) auswerten")
    s.add_argument("--modell", help="Claude ersetzen: deepseek oder openrouter:<modell-id>")
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
    s.add_argument("--labels", default="evaluation/echte_nachrichten_labels.jsonl")
    s.add_argument("--urteile", nargs="*", help="urteile_<modell>.jsonl aus einem Auftrag")
    s.add_argument("--ausgabe", help="Ergebnis zusätzlich als JSON speichern")
    s.set_defaults(fn=_labels_auswerten)

    s = sub.add_parser("mcp", help="MCP-Server mit Wissensbasis und Regel-Prüfung starten (stdio)")
    s.add_argument("--wissensbasis", help="Ordner mit Markdown-Dateien (Standard: knowledge/wettbewerbsrecht)")
    s.set_defaults(fn=_mcp)

    s = sub.add_parser("bericht", help="Auswertung über alle Läufe erstellen")
    s.add_argument("laeufe", nargs="?", default="runs")
    s.add_argument("--ausgabe", default="reports")
    s.set_defaults(fn=_bericht)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
