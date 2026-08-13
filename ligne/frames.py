#!/usr/bin/env python3
"""
LA LIGNE — frames.py — L'ŒIL.

Rend n'importe quelle frame d'un moteur `ligne/engine/lNN.html` en PNG **regardable**,
et compose une planche-contact de l'épisode entier. C'est l'outil qui permet d'appliquer
la LOI 7 (« maquette d'abord, frames avant vidéo », §M21/§M24) et la consigne répétée
d'AGENT_MOTEURS.md : « Vérifie sur des frames RENDUES, jamais sur du raisonnement. »

DIVISION DU TRAVAIL — les deux contrôles sont complémentaires, aucun ne remplace l'autre :
  · `frames.py`     = L'ŒIL. Composition, chevauchement, hors-cadre, lisibilité en 0,2 s.
                      Des défauts qu'aucun seuil numérique ne voit.
  · `preflight.sh`  = LE SCAN. Écran quasi-vide et absence de progression (LOI 9),
                      mêmes seuils que le fail-loud de `build_ligne.py`.

ZÉRO DÉPENDANCE : stdlib + un Chromium. Pas de Pillow, pas de numpy — l'outil doit
marcher partout (Mac de Matisse, runner GitHub, session cloud) sans `pip install`.
La planche-contact est composée par Chromium lui-même, pas par une lib d'images.

USAGE
  python3 ligne/frames.py l70                 # storyboard : 3 frames × 5 scènes + planche
  python3 ligne/frames.py l70 -t 0 3.4 12.5   # frames à des temps précis (secondes)
  python3 ligne/frames.py l70 -s 3            # la scène 3 seule
  python3 ligne/frames.py l70 -s 3 -n 8       # 8 frames étalées dans la scène 3
  python3 ligne/frames.py l70 --no-sheet      # PNG individuels seulement

Puis on REGARDE les fichiers annoncés (outil Read sur le PNG). On ne conclut jamais
sur la lecture du code : la LOI 10 (étiquettes) a été payée quatre fois comme ça.

NOTE — les durées de voix sont ESTIMÉES (pas d'appel ElevenLabs) : les temps sont
donc à ±10 % du master final. Suffisant pour juger une composition, insuffisant pour
juger une synchro à la frame près.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from pathlib import Path

LIGNE = Path(__file__).resolve().parent
ENGINE = LIGNE / "engine"
EPISODES = LIGNE / "episodes"
ASSETS = LIGNE / "assets"

TAIL = 0.12          # identique à build_ligne.TAIL (respiration de transition par scène)
W, H = 1080, 1920    # viewBox des moteurs


# ---------------------------------------------------------------- Chromium

def find_chrome() -> str:
    """Trouve un Chromium où qu'il soit. L'ordre compte : override explicite, puis PATH,
    puis les emplacements connus (Playwright en conteneur, Chrome sur le Mac)."""
    env = os.environ.get("CHROME") or os.environ.get("CHROMIUM")
    if env and Path(env).is_file():
        return env
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    cands = sorted(glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"), reverse=True)
    cands += sorted(glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"), reverse=True)
    cands += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium"]
    for c in cands:
        if Path(c).is_file():
            return c
    sys.exit("frames.py : aucun Chromium trouvé. Renseigne $CHROME avec le chemin du binaire.")


def chrome_flags() -> list[str]:
    f = ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1"]
    # En conteneur on tourne en root : sans --no-sandbox, Chromium refuse de démarrer
    # (« Running as root without --no-sandbox is not supported »). Sur le Mac, on n'y touche pas.
    if platform.system() == "Linux":
        f.append("--no-sandbox")
    return f


def shoot(chrome: str, url: str, out: Path, size: tuple[int, int], budget: int = 2500) -> bool:
    cmd = [chrome, *chrome_flags(), f"--window-size={size[0]},{size[1]}",
           f"--virtual-time-budget={budget}", f"--screenshot={out}", url]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    return out.is_file()


# ---------------------------------------------------------------- projection

# Le hook de temps : on fige l'horloge du moteur au temps demandé et on rend une seule
# frame. En cas d'erreur JS, on l'ÉCRIT DANS L'IMAGE — le défaut se voit alors sur la
# frame elle-même au lieu de produire un PNG blanc énigmatique.
TIME_HOOK = """
<script>window.addEventListener('load',function(){
  var T=parseFloat(location.hash.slice(1))||0;
  try{ clock.t=T; render(); }
  catch(e){
    var d=document.createElement('div');
    d.style.cssText='position:fixed;left:0;top:0;right:0;padding:40px;z-index:9999;'
      +'background:#20242A;color:#F2EFE7;font:700 34px/1.35 monospace;white-space:pre-wrap';
    d.textContent='ERREUR MOTEUR @ t='+T+'s\\n\\n'+(e&&e.message||e)+'\\n\\n'+(e&&e.stack||'');
    document.body.appendChild(d);
  }
});</script>"""


def load_episode(eid: str, override: Path | None) -> dict | None:
    p = override or (EPISODES / f"{eid.upper()}.json")
    if not p.is_file():
        return None
    return json.loads(p.read_text())


def estimate_timeline(ep: dict) -> dict:
    """Reproduit la forme de build_ligne.timeline() avec des durées de voix ESTIMÉES.
    `v` = fenêtre de voix, `d` = durée de scène (voix + respiration)."""
    sc, t = [], 0.0
    voices = ep.get("voice") or []
    for i, v in enumerate(voices):
        dur = max(5.5, len(v.split()) / 2.75 + 0.9)
        tail = TAIL if i < len(voices) - 1 else TAIL + 0.35
        d = dur + tail
        sc.append({"s": round(t, 3), "d": round(d, 3), "v": round(dur, 3)})
        t += d
    return {"sc": sc, "total": round(t, 3)}


def project(eid: str, ep: dict | None, tl: dict) -> str:
    """Applique les mêmes substitutions que build_ligne.build_anim() — includes de
    bibliothèques, narrateur, puis marqueurs. Source de vérité : ligne/build_ligne.py:145.
    Si les deux divergent, c'est build_ligne qui a raison."""
    src = ENGINE / f"{eid}.html"
    if not src.is_file():
        sys.exit(f"frames.py : moteur introuvable — {src}")
    html = src.read_text()

    for lib in ("verbs.js", "shapes.js"):
        marker = f"/*INCLUDE:{lib}*/"
        if marker in html and (ENGINE / lib).is_file():
            html = html.replace(marker, (ENGINE / lib).read_text())

    if "/*INCLUDE:narrator*/" in html:
        html = html.replace("/*INCLUDE:narrator*/", narrator_block())

    scenes_spec = (ep or {}).get("scenes", [])
    return (html
            .replace("__SCENES__", json.dumps(tl["sc"]))
            .replace("__SPEC__", json.dumps(scenes_spec))
            .replace("__WORDS__", "[]")
            .replace("__TOTAL__", f'{tl["total"]:.3f}')
            .replace("__AMP__", "[]")) + TIME_HOOK


