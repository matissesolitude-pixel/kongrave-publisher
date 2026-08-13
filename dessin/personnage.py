#!/usr/bin/env python3
"""
DESSIN — personnage.py — LE RIG.

Dessiner un personnage en vecteur à partir d'un SQUELETTE, pas d'un tas de courbes.
On pose les articulations, le rig fabrique le corps. Conséquence directe : le MÊME
personnage tient sur 3 poses ou sur 30 — ce qui est exactement le problème d'une série
(illustrer les exercices d'un programme, une suite de panneaux, un personnage récurrent).

POURQUOI UN RIG ET PAS UN DESSIN À MAIN LEVÉE
  Un personnage dessiné pose par pose dérive : la tête change de taille, la palette
  bouge, le trait s'épaissit. Ici les proportions, la palette et l'épaisseur de trait
  sont définies UNE FOIS ; une pose n'est plus qu'un jeu de coordonnées. Et une pose
  fausse se corrige dans le squelette, jamais en rattrapant le dessin.

CE QUE ÇA NE FAIT PAS
  Ce n'est pas du dessin à la main. On obtient un aplat vectoriel propre, lisible et
  cohérent — pas le trait vivant et l'expressivité d'un Zep. Pour ça il faut un modèle
  d'image piloté par une feuille de personnage (voir la skill dessin-personnage).

USAGE
  python3 dessin/personnage.py                       # planche des poses connues
  python3 dessin/personnage.py -p SQUAT              # une pose
  python3 dessin/personnage.py -p SQUAT FENTE -o /tmp/x.png
  python3 dessin/personnage.py --svg SQUAT > squat.svg
"""
from __future__ import annotations

import argparse
import math
import pathlib
import sys

# Chromium : découverte et flags déjà résolus pour tout le repo par ligne/frames.py
# (conteneur, runner, Mac). On ne duplique pas cette logique.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "ligne"))
import frames  # noqa: E402

INK = "#1B1B1F"
PAL = dict(skin="#F3C9A6", skin_far="#D9A47E", hair="#4A2F26", hair_far="#3A241D",
           top="#E8556D", legs="#2E3A59", legs_far="#222B44",
           shoe="#F5F3EE", shoe_far="#D8D5CE", paper="#F7F4EE")

HEAD_RX, HEAD_RY = 92, 84      # tête volontairement grosse — école « gros nez »
LIMB_ARM, LIMB_LEG = 32, 48    # épaisseur de chair ; le contour ajoute CONTOUR
CONTOUR = 14
NECK_MIN = 106                 # cou -> centre de tête ; en dessous, le crâne mange le cou
LIMB_MIN_ANGLE = 62            # angle au genou/coude ; en dessous, les segments fusionnent
GROUND = 898

JOINTS = ("ankleR kneeR hipR ankleL kneeL hipL shoulderR elbowR wristR "
          "shoulderL elbowL wristL hip shoulder neck head").split()


# ---------------------------------------------------------------- primitives

def _path(pts):
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def limb(pts, w, color):
    """Un membre = UN trait épais, bouts et jointures ronds. Le sandwich (un trait
    d'encre large, un trait de chair plus fin par-dessus) donne le contour fermé
    sans avoir à décrire le contour."""
    d = _path(pts)
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w + CONTOUR}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def blob(d, fill, sw=13):
    return f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'


def disc(c, r, fill, sw=13):
    return f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{r}" fill="{fill}" stroke="{INK}" stroke-width="{sw}"/>'


def shoe(ankle, ang, far=False):
    ax, ay = ankle
    d = "M -32 -18 L 28 -18 Q 68 -12 72 14 Q 72 24 56 24 L -32 24 Q -48 6 -32 -18 Z"
    return (f'<g transform="translate({ax:.1f},{ay:.1f}) rotate({ang})">'
            f'{blob(d, PAL["shoe_far"] if far else PAL["shoe"])}</g>')


def head(J):
    """Profil « gros nez » : le nez DÉPASSE du crâne, l'œil reste bien à l'intérieur,
    la calotte de cheveux s'arrête avant le sourcil. Ces trois règles font le style."""
    hx, hy = J["head"]
    p = [blob(f"M {hx-72} {hy-38} Q {hx-158} {hy-58} {hx-182} {hy+30} "
              f"Q {hx-150} {hy-2} {hx-108} {hy+16} Q {hx-84} {hy-6} {hx-72} {hy-38} Z",
              PAL["hair_far"]),
         f'<ellipse cx="{hx}" cy="{hy}" rx="{HEAD_RX}" ry="{HEAD_RY}" '
         f'fill="{PAL["skin"]}" stroke="{INK}" stroke-width="14"/>',
         blob(f"M {hx-92} {hy+6} Q {hx-100} {hy-84} {hx-6} {hy-90} "
              f"Q {hx+70} {hy-88} {hx+74} {hy-44} "
              f"Q {hx+24} {hy-62} {hx-26} {hy-50} "
              f"Q {hx-68} {hy-40} {hx-70} {hy+12} Z", PAL["hair"]),
         f'<ellipse cx="{hx+38}" cy="{hy-4}" rx="9" ry="13" fill="{INK}"/>',
         f'<path d="M {hx+20} {hy-34} Q {hx+42} {hy-46} {hx+58} {hy-32}" '
         f'fill="none" stroke="{INK}" stroke-width="10" stroke-linecap="round"/>',
         disc((hx + 84, hy + 14), 25, PAL["skin"]),
         f'<path d="M {hx+56} {hy+50} Q {hx+74} {hy+42} {hx+84} {hy+50}" '
         f'fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>']
    return "".join(p)


