#!/usr/bin/env python3
"""Court-circuit du workflow de publication LIGNE.

Répond à une seule question, avec la bibliothèque standard et sans rien
installer : ce run a-t-il une chance de publier ? Trois refus possibles, et ce
sont EXACTEMENT les trois premiers refus de publish_ligne.py, dans le même
ordre — pause, cadence non écoulée, file vide. Le filet Telegram n'est lu
qu'après ces trois portes dans le script réel, donc court-circuiter ici ne
change aucun comportement.

L'intérêt est le coût : un sondage à vide passe de ~1,7 minute de runner
(checkout + setup-python + pip install) à quelques secondes, ce qui autorise
un cron fréquent. La fréquence est ce qui protège la publication quand GitHub
retarde ou abandonne un créneau planifié, comme le 28/08/2026 au matin.

Écrit GO ou SKIP sur la sortie standard, et sort toujours en code 0 : le
workflow décide, ce fichier ne fait que constater.
"""

import datetime as dt
import json
import pathlib
import sys

LIGNE_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = LIGNE_DIR / "config.json"
LOG_PATH = LIGNE_DIR / "publish_log.json"
QUEUE_DIR = LIGNE_DIR / "queue"

CADENCE_GRACE_H = 0.5      # doit rester aligné sur publish_ligne.py
CADENCE_DEFAUT_H = 24.0


def _json(path: pathlib.Path, defaut):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def _dernier_succes(log):
    """Date du dernier succès, ou None. Annotation volontairement absente :
    ce fichier doit tourner sur le python système du runner, quel qu'il soit."""
    dates = []
    for entree in log if isinstance(log, list) else []:
        if entree.get("status") != "success" or not entree.get("published_at"):
            continue
        try:
            quand = dt.datetime.fromisoformat(
                str(entree["published_at"]).replace("Z", "+00:00"))
        except ValueError:
            continue
        if quand.tzinfo is None:
            quand = quand.replace(tzinfo=dt.timezone.utc)
        dates.append(quand)
    return max(dates) if dates else None


def verdict() -> str:
    config = _json(CONFIG_PATH, {})
    if config.get("paused"):
        return "SKIP — publication en pause (config.json paused=true)."

    dernier = _dernier_succes(_json(LOG_PATH, []))
    if dernier is not None:
        try:
            cadence = float(config.get("cadence_hours", CADENCE_DEFAUT_H))
        except (TypeError, ValueError):
            cadence = CADENCE_DEFAUT_H
        ecoule = (dt.datetime.now(dt.timezone.utc) - dernier).total_seconds() / 3600.0
        if ecoule < cadence - CADENCE_GRACE_H:
            return (f"SKIP — cadence non écoulée ({ecoule:.1f}h < {cadence}h), "
                    f"dernière publication le {dernier.isoformat()}.")

    if not QUEUE_DIR.is_dir():
        return "SKIP — pas de file."
    en_file = [p for p in QUEUE_DIR.iterdir()
               if p.is_dir() and not p.name.startswith(".")]
    if not en_file:
        return "SKIP — file vide, rien à publier."

    return f"GO — {len(en_file)} épisode(s) en file, cadence atteinte."


if __name__ == "__main__":
    print(verdict())
    sys.exit(0)