def narrator_block() -> str:
    """Mr Dollar est neutralisé depuis le 03/08 (draw = no-op) et INTERDIT dans les
    nouveaux moteurs. On injecte quand même la bibliothèque : 20 moteurs d'archive
    appellent encore `MrD.*` et lèveraient une ReferenceError sans elle."""
    js = ASSETS / "narrator.js"
    if not js.is_file():
        return "var MrD={enter(){},say(){},pointAt(){},hide(){},gag(){},setEyes(){},setAmp(){}};"
    poses, defs, sizes = sorted((ASSETS / "narrator").glob("*.svg")), [], {}
    for f in poses:
        svg = f.read_text()
        mw, mh = re.search(r'width="(\d+)"', svg), re.search(r'height="(\d+)"', svg)
        if not (mw and mh):
            continue
        defs.append(f'<g id="np_{f.stem}">' + "".join(re.findall(r"<path[^>]*/>", svg)) + "</g>")
        sizes[f.stem] = {"w": int(mw.group(1)), "h": int(mh.group(1))}
    eyes_p = ASSETS / "narrator" / "eyes.json"
    eyes_all = json.loads(eyes_p.read_text()) if eyes_p.is_file() else {}
    eyes = {k: v for k, v in eyes_all.items() if k in sizes and v}
    return (js.read_text().rstrip() + "\n"
            + "const NPOSE=" + json.dumps(sizes) + ";\n"
            + "const NEYES=" + json.dumps(eyes, ensure_ascii=False) + ";\n"
            + "(function(){var d=document.createElementNS('http://www.w3.org/2000/svg','defs');"
            + "d.innerHTML=" + json.dumps("".join(defs)) + ";SVG.appendChild(d);})();\n"
            + "const MrD=MrDollar.init({svg:SVG,poses:NPOSE,defaultPose:'idle_soft'});\n"
            + "MrD.setEyes(NEYES); MrD.setAmp([],30);\n")


