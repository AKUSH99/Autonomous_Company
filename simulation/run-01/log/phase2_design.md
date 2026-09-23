# Run 01 · Phase 2 – Design (T3–T4)

---

```
=== TICK-REPORT T3 ===
Phase: 2 – Design | Meilenstein: Design-Lock ⏳ (Ende T4)
Tick-Budget: 3/13 verbraucht · Puffer: unbenutzt

KERNWERTE      aktuell  Ziel  Quelle
Spaß           7        8     CD-Prognose
Kreativität    8        8     CD-Prognose
Grafik         8        7     CD-Prognose (Potenzial)
Sound          7        6     CD-Prognose (Potenzial)
Bugs offen     K:0 M:0 N:0
Hype           0/100          –

EINGÄNGE
- CD: Konzeptdokument v1.0 (FINAL)

AUFTRÄGE
- AUF-003 → GD: GDD-Entwurf v0.9 · Constraints: Scope-Guard Standard, Maus + Touch (D-003) · Default: 3 Nächte

BLOCKER: keine
======================
```

---

```
=== ÜBERGABE ===
Von: GD            An: PRD → DEV, ART, CD (Feedback-Runde)
Dokument: GDD „Nachtwache"            Version: v0.9   Status: ENTWURF
Phase / Tick: 2 / T3
Bezug: Konzeptdokument v1.0 (FINAL), AUF-003, D-003
================
```

### 1. Überblick
Leuchtturm im Bildzentrum (Insel), ringförmiges Riff mit Durchfahrten, Schiffe von allen Bildrändern. Logische Spielfläche 960 × 540. Session 8–12 Minuten über 3 Nächte.

### 2. Spielmechaniken
| ID | Name | Beschreibung | Input | Regeln | Feedback | Prio | Parameter |
|---|---|---|---|---|---|---|---|
| M-01 | Lichtkegel drehen | Kegel zeigt vom Leuchtturm in Richtung Zeiger | Maus bewegen / Finger | Winkel = Richtung Zentrum → Zeiger, sofort | Kegel hellt Dunkelheit auf | MUST | P-01, P-02 |
| M-02 | Fokus-Strahl | Schmaler, weit reichender Strahl | Maustaste halten / Fokus-Button | Solange gehalten: Halbwinkel P-03, Reichweite P-04 | Kegel wird schmal und heller, leises Summen | MUST | P-03, P-04 |
| M-03 | Lotsen | Schiffe im Kegel werden „geführt" | – | Geführte Schiffe steuern die nächste Riff-Durchfahrt und dann den Hafen an; nach Verlassen des Kegels bleiben sie P-05 s geführt | Laterne leuchtet hell, Ring zeigt Rest-Orientierung | MUST | P-05, P-06, P-12 |
| M-04 | Riff & Schiffbruch | Verlorene Schiffe treiben im Dunkeln | – | Kollision Schiff–Fels → Wrack; P-10 Wracks → Nacht verloren | Krachen, Trümmer, Wrack-Zähler | MUST | P-07, P-08, P-09, P-10 |
| M-05 | Hafen & Nachtziel | Anlegen im Hafen | – | Schiff im Hafen-Radius → angelegt, +100; alle Schiffe der Nacht abgearbeitet und Wracks < P-10 → Nacht geschafft | Glocke, Zähler | MUST | P-11 |
| – | Sterne-Wertung | 3/2/1 Sterne bei 0/1/2 Wracks | – | – | Sterne auf S-04 | SHOULD | – |
| – | Tutorial-Hinweise | Kurze Einblendungen in Nacht 1 | – | – | Text | SHOULD | – |
| – | Regen/Sturm-Effekt, Nebelbänke, Schiffstypen, Endlos-Modus | – | – | – | – | COULD | – |

### 3. Kern-Loop im Detail
Laterne entdecken (Dunkelheit) → Kegel drehen (M-01) → ggf. Fokus für ferne Schiffe (M-02) → Schiff geführt (M-03) → zum nächsten Schiff wechseln, bevor ein verlorenes aufs Riff treibt (M-04) → Anlegen (M-05) → nächstes Schiff erscheint.
**Entscheidung des Spielers:** Welches Schiff ist gerade am gefährdetsten, und reicht die Rest-Orientierung des geführten Schiffs, um kurz wegzuschauen?

