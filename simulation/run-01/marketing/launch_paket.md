# Launch-Paket „Nachtwache" · v1.0 FINAL

```
=== ÜBERGABE ===
Von: MKT           An: PRD            CC: CD, QA
Dokument: Launch-Paket                 Version: v1.0   Status: FINAL
Phase / Tick: 5 / T13
Bezug: Konzept v1.0, GDD v1.3, Build 1.0.0, QA-RC-Report, Claims-Check v1.0
================
```

## 1. Marketing-Plan

**Positionierung:** Für Menschen, die in kurzen Pausen etwas Ruhiges mit Spannung suchen, ist *Nachtwache* ein Browser-Lotsenspiel, in dem ein einziger Lichtkegel über Rettung und Schiffbruch entscheidet. Anders als hektische Arcade-Spiele setzt es auf Atmosphäre und kluge Prioritäten.

**Personas**
| Persona | Profil | Wo erreichbar |
|---|---|---|
| Lea, 27 | Pendelt, spielt 5–10 Minuten am Handy, mag Mini Metro und Alto | Reddit r/WebGames, r/incremental_games, Kurzvideos |
| Jonas, 34 | Entwickler, spielt Indie-Browsergames in der Mittagspause, schätzt Stil | itch.io-Browse, r/indiegaming, Hacker-News-Kommentare |

**Key Messages**
| Botschaft | Beleg |
|---|---|
| Ein Lichtkegel ist dein einziges Werkzeug | M-01/M-02 ✅ |
| Beleuchtete Schiffe finden heim – der Rest ist auf sich gestellt | AC-04: 2080/2080 |
| Ruhig, aber mit Druck: immer mehr Schiffe, am Ende ein Sturm | 8 → 18 → 26 Schiffe, Sturmnacht-Fehlschlag 33 % (Casual-Bot) |

**Tonalität:** ruhig · atmosphärisch · ehrlich. Do: kurze Sätze, Bilder statt Superlative. Don't: „das beste", Countdown-Druck, erfundene Zitate.

**Kanäle:** itch.io (Store, Priorität 1) · Reddit (r/WebGames, r/indiegaming – als Entwickler gekennzeichnet, Selbstpromo-Regeln beachten, Priorität 1) · Kurzvideo (15-s-Clip, Priorität 2).

**Timeline:** T8 Devlog · T9 Clip „Drei Schiffe, ein Licht" · T13 Store-Seite fertig · T14 Launch · Launch +2 Tage Reddit-Post · +7 Tage Rückblick-Devlog mit ehrlichen Zahlen.

**Budget:** 0 € (organisch) – Annahme `MKT-A02`.

**KPIs (Schätzungen, nicht verifiziert – `MKT-A03`: typische Werte kleiner Browser-Indies ohne Budget)**
| KPI (erste Woche) | Zielwert |
|---|---|
| itch.io-Seitenaufrufe | 500–1 500 |
| Plays im Browser | 150–400 |
| Bewertungen/Kommentare | 5–15 |

## 2. Store-Listing (itch.io)

- **Titel:** Nachtwache *(Alternativen: „Letztes Licht", „Lotsenlicht")*
- **Tagline:** Dein Licht ist ihr einziger Weg nach Hause.
- **Kurzbeschreibung:** Ein ruhiges Spiel mit Spannung: Dreh den Lichtkegel deines Leuchtturms und lotse Schiffe durchs nächtliche Riff. Maus oder Touch.
- **Langbeschreibung:**
  > Es ist Nacht, der Wind frischt auf, und von allen Seiten tasten sich Schiffe auf deine Insel zu. Zwischen ihnen und dem Hafen liegt ein Riff.
  >
  > Du hast genau ein Werkzeug: den Lichtkegel deines Leuchtturms. Jedes Schiff, das du beleuchtest, findet die Durchfahrt. Jedes Schiff im Dunkeln treibt auf die Felsen zu. Und es sind immer mehr Schiffe als Licht.
  >
  > Drei kurze Hinweise, dann geht's los. Halte die Maustaste für einen weit reichenden Fokus-Strahl. Drei Wracks, und die Nacht ist verloren.
- **Features (nur belegte):**
  - Ein Lichtkegel, zwei Modi: weit und nah oder fokussiert und fern
  - Drei Nächte, immer mehr Schiffe – und am Ende ein Sturm
  - Spielbar mit Maus oder Touch, direkt im Browser
  - Synthetisierter Ambient-Soundtrack
  - Keine Werbung, keine Käufe, keine Datenerhebung
- **Genre & Tags:** Casual, Arcade, Atmospheric, Minimalist, Lighthouse, Browser, Touch, Short
- **Screenshots** (echt, aus Build 1.0.0 – `marketing/screenshots/`)

