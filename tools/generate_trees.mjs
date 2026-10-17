// Generuje build/drzewa.raw.glb: drzewa EZ-Tree na pozycjach z ortofotomapy (tools/trees/generate.js).
// Użycie: npm run trees:build (generowanie + kompresja do public/assets/drzewa.glb)
import puppeteer from 'puppeteer-core';
import { createServer } from 'vite';
import fs from 'node:fs';

const exe = ['/usr/bin/google-chrome-stable', '/usr/bin/chromium'].find((p) => fs.existsSync(p));
const server = await createServer({ root: 'tools/trees', server: { port: 3921, strictPort: true }, logLevel: 'error' });
await server.listen();
const browser = await puppeteer.launch({ executablePath: exe, headless: true, args: ['--no-sandbox'] });
try {
  const page = await browser.newPage();
  page.on('pageerror', (e) => console.error(`[pageerror] ${e.message}`));
  await page.goto('http://localhost:3921/', { waitUntil: 'load', timeout: 120000 });
  await page.waitForFunction(() => window.__result, { timeout: 120000 });
  const r = await page.evaluate(() => window.__result);
  if (r.error) throw new Error(r.error);
  console.table(r.stats);
  fs.mkdirSync('build', { recursive: true });
  fs.writeFileSync('build/drzewa.raw.glb', Buffer.from(r.glb, 'base64'));
  console.log(`build/drzewa.raw.glb: ${(fs.statSync('build/drzewa.raw.glb').size / 1048576).toFixed(2)} MB`);
} finally {
  await browser.close();
  await server.close();
}
