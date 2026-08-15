# Instructions d'utilisation de Talos — Sentarr

> À relire avant chaque utilisation de Talos (CLI, MCP `talos_*`, soumission de job).

## Modèles et endpoint Ollama

- Modèle rapide/lent local : `ollama/qwen2.5-coder:14b`.
- Endpoint Ollama : `http://10.20.0.4:11434` (via VPN AkashaVPN), configuré dans `~/.talos/.env`.
- Chaîne de fallback automatique si 10.20.0.4 ne répond pas :
  1. `10.20.0.4:11434`
  2. `192.168.1.100:11434`
  3. `192.168.1.16:11434`
  4. `127.0.0.1:11434` (dernier recours)
- Le premier endpoint sain est sélectionné avec un cache de 30 s.
- Format d'édition Aider : `diff` (SEARCH/REPLACE), activé dans `~/.aider.conf.yml`.

## Workflow de sécurité

1. **Sandbox par défaut** : les jobs doivent utiliser le sandbox (`TALOS_AUTO_APPLY=false`) sauf exception justifiée.
2. **Validation dans le venv projet** : utiliser `/home/jerem/workspace/talos/.venv/bin/python3 -m pytest ...` ou le venv du projet Sentarr, car le `python3` par défaut du daemon n'a pas pytest.
3. **Revue manuelle obligatoire** avant d'appliquer tout fichier généré par Talos.
4. **Pas de secrets** dans les prompts, les fichiers générés ou les validations.
5. **Réessai max 3 fois** par job. En cas d'échec persistant, implémenter manuellement mais continuer à utiliser Talos pour les jobs suivants.

## Découpage des jobs — limite de tokens

- Le modèle `qwen2.5-coder:14b` a une fenêtre de contexte limitée ; un prompt trop gros ou une tâche trop large fait perdre en précision et peut échouer ou dépasser la fenêtre.
- **Préférer plusieurs petits jobs indépendants** plutôt qu'un seul job monolithique.
- Chaque job doit viser un objectif atomique (ex : un modèle, un endpoint, un composant, un test) avec sa propre commande de validation.
- Pour des travaux complexes comme le **Guru**, découper en étapes successives :
  1. définition du modèle de données,
  2. API de base,
  3. logique métier,
  4. tests,
  5. composant frontend,
- Utiliser `talos chain <batch_id>` pour exécuter et relier les étapes sans avoir à les attendre une par une.

## Rapports

- Consigner chaque utilisation de Talos dans `docs/talos-reports.md`.
- Noter le job ID, le provider, la validation, le résultat et les apprentissages.

## Vérification pré-job

- [ ] VPN AkashaVPN actif (ping `10.20.0.4`).
- [ ] Ollama répond (`ollama list` via le endpoint configuré).
- [ ] Le modèle `qwen2.5-coder:14b` est disponible.
- [ ] Le prompt est atomique, isolé et inclut la validation attendue.

## Post-job

- [ ] Relire le diff proposé.
- [ ] Vérifier qu'aucun secret/token n'apparaît.
- [ ] Lancer les tests/linters dans le bon venv.
- [ ] Mettre à jour `docs/talos-reports.md`.
- [ ] Évaluer le job avec `talos review <job_id>` si le résultat est notable (note, feedback, motif d'échec).

## Statistiques, review, score et économie de tokens

### Statistiques automatiques

- Talos agrège les exécutions dans `~/.talos/stats.json` :
  - nombre de runs, statuts, providers, sources ;
  - validations passées/échouées ;
  - durée totale et moyenne ;
  - tokens envoyés/reçus ;
  - équivalent `devin_offload` (temps + tokens épargnés à Devin).
- `talos report` génère un rapport Markdown de la file active.
- `talos status` et `talos dashboard` affichent l'état live.

### Review et score

- `talos review <job_id>` permet d'évaluer un job terminé (score 0–10, feedback, correction optionnelle).
- La review alimente `LearningStore` pour construire un *negative preamble* (jusqu'à 3 motifs d'échec connus) injecté dans les prompts suivants du même modèle.
- Le score est **manuel** : Talos ne note pas automatiquement la qualité d'un livrable.
- `talos chain <batch_id>` permet d'attendre et reviewer une chaîne de jobs.

### Coût / économies

- Talos calcule un **coût estimé par job** dans `~/.talos/stats.json` :
  - `cost.estimated_devin_cost_usd` : ce qu'aurait coûté le même volume de tokens en usage Devin/API ;
  - `cost.estimated_talos_cost_usd` : coût de l'inférence locale (Ollama) ;
  - `cost.estimated_savings_usd` = Devin − Talos.
- Le tarif Devin est configurable via `TALOS_DEVIN_COST_PER_1M_TOKENS` (défaut : `5.0` USD / million de tokens).
- Le coût Talos est configurable via `TALOS_TALOS_COST_PER_1M_TOKENS` (défaut : `0.0` pour Ollama local).
- Les agrégations sont aussi par modèle dans `by_model`.
- `talos report` affiche le total et les économies.
