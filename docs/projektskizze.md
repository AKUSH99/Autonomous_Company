# Projektskizze: KI-Kartell

**Bilden KI-Preisagenten in einem realistischen Online-Markt von selbst ein Kartell – und kann man es verhindern?**

Modul Generative KI & Agentensysteme · FHNW BSc Business Artificial Intelligence · Gruppenarbeit HS 2026
Stand: 05.10.2026 · Abschlusspräsentation: 23.11.2026, 13:00 Uhr (10 Min. inkl. Verständnisfragen)

## Team

> **Vom Team auszufüllen.** Laut Moodle-Aufgabe «Abgabe» müssen die Namen aller Beteiligten angegeben werden; Teams aus
> 3 Studierenden, höchstens 4 (SW4, Folie 4). Wer welche Rolle verantwortet, steht in Abschnitt 10 und in
> [beitraege.md](beitraege.md).

| Name | Rolle (Abschnitt 10) |
|---|---|
| _Name eintragen_ | _Rolle_ |
| _Name eintragen_ | _Rolle_ |
| _Name eintragen_ | _Rolle_ |
| _(optional) Name eintragen_ | _Rolle_ |

## 1. Problemstellung und Relevanz

Online-Händler setzen zunehmend Algorithmen ein, die Preise automatisch an die Konkurrenz anpassen. Mit LLM-Agenten
entstehen Preissysteme, die selbstständig Marktdaten deuten, Strategien formulieren und – wenn man sie lässt – mit
anderen Systemen kommunizieren. Erste Forschung zeigt, dass LLM-basierte Preisagenten ohne Anweisung zu Preisen über
dem Wettbewerbsniveau finden können (Fish et al. 2024).

Für Unternehmen ist das ein reales Haftungsrisiko: Nach dem Schweizer Kartellgesetz sind Preisabsprachen zwischen
Konkurrenten grundsätzlich unzulässig (Art. 5 Abs. 3 KG) und können mit bis zu 10 % des Schweizer Umsatzes der
letzten drei Jahre sanktioniert werden (Art. 49a KG). Wettbewerbsbehörden betonen, dass Unternehmen für ihre
Algorithmen verantwortlich sind. Die praktische Frage lautet deshalb: **Wie erkennt und verhindert man, dass
agentische Preissysteme Absprachen treffen?**

## 2. Use Case und Nutzerbedürfnisse

Das System ist ein **Prüfstand für KI-Preisagenten**: Es simuliert einen Online-Markt, in dem KI-Agenten Preise
setzen, und zeigt, ob sie kartellieren und ob ein Compliance-Agent das verhindert. Wer es nutzt:

| Nutzerrolle | Bedürfnis |
|---|---|
| **Compliance-Verantwortliche** eines Online-Händlers, der KI-Preisagenten einführen will | wissen, ob der Agent Absprachen trifft, bevor er live geht |
| **Pricing-Verantwortliche** | sehen, wie sich ein KI-Agent im Wettbewerb verhält (Preiskrieg, Signale, Reaktion auf Schocks) |
| **Wettbewerbsbehörde** (z. B. WEKO) | verstehen, woran man algorithmische Kollusion erkennt – auch ohne offenen Chat |

**User Stories** (Form nach SW4, Folie 14):

- Als **Compliance-Verantwortliche** eines Online-Händlers möchte ich unseren KI-Preisagenten vor dem Einsatz in einem
  realistischen Markt testen, damit ich sehe, ob er sich mit der Konkurrenz abspricht.
- Als **Compliance-Verantwortliche** möchte ich, dass jede öffentliche Mitteilung des Agenten vor der Veröffentlichung
  auf Preissignale geprüft wird und die Begründung samt Rechtsgrundlage sehe, damit wir kein Bussgeld riskieren.
- Als **Pricing-Verantwortlicher** möchte ich sehen, wie der Agent auf Zölle, Rezession oder Black Friday reagiert,
  damit ich verstehe, ob er Schocks für Preiserhöhungen ausnutzt.
