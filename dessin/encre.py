#!/usr/bin/env python3
"""
DESSIN — encre.py — LE TRAIT (line art noir et blanc).

Un troisième langage, et le plus proche de l'illustration fitness de référence :
noir et blanc pur, corps laissé BLANC, aucune teinte. Tout est dit par le trait.

CE QUI LE SÉPARE DE figure.py (aplat + ombre)
  · LE TRAIT FUSELÉ est la brique de base. Un trait d'encre naît fin, enfle, meurt en
    pointe. C'est LUI qui fait « dessiné » — pas la couleur, pas l'ombre portée. Un
    contour d'épaisseur constante trahit l'ordinateur en une fraction de seconde.
  · LES LIGNES D'ANATOMIE INTÉRIEURES portent le volume : abdominaux, ligne blanche,
    sillon des quadriceps, deltoïde, genou, mollet, clavicule. Sans elles, une silhouette
    blanche reste une découpe, quelle que soit la finesse du contour.
  · LES APLATS NOIRS (cheveux, brassière, short) donnent le poids et le contraste. Un
    dessin sans masse noire reste un croquis.

USAGE
  python3 dessin/encre.py                # planche des poses
  python3 dessin/encre.py -p SQUAT
  python3 dessin/encre.py --svg SQUAT > squat.svg

Le squelette et les poses viennent de figure.py — un seul rig, trois rendus.
"""
from __future__ import annotations

import argparse
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "ligne"))
import frames                                                   # noqa: E402
from figure import POSES, R, GROUND, chain_d, torso_outline, check, _lerp   # noqa: E402

INK = "#101014"
PAPER = "#FFFFFF"
CONTOUR = 3.4


# ============================================================== LE TRAIT FUSELÉ

def _resample(pts, n):
    """Rééchantillonne une polyligne à pas constant : sans ça, l'épaisseur du trait
    suivrait la densité des points d'entrée au lieu de la longueur parcourue."""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg) or 1.0
    out, acc = [pts[0]], 0.0
    for k in range(1, n):
        target, i, run = total * k / n, 0, 0.0
        while i < len(seg) - 1 and run + seg[i] < target:
            run += seg[i]; i += 1
        u = (target - run) / (seg[i] or 1.0)
        out.append(_lerp(pts[i], pts[i + 1], min(max(u, 0), 1)))
    out.append(pts[-1])
    return out


def _smooth(pts, k=2):
    for _ in range(k):
        pts = [pts[0]] + [((pts[i-1][0] + 2*pts[i][0] + pts[i+1][0]) / 4,
                           (pts[i-1][1] + 2*pts[i][1] + pts[i+1][1]) / 4)
                          for i in range(1, len(pts) - 1)] + [pts[-1]]
    return pts


def brush(pts, w, a=0.55, b=0.55, n=26):
    """UN COUP DE PINCEAU. Le profil d'épaisseur t^a·(1-t)^b, normalisé, naît en pointe,
    enfle, meurt en pointe. `a` petit = attaque franche ; `b` petit = fin franche.
    C'est la primitive dont tout le reste découle."""
    if len(pts) < 2:
        return ""
    P = _smooth(_resample(list(pts), n))
    peak = (a / (a + b)) if (a + b) else 0.5
    norm = (peak ** a) * ((1 - peak) ** b) or 1.0
    left, right = [], []
    for i, p in enumerate(P):
        t = i / (len(P) - 1)
        q = P[min(i + 1, len(P) - 1)]; r = P[max(i - 1, 0)]
        dx, dy = q[0] - r[0], q[1] - r[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        hw = w * ((t ** a) * ((1 - t) ** b)) / norm / 2
        left.append((p[0] + nx * hw, p[1] + ny * hw))
        right.append((p[0] - nx * hw, p[1] - ny * hw))
    pth = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in left)
    pth += " L " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in reversed(right)) + " Z"
    return f'<path d="{pth}" fill="{INK}"/>'


