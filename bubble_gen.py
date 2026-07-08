#!/usr/bin/env python3
"""Génère des bulles burst comic (style Simon 'WIPED OUT') en PNG transparent.
Starburst blanc contour noir + trame Ben-Day + texte Bangers blanc contour noir."""
import math, random, sys
from PIL import Image, ImageDraw, ImageFont

FONT = "output/v3/fonts/Bangers-Regular.ttf"

def make_bubble(lines, out, font_size=200, rotate=-5, W=1200, H=1000, seed=7,
                spikes=12, dot_band=(560, 320)):
    random.seed(seed)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = W / 2, H / 2

    # --- starburst : pointes longues, acerees, tres irregulieres ---
    outer = min(W, H) * 0.56
    inner = outer * 0.40
    pts = []
    for i in range(spikes * 2):
        ang = math.pi * i / spikes - math.pi / 2
        if i % 2 == 0:
            r = outer * (0.70 + random.random() * 0.55)   # grande variation de longueur
        else:
            r = inner * (0.80 + random.random() * 0.22)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d.polygon(pts, fill=(255, 255, 255, 255))
    d.line(pts + [pts[0]], fill=(0, 0, 0, 255), width=12, joint="curve")

    # --- trame Ben-Day derriere le texte ---
    dot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dot)
    step, rdot = 30, 7
    bw, bh = dot_band
    for yy in range(int(cy - bh / 2), int(cy + bh / 2), step):
        for xx in range(int(cx - bw / 2), int(cx + bw / 2), step):
            dd.ellipse([xx - rdot, yy - rdot, xx + rdot, yy + rdot], fill=(0, 0, 0, 200))
    img.alpha_composite(dot)

    # --- texte (chaque ligne, contour noir epais, empilees) ---
    font = ImageFont.truetype(FONT, font_size)
    sw = max(6, int(font_size * 0.11))
    rendered = []
    for ln in lines:
        bb = d.textbbox((0, 0), ln, font=font, stroke_width=sw)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        ti = Image.new("RGBA", (tw + 30, th + 30), (0, 0, 0, 0))
        ImageDraw.Draw(ti).text((15 - bb[0], 15 - bb[1]), ln, font=font,
                                fill=(255, 255, 255, 255), stroke_width=sw,
                                stroke_fill=(0, 0, 0, 255))
        rendered.append(ti)

    gap = int(font_size * 0.05)
    block_h = sum(i.height for i in rendered) + gap * (len(rendered) - 1)
    block_w = max(i.width for i in rendered)
    block = Image.new("RGBA", (block_w, block_h), (0, 0, 0, 0))
    y = 0
    for i, ti in enumerate(rendered):
        block.alpha_composite(ti, ((block_w - ti.width) // 2, y))
        y += ti.height + gap
    block = block.rotate(rotate, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(block, (int(cx - block.width / 2), int(cy - block.height / 2)))

    img.save(out)
    print("saved", out, img.size)

def make_dialog(lines, out, font_size=150, W=1100, H=900, tip=(0.80, 0.99)):
    """Ballon de dialogue ovale (blanc, contour noir) + texte Bangers NOIR.
    `tip` = position (fraction W,H) de la POINTE de la queue -> a diriger vers le perso.
    Concu pour etre ancre dans un coin (poser avec offset negatif => rogne par le cadre)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = 30
    ell = [m, m, W - m, int(H * 0.66)]
    cyE = (ell[1] + ell[3]) / 2
    tx, ty = tip[0] * W, tip[1] * H
    # base de la queue sur le bord bas de l'ellipse, decalee vers la pointe
    bx = (ell[0] + ell[2]) / 2 + (tx - (ell[0] + ell[2]) / 2) * 0.35
    baseY = ell[3] - 12
    b1, b2 = (bx - 60, baseY), (bx + 60, baseY)
    d.polygon([b1, b2, (tx, ty)], fill=(255, 255, 255, 255))
    d.ellipse(ell, fill=(255, 255, 255, 255))
    d.line([b1, (tx, ty), b2], fill=(0, 0, 0, 255), width=13, joint="curve")
    d.ellipse(ell, outline=(0, 0, 0, 255), width=13)  # contour ellipse par-dessus (masque haut queue)
    # texte NOIR centre dans l'ellipse
    font = ImageFont.truetype(FONT, font_size)
    txt = "\n".join(lines)
    bb = d.multiline_textbbox((0, 0), txt, font=font, align="center", spacing=int(font_size * 0.05))
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.multiline_text(((W - tw) / 2 - bb[0], cyE - th / 2 - bb[1]), txt, font=font,
                     fill=(0, 0, 0, 255), align="center", spacing=int(font_size * 0.05))
    img.save(out)
    print("saved", out, img.size)


if __name__ == "__main__":
    W = "output/v3/work/"
    # DISCIPLINE : ovale flottant, queue longue vers la tete (plan large)
    make_dialog(["DISCIPLINE"], W + "bubble_discipline.png", font_size=165, W=1000, H=1050, tip=(0.66, 0.99))
    # REAL CAPITAL : ancre dans le coin (buste), queue vers le visage
    make_dialog(["REAL CAPITAL"], W + "bubble_realcapital.png", font_size=150, W=1300, H=820, tip=(0.82, 0.99))
    # impact (burst, texte blanc contour noir)
    make_bubble(["ZERO"], W + "bubble_zero.png", font_size=300, rotate=-6, W=1100, H=1000, seed=3)
    make_bubble(["FEED THE", "MARKET"], W + "bubble_feed.png", font_size=170, rotate=-4, W=1250, H=1050, seed=9)
