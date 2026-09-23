# Run 01 · Phase 1 – Ideenfindung (T1–T2)

---

```
=== TICK-REPORT T1 ===
Phase: 1 – Ideenfindung | Meilenstein: Konzept-Freeze ⏳ (Ende T2)
Tick-Budget: 1/13 verbraucht · Puffer: unbenutzt

KERNWERTE      aktuell  Ziel  Quelle
Spaß           –        8     –
Kreativität    –        8     –
Grafik         –        7     –
Sound          –        6     –
Bugs offen     K:0 M:0 N:0
Hype           0/100          –

EINGÄNGE
- Kein Startimpuls der Umgebung vorhanden.

ENTSCHEIDUNGEN
- D-001: Startimpuls selbst gewählt (siehe Protokoll)

AUFTRÄGE
- AUF-001 → CD: 2–3 Konzeptoptionen zum Startimpuls

BLOCKER: keine
======================
```

```
=== AUFTRAG AUF-001 ===
An: CD               Phase / Tick: 1 / T1
Ziel: 2–3 substanziell unterschiedliche Konzeptoptionen zum Startimpuls D-001
Eingaben: D-001
Erwarteter Output: Konzept-Paket v0.1 (Optionen, Vergleichsmatrix, Empfehlung)
Constraints: Spielbar mit einer Hand (Maus oder Finger), in 60 Sekunden verstanden, Browser, MVP in 4 Entwicklungs-Ticks
Fällig: Ende T1
Default bei Unklarheit: Casual-Zielgruppe, 2D, Session 5–10 Minuten
=======================
```

**D-001** · Startimpuls: *„Ein Spiel, das man mit einer Hand spielt (Maus oder Finger) und in 60 Sekunden versteht. Stimmung: ruhig, aber mit Spannung."* · Wer: PRD · Warum: Keine Vorgabe der Umgebung. Ein-Hand-Steuerung hält den MVP-Scope klein, läuft auf Desktop und Handy und macht QA-Tests mit Bots einfach · Wann: T1

---

```
=== ÜBERGABE ===
Von: CD            An: PRD            CC: –
Dokument: Konzept-Paket               Version: v0.1   Status: ENTWURF
Phase / Tick: 1 / T1
Bezug: AUF-001, D-001
================
```

### Option A: Pollenflug *(sichere Option)*
| Feld | Inhalt |
|---|---|
| Elevator Pitch | Steuere eine Biene mit der Maus, sammle Pollen und bring sie heim, bevor die Wespen dich erwischen. |
| Genre × Thema | Arcade-Sammelspiel × Bienenwiese |
| Kombo-Begründung | Bewährt: „Sammeln und abliefern" passt natürlich zum Bienenstock. Solide, aber wenig überraschend. |
| Plattform | Browser (itch.io) |
| Kern-Loop | Blüte anfliegen → Pollen sammeln → zum Stock fliegen → Punkte → neue Blüten blühen auf |
| Session-Länge | 5 Minuten |
| Zielgruppe | Casual-Spielende 8–40 Jahre, weil die Steuerung sofort verständlich und das Thema freundlich ist |
| USP | Blüten blühen im Rhythmus der Musik auf. |
| Referenzen | „Snake trifft Flower" |
| Spielgefühl | fröhlich, flink, leicht |
| MVP-Skizze | 1 Wiese, 3 Wellen, 1 Gegnertyp |
| Scope-Schätzung | S – sehr bekanntes Muster |
| Top-Risiken | 1) Austauschbar → Rhythmus-USP betonen · 2) Wenig Tiefe → Wespen-Muster variieren |
| Kernwert-Prognose | Spaß 6 (solide, bekannt) · Kreativität 4 (wenig neu) · Grafik-Potenzial 6 · Sound-Potenzial 6 |

