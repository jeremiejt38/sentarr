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

## Modules V2

### Module V2.1 — Connecteurs Radarr/Sonarr

Interface commune `AcquisitionConnector`. Support multi-instance. Lecture de `/api/v3/queue` et `/api/v3/history`.

### Module V2.2 — Pipeline d'acquisition

Construction de la timeline Recherché → Release → Grab → Téléchargement → Terminé → Importé. Détection de stall.

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

Voir `phases.md`. Les blocs sont indépendants et priorisables : Bazarr, Prowlarr, Analytics, Multi-serveur, Auth, Notifications avancées/Home Assistant, API publique, plugins, ouverture communautaire.