# ---------------------------------------------------------------- contrôles

def angle_at(a, b, c):
    """Angle en b, en degrés."""
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if not n1 or not n2:
        return 180.0
    cos = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return math.degrees(math.acos(cos))


def check(J, name=""):
    """Le squelette se contrôle AVANT le rendu. Ces trois défauts ne sont pas
    rattrapables au dessin : ils se corrigent dans les coordonnées."""
    warn = []
    missing = [k for k in JOINTS if k not in J]
    if missing:
        warn.append(f"articulations manquantes : {', '.join(missing)}")
        return warn
    d = math.dist(J["neck"], J["head"])
    if d < NECK_MIN:
        warn.append(f"cou {d:.0f}px < {NECK_MIN} — le crâne mange le cou")
    for side in "RL":
        for tag, (a, b, c) in {
                "genou": (f"hip{side}", f"knee{side}", f"ankle{side}"),
                "coude": (f"shoulder{side}", f"elbow{side}", f"wrist{side}")}.items():
            ang = angle_at(J[a], J[b], J[c])
            if ang < LIMB_MIN_ANGLE:
                warn.append(f"{tag} {side} plié à {ang:.0f}° < {LIMB_MIN_ANGLE}° — "
                            f"les deux segments vont fusionner en une masse")
    for side in "RL":
        foot = J[f"ankle{side}"][1] + 24
        if foot > GROUND + 8:
            warn.append(f"pied {side} sous le sol ({foot:.0f} > {GROUND})")
    return warn


# ---------------------------------------------------------------- la figure

def figure(J):
    """Ordre de tracé = profondeur. Les membres LOINTAINS (assombris) d'abord, puis le
    cou, puis le tronc, puis les membres PROCHES. Le cou passe AVANT le tronc : il doit
    sortir de la masse des épaules, pas se poser dessus."""
    p = [shoe(J["ankleL"], J["footL"], far=True),
         limb([J["hipL"], J["kneeL"], J["ankleL"]], LIMB_LEG, PAL["legs_far"]),
         limb([J["shoulderL"], J["elbowL"], J["wristL"]], LIMB_ARM, PAL["skin_far"]),
         disc(J["wristL"], 24, PAL["skin_far"]),
         limb([J["shoulder"], J["neck"]], 36, PAL["skin"])]

    sx, sy = J["shoulder"]; hx, hy = J["hip"]
    ang = math.atan2(hx - sx, sy - hy)          # inclinaison du buste
    nx, ny = math.cos(ang), math.sin(ang)       # sa normale
    ws, wh = 60, 54
    p.append(blob(f"M {sx-nx*ws:.1f} {sy-ny*ws:.1f} Q {sx+nx*ws*1.2:.1f} {sy-ny*ws*0.5:.1f} "
                  f"{sx+nx*ws:.1f} {sy+ny*ws:.1f} "
                  f"L {hx+nx*wh:.1f} {hy+ny*wh:.1f} Q {hx:.1f} {hy+wh*0.8:.1f} "
                  f"{hx-nx*wh:.1f} {hy-ny*wh:.1f} Z", PAL["top"]))
    p.append(disc(J["hip"], 52, PAL["legs"]))          # bassin
    p.append(disc(J["shoulder"], 46, PAL["top"]))      # épaule : l'attache du bras

    p += [shoe(J["ankleR"], J["footR"]),
          limb([J["hipR"], J["kneeR"], J["ankleR"]], LIMB_LEG, PAL["legs"]),
          head(J),
          limb([J["shoulderR"], J["elbowR"], J["wristR"]], LIMB_ARM, PAL["skin"]),
          disc(J["wristR"], 26, PAL["skin"])]
    return "".join(p)


# ---------------------------------------------------------------- les poses

