#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Story 6 — TEST faisabilité : DomoAI image-to-video (ACTION corporelle, pas lip-sync).

Endpoint : POST /v1/video/image2video (modèle animate-2.4-*). Même polling/tasks que
le talking-avatar. On teste si le perso BOUGE en gardant le binaire strict + son visage.

Sortie : output/test_anim/anim_<slug>.mp4. Aucune intégration — juste le constat.
DOMOAI_API_KEY lue dans .env.local, jamais imprimée.
"""

import base64
import sys
import time
from pathlib import Path

import requests
from avatar_to_video import load_api_key, auth_headers, poll_task, _safe_json

I2V_URL = "https://api.domoai.com/v1/video/image2video"
MODEL = "animate-2.4-faster"
ASPECT = "9:16"
COST_PER_SECOND = 0.06   # estimation (tarif talking-avatar) — à confirmer sur la facture

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "output" / "test_anim"
IMAGE = ROOT / "assets" / "plein_pied_binaire_parfait.png"

BINARY = ("high-contrast pure black and white ink comic style, sharp inked linework, "
          "no grayscale, no smoothing, no blur")
CLIPS = [
    ("bras_croises", 4,
     "The man crosses his arms slowly with a calm, authoritative posture, minimal subtle "
     "body motion, he stays in frame, " + BINARY),
    ("boit_verre", 5,
     "The man slowly raises a glass and drinks, minimal subtle motion, he stays in frame, " + BINARY),
]


def create_i2v(api_key, image_b64, seconds, prompt):
    payload = {"model": MODEL, "image": {"bytes_base64_encoded": image_b64},
               "seconds": seconds, "aspect_ratio": ASPECT, "prompt": prompt}
    r = requests.post(I2V_URL, headers=auth_headers(api_key), json=payload, timeout=180)
    if r.status_code == 401:
        sys.exit("[ERREUR] DomoAI 401 : clé invalide/expirée (.env.local).")
    if r.status_code == 404:
        sys.exit("[CONSTAT] image2video introuvable (404) → DomoAI ne fait peut-être que le talking-avatar.")
    if r.status_code != 200:
        sys.exit(f"[ERREUR] DomoAI HTTP {r.status_code} : {r.text[:400]}")
    body = _safe_json(r)
    if body.get("code") not in (0, None):
        sys.exit(f"[ERREUR] DomoAI code {body.get('code')} : {body.get('message', r.text[:200])}")
    tid = (body.get("data") or {}).get("task_id")
    if not tid:
        sys.exit(f"[ERREUR] pas de task_id : {r.text[:300]}")
    return tid


def download(url, path):
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for ch in r.iter_content(1 << 16):
                if ch:
                    f.write(ch)
    return path


def main():
    if not IMAGE.exists():
        sys.exit(f"[ERREUR] image introuvable : {IMAGE}")
    api_key = load_api_key()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image_b64 = base64.b64encode(IMAGE.read_bytes()).decode("ascii")
    print(f"image2video | modèle {MODEL} | {ASPECT} | image {IMAGE.name}")
    total = 0.0
    for slug, secs, prompt in CLIPS:
        print(f"\n=== {slug} ({secs}s) ===")
        tid = create_i2v(api_key, image_b64, secs, prompt)
        print(f"    task_id : {tid}")
        url = poll_task(api_key, tid)
        out = OUT_DIR / f"anim_{slug}.mp4"
        download(url, out)
        cost = secs * COST_PER_SECOND
        total += cost
        print(f"    -> {out}  ({out.stat().st_size/1024/1024:.1f} Mo)  coût est.~${cost:.2f}")
    print(f"\nCoût total estimé ~${total:.2f} (à {COST_PER_SECOND}$/s, estimation)")


if __name__ == "__main__":
    main()
