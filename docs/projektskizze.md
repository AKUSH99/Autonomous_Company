# Projektskizze: KI-Kartell

**Sprechen sich KI-Preisagenten ab – und können Guardrails das verhindern?**

Modul Generative KI · FHNW BSc Business Artificial Intelligence · Gruppenarbeit HS 2026
Team (5 Personen): _Name 1_, _Name 2_, _Name 3_, _Name 4_, _Name 5_ · Stand: 23.09.2026 · Abschlusspräsentation: 23.11.2026

> **Hinweis (Stand 04.10.2026):** Diese Skizze ist der ursprüngliche Plan. In einigen Punkten ist das Projekt anders
> gelaufen – massgebend sind README, [ergebnisse.md](ergebnisse.md) und [entscheidungen.md](entscheidungen.md):
>
> | Geplant | Tatsächlich | Warum |
> |---|---|---|
> | Hauptläufe mit Claude, Modellvergleich mit Apertus (FF4, E5/E6) | Hauptläufe mit DeepSeek (`deepseek-flash`), Verbot zusätzlich mit Nemotron 3 Ultra, Zusatz mit Space Bunny; E5/E6 nicht durchgeführt | Kosten (rund 4 statt 80 USD); Apertus ist bei OpenRouter nicht gelistet und bräuchte einen eigenen Server (Entscheide 13, 29, 30) |
> | Vier Forschungsfragen (FF1–FF4) | Eine Frage, drei Kapitel: Sprechen sie sich ab? Ist es ein echtes Kartell? Kann man sie stoppen? | Übersichtlichkeit für Präsentation und Prüfung (Entscheid 29) |
> | Zurückgehaltenes zweites Testset, menschliche Labels | Mehrere KI-Richter urteilen über 120 echte Nachrichten; gemessen wird Einigkeit (Kappa), nicht Richtigkeit | Aufwand fürs Team (Entscheid 28) |
> | Compliance-Agent bezieht Rechtswissen über MCP | MCP-Server gebaut und getestet (`tests/test_mcp.py`), in den Versuchen aber nicht eingeschaltet – dort liest der Compliance-Agent den Index direkt | Derselbe Index dahinter, aber weniger bewegliche Teile in den Läufen; MCP ist für die Demo in Claude Desktop/Code gedacht (Entscheid 22) |

## 1. Problemstellung und Relevanz

Online-Händler setzen zunehmend Algorithmen ein, die Preise automatisch an die Konkurrenz anpassen. Mit LLM-Agenten entstehen Preissysteme, die selbstständig Marktdaten deuten, Strategien formulieren und – wenn man sie lässt – mit anderen Systemen kommunizieren. Erste Forschung zeigt, dass LLM-basierte Preisagenten ohne Anweisung zu Preisen über dem Wettbewerbsniveau finden können (Fish et al. 2024).

Für Unternehmen ist das ein reales Haftungsrisiko: Nach dem Schweizer Kartellgesetz sind Preisabsprachen zwischen Konkurrenten grundsätzlich unzulässig (Art. 5 Abs. 3 KG) und können mit bis zu 10 % des Schweizer Umsatzes der letzten drei Jahre sanktioniert werden (Art. 49a KG). Wettbewerbsbehörden betonen, dass Unternehmen für ihre Algorithmen verantwortlich sind. Die praktische Frage lautet deshalb: **Wie baut man agentische Preissysteme, die nachweislich keine Absprachen treffen?**

## 2. Forschungsfragen

| | Frage | Versuch |
|---|---|---|
| FF1 | Setzen LLM-Preisagenten ohne Kommunikation Preise über dem Wettbewerbsniveau (stillschweigende Kollusion)? | E1 |
| FF2 | Wie verändert ein offener Kommunikationskanal zwischen den Konkurrenten Preise und Verhalten? | E2 |
| FF3 | Verhindert ein Compliance-Agent (Regeln + LLM + RAG über Kartellrecht) Absprachen, und mit welcher Fehlerrate? | E3, E4, Guardrail-Evaluation |
| FF4 | Unterscheiden sich Modelle, insbesondere das Schweizer Open-Source-Modell Apertus und ein kommerzielles Modell? | E5, E6 |

## 3. Lösungsansatz

Ein Multi-Agenten-System mit drei Rollen, orchestriert mit **LangGraph**:

