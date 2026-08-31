# Sentarr — Statut des phases de developpement

> Derniere mise a jour : 2026-08-30. Genere apres audit complet du code (100 tests backend, tests frontend, ruff/mypy clean, frontend build OK, staging Unraid healthy).
> Referentiel : `docs/phases.md`.

## V1 — Pipeline Plex Films/Series

| Phase | Intitule | Statut | Details |
|-------|----------|--------|---------|
| 0 | Cadrage | DONE | `docs/architecture.md`, `cadrage-questions.md`, `decisions.md` complets. |
| 1 | Socle technique | DONE | pyproject.toml, package.json, Dockerfile, plex_api.py, models/plex.py. docker-compose sous `docker/`. |
| 2 | Modele Series | DONE | Show/Season/Episode models, RETRO_SCAN=true. |
| 3 | Parseur de logs | DONE | `plex_log_parser.py` suit l'offset par fichier (`LogFileState`) et reprend la ou il s'est arrete ; gestion de la rotation par taille. |
| 4 | Moteur de correlation | DONE | Correlation par ratingKey/path, propagation persistante de `overall_status`/`progress_percent` vers les parents (MovieTask, Season, Show). |
| 5 | API backend | DONE | Routers movies, shows, search, summary, websocket tous wires dans main.py. |
| 6 | Frontend | DONE | SummaryPage, MoviesPage, ShowsPage, AcquisitionPage, SettingsPage, Timeline. WebSocket rafraichit automatiquement les pages de donnees via un evenement global. |
| 7 | Gestion erreurs | DONE | `health/anomalies.py` (doublons + mal identifies), mode degrade Plex, SQLAlchemyJobStore. |
| 8 | Packaging final | DONE | Dockerfile multi-stage, `docker-compose.yml` racine, `docker-compose.dev.yml`, `docker-compose.staging.yml`, `docker-compose.postgres.yml`, dossiers `traefik/`, `prometheus/`, `grafana/`, `.env.example`, docs/deployment.md. |
| 9 | Validation | **PARTIAL** | Deploiement staging sur Unraid OK, 100 tests backend, tests frontend pages principales. Validation comportementale lancee sur la bibliotheque Plex reelle (bibliotheque "Emissions TV"). **Manque** : validation sur l'ensemble des bibliotheques + chaine Radarr/Sonarr en conditions reelles. |

**Score V1 : 9/10 DONE, 1/10 PARTIAL, 0 NOT STARTED**

---

## V2 — Chaine d'acquisition Radarr/Sonarr

| Phase | Intitule | Statut | Details |
|-------|----------|--------|---------|
| 0 | Cadrage V2 | DONE | cadrage-questions.md V2 complet. |
| 1 | Client *arr read-only | DONE | ArrClient (GET, timeout, retry), radarr.py, sonarr.py, `sync_quality_profiles()` / `sync_root_folders()` peuplent les tables associees. |
| 2 | Modeles et persistance | DONE | ArrInstance, AcquisitionItem, AcquisitionEvent, Alert, QualityProfile, RootFolder + migrations Alembic. |
| 3 | Sync queue + history | DONE | `arr_sync.py` lit queue + history, dedup sur (source_id, external_id). |
| 4 | Correlation acq-plex | DONE | `_correlate_unmatched` par path normalise, delai import-to-detect dans `/api/v1/health/delays`. |
| 5 | Download clients | DONE | qBittorrent + Transmission + abstraction OK. Liaison par `download_id` (hash du torrent) ou fallback titre ; `download_progress` synchronise dans `acquisition_items` a chaque sync *arr et affiche dans le frontend. |
| 6 | Score de sante | DONE | `health/score.py` calcul 0-100 par item + global, seuils configurables, affiche dans les listes et le health endpoint. |
| 7 | Alertes | DONE | Moteur `alerts/engine.py` aligne les seuils `searched`/`downloading`/`importing` sur les statuts reels du modele (`monitored`, `grabbed`/`downloading`, `imported`) ; API / WebSocket alertes fonctionnels. |
| 8 | Frontend Acquisition | DONE | AcquisitionPage avec pipeline unifie 16 etapes, delai import-to-detect. |
| 9 | Validation | DONE | Tests arr_client, alert_thresholds, health_score, api_endpoints. |

