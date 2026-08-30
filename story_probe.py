#!/usr/bin/env python3
"""
story_probe.py — SPIKE. Répond à une seule question : le jeton en Secrets
peut-il publier une STORY sur @kongrave_ ?

Ce fichier est jetable. Il ne modifie ni ig_api.py ni aucune chaîne existante,
il n'écrit rien sur le disque, il ne commite rien. Il ne fait que constater.

Quatre constats, du moins cher au plus concluant :

  1. /debug_token          les permissions RÉELLEMENT portées par le jeton
  2. /content_publishing_limit  l'état du quota — et donc si les stories le
                           partagent avec les Reels et les carrousels, au lieu
                           de le supposer
  3. conteneur STORIES     création d'un conteneur media_type=STORIES depuis une
                           image DÉJÀ en ligne sur le Pages de disruptive-legal,
                           attente du FINISHED, puis ARRÊT. Le conteneur expire
                           seul sous 24 h. C'est le dry-run.
  4. --publish             (optionnel, JAMAIS par défaut) publie vraiment. Une
                           story meurt en 24 h : c'est le test réel le moins cher
                           qui existe, mais il reste une publication visible.

Sur l'étape 3, deux échecs sont possibles et il ne faut pas les confondre :
  - erreur de PERMISSION  -> OAuthException, le jeton ne porte pas le droit
  - erreur de RATIO/MÉDIA -> Meta le dit explicitement ; l'image de test est une
    slide de carrousel en 4:5, pas une story en 9:16. Un refus de ratio est une
    bonne nouvelle déguisée : il prouve que l'appel STORIES a été AUTORISÉ puis
    évalué sur son contenu.
"""
import argparse
import json
import sys
import time

import ig_api

GRAPH = f"{ig_api.GRAPH_HOST}/{ig_api.GRAPH_VERSION}"

# Image de test : une slide de carrousel DÉJÀ publiée et déjà servie par le
# Pages. Zéro asset à produire, zéro décision de design engagée par ce probe.
DEFAULT_IMAGE = (
    "https://matissesolitude-pixel.github.io/disruptive-legal"
    "/media/carrousel/C17/slide_1.jpg"
)

POLL_INTERVAL = 4
POLL_TIMEOUT = 120


def titre(n, texte):
    print(f"\n{'='*70}\n[{n}] {texte}\n{'='*70}", flush=True)


def constat_1_permissions(token):
    titre(1, "Permissions portées par le jeton (/debug_token)")
    try:
        resp = ig_api._request(
            "GET", f"{ig_api.GRAPH_HOST}/debug_token",
            params={"input_token": token, "access_token": token},
        )
        data = ig_api._raise_for_api_error(resp, "debug_token").get("data", {})
    except ig_api.IgApiError as exc:
        # Non fatal : debug_token demande parfois un jeton d'app. Le vrai juge
        # reste l'étape 3.
        print(f"  indisponible — {exc}")
        print("  (non bloquant : l'étape 3 tranche pour de bon)")
        return None

    scopes = data.get("scopes") or []
    print(f"  type       : {data.get('type')}")
    print(f"  app_id     : {data.get('application')} ({data.get('app_id')})")
    expire = data.get("expires_at")
    print(f"  expire     : {'jamais' if expire in (0, None) else expire}")
    print(f"  valide     : {data.get('is_valid')}")
    print(f"\n  {len(scopes)} permission(s) :")
    for s in sorted(scopes):
        marque = " <-- publication de contenu" if s == "instagram_content_publish" else ""
        print(f"    - {s}{marque}")

    if "instagram_content_publish" in scopes:
        print("\n  VERDICT : instagram_content_publish est présent. C'est la MÊME")
        print("  permission que pour les Reels et les carrousels — l'API Graph n'a")
        print("  pas de scope distinct pour les stories.")
    else:
        print("\n  VERDICT : instagram_content_publish ABSENT de la liste.")
    return scopes


