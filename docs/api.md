# API Sentarr

## Généralités

- API REST + WebSocket temps réel.
- Tous les endpoints sont **en lecture seule** en V1.
- Authentification V1 : aucune (protection par réseau / Traefik / Authelia).
- V3 : versionnement explicite `/api/v1/` et documentation OpenAPI/Swagger.

## Base URL

```
https://sentarr.drac-lab.fr/api
ws://sentarr.drac-lab.fr/ws   (upgrade vers WebSocket)
```

## Endpoints V1

### Synthèse globale

```
GET /api/summary
```

Réponse :

```json
{
  "movies": {"pending": 0, "in_progress": 3, "completed": 1240, "error": 2, "not_applicable": 0},
  "shows": {"pending": 1, "in_progress": 5, "completed": 86, "error": 0, "not_applicable": 0},
  "active_alerts": 2,
  "oldest_in_progress": [...],
  "unparsed_log_lines_count": 47
}
```

### Films

```
GET /api/movies
GET /api/movies/{id}
```

Paramètres `GET /api/movies` :
- `library_id` (int)
- `status` (`pending|in_progress|completed|error|not_applicable`)
- `q` (texte libre sur titre)

Réponse `GET /api/movies` :

```json
{
  "items": [
    {
      "id": 1,
      "plex_rating_key": 12345,
      "library_id": 2,
      "title": "Inception",
      "year": 2010,
      "file_path": "/mnt/user/plex/data/movies/Inception (2010)/...",
      "added_at": "2026-08-14T10:00:00Z",
      "overall_status": "in_progress",
      "progress_percent": 67,
      "tasks": [
        {"task_type": "scan", "status": "completed", "started_at": "...", "completed_at": "..."},
        {"task_type": "identification", "status": "completed", ...},
        {"task_type": "bif", "status": "in_progress", "progress_percent": 45, ...}
      ]
    }
  ]
}
```

### Séries

```
GET /api/shows
GET /api/shows/{id}
GET /api/shows/{id}/seasons/{number}
GET /api/shows/{id}/seasons/{number}/episodes/{number}
```

Réponse `GET /api/shows/{id}` :

```json
{
  "id": 10,
  "plex_rating_key": 50001,
  "library_id": 3,
  "title": "Breaking Bad",
  "overall_status": "in_progress",
  "progress_percent": 87,
  "summary": "8/8 saisons complètes — 22/24 épisodes en cours",
  "seasons": [
    {
      "season_number": 1,
      "overall_status": "completed",
      "progress_percent": 100,
      "completed_episodes": 7,
      "total_episodes": 7,
      "episodes": [...]
    }
  ],
  "show_tasks": [...]
}
```

### Recherche cross-domaine

```
GET /api/search?q=breaking
```

Réponse : films + séries correspondants.

### Logs bruts (lecture)

```
GET /api/logs/unparsed?limit=50&offset=0
GET /api/logs/events?target_type=movie&target_id=1
```

## WebSocket `/ws`

Événements poussés au frontend :

```json
{"type": "task_update", "payload": {"target_type": "episode", "target_id": 42, "task_type": "bif", "status": "completed"}}
{"type": "summary_update", "payload": {"movies": {...}, "shows": {...}}}
{"type": "new_alert", "payload": {...}}
```

Le frontend s'abonne en ouvrant la connexion WebSocket. Pas de topic complexe en V1.

## Endpoints V2

### Acquisition

```
GET /api/acquisition
GET /api/acquisition/{id}
GET /api/acquisition/{id}/timeline
```

Paramètres `GET /api/acquisition` :
- `source_id`
- `status`
- `instance_name`

Réponse : items en cours d'acquisition avec statut, progression, health score.

### Alertes

```
GET /api/alerts
GET /api/alerts/{id}
```

### Health scores

```
GET /api/health/{type}/{id}   # type = movie, episode, acquisition_item
```

## Endpoints V3

### Authentification (si auth interne)

```
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

### API publique documentée

```
GET /api/v1/openapi.json
GET /api/v1/docs
```

## Codes d'erreur

- `200 OK` : succès.
- `404 Not Found` : ressource inconnue.
- `500 Internal Server Error` : erreur interne, loggée côté serveur.

Les réponses d'erreur utilisent le schéma Pydantic `HTTPError` avec `detail`.
