# Run 01 · Phase 5 – Marketing & Launch (T13–T14)

---

```
=== TICK-REPORT T13 ===
Phase: 5 – Marketing & Launch | Meilenstein: Launch ⏳ (T14)
Tick-Budget: 13/13 + 1 Puffer
EINGÄNGE: MKT Launch-Paket v0.9 · DEV Material für Marketing (5 echte Screenshots aus 1.0.0)
AUFTRÄGE: AUF-021 → QA Claims-Check · AUF-022 → MKT Korrekturen → FINAL
======================
```

```
=== ÜBERGABE ===
Von: MKT           An: PRD → QA (Claims-Check)   CC: CD
Dokument: Launch-Paket                 Version: v0.9   Status: ENTWURF
Phase / Tick: 5 / T13
Bezug: Konzept v1.0, GDD v1.3, Build 1.0.0, QA-RC-Report, marketing/screenshots/
================
```
Vollständiges Paket: [`marketing/launch_paket.md`](../marketing/launch_paket.md). Entwurf enthielt u. a. diese Aussagen:
1. „Drei Nächte mit **steigender Schwierigkeit**"
2. „Spielbar mit Maus oder Touch"
3. „**In einer Minute verstanden**"
4. „Beleuchtete Schiffe finden sicher durchs Riff"
5. „Kein Tracking, keine Datenerhebung, keine Werbung, keine Käufe"
6. „**Atmosphärischer Synth-Soundtrack**"
7. „Läuft im Browser, ohne Installation" · „Eine Runde: ca. 5–10 Minuten"

Hype: **38/100** (Simulationswert: 2 Teaser in T8/T9 + starke USP + Mock-Review 29/40).

```
=== ÜBERGABE ===
Von: QA            An: PRD, MKT
Dokument: Claims-Check                 Version: v1.0   Status: FINAL
Phase / Tick: 5 / T13
Bezug: Launch-Paket v0.9, Build 1.0.0
================
```
| Aussage | Belegt? | Beleg / Korrekturvorschlag |
|---|---|---|
| 1 Steigende Schwierigkeit | ⚠️ | Schiffe, Felsen und Drift steigen (8 → 18 → 26 Schiffe), die gemessene Fehlschlagquote steigt aber erst in Nacht 3 (0 / 0 / 33 %). → „Drei Nächte, immer mehr Schiffe – und am Ende ein Sturm" |
| 2 Maus oder Touch | ✅ | AC-11 (synthetische Touch-Events, Konfidenz mittel) |
| 3 In einer Minute verstanden | ⚠️ | Mit Bots nicht messbar. Belegt ist nur: 3 kurze Tutorial-Hinweise in Nacht 1, Casual-Fehlschlag 0 % → „Drei kurze Hinweise, dann geht's los" |
| 4 Beleuchtete Schiffe sicher | ✅ | AC-04: 2080/2080 Schiffe im Hafen |
| 5 Keine Daten/Werbung/Käufe | ✅ | Code-Prüfung: keine Netzwerkaufrufe, kein lokaler Speicher, keine Cookies, keine Werbung oder Käufe |
| 6 Synth-Soundtrack | ⚠️ | Musik und 8 Soundeffekte laufen fehlerfrei, klanglich aber ungeprüft (Headless) → neutral formulieren: „Synthetisierter Ambient-Soundtrack" |
| 7 Browser, 5–10 min | ✅ | Ø Nachtdauer 65 / 100 / 127 s ≈ 5 min ohne Wiederholungen |
| Zusatz | ⚠️ NIEDRIG | Titelbildschirm zeigt auf Touch-Geräten vor der ersten Berührung „Klicken zum Starten" und Maus-Hinweise → Known Issue, Post-Launch |

**Status-Update:** 4 ✅, 3 ⚠️ mit Korrekturvorschlag, 0 ❌.

**MKT** übernimmt alle Korrekturen → Launch-Paket **v1.0 FINAL**. Der Titel-Hinweis kommt in die Known Issues.

---