def arc_pts(a, b, bow=0.0, n=9):
    """Trois points -> une courbe. `bow` = flèche latérale ; un trait d'anatomie n'est
    jamais droit, c'est ce qui le distingue d'un trait de construction."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    cx, cy = mx - dy / L * bow, my + dx / L * bow
    return [((1-t)**2 * a[0] + 2*(1-t)*t*cx + t*t*b[0],
             (1-t)**2 * a[1] + 2*(1-t)*t*cy + t*t*b[1]) for t in
            [i / (n - 1) for i in range(n)]]


def along(a, b, t, off=0.0):
    """Un point à la fraction t d'un os, décalé latéralement de `off`."""
    p = _lerp(a, b, t)
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    return (p[0] - dy / L * off, p[1] + dx / L * off)


# ============================================================== les volumes

def silhouette(d):
    """Pour un tracé SIMPLE (torse, crâne, chaussure) : blanc + contour."""
    return (f'<path d="{d}" fill="{PAPER}" stroke="{INK}" stroke-width="{CONTOUR}" '
            f'stroke-linejoin="round"/>')


def silhouette_chain(joints, radii):
    """Pour un tracé COMPOSÉ (un membre = capsules + disques qui se recouvrent) :
    JAMAIS un stroke — il tracerait le contour de chaque sous-chemin et ferait
    apparaître les articulations en bulles. Deux passes pleines : encre élargie,
    puis papier. Seule la frontière extérieure survit."""
    return (f'<path d="{chain_d(joints, radii, CONTOUR)}" fill="{INK}"/>'
            f'<path d="{chain_d(joints, radii)}" fill="{PAPER}"/>')


def spot(d):
    """Aplat noir : cheveux, brassière, short. C'est la masse qui donne le poids."""
    return f'<path d="{d}" fill="{INK}"/>'


def limb_art(joints, radii, side=1):
    """Membre : silhouette blanche, puis les traits qui la font exister. Le trait de
    galbe suit le bord OPPOSÉ à la lumière, celui du muscle court à l'intérieur."""
    out = [silhouette_chain(joints, radii)]
    for i in range(len(joints) - 1):
        a, b, r = joints[i], joints[i + 1], radii[i]
        # UN SEUL trait par segment : le galbe, posé en dedans du bord d'ombre.
        # Deux traits parallèles par membre ne lisent pas comme du muscle mais comme
        # des griffures — le bruit se voit à l'image, jamais dans le code.
        out.append(brush(arc_pts(along(a, b, 0.20, r * 0.60 * side),
                                 along(a, b, 0.84, radii[i+1] * 0.55 * side),
                                 bow=5 * side), 6.4, 0.75, 0.45))
    return "".join(out)


def knee_art(knee, hip, ankle):
    p = along(knee, ankle, 0.10, R["knee"] * 0.5)
    q = along(knee, ankle, 0.30, -R["knee"] * 0.25)
    return brush(arc_pts(p, q, bow=4), 4.2, 0.5, 0.8)


def abdomen(sh, hp):
    """Les abdominaux : une LIGNE BLANCHE verticale et des refends courts de part et
    d'autre. C'est le détail qui fait basculer un torse de « forme » à « corps »."""
    out = []
    mid_a, mid_b = _lerp(sh, hp, 0.44), _lerp(sh, hp, 0.90)
    out.append(brush(arc_pts(mid_a, mid_b, bow=3), 3.6, 0.8, 0.8))
    for t in (0.54, 0.66, 0.78):
        for s in (1, -1):
            a = along(sh, hp, t, 4 * s)
            b = along(sh, hp, t + 0.015, 21 * s)
            out.append(brush(arc_pts(a, b, bow=2 * s), 3.6, 0.45, 0.9))
    # pli de la taille + arc du bassin
    out.append(brush(arc_pts(along(sh, hp, 0.60, 26), along(sh, hp, 0.66, 40), bow=3), 3.2, .5, .9))
    out.append(brush(arc_pts(along(sh, hp, 0.88, 30), along(sh, hp, 0.98, 44), bow=5), 4.0, .5, .8))
    return "".join(out)


