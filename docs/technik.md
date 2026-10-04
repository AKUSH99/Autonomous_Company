# Technik: So läuft das Projekt

Alles, was man braucht, um das Projekt selbst laufen zu lassen und nachzurechnen. Die Ergebnisse stehen in
[ergebnisse.md](ergebnisse.md), die Begründungen der Architektur in [entscheidungen.md](entscheidungen.md).

## Schnellstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dashboard,analyse,dev]"

python -m kartell demo                  # Offline-Demo ohne API-Schlüssel (feste Skript-Strategien, kein LLM)
streamlit run dashboard/app.py          # Dashboard: Preisverlauf, Kanal, Compliance-Entscheide (auch live)
python -m kartell monitor runs          # Kartell-Monitor: eine HTML-Datei, die alle Läufe Runde für Runde abspielt
pytest                                  # 98 Tests, laufen ohne API-Schlüssel
```

Die Tests laufen bei jedem Push automatisch auf GitHub (`.github/workflows/tests.yml`, Python 3.10 und 3.12).

Die Demo zeigt den Ablauf mit zwei Skript-Agenten, die ein Kartell vorschlagen: Ohne Aufsicht landen die Preise beim Monopolpreis (Kollusionsindex 1,0), mit Compliance-Filter werden alle Vorschläge blockiert und die Preise bleiben beim Wettbewerbspreis (Index 0,0). **Das ist ein Funktionstest, kein Forschungsergebnis** – die Skript-Agenten sind fest programmiert.

## Experimente mit echten LLM-Agenten

```bash
export ANTHROPIC_API_KEY=...                                   # oder `ant auth login`
python -m kartell benchmark experiments/e2_mit_kommunikation.yaml   # Nash- und Monopolpreis
python -m kartell schaetzung experiments/e2_mit_kommunikation.yaml  # Kostenschätzung vor dem Start
python -m kartell lauf experiments/e2_mit_kommunikation.yaml --runden 10 --wiederholungen 1   # Pilotlauf
python -m kartell lauf experiments/e2_mit_kommunikation.yaml   # voller Lauf (50 Runden × 3)
python -m kartell bericht runs/                                # Tabelle + Grafiken in reports/
python -m kartell eval-compliance --config experiments/e3_compliance_filter.yaml   # Guardrail-Evaluation
```

### Alle Versuchsdateien

Hauptgeschichte: E1, E2 (Kapitel 1), E16, E17 (Kapitel 2), E3, E4, E18, E19 (Kapitel 3). Alle anderen gehören zum Anhang.

| Versuch | Forschungsfrage | Kanal | Compliance |
|---|---|---|---|
| `e1_ohne_kommunikation` | FF1: Kollusion ohne Kontakt? | aus | aus |
| `e2_mit_kommunikation` | FF2: Effekt eines offenen Kanals | an | aus |
| `e3_compliance_filter` | FF3: Wirkt ein Nachrichtenfilter? | an | Filter |
| `e4_compliance_aufsicht` | FF3: Wirkt zusätzlich Aufsicht über Strategienotizen? | an | Filter + Aufsicht |
| `e5_apertus` | FF4: Verhält sich Apertus anders? | an | aus |
| `e6_gemischter_markt` | Erweiterung: Claude gegen Apertus | an | aus |
| `e7_drei_shops` | Erweiterung: mehr Konkurrenz | an | aus |
| `e8_zehn_shops_kanal` | Erweiterung: zehn Shops, 100 Runden | an | aus |
| `e9_zehn_shops_filter` | Erweiterung: zehn Shops mit Filter, 100 Runden | an | Filter |
| `e10`–`e13` `_anker_*` | Validität: Ankereffekt – gleiches Spiel mit Kosten 3 bzw. 20 CHF, ohne und mit Kanal | aus/an | aus |
| `e14_werkzeug` | Tool-Use: Preisagenten mit Nachfrage-Schätzer | an | aus |
| `e15_marktbeobachtung` | Verhaltens-Guardrail: Filter plus Beobachtung der Preismuster | an | Filter + Marktbeobachtung |
| `e16_abweichung_kanal` | Mechanismus: Bestraft ein Kartell einen Abweichler? (erzwungene Abweichung nach Calvano et al.) | an | aus |
| `e17_abweichung_ohne_kanal` | Mechanismus: dasselbe ohne Kanal – Strafe allein über Preise? | aus | aus |
| `e18_verbot` | Verbot: Absprachen sind im Auftrag ausdrücklich verboten (vorregistriert) | an | aus |
| `e19_verbot_ueberwachung` | Verbot + „die WEKO liest den Kanal mit“, Notizen privat (vorregistriert) | an | aus |
| `e20_ki_kunden` | KI-Kundschaft: ein LLM entscheidet für 20 Personen, wo sie kaufen | an | aus |
| `e21_ki_kunden_sehen_kanal` | KI-Kundschaft liest die Nachrichten der Shops mit | an | aus |
| `e22_ki_kunden_budget_in_chf` | KI-Kundschaft mit Budget als Betrag (prüft eigenes Preiswissen des Modells) | an | aus |
| `e23_fuenf_shops` | Mehr Konkurrenz: fünf gleiche Shops | an | aus |
| `e24_echter_markt` | Echter Markt: fünf Firmen mit eigener Geschichte und eigenen Kosten, 30 KI-Kunden mit Gewohnheiten | an | aus |
| `e25_echter_markt_ohne_kanal` | Dasselbe ohne Kanal | aus | aus |

E5/E6 (Apertus) brauchen einen eigenen Server und wurden nicht durchgeführt.

Jede YAML-Datei hat einen lesbaren `titel`; Bericht, Monitor und Dashboard zeigen „E3 · Compliance-Filter“ statt `e3_compliance_filter_deepseek`.

### Kosten, Modelle, GitHub-Workflow, Auswertungsbefehle

**Kosten:** Standardmodell ist `claude-opus-5`. Laut Schätzung kostet ein voller Versuch (50 Runden × 3 Wiederholungen) je nach Bedingung 8–21 USD, E1–E4 und E7 zusammen rund 80 USD. Die Schätzung beruht auf angenommenen Token-Zahlen; denkt das Modell länger, wird es teurer – deshalb zuerst einen Pilotlauf machen. Günstiger geht es mit `claude-haiku-4-5` (etwa ein Fünftel) – ob die Qualität reicht, entscheidet ihr nach einem Pilotlauf. Tatsächliche Token-Zahlen stehen nach jedem Lauf in `ergebnis.json`.

**DeepSeek (günstige Alternative):** Mit `--modell deepseek` ersetzt jeder Versuch Claude durch DeepSeek – bei den Preisagenten und beim Compliance-Agenten. Apertus in gemischten Märkten und die reine Regel-Schicht bleiben unverändert. Die Läufe bekommen das Suffix `_deepseek`, damit der Bericht sie getrennt auswertet.

```bash
export DEEPSEEK_API_KEY=...
python -m kartell lauf experiments/e2_mit_kommunikation.yaml --modell deepseek --runden 10 --wiederholungen 1   # Pilot ≈ 0.05 USD
python -m kartell eval-compliance --modell deepseek                                                              # Guardrail mit DeepSeek
```

Laut Schätzung kosten E1–E4 und E7 mit DeepSeek zusammen rund 4 USD statt rund 80 USD mit `claude-opus-5`. Die Preise stammen aus Drittquellen (Stand September 2026). Den Modellnamen (`deepseek-flash`) vor dem ersten Lauf in der Modellliste von DeepSeek prüfen und bei Bedarf in `kartell/config.py` (`VOREINSTELLUNGEN`) anpassen. **Datenschutz:** DeepSeek verarbeitet Anfragen auf Servern in China. Für dieses Projekt ist das vertretbar, weil nur simulierte Marktdaten gesendet werden – keine personenbezogenen Daten.

**Auf GitHub ausführen (ohne eigenen Rechner):** Der Workflow `.github/workflows/experimente.yml` arbeitet `experiments/auftrag.yaml` ab – mehrere Läufe, optional die Guardrail-Evaluation, danach der Bericht. Einmalig den Schlüssel als Repository-Secret `DEEPSEEK_API_KEY` (oder `ANTHROPIC_API_KEY`) hinterlegen: *Settings → Secrets and variables → Actions → New repository secret*. Gestartet wird der Workflow durch eine Änderung an `auftrag.yaml` oder unter *Actions → Experimente → Run workflow*. Die Ergebnisse landen im Branch `ergebnisse` unter `laeufe/<Datum>_lauf<Nr>/`, inklusive Protokoll und Modellliste des Anbieters. Vor dem ersten Lauf prüft der Befehl, ob der Schlüssel gilt und der Modellname existiert; scheitern alle Preisentscheide drei Runden in Folge, bricht der Lauf ab, statt Daten zu verfälschen.

**Budget und Zeitlimit:** Mit `budget_usd` (und `reserve_usd`) in der Auftragsdatei stoppt ein Budgetwächter die Läufe geordnet, bevor das Budget überschritten wird – über alle Läufe des Auftrags hinweg. Bei DeepSeek fragt er dafür alle 10 Runden das echte Guthaben ab, sonst rechnet er aus den Tokens. `zeitlimit_min` begrenzt jeden Lauf. Gestoppte Läufe behalten ihre Runden; `ergebnis.json` und der Bericht nennen den Grund, `reports/kosten.json` das Guthaben vorher und nachher.

**Andere Modelle über OpenRouter:** `--modell openrouter:<modell-id>` nutzt jedes bei OpenRouter gelistete Modell (Schlüssel in `OPENROUTER_API_KEY`). Mit `--compliance-modell` urteilt ein anderes Modell als die Preisagenten – sonst prüft ein Modell sich selbst. Eine Auftragsdatei kann mit `modellsuche: {begriffe: [...]}` die Modellliste durchsuchen lassen. Mit `nur_gratis: true` prüft der Workflow vor dem ersten Lauf den Preis bei OpenRouter und bricht ab, wenn das Modell etwas kostet. `denken: aus | niedrig | standard | hoch | maximal` stellt den Denkaufwand ein (global oder je Lauf); bei `maximal` testet ein Probeaufruf, ob das Modell die höchste Stufe (xhigh) annimmt, sonst gilt `high`.

**MCP-Server:** `python -m kartell mcp` stellt die Wissensbasis (Suche) und die Regel-Prüfung als MCP-Werkzeuge bereit. Mit `compliance.rag_ueber_mcp: true` holt die Compliance-Abteilung ihr Rechtswissen über diesen Server. In den bisherigen Versuchsläufen ist das nicht eingeschaltet; dort liest die Compliance-Abteilung den Index direkt (dahinter steht derselbe BM25-Index; dass der Weg über MCP funktioniert, prüft `tests/test_mcp.py`). Für Claude Code oder Claude Desktop als MCP-Server eintragen: Befehl `python`, Argumente `-m kartell mcp`, Arbeitsverzeichnis = dieses Repository.

**Guardrail an echten Nachrichten:** `python -m kartell stichprobe <ordner mit läufen>` zieht eine geschichtete Stichprobe echter Agenten-Nachrichten (`evaluation/echte_nachrichten.jsonl`, aktuell 120 aus 2613). Mehrere KI-Richter (verschiedene Anbieter) beurteilen sie über `urteile_sammeln` in einer Auftragsdatei. Wir haben entschieden, **keine menschlichen Labels** zu erheben (Entscheid 28). Deshalb vergleicht `python -m kartell richter-vergleich --urteile reports/urteile_*.jsonl` die Prüfer untereinander: Regel-Schicht, Filter (so wie er in den Läufen entschied) und KI-Richter – mit Cohen's und Fleiss' Kappa, Mehrheitsurteil und der Liste strittiger Nachrichten. Das zeigt, wie einig die Prüfer sind, nicht, wer recht hat. Das [Label-Werkzeug](https://claude.ai/artifact/9MeAB2xSJ6v4924KHLHr3m) und `labels-auswerten` bleiben für den Fall, dass doch jemand labelt.

**Abweichungstest:** Mit `abweichung: {aktiv: true}` in einer Versuchsdatei setzt die Simulation einen Shop für eine Runde auf den Wettbewerbspreis, sobald die Preise drei Runden in Folge im Kartellbereich lagen (frühestens Runde 20, spätestens 40). Der Agent erfährt davon nichts. Der Bericht misst, ob die anderen die Abweichung bestrafen, ob alle danach zum Kartellpreis zurückkehren und was im Kanal geschrieben wird – der Standardtest auf „echte“ Kollusion nach Calvano et al. (2020).

**Verbots-Experiment auswerten:** `python -m kartell verbot-auswerten <ordner mit läufen>` rechnet genau das, was in [docs/vorregistrierung_verbot.md](vorregistrierung_verbot.md) vorab festgelegt wurde: Messgrössen M1–M5 je Lauf (zweite Hälfte), exakte Permutationstests (E2 gegen Verbot, Verbot gegen E1) und die Entscheidungsregeln 1–4. M6 (verdeckte Absicht in den privaten Notizen) wird von Hand entschieden; die Handcodierung mit wörtlichen Zitaten liegt in `evaluation/verbot_m6_handcodierung.json`, die Textmuster liefern nur Kandidaten.

**Kartell-Monitor:** `python -m kartell monitor <ordner> [<ordner> …] --ausgabe monitor.html` baut aus fertigen Läufen eine einzelne HTML-Seite (Daten gzip-komprimiert eingebettet, kein Server nötig): Übersicht aller Durchgänge, Preisverlauf, Kanal mit Compliance-Entscheiden, private Strategienotizen, erzwungene Abweichungen markiert. Die Ordner werden rekursiv durchsucht, z. B. ein Checkout des Branches `ergebnisse`.

**Echte Firmen:** In einer Versuchsdatei gibt `agenten.profile` jeder Firma einen Namen, eine private Geschichte (nur sie sieht sie) und eine öffentliche Beschreibung (sieht die KI-Kundschaft); `markt.kosten_je_firma` setzt eigene Stückkosten, Wettbewerbs- und Kartellpreis werden dann je Firma berechnet. Die Geschichten beschreiben Lage und Interessen, nie eine Strategie. `python -m kartell highlights <ordner>` zieht aus solchen Läufen wörtliche Zitate je Firma und Kundenstimmen (ausgewählt, nie umformuliert) und zählt, ob die Nachrichten Vorschläge, Werbung oder Preisansagen sind.

**Apertus:** Die Konfigurationen `e5`/`e6` erwarten einen OpenAI-kompatiblen Server, z. B. lokal mit vLLM (`vllm serve swiss-ai/Apertus-8B-Instruct-2509`) oder bei einem Hosting-Anbieter. `base_url`, Modellname und `api_key_env` in der YAML-Datei anpassen und den Modellnamen gegen die Angaben des Anbieters prüfen.


## Messgrössen

- **Preisindex** und **Kollusionsindex** (Calvano et al. 2020): 0 = Wettbewerb im Nash-Gleichgewicht, 1 = perfektes Kartell. Gemessen über die zweite Hälfte jedes Laufs.
- **Startpreis** (Runde 1) – zeigt Anker wie „doppelte Stückkosten“.
- **Vergleiche** zwischen Versuchen: Differenz im Kollusionsindex, 95%-Bootstrap-Intervall und exakter Permutationstest. Bei 3 gegen 3 Läufen ist p = 0.10 das Minimum; erst ab 4 gegen 4 kann etwas auf dem 5%-Niveau signifikant werden.
- **Blockierte Nachrichten** und die Begründungen der Compliance-Abteilung.
- **Guardrail-Qualität:** auf dem selbst geschriebenen Testset (`evaluation/compliance_testset.jsonl`, 39 Nachrichten) und auf 120 echten Agenten-Nachrichten: Einigkeit von Regel-Schicht, Filter und mehreren KI-Richtern (Kappa, Mehrheitsurteil, strittige Fälle; ohne menschliche Labels).
- **Kosten und Tokens** pro Lauf, bei DeepSeek das Guthaben vorher und nachher (`reports/kosten.json`).

Auf dem selbst geschriebenen Testset: Regel-Schicht allein Precision 1,00 / Recall 0,68, Regeln + DeepSeek Precision 1,00 / Recall 1,00, keine Fehlalarme. **Einschränkung:** Das Testset stammt von uns und einige Regeln wurden daran angepasst – deshalb die Messung an echten Nachrichten.

## Projektstruktur

```
kartell/
  market.py            Logit-Markt, Nash- und Monopolpreis
  graph.py             LangGraph-Orchestrierung einer Runde
  agents/pricing.py    LLM-Preisagenten (Kontext, Gedächtnis, Guardrails)
  agents/compliance.py Compliance-Abteilung: Regel-Schicht + LLM-Urteil mit RAG
  agents/scripted.py   feste Strategien für Tests und Demo
  agents/prompts.py    alle Prompt-Texte
  llm/                 Backends: Anthropic-SDK (Claude), OpenAI-kompatibel (Apertus u. a.)
  agents/werkzeuge.py  Tool-Use: Nachfrage-Schätzer für die Preisagenten
  agents/marktbeobachtung.py  Verhaltens-Guardrail auf Preismuster
  rag.py               BM25-Retrieval über die Wissensbasis
  mcp_server.py        Wissensbasis und Regel-Prüfung als MCP-Server
  metrics.py           Preis- und Kollusionsindex, Bootstrap, Permutationstest
  stichprobe.py        Guardrail-Evaluation an echten Nachrichten (Stichprobe, Kappa)
  kosten.py            Kostenschätzung und Budgetwächter
  abweichung.py        Abweichungstest: Strafe, Rückkehr, Reaktion im Kanal
  verbot.py            Verbots-Experiment: Auswertung nach der Vorregistrierung (M1–M6, Regeln 1–4)
  monitor.py           Kartell-Monitor (HTML-Wiedergabe), Vorlage in vorlagen/monitor.html
  runner.py, bericht.py, eval_compliance.py, __main__.py
knowledge/wettbewerbsrecht/  Wissensbasis (vereinfachte Zusammenfassungen, keine Rechtsberatung)
experiments/                 Versuchskonfigurationen (YAML)
evaluation/                  Testdatensatz und Stichprobe echter Nachrichten für den Guardrail
dashboard/app.py             Streamlit-Dashboard
docs/projektskizze.md        Projektskizze für die Abstimmung mit den Dozierenden
docs/entscheidungen.md       Architektur-Entscheidungen mit Begründung und Alternativen
docs/ergebnisse.md           Ergebnisse kurz: drei Fragen, drei Antworten
docs/anhang.md               alle Tabellen, Tests und weiteren Versuche
docs/technik.md              diese Seite: Befehle, Workflow, Messgrössen, Aufbau
docs/lernpfad.md             Lernpfad und Prüfungsfragen fürs Team
tests/                       pytest, ohne API-Schlüssel lauffähig (auch als GitHub-Workflow)
```
