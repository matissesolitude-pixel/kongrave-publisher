#!/usr/bin/env python3
"""
publish_dct.py — Publisher du Reel quotidien DCT (War Room).

Modèle : une FILE, pas un planning, comme pour LIGNE. Un Reel prêt = UN sous-dossier
de `dct/queue/` contenant UN `.mp4` et un `caption.txt`. Le seul geste : déposer ce
dossier, commit, push.

Le run prend la PLUS ANCIENNE date de la file et publie TOUS ses dossiers, l un après
l autre (M, 28/10 : un Reel par actif gagnant et au plus un perdant, donc plusieurs Reels
le même soir ; le nom `AAAA-MM-JJ-...` porte la date). Chaque dossier publié part en
`dct/published/` SANS le .mp4 : le master vit déjà dans le dossier du lot sur le Mac,
et le dépôt pèse déjà 3 Go à cause des masters LIGNE. On garde la trace, pas le poids.

Garde-fous :
  * FENÊTRE : ne publie qu'à PUBLISH_HOUR_PARIS heure de Paris. Le workflow tourne à
    18h15 ET 19h15 UTC pour couvrir été/hiver ; le script tranche sur l'heure de Paris.
  * CADENCE : refuse si le précédent Reel DCT date de moins de cadence_hours.
  * FIFO : plus ancien = nom de dossier trié en premier. Jamais mtime, qu'un
    `git checkout` réécrit sur le runner.
  * QUARANTAINE : après QUARANTINE_AFTER refus Meta cumulés, le dossier part en
    `dct/_hold/` pour que la file ne gèle pas.

Options :
  --dry-run   Crée le conteneur Meta mais NE PUBLIE PAS et NE DÉPLACE PAS.
  --force     Ignore la fenêtre horaire ET la cadence (publication manuelle).
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    PARIS = ZoneInfo("Europe/Paris")
except Exception:
    PARIS = timezone(timedelta(hours=1))

import notify
from publish_reel import PublishError, publish_episode

BASE_DIR = Path(__file__).resolve().parent
DCT_DIR = BASE_DIR / "dct"
QUEUE_DIR = DCT_DIR / "queue"
PUBLISHED_DIR = DCT_DIR / "published"
HOLD_DIR = DCT_DIR / "_hold"
CONFIG_PATH = DCT_DIR / "config.json"
LOG_PATH = DCT_DIR / "publish_log.json"
STATE_PATH = DCT_DIR / "publish_state.json"

PUBLISH_HOUR_PARIS = 20       # 20h15 Paris : le cron cadre, le script tranche
CADENCE_GRACE_H = 0.5
QUARANTINE_AFTER = 3


def _load(path: Path, default):
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise SystemExit(f"[dct] Impossible de lire {path} : {exc}")


def _save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _cfg() -> dict:
    c = _load(CONFIG_PATH, {})
    return c if isinstance(c, dict) else {}


def _log() -> list:
    d = _load(LOG_PATH, [])
    return d if isinstance(d, list) else []


def _dernier_succes() -> datetime | None:
    for e in reversed(_log()):
        if e.get("status") == "success":
            try:
                return datetime.fromisoformat(e["published_at"].replace("Z", "+00:00"))
            except (KeyError, ValueError):
                continue
    return None


def _fenetre_ouverte() -> bool:
    return datetime.now(PARIS).hour == PUBLISH_HOUR_PARIS


def _cadence_ok() -> tuple[bool, str]:
    h = float(_cfg().get("cadence_hours", 24))
    dernier = _dernier_succes()
    if dernier is None:
        return True, "aucune publication DCT antérieure"
    ecoule = (datetime.now(timezone.utc) - dernier).total_seconds() / 3600
    if ecoule + CADENCE_GRACE_H < h:
        return False, f"dernier Reel DCT il y a {ecoule:.1f} h, cadence {h:.0f} h"
    return True, f"dernier Reel DCT il y a {ecoule:.1f} h"


def _file() -> list[Path]:
    if not QUEUE_DIR.is_dir():
        return []
    return sorted(d for d in QUEUE_DIR.iterdir() if d.is_dir() and not d.name.startswith("."))


# Profil exactement conforme a ce que CE compte a deja accepte (masters LIGNE publies) :
# H.264 High 4.0, yuv420p, 30 i/s, GOP ferme, AAC LC 44,1 kHz MONO, moov en tete.
# Un master en 48 kHz stereo a ete refuse par Meta le 27/10 avec un ProcessingFailedError
# opaque ; on normalise donc TOUJOURS avant l envoi plutot que de deviner apres coup.
FFMPEG = [
    "ffmpeg", "-y", "-loglevel", "error", "-i", "{src}",
    "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
    "-r", "30", "-g", "60", "-keyint_min", "60", "-sc_threshold", "0",
    "-crf", "20", "-maxrate", "5M", "-bufsize", "10M",
    "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "1",
    "-movflags", "+faststart", "{dst}",
]


def _normalise(src: Path) -> Path:
    """Reencode vers le profil accepte. Si ffmpeg manque, on envoie le fichier tel quel
       plutot que de bloquer la file, et on le dit."""
    dst = Path(tempfile.gettempdir()) / f"dct_{src.stem}_meta.mp4"
    cmd = [a.format(src=str(src), dst=str(dst)) for a in FFMPEG]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except FileNotFoundError:
        print("[dct] ffmpeg absent — envoi du master sans normalisation.", file=sys.stderr)
        return src
    except subprocess.CalledProcessError as exc:
        print(f"[dct] normalisation impossible ({exc.stderr.decode()[:300]}) — "
              f"envoi du master tel quel.", file=sys.stderr)
        return src
    print(f"[dct] normalise : {dst.stat().st_size / 1e6:.1f} Mo (depuis "
          f"{src.stat().st_size / 1e6:.1f} Mo)")
    return dst


def _contenu(dossier: Path) -> tuple[Path, str]:
    mp4 = sorted(dossier.glob("*.mp4"))
    if len(mp4) != 1:
        raise PublishError(f"{dossier.name} : il faut exactement un .mp4, trouvé {len(mp4)}.")
    cap = dossier / "caption.txt"
    if not cap.is_file():
        raise PublishError(f"{dossier.name} : caption.txt manquant.")
    texte = cap.read_text(encoding="utf-8").strip()
    if not texte:
        raise PublishError(f"{dossier.name} : caption.txt vide.")
    return mp4[0], texte


def _archive(dossier: Path, media_id: str) -> None:
    """Déplace en published/ SANS le master : on garde la trace, pas les 13 Mo."""
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    cible = PUBLISHED_DIR / dossier.name
    if cible.exists():
        shutil.rmtree(cible)
    cible.mkdir(parents=True)
    shutil.copy2(dossier / "caption.txt", cible / "caption.txt")
    (cible / "media.json").write_text(
        json.dumps({"media_id": media_id,
                    "published_at": datetime.now(timezone.utc).isoformat()},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(dossier)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    if _cfg().get("paused") and not (a.force or a.dry_run):
        print("[dct] publication en pause (config.json) — rien à faire.")
        return 0

    if not a.force and not a.dry_run and not _fenetre_ouverte():
        print(f"[dct] hors fenêtre : il est {datetime.now(PARIS):%H:%M} à Paris, "
              f"la publication est à {PUBLISH_HOUR_PARIS}h. Rien à faire.")
        return 0

    if not a.force and not a.dry_run:
        ok, raison = _cadence_ok()
        if not ok:
            print(f"[dct] cadence non respectée : {raison}. Rien à faire.")
            return 0

    file = _file()
    if not file:
        msg = "File DCT VIDE à l'heure de publier. Aucun Reel n'est parti."
        print(f"[dct] {msg}", file=sys.stderr)
        notify.send(f"⚠️ {msg}")
        return 1

    etat = _load(STATE_PATH, {})
    etat = etat if isinstance(etat, dict) else {}
    lot = [d for d in file if d.name[:10] == file[0].name[:10]]
    print(f"[dct] lot du {file[0].name[:10]} : {len(lot)} Reel(s)")
    echecs = 0
    for n, dossier in enumerate(lot):
        if n:
            time.sleep(PAUSE_ENTRE_REELS_S)
        echecs += _publier(dossier, etat, a.dry_run)
    return 1 if echecs else 0


PAUSE_ENTRE_REELS_S = 60


def _publier(dossier: Path, etat: dict, dry_run: bool) -> int:
    try:
        mp4, caption = _contenu(dossier)
    except PublishError as exc:
        print(f"[dct] {exc}", file=sys.stderr)
        notify.send(f"⚠️ Reel DCT malformé : {exc}")
        return 1

    print(f"[dct] publication de {dossier.name} ({mp4.name}, "
          f"{mp4.stat().st_size / 1e6:.1f} Mo){' [DRY-RUN]' if dry_run else ''}")

    try:
        res = publish_episode(_normalise(mp4), caption, dry_run=dry_run)
    except (PublishError, RuntimeError) as exc:
        n = int(etat.get(dossier.name, 0)) + 1
        etat[dossier.name] = n
        _save(STATE_PATH, etat)
        print(f"[dct] échec ({n}/{QUARANTINE_AFTER}) : {exc}", file=sys.stderr)
        if n >= QUARANTINE_AFTER:
            HOLD_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dossier), str(HOLD_DIR / dossier.name))
            notify.send(f"🛑 Reel DCT {dossier.name} écarté en _hold après {n} refus Meta. "
                        f"La file est débloquée.")
        else:
            notify.send(f"⚠️ Reel DCT {dossier.name} refusé par Meta ({n}/{QUARANTINE_AFTER}). "
                        f"Nouvelle tentative au prochain run.")
        return 1

    if dry_run:
        print(f"[dct] DRY-RUN OK — conteneur {res['container_id']}, rien n'est publié.")
        return 0

    media_id = res["media_id"]
    etat.pop(dossier.name, None)
    _save(STATE_PATH, etat)
    log = _log()
    log.append({"dossier": dossier.name, "media_id": media_id, "status": "success",
                "published_at": datetime.now(timezone.utc).isoformat()})
    _save(LOG_PATH, log)
    _archive(dossier, media_id)
    print(f"[dct] PUBLIÉ — media_id {media_id}")
    notify.send(f"✅ Reel DCT publié : {dossier.name} (media_id {media_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
