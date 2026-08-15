# Instructions d'utilisation de Talos — Sentarr

## Avertissement

Avant chaque utilisation de Talos (CLI, MCP `talos_*`, soumission de job), **relis ce fichier**. S'il n'existe pas, crée-le et synthétise les consignes en vigueur.

## Configuration Ollama

- **Endpoint** : `http://10.20.0.4:11434` (VPN obligatoire).
- Vérifier que `10.20.0.4` répond avant de soumettre un job (`ping`, `curl /api/tags`).
- Si le VPN est coupé, basculer temporairement sur `http://127.0.0.1:11434` si un Ollama local est disponible.

## Modèles recommandés (12 Go de VRAM)

- **Fast + slow** : `ollama/qwen2.5-coder:14b`.
  - Tient dans ~9,3 Go de VRAM avec 32 768 tokens de contexte.
  - Format Q4_K_M, supporte `tools` et `insert`.
- **À éviter** (trop gros pour 12 Go) : `qwen3-coder:latest` (17,6 Go), `qwen3-coder-next:latest` (49 Go), `qwen2.5-coder:32b` (18,9 Go), `gpt-oss:20b` (13,1 Go).
- Config `~/.talos/.env` :
  ```
  TALOS_FAST_LOCAL_MODEL=ollama/qwen2.5-coder:14b
  TALOS_SLOW_LOCAL_MODEL=ollama/qwen2.5-coder:14b
  OLLAMA_API_BASE=http://10.20.0.4:11434
  ```

## Format d'édition Aider

- Forcer le format SEARCH/REPLACE (`diff`) pour des éditions fiables.
- `~/.aider.conf.yml` doit contenir `edit-format: diff`.
- Vérifier dans les logs Aider que le modèle n'utilise pas le format `whole`.

## Sandbox et application

- **Par défaut** : `sandbox: true` pour tout job dans le repo Sentarr.
- **Exception** : `sandbox: false` uniquement pour des tests temporaires hors repo (`/tmp/...`).
- `TALOS_AUTO_APPLY=false` est la règle : jamais d'application automatique sur le repo.
- Relire le diff avant toute application manuelle.

## Validation des jobs

- La commande de validation (`validate_cmd`) doit utiliser le Python du venv du projet ou un chemin absolu vers l'interpréteur disposant des dépendances (`pytest`, etc.).
- Le daemon Talos hérite du `PATH` du processus parent ; le `python3` par défaut n'a pas forcément les déps.

## Paramètres d'auto-fix

- `TALOS_MAX_FIX_ATTEMPTS=1` est le défaut pour éviter les boucles de token.
- Pour des tâches complexes, on peut passer à `2` dans le job ou dans `~/.talos/.env`.

## Ce qu'on ne délègue pas à Talos

- Architecture globale et décisions de conception.
- Moteur de corrélation, logique métier critique.
- Gestion des secrets, sécurité, déploiement sur l'infrastructure réelle.
- Revue finale avant merge.

## Reporting

- Après chaque utilisation, consigner un bref rapport dans `docs/talos-reports.md`.
- Indiquer le job ID, le prompt (résumé), le résultat, les problèmes et les apprentissages.
- Ne jamais inclure de secrets, tokens, ou contenu du `~/.talos` dans les fichiers versionnés.

## Checklist avant job

1. Lire `docs/talos-instructions.md` (ce fichier).
2. Vérifier le VPN / endpoint Ollama.
3. Confirmer le modèle actif (`qwen2.5-coder:14b`).
4. Vérifier `edit-format: diff` dans `~/.aider.conf.yml`.
5. Choisir `sandbox: true` ou `false` selon le contexte.
6. Définir `validate_cmd` avec le bon Python.
7. Prévoir la mise à jour de `docs/talos-reports.md`.