### Option B: Nachtwache *(mutige Option)*
| Feld | Inhalt |
|---|---|
| Elevator Pitch | Du bist Leuchtturmwärterin in einer stürmischen Nacht. Nur Schiffe in deinem Lichtkegel finden den Weg durchs Riff. |
| Genre × Thema | Echtzeit-Lotsenspiel × Leuchtturm bei Nacht |
| Kombo-Begründung | **Great Combo:** Die Mechanik („Licht lenken") ist gleichzeitig die Fantasie des Settings. Die Dunkelheit erzeugt die Spannung, das Licht ist Werkzeug und visuelle Belohnung zugleich. |
| Plattform | Browser (itch.io), Desktop und Handy |
| Kern-Loop | Schiff im Dunkeln entdecken → Lichtkegel darauf richten → Schiff findet die Riff-Durchfahrt → legt im Hafen an → nächstes Schiff taucht auf, mehrere gleichzeitig jonglieren |
| Session-Länge | 8–12 Minuten (3 Nächte) |
| Zielgruppe | Casual- und Mid-Core-Spielende 16–40 Jahre, die ruhige Spiele mit Druckmomenten mögen (Mini-Metro-Publikum), weil das Spiel in Sekunden verständlich ist, aber Priorisierung verlangt |
| USP | Dein einziges Werkzeug ist ein Lichtkegel: Was du beleuchtest, findet heim – was im Dunkeln bleibt, ist auf sich allein gestellt. |
| Referenzen | „Mini Metro trifft Lighthouse-Stimmung" |
| Spielgefühl | ruhig, atmosphärisch, angespannt |
| MVP-Skizze | 1 Insel mit Riff-Ring, 3 Nächte mit steigender Schiffszahl, Fokus-Strahl als zweite Fähigkeit |
| Scope-Schätzung | M – Schiffsverhalten (geführt vs. verloren) ist der Hauptaufwand |
| Top-Risiken | 1) Schiffe finden den Weg nicht zuverlässig → feste Durchfahrten als Wegpunkte · 2) Dunkelheit wird unlesbar → Schiffslaternen immer sichtbar |
| Kernwert-Prognose | Spaß 7 (Jonglieren erzeugt Flow) · Kreativität 8 (frische Kombo) · Grafik-Potenzial 8 (Licht und Schatten) · Sound-Potenzial 7 (Nebelhorn, Wellen) |

### Option C: Echolot *(Wildcard)*
| Feld | Inhalt |
|---|---|
| Elevator Pitch | Ein U-Boot in völliger Dunkelheit: Jeder Sonar-Ping zeigt die Höhle für eine Sekunde – dann musst du dich erinnern. |
| Genre × Thema | Gedächtnis-Navigation × Tiefsee-Sonar |
| Kombo-Begründung | Sonar macht das Merken zur Mechanik; stark, aber schwer zu balancieren. |
| Plattform | Browser |
| Kern-Loop | Ping → Höhle einprägen → blind steuern → Kristall einsammeln → nächster Ping |
| Session-Länge | 5–10 Minuten |
| Zielgruppe | Puzzle-Fans 18–35 Jahre, weil Gedächtnis-Herausforderungen eine treue Nische haben |
| USP | Ein Spiel, das du größtenteils im Dunkeln und aus der Erinnerung spielst. |
| Referenzen | „Wave Race trifft Memory" |
| Spielgefühl | still, konzentriert, klaustrophobisch |
| MVP-Skizze | 3 Höhlen, 1 Ping-Typ |
| Scope-Schätzung | M – Level-Design ist aufwendig |
| Top-Risiken | 1) Frustrierend für Casuals · 2) Schwer testbar mit Bots |
| Kernwert-Prognose | Spaß 5 · Kreativität 9 · Grafik-Potenzial 5 · Sound-Potenzial 8 |

### Vergleichsmatrix
| Kriterium (Gewicht) | A Pollenflug | B Nachtwache | C Echolot |
|---|---|---|---|
| Klarheit des Kern-Loops (25 %) | 5 | 4 | 3 |
| Machbarkeit im Tick-Budget (25 %) | 5 | 4 | 3 |
| Kreativität / Kombo-Stärke (20 %) | 2 | 5 | 5 |
| Zielgruppen-Fit & USP (20 %) | 3 | 4 | 3 |
| Marketing-Potenzial (10 %) | 3 | 4 | 3 |
| **Gewichteter Score** | **3,80** | **4,20** | **3,40** |

**Empfehlung: B – Nachtwache.** Die stärkste Kombo mit klar kommunizierbarer USP. Das bewusst eingegangene Risiko ist das Schiffsverhalten; die Gegenmaßnahme (feste Riff-Durchfahrten als Wegpunkte) hält es im Budget.

**Was ist definiert:** 3 Optionen mit allen Pflichtfeldern, Matrix, Empfehlung B.
**Annahmen / Unsicherheiten:**
- `CD-A01: Ruhige Spiele mit Druckmomenten (Mini-Metro-Muster) sind im Indie-Browser-Segment gefragt | Begründung: allgemeines Genre-Wissen, nicht verifiziert | Risiko: mittel`
- `CD-A02: Ein Lichtkegel ist auf dem Handy per Finger genauso gut steuerbar wie mit der Maus | Begründung: Zielen = Zeigen | Risiko: mittel`

**Abhängigkeiten / offene Fragen:** `CD-Q01: Soll das Spiel auf dem Handy spielbar sein? | An: PRD | Default: Ja, Maus und Touch.`
**Entscheidungen:** `| CD-D01 | Risiko-Portfolio sicher/mutig/Wildcard | CD | Prompt-Regel, breite Auswahl | T1 |`
**Status-Update:** Konzept-Paket fertig: 3 Optionen, Empfehlung B (4,20), 1 offene Frage zur Handy-Tauglichkeit.

---

