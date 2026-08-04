#!/usr/bin/env python3
"""Affiche sérigraphie AMADEUS — 3 encres a plat sur papier creme.

Genere un SVG 1000x1500 (ratio 2:3) imitant une serigraphie tiree main :
aplats, trame de points, decalage de reperage, grain papier.

Usage: python3 gen_affiche.py [sortie.svg]
"""
import sys

W, H = 1000, 1500

PAPIER = "#EFE6D2"
NOIR = "#17181D"
ROUGE = "#C3341F"
OR = "#D9A32B"

# ---------------------------------------------------------------- silhouette
# Buste de Mozart de profil, tourne vers la gauche : perruque, queue nouee,
# jabot et col d'habit. Trace en un seul chemin ferme.
SILHOUETTE = (
    "M 512 296 "
    "C 452 296 404 336 394 404 "
    "C 388 440 392 466 402 480 "          # tempe / naissance du front
    "C 396 492 388 500 384 514 "          # front bombe -> arcade
    "C 381 524 386 530 388 534 "          # creux de l'oeil
    "C 382 544 370 556 356 568 "          # arete puis pointe du nez
    "C 352 572 356 576 366 577 "          # narine
    "C 374 578 382 580 386 584 "          # base / philtrum
    "C 380 590 376 596 384 601 "          # levre superieure
    "C 390 605 380 610 386 618 "          # levre inferieure
    "C 390 624 392 630 398 640 "          # creux du menton
    "C 404 654 420 662 446 668 "          # menton
    "C 474 678 496 680 512 682 "          # machoire
    "C 510 706 506 738 500 766 "          # cou (avant)
    "C 478 788 300 840 262 1010 "         # epaule gauche
    "L 262 1180 L 786 1180 "              # base (recoupee par le clavier)
    "C 780 850 630 796 606 780 "          # epaule droite
    "C 600 752 600 726 604 700 "          # cou (arriere)
    "C 652 700 690 668 696 616 "          # bas de perruque
    "C 706 560 704 470 694 428 "          # arriere du crane
    "C 676 344 596 296 512 296 Z"
)

# Rouleaux lateraux de la perruque
BOUCLES = [(662, 548, 54), (672, 616, 48), (652, 486, 44)]

# Queue nouee dans le dos, prise dans son ruban
QUEUE = (
    "M 700 620 C 734 652 748 706 740 762 "
    "C 734 804 720 824 704 830 "
    "C 692 806 690 754 682 712 "
    "C 676 676 684 640 700 620 Z"
)
NOEUD = (
    "M 722 634 C 704 610 692 604 682 610 C 672 618 676 640 688 650 Z "
    "M 722 634 C 742 612 758 608 768 616 C 778 626 770 648 756 654 Z "
    "M 722 634 m -12 0 a 12 12 0 1 0 24 0 a 12 12 0 1 0 -24 0 Z"
)


def clavier(y, hauteur=140, x0=60, x1=940):
    """Bande de clavier : touches creme evidees sur un aplat noir."""
    out = [f'<rect x="0" y="{y}" width="{W}" height="{hauteur}" fill="{NOIR}"/>']
    n = 26
    pas = (x1 - x0) / n
    for i in range(n):
        x = x0 + i * pas
        out.append(
            f'<rect x="{x:.1f}" y="{y + 12}" width="{pas - 6:.1f}" '
            f'height="{hauteur - 24}" fill="{PAPIER}"/>'
        )
    # touches noires : motif 2-3 des octaves
    motif = [0, 1, 3, 4, 5]
    for i in range(n):
        if i % 7 in motif and i < n - 1:
            x = x0 + (i + 1) * pas - pas * 0.30
            out.append(
                f'<rect x="{x:.1f}" y="{y + 12}" width="{pas * 0.56:.1f}" '
                f'height="{(hauteur - 24) * 0.62:.0f}" fill="{NOIR}"/>'
            )
    return "\n    ".join(out)


