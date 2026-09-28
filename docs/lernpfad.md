# Lernpfad fürs Team

Die mündliche Prüfung bezieht sich zur Hälfte auf die Gruppenarbeit. Jede Person muss den Gesamtablauf erklären können und ihr eigenes Modul im Detail. Dieser Lernpfad führt in etwa vier Stunden durch das Projekt – am besten gemeinsam am Bildschirm, eine Person teilt, die anderen fragen.

**Offenlegung:** Der Code und diese Dokumentation sind mit Unterstützung eines KI-Assistenten (Claude Code) entstanden. Das gehört in die Abgabe und in die Präsentation. Entscheidend für die Prüfung ist, dass ihr jede Entscheidung selbst begründen könnt – dafür ist `docs/entscheidungen.md` da.

## Schritt 1 – Das System laufen sehen (30 Min.)

```bash
pip install -e ".[dashboard,analyse,dev]"
python -m kartell demo          # zwei feste Skript-Agenten: einmal ohne, einmal mit Filter
pytest                          # alle Tests, ohne API-Schlüssel
streamlit run dashboard/app.py  # Läufe anschauen
python -m kartell monitor runs  # dieselben Läufe als HTML-Seite (reports/monitor.html)
```

Dann den [Kartell-Monitor](https://claude.ai/artifact/DwakevS33U9rD7ABgZp91P) öffnen und E2, Durchgang 3 abspielen: Wie entsteht die Absprache im Kanal? Danach E16, Durchgang 8, Runden 19–23: Wie reagiert Shop B auf die erzwungene Abweichung, und was schreibt Shop A, der gar nicht abgewichen ist?

**Verstanden, wenn ihr erklären könnt:** Was passiert in einer Runde, in welcher Reihenfolge, und warum sind die Skript-Agenten nur ein Funktionstest?

## Schritt 2 – Markt und Messgrössen (45 Min.)

Lesen: `kartell/market.py`, `kartell/metrics.py`, `tests/test_market.py`.

- Logit-Nachfrage: Wer billiger ist, verkauft mehr, aber nicht alles – Kunden haben Vorlieben (Differenzierung μ) und können ganz verzichten (Aussenoption).
- Nash-Preis: Kein Shop kann sich allein durch eine Preisänderung verbessern. Monopolpreis: der Preis, den ein perfektes Kartell setzen würde.
- Kollusionsindex Δ = (Gewinn − Nash-Gewinn) / (Monopol-Gewinn − Nash-Gewinn). 0 = Wettbewerb, 1 = Kartell.

**Verstanden, wenn ihr erklären könnt:** Warum ist der Nash-Preis höher als die Stückkosten? Warum messen wir nur die zweite Hälfte eines Laufs?

## Schritt 3 – Agenten und Orchestrierung (60 Min.)

Lesen: `kartell/graph.py`, `kartell/agents/pricing.py`, `kartell/agents/prompts.py`.

- LangGraph-Zustandsgraph: kommunikation → compliance_filter → preisentscheid → aufsicht → markt, Knoten je Versuch an- oder abgeschaltet.
- Die Agenten bekommen keine Anweisung zu kooperieren und kennen weder Nash- noch Monopolpreis (Validität!).
- Gedächtnis: Strategienotizen (Plan, Erkenntnisse) plus die letzten 10 Runden.
- Guardrails im Agenten: Preisgrenze, Vorrundenpreis bei Modellausfall, Abbruch nach drei Ausfallrunden.
- Tool-Use (`agents/werkzeuge.py`): Nachfrage-Schätzer, der nur mit sichtbaren Daten rechnet.

**Verstanden, wenn ihr erklären könnt:** Woher kommen die Absprachen, wenn im Prompt nichts von Kooperation steht? Was wäre, wenn wir den Agenten den Nash-Preis verraten würden?

## Schritt 4 – Compliance, RAG, MCP (60 Min.)

Lesen: `kartell/agents/compliance.py`, `kartell/rag.py`, `kartell/mcp_server.py`, `kartell/agents/marktbeobachtung.py`, `knowledge/wettbewerbsrecht/`.

- Zwei Schichten: transparente Regeln (schnell, kostenlos) und LLM-Urteil mit BM25-Retrieval über die Wissensbasis; fällt das LLM aus, entscheiden die Regeln.
- MCP: dieselbe Wissensbasis als Server; der Compliance-Agent kann sie über das Protokoll abfragen (`rag_ueber_mcp`).
- Marktbeobachtung: achtet auf Preismuster statt Worte und bestraft nichts – Parallelverhalten ist zulässig.

**Verstanden, wenn ihr erklären könnt:** Warum BM25 statt Embeddings? Warum ist ein Filter auf Worte allein nicht genug (Beobachtung aus E3/E4)?

## Schritt 5 – Auswertung und ehrliche Grenzen (45 Min.)

Lesen: `kartell/bericht.py`, `kartell/stichprobe.py`, `docs/ergebnisse.md`.

- Permutationstest: bei 3 gegen 3 Läufen ist p = 0.10 das Minimum – darum die Wiederholungen w4–w6.
- Ankereffekt: „2 × Kosten“ liegt im Grundmodell fast beim Kartellpreis; E10–E13 trennen das.
- Guardrail an echten Nachrichten: zwei Personen labeln blind, Kappa misst, wie einig ihr euch seid.
- Abweichungstest (`kartell/abweichung.py`, E16/E17): Hohe Preise allein beweisen kein Kartell. Erst wenn ein Abweichler bestraft wird und danach alle zum hohen Preis zurückkehren, hält sich das Kartell durch Belohnung und Drohung – so prüfen Calvano et al. (2020) ihre Q-Learning-Agenten.

**Verstanden, wenn ihr erklären könnt:** Warum ist „Strafe, dann Rückkehr“ ein stärkerer Beleg als ein hoher Kollusionsindex? Warum erfährt der abweichende Agent nichts von der Abweichung?

## Wer übernimmt was

| Rolle | Module | Kernfragen für die Prüfung |
|---|---|---|
| Markt und Auswertung | `market.py`, `metrics.py`, `bericht.py`, `stichprobe.py`, `abweichung.py` | Nash vs. Monopol, Kollusionsindex, Permutationstest, Kappa, Abweichungstest |
| Agenten und Orchestrierung | `graph.py`, `agents/pricing.py`, `agents/prompts.py`, `agents/werkzeuge.py` | LangGraph-Ablauf, Prompt-Validität, Tool-Use, Guardrails im Agenten |
| Compliance, RAG, MCP | `agents/compliance.py`, `rag.py`, `mcp_server.py`, `agents/marktbeobachtung.py`, `knowledge/` | Zwei Schichten, Fail-safe, BM25, MCP, Verhaltens-Guardrail |
| Modelle, Betrieb, Demo | `llm/`, `kosten.py`, `runner.py`, `monitor.py`, `.github/workflows/`, `dashboard/` | Backends, Kosten und Budgetwächter, GitHub Actions, Tests, Monitor und Demo |

## Typische Prüfungsfragen

1. Was genau misst der Kollusionsindex, und warum ist ein Wert unter 0 möglich?
2. Wie stellt ihr sicher, dass die Absprachen nicht durch den Prompt entstehen?
3. Warum reichen drei Durchgänge pro Versuch nicht für eine statistische Aussage?
4. Welche Rolle spielt der Ankereffekt, und wie habt ihr ihn geprüft?
5. Der Filter blockiert viele Nachrichten – woher wisst ihr, dass er nicht zu streng ist?
6. Warum reicht es nicht, Nachrichten zu filtern? Was habt ihr dagegen gebaut?
7. Wofür nutzt ihr MCP, und was wäre die Alternative gewesen?
8. Warum habt ihr DeepSeek statt Claude verwendet, und was bedeutet das für den Datenschutz?
9. Was passiert, wenn das Modell ausfällt oder das Guthaben zu Ende geht?
10. Wie unterscheidet ihr ein echtes Kartell von zufällig hohen Preisen? (Abweichungstest)
11. Was würdet ihr mit mehr Zeit und Budget als Nächstes untersuchen?
