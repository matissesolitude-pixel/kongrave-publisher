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

import os
ROOT = Path(__file__).resolve().parent
JSON = Path(os.environ.get("KONGRAVE_JSON") or ROOT / "KONGRAVE_episodes_02_to_28_v3.json")
INBOX = ROOT / "inbox"
SCHEDULE = ROOT / "schedule.json"
HF = ROOT / "hf"                       # projet HyperFrames (hyperframes.json/meta.json/assets)
PROPS = ROOT / "props"                 # compositions prop commitées : props/ep{NN}.html
PY = sys.executable

from seg4_routing import resolve_seg4_type, log_s2_metadata

# --- classification seg4 (v4 : le routage lit seg4_type explicite via seg4_routing) -----------
NARRATIVE_TEXT_OK = {11}               # journal : écriture manuscrite intrinsèque -> pas d'OCR

# --- planning ----------------------------------------------------------------
# CADENCE 6h à partir du 9 juillet 2026 01:00 Dubai (UTC+4) : ep_n = base + 6h*(n-1).
TZ = timezone(timedelta(hours=4))
BASE = datetime(2026, 7, 9, 2, 0, tzinfo=TZ)     # ancre = ep02 (9 juil 02:00 Dubai)

def publish_dt(n):
    return BASE + timedelta(hours=6 * (n - 2))   # ep02=base, ep03=+6h, … ep12=+60h (fallback)

def next_publish_dt(sched):
    """Prochain créneau = dernier planifié + 6h. ROBUSTE aux recalages manuels du schedule
    (holds, réinsertions) : on ne recalcule pas par formule (qui ignore les décalages faits à
    la main), on continue la cadence après le dernier créneau réel. Fallback formule si vide."""
    dts = []
    for x in sched:
        try:
            dts.append(datetime.fromisoformat(x["publish_datetime"]))
        except (KeyError, ValueError, TypeError):
            pass
    return (max(dts) + timedelta(hours=6)) if dts else BASE

HASHTAGS = "#kongrave #trading #forex #tradingpsychology #riskmanagement #disruptive"
# CTA en PREMIÈRE ligne (décision PO), "Comment" (pas "Reply")
CTA = "Comment GAME — tell me what wiped YOU out. The best stories become episodes."

def caption_for(ep):
    # template : CTA d'abord, puis la règle (punchline seg5), puis hashtags
    rule = next(s["voice"] for s in ep["segments"] if s["segment"] == 5).strip()
    return f"{CTA}\n\n{rule}\n\n{HASHTAGS}"

# --- helpers -----------------------------------------------------------------
def run(cmd, **kw):
    print("  $ " + " ".join(str(c) for c in cmd), flush=True)
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        sys.exit(f"[AUTOPROD] échec : {' '.join(str(c) for c in cmd)}")
    return r

def load_episodes():
    import kongrave_episodes
    return kongrave_episodes.load_all()   # s1 (v3) + s2 (saison2 si présent), triés par number

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
def make_narrative(n, e=None):
    """Insert narratif (Gemini -> OCR anti-texte/chiffre -> DomoAI).
    s1 : prompt figé dans g.SCENES. s2 (ep>=29) : le prompt vient du `plan` du seg4 dans le JSON."""
    import gen_seg4_narratif as g
    if n in g.SCENES:
        scene, anim = g.SCENES[n]
    elif e is not None:
        seg4 = next((s for s in e["segments"] if s["segment"] == 4), None)
        if not seg4 or not seg4.get("plan"):
            sys.exit(f"[AUTOPROD] ep{n:02d} narratif : ni g.SCENES ni plan seg4 dans le JSON.")
        scene = seg4["plan"]                     # le plan JSON EST la description de scène
        anim = "Slow subtle push-in, faint motion, oppressive noir stillness. No people, no text, no numbers."
    else:
        sys.exit(f"[AUTOPROD] pas de prompt narratif pour ep{n:02d}.")
    img = ROOT / "assets" / f"scene_seg4_ep{n:02d}.png"
    # gen_image applique déjà NO_NUMBERS + garde-fou OCR (texte ET chiffres) en interne.
    g.gen_image(scene, img, allow_text=(n in NARRATIVE_TEXT_OK))
    d = ROOT / "output" / "batch" / f"ep{n:02d}"; d.mkdir(parents=True, exist_ok=True)
    raw = d / "seg4_i2v_raw.mp4"; dst = d / "seg4_hf.mp4"
    g.animate(anim, img, raw)
    g.finish(raw, dst)
    print(f"  [narratif] -> {dst}", flush=True)

# --- pipeline ----------------------------------------------------------------
def produce(e):
    n = e["number"]
    log_s2_metadata(e, n)               # métadonnées v4 : loggées, jamais bloquantes
    typ = resolve_seg4_type(e, n)       # routage explicite (fail loud si s2 sans seg4_type)
    print(f"=== AUTOPROD ep{n:02d} {e['title']} | seg4={typ} ===", flush=True)

    # 1) voix (build_episode génère les v{n}.mp3 puis s'arrête au buste manquant : normal)
    subprocess.run([PY, "build_episode.py", str(n)], cwd=ROOT)

    # 2) seg4 insert
    if typ == "prop":
        make_prop(n)
    elif typ == "narratif":
        make_narrative(n, e)
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
    reserved = next((x for x in sched if x.get("episode_number") == n), None)
    sched = [x for x in sched if x.get("episode_number") != n]
    if reserved and reserved.get("publish_datetime"):
        # créneau DÉJÀ réservé (pré-planifié à la main) : on le respecte, on ne recalcule pas.
        # sinon un épisode produit dans le désordre (pilotes pré-faits, quota) casserait l'ordre.
        when = datetime.fromisoformat(reserved["publish_datetime"])
    else:
        when = next_publish_dt(sched)           # nouvel épisode : après le dernier créneau réel (+6h)
    sched.append({
        "episode_number": n,
        "filepath": f"inbox/EPISODE_{n:02d}_kongrave.mp4",
        "caption": caption_for(e),
        "publish_datetime": when.isoformat(),
    })
    sched.sort(key=lambda x: x["episode_number"])
    json.dump(sched, open(SCHEDULE, "w"), ensure_ascii=False, indent=2)
    print(f"[AUTOPROD] ep{n:02d} PRODUIT -> {dst.name}  (publish {when.isoformat()})", flush=True)


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
        return None
    produce(e)
    return e["number"]


if __name__ == "__main__":
    # notify.py est optionnel en local (il vit dans publisher/) ; sur le runner il est présent.
    try:
        import notify
    except Exception:
        notify = None

    def _notify(msg):
        if notify:
            try:
                notify.send(msg)
            except Exception:
                pass

    try:
        produced = main()
    except SystemExit as exc:
        # run()/make_*() font sys.exit("[AUTOPROD] ..."). exc.code = ce message (échec).
        if exc.code not in (None, 0):
            _notify(f"⚠️ KONGRAVE autoprod — ÉCHEC : {exc.code}")
        raise
    except Exception as exc:
        _notify(f"⚠️ KONGRAVE autoprod — EXCEPTION : {type(exc).__name__}: {exc}")
        raise
    else:
        if produced:
            _notify(f"✅ KONGRAVE autoprod — ep{produced:02d} produit et planifié.")
