#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Story 5 — détourage VIDÉO : fond blanc DomoAI → alpha transparent, frame par frame.

Même principe que detourage.py (images) : segmentation par FORME (isnet-anime),
JAMAIS de chroma key blanc (ça trouerait chemise/visage blancs). Par frame :
  masque anime ∪ (tout SAUF le blanc connecté aux bords) → trous bouchés →
  plus grande composante → érosion 1 px (anti-halo).

Décodage cv2, ré-encodage ProRes 4444 (alpha, yuva444p10le) via ffmpeg embarqué
(imageio-ffmpeg). AUCUN audio (la voix vient des mp3, piste séparée).

Usage : python detourage_video.py in.mp4 out.mov
Sort aussi une frame de contrôle sur damier : <out>_check.png
"""

import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage
import imageio_ffmpeg

BG_WHITE = 234          # pixel quasi-blanc si tous canaux >= seuil
THRESH = 50             # binarisation du masque anime
ERODE = 1               # anti-halo


def alpha_from_rgb(rgb: np.ndarray, session) -> np.ndarray:
    """rgb HxWx3 uint8 -> alpha HxW uint8 (0/255), figure pleine, blanc préservé."""
    from rembg import remove
    pil = Image.fromarray(rgb, "RGB")
    mask = np.array(remove(pil, session=session, only_mask=True))
    anime = ndimage.binary_fill_holes(mask > THRESH)

    near_white = np.all(rgb >= BG_WHITE, axis=2)
    wl, _ = ndimage.label(near_white)
    border = set(np.unique(np.concatenate([wl[0, :], wl[-1, :], wl[:, 0], wl[:, -1]])))
    border.discard(0)
    background = np.isin(wl, list(border))

    binar = (~background) | anime
    binar = ndimage.binary_fill_holes(binar)
    lbl, n = ndimage.label(binar)
    if n > 1:
        sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
        binar = lbl == (1 + int(np.argmax(sizes)))
    if ERODE:
        binar = ndimage.binary_erosion(binar, iterations=ERODE)
    return np.where(binar, 255, 0).astype(np.uint8)


def checker(w, h, sq=40):
    a = np.zeros((h, w, 3), np.uint8)
    for y in range(0, h, sq):
        for x in range(0, w, sq):
            a[y:y+sq, x:x+sq] = 200 if ((x//sq + y//sq) % 2 == 0) else 120
    return a


def main():
    src = Path(sys.argv[1]); dst = Path(sys.argv[2])
    if not src.exists():
        sys.exit(f"[ERREUR] introuvable : {src}")

    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"{src.name} : {n} frames, {fps:.0f} fps, {w}x{h} -> {dst.name} (ProRes 4444 alpha)")

    from rembg import new_session
    session = new_session("isnet-anime")

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-f", "rawvideo", "-pixel_format", "rgba",
           "-video_size", f"{w}x{h}", "-framerate", f"{fps}", "-i", "-",
           "-an", "-c:v", "prores_ks", "-profile:v", "4444",
           "-pix_fmt", "yuva444p10le", str(dst)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    check_idx = n // 2
    i = 0
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        alpha = alpha_from_rgb(rgb, session)
        rgba = np.dstack([rgb, alpha])
        proc.stdin.write(rgba.tobytes())
        if i == check_idx:                       # frame de contrôle sur damier
            base = checker(w, h)
            a = alpha.astype(np.float32) / 255.0
            comp = (rgb * a[..., None] + base * (1 - a[..., None])).astype(np.uint8)
            Image.fromarray(comp).save(str(dst.with_name(dst.stem + "_check.png")))
        i += 1
        if i % 25 == 0:
            print(f"   {i}/{n}")
    cap.release()
    proc.stdin.close()
    proc.wait()
    print(f"OK : {dst}  ({dst.stat().st_size/1024/1024:.1f} Mo) | check: {dst.stem}_check.png")


if __name__ == "__main__":
    main()
