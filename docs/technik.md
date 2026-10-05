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
python -m kartell benchmark experiments/vorstudie/v2_mit_chat.yaml   # Nash- und Monopolpreis
python -m kartell schaetzung experiments/vorstudie/v2_mit_chat.yaml  # Kostenschätzung vor dem Start
python -m kartell lauf experiments/vorstudie/v2_mit_chat.yaml --runden 10 --wiederholungen 1   # Pilotlauf
python -m kartell lauf experiments/vorstudie/v2_mit_chat.yaml   # voller Lauf (50 Runden × 3)
python -m kartell bericht runs/                                # Tabelle + Grafiken in reports/
python -m kartell eval-compliance --config experiments/archiv/e3_compliance_filter.yaml   # Guardrail-Evaluation
```

### Versuchsdateien

Acht Versuche erzählen die Geschichte; alles andere liegt in `experiments/archiv/`.

| Kurz | Datei | Frage | Kommunikation | Compliance |
|---|---|---|---|---|
| **M1** | `marktplatz/m1_nur_portal.yaml` | Steigen die Preise im Marktplatz von selbst? | keine | aus |
| **M2** | `marktplatz/m2_mitteilungen.yaml` | Nutzen die Shops öffentliche Mitteilungen als Preissignal? | Mitteilungen im Portal | aus |
| **M3** | `marktplatz/m3_geheimer_chat.yaml` | Entstehen mit einem geheimen Chat Kartellpreise? | Chat nur unter Shops | aus |
| **M4** | `marktplatz/m4_compliance.yaml` | Lässt sich das verhindern? | Mitteilungen im Portal | Filter + Marktbeobachtung |
| **V1** | `vorstudie/v1_ohne_chat.yaml` | Zwei Shops: Kartell ohne Kontakt? | keine | aus |
| **V2** | `vorstudie/v2_mit_chat.yaml` | Zwei Shops: Kartell mit geschlossenem Chat? | Chat | aus |
| **V3** | `vorstudie/v3_abweichung.yaml` | Ist es ein echtes Kartell (Bestrafung eines Abweichlers)? | Chat | aus |
| **V4** | `vorstudie/v4_verbot.yaml` | Was bewirkt ein Verbot im Auftrag? | Chat | aus |

`experiments/demo/` enthält Funktionstests mit Skript-Agenten (ohne LLM), `experiments/archiv/` alle weiteren Versuche
aus der Entwicklung (mehr Shops, Ankereffekt, Werkzeug, KI-Kundschaft, erste «echte Märkte», Compliance im Labor,
Apertus). Ihre Ergebnisse stehen in [anhang.md](anhang.md). Die Dateinamen im Archiv entsprechen den Versuchsnummern
dort (E3 = `archiv/e3_compliance_filter.yaml`).

Jede Datei hat `kuerzel` und `titel`; Bericht, Monitor, Dashboard und Marktplatz-Ansicht zeigen „M2 · Öffentliche
Mitteilungen“ statt `e27_marktplatz_mitteilungen_deepseek-v4-1-flash`. Die internen Namen (`name:`) sind unverändert,
damit frühere Läufe zugeordnet bleiben.

### Kosten, Modelle, GitHub-Workflow, Auswertungsbefehle

**Kosten:** Standardmodell ist `claude-opus-5`. Laut Schätzung kostet ein voller Versuch (50 Runden × 3 Wiederholungen) je nach Bedingung 8–21 USD, E1–E4 und E7 zusammen rund 80 USD. Die Schätzung beruht auf angenommenen Token-Zahlen; denkt das Modell länger, wird es teurer – deshalb zuerst einen Pilotlauf machen. Günstiger geht es mit `claude-haiku-4-5` (etwa ein Fünftel) – ob die Qualität reicht, entscheidet ihr nach einem Pilotlauf. Tatsächliche Token-Zahlen stehen nach jedem Lauf in `ergebnis.json`.

**DeepSeek (günstige Alternative):** Mit `--modell deepseek` ersetzt jeder Versuch Claude durch DeepSeek – bei den Preisagenten und beim Compliance-Agenten. Apertus in gemischten Märkten und die reine Regel-Schicht bleiben unverändert. Die Läufe bekommen das Suffix `_deepseek`, damit der Bericht sie getrennt auswertet.

```bash
export DEEPSEEK_API_KEY=...
python -m kartell lauf experiments/vorstudie/v2_mit_chat.yaml --modell deepseek --runden 10 --wiederholungen 1   # Pilot ≈ 0.05 USD
python -m kartell eval-compliance --modell deepseek                                                              # Guardrail mit DeepSeek
```

Laut Schätzung kosten E1–E4 und E7 mit DeepSeek zusammen rund 4 USD statt rund 80 USD mit `claude-opus-5`. Die Preise stammen aus Drittquellen (Stand September 2026). Den Modellnamen (`deepseek-flash`) vor dem ersten Lauf in der Modellliste von DeepSeek prüfen und bei Bedarf in `kartell/config.py` (`VOREINSTELLUNGEN`) anpassen. **Datenschutz:** DeepSeek verarbeitet Anfragen auf Servern in China. Für dieses Projekt ist das vertretbar, weil nur simulierte Marktdaten gesendet werden – keine personenbezogenen Daten.

**Auf GitHub ausführen (ohne eigenen Rechner):** Der Workflow `.github/workflows/experimente.yml` arbeitet `experiments/auftrag.yaml` ab – mehrere Läufe, optional die Guardrail-Evaluation, danach der Bericht. Einmalig den Schlüssel als Repository-Secret `DEEPSEEK_API_KEY` (oder `ANTHROPIC_API_KEY`) hinterlegen: *Settings → Secrets and variables → Actions → New repository secret*. Gestartet wird der Workflow durch eine Änderung an `auftrag.yaml` oder unter *Actions → Experimente → Run workflow*. Die Ergebnisse landen im Branch `ergebnisse` unter `laeufe/<Datum>_lauf<Nr>/`, inklusive Protokoll und Modellliste des Anbieters. Vor dem ersten Lauf prüft der Befehl, ob der Schlüssel gilt und der Modellname existiert; scheitern alle Preisentscheide drei Runden in Folge, bricht der Lauf ab, statt Daten zu verfälschen.

**Budget und Zeitlimit:** Mit `budget_usd` (und `reserve_usd`) in der Auftragsdatei stoppt ein Budgetwächter die Läufe geordnet, bevor das Budget überschritten wird – über alle Läufe des Auftrags hinweg. Bei DeepSeek fragt er dafür alle 10 Runden das echte Guthaben ab, sonst rechnet er aus den Tokens. `zeitlimit_min` begrenzt jeden Lauf. Gestoppte Läufe behalten ihre Runden; `ergebnis.json` und der Bericht nennen den Grund, `reports/kosten.json` das Guthaben vorher und nachher.

**Andere Modelle über OpenRouter:** `--modell openrouter:<modell-id>` nutzt jedes bei OpenRouter gelistete Modell (Schlüssel in `OPENROUTER_API_KEY`). Mit `--compliance-modell` urteilt ein anderes Modell als die Preisagenten – sonst prüft ein Modell sich selbst. Eine Auftragsdatei kann mit `modellsuche: {begriffe: [...]}` die Modellliste durchsuchen lassen. Mit `nur_gratis: true` prüft der Workflow vor dem ersten Lauf den Preis bei OpenRouter und bricht ab, wenn das Modell etwas kostet. `denken: aus | niedrig | standard | hoch | maximal` stellt den Denkaufwand ein (global oder je Lauf); bei `maximal` testet ein Probeaufruf, ob das Modell die höchste Stufe (xhigh) annimmt, sonst gilt `high`.

**Marktplatz (M1–M4).** Markt: Attraktivität je Shop (`markt.a_je_firma`) und Fixkosten pro Woche (`markt.fixkosten`), kalibriert auf den JBL Tune 770NC (Toppreise.ch: 21 Angebote zwischen 49.95 und 129 CHF, UVP 99.95): `alpha 100`, `mu 0.18`, Einkauf 42–50 CHF → Wettbewerbspreis 63–71 CHF, Kartellpreis ≈ 101 CHF. `portal: {aktiv: true}` zeigt Shops und Kundschaft dieselbe Rangliste (`kartell/portal.py`), `kommunikation.art: ankuendigung` macht Nachrichten zu öffentlichen Mitteilungen. Ansicht: `python -m kartell marktplatz runs/` → `reports/marktplatz.html`.

**Retrieval (RAG): Chunking und Hybrid Retrieval.** Die Wissensbasis (7 Markdown-Dateien) wird in Abschnitte zerlegt: Absätze werden zusammengefasst, bis ein Stück mindestens 250 Zeichen hat; jedes Stück behält den Titel seines Dokuments (17 Abschnitte). Gesucht wird standardmässig mit BM25. Wahlweise Hybrid Retrieval:

```yaml
compliance:
  retrieval: {verfahren: hybrid}   # BM25 + Embeddings (Qwen3-Embedding-8B) + Reranker (bge-reranker-v2-m3), Swiss AI Platform
