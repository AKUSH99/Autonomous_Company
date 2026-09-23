# Run 01 · Phase 3 – Entwicklung & Assets (T5–T8)

---

```
=== TICK-REPORT T5 ===
Phase: 3 – Entwicklung & Assets | Meilensteine: Alpha ⏳ (Ende T6) · Beta ⏳ (Ende T8)
Tick-Budget: 5/13 verbraucht · Puffer: unbenutzt
EINGÄNGE: GDD v1.0 (FINAL)
AUFTRÄGE (parallel)
- AUF-005 → DEV: Tech-Design + Projektgerüst · Default: HTML5 Canvas + JS ohne Build-Schritt
- AUF-006 → ART: Art-Style-Guide + Asset-Liste · Default: Lieferstufe 2 (code-basiert)
SCHNITTSTELLE: DEV-Constraints (TDD §6) ↔ ART-Asset-Liste – Producer prüft Abgleich am Tick-Ende
======================
```

---

```
=== ÜBERGABE ===
Von: DEV           An: PRD → ART, QA
Dokument: Tech-Design-Dokument        Version: v1.0   Status: FINAL
Phase / Tick: 3 / T5
Bezug: GDD v1.0, AUF-005
================
```
1. **Tech-Stack:** HTML5 Canvas + Vanilla-JavaScript, kein Build-Schritt. Matrix (MVP-Tempo / Plattform-Fit / Testbarkeit / Assets / Deployment / Risiko): Canvas+JS 5/5/5/4/5/5 · Phaser 4/5/4/5/4/4 · Godot-Web 3/4/2/5/3/3. **Gewählt: Canvas + JS.**
2. **Architektur:** Strikte Trennung **Welt** (`createWorld`, `stepWorld` – reine Simulation, kein Rendering) und **Live-Spiel** (Eingabe, Audio, Rendering, Screens). Feste Zeitschritte (1/60 s) → deterministisch. Zustände: `title · play · pause · win · lose · end` (= S-01…S-05).
3. **Konfiguration:** `config.js` mit GDD-IDs als Schlüssel (`"P-01": 22`). **DEV-D02:** JS-Datei statt JSON, weil `fetch()` unter `file://` blockiert wird und QA das Spiel ohne Server starten soll.
4. **Asset-Pipeline:** `assets.js` (ART) liefert `graphics[ID]`, `sfx[ID]`, `loops[ID]`, `music[ID]`. Fehlt eine ID, zeichnet `game.js` einen Platzhalter bzw. spielt einen Piepton. **Asset-Vertrag (Signaturen):** z. B. `G-006(ctx, ship{x,y,heading,guided,lit,guideFrac}, t)`, `G-012(ctx, x, y, guided, t, frac)`, SFX als `{ layers:[{wave, freq:[start,end], dur, attack, gain, filter}] }`.
5. **Projektstruktur:** `index.html` · `config.js` (GD) · `assets.js` (ART) · `game.js` (DEV).
6. **Constraints für ART:** logisch 960 × 540, Vektorgrafik per Canvas-Pfad, Objekte ≤ 40 px, Synthese über Web Audio (Wellenformen sine/triangle/square/sawtooth/noise), max. ~20 gleichzeitige Stimmen.
7. **Feature-Plan:** Alpha (T6): M-01…M-05, alle Screens, Platzhalter · Beta (T8): Assets, Audio, Tutorial, Sterne, Regen (COULD, günstig).
8. **Performance-Budget:** 60 fps, Ladezeit < 1 s (keine Dateien außer 4 Skripten).
9. **Debug-API für QA (DEV-D01):** `window.__nachtwache.simulate({seed, level, bot})` spielt eine Nacht im Zeitraffer; `live.setOverride()` steuert den Kegel für Tests und Screenshots; `?debug=1` zeigt Hitboxen, Taste N überspringt eine Nacht.

**Annahmen:** `DEV-A02: Die lichte Breite einer Durchfahrt fehlt im GDD → gapWidth 60/50/40 px je Nacht | Risiko: mittel` → GD bestätigt per Konsultation.
**Entscheidungen:** DEV-D01 (Debug-API), DEV-D02 (config.js statt JSON).
**Status-Update:** TDD FINAL, Gerüst steht, Asset-Vertrag an ART.

---