def constat_2_quota(ig_user, token):
    titre(2, "Quota de publication (/content_publishing_limit)")
    resp = ig_api._request(
        "GET", f"{GRAPH}/{ig_user}/content_publishing_limit",
        params={"fields": "config,quota_usage", "access_token": token},
    )
    payload = ig_api._raise_for_api_error(resp, "content_publishing_limit")
    entries = payload.get("data") or []
    if not entries:
        print(f"  réponse vide : {payload}")
        return
    for e in entries:
        conf = e.get("config") or {}
        print(f"  quota_usage        : {e.get('quota_usage')}")
        print(f"  quota_total        : {conf.get('quota_total')}")
        print(f"  fenêtre (secondes) : {conf.get('quota_duration')}")
    print("\n  Ce compteur est celui de TOUT le compte. Si les stories API le")
    print("  consomment, elles mangent le même plafond que LIGNE et les carrousels.")
    print("  Relever ce chiffre AVANT et APRÈS une vraie publication est la seule")
    print("  façon de le prouver — d'où le --publish, plus tard et sur ta décision.")


def constat_3_conteneur(ig_user, token, image_url):
    titre(3, "Conteneur STORIES (dry-run — création puis ARRÊT)")
    print(f"  image de test : {image_url}")

    resp = ig_api._request(
        "POST", f"{GRAPH}/{ig_user}/media",
        data={"media_type": "STORIES", "image_url": image_url, "access_token": token},
    )
    try:
        payload = ig_api._raise_for_api_error(resp, "Conteneur STORIES")
    except ig_api.IgApiError as exc:
        texte = str(exc)
        print(f"\n  ÉCHEC : {texte}")
        bas = texte.lower()
        if "aspect ratio" in bas or "ratio" in bas or "size" in bas or "dimension" in bas:
            print("\n  LECTURE : refus sur le MÉDIA, pas sur le droit. L'appel STORIES a")
            print("  donc été autorisé. Le jeton peut publier une story ; il faut juste")
            print("  lui donner du 1080x1920.")
        elif "oauth" in bas or "permission" in bas or "(#10)" in bas or "(#200)" in bas:
            print("\n  LECTURE : refus sur le DROIT. Le jeton ne porte pas la permission")
            print("  de publier une story. Il faut le ré-autoriser côté Meta.")
        else:
            print("\n  LECTURE : à qualifier à la main — l'erreur n'est ni un ratio ni un droit.")
        return None

    container_id = payload.get("id")
    print(f"  conteneur créé : {container_id}")

    deadline = time.time() + POLL_TIMEOUT
    while time.time() < deadline:
        status = ig_api.get_status(container_id)
        print(f"    statut : {status}", flush=True)
        if status in (ig_api.STATUS_FINISHED, ig_api.STATUS_PUBLISHED):
            print(f"\n  VERDICT : conteneur STORIES accepté et {status}.")
            print("  Tout le chemin est validé SAUF le media_publish final.")
            print("  Le conteneur n'est PAS publié et expire seul sous 24 h.")
            return container_id
        if status in (ig_api.STATUS_ERROR, ig_api.STATUS_EXPIRED):
            print(f"\n  VERDICT : conteneur en {status} — Meta a refusé le média.")
            return None
        time.sleep(POLL_INTERVAL)
    print(f"\n  VERDICT : toujours pas FINISHED après {POLL_TIMEOUT}s.")
    return None


def constat_4_publication(container_id):
    titre(4, "PUBLICATION RÉELLE (--publish)")
    print("  Une story visible 24 h va partir sur @kongrave_.")
    media_id = ig_api.publish(container_id)
    print(f"\n  PUBLIÉ — media_id={media_id}")
    print("  VERDICT : le jeton publie des stories. Preuve complète.")
    return media_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-url", default=DEFAULT_IMAGE)
    ap.add_argument("--publish", action="store_true",
                    help="publie VRAIMENT la story de test (défaut : non)")
    args = ap.parse_args()

    token = ig_api._access_token()
    ig_user = ig_api._ig_user_id()
    print(f"[probe] compte Instagram {ig_user} — Graph {ig_api.GRAPH_VERSION}")
    print(f"[probe] mode : {'PUBLICATION RÉELLE' if args.publish else 'DRY-RUN'}")

    constat_1_permissions(token)
    constat_2_quota(ig_user, token)
    container_id = constat_3_conteneur(ig_user, token, args.image_url)

    if args.publish:
        if not container_id:
            sys.exit("\n[probe] --publish demandé mais aucun conteneur valide — rien publié.")
        constat_4_publication(container_id)
        print("\n[probe] quota APRÈS publication :")
        constat_2_quota(ig_user, token)

    print("\n[probe] terminé.")


if __name__ == "__main__":
    main()