- Als **Analystin einer Wettbewerbsbehörde** möchte ich Preisverläufe und Mitteilungen nebeneinander sehen, damit ich
  stillschweigende Signale («keine Rabattschlacht») von normaler Werbung unterscheiden kann.
- Als **Projektteam** möchten wir jede Einstellung reproduzierbar rechnen und vergleichen, damit unsere Aussagen
  belegbar sind.

**Vergleich mit heute:** Händler setzen meist regelbasierte Repricer ein («1 CHF unter dem Günstigsten»), die nicht
kommunizieren. Compliance-Prüfungen von Preisalgorithmen sind nachträglich und manuell. LLM-Agenten können erstmals
selbst Strategien formulieren und Texte schreiben – das schafft ein neues Risiko, für das es noch kein Prüfverfahren
gibt.

## 3. Forschungsfrage und Versuche

Hauptgeschichte im **Marktplatz** (sechs Firmen, Vergleichsportal, KI-Kundschaft, Preisniveau des JBL Tune 770NC nach
Toppreise.ch):

| Versuch | Was die Shops dürfen | Frage |
|---|---|---|
| **M1** Nur Portal | nur Preise setzen | Steigen die Preise von selbst? |
| **M2** Mitteilungen | öffentliche Mitteilungen im Portal | Nutzen die Shops sie als Preissignal? |
| **M3** Geheimer Chat | Chat nur unter den Shops | Entstehen mit geheimem Kanal Kartellpreise? |
| **M4** Compliance | wie M2, Mitteilungen werden geprüft, Marktbeobachtung | Lässt sich das verhindern? |

Dazu die **Vorstudie** mit zwei Shops (V1–V4: ohne/mit Chat, Abweichungstest, Verbot) und das **Szenario-Labor**
(eigene Regeln und Ereignisse wie Zoll, Black Friday, Rezession) mit einem vorgerechneten Raster aller Kombinationen.

## 4. Lösungsansatz

Ein Multi-Agenten-System, orchestriert mit **LangGraph**. Eine Woche ist ein Durchlauf durch den Graphen:
Mitteilungen bzw. Chat → Compliance-Filter → Preisentscheid (6 Agenten parallel) → Markt (Portal, KI-Kundschaft,
Gewinne). Jeder Preisagent kennt seine Kosten, sein Firmenprofil, das Portal und seine eigenen Notizen (Memory), aber
keine Anweisung zu kooperieren und keine Referenzpreise. Der Compliance-Agent prüft Mitteilungen mit Regeln, RAG über
eine Kartellrecht-Wissensbasis (über MCP, Hybrid-Suche) und einem LLM-Urteil. Wettbewerbs- und Kartellpreis werden
aus dem Marktmodell exakt berechnet – der Massstab für die Auswertung.

## 5. Erfolgskriterien und Zielwerte

| Kriterium | Zielwert | Stand 05.10.2026 |
|---|---|---|
| Läufe technisch sauber | < 1 % ausgefallene Entscheide je Lauf | M1, M2: 0 %; M4: 0 %, 0 % und 6 % (ein Lauf während einer Überlastung der Plattform) |
| Aussagekraft | je Versuch ≥ 3 Läufe à ≥ 15 Wochen, Unterschiede mit t-Test berichtet | M1, M2, M4: 3 × 30 Wochen; M3 läuft |
| Kartell erkennbar machen | Preisindex (0 = Wettbewerb, 1 = Kartell) je Woche; Kartell = Index ≥ 0.5 in der zweiten Hälfte | umgesetzt (Marktplatz-Ansicht, Bericht) |
| Guardrail findet Absprachen | Precision ≥ 0.95 und Recall ≥ 0.80 auf dem gelabelten Testset | Regeln + LLM: Precision 1.00, Recall 1.00 (39 Nachrichten); in Läufen Recall 0.78 |
| Retrieval findet die Rechtsgrundlage | MRR ≥ 0.85 auf dem Retrieval-Testset | Hybrid 0.94 (BM25 allein 0.67) |
| Nachvollziehbarkeit | jede Woche mit Preisen, Mitteilungen, Notizen und Kaufgründen einsehbar | Marktplatz-Ansicht |
| Verständnis im Team | jede Person kann Problem, Architektur, Evaluation und Grenzen erklären | Lernpfad `docs/lernpfad.md` |

