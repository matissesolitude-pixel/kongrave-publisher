#!/usr/bin/env python3
"""
autoprod_ligne.py — BOUCLE DE FABRICATION AUTONOME LIGNE.

Pour chaque épisode `Lx.json` de `episodes/` NON encore fabriqué (absent de
publisher/ligne/queue|published), le plus ancien d'abord, sans intervention :

  1. FABRIQUE depuis le JSON (voix + anim via build_ligne.py, moteur lX.html).
  2. AUTO-SCAN (fail-loud de build_ligne : progression 80% + jamais d'écran vide ;
     les safe-zones/débordements sont empêchés structurellement par le clamp
     `putCap` du moteur — la détection FINE de chevauchement reste l'œil du PO).
  3. SCAN OK  -> monte la vidéo -> transcode 25fps (recette Meta) -> dépose dans
     ligne/queue/L0x/ (+ caption.txt extrait du champ `caption` du JSON) ->
     notif Telegram "🟢 L0x fabriqué, à valider" + le mp4.
  4. SCAN KO  -> N'ALIMENTE PAS LA FILE -> notif "🔴 L0x à revoir" + frames DoD.

Boucle tant qu'il reste des JSON non fabriqués. La PUBLICATION (cadence 6/j =
config.json cadence_hours=4, FIFO, garde-fou file vide fail-loud) reste le job
séparé de publish_ligne.py / du cron E6.

Usage : python3 autoprod_ligne.py            (fabrique tout le pending)
        python3 autoprod_ligne.py --one       (un seul, le plus ancien)
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

LIGNE = Path(__file__).resolve().parent
ROOT = LIGNE.parent
EPISODES = LIGNE / "episodes"
RENDER = LIGNE / "render"
OUTDIR = ROOT / "output" / "pilotes"
# Chemins file/notify configurables par env : local = ROOT/publisher/ligne/... ;
# cloud (repo kongrave-publisher) = ROOT/ligne/... (via LIGNE_QUEUE etc. dans le workflow).
QUEUE = Path(os.environ.get("LIGNE_QUEUE", str(ROOT / "publisher" / "ligne" / "queue")))
PUBLISHED = Path(os.environ.get("LIGNE_PUBLISHED", str(ROOT / "publisher" / "ligne" / "published")))

# ANTI-BLOCAGE DE FABRICATION (symétrique du skip-to-next de publish_ligne.py).
# L'auto-scan (build_ligne.scan_progression) est un FAIL-LOUD DÉTERMINISTE : un moteur qui
# laisse un temps mort / écran vide échouera à CHAQUE run. Or l'autoprod tourne en `--one`
# et prend TOUJOURS le plus petit numéro non produit — sans garde-fou, un seul épisode fautif
# (ex. L45) gèle la fabrication pour de bon : la file ne se remplit plus, plus rien ne poste.
# Règle : au refus de l'auto-scan, on QUARANTAINE l'épisode (autoprod_hold.json) et la
# fabrication passe au suivant. La quarantaine est indexée sur le HASH du moteur : dès que le
# moteur est recodé (hash différent), l'épisode ressort automatiquement de quarantaine et
# est re-fabriqué. Aucune intervention pour le débloquer une fois le moteur corrigé.
SCAN_HOLD_PATH = LIGNE / "autoprod_hold.json"    # {eid: hash-moteur-qui-a-raté-le-scan}

sys.path.insert(0, os.environ.get("LIGNE_NOTIFY_DIR", str(ROOT / "publisher")))
try:
    import notify  # bot saga réutilisé (send / send_video / send_photo)
except Exception as exc:  # pragma: no cover
    notify = None
    print(f"[autoprod] notify indisponible ({exc}) — notifs en console seulement.", file=sys.stderr)

EP_RE = re.compile(r"^L(\d+)$")  # L5, L6, … ; jamais _L5S1, L3S3, DSLTEST, PROOF…


def folder_name(eid: str) -> str:
    return f"L{int(eid[1:]):02d}"


def is_ready_episode(p: Path) -> bool:
    m = EP_RE.match(p.stem)
    if not m or int(m.group(1)) < 4:  # L1-L3 = legacy (déjà publiés) ; L4+ = moteur custom
        return False
    try:
        d = json.loads(p.read_text())
    except Exception:
        return False
    eng = d.get("engine")
    if not eng:
        return False
    # « prêt » exige que le FICHIER moteur existe (sinon build tomberait sur index.html -> blanc).
    # Un moteur en cours = renommer lXX.html -> lXX.html.wip pour que l'autoprod l'ignore proprement.
    return (LIGNE / "engine" / f"{eng}.html").exists()


def already_made(eid: str) -> bool:
    n = folder_name(eid)
    return (QUEUE / n).exists() or (PUBLISHED / n).exists()


def _engine_path(eid: str) -> Path | None:
    """Fichier moteur d'un épisode (champ `engine` de son JSON), ou None si introuvable."""
    jp = EPISODES / f"{eid}.json"
    if not jp.is_file():
        return None
    try:
        eng = (json.loads(jp.read_text()) or {}).get("engine")
    except Exception:
        return None
    if not eng:
        return None
    p = LIGNE / "engine" / f"{eng}.html"
    return p if p.is_file() else None


