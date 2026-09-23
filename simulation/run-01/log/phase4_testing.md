# Run 01 · Phase 4 – Testing & Feedback (T9–T12)

Alle Messwerte stammen aus echten Läufen der Skripte in `qa/` (Rohdaten in `qa/results/*.json`). Balancing-Läufe: 40 Seeds je Nacht und Persona, echte Spiellogik im Headless-Chromium, Zeitraffer.

---

```
=== TICK-REPORT T9 ===
Phase: 4 – Testing & Feedback | Meilenstein: Release Candidate ⏳ (Ende T11)
Tick-Budget: 9/13 verbraucht · Puffer: unbenutzt
AUFTRÄGE: AUF-013 → QA Volltest Beta 0.2.0 + Mock-Review v1
======================
```

```
=== ÜBERGABE ===
Von: QA            An: PRD → DEV, GD, ART
Dokument: Bug- & Feedback-Report Beta  Version: v1.0   Status: FINAL
Phase / Tick: 4 / T9
Bezug: Build 0.2.0-beta, GDD v1.0 · Testmodus A (qa/balance_test.js, qa/ui_acceptance_test.js, qa/smoke_test.js)
================
```

**1. Zusammenfassung:** Stabil (keine Laufzeitfehler, alle Screens erreichbar), Steuerung und Lesbarkeit erfüllen die Kriterien. **Aber:** Das Spiel ist deutlich zu leicht und zu kurz, und durchgehend beleuchtete Schiffe zerschellen in Nacht 3 gelegentlich. **Empfehlung:** Fix-Zyklus.

**2. Akzeptanzkriterien**
| AC | Ergebnis | Beleg |
|---|---|---|
| AC-01 Kegel folgt Zeiger | ✅ | Abweichung < 0,02 rad nach 1 Frame |
| AC-02 Fokus | ✅ | Fokus 1,00 nach 0,4 s Halten |
| AC-03 Orientierungszeit | ✅ | Code und Laufzeit geprüft |
| AC-04 Beleuchtetes Schiff kommt an | ❌ | L-03: **9 von 480** Schiffen gesunken (98 %) |
| AC-05 Wrack / 3 Wracks → S-05 | ✅ | Smoke-Test SMK-09 |
| AC-06 / AC-07 Anlegen / Nacht geschafft | ✅ | SMK-11 bis SMK-13 |
| AC-08 Ohne Input verloren (≥ 80 %) | ❌ | L-01: nur **73 %** |
| AC-09 Casual-Zielwerte | ❌ | siehe Balancing-Befunde |
| AC-10 Pause | ✅ | Spielzeit eingefroren (5,25 s → 5,25 s) |
| AC-11 Touch | ✅ | synthetische Touch-Events (Konfidenz mittel) |
| AC-12 Audio | ⚠️ | AudioContext erst nach Interaktion ✅; Stummschalten nicht prüfbar |
| AC-13 Felsen im Dunkeln | ✅ | Luminanz Felsumriss 102 vs. Meer 11 (Konfidenz mittel) |

**3. Bug-Liste**
```
BUG-001 | MITTEL | M-03/M-04, L-03 | 0.2.0-beta | Konfidenz hoch (Modus A)
Titel: Durchgehend beleuchtete Schiffe zerschellen an äußeren Felsen
Schritte: L-03, ein Schiff gleichzeitig, Fokus-Strahl permanent auf dem Schiff (Seeds 7, 11, 14, 18, 29, 35, 37, 39, 40)
Erwartet (GDD): AC-04 – Hafen ohne Felskontakt (100 %)
Tatsächlich: 9/480 Wracks, alle an äußeren Felsen (Abstand zum Zentrum 234–359 px)
Vermutete Ursache: Bei Frontalkurs auf einen Felsen hebt die Abstoßung die Zielrichtung auf – es fehlt eine seitliche Ausweichkomponente.

BUG-002 | MITTEL | Riff-Geometrie | 0.2.0-beta | Konfidenz hoch
Titel: Durchfahrten ca. 20 px breiter als spezifiziert
Gemessen (lichte Breite, Ø über 40 Seeds): L-01 79,9 px (Soll 60) · L-02 70,5 px (Soll 50) · L-03 62,1 px (Soll 40)
Vermutete Ursache: Felsen sitzen auf einem festen 10°-Raster; das Raster rundet die Lücke nach oben.
Folge: Verlorene Schiffe treiben öfter zufällig hindurch → AC-08 verfehlt, Spiel leichter.

BUG-003 | NIEDRIG | G-004 | gemeldet von ART (T8): Kegel wirkt kühl-weißlich.
BUG-004 | NIEDRIG | Debug-API | Stumm-Zustand nicht auslesbar → AC-12 nicht vollständig prüfbar.
```

