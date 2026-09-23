// QA · Balancing- und Akzeptanztest (Modus A – echte Spiellogik im Headless-Chromium, Zeitraffer)
// Misst mit drei Bot-Personas die Fehlschlagquote und Dauer je Nacht (AC-08, AC-09),
// prüft AC-04 (durchgehend beleuchtetes Schiff) und vermisst die Riff-Durchfahrten gegen das GDD.
// Aufruf: NODE_PATH=$(npm root -g) node qa/balance_test.js [label] [seeds]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const label = process.argv[2] || 'balance';
const SEEDS = parseInt(process.argv[3] || '40', 10);
const outDir = path.join(__dirname, 'results');
fs.mkdirSync(outDir, { recursive: true });
const url = 'file://' + path.resolve(__dirname, '../game/index.html');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(url);
  await page.waitForFunction(() => !!window.__nachtwache);

  const results = await page.evaluate((SEEDS) => {
    const NW = window.__nachtwache;
    const { CX, CY, SHIP_R, DT } = NW.constants;
    const CFG = window.BALANCING;
    const rad = d => d * Math.PI / 180;
    const mulberry = seed => { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
    const turnToward = (aim, want, maxStep, angDiff) => aim + Math.max(-maxStep, Math.min(maxStep, angDiff(want, aim)));

    // Persona 1: kein Input – der Kegel bleibt, wo er beim Start steht
    const idle = () => () => null;

    // Persona 2: Casual-Erstspieler – träge Reaktion (0,6–0,9 s), ±8° Zielfehler,
    // nimmt das Schiff, das der Insel am nächsten ist, vergisst den Fokus manchmal, 10 % Unaufmerksamkeit
    const casual = seed => {
      const rnd = mulberry(seed * 7919);
      let target = null, next = 0, aim = -Math.PI / 2, focus = false, noise = 0;
      return (w, api) => {
        if (w.t >= next) {
          next = w.t + 0.6 + rnd() * 0.3;
          if (rnd() > 0.1) {
            let best = null, bs = Infinity;
            for (const s of w.ships) {
              if (s.inside && s.guideT > 0) continue;
              const score = Math.hypot(s.x - CX, s.y - CY) + (s.guideT > 0.8 ? 200 : 0);
              if (score < bs) { bs = score; best = s; }
            }
            target = best ? best.id : null;
            noise = (rnd() * 2 - 1) * rad(8);
            focus = !!best && Math.hypot(best.x - CX, best.y - CY) > api.P('P-02') && rnd() < 0.6;
          }
        }
        const t = w.ships.find(s => s.id === target);
        if (t) aim = turnToward(aim, Math.atan2(t.y - CY, t.x - CX) + noise, 5 * DT, api.angDiff);
        return { aim, focus };
      };
    };

    // Persona 3: Erfahrene Spielerin – schätzt, welches verlorene Schiff zuerst aufs Riff trifft,
    // hält das Licht auf dem geführten Schiff, bis es durch die Durchfahrt ist, nutzt Fokus gezielt
    const expert = seed => {
      const rnd = mulberry(seed * 104729);
      let target = null, next = 0, aim = -Math.PI / 2, focus = false, noise = 0;
      const timeToRock = (w, s, speed) => {
        for (let t = 0.25; t <= 10; t += 0.25) {
          const x = s.x + Math.cos(s.heading) * speed * t, y = s.y + Math.sin(s.heading) * speed * t;
          for (const k of w.rocks) if (Math.hypot(x - k.x, y - k.y) < k.r + SHIP_R + 2) return t;
        }
        return 10;
      };
      return (w, api) => {
        if (w.t >= next) {
          next = w.t + 0.25;
          const dark = api.P('P-07') * w.L.speedMul;
          const cur = w.ships.find(s => s.id === target);
          let best = null, bu = Infinity;
          for (const s of w.ships) {
            if (s.inside) continue;
            const u = s.guideT > 0 ? s.guideT + 2.5 : timeToRock(w, s, dark);
            if (u < bu) { bu = u; best = s; }
          }
          const keep = cur && !cur.inside && cur.guideT > 0 && bu > 1.5;
          if (!keep) target = best ? best.id : null;
          noise = (rnd() * 2 - 1) * rad(3);
          const t = w.ships.find(s => s.id === target);
          focus = !!t && Math.hypot(t.x - CX, t.y - CY) > api.P('P-02') - 10;
        }
        const t = w.ships.find(s => s.id === target);
        if (t) aim = turnToward(aim, Math.atan2(t.y - CY, t.x - CX) + noise, 8 * DT, api.angDiff);
        return { aim, focus };
      };
    };

    const personas = { idle, casual, expert };
    const out = { balance: {}, ac04: {}, gaps: {}, config: JSON.parse(JSON.stringify(CFG)) };
    const t0 = performance.now();

    for (let lv = 0; lv < CFG.levels.length; lv++) {
      out.balance[CFG.levels[lv].id] = {};
      for (const [name, make] of Object.entries(personas)) {
        const runs = [];
        for (let s = 1; s <= SEEDS; s++) runs.push(NW.simulate({ seed: s, level: lv, bot: make(s) }));
        const wins = runs.filter(r => r.result === 'win');
        const avg = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : null;
        out.balance[CFG.levels[lv].id][name] = {
          runs: runs.length,
          failRate: +(1 - wins.length / runs.length).toFixed(3),
          avgDurationWin: wins.length ? +avg(wins.map(r => r.time)).toFixed(1) : null,
          avgDurationAll: +avg(runs.map(r => r.time)).toFixed(1),
          avgDocked: +avg(runs.map(r => r.docked)).toFixed(2),
          avgWrecked: +avg(runs.map(r => r.wrecked)).toFixed(2),
          timeouts: runs.filter(r => r.result === 'play').length
        };
      }
    }

    // AC-04: Immer nur ein Schiff, Licht mit Fokus exakt darauf – jedes Wrack ist ein Verstoß
    for (let lv = 0; lv < CFG.levels.length; lv++) {
      let ships = 0, wrecks = 0; const failSeeds = [];
      for (let s = 1; s <= SEEDS; s++) {
        const w = NW.createWorld(lv, s);
        w.L = Object.assign({}, w.L, { maxActive: 1 });
        while (w.status === 'play' && w.t < 900) {
          const sh = w.ships[0];
          NW.stepWorld(w, DT, sh ? { aim: Math.atan2(sh.y - CY, sh.x - CX), focus: true } : { aim: w.aim, focus: true });
          w.events.length = 0;
        }
        ships += w.docked + w.wrecked; wrecks += w.wrecked;
        if (w.wrecked) failSeeds.push(s);
      }
      out.ac04[CFG.levels[lv].id] = { ships, wrecks, successRate: +(1 - wrecks / ships).toFixed(3), failSeeds: failSeeds.slice(0, 10) };
    }

    // Geometrie: lichte Breite der Durchfahrten gegen gapWidth aus dem GDD
    for (let lv = 0; lv < CFG.levels.length; lv++) {
      const widths = [];
      for (let s = 1; s <= SEEDS; s++) {
        const w = NW.createWorld(lv, s);
        for (const g of w.gaps) {
          let left = Infinity, right = Infinity;
          for (const k of w.rocks.filter(r => r.reef)) {
            const a = Math.atan2(k.y - CY, k.x - CX);
            const d = NW.angDiff ? 0 : 0; // Platzhalter, falls API erweitert wird
            let dd = a - g; while (dd > Math.PI) dd -= 2 * Math.PI; while (dd < -Math.PI) dd += 2 * Math.PI;
            if (Math.abs(dd) > Math.PI / 2) continue;
            const r = Math.hypot(k.x - CX, k.y - CY);
            const lat = r * Math.sin(Math.abs(dd)) - k.r;
            if (dd > 0) left = Math.min(left, lat); else right = Math.min(right, lat);
          }
          widths.push(left + right);
        }
      }
      const avg = widths.reduce((a, b) => a + b, 0) / widths.length;
      out.gaps[CFG.levels[lv].id] = { spec: CFG.levels[lv].gapWidth, measuredAvg: +avg.toFixed(1), min: +Math.min(...widths).toFixed(1), max: +Math.max(...widths).toFixed(1) };
    }

    out.runtimeMs = Math.round(performance.now() - t0);
    return out;
  }, SEEDS);

  results.label = label; results.seeds = SEEDS; results.date = new Date().toISOString(); results.pageErrors = errors;
  fs.writeFileSync(path.join(outDir, `${label}.json`), JSON.stringify(results, null, 2));

  const pct = v => (v * 100).toFixed(0).padStart(3) + ' %';
  console.log(`\nBalancing (${SEEDS} Seeds je Nacht und Persona, Laufzeit ${results.runtimeMs} ms)`);
  console.log('Nacht  Persona  Fehlschlag  Ø Dauer (Sieg)  Ø angelegt  Ø Wracks');
  for (const [lv, per] of Object.entries(results.balance))
    for (const [p, r] of Object.entries(per))
      console.log(`${lv}  ${p.padEnd(7)}  ${pct(r.failRate)}       ${r.avgDurationWin == null ? '   –  ' : (r.avgDurationWin + ' s').padStart(7)}        ${String(r.avgDocked).padStart(5)}      ${r.avgWrecked}${r.timeouts ? '  TIMEOUTS:' + r.timeouts : ''}`);
  console.log('\nAC-04 (durchgehend beleuchtet):');
  for (const [lv, r] of Object.entries(results.ac04)) console.log(`${lv}  ${r.wrecks}/${r.ships} Wracks  Erfolg ${pct(r.successRate)}  ${r.failSeeds.length ? 'Seeds: ' + r.failSeeds.join(',') : ''}`);
  console.log('\nDurchfahrten (lichte Breite):');
  for (const [lv, r] of Object.entries(results.gaps)) console.log(`${lv}  Soll ${r.spec} px  Ist Ø ${r.measuredAvg} px (min ${r.min}, max ${r.max})`);
  if (errors.length) console.log('Seitenfehler:', errors);
  await browser.close();
})();
