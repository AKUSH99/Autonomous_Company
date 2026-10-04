# KI-Kartell

[![Tests](https://github.com/AKUSH99/Autonomous_Company/actions/workflows/tests.yml/badge.svg)](https://github.com/AKUSH99/Autonomous_Company/actions/workflows/tests.yml)

**Bilden KI-Preisagenten in einem realistischen Online-Markt von selbst ein Kartell – und kann man es verhindern?**

Sechs Online-Shops verkaufen denselben Kopfhörer. Jeder Shop wird von einem KI-Agenten geführt, der jede Woche seinen
Preis setzt. Die Kundschaft vergleicht die Angebote auf einem Preisvergleichsportal und kauft dort, wo es für sie am
besten passt. Niemand sagt den Shops, dass sie zusammenarbeiten sollen. Wir schauen zu, ob die Preise trotzdem Richtung
Kartellpreis steigen – und ob ein Compliance-Agent das stoppen kann.

Gruppenarbeit im Modul Generative KI & Agentensysteme, FHNW BSc Business Artificial Intelligence · Präsentation 23.11.2026

## Der Marktplatz

So nah an einem echten Markt wie möglich:

| | Im Projekt | In der Wirklichkeit (Toppreise.ch, 04.10.2026) |
|---|---|---|
| Produkt | JBL Tune 770NC (Over-Ear, Noise-Cancelling) | 21 Angebote zwischen 49.95 und 129 CHF |
| Preis bei echtem Wettbewerb | 63–71 CHF je Shop | günstige Angebote um 60–70 CHF |
| Preis bei einem perfekten Kartell | rund 101 CHF | unverbindlicher Verkaufspreis 99.95 CHF |
| Shops | 6 Firmen mit eigener Geschichte, eigenen Einkaufspreisen (42–50 CHF), Bewertung und Lieferzeit, 400 CHF Fixkosten pro Woche | Discounter, Fachgeschäft, Premium-Händler, Kette … |
| Kundschaft | 40 KI-Kundinnen und -Kunden mit Budget und Gewohnheiten («vergleicht Preise», «will Beratung», «kauft Schweizer») | |
| Wie man sich sieht | Vergleichsportal: Rangliste nach Preis mit Sternen, Lieferzeit und öffentlicher Mitteilung jedes Shops | Preisvergleichsportale |

![Preisniveau im Modell und auf Toppreise.ch: Wettbewerbspreis 63–71 CHF, Kartellpreis rund 101 CHF, echte Angebote 49.95–129 CHF, UVP 99.95 CHF](docs/bilder/preisniveau.png)

Drei Versuche, die aufeinander aufbauen:

| Versuch | Was die Shops dürfen | Frage |
|---|---|---|
| **E26** Nur Portal | nur Preise setzen | Steigen die Preise von selbst? |
| **E27** Mitteilungen | zusätzlich öffentliche Mitteilungen auf der eigenen Angebotsseite – Kundschaft *und* Konkurrenz lesen mit | Nutzen die Shops die Mitteilungen als Preissignal? |
| **E28** Compliance | wie E27, aber ein Compliance-Agent prüft jede Mitteilung vor der Veröffentlichung, und eine Marktbeobachtung achtet auf Preismuster | Lässt sich ein Kartell verhindern? |

**Stand 04.10.2026:** Die Hauptläufe (je 30 Wochen, 3 Wiederholungen, DeepSeek V4.1 Flash über die Swiss AI Research
Platform) laufen. Die Ergebnisse folgen hier. Im ersten Pilot (je 1 Lauf, noch mit technischen Abbrüchen, darum nicht
belastbar) sanken die Preise ohne Mitteilungen, mit Mitteilungen stiegen sie. Mehrere Shops warben dabei mit Sätzen wie
„Wir spielen die Rabattschlacht nicht mit“ – genau die Art Signal gegen Preiswettbewerb, die das Kartellrecht verbietet.

Jeden Lauf Woche für Woche ansehen – Rangliste, Mitteilungen, private Notizen der Shops, Preiskurve, Kaufentscheide:

```bash
python -m kartell marktplatz runs/          # schreibt reports/marktplatz.html
```

![Marktplatz-Ansicht: Rangliste der sechs Shops mit Preis, Bewertung, Lieferzeit und öffentlicher Mitteilung, daneben die Preiskurve zwischen Wettbewerbs- und Kartellpreis](docs/bilder/marktplatz.png)

*Pilot-Lauf E27, Woche 6 (nicht belastbar). Mehrere Shops werben mit „stabilem Preis ohne Lockangebote“ – ein Signal an die Konkurrenz, verpackt als Werbung.*

## Vorstudie im Labor: zwei Shops

Bevor wir den Marktplatz gebaut haben, haben wir im einfachsten Markt (zwei Shops, ein geschlossener Chat) geprüft, ob
KI-Preisagenten überhaupt kartellieren. Die drei wichtigsten Befunde:

1. **Sie sprechen sich ab.** Dürfen die Shops miteinander schreiben, landen 4 von 6 Läufen im Kartell (ohne Chat 2 von 6).
   Die Absprache schlagen sie selbst vor: „Ich stimme deinem Vorschlag eines stabilen Niveaus um 18.50 CHF zu.“
2. **Es ist ein echtes Kartell.** Setzen wir einen Shop heimlich für eine Runde auf einen tiefen Preis, bestraft ihn der
   andere sofort (6 von 6) und bietet danach Versöhnung an – das Verhaltensmuster, an dem die Forschung echte Kollusion erkennt.

   ![Abweichungstest: Nach dem Bruch senkt der andere Shop sofort den Preis, danach kehren beide zum Kartellpreis zurück](docs/bilder/abweichungstest.png)

3. **Ein Verbot macht sie stumm, aber nicht ehrlich.** Mit Verbot im Auftrag schweigen sie im Chat (p = 0.0003), in den
   privaten Notizen planen sie weiter: „Stillschweigende Signale über eigene Preise wirken, aber ich muss öffentliche
   Kommunikation weiterhin vermeiden, da die WEKO mitliest.“

Zahlen, Tests und Grenzen: [docs/ergebnisse.md](docs/ergebnisse.md) · alle weiteren Versuche: [docs/anhang.md](docs/anhang.md)

## So funktioniert es

Eine Woche ist ein Durchlauf durch einen LangGraph-Graphen:

```mermaid
flowchart LR
    subgraph Woche["Eine Woche (LangGraph)"]
        K["kommunikation<br/>öffentliche Mitteilungen"] --> F["compliance_filter<br/>Regeln + RAG + LLM"]
        F --> P["preisentscheid<br/>6 Agenten parallel"]
        P --> M["markt<br/>Portal, KI-Kundschaft, Gewinne"]
    end
    M -->|nächste Woche| K
    W[("Wissensbasis<br/>Kartellrecht")] -.->|MCP · Hybrid-Suche| F
    M --> L[("runden.jsonl")] --> D["Marktplatz-Ansicht / Bericht"]
```

Je nach Versuch werden Knoten zu- oder weggeschaltet (E26 ohne Mitteilungen und Filter, E28 mit Filter und Marktbeobachtung).

| Modulthema | Im Projekt |
|---|---|
| Agenten & Multi-Agent | 6 Preisagenten, KI-Kundschaft, Compliance-Agent – das untersuchte Verhalten entsteht erst aus ihrem Zusammenspiel |
| Orchestrierung | LangGraph: ein Knoten pro Phase, bedingte Kanten je Versuch, Agenten laufen parallel |
| System-Prompts & strukturierte Ausgaben | Rollen ohne Hinweis auf Kooperation; jede Antwort als validiertes JSON (Pydantic) |
| Memory | Jeder Shop führt einen Plan und Erkenntnisse, die er nächste Woche wieder sieht |
| RAG | Wissensbasis zum Kartellrecht (KG, AEUV, Behördenpraxis), Hybrid-Suche aus BM25 und Embeddings (MRR 0.94 statt 0.67 mit BM25 allein) |
| MCP | Wissensbasis und Regel-Prüfung als MCP-Server, über den der Compliance-Agent nachschlägt |
| Guardrails | Compliance-Filter für Mitteilungen, Marktbeobachtung auf Preismuster, Preisgrenzen |
| Evaluation | Guardrail: Precision/Recall auf gelabelten Nachrichten; Retrieval: Hit@k und MRR; Versuche mit Wiederholungen und Statistik |
| Tracing | Jeder Lauf als Trace in LangSmith |
| Modellwahl | Swiss AI Research Platform (DeepSeek, Apertus) und FHNW-LiteLLM, dazu Claude und OpenRouter |

## Ausprobieren

```bash
pip install -e ".[dashboard,analyse,dev]"
python -m kartell demo      # Ablauf ohne API-Schlüssel (feste Skript-Agenten, kein LLM)
pytest                      # alle Tests, ohne API-Schlüssel
```

Echte Läufe mit LLMs, GitHub-Workflow und alle Befehle: [docs/technik.md](docs/technik.md)

## Mehr lesen

| Datei | Inhalt |
|---|---|
| [docs/technik.md](docs/technik.md) | Befehle, Modelle, Retrieval, MCP, Versuchsdateien, Projektstruktur |
| [docs/entscheidungen.md](docs/entscheidungen.md) | Warum wir was so gebaut haben – mit Alternativen |
| [docs/ergebnisse.md](docs/ergebnisse.md) | Vorstudie: die drei Befunde mit Zahlen, Zitaten und Grenzen |
| [docs/anhang.md](docs/anhang.md) | Alle Tabellen und Tests der Vorstudie, weitere Versuche |
| [docs/lernpfad.md](docs/lernpfad.md) | Lernpfad und Prüfungsfragen fürs Team |
| [docs/projektskizze.md](docs/projektskizze.md) | Ursprüngliche Projektskizze |

## Quellen

- Calvano, E., Calzolari, G., Denicolò, V., Pastorello, S. (2020): Artificial Intelligence, Algorithmic Pricing, and Collusion. *American Economic Review*, 110(10).
- Fish, S., Gonczarowski, Y. A., Shorrer, R. I. (2024): Algorithmic Collusion by Large Language Models. arXiv:2404.00806.
- Bundesgesetz über Kartelle und andere Wettbewerbsbeschränkungen (Kartellgesetz, KG), SR 251.
- Vertrag über die Arbeitsweise der Europäischen Union (AEUV), Art. 101.
- Toppreise.ch: Preisvergleich JBL Tune 770NC, abgerufen am 04.10.2026.
