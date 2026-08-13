#!/usr/bin/env python3
"""
DESSIN — figure.py — LA FIGURE (manga / comics).

Ce que `personnage.py` ne pouvait pas faire : montrer un CORPS. Son rig dessine des
membres en traits d'épaisseur constante et une tête d'un tiers de la hauteur — une
silhouette de gag, sans galbe et sans anatomie.

CE QUI CHANGE ICI, ET POURQUOI
  1. PROPORTIONS 7 TÊTES. La tête fait 1/7 de la hauteur au lieu de 1/3. C'est ce
     rapport, et lui seul, qui fait basculer une silhouette du cartoon vers le manga.
  2. MEMBRES FUSELÉS. Chaque segment est une capsule à DEUX rayons (large à la cuisse,
     fin au genou ; large au mollet, fin à la cheville). Un tube d'épaisseur constante
     ne peut pas décrire une jambe.
  3. TORSE À PROFIL DISSYMÉTRIQUE. En vue de profil, les formes féminines ne sont pas
     une largeur : c'est un AVANT (poitrine) et un ARRIÈRE (fessier) qui ne bombent pas
     au même endroit, séparés par une taille creusée. Le torse est donc construit à
     partir de deux profils de largeur indépendants, échantillonnés le long de l'axe
     épaules→bassin.
  4. TENUE BRASSIÈRE + SHORT. Le ventre reste nu : c'est ce qui rend la taille visible.
     Habiller le torse d'un seul aplat annule tout le travail du point 3.

USAGE
  python3 dessin/figure.py                    # planche des poses
  python3 dessin/figure.py -p SQUAT
  python3 dessin/figure.py --style comics     # trait plus épais, palette contrastée
  python3 dessin/figure.py --svg SQUAT > squat.svg
"""
from __future__ import annotations

import argparse
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "ligne"))
import frames  # noqa: E402  (découverte de Chromium, déjà résolue pour tout le repo)

GROUND = 898

STYLES = {
    "manga": dict(
        ink="#15151C", contour=9,
        skin="#F7D3B6", skin_far="#DDB394",
        hair="#26262F", hair_far="#181820",
        bra="#E24A63", bra_far="#B93A50",
        short="#303B58", short_far="#232B42",
        shoe="#FAFAF7", shoe_far="#DAD9D4",
        paper="#F7F4EE", eye_white="#FFFFFF"),
    "comics": dict(
        ink="#101014", contour=13,
        skin="#F2BE96", skin_far="#D29B74",
        hair="#3A1F14", hair_far="#28150E",
        bra="#D62828", bra_far="#A81E1E",
        short="#1D3557", short_far="#142640",
        shoe="#F1FAEE", shoe_far="#CBD4C8",
        paper="#F4EFE4", eye_white="#FFFFFF"),
}
S = STYLES["manga"]

# --- rayons de chair par articulation (c'est ici que vit le galbe) -----------
R = dict(hip=40, knee=26, ankle=15, shoulder=25, elbow=17, wrist=11, neck=17)

HEAD_RY = 50          # demi-hauteur de tête -> 7 têtes pour ~700 px de figure
NECK_MIN = 62
LIMB_MIN_ANGLE = 58

JOINTS = ("ankleR kneeR hipR ankleL kneeL hipL shoulderR elbowR wristR "
          "shoulderL elbowL wristL hip shoulder neck head").split()


# ---------------------------------------------------------------- primitives

