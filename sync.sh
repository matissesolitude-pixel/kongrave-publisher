#!/usr/bin/env bash
#
# sync.sh — Pousse les .mp4 finis + schedule.json du Mac vers le VPS.
#
# Tourne sur le Mac. Le VPS publie ensuite tout seul via cron_publisher.py.
#
# Usage :
#   ./sync.sh                 # utilise les valeurs par défaut ci-dessous / l'env
#   VPS_HOST=user@1.2.3.4 ./sync.sh
#
# Prérequis : clé SSH configurée vers le VPS (ssh user@host doit passer sans mot de passe).
#
# NE SYNCHRONISE JAMAIS .env.local ni output/ : le token vit uniquement sur le VPS,
# et les logs se produisent côté VPS.

set -euo pipefail

# --- Config (surchargée par l'environnement) ---------------------------------
VPS_HOST="${VPS_HOST:-}"                       # ex : deploy@203.0.113.10
VPS_DIR="${VPS_DIR:-~/kongrave-publisher}"     # dossier cible sur le VPS
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "$VPS_HOST" ]]; then
  echo "Erreur : définis VPS_HOST (ex : VPS_HOST=deploy@203.0.113.10 ./sync.sh)" >&2
  exit 1
fi

echo "→ Synchronisation vers ${VPS_HOST}:${VPS_DIR}"

# 1) Les vidéos de inbox/ (grosses, on garde --archive + compression désactivée pour mp4).
rsync -av --progress \
  --exclude '.gitkeep' \
  "${LOCAL_DIR}/inbox/" \
  "${VPS_HOST}:${VPS_DIR}/inbox/"

# 2) Le planning.
rsync -av \
  "${LOCAL_DIR}/schedule.json" \
  "${VPS_HOST}:${VPS_DIR}/schedule.json"

echo "✓ Sync terminée. Le VPS publiera aux dates prévues dans schedule.json."
