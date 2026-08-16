# Sentarr

Self-hosted dashboard for tracking Plex media processing tasks, with a clear split between Movies (flat model) and TV Shows (hierarchical model), and extensions to the Radarr/Sonarr acquisition pipeline and the broader *arr ecosystem.

## Current scope

- **V1**: monitor the Plex pipeline (movies & TV shows), real-time web dashboard.
- **V2**: connect to Radarr/Sonarr, unified acquisition → Plex timeline, health score, alerts.
- **V3**: Bazarr, Prowlarr, analytics, multi-server, authentication, advanced notifications, public API.

## Goal

Give a Plex homelab admin a clear view of the progress of every task for each movie, season, and episode, to answer questions like:

- Is the movie I just added still being processed?
- This season shows 22/24 episodes ready — what is happening with the remaining 2?
- Why does this movie still not have a poster 3 hours after being added?

## Stack

- **Backend**: Python 3.12, FastAPI, SQLModel/SQLAlchemy, Pydantic, APScheduler, `plexapi`, `watchdog`, `apprise` (V2+ notifications).
- **Frontend**: React + Vite + PWA, dark *arr theme (Radarr/Sonarr conventions).
- **Database**: SQLite by default in V1, transparent migration to PostgreSQL possible.
- ***arr integration**: read-only connectors for Radarr/Sonarr (V2), qBittorrent/Transmission download clients, versioned `/api/v1/arr` API.
- **V3 monitoring**: Prometheus `/metrics` export + Grafana dashboards.
- **Deployment**: Docker / docker-compose on Unraid, exposed via Traefik at `sentarr.drac-lab.fr`.

## Quick start

See `docs/deployment.md` for full installation instructions.

```bash
cp .env.example .env
# edit .env with PLEX_URL, PLEX_TOKEN, etc.
docker compose up -d
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — architecture and modules.
- [`docs/data-model.md`](docs/data-model.md) — data model.
- [`docs/api.md`](docs/api.md) — REST API + WebSocket.
- [`docs/frontend.md`](docs/frontend.md) — UI/UX specifications.
- [`docs/deployment.md`](docs/deployment.md) — deployment.
- [`docs/configuration.md`](docs/configuration.md) — configuration.
- [`docs/phases.md`](docs/phases.md) — development plan.
- [`docs/talos-strategy.md`](docs/talos-strategy.md) — using Talos.
- [`docs/development.md`](docs/development.md) — KSP, tests, linting.

## License

To be defined (recommendation: MIT if opening to the community in V3).
