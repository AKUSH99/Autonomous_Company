// Nachtwache – Assets (Eigentümer: ART)
// Lieferstufe 2: code-basierte Grafik (Canvas-Zeichenanweisungen) und Audio (Synthese-Parameter).
// Signaturen folgen dem Asset-Vertrag aus dem Tech-Design-Dokument (TDD §4). Lizenz: eigene Erstellung.
(() => {
  'use strict';
  const TAU = Math.PI * 2;

  // Art-Style-Guide §3 – Palette „Nachtblau & Bernstein"
  const C = {
    sea: '#0B1A2E', deep: '#07111F', seaLight: '#12294A',
    beam: '#FFD98A', lantern: '#FFB347', rock: '#2A3441', rockHi: '#3B4757', foam: '#9FB4C7',
    harbor: '#7FE0C8', ui: '#E8EEF5', danger: '#FF5A5F', wood: '#6B4F3A', woodHi: '#8A6A4E', sail: '#D8DEE6',
    island: '#2C3A2F', islandRim: '#4A5A48', tower: '#E8EEF5', stripe: '#C8553D'
  };

  // Deterministische Felsform aus rock.seed (7 Eckpunkte, ±20 % Radius)
  function rockPath(c, r, scale = 1) {
    const n = 7;
    c.beginPath();
    for (let i = 0; i <= n; i++) {
      const a = i / n * TAU + r.seed * 6;
      const j = 0.8 + 0.4 * Math.abs(Math.sin(r.seed * 97 + i * 1.7));
      const px = r.x + Math.cos(a) * r.r * j * scale, py = r.y + Math.sin(a) * r.r * j * scale;
      if (i === 0) c.moveTo(px, py); else c.lineTo(px, py);
    }
    c.closePath();
  }
  function wedge(c, x, y, a, half, range) { c.beginPath(); c.moveTo(x, y); c.arc(x, y, range, a - half, a + half); c.closePath(); }
  function circle(c, x, y, r) { c.beginPath(); c.arc(x, y, r, 0, TAU); }
  function glow(c, x, y, r, color, alpha) {
    const g = c.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, color); g.addColorStop(1, 'rgba(0,0,0,0)');
    c.globalAlpha = alpha; c.fillStyle = g; circle(c, x, y, r); c.fill(); c.globalAlpha = 1;
  }
  function star(c, x, y, R) {
    c.beginPath();
    for (let i = 0; i < 10; i++) {
      const a = -Math.PI / 2 + i * Math.PI / 5, r = i % 2 ? R * 0.45 : R;
      c.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r);
    }
    c.closePath();
  }

  window.ASSETS = {
    palette: {
      sea: C.sea, darkness: 'rgba(4,10,22,0.9)', ui: C.ui, uiDim: 'rgba(232,238,245,0.7)',
      accent: C.beam, danger: C.danger, harbor: C.harbor, panel: 'rgba(7,17,31,0.88)'
    },

    graphics: {
      // G-001 Meer mit langsam treibenden Wellenlinien
      'G-001': (c, t, W, H) => {
        const g = c.createRadialGradient(W / 2, H / 2, 40, W / 2, H / 2, W * 0.65);
        g.addColorStop(0, C.seaLight); g.addColorStop(1, C.deep);
        c.fillStyle = g; c.fillRect(0, 0, W, H);
        c.strokeStyle = C.foam; c.lineWidth = 1.2; c.globalAlpha = 0.13;
        for (let i = 0; i < 90; i++) {
          const x = ((i * 137.5) % W + t * (4 + (i % 5))) % (W + 30) - 15;
          const y = (i * 71.3) % H + Math.sin(t * 0.7 + i) * 2;
          c.beginPath(); c.moveTo(x - 7, y); c.quadraticCurveTo(x, y - 3, x + 7, y); c.stroke();
        }
      },
      // G-002 Insel
      'G-002': (c, x, y) => {
        c.fillStyle = C.islandRim; circle(c, x, y, 35); c.fill();
        c.fillStyle = C.island; circle(c, x + 1, y + 1, 29); c.fill();
        c.fillStyle = '#34463A'; circle(c, x - 9, y + 8, 9); c.fill(); circle(c, x + 11, y - 6, 7); c.fill();
      },
      // G-003 Leuchtturm (Draufsicht), Lampe zeigt in Kegelrichtung
      'G-003': (c, x, y, aim) => {
        c.fillStyle = C.tower; circle(c, x, y, 13); c.fill();
        c.strokeStyle = C.stripe; c.lineWidth = 3; circle(c, x, y, 9.5); c.stroke();
        c.fillStyle = '#FFE6A8'; circle(c, x, y, 5.5); c.fill();
        c.fillStyle = '#FFFFFF'; circle(c, x + Math.cos(aim) * 3, y + Math.sin(aim) * 3, 2.5); c.fill();
      },
      // G-004 Lichtkegel weit / G-005 Fokus-Strahl (additiv, focus 0…1)
      'G-004': (c, x, y, a, half, range, focus) => {
        const g = c.createRadialGradient(x, y, 8, x, y, range);
        // BUG-003: wärmerer, satterer Bernstein-Ton, damit der Kegel über dem blauen Meer nicht weißlich wirkt
        g.addColorStop(0, `rgba(255,205,120,${0.30 + focus * 0.12})`);
        g.addColorStop(0.55, `rgba(255,170,70,${0.16 + focus * 0.08})`);
        g.addColorStop(1, 'rgba(255,160,60,0)');
        c.fillStyle = g;
        wedge(c, x, y, a, half * 1.25, range); c.globalAlpha = 0.45; c.fill();
        wedge(c, x, y, a, half, range); c.globalAlpha = 1; c.fill();
      },
      // G-006 Schiff (verloren) / G-007 Schiff (geführt: wärmeres Segel, Kielwasser)
      'G-006': (c, s, t) => {
        c.translate(s.x, s.y); c.rotate(s.heading);
        c.strokeStyle = 'rgba(200,220,235,0.28)'; c.lineWidth = 1.2;
        c.beginPath(); c.moveTo(-9, -3); c.lineTo(-22, -8); c.moveTo(-9, 3); c.lineTo(-22, 8); c.stroke();
        c.fillStyle = C.wood;
        c.beginPath(); c.moveTo(11, 0); c.quadraticCurveTo(4, -5.5, -9, -4.5); c.lineTo(-9, 4.5); c.quadraticCurveTo(4, 5.5, 11, 0); c.fill();
        c.fillStyle = C.woodHi; c.fillRect(-6, -2.5, 11, 5);
        c.fillStyle = s.guided ? '#F4E3C0' : C.sail;
        c.beginPath(); c.moveTo(1, -7); c.lineTo(4, 0); c.lineTo(1, 7); c.lineTo(-2, 0); c.closePath(); c.fill();
      },
      // G-008 Fels mit Gischtsaum
      'G-008': (c, r, t) => {
        c.strokeStyle = C.foam; c.globalAlpha = 0.45 + 0.15 * Math.sin(t * 1.5 + r.seed * 10); c.lineWidth = 2;
        rockPath(c, r, 1.18); c.stroke(); c.globalAlpha = 1;
        c.fillStyle = C.rock; rockPath(c, r); c.fill();
        c.fillStyle = C.rockHi; rockPath(c, { ...r, x: r.x - r.r * 0.2, y: r.y - r.r * 0.25 }, 0.55); c.fill();
      },
      // G-009 Gischt-Umriss über der Dunkelheit (D-004: ca. 35 % Deckkraft)
      'G-009': (c, r, t) => {
        c.strokeStyle = C.foam; c.lineWidth = 1.3;
        c.globalAlpha = 0.3 + 0.07 * Math.sin(t * 1.5 + r.seed * 10);
        rockPath(c, r, 1.18); c.stroke();
      },
      // G-010 Wrack: Trümmer und Warnring, verblasst über 4 s
      'G-010': (c, wr, age) => {
        const a = Math.max(0, 1 - age / 4);
        c.translate(wr.x, wr.y);
        c.strokeStyle = C.danger; c.lineWidth = 1.5; c.globalAlpha = a * 0.7;
        circle(c, 0, 0, 12 + age * 3); c.stroke();
        c.globalAlpha = a;
        c.rotate(wr.heading + age * 0.2);
        c.fillStyle = C.wood; c.fillRect(-8, -3, 7, 4); c.rotate(0.9); c.fillRect(1, -1, 6, 3);
      },
      // G-011 Hafenring mit vier Anlegelichtern
      'G-011': (c, x, y, r, t) => {
        c.strokeStyle = C.harbor; c.globalAlpha = 0.4; c.lineWidth = 1.5; c.setLineDash([3, 7]);
        c.lineDashOffset = -t * 6; circle(c, x, y, r); c.stroke(); c.setLineDash([]); c.globalAlpha = 1;
        for (let i = 0; i < 4; i++) {
          const a = Math.PI / 4 + i * Math.PI / 2;
          glow(c, x + Math.cos(a) * r, y + Math.sin(a) * r, 7, C.harbor, 0.8 + 0.2 * Math.sin(t * 2 + i));
        }
      },
      // G-012 Laterne (additiv); geführt: hellerer Kern + Ring für die Rest-Orientierung (M-03)
      'G-012': (c, x, y, guided, t, frac) => {
        const flick = 0.85 + 0.15 * Math.sin(t * 9 + x * 0.1);
        if (guided) {
          glow(c, x, y, 18, '#FFF1D0', 0.9);
          c.globalCompositeOperation = 'source-over';
          c.strokeStyle = C.harbor; c.lineWidth = 2; c.globalAlpha = 0.9;
          c.beginPath(); c.arc(x, y, 13, -Math.PI / 2, -Math.PI / 2 + TAU * Math.max(0, Math.min(1, frac))); c.stroke();
        } else {
          glow(c, x, y, 12, C.lantern, 0.9 * flick);
        }
      },
      // G-013 UI-Panel
      'G-013': (c, x, y, w, h) => {
        c.shadowColor = 'rgba(0,0,0,0.5)'; c.shadowBlur = 24;
        c.fillStyle = 'rgba(7,17,31,0.9)';
        c.beginPath(); if (c.roundRect) c.roundRect(x, y, w, h, 16); else c.rect(x, y, w, h); c.fill();
        c.shadowBlur = 0; c.strokeStyle = 'rgba(255,217,138,0.35)'; c.lineWidth = 1; c.stroke();
      },
      // G-014 Stern (voll/leer)
      'G-014': (c, x, y, size, filled) => {
        star(c, x, y, size / 2);
        if (filled) { c.shadowColor = C.beam; c.shadowBlur = 14; c.fillStyle = C.beam; c.fill(); }
        else { c.strokeStyle = 'rgba(232,238,245,0.35)'; c.lineWidth = 2; c.stroke(); }
      },
      // G-015 Fokus-Button (Touch)
      'G-015': (c, x, y, r, active) => {
        c.fillStyle = active ? 'rgba(255,217,138,0.45)' : 'rgba(232,238,245,0.12)';
        circle(c, x, y, r); c.fill();
        c.strokeStyle = active ? C.beam : 'rgba(232,238,245,0.5)'; c.lineWidth = 2; c.stroke();
        c.strokeStyle = C.ui; c.lineWidth = 2; circle(c, x, y - 6, 9); c.stroke();
        c.fillStyle = C.ui; circle(c, x, y - 6, 3); c.fill();
        c.fillStyle = C.ui; c.font = '600 12px system-ui, sans-serif'; c.textAlign = 'center'; c.fillText('FOKUS', x, y + 20);
      },
      // G-016 Icons: pause | sound | mute
      'G-016': (c, name, x, y, r) => {
        c.fillStyle = 'rgba(232,238,245,0.12)'; circle(c, x, y, r); c.fill();
        c.fillStyle = C.ui; c.strokeStyle = C.ui; c.lineWidth = 1.8;
        if (name === 'pause') { c.fillRect(x - 5, y - 6, 3.5, 12); c.fillRect(x + 1.5, y - 6, 3.5, 12); return; }
        c.beginPath(); c.moveTo(x - 8, y - 3); c.lineTo(x - 4, y - 3); c.lineTo(x + 1, y - 7); c.lineTo(x + 1, y + 7); c.lineTo(x - 4, y + 3); c.lineTo(x - 8, y + 3); c.closePath(); c.fill();
        if (name === 'sound') { c.beginPath(); c.arc(x + 2, y, 5, -0.8, 0.8); c.stroke(); c.beginPath(); c.arc(x + 2, y, 8.5, -0.8, 0.8); c.stroke(); }
        else { c.beginPath(); c.moveTo(x + 4, y - 4); c.lineTo(x + 10, y + 4); c.moveTo(x + 10, y - 4); c.lineTo(x + 4, y + 4); c.stroke(); }
      },
      // G-017 Regen (Sturmnacht, kosmetisch)
      'G-017': (c, t, intensity) => {
        c.strokeStyle = 'rgba(170,190,215,0.16)'; c.lineWidth = 1;
        c.beginPath();
        for (let i = 0; i < 140 * intensity; i++) {
          const x = ((i * 97.3) % 1000 + t * 90) % 1000 - 20;
          const y = ((i * 53.9) % 580 + t * 420) % 580 - 20;
          c.moveTo(x, y); c.lineTo(x - 5, y + 14);
        }
        c.stroke();
      }
    },

    // Einmalige Soundeffekte (Art-Style-Guide §8)
    sfx: {
      'SFX-001': { layers: [ // Nebelhorn – Schiff erscheint
        { wave: 'sawtooth', freq: [110, 104], dur: 1.2, attack: 0.18, gain: 0.07, filter: { type: 'lowpass', freq: [650, 380], q: 1 } },
        { wave: 'sawtooth', freq: [55, 52], dur: 1.2, attack: 0.2, gain: 0.05, filter: { type: 'lowpass', freq: 300 } }
      ] },
      'SFX-002': { layers: [ // Glocke – Anlegen
        { wave: 'sine', freq: 880, dur: 1.4, gain: 0.16, attack: 0.003 },
        { wave: 'sine', freq: 2210, dur: 0.6, gain: 0.05, attack: 0.003 },
        { wave: 'sine', freq: 1320, dur: 0.9, gain: 0.06, attack: 0.003, delay: 0.12 }
      ] },
      'SFX-003': { layers: [ // Krachen – Schiffbruch
        { wave: 'noise', dur: 0.55, gain: 0.32, filter: { type: 'lowpass', freq: [1800, 180] } },
        { wave: 'sine', freq: [95, 38], dur: 0.45, gain: 0.3 },
        { wave: 'noise', dur: 0.14, gain: 0.16, filter: { type: 'bandpass', freq: 950, q: 3 }, delay: 0.05 }
      ] },
      'SFX-005': { layers: [ // UI-Klick
        { wave: 'sine', freq: [700, 950], dur: 0.07, gain: 0.1 }
      ] },
      'SFX-006': { layers: [ // Nacht geschafft – Arpeggio A-Dur
        { wave: 'triangle', freq: 440, dur: 0.7, gain: 0.12, delay: 0 },
        { wave: 'triangle', freq: 554.37, dur: 0.7, gain: 0.12, delay: 0.13 },
        { wave: 'triangle', freq: 659.25, dur: 0.7, gain: 0.12, delay: 0.26 },
        { wave: 'sine', freq: 880, dur: 1.2, gain: 0.12, delay: 0.39 }
      ] },
      'SFX-007': { layers: [ // Nacht verloren – absteigend, gedämpftes Horn
        { wave: 'triangle', freq: 329.63, dur: 0.7, gain: 0.12, delay: 0 },
        { wave: 'triangle', freq: 261.63, dur: 0.7, gain: 0.12, delay: 0.28 },
        { wave: 'triangle', freq: 220, dur: 1.2, gain: 0.12, delay: 0.56 },
        { wave: 'sawtooth', freq: [82, 78], dur: 1.6, attack: 0.3, gain: 0.05, delay: 0.5, filter: { type: 'lowpass', freq: 400 } }
      ] }
    },

    // Dauerschleifen
    loops: {
      'SFX-004': { wave: 'sine', freq: 220, gain: 0.04, trigger: 'focus', filter: { type: 'lowpass', freq: 800 } }, // Fokus-Summen
      'SFX-008': { wave: 'noise', gain: 0.045, filter: { type: 'lowpass', freq: 520, q: 0.7 }, lfo: { rate: 0.12, depth: 0.02 } } // Wellenrauschen
    },

    // MUS-001 Nachtthema: ruhige Pads a-Moll, sparsames Arpeggio
    music: {
      'MUS-001': {
        bpm: 56, beatsPerChord: 8,
        chords: [['A2', 'E3', 'A3', 'C4'], ['F2', 'C3', 'E3', 'A3'], ['C3', 'G3', 'C4', 'E4'], ['G2', 'D3', 'G3', 'B3']],
        pad: { wave: 'triangle', gain: 0.03, attack: 2, release: 2.5, detune: 7, filter: { type: 'lowpass', freq: 900 } },
        arp: { wave: 'sine', gain: 0.018, attack: 0.01, dur: 1.6, pattern: [1, 2, 3, 2], every: 2, octave: 1 }
      }
    }
  };
})();
