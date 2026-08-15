# Instructions d'utilisation de Talos — Sentarr

> À relire avant chaque utilisation de Talos (CLI, MCP `talos_*`, soumission de job).

## Modèles et endpoint Ollama

- Modèle rapide/lent local : `ollama/qwen2.5-coder:14b`.
- Endpoint Ollama : `http://10.20.0.4:11434` (via VPN AkashaVPN).
- Format d'édition Aider : `diff` (SEARCH/REPLACE), activé dans `~/.aider.conf.yml`.

## Workflow de sécurité

1. **Sandbox par défaut** : les jobs doivent utiliser le sandbox (`TALOS_AUTO_APPLY=false`) sauf exception justifiée.
2. **Validation dans le venv projet** : utiliser `/home/jerem/workspace/talos/.venv/bin/python3 -m pytest ...` ou le venv du projet Sentarr, car le `python3` par défaut du daemon n'a pas pytest.
3. **Revue manuelle obligatoire** avant d'appliquer tout fichier généré par Talos.
4. **Pas de secrets** dans les prompts, les fichiers générés ou les validations.
5. **Réessai max 3 fois** par job. En cas d'échec persistant, implémenter manuellement mais continuer à utiliser Talos pour les jobs suivants.

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
