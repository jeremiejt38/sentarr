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

## Tables V2 — Intégration *arr

Principes :
- `id` est toujours l'identifiant interne Sentarr.
- `(source_id, external_id)` est la clé d'unicité pour une ressource provenant d'une instance *arr.
- `RootFolder` et `QualityProfile` sont des **snapshots de référence** : la source reste Radarr/Sonarr.
- Aucun modèle d'acquisition n'autorise une mutation distante.
- `Movie` et `Show` peuvent être reliés à leur équivalent Plex par `plex_movie_id`/`plex_show_id`, sans confondre leurs identifiants.

### `external_sources`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `type` | enum | `radarr`, `sonarr`, `bazarr` (V3), custom |
| `name` | str | Nom d'affichage, unique par installation |
| `base_url` | str | URL interne de l'instance (sans secret) |
| `api_version` | str | ex. `v3` |
| `api_key_ref` | str | Nom de la variable d'environnement contenant la clé |
| `profile_label` | str nullable | Badge qualité, ex: `1080p`, `4K` |
| `enabled` | bool | défaut `true` |
| `created_at`, `updated_at` | datetime | — |

### `quality_profiles`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `source_id` | FK | instance propriétaire |
| `external_id` | int | ID du profil source |
| `name` | str | ex: `HD-1080p` |
| `cutoff_quality` | str nullable | qualité cible |
| `items` | JSON | qualités autorisées, ordre et poids |
| `updated_at` | datetime | dernier snapshot |

Contrainte : `UNIQUE(source_id, external_id)`.

### `root_folders`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `source_id` | FK | instance propriétaire |
| `external_id` | int nullable | ID source si fourni |
| `path` | str | chemin racine canonique |
| `free_space_bytes` | int nullable | dernier état connu |
| `accessible` | bool | dernier état connu |
| `updated_at` | datetime | — |

Contrainte : `UNIQUE(source_id, path)`.

### `arr_movies` (équivalent Radarr `movie`)

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | identifiant Sentarr |
| `source_id` | FK | instance Radarr |
| `external_id` | int | `movie.id` Radarr |
| `title` | str | titre affiché |
| `year` | int nullable | année |
| `tmdb_id`, `imdb_id` | str nullable | identifiants externes |
| `monitored` | bool | snapshot |
| `has_file` | bool | snapshot |
| `path` | str nullable | chemin item |
| `root_folder_id` | FK nullable | racine associée |
| `quality_profile_id` | FK nullable | profil associé |
| `plex_movie_id` | FK nullable | corrélation Sentarr |
| `updated_at` | datetime | — |

Contrainte : `UNIQUE(source_id, external_id)`.

### `arr_series` (équivalent Sonarr `series`)

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | identifiant Sentarr |
| `source_id` | FK | instance Sonarr |
| `external_id` | int | `series.id` Sonarr |
| `title` | str | titre |
| `year` | int nullable | année |
| `tvdb_id`, `imdb_id`, `tvmaze_id` | str nullable | identifiants externes |
| `monitored` | bool | snapshot |
| `path` | str nullable | chemin série |
| `root_folder_id`, `quality_profile_id` | FK nullable | références |
| `plex_show_id` | FK nullable | corrélation Plex |
| `updated_at` | datetime | — |

### `arr_episodes`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `series_id` | FK | `arr_series` |
| `external_id` | int | ID Sonarr |
| `season_number`, `episode_number` | int | position |
| `title` | str nullable | titre |
| `air_date` | date nullable | date de diffusion |
| `has_file` | bool | snapshot |
| `path` | str nullable | chemin fichier |
| `plex_episode_id` | FK nullable | corrélation Plex |

Contrainte : `UNIQUE(series_id, external_id)`.

### `acquisition_items`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `source_id` | FK | `external_sources` |
| `external_id` | str | ID queue/history ou clé stable |
| `target_type` | enum | `movie`, `series`, `episode` |
| `target_id` | FK nullable | `arr_movies`/`arr_series`/`arr_episodes` |
| `status` | enum | `queued`, `downloading`, `completed`, `imported`, `failed`, `unmatched` |
| `progress_percent` | int nullable | 0–100 |
| `download_id` | str nullable | ID client, non secret |
| `path` | str nullable | chemin observé |
| `profile_label` | str nullable | badge UI |
| `created_at`, `updated_at` | datetime | — |

Contrainte : `UNIQUE(source_id, external_id)`.

### `acquisition_events`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `acquisition_item_id` | FK | Item d'acquisition |
| `step` | enum | `searched`, `release_found`, `grabbed`, `downloading`, `completed`, `imported`, `plex_detected` |
| `timestamp` | datetime | — |
| `progress_percent` | int nullable | — |
| `source_event_id` | str nullable | ID de l'événement source |
| `extra_data` | JSON nullable | Détails contextuels |

