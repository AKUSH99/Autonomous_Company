// DEV · „Material für Marketing" aus dem RC-Build: echte Screenshots ausgewählter Spielszenen.
// Eine einfache Lotsen-Automatik steuert den Kegel, damit die Szenen typisches Spiel zeigen.
// Aufruf: NODE_PATH=$(npm root -g) node tools/screenshots.js
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const outDir = path.join(__dirname, '../marketing/screenshots');
fs.mkdirSync(outDir, { recursive: true });
const url = 'file://' + path.resolve(__dirname, '../game/index.html');

const scenes = [
  { file: '01_titel.png', query: '?seed=7', setup: null },
  { file: '02_nacht1_lotsen.png', query: '?seed=4&autostart=1&level=0', seconds: 11, focus: false },
  { file: '03_nacht2_jonglieren.png', query: '?seed=12&autostart=1&level=1', seconds: 34, focus: false },
  { file: '04_nacht3_sturm.png', query: '?seed=21&autostart=1&level=2', seconds: 26, focus: true }
];

(async () => {
  const browser = await chromium.launch();
  for (const sc of scenes) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
    await page.goto(url + sc.query);
    await page.waitForTimeout(400);
    if (sc.seconds) {
      await page.evaluate(({ seconds, focus }) => {
        const L = window.__nachtwache.live, { CX, CY } = window.__nachtwache.constants;
        let aim = -Math.PI / 2;
        for (let f = 0; f < seconds * 60; f++) {
          const w = L.world;
          const lost = w.ships.filter(s => !s.inside).sort((a, b) => a.guideT - b.guideT || Math.hypot(a.x - CX, a.y - CY) - Math.hypot(b.x - CX, b.y - CY));
          const t = lost[0];
          if (t) {
            const want = Math.atan2(t.y - CY, t.x - CX);
            let d = want - aim; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI;
            aim += Math.max(-0.12, Math.min(0.12, d));
          }
          const far = t && Math.hypot(t.x - CX, t.y - CY) > 250;
          L.setOverride({ aim, focus: focus && far });
          L.tick(1);
        }
      }, sc);
    }
    await page.screenshot({ path: path.join(outDir, sc.file) });
    console.log('✓', sc.file);
    await page.close();
  }

  // Nacht-geschafft-Screen mit Sternen (echter Durchlauf von Nacht 1 mit Automatik)
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  await page.goto(url + '?seed=4&autostart=1&level=0');
  await page.waitForTimeout(300);
  const result = await page.evaluate(() => {
    const L = window.__nachtwache.live, { CX, CY } = window.__nachtwache.constants;
    let aim = -Math.PI / 2, frames = 0;
    while (L.state === 'play' && frames++ < 60 * 300) {
      const w = L.world;
      const t = w.ships.filter(s => !s.inside).sort((a, b) => a.guideT - b.guideT)[0];
      if (t) {
        const want = Math.atan2(t.y - CY, t.x - CX);
        let d = want - aim; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI;
        aim += Math.max(-0.12, Math.min(0.12, d));
      }
      L.setOverride({ aim, focus: false });
      L.tick(1);
    }
    for (let i = 0; i < 30; i++) L.tick(1);
    return L.state;
  });
  await page.screenshot({ path: path.join(outDir, '05_nacht_geschafft.png') });
  console.log('✓ 05_nacht_geschafft.png', result);
  await browser.close();
})();
