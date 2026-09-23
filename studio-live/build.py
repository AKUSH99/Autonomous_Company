import json, pathlib, sys

SP = pathlib.Path(__file__).parent
REPO = pathlib.Path(__file__).resolve().parent.parent

def tick(t, phase=None):
    e = {'type': 'tick', 't': t}
    if phase: e['phase'] = phase
    return e
def work(who, label): return {'type': 'work', 'who': who, 'label': label}
def doc(who, to, title, text): return {'type': 'doc', 'who': who, 'to': to, 'title': title, 'text': text}
def stats(who, v, src): return {'type': 'stats', 'who': who, 'v': v, 'src': src}
def dec(i): return {'type': 'decision', 'id': i}
def banner(t, sub=None):
    e = {'type': 'banner', 'text': t}
    if sub: e['sub'] = sub
    return e

R = [
  tick(1, 'Ideenfindung'),
  work('PRD', 'Startimpuls'),
  doc('PRD', 'CD', 'Tick-Report T1 · AUF-001',
      'D-001 · Startimpuls (keine Vorgabe der Umgebung, selbst gewählt):\n'
      '**„Ein Spiel, das man mit einer Hand spielt (Maus oder Finger) und in 60 Sekunden versteht. Stimmung: ruhig, aber mit Spannung."**\n\n'
      'AUF-001 → CD: 2–3 substanziell unterschiedliche Konzeptoptionen\n'
      '- Constraints: Browser, MVP in 4 Entwicklungs-Ticks\n- Default bei Unklarheit: Casual, 2D, 5–10 Minuten'),
  dec('D-001'),
  work('CD', '3 Konzepte'),
  doc('CD', 'PRD', 'Konzept-Paket v0.1',
      '### Option A · Pollenflug (sicher)\nArcade-Sammelspiel × Bienenwiese · Score 3,80\n'
      '### Option B · Nachtwache (mutig)\nEchtzeit-Lotsenspiel × Leuchtturm bei Nacht · Score 4,20\n'
      '„Du bist Leuchtturmwärterin. Nur Schiffe in deinem Lichtkegel finden den Weg durchs Riff."\n'
      '**Great Combo:** Die Mechanik „Licht lenken" ist zugleich die Fantasie des Settings.\n'
      '### Option C · Echolot (Wildcard)\nGedächtnis-Navigation × Tiefsee-Sonar · Score 3,40\n\n'
      '**Empfehlung: B** – stärkste Kombo, Risiko Wegfindung mit Gegenmaßnahme.'),
  stats('CD', {'spass': 7, 'kreativitaet': 8, 'grafik': 8, 'sound': 7}, 'Prognose CD'),
  tick(2),
  work('PRD', 'Auswahlmatrix'),
  doc('PRD', 'ALL', 'D-002 · Gate Konzept-Freeze',
      'Konzept **„Nachtwache"** gewählt – B 4,20 vor A 3,80 und C 3,40.\n'
      '- Verworfen: A (austauschbar), C (frustrierend, schwer testbar)\n'
      '- D-003: Maus UND Touch sind Pflicht\n\n**GATE Konzept-Freeze: GO**'),
  dec('D-002'), dec('D-003'),
  {'type': 'project', 'title': 'Nachtwache', 'genre': 'Lotsenspiel × Leuchtturm bei Nacht'},
  banner('Konzept-Freeze!', 'Nachtwache'),
  tick(3, 'Design'),
  work('GD', 'GDD schreiben'),
  doc('GD', 'DEV ART CD', 'GDD v0.9',
      '- M-01 Lichtkegel drehen · M-02 Fokus-Strahl · M-03 Lotsen\n- M-04 Riff & Schiffbruch · M-05 Hafen & Nachtziel\n'
      '- 3 Nächte: Ruhige See (5 Schiffe) · Auflandiger Wind (8) · Sturmnacht (12)\n'
      '- 13 Balancing-Parameter, 12 Akzeptanzkriterien\n\n'
      '**AC-04:** Ein durchgehend beleuchtetes Schiff erreicht den Hafen ohne Felskontakt.\n'
      'GD-A02: Heimzug 0,35 – Risiko hoch, QA misst.'),
  stats('GD', {'spass': 7, 'kreativitaet': 8}, 'Prognose GD'),
  tick(4),
  work(['DEV', 'ART', 'CD'], ['Machbarkeit', 'Stil-Skizze', 'Vision-Check']),
  doc('DEV', 'GD', 'Machbarkeits-Check',
      '- M-03 Lotsen durchs Riff: ⚠️ – freie Pfadsuche sprengt das Budget\n'
      '- **Vereinfachung:** Schiffe umrunden das Riff auf einer Kreisbahn bis zur nächsten Durchfahrt\n'
      '- Fokus per Touch: ⚠️ → eigener Fokus-Button\n\nFazit: passt in 4 Entwicklungs-Ticks, keine ⛔.'),
  doc('ART', 'GD DEV', 'Stil-Skizze v0.1',
      'Stil-Säulen: nachtblau · bernsteinwarm · still\n'
      'Palette: Meer #0B1A2E · Kegel #FFD98A · Laternen #FFB347 · Gischt #9FB4C7\n\n'
      '**Felsen: im Dunkeln unsichtbar**, nur im Lichtkegel – maximale Spannung.'),
  doc('CD', 'GD', 'Vision-Check',
      'Ergebnis: ⚠️ kleine Abweichung\n- Tutorial-Hinweise dürfen die Stille nicht zerreden: höchstens 3 Einzeiler\n- Positiv: Fokus-Strahl verstärkt „Licht ist alles"'),
  doc('GD', 'ART', 'Konsultation · Konflikt',
      '**GD → ART:** Können Felsen im Dunkeln schwach sichtbar sein? Sonst wird die Kernentscheidung „Welches Schiff zuerst?" zum Raten.\n'
      '**ART → GD:** Sichtbare Felsen nehmen der Dunkelheit ihren Schrecken.\n\n→ Nach einer Runde ungelöst – der Producer entscheidet.'),
  work('PRD', 'Konflikt lösen'),
  doc('PRD', 'ALL', 'D-004 · Gate Design-Lock',
      '**D-004:** Felsen im Dunkeln als schwache Gischt-Umrisse (~35 %), volle Details nur im Licht.\n'
      'Warum: Prio 4 Lesbarkeit schlägt Prio 5 Ästhetik – kostet keine Ticks.\n'
      '**D-005:** Kreisbahn-Wegpunkte und Fokus-Button übernommen.\n\n**GATE Design-Lock: GO**'),
  dec('D-004'), dec('D-005'),
  banner('Design-Lock!'),
  tick(5, 'Entwicklung'),
  work(['DEV', 'ART'], ['Tech-Design', 'Style-Guide']),
  doc('DEV', 'ART QA', 'Tech-Design-Dokument v1.0',
      '- Canvas + JavaScript ohne Build-Schritt (Matrix 5/5/5/4/5/5)\n'
      '- Simulation getrennt vom Rendering, feste Zeitschritte → reproduzierbar\n'
      '- config.js mit GDD-IDs (DEV-D02: JSON scheitert unter file://)\n'
      '- Debug-API: simulate({seed, level, bot}) für QA-Bots'),
  doc('ART', 'DEV GD QA', 'Art-Style-Guide + Asset-Liste',
      '- 17 Grafik-IDs, 8 Soundeffekte, 1 Musikstück – alles als Code (Lieferstufe 2)\n'
      '- Geführte Schiffe: türkiser Ring, der die Rest-Orientierung abbaut – Info nie nur über Farbe\n'
      '- Audio: Nebelhorn (Sägezahn + Tiefpass), Glocke (880/1320/2210 Hz), a-Moll-Pads 56 BPM'),
  tick(6),
  work('DEV', 'Alpha bauen'),
  doc('DEV', 'QA', 'Build-Report Alpha 0.1.0',
      '- Kern-Loop spielbar von Titel bis Sieg/Niederlage, alle 5 Screens\n- Assets: Platzhalter (assets.js folgt)\n- Bekannt: Konsolenmeldung wegen fehlendem assets.js'),
  work('QA', 'Smoke-Test'),
  doc('QA', 'DEV', 'Smoke-Test Alpha',
      'Modus A – echter Headless-Chromium.\n**15/15 Checks:** Start, Kegel folgt Zeiger, Fokus, Pause friert Zeit ein, Niederlage, Sieg, alle 3 Nächte, zurück zum Titel.\nKeine Laufzeitfehler.'),
  dec('D-007'),
  banner('Alpha!'),
  tick(7),
  work(['ART', 'DEV', 'MKT'], ['Assets + Audio', 'Content', 'Positionierung']),
  doc('MKT', 'PRD', 'Positionierungs-Entwurf',
      'Für Menschen, die in kurzen Pausen etwas Ruhiges mit Spannung suchen: ein Browser-Lotsenspiel, in dem ein einziger Lichtkegel über Rettung und Schiffbruch entscheidet.\n\nTeaser (Absicht): Devlog „Licht ist das einzige Werkzeug".'),
  {'type': 'hype', 'v': 12},
  stats('ART', {'grafik': 7, 'sound': 6}, 'Asset-Check ART'),
  tick(8),
  work('DEV', 'Beta integrieren'),
  doc('DEV', 'QA', 'Build-Report Beta 0.2.0',
      '- Alle MUST-Mechaniken ✅, Sterne + Tutorial ✅, Regen (COULD) ✅\n- 17/17 Grafiken, 8/8 SFX, 1/1 Musik – keine Platzhalter mehr'),
  doc('ART', 'DEV', 'Asset-Check im Build',
      '**BUG-003 (NIEDRIG):** Der Kegel wirkt über dem blauen Meer kühl-weißlich statt bernsteinfarben.'),
  {'type': 'bugs', 'v': ['NIEDRIG'], 'who': 'ART', 'label': 'BUG-003'},
  {'type': 'hype', 'v': 22},
  dec('D-008'),
  banner('Beta!'),
  tick(9, 'Testing'),
  work('QA', '360 Bot-Nächte'),
  doc('QA', 'PRD', 'Bug- & Feedback-Report Beta',
      '**Balancing** (Casual-Bot, 40 Seeds): Fehlschlag 0 % / 0 % / 3 % – Ziel < 10 / 20–40 / 30–50 %\n'
      '- **BUG-001 (MITTEL):** 9 von 480 durchgehend beleuchteten Schiffen zerschellen an äußeren Felsen\n'
      '- **BUG-002 (MITTEL):** Durchfahrten 79,9 / 70,5 / 62,1 px statt 60 / 50 / 40\n'
      '- Ziel-Dauern widersprechen den Spawn-Parametern\n\nEmpfehlung: Fix-Zyklus.'),
  stats('QA', {'spass': 5, 'kreativitaet': 8, 'grafik': 7, 'sound': 6}, 'QA-Messung (Bots)'),
  {'type': 'bugs', 'v': ['MITTEL', 'MITTEL', 'NIEDRIG', 'NIEDRIG'], 'who': 'QA', 'label': '4 Bugs'},
  {'type': 'review', 'v': [7, 4, 7, 6]},
  work('PRD', 'Triage'),
  doc('PRD', 'DEV GD ART', 'D-009 · Triage',
      '- BUG-001, BUG-002 fixen – verletzen AC-04 bzw. die Spezifikation\n- Balancing per GD-Patch, BUG-003/004 laufen im selben Zyklus mit\n- **D-010:** GD darf die Ziel-Dauern revidieren'),
  dec('D-009'), dec('D-010'),
  tick(10),
  work(['DEV', 'GD', 'ART'], ['Bugfixes', 'Balancing-Patch 1', 'Kegel-Farbe']),
  doc('DEV', 'QA', 'Fix-Report 0.2.1-beta',
      '- **BUG-001:** Vorausschau-Ausweichen – liegt ein Fels voraus, lenkt das Schiff zur freien Seite\n- **BUG-002:** Riff von Kante zu Kante aufgebaut, lichte Breite exakt'),
  doc('GD', 'DEV QA', 'Balancing-Patch 1',
      '| Param | alt | neu |\n| Kegel | 22° | 18° |\n| Orientierung | 2,5 s | 2,0 s |\n| Tempo im Dunkeln | 24 | 27 |\n| Schiffe | 5/8/12 | 7/14/22 |\n\nNeue Ziel-Dauern: 1–2 / 1,5–3 / 2–4 min'),
  work('QA', 'Regression'),
  doc('QA', 'PRD', 'Regression Fix 1',
      '- AC-04: 0/280 · 0/560 · 0/880 Wracks ✅\n- Durchfahrten exakt 60 / 50 / 40 px ✅\n- Casual-Fehlschlag 0 % / 0 % / 5 % ❌ – weiter zu leicht\n\nEigener Fehler: Die AC-12c-Prüfung im Testskript wertet falsch aus → Fix in T11.'),
  {'type': 'bugs', 'v': [], 'who': 'DEV', 'label': '4 gefixt'},
  tick(11),
  work('GD', 'Balancing-Patch 2'),
  doc('GD', 'DEV QA', 'Balancing-Patch 2',
      '- Orientierung 2,0 → 1,4 s (Hauptstellschraube)\n- Tempo geführt 42 → 38 · Heimzug 0,35 → 0,5\n- max. gleichzeitig in Nacht 2/3: 4/5 → 5/6'),
  work('QA', 'RC-Test'),
  doc('QA', 'PRD', 'RC-Report 1.0.0-rc1',
      '| Nacht | Casual | Ziel |\n| 1 | 0 % | < 10 % ✅ |\n| 2 | 0 % | 20–40 % ❌ |\n| 3 | 33 % | 30–50 % ✅ |\n\nAC-04 2000/2000 ✅ · UI 9/9 ✅ · 0 kritische Bugs\n**Empfehlung: GO MIT AUFLAGEN**'),
  stats('QA', {'spass': 7, 'kreativitaet': 8, 'grafik': 8, 'sound': 6}, 'QA-Messung (Bots)'),
  {'type': 'review', 'v': [8, 6, 7, 8]},
  work('PRD', 'Gate RC'),
  doc('PRD', 'ALL', 'D-012 · Gate Release Candidate',
      '**GO MIT AUFLAGEN.** Die Schwierigkeit springt von 0 % auf 33 % – ein Puffer-Tick für einen Patch nur an Nacht 2.'),
  dec('D-011'), dec('D-012'),
  banner('Release Candidate!'),
  tick(12, 'Puffer'),
  work('GD', 'Patch 3 · Nacht 2'),
  doc('QA', 'PRD', 'Regression RC2',
      'Nacht 2 Casual weiterhin 0 % (Ø Wracks 0,4 → 0,5). Keine Rückschritte.\nHinweis: Hauptunterschied zu Nacht 3 sind gleichzeitige Schiffe (5 vs. 6).'),
  work('PRD', 'Iterationslimit'),
  doc('PRD', 'ALL', 'D-013 · Iterationslimit',
      'Drei Balancing-Patches – Regel „max. 2 Iterationen" überschritten.\n- RC2 wird Launch-Build\n- Nacht 2 → Known Issue, Patch nach dem Launch\n- Verworfen: zweiter Puffer-Tick (Perfektionsschleife)'),
  dec('D-013'),
  tick(13, 'Launch'),
  work(['MKT', 'DEV'], ['Launch-Paket', 'Screenshots']),
  doc('MKT', 'QA', 'Launch-Paket v0.9',
      'Tagline: **„Dein Licht ist ihr einziger Weg nach Hause."**\n- 5 echte Screenshots, 8 Social-Posts, Store-Listing, KPIs als Schätzung\n- Claims u. a.: „steigende Schwierigkeit" · „in einer Minute verstanden" · „Synth-Soundtrack"'),
  {'type': 'hype', 'v': 38},
  work('QA', 'Claims-Check'),
  doc('QA', 'MKT', 'Claims-Check',
      '4 ✅ · 3 ⚠️ · 0 ❌\n- ⚠️ „steigende Schwierigkeit" – gemessen steigt sie erst in Nacht 3 → „immer mehr Schiffe"\n- ⚠️ „in einer Minute verstanden" – nicht messbar → „drei kurze Hinweise"\n- ⚠️ „Synth-Soundtrack" – klanglich ungeprüft → neutral formulieren'),
  tick(14),
  work('PRD', 'Launch'),
  doc('PRD', 'ALL', 'Launch-Bericht & Post-Mortem',
      'Nachtwache 1.0.0 · 13 Ticks + 1 Puffer · Mock-Review 29/40 · Bugs K0 · M1 · N1\n\n**Studio-Wissen für Run 02:**\n- Ziel-Dauern gegen Spawn-Parameter rechnen\n- Bot-Balancing schon ab Alpha\n- Geometrie-Vorgaben messen statt dem Raster trauen\n- Eine Schwierigkeits-Stellschraube pro Nacht\n- Testskripte zuerst gegen einen bekannten Fall prüfen'),
  {'type': 'bugs', 'v': ['MITTEL', 'NIEDRIG'], 'who': 'PRD', 'label': 'Known Issues'},
  dec('D-014'), dec('D-015'),
  banner('Launch!', 'Nachtwache 1.0.0'),
  {'type': 'launch', 'title': 'Nachtwache 1.0.0', 'tagline': 'Dein Licht ist ihr einziger Weg nach Hause.', 'shot': True, 'link': 'https://claude.ai/artifact/V9HZS3qVg8vxEhdgzKxRap'},
]

t = (SP / 'template.html').read_text()
for role, f in [('PRD', '00_producer'), ('CD', '01_creative_director'), ('GD', '02_game_designer'), ('DEV', '03_programmierer'),
                ('ART', '04_artist_sound'), ('QA', '05_qa_testing'), ('MKT', '06_marketing')]:
    txt = (REPO / 'prompts' / f'{f}.md').read_text()
    assert '</script' not in txt
    t = t.replace(f'__P_{role}__', txt)
replay = json.dumps(R, ensure_ascii=False)
assert '</script' not in replay
t = t.replace('__REPLAY__', replay)
t = t.replace('__SHOT__', (SP / 'nachtwache_thumb.b64').read_text().strip())
(SP / 'index.html').write_text(t)
print('events', len(R), 'size KB', len(t.encode()) // 1024)