### Schémas d'ingestion (Pydantic)

```python
from datetime import datetime
from pydantic import BaseModel, Field

class QueueItem(BaseModel):
    id: int | str
    title: str
    status: str
    tracked_download_status: str | None = None
    size: float | None = None
    sizeleft: float | None = None
    progress: float | None = Field(default=None, ge=0, le=100)
    output_path: str | None = None

class HistoryEvent(BaseModel):
    id: int | str
    event_type: str
    source_id: int | None = None
    movie_id: int | None = None
    series_id: int | None = None
    episode_id: int | None = None
    date: datetime
    data: dict[str, object] = {}
```

Les champs absents selon la version d'instance restent optionnels ; l'ingestion valide puis journalise les champs inconnus sans interrompre le polling.

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

### `subtitle_events` (Bloc A — Bazarr)

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `movie_id` | FK nullable | Lien film si applicable |
| `episode_id` | FK nullable | Lien épisode si applicable |
| `language` | str | Langue demandée (ex: `fra`, `eng`) |
| `status` | enum | `pending`, `searching`, `found`, `missing`, `error` |
| `provider` | str nullable | Fournisseur de sous-titres |
| `timestamp` | datetime | Date de l'événement |

### `indexer_status` (Bloc B — Prowlarr)

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `indexer_name` | str | Nom de l'indexeur |
| `health` | enum | `healthy`, `degraded`, `failing` |
| `last_checked_at` | datetime | Dernier contrôle |

### `analytics_snapshots` (Bloc C — Analytics)

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `period_start` | datetime | Début de la période |
| `period_end` | datetime | Fin de la période |
| `avg_duration_by_step` | JSON | Durée moyenne par étape, par domaine |
| `anomalies` | JSON | Liste des anomalies détectées |
| `scope` | enum | `movie`, `episode`, `acquisition` |

### `plex_servers` (Bloc D — Multi-serveur)

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `name` | str | Nom du serveur |
| `base_url` | str | URL d'accès |
| `token_ref` | str | Nom de la variable d'environnement contenant le token |

Ajout d'une colonne `plex_server_id` sur `libraries`, `movies` et `shows`.

### `users` (Bloc E — Auth multi-utilisateur)

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `username` | str | Nom d'utilisateur |
| `role` | enum | `admin`, `readonly` |
| `auth_ref` | str nullable | Référence externe (hash mot de passe, identifiant SSO, etc.) |

### `plugins` (Bloc G — Système de plugins)

| Champ | Type | Description |
|-------|------|-------------|
| `id` | PK int | — |
| `name` | str | Nom du plugin |
| `type` | str | Type de connecteur (`acquisition`, `log_parser`, etc.) |
| `config` | JSON | Configuration spécifique |
| `enabled` | bool | Actif ou non |

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

```sql
CREATE UNIQUE INDEX uq_external_source_name ON external_sources(name);
CREATE UNIQUE INDEX uq_quality_profile_source_external ON quality_profiles(source_id, external_id);
CREATE UNIQUE INDEX uq_root_folder_source_path ON root_folders(source_id, path);
CREATE UNIQUE INDEX uq_arr_movie_source_external ON arr_movies(source_id, external_id);
CREATE UNIQUE INDEX uq_arr_series_source_external ON arr_series(source_id, external_id);
CREATE UNIQUE INDEX uq_arr_episode_series_external ON arr_episodes(series_id, external_id);
CREATE UNIQUE INDEX uq_acquisition_source_external ON acquisition_items(source_id, external_id);
CREATE INDEX ix_arr_movies_path ON arr_movies(path);
CREATE INDEX ix_arr_episodes_path ON arr_episodes(path);
CREATE INDEX ix_acquisition_status ON acquisition_items(status, updated_at);
CREATE INDEX ix_movies_plex_rating_key ON movies(plex_rating_key);
CREATE INDEX ix_shows_plex_rating_key ON shows(plex_rating_key);
CREATE INDEX ix_seasons_plex_rating_key ON seasons(plex_rating_key);
CREATE INDEX ix_episodes_plex_rating_key ON episodes(plex_rating_key);
CREATE INDEX ix_log_events_raw ON log_events_raw(timestamp, parsed);
CREATE INDEX ix_movie_tasks ON movie_tasks(movie_id, task_type);
CREATE INDEX ix_episode_tasks ON episode_tasks(episode_id, task_type);
```

Les chemins sont normalisés avant comparaison (séparateurs, slash final, casse selon le filesystem). En cas d'échec de corrélation, conserver l'état `unmatched` et ne jamais inventer un lien Plex.