def capsule(p0, r0, p1, r1):
    """Contour d'un tronc de cône à bouts ronds : les deux tangentes extérieures
    fermées par un arc à chaque bout. C'est la brique du membre fuselé."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L < 1e-6 or L <= abs(r1 - r0):                     # un disque contient l'autre
        c, r = (p0, r0) if r0 >= r1 else (p1, r1)
        return (f'M {c[0]-r:.1f} {c[1]:.1f} a {r} {r} 0 1 0 {2*r} 0 '
                f'a {r} {r} 0 1 0 {-2*r} 0 Z')
    base = math.atan2(dy, dx)
    delta = math.asin((r0 - r1) / L)
    a1, a2 = base + math.pi / 2 + delta, base - math.pi / 2 - delta
    P = lambda c, r, a: (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
    s0, e0 = P(p0, r0, a1), P(p1, r1, a1)
    e1, s1 = P(p1, r1, a2), P(p0, r0, a2)
    return (f'M {s0[0]:.1f} {s0[1]:.1f} L {e0[0]:.1f} {e0[1]:.1f} '
            f'A {r1} {r1} 0 0 0 {e1[0]:.1f} {e1[1]:.1f} '
            f'L {s1[0]:.1f} {s1[1]:.1f} A {r0} {r0} 0 0 0 {s0[0]:.1f} {s0[1]:.1f} Z')


def chain(joints, radii, color, grow=0):
    """Un membre entier en UNE passe de couleur. Les capsules se recouvrent aux
    articulations : même couleur, donc aucune couture visible. On appelle deux fois —
    une passe encre élargie, une passe chair — pour obtenir le contour."""
    d = "".join(capsule(joints[i], radii[i] + grow, joints[i + 1], radii[i + 1] + grow)
                for i in range(len(joints) - 1))
    for c, r in zip(joints, radii):
        d += (f'M {c[0]-r-grow:.1f} {c[1]:.1f} a {r+grow} {r+grow} 0 1 0 {2*(r+grow)} 0 '
              f'a {r+grow} {r+grow} 0 1 0 {-2*(r+grow)} 0 Z')
    return f'<path d="{d}" fill="{color}" fill-rule="nonzero"/>'


def limb(joints, radii, color):
    return (chain(joints, radii, S["ink"], grow=S["contour"])
            + chain(joints, radii, color))


def _lerp(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)


def leg(hip, knee, ankle, skin, short):
    """La jambe se dessine en CHAIR entière, puis le short par-dessus sur le haut de
    cuisse seulement. Habiller toute la jambe d'un aplat sombre la transforme en masse :
    genou et mollet disparaissent, et le galbe avec eux."""
    return (limb([hip, knee, ankle], [R["hip"], R["knee"], R["ankle"]], skin)
            + limb([hip, _lerp(hip, knee, 0.52)],
                   [R["hip"] + 2, R["hip"] * 0.78], short))


def hand(wrist, elbow, skin):
    """Sans main, un bras se termine en moignon arrondi. Une mitaine suffit : la
    direction vient de l'avant-bras, jamais d'un angle écrit à la main."""
    dx, dy = wrist[0] - elbow[0], wrist[1] - elbow[1]
    n = math.hypot(dx, dy) or 1.0
    tip = (wrist[0] + dx / n * 20, wrist[1] + dy / n * 20)
    return limb([wrist, tip], [R["wrist"] + 3, R["wrist"] + 1], skin)


def blob(d, fill, sw=None):
    sw = S["contour"] if sw is None else sw
    return f'<path d="{d}" fill="{fill}" stroke="{S["ink"]}" stroke-width="{sw}" stroke-linejoin="round"/>'


def shoe(ankle, ang, far=False):
    ax, ay = ankle
    d = "M -22 -14 L 18 -14 Q 50 -10 54 10 Q 54 18 40 18 L -22 18 Q -34 4 -22 -14 Z"
    return (f'<g transform="translate({ax:.1f},{ay:.1f}) rotate({ang})">'
            f'{blob(d, S["shoe_far"] if far else S["shoe"])}</g>')


# ---------------------------------------------------------------- le torse

# Profils de largeur le long de l'axe épaules(0) -> bassin(1), prolongé à 1.18.
# AVANT et ARRIÈRE sont indépendants : c'est ce qui donne un profil féminin plutôt
# qu'un tube symétrique. Le creux de taille est le même sur les deux profils (0.60).
FRONT = [(0.00, 26), (0.14, 38), (0.30, 47), (0.44, 38), (0.60, 27), (0.78, 33), (1.00, 40), (1.18, 34)]
BACK = [(0.00, 34), (0.16, 31), (0.38, 29), (0.60, 30), (0.80, 47), (1.00, 54), (1.18, 44)]


def _w(profile, t):
    for i in range(len(profile) - 1):
        (t0, w0), (t1, w1) = profile[i], profile[i + 1]
        if t0 <= t <= t1:
            k = (t - t0) / (t1 - t0)
            k = k * k * (3 - 2 * k)                 # lissage : pas d'angle au raccord
            return w0 + (w1 - w0) * k
    return profile[-1][1]


def torso_outline(shoulder, hip, t0=0.0, t1=1.18, n=44, inset=0.0):
    sx, sy = shoulder; hx, hy = hip
    dx, dy = hx - sx, hy - sy
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux                                # normale = l'AVANT (côté du regard)
    pts_f, pts_b = [], []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        cx, cy = sx + ux * L * t, sy + uy * L * t
        wf, wb = max(_w(FRONT, t) - inset, 2), max(_w(BACK, t) - inset, 2)
        pts_f.append((cx + nx * wf, cy + ny * wf))
        pts_b.append((cx - nx * wb, cy - ny * wb))
    pts = pts_f + pts_b[::-1]
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"


# ---------------------------------------------------------------- la tête

def head(J, ang=0.0):
    """Profil manga : front bombé, nez COURT, menton pointu, gros œil en amande.
    C'est l'inverse exact de l'école gros-nez — si le nez dépasse, ce n'est plus du manga."""
    hx, hy = J["head"]
    ink, sw = S["ink"], S["contour"]
    skull = ("M 0 -50 Q 30 -49 40 -28 Q 47 -15 40 -7 L 49 8 L 38 12 "
             "Q 45 16 40 20 Q 35 24 39 28 Q 41 39 25 47 Q 5 55 -14 41 "
             "Q -33 28 -41 5 Q -49 -20 -30 -41 Q -17 -52 0 -50 Z")
    tail = ("M -36 -30 Q -100 -40 -126 22 Q -134 48 -116 54 "
            "Q -110 22 -82 8 Q -54 -4 -36 -30 Z")
    cap = ("M -44 -4 Q -52 -46 -16 -55 Q 20 -59 42 -32 "
           "Q 20 -43 -4 -39 Q -30 -35 -33 -2 Z")
    bang = "M 42 -32 Q 30 -20 35 -8 Q 27 -22 18 -28 Z"
    g = [blob(tail, S["hair_far"]),
         blob(skull, S["skin"]),
         f'<path d="M 13 -17 Q 26 -24 37 -11 Q 26 -6 15 -9 Z" fill="{S["eye_white"]}" '
         f'stroke="{ink}" stroke-width="{sw*0.62:.1f}" stroke-linejoin="round"/>',
         f'<circle cx="30" cy="-12" r="5.6" fill="{ink}"/>',
         f'<circle cx="32" cy="-14" r="1.9" fill="#FFFFFF"/>',
         f'<path d="M 12 -27 Q 25 -33 38 -25" fill="none" stroke="{ink}" '
         f'stroke-width="{sw*0.72:.1f}" stroke-linecap="round"/>',
         f'<path d="M 34 23 L 41 24" fill="none" stroke="{ink}" '
         f'stroke-width="{sw*0.6:.1f}" stroke-linecap="round"/>',
         blob(cap, S["hair"]), blob(bang, S["hair"])]
    return (f'<g transform="translate({hx:.1f},{hy:.1f}) rotate({ang})">'
            f'{"".join(g)}</g>')


# ---------------------------------------------------------------- contrôles

def angle_at(a, b, c):
    v1, v2 = (a[0] - b[0], a[1] - b[1]), (c[0] - b[0], c[1] - b[1])
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if not n1 or not n2:
        return 180.0
    return math.degrees(math.acos(max(-1, min(1, (v1[0]*v2[0] + v1[1]*v2[1]) / (n1*n2)))))


def check(J):
    """Sur une figure à 7 têtes, la faute qui saute aux yeux n'est plus la même que sur
    un cartoon : ce sont les LONGUEURS D'OS. Un fémur et un tibia qui ne font pas la même
    longueur d'une pose à l'autre, et le personnage n'est plus le même."""
    warn = []
    if [k for k in JOINTS if k not in J]:
        return [f"articulations manquantes : {', '.join(k for k in JOINTS if k not in J)}"]
    if (d := math.dist(J["neck"], J["head"])) < NECK_MIN:
        warn.append(f"cou {d:.0f}px < {NECK_MIN} — le crâne mange le cou")
    for side in "RL":
        for tag, (a, b, c) in {"genou": (f"hip{side}", f"knee{side}", f"ankle{side}"),
                               "coude": (f"shoulder{side}", f"elbow{side}", f"wrist{side}")}.items():
            if (ang := angle_at(J[a], J[b], J[c])) < LIMB_MIN_ANGLE:
                warn.append(f"{tag} {side} à {ang:.0f}° < {LIMB_MIN_ANGLE}° — segments fusionnés")
    for tag, (a, b), ref in (("fémur", ("hip", "knee"), 180), ("tibia", ("knee", "ankle"), 175),
                             ("bras", ("shoulder", "elbow"), 128), ("avant-bras", ("elbow", "wrist"), 118)):
        for side in "RL":
            d = math.dist(J[f"{a}{side}"], J[f"{b}{side}"])
            if abs(d - ref) > ref * 0.14:
                warn.append(f"{tag} {side} = {d:.0f}px (attendu ~{ref}) — proportions cassées")
    for side in "RL":
        if J[f"ankle{side}"][1] + R["ankle"] + 18 > GROUND + 14:
            warn.append(f"pied {side} sous le sol")
    return warn


