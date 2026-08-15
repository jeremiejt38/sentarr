# Architecture Sentarr

## Vue d'ensemble

Sentarr est structuré en modules backend indépendants, une API REST/WebSocket commune et un frontend React. Le backend est organisé autour d'un moteur de corrélation réactif qui fusionne les données issues de Plex (API + logs) et, en V2+, des connecteurs d'acquisition (*arr).

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Frontend (React/Vite)                     │
│        Vue Films, Vue Séries, Vue Acquisition, Vue Alertes         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ REST / WebSocket
┌──────────────────────────────▼──────────────────────────────────────┐
│                          API FastAPI                               │
│    /api/movies, /api/shows, /api/acquisition, /ws                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐    ┌─────────────────┐    ┌──────────────────┐
│ Module 1      │    │ Module 2        │    │ Module 4+ (V2+)  │
│ Collecteur    │    │ Parseur logs    │    │ Connecteurs      │
│ Plex API      │    │ Plex            │    │ Radarr/Sonarr/…  │
└───────┬───────┘    └────────┬────────┘    └────────┬─────────┘
        │                     │                      │
        └─────────────────────┼──────────────────────┘
                              ▼
                ┌─────────────────────────┐
                │ Module 3                │
                │ Moteur de corrélation   │
                │ + agrégation            │
                └───────────┬─────────────┘
                            ▼
                ┌─────────────────────────┐
                │ Module 4                │
                │ Persistance             │
                │ (SQLite / PostgreSQL)     │
                └─────────────────────────┘
```

## Modules V1

### Module 1 — Collecteur Plex API

**Rôle** : interroger périodiquement l'API Plex Media Server pour obtenir l'état déclaratif des items.

**Fonctionnalités** :
- Lister les bibliothèques et leur type (`movie`, `show`).
- Récupérer les films avec leurs champs (`thumb`, `art`, `summary`, `duration`, pistes, chapitres).
- Récupérer la hiérarchie série/saison/épisode via `/library/metadata/{ratingKey}/children`.
- Déduire l'état de certaines tâches par présence/absence de champs (ex: `thumb` présent = artwork OK).
- Requêtes incrémentales quand c'est possible (`updatedAt`), scan complet sinon.

**Implémentation** : service Python utilisant `plexapi`, exécuté via APScheduler.

### Module 2 — Parseur de logs Plex

**Rôle** : lire en continu le log Plex pour capturer les événements que l'API seule ne fournit pas (début de scan, matching ambigu, génération de vignettes, erreurs).

**Fonctionnalités** :
- Suivi continu du fichier de log avec gestion de rotation.
- Bibliothèque de patterns organisés par type d'événement et version de Plex.
- Extraction de `ratingKey` et/ou chemin de fichier pour corrélation.
- Compteur de lignes non reconnues pour audit.

**Implémentation** : service Python dédié, thread séparé, `watchdog` pour la rotation.

### Module 3 — Moteur de corrélation

**Rôle** : fusionner les données API et logs dans le modèle de données Films/Séries, et calculer les statuts agrégés.

**Fonctionnalités** :
- Résolution par `ratingKey` puis par chemin de fichier.
- Application du pipeline approprié selon le type d'item.
- Calcul des statuts agrégés saison/série (propagation ascendante uniquement).
- Gestion des cas particuliers : épisode mal classé, doublon, tâche non applicable.

**Implémentation** : module Python pur, ensemble de règles unitaires testables.

### Module 4 — Persistance

**Rôle** : stocker l'état, l'historique et les événements bruts.

**Fonctionnalités** :
- SQLite en V1, migration vers PostgreSQL possible.
- Migrations via Alembic.
- Accès via SQLModel/SQLAlchemy.

**Tables principales V1** : voir `data-model.md`.

### Module 5 — API backend

**Rôle** : exposer les données en lecture seule.

**Fonctionnalités** :
- Endpoints REST distincts Films (`/api/movies`) et Séries (`/api/shows`, `/api/shows/{id}/seasons/...`).
- Filtres (bibliothèque, statut, texte libre).
- WebSocket temps réel pour les mises à jour de statut.
- Endpoint de synthèse globale.

**Implémentation** : FastAPI + Pydantic.

### Module 6 — Frontend Dashboard

**Rôle** : interface utilisateur.

**Fonctionnalités** :
- Vue Films : grille/liste plate, badge de statut global.
- Vue Séries : arborescence dépliable Série → Saison → Épisode, barres de progression agrégées.
- Vue détail film/épisode : timeline des étapes.
- Vue synthèse globale : compteurs + tâches bloquées + lignes de log non reconnues.
- Recherche cross-domaine.

**Implémentation** : React/Vite, thème sombre *arr.

### Module 7 — Configuration et déploiement

**Rôle** : packaging et configuration.

**Fonctionnalités** :
- Configuration par variables d'environnement.
- Healthcheck Docker.
- Démarrage résilient (mode dégradé si log inaccessible).

**Implémentation** : Docker unique ou docker-compose backend+frontend.

## Pipeline unifié bout en bout (V2)

La V2 relie la chaîne d'acquisition Radarr/Sonarr (étapes 1–6) au pipeline de traitement Plex (étapes 7–16) en une seule timeline par item.

```
[ACQUISITION — Radarr/Sonarr]              [TRAITEMENT PLEX — V1]
1. Recherché                                 7.  Détecté par Plex
2. Release trouvée                           8.  Scanné
3. Grab                                      9.  Identifié
4. Téléchargement (%)                      10.  Métadonnées
5. Terminé                                 11.  Artworks
6. Importé                                 12.  Vignettes BIF
                                            13.  Marqueurs intro/générique
                                            14.  Chapitres
                                            15.  Flux audio/sous-titres
                                            16.  Prêt