def _engine_hash(eid: str) -> str | None:
    """SHA1 du moteur — sert de clé de quarantaine : un moteur recodé (hash ≠) sort de hold."""
    p = _engine_path(eid)
    if p is None:
        return None
    return hashlib.sha1(p.read_bytes()).hexdigest()


def _load_hold() -> dict:
    if not SCAN_HOLD_PATH.is_file():
        return {}
    try:
        data = json.loads(SCAN_HOLD_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def _save_hold(hold: dict) -> None:
    tmp = SCAN_HOLD_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(hold, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(SCAN_HOLD_PATH)  # écriture atomique


def _quarantine(eid: str) -> None:
    """Écarte un épisode qui a raté l'auto-scan (clé = hash du moteur fautif)."""
    h = _engine_hash(eid)
    if h is None:
        return  # sans moteur identifiable, is_ready_episode l'exclut déjà
    hold = _load_hold()
    hold[eid] = h
    _save_hold(hold)


def _is_held(eid: str) -> bool:
    """En quarantaine tant que le moteur n'a PAS changé depuis l'échec du scan.
    Moteur recodé (hash différent) -> auto-libération : on nettoie l'entrée et on re-fabrique."""
    hold = _load_hold()
    if eid not in hold:
        return False
    if _engine_hash(eid) != hold[eid]:
        hold.pop(eid, None)
        _save_hold(hold)
        return False
    return True


def pending() -> list[Path]:
    eps = [p for p in EPISODES.glob("L*.json")
           if is_ready_episode(p) and not already_made(p.stem) and not _is_held(p.stem)]
    return sorted(eps, key=lambda p: int(p.stem[1:]))


# GARDE-FOU DE PROFONDEUR DE FILE (économie de minutes Actions). La fabrication rend une vidéo
# (Chromium, ~18 min/run) : c'est le gros poste de conso. Inutile de rendre en avance quand la
# file a déjà de quoi tenir plusieurs créneaux de publication. Tant que la file contient au moins
# QUEUE_TARGET_DEPTH épisodes, l'autoprod SORT sans rien fabriquer (court-circuit <1 min). Elle ne
# reprend que lorsque la publication a fait descendre la file sous le seuil. Réglable par env.
QUEUE_TARGET_DEPTH = max(1, int(os.environ.get("LIGNE_QUEUE_TARGET", "3")))


def queue_depth() -> int:
    """Nombre d'épisodes déjà en file d'attente de publication (dossiers LXX de queue/)."""
    if not QUEUE.is_dir():
        return 0
    return sum(1 for p in QUEUE.iterdir()
               if p.is_dir() and EP_RE.match(p.name))


def buffer_full() -> bool:
    """True si la file a déjà QUEUE_TARGET_DEPTH épisodes d'avance : on ne fabrique pas ce run."""
    return queue_depth() >= QUEUE_TARGET_DEPTH


def notify_text(msg: str):
    print(f"[TELEGRAM] {msg}")
    if notify:
        try:
            notify.send(msg)
        except Exception as exc:
            print(f"[notify] {exc}", file=sys.stderr)


def notify_video(msg: str, path: Path):
    n = path.parent.name  # ex : L10
    # CLOUD (workflow autoprod-ligne) : le mp4 est déjà sur le runner + secrets Telegram en env →
    # notif directe ; le commit/push de la file est fait par le workflow (résilient). Pas de git ici.
    if os.environ.get("LIGNE_AUTOPROD_NOPUSH"):
        print(f"[TELEGRAM] {n} — {msg.splitlines()[0]}")
        if notify:
            try:
                if hasattr(notify, "send_video"):
                    rm = notify.block_button(n) if hasattr(notify, "block_button") else None
                    notify.send_video(msg, path, reply_markup=rm)
                else:
                    notify.send(msg)
            except Exception as exc:
                print(f"[notify] {exc}", file=sys.stderr)
        return
    # LOCAL : le token Telegram n'est pas là → notif via CI : commit+push la file, déclenche notify-episode.
    pub = str(ROOT / "publisher")
    print(f"[TELEGRAM via CI] {n} — {msg.splitlines()[0]}")
    try:
        subprocess.run(["git", "add", f"ligne/queue/{n}"], cwd=pub, check=True)
        subprocess.run(["git", "commit", "-q", "-m", f"ligne: {n} en file (auto) + notif Telegram"], cwd=pub, check=True)
        subprocess.run(["git", "push", "origin", "HEAD"], cwd=pub, check=True)
        subprocess.run(["gh", "workflow", "run", "notify-episode.yml", "-f", f"folder={n}"], cwd=pub, check=True)
        print(f"[{n}] poussé + notif Telegram (CI) déclenchée")
    except subprocess.CalledProcessError as exc:
        print(f"[notify-ci] échec ({exc}) — {n} est en file mais non notifié.", file=sys.stderr)


def notify_frames(msg: str, frames: list[Path]):
    # Matisse (26/07) : PLUS D'IMAGES sur Telegram, ça ne sert à rien. Texte seulement.
    # On garde la signature (les frames restent sur le runner) mais on ne les envoie plus.
    print(f"[TELEGRAM] {msg} (frames non envoyées : {[f.name for f in frames]})")
    if notify:
        try:
            notify.send(msg)
        except Exception as exc:
            print(f"[notify] {exc}", file=sys.stderr)


def _run(args, screenshot=False) -> int:
    env = dict(os.environ)
    if screenshot:
        env["PRODUCER_FORCE_SCREENSHOT"] = "true"
    return subprocess.run(["python3", "build_ligne.py", *args], cwd=str(LIGNE), env=env).returncode


def _dur(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)]
    )
    return float(out.strip())