**4. Balancing-Befunde (Beta 0.2.0)**
| Nacht | Persona | Fehlschlag | Ø Dauer (Sieg) | GDD-Ziel |
|---|---|---|---|---|
| L-01 | ohne Input | 73 % | – | ≥ 80 % (AC-08) |
| L-01 | Casual | 0 % | 44,6 s | < 10 % · 1,5–3 min |
| L-02 | Casual | 0 % | 54,6 s | 20–40 % · 2–3,5 min |
| L-03 | Casual | 3 % | 67,4 s | 30–50 % · 3–5 min |
| L-03 | Erfahren | 0 % | 69,1 s | – |

**Befund Dauer:** Die Ziel-Dauern sind mit den Spawn-Parametern nicht erreichbar: L-01 hat 5 Schiffe × 8 s Abstand = 40 s plus ca. 10 s Fahrt. `GD-A01` hat nur die Fahrzeit betrachtet.

**5. UX & Spielgefühl:** Casual-Erstspieler: Einstieg sofort klar, die Tutorial-Hinweise greifen. Erfahrene Spielerin: nie unter Druck, max. 2 Schiffe in L-01 sind trivial. Chaos-Tester: keine Softlocks, Pause/Blur robust.

**6. Kernwerte (unabhängig):** Spaß **5** (kein Druck) · Kreativität **8** · Grafik **7** · Sound **6** (Konfidenz **niedrig**: im Headless-Browser nicht hörbar, nur Synthese-Parameter und fehlerfreie Ausführung geprüft).

**7. Mock-Review v1**
| Kritiker | Wertung | Zitat |
|---|---|---|
| Die Casual-Kritikerin | 7/10 | „Sofort verstanden und wunderschön still – aber nach drei Minuten war ich durch." |
| Der Core-Gamer | 4/10 | „Selbst die Sturmnacht bestehe ich fast immer. Wo ist der Druck?" |
| Der Indie-Ästhet | 7/10 | „Licht und Dunkelheit tragen das Spiel. Der Kegel dürfte wärmer leuchten." |
| Die Tech-Reviewerin | 6/10 | „Keine Abstürze. Aber ein Schiff, das ich beleuchte, zerschellt trotzdem – das fühlt sich unfair an." |
| **Gesamt** | **24/40** | |

