#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère les BUSTES LIP-SYNC PROPRES à un épisode (RÈGLE GRAVÉE : on ne réutilise JAMAIS les
bustes d'un autre épisode). DomoAI Talking-Avatar(image buste face, audio du segment) -> lip-sync
calé sur l'audio ElevenLabs de CET épisode -> détour alpha (detourage_video.py, fond blanc).

Sortie : output/batch/ep{NN}/buste{2,5}_alpha.mov (consommés par build_episode.py).
Usage : python regen_bustes.py <ep>   (ex. python regen_bustes.py 2)
"""
import math
import os
import subprocess
import sys
from pathlib import Path

from avatar_to_video import (load_api_key, create_task, poll_task, download_video,
                             audio_seconds, b64_file)

ROOT = Path(__file__).resolve().parent
FF = os.environ.get("FFMPEG") or "/opt/homebrew/bin/ffmpeg"
BUSTE_IMG = ROOT / "assets" / "buste_binaire_parfait.png"   # face cam N&B sur blanc (détourable)
BUSTE_SEGS = (2, 5)   # seg2 = reveal face cam, seg5 = cta face cam
# DomoAI talking-avatar : durée de sortie plafonnée à 4s (contrainte 2026-07-08, error 1004).
# Voix ≤ MONO_MAX -> 1 clip (seconds=4). Voix plus longues -> découpage en tranches ≤ CHUNK_MAX,
# 1 clip par tranche (MÊME image source -> le visage NE DÉRIVE PAS), puis concat -> lip-sync complet.
MAX_SECS = 4
MONO_MAX = 4.15      # au-delà, on découpe (sous ça, un léger gel de fin <0.15s est invisible)
CHUNK_MAX = 3.8


def _dur(path):
    r = subprocess.run([FF.replace("ffmpeg", "ffprobe"), "-v", "error",
                        "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def _one_clip(api_key, audio_path, out, secs):
    # DomoAI plafonne (et fait fluctuer) la durée max du talking-avatar -> on tente en descendant
    # les secondes jusqu'à ce que ça passe (un léger gel de fin est invisible).
    ib, ab = b64_file(BUSTE_IMG), b64_file(audio_path)
    tried = []
    for s in [min(MAX_SECS, max(1, secs)), 3, 2]:
        if s in tried:
            continue
        tried.append(s)
        try:
            tid = create_task(api_key, ib, ab, s)
            print(f"    task_id : {tid} (seconds={s})", flush=True)
            download_video(poll_task(api_key, tid), out)
            return
        except SystemExit as e:
            if "cannot exceed" in str(e) or "1004" in str(e):
                print(f"    plafond DomoAI atteint à {s}s, retry plus court…", flush=True)
                continue
            raise
    sys.exit("[ERREUR] DomoAI refuse même 2s pour ce buste (throttling sévère).")


def gen_buste(api_key, ep, seg):
    work = ROOT / "output" / "batch" / f"ep{ep:02d}"
    audio = work / f"v{seg}.mp3"
    if not audio.is_file():
        sys.exit(f"[ERREUR] audio segment manquant : {audio}\n"
                 f"Lance d'abord build_episode.py {ep} (il synthétise les voix par segment).")
    raw = work / f"buste{seg}_raw.mp4"
    alpha = work / f"buste{seg}_alpha.mov"
    if not raw.exists():
        D = _dur(audio)
        if D <= MONO_MAX:
            print(f"=== ep{ep:02d} buste seg{seg} ({D:.2f}s, 1 clip) — DomoAI ===", flush=True)
            _one_clip(api_key, audio, raw, MAX_SECS)
        else:
            n = math.ceil(D / CHUNK_MAX)
            print(f"=== ep{ep:02d} buste seg{seg} ({D:.2f}s > 4s) — {n} tranches lip-sync concaténées ===", flush=True)
            parts = []
            for i in range(n):
                st, du = i * D / n, D / n
                chunk = work / f"v{seg}_p{i}.mp3"
                subprocess.run([FF, "-y", "-v", "error", "-ss", f"{st:.3f}", "-t", f"{du:.3f}",
                                "-i", str(audio), "-c", "copy", str(chunk)], check=True)
                praw = work / f"buste{seg}_p{i}_raw.mp4"
                _one_clip(api_key, chunk, praw, math.ceil(du))
                # recaler la durée exacte de la tranche (le clip DomoAI peut être un peu plus long) -> pas de dérive
                ptrim = work / f"buste{seg}_p{i}.mp4"
                subprocess.run([FF, "-y", "-v", "error", "-i", str(praw), "-t", f"{du:.3f}",
                                "-an", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(ptrim)], check=True)
                parts.append(ptrim)
            lst = work / f"buste{seg}_concat.txt"
            lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
            subprocess.run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                            "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(raw)], check=True)
        print(f"    -> {raw.name} ({raw.stat().st_size/1024/1024:.1f} Mo)", flush=True)
    else:
        print(f"=== ep{ep:02d} buste seg{seg} déjà généré (skip) ===", flush=True)
    if not alpha.exists():
        r = subprocess.run([sys.executable, "detourage_video.py", str(raw), str(alpha)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("[DETOUR ERR]\n" + r.stderr[-1000:])
        print(f"    détouré -> {alpha.name}", flush=True)


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage : python regen_bustes.py <ep>")
    ep = int(sys.argv[1])
    api_key = load_api_key()
    for seg in BUSTE_SEGS:
        gen_buste(api_key, ep, seg)
    cost = sum(audio_seconds(ROOT / "output" / "batch" / f"ep{ep:02d}" / f"v{s}.mp3") for s in BUSTE_SEGS) * 0.06
    print(f"\n[FAIT] ep{ep:02d} bustes {BUSTE_SEGS} lip-sync. Coût DomoAI estimé ~${cost:.2f}", flush=True)


if __name__ == "__main__":
    main()
