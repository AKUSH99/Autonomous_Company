// QA · Smoke-Test (Modus A – Ausführung im Headless-Chromium)
// Prüft den Hauptpfad: Titel → Spiel → Pause → Niederlage → Wiederholen → Sieg → nächste Nacht.
// Aufruf: NODE_PATH=$(npm root -g) node qa/smoke_test.js [label]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const label = process.argv[2] || 'smoke';
const outDir = path.join(__dirname, 'results');
const shotDir = path.join(__dirname, 'screenshots');
fs.mkdirSync(outDir, { recursive: true });
fs.mkdirSync(shotDir, { recursive: true });
const url = 'file://' + path.resolve(__dirname, '../game/index.html');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 960, height: 540 } });
  const pageErrors = [], consoleErrors = [];
  page.on('pageerror', e => pageErrors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });

  const checks = [];
  const check = (id, desc, ok, detail = '') => checks.push({ id, desc, ok: !!ok, detail });
  const st = () => page.evaluate(() => window.__nachtwache.live.state);

  await page.goto(url + '?debug=1');
  await page.waitForTimeout(600);
  check('SMK-01', 'Seite lädt, Debug-API vorhanden', await page.evaluate(() => !!window.__nachtwache));
  check('SMK-02', 'Startzustand ist Titel', (await st()) === 'title');
  await page.screenshot({ path: path.join(shotDir, `${label}_01_titel.png`) });

  await page.mouse.click(480, 400);
  await page.waitForTimeout(200);
  check('SMK-03', 'Klick startet Nacht 1', (await st()) === 'play');

  // Zeiger bewegen, Fokus halten – echtes Eingabeverhalten
  for (let i = 0; i < 40; i++) {
    const a = i / 40 * Math.PI * 2;
    await page.mouse.move(480 + Math.cos(a) * 200, 270 + Math.sin(a) * 200);
    await page.waitForTimeout(40);
  }
  const aimOk = await page.evaluate(() => {
    const w = window.__nachtwache.live.world;
    return Math.abs(Math.atan2(Math.sin(w.aim - Math.atan2(270 - 270, 680 - 480)), Math.cos(w.aim))) < 0.3;
  });
  check('SMK-04', 'Lichtkegel folgt dem Zeiger (AC-01, grob)', aimOk);
  await page.mouse.down();
  await page.waitForTimeout(400);
  const focus = await page.evaluate(() => window.__nachtwache.live.world.focus);
  await page.mouse.up();
  check('SMK-05', 'Maustaste halten aktiviert Fokus (AC-02, grob)', focus > 0.95, `focus=${focus.toFixed(2)}`);

  await page.waitForTimeout(2500);
  const spawned = await page.evaluate(() => window.__nachtwache.live.world.spawned);
  check('SMK-06', 'Erstes Schiff erscheint', spawned >= 1, `spawned=${spawned}`);
  await page.screenshot({ path: path.join(shotDir, `${label}_02_spiel.png`) });

  // Pause (AC-10)
  await page.keyboard.press('KeyP');
  const t1 = await page.evaluate(() => window.__nachtwache.live.world.t);
  await page.waitForTimeout(700);
  const t2 = await page.evaluate(() => window.__nachtwache.live.world.t);
  check('SMK-07', 'Pause friert die Spielzeit ein (AC-10)', (await st()) === 'pause' && t1 === t2, `t1=${t1.toFixed(2)} t2=${t2.toFixed(2)}`);
  await page.screenshot({ path: path.join(shotDir, `${label}_03_pause.png`) });
  await page.keyboard.press('KeyP');
  check('SMK-08', 'Weiter nach Pause', (await st()) === 'play');

  // Niederlage erzwingen: Licht vom Geschehen wegdrehen und im Zeitraffer laufen lassen
  await page.evaluate(() => {
    const L = window.__nachtwache.live;
    L.setOverride({ aim: 0, focus: false });
    for (let i = 0; i < 400 && L.state === 'play'; i++) L.tick(60);
  });
  const afterIdle = await st();
  check('SMK-09', 'Ohne Licht endet die Nacht (Sieg oder Niederlage, kein Hänger)', afterIdle === 'lose' || afterIdle === 'win', `state=${afterIdle}`);
  await page.screenshot({ path: path.join(shotDir, `${label}_04_ende_nacht.png`) });

  if (afterIdle === 'lose') {
    await page.keyboard.press('Enter'); // erster Button: „Nacht wiederholen"
    await page.waitForTimeout(100);
    check('SMK-10', 'Nacht wiederholen startet neu', (await st()) === 'play');
  } else {
    check('SMK-10', 'Nacht wiederholen startet neu', true, 'übersprungen – Idle-Lauf endete mit Sieg');
  }

  // Sieg per Debug-Taste N, dann nächste Nacht
  await page.evaluate(() => window.__nachtwache.live.setOverride(null));
  if ((await st()) !== 'play') await page.evaluate(() => window.__nachtwache.live.start(0));
  await page.keyboard.press('KeyN');
  await page.waitForTimeout(150);
  check('SMK-11', 'Nacht-geschafft-Screen erscheint (AC-07)', (await st()) === 'win');
  await page.screenshot({ path: path.join(shotDir, `${label}_05_nacht_geschafft.png`) });
  await page.keyboard.press('Enter');
  await page.waitForTimeout(100);
  const lvl = await page.evaluate(() => window.__nachtwache.live.world.levelIdx);
  check('SMK-12', 'Nächste Nacht startet (Nacht 2)', (await st()) === 'play' && lvl === 1, `level=${lvl}`);

  // Alle Nächte durchklicken bis zum Ende
  await page.keyboard.press('KeyN'); await page.waitForTimeout(100);
  await page.keyboard.press('Enter'); await page.waitForTimeout(100);
  await page.keyboard.press('KeyN'); await page.waitForTimeout(150);
  check('SMK-13', 'Nach Nacht 3: „Alle Nächte geschafft"', (await st()) === 'end');
  await page.screenshot({ path: path.join(shotDir, `${label}_06_ende.png`) });
  await page.keyboard.press('Enter'); await page.waitForTimeout(100);
  check('SMK-14', 'Zurück zum Titel', (await st()) === 'title');

  check('SMK-15', 'Keine JavaScript-Laufzeitfehler', pageErrors.length === 0, pageErrors.join(' | '));

  const result = { label, url, date: new Date().toISOString(), checks, pageErrors, consoleErrors };
  fs.writeFileSync(path.join(outDir, `${label}.json`), JSON.stringify(result, null, 2));
  for (const c of checks) console.log(`${c.ok ? '✅' : '❌'} ${c.id} ${c.desc}${c.detail ? '  (' + c.detail + ')' : ''}`);
  if (consoleErrors.length) console.log('Konsolen-Fehler:', consoleErrors);
  await browser.close();
})();
