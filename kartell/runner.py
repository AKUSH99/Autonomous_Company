"""Experimente ausführen und protokollieren (eine JSONL-Zeile pro Runde, live lesbar fürs Dashboard)."""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from .config import ExperimentConfig
from .graph import Simulation
from .metrics import zusammenfassung


class LaufProtokoll:
    def __init__(self, ordner: Path):
        self.ordner = ordner
        self.ordner.mkdir(parents=True, exist_ok=True)
        self._runden = (self.ordner / "runden.jsonl").open("a", encoding="utf-8")

    def meta(self, daten: dict) -> None:
        (self.ordner / "meta.json").write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")

    def runde(self, eintrag: dict) -> None:
        self._runden.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
        self._runden.flush()

    def ergebnis(self, daten: dict) -> None:
        self._runden.close()
        (self.ordner / "ergebnis.json").write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")


def fuehre_lauf_aus(cfg: ExperimentConfig, seed: int, ausgabe: str | Path = "runs", ausgabe_konsole: bool = True) -> dict:
    zeit = datetime.now().strftime("%Y%m%d-%H%M%S")
    protokoll = LaufProtokoll(Path(ausgabe) / f"{zeit}_{cfg.name}_w{seed}")
    sim = Simulation(cfg, seed=seed, logger=protokoll)
    protokoll.meta({
        "name": cfg.name, "beschreibung": cfg.beschreibung, "wiederholung": seed, "start": zeit,
        "benchmarks": sim.benchmarks.als_dict(),
        "agenten": {a.name: a.modell for a in sim.agenten},
        "compliance": sim.compliance.modell if sim.compliance else None,
        "config": cfg.model_dump(mode="json"),
    })
    t0 = time.time()
    if ausgabe_konsole:
        print(f"▶ {cfg.name} · Wiederholung {seed} · {cfg.runden} Runden · Nash {sim.benchmarks.nash_preis:.2f} / "
              f"Monopol {sim.benchmarks.monopol_preis:.2f} CHF")
    verlauf = sim.starte()
    ergebnis = zusammenfassung(verlauf, sim.benchmarks) | {"dauer_s": round(time.time() - t0, 1), "ordner": str(protokoll.ordner)}
    protokoll.ergebnis(ergebnis)
    if ausgabe_konsole:
        print(f"  ✓ Preisindex {round(ergebnis['preisindex'], 2) + 0.0:+.2f} · Kollusionsindex {round(ergebnis['kollusionsindex'], 2) + 0.0:+.2f} · "
              f"{ergebnis['blockierte_nachrichten']}/{ergebnis['nachrichten']} Nachrichten blockiert · {protokoll.ordner}")
    return ergebnis


def fuehre_experiment_aus(cfg: ExperimentConfig, ausgabe: str | Path = "runs") -> list[dict]:
    return [fuehre_lauf_aus(cfg, seed, ausgabe) for seed in range(1, cfg.wiederholungen + 1)]
