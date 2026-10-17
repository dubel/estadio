// Regresja fizyki trybu Spacer: uruchamia Vite + headless Chrome i sprawdza
// grawitację, skok oraz chodzenie po stopniach trybun.
// Użycie: npm run test:physics
import puppeteer from 'puppeteer-core';
import { createServer } from 'vite';
import fs from 'node:fs';

const exe = ['/usr/bin/google-chrome-stable', '/usr/bin/chromium'].find((p) => fs.existsSync(p));

const server = await createServer({ server: { port: 3917, strictPort: true }, logLevel: 'error' });
await server.listen();

const browser = await puppeteer.launch({
  executablePath: exe,
  headless: true,
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']
});

let failed = 0;
try {
  const page = await browser.newPage();
  page.on('pageerror', (e) => console.error(`[pageerror] ${e.message}`));
  await page.goto('http://localhost:3917/', { waitUntil: 'networkidle0', timeout: 120000 });
  await page.waitForFunction(() => window.__getPlayerState?.().octreeReady, { timeout: 180000 });

  const r = await page.evaluate(() => {
    const W = window;
    const y = () => W.__getPlayerState().pos[1];
    const x = () => W.__getPlayerState().pos[0];
    const out = {};

    W.__setCam(0, 10, 0, -60, 10, 0);
    W.__simulateWalk(2, false);
    out.fall = y();

    W.__setViewpoint(5); // Jupiter NW, 26 m nad ziemią
    W.__simulateWalk(3, false);
    out.viewpointAir = y();

    W.__setCam(0, 1.65, 0, -60, 1.65, 0);
    W.__simulateWalk(0.5, false);
    const y0 = y();
    let yMax = y0;
    W.__simulateWalk(1 / 60, false, false, true);
    for (let i = 0; i < 90; i++) { W.__simulateWalk(1 / 60, false); yMax = Math.max(yMax, y()); }
    out.jump = yMax - y0;

    // korona trybuny głównej, w dół przejściem przy dźwigarze (oś 7: lokalnie Y = 7 * 130/14 + 0.4 m)
    W.__setCam(-81, 20.3, -2.57, 0, 4, -2.57);
    W.__simulateWalk(0.5, false);
    out.mainStandTop = y();
    W.__simulateWalk(6, true);
    out.mainStandBottom = y();

    W.__setCam(64, 8.5, 1.3, -55, 7, 1.3); // korona Galery, w dół na zachód
    W.__simulateWalk(0.5, false);
    out.galeraTop = y();
    W.__simulateWalk(6, true);
    out.galeraBottom = y();
    out.galeraX = x();

    W.__setCam(55, 6, 1.3, 100, 6, 1.3); // środek Galery (poza krawędzią podziału siatki), w górę na wschód
    W.__simulateWalk(0.5, false);
    out.galeraMid = y();
    W.__simulateWalk(2.5, true); // dłużej = przejście przez koronę i zejście tylną skarpą
    out.galeraClimb = y();

    W.__setViewpoint(7); // tunel pod trybuną główną: schody z hali na widownię sektora górnego
    W.__simulateWalk(0.5, false);
    out.tunnelStart = y();
    out.tunnelEnd = out.tunnelStart;   // najwyższy punkt: po wyjściu z tunelu ścieżka schodzi ku boisku
    for (let i = 0; i < 70; i++) { W.__simulateWalk(0.1, true); out.tunnelEnd = Math.max(out.tunnelEnd, y()); }

    W.__setCam(40, 1.65, 10, 100, 1.65, 10); // bieżnia -> mur oporowy z ogrodzeniem Galery
    W.__simulateWalk(3, true);
    out.fenceX = x();
    out.fenceY = y();

    W.__setCam(64, 8.5, 1.3, 200, 8.5, 1.3); // przez koronę Galery na teren za stadionem
    W.__simulateWalk(6, true);
    out.outsideX = x();
    out.outsideY = y();
    return out;
  });

  const check = (name, ok, detail) => {
    console.log(`${ok ? 'OK  ' : 'FAIL'} ${name}: ${detail}`);
    if (!ok) failed++;
  };
  const f = (v) => v.toFixed(2);
  check('spadanie z 10 m na murawę', Math.abs(r.fall - 1.65) < 0.1, `y=${f(r.fall)}`);
  check('punkt widokowy w powietrzu opada', r.viewpointAir < 5, `y=${f(r.viewpointAir)}`);
  check('wysokość skoku 0.4–0.6 m', r.jump > 0.4 && r.jump < 0.6, `${f(r.jump)} m`);
  check('zejście po rzędach trybuny głównej', r.mainStandTop > 12 && r.mainStandBottom < r.mainStandTop - 7, `y ${f(r.mainStandTop)} → ${f(r.mainStandBottom)}`);
  check('zejście po stopniach Galery', r.galeraTop > 7 && r.galeraBottom < r.galeraTop - 3, `y ${f(r.galeraTop)} → ${f(r.galeraBottom)} (x=${f(r.galeraX)})`);
  check('wejście po stopniach Galery', r.galeraClimb > r.galeraMid + 1.5, `y ${f(r.galeraMid)} → ${f(r.galeraClimb)}`);
  check('tunel: schody na sektor górny', r.tunnelStart < 2 && r.tunnelEnd > 8.5, `y ${f(r.tunnelStart)} → ${f(r.tunnelEnd)}`);
  check('mur z ogrodzeniem zatrzymuje na bieżni', r.fenceX < 45 && r.fenceY < 2, `x=${f(r.fenceX)} y=${f(r.fenceY)}`);
  check('teren za Galerą (bez spadania)', r.outsideX > 75 && Math.abs(r.outsideY - 1.40) < 0.1, `x=${f(r.outsideX)} y=${f(r.outsideY)}`);
} finally {
  await browser.close();
  await server.close();
}
process.exit(failed ? 1 : 0);
