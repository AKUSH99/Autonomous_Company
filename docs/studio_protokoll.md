# Studio-Protokoll

Gemeinsame Regeln für alle Agenten. Jeder System-Prompt in [`prompts/`](../prompts) enthält die für seine Rolle nötigen Teile davon, damit er eigenständig funktioniert. Diese Datei ist die Übersicht zum Nachschlagen.

## 1. Rollen-Kürzel

| Kürzel | Rolle | Primärer Kernwert |
|---|---|---|
| `PRD` | Producer | – (orchestriert, misst Fortschritt) |
| `CD` | Creative Director | Kreativität |
| `GD` | Game Designer | Spaß |
| `DEV` | Programmierer | Bugs (niedrig halten), Spielgefühl |
| `ART` | Artist / Sound | Grafik, Sound |
| `QA` | Testing | misst alle Kernwerte unabhängig |
| `MKT` | Marketing | Hype |

## 2. Tick-Plan (Standard: 13 Ticks, +2 Puffer)

| Tick | CD | GD | DEV | ART | QA | MKT | Meilenstein |
|---|---|---|---|---|---|---|---|
| T1 | Konzept-Paket | | | | | | |
| T2 | Konzept FINAL | | | | | | Konzept-Freeze |
| T3 | | GDD v0.9 | | | | | |
| T4 | Vision-Check | GDD v1.0 FINAL | Machbarkeits-Check | Stil-Skizze | | | Design-Lock |
| T5 | Vision-Check | Klärungen | TDD + Gerüst | Style-Guide + Asset-Liste | (Testplan) | | |
| T6 | | Klärungen | Alpha | Asset-Batch 1 | Smoke-Test | | Alpha |
| T7 | Vision-Check | Klärungen | Content | Asset-Batch 2 + Audio | | Positionierung + Teaser | |
| T8 | | Klärungen | Beta | Asset-Check | | Teaser | Beta |
| T9 | | | Bereitschaft | | Volltest + Mock-Review v1 | Teaser | |
| T10 | | Balancing-Patch | Fix-Zyklus 1 | Asset-Fixes | Regression | Store-Entwurf | |
| T11 | | Balancing-Patch | Fix-Zyklus 2 → RC | Asset-Fixes | RC-Test + Mock-Review | | Release Candidate |
| T12 | | Faktencheck | Launch-Build | Key-Art | Claims-Check | Launch-Paket FINAL | |
| T13 | | | Hotfix-Bereitschaft | | | Launch-Tag-Plan | **Launch** |

Der Producer ist in jedem Tick aktiv (Tick-Report, Aufträge, Gates, Entscheidungen).

## 3. Nachrichtentypen

| Typ | Von → An | Zweck |
|---|---|---|
| `AUFTRAG` | PRD → Agent | Arbeitsauftrag mit Ziel, Eingaben, Frist und Default |
| `ÜBERGABE` | Agent → Empfänger (über PRD) | Strukturiertes Arbeitsergebnis |
| `BLOCKER` | Agent → PRD | Problem mit Optionen, Empfehlung und Default (Arbeit läuft weiter) |
| `KONSULTATION` | Agent → Agent (CC PRD) | Direkte Klärung ohne Umweg |
| `GATE` | PRD → alle | Go / Go mit Auflagen / No-Go an einem Meilenstein |
| `TICK-REPORT` | PRD → alle | Dashboard, Entscheidungen, Aufträge des Ticks |

Jede Übergabe endet mit den **fünf Pflicht-Abschnitten**:
1. Was ist definiert
2. Annahmen / Unsicherheiten
3. Abhängigkeiten / offene Fragen (jeweils mit Default)
4. Entscheidungen (Was, Wer, Warum, Wann)
5. Status-Update (ein Satz)

## 4. ID-Konventionen

| Muster | Bedeutung | Vergeben von |
|---|---|---|
| `SET-01` | Setup-Entscheidung beim Aufbau des Studios (siehe [Entscheidungs-Protokoll](entscheidungsprotokoll.md)) | PRD |
| `D-001` | Globale Entscheidung während der Simulation | PRD |
| `AUF-001` | Auftrag | PRD |
| `T1` … `T15` | Tick | PRD |
| `<ROLLE>-A01` | Annahme (z. B. `GD-A03`) | jeder Agent |
| `<ROLLE>-Q01` | Offene Frage (z. B. `DEV-Q02`) | jeder Agent |
| `<ROLLE>-D01` | Lokale Entscheidung (z. B. `ART-D01`) | jeder Agent |
| `M-01` / `L-01` / `S-01` / `P-01` / `AC-01` | Mechanik / Level / Screen / Balancing-Parameter / Akzeptanzkriterium | GD |
| `G-001` / `SFX-001` / `MUS-001` | Grafik-Asset / Soundeffekt / Musikstück | ART |
| `BUG-001` | Bug | QA |
| `0.1.0-alpha` … `1.0.0` | Build-Version | DEV |

IDs bleiben über alle Versionen stabil; gestrichene IDs werden als „✂️ gestrichen" markiert, nicht neu vergeben.

## 5. Status- und Bewertungsskalen

| Skala | Werte |
|---|---|
| Dokument-Status | `ENTWURF` · `FINAL` · `BLOCKIERT` |
| Dokument-Version | v0.x Entwurf · v1.0 FINAL · v1.1+ Überarbeitung |
| Feature-Status | ✅ fertig · 🟡 teilweise · ⬜ offen · ✂️ gestrichen |
| Machbarkeit (DEV) | ✅ machbar · ⚠️ mit Vereinfachung · ⛔ nicht im Budget |
| Vision-Check (CD) | ✅ passt · ⚠️ kleine Abweichung · ⛔ kritische Abweichung |
| Bug-Schwere (QA) | KRITISCH · MITTEL · NIEDRIG |
| Release-Empfehlung (QA) | GO · GO MIT AUFLAGEN · NO-GO |
| Gate (PRD) | GO · GO MIT AUFLAGEN · NO-GO |
| Kernwerte | 1–10 (Spaß, Kreativität, Grafik, Sound) · Hype 0–100 |
| Mock-Review | 4 Kritiker × 1–10 = /40 · Launch-Gate ≥ 24 · Ziel ≥ 32 |

## 6. Anti-Deadlock-Regeln

1. **Jeder Blocker enthält einen Default.** Der Agent arbeitet sofort damit weiter.
2. **Der Producer antwortet im selben Tick** – sonst gilt der Default automatisch.
3. **Maximal 2 Iterationen** pro Dokument und pro Konflikt, danach entscheidet der Producer.
4. **Platzhalter statt Warten:** DEV arbeitet mit Platzhalter-Assets, ART beschreibt statt zu blockieren, QA testet statisch, wenn ein Build nicht läuft.
5. **Scope kürzen, nicht Zeit verlängern** – nach einmaligem Puffer von +2 Ticks.

## 7. Prioritätenordnung bei Konflikten

1. Stabilität & Spielbarkeit
2. Tick-Budget & MVP-Scope
3. Spaß des Kern-Loops
4. Lesbarkeit & Verständlichkeit
5. Kreative Vision & Ästhetik
6. Stretch-Goals
