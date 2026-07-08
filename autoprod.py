#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""autoprod.py — production autonome d'UN épisode KONGRAVE par run (GitHub Actions, cron 4h).

Bout en bout, sans intervention :
  1. prochain épisode non produit  (ordre JSON, marqueur = inbox/EPISODE_NN_kongrave.mp4)
  2. insert seg4 selon le type :
       - champ (ep02/03/13)      : asset statique (champ_bataille.png, géré par build_episode)
       - prop concept            : rendu HyperFrames du HTML commité props/ep{NN}.html (Node/Chromium)
       - narratif                : Gemini image -> OCR anti-texte + retry -> DomoAI i2v
  3. voix ElevenLabs  ->  bustes DomoAI (cap 4s + découpage/concat + retry, cf. regen_bustes)
  4. assemblage build_episode  ->  output/v3/EPISODE_NN_kongrave.mp4
  5. copie inbox/  +  MAJ schedule.json (date planifiée + caption)  [le commit/push est fait par le workflow]

1 seul épisode par run pour ménager le throttle DomoAI. Env requis : ELEVENLABS_API_KEY,
DOMOAI_API_KEY, GEMINI_API_KEY (+ FFMPEG/FFPROBE sur le runner Linux).
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON = ROOT / "KONGRAVE_episodes_02_to_28_v2.json"
INBOX = ROOT / "inbox"
SCHEDULE = ROOT / "schedule.json"
HF = ROOT / "hf"                       # projet HyperFrames (hyperframes.json/meta.json/assets)
PROPS = ROOT / "props"                 # compositions prop commitées : props/ep{NN}.html
PY = sys.executable

# --- classification seg4 -----------------------------------------------------
CHAMP = {2, 3, 13}
PROP = {5, 7, 9, 10, 15, 17, 19, 22, 24, 25}
NARRATIVE_TEXT_OK = {11}               # journal : écriture manuscrite intrinsèque -> pas d'OCR

def seg4_type(n):
    return "champ" if n in CHAMP else ("prop" if n in PROP else "narrative")

# --- planning ----------------------------------------------------------------
# 4 reels/jour à partir du lundi 14 juillet 2026, heures Dubai (UTC+4). 28 ép. = 7 j (jusqu'au 20).
TZ = timezone(timedelta(hours=4))
START = datetime(2026, 7, 14, tzinfo=TZ)
SLOTS = [8, 12, 17, 21]

def publish_dt(n):
    idx = n - 1                        # ep01 = index 0
    day, slot = divmod(idx, len(SLOTS))
    return (START + timedelta(days=day)).replace(hour=SLOTS[slot], minute=0, second=0)

HASHTAGS = "#kongrave #trading #forex #tradingpsychology #riskmanagement #disruptive"
CTA = "Reply GAME — tell me what wiped YOU out. The best stories become episodes."

def caption_for(ep):
    # "règle en une phrase" = la punchline de fermeture (seg5), sans le point final superflu
    rule = next(s["voice"] for s in ep["segments"] if s["segment"] == 5).strip()
    return f"{rule}\n\n{CTA}\n\n{HASHTAGS}"

# --- helpers -----------------------------------------------------------------
def run(cmd, **kw):
    print("  $ " + " ".join(str(c) for c in cmd), flush=True)
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        sys.exit(f"[AUTOPROD] échec : {' '.join(str(c) for c in cmd)}")
    return r

def load_episodes():
    return sorted(json.load(open(JSON))["episodes"], key=lambda e: e["number"])

def next_episode(eps):
    for e in eps:
        n = e["number"]
        if n < 2:
            continue
        if not (INBOX / f"EPISODE_{n:02d}_kongrave.mp4").exists():
            return e
    return None

