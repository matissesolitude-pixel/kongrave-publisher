#!/usr/bin/env python3
"""Caption box comics : rectangle jaune plat (#F7E017), texte noir, bord noir epais,
ombre portee dure decalee (pas de flou). Police Bangers (lettering comics, italique leger)."""
from PIL import Image, ImageDraw, ImageFont
FONT = "output/v3/fonts/Bangers-Regular.ttf"
YELLOW = (247, 224, 23, 255)
BLACK = (0, 0, 0, 255)

def _italic(img, shear=0.16):
    w, h = img.size
    return img.transform((w + int(h * shear), h), Image.AFFINE,
                         (1, shear, 0, 0, 1, 0), resample=Image.BICUBIC)

def _wrap(words, font, max_w):
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines

def make_caption(text, out, font_size=58, pad_x=26, pad_y=14, border=4,
                 shadow=(12, 12), shear=0.14, max_w=880, max_lines=2, line_gap=8):
    # ajuste la police pour tenir en <= max_lines lignes dans max_w
    words = text.split()
    fs = font_size
    while fs > 26:
        font = ImageFont.truetype(FONT, fs)
        lines = _wrap(words, font, max_w)
        if len(lines) <= max_lines:
            break
        fs -= 2
    font = ImageFont.truetype(FONT, fs)
    lines = _wrap(words, font, max_w)
    d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    # rendu de chaque ligne (italique) puis empilage centre
    line_imgs = []
    for ln in lines:
        b = d0.textbbox((0, 0), ln, font=font)
        lw, lh = b[2] - b[0], b[3] - b[1]
        li = Image.new("RGBA", (lw + 20, lh + 20), (0, 0, 0, 0))
        ImageDraw.Draw(li).text((10 - b[0], 10 - b[1]), ln, font=font, fill=BLACK)
        line_imgs.append(_italic(li, shear))
    block_w = max(li.width for li in line_imgs)
    block_h = sum(li.height for li in line_imgs) + line_gap * (len(line_imgs) - 1)
    block = Image.new("RGBA", (block_w, block_h), (0, 0, 0, 0))
    y = 0
    for li in line_imgs:
        block.alpha_composite(li, ((block_w - li.width) // 2, y))
        y += li.height + line_gap
    box_w, box_h = block_w + 2 * pad_x, block_h + 2 * pad_y
    W, H = box_w + shadow[0] + border, box_h + shadow[1] + border
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([shadow[0], shadow[1], shadow[0] + box_w, shadow[1] + box_h], fill=BLACK)
    d.rectangle([0, 0, box_w, box_h], fill=YELLOW, outline=BLACK, width=border)
    im.alpha_composite(block, (pad_x, pad_y))
    im.save(out)
    print("saved", out, im.size, "lines", len(lines), "fs", fs)

if __name__ == "__main__":
    make_caption("IN THIS GAME", "output/v3/work/cap_test.png")
