#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Story 2 (variante DomoAI) — voix → vidéo : anime l'avatar dessiné (Frank Miller)
à partir d'un .mp3 ElevenLabs, via l'API DomoAI Talking Avatar.

Remplace l'étape HeyGen. Flux :
  1. Charge l'image (avatar Frank Miller) et l'audio (.mp3 de output/).
  2. Calcule la durée réelle de l'audio → `seconds` (cap 60).
  3. POST /v1/video/talking-avatar (image + audio en base64) → task_id.
  4. Poll GET /v1/tasks/{task_id} jusqu'à SUCCESS/FAILED.
  5. Télécharge le .mp4 dans output/.

Usage :
    python avatar_to_video.py --image chemin/vers/frank_miller.png
    python avatar_to_video.py --image avatar.png --mp3 output/reel_2026-06-19_130805.mp3

DOMOAI_API_KEY est lue dans .env.local — jamais en dur, jamais loggée en clair.
"""

import argparse
import base64
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
import os

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────

CREATE_URL = "https://api.domoai.com/v1/video/talking-avatar"
TASK_URL = "https://api.domoai.com/v1/tasks/{task_id}"
MODEL = "talking-avatar-v1"
ASPECT_RATIO = "9:16"          # format Reels portrait
MAX_SECONDS = 60               # plafond API
COST_PER_SECOND = 0.06         # $ par seconde de vidéo (pour le log de conso)

# Prompt d'animation (style et comportement de l'avatar dessiné).
PROMPT = (
    "The character blinks his eyes naturally and regularly throughout the video. "
    "Subtle calm head movements and natural facial micro-expressions. "
    "Keep the high-contrast black-and-white Frank Miller comic ink style fully intact — "
    "sharp inked linework, no smoothing, no blurring. "
    "Composed, serious, authoritative mood."
)

# Polling.
POLL_INTERVAL_S = 10
POLL_TIMEOUT_S = 900           # 15 min

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
ENV_PATH = ROOT / ".env.local"


# ─────────────────────────────────────────────────────────────────────────────
# OUTILS
# ─────────────────────────────────────────────────────────────────────────────

def fatal(message: str) -> None:
    print(f"\n[ERREUR] {message}\n", file=sys.stderr)
    sys.exit(1)


def load_api_key() -> str:
    load_dotenv(ENV_PATH)
    key = os.getenv("DOMOAI_API_KEY", "").strip()
    if not key:
        fatal("DOMOAI_API_KEY manquante dans .env.local (ouvre le fichier, colle la clé).")
    return key


def auth_headers(api_key: str) -> dict:
    # La clé n'est jamais imprimée ; elle ne vit que dans ce header.
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def latest_mp3() -> Path:
    mp3s = sorted(OUTPUT_DIR.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not mp3s:
        fatal("Aucun .mp3 dans output/. Lance d'abord generate.py (Story 1).")
    return mp3s[0]


def audio_seconds(mp3_path: Path) -> int:
    """
    Durée réelle de l'audio, arrondie à l'entier supérieur, plafonnée à MAX_SECONDS.
    Utilise mutagen si dispo (précis) ; sinon estimation 128 kbps (~16 000 octets/s).
    """
    import math
    try:
        from mutagen.mp3 import MP3
        length = MP3(str(mp3_path)).info.length
    except Exception:  # noqa: BLE001 — fallback si mutagen indisponible/illisible
        length = mp3_path.stat().st_size / 16000.0
    return max(1, min(MAX_SECONDS, math.ceil(length)))


def b64_file(path: Path) -> str:
    """Encode un fichier en base64 (chaîne ASCII, sans préfixe data:)."""
    return base64.b64encode(path.read_bytes()).decode("ascii")


# ─────────────────────────────────────────────────────────────────────────────
# API DOMOAI
# ─────────────────────────────────────────────────────────────────────────────

def create_task(api_key: str, image_b64: str, audio_b64: str, seconds: int) -> str:
    """POST de création ; renvoie le task_id."""
    payload = {
        "image": {"bytes_base64_encoded": image_b64},
        "audio": {"bytes_base64_encoded": audio_b64},
        "prompt": PROMPT,
        "seconds": seconds,
        "aspect_ratio": ASPECT_RATIO,
        "model": MODEL,
    }
    try:
        resp = requests.post(CREATE_URL, headers=auth_headers(api_key), json=payload, timeout=180)
    except requests.exceptions.RequestException as exc:
        fatal(f"DomoAI : problème réseau à la création. Détail : {exc}")

    if resp.status_code == 401:
        fatal("DomoAI 401 : clé API invalide ou absente. Vérifie DOMOAI_API_KEY dans .env.local.")
    if resp.status_code == 403:
        body = _safe_json(resp)
        if str(body.get("code")) == "4002":
            fatal("DomoAI 4002 : organisation bannie (Organization is banned). Contacte le support DomoAI.")
        fatal(f"DomoAI 403 : accès refusé. Détail : {resp.text[:300]}")
    if resp.status_code == 402:
        fatal("DomoAI 402 (code 2001) : crédits insuffisants. Recharge ton compte DomoAI, "
              "puis relance la même commande (aucun crédit n'a été débité).")
    if resp.status_code == 422:
        fatal(f"DomoAI 422 : corps invalide (image/audio/seconds ?). Détail : {resp.text[:400]}")
    if resp.status_code != 200:
        fatal(f"DomoAI : HTTP {resp.status_code} à la création. Détail : {resp.text[:400]}")

    body = _safe_json(resp)
    if body.get("code") not in (0, None):
        fatal(f"DomoAI : code d'erreur {body.get('code')} — {body.get('message', resp.text[:200])}")
    task_id = (body.get("data") or {}).get("task_id")
    if not task_id:
        fatal(f"DomoAI : pas de task_id renvoyé. Réponse : {resp.text[:300]}")
    return task_id


def poll_task(api_key: str, task_id: str) -> str:
    """Poll jusqu'à SUCCESS ; renvoie l'URL de la vidéo. Échoue sur FAILED/CANCELED/timeout."""
    url = TASK_URL.format(task_id=task_id)
    deadline = time.monotonic() + POLL_TIMEOUT_S
    last = None
    while time.monotonic() < deadline:
        try:
            resp = requests.get(url, headers=auth_headers(api_key), timeout=60)
        except requests.exceptions.RequestException as exc:
            fatal(f"DomoAI : problème réseau au polling. Détail : {exc}")
        if resp.status_code != 200:
            fatal(f"DomoAI (statut) : HTTP {resp.status_code}. Détail : {resp.text[:300]}")

        data = (_safe_json(resp).get("data") or {})
        status = data.get("status")
        if status != last:
            print(f"    statut : {status}")
            last = status

        if status == "SUCCESS":
            videos = data.get("output_videos") or []
            if not videos or not videos[0].get("url"):
                fatal("DomoAI : tâche réussie mais aucune URL vidéo renvoyée.")
            return videos[0]["url"]
        if status in ("FAILED", "CANCELED"):
            fatal(f"DomoAI : génération {status}. Détail : {resp.text[:300]}")

        time.sleep(POLL_INTERVAL_S)

    fatal(f"DomoAI : délai dépassé ({POLL_TIMEOUT_S}s) sans completion. task_id={task_id}")


def download_video(url: str, out_path: Path = None) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    if out_path is not None:
        path = out_path
    else:
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        path = OUTPUT_DIR / f"reel_domo_{stamp}.mp4"
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                if chunk:
                    f.write(chunk)
    return path


def _safe_json(resp) -> dict:
    try:
        return resp.json() or {}
    except ValueError:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATION
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Story 2 (DomoAI) — voix → avatar dessiné animé.")
    parser.add_argument("--image", required=True, help="Chemin de l'avatar Frank Miller (png/jpg).")
    parser.add_argument("--mp3", default=None, help="Chemin du .mp3 (défaut : le plus récent de output/).")
    parser.add_argument("--seconds", type=int, default=None, help="Forcer la durée (sinon = durée du .mp3, cap 60).")
    parser.add_argument("--out", default=None, help="Forcer le chemin du .mp4 de sortie (sinon nommage auto reel_domo_<stamp>.mp4).")
    args = parser.parse_args()

    api_key = load_api_key()

    image_path = Path(args.image)
    if not image_path.exists():
        fatal(f"Image introuvable : {image_path}")
    mp3_path = Path(args.mp3) if args.mp3 else latest_mp3()
    if not mp3_path.exists():
        fatal(f"Audio introuvable : {mp3_path}")

    seconds = args.seconds if args.seconds else audio_seconds(mp3_path)
    seconds = max(1, min(MAX_SECONDS, seconds))
    cost = seconds * COST_PER_SECOND

    print("=" * 70)
    print(f"Image    : {image_path.name}")
    print(f"Audio    : {mp3_path.name}")
    print(f"Durée    : {seconds}s ({ASPECT_RATIO}, modèle {MODEL})")
    print(f"Coût est.: ~${cost:.2f} ({seconds}s × ${COST_PER_SECOND}/s)")
    print("=" * 70)

    print("\n[1/4] Encodage base64 image + audio…")
    image_b64 = b64_file(image_path)
    audio_b64 = b64_file(mp3_path)
    print(f"    image ~{len(image_b64)//1024} Ko b64 | audio ~{len(audio_b64)//1024} Ko b64")

    print("\n[2/4] Création de la tâche DomoAI…")
    task_id = create_task(api_key, image_b64, audio_b64, seconds)
    print(f"    task_id : {task_id}")

    print("\n[3/4] Génération en cours (polling)…")
    url = poll_task(api_key, task_id)

    print("\n[4/4] Téléchargement du .mp4…")
    out_path = Path(args.out) if args.out else None
    mp4_path = download_video(url, out_path)

    print("\n" + "=" * 70)
    print("✓ TERMINÉ")
    print(f"Vidéo    : {mp4_path}")
    print(f"Taille   : {mp4_path.stat().st_size / (1024*1024):.1f} Mo")
    print(f"Coût est.: ~${cost:.2f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