def trame_disque(cx, cy, r, haut, bas):
    """Fondu tramé : le rouge se dissout en points papier vers le bas."""
    bandes = []
    n = 7
    for i in range(n):
        y0 = haut + (bas - haut) * i / n
        y1 = haut + (bas - haut) * (i + 1) / n
        rayon = 2.0 + 4.6 * (i / (n - 1))
        pas = 15
        pts = []
        yy = y0
        ligne = 0
        while yy < y1:
            xx = cx - r - pas + (pas / 2 if ligne % 2 else 0)
            while xx < cx + r + pas:
                pts.append(f'<circle cx="{xx:.0f}" cy="{yy:.0f}" r="{rayon:.1f}"/>')
                xx += pas
            yy += pas
            ligne += 1
        bandes.append("".join(pts))
    return f'<g fill="{PAPIER}">' + "".join(bandes) + "</g>"


def portee(y, x0=70, x1=930, ecart=17):
    lignes = "".join(
        f'<line x1="{x0}" y1="{y + i * ecart}" x2="{x1}" y2="{y + i * ecart}"/>'
        for i in range(5)
    )
    notes = ""
    for i, (nx, ny) in enumerate(
        [(190, 2), (268, 0), (346, 3), (462, 1), (540, 4), (700, 2), (790, 1)]
    ):
        cy = y + ny * ecart
        notes += (
            f'<ellipse cx="{nx}" cy="{cy}" rx="11" ry="8.5" '
            f'transform="rotate(-18 {nx} {cy})"/>'
            f'<rect x="{nx + 9}" y="{cy - 54}" width="3.5" height="54"/>'
        )
    return (
        f'<g stroke="{OR}" stroke-width="2.4">{lignes}</g>'
        f'<g fill="{OR}">{notes}</g>'
    )


