# Décisions de conception — Sentarr

## Général

| Sujet | Décision | Justification |
|-------|----------|---------------|
| Nom du projet | **Sentarr** | Remplace `PlexTaskMon` du cahier des charges initial. |
| Stack backend | Python 3.12 + FastAPI + SQLModel | Familier, bonne performance, ORM léger compatible PostgreSQL. |
| Stack frontend | React + Vite + TypeScript + PWA | Standard, léger, thème sombre *arr, installable sur mobile/bureau. |
| Base de données V1 | SQLite par défaut, PostgreSQL possible via `DATABASE_URL` | Usage mono-utilisateur en V1 ; volumétrie des logs/events peut justifier PostgreSQL plus tard. |
| Auth V1 | Aucune (protection réseau/Traefik/Authelia) | KISS, pas de données utilisateurs. |
| Auth V3 | Mode similaire à Radarr/Sonarr : `none`, `forms` (JWT), `external` (header HTTP) | Pour l'ouverture communautaire et le multi-utilisateur. |
| Notifications V2 | Webhook générique | Minimum viable. |
| Notifications V3 | Apprise Python | Couvre la très large liste de canaux demandée. |
| Export métriques V3 | Endpoint `/metrics` au format Prometheus + dashboards Grafana | Monitoring compatible avec l'infrastructure existante. |
| Clients de téléchargement V2+ | Abstraction `DownloadClientConnector` (qBittorrent, Transmission, etc.) | Affiner la progression et l'état natif. |
| PWA V1 | Application installable avec service worker et manifeste | Mode hors-ligne partiel et accès mobile/bureau. |
| Polling Plex API | Toutes les 60 secondes par défaut | Réactif sans surcharger Plex. |
| Log tail | 5 secondes | Lecture continue avec `watchdog`. |
| Rétro-scan | `true` par défaut | L'utilisateur souhaite importer l'état existant. |
| Bibliothèques | Toutes les bibliothèques `movie`/`show` découvertes | Pas de filtre manuel. |
| Tâches non applicables | Gérées via `not_applicable` | Affichage conditionnel selon Plex Pass et contexte. |
| API versionnée V2+ | `/api/v1/arr/...` + `/api/v1/health` | Compatibilité *arr sans casser `/api/movies`/`/api/shows`. |
| Client *arr | `ArrClient` read-only, uniquement `GET` | Aucun appel d'écriture vers Radarr/Sonarr. |
| Modèles *arr | Classes `ArrMovie`, `ArrSeries`, `ArrEpisode`, `QualityProfile`, `RootFolder` | Tables SQL au pluriel ; clé `(source_id, external_id)`. |
| Corrélation *arr ↔ Plex | Par chemin normalisé ; état `unmatched` explicite | Ne jamais inventer un lien. |
| Instances *arr | Multi-instance avec `profile_label` | Badge qualité ex: `1080p`, `4K`. |
| Structure code | `backend/sentarr/{api/v1,clients,models,schemas,services}` | Aligné sur les conventions *arr. |

## Modèle Films / Séries

| Sujet | Décision |
|-------|----------|
| Séparation | Tables distinctes `movies`/`movie_tasks` et `shows`/`seasons`/`episodes`/`show_tasks`/`season_tasks`/`episode_tasks`. |
| Agrégation | Statut d'une saison dérivé de ses épisodes. Statut d'une série dérivé de ses saisons + de ses `show_tasks`. |
| Propagation | Uniquement ascendante (épisodes → saison → série). Le statut d'un parent n'affecte jamais ses enfants. |
| Progression | Pourcentage calculé à partir du ratio de tâches `completed` / total applicable. |

## Déploiement

| Sujet | Décision |
|-------|----------|
| Hôte principal | Unraid (`192.168.100.133`). |
| Réseau Docker | `plex-backend` (même que Plex). |
| Exposition | `sentarr.drac-lab.fr` via Traefik Unraid, middleware `private-network`. |
| Image | Backend + frontend dans un seul conteneur multi-stage. |
| Healthcheck | Endpoint `/health` interne. |

## Interface utilisateur

| Sujet | Décision |
|-------|----------|
| Thème | Sombre façon *arr (Radarr/Sonarr/Bazarr). |
| Erreurs | Message simplifié dans l'interface + accès au log brut en un clic. |
| Tâches en cours | Indicateur de chargement rond/spinner sur l'item concerné. |
| Vue Séries | Arborescence dépliable sans changement de page. |
| Recherche | Cross-domaine films + séries. |

## Talos

| Sujet | Décision |
|-------|----------|
| Rôle | Génération de morceaux isolés uniquement. |
| Réessai | Jusqu'à 3 tentatives par job. |
| Continuité | Un échec n'empêche pas d'utiliser Talos sur les jobs suivants. |
| Vérification | Tout résultat est relu et validé manuellement avant intégration. |

## Questions de cadrage V1 — réponses utilisateur

1. **Accès Plex** : infos récupérées via Atlas/SSH Unraid (voir `operations.md`).
2. **Bibliothèques** : toutes automatiquement.
3. **Fréquence/rétention** : laissé au choix technique → 60s polling, 30j rétention par défaut, ajustable via env.
4. **Rétro-scan** : complet.
5. **Déploiement** : `sentarr.drac-lab.fr`, SQLite V1 avec migration PostgreSQL possible.
6. **Interface** : thème sombre *arr, log brut accessible.
7. **Tâches non applicables** : détection Plex Pass pour activer/désactiver les marqueurs intro.

## Questions de cadrage V2 — réponses utilisateur

1. **Scope V2** : connecteurs Radarr/Sonarr développés après la V1, sauf si nécessaire au bon fonctionnement de la V1.
2. **Instances** : multi-instance avec badge qualité (`profile_label` ex: `1080p`, `4K`).
3. **URLs/clés** : extraites via SSH Unraid/Atlas et passées par variables d'environnement.
4. **Seuils d'alerte** :
   - Recherche bloquée (`searched`) : 60 min.
   - Téléchargement bloqué (`downloading`) : 30 min.
   - Import bloqué (`importing`) : 15 min.
   - Traitement Plex bloqué (`overall`) : 60 min.
5. **Canal de notification V2** : webhook générique.
6. **Historique alertes résolues** : conservées 90 jours.
7. **Score de santé** : par item + indicateur global agrégé sur le dashboard.
8. **Clients de téléchargement** : abstraction `DownloadClientConnector` supportant qBittorrent, Transmission et autres clients courants pour affiner la progression.

## Questions de cadrage V3 — réponses utilisateur

1. **Priorités** : tous les blocs A–G souhaités à terme.
2. **Intégrations Bazarr/Prowlarr** : Prowlarr en V3, Bazarr en V3.
3. **Rétention events bruts** : 90 jours avant agrégation/purge.
4. **PostgreSQL** : pas obligatoire en V1 ; ORM compatible pour migration future.
5. **Multi-serveur Plex** : prioritaire en V3.
6. **Authelia** : optionnel côté Sentarr ; mode `external` disponible en V3.
7. **Rôles** : 2 rôles (`admin`, `readonly`).
8. **Notifications** : grande variété de canaux via Apprise.
9. **Export métriques** : Prometheus `/metrics` + dashboards Grafana. Home Assistant hors scope.
10. **PWA** : oui, dès la V1.
11. **Publication communautaire** : oui en V3 avec doc anglaise et template Unraid CA.
