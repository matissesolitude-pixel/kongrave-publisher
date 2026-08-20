// Injecte les .woff2 (fonts/) en base64 dans template.html -> poster-la-ligne.html
import { readFileSync, writeFileSync } from 'node:fs';

const faces = [
  ['Barlow Condensed', 400, 'barlow-condensed-400.woff2', null],
  ['Barlow Condensed', 500, 'barlow-condensed-500.woff2', null],
  ['Barlow Condensed', 600, 'barlow-condensed-600.woff2', null],
  ['Barlow Condensed', 700, 'barlow-condensed-700.woff2', null],
  ['IBM Plex Mono',    400, 'ibm-plex-mono-400.woff2',    null],
  ['IBM Plex Mono',    500, 'ibm-plex-mono-500.woff2',    null],
  ['IBM Plex Mono',    400, 'ibm-plex-mono-arrow.woff2',  'U+2192'],
];

const css = faces.map(([fam, w, file, range]) => {
  const b64 = readFileSync(new URL(`./fonts/${file}`, import.meta.url)).toString('base64');
  return `@font-face{font-family:'${fam}';font-style:normal;font-weight:${w};font-display:block;` +
         `src:url(data:font/woff2;base64,${b64}) format('woff2');` +
         (range ? `unicode-range:${range};` : '') + `}`;
}).join('\n');

const html = readFileSync('template.html', 'utf8').replace('__FONTS__', css);
writeFileSync('poster-la-ligne.html', html);
console.log(`poster-la-ligne.html écrit — ${(html.length / 1024).toFixed(1)} Ko`);
