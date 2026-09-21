/**
 * Rasterises the "500K" app icon into the PNG sizes the PWA manifest needs.
 * Run with: npm run icons
 */
import sharp from 'sharp'
import { mkdir, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const OUT = join(dirname(fileURLToPath(import.meta.url)), '..', 'public', 'icons')

const BG = '#08090A'
const FG = '#F2F3F5'
const GREEN = '#21D07A'
const EDGE = '#1D2024'

/** @param {{radius:number, inset:number, scale:number}} o */
const svg = ({ radius, inset, scale }) => `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="${radius}" fill="${BG}"/>
  <g transform="translate(256 256) scale(${scale}) translate(-256 -256)">
    <rect x="${16 + inset}" y="${16 + inset}" width="${480 - inset * 2}" height="${480 - inset * 2}"
          rx="${Math.max(0, radius - 16)}" fill="none" stroke="${EDGE}" stroke-width="8"/>
    <text x="256" y="268" font-family="DejaVu Sans, Helvetica, Arial, sans-serif"
          font-size="122" font-weight="bold" letter-spacing="-4"
          text-anchor="middle" fill="${FG}">500K</text>
    <path d="M140 378 L204 346 L268 362 L332 306 L380 326" fill="none"
          stroke="${GREEN}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
</svg>`

const targets = [
  { file: 'icon-192.png', size: 192, opts: { radius: 112, inset: 0, scale: 1 } },
  { file: 'icon-512.png', size: 512, opts: { radius: 112, inset: 0, scale: 1 } },
  // iOS applies its own mask to the home-screen icon: keep it square and full-bleed.
  { file: 'apple-touch-icon.png', size: 180, opts: { radius: 0, inset: 10, scale: 0.9 } },
  // Maskable icons must keep their content inside the 80% safe zone.
  { file: 'maskable-512.png', size: 512, opts: { radius: 0, inset: 0, scale: 0.7 } },
]

await mkdir(OUT, { recursive: true })
for (const { file, size, opts } of targets) {
  const png = await sharp(Buffer.from(svg(opts))).resize(size, size).png().toBuffer()
  await writeFile(join(OUT, file), png)
  console.log(`wrote ${file} (${size}x${size}, ${png.length} bytes)`)
}
