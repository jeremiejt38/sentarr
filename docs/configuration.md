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

## Variables V2

| Variable | Description |
|----------|-------------|
| `RADARR_URLS` | JSON des instances Radarr : `[{"name":"radarr-1080p","url":"http://radarr:7878","api_key_env":"RADARR_1080P_API_KEY","profile_label":"1080p"}]` |
| `SONARR_URLS` | Idem pour Sonarr |
| `ACQUISITION_POLL_INTERVAL_SECONDS` | Intervalle de polling R/S |
| `STALL_THRESHOLD_MINUTES` | Seuil de détection de blocage acquisition |
| `WEBHOOK_URL` | URL webhook générique pour les alertes |

## Variables V3

| Variable | Description |
|----------|-------------|
| `BAZAAR_URLS` | JSON des instances Bazarr |
| `PROWLARR_URLS` | JSON des instances Prowlarr |
| `AUTH_MODE` | `none`, `forms`, `external` |
| `NOTIFICATION_CHANNELS` | Configuration Apprise ou webhooks |
| `HOME_ASSISTANT_URL` | URL de l'instance Home Assistant |
| `HOME_ASSISTANT_TOKEN` | Long-lived access token |

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
```

## Secrets

Les tokens et clés API ne doivent **jamais** être versionnés. Ils seront passés via `.env` ou un gestionnaire de secrets (Docker secrets en V2+).