def bust(sh, hp):
    """Sous-poitrine et sternum : deux courbes, jamais un cercle."""
    return (brush(arc_pts(along(sh, hp, 0.20, 16), along(sh, hp, 0.42, 40), bow=-11), 5.4, .6, .7)
            + brush(arc_pts(along(sh, hp, 0.16, 6), along(sh, hp, 0.34, 12), bow=-4), 3.0, .7, .8))


def collar(sh, hp, neck):
    return brush(arc_pts(along(sh, hp, 0.03, -22), along(sh, hp, 0.10, 26), bow=6), 4.0, .5, .8)


def head_art(J, ang=0.0):
    """Profil : contour blanc, aplat noir des cheveux, et les traits du visage. Les
    mèches se disent en RÉSERVES BLANCHES dans le noir, jamais en traits sur du blanc."""
    hx, hy = J["head"]
    skull = ("M 0 -50 Q 30 -49 40 -28 Q 47 -15 40 -7 L 49 8 L 38 12 "
             "Q 45 16 40 20 Q 35 24 39 28 Q 41 39 25 47 Q 5 55 -14 41 "
             "Q -33 28 -41 5 Q -49 -20 -30 -41 Q -17 -52 0 -50 Z")
    hair = ("M -44 -2 Q -56 -48 -16 -57 Q 24 -61 43 -30 Q 22 -44 -2 -40 "
            "Q -20 -37 -27 -22 Q -30 -8 -26 4 Q -40 -6 -33 -30 "
            "Q -52 -20 -44 -2 Z")
    tail = ("M -30 -34 Q -104 -42 -130 24 Q -140 54 -118 58 "
            "Q -112 24 -84 8 Q -50 -8 -30 -34 Z")
    g = [spot(tail), silhouette(skull), spot(hair),
         # réserves blanches = les mèches
         f'<path d="M -118 40 Q -104 8 -78 -8" fill="none" stroke="{PAPER}" '
         f'stroke-width="4" stroke-linecap="round"/>',
         f'<path d="M -108 44 Q -92 14 -66 -2" fill="none" stroke="{PAPER}" '
         f'stroke-width="2.6" stroke-linecap="round"/>',
         # oeil : paupière lourde, iris, cil
         brush(arc_pts((13, -18), (37, -11), bow=-5), 4.6, .5, .85),
         f'<ellipse cx="27" cy="-11" rx="5.4" ry="6.2" fill="{INK}"/>',
         f'<circle cx="29" cy="-13" r="1.7" fill="{PAPER}"/>',
         brush(arc_pts((36, -13), (43, -17), bow=-2), 3.4, .4, .9),
         brush(arc_pts((11, -28), (37, -25), bow=-4), 3.8, .6, .8),      # sourcil
         brush(arc_pts((36, 21), (43, 23), bow=-1.5), 3.0, .5, .8),      # bouche
         brush(arc_pts((30, 44), (6, 50), bow=3), 3.0, .6, .8),          # menton/mâchoire
         brush(arc_pts((-4, 34), (-16, 24), bow=-3), 2.6, .6, .8)]       # oreille
    return (f'<g transform="translate({hx:.1f},{hy:.1f}) rotate({ang})">'
            f'{"".join(g)}</g>')


def shoe_art(ankle, ang):
    ax, ay = ankle
    d = "M -22 -14 L 18 -14 Q 50 -10 54 10 Q 54 18 40 18 L -22 18 Q -34 4 -22 -14 Z"
    lace = brush(arc_pts((-4, -10), (26, -6), bow=3), 3.2, .5, .8)
    sole = f'<path d="M -30 12 L 52 12 Q 54 18 40 18 L -22 18 Q -32 16 -30 12 Z" fill="{INK}"/>'
    return (f'<g transform="translate({ax:.1f},{ay:.1f}) rotate({ang})">'
            f'{silhouette(d)}{sole}{lace}</g>')


# ============================================================== la figure

