# Plugin System — Sentarr

Sentarr supports a plugin architecture that allows third-party developers to extend functionality without modifying core code.

## Architecture

Plugins are standard Python packages that declare a `sentarr_plugin` entry-point. At startup, the plugin manager:

1. **Discovers** all installed packages with a `sentarr_plugin` entry-point.
2. **Validates** each plugin (must subclass `SentarrPlugin`, must have a `meta` attribute).
3. **Activates** each plugin — calling `on_activate()`, registering routes and scheduled jobs.

## Creating a Plugin

### 1. Create a Python package

```
sentarr-plugin-example/
├── pyproject.toml
└── sentarr_plugin_example/
    └── __init__.py
```

### 2. Subclass `SentarrPlugin`

```python
from sentarr.plugins.base import PluginMeta, SentarrPlugin
from fastapi import APIRouter

class ExamplePlugin(SentarrPlugin):
    meta = PluginMeta(
        name="example",
        version="1.0.0",
        description="An example Sentarr plugin",
        author="Your Name",
        url="https://github.com/you/sentarr-plugin-example",
    )

    def on_activate(self, app):
        print("Example plugin activated!")

    def register_routes(self):
        router = APIRouter()

        @router.get("/hello")
        async def hello():
            return {"message": "Hello from example plugin!"}

        return router

    def on_sync_complete(self, source, session):
        print(f"Sync completed for {source}")
```

### 3. Declare the entry-point

In `pyproject.toml`:

```toml
[project]
name = "sentarr-plugin-example"
version = "1.0.0"

[project.entry-points."sentarr_plugin"]
example = "sentarr_plugin_example:ExamplePlugin"
```

### 4. Install

```bash
pip install sentarr-plugin-example
# or during development:
pip install -e ./sentarr-plugin-example
```

The plugin will be auto-discovered on the next Sentarr restart.

## Available Hooks

| Hook | When it fires | Arguments |
|------|--------------|-----------|
| `on_activate(app)` | Plugin activation at startup | FastAPI app instance |
| `on_deactivate()` | App shutdown or plugin disabled | — |
| `on_sync_complete(source, session)` | After a sync job completes | `"plex"`, `"arr"`, `"bazarr"`, `"prowlarr"` |
| `on_alert_created(alert_data, session)` | New alert created | Alert dict |
| `on_alert_resolved(alert_data, session)` | Alert resolved | Alert dict |
| `on_item_added(item_type, item_data, session)` | New movie/show/episode discovered | `"movie"`, `"show"`, `"episode"` |
| `on_item_status_changed(item_type, item_id, old_status, new_status, session)` | Status change | All status transitions |
| `on_notification_send(title, body, event_type)` | Before Apprise notification | Return `{"title": ..., "body": ...}` to modify |

## Route Registration

If `register_routes()` returns a `FastAPI APIRouter`, it is mounted at:

```
/api/v1/plugins/{plugin_name}/
```

For the example above, the endpoint would be `GET /api/v1/plugins/example/hello`.

## Scheduled Jobs

Override `register_scheduled_jobs()` to return APScheduler job definitions:

```python
def register_scheduled_jobs(self):
    return [{
        "func": self.check_something,
        "trigger": "interval",
        "minutes": 10,
        "id": f"plugin_{self.meta.name}_check",
    }]
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/plugins` | List all discovered plugins with status |

## Security

- Plugins run with the same permissions as the Sentarr backend.
- Only install plugins from trusted sources.
- Plugin routes are protected by the same auth middleware as core routes.
