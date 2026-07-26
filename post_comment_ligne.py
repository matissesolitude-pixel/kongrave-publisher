#!/usr/bin/env python3
"""
post_comment_ligne.py — poste le commentaire épinglé (CTA) d'un épisode LIGNE
sur un média déjà publié.

Usage :
    python post_comment_ligne.py <EP> <media_id>
    python post_comment_ligne.py <EP> <media_id> --message "texte libre"

Le texte par défaut est le champ `pinned_comment` du JSON de l'épisode.
Requiert la permission instagram_manage_comments sur le token — si elle manque,
Meta renvoie une erreur claire (et on saura enfin à quoi s'en tenir).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import ig_api  # noqa: E402

EPISODES = BASE_DIR / "ligne" / "episodes"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Poste le CTA en commentaire d'un Reel LIGNE.")
    ap.add_argument("episode", help="Identifiant de l'épisode (ex : L22v2)")
    ap.add_argument("media_id", help="media_id du Reel déjà publié")
    ap.add_argument("--message", default=None, help="Texte du commentaire (défaut : pinned_comment du JSON)")
    ap.add_argument("--replace", default=None, metavar="COMMENT_ID",
                    help="Supprime d'abord ce commentaire (pour corriger un CTA déjà posté)")
    args = ap.parse_args(argv)

    message = args.message
    if message is None:
        p = EPISODES / f"{args.episode}.json"
        if not p.is_file():
            print(f"[ERREUR] brief introuvable : {p}")
            return 1
        message = (json.loads(p.read_text(encoding="utf-8")).get("pinned_comment") or "").strip()
    if not message:
        print(f"[ERREUR] aucun commentaire à poster pour {args.episode}")
        return 1

    if args.replace:
        try:
            ig_api.delete_comment(args.replace)
            print(f"[OK] ancien commentaire supprimé : {args.replace}")
        except ig_api.IgApiError as exc:
            print(f"[ERREUR] suppression ancien commentaire : {exc}")
            return 1

    try:
        cid = ig_api.post_comment(args.media_id, message)
    except ig_api.IgApiError as exc:
        print(f"[ERREUR] commentaire : {exc}")
        return 1
    print(f"[OK] commentaire posté : id={cid} sur media {args.media_id}")
    print(f"     texte : {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
