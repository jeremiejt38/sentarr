# Sentarr — Statut des phases de developpement

> Derniere mise a jour : 2026-08-29. Genere apres audit complet du code (96 tests, ruff/mypy clean, frontend build OK).
> Referentiel : `docs/phases.md`.

## V1 — Pipeline Plex Films/Series

| Phase | Intitule | Statut | Details |
|-------|----------|--------|---------|
| 0 | Cadrage | DONE | `docs/architecture.md`, `cadrage-questions.md`, `decisions.md` complets. |
| 1 | Socle technique | DONE | pyproject.toml, package.json, Dockerfile, plex_api.py, models/plex.py. docker-compose sous `docker/`. |
| 2 | Modele Series | DONE | Show/Season/Episode models, RETRO_SCAN=true. |
| 3 | Parseur de logs | **PARTIAL** | `plex_log_parser.py` complet (regex, dedup, correlation). **Manque** : `plex_log_tail.py` est un alias, pas un vrai tail temps reel (re-parse l'ensemble a chaque intervalle). |
| 4 | Moteur de correlation | **PARTIAL** | Correlation par ratingKey/path OK, _update_task OK. **Manque** : aggregation persistee de `overall_status`/`progress_percent` des parents (Season/Show) depuis les enfants. Le calcul existe en memoire (`health/score.py`) mais n'est pas ecrit en base. |
| 5 | API backend | DONE | Routers movies, shows, search, summary, websocket tous wires dans main.py. |
| 6 | Frontend | DONE | SummaryPage, MoviesPage, ShowsPage, AcquisitionPage, SettingsPage, Timeline. WebSocket rafraichit automatiquement les pages de donnees via un evenement global. |
| 7 | Gestion erreurs | DONE | `health/anomalies.py` (doublons + mal identifies), mode degrade Plex, SQLAlchemyJobStore. |
| 8 | Packaging final | **PARTIAL** | Dockerfile multi-stage, docker-compose, .env.example, docs/deployment.md. **Manque** : pas de docker-compose.yml racine, pas de fichier Traefik dedie, reference a `docker-compose.dev.yml` inexistant dans deployment.md. |
| 9 | Validation | **PARTIAL** | CI GitHub Actions, 96 tests backend. **Manque** : deploiement reel sur Unraid non fait, tests frontend limites. |

**Score V1 : 6/10 DONE, 4/10 PARTIAL, 0 NOT STARTED**

---

## V2 — Chaine d'acquisition Radarr/Sonarr

| Phase | Intitule | Statut | Details |
|-------|----------|--------|---------|
| 0 | Cadrage V2 | DONE | cadrage-questions.md V2 complet. |
| 1 | Client *arr read-only | **PARTIAL** | ArrClient (GET, timeout, retry), radarr.py, sonarr.py OK. **Manque** : pas de methodes `get_quality_profiles()` / `get_root_folders()` ; les tables QualityProfile/RootFolder existent mais ne sont jamais peuplees. |
| 2 | Modeles et persistance | DONE | ArrInstance, AcquisitionItem, AcquisitionEvent, Alert, QualityProfile, RootFolder + migrations Alembic. |
| 3 | Sync queue + history | DONE | `arr_sync.py` lit queue + history, dedup sur (source_id, external_id). |
| 4 | Correlation acq-plex | DONE | `_correlate_unmatched` par path normalise, delai import-to-detect dans `/api/v1/health/delays`. |
| 5 | Download clients | **PARTIAL** | qBittorrent + Transmission + abstraction OK. **Manque** : pas de liaison entre les torrents actifs et les items *arr (progress_percent non affine depuis le download client). |
| 6 | Score de sante | DONE | `health/score.py` calcul 0-100 par item + global, seuils configurables, affiche dans les listes et le health endpoint. |
| 7 | Alertes | **PARTIAL** | Moteur `alerts/engine.py` + API OK. **Manque** : les regles referent des statuts `searched`/`importing` que le modele d'acquisition ne produit jamais ; webhook V2 generique non implemente (remplace par Apprise V3). |
| 8 | Frontend Acquisition | DONE | AcquisitionPage avec pipeline unifie 16 etapes, delai import-to-detect. |
| 9 | Validation | DONE | Tests arr_client, alert_thresholds, health_score, api_endpoints. |

**Score V2 : 7/10 DONE, 3/10 PARTIAL, 0 NOT STARTED**

---

## V3 — Extensions

| Phase | Intitule (Bloc) | Statut | Details |
|-------|-----------------|--------|---------|
| 0 | Cadrage V3 | DONE | cadrage-questions.md V3, phases.md. |
| 1 | Bazarr (A) | DONE | BazarrClient, bazarr_sync, SubtitleTrack model, /api/v1/subtitles. |
| 2 | Prowlarr (B) | DONE | ProwlarrClient, /api/v1/indexers + /stats. |
| 3 | Analytics (C) | DONE | Snapshots periodiques, detection d'anomalies (2-sigma), purge anciens log events. |
| 4 | Multi-serveur/PostgreSQL (D) | DONE | PlexServerConfig, CRUD /api/v1/servers, multi-server JSON, docker-compose.postgres.yml. |
| 5 | Auth / API publique (E) | **PARTIAL** | User model (bcrypt), JWT login, RBAC (admin/user/readonly), ApiKey model + middleware. **Manque** : le mode `forms` dans AuthMiddleware ne valide pas reellement les credentials (`verify_credentials` defini mais jamais appele) ; pas d'UI de login frontend. |
| 6 | Notifications (F1) | DONE | Apprise multi-canaux, /api/v1/notifications/test, config JSON. |
| 7 | Prometheus/Grafana (F2) | DONE | /metrics endpoint, 5 metriques custom, dashboard Grafana 10 panels, Prometheus dans docker-compose. |
| 8 | Ouverture communautaire (G) | DONE | README_EN.md, systeme de plugins (SentarrPlugin + PluginManager + 7 hooks), docs/plugins.md, unraid-template.xml. |
| 9 | Validation finale | **NOT STARTED** | Deploiement complet en conditions reelles non fait. |

**Score V3 : 8/10 DONE, 1/10 PARTIAL, 1 NOT STARTED**

---

## Synthese globale

| Version | DONE | PARTIAL | NOT STARTED | Total |
|---------|------|---------|-------------|-------|
| V1 | 6 | 4 | 0 | 10 |
| V2 | 7 | 3 | 0 | 10 |
| V3 | 8 | 1 | 1 | 10 |
| **Total** | **21** | **8** | **1** | **30** |

**Completion : 21/30 phases DONE (70 %), 8 PARTIAL (27 %), 1 NOT STARTED (3 %)**

---

## Elements restants a traiter (par priorite)

### Priorite haute (fonctionnalite core incomplete)

1. **V1-P4 : Aggregation parent** — Apres mise a jour d'une tache film/episode, propager `overall_status` et `progress_percent` vers le parent (Movie depuis MovieTask, Season depuis Episodes, Show depuis Seasons) et persister en base.
2. **V1-P3 : Vrai tail de log** — Remplacer le re-parse complet par un suivi d'offset (ou watchdog) pour ne traiter que les nouvelles lignes.
3. **V2-P7 : Alignement statuts alertes** — Les regles `searched`/`importing` ne matchent aucun statut reel. Corriger les noms ou emettre les bons statuts.

### Priorite moyenne (packaging et UX)

4. **V1-P8 : Packaging** — Ajouter un `docker-compose.yml` racine (ou symlink), creer `docker-compose.dev.yml`, corriger la ref dans deployment.md.
5. **V3-P5 : Auth forms** — Connecter `verify_credentials` dans AuthMiddleware ou supprimer le mode `forms` ; ajouter une page de login frontend.
6. **V1-P6 : WebSocket live refresh** — Les events `sync_complete` sont broadcastes mais le frontend ne les utilise pas pour rafraichir les donnees.
7. **V2-P1 : Quality profiles / root folders** — Ajouter les appels API et la synchronisation en base.

### Priorite basse (polish)

8. **V2-P5 : Liaison download clients <-> acq** — Mapper les torrents actifs aux items *arr pour affiner progress_percent.
9. **V1-P9 / V3-P9 : Validation reelle** — Deployer sur Unraid et tester avec la bibliotheque complete.
10. **Tests frontend** — Ajouter des tests pour les pages principales (SummaryPage, MoviesPage, ShowsPage).
