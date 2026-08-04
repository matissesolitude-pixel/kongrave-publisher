#!/usr/bin/env bash
# Rend l'affiche SVG en PNG via Chromium headless.
# Usage : ./render.sh [facteur_echelle]   (2 = 2000x3000)
set -euo pipefail
cd "$(dirname "$0")"
SCALE="${1:-2}"
CHROME=/opt/pw-browsers/chromium-1194/chrome-linux/chrome

python3 gen_affiche.py affiche_amadeus.svg >/dev/null

# Marge basse volontaire : Chromium salit les dernieres lignes du viewport
# quand la hauteur de page vaut exactement celle de la fenetre. On recadre apres.
{
  cat <<'HTML'
<!doctype html><meta charset="utf-8">
<style>html,body{margin:0;padding:0;background:#EFE6D2}
svg{display:block;width:1000px;height:1500px}</style>
HTML
  cat affiche_amadeus.svg
} > .render.html

"$CHROME" --headless --no-sandbox --disable-gpu --hide-scrollbars \
  --force-device-scale-factor="$SCALE" --window-size=1000,1620 \
  --virtual-time-budget=4000 \
  --screenshot=.raw.png "file://$PWD/.render.html" 2>/dev/null

python3 - "$SCALE" <<'PY'
import sys
from PIL import Image
s = float(sys.argv[1])
im = Image.open(".raw.png").convert("RGB")
im.crop((0, 0, int(1000 * s), int(1500 * s))).save("affiche_amadeus.png")
print("affiche_amadeus.png", Image.open("affiche_amadeus.png").size)
PY

rm -f .render.html .raw.png
