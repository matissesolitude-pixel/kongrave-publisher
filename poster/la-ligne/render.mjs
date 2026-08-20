// Rendu du poster : PNG 3200x4800 (A2 > 300 dpi), PNG Instagram, PDF A2.
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const SRC = pathToFileURL(resolve('poster-la-ligne.html')).href;
const OUT = resolve('out');
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();

async function shoot({ width, height, scale, file }) {
  const ctx = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: scale });
  const page = await ctx.newPage();
  await page.goto(SRC, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1200);
  const check = await page.evaluate(() => ({
    barlow: document.fonts.check('700 100px "Barlow Condensed"'),
    plex: document.fonts.check('400 20px "IBM Plex Mono"'),
    titleW: document.querySelector('.title span').getBoundingClientRect().width,
    posterW: document.querySelector('.poster').getBoundingClientRect().width,
    posterH: document.querySelector('.poster').getBoundingClientRect().height,
  }));
  console.log(`[${file}]`, JSON.stringify(check));
  if (!check.barlow || !check.plex) throw new Error('Fonts non chargées — rendu avorté');
  await page.locator('.poster').screenshot({ path: `${OUT}/${file}` });
  await ctx.close();
  return check;
}

await shoot({ width: 1600, height: 2400, scale: 2, file: 'poster-la-ligne@3200.png' });
await shoot({ width: 1080, height: 1620, scale: 1, file: 'poster-la-ligne@1080x1620.png' });

// PDF A2
const ctx = await browser.newContext();
const page = await ctx.newPage();
await page.goto(SRC, { waitUntil: 'load' });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(1200);
await page.pdf({
  path: `${OUT}/poster-la-ligne-A2.pdf`,
  width: '420mm', height: '594mm',
  printBackground: true,
  margin: { top: '0', right: '0', bottom: '0', left: '0' },
});
await ctx.close();
await browser.close();
console.log('OK');
