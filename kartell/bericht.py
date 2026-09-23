"""Auswertung über alle Läufe: Tabelle je Versuchsbedingung und Preisverläufe als Grafik."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .market import Benchmarks
from .metrics import mittelwert_und_streuung, zusammenfassung


def lade_lauf(ordner: Path) -> dict | None:
    meta_datei, runden_datei = ordner / "meta.json", ordner / "runden.jsonl"
    if not meta_datei.exists() or not runden_datei.exists():
        return None
    meta = json.loads(meta_datei.read_text(encoding="utf-8"))
    runden = [json.loads(z) for z in runden_datei.read_text(encoding="utf-8").splitlines() if z.strip()]
    b = meta["benchmarks"]
    benchmarks = Benchmarks(b["nash_preis"], b["monopol_preis"], b["nash_gewinn"], b["monopol_gewinn"], b["grenzkosten"])
    return {"ordner": ordner, "meta": meta, "runden": runden, "benchmarks": benchmarks,
            "kennzahlen": zusammenfassung(runden, benchmarks), "fertig": (ordner / "ergebnis.json").exists()}


def lade_laeufe(wurzel: str | Path) -> list[dict]:
    return [l for o in sorted(Path(wurzel).iterdir()) if o.is_dir() and (l := lade_lauf(o))]


def erstelle_bericht(wurzel: str | Path, ausgabe: str | Path = "reports") -> Path:
    laeufe = [l for l in lade_laeufe(wurzel) if l["runden"]]
    ausgabe = Path(ausgabe)
    ausgabe.mkdir(parents=True, exist_ok=True)
    gruppen: dict[str, list[dict]] = defaultdict(list)
    for l in laeufe:
        gruppen[l["meta"]["name"]].append(l)

    zeilen = ["# Auswertung KI-Kartell", "",
              "Kennzahlen über die zweite Hälfte jedes Laufs (die erste Hälfte gilt als Lernphase). "
              "Mittelwert ± Standardabweichung über die Wiederholungen.", "",
              "| Versuch | Läufe | Modelle | Ø Preis (CHF) | Preisindex | Kollusionsindex | blockiert / Nachrichten |",
              "|---|---|---|---|---|---|---|"]
    for name, gruppe in gruppen.items():
        k = [l["kennzahlen"] for l in gruppe]
        preis = mittelwert_und_streuung(x["mittlerer_preis"] for x in k)
        pi = mittelwert_und_streuung(x["preisindex"] for x in k)
        ki = mittelwert_und_streuung(x["kollusionsindex"] for x in k)
        modelle = ", ".join(sorted(set(gruppe[0]["meta"]["agenten"].values())))
        zeilen.append(f"| {name} | {len(gruppe)} | {modelle} | {preis[0]:.2f} ± {preis[1]:.2f} | "
                      f"{round(pi[0], 2) + 0.0:+.2f} ± {pi[1]:.2f} | {round(ki[0], 2) + 0.0:+.2f} ± {ki[1]:.2f} | "
                      f"{sum(x['blockierte_nachrichten'] for x in k)} / {sum(x['nachrichten'] for x in k)} |")
    zeilen += ["", "Preisindex und Kollusionsindex: 0 = Wettbewerb (Nash), 1 = perfektes Kartell (Monopol).", ""]

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        zeilen.append("_Grafiken übersprungen: matplotlib ist nicht installiert (pip install -e '.[analyse]')._")
    else:
        for name, gruppe in gruppen.items():
            fig, ax = plt.subplots(figsize=(8, 4.2))
            b = gruppe[0]["benchmarks"]
            ax.axhspan(b.nash_preis, b.monopol_preis, color="#2E9C86", alpha=0.08)
            ax.axhline(b.nash_preis, color="#2E9C86", lw=1, ls="--", label=f"Nash {b.nash_preis:.2f}")
            ax.axhline(b.monopol_preis, color="#C0392B", lw=1, ls="--", label=f"Monopol {b.monopol_preis:.2f}")
            for l in gruppe:
                x = [r["runde"] for r in l["runden"]]
                for shop in l["runden"][0]["preise"]:
                    ax.plot(x, [r["preise"][shop] for r in l["runden"]], lw=1.4, alpha=0.8,
                            label=f"W{l['meta']['wiederholung']} {shop}")
            ax.set_title(name)
            ax.set_xlabel("Runde")
            ax.set_ylabel("Preis (CHF)")
            ax.legend(fontsize=7, ncol=3, frameon=False)
            ax.grid(alpha=0.2)
            fig.tight_layout()
            datei = ausgabe / f"{name}.png"
            fig.savefig(datei, dpi=140)
            plt.close(fig)
            zeilen += [f"## {name}", "", f"![Preisverlauf {name}]({datei.name})", ""]

    bericht = ausgabe / "bericht.md"
    bericht.write_text("\n".join(zeilen), encoding="utf-8")
    return bericht