POSES = {
    # Squat : cuisse ~horizontale, tibia incliné vers l'arrière, buste penché en avant.
    "SQUAT": dict(
        ankleR=(430, 872), kneeR=(470, 720), hipR=(350, 726), footR=0,
        ankleL=(398, 866), kneeL=(438, 714), hipL=(318, 720), footL=0,
        shoulderR=(430, 578), elbowR=(522, 600), wristR=(612, 570),
        shoulderL=(404, 594), elbowL=(490, 636), wristL=(576, 622),
        hip=(350, 726), shoulder=(430, 578), neck=(450, 540), head=(482, 436),
        vb=(143, 322, 620, 620)),

    # Fente : tibia avant vertical, genou arrière bas, buste droit.
    "FENTE": dict(
        ankleR=(520, 866), kneeR=(515, 726), hipR=(400, 712), footR=0,
        ankleL=(218, 872), kneeL=(288, 836), hipL=(392, 706), footL=-58,
        shoulderR=(402, 560), elbowR=(424, 648), wristR=(414, 730),
        shoulderL=(376, 566), elbowL=(396, 652), wristL=(386, 734),
        hip=(400, 712), shoulder=(402, 560), neck=(414, 518), head=(436, 408),
        vb=(110, 320, 620, 620)),

    # Gainage : corps en ligne droite chevilles->épaules, bras vertical, pointes au sol.
    "GAINAGE": dict(
        ankleR=(240, 822), kneeR=(336, 792), hipR=(432, 764), footR=90,
        ankleL=(224, 836), kneeL=(322, 806), hipL=(418, 778), footL=90,
        shoulderR=(604, 714), elbowR=(610, 796), wristR=(616, 872),
        shoulderL=(582, 730), elbowL=(588, 810), wristL=(594, 882),
        hip=(432, 764), shoulder=(604, 714), neck=(648, 700), head=(760, 664),
        vb=(170, 470, 720, 720)),
}


def svg_of(name, J=None):
    J = J or POSES[name]
    x, y, w, h = J.get("vb", (110, 320, 620, 620))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" '
            f'width="{w}" height="{h}">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PAL["paper"]}"/>'
            f'<path d="M {x+24} {GROUND} L {x+w-24} {GROUND}" stroke="{INK}" '
            f'stroke-width="9" stroke-linecap="round" opacity="0.28"/>'
            f'{figure(J)}</svg>')


# ---------------------------------------------------------------- rendu

CELL = 700


def sheet_html(names):
    cells = []
    for n in names:
        # Le viewBox DOIT avoir le ratio de la cellule, sinon le papier ne remplit
        # pas le cadre et le personnage se retrouve décadré.
        cells.append(f'<figure>{svg_of(n)}<figcaption>{n}</figcaption></figure>')
    return f"""<!doctype html><meta charset="utf-8"><style>
*{{box-sizing:border-box}} body{{margin:0;padding:18px;background:#20242A;
font:700 16px/1.2 'Helvetica Neue',Arial,sans-serif;color:#F7F4EE}}
.g{{display:grid;grid-template-columns:repeat({len(names)},{CELL}px);gap:16px}}
figure{{margin:0}} svg{{width:{CELL}px;height:{CELL}px;display:block;border:1px solid #474D50}}
figcaption{{padding-top:8px;text-align:center;letter-spacing:2px}}
</style><div class="g">{''.join(cells)}</div>"""


def main():
    ap = argparse.ArgumentParser(description="Dessine le personnage dans une ou plusieurs poses.")
    ap.add_argument("-p", "--poses", nargs="+", default=list(POSES), help="poses à dessiner")
    ap.add_argument("-o", "--out", type=pathlib.Path,
                    default=pathlib.Path("/tmp/dessin/planche.png"))
    ap.add_argument("--svg", metavar="POSE", help="écrit le SVG d'une pose sur la sortie standard")
    ap.add_argument("--list", action="store_true", help="liste les poses connues")
    args = ap.parse_args()

    if args.list:
        print("\n".join(POSES)); return
    if args.svg:
        print(svg_of(args.svg)); return

    unknown = [n for n in args.poses if n not in POSES]
    if unknown:
        sys.exit(f"pose inconnue : {', '.join(unknown)} (connues : {', '.join(POSES)})")

    ko = False
    for n in args.poses:
        for w in check(POSES[n], n):
            print(f"  ⚠ {n}: {w}"); ko = True
    if not ko:
        print("  squelettes ✓ (cou dégagé, articulations ouvertes, pieds au sol)")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    html = args.out.parent / "_planche.html"
    html.write_text(sheet_html(args.poses))
    w = len(args.poses) * CELL + (len(args.poses) - 1) * 16 + 36
    if frames.shoot(frames.find_chrome(), f"file://{html}", args.out, (w, CELL + 62)):
        print(f"→ {args.out}\nREGARDE l'image. La checklist est dans "
              f".claude/skills/dessin-personnage/SKILL.md")
    else:
        sys.exit("rendu échoué")


if __name__ == "__main__":
    main()
