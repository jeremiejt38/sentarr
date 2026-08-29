#!/bin/bash
# Test Sentarr sur une seule bibliotheque Plex sans toucher au container Plex.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

ENV_FILE=".env.staging"

if [ ! -f "$ENV_FILE" ]; then
    echo "Fichier $ENV_FILE manquant. Copie .env.staging.example vers $ENV_FILE et remplis PLEX_TOKEN."
    exit 1
fi

echo "=== Sentarr staging — test sur une bibliotheque ==="
echo "Assure-toi que PLEX_TOKEN et LIBRARIES_FILTER sont bien definis dans $ENV_FILE"
echo ""

mkdir -p data-staging
docker compose -f docker-compose.staging.yml down 2>/dev/null || true
docker compose -f docker-compose.staging.yml up --build -d

echo ""
echo "Container demarre sur http://<ip>:8001"
echo "Suivi des logs : docker logs -f sentarr-staging"
echo "Arret : docker compose -f docker-compose.staging.yml down"
