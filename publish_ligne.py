#!/usr/bin/env python3
"""
publish_ligne.py — Publisher LIGNE (file d'attente). Extension du publisher KONGRAVE.

Modèle : une FILE, pas un planning. Un épisode validé PO = UN sous-dossier de
`ligne/queue/` contenant UN `.mp4` (le master final) et un `caption.txt`. Le seul
geste du PO : déposer ce dossier (+ commit/push). C'est tout.

Chaque jour à ~18h30 Paris, on prend le PLUS ANCIEN dossier de la file, on le
publie sur @kongrave_ via Graph API (réutilise publish_reel/ig_api), puis on le
déplace en `ligne/published/`. File vide à l'heure de publier -> on NOTIFIE et on
ne publie RIEN (fail loud, jamais de bruit de remplissage).

Garde-fous :
  * CADENCE : refuse de publier si le précédent post Ligne date de moins de
    CADENCE_HOURS (lu dans ligne/config.json, défaut 24). Anti-spam même par
    erreur de file. Une marge de 0,5 h absorbe la gigue du cron (sinon un écart
    de 23h59 bloquerait le post quotidien).
  * FENÊTRE : ne publie qu'à 18h heure de Paris. Le workflow tourne à 16h30 ET
    17h30 UTC pour couvrir été/hiver ; le script filtre sur l'heure de Paris ->
    18h30 Paris toute l'année, sans dépendre du fuseau du runner.
  * FIFO : plus ancien = nom de dossier trié en premier (préfixe sortable).
    Jamais mtime : un `git checkout` réécrit les mtime sur le runner.

Options :
  --dry-run   Crée le conteneur Meta mais NE PUBLIE PAS et NE DÉPLACE PAS.
  --force     Ignore la fenêtre horaire ET la cadence (test / publication manuelle).
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests

try:
    from zoneinfo import ZoneInfo
    PARIS = ZoneInfo("Europe/Paris")
except Exception:  # zoneinfo indisponible : repli approximatif (UTC+1, pas d'été)
    PARIS = timezone(timedelta(hours=1))

import ig_api
import notify
from publish_reel import PublishError, publish_episode

BASE_DIR = Path(__file__).resolve().parent
LIGNE_DIR = BASE_DIR / "ligne"
QUEUE_DIR = LIGNE_DIR / "queue"
PUBLISHED_DIR = LIGNE_DIR / "published"
CONFIG_PATH = LIGNE_DIR / "config.json"
LOG_PATH = LIGNE_DIR / "publish_log.json"
BLOCKED_PATH = LIGNE_DIR / "blocked.json"     # filet passif : épisodes retirés par ❌ / "STOP Lxx"
OFFSET_PATH = LIGNE_DIR / "tg_offset.json"    # dernier update_id Telegram consommé
BLOCKED_DIR = LIGNE_DIR / "_blocked"          # les épisodes bloqués y sont déplacés (hors file)

PUBLISH_HOUR_PARIS = 18       # publie quand il est 18h à Paris (le cron cadre la fenêtre)
CADENCE_GRACE_H = 0.5         # marge anti-gigue sur la cadence


# --------------------------------------------------------------------------- #
# Chargement / persistance
# --------------------------------------------------------------------------- #
def _load_json(path: Path, default):
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise SystemExit(f"[ligne] Impossible de lire {path} : {exc}")


def _cadence_hours() -> float:
    cfg = _load_json(CONFIG_PATH, {})
    try:
        return float(cfg.get("cadence_hours", 24))
    except (TypeError, ValueError):
        print("[ligne] cadence_hours invalide dans config.json — défaut 24h.", file=sys.stderr)
        return 24.0


def _is_paused() -> bool:
    """Publication AUTO en pause ? Gate manuel/auto : quand True, le run PLANIFIÉ ne
    publie rien ; seuls --dry-run et --force (manuels) passent. (Pilote L1 : paused=true,
    on repasse à false après le premier vrai run pour l'automatique.)"""
    return bool(_load_json(CONFIG_PATH, {}).get("paused", False))


def _load_log() -> list:
    data = _load_json(LOG_PATH, [])
    return data if isinstance(data, list) else []


def _append_log(entry: dict) -> None:
    LIGNE_DIR.mkdir(parents=True, exist_ok=True)
    log = _load_log()
    log.append(entry)
    tmp = LOG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(LOG_PATH)  # écriture atomique


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


# --------------------------------------------------------------------------- #
# FILET PASSIF Telegram — silence = validé. Un ❌ (bouton) ou "STOP Lxx" RETIRE.
# --------------------------------------------------------------------------- #
def _blocked_set() -> set:
    data = _load_json(BLOCKED_PATH, [])
    return set(data) if isinstance(data, list) else set()


def _ingest_blocks() -> None:
    """Lit les updates Telegram (bouton ❌ 'block:Lxx' ou message 'STOP Lxx') et alimente
    blocked.json. AUCUN update = rien bloqué = publication normale (filet PASSIF). L'offset
    consommé est persisté (tg_offset.json) pour ne traiter chaque update qu'une fois."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    off = 0
    o = _load_json(OFFSET_PATH, {})
    if isinstance(o, dict):
        off = int(o.get("offset", 0) or 0)
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={"offset": off + 1, "timeout": 0,
                    "allowed_updates": json.dumps(["message", "callback_query"])},
            timeout=25,
        )
        updates = r.json().get("result", []) if r.status_code < 400 else []
    except (requests.RequestException, ValueError) as exc:
        print(f"[ligne] getUpdates impossible ({exc}) — filet passif ignoré ce run.", file=sys.stderr)
        return
    blocked = _blocked_set()
    max_off = off
    for u in updates:
        max_off = max(max_off, int(u.get("update_id", off)))
        ep = None
        cq = u.get("callback_query")
        if cq and str(cq.get("data", "")).startswith("block:"):
            ep = cq["data"].split(":", 1)[1].strip().upper()
            try:  # ACK du bouton (retire le spinner côté Telegram)
                requests.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery",
                              data={"callback_query_id": cq.get("id", ""),
                                    "text": f"{ep} bloqué — ne sera pas publié."}, timeout=15)
            except requests.RequestException:
                pass
        else:
            txt = (u.get("message") or {}).get("text", "") or ""
            m = re.search(r"(?:stop|bloqu\w*|❌)\s*[:#]?\s*(L\d+)", txt, re.I)
            if m:
                ep = m.group(1).upper()
        if ep:
            blocked.add(ep)
            print(f"[ligne] filet passif : {ep} BLOQUÉ (retiré de la publication).")
    _save_json(OFFSET_PATH, {"offset": max_off})
    _save_json(BLOCKED_PATH, sorted(blocked))


# --------------------------------------------------------------------------- #
# Temps / cadence
# --------------------------------------------------------------------------- #
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse_dt(raw: str) -> datetime:
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _last_publish(log: list) -> Optional[datetime]:
    times = [
        _parse_dt(e["published_at"])
        for e in log
        if e.get("status") == "success" and e.get("published_at")
    ]
    return max(times) if times else None


# --------------------------------------------------------------------------- #
# File d'attente
# --------------------------------------------------------------------------- #
def _oldest_episode() -> Optional[Path]:
    """Plus ancien = sous-dossier au nom trié en premier (préfixe sortable)."""
    if not QUEUE_DIR.is_dir():
        return None
    subs = sorted(
        (p for p in QUEUE_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")),
        key=lambda p: p.name,
    )
    return subs[0] if subs else None


def _episode_files(folder: Path):
    """Un dossier d'épisode = exactement un .mp4 + un caption.txt (optionnel)."""
    mp4s = sorted(folder.glob("*.mp4"))
    if not mp4s:
        raise PublishError(f"{folder.name} : aucun .mp4 dans le dossier.")
    if len(mp4s) > 1:
        raise PublishError(f"{folder.name} : plusieurs .mp4 (un seul master attendu).")
    cap = folder / "caption.txt"
    caption = cap.read_text(encoding="utf-8").strip() if cap.is_file() else ""
    return mp4s[0], caption


# --------------------------------------------------------------------------- #
# Point d'entrée
# --------------------------------------------------------------------------- #
def run(dry_run: bool = False, force: bool = False) -> int:
    now = _now_utc()
    paris = now.astimezone(PARIS)

    # GATE manuel/auto : en pause, le run PLANIFIÉ ne publie rien (dry-run/force passent).
    if _is_paused() and not force and not dry_run:
        print("[ligne] Publication AUTO en pause (config.json paused=true) — rien à faire.")
        return 0

    # CADENCE = seul garde-fou temporel (6/jour = cron toutes les 4h + cadence_hours=4).
    # Plus de fenêtre d'heure unique : le cron cadence les créneaux, la cadence empêche le double-post.
    cadence = _cadence_hours()
    log = _load_log()
    last = _last_publish(log)

    # GARDE-FOU cadence : refuse si le dernier post Ligne date de < CADENCE_HOURS.
    if last is not None and not force:
        elapsed = (now - last).total_seconds() / 3600.0
        if elapsed < cadence - CADENCE_GRACE_H:
            print(f"[ligne] Cadence non écoulée ({elapsed:.1f}h < {cadence}h) — refus de publier.")
            return 0

    # FILET PASSIF : intègre les ❌ reçus depuis Telegram, puis sélectionne le plus ancien NON bloqué.
    if not dry_run:
        _ingest_blocks()
    blocked = _blocked_set()
    ep = None
    while True:
        ep = _oldest_episode()
        if ep is None:
            break
        if ep.name.upper() in blocked:
            BLOCKED_DIR.mkdir(parents=True, exist_ok=True)
            dest_b = BLOCKED_DIR / ep.name
            if dest_b.exists():
                shutil.rmtree(dest_b)
            shutil.move(str(ep), str(dest_b))
            print(f"[ligne] {ep.name} bloqué (filet passif) — retiré de la file.")
            if not dry_run:
                notify.send(f"❌ LIGNE : {ep.name} retiré de la file (bloqué), non publié.")
            continue
        break

    if ep is None:
        # FAIL LOUD : c'est l'heure de publier mais la file est vide.
        msg = ("⚠️ LIGNE : file vide à l'heure de publier — rien publié.\n"
               "Dépose un épisode (dossier .mp4 + caption.txt) dans ligne/queue/.")
        print(f"[ligne] {msg}")
        if not dry_run:
            notify.send(msg)
        return 0

    try:
        mp4, caption = _episode_files(ep)
    except PublishError as exc:
        print(f"[ligne] {exc}", file=sys.stderr)
        notify.send(f"❌ LIGNE : {exc}")
        _append_log({"episode": ep.name, "status": "error", "error": str(exc), "logged_at": _iso(now)})
        return 0

    # Meta renvoie parfois un ProcessingFailedError INTERMITTENT à l'upload (constaté : un
    # même fichier échoue puis passe au retry). On retente jusqu'à 3× sur cette erreur-là
    # uniquement ; toute autre erreur casse tout de suite (pas de retry aveugle).
    pub = last_exc = None
    for attempt in range(1, 4):
        try:
            pub = publish_episode(mp4.resolve(), caption, dry_run=dry_run)
            break
        except (ig_api.IgApiError, PublishError) as exc:
            last_exc = exc
            if "ProcessingFailedError" in str(exc) and attempt < 3:
                print(f"[ligne] ProcessingFailedError (tentative {attempt}/3) — retry dans 25s…", file=sys.stderr)
                time.sleep(25)
                continue
            break
    if pub is None:
        print(f"[ligne] Échec publication {ep.name} : {last_exc}", file=sys.stderr)
        notify.send(f"❌ LIGNE {ep.name} : échec publication (après retries).\n{last_exc}")
        _append_log({"episode": ep.name, "status": "error", "error": str(last_exc), "logged_at": _iso(now)})
        return 0

    if dry_run:
        print(f"[ligne] DRY-RUN {ep.name} OK — conteneur {pub.get('container_id')} "
              f"(non publié, dossier non déplacé).")
        return 0

    # Succès : déplacer en published/ + journaliser + notifier.
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    dest = PUBLISHED_DIR / ep.name
    if dest.exists():
        dest = PUBLISHED_DIR / f"{ep.name}_{now.strftime('%Y%m%dT%H%M%SZ')}"
    shutil.move(str(ep), str(dest))
    _append_log({
        "episode": ep.name,
        "status": "success",
        "media_id": pub["media_id"],
        "container_id": pub["container_id"],
        "published_at": _iso(now),
        "logged_at": _iso(now),
    })
    notify.send(f"✅ LIGNE {ep.name} publié sur @kongrave_.\nmedia_id : {pub['media_id']}")
    print(f"[ligne] {ep.name} publié et déplacé en published/.")
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Publisher LIGNE (file d'attente).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Crée le conteneur sans publier ni déplacer.")
    parser.add_argument("--force", action="store_true",
                        help="Ignore la fenêtre horaire ET la cadence (test/manuel).")
    args = parser.parse_args(argv)
    return run(dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
