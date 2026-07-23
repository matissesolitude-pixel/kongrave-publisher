#!/bin/bash
# PRÉ-VOL LIGNE — reproduit en local le scan fail-loud de build_ligne.py (écran quasi-vide + sans progression),
# sans passer par ElevenLabs : durées de voix estimées, sondes de paires de frames à 1/15 s.
# usage: preflight.sh <lXX> <LXX.json>
set -e
ENG="$1"; JSON="$2"
OUT="${PF_OUT:-/tmp}/_pf_$ENG"
rm -rf "$OUT"; mkdir -p "$OUT"
LIGNE=~/disruptive-reels-pipeline/ligne
python3 - "$ENG" "$JSON" "$OUT" <<'PY'
import json, sys, pathlib
eng, jsonp, out = sys.argv[1], sys.argv[2], sys.argv[3]
L = pathlib.Path.home()/"disruptive-reels-pipeline/ligne"
ep = json.loads((L/"episodes"/jsonp).read_text())
sc, s = [], 0.0
for v in ep["voice"]:
    d = max(6.0, len(v.split())/2.75 + 0.9)
    sc.append({"s": round(s,3), "d": round(d,3), "v": round(d-0.5,3)}); s += d
html = (L/"engine"/f"{eng}.html").read_text()
html = (html.replace("__SCENES__", json.dumps(sc)).replace("__SPEC__", json.dumps(ep["scenes"]))
            .replace("__WORDS__","[]").replace("__TOTAL__", f"{s:.3f}"))
html += """
<script>window.addEventListener('load',function(){var T=parseFloat(location.hash.slice(1))||0;try{clock.t=T;render();}catch(e){document.title='ERR '+e.message;}});</script>"""
(pathlib.Path(out)/"proj.html").write_text(html)
# sondes : tous les 0,8 s dans chaque fenêtre de voix
probes=[]
for x in sc:
    t=x["s"]+0.05
    while t < x["s"]+x["v"]:
        probes.append(round(t,3)); t+=0.8
(pathlib.Path(out)/"probes.txt").write_text("\n".join(str(p) for p in probes))
print(f"TOTAL={s:.1f}s  scenes={[(x['s'],x['d']) for x in sc]}  sondes={len(probes)}")
PY
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ABS="$(cd "$OUT" && pwd)"
while read -r T; do
  T2=$(python3 -c "print(round($T+1/15,4))")
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1080,1920 --virtual-time-budget=2200 \
    --screenshot="$OUT/a_$T.png" "file://$ABS/proj.html#$T" >/dev/null 2>&1
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1080,1920 --virtual-time-budget=2200 \
    --screenshot="$OUT/b_$T.png" "file://$ABS/proj.html#$T2" >/dev/null 2>&1
done < "$OUT/probes.txt"
python3 - "$OUT" <<'PY'
import sys, pathlib
from PIL import Image
import numpy as np
out = pathlib.Path(sys.argv[1])
probes = [float(x) for x in (out/"probes.txt").read_text().split()]
BLANK, THR = 0.004, 0.00015
bad = []
for t in probes:
    if not (out/f"a_{t}.png").exists() or not (out/f"b_{t}.png").exists():
        print(f"t={t:6.2f}  (frame manquante — ignorée)"); continue
    a = np.asarray(Image.open(out/f"a_{t}.png").convert('L').resize((432,768)), dtype=np.int16)
    b = np.asarray(Image.open(out/f"b_{t}.png").convert('L').resize((432,768)), dtype=np.int16)
    ink = (np.abs(a-238) > 24).mean()
    diff = (np.abs(a-b) > 16).mean()
    flag = []
    if ink < BLANK: flag.append("QUASI-VIDE")
    if diff < THR:  flag.append("SANS PROGRESSION")
    if flag: bad.append((t, ink, diff, "+".join(flag)))
    print(f"t={t:6.2f}  encre={ink*100:5.2f}%  progression={diff*100:6.3f}%  {' '.join(flag)}")
print("\n" + ("PRE-VOL OK — aucun point mort." if not bad else f"PRE-VOL KO — {len(bad)} point(s) : " + ", ".join(f"{t:.1f}s({f})" for t,_,_,f in bad)))
PY