### 4. Level-Struktur
| ID | Name | Schiffe | Spawn-Intervall | Max. gleichzeitig | Durchfahrten | Äußere Felsen | Tempo × | Drift × | Ziel-Dauer | Ziel-Fehlschlagquote (Casual) |
|---|---|---|---|---|---|---|---|---|---|---|
| L-01 | Ruhige See | 5 | 8 s | 2 | 4 | 0 | 1,0 | 1,0 | 1,5–3 min | < 10 % |
| L-02 | Auflandiger Wind | 8 | 6 s | 3 | 3 | 4 | 1,1 | 1,2 | 2–3,5 min | 20–40 % |
| L-03 | Sturmnacht | 12 | 5 s | 4 | 3 | 7 | 1,2 | 1,5 | 3–5 min | 30–50 % |

### 5. Progression
Nacht für Nacht mehr Schiffe gleichzeitig, weniger Durchfahrten, zusätzliche Felsen außerhalb des Riffs, stärkere Drift. Nacht n+1 wird nach Abschluss von Nacht n freigeschaltet. Gesamtpunktzahl über alle Nächte.

### 6. UI-Flows
| ID | Name | Zweck | Elemente | Übergänge |
|---|---|---|---|---|
| S-01 | Titel | Einstieg | Titel, „Klicken zum Starten", Ton an/aus | → S-02 |
| S-02 | Spiel | Spielen | HUD: Nacht, angelegt x/N, Wracks x/3, Punkte; Fokus-Button (Touch) | → S-03, S-04, S-05 |
| S-03 | Pause | Unterbrechen | „Pause", Weiter, Neustart | → S-02 |
| S-04 | Nacht geschafft | Belohnung | Sterne, Punkte, „Nächste Nacht" / nach L-03 „Alle Nächte geschafft" | → S-02 (nächste Nacht) / S-01 |
| S-05 | Nacht verloren | Neuversuch | Wracks, „Nacht wiederholen", „Titel" | → S-02 / S-01 |

Flow: S-01 →[Klick]→ S-02 →[P/Esc]→ S-03 →[Weiter]→ S-02 →[alle Schiffe]→ S-04 →[Weiter]→ S-02 (L+1) … · S-02 →[3 Wracks]→ S-05 →[Wiederholen]→ S-02

### 7. Balancing-Parameter
| ID | Parameter | Startwert | Einheit | Bereich | Begründung |
|---|---|---|---|---|---|
| P-01 | Kegel-Halbwinkel weit | 22 | ° | 15–30 | Deckt 1–2 Schiffe in Riffnähe ab |
| P-02 | Reichweite weit | 260 | px | 200–320 | Knapp über den Riffring hinaus |
| P-03 | Kegel-Halbwinkel Fokus | 7 | ° | 4–10 | Präzise, verlangt Zielen |
| P-04 | Reichweite Fokus | 560 | px | 450–600 | Erreicht die Bildecken (551 px) |
| P-05 | Orientierungszeit | 2,5 | s | 1,5–4 | Erlaubt kurzes Wegschauen, nicht mehr |
| P-06 | Tempo geführt | 42 | px/s | 30–60 | Weg Rand → Hafen ≈ 10 s |
| P-07 | Tempo im Dunkeln | 24 | px/s | 15–35 | Zeit zum Reagieren |
| P-08 | Drift im Dunkeln | 1,2 | rad/s | 0,5–2 | Unberechenbar, aber nicht chaotisch |
| P-09 | Heimzug im Dunkeln | 0,35 | – | 0–1 | Schiffe ahnen die Richtung der Insel |
| P-10 | Max. Wracks | 3 | – | – | Klassisch, verständlich |
| P-11 | Hafen-Radius | 50 | px | – | Etwas größer als die Insel |
| P-12 | Wendegeschwindigkeit geführt | 2,2 | rad/s | 1,5–3 | Enge Durchfahrten treffbar |
| P-13 | Riff-Radius | 125 | px | 110–150 | Genug Raum zwischen Rand und Riff |

### 8. Sieg- & Niederlage-Bedingungen
Nacht geschafft: alle N Schiffe angelegt oder gesunken und Wracks < P-10. Nacht verloren: Wracks = P-10. Spiel geschafft: L-03 geschafft.

