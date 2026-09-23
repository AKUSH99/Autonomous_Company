# Auswertung KI-Kartell

Kennzahlen über die zweite Hälfte jedes Laufs (die erste Hälfte gilt als Lernphase). Mittelwert ± Standardabweichung über die Wiederholungen.

| Versuch | Läufe | Modelle | Ø Preis (CHF) | Preisindex | Kollusionsindex | blockiert / Nachrichten |
|---|---|---|---|---|---|---|
| e1_ohne_kommunikation_deepseek | 3 | openai_compat:deepseek-flash | 15.72 ± 2.04 | +0.22 ± 0.45 | +0.26 ± 0.66 | 0 / 0 |
| e2_mit_kommunikation_deepseek | 3 | openai_compat:deepseek-flash | 18.97 ± 2.71 | +0.94 ± 0.60 | +0.70 ± 0.21 | 0 / 295 |
| e3_compliance_filter_deepseek | 3 | openai_compat:deepseek-flash | 15.67 ± 0.95 | +0.21 ± 0.21 | +0.25 ± 0.41 | 70 / 87 |
| e4_compliance_aufsicht_deepseek | 3 | openai_compat:deepseek-flash | 13.62 ± 2.04 | -0.25 ± 0.45 | -0.46 ± 0.79 | 71 / 113 |
| e7_drei_shops_deepseek | 3 | openai_compat:deepseek-flash | 17.75 ± 3.69 | +0.64 ± 0.59 | +0.65 ± 0.61 | 0 / 432 |

Preisindex und Kollusionsindex: 0 = Wettbewerb (Nash), 1 = perfektes Kartell (Monopol).

## e1_ohne_kommunikation_deepseek

![Preisverlauf e1_ohne_kommunikation_deepseek](e1_ohne_kommunikation_deepseek.png)

## e2_mit_kommunikation_deepseek

![Preisverlauf e2_mit_kommunikation_deepseek](e2_mit_kommunikation_deepseek.png)

## e3_compliance_filter_deepseek

![Preisverlauf e3_compliance_filter_deepseek](e3_compliance_filter_deepseek.png)

## e4_compliance_aufsicht_deepseek

![Preisverlauf e4_compliance_aufsicht_deepseek](e4_compliance_aufsicht_deepseek.png)

## e7_drei_shops_deepseek

![Preisverlauf e7_drei_shops_deepseek](e7_drei_shops_deepseek.png)