def svg():
    cx, cy, r = 500, 612, 336
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"
     width="{W}" height="{H}" font-family="'Liberation Serif',Georgia,serif">
  <defs>
    <filter id="grain" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4" seed="7"/>
      <feColorMatrix type="saturate" values="0"/>
    </filter>
    <filter id="encre" x="-8%" y="-8%" width="116%" height="116%">
      <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="3" seed="21" result="b"/>
      <feDisplacementMap in="SourceGraphic" in2="b" scale="5"
                         xChannelSelector="R" yChannelSelector="G"/>
    </filter>
    <filter id="encre2" x="-8%" y="-8%" width="116%" height="116%">
      <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="3" seed="4" result="b"/>
      <feDisplacementMap in="SourceGraphic" in2="b" scale="3.5"
                         xChannelSelector="R" yChannelSelector="G"/>
    </filter>
    <clipPath id="disque">
      <circle cx="{cx}" cy="{cy}" r="{r}"/>
    </clipPath>
    <g id="buste">
      <path d="{QUEUE}"/>
      <path d="{NOEUD}"/>
      {"".join(f'<circle cx="{a}" cy="{b}" r="{c}"/>' for a, b, c in BOUCLES)}
      <path d="{SILHOUETTE}"/>
    </g>
  </defs>

  <!-- papier -->
  <rect width="{W}" height="{H}" fill="{PAPIER}"/>

  <!-- encre OR : portee musicale -->
  <g filter="url(#encre2)" opacity="0.92">
    {portee(262)}
  </g>

  <!-- encre ROUGE : disque + fondu trame -->
  <g filter="url(#encre)">
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="{ROUGE}"/>
    <g clip-path="url(#disque)">
      {trame_disque(cx, cy, r, cy + 40, cy + r)}
    </g>
  </g>

  <!-- ROUGE : fantome de reperage decale -->
  <g fill="{ROUGE}" opacity="0.55" transform="translate(-9,-6)" filter="url(#encre2)">
    <use href="#buste"/>
  </g>

  <!-- encre NOIRE : buste -->
  <g fill="{NOIR}" filter="url(#encre2)">
    <use href="#buste"/>
  </g>

  <!-- reserves creme : rouleaux de perruque, oeil, jabot, revers d'habit -->
  <g fill="none" stroke="{PAPIER}" stroke-width="5" stroke-linecap="round" opacity="0.88">
    <path d="M 606 508 C 650 494 688 504 700 528"/>
    <path d="M 602 574 C 648 560 688 570 700 596"/>
    <path d="M 610 642 C 652 630 686 638 694 660"/>
    <path d="M 690 620 C 702 626 712 632 718 640"/>
    <path d="M 756 624 C 744 628 734 632 728 640"/>
    <path d="M 430 452 C 470 424 512 414 556 420"/>
  </g>
  <ellipse cx="426" cy="530" rx="14" ry="8" fill="{PAPIER}"
           transform="rotate(-10 426 530)"/>
  <g fill="{PAPIER}" opacity="0.95">
    <path d="M 486 766 C 514 762 546 770 562 782 C 544 796 510 800 490 794 Z"/>
    <path d="M 488 796 C 518 788 552 794 566 810 C 548 828 512 832 494 822 Z"/>
    <path d="M 494 830 C 522 822 552 828 564 844 C 548 860 518 864 500 854 Z"/>
    <path d="M 502 864 C 526 858 550 862 558 878 C 546 892 520 894 508 884 Z"/>
  </g>
  <g fill="none" stroke="{PAPIER}" stroke-width="6" stroke-linecap="round" opacity="0.9">
    <path d="M 486 792 C 448 858 422 942 410 1012"/>
    <path d="M 556 818 C 596 876 616 946 626 1012"/>
  </g>

  <!-- clavier -->
  <g filter="url(#encre)">
    {clavier(1012)}
  </g>
  <rect x="0" y="1160" width="{W}" height="7" fill="{ROUGE}" opacity="0.8"/>

  <!-- titre : noir + fantome rouge decale -->
  <g text-anchor="middle">
    <text x="494" y="1316" font-size="152" font-weight="bold" letter-spacing="14"
          fill="{ROUGE}" opacity="0.6">AMADEUS</text>
    <text x="500" y="1310" font-size="152" font-weight="bold" letter-spacing="14"
          fill="{NOIR}">AMADEUS</text>
    <text x="500" y="1362" font-size="23" letter-spacing="11" fill="{NOIR}"
          opacity="0.9">W O L F G A N G &#160; · &#160; 1 7 5 6 – 1 7 9 1</text>
  </g>

  <!-- filets + mentions -->
  <g stroke="{NOIR}" stroke-width="2.5">
    <line x1="70" y1="1392" x2="930" y2="1392"/>
    <line x1="70" y1="1400" x2="930" y2="1400"/>
  </g>
  <g text-anchor="middle" font-size="19" letter-spacing="5">
    <text x="500" y="1432" fill="{NOIR}">SÉRIGRAPHIE ORIGINALE · TROIS ENCRES · TIRÉE À LA MAIN</text>
    <text x="500" y="1460" fill="{OR}">ÉDITION LIMITÉE 12/50 · PAPIER CHIFFON 300 G</text>
  </g>

  <!-- marques de reperage -->
  <g stroke-width="2" opacity="0.55">
    <g stroke="{NOIR}">
      <line x1="34" y1="52" x2="70" y2="52"/><line x1="52" y1="34" x2="52" y2="70"/>
      <line x1="930" y1="52" x2="966" y2="52"/><line x1="948" y1="34" x2="948" y2="70"/>
    </g>
    <g stroke="{ROUGE}" transform="translate(3,3)">
      <line x1="34" y1="52" x2="70" y2="52"/><line x1="52" y1="34" x2="52" y2="70"/>
      <line x1="930" y1="52" x2="966" y2="52"/><line x1="948" y1="34" x2="948" y2="70"/>
    </g>
  </g>

  <!-- grain papier -->
  <rect width="{W}" height="{H}" filter="url(#grain)" opacity="0.20"
        style="mix-blend-mode:multiply"/>
  <rect width="{W}" height="{H}" fill="none" stroke="{NOIR}" stroke-width="3"
        opacity="0.25"/>
</svg>
"""


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "affiche_amadeus.svg"
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg())
    print(out)
