#!/usr/bin/env python3
"""
cron_publisher.py — Cœur autonome, lancé toutes les 5 min par cron sur le VPS.

Boucle : lit schedule.json -> sélectionne les épisodes DUS et non encore publiés
-> publie via publish_reel.publish_episode -> journalise dans output/publish_log.json
-> notifie via Telegram.

Garde-fous :
  * Verrou fcntl : deux exécutions cron ne se chevauchent jamais (un upload peut
    durer > 5 min).
  * Idempotence : un épisode déjà "success" dans le log n'est jamais republié.
  * Rate limit : refuse de publier au-delà de MAX_PUBLISH_PER_DAY (50) sur 24 h.

Crontab type (VPS) :
  */5 * * * * cd ~/kongrave-publisher && /usr/bin/python3 cron_publisher.py >> output/cron.out 2>&1

Options :
  --dry-run   Traite les épisodes dus SANS publier (conteneur FINISHED seulement).
              N'écrit PAS d'entrée "success" -> l'épisode reste éligible ensuite.
"""

import argparse
import fcntl
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import notify
from publish_reel import PublishError, publish_episode
import ig_api

BASE_DIR = Path(__file__).resolve().parent
SCHEDULE_PATH = BASE_DIR / "schedule.json"
OUTPUT_DIR = BASE_DIR / "output"
LOG_PATH = OUTPUT_DIR / "publish_log.json"
LOCK_PATH = OUTPUT_DIR / ".cron.lock"

MAX_PUBLISH_PER_DAY = 50


# --------------------------------------------------------------------------- #
# Chargement / persistance
# --------------------------------------------------------------------------- #
def _load_json(path: Path, default):
    if not path.is_file():
        return default
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (ValueError, OSError) as exc:
        raise SystemExit(f"[cron] Impossible de lire {path} : {exc}")


def _load_schedule() -> List[dict]:
    data = _load_json(SCHEDULE_PATH, [])
    if not isinstance(data, list):
        raise SystemExit(f"[cron] {SCHEDULE_PATH} doit contenir une liste JSON.")
    return data


def _load_log() -> List[dict]:
    return _load_json(LOG_PATH, [])


def _append_log(entry: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log = _load_log()
    log.append(entry)
    tmp = LOG_PATH.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(log, fh, ensure_ascii=False, indent=2)
    tmp.replace(LOG_PATH)  # écriture atomique


# --------------------------------------------------------------------------- #
# Sélection des épisodes à publier
# --------------------------------------------------------------------------- #
def _parse_dt(raw: str) -> datetime:
    """Parse une date ISO. 'Z' accepté. Une date naïve est interprétée en heure locale."""
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.astimezone()  # attache le fuseau local du VPS
    return dt


def _published_episode_numbers(log: List[dict]) -> set:
    return {e["episode_number"] for e in log if e.get("status") == "success"}


def _publishes_last_24h(log: List[dict], now: datetime) -> int:
    cutoff = now - timedelta(hours=24)
    count = 0
    for e in log:
        if e.get("status") != "success":
            continue
        ts = e.get("published_at")
        if ts and _parse_dt(ts) >= cutoff:
            count += 1
    return count


def _due_episodes(schedule: List[dict], log: List[dict], now: datetime) -> List[dict]:
    already = _published_episode_numbers(log)
    due = []
    for entry in schedule:
        num = entry.get("episode_number")
        if num in already:
            continue
        try:
            when = _parse_dt(entry["publish_datetime"])
        except (KeyError, ValueError) as exc:
            print(f"[cron] Entrée ignorée (date invalide) ep {num}: {exc}", file=sys.stderr)
            continue
        if when <= now:
            due.append(entry)
    # Publie dans l'ordre chronologique prévu.
    due.sort(key=lambda e: _parse_dt(e["publish_datetime"]))
    return due


# --------------------------------------------------------------------------- #
# Traitement d'un épisode
# --------------------------------------------------------------------------- #
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _process(entry: dict, dry_run: bool) -> dict:
    num = entry.get("episode_number")
    mp4_path = (BASE_DIR / entry["filepath"]).resolve()
    caption = entry.get("caption", "")

    if not mp4_path.is_file():
        result = {
            "episode_number": num,
            "status": "error",
            "error": f"Fichier introuvable : {mp4_path}",
            "logged_at": _now_iso(),
        }
        _append_log(result)
        notify.send(f"❌ KONGRAVE ep {num} : fichier introuvable ({mp4_path.name}).")
        return result

    try:
        pub = publish_episode(mp4_path, caption, dry_run=dry_run)
    except (ig_api.IgApiError, PublishError) as exc:
        result = {
            "episode_number": num,
            "status": "error",
            "error": str(exc),
            "logged_at": _now_iso(),
        }
        _append_log(result)
        notify.send(f"❌ KONGRAVE ep {num} : échec publication.\n{exc}")
        return result

    if dry_run:
        # On NE journalise PAS un succès en dry-run : l'épisode reste éligible.
        print(f"[cron] DRY-RUN ep {num} OK — conteneur {pub['container_id']} (non publié).")
        return {"episode_number": num, "status": "dry_run_ok"}

    result = {
        "episode_number": num,
        "status": "success",
        "media_id": pub["media_id"],
        "container_id": pub["container_id"],
        "published_at": _now_iso(),
        "logged_at": _now_iso(),
    }
    _append_log(result)
    notify.send(f"✅ KONGRAVE ep {num} publié.\nmedia_id : {pub['media_id']}")
    return result


# --------------------------------------------------------------------------- #
# Point d'entrée
# --------------------------------------------------------------------------- #
def run(dry_run: bool = False) -> int:
    now = datetime.now(timezone.utc)
    schedule = _load_schedule()
    log = _load_log()

    due = _due_episodes(schedule, log, now)
    if not due:
        print(f"[cron] {now.isoformat()} — rien à publier.")
        return 0

    published_today = _publishes_last_24h(log, now)
    budget = MAX_PUBLISH_PER_DAY - published_today

    print(f"[cron] {len(due)} épisode(s) dû(s) ; budget 24h restant : {budget}.")

    # Un seul épisode par exécution. Après une interruption (panne GitHub, échec
    # Meta), plusieurs épisodes deviennent dus en même temps : les publier en
    # rafale enverrait deux Reels à quelques minutes d'intervalle. On traite le
    # plus ancien et on sort — les suivants partiront aux exécutions d'après.
    # Effet de bord assumé : un épisode qui échoue durablement bloque la file.
    for entry in due:
        if not dry_run and budget <= 0:
            msg = f"⚠️ KONGRAVE : limite {MAX_PUBLISH_PER_DAY} pubs/24h atteinte — report."
            print(f"[cron] {msg}", file=sys.stderr)
            notify.send(msg)
            break
        _process(entry, dry_run)
        break
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Publieur cron KONGRAVE.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Traite les épisodes dus sans publier (aucune trace 'success').",
    )
    args = parser.parse_args(argv)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Verrou : si une autre exécution cron tourne encore, on sort proprement.
    lock_file = LOCK_PATH.open("w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("[cron] Une autre exécution est en cours — on saute ce tick.")
        return 0

    try:
        return run(dry_run=args.dry_run)
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()


if __name__ == "__main__":
    raise SystemExit(main())
