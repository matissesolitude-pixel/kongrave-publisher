"""
ig_api.py — Client bas niveau pour l'Instagram Content Publishing API (Graph API).

Une seule responsabilité : parler à l'API Graph. Aucune logique de planning ici.

Flux d'un Reel avec fichier local (resumable upload) :
  1. create_container(mp4, caption)  -> POST /{ig-user}/media (upload_type=resumable)
                                        puis upload binaire vers rupload.facebook.com
  2. get_status(container_id)        -> GET /{container}?fields=status_code
  3. publish(container_id)           -> POST /{ig-user}/media_publish

Le token n'est JAMAIS écrit en clair : il est chargé depuis .env.local (à côté de ce
fichier) via python-dotenv. Voir .env.example.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env.local")

GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v20.0")
GRAPH_HOST = "https://graph.facebook.com"
UPLOAD_HOST = "https://rupload.facebook.com"

# Statuts renvoyés par le conteneur média.
STATUS_FINISHED = "FINISHED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_ERROR = "ERROR"
STATUS_EXPIRED = "EXPIRED"
STATUS_PUBLISHED = "PUBLISHED"

# Réglages réseau.
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5  # 5s, 10s, 15s (linéaire, largement suffisant ici)
REQUEST_TIMEOUT = 60


class IgApiError(RuntimeError):
    """Erreur remontée par l'API Graph ou par le protocole d'upload."""


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise IgApiError(
            f"Variable d'environnement manquante : {name}. "
            f"Renseigne-la dans {BASE_DIR / '.env.local'} (voir .env.example)."
        )
    return value


def _ig_user_id() -> str:
    return _require_env("INSTAGRAM_BUSINESS_ACCOUNT_ID")


def _access_token() -> str:
    return _require_env("META_ACCESS_TOKEN")


def _is_retryable(status_code: int) -> bool:
    # 429 (rate limit transitoire) + 5xx (panne serveur Meta) = on retente.
    return status_code == 429 or 500 <= status_code < 600


def _request(method: str, url: str, **kwargs) -> requests.Response:
    """Requête HTTP avec retry 3x + backoff sur erreurs réseau / 429 / 5xx."""
    last_exc: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
        except requests.RequestException as exc:  # DNS, timeout, connexion coupée…
            last_exc = exc
            if attempt == MAX_RETRIES:
                break
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)
            continue

        if _is_retryable(resp.status_code) and attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)
            continue
        return resp

    raise IgApiError(f"Échec réseau après {MAX_RETRIES} tentatives : {last_exc}")


def _raise_for_api_error(resp: requests.Response, context: str) -> dict:
    """Renvoie le JSON, ou lève IgApiError avec le message d'erreur Meta."""
    try:
        payload = resp.json()
    except ValueError:
        payload = {}
    if resp.status_code >= 400 or "error" in payload:
        err = payload.get("error", {})
        message = err.get("message", resp.text)
        raise IgApiError(f"{context} — HTTP {resp.status_code} : {message}")
    return payload


def create_container(mp4_path: Path, caption: str, trial_params: Optional[dict] = None) -> str:
    """
    Crée un conteneur Reel puis y téléverse le fichier local (resumable upload).
    Retourne le container_id (creation_id à publier ensuite).

    trial_params : si fourni (ex. {"graduation_strategy": "MANUAL"}), le Reel est
    créé en mode ESSAI — visible uniquement des NON-abonnés. MANUAL = il ne passe
    aux abonnés que sur action manuelle dans l'app ; SS_PERFORMANCE = promotion auto
    s'il performe. Absent -> Reel normal (comportement inchangé).
    """
    mp4_path = Path(mp4_path)
    if not mp4_path.is_file():
        raise IgApiError(f"Fichier introuvable : {mp4_path}")
    file_size = mp4_path.stat().st_size
    token = _access_token()

    # 1) Réservation du conteneur.
    init_url = f"{GRAPH_HOST}/{GRAPH_VERSION}/{_ig_user_id()}/media"
    init_data = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "access_token": token,
    }
    if trial_params:
        # objet JSON-encodé attendu par l'API Graph (Trial Reels)
        init_data["trial_params"] = json.dumps(trial_params)
    init_resp = _request(
        "POST",
        init_url,
        data=init_data,
    )
    payload = _raise_for_api_error(init_resp, "Création du conteneur")
    container_id = payload.get("id")
    if not container_id:
        raise IgApiError(f"Réponse sans id de conteneur : {payload}")

    # 2) Upload binaire du .mp4 vers l'endpoint resumable.
    upload_url = f"{UPLOAD_HOST}/ig-api-upload/{GRAPH_VERSION}/{container_id}"
    with mp4_path.open("rb") as fh:
        up_resp = _request(
            "POST",
            upload_url,
            headers={
                "Authorization": f"OAuth {token}",
                "offset": "0",
                "file_size": str(file_size),
            },
            data=fh,
        )
    up_payload = _raise_for_api_error(up_resp, "Upload du fichier")
    if not up_payload.get("success", False):
        raise IgApiError(f"Upload non confirmé par Meta : {up_payload}")

    return container_id


def get_status(container_id: str) -> str:
    """Retourne le status_code du conteneur (FINISHED / IN_PROGRESS / ERROR / EXPIRED / PUBLISHED)."""
    url = f"{GRAPH_HOST}/{GRAPH_VERSION}/{container_id}"
    resp = _request(
        "GET",
        url,
        params={"fields": "status_code", "access_token": _access_token()},
    )
    payload = _raise_for_api_error(resp, "Lecture du statut")
    return payload.get("status_code", "UNKNOWN")


def publish(container_id: str) -> str:
    """Publie le conteneur. Retourne le media_id Instagram."""
    url = f"{GRAPH_HOST}/{GRAPH_VERSION}/{_ig_user_id()}/media_publish"
    resp = _request(
        "POST",
        url,
        data={"creation_id": container_id, "access_token": _access_token()},
    )
    payload = _raise_for_api_error(resp, "Publication")
    media_id = payload.get("id")
    if not media_id:
        raise IgApiError(f"Réponse sans media_id : {payload}")
    return media_id


def post_comment(media_id: str, message: str) -> str:
    """Poste un commentaire sur un média publié. Retourne l'id du commentaire.
    Requiert la permission instagram_manage_comments sur le token."""
    url = f"{GRAPH_HOST}/{GRAPH_VERSION}/{media_id}/comments"
    resp = _request(
        "POST",
        url,
        data={"message": message, "access_token": _access_token()},
    )
    payload = _raise_for_api_error(resp, "Commentaire")
    comment_id = payload.get("id")
    if not comment_id:
        raise IgApiError(f"Réponse sans id de commentaire : {payload}")
    return comment_id
