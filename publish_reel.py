#!/usr/bin/env python3
"""
publish_reel.py — Publie UN Reel de bout en bout.

Orchestration : create_container -> poll status_code jusqu'à FINISHED
-> publish. Un conteneur EXPIRED ou ERROR n'est JAMAIS publié.

Utilisé en CLI (test manuel) et importé par cron_publisher.py.

CLI :
  python publish_reel.py <chemin.mp4> "<caption>"            # publie pour de vrai
  python publish_reel.py <chemin.mp4> "<caption>" --dry-run  # va jusqu'à FINISHED
                                                             # SANS publier (test sûr)
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

import ig_api

# Le processing vidéo côté Meta prend de quelques secondes à ~1 min.
POLL_INTERVAL_SECONDS = 10
POLL_TIMEOUT_SECONDS = 300  # 5 min : au-delà, on considère l'encodage bloqué.


class PublishError(RuntimeError):
    pass


def _wait_until_finished(container_id: str) -> None:
    """Attend que le conteneur soit FINISHED. Lève si ERROR / EXPIRED / timeout."""
    deadline = time.time() + POLL_TIMEOUT_SECONDS
    while True:
        status = ig_api.get_status(container_id)
        if status == ig_api.STATUS_FINISHED:
            return
        if status in (ig_api.STATUS_ERROR, ig_api.STATUS_EXPIRED):
            raise PublishError(
                f"Conteneur {container_id} en statut {status} — publication annulée."
            )
        if time.time() >= deadline:
            raise PublishError(
                f"Timeout : conteneur {container_id} toujours {status} après "
                f"{POLL_TIMEOUT_SECONDS}s."
            )
        time.sleep(POLL_INTERVAL_SECONDS)


def publish_episode(mp4_path: Path, caption: str, dry_run: bool = False,
                    trial_params: Optional[dict] = None) -> dict:
    """
    Publie un épisode. Retourne un dict résultat exploitable par le logger.

    dry_run=True : crée le conteneur, attend FINISHED, mais N'APPELLE PAS media_publish.
    C'est le mode test sûr — rien n'apparaît sur le compte.

    trial_params : transmis à create_container pour publier en Reel d'ESSAI
    (visible uniquement des non-abonnés). Absent -> Reel normal.
    """
    mp4_path = Path(mp4_path)
    container_id = ig_api.create_container(mp4_path, caption, trial_params=trial_params)
    _wait_until_finished(container_id)

    if dry_run:
        return {
            "status": "dry_run_ok",
            "container_id": container_id,
            "media_id": None,
            "dry_run": True,
        }

    media_id = ig_api.publish(container_id)
    return {
        "status": "success",
        "container_id": container_id,
        "media_id": media_id,
        "dry_run": False,
    }


def _parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publie un Reel Instagram (KONGRAVE).")
    parser.add_argument("mp4", help="Chemin du fichier .mp4")
    parser.add_argument("caption", help="Légende du Reel")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Va jusqu'au conteneur FINISHED sans publier (test sûr).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    args = _parse_args(argv)
    try:
        result = publish_episode(Path(args.mp4), args.caption, dry_run=args.dry_run)
    except (ig_api.IgApiError, PublishError) as exc:
        print(f"[ÉCHEC] {exc}", file=sys.stderr)
        return 1

    if result["dry_run"]:
        print(f"[DRY-RUN OK] Conteneur prêt (FINISHED) : {result['container_id']}")
        print("Aucune publication effectuée. Retire --dry-run pour publier.")
    else:
        print(f"[PUBLIÉ] media_id = {result['media_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
