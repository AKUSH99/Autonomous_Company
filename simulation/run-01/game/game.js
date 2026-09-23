// Nachtwache – Engine & Spiellogik
// Eigentümer: DEV. Balancing kommt aus config.js (GD), Grafik und Audio aus assets.js (ART).
// Fehlt assets.js oder ein einzelnes Asset, greifen Platzhalter.
(() => {
  'use strict';

  const VERSION = '1.0.0';
  const CFG = window.BALANCING;
  const ASSETS = window.ASSETS || null;
  const W = 960, H = 540, CX = W / 2, CY = H / 2;
  const TAU = Math.PI * 2;
  const SHIP_R = 7;
  const DT = 1 / 60;
  const P = id => CFG[id];

  const rad = d => d * Math.PI / 180;
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const angNorm = a => { a %= TAU; if (a > Math.PI) a -= TAU; if (a < -Math.PI) a += TAU; return a; };
  const angDiff = (a, b) => angNorm(a - b);
  const polar = (a, r) => ({ x: CX + Math.cos(a) * r, y: CY + Math.sin(a) * r });
  const dist = (ax, ay, bx, by) => Math.hypot(ax - bx, ay - by);

  // Seed-basierter Zufall (mulberry32) – reproduzierbare Nächte für QA (DEV-D01)
  function makeRng(seed) {
    let a = seed >>> 0;
    return () => {
      a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ===================================================================
  // Welt: reine Simulation ohne Rendering – vom Spiel und von QA genutzt
  // ===================================================================

  function createWorld(levelIdx, seed) {
    const L = CFG.levels[levelIdx];
    const rng = makeRng(seed);
    const R = P('P-13');
    const gapOffset = rng() * TAU;
    const gaps = Array.from({ length: L.gaps }, (_, i) => angNorm(gapOffset + i * TAU / L.gaps));
    const rocks = [];

    // Riff-Ring (BUG-002): je Segment zwischen zwei Durchfahrten Felsen von Kante zu Kante.
    // Die Kantenfelsen sitzen exakt so, dass die lichte Breite L.gapWidth entspricht.
    const spacing = rad(10), edgeR = 14;
    const edge = Math.asin((L.gapWidth / 2 + edgeR) / R);
    const sorted = gaps.slice().sort((a, b) => a - b);
    for (let i = 0; i < sorted.length; i++) {
      const start = sorted[i] + edge;
      const end = (i + 1 < sorted.length ? sorted[i + 1] : sorted[0] + TAU) - edge;
      const count = Math.max(1, Math.ceil((end - start) / spacing));
      for (let j = 0; j <= count; j++) {
        const a = start + (end - start) * j / count;
        const isEdge = j === 0 || j === count;
        const r = isEdge ? R : R + (rng() - 0.5) * 10;
        const rr = isEdge ? edgeR : 12 + rng() * 4;
        rocks.push({ ...polar(a, r), r: rr, reef: true, seed: rng() });
      }
    }

    // Äußere Felsen: außerhalb der Kreisbahn, nicht vor den Einfahrten
    let outer = 0, tries = 0;
    while (outer < L.outerRocks && tries++ < 1000) {
      const a = rng() * TAU, r = R + 85 + rng() * 150;
      const p = polar(a, r), rr = 14 + rng() * 6;
      if (p.x < 40 || p.x > W - 40 || p.y < 40 || p.y > H - 40) continue;
      if (gaps.some(g => Math.abs(angDiff(a, g)) < rad(18))) continue;
      if (rocks.some(o => !o.reef && dist(o.x, o.y, p.x, p.y) < 70)) continue;
      rocks.push({ ...p, r: rr, reef: false, seed: rng() });
      outer++;
    }

    return {
      levelIdx, L, rng, R, gaps, rocks,
      ships: [], wrecks: [], events: [],
      t: 0, spawnT: 2, spawned: 0, docked: 0, wrecked: 0, score: 0, stars: 0,
      status: 'play', nextId: 1,
      aim: -Math.PI / 2, focus: 0, focusTarget: false
    };
  }

  function spawnShip(w) {
    const rng = w.rng, m = 12;
    let d = rng() * 2 * (W + H), x, y;
    if (d < W) { x = d; y = -m; }
    else if ((d -= W) < H) { x = W + m; y = d; }
    else if ((d -= H) < W) { x = W - d; y = H + m; }
    else { d -= W; x = -m; y = H - d; }
    const heading = Math.atan2(CY - y, CX - x) + (rng() - 0.5) * rad(50);
    w.ships.push({ id: w.nextId++, x, y, heading, wander: 0, guideT: 0, lit: false, inside: false, age: 0 });
    w.spawned++;
    w.events.push({ type: 'spawn', x, y });
  }

  function beam(w) {
    return {
      angle: w.aim,
      half: rad(lerp(P('P-01'), P('P-03'), w.focus)),
      range: lerp(P('P-02'), P('P-04'), w.focus)
    };
  }

  function isLit(s, b) {
    const dx = s.x - CX, dy = s.y - CY, d = Math.hypot(dx, dy);
    if (d > b.range + SHIP_R) return false;
    const tol = Math.atan2(SHIP_R, Math.max(d, 1));
    return Math.abs(angDiff(Math.atan2(dy, dx), b.angle)) <= b.half + tol;
  }

  // M-03 (D-005): Kreisbahn ums Riff bis zur nächsten Durchfahrt, dann hinein, dann Hafen
  function guidedTarget(w, s) {
    if (s.inside) return { x: CX, y: CY };
    const a = Math.atan2(s.y - CY, s.x - CX);
    let g = w.gaps[0], best = Infinity;
    for (const gg of w.gaps) {
      const d = Math.abs(angDiff(gg, a));
      if (d < best) { best = d; g = gg; }
    }
    const d = angDiff(g, a);
    if (Math.abs(d) > rad(4)) return polar(a + Math.sign(d) * Math.min(Math.abs(d), 0.5), w.R + 40);
    return polar(g, w.R - 45);
  }

  function avoidance(w, s) {
    let ax = 0, ay = 0;
    const hx = Math.cos(s.heading), hy = Math.sin(s.heading);
    for (const k of w.rocks) {
      const dx = k.x - s.x, dy = k.y - s.y, d = Math.hypot(dx, dy);
      const reach = k.r + SHIP_R + 30;
      if (d < reach && d > 0.001) {
        const f = (reach - d) / reach * 2.2;
        ax -= dx / d * f; ay -= dy / d * f;
      }
      // BUG-001: Frontal voraus liegende Felsen seitlich umfahren – reine Abstoßung hebt sich
      // bei Frontalkurs mit der Zielrichtung auf.
      const ahead = dx * hx + dy * hy;
      if (ahead > 0 && ahead < 70) {
        const lat = dx * -hy + dy * hx;
        if (Math.abs(lat) < k.r + SHIP_R + 8) {
          const side = lat >= 0 ? -1 : 1;
          const f = (1 - ahead / 70) * 2.5;
          ax += -hy * side * f; ay += hx * side * f;
        }
      }
    }
    return { ax, ay };
  }

  function stepShip(w, s, dt, b) {
    const L = w.L;
    s.lit = isLit(s, b);
    s.guideT = s.lit ? P('P-05') : Math.max(0, s.guideT - dt);
    if (dist(s.x, s.y, CX, CY) < w.R - 12) s.inside = true;

    let turn, speed;
    if (s.guideT > 0) {
      const t = guidedTarget(w, s);
      let vx = t.x - s.x, vy = t.y - s.y;
      const n = Math.hypot(vx, vy) || 1;
      vx /= n; vy /= n;
      const av = avoidance(w, s);
      const desired = Math.atan2(vy + av.ay, vx + av.ax);
      const maxT = P('P-12') * dt;
      turn = clamp(angDiff(desired, s.heading), -maxT, maxT);
      speed = P('P-06') * L.speedMul;
    } else {
      const drift = P('P-08') * L.driftMul;
      s.wander += (-s.wander * 0.8 + (w.rng() * 2 - 1) * drift * 10) * dt;
      s.wander = clamp(s.wander, -drift, drift);
      const toC = Math.atan2(CY - s.y, CX - s.x);
      let rate = s.wander + P('P-09') * angDiff(toC, s.heading);
      const off = s.x < 0 || s.x > W || s.y < 0 || s.y > H;
      if (off && s.age > 3) rate += 2 * angDiff(toC, s.heading);
      turn = rate * dt;
      speed = P('P-07') * L.speedMul;
    }
    s.heading = angNorm(s.heading + turn);
    s.x += Math.cos(s.heading) * speed * dt;
    s.y += Math.sin(s.heading) * speed * dt;
    s.age += dt;
  }

  function stepWorld(w, dt, input) {
    if (w.status !== 'play') return;
    w.t += dt;
    if (input) {
      if (input.aim != null) w.aim = input.aim;
      w.focusTarget = !!input.focus;
    }
    w.focus = clamp(w.focus + (w.focusTarget ? 1 : -1) * dt / 0.15, 0, 1);
    const b = beam(w);

    w.spawnT -= dt;
    if (w.spawnT <= 0 && w.spawned < w.L.ships && w.ships.length < w.L.maxActive) {
      spawnShip(w);
      w.spawnT = w.L.spawnInterval;
    }

    for (const s of w.ships) stepShip(w, s, dt, b);

    for (let i = w.ships.length - 1; i >= 0; i--) {
      const s = w.ships[i];
      if (dist(s.x, s.y, CX, CY) < P('P-11')) {
        w.ships.splice(i, 1);
        w.docked++;
        w.score += 100;
        w.events.push({ type: 'dock', x: s.x, y: s.y });
        continue;
      }
      for (const k of w.rocks) {
        if (dist(s.x, s.y, k.x, k.y) < k.r + SHIP_R) {
          w.ships.splice(i, 1);
          w.wrecked++;
          w.wrecks.push({ x: s.x, y: s.y, heading: s.heading, t: w.t });
          w.events.push({ type: 'wreck', x: s.x, y: s.y });
          break;
        }
      }
    }

    if (w.wrecked >= P('P-10')) {
      w.status = 'lose';
      w.events.push({ type: 'lose' });
    } else if (w.docked + w.wrecked >= w.L.ships) {
      w.status = 'win';
      w.stars = P('P-10') - w.wrecked;
      w.score += w.stars * 50;
      w.events.push({ type: 'win' });
    }
  }

  // ===================================================================
  // Debug-Schnittstelle für QA (DEV-D01) – Simulation im Zeitraffer
  // Bots bekommen die Welt nur lesend: bot(world) -> { aim, focus }
  // ===================================================================

  function simulate({ seed = 1, level = 0, bot = null, maxTime = 900, dt = DT } = {}) {
    const w = createWorld(level, seed);
    let input = { aim: -Math.PI / 2, focus: false };
    while (w.status === 'play' && w.t < maxTime) {
      if (bot) input = bot(w, { CX, CY, W, H, SHIP_R, P, beam, isLit, angDiff }) || input;
      stepWorld(w, dt, input);
      w.events.length = 0;
    }
    return { result: w.status, time: +w.t.toFixed(2), docked: w.docked, wrecked: w.wrecked, spawned: w.spawned, score: w.score };
  }

  // ===================================================================
  // Live-Spiel: Canvas, Eingabe, Audio, Rendering, Screens
  // ===================================================================

  const params = new URLSearchParams(location.search);
  const DEBUG = params.has('debug');
  const FIXED_SEED = params.has('seed') ? parseInt(params.get('seed'), 10) : null;
  const reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');
  const dark = document.createElement('canvas');
  const dctx = dark.getContext('2d');
  let k = 1; // Pixel pro logischer Einheit

  const PAL = Object.assign({
    sea: '#16324f', darkness: 'rgba(2,6,14,0.9)', ui: '#ffffff', uiDim: 'rgba(255,255,255,0.65)',
    accent: '#ffd98a', danger: '#ff5a5f', harbor: '#7fe0c8', panel: 'rgba(0,0,0,0.72)',
    font: 'system-ui, -apple-system, "Segoe UI", sans-serif'
  }, ASSETS && ASSETS.palette);

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const scale = Math.min(window.innerWidth / W, window.innerHeight / H);
    const cssW = Math.max(1, Math.floor(W * scale)), cssH = Math.max(1, Math.floor(H * scale));
    canvas.style.width = cssW + 'px';
    canvas.style.height = cssH + 'px';
    canvas.width = Math.round(cssW * dpr);
    canvas.height = Math.round(cssH * dpr);
    dark.width = canvas.width;
    dark.height = canvas.height;
    k = canvas.width / W;
  }
  window.addEventListener('resize', resize);
  resize();

  // ---------- Zustand ----------
  let state = 'title';            // title | play | pause | win | lose | end
  let world = null;
  let levelIdx = 0;
  let levelSeed = 1;
  let runScore = 0;
  let clock = 0;
  const demoWorld = createWorld(0, 7);
  let titleAim = -Math.PI / 2;
  let particles = [];
  let flashes = [];
  let shake = 0;
  let buttons = [];
  let override = null;            // QA/Marketing: { aim, focus }

  // ---------- Eingabe ----------
  let pointerAim = -Math.PI / 2;
  let mouseFocus = false, keyFocus = false;
  const focusPointers = new Set();
  let touchUsed = false;
  let aimMoved = 0, focusUsed = false;

  const pauseBtn = { x: W - 34, y: 30, r: 17 };
  const soundBtn = { x: W - 78, y: 30, r: 17 };
  const focusBtn = { x: W - 78, y: H - 78, r: 48 };

  function toLogical(e) {
    const r = canvas.getBoundingClientRect();
    return { x: (e.clientX - r.left) / r.width * W, y: (e.clientY - r.top) / r.height * H };
  }
  function aimAt(p) {
    const a = Math.atan2(p.y - CY, p.x - CX);
    aimMoved += Math.abs(angDiff(a, pointerAim));
    pointerAim = a;
  }
  const inCircle = (p, c) => dist(p.x, p.y, c.x, c.y) <= c.r;
  const inRect = (p, b) => p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h;

  canvas.addEventListener('pointerdown', e => {
    e.preventDefault();
    ensureAudio();
    const p = toLogical(e);
    if (e.pointerType === 'touch') touchUsed = true;
    if (inCircle(p, soundBtn)) { toggleMute(); return; }
    if (state === 'play' && inCircle(p, pauseBtn)) { setPaused(true); return; }
    if (state !== 'play') {
      const b = buttons.find(bt => inRect(p, bt));
      if (b) { playSfx('SFX-005'); b.action(); }
      else if (state === 'title') { playSfx('SFX-005'); startRun(); }
      return;
    }
    if (e.pointerType === 'touch' && inCircle(p, focusBtn)) { focusPointers.add(e.pointerId); return; }
    if (e.pointerType === 'mouse' && e.button === 0) mouseFocus = true;
    aimAt(p);
  });
  canvas.addEventListener('pointermove', e => {
    if (focusPointers.has(e.pointerId)) return;
    if (e.pointerType === 'touch' && e.pressure === 0) return;
    aimAt(toLogical(e));
  });
  const release = e => {
    focusPointers.delete(e.pointerId);
    if (e.pointerType === 'mouse') mouseFocus = false;
  };
  canvas.addEventListener('pointerup', release);
  canvas.addEventListener('pointercancel', release);
  canvas.addEventListener('contextmenu', e => e.preventDefault());

  window.addEventListener('keydown', e => {
    ensureAudio();
    if (e.code === 'Space') { keyFocus = true; e.preventDefault(); }
    if (e.code === 'KeyM') toggleMute();
    if (e.code === 'KeyP' || e.code === 'Escape') {
      if (state === 'play') setPaused(true); else if (state === 'pause') setPaused(false);
    }
    if (e.code === 'Enter') {
      if (state === 'title') startRun();
      else if (buttons[0]) buttons[0].action();
    }
    if (DEBUG && e.code === 'KeyN' && state === 'play') {
      world.docked = world.L.ships - world.wrecked; world.ships.length = 0;
    }
  });
  window.addEventListener('keyup', e => { if (e.code === 'Space') keyFocus = false; });
  window.addEventListener('blur', () => { if (state === 'play') setPaused(true); mouseFocus = keyFocus = false; focusPointers.clear(); });
  document.addEventListener('visibilitychange', () => { if (document.hidden && state === 'play') setPaused(true); });

  function currentInput() {
    if (override) return override;
    return { aim: pointerAim, focus: mouseFocus || keyFocus || focusPointers.size > 0 };
  }

  // ---------- Ablauf ----------
  function newSeed() { return FIXED_SEED != null ? FIXED_SEED + levelIdx : (Math.random() * 1e9) | 0; }

  function startLevel(i, seed) {
    levelIdx = i;
    levelSeed = seed != null ? seed : newSeed();
    world = createWorld(levelIdx, levelSeed);
    world.aim = pointerAim;
    particles = []; flashes = [];
    hintIdx = levelIdx === 0 ? 0 : HINTS.length; hintT = 0;
    state = 'play';
  }
  function startRun() { runScore = 0; startLevel(0); }
  function setPaused(p) { if (p && state === 'play') state = 'pause'; else if (!p && state === 'pause') state = 'play'; }

  function handleEvents() {
    for (const ev of world.events) {
      if (ev.type === 'spawn') playSfx('SFX-001');
      if (ev.type === 'dock') { playSfx('SFX-002'); burst(ev.x, ev.y, PAL.harbor, 14, 60); }
      if (ev.type === 'wreck') {
        playSfx('SFX-003');
        burst(ev.x, ev.y, '#c9a27a', 18, 90); burst(ev.x, ev.y, '#dfe8f0', 12, 50);
        flashes.push({ x: ev.x, y: ev.y, t: 0 });
        if (!reducedMotion) shake = 0.35;
      }
      if (ev.type === 'win') {
        runScore += world.score;
        playSfx('SFX-006');
        state = levelIdx === CFG.levels.length - 1 ? 'end' : 'win';
      }
      if (ev.type === 'lose') { playSfx('SFX-007'); state = 'lose'; }
    }
    world.events.length = 0;
  }

  function burst(x, y, color, n, speed) {
    for (let i = 0; i < n; i++) {
      const a = Math.random() * TAU, v = speed * (0.3 + Math.random() * 0.7);
      particles.push({ x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, life: 0.6 + Math.random() * 0.6, age: 0, color });
    }
  }

  // ---------- Tutorial-Hinweise (nur Nacht 1, GDD v1.0) ----------
  const HINTS = [
    { mouse: 'Zeige mit der Maus, wohin das Licht fällt', touch: 'Tippe und ziehe, um das Licht zu drehen', done: () => aimMoved > 1.2 },
    { mouse: 'Beleuchtete Schiffe finden durchs Riff', touch: 'Beleuchtete Schiffe finden durchs Riff', done: () => world.ships.some(s => s.guideT > 0), needsShip: true },
    { mouse: 'Maustaste halten: Fokus-Strahl für ferne Schiffe', touch: 'Fokus-Knopf halten: Strahl für ferne Schiffe', done: () => focusUsed }
  ];
  let hintIdx = HINTS.length, hintT = 0;
  function updateHints(dt) {
    if (hintIdx >= HINTS.length) return;
    const h = HINTS[hintIdx];
    if (h.needsShip && world.spawned === 0) return;
    hintT += dt;
    if ((hintT > 2.5 && h.done()) || hintT > 6) { hintIdx++; hintT = 0; }
  }

  // ---------- Audio (Synthese aus ARTs Parametern) ----------
  let actx = null, master = null, sfxBus = null, musicBus = null, humGain = null;
  let muted = false;
  function ensureAudio() {
    if (actx) { if (actx.state === 'suspended') actx.resume(); return; }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    actx = new AC();
    master = actx.createGain(); master.gain.value = muted ? 0 : 0.8; master.connect(actx.destination);
    sfxBus = actx.createGain(); sfxBus.gain.value = 0.9; sfxBus.connect(master);
    musicBus = actx.createGain(); musicBus.gain.value = 0.55; musicBus.connect(master);
    startLoops();
    startMusic();
  }
  function toggleMute() {
    muted = !muted;
    if (master) master.gain.setTargetAtTime(muted ? 0 : 0.8, actx.currentTime, 0.05);
  }

  let noiseBuf = null;
  function noiseBuffer() {
    if (noiseBuf) return noiseBuf;
    noiseBuf = actx.createBuffer(1, actx.sampleRate * 2, actx.sampleRate);
    const d = noiseBuf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    return noiseBuf;
  }
  function makeSource(wave, freq, loop) {
    if (wave === 'noise') {
      const s = actx.createBufferSource(); s.buffer = noiseBuffer(); s.loop = true; return s;
    }
    const o = actx.createOscillator(); o.type = wave; o.frequency.value = freq; return o;
  }
  function synthLayer(L, t0, out) {
    const t = t0 + (L.delay || 0), dur = L.dur || 0.2;
    const f = Array.isArray(L.freq) ? L.freq : [L.freq || 440, L.freq || 440];
    const src = makeSource(L.wave || 'sine', f[0]);
    if (src.frequency) {
      src.frequency.setValueAtTime(f[0], t);
      if (f[1] !== f[0]) src.frequency.exponentialRampToValueAtTime(Math.max(1, f[1]), t + dur);
      if (L.detune) src.detune.value = L.detune;
    }
    let node = src;
    if (L.filter) {
      const fl = actx.createBiquadFilter();
      fl.type = L.filter.type || 'lowpass';
      const ff = Array.isArray(L.filter.freq) ? L.filter.freq : [L.filter.freq, L.filter.freq];
      fl.frequency.setValueAtTime(ff[0], t);
      if (ff[1] !== ff[0]) fl.frequency.exponentialRampToValueAtTime(Math.max(1, ff[1]), t + dur);
      fl.Q.value = L.filter.q || 1;
      node.connect(fl); node = fl;
    }
    const g = actx.createGain();
    const peak = L.gain != null ? L.gain : 0.3, atk = L.attack || 0.005;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + atk);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    node.connect(g); g.connect(out);
    src.start(t); src.stop(t + dur + 0.05);
  }
  function playSfx(id) {
    if (!actx || muted) return;
    const spec = ASSETS && ASSETS.sfx && ASSETS.sfx[id];
    const t0 = actx.currentTime + 0.01;
    if (!spec) { synthLayer({ wave: 'square', freq: 660, dur: 0.08, gain: 0.08 }, t0, sfxBus); return; } // Platzhalter-Piep
    for (const L of spec.layers) synthLayer(L, t0, sfxBus);
  }
  function startLoops() {
    const loops = (ASSETS && ASSETS.loops) || {};
    for (const [id, L] of Object.entries(loops)) {
      const src = makeSource(L.wave, L.freq);
      let node = src;
      if (L.filter) { const fl = actx.createBiquadFilter(); fl.type = L.filter.type || 'lowpass'; fl.frequency.value = L.filter.freq; fl.Q.value = L.filter.q || 1; node.connect(fl); node = fl; }
      const g = actx.createGain(); g.gain.value = 0;
      node.connect(g); g.connect(sfxBus);
      if (L.lfo) {
        const lfo = actx.createOscillator(); lfo.frequency.value = L.lfo.rate;
        const lg = actx.createGain(); lg.gain.value = L.lfo.depth;
        lfo.connect(lg); lg.connect(g.gain); lfo.start();
      }
      src.start();
      if (L.trigger === 'focus') humGain = { g, peak: L.gain };
      else g.gain.setTargetAtTime(L.gain, actx.currentTime, 1.5);
    }
  }
  const NOTE = { C: 0, 'C#': 1, D: 2, 'D#': 3, E: 4, F: 5, 'F#': 6, G: 7, 'G#': 8, A: 9, 'A#': 10, B: 11 };
  function noteFreq(n) {
    const m = /^([A-G]#?)(\d)$/.exec(n);
    return 440 * Math.pow(2, (NOTE[m[1]] + (parseInt(m[2], 10) + 1) * 12 - 69) / 12);
  }
  function startMusic() {
    const M = ASSETS && ASSETS.music && ASSETS.music['MUS-001'];
    if (!M) return;
    const beat = 60 / M.bpm, chordLen = beat * M.beatsPerChord;
    let next = actx.currentTime + 0.2, idx = 0;
    const schedule = () => {
      while (next < actx.currentTime + 1.5) {
        const chord = M.chords[idx % M.chords.length];
        for (const n of chord) {
          synthLayer({ ...M.pad, freq: noteFreq(n), dur: chordLen + M.pad.release, delay: 0 }, next, musicBus);
          if (M.pad.detune) synthLayer({ ...M.pad, freq: noteFreq(n), dur: chordLen + M.pad.release, detune: M.pad.detune }, next, musicBus);
        }
        if (M.arp) {
          const steps = Math.floor(M.beatsPerChord / M.arp.every);
          for (let i = 0; i < steps; i++) {
            const n = chord[M.arp.pattern[i % M.arp.pattern.length] % chord.length];
            synthLayer({ ...M.arp, freq: noteFreq(n) * Math.pow(2, M.arp.octave || 0) }, next + i * beat * M.arp.every, musicBus);
          }
        }
        next += chordLen; idx++;
      }
    };
    schedule();
    setInterval(schedule, 400);
  }

  // ---------- Rendering-Hilfen ----------
  function circle(c, x, y, r) { c.beginPath(); c.arc(x, y, r, 0, TAU); }
  function wedge(c, x, y, a, half, range) { c.beginPath(); c.moveTo(x, y); c.arc(x, y, range, a - half, a + half); c.closePath(); }

  // Platzhalter, solange ART-Assets fehlen (Asset-Vertrag siehe TDD §4)
  const PLACEHOLDER = {
    'G-001': c => { c.fillStyle = PAL.sea; c.fillRect(0, 0, W, H); },
    'G-002': (c, x, y) => { c.fillStyle = '#6b5a3a'; circle(c, x, y, 32); c.fill(); },
    'G-003': (c, x, y) => { c.fillStyle = '#dddddd'; circle(c, x, y, 12); c.fill(); },
    'G-004': (c, x, y, a, half, range) => { c.globalAlpha = 0.18; c.fillStyle = '#ffff66'; wedge(c, x, y, a, half, range); c.fill(); },
    'G-006': (c, s) => {
      c.translate(s.x, s.y); c.rotate(s.heading);
      c.fillStyle = s.guided ? '#88ff88' : '#ffffff';
      c.beginPath(); c.moveTo(10, 0); c.lineTo(-7, -6); c.lineTo(-7, 6); c.closePath(); c.fill();
    },
    'G-008': (c, r) => { c.fillStyle = '#777777'; circle(c, r.x, r.y, r.r); c.fill(); },
    'G-009': (c, r) => { c.strokeStyle = 'rgba(200,200,200,0.35)'; circle(c, r.x, r.y, r.r); c.stroke(); },
    'G-010': (c, wr, age) => { c.globalAlpha = Math.max(0, 1 - age / 4); c.fillStyle = '#aa3333'; c.fillRect(wr.x - 5, wr.y - 5, 10, 10); },
    'G-011': (c, x, y, r) => { c.strokeStyle = PAL.harbor; c.setLineDash([4, 6]); circle(c, x, y, r); c.stroke(); },
    'G-012': (c, x, y, guided) => { c.fillStyle = guided ? '#88ff88' : '#ffbb44'; circle(c, x, y, 3); c.fill(); },
    'G-013': (c, x, y, w, h) => { c.fillStyle = PAL.panel; c.fillRect(x, y, w, h); },
    'G-014': (c, x, y, size, filled) => { c.fillStyle = filled ? PAL.accent : 'rgba(255,255,255,0.25)'; c.font = `${size}px ${PAL.font}`; c.textAlign = 'center'; c.fillText('★', x, y + size / 3); },
    'G-015': (c, x, y, r, active) => { c.fillStyle = active ? 'rgba(255,217,138,0.5)' : 'rgba(255,255,255,0.15)'; circle(c, x, y, r); c.fill(); c.fillStyle = PAL.ui; c.font = `14px ${PAL.font}`; c.textAlign = 'center'; c.fillText('FOKUS', x, y + 5); },
    'G-016': (c, name, x, y, r) => { c.fillStyle = 'rgba(255,255,255,0.2)'; circle(c, x, y, r); c.fill(); c.fillStyle = PAL.ui; c.font = `12px ${PAL.font}`; c.textAlign = 'center'; c.fillText(name === 'pause' ? 'II' : name === 'mute' ? 'x' : '♪', x, y + 4); }
  };
  function asset(id, ...args) {
    const f = (ASSETS && ASSETS.graphics && ASSETS.graphics[id]) || PLACEHOLDER[id];
    if (!f) return;
    ctx.save();
    f(ctx, ...args);
    ctx.restore();
  }

  function renderDarkness(w, b) {
    dctx.setTransform(1, 0, 0, 1, 0, 0);
    dctx.globalCompositeOperation = 'source-over';
    dctx.globalAlpha = 1;
    dctx.clearRect(0, 0, dark.width, dark.height);
    dctx.setTransform(k, 0, 0, k, 0, 0);
    dctx.fillStyle = PAL.darkness;
    dctx.fillRect(0, 0, W, H);
    dctx.globalCompositeOperation = 'destination-out';
    const g = dctx.createRadialGradient(CX, CY, 10, CX, CY, b.range);
    g.addColorStop(0, 'rgba(0,0,0,1)');
    g.addColorStop(0.75, 'rgba(0,0,0,0.92)');
    g.addColorStop(1, 'rgba(0,0,0,0)');
    for (const [m, a] of [[1.4, 0.3], [1.18, 0.5], [1, 1]]) {
      dctx.globalAlpha = a; dctx.fillStyle = g;
      wedge(dctx, CX, CY, b.angle, b.half * m, b.range); dctx.fill();
    }
    dctx.globalAlpha = 1;
    const hole = (x, y, r, a) => {
      const hg = dctx.createRadialGradient(x, y, 0, x, y, r);
      hg.addColorStop(0, `rgba(0,0,0,${a})`); hg.addColorStop(1, 'rgba(0,0,0,0)');
      dctx.fillStyle = hg; circle(dctx, x, y, r); dctx.fill();
    };
    hole(CX, CY, 78, 1);
    if (w) for (const s of w.ships) hole(s.x, s.y, s.guideT > 0 ? 26 : 18, 0.85);
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(dark, 0, 0);
    ctx.restore();
  }

  function shipView(s) {
    return { x: s.x, y: s.y, heading: s.heading, guided: s.guideT > 0, lit: s.lit, guideFrac: s.guideT / P('P-05'), id: s.id };
  }

  function renderScene(w, b, t) {
    asset('G-001', t, W, H);
    asset('G-011', CX, CY, P('P-11'), t);
    for (const r of w.rocks) asset('G-008', r, t);
    for (const s of w.ships) asset('G-006', shipView(s), t);
    asset('G-002', CX, CY, t);
    asset('G-003', CX, CY, b.angle, t);
    renderDarkness(w, b);
    for (const r of w.rocks) asset('G-009', r, t);
    for (const wr of w.wrecks) { const age = w.t - wr.t; if (age < 4) asset('G-010', wr, age); }
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    asset('G-004', CX, CY, b.angle, b.half, b.range, w.focus);
    for (const s of w.ships) asset('G-012', s.x, s.y, s.guideT > 0, t, s.guideT / P('P-05'));
    ctx.restore();
    if (w.levelIdx === 2) asset('G-017', t, 1);
    for (const p of particles) {
      ctx.globalAlpha = Math.max(0, 1 - p.age / p.life);
      ctx.fillStyle = p.color;
      ctx.fillRect(p.x - 1.5, p.y - 1.5, 3, 3);
    }
    ctx.globalAlpha = 1;
    for (const f of flashes) {
      ctx.strokeStyle = PAL.danger;
      ctx.globalAlpha = Math.max(0, 1 - f.t);
      ctx.lineWidth = 2;
      circle(ctx, f.x, f.y, 10 + f.t * 30); ctx.stroke();
    }
    ctx.globalAlpha = 1;
    if (DEBUG) {
      ctx.strokeStyle = 'rgba(255,0,255,0.6)';
      for (const r of w.rocks) { circle(ctx, r.x, r.y, r.r); ctx.stroke(); }
      for (const s of w.ships) { circle(ctx, s.x, s.y, SHIP_R); ctx.stroke(); }
      circle(ctx, CX, CY, w.R + 40); ctx.stroke();
    }
  }

  function text(str, x, y, size, color, align = 'center', weight = 400) {
    ctx.font = `${weight} ${size}px ${PAL.font}`;
    ctx.textAlign = align;
    ctx.fillStyle = color;
    ctx.fillText(str, x, y);
  }

  function button(label, x, y, w, h, action, primary) {
    buttons.push({ x, y, w, h, action });
    ctx.fillStyle = primary ? PAL.accent : 'rgba(255,255,255,0.14)';
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(x, y, w, h, 10); else ctx.rect(x, y, w, h);
    ctx.fill();
    text(label, x + w / 2, y + h / 2 + 6, 17, primary ? '#1a1206' : PAL.ui, 'center', 600);
  }

  function renderHUD(w) {
    text(`Nacht ${w.levelIdx + 1} · ${w.L.name}`, 20, 34, 19, PAL.ui, 'left', 600);
    text(`Angelegt ${w.docked}/${w.L.ships}   Wracks ${w.wrecked}/${P('P-10')}   Punkte ${runScore + w.score}`, 20, 58, 15, PAL.uiDim, 'left');
    asset('G-016', 'pause', pauseBtn.x, pauseBtn.y, pauseBtn.r);
    if (touchUsed) asset('G-015', focusBtn.x, focusBtn.y, focusBtn.r, focusPointers.size > 0);
    if (hintIdx < HINTS.length && !(HINTS[hintIdx].needsShip && w.spawned === 0)) {
      const h = HINTS[hintIdx];
      const a = Math.min(1, hintT * 2, (6 - hintT) * 2);
      ctx.globalAlpha = Math.max(0, a);
      text(touchUsed ? h.touch : h.mouse, CX, H - 28, 18, PAL.ui);
      ctx.globalAlpha = 1;
    }
  }

  function panel(title, lines, h = 250) {
    const pw = 440, px = CX - pw / 2, py = CY - h / 2;
    asset('G-013', px, py, pw, h);
    text(title, CX, py + 50, 28, PAL.ui, 'center', 700);
    lines.forEach((l, i) => text(l, CX, py + 88 + i * 26, 16, PAL.uiDim));
    return { px, py, pw, h };
  }

  function render() {
    buttons = [];
    ctx.setTransform(k, 0, 0, k, 0, 0);
    if (shake > 0) ctx.translate((Math.random() - 0.5) * 6 * shake, (Math.random() - 0.5) * 6 * shake);

    if (state === 'title') {
      const b = { angle: titleAim, half: rad(P('P-01')), range: P('P-02') + 60 };
      renderScene(demoWorld, b, clock);
      text('NACHTWACHE', CX, 150, 64, PAL.ui, 'center', 800);
      text('Lotse die Schiffe mit deinem Licht sicher durchs Riff.', CX, 188, 18, PAL.uiDim);
      text(touchUsed ? 'Tippen zum Starten' : 'Klicken zum Starten', CX, H - 92, 22, PAL.accent, 'center', 600);
      text('Maus: Licht drehen · Maustaste/Leertaste: Fokus · P: Pause · M: Ton', CX, H - 56, 14, PAL.uiDim);
      asset('G-016', muted ? 'mute' : 'sound', soundBtn.x, soundBtn.y, soundBtn.r);
      if (DEBUG) text(VERSION, W - 12, H - 12, 12, PAL.uiDim, 'right');
      return;
    }

    const w = world;
    renderScene(w, beam(w), clock);
    renderHUD(w);
    asset('G-016', muted ? 'mute' : 'sound', soundBtn.x, soundBtn.y, soundBtn.r);

    if (state === 'pause') {
      ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.fillRect(0, 0, W, H);
      const p = panel('Pause', ['Die Schiffe warten auf dein Licht.'], 220);
      button('Weiter', p.px + 40, p.py + 130, 170, 48, () => setPaused(false), true);
      button('Nacht neu', p.px + 230, p.py + 130, 170, 48, () => startLevel(levelIdx, levelSeed));
    } else if (state === 'win' || state === 'end') {
      const last = state === 'end';
      const p = panel(last ? 'Alle Nächte geschafft!' : `Nacht ${levelIdx + 1} geschafft`, [
        `Angelegt ${w.docked} · Wracks ${w.wrecked}`,
        last ? `Gesamtpunktzahl: ${runScore}` : `Punkte bisher: ${runScore}`
      ], 280);
      for (let i = 0; i < 3; i++) asset('G-014', CX - 50 + i * 50, p.py + 162, 36, i < w.stars);
      if (last) button('Zum Titel', CX - 100, p.py + 200, 200, 48, () => { state = 'title'; }, true);
      else button('Nächste Nacht', CX - 100, p.py + 200, 200, 48, () => startLevel(levelIdx + 1), true);
    } else if (state === 'lose') {
      const p = panel('Das Riff war stärker', [`${w.wrecked} Schiffe sind gesunken.`, `Angelegt: ${w.docked} von ${w.L.ships}`], 230);
      button('Nacht wiederholen', p.px + 30, p.py + 150, 200, 48, () => startLevel(levelIdx, levelSeed), true);
      button('Titel', p.px + 250, p.py + 150, 160, 48, () => { state = 'title'; });
    }
  }

  // ---------- Hauptschleife (feste Zeitschritte) ----------
  function tick(dt) {
    clock += dt;
    if (state === 'title') titleAim = angNorm(titleAim + dt * 0.5);
    if (state === 'play') {
      const inp = currentInput();
      if (inp.focus) focusUsed = true;
      stepWorld(world, dt, inp);
      handleEvents();
      updateHints(dt);
    }
    if (state !== 'pause') {
      for (const p of particles) { p.x += p.vx * dt; p.y += p.vy * dt; p.vx *= 0.96; p.vy *= 0.96; p.age += dt; }
      particles = particles.filter(p => p.age < p.life);
      for (const f of flashes) f.t += dt;
      flashes = flashes.filter(f => f.t < 1);
      shake = Math.max(0, shake - dt);
    }
    if (humGain && actx) {
      const f = state === 'play' && world ? world.focus : 0;
      humGain.g.gain.setTargetAtTime(f * humGain.peak, actx.currentTime, 0.05);
    }
  }

  let last = performance.now(), acc = 0;
  function frame(now) {
    acc += Math.min(0.1, (now - last) / 1000);
    last = now;
    while (acc >= DT) { tick(DT); acc -= DT; }
    render();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  if (params.has('autostart')) startLevel(parseInt(params.get('level') || '0', 10), FIXED_SEED != null ? FIXED_SEED : undefined);

  window.__nachtwache = {
    version: VERSION,
    constants: { W, H, CX, CY, SHIP_R, DT },
    createWorld, stepWorld, beam, isLit, simulate,
    live: {
      get state() { return state; },
      get world() { return world; },
      get muted() { return muted; },
      start: (level, seed) => startLevel(level, seed),
      setOverride: o => { override = o; },
      tick: n => { for (let i = 0; i < n; i++) tick(DT); render(); }
    }
  };
})();
