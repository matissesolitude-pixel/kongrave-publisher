# LA LIGNE — poster A2 portrait

Poster « LA LIGNE — une vie en une seule ligne » : la vie de Matisse tracée comme une
structure de marché (Lyon 1990 → sweep → order block → BOS Dubaï → expansion KONGRAVE →
Disruptive Investment → projection pointillée vers 5 000 €/mois net).

## Fichiers

| Fichier | Rôle |
|---|---|
| `poster-la-ligne.html` | **Le poster.** Fichier autonome, zéro dépendance réseau (fonts Google embarquées en base64). C'est la source de rendu. |
| `template.html` | Source éditable, avec le marqueur `__FONTS__` à la place du bloc `@font-face`. |
| `build.mjs` | Injecte les `.woff2` de `fonts/` en base64 → régénère `poster-la-ligne.html`. |
| `fonts/fetch.sh` | Retélécharge les sous-ensembles latin depuis Google Fonts (Barlow Condensed 400/500/600/700, IBM Plex Mono 400/500 + glyphe `→`). |
| `render.mjs` | Playwright/Chromium → les 3 sorties dans `out/`. |

## Sorties (`out/`)

- `poster-la-ligne@3200.png` — 3200 × 4800 px (A2 à ~193 dpi en 420×630 mm, > 300 dpi en A2 ajusté)
- `poster-la-ligne@1080x1620.png` — Instagram 2:3
- `poster-la-ligne-A2.pdf` — 420 × 594 mm, fonds imprimés

## Rendu

```sh
npm i -D playwright && npx playwright install chromium   # une seule fois
node build.mjs      # seulement si on a touché template.html ou fonts/
node render.mjs
```
Sur macOS, préfixer par `caffeinate -di`.

## Notes

- **Fonts** : embarquées en base64 dans le HTML. `render.mjs` refuse de screenshoter si
  `document.fonts.check()` renvoie false — impossible de livrer un rendu en fallback Arial Narrow.
- **Format** : le poster est en 2/3 (ratio Instagram/affiche), l'A2 est en 1/1,414. Le PDF
  place donc le poster à 396 × 594 mm centré sur la page 420 × 594 mm, sur fond `--ink-deep`
  plein papier (bandes latérales de 12 mm, invisibles à l'impression sur fond sombre).
  Pour un tirage 2/3 plein format, imprimer en 420 × 630 mm.
- **Grain** : feTurbulence en `mix-blend-mode: overlay`. Visible sur les PNG ; il peut sauter
  au rendu PDF (support partiel des blend modes), c'est accepté.
- **Aucune animation** : le poster est statique par construction, rien à figer au rendu.