# --- seg4 : prop HyperFrames -------------------------------------------------
def make_prop(n):
    html = PROPS / f"ep{n:02d}.html"
    if not html.exists():
        sys.exit(f"[AUTOPROD] composition prop absente : {html} (à committer).")
    shutil.copy(html, HF / "index.html")
    run(["npm", "--prefix", str(HF), "run", "render"])
    renders = sorted((HF / "renders").glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    if not renders:
        sys.exit("[AUTOPROD] aucun rendu HyperFrames produit.")
    dst = ROOT / "output" / "batch" / f"ep{n:02d}" / "seg4_hf.mp4"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(renders[-1], dst)
    print(f"  [prop] {html.name} -> {dst}", flush=True)

# --- seg4 : scène narrative (Gemini + OCR retry + DomoAI) --------------------
def make_narrative(n):
    import gen_seg4_narratif as g
    import scene_textcheck as tc
    if n not in g.SCENES:
        sys.exit(f"[AUTOPROD] pas de prompt narratif pour ep{n:02d} (dict SCENES).")
    scene, anim = g.SCENES[n]
    img = ROOT / "assets" / f"scene_seg4_ep{n:02d}.png"
    check = n not in NARRATIVE_TEXT_OK
    for attempt in range(3):
        extra = "" if attempt == 0 else (
            " ABSOLUTELY NO text, NO letters, NO words, NO signage with writing anywhere in the image.")
        g.gen_image(scene + extra, img)
        if not check or not tc.image_has_text(str(img)):
            break
        print(f"  [narratif] texte détecté, régénération {attempt+2}/3…", flush=True)
    d = ROOT / "output" / "batch" / f"ep{n:02d}"; d.mkdir(parents=True, exist_ok=True)
    raw = d / "seg4_i2v_raw.mp4"; dst = d / "seg4_hf.mp4"
    g.animate(anim, img, raw)
    g.finish(raw, dst)
    print(f"  [narratif] -> {dst}", flush=True)

# --- pipeline ----------------------------------------------------------------
def produce(e):
    n = e["number"]
    typ = seg4_type(n)
    print(f"=== AUTOPROD ep{n:02d} {e['title']} | seg4={typ} ===", flush=True)

    # 1) voix (build_episode génère les v{n}.mp3 puis s'arrête au buste manquant : normal)
    subprocess.run([PY, "build_episode.py", str(n)], cwd=ROOT)

    # 2) seg4 insert
    if typ == "prop":
        make_prop(n)
    elif typ == "narrative":
        make_narrative(n)
    # champ : rien à faire, build_episode le génère depuis champ_bataille.png

    # 3) bustes lip-sync (cap 4s + découpage/concat + retry auto intégrés dans regen_bustes)
    run([PY, "regen_bustes.py", str(n)], cwd=ROOT)

    # 4) assemblage final
    run([PY, "build_episode.py", str(n)], cwd=ROOT)
    src = ROOT / "output" / "v3" / f"EPISODE_{n:02d}_kongrave.mp4"
    if not src.exists():
        sys.exit(f"[AUTOPROD] assemblage manquant : {src}")

    # 5) inbox + schedule
    INBOX.mkdir(exist_ok=True)
    dst = INBOX / f"EPISODE_{n:02d}_kongrave.mp4"
    shutil.copy(src, dst)
    sched = json.load(open(SCHEDULE)) if SCHEDULE.exists() else []
    sched = [x for x in sched if x.get("episode_number") != n]
    sched.append({
        "episode_number": n,
        "filepath": f"inbox/EPISODE_{n:02d}_kongrave.mp4",
        "caption": caption_for(e),
        "publish_datetime": publish_dt(n).isoformat(),
    })
    sched.sort(key=lambda x: x["episode_number"])
    json.dump(sched, open(SCHEDULE, "w"), ensure_ascii=False, indent=2)
    print(f"[AUTOPROD] ep{n:02d} PRODUIT -> {dst.name}  (publish {publish_dt(n).isoformat()})", flush=True)


def main():
    import os
    eps = load_episodes()
    forced = (os.environ.get("FORCE_EPISODE") or "").strip()
    if forced:
        e = next((x for x in eps if x["number"] == int(forced)), None)
        if e is None:
            sys.exit(f"[AUTOPROD] épisode forcé introuvable : {forced}")
    else:
        e = next_episode(eps)
    if e is None:
        print("[AUTOPROD] tous les épisodes sont produits — rien à faire.", flush=True)
        return
    produce(e)


if __name__ == "__main__":
    main()