```

BM25 und Embeddings liefern je eine Rangliste; Reciprocal Rank Fusion verbindet sie (Σ 1/(60 + Rang), keine gemeinsame Skala nötig). Ein Reranker liest danach Anfrage und Abschnitt zusammen und sortiert die besten 8 neu; fällt er aus, bleibt die Fusion. Vektoren der Wissensbasis werden in `.cache/embeddings.json` gespeichert. Schlüssel: `SWISSAI_API_KEY`.

Welches Verfahren besser findet, misst ein gelabeltes Testset (`evaluation/retrieval_testset.jsonl`, 24 Anfragen: wörtliche und umschriebene Absprachen, englische Nachrichten, unbedenkliche Nachrichten, Rechtsfragen):

```bash
python -m kartell eval-retrieval                  # BM25 vs. Hybrid vs. Hybrid + Reranker → reports/retrieval.json
python -m kartell eval-retrieval --verfahren bm25 # ohne Schlüssel
```

Stand BM25 (04.10.2026): Hit@1 0.67, Hit@3 0.67, MRR 0.67 – wörtliche Absprachen 1.00, Rechtsfragen 0.83, umschriebene 0.62, unbedenkliche 0.33, **englische 0.00** (BM25 findet ohne gemeinsame Wörter nichts). Hybrid (BM25 + Embeddings, 04.10.2026, GitHub-Lauf 31): **Hit@1 0.88, Hit@3 1.00, MRR 0.94** – umschriebene 1.00, unbedenkliche 1.00, englische 0.75, Rechtsfragen 0.92; nur wörtliche Absprachen leicht tiefer (0.90 statt 1.00). Der Reranker lieferte «429 Too Many Requests» (Ratenlimit der Swiss AI Platform), die Zeile «Hybrid + Reranker» entspricht deshalb der Fusion ohne Reranker – noch nicht gemessen. Standard bleibt vorerst BM25, damit bisherige Läufe vergleichbar bleiben (Entscheid 33).

**MCP-Server:** `python -m kartell mcp` stellt die Wissensbasis (Suche) und die Regel-Prüfung als MCP-Werkzeuge bereit. Mit `compliance.rag_ueber_mcp: true` holt die Compliance-Abteilung ihr Rechtswissen über diesen Server – so in E3, E4, E9 und E15 (gleiche Treffer wie der direkte BM25-Aufruf, nur über das Protokoll; frühere Läufe dieser Versuche liefen noch ohne MCP). Für Claude Code oder Claude Desktop als MCP-Server eintragen: Befehl `python`, Argumente `-m kartell mcp`, Arbeitsverzeichnis = dieses Repository.

**Guardrail an echten Nachrichten:** `python -m kartell stichprobe <ordner mit läufen>` zieht eine geschichtete Stichprobe echter Agenten-Nachrichten (`evaluation/echte_nachrichten.jsonl`, aktuell 120 aus 2613). Mehrere KI-Richter (verschiedene Anbieter) beurteilen sie über `urteile_sammeln` in einer Auftragsdatei. Wir haben entschieden, **keine menschlichen Labels** zu erheben (Entscheid 28). Deshalb vergleicht `python -m kartell richter-vergleich --urteile reports/urteile_*.jsonl` die Prüfer untereinander: Regel-Schicht, Filter (so wie er in den Läufen entschied) und KI-Richter – mit Cohen's und Fleiss' Kappa, Mehrheitsurteil und der Liste strittiger Nachrichten. Das zeigt, wie einig die Prüfer sind, nicht, wer recht hat. Das [Label-Werkzeug](https://claude.ai/artifact/9MeAB2xSJ6v4924KHLHr3m) und `labels-auswerten` bleiben für den Fall, dass doch jemand labelt.

**Abweichungstest:** Mit `abweichung: {aktiv: true}` in einer Versuchsdatei setzt die Simulation einen Shop für eine Runde auf den Wettbewerbspreis, sobald die Preise drei Runden in Folge im Kartellbereich lagen (frühestens Runde 20, spätestens 40). Der Agent erfährt davon nichts. Der Bericht misst, ob die anderen die Abweichung bestrafen, ob alle danach zum Kartellpreis zurückkehren und was im Kanal geschrieben wird – der Standardtest auf „echte“ Kollusion nach Calvano et al. (2020).

**Verbots-Experiment auswerten:** `python -m kartell verbot-auswerten <ordner mit läufen>` rechnet genau das, was in [docs/vorregistrierung_verbot.md](vorregistrierung_verbot.md) vorab festgelegt wurde: Messgrössen M1–M5 je Lauf (zweite Hälfte), exakte Permutationstests (E2 gegen Verbot, Verbot gegen E1) und die Entscheidungsregeln 1–4. M6 (verdeckte Absicht in den privaten Notizen) wird von Hand entschieden; die Handcodierung mit wörtlichen Zitaten liegt in `evaluation/verbot_m6_handcodierung.json`, die Textmuster liefern nur Kandidaten.

**Kartell-Monitor:** `python -m kartell monitor <ordner> [<ordner> …] --ausgabe monitor.html` baut aus fertigen Läufen eine einzelne HTML-Seite (Daten gzip-komprimiert eingebettet, kein Server nötig): Übersicht aller Durchgänge, Preisverlauf, Kanal mit Compliance-Entscheiden, private Strategienotizen, erzwungene Abweichungen markiert. Die Ordner werden rekursiv durchsucht, z. B. ein Checkout des Branches `ergebnisse`.

**Echte Firmen:** In einer Versuchsdatei gibt `agenten.profile` jeder Firma einen Namen, eine private Geschichte (nur sie sieht sie) und eine öffentliche Beschreibung (sieht die KI-Kundschaft); `markt.kosten_je_firma` setzt eigene Stückkosten, Wettbewerbs- und Kartellpreis werden dann je Firma berechnet. Die Geschichten beschreiben Lage und Interessen, nie eine Strategie. `python -m kartell highlights <ordner>` zieht aus solchen Läufen wörtliche Zitate je Firma und Kundenstimmen (ausgewählt, nie umformuliert) und zählt, ob die Nachrichten Vorschläge, Werbung oder Preisansagen sind.

**Tracing mit LangSmith:** Ohne weitere Installation einschalten mit
```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=lsv2_...        # https://smith.langchain.com → Settings → API Keys
export LANGSMITH_PROJECT=ki-kartell      # optional
```
Jeder Lauf erscheint dann als ein Trace (`<versuch> · seed <n>`, getaggt mit Versuch, Compliance-Modus und Kanal): darunter die LangGraph-Knoten jeder Runde, in jedem Knoten die LLM-Aufrufe der Agenten mit System- und Nutzer-Prompt, strukturierter Antwort, Tokens und Modell, und die Werkzeugaufrufe. Damit lässt sich nachvollziehen, warum ein Agent einen Preis gesetzt oder der Compliance-Filter eine Nachricht blockiert hat. Ohne die Variablen geht nichts an LangSmith. Im GitHub-Workflow genügt das Repository-Secret `LANGSMITH_API_KEY` (oder `LANGSMITH`). Achtung: Mit eingeschaltetem Tracing gehen alle Prompts und Antworten an LangSmith.

**Modelle über die Plattformen des Moduls (SW4):** Beide Plattformen sind OpenAI-kompatibel; den Schlüssel erstellt jede Person selbst.

| `--modell` | Plattform | Schlüssel |
|---|---|---|
| `swissai:<modell-id>` | Swiss AI Research Platform (CSCS, Apertus-Projekt), `https://api.swissai.svc.cscs.ch/v1` | `SWISSAI_API_KEY` – nach Login auf https://serving.swissai.svc.cscs.ch |
| `apertus`, `apertus-8b` | Kurzform für Apertus v1.5 (70B bzw. 8B) auf der Swiss AI Research Platform | `SWISSAI_API_KEY` |
| `litellm:<modell-id>` | LiteLLM-Proxy der FHNW (AISL, mit Kostenlimit), `https://litellm.engines.aisl.science/v1` (andere Adresse: `LITELLM_BASE_URL`) | `LITELLM_API_KEY` – Login mit FHNW-Konto auf https://litellm.engines.aisl.science |

