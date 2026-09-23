# Architektur-Entscheidungen

Jede Entscheidung mit Begründung und verworfenen Alternativen – als Grundlage für Präsentation und Prüfungsfragen.

| # | Entscheidung | Warum | Verworfene Alternativen |
|---|---|---|---|
| 1 | **Markt: Bertrand-Wettbewerb mit Logit-Nachfrage** | Standardmodell der Kollusionsforschung (Calvano et al. 2020, Fish et al. 2024): Ergebnisse sind vergleichbar, Nash- und Monopolpreis lassen sich exakt berechnen | Eigenes Nachfragemodell (nicht vergleichbar), echte Marktdaten (keine Referenzpreise, Datenschutz) |
| 2 | **Orchestrierung mit LangGraph** | Expliziter Zustandsgraph: jede Phase einer Runde ist ein Knoten, Versuchsbedingungen schalten Knoten zu oder weg; gut erklär- und testbar | Einfache Python-Schleife (weniger strukturiert), CrewAI/AutoGen (weniger Kontrolle über Ablauf und Zustand) |
| 3 | **Claude über das offizielle Anthropic-SDK, nicht über LangChain-Modellklassen** | LangGraph braucht keine LangChain-Modelle; das SDK bietet strukturierte Ausgaben und den serverseitigen Refusal-Fallback direkt | LangChain-Wrapper (zusätzliche Abstraktionsschicht, Funktionen verzögert verfügbar) |
| 4 | **Offene Modelle über eine OpenAI-kompatible Schnittstelle** | vLLM, Ollama und viele Anbieter bieten diese Schnittstelle an; Apertus lässt sich so ohne Spezialcode anbinden | Hugging Face `transformers` direkt (GPU im Prozess nötig, schwer reproduzierbar) |
| 5 | **Strukturierte Ausgaben (JSON-Schema, Pydantic)** | Preise und Urteile sind maschinenlesbar und validiert; kein fehleranfälliges Parsen von Freitext | Freitext mit Regex-Parsing |
| 6 | **Agenten ohne Kooperationsanweisung und ohne Referenzpreise** | Sonst wäre Kollusion vorgegeben statt beobachtet (Validität) | Prompts mit Hinweisen auf Kartelle oder Wettbewerb |
| 7 | **Gedächtnis über Strategienotizen (Plan, Erkenntnisse) plus die letzten 10 Runden** | Begrenzte Kontextlänge und Kosten, trotzdem langfristige Strategie möglich; Ansatz aus Fish et al. 2024 | Gesamte Historie im Prompt (teuer, wächst mit jeder Runde) |
| 8 | **Öffentlicher Kanal statt Privatnachrichten** | Einfach, alle sehen dasselbe; entspricht öffentlichen Preissignalen | Bilaterale Kanäle (Erweiterung für später) |
| 9 | **Zweischichtiger Guardrail: Regeln + LLM mit RAG** | Regeln sind schnell, kostenlos und transparent, übersehen aber Umschreibungen; das LLM erkennt verschleierte Signale und begründet mit Rechtsgrundlagen | Nur Regeln (zu viele verpasste Fälle), nur LLM (teurer, ohne Sicherheitsnetz) |
| 10 | **Fail-safe: fällt das LLM aus, entscheidet die Regel-Schicht** | Der Filter bleibt auch bei API-Fehlern wirksam | Bei Fehlern immer zustellen (unsicher) oder immer blockieren (legt den Kanal lahm) |
| 11 | **BM25 statt Embeddings für das Retrieval** | Kleine Wissensbasis, Rechtsbegriffe sollen exakt treffen, keine externe API, vollständig nachvollziehbar | Embedding-Suche (sinnvoller Vergleich als Erweiterung) |
| 12 | **Preisgrenze 0 bis 5 × Stückkosten; bei Modellausfall Preis der Vorrunde** | Ein einzelner Fehler (Einheit, Tippfehler, Ausfall) soll ein Experiment nicht verfälschen oder abbrechen; Korrekturen werden protokolliert | Lauf abbrechen (verschwendet Budget), ungeprüft übernehmen |
| 13 | **Standardmodell `claude-opus-5`, Modell je Versuch konfigurierbar** | Hohe Qualität der Entscheidungen; ein günstigeres Modell ist eine bewusste Team-Entscheidung nach dem Pilotlauf | Fest verdrahtetes Modell |
| 14 | **Skript-Agenten nur für Tests und Demo, klar getrennt** | Ablauf lässt sich ohne API-Schlüssel und kostenlos prüfen; im Code und in den Logs als `scripted:*` markiert | Tests nur mit echten API-Aufrufen (teuer, nicht reproduzierbar) |
| 15 | **Protokoll als JSONL, eine Zeile pro Runde** | Live lesbar für das Dashboard, robust bei Abbrüchen, einfach auszuwerten | Datenbank (für den Umfang unnötig) |
| 16 | **DeepSeek als Voreinstellung (`--modell deepseek`) über dieselbe OpenAI-kompatible Schnittstelle** | Etwa 20-mal günstiger als `claude-opus-5`: mehr Wiederholungen und ein zusätzlicher Modellvergleich im selben Budget; kein zusätzlicher Code nötig. Es werden nur simulierte Daten gesendet, deshalb ist der Serverstandort China vertretbar | Eigene YAML-Dateien je Modell (Duplikate, laufen auseinander), eigenes DeepSeek-Backend (unnötig) |