# ---------------------------------------------------------------- plan de tir

def shots(tl: dict, scene: int | None, per: int, times: list[float] | None) -> list[tuple[float, str]]:
    """Quelles frames rendre. Par défaut : un STORYBOARD — ouverture / milieu / DoD de
    chaque scène. L'ouverture porte l'émotion (LOI 1bis), la DoD porte ce que l'image
    doit dire sans le son (§M24). Les trois côte à côte disent si la scène raconte."""
    if times:
        return [(t, f"t={t:g}s") for t in times]
    scs = tl["sc"]
    if not scs:
        return [(0.0, "t=0s")]
    idxs = [scene - 1] if scene else range(len(scs))
    out: list[tuple[float, str]] = []
    for i in idxs:
        if not (0 <= i < len(scs)):
            sys.exit(f"frames.py : scène {i + 1} inexistante (l'épisode en a {len(scs)}).")
        s, v = scs[i]["s"], scs[i]["v"]
        # 0,15 s après l'attaque (la frame 0 stricte peut précéder le premier paint),
        # puis étalement jusqu'à 85 % de la fenêtre de voix = la tenue DoD.
        span = max(v - 0.15, 0.1)
        for k in range(per):
            frac = 0 if per == 1 else k / (per - 1)
            t = s + 0.15 + span * 0.85 * frac
            tag = "ouverture" if k == 0 else ("DoD" if k == per - 1 else f"milieu {k}")
            out.append((round(t, 3), f"S{i + 1} · {tag} · t={t:.2f}s"))
    return out


# ---------------------------------------------------------------- planche

