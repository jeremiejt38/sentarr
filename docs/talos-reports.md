# Rapports d'utilisation de Talos — Sentarr

Ce document consigne les utilisations de Talos sur le projet Sentarr : prompts, résultats, problèmes rencontrés, corrections apportées et apprentissages.

## Format d'une entrée

```markdown
## YYYY-MM-DD — <titre du job>

- **Job ID** : `<id>`
- **Label** : `<label>`
- **Fichiers concernés** : `<chemins>`
- **Provider** : `<provider>`
- **Validation** : `<commande>` ✅ / ❌
- **Score (talos review)** : `<0-10>`
- **Résultat** : <résumé>

### Prompt (résumé)

<résumé du prompt envoyé à Talos>

### Problèmes constatés

1. ...

### Corrections appliquées

- ...

### Évaluation

✅ Réussi / ⚠️ Partiel / ❌ Échoué

### Apprentissages pour les prochains prompts

- ...
```

## Entrées

## 2026-08-15 — Smoke test via VPN (10.20.0.4)

- **Job ID** : `12ab4477`
- **Label** : `talos-smoke-test-vpn`
- **Fichiers concernés** : `/tmp/talos-smoke-test-vpn/hello.py`
- **Provider** : `ollama/qwen3:8b`
- **Validation** : `python3 -m py_compile hello.py` ✅
- **Résultat** : `Hello, Talos!`

### Prompt (résumé)

Créer un petit fichier `hello.py` contenant une fonction `greet(name: str) -> str` retournant `f"Hello, {name}!"`, plus un bloc `if __name__ == "__main__"` appelant `print(greet("Talos"))`.

### Diagnostic

- Le VPN n'était effectivement pas démarré lors du premier test (`ping 10.20.0.4` à 100% de perte).
- Une fois le VPN actif, `10.20.0.4` a répondu et Ollama a listé ses modèles (`qwen3:8b`, `qwen3-coder:latest`, `qwen2.5-coder`, etc.).

### Corrections appliquées

- `OLLAMA_API_BASE=http://10.20.0.4:11434` a été ajouté à `~/.talos/.env` pour que les prochains jobs utilisent le bon endpoint.

### Évaluation

✅ Réussi — Talos fonctionne via le VPN. Job terminé en ~22 s.

### Apprentissages

- Si Ollama ne répond pas, vérifier que le VPN est bien monté.

## 2026-08-15 — Sélection des modèles pour 12 Go de VRAM

- **Provider** : `ollama/qwen2.5-coder:14b`
- **Résultat** : tests de chargement réels sur le serveur Ollama

### Problèmes constatés

- Les modèles par défaut (`qwen3:8b` fast / `deepseek-coder-v2:latest` slow) fonctionnent, mais le format `whole` d'Aider est moins fiable pour les éditions.
- `qwen3-coder`, `qwen3-coder-next`, `qwen2.5-coder:32b` et `gpt-oss:20b` ne rentrent pas dans 12 Go de VRAM.

### Corrections appliquées

- Mise à jour de `~/.talos/.env` : `TALOS_FAST_LOCAL_MODEL=ollama/qwen2.5-coder:14b` et `TALOS_SLOW_LOCAL_MODEL=ollama/qwen2.5-coder:14b`.
- Création/mise à jour de `~/.aider.conf.yml` avec `edit-format: diff` pour forcer le format SEARCH/REPLACE d'Aider.

### Évaluation

✅ Le modèle 14B tient en VRAM avec 32 768 tokens de contexte et génère du code de qualité.

## 2026-08-15 — Test de génération réelle (Calculator)

- **Job ID** : `d914af21`
- **Label** : `talos-real-create`
- **Fichiers concernés** : `/tmp/talos-real-test/calculator.py`, `/tmp/talos-real-test/test_calculator.py`
- **Provider** : `ollama/qwen2.5-coder:14b`
- **Validation** : `python3 -m pytest test_calculator.py -q` ❌ (pytest absent du `python3` du daemon)
- **Résultat** : code généré correct — 5 tests passent à la main avec le venv Talos.

### Évaluation

⚠️ Partiel — le code est bon mais la commande de validation a échoué parce que le daemon n'utilise pas le venv du projet. Le résultat valide manuellement.

