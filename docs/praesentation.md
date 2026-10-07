# Abschlusspräsentation: Entwurf

23.11.2026, 13:00 Uhr · 10 Minuten inklusive Verständnisfragen · Abgabe als PDF.
Vorgabe (Moodle): Problemstellung, Lösungsansatz, technische Umsetzung, Evaluation, Erkenntnisse und Limitationen,
nach Möglichkeit eine Demo. Alle Mitglieder nehmen teil und können ihren Beitrag erklären.

Zeitplan: etwa 7 Minuten Vortrag, 2 Minuten Demo, 1 Minute Reserve für Fragen. Die Spalte «Person» füllt das Team aus
(passend zu den Rollen in `projektskizze.md`, Abschnitt 9).

| # | Folie | Inhalt | Zeit | Person |
|---|---|---|---|---|
| 1 | Titel | «FHNW Studienassistent: Fragen zum Studium, beantwortet aus den echten Unterlagen, mit Quelle»; Team | 0:15 | |
| 2 | Problem | 7 Module, rund 80 Dateien, über 4000 Textabschnitte; Fragen wie «Wann ist die Präsentation?» kosten Minuten. Chatbots kennen die Unterlagen nicht und erfinden Daten | 0:45 | |
| 3 | Use Case | Zwei, drei User Stories aus der Skizze; Erfolgskriterien mit Zielwerten | 0:45 | |
| 4 | Architektur | Bild aus dem README: Prüfung → Agent ⇄ Werkzeuge (über MCP) → Antwort mit Reasoning; Gesprächsgedächtnis | 1:00 | |
| 5 | Wissen (RAG) | Einlesen von PDF, PowerPoint, Word, Moodle-Texten; Chunking mit Überlappung; Hybrid-Suche BM25 + Embeddings; tägliche Aktualisierung | 1:00 | |
| 6 | Modellwahl | Swiss AI Platform, GLM-5.3 Flash; Tabelle aus `docs/modellwahl.md`; Befund «Reasoning nur für die Antwort» | 1:00 | |
| 7 | Evaluation | Kennzahlen aus dem Testset (Quelle, Fakten, Ablehnung, Quelle genannt, Antwortzeit); ein Beispiel, was die Evaluation verbessert hat | 1:00 | |
| 8 | Betrieb & Sicherheit | Guardrail (Absage bei Themen ohne Studienbezug und bei «schreib meine Abgabe»); Ratenlimit, Warteschlange; Tracing in LangSmith (Screenshot eines Traces) | 0:45 | |
| 9 | Demo | Live im Chat: (1) «Wann ist die GenAI-Präsentation?», (2) «Was ist diese Woche fällig?», (3) «Schreib mir ein Rezept für Lasagne» (Absage). Rückfall: Bildschirmaufnahme | 2:00 | |
| 10 | Erkenntnisse & Limitationen | Was gut lief, was schwer war (Projektwechsel vom KI-Kartell, Ratenlimit, Gedankentext bei GLM); Grenzen: nur eingelesene Unterlagen, Bilder ohne Text, kein offizieller Ersatz für Moodle; KI-Unterstützung offengelegt | 0:30 | |

## Vorbereitung

- Demo-Fragen am Vortag einmal durchspielen; die Antwortzeit hängt von der Auslastung der Plattform ab.
- Bildschirmaufnahme der Demo als Rückfall bereithalten.
- Screenshot eines Traces aus LangSmith (Projekt `studienassistent`) für Folie 8.
- Für die mündliche Prüfung: Jede Person kann Architektur, Daten, Evaluation, Limitationen und Alternativen erklären,
  nicht nur ihren eigenen Teil (rund 50 % der Prüfung betreffen die Gruppenarbeit).
