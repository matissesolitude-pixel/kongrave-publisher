#!/usr/bin/env python3
"""Court-circuit du workflow de publication CARROUSEL.

Ne répond qu'aux deux questions qu'on peut trancher SANS appeler Instagram :
la file est-elle vide, et la cadence de 20 h est-elle écoulée ? Ce sont les
deux mêmes portes que check_gates() dans publish_carrousel.py, avec la même
source — carrousel/journal.jsonl.

La troisième porte, l'espacement réel de la grille, demande de lire le compte
sur l'API Graph : elle reste dans le script complet. Ce fichier ne prétend
donc pas dire oui, seulement dire non plus tôt et pour presque rien.

Écrit GO ou SKIP, et sort toujours en code 0.
"""

import datetime as dt
import json
import pathlib
import sys

CARROUSEL_DIR = pathlib.Path(__file__).resolve().parent
JOURNAL = CARROUSEL_DIR / "journal.jsonl"
QUEUE_DIR = CARROUSEL_DIR / "queue"

CADENCE_HOURS = 20.0       # doit rester aligné sur publish_carrousel.py


def _dernier_publie():
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
            quand = dt.datetime.fromisoformat(str(entree["at"]))
        except ValueError:
            continue
        if quand.tzinfo is None:
            quand = quand.replace(tzinfo=dt.timezone.utc)
        dates.append(quand)
    return max(dates) if dates else None


def verdict() -> str:
    if not QUEUE_DIR.is_dir():
        return "SKIP — pas de file."
    en_file = [p for p in QUEUE_DIR.iterdir()
               if p.is_file() and p.suffix == ".json" and not p.name.startswith(".")]
    if not en_file:
        return "SKIP — file vide, rien à publier."

    dernier = _dernier_publie()
    if dernier is not None:
        ecoule = (dt.datetime.now(dt.timezone.utc) - dernier).total_seconds() / 3600.0
        if ecoule < CADENCE_HOURS:
            return (f"SKIP — cadence, dernier carrousel il y a {ecoule:.1f}h "
                    f"(minimum {CADENCE_HOURS:.0f}h).")

    return (f"GO — {len(en_file)} carrousel(s) en file, cadence écoulée. "
            "L'espacement de la grille reste à vérifier par le script complet.")


if __name__ == "__main__":
    print(verdict())
    sys.exit(0)
