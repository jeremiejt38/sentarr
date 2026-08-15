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

Exemples :

```
feat(api): ajoute l'endpoint de synthèse globale
fix(correlator): corrige la propagation du statut saison
refactor(logs): simplifie le parsing des lignes Plex
docs(readme): met à jour les variables d'environnement
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

## Structure du code

```
backend/
├── sentarr/
│   ├── __init__.py
│   ├── main.py              # point d'entrée FastAPI
│   ├── config.py            # pydantic-settings
│   ├── db.py                # SQLModel engine/session
│   ├── api/
│   │   ├── movies.py
│   │   ├── shows.py
│   │   ├── summary.py
│   │   └── websocket.py
│   ├── collectors/
│   │   ├── plex_api.py
│   │   ├── plex_log_tail.py
│   │   └── radarr.py        # V2
│   ├── correlator/
│   │   ├── engine.py
│   │   ├── rules.py
│   │   └── aggregator.py
│   ├── models/
│   │   ├── base.py
│   │   ├── movies.py
│   │   └── shows.py
│   └── tasks/
│       └── scheduler.py
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── api.ts
│   ├── websocket.ts
│   └── theme.css
└── package.json
docker/
├── Dockerfile
└── docker-compose.yml
tests/
├── backend/
└── frontend/
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

## Talos

Voir `docs/talos-strategy.md`.