```
=== TICK-REPORT T14 (Puffer 2/2 nicht genutzt – Launch in T14 durch Puffer 1) ===
Phase: 5 | Meilenstein: Launch ✅
Tick-Budget: 13/13 + 1 Puffer
KERNWERTE      final  Ziel  Quelle
Spaß           7      8     QA RC-Report
Kreativität    8      8     QA RC-Report
Grafik         8      7     QA RC-Report
Sound          6      6     QA RC-Report (Konfidenz niedrig)
Bugs offen     K:0 M:1 N:1  (BAL-L02, Touch-Titeltext)
Hype           38/100       MKT-Schätzung
ENTSCHEIDUNGEN: D-014 Gate Launch GO · D-015 Launch
======================
```

```
=== GATE: Launch ===
Ergebnis: GO
Kriterien: [x] Store-Listing nur mit belegten Aussagen (Claims-Check nach Korrektur)  [x] Marketing-Plan, Store-Listing, Social-Plan vollständig  [x] Known Issues dokumentiert
Begründung: Alle Launch-Kriterien erfüllt; offene Punkte sind dokumentiert und im Post-Launch-Backlog.
Protokoll: D-014
=========================
```

---

```
=== LAUNCH-BERICHT ===
Spiel: Nachtwache 1.0.0 | Launch: T14 (Simulationsereignis) | Tick-Verbrauch: 13/13 (+1 Puffer)
Finale Kernwerte (QA): Spaß 7 · Kreativität 8 · Grafik 8 · Sound 6 (Konfidenz niedrig)
Mock-Review: 29/40 (Casual-Kritikerin 8 · Core-Gamer 6 · Indie-Ästhet 7 · Tech-Reviewerin 8)
Bugs bei Launch: K:0 M:1 N:1 · Hype: 38/100
Gestrichen / verschoben: COULD Nebelbänke, Schiffstypen, Endlos-Modus · WON'T Online-Bestenliste
Known Issues & Post-Launch-Backlog:
  1. BAL-L02 (MITTEL): Nacht 2 zu leicht (Casual 0 % statt 20–40 %) → maxActive L-02 5 → 6 testen
  2. Touch-Titeltext (NIEDRIG): „Klicken" statt „Tippen" vor der ersten Berührung → pointer:coarse abfragen
  3. Audio klanglich ungeprüft → Hörtest mit echten Geräten

POST-MORTEM
Was lief gut:
  - Frühe Parallel-Checks (T4) haben zwei Probleme vor dem Code gelöst: Wegfindung (D-005) und Felsen-Lesbarkeit (D-004).
  - Seed-Zufall + Debug-API (DEV-D01) machten QA-Messungen reproduzierbar – jede Balancing-Entscheidung beruht auf Zahlen.
  - Platzhalter-Pipeline: DEV lieferte den Alpha-Build ohne auf Assets zu warten.
Was lief schlecht:
  - Die Ziel-Dauern im GDD widersprachen den eigenen Spawn-Parametern (GD-A01) – erst QA hat es gemerkt.
  - DEV setzte die Durchfahrten auf einem Raster um, das die Spezifikation um ~20 px verfehlte (BUG-002).
  - Drei Balancing-Patches, Ziel für L-02 trotzdem verfehlt.
  - QA hatte einen Fehler im eigenen Testskript (AC-12c).
Engpässe: Phase 4 / GD+QA / Balancing ohne Messwerte vor der Beta
Entscheidungen, die sich bewährt haben: D-004, D-005, D-009, D-013 (Iterationslimit statt Perfektionsschleife)
Entscheidungen, die sich nicht bewährt haben: Balancing-Startwerte ohne Durchrechnen der Spawn-Zeiten (GDD v1.0)
STUDIO-WISSEN für das nächste Projekt:
  1. GD rechnet Ziel-Dauern gegen Spawn-Parameter durch, bevor das GDD FINAL wird.
  2. QA liefert ab Alpha einen Bot-Balancing-Lauf, nicht erst zur Beta.
  3. DEV prüft Geometrie-Spezifikationen mit einem Messskript (wie QA es tat).
  4. Pro Nacht eine dominante Schwierigkeits-Stellschraube definieren (hier: gleichzeitige Schiffe).
  5. Testskripte selbst gegen einen bekannten Fall prüfen, bevor sie Befunde liefern.
======================
```
