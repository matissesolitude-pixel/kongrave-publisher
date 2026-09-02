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
VOICE = "0jNVx6MiRPvEBiq9DBhH"          # LIGNE — Coach (A2), Voice Design, retenue par le PO le 25/08
# ancienne voix canon (L01 -> L95) : George "JBFqnCBsd6RMkjVDRZzb"
MODEL = "eleven_multilingual_v2"
FMT = "mp3_44100_128"
# Réglages par DÉFAUT (décision PO du 25/08 : on revient au posé après mesure).
SETTINGS = {"stability": 0.50, "similarity_boost": 0.75, "style": 0.0, "speed": 1.12, "use_speaker_boost": True}
# Variante agressive, réservée aux épisodes de TEST : un JSON qui porte "_voice": "agressif"
# est fabriqué avec ces réglages-là. Coût mesuré sur L91 : 40,2 s contre 34,3 s, soit +6,0 s.
SETTINGS_AGRESSIF = {"stability": 0.25, "similarity_boost": 0.80, "style": 0.50, "speed": 1.12, "use_speaker_boost": True}
# Garde-fou de durée : si la voix dépasse ce seuil, l'épisode est refait avec les réglages par
# défaut. Le format court (rétention 30 % sous 40 s contre 19 % au-dessus de 60 s) prime sur le style.
DUREE_MAX_TEST = 36.0
H = {"xi-api-key": KEY}

TAIL = 0.12                              # respiration de transition par scène (dernier segment un peu +)
PAD_MAX = 1.0                            # rallonge de fin maximale (voir timeline) — au-delà, c'est un vide
QUEUE_MAX = 2.0                          # silence toléré après le dernier mot ; au-delà = échec du scan
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


def tts_timed(text, settings=None):
    r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps",
                      headers={**H, "Content-Type": "application/json"}, params={"output_format": FMT},
                      json={"text": text, "model_id": MODEL, "voice_settings": settings or SETTINGS}, timeout=180)
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
    # TEST A/B décidé par le PO le 25/08 : un épisode sur deux en agressif, un sur deux en posé,
    # pendant une semaine, puis on tranche sur les statistiques. Chaque épisode fabriqué emporte
    # son marqueur `voice.txt` jusque dans `published/`, ce qui rend le dépouillement possible.
    # Un JSON qui porte explicitement "_voice" garde le dernier mot.
    forced = ep.get("_voice")
    if forced in ("agressif", "pose", "posé"):
        test = forced == "agressif"
    else:
        # On alterne sur le RANG de fabrication, pas sur le numéro d'épisode : un trou dans la
        # numérotation (L95 est resté en voix George) casserait la parité et donnerait deux
        # épisodes de suite dans le même réglage. Le rang se recompte depuis les marqueurs déjà
        # déposés — file et publiés confondus — donc aucun fichier d'état à maintenir.
        deja = sum(1 for d in (LIGNE / "queue", LIGNE / "published") if d.is_dir()
                   for f in d.glob("*/voice.txt"))
        test = deja % 2 == 0
    settings = SETTINGS_AGRESSIF if test else SETTINGS
    mode = "agressif" if test else "pose"

    def passe(st, etiquette):
        durs, allwords = [], []
        for i, txt in enumerate(ep["voice"], 1):
            mp3, words = tts_timed(txt, st)
            (work / f"v{i}.mp3").write_bytes(mp3)
            durs.append(dur_of(work / f"v{i}.mp3")); allwords.append(words)
            print(f"  S{i} {durs[-1]:.2f}s ({len(words)} mots) [{etiquette}]")
        return durs, allwords

    durs, allwords = passe(settings, "agressif" if test else "défaut")

    # Le repli ne se déclenche PAS sur un échec de publication — Meta refuse pour des raisons
    # d'encodage, jamais à cause d'un réglage de voix. Le seul signal pertinent est la DURÉE.
    if test and sum(durs) > DUREE_MAX_TEST:
        print(f"[voice] {eid} : test agressif à {sum(durs):.1f}s > {DUREE_MAX_TEST}s — "
              f"on refait la voix aux réglages par défaut.")
        durs, allwords = passe(SETTINGS, "repli défaut")
        mode = "pose_repli"

    # Trace d'attribution : sans elle, la semaine de test ne se dépouille pas.
    (work / "voice_mode.txt").write_text(mode, encoding="utf-8")

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
    # RALLONGE DE FIN — PLAFONNÉE. Le champ `total` du JSON est une ESTIMATION de
    # l'auteur, calculée sur un budget de caractères ; la voix réelle est presque
    # toujours plus courte. Avant le 02/09/2026, tout l'écart (jusqu'à 6s) était
    # collé à la dernière scène : L99 est parti avec 4,5s de silence en fin, soit
    # 17% de l'épisode, et le scan ne l'a pas vu — il ne mesure le mouvement que
    # PENDANT les fenêtres de voix. On garde la rallonge, qui sert aux scènes à
    # silence voulu, mais on la borne à PAD_MAX : de quoi laisser le CTA de S5
    # s'afficher, pas de quoi créer un vide.
    if total and total > t:
        pad = total - t
        if pad > PAD_MAX:
            print(f"[timeline] total={total:.1f}s dépasse la voix de {pad:.1f}s — "
                  f"rallonge PLAFONNÉE à {PAD_MAX:.1f}s (durée ≈ voix).")
            pad = PAD_MAX
        sc[-1]["d"] = round(sc[-1]["d"] + pad, 3); t += pad
    return {"sc": sc, "total": round(t, 3)}