### 9. Content- & Asset-Bedarf
| Bezug | Asset | Funktion | Lesbarkeit |
|---|---|---|---|
| M-01 | Leuchtturm + Insel | Zentrum, Ursprung des Lichts | immer sichtbar |
| M-01/M-02 | Lichtkegel (weit/Fokus) | Werkzeug | klar abgegrenzt |
| M-03 | Schiff (verloren / geführt) | Hauptobjekt | Laterne immer sichtbar, Zustand unterscheidbar |
| M-04 | Felsen, Wrack-Effekt | Gefahr | im Kegel eindeutig |
| M-05 | Hafen-Markierung | Ziel | immer sichtbar |
| S-01…S-05 | UI, Schrift, Sterne | – | hoher Kontrast |
| Audio | Nebelhorn (Schiff erscheint), Glocke (Anlegen), Krachen (Wrack), Fokus-Summen, UI-Klick, Nacht geschafft/verloren, Musik | Feedback | jede Aktion hörbar |

### 10. Akzeptanzkriterien
| ID | Bezug | Kriterium |
|---|---|---|
| AC-01 | M-01 | Der Kegel folgt dem Zeiger ohne spürbare Verzögerung (≤ 1 Frame). |
| AC-02 | M-02 | Beim Halten schrumpft der Kegel auf P-03 / wächst auf P-04; beim Loslassen zurück. |
| AC-03 | M-03 | Ein Schiff im Kegel wird geführt und bleibt es P-05 s nach Verlassen des Kegels. |
| AC-04 | M-03 | Ein durchgehend beleuchtetes Schiff erreicht den Hafen ohne Felskontakt (Ziel: 100 %). |
| AC-05 | M-04 | Felskontakt → Wrack, Zähler +1, Ton + Effekt; bei P-10 Wracks erscheint S-05. |
| AC-06 | M-05 | Hafen erreicht → angelegt, Zähler +1, +100 Punkte, Glocke. |
| AC-07 | M-05 | Alle Schiffe abgearbeitet, Wracks < P-10 → S-04 mit Sternen. |
| AC-08 | M-04 | Ohne Spieler-Input geht L-01 in ≥ 80 % der Fälle verloren (Herausforderung existiert). |
| AC-09 | L-01…L-03 | Casual-Spielende erreichen Ziel-Dauer und Ziel-Fehlschlagquote je Nacht. |
| AC-10 | S-03 | Pause friert alles ein; Weiter setzt exakt fort. |
| AC-11 | D-003 | Touch: Finger dreht den Kegel, Fokus ist per Touch auslösbar. |
| AC-12 | Audio | Ton startet erst nach der ersten Interaktion; Ton an/aus (Taste M) funktioniert. |

### 11. MVP-Scope
**MUST:** M-01 bis M-05, 3 Nächte, S-01 bis S-05 · **SHOULD:** Sterne, Tutorial-Hinweise · **COULD:** Regen-Effekt, Nebelbänke, Schiffstypen, Endlos-Modus · **WON'T:** Online-Bestenliste (Datenschutz und Scope), Story-Zwischensequenzen.

**Was ist definiert:** 5 MUST-Mechaniken, 3 Nächte, 5 Screens, 13 Parameter, 12 Akzeptanzkriterien. Scope-Guard eingehalten.
**Annahmen / Unsicherheiten:**
- `GD-A01: Rand → Hafen dauert geführt ≈ 10 s | Begründung: ≈ 420 px / 42 px/s | Risiko: niedrig`
- `GD-A02: Heimzug 0,35 lässt verlorene Schiffe grob aufs Riff zutreiben, ohne die Durchfahrten zu treffen | Begründung: Schätzung, ohne Messdaten | Risiko: hoch → QA misst AC-08`
**Abhängigkeiten / offene Fragen:** `GD-Q01: Wie finden geführte Schiffe zuverlässig die Durchfahrt? | An: DEV | Default: Schiffe steuern die nächstgelegene Durchfahrt an.`
**Entscheidungen:** `| GD-D01 | 3 Nächte statt Endlos-Modus | GD | Klare Ziele, Scope-Guard | T3 |` · `| GD-D02 | Online-Bestenliste = WON'T | GD | Datenschutz, Scope | T3 |`
**Status-Update:** GDD v0.9: 5 MUST-Mechaniken, 3 Nächte, 12 Akzeptanzkriterien, 1 offene Frage zur Wegfindung.

---

```
=== TICK-REPORT T4 ===
Phase: 2 – Design | Meilenstein: Design-Lock ✅
Tick-Budget: 4/13 verbraucht · Puffer: unbenutzt

EINGÄNGE
- GD: GDD v0.9 → parallel geprüft von DEV, ART, CD
- DEV: Machbarkeits-Check · ART: Stil-Skizze · CD: Vision-Check
- KONFLIKT: ART ↔ GD zur Sichtbarkeit der Felsen

ENTSCHEIDUNGEN
- D-004: Felsen im Dunkeln schwach sichtbar (Kompromiss, siehe unten)
- D-005: DEVs Wegpunkt-Lösung für M-03 übernommen

AUFTRÄGE
- AUF-004 → GD: Feedback einarbeiten → GDD v1.0 FINAL
- AUF-005 → DEV (T5): Tech-Design + Projektgerüst
- AUF-006 → ART (T5): Art-Style-Guide + Asset-Liste

BLOCKER: keine
======================
```

