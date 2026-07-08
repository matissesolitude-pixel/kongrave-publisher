#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Story 6 — ALPHA v2 : scène chaînée + voix + couches DA. Montage 100% local FFmpeg.
Textes rendus en PNG (PIL) puis incrustés en overlay (ce ffmpeg n'a pas drawtext).
Inversion N&B (negate) sur les 3 impacts. Calage approximatif assumé.
"""
import math
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FF = os.environ.get("FFMPEG") or "/opt/homebrew/bin/ffmpeg"
FFPROBE = os.environ.get("FFPROBE") or "/opt/homebrew/bin/ffprobe"
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "alpha"
ASSET = OUT / "layers"
SCENE = ROOT / "output" / "scene_longue" / "scene_chainee.mp4"
VOICES = [ROOT / "output" / "ep01" / f"plan{i}.mp3" for i in (1, 2, 3, 4, 5)]
BUSTES = {2: ROOT / "output" / "ep01" / "plan2_domoai_final.mp4",
          5: ROOT / "output" / "ep01" / "plan5_domoai_final.mp4"}
W, H = 1080, 1920
LEAD, HOLD = 1.0, 0.45
DUR = {1: 4.18, 2: 5.80, 3: 5.25, 4: 5.75, 5: 6.53}
SCRIPT = {
    1: "In this game almost everyone gets wiped out. You included. For now.",
    2: "I'm Matisse. I run an investment fund. While most people pray for one good trade I answer for real capital.",
    3: "What separates a manager from a gambler isn't luck. It's discipline. And that can be learned.",
    4: "Nine traders out of ten end up back at zero. I'm still here. Ten years later. That's no accident.",
    5: "I'll teach you to think like a manager. Not a gambler. Here. Every day. Follow me or keep feeding the market.",
}
# offsets : avancés puis légèrement RE-RETARDÉS (~+0,3s) pour claquer pile sur le mot
SHOCK = {1: ("WIPED OUT", "impact", 2.3), 2: ("REAL CAPITAL", "dialog", 4.8),
         3: ("DISCIPLINE", "dialog", 2.7), 4: ("ZERO", "impact", 2.1), 5: ("FEED THE MARKET", "impact", 5.4)}


def fmt_word(word):
    t = word.split()
    if len(t) == 3:
        return f"{t[0]} {t[1]}\n{t[2]}"
    if len(t) == 2:
        return f"{t[0]}\n{t[1]}"
    return word
FONTS = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
         "/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]


def FT():
    for f in FONTS:
        if Path(f).exists():
            return f
    sys.exit("[ERREUR] aucune police trouvée.")


def dur_of(p):
    return float(subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=nk=1:nw=1", str(p)], capture_output=True, text=True).stdout.strip())


def text_png(text, size, stroke, path, ft):
    fnt = ImageFont.truetype(ft, size)
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    b = d0.multiline_textbbox((0, 0), text, font=fnt, stroke_width=stroke, align="center", spacing=10)
    w, h = int(b[2] - b[0] + stroke * 2 + 40), int(b[3] - b[1] + stroke * 2 + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).multiline_text((w / 2, h / 2), text, font=fnt, fill="white", stroke_width=stroke,
                                      stroke_fill="black", anchor="mm", align="center", spacing=10)
    im.save(path)


def fit_text_png(text, max_w, max_h, path, ft, size_max=100):
    """Réduit la police jusqu'à ce que le texte tienne dans (max_w,max_h) = zone intérieure
    de la bulle. Garantit une marge : le texte ne touche jamais le contour."""
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    size = size_max
    while size > 34:
        fnt = ImageFont.truetype(ft, size)
        st = max(5, round(size * 0.11))
        b = d0.multiline_textbbox((0, 0), text, font=fnt, stroke_width=st, align="center", spacing=8)
        if (b[2] - b[0]) <= max_w and (b[3] - b[1]) <= max_h:
            break
        size -= 3
    text_png(text, size, max(5, round(size * 0.11)), path, ft)


def bubbles(ft):
    # tailles réduites pour tenir dans la safe zone (~15% de marge de chaque côté → ≤ ~756px)
    sz = 720
    im = Image.new("RGBA", (sz, sz), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = sz / 2; pts = []
    for i in range(22):
        ang = math.pi * i / 11 - math.pi / 2
        r = sz * 0.49 if i % 2 == 0 else sz * 0.30
        pts.append((c + r * math.cos(ang), c + r * math.sin(ang)))
    d.polygon(pts, fill="white"); d.line(pts + [pts[0]], fill="black", width=9)
    im.save(ASSET / "bub_impact.png")
    iw, ih = 740, 430
    im2 = Image.new("RGBA", (iw, ih), (0, 0, 0, 0)); d2 = ImageDraw.Draw(im2)
    d2.ellipse([8, 8, iw - 8, ih - 130], fill="white", outline="black", width=9)
    d2.polygon([(iw*0.30, ih-145), (iw*0.20, ih-12), (iw*0.46, ih-155)], fill="white", outline="black")
    im2.save(ASSET / "bub_dialog.png")


def subtract(a, b, s, e):
    if e <= a or s >= b:
        return [(a, b)]
    out = []
    if a < s:
        out.append((a, s))
    if e < b:
        out.append((e, b))
    return out


def chunks(text, n=4):
    t = [w.strip("….—") for w in text.split() if w.strip("….—")]
    return [" ".join(t[i:i+n]) for i in range(0, len(t), n)]


def main():
    if not SCENE.exists():
        sys.exit(f"[ERREUR] scène introuvable : {SCENE}")
    ASSET.mkdir(parents=True, exist_ok=True)
    ft = FT()
    bubbles(ft)

    # voix concat + durées
    lf = OUT / "voices.txt"; lf.write_text("".join(f"file '{v}'\n" for v in VOICES))
    voice_all = OUT / "voice_all.mp3"
    subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", str(lf), "-c", "copy", str(voice_all)], capture_output=True)
    voice_dur, scene_dur = dur_of(voice_all), dur_of(SCENE)
    total = LEAD + voice_dur
    ext = max(0.1, total - scene_dur)

    vstart = {}; acc = LEAD
    for p in (1, 2, 3, 4, 5):
        vstart[p] = round(acc, 3); acc += DUR[p]
    shock_t = {p: round(vstart[p] + SHOCK[p][2], 3) for p in SHOCK}

    # binariser les bustes (composités décor) + scale, et lire leurs durées
    binv = f"scale={W}:{H},setsar=1,format=gray,lut=y=255*gt(val\\,140),format=yuv420p"
    bdur = {}
    for p, src in BUSTES.items():
        dst = ASSET / f"buste{p}.mp4"
        subprocess.run([FF, "-y", "-i", str(src), "-an", "-vf", binv, "-c:v", "libx264", "-crf", "18", str(dst)], capture_output=True)
        bdur[p] = min(dur_of(dst), DUR[p])     # ne pas dépasser la fenêtre voix

    # PNG des mots + sous-titres
    # auto-fit dans la zone intérieure de chaque bulle (marge garantie)
    for p in (1, 2, 3, 4, 5):
        box = (500, 360) if SHOCK[p][1] == "impact" else (520, 200)   # impact (burst 720) / dialog (740x430)
        fit_text_png(fmt_word(SHOCK[p][0]), *box, ASSET / f"word{p}.png", ft)
    subs = []   # (path, a, b)
    si = 0
    for p in (1, 2, 3, 4, 5):
        ch = chunks(SCRIPT[p]); seg = DUR[p] / len(ch)
        bs, be = shock_t[p] - 0.1, shock_t[p] + HOLD + 0.05
        for i, c in enumerate(ch):
            cs, ce = vstart[p] + i * seg, vstart[p] + (i + 1) * seg
            for a, b in subtract(cs, ce, bs, be):
                if b - a >= 0.25:
                    pth = ASSET / f"sub{si}.png"; text_png(c.upper(), 54, 5, pth, ft); subs.append((pth, a, b)); si += 1

    # flash blanc plein cadre (coupes corps↔buste)
    Image.new("RGBA", (W, H), (255, 255, 255, 255)).save(ASSET / "flash.png")

    # inputs (index dynamique)
    inputs = ["-i", str(SCENE), "-i", str(voice_all)]   # 0,1
    idx = 2
    bub_imp = idx; inputs += ["-i", str(ASSET / "bub_impact.png")]; idx += 1
    bub_dia = idx; inputs += ["-i", str(ASSET / "bub_dialog.png")]; idx += 1
    flash_i = idx; inputs += ["-i", str(ASSET / "flash.png")]; idx += 1
    buste_i = {}
    for p in (2, 5):
        buste_i[p] = idx; inputs += ["-itsoffset", f"{vstart[p]}", "-i", str(ASSET / f"buste{p}.mp4")]; idx += 1
    word_idx = {}
    for p in (1, 2, 3, 4, 5):
        word_idx[p] = idx; inputs += ["-i", str(ASSET / f"word{p}.png")]; idx += 1
    sub_idx = []
    for (pth, a, b) in subs:
        sub_idx.append(idx); inputs += ["-i", str(pth)]; idx += 1

    # filtergraph : scène étirée → bustes incrustés → inversion impacts → flashs de coupe → bulles/mots → sous-titres
    nodes = [f"[0:v]scale={W}:{H},setsar=1,tpad=stop_mode=clone:stop_duration={ext:.2f}[scn]"]
    cur, k = "scn", 0
    cut_times = []
    for p in (2, 5):                                  # buste sur sa fenêtre voix
        a, d = vstart[p], bdur[p]
        k += 1; n = f"v{k}"
        nodes.append(f"[{cur}][{buste_i[p]}:v]overlay=0:0:enable='between(t,{a},{round(a+d,3)})'[{n}]")
        cur = n; cut_times += [a, round(a + d, 3)]
    inv = "+".join(f"between(t,{shock_t[p]},{shock_t[p]+HOLD})" for p in (1, 4, 5))
    k += 1; nv = f"v{k}"; nodes.append(f"[{cur}]negate=enable='{inv}'[{nv}]"); cur = nv
    for ct in cut_times:                              # flash N&B bref sur chaque coupe corps↔buste
        k += 1; nf = f"v{k}"
        nodes.append(f"[{cur}][{flash_i}:v]overlay=0:0:enable='between(t,{ct-0.02:.2f},{ct+0.05:.2f})'[{nf}]")
        cur = nf
    for p in (1, 2, 3, 4, 5):                         # bulle + mot, centrés H+V (~26%)
        bub = bub_imp if SHOCK[p][1] == "impact" else bub_dia
        t = shock_t[p]
        k += 1; n1 = f"v{k}"
        nodes.append(f"[{cur}][{bub}:v]overlay=x=(W-w)/2:y=(H*0.26)-(h/2):enable='between(t,{t},{t+HOLD})'[{n1}]")
        k += 1; n2 = f"v{k}"
        sx = f"(W-w)/2+8*sin(26*(t-{t}))*exp(-6*(t-{t}))"     # shake léger autour du centre
        nodes.append(f"[{n1}][{word_idx[p]}:v]overlay=x='{sx}':y=(H*0.26)-(h/2):enable='between(t,{t},{t+HOLD})'[{n2}]")
        cur = n2
    for (pth, a, b), ix in zip(subs, sub_idx):        # sous-titres
        k += 1; nn = f"v{k}"
        nodes.append(f"[{cur}][{ix}:v]overlay=x=(W-w)/2:y=H-260:enable='between(t,{a:.2f},{b:.2f})'[{nn}]")
        cur = nn
    # N&B PUR : desaturer en fin de chaîne (tue toute teinte réintroduite par le negate)
    k += 1; nodes.append(f"[{cur}]hue=s=0[vout]"); cur = "vout"
    fc = ";".join(nodes)

    out = OUT / "reel_alpha_v2b.mp4"
    cmd = [FF, "-y", *inputs, "-filter_complex", fc, "-map", f"[{cur}]",
           "-af", f"adelay={int(LEAD*1000)}|{int(LEAD*1000)}", "-map", "1:a",
           "-t", f"{total:.2f}", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("[ERREUR] ffmpeg:\n" + r.stderr[-1500:])
    print(f"✓ {out} ({out.stat().st_size/1024/1024:.2f} Mo, {total:.2f}s)")
    print(f"  scène {scene_dur:.1f}s +{ext:.1f}s tenue | voix {voice_dur:.1f}s | lead {LEAD}s | {len(subs)} sous-titres")
    print(f"  BUSTES : plan2 @ {vstart[2]:.1f}-{vstart[2]+bdur[2]:.1f}s | plan5 @ {vstart[5]:.1f}-{vstart[5]+bdur[5]:.1f}s")
    print("  mots-chocs @ " + ", ".join(f"{SHOCK[p][0]}={shock_t[p]:.1f}" for p in (1,2,3,4,5)))


if __name__ == "__main__":
    main()
