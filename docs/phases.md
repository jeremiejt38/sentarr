# Plan de développement Sentarr

> Aucune tâche n'est estimée en durée. Chaque phase se termine quand son livrable est validé.

## V1 — Pipeline Plex Films/Séries

### Phase 0 — Cadrage

- Récolte des informations opérationnelles (URLs, token, logs, version Plex).
- Réponses aux questions de cadrage V1.
- Création/validation des documents `docs/`.

### Phase 1 — Socle technique

- Initialisation du repo (backend, frontend, docker, tests).
- Configuration du projet Python (pyproject, ruff, mypy, pytest).
- Configuration du projet frontend (Vite, React, TypeScript, ESLint, Prettier).
- Dockerfile + docker-compose.
- Connexion API Plex basique : lister les bibliothèques, récupérer les films.
- Modèle de données plat pour les films.

### Phase 2 — Modèle Séries

- Extension du collecteur Plex API pour la hiérarchie série/saison/épisode.
- Schéma hiérarchique en base de données.
- Remplissage initial des séries/saisons/épisodes existants (`RETRO_SCAN=true`).

### Phase 3 — Parseur de logs Plex

- Service de lecture continue du fichier de log.
- Bibliothèque de patterns de parsing.
- Stockage des événements bruts (`log_events_raw`).
- Gestion de la rotation de logs.

### Phase 4 — Moteur de corrélation

- Résolution de clé (ratingKey, chemin de fichier).
- Règles de mise à jour des statuts pour films et épisodes.
- Agrégation saison/série.
- Gestion des cas particuliers (mal classé, doublon, non applicable).

### Phase 5 — API backend

- Endpoints REST distincts Films/Séries.
- Filtres et recherche.
- WebSocket temps réel.
- Endpoint de synthèse globale.

### Phase 6 — Frontend

- Page d'accueil / synthèse.
- Vue Films (grille + détail).
- Vue Séries (arborescence + détail épisode).
- Timeline des tâches.
- WebSocket intégré.

### Phase 7 — Gestion des erreurs et cas limites

- Items mal classés.
- Doublons.
- Tâches non applicables (Plex Pass, chapitres rares).
- Redémarrage sans perte d'état.
- Mode dégradé si le log Plex n'est pas accessible.

### Phase 8 — Packaging final

- Dockerfile + docker-compose finalisés.
- `.env.example`.
- Documentation d'installation.
- Intégration Traefik.

### Phase 9 — Validation

- Déploiement sur Unraid.
- Vérification sur la bibliothèque complète films/séries.
- Ajustements.

## V2 — Chaîne d'acquisition Radarr/Sonarr

### Phase 0 — Cadrage V2

- Confirmer les instances Radarr/Sonarr, badges qualité, clés API.
- Seuils d'alerte.
- Canal de notification webhook.

### Phase 1 — Connecteurs Radarr/Sonarr

- Interface `AcquisitionConnector`.
- Clients HTTP Radarr/Sonarr multi-instance.
- Lecture queue + history.

### Phase 2 — Pipeline d'acquisition

- Construction de la timeline Recherché → Importé.
- Détection de stall.
- Historique des tentatives.

### Phase 3 — Corrélation Acquisition ↔ Plex

- Lien par chemin de fichier.
- Gestion des non-correspondances.
- Calcul du délai Importé → Détecté.

### Phase 4 — Persistance étendue

- Tables V2 (`external_sources`, `acquisition_items`, `acquisition_events`, `health_scores`, `alert_rules`, `alerts_active`).

### Phase 5 — Score de santé

- Calcul 0–100.
- Seuils configurables.

### Phase 6 — Alertes

- Moteur de règles par seuil de temps/étape.
- Webhook générique.
- Vue Alertes.

### Phase 7 — Frontend Acquisition

- Vue acquisition.
- Pipeline unifié 1–16 étapes.
- Affichage du délai Importé → Détecté.

### Phase 8 — Validation

- Tests sur des cas de blocage réels/simulés.
- Ajustements.

## V3 — Extensions

Les blocs V3 sont indépendants. Priorité initiale proposée : multi-serveur/PostgreSQL, notifications avancées, export Prometheus/Grafana, auth, puis ouverture communautaire.

### Phase 0 — Cadrage V3

- Priorisation définitive des blocs A–G.

### Phase 1 — Bazarr (Bloc A)

- Connecteur Bazarr.
- Suivi des sous-titres par langue et item.

### Phase 2 — Prowlarr (Bloc B)

- Connecteur Prowlarr.
- Affichage de l'état des indexeurs.

### Phase 3 — Analytics (Bloc C)

- Snapshots périodiques.
- Détection d'anomalies par rapport à la moyenne historique.
- Purge des événements bruts anciens une fois agrégés.

### Phase 4 — Multi-serveur / PostgreSQL (Bloc D)

- Support multi-serveur Plex.
- Migration PostgreSQL si volume justifié.

### Phase 5 — Auth / API publique (Bloc E)

- Authentification multi-utilisateur (similaire Radarr/Sonarr).
- Documentation OpenAPI versionnée.

### Phase 6 — Notifications avancées (Bloc F1)

- Intégration Apprise pour notifications multi-canaux.
- Connecteurs clients de téléchargement (qBittorrent, Transmission, etc.).

### Phase 7 — Export Prometheus / Grafana (Bloc F2)

- Endpoint `/metrics` au format Prometheus.
- Dashboards Grafana pré-configurés.

### Phase 8 — Ouverture communautaire (Bloc G)

- Publication du repo.
- Documentation anglaise.
- Template Unraid Community Applications.
- Système de plugins.

### Phase 9 — Validation finale

- Déploiement complet en conditions réelles.
