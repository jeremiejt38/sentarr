# Sentarr — Development Guidelines

## Vision

Sentarr est un dashboard self-hosted de suivi de l'avancement des tâches de traitement de contenu Plex (scan, identification, métadonnées, artworks, BIF, marqueurs, chapitres, flux), avec une distinction forte entre Films (modèle plat) et Séries (hiérarchie Série → Saison → Épisode). Les versions ultérieures étendent le suivi à la chaîne d'acquisition Radarr/Sonarr (V2), puis à l'écosystème *arr complet, analytics, multi-serveur, auth et notifications (V3).

## Contraintes générales

- **Lecture seule** : Sentarr n'effectue jamais d'écriture sur Plex, Radarr, Sonarr, Bazarr ou Prowlarr. Il observe et agrège uniquement.
- **Self-hosted** : 100 % local, aucune dépendance à un compte cloud tiers.
- **Mono-utilisateur en V1** : pas d'auth applicative. Protection par le réseau local / VPN / Traefik + Authelia si besoin.
- **ORM SQLAlchemy/SQLModel** : pour garder la porte ouverte à PostgreSQL sans réécriture.
- **Style *arr** : interface sombre cohérente avec Radarr/Sonarr/Bazarr, pour que l'utilisateur soit immédiatement familier.

## Kit Standards Projet (KSP)

- Voir `docs/development.md` pour les conventions de branches, commits, versions, tests et linting.
- Commits au format **Conventional Commits** (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `perf:`, `build:`, `ci:`, `chore:`).
- Branches courtes : `feature/*`, `fix/*`, `docs/*`, `chore/*`, `refactor/*`, `test/*`.
- `main` reste stable. Rebase + fast-forward après validation.
- Pas de tag annoté `vX.Y.Z` sans validation explicite.

## Talos

- Voir `docs/talos-strategy.md`.
- Talos est un outil de génération de code auxiliaire : on lui confie des morceaux isolés, on vérifie chaque livrable, on réessaie jusqu'à 3 fois par job, et on continue à l'utiliser pour les jobs suivants même en cas d'échec.
- On consigne les rapports d'utilisation de Talos pour l'aider à progresser.

## Structure du repo

```
sentarr/
├── AGENTS.md                 ← ce fichier
├── README.md                 ← présentation et démarrage rapide
├── CHANGELOG.md              ← historique des releases
├── docs/                     ← documentation du projet
│   ├── architecture.md       ← modules, flux, stack technique
│   ├── data-model.md         ← schémas de base de données
│   ├── api.md                ← endpoints REST + WebSocket
│   ├── frontend.md           ← spécifications UI/UX
│   ├── configuration.md      ← variables d'environnement
│   ├── deployment.md         ← Docker, Unraid, Traefik
│   ├── development.md        ← KSP, tests, linting
│   ├── phases.md             ← plan de développement V1/V2/V3
│   ├── talos-strategy.md     ← comment utiliser Talos
│   ├── notifications.md      ← stratégie de notifications V2/V3
│   ├── decisions.md          ← décisions de conception et réponses au cadrage
│   ├── cadrage-questions.md  ← questionnaires V1/V2/V3 et réponses
│   ├── definition-of-done.md ← critères d'acceptation V1/V2/V3
│   ├── operations.md         ← infos opérationnelles d'Atlas/Unraid (pas de secrets)
│   └── talos-reports.md      ← rapports d'utilisation de Talos
├── backend/                  ← API FastAPI + modules métier
├── frontend/                 ← React/Vite
├── docker/                   ← Dockerfiles, docker-compose
└── tests/
```

## Vérification avant merge

- Tests backend/frontend passent.
- Linting/typechecking passent.
- Pas de secrets dans les fichiers versionnés (vérification via `git grep` sur les tokens récupérés en ops).
