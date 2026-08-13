#!/usr/bin/env python3
"""
DESSIN — athlete.py — LA FIGURE MUSCLÉE, DE FACE, EN COULEUR.

Pourquoi un quatrième module et pas une pose de plus dans figure.py : le rig est un
squelette 2D DE PROFIL. Un buste de trois quarts ne s'en déduit pas — il se CONSTRUIT.
Ici le torse est un tracé dessiné (V dorsal, taille creusée, évasement des hanches) et
non une largeur déduite d'un os, et l'anatomie est posée trait par trait.

CE QUI FAIT « MUSCLÉ », dans l'ordre d'importance — aucun n'est décoratif :
  1. LE V DORSAL. Épaules larges, taille étroite, hanches qui s'évasent. Le rapport
     taille/épaules fait plus pour la lecture « athlète » que tous les traits d'abdos.
  2. LES DELTOÏDES EN CAPUCHON. Une masse ronde POSÉE sur l'épaule, séparée du bras par
     un trait. Sans elle, un bras large lit comme gras, pas comme musclé.
  3. LES LIGNES D'ANATOMIE : clavicules, sternum, ligne blanche, trois refends d'abdos,
     obliques, dentelé, V des fléchisseurs de hanche, biceps, avant-bras.
  4. LE CEL-SHADING À DEUX TONS. Une seule source, une teinte d'ombre franche par
     matière. Un dégradé ferait de la 3D, pas de la BD.

USAGE
  python3 dessin/athlete.py                 # le buste
  python3 dessin/athlete.py --svg > a.svg
"""
from __future__ import annotations

import argparse
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "ligne"))
import frames                                     # noqa: E402
from encre import brush, arc_pts                  # noqa: E402  (le trait fuselé)
from figure import capsule, chain_d               # noqa: E402

W, H = 900, 1120
CX = 450                       # axe du corps

INK = "#2A1A12"
PAL = dict(
    skin="#E9A97B", skin_sh="#CB855A", skin_hi="#F6CCA4",
    bra="#4E8FA6", bra_sh="#3A7085",
    legging="#2F3A4B", legging_sh="#222B39",
    hair="#D9B45C", hair_sh="#AE8B39", hair_hi="#F0DB9B",
    paper="#F5F2EB", mouth="#B4574F", eye="#3E6C7A")
CONTOUR = 7


def P(*pts):
    return " ".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def outline(d, fill, sw=CONTOUR):
    return (f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="{sw}" '
            f'stroke-linejoin="round" stroke-linecap="round"/>')


def clip(uid, d, inner):
    return (f'<clipPath id="{uid}"><path d="{d}"/></clipPath>'
            f'<g clip-path="url(#{uid})">{inner}</g>')


def limb(pts, radii, color):
    """Bras et cuisses : capsules fuselées, deux passes (encre puis chair)."""
    d = chain_d(pts, radii)
    return (f'<path d="{chain_d(pts, radii, CONTOUR)}" fill="{INK}"/>'
            f'<path d="{d}" fill="{color}"/>'), d


# ---------------------------------------------------------------- le torse

# Demi-largeurs le long du corps. C'est CE tableau qui fait l'athlète : 188 aux épaules,
# 76 à la taille, 120 aux hanches. Un torse qui ne se resserre pas n'est pas musclé.
PROFILE = [(330, 50), (372, 128), (404, 176), (438, 188), (508, 140), (572, 104),
           (648, 78), (716, 104), (772, 126), (860, 132), (908, 128)]


def half(y):
    for i in range(len(PROFILE) - 1):
        (y0, w0), (y1, w1) = PROFILE[i], PROFILE[i + 1]
        if y0 <= y <= y1:
            k = (y - y0) / (y1 - y0)
            k = k * k * (3 - 2 * k)
            return w0 + (w1 - w0) * k
    return PROFILE[-1][1]