**8. Testabdeckung & Lücken:** Bots bilden menschliche Wahrnehmung nur näherungsweise ab (sie „sehen" alle Laternen perfekt) → Fehlschlagquoten für echte Menschen vermutlich etwas höher (Konfidenz mittel). Audio nicht hörbar geprüft.

**Status-Update:** Beta getestet: 0 kritische, 2 mittlere, 2 niedrige Bugs, Balancing deutlich zu leicht, Mock-Review 24/40, Empfehlung: Fix-Zyklus.

---

```
=== TICK-REPORT T9 (Fortsetzung: Triage) ===
ENTSCHEIDUNGEN
- D-009: Triage – BUG-001 und BUG-002 fixen (verletzen AC einer MUST-Mechanik bzw. die Spezifikation) · Balancing (AC-08/AC-09) per GD-Patch · BUG-003/004 trivial → laufen im selben Zyklus mit
- D-010: GD darf die Ziel-Dauern revidieren (Originalziele widersprechen den eigenen Spawn-Parametern)
AUFTRÄGE (T10, parallel): AUF-014 → DEV BUG-001/002/004 · AUF-015 → GD Balancing-Patch 1 · AUF-016 → ART BUG-003 · danach AUF-017 → QA Regression
======================
```

---

```
=== TICK-REPORT T10 ===
Tick-Budget: 10/13 verbraucht
EINGÄNGE: DEV Fix-Build 0.2.1-beta · GD Balancing-Patch 1 · ART Asset-Fix · QA Regression
======================
```

**DEV Fix-Report 0.2.1-beta:** BUG-001 – Vorausschau-Ausweichen: Liegt ein Fels innerhalb von 70 px voraus und seitlich näher als Felsradius + 15 px, lenkt das Schiff zur freien Seite. BUG-002 – Riff wird je Segment von Kante zu Kante aufgebaut; Kantenfelsen sitzen exakt auf lichter Breite = gapWidth. BUG-004 – `live.muted` im Debug-API.

**GD Balancing-Patch 1 (GDD v1.1)**
| Param | Alt | Neu | Grund |
|---|---|---|---|
| P-01 | 22° | 18° | Weiter Kegel erfasst zu viele Schiffe gleichzeitig |
| P-05 | 2,5 s | 2,0 s | Mehr Umschalt-Druck |
| P-07 | 24 | 27 px/s | Verlorene Schiffe erreichen das Riff schneller |
| L-01/02/03 Schiffe | 5/8/12 | 7/14/22 | Längere Nächte |
| L-01/02/03 Spawn | 8/6/5 s | 7/5,5/4,5 s | Dichter |
| L-02/03 max. gleichzeitig | 3/4 | 4/5 | Mehr Jonglieren |
| Ziel-Dauer (D-010) | 1,5–3 / 2–3,5 / 3–5 min | **1–2 / 1,5–3 / 2–4 min** | Konsistent mit Spawn-Parametern; Session 5–10 min inkl. Wiederholungen |

**ART:** BUG-003 – Kegel-Verlauf auf satteres Bernstein (`rgba(255,205,120)` → `rgba(255,170,70)`).

```
=== ÜBERGABE ===
Von: QA            An: PRD, DEV, GD
Dokument: Regressions-Report Fix 1     Version: v1.0   Status: FINAL
Bezug: Build 0.2.1-beta, GDD v1.1
================
```
| Befund | Ergebnis |
|---|---|
| BUG-001 / AC-04 | ✅ **0/280 · 0/560 · 0/880** Wracks (100 %) |
| BUG-002 | ✅ lichte Breite exakt 60 / 50 / 40 px (min = max) |
| AC-08 | ✅ ohne Input 100 % verloren in allen Nächten |
| BUG-003 | ✅ visuell geprüft (Screenshot) |
| AC-09 Casual | ❌ **0 % / 0 % / 5 %** Fehlschlag · Ø 55 / 84 / 107 s |
| Smoke-Test | ✅ 15/15 |
| AC-12c | ⚠️ **QA-Skriptfehler:** Prüfung wertete nur die Existenz des Werts aus → Skript in T11 korrigiert |

**Status-Update:** Bugs geschlossen, Balancing weiterhin zu leicht (L-02/L-03).

---

```
=== TICK-REPORT T11 ===
Tick-Budget: 11/13 verbraucht
ENTSCHEIDUNGEN: D-011 Fix-Zyklus 2 nur Balancing (GD-Patch 2) + QA-Skriptfix
======================
```

**GD Balancing-Patch 2 (GDD v1.2)**
| Param | Alt | Neu | Grund |
|---|---|---|---|
| P-05 | 2,0 s | 1,4 s | Hauptstellschraube: Licht muss öfter zurückkehren |
| P-06 | 42 | 38 px/s | Geführte Passage dauert länger |
| P-09 | 0,35 | 0,5 | Verlorene Schiffe halten direkter aufs Riff zu |
| Schiffe L-01/02/03 | 7/14/22 | 8/16/26 | Dauer in den Zielbereich |
| max. gleichzeitig L-02/03 | 4/5 | 5/6 | Mehr Jonglieren |

```
=== ÜBERGABE ===
Von: QA            An: PRD
Dokument: RC-Report 1.0.0-rc1 + Mock-Review Version: v1.0   Status: FINAL
================
```
| Nacht | Casual | Erfahren | Ø Dauer | Ziel Fehlschlag / Dauer | |
|---|---|---|---|---|---|
| L-01 | 0 % | 0 % | 64,6 s | < 10 % / 1–2 min | ✅ |
| L-02 | 0 % | 0 % | 96,6 s | 20–40 % / 1,5–3 min | ❌ Fehlschlag |
| L-03 | 33 % | 20 % | 127,1 s | 30–50 % / 2–4 min | ✅ |

AC-04 ✅ 2000/2000 · AC-08 ✅ · UI-Kriterien 9/9 ✅ (AC-12c jetzt geprüft: stumm → an) · Smoke 15/15 · 0 kritische Bugs.
**Kernwerte:** Spaß 7 · Kreativität 8 · Grafik 8 · Sound 6 (Konfidenz niedrig).
**Mock-Review:** Casual-Kritikerin 8 · Core-Gamer 6 · Indie-Ästhet 7 · Tech-Reviewerin 8 = **29/40**.
„Die Sturmnacht fordert wirklich – aber Nacht 2 plätschert noch dahin." (Core-Gamer)
**Release-Empfehlung: GO MIT AUFLAGEN** (L-02 zu leicht → Schwierigkeitssprung zu L-03).

```
=== GATE: Release Candidate ===
Ergebnis: GO MIT AUFLAGEN
Kriterien: [x] 0 kritische Bugs  [x] mittlere Bugs triagiert  [ ] AC-09 (L-02 verfehlt)  [x] Mock-Review 29/40 ≥ 24  [x] QA-Empfehlung
Auflagen: Gezielter L-02-Patch im Puffer-Tick T12
Protokoll: D-012
=========================
```

**D-012** · RC1 ist freigegeben; **Puffer +1 Tick (T12)** für einen Patch nur an L-02 · Wer: PRD · Warum: Die Schwierigkeitskurve springt von 0 % auf 33 % – Prio 3 (Spaß des Kern-Loops). Der Patch betrifft nur die Konfiguration (geringes Risiko), Marketing arbeitet in T12 ohnehin parallel am Launch-Paket · Revisionsauslöser: Patch verschlechtert andere Werte · Wann: T11

---

```
=== TICK-REPORT T12 (Puffer 1/2) ===
Tick-Budget: 12/13 + 1 Puffer
EINGÄNGE: GD Balancing-Patch 3 · DEV 1.0.0-rc2 · QA Regression · MKT Launch-Paket-Entwurf (parallel)
======================
```

**GD Balancing-Patch 3 (GDD v1.3, nur L-02):** Schiffe 16 → 18 · Spawn 5,5 → 5 s · Durchfahrt 50 → 44 px · äußere Felsen 4 → 6 · Tempo ×1,1 → ×1,15 · Drift ×1,2 → ×1,35.

**QA-Regression 1.0.0-rc2:** L-02 Casual **0 %** (Ø 0,5 Wracks, vorher 0,4), Erfahren 3 %, Ø 99,8 s · L-01/L-03 unverändert · AC-04 ✅ 2080/2080 · Smoke 15/15 · UI 9/9. **Befund:** Patch 3 erhöht den Druck leicht, erreicht das Ziel aber nicht. Hinweis an GD: Der größte verbleibende Unterschied zu L-03 ist die Zahl gleichzeitiger Schiffe (5 vs. 6).

**D-013** · **Iterationslimit erreicht** (3 Balancing-Patches): 1.0.0-rc2 wird Launch-Build (1.0.0). L-02-Schwierigkeit wird Known Issue; Post-Launch-Patch: `maxActive` L-02 → 6 prüfen · Wer: PRD · Warum: Harte Regel „max. 2 Iterationen pro Dokument" ist überschritten; Prio 2 (Tick-Budget) vor Prio 3. Patch 3 bringt keinen Rückschritt, daher bleibt er drin · Verworfen: zweiter Puffer-Tick für Patch 4 (Perfektionsschleife) · Wann: T12