# ---------------------------------------------------------------- la figure

def figure(J):
    p = []
    # --- membres lointains ---
    p.append(shoe(J["ankleL"], J["footL"], far=True))
    p.append(leg(J["hipL"], J["kneeL"], J["ankleL"], S["skin_far"], S["short_far"]))
    p.append(limb([J["shoulderL"], J["elbowL"], J["wristL"]],
                  [R["shoulder"], R["elbow"], R["wrist"]], S["skin_far"]))
    p.append(hand(J["wristL"], J["elbowL"], S["skin_far"]))

    # --- cou avant le torse : il sort des épaules, il ne se pose pas dessus ---
    p.append(limb([J["shoulder"], J["neck"]], [R["neck"] + 3, R["neck"]], S["skin"]))

    # --- torse : chair d'abord, vêtements ensuite (le ventre reste nu) ---
    sh, hp = J["shoulder"], J["hip"]
    p.append(blob(torso_outline(sh, hp), S["skin"]))
    p.append(f'<path d="{torso_outline(sh, hp, 0.10, 0.46, inset=-1)}" fill="{S["bra"]}"/>')
    p.append(f'<path d="{torso_outline(sh, hp, 0.78, 1.18, inset=-1)}" fill="{S["short"]}"/>')
    p.append(blob(torso_outline(sh, hp), "none"))          # le contour repasse par-dessus

    # --- membres proches ---
    p.append(shoe(J["ankleR"], J["footR"]))
    p.append(leg(J["hipR"], J["kneeR"], J["ankleR"], S["skin"], S["short"]))
    p.append(head(J, J.get("headAng", 0)))
    p.append(limb([J["shoulderR"], J["elbowR"], J["wristR"]],
                  [R["shoulder"], R["elbow"], R["wrist"]], S["skin"]))
    p.append(hand(J["wristR"], J["elbowR"], S["skin"]))
    return "".join(p)