def torso_d(y0=330, y1=906, n=52):
    right = [(CX + half(y0 + (y1 - y0) * i / n), y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    left = [(CX - half(y0 + (y1 - y0) * i / n), y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    return "M " + P(*right) + " L " + P(*reversed(left)) + " Z"


def anatomy():
    """Les traits qui disent le muscle. Chacun est un coup de pinceau fuselé : un trait
    d'épaisseur constante lirait comme un trait de construction, pas comme un sillon."""
    o = []
    # clavicules — elles ouvrent la poitrine et posent la largeur d'épaules
    o.append(brush(arc_pts((CX - 20, 416), (CX - 132, 400), bow=20), 7.5, .8, .45))
    o.append(brush(arc_pts((CX + 20, 416), (CX + 132, 400), bow=-20), 7.5, .8, .45))
    o.append(brush(arc_pts((CX, 422), (CX, 456), bow=0), 5.0, .6, .8))          # sternum
    # sous-poitrine
    o.append(brush(arc_pts((CX - 118, 500), (CX - 20, 545), bow=-26), 8.0, .7, .6))
    o.append(brush(arc_pts((CX + 118, 500), (CX + 20, 545), bow=26), 8.0, .7, .6))
    # dentelé antérieur : trois griffes sous chaque aisselle
    for k, ty in enumerate((548, 578, 606)):
        w = 30 - k * 5
        o.append(brush(arc_pts((CX - 104 + k * 6, ty), (CX - 104 + k * 6 - w, ty - 12), bow=3), 5.0, .5, .85))
        o.append(brush(arc_pts((CX + 104 - k * 6, ty), (CX + 104 - k * 6 + w, ty - 12), bow=-3), 5.0, .5, .85))
    # ligne blanche + trois refends d'abdos
    o.append(brush(arc_pts((CX, 556), (CX, 716), bow=0), 6.0, .75, .75))
    for ty, w in ((594, 60), (640, 56), (686, 48)):
        o.append(brush(arc_pts((CX - 6, ty), (CX - w, ty - 8), bow=6), 6.0, .55, .9))
        o.append(brush(arc_pts((CX + 6, ty), (CX + w, ty - 8), bow=-6), 6.0, .55, .9))
    # V des fléchisseurs de hanche — le trait le plus « athlète » du bas du torse
    o.append(brush(arc_pts((CX - 96, 742), (CX - 24, 830), bow=-14), 8.5, .8, .5))
    o.append(brush(arc_pts((CX + 96, 742), (CX + 24, 830), bow=14), 8.5, .8, .5))
    # obliques
    o.append(brush(arc_pts((CX - 92, 636), (CX - 74, 712), bow=-10), 5.5, .6, .8))
    o.append(brush(arc_pts((CX + 92, 636), (CX + 74, 712), bow=10), 5.5, .6, .8))
    return "".join(o)


# ---------------------------------------------------------------- la tête

def head():
    hx, hy = CX + 6, 232
    skull = ("M -78 -20 Q -80 -104 0 -110 Q 80 -104 78 -20 "
             "Q 76 22 62 44 Q 44 88 0 100 Q -44 88 -62 44 Q -76 22 -78 -20 Z")
    g = [outline(skull, PAL["skin"])]
    # cel-shading : côté opposé à la lumière (elle vient de la gauche du spectateur)
    g.append(clip("hd", skull,
                  f'<path d="M 18 -112 Q 96 -60 84 40 Q 70 96 6 104 L 100 104 L 100 -112 Z" '
                  f'fill="{PAL["skin_sh"]}"/>'))
    # yeux : amande + iris + cil lourd. Deux yeux = vue de face, la moitié du travail.
    for s in (-1, 1):
        ex = 38 * s
        g.append(f'<path d="M {ex-26} -12 Q {ex} -30 {ex+26} -12 Q {ex} 4 {ex-26} -12 Z" '
                 f'fill="#FFFFFF" stroke="{INK}" stroke-width="4"/>')
        g.append(f'<circle cx="{ex+2*s}" cy="-14" r="10" fill="{PAL["eye"]}"/>')
        g.append(f'<circle cx="{ex+2*s}" cy="-14" r="4.5" fill="{INK}"/>')
        g.append(f'<circle cx="{ex+6*s}" cy="-18" r="3" fill="#FFFFFF"/>')
        g.append(brush(arc_pts((ex - 28, -16), (ex + 28, -14), bow=-9 * s), 7.0, .5, .7))
        g.append(brush(arc_pts((ex - 30, -44), (ex + 26, -40), bow=-8), 6.5, .6, .8))
    g.append(brush(arc_pts((6, -4), (14, 26), bow=4), 4.5, .8, .7))            # nez
    g.append(brush(arc_pts((2, 30), (16, 30), bow=0), 4.0, .6, .8))
    g.append(f'<path d="M -18 52 Q 0 46 20 52 Q 2 68 -18 52 Z" fill="{PAL["mouth"]}" '
             f'stroke="{INK}" stroke-width="4.5" stroke-linejoin="round"/>')
    hair_back = ("M -84 -26 Q -96 -118 0 -126 Q 96 -118 84 -26 "
                 "Q 78 -70 40 -84 Q 0 -96 -40 -84 Q -78 -70 -84 -26 Z")
    tail = ("M 40 -104 Q 150 -140 196 -60 Q 226 -6 206 66 Q 190 8 154 -24 "
            "Q 110 -62 40 -104 Z")
    g.insert(0, outline(tail, PAL["hair"]))
    g.insert(1, clip("ht", tail, f'<path d="M 120 -120 L 240 -120 L 240 90 L 150 90 Z" '
                                 f'fill="{PAL["hair_sh"]}"/>'))
    g.append(outline(hair_back, PAL["hair"]))
    g.append(clip("hb", hair_back,
                  f'<path d="M 20 -130 L 110 -130 L 110 10 L 40 10 Z" fill="{PAL["hair_sh"]}"/>'))
    for a, b, bw in (((-70, -60), (-14, -104), 10), ((-40, -78), (24, -108), 8),
                     ((30, -104), (74, -66), -8)):
        g.append(brush(arc_pts(a, b, bow=bw), 6.0, .6, .8))
    return f'<g transform="translate({hx},{hy})">{"".join(g)}</g>'


# ---------------------------------------------------------------- la figure

def figure():
    o = []
    dt = torso_d()
    art, dn = limb([(CX + 6, 306), (CX + 2, 396)], [46, 54], PAL["skin"])
    o.append(art)
    o.append(clip("nk", dn, f'<path d="M {CX+18} 280 L {CX+200} 280 L {CX+200} 430 '
                            f'L {CX+30} 430 Z" fill="{PAL["skin_sh"]}"/>'))

    # --- bras GAUCHE du spectateur : fléchi, poing devant (la pose « athlète ») ---
    aL = [(CX - 168, 424), (CX - 236, 596), (CX - 96, 596)]
    rL = [54, 36, 27]
    art, dL = limb(aL, rL, PAL["skin"])
    o.append(art)
    o.append(clip("al", dL, f'<path d="M {CX-300} 640 L {CX-40} 640 L {CX-40} 700 '
                            f'L {CX-300} 700 Z" fill="{PAL["skin_sh"]}"/>'))
    # --- bras DROIT : le long du corps, poing fermé ---
    aR = [(CX + 168, 424), (CX + 244, 606), (CX + 214, 790)]
    rR = [54, 36, 27]
    art, dR = limb(aR, rR, PAL["skin"])
    o.append(art)

    # --- torse (il s'arrête à la ceinture) ---
    o.append(outline(dt, PAL["skin"]))
    o.append(clip("ts", dt, f'<path d="M {CX+34} 300 Q {CX+120} 620 {CX+70} 1140 '
                            f'L {CX+300} 1140 L {CX+300} 300 Z" fill="{PAL["skin_sh"]}"/>'))

    # --- brassière : deux bonnets + une bande, jamais un rectangle ---
    bra = (f"M {CX-152} 436 Q {CX-118} 400 {CX-56} 424 Q {CX} 452 {CX+56} 424 "
           f"Q {CX+118} 400 {CX+152} 436 "
           f"Q {CX+142} 524 {CX+54} 550 Q {CX} 560 {CX-54} 550 "
           f"Q {CX-142} 524 {CX-152} 436 Z")
    o.append(outline(bra, PAL["bra"]))
    o.append(clip("br", bra, f'<path d="M {CX+10} 390 Q {CX+90} 470 {CX+40} 570 '
                             f'L {CX+200} 570 L {CX+200} 390 Z" fill="{PAL["bra_sh"]}"/>'))
    o.append(brush(arc_pts((CX, 430), (CX, 540), bow=0), 5.0, .7, .7))
    o.append(brush(arc_pts((CX - 150, 430), (CX - 96, 396), bow=6), 8.0, .7, .6))
    o.append(brush(arc_pts((CX + 150, 430), (CX + 96, 396), bow=-6), 8.0, .7, .6))

    # --- cuisses PUIS ceinture : l'ordre décide de qui recouvre qui ---
    for sg in (-1, 1):
        art, dth = limb([(CX + 66 * sg, 876), (CX + 104 * sg, 1140)], [74, 68], PAL["legging"])
        o.append(art)
        o.append(clip(f"th{sg}", dth, f'<path d="M {CX+30*sg} 850 Q {CX+150*sg} 1000 '
                                      f'{CX+110*sg} 1150 L {CX+260*sg} 1150 L {CX+260*sg} 850 Z" '
                                      f'fill="{PAL["legging_sh"]}"/>'))
    belt = (f"M {CX-132} 846 Q {CX} 812 {CX+132} 846 Q {CX+138} 872 {CX+136} 892 "
            f"Q {CX} 858 {CX-136} 892 Q {CX-138} 872 {CX-132} 846 Z")
    o.append(outline(belt, PAL["legging"]))

    o.append(anatomy())

    # --- deltoïdes : POSÉS sur l'épaule, séparés du bras. Sans eux, pas d'athlète. ---
    for s in (-1, 1):
        dd = (f"M {CX+126*s} 396 Q {CX+196*s} 388 {CX+214*s} 452 "
              f"Q {CX+222*s} 508 {CX+168*s} 520 Q {CX+126*s} 498 {CX+126*s} 396 Z")
        o.append(outline(dd, PAL["skin"]))
        o.append(clip(f"dl{s}", dd, f'<path d="M {CX+150*s} 380 Q {CX+230*s} 440 '
                                    f'{CX+180*s} 530 L {CX+260*s} 530 L {CX+260*s} 380 Z" '
                                    f'fill="{PAL["skin_sh"]}"/>'))
        o.append(brush(arc_pts((CX + 138 * s, 442), (CX + 190 * s, 486), bow=8 * s), 6.0, .6, .8))

    # --- biceps du bras fléchi + poings ---
    o.append(brush(arc_pts((CX - 196, 470), (CX - 226, 556), bow=-12), 7.0, .7, .7))
    for c in ((CX - 96, 596), (CX + 214, 790)):
        o.append(outline(f'M {c[0]-34} {c[1]-30} Q {c[0]+36} {c[1]-36} {c[0]+36} {c[1]+4} '
                         f'Q {c[0]+30} {c[1]+40} {c[0]-14} {c[1]+36} '
                         f'Q {c[0]-42} {c[1]+22} {c[0]-34} {c[1]-30} Z', PAL["skin"]))
        for k in range(2):
            o.append(brush(arc_pts((c[0] - 10 + k * 22, c[1] - 20), (c[0] - 6 + k * 22, c[1] + 2),
                                   bow=4), 4.5, .6, .8))
    return "".join(o)


def svg():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="{PAL["paper"]}"/>'
            f'{figure()}{head()}</svg>')


def main():
    ap = argparse.ArgumentParser(description="Figure musclée de face, en couleur.")
    ap.add_argument("-o", "--out", type=pathlib.Path, default=pathlib.Path("/tmp/dessin/athlete.png"))
    ap.add_argument("--svg", action="store_true")
    a = ap.parse_args()
    if a.svg:
        print(svg()); return
    a.out.parent.mkdir(parents=True, exist_ok=True)
    f = a.out.parent / "_athlete.html"
    f.write_text(f'<!doctype html><meta charset="utf-8"><style>body{{margin:0}}</style>{svg()}')
    if frames.shoot(frames.find_chrome(), f"file://{f}", a.out, (W, H)):
        print(f"→ {a.out}")
    else:
        sys.exit("rendu échoué")


if __name__ == "__main__":
    main()
