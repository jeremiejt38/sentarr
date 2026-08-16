# Déploiement Sentarr

## Cible principale

- Serveur **Unraid** (`192.168.100.133`), conteneur Docker unique ou stack `docker-compose`.
- Réseau Docker : `plex-backend` (même réseau que Plex, Radarr, Sonarr, etc.).
- Exposition privée via Traefik : `sentarr.drac-lab.fr`.
- Pas d'ouverture WAN directe.

## Prérequis

- Accès au serveur Unraid via SSH.
- `PLEX_TOKEN` disponible.
- Volume monté en lecture seule vers le log Plex.
- Traefik déjà en place avec le provider Docker et le middleware `private-network`.

## Docker Compose (V1)

```yaml
services:
  sentarr:
    image: sentarr:latest
    container_name: sentarr
    restart: unless-stopped
    networks:
      - plex-backend
    environment:
      - PLEX_URL=http://plex:32400
      - PLEX_TOKEN=${PLEX_TOKEN}
      - DATABASE_URL=sqlite:///app/data/sentarr.db
      - POLL_INTERVAL_SECONDS=60
      - LOG_TAIL_INTERVAL_SECONDS=5
      - HISTORY_RETENTION_DAYS=30
      - RETRO_SCAN=true
      - LOG_LEVEL=INFO
      - HOST=0.0.0.0
      - PORT=8000
    volumes:
      - /mnt/user/appdata/sentarr/data:/app/data
      - /mnt/user/appdata/plex/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log:/var/log/plex/Plex Media Server.log:ro
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.sentarr.rule=Host(`sentarr.drac-lab.fr`)"
      - "traefik.http.routers.sentarr.entrypoints=http,https"
      - "traefik.http.routers.sentarr.priority=1000"
      - "traefik.http.routers.sentarr.middlewares=private-network"
      - "traefik.http.services.sentarr.loadbalancer.server.port=8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

networks:
  plex-backend:
    external: true
```

## Construction de l'image

```bash
docker build -t sentarr:latest -f docker/Dockerfile .
```

Ou en mode développement :

```bash
docker compose -f docker/docker-compose.dev.yml up --build
```

## Dockerfile (V1, backend + frontend)

```dockerfile
# Étape 1 — build du frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Étape 2 — backend Python
FROM python:3.12-slim AS backend
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-builder /app/frontend/dist ./static
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "sentarr.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Intégration Unraid

### Méthode 1 — User Scripts + docker-compose

1. Placer le `docker-compose.yml` et le `.env` dans `/mnt/user/appdata/sentarr/`.
2. Créer un User Script "Sentarr" qui exécute `docker compose up -d`.
3. Optionnel : ajouter au démarrage automatique d'Unraid.

### Méthode 2 — Template Community Applications (V3+)

A ready-to-use Unraid CA template is provided as `unraid-template.xml`. Import it from the CA interface or use the URL:

```
https://raw.githubusercontent.com/jeremiejt38/sentarr/main/unraid-template.xml
```

Variables : `PLEX_TOKEN`, `PLEX_LOG_PATH`, `POLL_INTERVAL_SECONDS`, `RADARR_URLS`, `SONARR_URLS`, `DOWNLOAD_CLIENTS`, etc.

## Intégration Traefik

Aucune configuration statique nécessaire si le provider Docker est actif et que les labels ci-dessus sont appliqués. Le wildcard `*.drac-lab.fr` est déjà géré par OPNsense Unbound.

Redémarrage de Traefik si nécessaire :

```bash
ssh unraid "docker restart traefik"
```

## Commandes utiles

```bash
# Logs de Sentarr
ssh unraid "docker logs -f sentarr"

# Redémarrer
ssh unraid "docker restart sentarr"

# Vérifier la santé
ssh unraid "docker exec sentarr curl -s http://localhost:8000/health"
```

## Scalabilité V2/V3

- Si la base SQLite devient trop lourde (événements bruts + analytics), migrer vers PostgreSQL via `DATABASE_URL`.
- Le docker-compose V3 ajoutera un service `sentarr-postgres`.

## Considérations de sécurité

- `PLEX_TOKEN` en variable d'environnement, jamais dans l'image.
- Log Plex monté en lecture seule (`:ro`).
- Pas de binding du port applicatif sur l'hôte ; tout passe par Traefik.
- Pas d'exposition WAN : `sentarr.drac-lab.fr` résout localement via OPNsense.
