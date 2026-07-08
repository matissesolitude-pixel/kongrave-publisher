#!/usr/bin/env python3
"""Pose un texte DANS un template de bulle extrait de Simon (fond transparent).
Le texte est centre dans la zone blanche (ovale), avec marge interieure, leger italique."""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
FONT = "output/v3/fonts/Bangers-Regular.ttf"

def _oval_box(arr):
    """bbox de la partie large (ovale) de l'interieur blanc, en ignorant la queue etroite."""
    white = (arr[:, :, 0] > 200) & (arr[:, :, 3] > 128)
    rw = white.sum(axis=1)
    thr = 0.55 * rw.max()
    rows = np.where(rw > thr)[0]
    y0, y1 = rows.min(), rows.max()
    cols = np.where(white[y0:y1 + 1].any(axis=0))[0]
    x0, x1 = cols.min(), cols.max()
    return x0, y0, x1, y1

def _italic(img, shear=0.20):
    w, h = img.size
    return img.transform((w + int(h * shear), h), Image.AFFINE,
                         (1, shear, -shear * h * 0.3, 0, 1, 0), resample=Image.BICUBIC)

def render(template_png, text, out, margin=0.15, shear=0.20, color=(0, 0, 0, 255)):
    tmpl = Image.open(template_png).convert("RGBA")
    arr = np.array(tmpl)
    x0, y0, x1, y1 = _oval_box(arr)
    bw, bh = (x1 - x0) * (1 - 2 * margin), (y1 - y0) * (1 - 2 * margin)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # ajuste la taille de police pour tenir dans la boite
    fs = 10
    while fs < 400:
        f = ImageFont.truetype(FONT, fs + 6)
        d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        b = d.textbbox((0, 0), text, font=f)
        tw = (b[2] - b[0]) + (b[3] - b[1]) * shear
        if tw > bw or (b[3] - b[1]) > bh:
            break
        fs += 6
    f = ImageFont.truetype(FONT, fs)
    d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    b = d0.textbbox((0, 0), text, font=f)
    tw, th = b[2] - b[0], b[3] - b[1]
    ti = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
    ImageDraw.Draw(ti).text((10 - b[0], 10 - b[1]), text, font=f, fill=color)
    ti = _italic(ti, shear)
    out_im = tmpl.copy()
    out_im.alpha_composite(ti, (int(cx - ti.width / 2), int(cy - ti.height / 2)))
    out_im.save(out)
    print("saved", out, out_im.size, "font", fs)

if __name__ == "__main__":
    render("output/v3/work/tmpl_disc.png", "DISCIPLINE", "output/v3/work/disc_final.png")
