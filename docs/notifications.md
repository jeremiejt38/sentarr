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

## Home Assistant

Deux options pour exposer Sentarr à Home Assistant :

### Option A — REST générique (recommandée en V3)

Endpoint dédié exposant les valeurs au format attendu par Home Assistant (ou JSON générique interprété par une intégration REST) :

```
GET /api/home-assistant/sensors
```

Exemple :

```json
{
  "sentarr_movies_in_progress": 3,
  "sentarr_movies_error": 1,
  "sentarr_shows_in_progress": 5,
  "sentarr_active_alerts": 2
}
```

### Option B — MQTT

Publication périodique sur des topics MQTT :

```
sentarr/summary/movies_in_progress → 3
sentarr/summary/movies_error → 1
sentarr/alerts/active → 2
```

À activer si l'utilisateur dispose d'un broker MQTT.

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
