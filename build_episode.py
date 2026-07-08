#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_episode.py N — assemble EPISODE_NN_kongrave.mp4 (pipeline v3, JSON-driven).

Chaîne (identique au master ep01) :
  voix par segment (ElevenLabs) -> corps 5 segments (décor Simon binarisé + perso alpha /
  buste / champ) + orage (flashs + éclair + SFX) -> mots-chocs (impact_inversion = negate
  plein cadre + burst ; bulle_dialogue = bulle comics) -> captions jaunes (phrases, masquées
  pendant les chocs) -> générique Veo + transition audio (orage monte, son Veo bave, voix
  dans la continuité).
Usage : build_episode.py 2 [3 ...]   (défaut : tous ep02-28)
"""
import json, math, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
from alpha_assemble import text_png, dur_of, subtract, chunks, fmt_word, FT
from bubble_gen import make_bubble   # impact = starburst CANONIQUE du master
import bubble_fill                    # dialogue = templates Simon EXTRAITS (tmpl_rc / tmpl_disc)
from batch_voice import tts

FF = os.environ.get("FFMPEG") or "/opt/homebrew/bin/ffmpeg"
ROOT = Path(__file__).resolve().parent
W, H = 1080, 1920
# PLANCHE BD (Sin City) : la CASE ACTIVE (qui joue la vidéo) est une cellule d'une page plus grande.
# Gouttières symétriques (blanc cassé), cases VOISINES en encre noire au-dessus/en-dessous (coupées
# par le cadre). Générique = plein cadre (pas de case). Un seul gabarit pour toute la série.
SIDE = 80                     # gouttière latérale (gauche = droite, symétrique)
VG = 44                       # gouttière verticale (blanc) entre case active et cases voisines
ACT_TOP, ACT_BOT = 250, 1570  # bords haut/bas de la case active (contenu clair de l'UI Instagram)
PANEL_X0, PANEL_X1 = SIDE, W - SIDE      # 80 .. 1000
PANEL_W = PANEL_X1 - PANEL_X0            # 920
PANEL_H = ACT_BOT - ACT_TOP              # 1320
GUTTER = "0xEFEAE0@1"         # blanc cassé (gouttière BD)
PANEL_BORDER = 14             # trait noir épais de la case
BUSTE_W = 820                 # le buste REMPLIT la case (tête proche du bord haut, petit air)
BUSTE_TOP = ACT_TOP + 22
# repères pour bulles/captions (rester DANS la case active)
INX = PANEL_X0 + PANEL_BORDER + 6         # bord intérieur gauche
INY_TOP = ACT_TOP + PANEL_BORDER + 4      # bord intérieur haut
CAP_MAXW = PANEL_W - 2 * (PANEL_BORDER + 24)   # largeur max cartouche caption (dans la case)

NB_TOP_H = ACT_TOP - VG               # hauteur de la case voisine du haut (bas à ACT_TOP-VG)
NB_BOT_Y = ACT_BOT + VG               # haut de la case voisine du bas
NB_BOT_H = H - NB_BOT_Y               # hauteur de la case voisine du bas
# gouttière blanc cassé hors case active (chaîne de filtres, sans virgule finale)
GUTTERS = (
    f"drawbox=x=0:y=0:w={W}:h={ACT_TOP}:color={GUTTER}:t=fill,"
    f"drawbox=x=0:y={ACT_BOT}:w={W}:h={H-ACT_BOT}:color={GUTTER}:t=fill,"
    f"drawbox=x=0:y=0:w={SIDE}:h={H}:color={GUTTER}:t=fill,"
    f"drawbox=x={W-SIDE}:y=0:w={SIDE}:h={H}:color={GUTTER}:t=fill")
# traits noirs épais : case active + amorces voisines (même trait partout)
BORDERS = (
    f"drawbox=x={PANEL_X0}:y={ACT_TOP}:w={PANEL_W}:h={PANEL_H}:color=black:t={PANEL_BORDER},"
    f"drawbox=x={PANEL_X0}:y=0:w={PANEL_W}:h={NB_TOP_H}:color=black:t={PANEL_BORDER},"
    f"drawbox=x={PANEL_X0}:y={NB_BOT_Y}:w={PANEL_W}:h={NB_BOT_H}:color=black:t={PANEL_BORDER}")
BUSTE_W = 600         # largeur du buste au compositing (réduit : tête + bulle tiennent dans la zone sûre)
BUSTE_TOP = 300       # haut du buste bien SOUS la barre de statut (tête dégagée)
LEAD, HOLD = 1.5, 0.5
JSON = ROOT / "KONGRAVE_episodes_02_to_28_v3.json"
AUDIO = ROOT / "audio"
DECOR = ROOT / "assets" / "BACKGROUND.MOV"
DECOR_A, DECOR_B = 8.5, 14.85          # région du décor SANS le burst WIPED OUT
DECOR_LOOP = ROOT / "output" / "v3" / "work" / "decor_bin_red.mp4"  # pré-rendu : N&B + fauteuil rouge
PERSO_BIN = r"format=yuva420p,lut=y=255*gt(val\,140)"  # binarise la luma, GARDE l'alpha
GEN = ROOT / "output" / "v3" / "work" / "generique_intro_clean.mp4"
CHAMP = ROOT / "assets" / "champ_bataille.png"
ECLAIR = ROOT / "output" / "v3" / "work" / "eclair_alpha.png"
RUMBLE = ROOT / "output" / "v3" / "work" / "rumble_v3.wav"
CRACK = ROOT / "output" / "v3" / "work" / "crack.wav"
BANGERS = str(ROOT / "output" / "v3" / "fonts" / "Bangers-Regular.ttf")
TMPL_RC = ROOT / "output" / "v3" / "work" / "tmpl_rc.png"      # cartouche Simon (haut, au-dessus visage)
TMPL_DISC = ROOT / "output" / "v3" / "work" / "tmpl_disc.png"  # ovale Simon + queue vers le perso
YELLOW = (247, 224, 23)
BIN = r"format=gray,lut=y=255*gt(val\,140),format=yuv420p"
SHOTS = {   # DOCTRINE : plein-pied TOUJOURS dos/profil (visage jamais de face). Clips chaînés
            # régénérés sur fond blanc puis détourés (regen_dosprofil.py), portions pures.
    "dos":  ROOT / "output/perso_detoure/v2/dos_clean.mov",
    "profil": ROOT / "output/perso_detoure/v2/profil_clean.mov",
    # 'front'/'poche' interdits en plein-pied -> repointés sur dos/profil par sécurité doctrine.
    "front": ROOT / "output/perso_detoure/v2/dos_clean.mov",
    "poche": ROOT / "output/perso_detoure/v2/profil_clean.mov",
    "buste2": ROOT / "output/ep01/plan2_domoai_alpha.mov",   # buste lip-sync face cam : pas de boucle
    "buste5": ROOT / "output/ep01/plan5_domoai_alpha.mov",
}


def run(cmd, tag):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"[ERREUR] {tag}:\n{r.stderr[-1200:]}")


def pick_shot(seg_num, plan):
    if seg_num == 2:
        return "buste2"
    if seg_num == 5:
        return "buste5"
    pl = plan.lower()
    if "dos" in pl:
        return "dos"
    if "profil" in pl:
        return "profil"
    # DOCTRINE : jamais de visage de face en plein-pied. À défaut d'indice, on prend le profil.
    return "profil"


def decor_clip(dur, dst):
    """Boucle du décor Simon pré-rendu (N&B seuil dur + fauteuil rouge), à la durée voulue."""
    run([FF, "-y", "-v", "error", "-stream_loop", "-1", "-i", str(DECOR_LOOP),
         "-t", f"{dur:.3f}", "-an", "-r", "30", "-c:v", "libx264", "-crf", "18",
         "-pix_fmt", "yuv420p", str(dst)], "decor")


def champ_png(dst):
    im = Image.open(CHAMP).convert("L")
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)))
    im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
    im.point(lambda v: 255 if v > 140 else 0).convert("RGB").save(dst)


def seg_clip(seg_num, shot, dur, work, champ):
    """Un segment : décor + perso (ou champ plein cadre pour seg4), binarisé, durée exacte."""
    dst = work / f"seg{seg_num}.mp4"
    if seg_num == 4:
        hf = work / "seg4_hf.mp4"
        if hf.is_file():
            # INSERT seg4 (concept/narratif) : vidéo pré-stylée (HyperFrames prop OU illustration
            # dessinée animée DomoAI). Déjà au bon look Sin City (N&B + 1 rouge) -> PAS de binarisation
            # (elle tuerait le rouge). Juste plein cadre + durée exacte du segment.
            vf = f"scale={W}:{H},setsar=1,fps=30"
            run([FF, "-y", "-v", "error", "-stream_loop", "-1", "-i", str(hf), "-t", f"{dur:.3f}",
                 "-an", "-vf", vf, "-r", "30", "-c:v", "libx264", "-crf", "18",
                 "-pix_fmt", "yuv420p", str(dst)], "seg4hf")
            return dst
        vf = f"scale={W}:{H},setsar=1,zoompan=z='min(zoom+0.0010\\,1.10)':d={int(dur*30)}:s={W}x{H}:fps=30,{BIN}"
        run([FF, "-y", "-v", "error", "-loop", "1", "-i", str(champ), "-t", f"{dur:.3f}", "-vf", vf,
             "-r", "30", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(dst)], "seg4")
        return dst
    dec = work / f"dec{seg_num}.mp4"
    decor_clip(dur, dec)
    if shot.startswith("buste"):
        # RÈGLE GRAVÉE : buste lip-sync PROPRE à cet épisode (généré par regen_bustes.py sur
        # l'audio de CET épisode). JAMAIS le buste d'un autre épisode.
        src = work / f"buste{seg_num}_alpha.mov"
        if not src.is_file():
            sys.exit(f"[ERREUR] buste lip-sync manquant : {src}\n"
                     f"Génère-le : python regen_bustes.py {work.name.replace('ep','')}  "
                     f"(chaque épisode a ses PROPRES bustes lip-sync, jamais ceux d'un autre).")
    else:
        src = SHOTS[shot]
    if shot.startswith("buste"):
        # gros plan : le buste REMPLIT la case bord à bord (object-fit COVER) — scale pour couvrir
        # toute la surface intérieure de la case puis crop les côtés. Aucun bord vidéo visible.
        # Détouré (alpha) sur le décor : le perso couvre la case, le décor comble d'éventuels trous.
        ov = (f"[1:v]scale={PANEL_W}:{PANEL_H}:force_original_aspect_ratio=increase,"
              f"crop={PANEL_W}:{PANEL_H},{PERSO_BIN}[p];"
              f"[0:v][p]overlay={PANEL_X0}:{ACT_TOP}:format=auto[v]")
    else:
        # plein-pied : ~0.70, pieds au sol, calage ep01 (x=384,y=834)
        ov = (f"[1:v]scale=504:-1,{PERSO_BIN}[p];"
              f"[0:v][p]overlay=384:834:format=auto[v]")
    # plein-pied bouclé (boomerang) pour couvrir toute la durée ; buste joué une fois (lip-sync)
    perso_in = ["-i", str(src)] if shot.startswith("buste") else ["-stream_loop", "-1", "-i", str(src)]
    run([FF, "-y", "-v", "error", "-i", str(dec), *perso_in,
         "-filter_complex", ov, "-map", "[v]", "-t", f"{dur:.3f}", "-r", "30",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(dst)], f"seg{seg_num}")
    return dst


GAP = 0.45   # respiration entre segments (timing exact + pacing naturel)


def make_voice(ep, segs, work):
    """Voix par segment (timing exact) + concat avec GAP -> audio/epNN_voice.mp3. Retourne [durées]."""
    durs, parts = [], []
    for s in segs:
        p = work / f"v{s['segment']}.mp3"
        if not p.exists():
            p.write_bytes(tts(s["voice"].strip()))
        durs.append(dur_of(p)); parts.append(p)
    voice = AUDIO / f"ep{ep:02d}_voice.mp3"
    inp = []
    for p in parts:
        inp += ["-i", str(p)]
    inp += ["-f", "lavfi", "-t", str(GAP), "-i", "anullsrc=r=44100:cl=mono"]
    sil = len(parts)
    order = []
    for i in range(len(parts)):
        order.append(f"[{i}:a]")
        if i < len(parts) - 1:
            order.append(f"[{sil}:a]")
    fc = "".join(order) + f"concat=n={len(order)}:v=0:a=1[a]"
    run([FF, "-y", "-v", "error", *inp, "-filter_complex", fc, "-map", "[a]",
         "-c:a", "libmp3lame", "-q:a", "2", str(voice)], "voiceconcat")
    return durs, voice


def split_sentences(voice):
    parts = [x.strip() for x in voice.replace("…", "… ").replace("—", " ").split(".") if x.strip()]
    return parts or [voice.strip()]


def sentence_spans(mp3, n, seg_dur, vstart):
    """n spans (start,end) ABSOLUS alignés sur les vraies pauses de la voix (silencedetect)."""
    if n <= 1:
        return [(round(vstart, 3), round(vstart + seg_dur, 3))]
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", str(mp3),
                        "-af", "silencedetect=noise=-33dB:d=0.14", "-f", "null", "-"],
                       capture_output=True, text=True)
    sil, cs = [], None
    for line in r.stderr.splitlines():
        if "silence_start:" in line:
            try: cs = float(line.split("silence_start:")[1].strip())
            except ValueError: cs = None
        elif "silence_end:" in line and cs is not None:
            try: e = float(line.split("silence_end:")[1].split("|")[0].strip())
            except ValueError: e = None
            if e is not None:
                sil.append(((cs + e) / 2, e - cs)); cs = None
    sil = [(m, d) for (m, d) in sil if 0.15 < m < seg_dur - 0.15]
    sil.sort(key=lambda x: -x[1])
    bounds = sorted(m for m, _ in sil[:n - 1])
    while len(bounds) < n - 1:                       # complète par répartition si pauses manquantes
        bounds = sorted(set(bounds) | {seg_dur * (len(bounds) + 1) / n})
    pts = [0.0] + bounds[:n - 1] + [seg_dur]
    return [(round(vstart + pts[i], 3), round(vstart + pts[i + 1], 3)) for i in range(n)]


def shock_at(word, sents, spans, kind="dialog"):
    """Place le mot-choc SUR le mot prononcé (position du mot dans sa phrase). Retourne t0.
    Un mot en fin de phrase (YOU LOST, ZERO, FEED du master) tombe alors PILE dans le silence
    qui suit la phrase ; un mot au milieu (BLOWN, STRIKE BACK) claque sur le mot. Robuste."""
    mw = [w for w in word.lower().replace("—", " ").split() if w]
    last = (mw[-1] if mw else word.lower()).strip("…—.,!?")
    for txt, (a, b) in zip(sents, spans):
        low = txt.lower()
        if last and last in low:
            idx = low.rfind(last)
            ratio = min(1.0, max(0.0, (idx + len(last)) / max(1, len(low))))
            return a + ratio * (b - a) - 0.10
    a, b = spans[-1]
    return a + 0.6 * (b - a)


def impact_word_png(word, dst):
    """Mot-choc plein cadre : Bangers blanc, contour noir épais, sur transparent (pour negate N&B)."""
    from PIL import ImageDraw, ImageFont
    text = fmt_word(word)
    f = ImageFont.truetype(BANGERS, 150)
    st = 12
    d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    b = d0.multiline_textbbox((0, 0), text, font=f, stroke_width=st, align="center", spacing=8)
    w, h = int(b[2] - b[0] + st * 2 + 40), int(b[3] - b[1] + st * 2 + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).multiline_text((w / 2, h / 2), text, font=f, fill=(255, 255, 255, 255),
                                      stroke_width=st, stroke_fill=(0, 0, 0, 255), anchor="mm",
                                      align="center", spacing=8)
    im.save(dst)


def caption_png(text, dst):
    from PIL import ImageDraw, ImageFont
    fs = 46                       # réduit pour l'échelle case BD (tient DANS la case)
    while fs > 28:
        f = ImageFont.truetype(BANGERS, fs)
        d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        # wrap <= 2 lignes, largeur max = intérieur de la case active
        words = text.split(); lines = []; cur = ""
        for w in words:
            t = (cur + " " + w).strip()
            if d0.textlength(t, font=f) <= CAP_MAXW or not cur:
                cur = t
            else:
                lines.append(cur); cur = w
        if cur:
            lines.append(cur)
        if len(lines) <= 2:
            break
        fs -= 2
    adv = int(fs * 1.05)
    line_imgs = []
    for ln in lines:
        b = d0.textbbox((0, 0), ln, font=f)
        li = Image.new("RGBA", (int(b[2] - b[0]) + 24, int(b[3] - b[1]) + 24), (0, 0, 0, 0))
        ImageDraw.Draw(li).text((12 - b[0], 12 - b[1]), ln, font=f, fill=(0, 0, 0, 255))
        line_imgs.append(li)
    bw = max(li.width for li in line_imgs); bh = adv * len(line_imgs)
    blk = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    y = 0
    for li in line_imgs:
        blk.alpha_composite(li, ((bw - li.width) // 2, y)); y += adv
    pad_x, pad_y, bd, sh = 26, 12, 4, 10
    box_w, box_h = bw + 2 * pad_x, bh + 2 * pad_y
    im = Image.new("RGBA", (box_w + sh + bd, box_h + sh + bd), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([sh, sh, sh + box_w, sh + box_h], fill=(0, 0, 0, 255))
    d.rectangle([0, 0, box_w, box_h], fill=YELLOW, outline=(0, 0, 0, 255), width=bd)
    im.alpha_composite(blk, (pad_x, pad_y))
    im.save(dst)


def word_lines(word):
    """Découpe un mot-choc en 1-2 lignes équilibrées (master : 'FEED THE' / 'MARKET')."""
    w = word.upper().replace("—", " ").split()
    if len(w) <= 1:
        return w or [word.upper()]
    if len(w) == 2:
        # 2 mots : sur une ligne si court, sinon empilés
        return [" ".join(w)] if len(w[0]) + len(w[1]) + 1 <= 9 else w
    mid = (len(w) + 1) // 2
    return [" ".join(w[:mid]), " ".join(w[mid:])]


def impact_fs(lines):
    """Taille Bangers pour un burst starburst : tient dans la zone centrale (~600px)."""
    longest = max((len(l) for l in lines), default=4)
    return max(140, min(300, int(600 / max(1.0, 0.5 * longest))))


def dialog_fs(lines, box_w):
    """Taille Bangers pour un ovale : le plus long tient dans ~80% de la largeur d'ovale."""
    longest = max((len(l) for l in lines), default=6)
    return max(90, min(180, int(box_w * 0.80 / max(1.0, 0.52 * longest))))


