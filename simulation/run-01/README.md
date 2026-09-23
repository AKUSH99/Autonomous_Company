# Run 01 · „Nachtwache"

Der erste vollständige Durchlauf des autonomen Studios: von einem selbst gewählten Startimpuls bis zum Launch eines spielbaren Browser-Spiels.

**Spielen:** [`game/index.html`](game/index.html) im Browser öffnen – keine Installation, kein Server.

## Ergebnis

| | |
|---|---|
| Spiel | **Nachtwache 1.0.0** – Leuchtturm-Lotsenspiel, 3 Nächte, Maus und Touch |
| Ticks | 13/13 + 1 Puffer-Tick |
| Mock-Review | 29/40 (Launch-Gate ≥ 24 ✅, Ziel 32 verfehlt) |
| Kernwerte (QA) | Spaß 7 · Kreativität 8 · Grafik 8 · Sound 6 (Konfidenz niedrig) |
| Bugs bei Launch | 0 kritisch · 1 mittel (Nacht 2 zu leicht) · 1 niedrig |
| Entscheidungen | 15 Producer-Entscheidungen, davon 1 Konfliktlösung (D-004) und 1 Iterationsstopp (D-013) |

## Was echt ist und was simuliert

- **Echt:** Der Code (`game/`), alle QA-Messungen (`qa/` – Skripte laufen im Headless-Chromium gegen die echte Spiellogik, Rohdaten in `qa/results/`), die Screenshots (`marketing/screenshots/`).
- **Simuliert:** Hype-Wert, KPI-Ziele, Mock-Review-Kritiker und der Launch selbst (es wurde nichts veröffentlicht).
- **Ausführungsmodus:** Variante C aus dem README – ein einziges Modell hat die sieben Rollen nacheinander gespielt, jeweils nach dem Rollen-Prompt und im Übergabe-Format. Getrennte Agenten-Instanzen (Variante A) würden unabhängiger urteilen.

## Die Befunde, die das Studio selbst gefunden hat

| Befund | Gefunden von | Gelöst durch |
|---|---|---|
| Felsen im Dunkeln unsichtbar → Kernentscheidung wird Raten | GD (T4) | Producer-Kompromiss D-004 |
| Freie Pfadsuche zu teuer | DEV (T4) | Kreisbahn-Wegpunkte D-005 |
| Beleuchtete Schiffe zerschellen an Felsen (9/480) | QA-Messung (T9) | DEV: Vorausschau-Ausweichen → 2080/2080 |
| Durchfahrten 20 px breiter als spezifiziert | QA-Geometriemessung (T9) | DEV: Riff von Kante zu Kante |
| Ziel-Dauern widersprechen den Spawn-Parametern | QA (T9) | GD revidiert Ziele (D-010) |
| Spiel viel zu leicht (0 % Fehlschlag) | QA-Bots (T9) | 3 Balancing-Patches; Nacht 2 bleibt offen (D-013) |
| QA-Testskript wertet falsch aus | QA selbst (T10) | Skriptfix T11 |
| Werbeaussagen ohne Beleg | QA-Claims-Check (T13) | MKT formuliert um |

## Verlauf

| Phase | Log |
|---|---|
| 1 Ideenfindung (T1–T2) | [`log/phase1_ideenfindung.md`](log/phase1_ideenfindung.md) |
| 2 Design (T3–T4) | [`log/phase2_design.md`](log/phase2_design.md) |
| 3 Entwicklung & Assets (T5–T8) | [`log/phase3_entwicklung.md`](log/phase3_entwicklung.md) |
| 4 Testing & Feedback (T9–T12) | [`log/phase4_testing.md`](log/phase4_testing.md) |
| 5 Marketing & Launch (T13–T14) | [`log/phase5_launch.md`](log/phase5_launch.md) |

Entscheidungen: [`entscheidungen.md`](entscheidungen.md) · Launch-Paket: [`marketing/launch_paket.md`](marketing/launch_paket.md)

## Tests selbst ausführen

```bash
cd simulation/run-01
export NODE_PATH=$(npm root -g)      # global installiertes Playwright
node qa/smoke_test.js                # Hauptpfad Titel → Sieg → Titel
node qa/ui_acceptance_test.js        # Touch, Audio, Reaktionszeit, Lesbarkeit
node qa/balance_test.js balance 40   # Balancing mit 3 Bot-Personas × 40 Seeds
node tools/screenshots.js            # Marketing-Screenshots neu erzeugen
```

## Struktur

```
game/        index.html · config.js (GD) · assets.js (ART) · game.js (DEV)
qa/          Testskripte, results/ (JSON je Build), screenshots/
tools/       Screenshot-Automatik (DEV, Material für Marketing)
marketing/   launch_paket.md, screenshots/
log/         Tick-Reports und Übergaben je Phase
```
