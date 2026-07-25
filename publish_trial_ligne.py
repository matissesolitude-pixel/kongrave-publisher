#!/usr/bin/env python3
"""
publish_trial_ligne.py — publie UN épisode LIGNE en Reel d'ESSAI (Trial Reel).

Un Reel d'essai n'est montré qu'aux NON-abonnés : il sert à mesurer la rétention
d'une variante sans l'exposer à ton audience. Il ne passe aux abonnés que si TU le
« gradues » manuellement dans l'app (graduation_strategy = MANUAL).

Ce script est VOLONTAIREMENT séparé de la file (publish_ligne.py) :
  · il ne touche NI ligne/queue/ NI ligne/published/ NI publish_state.json ;
  · il ne rejoue rien, ne déplace rien, ne commit rien ;
  · il prend un épisode nommé, transcode son master en 25 fps (exigence Meta),
    crée le conteneur en mode essai, attend FINISHED, puis publie.

Le master doit exister (output/pilotes/<EP>.mp4) — le workflow le fabrique avant.

Usage :
    python publish_trial_ligne.py L22v2
    python publish_trial_ligne.py L22v2 --dry-run   # va jusqu'à FINISHED sans publier
    python publish_trial_ligne.py L22v2 --graduation SS_PERFORMANCE
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ligne"))

from publish_reel import PublishError, publish_episode  # noqa: E402
import ig_api  # noqa: E402
from autoprod_ligne import transcode_25  # noqa: E402

EPISODES = BASE_DIR / "ligne" / "episodes"
PILOTES = BASE_DIR / "output" / "pilotes"


def _load_episode(ep: str) -> dict:
    p = EPISODES / f"{ep}.json"
    if not p.is_file():
        raise SystemExit(f"[ERREUR] brief introuvable : {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _master(ep: str) -> Path:
    mp4 = PILOTES / f"{ep}.mp4"
    if not mp4.is_file():
        raise SystemExit(
            f"[ERREUR] master introuvable : {mp4}\n"
            f"          Fabrique-le d'abord : cd ligne && python3 build_ligne.py {ep} all"
        )
    return mp4


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Publie un épisode LIGNE en Reel d'essai.")
    ap.add_argument("episode", help="Identifiant de l'épisode (ex : L22v2)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Va jusqu'au conteneur FINISHED sans publier (test sûr).")
    ap.add_argument("--graduation", default="MANUAL", choices=["MANUAL", "SS_PERFORMANCE"],
                    help="MANUAL (défaut) : ne passe aux abonnés que sur action manuelle. "
                         "SS_PERFORMANCE : promotion auto s'il performe.")
    args = ap.parse_args(argv)

    ep = args.episode
    brief = _load_episode(ep)
    caption = (brief.get("caption") or "").strip()
    master = _master(ep)

    # 25 fps + 6M CBR + sans faststart — sinon Meta rejette (ProcessingFailedError).
    with tempfile.TemporaryDirectory() as td:
        pub_mp4 = Path(td) / f"{ep}_25fps.mp4"
        print(f"[trial] transcodage 25 fps -> {pub_mp4.name}")
        transcode_25(master, pub_mp4)

        trial = {"graduation_strategy": args.graduation}
        print(f"[trial] publication de {ep} en Reel d'ESSAI (graduation={args.graduation}, "
              f"dry_run={args.dry_run}) — visible uniquement des non-abonnés")
        try:
            res = publish_episode(pub_mp4, caption, dry_run=args.dry_run, trial_params=trial)
        except (ig_api.IgApiError, PublishError) as exc:
            print(f"[ERREUR] publication essai : {exc}")
            return 1

    if res.get("dry_run"):
        print(f"[DRY-RUN OK] conteneur essai prêt (FINISHED) : {res['container_id']} — RIEN publié")
    else:
        print(f"[OK] Reel d'ESSAI publié : media_id={res['media_id']} "
              f"(container={res['container_id']})")
        print("     → visible des non-abonnés uniquement ; graduation manuelle dans l'app.")
        if brief.get("pinned_comment"):
            print("     ⚠ commentaire épinglé NON posté (permission instagram_manage_comments) — "
                  "à coller à la main :")
            print(f'       {brief["pinned_comment"]}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
