#!/usr/bin/env python3
"""
publish_story.py — publie une SÉQUENCE DE STORIES KONGRAVE sur @kongrave_.

Deux modes :

  # FILE (mode cron) : prend le plus ancien manifeste de story/queue/
  python3 publish_story.py --queue --base-url https://.../media/story

  # EXPLICITE : publie un manifeste nommé, sans aucune barrière
  python3 publish_story.py kongrave-story-01 --base-url https://.../media/story --force

Flux Instagram — DIFFÉRENT d'un carrousel : il n'existe PAS de conteneur qui
agrège les slides. Une séquence de dix slides, ce sont DIX conteneurs et DIX
media_publish distincts. Les stories s'affichent dans l'ordre de publication :
slide 1 en premier, slide N en dernier.

--- LA CONTRAINTE QUI DÉCIDE DE TOUT -----------------------------------------------
Une story ne se supprime PAS par l'API. Si la slide 4 échoue après que les
trois premières sont parties, il reste une demi-séquence en ligne pour
toujours — un hook sans son CTA, que personne ne peut retirer.

RÈGLE D'OR : on crée TOUS les conteneurs et on attend qu'ils soient TOUS
FINISHED avant d'en publier UN SEUL. Si un seul conteneur échoue, on abandonne
AVANT la première publication — les conteneurs non publiés expirent seuls
sous 24h et personne ne voit rien. Voir wait_all_finished() ci-dessous.

Cette règle ne couvre PAS le risque symétrique : media_publish peut, en de
rares cas, échouer APRÈS que tous les conteneurs sont FINISHED (réseau coupé
en cours de boucle, refus définitif tardif de Meta). Aucune garde ne peut
l'éliminer complètement — on journalise alors ce qui est parti comme
"partial_publish" au lieu de se taire. Voir le bloc try/except autour de la
boucle de publication dans main().

--- LES DEUX BARRIÈRES DU MODE FILE ------------------------------------------------
1. PAUSE + CADENCE : lues dans story/config.json et story/journal.jsonl — une
   séquence par jour au maximum pour commencer (cadence_hours=24).
2. QUOTA : GET /{ig-user}/content_publishing_limit — mesuré à 100 publications
   par 24h, PARTAGÉ avec LIGNE et le carrousel. Avant de publier N slides, il
   faut qu'il reste au moins N + QUOTA_MARGIN de marge. Sinon on ne commence
   MÊME PAS à créer les conteneurs : mieux vaut décaler que tronquer.

La FILE est le vrai garde-fou éditorial : rien ne part si aucun manifeste n'y est.
"""
import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import ig_api

BASE_DIR = Path(__file__).resolve().parent
STORY_DIR = BASE_DIR / "story"
QUEUE_DIR = STORY_DIR / "queue"
PUBLISHED_DIR = STORY_DIR / "published"
JOURNAL = STORY_DIR / "journal.jsonl"
CONFIG_PATH = STORY_DIR / "config.json"

CADENCE_HOURS_DEFAUT = 24.0     # une séquence de stories par jour au maximum, pour commencer
QUOTA_MARGIN = 5                # marge de sécurité sous le quota mesuré à 100/24h

POLL_INTERVAL = 4
POLL_TIMEOUT = 180


def log(msg):
    print(msg, flush=True)


def skip(reason):
    log(f"[story] RIEN À FAIRE — {reason}")
    sys.exit(0)


def _load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _is_paused():
    return bool(_load_json(CONFIG_PATH, {}).get("paused", False))