def amp_curve(work, tl, fps=30):
    """Courbe d'AMPLITUDE de la voix (RMS par frame) -> SYNCHRO LABIALE de Mr Dollar.
    Bible : pas de lip-sync phonétique ; 2 à 4 formes de bouche pilotées par l'amplitude.
    Déterministe, tourne en cloud, zéro travail manuel par épisode. Les moteurs sans le
    marqueur __AMP__ ne sont pas affectés (substitution sans effet)."""
    import numpy as np
    N = int(tl["total"] * fps) + 2
    amp = [0.0] * N
    for i in range(len(tl["sc"])):
        f = work / f"v{i+1}.mp3"
        if not f.exists():
            continue
        raw = subprocess.run([FF, "-v", "error", "-i", str(f), "-f", "s16le",
                              "-ac", "1", "-ar", "8000", "-"], capture_output=True).stdout
        a = np.frombuffer(raw, dtype="<i2").astype("float32") / 32768.0
        if a.size == 0:
            continue
        win = max(1, int(8000 / fps))
        k0 = int(round(tl["sc"][i]["s"] * fps))
        for k in range(a.size // win):
            idx = k0 + k
            if 0 <= idx < N:
                amp[idx] = float(np.sqrt(float((a[k * win:(k + 1) * win] ** 2).mean())))
    m = max(amp) or 1.0
    return [round(min(1.0, v / m), 3) for v in amp]


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
    # INCLUDE:narrator — MR DOLLAR clé en main. Un moteur écrit UNE ligne et reçoit :
    # la bibliothèque narrateur, les poses vectorisées (defs SVG), leurs dimensions, la carte
    # des yeux (clignement) et l'objet MrD prêt à l'emploi, branché sur l'amplitude de la voix.
    # Évite d'inliner 300 Ko de SVG à la main dans chaque moteur (source d'erreurs).
    if "/*INCLUDE:narrator*/" in html:
        import re as _re
        A = LIGNE / "assets"
        # toutes les poses disponibles : ajouter un SVG dans assets/narrator suffit
        poses = sorted(f.stem for f in (A / "narrator").glob("*.svg"))
        defs, sizes = [], {}
        for name in poses:
            f = A / "narrator" / f"{name}.svg"
            if not f.is_file():
                continue
            svg = f.read_text()
            w = int(_re.search(r'width="(\d+)"', svg).group(1))
            h = int(_re.search(r'height="(\d+)"', svg).group(1))
            defs.append(f'<g id="np_{name}">' + "".join(_re.findall(r"<path[^>]*/>", svg)) + "</g>")
            sizes[name] = {"w": w, "h": h}
        eyes_all = json.loads((A / "narrator" / "eyes.json").read_text()) if (A / "narrator" / "eyes.json").is_file() else {}
        eyes = {k: v for k, v in eyes_all.items() if k in sizes and v}
        block = (A / "narrator.js").read_text().rstrip() + "\n" + \
            "const NPOSE=" + json.dumps(sizes) + ";\n" + \
            "const NEYES=" + json.dumps(eyes, ensure_ascii=False) + ";\n" + \
            "(function(){var d=document.createElementNS('http://www.w3.org/2000/svg','defs');" + \
            "d.innerHTML=" + json.dumps("".join(defs)) + ";SVG.appendChild(d);})();\n" + \
            "const MrD=MrDollar.init({svg:SVG,poses:NPOSE,defaultPose:'idle_soft'});\n" + \
            "MrD.setEyes(NEYES); MrD.setAmp(__AMP__,30);\n"
        html = html.replace("/*INCLUDE:narrator*/", block)
    html = (html
            .replace("__SCENES__", json.dumps(tl["sc"]))
            .replace("__WORDS__", json.dumps(words))
            .replace("__SPEC__", json.dumps(ep["scenes"]))
            .replace("__TOTAL__", f'{tl["total"]:.3f}')
            .replace("__AMP__", json.dumps(amp_curve(work, tl))))
    proj = rend / "proj"; proj.mkdir(parents=True, exist_ok=True)
    (proj / "index.html").write_text(html)
    out = rend / "anim.mp4"
    env = dict(os.environ, PRODUCER_FORCE_SCREENSHOT="true")
    print("[anim] rendu HyperFrames…")
    # version ÉPINGLÉE (0.7.37 = celle prouvée en cloud par KONGRAVE) ; args Chromium sûrs en CI/root.
    hf_ver = os.environ.get("HYPERFRAMES_VERSION", "0.7.37")
    r = subprocess.run(["npx", "--yes", f"hyperframes@{hf_ver}", "render", str(proj), "-o", str(out),
                        "--resolution", "portrait", "-f", "30"], cwd=str(proj), env=env, capture_output=True, text=True)
    if not out.exists():
        sys.exit(f"[ERREUR anim] pas de sortie (hyperframes@{hf_ver}, code {r.returncode})\n"
                 f"--- stdout ---\n{(r.stdout or '')[-2500:]}\n--- stderr ---\n{(r.stderr or '')[-2500:]}")
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
    # QUEUE MUETTE — le dernier mot ne doit pas tomber loin de la fin. Le scan ci-dessus
    # ne mesure QUE pendant les fenêtres de voix : tout ce qui suit le dernier mot était
    # hors de son champ, et L99 est parti avec 4,5s de vide sans que rien ne proteste.
    # La rallonge est désormais plafonnée en amont ; ce contrôle attrape les autres causes
    # (un segment de voix vide, une durée forcée à la main).
    fin_voix = max(b for a, b in voice)
    queue = tl["total"] - fin_voix
    if queue > QUEUE_MAX:
        dead.append(("queue muette", (round(fin_voix, 2), round(tl["total"], 2))))

    for f in fs:
        f.unlink()
    tmp.rmdir()
    if dead:
        dead.sort(key=lambda x: x[1][0])
        print("\n" + "=" * 60 + "\n[FAIL-LOUD] le build ÉCHOUE (doctrine = test) :")
        for kind, (a, b) in dead:
            sc = next((k + 1 for k in range(len(tl["sc"])) if voice[k][0] <= a <= voice[k][1]), "?")
            tag = {"gel": "SANS PROGRESSION",
                   "vide": "ÉCRAN QUASI-VIDE",
                   "queue muette": "SILENCE APRÈS LE DERNIER MOT"}.get(kind, kind.upper())
            print(f"   S{sc}  {a:.1f}s -> {b:.1f}s  ({b - a:.1f}s) — {tag}")
        print("Corrige : un élément AVANCE, ou la scène N+1 se construit avant la fin de N (jamais de vide).")
        print("Silence après le dernier mot : la voix est plus courte que prévu — raccourcis `total`.\n" + "=" * 60)
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


# ── SFX « PAR TOUCHE » ───────────────────────────────────────────────────────
# Effets sonores MINIMAUX, synthétisés (aucune banque externe, déterministe).
# Des ACCENTS sur les temps-clés, sous la voix — jamais un tapis. Déclarés dans le
# JSON de l'épisode : "sfx": [{"sc": 4, "t": 1.0, "s": "tick"}, ...]
#   sc = numéro de scène (1-based), t = décalage EN SECONDES depuis le début de la
#   scène (donc robuste aux variations de durée de la voix), s = nom du son.
# Absence de "sfx" -> rien ne change (audio = voix seule).
SFX_DEFS = {
    # nom      durée  source lavfi                    mise en forme                                              vol
    "tick":    (0.06, "sine=f=1800:d=0.06",           "afade=t=out:st=0.015:d=0.045",                            0.13),
    "tickhi":  (0.06, "sine=f=2300:d=0.06",           "afade=t=out:st=0.015:d=0.045",                            0.13),
    "pop":     (0.10, "sine=f=640:d=0.10",            "afade=t=out:st=0.02:d=0.08",                              0.15),
    "thunk":   (0.22, "sine=f=92:d=0.22",             "afade=t=out:st=0.03:d=0.19",                              0.24),
    "whoosh":  (0.30, "anoisesrc=d=0.30:c=pink",      "highpass=f=500,afade=t=in:d=0.12,afade=t=out:st=0.16:d=0.14", 0.11),
    "riser":   (0.50, "anoisesrc=d=0.50:c=pink",      "highpass=f=700,afade=t=in:d=0.45,volume=1.4",             0.10),
    "resolve": (0.80, "sine=f=294:d=0.80",            "afade=t=in:d=0.05,afade=t=out:st=0.25:d=0.55",            0.16),
}


def mix_sfx(audio, ep, tl, work):
    cues = ep.get("sfx") or []
    if not cues:
        return audio
    inp = ["-i", str(audio)]
    filters = ["[0:a]aformat=channel_layouts=mono[v0]"]
    mix = ["[v0]"]
    k = 1
    for c in cues:
        name = c.get("s")
        if name not in SFX_DEFS:
            continue
        sc = c.get("sc")
        off = float(c.get("t", 0))
        if sc is not None and 1 <= int(sc) <= len(tl["sc"]):
            t = tl["sc"][int(sc) - 1]["s"] + off      # relatif à la scène
        else:
            t = off                                    # temps absolu
        if t < 0 or t > tl["total"]:
            continue
        d, src, post, vol = SFX_DEFS[name]
        inp += ["-f", "lavfi", "-t", f"{d:.3f}", "-i", src]
        ms = int(round(t * 1000))
        filters.append(f"[{k}:a]{post},volume={vol},aformat=channel_layouts=mono,adelay={ms}[s{k}]")
        mix.append(f"[s{k}]")
        k += 1
    if len(mix) == 1:
        return audio
    filters.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:dropout_transition=0[out]")
    out = work / "audio_sfx.mp3"
    run([FF, "-y", "-v", "error", *inp, "-filter_complex", ";".join(filters),
         "-map", "[out]", "-c:a", "libmp3lame", "-q:a", "2", str(out)], "sfx")
    print(f"[sfx] {len(mix) - 1} touches mixées sous la voix")
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
        audio = mix_sfx(build_audio(tl, work), ep, tl, work)
        assemble(eid, tl, rend / "anim.mp4", audio)
    print("[done]")


if __name__ == "__main__":
    main()