def figure_art(J):
    p = []
    LR, AR = [R["hip"], R["knee"], R["ankle"]], [R["shoulder"], R["elbow"], R["wrist"]]
    p.append(shoe_art(J["ankleL"], J["footL"]))
    p.append(limb_art([J["hipL"], J["kneeL"], J["ankleL"]], LR, -1))
    p.append(limb_art([J["shoulderL"], J["elbowL"], J["wristL"]], AR, -1))

    sh, hp = J["shoulder"], J["hip"]
    p.append(silhouette_chain([sh, J["neck"]], [R["neck"] + 3, R["neck"]]))
    dt = torso_outline(sh, hp)
    p.append(silhouette(dt))
    p.append(spot(torso_outline(sh, hp, 0.10, 0.46, inset=-1)))       # brassière
    p.append(spot(torso_outline(sh, hp, 0.80, 1.18, inset=-1)))       # short
    p.append(bust(sh, hp)); p.append(abdomen(sh, hp)); p.append(collar(sh, hp, J["neck"]))

    p.append(shoe_art(J["ankleR"], J["footR"]))
    p.append(limb_art([J["hipR"], J["kneeR"], J["ankleR"]], LR, 1))
    p.append(knee_art(J["kneeR"], J["hipR"], J["ankleR"]))
    p.append(head_art(J, J.get("headAng", 0)))
    p.append(limb_art([J["shoulderR"], J["elbowR"], J["wristR"]], AR, 1))
    p.append(silhouette_chain([J["wristR"], along(J["elbowR"], J["wristR"], 1.22)],
                              [R["wrist"] + 3, R["wrist"] + 1]))
    p.append(silhouette_chain([J["wristL"], along(J["elbowL"], J["wristL"], 1.22)],
                              [R["wrist"] + 3, R["wrist"] + 1]))
    return "".join(p)


def svg_of(name, J=None):
    J = J or POSES[name]
    x, y, w, h = J.get("vb", (110, 320, 620, 620))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" '
            f'width="{w}" height="{h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="{PAPER}"/>'
            f'{brush(arc_pts((x+30, GROUND), (x+w-30, GROUND), bow=0), 5, .35, .35)}'
            f'{figure_art(J)}</svg>')


def main():
    ap = argparse.ArgumentParser(description="Dessine la figure en line art noir et blanc.")
    ap.add_argument("-p", "--poses", nargs="+", default=list(POSES))
    ap.add_argument("-o", "--out", type=pathlib.Path, default=pathlib.Path("/tmp/dessin/encre.png"))
    ap.add_argument("--svg", metavar="POSE")
    args = ap.parse_args()

    if args.svg:
        print(svg_of(args.svg)); return
    if unknown := [n for n in args.poses if n not in POSES]:
        sys.exit(f"pose inconnue : {', '.join(unknown)}")
    for n in args.poses:
        for w in check(POSES[n]):
            print(f"  ⚠ {n}: {w}")

    H = 620
    cells = "".join(
        f'<figure style="width:{POSES[n]["vb"][2]*H/POSES[n]["vb"][3]:.0f}px">'
        f'{svg_of(n)}<figcaption>{n}</figcaption></figure>' for n in args.poses)
    html = f"""<!doctype html><meta charset="utf-8"><style>
*{{box-sizing:border-box}} body{{margin:0;padding:16px;background:#20242A;
font:700 15px/1.2 'Helvetica Neue',Arial,sans-serif;color:#F7F4EE}}
.g{{display:flex;gap:14px;align-items:flex-start}} figure{{margin:0}}
svg{{width:100%;height:{H}px;display:block;border:1px solid #474D50}}
figcaption{{padding-top:7px;text-align:center;letter-spacing:2px}}
</style><div class="g">{cells}</div>"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    f = args.out.parent / "_encre.html"
    f.write_text(html)
    W = int(sum(POSES[n]["vb"][2] * H / POSES[n]["vb"][3] for n in args.poses)
            + 14 * (len(args.poses) - 1) + 32)
    if frames.shoot(frames.find_chrome(), f"file://{f}", args.out, (W, H + 60)):
        print(f"→ {args.out}")
    else:
        sys.exit("rendu échoué")


if __name__ == "__main__":
    main()
