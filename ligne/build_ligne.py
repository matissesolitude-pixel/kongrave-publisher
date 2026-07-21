#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_ligne.py <id> — moteur LA LIGNE, piloté par un épisode JSON.

Un épisode = ligne/episodes/<id>.json :
  { "id":"L2", "voice":[seg1,...,segN], "scenes":[{"type":..., ...sync...}, ...] }

Étapes :
  voice   -> voix + timestamps mot-à-mot par segment (ElevenLabs) -> work/<id>/{durations,words}.json
  anim    -> timeline + injecte SPEC/WORDS/SCENES dans engine/index.html -> rend anim.mp4 (screenshot)
  build   -> assemble anim + voix + FILIGRANE (drift 5%) -> output/pilotes/<id>.mp4 + frames
  all     -> tout (défaut)

Voix LIGNE = George (premade UK), speed 1.12. Clé ElevenLabs dans .env.local (jamais imprimée).
"""
import json, os, subprocess, sys, base64
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
LIGNE = ROOT / "ligne"
ENGINE = LIGNE / "engine" / "index.html"
EPISODES = LIGNE / "episodes"
OUTDIR = ROOT / "output" / "pilotes"
FF = "ffmpeg"

load_dotenv(ROOT / ".env.local")
KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE = "JBFqnCBsd6RMkjVDRZzb"          # George (canon Ligne)
MODEL = "eleven_multilingual_v2"
FMT = "mp3_44100_128"
SETTINGS = {"stability": 0.50, "similarity_boost": 0.75, "style": 0.0, "speed": 1.12, "use_speaker_boost": True}
H = {"xi-api-key": KEY}

TAIL = 0.12                              # respiration de transition par scène (dernier segment un peu +)
WATERMARK = ROOT / "assets" / "watermark_dark.png"
WM_Y, WM_OPACITY = 1545, 0.05           # décision PO : 5% + dérive (anti-crop)


def run(cmd, tag=""):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"[ERREUR {tag}] {' '.join(str(c) for c in cmd[:6])}…\n{r.stderr[-800:]}")
    return r


def dur_of(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nk=1:nw=1", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())


def tts_timed(text):
    r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps",
                      headers={**H, "Content-Type": "application/json"}, params={"output_format": FMT},
                      json={"text": text, "model_id": MODEL, "voice_settings": SETTINGS}, timeout=180)
    if r.status_code != 200:
        sys.exit(f"[ERREUR TTS] HTTP {r.status_code} : {r.text[:200]}")
    d = r.json()
    al = d.get("alignment") or d.get("normalized_alignment") or {}
    chars, st, en = al.get("characters", []), al.get("character_start_times_seconds", []), al.get("character_end_times_seconds", [])
    words, cur, cs, ce = [], "", None, None
    for i, c in enumerate(chars):
        if c.isspace():
            if cur:
                words.append({"w": cur, "s": round(cs, 3), "e": round(ce, 3)}); cur = ""
        else:
            if not cur:
                cs = st[i]
            cur += c; ce = en[i]
    if cur:
        words.append({"w": cur, "s": round(cs, 3), "e": round(ce, 3)})
    return base64.b64decode(d["audio_base64"]), words


def load_episode(eid):
    p = EPISODES / f"{eid}.json"
    if not p.exists():
        sys.exit(f"[ERREUR] épisode introuvable : {p}")
    ep = json.loads(p.read_text())
    n = len(ep["scenes"])
    if len(ep["voice"]) != n:
        sys.exit(f"[ERREUR] {eid}: {len(ep['voice'])} segments voix pour {n} scènes (doit être égal)")
    return ep


def gen_voice(eid, ep, work):
    if not KEY:
        sys.exit("[ERREUR] ELEVENLABS_API_KEY absente de .env.local")
    durs, allwords = [], []
    for i, txt in enumerate(ep["voice"], 1):
        mp3, words = tts_timed(txt)
        (work / f"v{i}.mp3").write_bytes(mp3)
        durs.append(dur_of(work / f"v{i}.mp3")); allwords.append(words)
        print(f"  S{i} {durs[-1]:.2f}s ({len(words)} mots)")
    (work / "durations.json").write_text(json.dumps(durs, indent=2))
    (work / "words.json").write_text(json.dumps(allwords, indent=2))
    print(f"[voice] {eid} total = {sum(durs):.1f}s")
    return durs


def timeline(durs, total=None):
    sc, t = [], 0.0
    for i, d in enumerate(durs):
        tail = TAIL if i < len(durs) - 1 else TAIL + 0.35
        dd = d + tail
        sc.append({"s": round(t, 3), "d": round(dd, 3), "v": round(d, 3)}); t += dd
    if total and total > t:                       # scène avec longs silences (ex. S4) : on étend la fin
        pad = total - t
        if pad > 6.0:                             # >6s d'écart = surestimation de l'auteur -> IGNORÉ (règle durée=voix)
            print(f"[timeline] total={total:.1f}s dépasse la voix de {pad:.1f}s (>6s) — IGNORÉ, durée=voix ({t:.1f}s).")
        else:
            sc[-1]["d"] = round(sc[-1]["d"] + pad, 3); t = total
    return {"sc": sc, "total": round(t, 3)}


def build_anim(ep, tl, work, rend):
    words = json.loads((work / "words.json").read_text())
    # index.html = engine VALIDÉ (L1/L2, figés). pivot.html = engine PIVOT/DSL (shapes+verbs+interpréteur).
    if ep.get("engine") == "pivot-dsl":
        engine = LIGNE / "engine" / "pivot.html"
    elif ep.get("engine") == "proof":
        engine = LIGNE / "engine" / "proof.html"
    elif ep.get("engine") == "proofq":
        engine = LIGNE / "engine" / "proofq.html"
    elif ep.get("engine") == "l3open":
        engine = LIGNE / "engine" / "l3open.html"
    elif ep.get("engine") == "hand-craft":
        engine = LIGNE / "engine" / "l3.html"
    elif ep.get("engine") == "l3s3":
        engine = LIGNE / "engine" / "l3s3.html"
    elif ep.get("engine") == "l3s4":
        engine = LIGNE / "engine" / "l3s4.html"
    elif ep.get("engine") == "l3s5":
        engine = LIGNE / "engine" / "l3s5.html"
    elif ep.get("engine") == "l3chute":
        engine = LIGNE / "engine" / "l3chute.html"
    elif ep.get("engine") == "l4":
        engine = LIGNE / "engine" / "l4.html"
    elif ep.get("engine") == "l5":
        engine = LIGNE / "engine" / "l5.html"
    elif ep.get("engine") == "l6":
        engine = LIGNE / "engine" / "l6.html"
    elif ep.get("engine") == "l8":
        engine = LIGNE / "engine" / "l8.html"
    elif ep.get("engine") == "l9":
        engine = LIGNE / "engine" / "l9.html"
    elif ep.get("engine") == "l10":
        engine = LIGNE / "engine" / "l10.html"
    elif ep.get("engine") == "l11":
        engine = LIGNE / "engine" / "l11.html"
    elif ep.get("engine") == "l12":
        engine = LIGNE / "engine" / "l12.html"
    elif ep.get("engine") == "l13":
        engine = LIGNE / "engine" / "l13.html"
    elif ep.get("engine") == "l14":
        engine = LIGNE / "engine" / "l14.html"
    elif ep.get("engine") == "l15":
        engine = LIGNE / "engine" / "l15.html"
    elif ep.get("engine") == "l16":
        engine = LIGNE / "engine" / "l16.html"
    elif ep.get("engine") == "l17":
        engine = LIGNE / "engine" / "l17.html"
    elif ep.get("engine") == "l18":
        engine = LIGNE / "engine" / "l18.html"
    elif ep.get("engine") == "l7":
        engine = LIGNE / "engine" / "l7.html"
    elif ep["id"] == "TESTPIVOT":
        engine = LIGNE / "engine" / "index_pivot.html"
    elif ep.get("engine") and (LIGNE / "engine" / f"{ep['engine']}.html").exists():
        # Générique : tout moteur "lNN" dont le fichier existe (l19+ et futurs) — évite d'étendre la chaîne à la main.
        engine = LIGNE / "engine" / f"{ep['engine']}.html"
    else:
        engine = ENGINE
    html = engine.read_text()
    # INCLUDE : inline les librairies verbs.js / shapes.js (évite tout <script src> sous Puppeteer)
    for lib in ("verbs.js", "shapes.js"):
        marker = f"/*INCLUDE:{lib}*/"
        if marker in html:
            html = html.replace(marker, (LIGNE / "engine" / lib).read_text())
    html = (html
            .replace("__SCENES__", json.dumps(tl["sc"]))
            .replace("__WORDS__", json.dumps(words))
            .replace("__SPEC__", json.dumps(ep["scenes"]))
            .replace("__TOTAL__", f'{tl["total"]:.3f}'))
    proj = rend / "proj"; proj.mkdir(parents=True, exist_ok=True)
    (proj / "index.html").write_text(html)
    out = rend / "anim.mp4"
    env = dict(os.environ, PRODUCER_FORCE_SCREENSHOT="true")
    print("[anim] rendu HyperFrames…")
    subprocess.run(["npx", "--yes", "hyperframes", "render", str(proj), "-o", str(out),
                    "--resolution", "portrait", "-f", "30"], cwd=str(proj), env=env, capture_output=True, text=True)
    if not out.exists():
        sys.exit("[ERREUR anim] pas de sortie")
    print(f"[anim] OK ({dur_of(out):.2f}s)")
    return out


def scan_progression(anim, tl, rend):
    """FAIL-LOUD : scanne les fenêtres de voix. L'oscillation étant BANNIE, tout mouvement = progression.
    Une fenêtre de voix >0,8s où rien ne progresse -> le build ÉCHOUE avec la liste (doctrine = test)."""
    import numpy as np
    from PIL import Image
    tmp = rend / "_scan"; tmp.mkdir(exist_ok=True)
    subprocess.run([FF, "-y", "-v", "error", "-i", str(anim), "-vf", "fps=15,scale=432:768,format=gray",
                    str(tmp / "f%04d.png")], check=True)
    fs = sorted(tmp.glob("f*.png"))
    arr = [np.asarray(Image.open(f), dtype=np.int16) for f in fs]
    diffs = [(i / 15.0, (np.abs(arr[i] - arr[i - 1]) > 16).mean()) for i in range(1, len(arr))]
    ink = [(i / 15.0, (np.abs(arr[i] - 238) > 24).mean()) for i in range(len(arr))]   # fraction d'encre par frame
    voice = [(s["s"], s["s"] + s["v"]) for s in tl["sc"]]
    def in_voice(t): return any(a <= t <= b for a, b in voice)
    THR = 0.00015
    MAXPAUSE = 1.5      # pause intentionnelle ≤1,5s tolérée ; au-delà = échec
    BLANK = 0.004       # <0,4% d'encre = écran quasi-vide (line-art sparse)
    dead, run = [], None
    for t, d in diffs:
        if in_voice(t) and d < THR:
            run = [t, t] if run is None else [run[0], t]
        else:
            if run and run[1] - run[0] > MAXPAUSE:
                dead.append(("gel", tuple(run)))
            run = None
    if run and run[1] - run[0] > MAXPAUSE:
        dead.append(("gel", tuple(run)))
    # écrans quasi-vides pendant la voix (règle continuité : jamais de vide entre scènes)
    brun = None
    for t, k in ink:
        if in_voice(t) and k < BLANK:
            brun = [t, t] if brun is None else [brun[0], t]
        else:
            if brun and brun[1] - brun[0] > 0.4:
                dead.append(("vide", tuple(brun)))
            brun = None
    if brun and brun[1] - brun[0] > 0.4:
        dead.append(("vide", tuple(brun)))
    for f in fs:
        f.unlink()
    tmp.rmdir()
    if dead:
        dead.sort(key=lambda x: x[1][0])
        print("\n" + "=" * 60 + "\n[FAIL-LOUD] le build ÉCHOUE (doctrine = test) :")
        for kind, (a, b) in dead:
            sc = next((k + 1 for k in range(len(tl["sc"])) if voice[k][0] <= a <= voice[k][1]), "?")
            tag = "SANS PROGRESSION" if kind == "gel" else "ÉCRAN QUASI-VIDE"
            print(f"   S{sc}  {a:.1f}s -> {b:.1f}s  ({b - a:.1f}s) — {tag}")
        print("Corrige : un élément AVANCE, ou la scène N+1 se construit avant la fin de N (jamais de vide).\n" + "=" * 60)
        sys.exit(1)
    print("[scan] progression continue + jamais d'écran vide ✓")


def build_audio(tl, work):
    inp, labels, k = [], [], 0
    for i in range(len(tl["sc"])):
        inp += ["-i", str(work / f"v{i+1}.mp3")]; labels.append(f"[{k}:a]"); k += 1
        tail = tl["sc"][i]["d"] - tl["sc"][i]["v"]
        inp += ["-f", "lavfi", "-t", f"{tail:.3f}", "-i", "anullsrc=r=44100:cl=mono"]; labels.append(f"[{k}:a]"); k += 1
    fc = "".join(labels) + f"concat=n={len(labels)}:v=0:a=1[a]"
    out = work / "voice_track.mp3"
    run([FF, "-y", "-v", "error", *inp, "-filter_complex", fc, "-map", "[a]", "-c:a", "libmp3lame", "-q:a", "2", str(out)], "audio")
    return out


def assemble(eid, tl, anim, audio):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / f"{eid}.mp4"
    fc = (f"[2:v]format=rgba,colorchannelmixer=aa={WM_OPACITY}[wm];"
          f"[0:v][wm]overlay=(W-w)/2+40*sin(2*PI*t/24):{WM_Y}-h/2+22*sin(2*PI*t/18):format=auto,format=yuv420p[v]")
    run([FF, "-y", "-v", "error", "-i", str(anim), "-i", str(audio), "-i", str(WATERMARK),
         "-filter_complex", fc, "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-crf", "18",
         "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(out)], "assemble")
    print(f"[build] -> {out} ({dur_of(out):.2f}s) [filigrane drift {int(WM_OPACITY*100)}%]")
    return out


def main():
    eid = sys.argv[1] if len(sys.argv) > 1 else "L1"
    stage = sys.argv[2] if len(sys.argv) > 2 else "all"
    ep = load_episode(eid)
    work = LIGNE / "work" / eid; work.mkdir(parents=True, exist_ok=True)
    rend = LIGNE / "render" / eid; rend.mkdir(parents=True, exist_ok=True)
    if stage in ("voice", "all"):
        gen_voice(eid, ep, work)
    durs = json.loads((work / "durations.json").read_text())
    tl = timeline(durs, ep.get("total")); (work / "timeline.json").write_text(json.dumps(tl, indent=2))
    print(f"[timeline] total = {tl['total']:.2f}s")
    if stage in ("anim", "all"):
        anim = build_anim(ep, tl, work, rend)
        scan_progression(anim, tl, rend)   # fail-loud : trou >0,8s sans progression -> build échoue
    if stage in ("build", "all"):
        assemble(eid, tl, rend / "anim.mp4", build_audio(tl, work))
    print("[done]")


if __name__ == "__main__":
    main()
