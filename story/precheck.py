#!/usr/bin/env python3
"""Court-circuit du workflow de publication STORY.

Ne répond qu'aux questions qu'on peut trancher SANS appeler Instagram : la
publication est-elle en pause, la cadence est-elle écoulée, la file est-elle
vide ? Ce sont les trois premiers refus de check_gates() dans
publish_story.py, dans le même ordre — la seule porte qui reste hors de ce
fichier est le QUOTA (content_publishing_limit), qui demande l'API Graph.

Même intérêt que pour LIGNE et le carrousel : un sondage à vide coûte
quelques secondes de python système au lieu du checkout + setup-python +
pip install du job de publication.

Écrit GO ou SKIP, et sort toujours en code 0 : le workflow décide, ce fichier
ne fait que constater.
"""

import datetime as dt
import json
import pathlib
import sys

STORY_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = STORY_DIR / "config.json"
JOURNAL = STORY_DIR / "journal.jsonl"
QUEUE_DIR = STORY_DIR / "queue"

CADENCE_HOURS_DEFAUT = 24.0     # doit rester aligné sur publish_story.py — une
                                 # séquence de stories par jour au maximum pour commencer


def _json(path: pathlib.Path, defaut):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def _dernier_publie():
    """Dernier événement "published" du journal (les "partial_publish" — une
    séquence tronquée par un échec en cours de boucle — ne comptent PAS comme
    une publication réussie et ne réarment donc pas la cadence)."""
    if not JOURNAL.is_file():
        return None
    dates = []
    try:
        lignes = JOURNAL.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            entree = json.loads(ligne)
        except ValueError:
            continue
        if entree.get("event") != "published" or not entree.get("at"):
            continue
        try:
            quand = dt.datetime.fromisoformat(str(entree["at"]).replace("Z", "+00:00"))
        except ValueError:
            continue
        if quand.tzinfo is None:
            quand = quand.replace(tzinfo=dt.timezone.utc)
        dates.append(quand)
    return max(dates) if dates else None


def verdict() -> str:
    config = _json(CONFIG_PATH, {})
    if config.get("paused"):
        return "SKIP — publication en pause (story/config.json paused=true)."

    if not QUEUE_DIR.is_dir():
        return "SKIP — pas de file."
    en_file = [p for p in QUEUE_DIR.iterdir()
               if p.is_file() and p.suffix == ".json" and not p.name.startswith(".")]
    if not en_file:
        return "SKIP — file vide, rien à publier."

    dernier = _dernier_publie()
    if dernier is not None:
        try:
            cadence = float(config.get("cadence_hours", CADENCE_HOURS_DEFAUT))
        except (TypeError, ValueError):
            cadence = CADENCE_HOURS_DEFAUT
        ecoule = (dt.datetime.now(dt.timezone.utc) - dernier).total_seconds() / 3600.0
        if ecoule < cadence:
            return (f"SKIP — cadence, dernière séquence il y a {ecoule:.1f}h "
                    f"(minimum {cadence:.0f}h).")

    return (f"GO — {len(en_file)} séquence(s) en file, pause levée, cadence écoulée. "
            "Le quota (mesuré à 100/24h, partagé avec LIGNE et le carrousel) reste "
            "à vérifier par le script complet.")


if __name__ == "__main__":
    print(verdict())
    sys.exit(0)