def contact_sheet(chrome: str, items: list[tuple[Path, str]], out: Path, cols: int, title: str) -> bool:
    """Compose la planche avec Chromium (aucune lib d'images). Une seule image à
    regarder pour juger l'épisode entier — c'est là qu'on voit d'un coup d'œil si
    deux scènes rejouent le même verbe visuel."""
    cw = 320
    ch = round(cw * H / W)
    rows = (len(items) + cols - 1) // cols
    cells = "".join(
        f'<figure><img src="file://{p}"><figcaption>{cap}</figcaption></figure>'
        for p, cap in items)
    html = f"""<!doctype html><meta charset="utf-8"><style>
    *{{box-sizing:border-box}}
    body{{margin:0;padding:16px;background:#20242A;
         font:600 14px/1.3 'Helvetica Neue',Arial,sans-serif;color:#F2EFE7}}
    h1{{margin:0 0 14px;font-size:20px;letter-spacing:1px;text-transform:uppercase}}
    .g{{display:grid;grid-template-columns:repeat({cols},{cw}px);gap:14px}}
    figure{{margin:0}}
    img{{width:{cw}px;height:{ch}px;display:block;border:1px solid #474D50;background:#F2EFE7}}
    figcaption{{padding-top:6px;text-align:center;letter-spacing:.5px}}
    </style><h1>{title}</h1><div class="g">{cells}</div>"""
    tmp = out.parent / "_sheet.html"
    tmp.write_text(html)
    sw = cols * cw + (cols - 1) * 14 + 32
    sh = rows * (ch + 26) + (rows - 1) * 14 + 32 + 34
    return shoot(chrome, f"file://{tmp}", out, (sw, sh), budget=4000)


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Rend les frames d'un moteur LA LIGNE en PNG regardables.")
    ap.add_argument("engine", help="identifiant du moteur : l70, 70, L70 — ou un chemin")
    ap.add_argument("-t", "--times", nargs="+", type=float, help="temps précis en secondes")
    ap.add_argument("-s", "--scene", type=int, help="ne rendre que cette scène (1-5)")
    ap.add_argument("-n", "--per-scene", type=int, default=3, help="frames par scène (défaut 3)")
    ap.add_argument("--json", type=Path, help="épisode JSON (défaut ligne/episodes/LNN.json)")
    ap.add_argument("--out", type=Path, help="dossier de sortie (défaut /tmp/ligne_frames/<moteur>)")
    ap.add_argument("--no-sheet", action="store_true", help="pas de planche-contact")
    args = ap.parse_args()

    # `l70`, `70`, `L70` désignent le même moteur ; `pivot` ou `proof` se prennent tels quels.
    stem = Path(args.engine).stem
    eid = next((c for c in (stem, stem.lower(), f"l{stem.lstrip('Ll')}")
                if (ENGINE / f"{c}.html").is_file()), None)
    if eid is None:
        sys.exit(f"frames.py : moteur introuvable — ni {ENGINE / f'{stem}.html'} "
                 f"ni {ENGINE / f'l{stem.lstrip(chr(76) + chr(108))}.html'}")

    ep = load_episode(eid, args.json)
    if ep is None:
        print(f"[frames] ⚠ pas d'épisode {eid.upper()}.json — __SPEC__ vide, "
              f"le moteur rendra probablement une image nue.", file=sys.stderr)
        ep = {"voice": [""] * 5, "scenes": []}
    tl = estimate_timeline(ep)

    out = args.out or Path("/tmp/ligne_frames") / eid
    out.mkdir(parents=True, exist_ok=True)
    proj = out / "proj.html"
    proj.write_text(project(eid, ep, tl))

    plan = shots(tl, args.scene, max(1, args.per_scene), args.times)
    chrome = find_chrome()

    print(f"[frames] {eid} · {len(tl['sc'])} scènes · total estimé {tl['total']:.1f}s")
    for i, s in enumerate(tl["sc"], 1):
        print(f"         S{i}  début {s['s']:6.2f}s   voix {s['v']:5.2f}s   scène {s['d']:5.2f}s")
    print(f"[frames] Chromium : {chrome}")
    print(f"[frames] rendu de {len(plan)} frame(s)…")

    def one(job):
        idx, (t, cap) = job
        png = out / f"{idx:02d}_t{t:07.3f}.png"
        ok = shoot(chrome, f"file://{proj}#{t}", png, (W, H))
        return (png, cap, ok)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(one, enumerate(plan, 1)))

    done = [(p, c) for p, c, ok in results if ok]
    for p, c, ok in results:
        print(("  ✓ " if ok else "  ✗ ÉCHEC ") + f"{c}  →  {p}")
    if not done:
        sys.exit("frames.py : aucune frame rendue.")

    if not args.no_sheet and len(done) > 1:
        sheet = out / "PLANCHE.png"
        cols = max(1, args.per_scene) if not args.times and not args.scene else min(3, len(done))
        if contact_sheet(chrome, done, sheet, cols, f"{eid.upper()} — planche-contact"):
            print(f"\n[frames] PLANCHE  →  {sheet}")

    print("\n[frames] REGARDE les images (Read sur le PNG). La checklist de l'œil est "
          "dans .claude/skills/revue-visuelle/SKILL.md — on ne conclut jamais sur le code.")


if __name__ == "__main__":
    main()