```

**Point focal** : l'écart entre l'étape 6 (Importé côté *arr) et l'étape 7 (Détecté par Plex) est souvent invisible dans les outils existants. Sentarr le rend visible en premier lieu.

## Positionnement par rapport aux outils existants

### vs Monitarr / Trackarr

| Fonctionnalité | Monitarr | Trackarr | Sentarr V2 |
|---|---|---|---|
| Vue file de téléchargement Radarr/Sonarr | ✅ | ✅ | ✅ |
| Score de santé / détection de blocage | ❌ | ✅ | ✅ |
| Suivi du traitement Plex après import | ❌ | ❌ | ✅ |
| Pipeline unifié acquisition → Plex | ❌ | ❌ | ✅ |
| Distinction films / séries hiérarchique | ❌ | ❌ | ✅ |

### vs Homarr / Organizr (V3)

Homarr et Organizr offrent des dashboards généralistes de l'écosystème *arr (liens, statuts de service). Sentarr ne cherche pas à les remplacer : il apporte un **suivi fin au niveau de chaque fichier**, de la recherche d'indexeur jusqu'aux sous-titres, en passant par le traitement Plex.

## Modules V2

### Module V2.1 — Connecteurs Radarr/Sonarr

Interface commune `AcquisitionConnector`. Support multi-instance. Lecture de `/api/v3/queue` et `/api/v3/history`.

### Module V2.2 — Pipeline d'acquisition

Construction de la timeline Recherché → Release → Grab → Téléchargement → Terminé → Importé. Détection de stall.

### Module V2.2b — Connecteurs clients de téléchargement (optionnel V2+)

Interface commune `DownloadClientConnector`. Support de qBittorrent, Transmission et autres clients courants. Permet d'affiner la progression du téléchargement (`progress_percent`) et l'état natif du client. Chaque connecteur renvoie un état normalisé exploité par le pipeline d'acquisition.

### Module V2.3 — Corrélation Acquisition ↔ Plex

Relier un item importé Radarr/Sonarr à l'item Plex via le chemin de fichier. Calcul du délai Importé → Détecté.

### Module V2.4 — Persistance étendue

Tables `external_sources`, `acquisition_items`, `acquisition_events`, `health_scores`, `alert_rules`, `alerts_active`.

### Module V2.5 — Score de santé

Indicateur 0–100 calculé sur le temps sans progression, les erreurs, les tentatives échouées.

### Module V2.6 — Alertes

Règles par seuil de temps/étape, webhook générique, résolution automatique.

### Module V2.7 — Frontend Acquisition

Vue acquisition + pipeline unifié 1–16 étapes + vue alertes.

## Modules V3

Voir `phases.md`. Les blocs sont indépendants et priorisables : Bazarr, Prowlarr, Analytics, Multi-serveur, Auth, Notifications avancées, Export Prometheus/Grafana, API publique, plugins, ouverture communautaire.

### Module V3.1 — Connecteur Bazarr (Bloc A)

Interrogation API Bazarr pour l'état de recherche/téléchargement de sous-titres par langue et par item (film ou épisode). Implémente `AcquisitionConnector`.

### Module V3.2 — Connecteur Prowlarr (Bloc B)

État de santé et latence des indexeurs utilisés par Radarr/Sonarr. Affichage croisé avec les alertes d'acquisition.

### Module V3.3 — Analytics (Bloc C)

Agrégations périodiques (temps moyen par étape, détection d'anomalies). Snapshots stockés dans `analytics_snapshots`. Calculs en tâche de fond planifiée.

### Module V3.4 — Multi-serveur Plex / PostgreSQL (Bloc D)

- Support de plusieurs instances Plex (`plex_servers`).
- Migration transparente vers PostgreSQL via `DATABASE_URL`.

### Module V3.5 — Authentification multi-utilisateur / API publique (Bloc E)

- Mode `none`/`forms`/`external` similaire à Radarr/Sonarr.
- Rôles `admin` et `readonly`.
- Documentation OpenAPI versionnée (`/api/v1/`).

### Module V3.6 — Notifications avancées (Bloc F1)

Intégration Apprise Python pour Discord, Telegram, Matrix, Slack, Mattermost, XMPP/Jabber, ntfy, Pushover, Pushbullet, Gotify, Boxcar, email SMTP, Twilio, custom webhooks.

### Module V3.7 — Export Prometheus / Grafana (Bloc F2)

Endpoint `/metrics` au format Prometheus. Dashboards Grafana pré-configurés pour le monitoring global, l'acquisition et la santé par bibliothèque.

### Module V3.8 — Plugins (Bloc G2)

Interface `AcquisitionConnector` formalisée comme point d'extension public. Chargement dynamique des plugins au démarrage.