```
=== TICK-REPORT T2 ===
Phase: 1 – Ideenfindung | Meilenstein: Konzept-Freeze ✅
Tick-Budget: 2/13 verbraucht · Puffer: unbenutzt

KERNWERTE      aktuell  Ziel  Quelle
Spaß           7        8     CD-Prognose
Kreativität    8        8     CD-Prognose
Grafik         8        7     CD-Prognose (Potenzial)
Sound          7        6     CD-Prognose (Potenzial)
Bugs offen     K:0 M:0 N:0
Hype           0/100          –

EINGÄNGE
- CD: Konzept-Paket v0.1

ENTSCHEIDUNGEN
- D-002: Option B „Nachtwache" gewählt
- D-003: CD-Q01 beantwortet – Maus UND Touch sind Pflicht

AUFTRÄGE
- AUF-002 → CD: Konzept B finalisieren (v1.0 FINAL)
- AUF-003 → GD (Vorankündigung T3): GDD-Entwurf auf Basis Konzept v1.0

BLOCKER: keine
======================
```

**D-002** · Konzept „Nachtwache" gewählt · Wer: PRD · Warum: Die eigene Auswahlmatrix des Producers bestätigt CDs Bewertung: B 4,20 vor A 3,80 und C 3,40. Die höhere Machbarkeit von A wiegt die deutlich schwächere Kreativität nicht auf; C fällt wegen Frust-Risiko für die Zielgruppe ab · Verworfen: A (austauschbar), C (schwer balancier- und testbar) · Revisionsauslöser: DEV stuft das Schiffsverhalten in T4 als ⛔ ein · Wann: T2

**D-003** · Maus- und Touch-Steuerung sind Pflicht · Wer: PRD · Warum: Ein-Hand-Constraint aus D-001; ein Browser-Spiel wird oft auf dem Handy geöffnet · Wann: T2

```
=== GATE: Konzept-Freeze ===
Ergebnis: GO
Kriterien: [x] Kern-Loop ≤ 5 Schritte  [x] Zielgruppe begründet, USP in 1 Satz  [x] MVP plausibel in 4 Ticks  [x] Annahmen dokumentiert
Auflagen: –
Begründung: Konzept vollständig, Risiko Schiffsverhalten mit Gegenmaßnahme adressiert.
Protokoll: D-002
=========================
```

---

```
=== ÜBERGABE ===
Von: CD            An: PRD → GD       CC: ART, MKT
Dokument: Konzeptdokument „Nachtwache" Version: v1.0   Status: FINAL
Phase / Tick: 1 / T2
Bezug: Konzept-Paket v0.1 Option B, D-002, D-003, AUF-002
================
```

**Pitch:** Du bist Leuchtturmwärterin in einer stürmischen Nacht. Schiffe tasten sich von allen Seiten auf deine Insel zu, doch ein Riff umschließt den Hafen. Nur wer in deinem Lichtkegel fährt, findet die Durchfahrt.

**Genre × Thema:** Echtzeit-Lotsenspiel × Leuchtturm bei Nacht (360°-Leuchtturm im Bildzentrum).

**Kern-Loop (4 Schritte):**
1. **Entdecken** – Schiffslaternen tauchen am Rand der Dunkelheit auf.
2. **Beleuchten** – Lichtkegel drehen (Zeigen = Zielen); weit und kurz oder fokussiert und lang.
3. **Lotsen** – Beleuchtete Schiffe steuern die nächste Riff-Durchfahrt an und behalten kurz Orientierung, wenn das Licht weiterzieht.
4. **Anlegen & Umschalten** – Schiff erreicht den Hafen (+Punkte), während schon das nächste im Dunkeln aufs Riff zutreibt.

**Die Spannung:** Es gibt nur einen Lichtkegel und immer mehr Schiffe als Licht.

**Zielgruppe:** Casual- und Mid-Core-Spielende 16–40, Browser/Handy, 8–12-Minuten-Sessions.
**USP:** Dein einziges Werkzeug ist ein Lichtkegel.
**Spielgefühl:** ruhig · atmosphärisch · angespannt
**Steuerung:** Maus (Bewegen = Drehen, Taste halten = Fokus) und Touch (Finger = Richtung, Fokus-Button).

**Vision-Säulen (für alle Agenten):**
1. **Licht ist alles** – jede Mechanik hängt am Lichtkegel.
2. **Dunkelheit ist die Gegnerin** – keine Monster, nur Nacht und Riff.
3. **Eine Hand, eine Minute** – in 60 Sekunden verstanden.

**Was ist definiert:** Konzept, Kern-Loop, Zielgruppe, USP, Steuerung, 3 Vision-Säulen.
**Annahmen / Unsicherheiten:** `CD-A02` (Touch-Steuerung gleichwertig) bleibt offen → QA prüft in Phase 4.
**Abhängigkeiten / offene Fragen:** keine.
**Entscheidungen:** `| CD-D02 | Leuchtturm im Bildzentrum (360°) statt am Rand | CD | Schiffe von allen Seiten → echtes Jonglieren, Drehen mit Zeigen ist intuitiv | T2 |`
**Status-Update:** Konzept „Nachtwache" v1.0 FINAL, bereit fürs GDD.
