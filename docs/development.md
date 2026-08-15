# Guide de développement Sentarr

## Kit Standards Projet (KSP)

Ce projet suit le Kit Standards Projet pour les conventions de branches, commits, versions, README, tests et releases.

## Branches

- `main` : branche stable. Tout merge se fait via rebase + fast-forward.
- Branches de travail courtes :
  - `feature/<nom>` : nouvelle fonctionnalité
  - `fix/<nom>` : correction de bug
  - `docs/<nom>` : documentation
  - `chore/<nom>` : tâches de maintenance
  - `refactor/<nom>` : refonte sans changement fonctionnel
  - `test/<nom>` : ajout/modification de tests

## Commits

Format Conventional Commits :

```
<type>(<scope>): <sujet en français ou anglais, impératif>

Corps optionnel.
```

Types autorisés : `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`.

Scopes conseillés : `api`, `arr`, `radarr`, `sonarr`, `queue`, `history`, `quality`, `root-folder`, `correlation`, `plex`, `frontend`, `docs`, `ci`.

Exemples :

```
feat(api): ajoute l'endpoint de synthèse globale
fix(correlator): corrige la propagation du statut saison
refactor(logs): simplifie le parsing des lignes Plex
docs(readme): met à jour les variables d'environnement
feat(arr): ajoute la lecture de la queue Radarr
fix(correlation): normalise les chemins Windows avant comparaison
feat(frontend): affiche le badge de profil 4K
```

## Versionnement

- Version initiale : `v0.1.0`.
- Incrémentation mineure (`v0.2.0`) : jalon fonctionnel (ex: fin V1, début V2).
- Incrémentation patch (`v0.1.1`) : correction de défaut.
- Aucune version majeure (`v1.0.0`) sans accord explicite.
- Release Please gère les Release PR et les tags annotés.

## Tests

### Backend

- Framework : `pytest`.
- Tests unitaires pour le moteur de corrélation et le parsing de logs.
- Tests d'intégration pour les connecteurs API (mock HTTP).
- Couverture minimale visée : 70 % en V1.

Commandes :

```bash
cd backend
pytest
```

### Frontend

- Framework : `vitest`.
- Tests des composants critiques (Timeline, TreeView, StatusBadge).

Commandes :

```bash
cd frontend
npm run test
```

## Linting & formatage

### Backend

- `ruff` pour le linting et le formatage.
- `mypy` pour le typage statique.
- `isort` intégré à ruff.

Commandes :

```bash
ruff check .
ruff format .
mypy .
```

### Frontend

- `eslint` + `prettier`.

Commandes :

```bash
npm run lint
npm run format
```

## CI/CD

Fichier `.github/workflows/ci.yml` (à créer) :

```yaml
name: CI
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-rye@v3  # ou uv
      - run: cd backend && pytest && ruff check . && mypy .
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: cd frontend && npm ci && npm run lint && npm run test && npm run build
```

## Structure canonique du code

```
backend/sentarr/
├── __init__.py
├── main.py                  # point d'entrée FastAPI
├── config.py                # pydantic-settings (Plex + instances *arr)
├── db.py                    # SQLModel engine/session
├── api/
│   ├── v1/
│   │   ├── movies.py        # endpoints historiques Sentarr
│   │   ├── shows.py
│   │   ├── arr.py           # endpoints d'intégration *arr (V2+)
│   │   └── health.py        # contrat public versionné
│   ├── movies.py            # alias historiques /api/movies
│   ├── shows.py
│   ├── summary.py
│   └── websocket.py
├── clients/
│   ├── base.py              # ArrClient read-only
│   ├── radarr.py
│   ├── sonarr.py
│   └── download.py          # qBittorrent/Transmission (V2+)
├── collectors/
│   ├── plex_api.py
│   └── plex_log_tail.py
├── correlator/
│   ├── engine.py
│   ├── rules.py
│   └── aggregator.py
├── models/
│   ├── base.py
│   ├── plex.py              # movies, shows, seasons, episodes, tasks
│   ├── arr.py               # external_sources, arr_movies, arr_series, arr_episodes
│   ├── quality.py           # quality_profiles
│   ├── root_folders.py      # root_folders
│   └── acquisition.py       # acquisition_items, acquisition_events
├── schemas/
│   ├── common.py
│   └── arr.py
├── services/
│   ├── acquisition.py
│   ├── correlation.py
│   └── health_score.py
└── tasks/
    ├── scheduler.py
    └── sync_arr.py
frontend/src/
├── components/
│   ├── StatusBadge/
│   ├── ProgressBar/
│   ├── Timeline/
│   └── TreeView/
├── features/
│   ├── movies/
│   ├── shows/
│   ├── acquisition/
│   └── alerts/
├── lib/
│   ├── api.client.ts
│   ├── arr.types.ts
│   └── websocket.ts
├── pages/
├── styles/
│   └── theme.css
└── package.json
docker/
├── Dockerfile
└── docker-compose.yml
tests/
├── backend/
└── frontend/
```