## 2026-08-15 — Test d'édition + auto-fix (modulo)

- **Job ID** : `77eb419a`
- **Label** : `talos-fix-modulo`
- **Fichiers concernés** : `/tmp/talos-real-test/calculator.py`
- **Provider** : `ollama/qwen2.5-coder:14b`
- **Validation** : `/home/jerem/workspace/talos/.venv/bin/python3 -m pytest test_calculator.py -q` ✅
- **Résultat** : 5 tests passent après correction de la méthode `modulo` (`math.fmod`).

### Évaluation

✅ Réussi — l'édition SEARCH/REPLACE fonctionne et Aider a corrigé son propre mismatch.

## 2026-08-15 — Test du workflow sandbox

- **Job ID** : `07075c8e`
- **Label** : `talos-sandbox-test`
- **Fichiers concernés** : `/tmp/talos-sandbox-test/greeting.py`, `test_greeting.py` (sandbox uniquement)
- **Provider** : `ollama/qwen2.5-coder:14b`
- **Validation** : `/home/jerem/workspace/talos/.venv/bin/python3 -m pytest test_greeting.py -q` ✅
- **Résultat** : le sandbox a généré les fichiers, validé les tests, et n'a pas écrit dans le répertoire d'origine (`TALOS_AUTO_APPLY=false`).

### Évaluation

✅ Réussi — le workflow sécurisé par défaut de Talos fonctionne.

## 2026-08-15 — Ajout du suivi de coût et économies

- **Job ID** : `424930f7`
- **Label** : `talos-cost-test-2`
- **Fichiers concernés** : `/tmp/talos-cost-test/greet.py`, `test_greet.py` (sandbox)
- **Provider** : `ollama/qwen2.5-coder:14b`
- **Validation** : `/home/jerem/workspace/talos/.venv/bin/python3 -m pytest test_greet.py -q` ✅
- **Score (talos review)** : 8/10
- **Résultat** : génération d'une fonction `goodbye` + test ; coût estimé Devin = 0.01573 USD, économies = 0.01573 USD pour 3146 tokens.

### Prompt (résumé)

Test de l'intégration du coût monétaire et du `tokens received` dans `talos/core/stats.py` : ajout de `goodbye` dans `greet.py` et test correspondant.

### Corrections appliquées

- Restauration du calcul de coût issu du stash Git (`39e2b6f`) dans `talos/core/stats.py`.
- Persistence de `resolved_model` dans `talos/core/daemon.py` pour les agrégations `by_model`.
- Correction du parsing `tokens received` dans `talos/core/jobs.py`.
- Affichage des coûts dans `talos report`.
- Mise à jour de `~/.talos/.env` et de `docs/talos-instructions.md`.

### Évaluation

✅ Réussi — `talos report` affiche les coûts, `~/.talos/stats.json` contient les agrégations par modèle.

## 2026-08-15 — Test d'appel via MCP

### 248859a1 — talos-mcp-test

- **Fichiers concernés** : `/tmp/talos-mcp-test/utils.py`, `test_utils.py` (sandbox)
- **Provider** : `ollama/qwen2.5-coder:14b`
- **Validation** : `/home/jerem/workspace/talos/.venv/bin/python3 -m pytest test_utils.py -q` ❌
- **Résultat** : la fonction `slugify` laissait des tirets en début/fin de chaîne ; l'auto-fix n'a pas corrigé en un seul essai.

### 4686ef12 — talos-mcp-counter

- **Fichiers concernés** : `/tmp/talos-mcp-test/counter.py`, `test_counter.py` (sandbox)
- **Provider** : `ollama/qwen2.5-coder:14b`
- **Validation** : `/home/jerem/workspace/talos/.venv/bin/python3 -m pytest test_counter.py -q` ✅
- **Résultat** : la classe `Counter` et ses tests ont été générés correctement, validation passée.

### Évaluation

✅/⚠️ Le MCP fonctionne (soumission, suivi, validation). Le modèle réussit les tâches simples et échoue sur certains cas de bord.

## Synthèse — Préparation aux gros travaux

### Ce qui fonctionne ✅