| Nr. | Datei | Bildunterschrift |
|---|---|---|
| 1 | 01_titel.png | Nachtwache |
| 2 | 02_nacht1_lotsen.png | Beleuchtete Schiffe finden die Durchfahrt |
| 3 | 03_nacht2_jonglieren.png | Mehrere Schiffe, ein Licht |
| 4 | 04_nacht3_sturm.png | Die Sturmnacht: Regen, Felsen, schmale Durchfahrten |
| 5 | 05_nacht_geschafft.png | Drei Sterne für eine Nacht ohne Wrack |

- **Trailer-Skript (15 s):** 0–3 s Dunkelheit, eine Laterne blinkt · 3–7 s Kegel schwenkt, Schiff wird geführt, Text „Dein Licht ist ihr Weg" · 7–11 s drei Schiffe gleichzeitig, eines treibt aufs Riff · 11–15 s Titel, „Kostenlos im Browser".
- **Preismodell:** kostenlos (Pay what you want optional) – Portfolio-Titel, Reichweite vor Umsatz.
- **Plattform:** jeder aktuelle Browser, Desktop und Handy.
- **Barrierefreiheit:** Gefahren an Form und Farbe erkennbar, Ton abschaltbar (M), Pause jederzeit (P/Esc), Bildschirmwackeln folgt der Systemeinstellung „Bewegung reduzieren".
- **Datenschutz:** Das Spiel sendet keine Daten und speichert nichts auf deinem Gerät.
- **Known Issues:** Nacht 2 ist leichter als geplant · Auf Touch-Geräten steht vor der ersten Berührung „Klicken zum Starten" · Klang auf echten Geräten noch nicht geprüft.

## 3. Social-Media-Content-Plan

| # | Zeitpunkt | Kanal | Format | Inhalt / Hook | Asset | CTA | KPI |
|---|---|---|---|---|---|---|---|
| 1 | T8 | Reddit r/WebGames | Devlog + GIF | „Wir bauen ein Spiel, in dem Licht das einzige Werkzeug ist" | GIF Kern-Loop | Feedback | Kommentare |
| 2 | T9 | Kurzvideo | 15-s-Clip | „Drei Schiffe. Ein Licht." | Screenshot 3 als Standbild | Folgen | Views |
| 3 | Launch | itch.io Devlog | Text + Screens | „Nachtwache ist da – kostenlos im Browser" | Screens 1–5 | Spielen | Plays |
| 4 | Launch | Reddit r/indiegaming | Post (als Entwickler gekennzeichnet) | „Mein Browser-Spiel über einen Leuchtturm – ehrliches Feedback willkommen" | Screen 4 | Spielen, Feedback | Upvotes, Kommentare |
| 5 | +1 Tag | Kurzvideo | 15-s-Trailer | Trailer-Skript oben | Trailer | Link | Klicks |
| 6 | +3 Tage | Reddit r/WebGames | Kurzpost | „Schafft ihr die Sturmnacht ohne Wrack?" | Screen 5 | Spielen | Plays |
| 7 | +5 Tage | itch.io | Community-Post | Antworten auf Feedback, Known Issues | – | Kommentieren | Kommentare |
| 8 | +7 Tage | itch.io Devlog | Rückblick | Echte Zahlen der ersten Woche, Post-Launch-Plan (Nacht 2) | Diagramm | Folgen | Follower |

**Sendefertiger Beispiel-Post (#4):**
> **[Selbst entwickelt] Nachtwache – ein ruhiges Browser-Spiel über einen Leuchtturm im Sturm**
> Du drehst einen Lichtkegel, und nur beleuchtete Schiffe finden durchs Riff. Drei Nächte, Maus oder Touch, keine Werbung, keine Daten. Ich freue mich über ehrliches Feedback – besonders zu Nacht 2, die ist noch zu leicht. 🔦⚓

## Pflicht-Abschnitte

- **Was ist definiert:** Positionierung, 2 Personas, 3 belegte Key Messages, Store-Listing, 8 Social-Posts, KPIs, Known Issues.
- **Annahmen / Unsicherheiten:** `MKT-A01` Zielgruppe primär auf itch.io und Reddit | Risiko mittel · `MKT-A02` 0 € Budget | niedrig · `MKT-A03` KPI-Zielwerte sind Schätzungen | hoch.
- **Abhängigkeiten / offene Fragen:** keine.
- **Entscheidungen:** `MKT-D01` Kostenlos statt Bezahlmodell (Reichweite, Portfolio) · `MKT-D02` Known Issues offen im Store und im Reddit-Post nennen.
- **Status-Update:** Launch-Paket FINAL, alle Aussagen durch den Claims-Check gedeckt, Hype 38/100.