```
=== ÜBERGABE ===
Von: ART           An: PRD → DEV, GD, QA   CC: CD
Dokument: Art-Style-Guide + Asset-Liste Version: v1.0   Status: FINAL
Phase / Tick: 3 / T5
Bezug: GDD v1.0, TDD §4/§6, Stil-Skizze v0.1, D-004
================
```
**Stil-Säulen:** nachtblau · bernsteinwarm · still. **Anti-Säulen:** Comic-Bunt, Horror.
**Palette:** unverändert zur Stil-Skizze (siehe `game/assets.js`, `C`-Objekt).
**Lesbarkeit (D-004):** Felsen unter der Dunkelheit voll gezeichnet (G-008), darüber Gischt-Umriss mit ~35 % Deckkraft (G-009). Laternen immer sichtbar; geführte Schiffe mit türkisem Ring, der die Rest-Orientierung abbaut (G-012) – Information nie nur über Farbe (Ring = Form).
**Audio:** Nebelhorn (Sägezahn + Tiefpass), Glocke (Sinus-Teiltöne 880/1320/2210 Hz), Krachen (Rauschen + Sinus-Thump), Fokus-Summen (220 Hz, gekoppelt an den Fokus), Wellenrauschen (gefiltertes Rauschen mit LFO), Musik a-Moll-Pads 56 BPM.

| Asset-ID | Name | GDD-Bezug | Lieferstufe | Status |
|---|---|---|---|---|
| G-001 | Meer mit Wellenlinien | – | 2 | final (T6) |
| G-002 / G-003 | Insel / Leuchtturm (Draufsicht) | M-01 | 2 | final (T6) |
| G-004 (+G-005) | Lichtkegel weit / Fokus (ein Asset, Parameter `focus`) | M-01, M-02 | 2 | final (T6) |
| G-006 (+G-007) | Schiff verloren / geführt (Parameter `guided`) | M-03 | 2 | final (T6) |
| G-008 / G-009 | Fels / Gischt-Umriss | M-04, D-004 | 2 | final (T6) |
| G-010 | Wrack-Effekt | M-04 | 2 | final (T7) |
| G-011 | Hafenring mit Anlegelichtern | M-05 | 2 | final (T6) |
| G-012 | Laterne + Orientierungsring | M-03 | 2 | final (T6) |
| G-013–G-016 | Panel, Stern, Fokus-Button, Icons | S-01…S-05, AC-11 | 2 | final (T7) |
| G-017 | Regen (Sturmnacht, COULD) | L-03 | 2 | final (T7) |
| SFX-001…SFX-008 | Nebelhorn, Glocke, Krachen, Fokus-Summen, Klick, Nacht geschafft, Nacht verloren, Wellen | alle | 2 | final (T7) |
| MUS-001 | Nachtthema | S-01…S-05 | 2 | final (T7) |

Budget: 17 Grafik-IDs (≤ 25), 8 SFX (≤ 10), 1 Musik (≤ 2). **Lizenz aller Assets:** eigene Erstellung.
**Status-Update:** Style-Guide und Asset-Liste FINAL, passt zum Asset-Vertrag.

---

```
=== TICK-REPORT T6 ===
Phase: 3 | Meilensteine: Alpha ✅ · Beta ⏳
Tick-Budget: 6/13 verbraucht
EINGÄNGE: DEV Alpha 0.1.0-alpha · QA Smoke-Test · ART Batch 1 (in Arbeit)
ENTSCHEIDUNGEN: D-006 DEV-D02 (config.js) übernommen, betrifft GD · D-007 Gate Alpha GO
AUFTRÄGE: AUF-008 → DEV Content · AUF-009 → ART Batch 2 + Audio · AUF-010 → MKT Positionierung (T7)
======================
```

```
=== ÜBERGABE ===
Von: DEV           An: PRD, QA            CC: ART
Dokument: Build-Report Alpha           Version: 0.1.0-alpha   Status: FINAL
Phase / Tick: 3 / T6
================
```
**Start:** `game/index.html` im Browser öffnen. **Feature-Mapping:** M-01 ✅ · M-02 ✅ · M-03 ✅ · M-04 ✅ · M-05 ✅ · S-01…S-05 ✅ · Tutorial ✅ · Sterne ✅ · Touch ✅. **Assets:** alle Platzhalter (assets.js folgt). **Bekannte Probleme:** Konsolenmeldung „Failed to load resource", weil `assets.js` noch fehlt (erwartet).