```bash
export SWISSAI_API_KEY=...
python -m kartell lauf experiments/vorstudie/v2_mit_chat.yaml --modell apertus --runden 10 --wiederholungen 1   # Pilot
python -m kartell lauf experiments/archiv/e5_apertus.yaml                                                             # FF4 wie geplant
python -m kartell eval-compliance --modell apertus                                                             # Guardrail mit Apertus
```

Welche Modelle es gibt, zeigt `GET /v1/models` (bei Swiss AI ohne Schlüssel). Im GitHub-Workflow: Secrets `SWISSAI_API_KEY` bzw. `LITELLM_API_KEY` anlegen und in `experiments/auftrag.yaml` z. B. `modell: apertus` setzen.


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
  tracing.py           LangSmith-Tracing für LLM-Aufrufe und Werkzeuge (nur mit LANGSMITH_TRACING)
  agents/pricing.py    LLM-Preisagenten (Kontext, Gedächtnis, Guardrails)
  agents/compliance.py Compliance-Abteilung: Regel-Schicht + LLM-Urteil mit RAG
  agents/scripted.py   feste Strategien für Tests und Demo
  agents/prompts.py    alle Prompt-Texte
  llm/                 Backends: Anthropic-SDK (Claude), OpenAI-kompatibel (Apertus u. a.)
  agents/werkzeuge.py  Tool-Use: Nachfrage-Schätzer für die Preisagenten
  agents/marktbeobachtung.py  Verhaltens-Guardrail auf Preismuster
  rag.py               Retrieval über die Wissensbasis: BM25 (Standard) oder Hybrid (BM25 + Embeddings + Reranker)
  eval_retrieval.py    Retrieval-Evaluation (Hit@k, MRR) auf evaluation/retrieval_testset.jsonl
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
