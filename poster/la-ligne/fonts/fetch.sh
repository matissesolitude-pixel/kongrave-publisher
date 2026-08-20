#!/usr/bin/env bash
set -euo pipefail
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
cd "$(dirname "$0")"
fetch() { # family_url_name  weight  outfile
  local fam="$1" w="$2" out="$3"
  local css
  css=$(curl -sS -A "$UA" "https://fonts.googleapis.com/css2?family=${fam}:wght@${w}&display=swap")
  # bloc latin (dernier bloc) -> url woff2
  local url
  url=$(printf '%s' "$css" | awk '/\/\* latin \*\//{f=1} f&&/src: url\(/{print; exit}' | sed -E 's/.*url\((https:[^)]*)\).*/\1/')
  [ -n "$url" ] || { echo "URL introuvable pour $fam $w"; exit 1; }
  curl -sS -A "$UA" "$url" -o "$out"
  echo "$out  $(stat -c%s "$out") octets"
}
fetch "Barlow+Condensed" 400 barlow-condensed-400.woff2
fetch "Barlow+Condensed" 500 barlow-condensed-500.woff2
fetch "Barlow+Condensed" 600 barlow-condensed-600.woff2
fetch "Barlow+Condensed" 700 barlow-condensed-700.woff2
fetch "IBM+Plex+Mono"    400 ibm-plex-mono-400.woff2
fetch "IBM+Plex+Mono"    500 ibm-plex-mono-500.woff2