**Erfolg** heisst damit: Wir können für jede Bedingung belegt sagen, ob die Preise Richtung Kartell gehen, warum
(Mitteilungen, Notizen), und ob der Compliance-Agent die Signale erkennt.

## 6. Scope (MVP) und Limitierungen

**Im Scope:** ein Produkt, sechs Firmen (Szenario-Labor: 2–10), wöchentliche Preisentscheide, KI-Kundschaft,
öffentliche Mitteilungen oder geheimer Chat, Compliance-Agent, Ereignisse; Auswertung über Preisindex, Gewinne,
Mitteilungen.

**Nicht im Scope:** echte Shops oder echte Preise, Lager und Logistik, mehrere Produkte, menschliche Kundschaft,
juristisch verbindliche Prüfung.

**Limitierungen:** simulierte Kundschaft (ein Sprachmodell spielt 40 Personen), ein Hauptmodell (DeepSeek V4.1 Flash;
Vergleich mit GLM-5.3 und mit Reasoning geplant), wenige Läufe pro Bedingung, Ratenlimit der Swiss AI Platform (rund
15 Anfragen pro Minute), vereinfachte Rechtstexte.

## 7. Eingesetzte Konzepte aus dem Modul

| Modulthema | Umsetzung |
|---|---|
| Agenten & Multi-Agent | 6 Preisagenten, KI-Kundschaft, Compliance-Agent |
| Orchestrierung | LangGraph-Zustandsgraph, bedingte Knoten je Versuch, Agenten parallel |
| System-Prompts & strukturierte Ausgaben | Rollen ohne Hinweis auf Kooperation, validiertes JSON (Pydantic) |
| Memory | Plan und Erkenntnisse je Shop, in der Folgewoche im Prompt |
| RAG | Wissensbasis Kartellrecht, Chunking, Hybrid-Suche (BM25 + Embeddings), Retrieval-Evaluation |
| MCP | Wissensbasis und Regel-Prüfung als MCP-Server |
| Guardrails | Compliance-Filter, Marktbeobachtung auf Preismuster, Preisgrenzen |
| Evaluation | Guardrail Precision/Recall, Retrieval Hit@k/MRR, Versuche mit Wiederholungen und Statistik |
| Tracing | LangSmith (jeder GitHub-Lauf im Projekt `ki-kartell`) |
| Modellwahl | Swiss AI Research Platform (DeepSeek, GLM, Apertus), FHNW-LiteLLM; Entscheide in `docs/entscheidungen.md` |
| Interface | Marktplatz-Ansicht, Szenario-Labor mit Reglern, Streamlit-Dashboard |

## 8. Evaluation

