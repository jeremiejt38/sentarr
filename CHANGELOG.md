# Changelog Sentarr

Toutes les modifications notables de ce projet seront documentées ici.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et ce projet adhère à [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

## [0.2.0] - 2026-08-15

### Added

- Connecteurs *arr read-only (Radarr/Sonarr) via `ArrClient`.
- Tables `arr_instances`, `acquisition_items`, `acquisition_events`, `alerts`.
- Synchronisation périodique queue/history des instances *arr.
- Corrélation acquisition ↔ Plex par chemin normalisé.
- Moteur d'alertes : items bloqués (stall) et échecs (failed).
- Endpoint `/api/health` de score de santé global.
- Page Acquisition avec filtres status/source/recherche.
- Page Alertes avec liste, filtre sévérité/résolues et résolution.

## [0.1.0] - 2026-08-15

### Added

- Backend FastAPI avec modèles SQLModel (libraries, movies, shows, seasons, episodes, tasks, raw log events).
- Collecteur Plex API pour synchroniser les bibliothèques, films et séries.
- Parseur de logs Plex détectant scan, analyse, deep-analysis, chapitres, crédits, matcher.
- Moteur de corrélation log ↔ item par `plex_rating_key` ou chemin de fichier.
- Scheduler APScheduler pour exécuter la synchro Plex et le parsing de logs périodiquement.
- Endpoints REST : `/api/summary`, `/api/movies`, `/api/shows`, `/api/search`, `/api/logs/*`.
- Filtres `library_id`, `status`, `q` sur les listes de films et séries.
- Frontend React + Vite + PWA avec thème sombre *arr.
- Pages : résumé, films, séries, détails film/série, acquisition, alertes.
- Composants `StatusBadge`, `ProgressBar`, `Timeline`, `TreeView`.
- WebSocket basique avec indicateur de connexion dans la barre latérale.
- Dockerisation avec Dockerfile et docker-compose.
- Tests backend et frontend, linting (ruff) et type checking (mypy).

### Fixed

- Configuration Vitest déplacée dans `vitest.config.ts` séparé pour corriger le build TypeScript.