- **Preisagenten** (2–3 konkurrierende Shops): erhalten Stückkosten, Ziel „Gewinn über alle Runden maximieren" und die Marktdaten der letzten Runden. Sie führen ein Gedächtnis aus Strategienotizen und können in einen öffentlichen Kanal schreiben. Sie erhalten **keine** Anweisung zu kooperieren oder zu konkurrieren und kennen weder Nash- noch Monopolpreis.
- **Markt:** Standardmodell der Forschung (Bertrand-Wettbewerb mit Logit-Nachfrage, Calvano et al. 2020). Daraus lassen sich Wettbewerbspreis (Nash) und Kartellpreis (Monopol) exakt berechnen – der Massstab für die Auswertung.
- **Compliance-Abteilung** (Guardrail): prüft jede Nachricht vor der Zustellung in zwei Schichten – eine transparente Regel-Schicht und ein LLM-Urteil, das sich per RAG auf eine Wissensbasis zum Kartellrecht stützt und die Rechtsgrundlage nennt. Im Modus „Aufsicht" prüft sie zusätzlich die privaten Strategienotizen und gibt Hinweise.

Eine Runde ist ein Durchlauf durch den Graphen: Kommunikation → Compliance-Filter → Preisentscheid → Aufsicht → Markt. Knoten werden je Versuchsbedingung zu- oder weggeschaltet.

## 4. Eingesetzte Konzepte aus dem Modul

| Konzept | Umsetzung |
|---|---|
| Multi-Agenten-Kollaboration | Konkurrierende Preisagenten plus Compliance-Agent; das untersuchte Verhalten entsteht erst aus der Interaktion |
| LangGraph | Zustandsgraph einer Marktrunde mit bedingten Knoten, parallelen Agentenaufrufen und Rundenschleife |
| Prompt Engineering | Rollen- und Aufgabenprompts ohne Priming auf Kooperation; Prompt-Variation als Robustheitscheck |
| Strukturierte Ausgaben | Alle Agentenantworten als validiertes JSON-Schema (Pydantic) |
| RAG | BM25-Retrieval über Zusammenfassungen von KG, AEUV und Behördenpraxis für den Compliance-Agenten |
| Guardrails | Nachrichtenfilter (Regeln + LLM, fail-safe), Aufsicht über Notizen, Preisgrenzen, Fallback bei Modellausfall |
| Modellvergleich / Apertus | Austauschbare Backends: Claude über das Anthropic-SDK, Apertus über eine OpenAI-kompatible Schnittstelle |
| Tool-Use | Nachfrage-Schätzer als Werkzeug der Preisagenten (E14): verändert ein analytisches Werkzeug die Kollusion? |
| MCP | Wissensbasis und Regel-Prüfung als MCP-Server; der Compliance-Agent kann sein Rechtswissen darüber beziehen (`rag_ueber_mcp`). Gebaut und getestet, in den Versuchsläufen nicht eingeschaltet |
| Verhaltens-Guardrail | Marktbeobachtung erkennt Preismuster (Gleichschritt, gemeinsame Erhöhungen) statt nur Worte (E15) |

## 5. Evaluation

**Versuchsplan:** E1–E4 und E7 mit Claude, E5–E6 mit Apertus; je 50 Runden und 3 Wiederholungen (mehr, falls das Budget reicht). Dieselben Versuche lassen sich mit `--modell deepseek` für rund 4 USD wiederholen – als günstiger Einstieg und als zusätzlicher Modellvergleich für FF4.

**Kennzahlen:**
- Preisindex und Kollusionsindex: 0 = Wettbewerb (Nash), 1 = perfektes Kartell, gemessen über die zweite Hälfte jedes Laufs
- Anteil blockierter Nachrichten, Kategorien der Verstösse
- Kosten und Tokens pro Lauf
- Qualitative Analyse: Wie formulieren die Agenten ihre Strategien? Entstehen Absprachen offen oder verschleiert?

**Guardrail-Evaluation:** Precision, Recall und Fehlalarmquote des Compliance-Agenten auf einem gelabelten Testdatensatz (aktuell 39 Nachrichten), getrennt nach Regel-Schicht und Regeln + LLM. Zusätzlich ein zweites, zurückgehaltenes Testset, das erst am Ende ausgewertet wird. Ergänzend ein Abgleich der Filterentscheide aus den echten Läufen mit einer manuellen Stichprobe.