def build(ep, e, work):
    work.mkdir(parents=True, exist_ok=True)
    ft = FT()
    segs = sorted(e["segments"], key=lambda s: s["segment"])
    durs, voice = make_voice(ep, segs, work)

    # timeline corps : LEAD d'orage avant seg1, + GAP (respiration) après chaque segment sauf le dernier
    seg_dur = {}
    last = segs[-1]["segment"]
    for i, s in enumerate(segs):
        n = s["segment"]
        seg_dur[n] = durs[i] + (LEAD if n == 1 else 0.0) + (GAP if n != last else 0.0)
    champ = work / "champ_bin.png"; champ_png(champ)

    files = []
    for s in segs:
        n = s["segment"]
        files.append(seg_clip(n, pick_shot(n, s["plan"]), seg_dur[n], work, champ))
    # concat corps
    ci = []
    for f in files:
        ci += ["-i", str(f)]
    base = work / "base.mp4"
    fc = "".join(f"[{i}:v]" for i in range(len(files))) + f"concat=n={len(files)}:v=1[v]"
    run([FF, "-y", "-v", "error", *ci, "-filter_complex", fc, "-map", "[v]",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(base)], "concat")
    body_dur = dur_of(base)

    # spans de phrases CALÉS SUR LA VOIX RÉELLE (silencedetect), par segment
    buste_segs = {2, 5}
    HOLD_IMPACT, HOLD_DIALOG = 1.2, 1.6   # mesurés sur le master (ZERO 1.05/FEED 1.26 ; DISC 1.65/RC 1.27)
    # Fenêtre VIDÉO de chaque segment (temps corps) : sert à clamper chocs/captions -> aucun
    # débordement d'une bulle/burst/caption sur le segment suivant (ex. champ de bataille).
    vidstart, vidend, accv = {}, {}, 0.0
    for s in segs:
        n = s["segment"]; vidstart[n] = round(accv, 3); accv += seg_dur[n]; vidend[n] = round(accv, 3)
    vstart, seg_spans = {}, {}
    shock_t, shock_end, shock_kind, shock_word = {}, {}, {}, {}
    acc = LEAD
    for i, s in enumerate(segs):
        n = s["segment"]; vstart[n] = round(acc, 3)
        sents = split_sentences(s["voice"])
        spans = sentence_spans(work / f"v{n}.mp3", len(sents), durs[i], vstart[n])
        seg_spans[n] = list(zip(sents, spans))
        acc += durs[i] + GAP
        shock_kind[n] = "impact" if "impact" in s["mot_choc_type"] else "dialog"
        shock_word[n] = s["mot_choc"]                          # mot AFFICHÉ (commentaire éditorial)
        # ANCRE de timing = mot de la VOIX où caler la bulle (jamais affiché). La bulle ne répète
        # JAMAIS le texte dit : mot_choc != mot_choc_anchor. Défaut = mot affiché (rétrocompat).
        anchor = s.get("mot_choc_anchor", s["mot_choc"])
        st = shock_at(anchor, sents, spans, shock_kind[n])
        hold = HOLD_IMPACT if shock_kind[n] == "impact" else HOLD_DIALOG
        # clamp DANS la fenêtre vidéo du segment (marge 0.05 avant la coupe)
        shock_t[n] = round(min(max(vstart[n], st), vidend[n] - 0.20), 3)
        shock_end[n] = round(min(shock_t[n] + hold, vidend[n] - 0.05), 3)

    # assets chocs : mêmes générateurs CANONIQUES que le master ep01 (bubble_gen).
    #   impact  -> make_bubble  (starburst blanc, contour noir, trame Ben-Day, Bangers blanc+contour)
    #   dialog  -> make_dialog  (ovale blanc, contour noir, queue vers le perso, Bangers noir)
    # AUCUN négatif N&B. Style INDISCERNABLE du master (voir STYLE_REFERENCE.md).
    asset = work / "assets"; asset.mkdir(exist_ok=True)
    for n in shock_word:
        lines = word_lines(shock_word[n])
        if shock_kind[n] == "impact":
            make_bubble(lines, asset / f"sh{n}.png", font_size=impact_fs(lines),
                        rotate=-6, W=1200, H=1000, seed=ep * 3 + n)
        else:
            # dialogue = template Simon EXTRAIT rempli (Bangers noir). buste = tmpl_rc (queue lisse),
            # plein-pied = tmpl_disc (queue ÉCLAIR), EXACTEMENT comme le master.
            tmpl = TMPL_RC if n in buste_segs else TMPL_DISC
            bubble_fill.render(str(tmpl), " ".join(lines), str(asset / f"sh{n}.png"))

    # captions par phrase, calées sur la voix. RÈGLE : les captions RESTENT VISIBLES en permanence
    # (elles sous-titrent la voix) ; la bulle éditoriale se superpose PAR-DESSUS (mot différent,
    # en haut de cadre). PLUS DE MASQUAGE pendant le mot-choc — les deux coexistent.
    subs = []
    for n in seg_spans:
        for c, (a, b) in seg_spans[n]:
            a = max(a, vidstart[n]); b = min(b, vidend[n] - 0.05)   # clamp caption dans le segment
            if b - a >= 0.35:
                p = asset / f"sp{len(subs)}.png"; caption_png(c.upper().rstrip(".") + ".", p); subs.append((p, a, b))

    Image.new("RGBA", (W, H), (255, 255, 255, 255)).save(asset / "flash.png")
    ecl = Image.open(ECLAIR).convert("RGBA")

    # flashs d'orage irréguliers 4-7s + éclair sur 2
    flashes = []
    t = 2.0
    seed = ep * 7
    while t < body_dur - 0.3:
        flashes.append(round(t, 2)); t += 4 + ((seed % 4))  # 4-7s pseudo-irrégulier
        seed = (seed * 5 + 3) % 97
    eclair_at = flashes[:2]
    # seg4 INSERT (prop HyperFrames / illustration animée) = anim autonome, lisible sans le son.
    # On NE fait PAS clignoter les flashs d'orage blancs par-dessus (ça casserait la métaphore).
    if (work / "seg4_hf.mp4").is_file() and 4 in vidstart:
        fs, fe = vidstart[4] - 0.10, vidend[4] + 0.10
        flashes = [ft for ft in flashes if not (fs <= ft <= fe)]
        eclair_at = [ft for ft in eclair_at if not (fs <= ft <= fe)]

    # CASES VOISINES (planche) : crops RÉELS de CET épisode (frame d'avant / d'après), assombris,
    # jamais rien de généré. Extraits de `base` (décor+perso binarisés, sans bulle ni caption).
    nb_top_img, nb_bot_img = work / "nb_top.png", work / "nb_bot.png"
    dim = "eq=brightness=-0.05:contrast=0.9:saturation=0.85"   # ~75-80% : dessin visible, en retrait
    run([FF, "-y", "-v", "error", "-ss", "1.6", "-i", str(base), "-frames:v", "1", "-vf",
         f"scale={PANEL_W}:{NB_TOP_H}:force_original_aspect_ratio=increase,crop={PANEL_W}:{NB_TOP_H},{dim}",
         str(nb_top_img)], "nbtop")
    run([FF, "-y", "-v", "error", "-ss", f"{max(0.0, body_dur-2.0):.2f}", "-i", str(base), "-frames:v", "1", "-vf",
         f"scale={PANEL_W}:{NB_BOT_H}:force_original_aspect_ratio=increase,crop={PANEL_W}:{NB_BOT_H},{dim}",
         str(nb_bot_img)], "nbbot")

    # filtergraph final
    inp = ["-i", str(base), "-i", str(voice), "-i", str(asset / "flash.png"), "-i", str(ECLAIR)]
    idx = 4
    shidx = {}
    for n in shock_word:
        shidx[n] = idx; inp += ["-i", str(asset / f"sh{n}.png")]; idx += 1
    spidx = []
    for (p, a, b) in subs:
        spidx.append(idx); inp += ["-i", str(p)]; idx += 1
    nbt_idx = idx; inp += ["-i", str(nb_top_img)]; idx += 1
    nbb_idx = idx; inp += ["-i", str(nb_bot_img)]; idx += 1

    # DOCTRINE : plus AUCUNE inversion N&B. Les impacts sont des burst bubbles (starburst), pas des flashs.
    nodes = ["[0:v]null[v0]"]
    cur, k = "v0", 0
    # éclair (dans le ciel, derrière) sur 2 flashs
    for i, ft2 in enumerate(eclair_at):
        k += 1; nn = f"v{k}"
        nodes.append(f"[3:v]scale=-1:820{',hflip' if i%2 else ''}[e{i}];"
                     f"[{cur}][e{i}]overlay={60 if i%2==0 else 470}:-180:enable='between(t,{ft2:.2f},{ft2+0.10:.2f})'[{nn}]")
        cur = nn
    for ft2 in flashes:
        k += 1; nn = f"v{k}"
        nodes.append(f"[{cur}][2:v]overlay=0:0:enable='between(t,{ft2:.2f},{ft2+0.08:.2f})'[{nn}]"); cur = nn
    for n in shock_word:
        t0, t1 = shock_t[n], shock_end[n]
        if shock_kind[n] == "impact":
            # starburst centré H, hauteur ~620. Position verticale SELON LE PLAN :
            #   buste (visage)        -> y=H*0.57 (sur le visage, cf. FEED THE MARKET)
            #   champ/insert (seg4)   -> y=H*0.42 (centré, pas d'avatar à éviter, cf. ZERO)
            #   plein-pied (avatar)   -> y=H*0.28 (AU-DESSUS de la tête du perso, pas dessus)
            # DANS LA CASE : buste rempli -> impact sur le visage (0.34) ; plein-pied 0.30 (top >= ACT_TOP) ;
            # seg4 insert centré 0.42. Starburst confiné dans la case active.
            yc = 0.34 if n in buste_segs else (0.42 if n == 4 else 0.30)
            pop = f"620*(0.86+0.14*min(1\\,(t-{t0})/0.12))"
            k += 1; nn = f"v{k}"
            nodes.append(f"[{shidx[n]}:v]scale=-1:h='{pop}':eval=frame[w{n}];"
                         f"[{cur}][w{n}]overlay=x=(W-w)/2:y='(H*{yc})-(h/2)':enable='between(t,{t0},{t1})'[{nn}]"); cur = nn
        else:
            # dialogue (template Simon) — COLLÉ au coin intérieur haut-gauche de la case : flush
            # trait haut + trait gauche (peut mordre le trait, jamais la gouttière). Pas de flottement.
            sc, px, py = (700, PANEL_X0, ACT_TOP) if n in buste_segs else (680, PANEL_X0, ACT_TOP)
            k += 1; nn = f"v{k}"
            nodes.append(f"[{shidx[n]}:v]scale={sc}:-1[b{n}];"
                         f"[{cur}][b{n}]overlay={px}:{py}:enable='between(t,{t0},{t1})'[{nn}]"); cur = nn
    for (p, a, b), ix in zip(subs, spidx):
        k += 1; nn = f"v{k}"
        nodes.append(f"[{cur}][{ix}:v]overlay=x=(W-w)/2:y={ACT_BOT - PANEL_BORDER - 8}-h:enable='between(t,{a:.2f},{b:.2f})'[{nn}]"); cur = nn
    # PLANCHE BD (corps uniquement, générique reste plein cadre) : gouttière blanc cassé ->
    # cases VOISINES (crops réels de l'épisode, assombris) -> traits noirs épais.
    k += 1; nn = f"v{k}"; nodes.append(f"[{cur}]{GUTTERS}[{nn}]"); cur = nn
    k += 1; nn = f"v{k}"; nodes.append(f"[{cur}][{nbt_idx}:v]overlay={PANEL_X0}:0[{nn}]"); cur = nn
    k += 1; nn = f"v{k}"; nodes.append(f"[{cur}][{nbb_idx}:v]overlay={PANEL_X0}:{NB_BOT_Y}[{nn}]"); cur = nn
    k += 1; nodes.append(f"[{cur}]{BORDERS},format=yuv420p[vb]")   # garde le jaune des captions

    # audio corps = voix (adelay LEAD) + orage (rumble bcl + crack sur flashs)
    total = body_dur
    an = [f"[1:a]adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo]",
          f"[4:a]volume=0.0[dummy]" if False else ""]
    an = [x for x in an if x]
    # rumble en lit
    inp += ["-stream_loop", "-1", "-i", str(RUMBLE)]
    rumble_i = idx; idx += 1
    an = [f"[1:a]adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=1.0[vo]",
          f"[{rumble_i}:a]atrim=0:{total:.2f},volume=0.30[amb]",
          f"[vo][amb]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.97[abody]"]
    fc = ";".join(nodes + an)

    body = work / "body_full.mp4"
    run([FF, "-y", "-v", "error", *inp, "-filter_complex", fc, "-map", "[vb]", "-map", "[abody]",
         "-t", f"{total:.2f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(body)], "bodyfull")

    # générique + transition audio (orage monte + Veo bave), même logique qu'ep01_fix
    gen_audio_fix(body, work, ep)


def gen_audio_fix(body, work, ep):
    out = ROOT / "output" / "v3" / f"EPISODE_{ep:02d}_kongrave.mp4"
    INTRO = 4.0
    body_dur = dur_of(body)
    bwav = work / "bodya.wav"
    run([FF, "-y", "-v", "error", "-i", str(body), "-vn", "-c:a", "pcm_s16le", str(bwav)], "bodya")
    # lit d'orage intro = RUMBLE PUR bouclé sur 4.0 s (PAS de voix). Bug corrigé : avant on
    # boomerangeait body[0:2] qui contient ~0.5 s de voix (la voix démarre à 1.5 s) -> la voix
    # de l'avatar fuyait dans le générique. Niveau calé sur l'orage du corps (rumble*0.30), montée.
    bed = work / "bed.wav"
    run([FF, "-y", "-v", "error", "-stream_loop", "-1", "-i", str(RUMBLE), "-t", "4",
         "-af", "volume='0.30*(0.22+0.78*t/4)':eval=frame", "-c:a", "pcm_s16le", str(bed)], "bed")
    basea = work / "basea.wav"
    run([FF, "-y", "-v", "error", "-i", str(bed), "-i", str(bwav), "-filter_complex",
         "[0:a][1:a]concat=n=2:v=0:a=1[a]", "-map", "[a]", "-c:a", "pcm_s16le", str(basea)], "basea")
    veo = work / "veo.wav"
    run([FF, "-y", "-v", "error", "-i", str(GEN), "-vn", "-af",
         "apad=whole_dur=5.6,aecho=0.85:0.5:280|560|960:0.4|0.28|0.18,afade=t=out:st=4.0:d=1.6",
         "-c:a", "pcm_s16le", str(veo)], "veo")
    fina = work / "fina.wav"
    run([FF, "-y", "-v", "error", "-i", str(basea), "-i", str(veo), "-filter_complex",
         "[0:a][1:a]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.97[a]",
         "-map", "[a]", "-c:a", "pcm_s16le", str(fina)], "fina")
    # concat vidéo générique + corps, mux audio final
    total = INTRO + body_dur
    genv = work / "genv.mp4"
    run([FF, "-y", "-v", "error", "-i", str(GEN), "-an", "-vf", f"scale={W}:{H},setsar=1,fps=30",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(genv)], "genv")
    catf = work / "cat.txt"; catf.write_text(f"file '{genv}'\nfile '{body}'\n")
    catv = work / "catv.mp4"
    r = subprocess.run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(catf),
                        "-an", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(catv)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        # fallback concat filter
        run([FF, "-y", "-v", "error", "-i", str(genv), "-i", str(body), "-filter_complex",
             "[0:v][1:v]concat=n=2:v=1[v]", "-map", "[v]", "-c:v", "libx264", "-crf", "18",
             "-pix_fmt", "yuv420p", str(catv)], "catv")
    run([FF, "-y", "-v", "error", "-i", str(catv), "-i", str(fina), "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.2f}", str(out)], "mux")
    print(f"[OK] ep{ep:02d} -> {out}  ({total:.1f}s)")


# ep01 (hors JSON) : mêmes répliques/mots-chocs que le master, voix existantes réutilisées.
EP01 = {"number": 1, "title": "WIPED OUT", "segments": [
    {"segment": 1, "type": "hook",   "voice": "In this game almost everyone gets wiped out. You included. For now.",
     "plan": "perso immobile, bras croisés", "mot_choc": "WIPED OUT", "mot_choc_type": "impact_inversion"},
    {"segment": 2, "type": "reveal", "voice": "I'm Matisse. I run an investment fund. While most people pray for one good trade I answer for real capital.",
     "plan": "buste animé face cam", "mot_choc": "REAL CAPITAL", "mot_choc_type": "bulle_dialogue"},
    {"segment": 3, "type": "lecon",  "voice": "What separates a manager from a gambler isn't luck. It's discipline. And that can be learned.",
     "plan": "corps profil", "mot_choc": "DISCIPLINE", "mot_choc_type": "bulle_dialogue"},
    {"segment": 4, "type": "preuve", "voice": "Nine traders out of ten end up back at zero. I'm still here. Ten years later. That's no accident.",
     "plan": "champ de bataille", "mot_choc": "ZERO", "mot_choc_type": "impact_inversion"},
    {"segment": 5, "type": "cta",    "voice": "I'll teach you to think like a manager. Not a gambler. Here. Every day. Follow me or keep feeding the market.",
     "plan": "buste animé regard caméra", "mot_choc": "FEED THE MARKET", "mot_choc_type": "impact_inversion"},
]}


def seed_ep01_voices(work):
    """Réutilise les voix ep01 validées (output/ep01/plan1..5.mp3) au lieu de re-synthétiser."""
    work.mkdir(parents=True, exist_ok=True)
    for k in (1, 2, 3, 4, 5):
        src = ROOT / "output" / "ep01" / f"plan{k}.mp3"
        dst = work / f"v{k}.mp3"
        if src.exists() and not dst.exists():
            dst.write_bytes(src.read_bytes())


def main():
    d = json.load(open(JSON))
    eps = [int(x) for x in sys.argv[1:]] or [e["number"] for e in d["episodes"]]
    by = {e["number"]: e for e in d["episodes"]}
    by[1] = EP01
    for ep in eps:
        if ep not in by:
            print(f"[skip] ep{ep} absent du JSON"); continue
        work = ROOT / "output" / "batch" / f"ep{ep:02d}"
        if ep == 1:
            seed_ep01_voices(work)
        build(ep, by[ep], work)


if __name__ == "__main__":
    main()
