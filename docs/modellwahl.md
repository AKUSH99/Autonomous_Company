# Modellwahl und Modellvergleich

Warum der Studienassistent **GLM-5.3 Flash** auf der **Swiss AI Research Platform** nutzt, gemessen an den
Kriterien aus SW4 (Folien 22 bis 38) und an unserem Testset.

## Messung

22 Testfragen aus `evaluation/fragen.jsonl` (Termine, Regeln, Inhalte aus sieben Modulen; drei Fragen ohne
Studienbezug, die abgelehnt werden sollen). Gleiche Unterlagen, gleiche Suche, gleicher Agent; nur das Modell und
das Reasoning ändern sich. Gemessen auf dem Thin Client am 07.10.2026 mit `python -m studienassistent bewerten`.

<!-- MESSUNG -->

**Suche allein** (ohne Sprachmodell): Die richtige Quelle steht bei 14 von 14 Fragen unter den ersten 5 Treffern,
mit BM25 allein wie mit der Hybrid-Suche (BM25 + Qwen3-Embeddings). Das Testset prüft die Quelle nur auf Ebene
des Moduls; der Nutzen der Embeddings zeigt sich bei Umschreibungen, etwa bei der Teamgrösse («Teams aus 3
Studierenden», nur über die Bedeutungssuche gefunden, Rang 7).

## Kriterien aus SW4

| Kriterium (SW4, Folie 25) | Was es für uns heisst | Entscheid |
|---|---|---|
| Endnutzer | Studierende erwarten richtige Daten und Regeln mit Quelle; eine falsche Frist ist schlimmer als keine Antwort | Antwort mit Reasoning, Quelle Pflicht, Fakten-Kennzahl im Testset |
| Throughput & Geschwindigkeit | Chat soll sich flüssig anfühlen; Ziel aus der Projektskizze: Antwort unter 20 s | Flash statt des grossen GLM-5.3 (siehe Messung) |
| Kosten | Kein Budget; Studierende sollen die App gratis nutzen | Swiss AI Research Platform: für uns ohne Kosten nutzbar (Zugang mit Hochschul-Login) |
| Technische Anforderungen | Function Calling für drei Werkzeuge, Deutsch, Kontext für 8 Treffer à 700 Zeichen | GLM-5.3 Flash kann alles davon; Ratenlimit unter 15 Anfragen/Min. pro Schlüssel |
| Betriebsmodell | Kursunterlagen und Fragen sollen in der Schweiz bleiben; offene Modelle | Plattform der Swiss AI Initiative (ETH, EPFL) am CSCS in der Schweiz; die GLM-Modelle sind offen verfügbar (Open Weights) |

**Alternativen, die wir nicht genommen haben:**
- **Kommerzielle APIs** (OpenAI, Anthropic, Google): stärker, aber kostenpflichtig, und Daten verlassen die Schweiz.
- **FHNW-LiteLLM-Proxy**: stellt Modelle mit Kostenobergrenze bereit; gut als Ausweichmöglichkeit, wenn das
  Ratenlimit der Swiss AI Platform nicht reicht.
- **Apertus** (das Schweizer Modell): für Deutsch und Schweizer Kontext interessant und per `--modell apertus`
  nutzbar; im Testset haben wir es noch nicht gemessen.

## Was wir beim Ausprobieren gelernt haben

- **GLM ohne Reasoning schreibt seine Gedanken in den Text.** Die Plattform trennt den Denkteil nur, wenn das
  Reasoning eingeschaltet ist; sonst steht vor der Antwort roher Gedankentext («…question is in German…»). Für
  Werkzeugaufrufe stört das nicht, für Antworten schon.
- **Reasoning nur für die Antwort.** Mit Reasoning in jeder Suchrunde dauerte eine unklare Frage über 3 Minuten und
  endete im Rekursionslimit. Jetzt prüft und sucht das Modell im schnellen Modus, und nur die Antwort entsteht mit
  maximalem Reasoning (Knoten `antworten`).
- **Strukturierte Ausgabe über Function Calling.** Die Eingangsprüfung als JSON-Schema brauchte mit GLM-5.3 und
  Reasoning bis zu 90 s; über einen Werkzeugaufruf im schnellen Modus 1 bis 3 s.
- **Ratenlimit statt Rechenleistung ist der Engpass.** Eine Frage braucht etwa 5 Aufrufe (Prüfung, Suche,
  Embedding, Antwort). Bei 14 Aufrufen pro Minute schafft ein Schlüssel rund 3 Fragen pro Minute; darum gibt es eine
  gemeinsame Taktbremse und eine Warteschlange (`betrieb.py`).
