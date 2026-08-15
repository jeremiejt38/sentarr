# Stratégie de notifications Sentarr

## Principe général

Les notifications sont déclenchées par le moteur d'alertes. Elles ne concernent initialement que les alertes de dépassement de seuil et les blocages détectés. En V3, les notifications peuvent couvrir davantage d'événements (tâche terminée, nouvelle saison ajoutée, etc.).

## V2 — Webhook générique

En V2, une URL webhook configurable (`WEBHOOK_URL`) permet de brancher un canal existant (n8n, Discord via un intermédiaire, etc.). Le payload est un JSON standardisé.

### Payload webhook

```json
{
  "event": "alert_triggered",
  "alert_id": 12,
  "rule": {
    "name": "Téléchargement bloqué > 30 min",
    "pipeline_step": "downloading",
    "threshold_minutes": 30
  },
  "target": {
    "type": "acquisition_item",
    "id": 45,
    "title": "Inception (2010)",
    "source": "radarr-4k"
  },
  "message": "Le téléchargement d'Inception (2010) est bloqué depuis 35 minutes.",
  "url": "https://sentarr.drac-lab.fr/acquisition/45",
  "timestamp": "2026-08-15T10:30:00Z"
}
```

## V3 — Notifications multi-canaux via Apprise

Pour répondre au besoin d'une grande variété de canaux, Sentarr V3 utilisera la bibliothèque Python **Apprise** comme couche d'abstraction. Apprise supporte nativement Discord, Telegram, Matrix, Slack, Mattermost, XMPP/Jabber, ntfy, Pushover, Pushbullet, Gotify, Boxcar, email SMTP, Twilio, et de nombreux webhooks.

### Avantages

- Un seul code d'envoi côté backend.
- L'utilisateur configure les canaux via URLs Apprise (une par canal).
- Support d'Apprise directement dans Python sans dépendances externes.

### Configuration V3

Variable d'environnement `NOTIFICATION_CHANNELS` :

```bash
NOTIFICATION_CHANNELS='[
  {"name": "discord", "url": "discord://webhook_id/webhook_token", "events": ["alert_triggered"]},
  {"name": "ntfy", "url": "ntfy://ntfy.drac-lab.fr/sentarr", "events": ["alert_triggered", "alert_resolved"]},
  {"name": "email", "url": "mailtos://user:pass@gmail.com", "events": ["alert_triggered"]}
]'
```

### Types d'événements notifiables

- `alert_triggered`
- `alert_resolved`
- `task_completed` (optionnel)
- `new_season_detected` (optionnel)
- `summary_daily` (optionnel)

## Export Prometheus / Grafana (V3)

Sentarr expose des métriques au format Prometheus pour être scrapé par Prometheus et visualisé dans Grafana.

### Endpoint

```
GET /metrics
```

### Métriques prévues

| Métrique | Type | Description |
|----------|------|-------------|
| `sentarr_movies_total` | gauge | Nombre total de films |
| `sentarr_movies_status{status="..."}` | gauge | Nombre de films par statut |
| `sentarr_shows_total` | gauge | Nombre total de séries |
| `sentarr_shows_status{status="..."}` | gauge | Nombre de séries par statut |
| `sentarr_episodes_total` | gauge | Nombre total d'épisodes |
| `sentarr_episodes_status{status="..."}` | gauge | Nombre d'épisodes par statut |
| `sentarr_active_alerts` | gauge | Nombre d'alertes actives |
| `sentarr_plex_api_poll_duration_seconds` | histogram | Durée du polling API Plex |
| `sentarr_log_lines_unparsed_total` | counter | Lignes de log non reconnues |

### Dashboards Grafana

Plusieurs dashboards pré-configurés seront fournis dans `grafana/dashboards/` :
- Vue globale (films + séries + alertes).
- Vue acquisition (downloads, stall).
- Vue santé par bibliothèque.

### Configuration

Variables d'environnement (V3) :

```bash
METRICS_ENABLED=true
METRICS_PORT=9090
METRICS_PATH=/metrics
```

## Règles d'alertes (V2)

- Règles configurables par étape et seuil de temps.
- Résolution automatique dès que la situation se débloque.
- Évaluation déclenchée par le recalcul du score de santé.

### Règles par défaut proposées

| Nom | Étape | Seuil | Description |
|-----|-------|-------|-------------|
| Recherche bloquée | `searched` | 60 min | Aucune release trouvée après 1h de recherche |
| Téléchargement bloqué | `downloading` | 30 min | Progression nulle depuis 30 min |
| Import bloqué | `importing` | 15 min | Item terminé mais non importé depuis 15 min |
| Traitement Plex bloqué | `overall` (Plex) | 60 min | Item détecté mais non prêt depuis 1h |

Les seuils sont configurables et désactivables.

## Sécurité

- Les tokens/credentials de notification passent par les variables d'environnement ou Docker secrets.
- Aucune clé API n'est stockée en base ou dans le code versionné.