**Score V2 : 10/10 DONE, 0 PARTIAL, 0 NOT STARTED**

---

## V3 — Extensions

| Phase | Intitule (Bloc) | Statut | Details |
|-------|-----------------|--------|---------|
| 0 | Cadrage V3 | DONE | cadrage-questions.md V3, phases.md. |
| 1 | Bazarr (A) | DONE | BazarrClient, bazarr_sync, SubtitleTrack model, /api/v1/subtitles. |
| 2 | Prowlarr (B) | DONE | ProwlarrClient, /api/v1/indexers + /stats. |
| 3 | Analytics (C) | DONE | Snapshots periodiques, detection d'anomalies (2-sigma), purge anciens log events. |
| 4 | Multi-serveur/PostgreSQL (D) | DONE | PlexServerConfig, CRUD /api/v1/servers, multi-server JSON, docker-compose.postgres.yml. |
| 5 | Auth / API publique (E) | DONE | User model (bcrypt), JWT login (`/api/v1/users/login`), RBAC admin/user, page de login frontend, middleware Bearer + cookie, routes protegees. |
| 6 | Notifications (F1) | DONE | Apprise multi-canaux, /api/v1/notifications/test, config JSON. |
| 7 | Prometheus/Grafana (F2) | DONE | /metrics endpoint, 5 metriques custom, dashboard Grafana 10 panels, Prometheus dans docker-compose. |
| 8 | Ouverture communautaire (G) | DONE | README_EN.md, systeme de plugins (SentarrPlugin + PluginManager + 7 hooks), docs/plugins.md, unraid-template.xml. |
| 9 | Validation finale | **PARTIAL** | Deploiement staging Unraid OK, health check / Traefik passent. Validation avec bibliotheque Plex reelle en cours (module V1). **Manque** : validation chaine d'acquisition et extensions V2/V3 en conditions reelles. |

**Score V3 : 9/10 DONE, 1/10 PARTIAL, 0 NOT STARTED**

---

## Synthese globale

| Version | DONE | PARTIAL | NOT STARTED | Total |
|---------|------|---------|-------------|-------|
| V1 | 9 | 1 | 0 | 10 |
| V2 | 10 | 0 | 0 | 10 |
| V3 | 9 | 1 | 0 | 10 |
| **Total** | **28** | **2** | **0** | **30** |

**Completion : 28/30 phases DONE (93 %), 2 PARTIAL (7 %), 0 NOT STARTED (0 %)**

---

## Retours de validation (2026-08-31)

Le redeploiement sur la bibliotheque Plex reelle a mis en lumiere et permis de corriger deux problemes de concurrence/stabilité :

1. **Scheduler bloquant l'event loop** — Les syncs synchrones tournaient sur la boucle asyncio, bloquant l'API et les autres jobs. Corrige en delestant chaque sync dans un thread via `asyncio.to_thread`.
2. **Contention SQLite (`database is locked`)** — Apres la mise en threads, le job store APScheduler et les workers syncs ecrivaient concurremment sur la meme base SQLite. Corrige par :
   - activation du mode WAL et `busy_timeout=30s` sur le moteur SQLite ;
   - isolation du job store APScheduler dans une base dediee ;
   - serialisation des syncs planifies par un `asyncio.Lock` pour eviter deux transactions d'ecriture simultanees.
3. **Propagation parent/enfant** — `_propagate_all` dans le sync Plex propagait les shows puis les saisons puis les episodes, ce qui faisait heriter les saisons d'une valeur de progression obsolete (ex. 82% alors que tous les episodes etaient `pending`). Corrige en propagant les feuilles (films/episodes) avant les parents (saisons/shows).

Le conteneur `sentarr-staging` est stable (memoire ~180MiB, CPU < 1% entre les syncs, pas d'erreur `database is locked`).

---

## Elements restants a traiter (par priorite)

### Priorite haute

Aucun element critique identifie. Toutes les phases documentees V1/V2/V3 sont implementees, testees et deployees en staging.

### Priorite basse (polish / validation)

1. **V1-P9 / V3-P9 : Validation reelle** — Valider le comportement avec la bibliotheque Plex/Radarr/Sonarr complete sur Unraid et decider du passage en production. Pour le moment seule la bibliotheque "Emissions TV" est active en staging ; les instances Radarr/Sonarr ne sont pas configurees dans `.env.staging`.