# ---------------------------------------------------------------- les poses

POSES = {
    "SQUAT": dict(
        ankleR=(430, 872), kneeR=(480, 705), hipR=(302, 715), footR=0,
        ankleL=(382, 860), kneeL=(432, 693), hipL=(254, 703), footL=0,
        shoulderR=(397, 580), elbowR=(510, 622), wristR=(606, 548),
        shoulderL=(373, 596), elbowL=(476, 650), wristL=(566, 600),
        hip=(302, 715), shoulder=(397, 580), neck=(418, 552), head=(452, 484),
        headAng=-6, vb=(150, 380, 560, 560)),

    "FENTE": dict(
        ankleR=(520, 872), kneeR=(516, 697), hipR=(338, 710), footR=0,
        ankleL=(68, 828), kneeL=(238, 866), hipL=(306, 700), footL=104,
        shoulderR=(345, 543), elbowR=(365, 672), wristR=(356, 790),
        shoulderL=(322, 556), elbowL=(342, 684), wristL=(334, 800),
        hip=(316, 706), shoulder=(345, 543), neck=(352, 508), head=(372, 436),
        headAng=0, vb=(30, 330, 620, 620)),

    "GAINAGE": dict(
        ankleR=(188, 845), kneeR=(357, 783), hipR=(531, 719), footR=104,
        ankleL=(176, 858), kneeL=(345, 796), hipL=(519, 732), footL=104,
        shoulderR=(690, 660), elbowR=(700, 780), wristR=(698, 898),
        shoulderL=(672, 674), elbowL=(682, 792), wristL=(680, 898),
        hip=(531, 719), shoulder=(690, 660), neck=(728, 646), head=(790, 620),
        headAng=-14, vb=(100, 500, 880, 440)),
}


