import puppeteer from 'puppeteer-core';
import fs from 'node:fs';

const [name = 'browser_preview', waitMs = '4000', size = '1280x720'] = process.argv.slice(2);
const [w, h] = size.split('x').map(Number);
const url = process.env.SHOT_URL ?? 'http://localhost:3000/';
const exe = ['/usr/bin/google-chrome-stable', '/usr/bin/chromium'].find((p) => fs.existsSync(p));

fs.mkdirSync('.shots', { recursive: true });

const browser = await puppeteer.launch({
  executablePath: exe,
  headless: true,
  args: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--enable-gpu',
    '--ignore-gpu-blocklist',
    '--use-gl=angle',
    '--use-angle=swiftshader',
    '--enable-unsafe-swiftshader'
  ],
});

const page = await browser.newPage();
await page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });

page.on('console', (m) => console.log(`[console.${m.type()}] ${m.text()}`));
page.on('pageerror', (e) => console.error(`[pageerror] ${e.stack ?? e.message}`));

console.log(`Nawigacja do ${url}...`);
await page.goto(url, { waitUntil: 'networkidle0', timeout: 180000 });

await new Promise((r) => setTimeout(r, Number(waitMs)));

if (process.env.EVAL) {
  console.log(`Wykonywanie skryptu EVAL: ${process.env.EVAL}`);
  await page.evaluate(process.env.EVAL);
  await new Promise((r) => setTimeout(r, 1000));
}

const outPath = `.shots/${name}.png`;
await page.screenshot({ path: outPath });
console.log(`Zapisano zrzut ekranu: ${outPath}`);

await browser.close();
