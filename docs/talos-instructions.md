# Instructions d'utilisation de Talos — Sentarr

## Avertissement

Avant chaque utilisation de Talos (CLI, MCP `talos_*`, soumission de job), **relis ce fichier**. S'il n'existe pas, crée-le et synthétise les consignes en vigueur.

## Configuration Ollama

- **Endpoint** : `http://10.20.0.4:11434` (VPN obligatoire).
- Vérifier que `10.20.0.4` répond avant de soumettre un job (`ping`, `curl /api/tags`).
- Si le VPN est coupé, basculer temporairement sur `http://127.0.0.1:11434` si un Ollama local est disponible.

## Modèles recommandés (12 Go de VRAM)

### Choix par défaut

- **Fast + slow** : `ollama/qwen2.5-coder:14b`.
  - Meilleur compromis pour du code dans 12 Go : ~9,3 Go de VRAM, 32 768 tokens de contexte.
  - Q4_K_M, supporte `tools` et `insert`, rapide en prompt eval.

### Alternatives selon les cas

| Cas | Modèle | Pourquoi | Inconvénient |
|---|---|---|---|
| Réponse très rapide, tâche minime | `qwen3:8b` | 5 Go, moins de charge | Pas spécialisé code, génère du *thinking*, moins fiable sur l'édition |
| Contexte très long, pas spécifiquement code | `mistral-nemo:latest` | 6,7 Go, 1 M de contexte | Modèle généraliste, moins bon en génération de code |
| Contexte long avec code | `deepseek-coder-v2:latest` | 8,4 Go, 163 840 tokens de contexte, bon en code | Q4_0, prompt eval ~2× plus lent, pas de `tools` |
| Raisonnement général, 14B | `qwen3:14b` | 8,8 Go, 40k contexte, raisonnement | Génère du *thinking*, perturbe Aider, moins bon qu'un modèle code dédié |
| Si tu montes à 24 Go+ VRAM | `qwen3-coder:latest` (30,5B) | Top actuel en code (SWE-Bench ~69,6%) | 17,6 Go, ne tient pas dans 12 Go |
| Si tu montes à 48 Go+ VRAM | `qwen3-coder-next:latest` (79,7B MoE) | Meilleur modèle code/agentic disponible | 49 Go, nécessite Ollama récent et beaucoup de VRAM |

- Avec 12 Go, on ne peut pas garder deux modèles en mémoire. Le choix d'un seul modèle (`qwen2.5-coder:14b`) évite les swaps coûteux entre jobs.

### Config `~/.talos/.env`

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
3. Choisir le modèle adapté (par défaut `qwen2.5-coder:14b`, voir section modèles).
4. Vérifier `edit-format: diff` dans `~/.aider.conf.yml`.
5. Choisir `sandbox: true` ou `false` selon le contexte.
6. Définir `validate_cmd` avec le bon Python.
7. Prévoir la mise à jour de `docs/talos-reports.md`.