def extract_frames(anim: Path, n: int = 5) -> list[Path]:
    outdir = anim.parent / "_dod"
    outdir.mkdir(parents=True, exist_ok=True)
    dur = _dur(anim)
    frames = []
    for i in range(n):
        t = dur * (i + 0.5) / n
        pth = outdir / f"scan_{i}.png"
        subprocess.run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(anim), "-vframes", "1", str(pth)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        frames.append(pth)
    return frames


def transcode_25(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-r", "25", "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-x264opts", "nal-hrd=cbr:force-cfr=1", "-b:v", "6M", "-minrate", "6M", "-maxrate", "6M", "-bufsize", "6M",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(dst)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def make_one(jp: Path) -> bool:
    eid = jp.stem
    n = folder_name(eid)
    d = json.loads(jp.read_text())
    title = d.get("title", eid)
    print(f"\n===== FABRICATION {eid} — {title} =====")

    if _run([eid, "voice"]) != 0:
        notify_text(f"⚠️ {n} : échec génération voix. À revoir.")
        return False

    anim_rc = _run([eid, "anim"], screenshot=True)   # le SCAN est ici (fail-loud)
    anim = RENDER / eid / "anim.mp4"
    if anim_rc != 0:
        # ANTI-BLOCAGE : l'auto-scan est déterministe -> on met l'épisode en quarantaine
        # (indexée sur le hash du moteur) pour que la fabrication passe AU SUIVANT au lieu
        # de re-buter éternellement dessus. Recoder le moteur libère l'épisode automatiquement.
        _quarantine(eid)
        frames = extract_frames(anim) if anim.exists() else []
        notify_frames(f"🔴 {n} À REVOIR — l'auto-scan a bloqué (temps mort / écran vide). "
                      f"Écarté de la file ; la fabrication passe au suivant. "
                      f"Recode le moteur {eid.lower()}.html pour le remettre en jeu.", frames)
        print(f"[{eid}] SCAN KO → quarantaine (moteur inchangé) → au suivant.")
        return False

    if _run([eid, "build"]) != 0:
        notify_text(f"⚠️ {n} : échec montage vidéo. À revoir.")
        return False

    master = OUTDIR / f"{eid}.mp4"
    dst = QUEUE / n / f"{eid}.mp4"
    transcode_25(master, dst)

    wm = QUEUE.parent / "work" / eid / "voice_mode.txt"
    if wm.is_file():
        (QUEUE / n / "voice.txt").write_text(wm.read_text().strip(), encoding="utf-8")

    cap = (d.get("caption") or "").strip()
    if cap:
        (QUEUE / n / "caption.txt").write_text(cap, encoding="utf-8")
    else:
        print(f"[{eid}] ⚠️ pas de champ 'caption' dans le JSON — déposé SANS caption.txt.", file=sys.stderr)

    notify_video(f"🟢 {n} en file — se publiera au créneau (silence = OK).\n"
                 f"❌ bouton ou réponds « STOP {n} » pour le retirer.\n{title}", dst)
    print(f"[{eid}] → {dst}  (caption: {'oui' if cap else 'NON'})")
    return True


def main() -> int:
    # --check : compte le TRAVAIL RÉEL et sort (court-circuit CI, aucune install/notif nécessaire).
    # Buffer plein -> PENDING=0 : le workflow sort avant toute install (économie de minutes Actions),
    # exactement comme quand aucun JSON n'est prêt.
    if "--check" in sys.argv:
        if buffer_full():
            print(f"[autoprod] buffer plein ({queue_depth()} ≥ {QUEUE_TARGET_DEPTH}) — rien à fabriquer ce run.")
            print("PENDING=0")
        else:
            print(f"PENDING={len(pending())}")
        return 0
    one = "--one" in sys.argv

    # GARDE-FOU DE PROFONDEUR : la file a déjà de quoi tenir -> on ne rend rien (le gros poste
    # de conso Actions est le rendu vidéo). On reprend quand la publication l'aura fait descendre.
    if buffer_full():
        print(f"[autoprod] buffer plein ({queue_depth()} ≥ {QUEUE_TARGET_DEPTH}) — pas de fabrication ce run.")
        return 0

    eps = pending()
    if not eps:
        print("[autoprod] file de fabrication vide — aucun JSON non fabriqué.")
        notify_text("ℹ️ LIGNE autoprod : rien à fabriquer (tous les JSON prêts sont déjà en file).")
        return 0
    if one:
        eps = eps[:1]
    print(f"[autoprod] {len(eps)} à fabriquer : {[p.stem for p in eps]}")
    for jp in eps:
        make_one(jp)
    print("\n[autoprod] terminé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