Kennzahlen je Lauf: Preisindex und Gewinnindex (0 = Wettbewerb, 1 = Kartell, zweite Hälfte), Gewinne je Shop, Anteil
Kundschaft ohne Kauf, Anzahl und Inhalt der Mitteilungen bzw. Chat-Nachrichten, blockierte Mitteilungen mit
Begründung. Guardrail- und Retrieval-Evaluation auf gelabelten Testsets (`evaluation/`). Alle Läufe liegen öffentlich
im Branch [`ergebnisse`](https://github.com/AKUSH99/Autonomous_Company/tree/ergebnisse).

## 9. Zeitplan

| Woche | Meilenstein laut Semesterprogramm | Stand |
|---|---|---|
| KW 41 (05.10.) | Gruppenbildung, Use Case, Evaluationskriterien | Use Case und Kriterien: diese Skizze; **Team eintragen** |
| KW 42 (12.10.) | erste lauffähige Version, Tracing | erledigt (Läufe M1–M4, LangSmith) |
| KW 43 (19.10.) | MCP-Server anbinden | erledigt |
| KW 44 (26.10.) | RAG, Chunking, Hybrid Retrieval | erledigt |
| KW 46 (09.11.) | Memory festlegen | erledigt (Notizen je Shop) |
| KW 47 (16.11.) | Safeguarding, Evaluation | erledigt; Ergebnisse M3 und Raster nachtragen |
| KW 48 (23.11.) | Abschlusspräsentation | Entwurf: `docs/praesentation_entwurf.md` |

## 10. Arbeitsteilung

| Rolle | Verantwortung | Module | Person |
|---|---|---|---|
| Markt und Auswertung | Marktmodell, Kalibrierung, Kennzahlen, Statistik | `market.py`, `metrics.py`, `bericht.py` | _Name_ |
| Agenten und Orchestrierung | Preisagenten, Prompts, LangGraph, Versuche | `graph.py`, `agents/pricing.py`, `agents/prompts.py` | _Name_ |
| Compliance und RAG | Wissensbasis, Retrieval, MCP, Guardrail, Testsets | `agents/compliance.py`, `rag.py`, `mcp_server.py`, `evaluation/` | _Name_ |
| Demo und Präsentation | Marktplatz-Ansicht, Szenario-Labor, Präsentation | `marktplatz_ansicht.py`, `szenario.py`, `docs/` | _Name_ |

Alle kennen den Gesamtablauf und die Entscheidungen in `docs/entscheidungen.md`. Was jede Person konkret beigetragen
hat, steht in [beitraege.md](beitraege.md).

## 11. Risiken

| Risiko | Gegenmassnahme |
|---|---|
| Ratenlimit der Plattform | Taktbremse (14/18 Anfragen pro Minute), Läufe nacheinander, vorgerechnetes Raster |
| Modell antwortet nicht im Format | tolerantes Parsing, Wiederholung, Ausfälle werden markiert und gezählt |
| Demo scheitert live | Marktplatz-Ansicht mit fertigen Läufen, keine Live-Rechnung nötig |
| Guardrail überangepasst ans Testset | zurückgehaltenes zweites Testset, Abgleich mit echten Nachrichten |
| Zu wenige Läufe für klare Aussagen | ≥ 3 Wiederholungen je Hauptversuch, Unsicherheit in jeder Aussage nennen |

## 12. Ethik und Grenzen

Der Markt ist vollständig simuliert, es werden keine echten Preise beeinflusst. Die Firmen sind erfunden. Ziel ist,
Risiken agentischer Preissysteme zu verstehen und Schutzmechanismen zu prüfen. Die Wissensbasis fasst Rechtstexte
vereinfacht zusammen und ist keine Rechtsberatung. Code und Dokumentation sind mit Unterstützung eines KI-Assistenten
(Claude Code) entstanden; das wird in Abgabe und Präsentation offengelegt.

## 13. Quellen

- Calvano, E., Calzolari, G., Denicolò, V., Pastorello, S. (2020): Artificial Intelligence, Algorithmic Pricing, and Collusion. *American Economic Review*, 110(10).
- Fish, S., Gonczarowski, Y. A., Shorrer, R. I. (2024): Algorithmic Collusion by Large Language Models. arXiv:2404.00806.
- Kartellgesetz (KG), SR 251; AEUV Art. 101.
- Toppreise.ch: Preisvergleich JBL Tune 770NC, abgerufen am 04.10.2026.
- Schwander, S. (2026): SW4 Agentensystem – Bausteine, Vorgehen, Modellauswahl. FHNW.