- Daemon Talos démarre et communique via CLI et MCP.
- Ollama distant (`10.20.0.4`) est joignable via VPN.
- `qwen2.5-coder:14b` rentre dans 12 Go de VRAM avec 32 768 tokens de contexte.
- Format d'édition SEARCH/REPLACE activé (`edit-format: diff` dans `~/.aider.conf.yml`).
- Sandbox actif par défaut, pas d'écriture directe sur le repo (`TALOS_AUTO_APPLY=false`).
- Appels MCP fonctionnels : soumission, statut, logs.
- Review manuelle avec `talos review` : score, feedback, apprentissage.
- Statistiques et coût monétaire estimé intégrés (Devin/Talos, économies, tokens, `by_model`).

### Ce qui reste à surveiller ⚠️

- Le `python3` par défaut du daemon n'a pas pytest : il faut utiliser le venv du projet dans `validate_cmd` ou installer les dépendances dans l'environnement du daemon.
- L'auto-fix avec `TALOS_MAX_FIX_ATTEMPTS=1` ne suffit pas toujours ; les cas de bord (négatifs, espaces) peuvent échapper au modèle.
- Le provider affiché par `talos providers` indique `ollama/qwen3-coder:latest` (fallback `DEFAULT_MODEL`) alors que les jobs utilisent réellement `qwen2.5-coder:14b` — affichage cosmétique.
- Le serveur MCP a chargé l'ancienne `.env` en mémoire : il faut le redémarrer pour que `talos_list_providers` reflète la nouvelle config.

## 2026-08-15 — Sentarr V1 — modèles SQLModel (échec)

- **Job ID** : `c764af4f`
- **Label** : `models-v1`
- **Fichiers concernés** : `backend/sentarr/models/base.py`, `backend/sentarr/models/plex.py` (jamais écrits par Talos)
- **Provider** : `ollama/qwen2.5-coder:14b`
- **Validation** : `uv run pytest tests/test_models.py -q`
- **Résultat** : échec après 3 tentatives / timeout 300 s.

### Diagnostic

- Le daemon a perdu/rechargé une `.env` sans `OLLAMA_API_BASE` après son redémarrage automatique.
- Aider n'a pas pu contacter Ollama (`Error getting model info for qwen2.5-coder:14b`) car l'API base n'était pas définie.

### Action

- Implémentation manuelle des modèles SQLModel V1 par Devin.
- Les modèles ont été testés avec `uv run pytest tests/test_models.py -q` (3 passed).

### Apprentissages

- Avant chaque batch de jobs Talos, redémarrer le daemon explicitement avec `OLLAMA_API_BASE` exporté.
- Vérifier `talos providers` pour confirmer que le modèle cible est bien résolu.

## 2026-08-15 — Sentarr V1 — frontend Vite PWA (échec)

- **Job ID** : `1bc258f8`
- **Label** : `frontend-vite-v1`
- **Fichiers concernés** : `frontend/` (jamais écrits par Talos)
- **Provider** : `ollama/qwen2.5-coder:14b`
- **Validation** : `npm install && npm run build`
- **Résultat** : échec après 3 tentatives / timeout 300 s (même cause Ollama).

### Action

- Initialisation et configuration manuelle du frontend Vite + React + TS + PWA par Devin.
- Build frontend OK (`npm run build`).

### Verdict

**Feu vert conditionnel.** Talos est prêt pour des travaux supervisés de refactoring et de génération de code modulaire une fois le daemon correctement configuré. Il n'est pas encore autonome pour des tâches complexes sans revue humaine.

## 2026-08-15 — Sentarr V1 — parseur de logs Plex (échec Talos, implémentation manuelle)

- **Job ID** : `901a6af5`
- **Label** : `plex-log-parser-v1`
- **Fichiers concernés** : `backend/sentarr/collectors/plex_log_parser.py`, `backend/tests/test_plex_log_parser.py`, `backend/sentarr/api/logs.py`, `backend/sentarr/api/search.py`, `frontend/src/pages/MovieDetail.tsx`, `frontend/src/pages/ShowDetail.tsx`
- **Provider** : `ollama/qwen2.5-coder:14b`
- **Validation** : `uv run pytest tests/test_plex_log_parser.py -q && uv run ruff check sentarr tests && uv run mypy sentarr`
- **Résultat** : timeout / échec du job Talos ; implémentation manuelle par Devin.

