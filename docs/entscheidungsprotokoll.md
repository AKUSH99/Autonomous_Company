# Entscheidungs-Protokoll

Hier stehen alle globalen Entscheidungen des Studios im Format **Was · Wer · Warum · Wann**. Die Einträge `SET-xx` sind die **Setup-Entscheidungen**, die der Producer beim Aufbau des Studios getroffen hat – dort, wo die Ausgangsspezifikation Spielraum ließ oder bewusst erweitert wurde. Während einer Simulation ergänzt der Producer ab `D-001`.

## Setup-Entscheidungen (vor T1)

| ID | Was wurde entschieden | Wer | Warum | Wann |
|---|---|---|---|---|
| SET-01 | **Tick-basiertes Zeitmodell**: 13 Ticks Standard-Budget, einmalig +2 Ticks Puffer, danach Scope kürzen statt Zeit verlängern. | PRD | Bildet die Zeitlogik von Game Dev Story ab und verhindert endlose Iterationsschleifen ohne Menschen, die einen Schlussstrich ziehen. | Setup, 2026-09-23 |
| SET-02 | **Hub-and-Spoke-Kommunikation**: Formale Übergaben laufen über den Producer; direkte Konsultationen zwischen Agenten sind erlaubt, immer mit CC an den Producer. | PRD | Hält jede Übergabe nachvollziehbar, ohne die parallele Abstimmung (z. B. Artist ↔ Designer) auszubremsen. | Setup, 2026-09-23 |
| SET-03 | **Default-Weiterarbeit**: Jede Blocker-Meldung enthält Optionen, Empfehlung und Default. Der Agent arbeitet sofort mit dem Default weiter; antwortet der Producer nicht im selben Tick, gilt der Default. | PRD | Ohne menschliche Eingriffe darf kein Agent auf eine Antwort warten müssen – sonst droht ein Deadlock. | Setup, 2026-09-23 |
| SET-04 | **Iterationslimit**: maximal 2 Iterationen pro Dokument und Konflikt, danach entscheidet der Producer. | PRD | Begrenzt Perfektionsschleifen zwischen Agenten. | Setup, 2026-09-23 |
| SET-05 | **Feste Prioritätenordnung für Konflikte**: Stabilität > Tick-Budget/Scope > Spaß des Kern-Loops > Lesbarkeit > Vision/Ästhetik > Stretch-Goals. | PRD | Macht Producer-Entscheidungen vorhersehbar und begründbar statt beliebig. | Setup, 2026-09-23 |
| SET-06 | **Kairosoft-Kernwerte als Studio-Metriken**: Spaß, Kreativität, Grafik, Sound (1–10), Bugs, Hype (0–100). Agenten liefern Prognosen, QA misst unabhängig; QA-Befunde ersetzen Prognosen. | PRD | Übersetzt die Spielwerte aus Game Dev Story in messbare, transparente Größen; trennt Selbsteinschätzung von unabhängiger Prüfung. | Setup, 2026-09-23 |
| SET-07 | **Frühe Parallel-Einbindung** (Erweiterung des Basis-Workflows): DEV-Machbarkeits-Check, ART-Stil-Skizze und CD-Vision-Check bereits in Phase 2 (T4); QA-Smoke-Test bei Alpha (T6); Marketing startet ab T7 mit Positionierung und Teasern statt erst in Phase 5. | PRD | Kairosoft-Logik: Das Team arbeitet parallel. Machbarkeitsprobleme werden vor dem Design-Lock sichtbar statt erst im Prototyp; Hype entsteht wie in Game Dev Story während der Produktion. | Setup, 2026-09-23 |
| SET-08 | **Mock-Review durch QA**: vier Kritiker-Personas × 1–10 = /40. Launch-Gate: 0 kritische Bugs (nicht verhandelbar) und Mock-Review ≥ 24/40; Ziel ≥ 32/40. | PRD | Simuliert das Kritiker-Urteil aus Game Dev Story als nachvollziehbares Qualitäts-Gate; QA ist als unabhängige Instanz dafür am besten geeignet. | Setup, 2026-09-23 |
| SET-09 | **Standard-Tech-Stack**: Browser-Spiel mit HTML5 Canvas + JavaScript ohne Build-Schritt; DEV darf mit Entscheidungsmatrix abweichen. | PRD | Maximale Portabilität, direkter itch.io-Upload, QA kann ohne Installation testen. Die Engine-Wahl bleibt trotzdem DEVs autonome Entscheidung. | Setup, 2026-09-23 |
| SET-10 | **Asset-Lieferstufen & Platzhalter-Fallback**: ART liefert echte Dateien, code-basierte Assets (SVG, Pixel-Matrix, Synthese-Parameter) oder präzise Beschreibungen; DEV lädt bei fehlenden Assets Platzhalter. Standard fürs MVP: code-basierte Assets. | PRD | Artist und Programmierer blockieren sich nie gegenseitig; der Build hat auch ohne externe Werkzeuge Grafik und Sound. | Setup, 2026-09-23 |
| SET-11 | **Launch als Simulationsereignis**: Marketing erstellt sendefertige Inhalte und einen Ausführungsplan, führt aber keine echten Veröffentlichungen durch. | PRD | Die Autonomie gilt innerhalb der Simulation. Echte Veröffentlichungen hätten reale Außenwirkung und liegen außerhalb dieses Rahmens. | Setup, 2026-09-23 |
| SET-12 | **Ethik-Leitplanken** in allen Rollen: keine Lootboxen/Glücksspiel-Mechaniken und Dark Patterns, keine Datenerhebung ohne ausdrückliche Einwilligung, nur eigene oder CC0-Assets mit dokumentierter Quelle, keine Fake-Reviews und kein Astroturfing, Marketing verspricht nur, was der Build nachweislich kann. | PRD | Verantwortungsvolle Produktentwicklung und Datenschutz sind Grundwerte des Studios; Transparenz verhindert „Black-Box"-Entscheidungen. | Setup, 2026-09-23 |

## Simulations-Entscheidungen

| ID | Was wurde entschieden | Wer | Warum | Wann | Verworfene Optionen | Revisionsauslöser |
|---|---|---|---|---|---|---|
| D-001 | | PRD | | T1 | | |