---

```
=== ÜBERGABE ===
Von: DEV           An: PRD → GD
Dokument: Machbarkeits-Check GDD v0.9 Version: v1.0   Status: FINAL
Phase / Tick: 2 / T4
Bezug: GDD v0.9, GD-Q01
================
```
| GDD-ID | Feature | Urteil | Aufwand | Anmerkung / Alternative |
|---|---|---|---|---|
| M-01 | Lichtkegel drehen | ✅ | S | `atan2` vom Zentrum zum Zeiger |
| M-02 | Fokus-Strahl | ✅ | S | Weicher Übergang über 0,15 s |
| M-03 | Lotsen durchs Riff | ⚠️ | L → M | Freie Pfadsuche ist zu teuer. **Vereinfachung:** geführte Schiffe umrunden das Riff auf einer Kreisbahn (Riff-Radius + 40 px) bis zur nächsten Durchfahrt, fahren dann hinein und zum Hafen. Äußere Felsen werden per Ausweich-Vektor umfahren. |
| M-04 | Riff & Schiffbruch | ✅ | S | Kreis-Kollision |
| M-05 | Hafen & Nachtziel | ✅ | S | – |
| Dunkelheit | Licht-Rendering | ✅ | M | Offscreen-Canvas, Kegel per `destination-out` ausschneiden |
| AC-11 | Fokus per Touch | ⚠️ | S | Langes Drücken kollidiert mit dem Zielen → **eigener Fokus-Button** unten rechts (Multi-Touch) |
| AC-08/09 | Messbarkeit | ✅ | S | Ich baue Seed-basierten Zufall und eine Debug-Schnittstelle ein, damit QA Nächte mit Bots im Zeitraffer simulieren kann. |

**Fazit:** Passt in 4 Entwicklungs-Ticks (T5–T8), keine ⛔.
**Annahmen / Unsicherheiten:** `DEV-A01: Kreisbahn-Umrundung ist für Spielende glaubwürdig | Risiko: niedrig`
**Abhängigkeiten / offene Fragen:** keine.
**Entscheidungen:** `| DEV-D01 | Seed-Zufall + Debug-API für QA | DEV | Reproduzierbare Messungen für AC-08/09 | T4 |`
**Status-Update:** Machbarkeit bestätigt, 2 Vereinfachungen (Wegpunkte, Fokus-Button).

---

