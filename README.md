# Sentarr

Dashboard self-hosted de suivi de l'avancement des tâches de traitement de contenu Plex, avec distinction Films (modèle plat) / Séries (modèle hiérarchique), et extension future au pipeline d'acquisition Radarr/Sonarr et à l'écosystème *arr.

## Périmètre actuel

- **V1** : monitoring du pipeline Plex (films & séries), dashboard web en temps réel.
- **V2** : connexion Radarr/Sonarr, timeline unifiée acquisition → Plex, score de santé, alertes.
- **V3** : Bazarr, Prowlarr, analytics, multi-serveur, auth, notifications avancées, API publique.

## Objectif

Donner au gestionnaire d'un serveur Plex (homelab) une vue claire de l'état d'avancement de chaque tâche pour chaque film, chaque saison et chaque épisode, afin de répondre à des questions comme :

- Ce film que je viens d'ajouter est-il encore en cours de traitement ?
- Cette saison affiche 22/24 épisodes prêts — que se passe-t-il pour les 2 restants ?
- Pourquoi ce film n'a-t-il toujours pas d'affiche 3 heures après l'ajout ?

## Stack

- **Backend** : Python 3.12, FastAPI, SQLModel/SQLAlchemy, Pydantic, APScheduler, `plexapi`, `watchdog`, `apprise` (notifications V2+).
- **Frontend** : React + Vite + PWA, thème sombre *arr.
- **Base de données** : SQLite par défaut en V1, migration transparente vers PostgreSQL possible.
- **Monitoring V3** : export Prometheus `/metrics` + dashboards Grafana.
- **Déploiement** : Docker / docker-compose sur Unraid, exposé via Traefik sur `sentarr.drac-lab.fr`.

## Démarrage rapide

Voir `docs/deployment.md` pour l'installation complète.

```bash
cp .env.example .env
# éditer .env avec PLEX_URL, PLEX_TOKEN, etc.
docker compose up -d
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — architecture et modules.
- [`docs/data-model.md`](docs/data-model.md) — modèle de données.
- [`docs/api.md`](docs/api.md) — API REST + WebSocket.
- [`docs/frontend.md`](docs/frontend.md) — spécifications UI/UX.
- [`docs/deployment.md`](docs/deployment.md) — déploiement.
- [`docs/configuration.md`](docs/configuration.md) — configuration.
- [`docs/phases.md`](docs/phases.md) — plan de développement.
- [`docs/talos-strategy.md`](docs/talos-strategy.md) — utilisation de Talos.
- [`docs/development.md`](docs/development.md) — KSP, tests, linting.

## Licence

À définir (recommandation : MIT si ouverture communautaire V3).