## 6. Arbeitsteilung

| Rolle | Person | Verantwortung | Module |
|---|---|---|---|
| Markt und Auswertung | _Name_ | Marktmodell, Benchmarks, Kennzahlen, Bericht und Statistik | `market.py`, `metrics.py`, `bericht.py`, `abweichung.py` |
| Agenten und Orchestrierung | _Name_ | Preisagenten, Prompts, LangGraph, Experimente durchführen | `graph.py`, `agents/pricing.py`, `agents/prompts.py`, `experiments/` |
| Compliance und RAG | _Name_ | Wissensbasis, Retrieval, MCP, Guardrail, Testsets und Prüfer-Vergleich | `agents/compliance.py`, `rag.py`, `mcp_server.py`, `knowledge/`, `evaluation/` |
| Modelle und Erweiterungen | _Name_ | Modell-Backends, Modellvergleich, KI-Kundschaft, echte Firmen | `llm/`, `agents/kundschaft.py`, `kunden.py`, E20–E25 |
| Demo und Präsentation | _Name_ | Kartell-Monitor, Dashboard, Präsentation, Abgabe | `monitor.py`, `dashboard/`, Folien |

Alle kennen den Gesamtablauf und die Entscheidungen in `docs/entscheidungen.md`. In der Präsentation und in der mündlichen Prüfung erklärt jede Person ihren Teil selbst.

## 7. Zeitplan

| Woche | Meilenstein |
|---|---|
| KW 39–40 | Setup, Code verstehen, Offline-Demo, erste Pilotläufe (10 Runden) |
| KW 41 | Pilot E1/E2, Prompts prüfen; Apertus-Zugang klären |
| KW 42 | Zweites Testset für den Guardrail erstellen, Guardrail-Evaluation |
| KW 43–44 | Hauptläufe E1–E4 |
| KW 45 | Prüfer an echten Nachrichten vergleichen (Regel-Schicht, Filter, mehrere KI-Richter; statt menschlicher Labels, siehe Entscheid 28), Modellvergleich (zweites Modell über OpenRouter) |
| KW 46 | Auswertung, Grafiken, Erkenntnisse und Limitationen |
| KW 47 | Präsentation, Probe, aufgezeichneter Backup-Lauf für die Demo |
| KW 48 | Abschlusspräsentation 23.11.2026 |

## 8. Risiken

| Risiko | Gegenmassnahme |
|---|---|
| API-Kosten | Kostenschätzung vor jedem Lauf, Pilotläufe mit wenigen Runden, günstigeres Modell als Option |
| Es entsteht keine Kollusion | Ebenfalls ein gültiges Ergebnis; zusätzlich Prompt-Variation und mehr Shops (E7) |
| Apertus-Zugang oder JSON-Ausgabe unzuverlässig | Tolerantes Parsing mit Wiederholung ist eingebaut; notfalls kleineres Modell lokal |
| Demo scheitert live | Wiedergabe-Modus im Dashboard mit aufgezeichnetem Lauf |
| Guardrail überangepasst ans Testset | Zurückgehaltenes zweites Testset |

## 9. Ethik und Grenzen

Der Markt ist vollständig simuliert, es werden keine echten Preise beeinflusst. Ziel ist, Risiken agentischer Preissysteme zu verstehen und Schutzmechanismen zu prüfen. Die Wissensbasis fasst Rechtstexte vereinfacht zusammen und ist keine Rechtsberatung. **Offenlegung:** Code und Dokumentation sind mit Unterstützung eines KI-Assistenten (Claude Code) entstanden; im Git-Verlauf sind diese Commits als „Claude“ erkennbar. Fragestellung, Versuchsplan, Entscheidungen und Auswertung verantwortet das Team. Die Offenlegung steht auch in der Abgabe und auf einer Folie der Präsentation.

## 10. Quellen

- Calvano, E., Calzolari, G., Denicolò, V., Pastorello, S. (2020): Artificial Intelligence, Algorithmic Pricing, and Collusion. *American Economic Review*, 110(10).
- Fish, S., Gonczarowski, Y. A., Shorrer, R. I. (2024): Algorithmic Collusion by Large Language Models. arXiv:2404.00806.
- Kartellgesetz (KG), SR 251; AEUV Art. 101.