```
=== ÜBERGABE ===
Von: ART           An: PRD → GD, DEV  CC: CD
Dokument: Stil-Skizze                 Version: v0.1   Status: ENTWURF
Phase / Tick: 2 / T4
Bezug: GDD v0.9, Konzept v1.0
================
```
- **Stil-Säulen:** nachtblau · bernsteinwarm · still. **Anti-Säulen:** kein Comic-Bunt, kein Horror.
- **Palette:** Meer `#0B1A2E` · Tiefe `#07111F` · Lichtkegel `#FFD98A` · Laternen `#FFB347` · Felsen `#2A3441` · Gischt `#9FB4C7` · Hafenlichter `#7FE0C8` · UI `#E8EEF5` · Gefahr `#FF5A5F`
- **Formsprache:** flache Vektor-Silhouetten mit weichen Glows, Schiffe als kleine Rümpfe mit Segel.
- **Felsen:** **Im Dunkeln unsichtbar**, nur im Lichtkegel sichtbar – das maximiert die Spannung (Vision-Säule „Dunkelheit ist die Gegnerin").
- **Audio-Richtung:** tiefe Pads, Wellenrauschen, Nebelhorn aus Sägezahn mit Tiefpass, Glocke aus Sinus-Obertönen.
- **Auflösung:** 960 × 540 logisch, skalierbar, Vektorgrafik (Canvas).

**Status-Update:** Stil-Skizze „Nachtblau & Bernstein", Felsen nur im Licht sichtbar.

---

```
=== KONSULTATION ===
Von: GD   An: ART   CC: PRD   Tick: T4
Frage: Können Felsen im Dunkeln wenigstens schwach sichtbar sein?
Kontext: Wer die Felsen nicht sieht, kann nicht einschätzen, welches verlorene Schiff gefährdet ist. Die Kernentscheidung des Loops („Welches Schiff zuerst?") wird zum Raten.
Mein Vorschlag / Default: Felsen im Dunkeln als dezente Gischt-Umrisse.
====================
```
```
=== KONSULTATION ===
Von: ART   An: GD   CC: PRD   Tick: T4
Antwort: Sichtbare Felsen nehmen der Dunkelheit ihren Schrecken. Ich möchte beim unsichtbaren Riff bleiben.
====================
```

**Konflikt nach 1 Iteration ungelöst → Producer entscheidet.**

**D-004** · Felsen sind im Dunkeln als schwache Gischt-Umrisse sichtbar (ca. 35 % Deckkraft); volle Detailtiefe nur im Lichtkegel · Wer: PRD · Warum: Prio 4 (Lesbarkeit) schlägt Prio 5 (Ästhetik): Die Kernentscheidung des Loops braucht sichtbare Gefahren. Der Kompromiss erhält ARTs Stimmung, weil die Felsen erst im Licht „echt" werden, und kostet keine zusätzlichen Ticks · Verworfen: unsichtbare Felsen (Frust), voll sichtbare Felsen (Stimmung weg) · Revisionsauslöser: QA meldet, dass Felsen im Dunkeln schlecht erkennbar sind · Wann: T4

**D-005** · DEVs Kreisbahn-/Wegpunkt-Lösung für M-03 und der Fokus-Button für Touch werden ins GDD übernommen · Wer: PRD · Warum: Prio 2 (Budget), Kern-Loop bleibt laut GD unverändert · Wann: T4

---

```
=== ÜBERGABE ===
Von: CD            An: GD             CC: PRD
Dokument: Vision-Check GDD v0.9       Version: v1.0   Status: FINAL
Phase / Tick: 2 / T4
================
```
Ergebnis: **⚠️ kleine Abweichung**
1. Tutorial-Hinweise dürfen die Stille nicht zerreden (Säule „Eine Hand, eine Minute") → höchstens 3 Einzeiler, die von selbst verschwinden.
2. Positiv: M-02 Fokus verstärkt Säule „Licht ist alles"; WON'T Bestenliste schützt die ruhige Stimmung.

---

```
=== ÜBERGABE ===
Von: GD            An: PRD → DEV, ART, QA   CC: MKT
Dokument: GDD „Nachtwache"            Version: v1.0   Status: FINAL
Phase / Tick: 2 / T4
Bezug: GDD v0.9, Machbarkeits-Check, Stil-Skizze, Vision-Check, D-004, D-005
================
```
**Changelog v0.9 → v1.0** (alle übrigen Inhalte unverändert):
1. **M-03** Regeln präzisiert (D-005): Geführte Schiffe fahren zur Kreisbahn (P-13 + 40 px), umrunden das Riff zur nächsten Durchfahrt, fahren hinein und zum Hafen. GD-Q01 geschlossen.
2. **M-02 / AC-11:** Fokus auf Touch über einen Fokus-Button unten rechts (D-005).
3. **Felsen-Lesbarkeit** (D-004): neues **AC-13** – Felsen sind im Dunkeln als Umriss erkennbar, im Kegel voll sichtbar.
4. **Tutorial:** genau 3 Einzeiler in Nacht 1, blenden nach 6 s oder bei erfüllter Aktion aus: „Zeige mit der Maus, wohin das Licht fällt" · „Beleuchtete Schiffe finden durchs Riff" · „Maustaste halten: Fokus-Strahl für ferne Schiffe".

**Was ist definiert:** GDD vollständig, 5 MUST-Mechaniken, 13 Akzeptanzkriterien, 13 Parameter.
**Annahmen / Unsicherheiten:** `GD-A02` bleibt offen (QA misst).
**Abhängigkeiten / offene Fragen:** keine.
**Entscheidungen:** übernommen: D-004, D-005.
**Status-Update:** GDD v1.0 FINAL: Design-Lock bereit.

```
=== GATE: Design-Lock ===
Ergebnis: GO
Kriterien: [x] MUST-Mechaniken mit Regeln, Feedback, AC  [x] Balancing-Tabelle  [x] Scope-Guard  [x] Machbarkeit ohne ⛔  [x] Asset-Bedarf  [x] Vision-Check ohne ⛔
Auflagen: –
Begründung: Alle Kriterien erfüllt; Konflikt ART ↔ GD per D-004 gelöst.
Protokoll: D-004, D-005
=========================
```
