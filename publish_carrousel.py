#!/usr/bin/env python3
"""
publish_carrousel.py — publie un CARROUSEL KONGRAVE sur @kongrave_.

Deux modes :

  # FILE (mode cron) : prend le plus ancien manifeste de carrousel/queue/
  python3 publish_carrousel.py --queue --base-url https://.../media/carrousel

  # EXPLICITE : publie un manifeste nommé, sans aucune barrière
  python3 publish_carrousel.py C2 --base-url https://.../media/carrousel --force

Flux Instagram (différent d'un Reel : aucun upload binaire possible pour les images) :
  1. un conteneur IMAGE par slide, l'API va CHERCHER chaque fichier à son URL publique
  2. un conteneur CAROUSEL qui référence les enfants, DANS L'ORDRE
  3. media_publish
  4. le commentaire CTA — l'API ne sait pas ÉPINGLER, seulement poster

Contraintes Meta appliquées : JPEG uniquement (le PNG est refusé), 2 à 10 images,
ratio entre 4:5 et 1.91:1 (nos slides 1080x1350 = 4:5 pile).

--- LES TROIS BARRIÈRES DU MODE FILE ---------------------------------------------
1. FENÊTRE : entre 20h et 22h heure de Paris. Le reel de LA LIGNE sort à 18h30 ; le
   carrousel doit passer APRÈS pour être le post le plus récent, sinon il n'est pas en
   haut à gauche de la grille.
2. ESPACEMENT : au moins 5 posts depuis le dernier carrousel, mesuré SUR INSTAGRAM
   (pas sur un compteur local). Cycle de 6 = 1 carrousel + 5 reels -> 6 est multiple de
   3, donc les carrousels tiennent la colonne de gauche.
3. CADENCE : jamais deux carrousels à moins de 20h d'intervalle (garde-fou contre un
   double déclenchement du cron).

La FILE est le vrai garde-fou éditorial : rien ne part si aucun manifeste n'y est.
"""
import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import ig_api

BASE_DIR = Path(__file__).resolve().parent
CARROUSEL_DIR = BASE_DIR / "carrousel"
QUEUE_DIR = CARROUSEL_DIR / "queue"
PUBLISHED_DIR = CARROUSEL_DIR / "published"
JOURNAL = CARROUSEL_DIR / "journal.jsonl"

PARIS = ZoneInfo("Europe/Paris")
WINDOW_HOURS = (20, 21, 22)     # heure de Paris
MIN_SPACING = 5                 # posts depuis le dernier carrousel
CADENCE_HOURS = 20              # entre deux carrousels

POLL_INTERVAL = 4
POLL_TIMEOUT = 180


def log(msg):
    print(msg, flush=True)


def skip(reason):
    log(f"[carrousel] RIEN À FAIRE — {reason}")
    sys.exit(0)


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


def posts_since_last_carousel():
    """(nb de posts publiés APRÈS le dernier carrousel, horodatage de ce carrousel).
    Renvoie (None, None) si aucun carrousel n'apparaît dans l'historique récent."""
    media = ig_api.list_recent_media(limit=30)
    for i, m in enumerate(media):
        if m.get("media_type") == "CAROUSEL_ALBUM":
            return i, m.get("timestamp")
    return None, None


