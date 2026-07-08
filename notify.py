"""
notify.py — Notification Telegram après chaque publication.

Un seul point d'entrée : send(message). Un échec de notification ne doit JAMAIS
faire échouer une publication : on log l'erreur et on continue.

Config (dans .env.local, à côté de ce fichier) :
  TELEGRAM_BOT_TOKEN  — token du bot (créé via @BotFather)
  TELEGRAM_CHAT_ID    — id du chat/destinataire
Si l'un des deux manque, send() devient un no-op silencieux (avec un warning stderr).
"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env.local")

TELEGRAM_API = "https://api.telegram.org"
REQUEST_TIMEOUT = 15


def send(message: str) -> bool:
    """Envoie un message Telegram. Retourne True si envoyé, False sinon (jamais d'exception)."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(
            "[notify] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID absent — notification ignorée.",
            file=sys.stderr,
        )
        return False

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    try:
        resp = requests.post(
            url,
            data={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code >= 400:
            print(f"[notify] Telegram HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
            return False
        return True
    except requests.RequestException as exc:
        print(f"[notify] Envoi Telegram impossible : {exc}", file=sys.stderr)
        return False


if __name__ == "__main__":
    # Test manuel : python notify.py "message de test"
    msg = sys.argv[1] if len(sys.argv) > 1 else "Test notify.py — KONGRAVE publisher ✅"
    ok = send(msg)
    print("Envoyé." if ok else "Non envoyé (voir warning ci-dessus).")
