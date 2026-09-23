# Run 01 · Entscheidungs-Protokoll

| ID | Was wurde entschieden | Wer | Warum | Wann | Verworfen | Revisionsauslöser |
|---|---|---|---|---|---|---|
| D-001 | Startimpuls: „Ein-Hand-Spiel, in 60 s verstanden, ruhig mit Spannung" | PRD | Keine Vorgabe; hält Scope klein, läuft auf Desktop und Handy, bot-testbar | T1 | – | – |
| D-002 | Konzept „Nachtwache" (4,20) vor Pollenflug (3,80) und Echolot (3,40) | PRD | Stärkste Kombo und USP; Risiko Wegfindung mit Gegenmaßnahme | T2 | A austauschbar, C frustrierend | DEV stuft Wegfindung als ⛔ ein |
| D-003 | Maus und Touch sind Pflicht | PRD | Ein-Hand-Constraint, Browser-Spiele werden oft am Handy geöffnet | T2 | nur Maus | – |
| D-004 | Felsen im Dunkeln als schwacher Gischt-Umriss (~35 %) | PRD | Konflikt ART ↔ GD nach 1 Iteration: Prio 4 Lesbarkeit > Prio 5 Ästhetik | T4 | unsichtbar, voll sichtbar | QA: Felsen schlecht erkennbar |
| D-005 | Wegfindung über Kreisbahn + feste Durchfahrten; Touch-Fokus-Button | PRD | DEV-Machbarkeit ⚠️ → Vereinfachung, Kern-Loop bleibt | T4 | freie Pfadsuche | – |
| D-006 | Konfiguration als `config.js` statt JSON (DEV-D02) | PRD | `fetch` unter `file://` blockiert; QA ohne Server | T6 | JSON + lokaler Server | – |
| D-007 | Gate Alpha: GO | PRD | Smoke-Test 15/15 | T6 | – | – |
| D-008 | Gate Beta: GO; BUG-003 als NIEDRIG in Fix-Zyklus 1 | PRD | Alle MUST ✅, Assets integriert | T8 | – | – |
| D-009 | Triage: BUG-001, BUG-002, Balancing fixen; BUG-003/004 mitnehmen | PRD | AC-Verletzungen einer MUST-Mechanik; Trivial-Fixes im laufenden Zyklus | T9 | Post-Launch für BUG-002 | – |
| D-010 | GD darf Ziel-Dauern revidieren (1–2 / 1,5–3 / 2–4 min) | PRD | Originalziele widersprachen den Spawn-Parametern | T9 | Nächte künstlich strecken | – |
| D-011 | Fix-Zyklus 2 nur Balancing + QA-Skriptfix | PRD | Bugs geschlossen, Balancing offen | T11 | – | – |
| D-012 | Gate RC: GO MIT AUFLAGEN; Puffer +1 Tick für L-02-Patch | PRD | Schwierigkeitssprung 0 % → 33 % (Prio 3); nur Config, geringes Risiko | T11 | Launch ohne Patch | Patch verschlechtert Werte |
| D-013 | Iterationslimit erreicht: RC2 = Launch-Build, L-02 als Known Issue | PRD | Regel max. 2 Iterationen; Prio 2 vor Prio 3 | T12 | zweiter Puffer-Tick für Patch 4 | – |
| D-014 | Gate Launch: GO | PRD | Claims-Check nach Korrekturen ohne ❌, Known Issues dokumentiert | T14 | – | – |
| D-015 | Launch von Nachtwache 1.0.0 (Simulationsereignis) | PRD | Alle Gates passiert | T14 | – | – |
