# Vorregistrierung: Replikation des Verbots-Experiments mit DeepSeek

Festgelegt am 29.09.2026, **bevor** die Läufe starten. Der Zeitstempel des Commits belegt das.

**Offenlegung:** Das Ergebnis mit Nemotron 3 Ultra kennen wir (siehe [ergebnisse.md](ergebnisse.md)): Mit Verbot
verstummen die Agenten (Regel 1 erfüllt); ob sie weiter koordinieren, blieb offen (Regel 3 nicht erfüllt, M3 gegen E1
p = 0.70). Diese Replikation prüft, ob das Muster für ein zweites Modell gilt – mit denselben Regeln, ohne nachträgliche
Anpassung.

## Was gleich bleibt

Frage, Bedingungen, Messgrössen M1–M6, Tests und Entscheidungsregeln 1–4 sind **wörtlich dieselben** wie in
[vorregistrierung_verbot.md](vorregistrierung_verbot.md). Ausgewertet wird mit demselben Befehl
(`python -m kartell verbot-auswerten <ordner> --modell deepseek_replikation`), M6 von Hand nach denselben Kriterien, mit
wörtlichen Zitaten in `evaluation/verbot_m6_handcodierung_deepseek.json`.

## Was anders ist

- **Modell:** DeepSeek (`deepseek-flash`, ohne Denkmodus) – dasselbe Modell wie in den Kern- und Abweichungsversuchen.
- **Läufe:** E1, E2, E18, E19 je 5 Durchgänge à 25 Runden, abwechselnd gestartet (E2, E18, E19, E1, dann der nächste
  Durchgang). Die Läufe tragen den Zusatz `_replikation`, damit sie sich nicht mit den älteren DeepSeek-Läufen
  (50 Runden) mischen.
- **Budget:** höchstens 0.90 USD, Reserve 0.05 USD auf dem DeepSeek-Konto. Stoppt der Budgetwächter vorzeitig, werden
  die bis dahin fertigen Läufe ausgewertet – es wird nichts nachträglich weggelassen oder nachgeholt, ohne das offen zu
  sagen.

## Was als Ergebnis gilt

Die Regeln 1–4 gelten unverändert für DeepSeek allein. Zusätzlich, ebenfalls vorab festgelegt:

- **„Repliziert“** heisst: Dieselbe Regel ist bei DeepSeek erfüllt wie bei Nemotron (also Regel 1, und Regel 3 nicht).
- Weicht das DeepSeek-Ergebnis ab, berichten wir beide Ergebnisse nebeneinander und sagen, dass das Muster vom Modell
  abhängt. Die Daten der beiden Modelle werden **nicht** zusammengelegt, um doch noch ein signifikantes Ergebnis zu
  erhalten.

## Bekannte Schwächen

- Weiterhin 5 bzw. 10 Läufe pro Bedingung: nur grosse Unterschiede werden sichtbar.
- DeepSeek ohne Denkmodus schreibt kürzere Notizen als Nemotron – M6 kann darum seltener zutreffen, ohne dass sich das
  Verhalten unterscheidet.