def read_journal():
    if not JOURNAL.is_file():
        return []
    out = []
    for line in JOURNAL.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def append_journal(entry):
    CARROUSEL_DIR.mkdir(parents=True, exist_ok=True)
    with JOURNAL.open("a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def pick_from_queue():
    if not QUEUE_DIR.is_dir():
        skip(f"pas de file ({QUEUE_DIR})")
    manifests = sorted(QUEUE_DIR.glob("*.json"))
    if not manifests:
        skip("file vide — aucun carrousel en attente")
    # ORDRE ALPHABÉTIQUE du nom de fichier, pas de l'ID : on préfixe donc les fichiers
    # de file (01-C5.json, 02-C3.json) pour imposer l'ordre éditorial de la LOI 3
    # (alternance occidental/japonais), qui ne suit pas la numérotation des carrousels.
    return manifests[0]


def check_gates(force):
    if force:
        log("[carrousel] --force : fenêtre, espacement et cadence ignorés")
        return

    now_paris = datetime.now(PARIS)
    if now_paris.hour not in WINDOW_HOURS:
        skip(f"hors fenêtre — il est {now_paris:%H:%M} à Paris, "
             f"la fenêtre est {WINDOW_HOURS[0]}h–{WINDOW_HOURS[-1]}h "
             f"(après le reel de 18h30, pour rester le post le plus récent)")

    # cadence : d'après notre propre journal (plus fiable qu'un aller-retour API)
    entries = [e for e in read_journal() if e.get("event") == "published"]
    if entries:
        last = entries[-1].get("at")
        try:
            last_dt = datetime.fromisoformat(last)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - last_dt
            if delta < timedelta(hours=CADENCE_HOURS):
                skip(f"cadence — dernier carrousel il y a {delta.total_seconds()/3600:.1f}h "
                     f"(minimum {CADENCE_HOURS}h)")
        except (TypeError, ValueError):
            log(f"[carrousel] journal : horodatage illisible ({last!r}), cadence non vérifiée")

    # espacement réel de la grille, lu sur Instagram
    since, ts = posts_since_last_carousel()
    if since is None:
        log("[carrousel] aucun carrousel dans l'historique récent — espacement considéré OK")
    elif since < MIN_SPACING:
        skip(f"espacement — seulement {since} post(s) depuis le dernier carrousel "
             f"(du {ts}), il en faut {MIN_SPACING}. Le carrousel doit ouvrir une rangée : "
             f"publier plus tôt le décalerait de colonne.")
    else:
        log(f"[carrousel] espacement OK — {since} posts depuis le dernier carrousel ({ts})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carrousel_id", nargs="?", help="ID du manifeste (mode explicite)")
    ap.add_argument("--queue", action="store_true",
                    help="mode file : prend le plus ancien manifeste de carrousel/queue/")
    ap.add_argument("--base-url", required=True,
                    help="racine publique HTTPS des slides, sans slash final "
                         "(les fichiers attendus sont <base>/<ID>/slide_<n>.jpg)")
    ap.add_argument("--dry-run", action="store_true",
                    help="crée les conteneurs mais NE PUBLIE PAS et ne commente pas")
    ap.add_argument("--no-comment", action="store_true", help="publie sans poster le commentaire")
    ap.add_argument("--force", action="store_true",
                    help="ignore fenêtre + espacement + cadence (mode file uniquement)")
    args = ap.parse_args()

    if args.queue == bool(args.carrousel_id):
        sys.exit("[ERREUR] donne un ID, OU --queue — pas les deux, pas aucun.")

    if args.queue:
        check_gates(args.force)
        man_path = pick_from_queue()
        cid = json.loads(man_path.read_text()).get("id") or man_path.stem
    else:
        cid = args.carrousel_id
        man_path = CARROUSEL_DIR / f"{cid}.json"
        if not man_path.is_file():
            man_path = QUEUE_DIR / f"{cid}.json"
        if not man_path.is_file():
            sys.exit(f"[ERREUR] manifeste introuvable pour {cid}")

    man = json.loads(man_path.read_text())
    slides = man.get("slides") or []
    caption = (man.get("caption") or "").strip()
    pinned = (man.get("pinned_comment") or "").strip()
    if not slides:
        sys.exit(f"[ERREUR] {man_path.name} : manifeste sans slides")
    if not caption:
        sys.exit(f"[ERREUR] {man_path.name} : manifeste sans caption")

    base = args.base_url.rstrip("/")
    urls = [f"{base}/{cid}/slide_{n}.jpg" for n in slides]

    log(f"[carrousel] {cid} ({man_path.name}) — {len(urls)} slides" + ("  (DRY-RUN)" if args.dry_run else ""))

    # 1) un conteneur par image
    children = []
    for i, url in enumerate(urls, 1):
        container = ig_api.create_image_item(url)
        wait_finished(container, f"slide {slides[i - 1]}")
        children.append(container)
        log(f"[{i}/{len(urls)}] conteneur image OK  {container}")

    # 2) le conteneur carrousel
    carousel_id = ig_api.create_carousel(children, caption)
    wait_finished(carousel_id, "carrousel")
    log(f"[carrousel] conteneur agrégé OK  {carousel_id}")

    if args.dry_run:
        log("[carrousel] DRY-RUN : rien publié. Les conteneurs expirent seuls sous 24h.")
        return

    # 3) publication
    media_id = ig_api.publish(carousel_id)
    log(f"[carrousel] PUBLIÉ  media_id={media_id}")

    comment_id = None
    if pinned and not args.no_comment:
        try:
            comment_id = ig_api.post_comment(media_id, pinned)
            log(f"[carrousel] commentaire posté  {comment_id}  (à ÉPINGLER à la main dans l'app)")
        except ig_api.IgApiError as exc:
            # le post est déjà en ligne : un échec de commentaire ne doit pas masquer le succès
            log(f"[carrousel] AVERTISSEMENT — commentaire non posté : {exc}")

    # 4) journal + sortie de file. Écrit APRÈS la publication : si le commit échoue,
    #    mieux vaut un doublon signalé qu'une publication invisible.
    append_journal({
        "event": "published", "id": cid, "media_id": media_id,
        "comment_id": comment_id, "slides": len(slides),
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    if man_path.parent == QUEUE_DIR:
        PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
        man_path.rename(PUBLISHED_DIR / man_path.name)
        log(f"[carrousel] {man_path.name} : queue -> published")


if __name__ == "__main__":
    main()
