// Pomiar wydajności: draw calle i trójkąty na klatkę (wszystkie przebiegi) oraz czas klatki w trzech ujęciach.
// Czas klatki w headless Chrome (SwiftShader, CPU) służy tylko do porównań przed/po — nie odpowiada GPU.
// Użycie: npm run perf
import puppeteer from 'puppeteer-core';
import { createServer } from 'vite';
import fs from 'node:fs';

const exe = ['/usr/bin/google-chrome-stable', '/usr/bin/chromium'].find((p) => fs.existsSync(p));
const server = await createServer({ server: { port: 3928, strictPort: true }, logLevel: 'error' });
await server.listen();
const b = await puppeteer.launch({ executablePath: exe, headless: true, args: ['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'] });
const p = await b.newPage();
await p.setViewport({ width: 1280, height: 720 });
await p.goto('http://localhost:3928/', { waitUntil: 'networkidle0', timeout: 120000 });
await p.waitForFunction(() => window.__getPlayerState?.().octreeReady, { timeout: 180000 });
await new Promise(r => setTimeout(r, 4000));
for (const [name, ev] of [['murawa', 'window.__setViewpoint(0)'], ['z Galery', 'window.__setCam(52,5.2,40,-60,6,-30)'], ['korona', 'window.__setViewpoint(1)']]) {
  await p.evaluate(ev);
  const r = await p.evaluate(() => window.__perf(20));
  console.log(name.padEnd(9), `${r.msPerFrame.toFixed(0)} ms/kl. (swiftshader)  draw calls: ${r.calls}  trójkąty: ${r.triangles}`);
}
await b.close(); await server.close();
