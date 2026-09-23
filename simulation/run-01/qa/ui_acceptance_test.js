// QA · UI-Akzeptanztest (Modus A, synthetische Eingaben im Headless-Chromium)
// AC-01 Reaktionszeit · AC-11 Touch · AC-12 Audio erst nach Interaktion · AC-13 Felsen im Dunkeln erkennbar
// Aufruf: NODE_PATH=$(npm root -g) node qa/ui_acceptance_test.js [label]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const label = process.argv[2] || 'ui';
const outDir = path.join(__dirname, 'results');
fs.mkdirSync(outDir, { recursive: true });
const url = 'file://' + path.resolve(__dirname, '../game/index.html');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 960, height: 540 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.addInitScript(() => {
    window.__acCount = 0;
    const Orig = window.AudioContext;
    if (Orig) window.AudioContext = class extends Orig { constructor(...a) { super(...a); window.__acCount++; } };
  });
  const checks = [];
  const check = (id, desc, ok, detail = '', confidence = 'hoch') => checks.push({ id, desc, ok, detail, confidence });

  await page.goto(url + '?seed=3');
  await page.waitForTimeout(500);
  const acBefore = await page.evaluate(() => window.__acCount);

  // Touch-Start (synthetische PointerEvents mit pointerType „touch")
  const touch = (type, x, y, id) => page.evaluate(({ type, x, y, id }) => {
    const c = document.getElementById('game'), r = c.getBoundingClientRect();
    c.dispatchEvent(new PointerEvent(type, { pointerId: id, pointerType: 'touch', isPrimary: id === 1, clientX: r.left + x / 960 * r.width, clientY: r.top + y / 540 * r.height, pressure: type === 'pointerup' ? 0 : 0.5, bubbles: true, cancelable: true }));
  }, { type, x, y, id });
  await touch('pointerdown', 480, 300, 1); await touch('pointerup', 480, 300, 1);
  await page.waitForTimeout(150);
  const acAfter = await page.evaluate(() => window.__acCount);
  check('AC-12a', 'Kein AudioContext vor der ersten Interaktion', acBefore === 0, `vorher=${acBefore}`);
  check('AC-12b', 'AudioContext nach der ersten Interaktion', acAfter === 1, `nachher=${acAfter}`);
  const st = await page.evaluate(() => window.__nachtwache.live.state);
  check('AC-11a', 'Tippen startet das Spiel', st === 'play', `state=${st}`);

  // AC-11: Finger dreht den Kegel
  await touch('pointerdown', 480 + 150, 270 + 150, 2);
  await touch('pointermove', 480 - 150, 270 + 150, 2);
  await page.waitForTimeout(60);
  const aim = await page.evaluate(() => window.__nachtwache.live.world.aim);
  const want = Math.atan2(150, -150);
  check('AC-11b', 'Ziehen mit dem Finger dreht den Kegel', Math.abs(Math.atan2(Math.sin(aim - want), Math.cos(aim - want))) < 0.05, `aim=${aim.toFixed(2)} soll=${want.toFixed(2)}`, 'mittel');

  // AC-11: Fokus-Button per zweitem Finger, erster Finger zielt weiter
  await touch('pointerdown', 960 - 78, 540 - 78, 3);
  await page.waitForTimeout(350);
  const focusOn = await page.evaluate(() => window.__nachtwache.live.world.focus);
  await touch('pointerup', 960 - 78, 540 - 78, 3);
  await page.waitForTimeout(350);
  const focusOff = await page.evaluate(() => window.__nachtwache.live.world.focus);
  check('AC-11c', 'Fokus-Button per Touch (Multi-Touch)', focusOn > 0.95 && focusOff < 0.05, `an=${focusOn.toFixed(2)} aus=${focusOff.toFixed(2)}`, 'mittel');
  await touch('pointerup', 480 - 150, 270 + 150, 2);

  // AC-01: Kegel folgt dem Zeiger innerhalb eines Frames
  await page.mouse.move(480, 100);
  await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
  const aim2 = await page.evaluate(() => window.__nachtwache.live.world.aim);
  check('AC-01', 'Kegel folgt dem Zeiger innerhalb eines Frames', Math.abs(aim2 - Math.atan2(100 - 270, 0)) < 0.02, `aim=${aim2.toFixed(3)}`);

  // AC-12: Stummschalten (QA-Skriptfix T11: Zustand vor/nach Taste M vergleichen statt nur Existenz prüfen)
  const mutedExposed = await page.evaluate(() => 'muted' in window.__nachtwache.live);
  if (mutedExposed) {
    const m0 = await page.evaluate(() => window.__nachtwache.live.muted);
    await page.keyboard.press('KeyM');
    const m1 = await page.evaluate(() => window.__nachtwache.live.muted);
    await page.keyboard.press('KeyM');
    const m2 = await page.evaluate(() => window.__nachtwache.live.muted);
    check('AC-12c', 'Taste M schaltet den Ton stumm und wieder an', m0 === false && m1 === true && m2 === false, `${m0}→${m1}→${m2}`);
  } else {
    await page.keyboard.press('KeyM');
    check('AC-12c', 'Taste M schaltet den Ton stumm', 'teilweise', 'Taste ohne Fehler; Zustand über Debug-API nicht auslesbar', 'niedrig');
  }

  // AC-13: Felsen im Dunkeln erkennbar – Helligkeit rund um einen unbeleuchteten Felsen vs. offenes Meer
  const ac13 = await page.evaluate(() => {
    const L = window.__nachtwache.live;
    L.start(0, 3);
    L.setOverride({ aim: 0, focus: false });
    L.tick(2);
    const w = L.world, c = document.getElementById('game'), g = c.getContext('2d');
    const k = c.width / 960;
    const lum = (x, y, s) => {
      const d = g.getImageData(Math.round((x - s) * k), Math.round((y - s) * k), Math.round(2 * s * k), Math.round(2 * s * k)).data;
      let m = 0; for (let i = 0; i < d.length; i += 4) m = Math.max(m, 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2]);
      return m;
    };
    const rock = w.rocks.find(r => r.reef && Math.abs(Math.atan2(r.y - 270, r.x - 480)) > 2.2);
    const rockLum = lum(rock.x, rock.y, rock.r * 1.3);
    const seaLum = lum(160, 470, 14);
    L.setOverride(null);
    return { rockLum: Math.round(rockLum), seaLum: Math.round(seaLum) };
  });
  check('AC-13', 'Unbeleuchtete Felsen heben sich vom dunklen Meer ab', ac13.rockLum > ac13.seaLum + 25, `Fels max. Luminanz ${ac13.rockLum} vs. Meer ${ac13.seaLum}`, 'mittel');

  check('UI-ERR', 'Keine JavaScript-Laufzeitfehler', errors.length === 0, errors.join(' | '));
  fs.writeFileSync(path.join(outDir, `${label}.json`), JSON.stringify({ label, date: new Date().toISOString(), checks, errors }, null, 2));
  for (const c of checks) console.log(`${c.ok === true ? '✅' : c.ok === 'teilweise' ? '⚠️' : '❌'} ${c.id} ${c.desc}  (${c.detail}${c.detail ? ', ' : ''}Konfidenz ${c.confidence})`);
  await browser.close();
})();
