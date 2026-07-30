#!/usr/bin/env python3
"""
publish_carrousel.py — publie un CARROUSEL KONGRAVE sur @kongrave_.

  python3 publish_carrousel.py C2 --base-url https://.../media/carrousel --dry-run
  python3 publish_carrousel.py C2 --base-url https://.../media/carrousel

Flux Instagram (différent d'un Reel : aucun upload binaire possible pour les images) :
  1. un conteneur IMAGE par slide, l'API va CHERCHER chaque fichier à son URL publique
  2. un conteneur CAROUSEL qui référence les enfants, DANS L'ORDRE
  3. media_publish
  4. le commentaire épinglé (CTA reformulé) — l'API ne sait pas épingler, seulement poster

Contraintes Meta appliquées ici :
  - JPEG uniquement (le PNG est refusé)
  - 2 à 10 images
  - ratio entre 4:5 et 1.91:1 (nos slides 1080x1350 = 4:5 pile, à la limite basse)

Le manifeste lu est carrousel/<ID>.json : {slides:[n…], caption, pinned_comment}.
Il est produit par prepare_carrousel.py à côté du moteur de rendu.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import ig_api

BASE_DIR = Path(__file__).resolve().parent
MANIFESTS = BASE_DIR / "carrousel"

POLL_INTERVAL = 4
POLL_TIMEOUT = 180


def log(msg):
    print(msg, flush=True)


def wait_finished(container_id, label):
    """Un conteneur image passe FINISHED en quelques secondes. ERROR = Meta a refusé le fichier."""
    deadline = time.time() + POLL_TIMEOUT
    while time.time() < deadline:
        status = ig_api.get_status(container_id)
        if status in (ig_api.STATUS_FINISHED, ig_api.STATUS_PUBLISHED):
            return
        if status in (ig_api.STATUS_ERROR, ig_api.STATUS_EXPIRED):
            raise ig_api.IgApiError(f"{label} : conteneur en {status}")
        time.sleep(POLL_INTERVAL)
    raise ig_api.IgApiError(f"{label} : toujours pas FINISHED après {POLL_TIMEOUT}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carrousel_id")
    ap.add_argument("--base-url", required=True,
                    help="racine publique HTTPS des slides, sans slash final "
                         "(les fichiers attendus sont <base>/<ID>/slide_<n>.jpg)")
    ap.add_argument("--dry-run", action="store_true",
                    help="crée les conteneurs mais NE PUBLIE PAS et ne commente pas")
    ap.add_argument("--no-comment", action="store_true",
                    help="publie sans poster le commentaire épinglé")
    args = ap.parse_args()

    man_path = MANIFESTS / f"{args.carrousel_id}.json"
    if not man_path.is_file():
        sys.exit(f"[ERREUR] manifeste introuvable : {man_path}")
    man = json.loads(man_path.read_text())

    slides = man.get("slides") or []
    caption = (man.get("caption") or "").strip()
    pinned = (man.get("pinned_comment") or "").strip()
    if not slides:
        sys.exit("[ERREUR] manifeste sans slides")
    if not caption:
        sys.exit("[ERREUR] manifeste sans caption")

    base = args.base_url.rstrip("/")
    urls = [f"{base}/{args.carrousel_id}/slide_{n}.jpg" for n in slides]

    log(f"[carrousel] {args.carrousel_id} — {len(urls)} slides"
        + ("  (DRY-RUN)" if args.dry_run else ""))
    for u in urls:
        log(f"   {u}")

    # 1) un conteneur par image
    children = []
    for i, url in enumerate(urls, 1):
        cid = ig_api.create_image_item(url)
        wait_finished(cid, f"slide {slides[i - 1]}")
        children.append(cid)
        log(f"[{i}/{len(urls)}] conteneur image OK  {cid}")

    # 2) le conteneur carrousel
    carousel_id = ig_api.create_carousel(children, caption)
    wait_finished(carousel_id, "carrousel")
    log(f"[carrousel] conteneur agrégé OK  {carousel_id}")

    if args.dry_run:
        log("[carrousel] DRY-RUN : rien n'a été publié. Les conteneurs expirent seuls sous 24h.")
        return

    # 3) publication
    media_id = ig_api.publish(carousel_id)
    log(f"[carrousel] PUBLIÉ  media_id={media_id}")

    # 4) commentaire épinglé (l'API ne sait pas épingler : à épingler à la main dans l'app)
    if pinned and not args.no_comment:
        try:
            comment_id = ig_api.post_comment(media_id, pinned)
            log(f"[carrousel] commentaire posté  {comment_id}  (à ÉPINGLER à la main dans l'app)")
        except ig_api.IgApiError as exc:
            # le post est déjà en ligne : un échec de commentaire ne doit pas masquer le succès
            log(f"[carrousel] AVERTISSEMENT — commentaire non posté : {exc}")


if __name__ == "__main__":
    main()