### Diagnostic

- Le prompt était probablement trop long et le timeout de 300 s a été atteint avant que le modèle ne produise de code.
- Les logs Plex réels ont été analysés au préalable via SSH pour identifier les patterns utiles.

### Action

- Implémentation manuelle du parseur de logs Plex et du moteur de corrélation log ↔ item.
- Ajout de la deduplication par hash de ligne dans `LogEventRaw`.
- Ajout des endpoints API `/api/search`, `/api/logs/*` et des pages `MovieDetail` / `ShowDetail`.
- Validation : 5 tests passent, ruff OK, mypy OK.

### Apprentissages

- Pour les jobs Talos complexes, diviser le travail en prompts plus petits et ciblés.
- Continuer à utiliser Talos pour des morceaux isolés après cette leçon.

## 2026-08-16 — Extra credits V2/V3 + tests (en cours)

### Jobs soumis

| Job ID | Label | Objectif | Provider | Validation |
|---|---|---|---|---|
| `a9648c6e` | `health-score-tests` | Tests unitaires `sentarr/health/score.py` | `ollama/qwen2.5-coder:14b` | `uv run pytest backend/tests/test_health_score.py -q` |
| `83e30c4a` | `download-client-tests` | Tests clients qBittorrent/Transmission | `ollama/qwen2.5-coder:14b` | `uv run pytest backend/tests/test_download_client.py -q` |
| `855f833c` | `analytics-tests` | Tests `sentarr/analytics/snapshot.py` | `ollama/qwen2.5-coder:14b` | `uv run pytest backend/tests/test_analytics.py -q` |
| `3044a952` | `arr-sync-timeline-tests` | Tests timeline acquisition | `ollama/qwen2.5-coder:14b` | `uv run pytest backend/tests/test_arr_sync.py -q` |

### Configuration Ollama

- Initialement `OLLAMA_API_BASE=http://127.0.0.1:11434` (hôte local, fallback).
- Après mise en ligne des hôtes distants par l'utilisateur, reconfiguration en `http://10.20.0.4:11434`.
- Daemon Talos redémarré avec `OLLAMA_API_BASE=http://10.20.0.4:11434` pour les nouveaux jobs.
- Correction de `validate_cmd` : utiliser `PYTHONPATH=backend /home/jerem/workspace/sentarr/backend/.venv/bin/python -m pytest ...` car le venv du projet est nécessaire pour importer `sentarr`, et `uv run` ne fonctionne pas dans le sandbox.

### Travail en parallèle

- Mise à jour de `docs/talos-reports.md` pendant que les jobs s'exécutent.
- Stratégie : attendre les résultats en file, reviewer chaque livrable, puis intégrer après validation.

### Résultat

| Job | État | Action |
|---|---|---|
| `a9648c6e` / `3bdb84c2` `health-score-tests` | ❌ Échec (génération OK, mais `TaskStatus` passé en tant que tâche) | Implémentation manuelle du test + correction de `calculate_health_season/show` pour agréger les sous-niveaux. 7 tests passent. |
| `04d0aa55` `qbittorrent-test` | ❌ Échec (test instancie `QBittorrentClient` qui appelle `_login` réseau) | Implémentation manuelle de `test_qbittorrent.py` : paramétrisation de `_map_status` + test d'init avec `_login` mocké. 21 tests passent. |
| Autres jobs | 🚫 Annulés | Re-soumission avec `validate_cmd` corrigée reportée ; priorité aux tests manuels validés. |

### Apprentissages

- La validation dans le sandbox doit utiliser le venv du projet (`PYTHONPATH=backend /home/jerem/workspace/sentarr/backend/.venv/bin/python -m pytest ...`).
- L'auto-fix a tenté de corriger le test, mais le modèle a échoué à comprendre la relation SQLModel `MovieTask`/`EpisodeTask` vs `TaskStatus` ; un prompt plus précis avec un snippet de fixture correcte serait nécessaire.
