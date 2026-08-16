# Sentarr

[![CI](https://github.com/jeremiejt38/sentarr/actions/workflows/ci.yml/badge.svg)](https://github.com/jeremiejt38/sentarr/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Self-hosted dashboard for tracking Plex media processing tasks, with a clear split between Movies (flat model) and TV Shows (hierarchical model), and full integration with the *arr ecosystem (Radarr, Sonarr, Bazarr, Prowlarr).

## Features

### V1 — Plex Pipeline Monitoring
- Real-time tracking of 9 task categories per movie/episode (scan, identify, metadata, artwork, BIF, markers, chapters, credits, stream analysis)
- Hierarchical view: Show > Season > Episode with status propagation
- Continuous log parsing with correlation to library items
- Health score (0-100) per item and globally

### V2 — Acquisition Pipeline
- Radarr/Sonarr read-only connectors with multi-instance support
- Unified acquisition timeline: Searched > Grabbed > Downloading > Imported > Detected by Plex
- Download client connectors (qBittorrent, Transmission) for progress tracking
- Configurable alert thresholds per pipeline step
- "Import to Plex detection" delay tracking

### V3 — Full Ecosystem
- **Multi-server Plex**: monitor multiple Plex servers from a single dashboard
- **Bazarr integration**: subtitle tracking per language and episode
- **Prowlarr integration**: indexer status and statistics
- **API key authentication**: Bearer token, X-Api-Key header, or query parameter
- **Multi-instance support**: configure multiple Bazarr/Prowlarr instances
- **Notifications**: multi-channel via Apprise (Discord, Telegram, ntfy, email, Slack, and 10+ more)
- **Prometheus metrics**: `/metrics` endpoint for Grafana dashboards
- **Plugin system**: extend Sentarr with custom hooks, routes, and scheduled jobs
- **PostgreSQL support**: optional migration from SQLite for high-volume setups
- **Versioned API**: all endpoints under `/api/v1/`

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLModel/SQLAlchemy, Pydantic, APScheduler |
| Frontend | React 18, Vite, TypeScript, PWA |
| Database | SQLite (default) or PostgreSQL |
| Integrations | plexapi, httpx, apprise, prometheus-client |
| Deployment | Docker, docker-compose, Traefik |

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/jeremiejt38/sentarr.git
cd sentarr
cp .env.example .env
# Edit .env with your Plex URL, token, and *arr API keys
docker compose -f docker/docker-compose.yml up -d
```

### With PostgreSQL

```bash
# Set POSTGRES_PASSWORD in .env
docker compose -f docker/docker-compose.yml -f docker/docker-compose.postgres.yml up -d
```

### Local Development

```bash
# Backend
cd backend
uv sync --all-extras
cp ../.env.example ../.env
uv run uvicorn sentarr.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Configuration

All configuration is done via environment variables or a `.env` file. See [`.env.example`](.env.example) for all available options.

### Required Variables

| Variable | Description | Example |
|----------|------------|---------|
| `PLEX_URL` | Plex server URL | `http://plex:32400` |
| `PLEX_TOKEN` | Plex authentication token | *(from Preferences.xml)* |
| `PLEX_LOG_PATH` | Path to Plex log file | `/var/log/plex/Plex Media Server.log` |

### Multi-Server Plex (V3)

```bash
PLEX_SERVERS='[
  {"name": "main", "url": "http://plex:32400", "token": "...", "log_path": "/var/log/plex/Plex Media Server.log"},
  {"name": "remote", "url": "http://plex2:32400", "token": "..."}
]'
```

### *arr Integration (V2)

```bash
RADARR_URLS='[{"name": "radarr-1080p", "url": "http://radarr:7878", "api_key": "...", "profile_label": "1080p"}]'
SONARR_URLS='[{"name": "sonarr", "url": "http://sonarr:8989", "api_key": "..."}]'
```

### Notifications (V3)

```bash
NOTIFICATION_CHANNELS='[
  {"name": "discord", "url": "discord://webhook_id/webhook_token", "events": ["alert_triggered"]},
  {"name": "ntfy", "url": "ntfy://ntfy.example.com/sentarr", "events": ["alert_triggered", "alert_resolved"]}
]'
```

### Authentication (V3)

```bash
AUTH_MODE=api_key
SENTARR_ADMIN_API_KEY=your-secret-key-here
```

### Alert Thresholds

Configurable via the WebUI (Settings > Alert Thresholds) or via environment:

```bash
ALERT_THRESHOLD_SEARCHED=60    # minutes before "search stuck" alert
ALERT_THRESHOLD_DOWNLOADING=30 # minutes before "download stuck" alert
ALERT_THRESHOLD_IMPORTING=15   # minutes before "import stuck" alert
ALERT_THRESHOLD_PLEX_OVERALL=60 # minutes before "Plex processing stuck" alert
```

## API

All endpoints are versioned under `/api/v1/`. Full OpenAPI documentation is available at `/docs` when the server is running.

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/summary` | Dashboard overview (movies, shows, errors) |
| `GET /api/v1/movies` | List movies with filters |
| `GET /api/v1/shows` | List shows with filters |
| `GET /api/v1/acquisition` | Acquisition pipeline items |
| `GET /api/v1/health` | Health score with alerts and *arr instance status |
| `GET /api/v1/alerts` | Active/resolved alerts |
| `GET /api/v1/alerts/thresholds` | Get/update alert thresholds |
| `GET /api/v1/indexers` | Prowlarr indexer status |
| `GET /api/v1/subtitles` | Bazarr subtitle tracks |
| `GET /api/v1/servers` | Plex server management (CRUD) |
| `GET /api/v1/auth/keys` | API key management |
| `GET /api/v1/plugins` | Installed plugins |
| `GET /api/v1/download` | Active downloads |
| `GET /api/v1/analytics` | Analytics snapshots |
| `GET /metrics` | Prometheus metrics |
| `GET /health` | Basic health check |
| `WS /ws` | WebSocket for real-time updates |

### Prometheus Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `sentarr_movies_total` | gauge | Total movies |
| `sentarr_movies_status{status}` | gauge | Movies by status |
| `sentarr_shows_total` | gauge | Total shows |
| `sentarr_shows_status{status}` | gauge | Shows by status |
| `sentarr_episodes_total` | gauge | Total episodes |
| `sentarr_episodes_status{status}` | gauge | Episodes by status |
| `sentarr_active_alerts` | gauge | Active alerts |
| `sentarr_health_score` | gauge | Overall health 0-100 |
| `sentarr_plex_api_poll_duration_seconds` | histogram | Plex API poll duration |
| `sentarr_log_lines_unparsed_total` | gauge | Unparsed log lines |

## Plugin System

Sentarr supports a plugin architecture for extending functionality. See [`docs/plugins.md`](docs/plugins.md) for the full guide.

### Quick Example

```python
from sentarr.plugins.base import PluginMeta, SentarrPlugin

class MyPlugin(SentarrPlugin):
    meta = PluginMeta(name="my-plugin", version="1.0.0", description="My custom plugin")

    def on_sync_complete(self, source, session):
        print(f"Sync completed for {source}")
```

Declare in `pyproject.toml`:

```toml
[project.entry-points."sentarr_plugin"]
my-plugin = "my_plugin:MyPlugin"
```

## Project Structure

```
sentarr/
├── backend/               # FastAPI backend
│   ├── sentarr/
│   │   ├── api/           # REST endpoints
│   │   ├── alerts/        # Alert engine
│   │   ├── analytics/     # Snapshots & anomaly detection
│   │   ├── collectors/    # Plex, *arr, download client connectors
│   │   ├── health/        # Health score calculation
│   │   ├── metrics/       # Prometheus registry
│   │   ├── models/        # SQLModel data models
│   │   ├── notifications/ # Apprise notification engine
│   │   ├── plugins/       # Plugin system (base, manager)
│   │   └── tasks/         # APScheduler jobs
│   ├── alembic/           # Database migrations
│   └── tests/             # pytest test suite
├── frontend/              # React + Vite + TypeScript
│   └── src/
│       ├── components/    # Reusable UI components
│       ├── pages/         # Route pages
│       └── lib/           # API client, WebSocket, types
├── docker/                # Dockerfile, docker-compose
├── docs/                  # Project documentation
└── .github/workflows/     # CI/CD (lint, test, build, push)
```

## Development

### Prerequisites

- Python 3.12+
- Node.js 22+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Running Tests

```bash
# Backend
cd backend
uv run pytest tests/ -v

# Frontend
cd frontend
npm test
```

### Linting & Type Checking

```bash
cd backend
uv run ruff check sentarr tests
uv run mypy sentarr
```

### Building

```bash
# Frontend
cd frontend && npm run build

# Docker
docker build -f docker/Dockerfile -t sentarr .
```

### Commit Conventions

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation
- `test:` — tests
- `refactor:` — code refactoring
- `perf:` — performance
- `build:` / `ci:` / `chore:` — infrastructure

### Branch Strategy

- `main` — stable, production-ready
- `feature/*`, `fix/*`, `docs/*`, `refactor/*`, `test/*` — short-lived branches
- Rebase + fast-forward merge after validation

## Deployment

### Unraid

An Unraid Community Applications template is available at [`unraid-template.xml`](unraid-template.xml).

### Docker Compose

```yaml
services:
  sentarr:
    image: ghcr.io/jeremiejt38/sentarr:latest
    ports:
      - "8000:8000"
    volumes:
      - sentarr-data:/app/data
      - /path/to/plex/logs:/var/log/plex:ro
    env_file: .env
```

### Traefik Integration

The included `docker-compose.yml` has Traefik labels pre-configured for `sentarr.drac-lab.fr`.

### Health Check

The Docker image includes a built-in health check hitting `GET /health`.

## Troubleshooting

### Plex token not found
Extract from `Preferences.xml` inside the Plex container:
```bash
docker exec plex cat "/config/Library/Application Support/Plex Media Server/Preferences.xml" | grep -oP 'PlexOnlineToken="\K[^"]+'
```

### *arr API key
Find in the *arr web UI under Settings > General > Security, or:
```bash
docker exec radarr cat /config/config.xml | grep -oP '<ApiKey>\K[^<]+'
```

### Database migration issues
Run migrations manually:
```bash
cd backend && uv run alembic upgrade head
```

### WebSocket not connecting
Ensure your reverse proxy forwards WebSocket connections on the `/ws` path.

### Plugin not loading
Check that the entry-point group is `sentarr_plugin` and the class subclasses `SentarrPlugin`.

## License

MIT — see [LICENSE](LICENSE) for details.
