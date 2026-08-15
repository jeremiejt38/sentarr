# Modèle de données Sentarr

## Principes généraux

- Les domaines **Films** et **Séries** sont séparés : `movies`/`movie_tasks` vs `shows`/`seasons`/`episodes`/`show_tasks`/`season_tasks`/`episode_tasks`.
- Les tâches portent sur l'objet qu'elles décrivent (`movie_tasks` pour les films, `episode_tasks` pour les épisodes).
- Les tâches de niveau série/saison (`show_tasks`, `season_tasks`) concernent les métadonnées/artworks propres à ces niveaux hiérarchiques.
- Les statuts agrégés saison/série sont stockés ou calculés à la volée selon la volumétrie (à décider lors de l'implémentation, voir `decisions.md`).
- L'historique des événements bruts est conservé dans `log_events_raw`.

## Tables V1

### `libraries`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | Identifiant interne |
| `plex_library_id` | int | `librarySectionID` de Plex |
| `name` | str | Nom de la bibliothèque |
| `type` | enum | `movie` ou `show` |
| `created_at` | datetime | Date de première découverte |
| `updated_at` | datetime | Dernière synchronisation |

### `movies` (domaine Films, modèle plat)

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | Identifiant interne |
| `plex_rating_key` | int | `ratingKey` Plex |
| `library_id` | FK | Bibliothèque parente |
| `title` | str | Titre du film |
| `year` | int | Année (optionnel) |
| `file_path` | str | Chemin du fichier sur le disque |
| `added_at` | datetime | Date d'ajout selon Plex |

### `movie_tasks`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `movie_id` | FK | Film concerné |
| `task_type` | enum | `scan`, `identification`, `metadata`, `artwork`, `bif`, `intro_markers`, `chapters`, `streams`, `overall` |
| `status` | enum | `pending`, `in_progress`, `completed`, `error`, `not_applicable` |
| `progress_percent` | int nullable | 0–100 si applicable |
| `started_at` | datetime nullable | — |
| `completed_at` | datetime nullable | — |
| `error_message` | str nullable | Message d'erreur ou contexte |
| `last_checked_at` | datetime | Dernière mise à jour |

### `shows` (domaine Séries)

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | Identifiant interne |
| `plex_rating_key` | int | `ratingKey` Plex |
| `library_id` | FK | Bibliothèque parente |
| `title` | str | Titre de la série |
| `year` | int | Année (optionnel) |
| `added_at` | datetime | Date d'ajout selon Plex |

### `show_tasks`

Tâches propres à la série elle-même (identification/métadonnées/artworks de la série).

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `show_id` | FK | Série concernée |
| `task_type` | enum | `identification`, `metadata`, `artwork_show` |
| `status` | enum | `pending`, `in_progress`, `completed`, `error`, `not_applicable` |
| `started_at`, `completed_at`, `error_message` | — | Idem `movie_tasks` |

### `seasons`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `show_id` | FK | Série parente |
| `plex_rating_key` | int | `ratingKey` Plex |
| `season_number` | int | Numéro de saison |

### `season_tasks`

Tâches propres à la saison (artwork saison, métadonnées saison rares).

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `season_id` | FK | Saison concernée |
| `task_type` | enum | `artwork_season`, `metadata_season` |
| `status` | enum | `pending`, `in_progress`, `completed`, `error`, `not_applicable` |

### `episodes`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `season_id` | FK | Saison parente |
| `plex_rating_key` | int | `ratingKey` Plex |
| `episode_number` | int | Numéro d'épisode |
| `title` | str | Titre de l'épisode |
| `file_path` | str | Chemin du fichier |
| `added_at` | datetime | Date d'ajout |

### `episode_tasks`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `episode_id` | FK | Épisode concerné |
| `task_type` | enum | `scan`, `identification`, `metadata`, `artwork`, `bif`, `intro_markers`, `chapters`, `streams`, `overall` |
| `status` | enum | `pending`, `in_progress`, `completed`, `error`, `not_applicable` |
| `progress_percent` | int nullable | 0–100 |
| `started_at`, `completed_at`, `error_message`, `last_checked_at` | — | Idem `movie_tasks` |

### `log_events_raw`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `timestamp` | datetime | Horodatage de la ligne de log |
| `raw_line` | str | Ligne brute du log |
| `parsed` | bool | `true` si un pattern a reconnu la ligne |
| `parsed_event_type` | str nullable | Type d'événement reconnu |
| `correlated_to_type` | str nullable | `movie`, `show`, `season`, `episode` |
| `correlated_to_id` | int nullable | ID interne Sentarr |

## Tables V2

### `external_sources`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `type` | enum | `radarr`, `sonarr`, `bazarr` (V3), custom |
| `instance_name` | str | Nom d'affichage |
| `base_url` | str | URL interne de l'instance |
| `api_key_ref` | str | Nom de la variable d'environnement contenant la clé |
| `profile_label` | str nullable | Badge qualité, ex: `1080p`, `4K` |

### `acquisition_items`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `source_id` | FK | `external_sources` |
| `external_id` | str | ID externe (Radarr/Sonarr) |
| `movie_id` | FK nullable | Lien vers `movies` si film |
| `episode_id` | FK nullable | Lien vers `episodes` si épisode |
| `file_path_target` | str nullable | Chemin final attendu après import |
| `created_at` | datetime | — |

### `acquisition_events`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `acquisition_item_id` | FK | Item d'acquisition |
| `step` | enum | `searched`, `release_found`, `grabbed`, `downloading`, `completed`, `imported` |
| `timestamp` | datetime | — |
| `progress_percent` | int nullable | — |
| `extra_data` | JSON nullable | Détails contextuels |

### `health_scores`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `acquisition_item_id` | FK nullable | — |
| `movie_id` | FK nullable | — |
| `episode_id` | FK nullable | — |
| `score` | int | 0–100 |
| `last_calculated_at` | datetime | — |
| `reason` | str | Raison du score |

### `alert_rules`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `name` | str | Nom de la règle |
| `pipeline_step` | enum | `all` ou étape spécifique |
| `threshold_minutes` | int | Seuil de déclenchement |
| `enabled` | bool | — |
| `applies_to` | enum | `acquisition`, `plex`, `both` |

### `alerts_active`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `rule_id` | FK | Règle déclenchée |
| `target_type` | str | `movie`, `episode`, `acquisition_item` |
| `target_id` | int | ID de la cible |
| `triggered_at` | datetime | — |
| `resolved_at` | datetime nullable | — |

## Tables V3

Voir `phases.md` pour le détail. Tables additionnelles : `subtitle_events`, `indexer_status`, `analytics_snapshots`, `plex_servers`, `users`, `plugins`.

## Agrégation des statuts

### Saison

Dérivée de ses épisodes :
- `completed` : tous les épisodes sont `completed`.
- `error` : au moins un épisode est `error` (même si d'autres sont prêts).
- `in_progress` : au moins un épisode est `in_progress`.
- `pending` : sinon, au moins un `pending`.
- `not_applicable` : tous `not_applicable`.

### Série

Dérivée de ses saisons + des tâches de niveau série (`show_tasks`) :
- `error` si un `show_task` est `error` OU si une saison est `error`.
- `in_progress` si un `show_task` est `in_progress` OU si une saison est `in_progress`.
- `completed` si tout est `completed`.
- Affichage visuel : "87 % prêt — 7/8 saisons complètes".

## Indexes recommandés

- `movies(plex_rating_key)`, `shows(plex_rating_key)`, `seasons(plex_rating_key)`, `episodes(plex_rating_key)`
- `log_events_raw(timestamp, parsed)`
- `movie_tasks(movie_id, task_type)`, `episode_tasks(episode_id, task_type)`
- `acquisition_items(source_id, external_id)`