def _cadence_hours():
    try:
        return float(_load_json(CONFIG_PATH, {}).get("cadence_hours", CADENCE_HOURS_DEFAUT))
    except (TypeError, ValueError):
        return CADENCE_HOURS_DEFAUT


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
    STORY_DIR.mkdir(parents=True, exist_ok=True)
    with JOURNAL.open("a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def check_gates(force):
    """Pause + cadence — les deux portes locales, rejouées à l'identique par
    story/precheck.py (même source, même ordre)."""
    if force:
        log("[story] --force : pause et cadence ignorées")
        return

    if _is_paused():
        skip("publication en pause (story/config.json paused=true)")

    entries = [e for e in read_journal() if e.get("event") == "published"]
    if entries:
        last = entries[-1].get("at")
        cadence = _cadence_hours()
        try:
            last_dt = datetime.fromisoformat(last)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - last_dt
            if delta < timedelta(hours=cadence):
                skip(f"cadence — dernière séquence il y a {delta.total_seconds()/3600:.1f}h "
                     f"(minimum {cadence:.0f}h)")
        except (TypeError, ValueError):
            log(f"[story] journal : horodatage illisible ({last!r}), cadence non vérifiée")


def pick_from_queue():
    if not QUEUE_DIR.is_dir():
        skip(f"pas de file ({QUEUE_DIR})")
    manifests = sorted(QUEUE_DIR.glob("*.json"))
    if not manifests:
        skip("file vide — aucune séquence en attente")
    # ORDRE ALPHABÉTIQUE du nom de fichier — le plus ancien déposé sort en premier.
    return manifests[0]


def check_quota(n_slides):
    """GET /{ig-user}/content_publishing_limit — mesuré à 100 publications par 24h,
    PARTAGÉ avec LIGNE et le carrousel (même compte). N'utilise volontairement
    aucune nouvelle fonction publique d'ig_api.py (qui fait tourner deux chaînes
    en production) : mêmes primitives internes que le probe qui a validé le flux."""
    ig_user = ig_api._ig_user_id()
    token = ig_api._access_token()
    resp = ig_api._request(
        "GET",
        f"{ig_api.GRAPH_HOST}/{ig_api.GRAPH_VERSION}/{ig_user}/content_publishing_limit",
        params={"fields": "config,quota_usage", "access_token": token},
    )
    payload = ig_api._raise_for_api_error(resp, "content_publishing_limit")
    entries = payload.get("data") or []
    if not entries:
        raise ig_api.IgApiError("content_publishing_limit : réponse vide, quota illisible")
    entry = entries[0]
    usage = entry.get("quota_usage")
    total = (entry.get("config") or {}).get("quota_total")
    if usage is None or total is None:
        raise ig_api.IgApiError(f"content_publishing_limit : champs manquants ({entry})")

    remaining = total - usage
    needed = n_slides + QUOTA_MARGIN
    if remaining < needed:
        skip(f"quota — il reste {remaining}/{total} publications sur 24h, il en faut au moins "
             f"{needed} ({n_slides} slides + marge de {QUOTA_MARGIN}). Mieux vaut décaler que "
             f"tronquer.")
    log(f"[story] quota OK — {usage}/{total} déjà utilisées, {remaining} restantes, "
        f"{n_slides} nécessaires (+{QUOTA_MARGIN} de marge)")


def create_all_containers(urls):
    """Un conteneur STORIES par slide. Aucune publication ici — c'est la
    première moitié de la RÈGLE D'OR : on prépare tout avant de rien exposer."""
    containers = []
    for i, (n, url) in enumerate(urls, 1):
        container_id = ig_api.create_story_item(url)
        log(f"[{i}/{len(urls)}] conteneur créé  slide {n}  {container_id}")
        containers.append((n, container_id))
    return containers


def wait_all_finished(containers):
    """RÈGLE D'OR — on crée TOUS les conteneurs et on attend qu'ils soient TOUS
    FINISHED avant d'en publier UN SEUL.

    Une story ne se supprime pas par l'API. Si un conteneur échoue ou expire
    ici, on lève AVANT d'avoir appelé publish() sur quoi que ce soit : la
    séquence entière est abandonnée, pas la moitié publiée. Les conteneurs
    déjà FINISHED mais non publiés meurent seuls sous 24h — personne sur
    Instagram ne voit jamais un hook sans son CTA.
    """
    for n, container_id in containers:
        deadline = time.time() + POLL_TIMEOUT
        status = None
        while time.time() < deadline:
            status = ig_api.get_status(container_id)
            if status in (ig_api.STATUS_FINISHED, ig_api.STATUS_PUBLISHED):
                log(f"[story] slide {n} : conteneur FINISHED  ({container_id})")
                break
            if status in (ig_api.STATUS_ERROR, ig_api.STATUS_EXPIRED):
                raise ig_api.IgApiError(
                    f"slide {n} : conteneur en {status} ({container_id}) — RÈGLE D'OR : "
                    f"abandon avant toute publication, rien n'est parti sur Instagram."
                )
            time.sleep(POLL_INTERVAL)
        else:
            raise ig_api.IgApiError(
                f"slide {n} : toujours pas FINISHED après {POLL_TIMEOUT}s ({container_id}) — "
                f"abandon avant toute publication."
            )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sequence_id", nargs="?", help="ID du manifeste (mode explicite)")
    ap.add_argument("--queue", action="store_true",
                    help="mode file : prend le plus ancien manifeste de story/queue/")
    ap.add_argument("--base-url", required=True,
                    help="racine publique HTTPS des slides, sans slash final "
                         "(les fichiers attendus sont <base>/<ID>/slide_<n>.jpg)")
    ap.add_argument("--dry-run", action="store_true",
                    help="crée tous les conteneurs, attend FINISHED, NE PUBLIE RIEN et ne "
                         "déplace rien")
    ap.add_argument("--force", action="store_true",
                    help="ignore pause + cadence (mode file uniquement) — le quota reste vérifié")
    args = ap.parse_args()

    if args.queue == bool(args.sequence_id):
        sys.exit("[ERREUR] donne un ID, OU --queue — pas les deux, pas aucun.")

    if args.queue:
        check_gates(args.force)
        man_path = pick_from_queue()
        sid = json.loads(man_path.read_text()).get("id") or man_path.stem
    else:
        sid = args.sequence_id
        man_path = STORY_DIR / f"{sid}.json"
        if not man_path.is_file():
            man_path = QUEUE_DIR / f"{sid}.json"
        if not man_path.is_file():
            sys.exit(f"[ERREUR] manifeste introuvable pour {sid}")

    man = json.loads(man_path.read_text())
    slides = man.get("slides") or []
    if not slides:
        sys.exit(f"[ERREUR] {man_path.name} : manifeste sans slides")

    base = args.base_url.rstrip("/")
    urls = [(n, f"{base}/{sid}/slide_{n}.jpg") for n in slides]

    # Le quota se vérifie AVANT de créer le moindre conteneur : un refus ici
    # ne coûte rien à Meta et rien à nous. Mieux vaut décaler que tronquer.
    check_quota(len(urls))

    log(f"[story] {sid} ({man_path.name}) — {len(urls)} slides" +
        ("  (DRY-RUN)" if args.dry_run else ""))

    # 1) TOUS les conteneurs, puis attente que TOUS soient FINISHED — RÈGLE D'OR.
    containers = create_all_containers(urls)
    wait_all_finished(containers)
    log(f"[story] les {len(containers)} conteneurs sont FINISHED — publication autorisée")

    if args.dry_run:
        log("[story] DRY-RUN : rien publié. Les conteneurs expirent seuls sous 24h.")
        return

    # 2) publication dans l'ORDRE CROISSANT, jamais en parallèle — l'ordre de
    #    publication EST l'ordre d'affichage des stories (slide 1 en premier).
    published = []
    try:
        for i, (n, container_id) in enumerate(containers, 1):
            media_id = ig_api.publish(container_id)
            log(f"[{i}/{len(containers)}] PUBLIÉ  slide {n}  media_id={media_id}")
            published.append({"slide": n, "container_id": container_id, "media_id": media_id})
    except ig_api.IgApiError as exc:
        # Risque résiduel qu'AUCUNE garde ne peut éliminer : les conteneurs
        # étaient TOUS FINISHED, mais media_publish peut échouer EN COURS de
        # boucle. On journalise ce qui est PARTI avant de remonter l'erreur —
        # mieux vaut une trace de séquence tronquée qu'un silence total.
        if published:
            append_journal({
                "event": "partial_publish", "id": sid, "slides": len(slides),
                "media": published, "error": str(exc),
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
            log(f"[story] ⚠ SÉQUENCE TRONQUÉE — {len(published)}/{len(containers)} slides "
                f"publiées avant l'échec. Journalisé comme partial_publish : vérifier "
                f"@kongrave_ à la main, le reste ne peut PAS être retiré ni complété "
                f"automatiquement.")
        raise

    # 3) journal + sortie de file. Écrit APRÈS la publication : si le commit
    #    échoue, mieux vaut un doublon signalé qu'une publication invisible.
    append_journal({
        "event": "published", "id": sid, "slides": len(slides),
        "media": published,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    if man_path.parent == QUEUE_DIR:
        PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
        man_path.rename(PUBLISHED_DIR / man_path.name)
        log(f"[story] {man_path.name} : queue -> published")


if __name__ == "__main__":
    main()
