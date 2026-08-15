# Décisions de conception — Sentarr

## Général

| Sujet | Décision | Justification |
|-------|----------|---------------|
| Nom du projet | **Sentarr** | Remplace `PlexTaskMon` du cahier des charges initial. |
| Stack backend | Python 3.12 + FastAPI + SQLModel | Familier, bonne performance, ORM léger compatible PostgreSQL. |
| Stack frontend | React + Vite + TypeScript | Standard, léger, thème sombre *arr. |
| Base de données V1 | SQLite par défaut, PostgreSQL possible via `DATABASE_URL` | Usage mono-utilisateur en V1 ; volumétrie des logs/events peut justifier PostgreSQL plus tard. |
| Auth V1 | Aucune (protection réseau/Traefik/Authelia) | KISS, pas de données utilisateurs. |
| Auth V3 | Mode similaire à Radarr/Sonarr : `none`, `forms` (JWT), `external` (header HTTP) | Pour l'ouverture communautaire et le multi-utilisateur. |
| Notifications V2 | Webhook générique | Minimum viable. |
| Notifications V3 | Apprise Python | Couvre la très large liste de canaux demandée. |
| Polling Plex API | Toutes les 60 secondes par défaut | Réactif sans surcharger Plex. |
| Log tail | 5 secondes | Lecture continue avec `watchdog`. |
| Rétro-scan | `true` par défaut | L'utilisateur souhaite importer l'état existant. |
| Bibliothèques | Toutes les bibliothèques `movie`/`show` découvertes | Pas de filtre manuel. |
| Tâches non applicables | Gérées via `not_applicable` | Affichage conditionnel selon Plex Pass et contexte. |

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

1. **Scope V2** : R/S si nécessaire au bon fonctionnement de la V1 (décision technique). Sinon V1 seule d'abord.
2. **Instances** : multi-instance avec badge qualité (à détailler avant la V2).
3. **URLs/clés** : à récupérer via SSH Unraid/Atlas.

## Questions de cadrage V3 — réponses utilisateur

1. **Priorités** : tous les blocs A–G importants à terme.
2. **Notifications** : grande variété de canaux → Apprise.
3. **Auth** : similaire à Radarr/Sonarr (`none`/`forms`/`external`).
