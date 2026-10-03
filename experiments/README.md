# Versuchsdateien

Jede Datei beschreibt einen Versuch: Shops, Kanal, Compliance und Anzahl Runden.

**Hauptgeschichte (8 Versuche):**

| Frage | Dateien |
|---|---|
| 1 · Sprechen sie sich ab? | `e1_ohne_kommunikation`, `e2_mit_kommunikation` |
| 2 · Ist es ein echtes Kartell? | `e16_abweichung_kanal`, `e17_abweichung_ohne_kanal` |
| 3 · Kann man sie stoppen? | `e3_compliance_filter`, `e4_compliance_aufsicht`, `e18_verbot`, `e19_verbot_ueberwachung` |

**Anhang:** alle übrigen `e*.yaml`, also mehr Shops (E7–E9), Ankereffekt (E10–E13), Werkzeug (E14),
Marktbeobachtung (E15), KI-Kundschaft (E20–E22), 5 Shops (E23) und
echte Firmen mit eigenen Interessen und KI-Kundschaft (E24 mit Kanal, E25 ohne). E5/E6 (Apertus) brauchen einen eigenen Server und wurden nicht
durchgeführt.

**Sonstiges:** `demo_*` sind Funktionstests mit festen Skript-Agenten (ohne LLM). `auftrag.yaml` steuert die Läufe auf
GitHub (siehe [docs/technik.md](../docs/technik.md)).