def svg_of(name, J=None):
    J = J or POSES[name]
    x, y, w, h = J.get("vb", (110, 320, 620, 620))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" '
            f'width="{w}" height="{h}">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{S["paper"]}"/>'
            f'<path d="M {x+18} {GROUND} L {x+w-18} {GROUND}" stroke="{S["ink"]}" '
            f'stroke-width="7" stroke-linecap="round" opacity="0.25"/>'
            f'{figure(J)}</svg>')


def sheet_html(names, h=620):
    cells = []
    for n in names:
        x, y, w, hh = POSES[n]["vb"]
        cells.append(f'<figure style="width:{w*h/hh:.0f}px">{svg_of(n)}'
                     f'<figcaption>{n}</figcaption></figure>')
    return f"""<!doctype html><meta charset="utf-8"><style>
*{{box-sizing:border-box}} body{{margin:0;padding:16px;background:#20242A;
font:700 15px/1.2 'Helvetica Neue',Arial,sans-serif;color:#F7F4EE}}
.g{{display:flex;gap:14px;align-items:flex-start}}
figure{{margin:0}} svg{{width:100%;height:{h}px;display:block;border:1px solid #474D50}}
figcaption{{padding-top:7px;text-align:center;letter-spacing:2px}}
</style><div class="g">{''.join(cells)}</div>"""


def main():
    global S
    ap = argparse.ArgumentParser(description="Dessine la figure (manga/comics) dans une ou plusieurs poses.")
    ap.add_argument("-p", "--poses", nargs="+", default=list(POSES))
    ap.add_argument("-s", "--style", choices=list(STYLES), default="manga")
    ap.add_argument("-o", "--out", type=pathlib.Path, default=pathlib.Path("/tmp/dessin/figure.png"))
    ap.add_argument("--svg", metavar="POSE")
    args = ap.parse_args()
    S = STYLES[args.style]

    if args.svg:
        print(svg_of(args.svg)); return
    if unknown := [n for n in args.poses if n not in POSES]:
        sys.exit(f"pose inconnue : {', '.join(unknown)}")

    ko = False
    for n in args.poses:
        for w in check(POSES[n]):
            print(f"  ⚠ {n}: {w}"); ko = True
    if not ko:
        print("  squelettes ✓ (os cohérents, cou dégagé, articulations ouvertes, pieds au sol)")

    H = 620
    args.out.parent.mkdir(parents=True, exist_ok=True)
    html = args.out.parent / "_figure.html"
    html.write_text(sheet_html(args.poses, H))
    W = sum(POSES[n]["vb"][2] * H / POSES[n]["vb"][3] for n in args.poses)
    W = int(W + 14 * (len(args.poses) - 1) + 32)
    if frames.shoot(frames.find_chrome(), f"file://{html}", args.out, (W, H + 60)):
        print(f"→ {args.out}  ({args.style})")
    else:
        sys.exit("rendu échoué")


if __name__ == "__main__":
    main()
