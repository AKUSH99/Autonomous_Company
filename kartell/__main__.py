"""Kommandozeile: python -m kartell <befehl> ..."""
from __future__ import annotations

import argparse
import json
import sys

from .config import ComplianceConfig, LLMSpec, lade_config


def _benchmark(args) -> None:
    from .market import LogitMarkt
    cfg = lade_config(args.config)
    b = LogitMarkt(cfg.markt).benchmarks()
    print(f"{cfg.name}: {cfg.markt.firmen} Shops, Stückkosten {b.grenzkosten:.2f} CHF")
    print(f"  Nash-Preis    {b.nash_preis:6.2f} CHF   Gewinn pro Shop {b.nash_gewinn:8.2f}")
    print(f"  Monopolpreis  {b.monopol_preis:6.2f} CHF   Gewinn pro Shop {b.monopol_gewinn:8.2f}")


def _schaetzung(args) -> dict:
    from .kosten import schaetze
    cfg = lade_config(args.config)
    s = schaetze(cfg)
    print(f"Kostenschätzung {cfg.name}: {cfg.runden} Runden × {cfg.wiederholungen} Wiederholungen")
    for z in s["zeilen"]:
        usd = "unbekannt" if z["usd"] is None else f"{z['usd']:.2f} USD"
        print(f"  {z['posten']:<28} {z['modell']:<40} {z['aufrufe']:>6} Aufrufe  {usd}")
    print(f"  Summe ≈ {s['usd']:.2f} USD{' (ohne Posten mit unbekanntem Preis)' if s['unvollstaendig'] else ''}")
    return s


def _lauf(args) -> None:
    from .runner import fuehre_experiment_aus
    cfg = lade_config(args.config)
    if args.runden:
        cfg.runden = args.runden
    if args.wiederholungen:
        cfg.wiederholungen = args.wiederholungen
    s = _schaetzung(args) if not args.ja else None
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
        cfg = lade_config(args.config).compliance if args.config else ComplianceConfig(llm=LLMSpec())
    r = evaluiere(cfg, lade_testset(args.testset))
    print(json.dumps(r, ensure_ascii=False, indent=2))


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
    s.set_defaults(fn=_schaetzung)

    s = sub.add_parser("lauf", help="Experiment ausführen")
    s.add_argument("config")
    s.add_argument("--runden", type=int)
    s.add_argument("--wiederholungen", type=int)
    s.add_argument("--ausgabe", default="runs")
    s.add_argument("--ja", action="store_true", help="ohne Rückfrage zur Kostenschätzung starten")
    s.set_defaults(fn=_lauf)

    s = sub.add_parser("demo", help="Offline-Demo ohne API-Schlüssel")
    s.add_argument("--ausgabe", default="runs")
    s.set_defaults(fn=_demo)

    s = sub.add_parser("eval-compliance", help="Guardrail gegen den Testdatensatz evaluieren")
    s.add_argument("--config", help="Experiment-Config, deren Compliance-Einstellungen verwendet werden")
    s.add_argument("--testset", default="evaluation/compliance_testset.jsonl")
    s.add_argument("--nur-regeln", action="store_true", help="nur die Regel-Schicht (ohne LLM) auswerten")
    s.set_defaults(fn=_eval_compliance)

    s = sub.add_parser("bericht", help="Auswertung über alle Läufe erstellen")
    s.add_argument("laeufe", nargs="?", default="runs")
    s.add_argument("--ausgabe", default="reports")
    s.set_defaults(fn=_bericht)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
