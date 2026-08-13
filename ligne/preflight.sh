#!/bin/bash
# PRÉ-VOL LIGNE — LE SCAN (LOI 9).
# Reproduit en local le fail-loud de build_ligne.py (écran quasi-vide + sans progression),
# sans passer par ElevenLabs : durées de voix estimées, sondes de paires de frames à 1/15 s.
#
# LE SCAN N'EST QUE LA MOITIÉ DU CONTRÔLE. Il mesure des pixels : il sait dire « ça bouge »,
# jamais « c'est lisible ». Le chevauchement, le hors-cadre et la composition se voient
# à l'ŒIL — `python3 ligne/frames.py lNN`, puis on REGARDE (skill revue-visuelle).
#
# usage: ligne/preflight.sh <lXX> <LXX.json>
set -e
ENG="$1"; JSON="$2"
[ -n "$ENG" ] && [ -n "$JSON" ] || { echo "usage: $(basename "$0") <lXX> <LXX.json>"; exit 2; }

# Racine déduite du script — le pré-vol tourne sur le Mac, sur le runner et en session
# cloud sans rien reconfigurer (avant : ~/disruptive-reels-pipeline codé en dur).
LIGNE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${PF_OUT:-/tmp}/_pf_$ENG"
rm -rf "$OUT"; mkdir -p "$OUT"

python3 - "$ENG" "$JSON" "$OUT" "$LIGNE" <<'PY'
import json, pathlib, sys
from concurrent.futures import ThreadPoolExecutor

eng, jsonp, out, ligne = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]), sys.argv[4]
sys.path.insert(0, ligne)
import frames  # projection, découverte de Chromium et flags : une seule source de vérité

L = pathlib.Path(ligne)
epf = L / "episodes" / jsonp
if not epf.is_file():
    sys.exit(f"PRÉ-VOL : épisode introuvable — {epf}")
ep = json.loads(epf.read_text())

tl = frames.estimate_timeline(ep)
(out / "proj.html").write_text(frames.project(eng, ep, tl))
print(f"TOTAL={tl['total']:.1f}s  scenes={[(s['s'], s['d']) for s in tl['sc']]}", end="  ")

# Sondes tous les 0,8 s DANS chaque fenêtre de voix (hors respiration de transition).
probes = []
for s in tl["sc"]:
    t = s["s"] + 0.05
    while t < s["s"] + s["v"]:
        probes.append(round(t, 3)); t += 0.8
print(f"sondes={len(probes)}")

chrome = frames.find_chrome()
print(f"Chromium : {chrome}")
print("Durées de voix ESTIMÉES (pas d'appel ElevenLabs) : ±10 %. Une plage détectée en toute "
      "fin de scène peut être un artefact d'estimation — la vérifier sur la frame.")
url = f"file://{out / 'proj.html'}"

def shoot(job):
    tag, t = job
    return frames.shoot(chrome, f"{url}#{t}", out / f"{tag}_{t}.png", (frames.W, frames.H))

jobs = [(k, t2) for t in probes
        for k, t2 in (("a", t), ("b", round(t + 1 / 15, 4)))]
with ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(shoot, jobs))

try:
    from PIL import Image
    import numpy as np
except ImportError:
    sys.exit("PRÉ-VOL INCOMPLET : frames rendues dans " + str(out) + " mais Pillow/numpy "
             "manquent pour les mesurer (pip install Pillow numpy). "
             "En attendant : python3 ligne/frames.py " + eng + " et REGARDE la planche.")

# Constantes IDENTIQUES à build_ligne.scan_progression — le pré-vol ne doit ni être plus
# laxiste (il laisserait passer un build qui échoue) ni plus sévère (il crierait au loup).
BLANK, THR = 0.004, 0.00015
MAXPAUSE, MAXVIDE = 1.5, 0.4

# Le vrai gate mesure des PLAGES, pas des points : un gel n'échoue qu'au-delà de 1,5 s,
# un vide au-delà de 0,4 s. Une sonde isolée sous le seuil est normale (sommet d'un geste,
# pause intentionnelle courte) — la signaler serait une fausse alerte, et une fausse alerte
# répétée fait ignorer l'outil. Les sondes étant espacées de 0,8 s, une plage se déduit du
# nombre de sondes CONSÉCUTIVES en défaut : 3 → 1,6 s (gel KO) · 2 → 0,8 s (vide KO).
gel, vide = [], []
prev_t = None
for t in probes:
    a_p, b_p = out / f"a_{t}.png", out / f"b_{round(t + 1 / 15, 4)}.png"
    if not a_p.exists() or not b_p.exists():
        print(f"t={t:6.2f}  (frame manquante — ignorée)"); prev_t = None; continue
    a = np.asarray(Image.open(a_p).convert('L').resize((432, 768)), dtype=np.int16)
    b = np.asarray(Image.open(b_p).convert('L').resize((432, 768)), dtype=np.int16)
    ink = (np.abs(a - 238) > 24).mean()
    diff = (np.abs(a - b) > 16).mean()
    flag = []
    if ink < BLANK:  flag.append("QUASI-VIDE")
    if diff < THR:   flag.append("SANS PROGRESSION")
    # une plage se poursuit si la sonde précédente était en défaut ET contiguë (même scène)
    for bucket, hit in ((gel, diff < THR), (vide, ink < BLANK)):
        if hit and bucket and prev_t is not None and bucket[-1][1] == prev_t:
            bucket[-1][1] = t
        elif hit:
            bucket.append([t, t])
    print(f"t={t:6.2f}  encre={ink*100:5.2f}%  progression={diff*100:6.3f}%  {' '.join(flag)}")
    prev_t = t

def scene_of(t):
    return next((i + 1 for i, s in enumerate(tl["sc"]) if s["s"] <= t <= s["s"] + s["v"]), "?")

bad = ([("SANS PROGRESSION", a, b) for a, b in gel if b - a > MAXPAUSE]
       + [("ÉCRAN QUASI-VIDE", a, b) for a, b in vide if b - a > MAXVIDE])
bad.sort(key=lambda x: x[1])
suspects = [(a, b) for a, b in vide if b - a <= MAXVIDE]

print()
if bad:
    print(f"PRÉ-VOL KO — {len(bad)} plage(s) :")
    for tag, a, b in bad:
        print(f"   S{scene_of(a)}  {a:.1f}s -> {b:.1f}s  ({b - a:.1f}s) — {tag}")
    print("Corrige : un élément AVANCE, ou la scène ouvre déjà pleine (jamais de vide).")
else:
    print("PRÉ-VOL OK — aucune plage morte au-delà des seuils du build.")
for a, b in suspects:
    print(f"   ⚠ S{scene_of(a)}  ~{a:.1f}s — sonde quasi-vide isolée : sous le seuil du build "
          f"(plage <{MAXVIDE}s), mais une ouverture qui s'ouvre presque nue est un défaut à l'ŒIL.")
print("\nLE SCAN NE VOIT PAS LA COMPOSITION. Avant de pousser :"
      f"\n  python3 ligne/frames.py {eng}   →  puis REGARDE la planche (skill revue-visuelle).")
sys.exit(1 if bad else 0)
PY
