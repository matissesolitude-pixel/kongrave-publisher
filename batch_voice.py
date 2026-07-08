#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch voix KONGRAVE ep02-ep28 : concatène les 5 segments 'voice' de chaque épisode
et synthétise via ElevenLabs (recette prod validée). Sortie audio/epNN_voice.mp3.
Usage : batch_voice.py            -> tous les épisodes
        batch_voice.py 2 3        -> seulement ep02, ep03
Clé lue dans .env.local (jamais imprimée)."""
import json, os, subprocess, sys
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env.local")
KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE = "5wFwpkZR2Yf6aS6EXd8M"
MODEL = "eleven_multilingual_v2"
FMT = "mp3_44100_128"
SETTINGS = {"stability": 0.50, "similarity_boost": 0.75, "style": 0.0,
            "speed": 1.00, "use_speaker_boost": True}
OUT = ROOT / "audio"; OUT.mkdir(exist_ok=True)
JSON = ROOT / "KONGRAVE_episodes_02_to_28.json"


def tts(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}"
    r = requests.post(url, headers={"xi-api-key": KEY, "Content-Type": "application/json"},
                      params={"output_format": FMT},
                      json={"text": text, "model_id": MODEL, "voice_settings": SETTINGS}, timeout=180)
    if r.status_code != 200:
        sys.exit(f"[ERREUR] ElevenLabs HTTP {r.status_code} : {r.text[:300]}")
    if not r.content:
        sys.exit("[ERREUR] réponse vide")
    return r.content


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nk=1:nw=1", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    if not KEY:
        sys.exit("[ERREUR] ELEVENLABS_API_KEY absente de .env.local")
    d = json.load(open(JSON))
    only = set(int(x) for x in sys.argv[1:]) if len(sys.argv) > 1 else None
    rows = []
    for e in d["episodes"]:
        n = e["number"]
        if only and n not in only:
            continue
        segs = sorted(e["segments"], key=lambda s: s["segment"])
        text = " ".join(s["voice"].strip() for s in segs)
        dst = OUT / f"ep{n:02d}_voice.mp3"
        dst.write_bytes(tts(text))
        dd = dur(dst)
        rows.append((n, e["title"], dd))
        print(f"ep{n:02d}  {e['title']:<18} {dd:5.1f}s" + ("   OVER 35s" if dd > 35 else ""))
    print(f"\n[OK] {len(rows)} voix -> {OUT}")
    over = [r for r in rows if r[2] > 35]
    if over:
        print("DEPASSEMENTS >35s : " + ", ".join(f"ep{n:02d} ({dd:.1f}s)" for n, _, dd in over))
    else:
        print("Aucun episode ne depasse 35s.")


if __name__ == "__main__":
    main()
