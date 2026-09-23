// Balancing-Konfiguration – Eigentümer: Game Designer (GDD-Abschnitt 7 und 4).
// Werte ändern, ohne den Code anzufassen. Schlüssel = GDD-IDs.
window.BALANCING = {
  version: "GDD v1.3 (Balancing-Patch 3, nur L-02)",

  "P-01": 18,    // Kegel-Halbwinkel weit (°)
  "P-02": 260,   // Reichweite weit (px)
  "P-03": 7,     // Kegel-Halbwinkel Fokus (°)
  "P-04": 560,   // Reichweite Fokus (px)
  "P-05": 1.4,   // Orientierungszeit nach Verlassen des Kegels (s)
  "P-06": 38,    // Tempo geführt (px/s)
  "P-07": 27,    // Tempo im Dunkeln (px/s)
  "P-08": 1.2,   // Drift im Dunkeln (rad/s, maximale Kursänderung durch Zufall)
  "P-09": 0.5,   // Heimzug im Dunkeln (Anteil der Kursabweichung pro Sekunde)
  "P-10": 3,     // Max. Wracks pro Nacht
  "P-11": 50,    // Hafen-Radius (px)
  "P-12": 2.2,   // Wendegeschwindigkeit geführt (rad/s)
  "P-13": 125,   // Riff-Radius (px)

  // Nächte (GDD-Abschnitt 4). gapWidth = lichte Breite einer Riff-Durchfahrt in px (DEV-A02).
  levels: [
    { id: "L-01", name: "Ruhige See",       ships: 8,  spawnInterval: 7, maxActive: 2, gaps: 4, gapWidth: 60, outerRocks: 0, speedMul: 1.0, driftMul: 1.0 },
    { id: "L-02", name: "Auflandiger Wind", ships: 18, spawnInterval: 5, maxActive: 5, gaps: 3, gapWidth: 44, outerRocks: 6, speedMul: 1.15, driftMul: 1.35 },
    { id: "L-03", name: "Sturmnacht",       ships: 26, spawnInterval: 4.5, maxActive: 6, gaps: 3, gapWidth: 40, outerRocks: 7, speedMul: 1.2, driftMul: 1.5 }
  ]
};
