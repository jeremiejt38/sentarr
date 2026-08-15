# Configuration Sentarr

## Mécanisme de configuration

Toute la configuration passe par des **variables d'environnement**. Aucun fichier de config complexe en V1. En V2/V3, on pourra ajouter un fichier YAML optionnel pour les règles d'alertes.

## Variables obligatoires V1

| Variable | Description | Exemple |
|----------|-------------|---------|
| `PLEX_URL` | URL interne du serveur Plex | `http://plex:32400` |
| `PLEX_TOKEN` | Token d'accès Plex (PlexOnlineToken) | `xxxxxxxxxxxxxxxxxxxx` |
| `PLEX_LOG_PATH` | Chemin hôte du fichier de log Plex (monté en lecture seule) | `/mnt/user/appdata/plex/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log` |

## Variables optionnelles V1

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL SQLAlchemy de la base | `sqlite:///./data/sentarr.db` |
| `LOG_LEVEL` | Niveau de log de l'application | `INFO` |
| `POLL_INTERVAL_SECONDS` | Intervalle de polling de l'API Plex | `60` |
| `LOG_TAIL_INTERVAL_SECONDS` | Fréquence de lecture du log Plex | `5` |
| `HISTORY_RETENTION_DAYS` | Durée de rétention des tâches terminées | `30` |
| `RETRO_SCAN` | Importer l'état des items existants au démarrage | `true` |
| `LIBRARIES_FILTER` | Liste de noms de bibliothèques à surveiller (vide = toutes) | `""` |
| `PLEX_PASS_ENABLED` | Détection/activation des tâches Plex Pass (marqueurs intro) | `auto` |
| `HOST` | Interface d'écoute du backend | `0.0.0.0` |
| `PORT` | Port d'écoute du backend | `8000` |

## Variables V2 — Instances *arr

Les instances Radarr/Sonarr sont configurées par objets structurés. Les secrets (clés API) sont référencés par le nom de leur variable d'environnement, jamais en clair.

| Variable | Description |
|----------|-------------|
| `RADARR_URLS` | JSON : `[{"name":"radarr-1080p","url":"http://radarr:7878","api_key_env":"RADARR_1080P_API_KEY","profile_label":"1080p"}]` |
| `SONARR_URLS` | Idem pour Sonarr |
| `RADARR_1080P_API_KEY`, `SONARR_1080P_API_KEY`, etc. | Clés API réelles, passées par env |
| `ARR_POLL_INTERVAL_SECONDS` | Intervalle de polling R/S | `60` |
| `STALL_THRESHOLD_MINUTES` | Seuil de détection de blocage acquisition | `30` |
| `WEBHOOK_URL` | URL webhook générique pour les alertes | — |

## Variables V3

| Variable | Description | Défaut |
|----------|-------------|--------|
| `BAZAAR_URLS` | JSON des instances Bazarr | `[]` |
| `PROWLARR_URLS` | JSON des instances Prowlarr | `[]` |
| `AUTH_MODE` | `none`, `forms`, `external` | `none` |
| `NOTIFICATION_CHANNELS` | Configuration Apprise ou webhooks | `[]` |
| `METRICS_ENABLED` | Activer l'endpoint Prometheus `/metrics` | `false` |
| `METRICS_PORT` | Port d'exposition des métriques (si distinct) | `8000` |
| `METRICS_PATH` | Chemin des métriques | `/metrics` |
| `ANALYTICS_RETENTION_DAYS` | Rétention des événements bruts avant agrégation | `90` |

## Détection de Plex Pass

- `PLEX_PASS_ENABLED=auto` : Sentarr tente de détecter si le compte/serveur bénéficie de Plex Pass via l'API Plex. Si oui, les tâches `intro_markers` sont affichées. Sinon, elles sont marquées `not_applicable`.
- `PLEX_PASS_ENABLED=true/false` : forçage manuel.

## Fichier `.env.example`

```bash
# Plex
PLEX_URL=http://plex:32400
PLEX_TOKEN=change_me
PLEX_LOG_PATH=/var/log/plex/Plex Media Server.log

# Application
DATABASE_URL=sqlite:///./data/sentarr.db
LOG_LEVEL=INFO
POLL_INTERVAL_SECONDS=60
LOG_TAIL_INTERVAL_SECONDS=5
HISTORY_RETENTION_DAYS=30
RETRO_SCAN=true
LIBRARIES_FILTER=
PLEX_PASS_ENABLED=auto

# API backend
HOST=0.0.0.0
PORT=8000

# ------------------------------------------------------------------
# Acquisition — Radarr / Sonarr (V2)
# ------------------------------------------------------------------
# Format JSON : [{"name":"radarr-1080p","url":"http://radarr:7878","api_key_env":"RADARR_1080P_API_KEY","profile_label":"1080p"}]
RADARR_URLS=[]
SONARR_URLS=[]
# Clés API correspondant aux valeurs de api_key_env ci-dessus
# RADARR_1080P_API_KEY=change_me
# SONARR_1080P_API_KEY=change_me
ARR_POLL_INTERVAL_SECONDS=60
STALL_THRESHOLD_MINUTES=30
WEBHOOK_URL=

# ------------------------------------------------------------------
# Notifications multi-canaux (V3)
# ------------------------------------------------------------------
# Format JSON Apprise : [{"name":"discord","url":"discord://...","events":["alert_triggered"]}]
NOTIFICATION_CHANNELS=[]

# ------------------------------------------------------------------
# Authentification (V3)
# ------------------------------------------------------------------
# none | forms | external
AUTH_MODE=none

# ------------------------------------------------------------------
# Métriques Prometheus / Grafana (V3)
# ------------------------------------------------------------------
METRICS_ENABLED=false
METRICS_PORT=8000
METRICS_PATH=/metrics
ANALYTICS_RETENTION_DAYS=90
```

## Secrets

Les tokens et clés API ne doivent **jamais** être versionnés. Ils seront passés via `.env` ou un gestionnaire de secrets (Docker secrets en V2+).