```
=== ÜBERGABE ===
Von: QA            An: PRD, DEV
Dokument: Smoke-Test-Report Alpha      Version: v1.0   Status: FINAL
Phase / Tick: 3 / T6
Bezug: Build 0.1.0-alpha · Testmodus A (Headless-Chromium, Skript qa/smoke_test.js)
================
```
**15/15 Checks bestanden:** Titel → Start → Kegel folgt Zeiger → Fokus → Schiff erscheint → Pause friert Zeit ein → Niederlage ohne Licht → Wiederholen → Sieg → Nacht 2 → Nacht 3 → „Alle Nächte geschafft" → Titel. **Keine JavaScript-Laufzeitfehler.** Einziger Konsolenfehler: fehlendes `assets.js` (von DEV angekündigt, kein Bug).
**Befund Konfidenz hoch · keine kritischen Bugs.** Ergebnisse: `qa/results/alpha_smoke.json`, Screenshots `qa/screenshots/alpha_smoke_*.png`.

---

```
=== TICK-REPORT T7 ===
Phase: 3 | Beta ⏳
Tick-Budget: 7/13 verbraucht
EINGÄNGE: ART Batch 1 + 2 (assets.js, 17 Grafik-, 8 SFX-, 1 Musik-Asset) · DEV Content komplett · MKT Positionierungs-Entwurf
AUFTRÄGE: AUF-011 → DEV Beta (Assets integrieren) · AUF-012 → ART Asset-Check im Build (T8)
======================
```

```
=== ÜBERGABE ===
Von: MKT           An: PRD            CC: CD
Dokument: Positionierungs-Entwurf + Teaser-Plan Version: v0.1   Status: ENTWURF
Phase / Tick: 3 / T7
================
```
**Positionierung:** Für Menschen, die in kurzen Pausen etwas Ruhiges mit Spannung suchen, ist *Nachtwache* ein Browser-Lotsenspiel, in dem ein einziger Lichtkegel über Rettung und Schiffbruch entscheidet. Anders als hektische Arcade-Spiele setzt es auf Atmosphäre und kluge Prioritäten.
**Teaser (Absicht, nicht Tatsache):** T8 Devlog „Wir bauen ein Spiel, in dem Licht das einzige Werkzeug ist" (Reddit r/WebGames, GIF aus Beta) · T9 Kurzclip „Drei Schiffe, ein Licht".
**Hype-Startwert: 12/100** (Simulationswert – starke USP, noch kein Material).
**CD-Vision-Check:** ✅ passt.

---

```
=== TICK-REPORT T8 ===
Phase: 3 | Meilensteine: Alpha ✅ · Beta ✅
Tick-Budget: 8/13 verbraucht · Puffer: unbenutzt
KERNWERTE      aktuell  Ziel  Quelle
Spaß           7        8     CD-Prognose (QA misst in T9)
Kreativität    8        8     CD-Prognose
Grafik         7        7     ART-Asset-Check
Sound          6        6     ART-Prognose
Bugs offen     K:0 M:0 N:1   (BUG-003)
Hype           22/100         MKT-Schätzung
ENTSCHEIDUNGEN: D-008 Gate Beta GO; BUG-003 als NIEDRIG in den ersten Fix-Zyklus
AUFTRÄGE: AUF-013 → QA Volltest + Mock-Review v1 (T9)
======================
```

```
=== ÜBERGABE ===
Von: DEV           An: PRD, QA            CC: ART, MKT
Dokument: Build-Report Beta            Version: 0.2.0-beta   Status: FINAL
Phase / Tick: 3 / T8
================
```
**Feature-Mapping:** alle MUST ✅ · SHOULD (Sterne, Tutorial) ✅ · COULD: Regen ✅, Nebelbänke ⬜, Schiffstypen ⬜, Endlos-Modus ⬜. **Assets:** 17/17 Grafik final, 8/8 SFX, 1/1 Musik – keine Platzhalter mehr. **Smoke-Test-Wiederholung:** 15/15, keine Konsolenfehler (`qa/results/beta_smoke.json`).
**Test-Hinweise für QA:** `__nachtwache.simulate()` für Balancing-Läufe, `?seed=` für reproduzierbare Nächte.

```
=== ÜBERGABE ===
Von: ART           An: PRD, DEV
Dokument: Asset-Check im Beta-Build     Version: v1.0   Status: FINAL
Phase / Tick: 3 / T8
================
```
Alle Assets korrekt integriert, Gischt-Umrisse (D-004) wirken wie geplant. **BUG-003 (NIEDRIG):** Der Lichtkegel wirkt über dem blauen Meer kühl-weißlich statt bernsteinfarben – die additive Mischung mit dem Meeresblau neutralisiert den Gelbton. Vorschlag: satteres Orange mit etwas mehr Deckkraft im Kern.