## Règles de nommage et de contrat

- Classes et composants : `PascalCase`; fonctions, variables et modules Python : `snake_case`.
- Composants React : `PascalCase.tsx`; hooks : `useX.ts`; clients : `*.client.ts`; tests : `*.test.tsx`.
- Modèles persistés : classes singulier Python (`ArrMovie`, `QualityProfile`), tables SQL au pluriel (`arr_movies`, `quality_profiles`).
- Ressource *arr source : `external_id` + `source_id`; ressource Plex : `plex_rating_key`.
- API Sentarr historique : `/api/movies`, `/api/shows`; API versionnée nouvelle : `/api/v1/arr/movies`, `/api/v1/arr/series`, `/api/v1/health`.
- Réponses d'erreur : `{ "detail": "..." }`; ne jamais exposer une clé API ou un token dans les réponses/logs.
- Migrations : `YYYYMMDD_<verbe>_<objet>.py`.

## Connecteurs

Un connecteur Arr n'expose volontairement que `get`, avec timeout, retry borné et journalisation sans secret. Les routes externes courantes sont `GET /api/v3/movie`, `GET /api/v3/series`, `GET /api/v3/queue`, `GET /api/v3/history`, `GET /api/v3/qualityprofile`, `GET /api/v3/rootfolder` et `GET /api/v3/health` selon le type d'instance.

Exemple de base :

```python
# backend/sentarr/clients/base.py
from typing import Any
import httpx

class ArrClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"X-Api-Key": api_key, "Accept": "application/json"},
        )

    async def get(self, path: str, **params: Any) -> Any:
        response = await self._client.get(path, params=params or None)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
```

## Tests obligatoires

1. Modèles : unicité `(source_id, external_id)` et profils/root folders.
2. Connecteurs : réponses 200, 401, timeout, payload incomplet, pagination si applicable.
3. Sécurité : aucun appel POST/PUT/PATCH/DELETE et aucune fuite de secret dans les logs.
4. Corrélation : chemins, multi-instance, doublons, `unmatched`, liaison Plex.
5. UI : badge, barre, arborescence, timeline 1–16 et reconnexion WebSocket.

Exemple de test de lecture seule :

```python
# tests/backend/test_arr_client.py
import httpx
import pytest
from sentarr.clients.base import ArrClient

@pytest.mark.asyncio
async def test_client_uses_read_only_get(respx_mock):
    route = respx_mock.get("http://radarr/api/v3/health").mock(
        return_value=httpx.Response(200, json={"status": "healthy"})
    )
    client = ArrClient("http://radarr", "test-key")
    assert (await client.get("/api/v3/health"))["status"] == "healthy"
    assert route.called
    await client.close()
```

## Conventions de code

- Python : type hints partout, pas de `Any` sauf justification.
- React : hooks, composants fonctionnels, props typées.
- Pas de secrets dans le code.
- Les constantes de scoring et de seuils sont configurables, jamais codées en dur.

## Processus de validation avant merge

1. Tous les tests passent.
2. Linting et typage passent.
3. Build Docker réussit.
4. Revue manuelle si le changement touche au moteur de corrélation, au modèle de données ou à la sécurité.
5. Pas de secrets dans le diff.

## Definition of Done — intégration *arr

- [ ] Multi-instance Radarr/Sonarr configurable sans collision d'identifiants.
- [ ] Queue/history affichées avec source, profil, étape, progression et chemin.
- [ ] Corrélation chemin → Plex traçable, sinon état `unmatched` explicite.
- [ ] Panne d'une instance *arr isolée et visible dans `/api/v1/health`.
- [ ] Aucun appel POST/PUT/PATCH/DELETE vers une instance distante.
- [ ] Aucun secret, URL interne d'infrastructure ou token commité.
- [ ] Migration réversible et compatibilité des endpoints Sentarr V1 vérifiée.
- [ ] Revue manuelle obligatoire pour modèle, corrélation, sécurité et migrations.

## Talos

Voir `docs/talos-strategy.md`.
