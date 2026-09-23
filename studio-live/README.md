# Studio Live

Pixel-Studio im Kairosoft-Stil, in dem man den sieben Agenten beim Arbeiten zusieht.

- **Aufzeichnung:** spielt Run 01 „Nachtwache" ab – gekürzte Originalübergaben und echte QA-Messwerte aus `simulation/run-01/`.
- **Live:** startet ein neues Projekt. Jeder Agent ist ein echter Claude-Aufruf mit seinem System-Prompt aus `prompts/` (rund 20 Aufrufe). Das braucht eine Claude-Artifact-Ansicht mit der Fähigkeit `sample`; außerhalb davon läuft nur die Aufzeichnung.

`python3 studio-live/build.py` baut `index.html` aus `template.html`, den Prompts und der Aufzeichnung.
