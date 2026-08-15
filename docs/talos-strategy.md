# Stratégie d'utilisation de Talos — Sentarr

## Objectif

Talos est utilisé comme outil de génération de code auxiliaire. Il doit soulager une partie du travail en produisant des morceaux isolés, pendant que le développement principal continue ailleurs.

## Principes d'utilisation

1. **Morceaux isolés** : chaque job Talos porte sur une tâche précise et limitée (un fichier, une fonction, un composant).
2. **Vérification systématique** : tout résultat de Talos est relu et validé avant intégration. On ne copie-colle pas aveuglément.
3. **Réessai** : si un job échoue (résultat incorrect ou validation KO), on réessaie jusqu'à 3 fois avec un prompt affiné.
4. **Pas d'abandon** : un échec sur un job ne doit pas empêcher d'utiliser Talos sur les jobs suivants.
5. **Rapport** : chaque utilisation de Talos est consignée pour l'aider à progresser, qu'il réussisse ou échoue.

## Types de jobs adaptés à Talos

- Génération de code répétitif ou mécanique :
  - Schémas Pydantic pour les endpoints API.
  - Modèles SQLModel répétitifs.
  - Composants React simples (StatusBadge, ProgressBar, LoadingIndicator).
  - Fichiers de configuration initiaux (Dockerfile, docker-compose, .env.example).
- Parsing de formats connus :
  - Patterns regex pour les logs Plex (avec validation sur un échantillon).
- Tests unitaires ciblés :
  - Tests pour une règle de corrélation donnée.
- Documentation structurée :
  - Templates de documents.

## Types de jobs à NE PAS déléguer à Talos

- Architecture globale et décisions de conception.
- Moteur de corrélation (logique métier critique).
- Gestion des secrets et sécurité.
- Configuration de déploiement sur l'infrastructure réelle.
- Revue finale avant merge.

## Workflow d'un job Talos

1. **Préparation du prompt** :
   - Contexte clair (fichiers ou snippets pertinents).
   - Objectif précis.
   - Contraintes (style KSP, pas de secrets, langage).
   - Commande de validation si possible (`pytest tests/...`, `ruff check`, etc.).

2. **Soumission** via `talos_add` ou `talos_add_batch`.

3. **Suivi** via `talos_status` ou `talos_batch_status` (non bloquant).

4. **Validation** du résultat :
   - Lire les fichiers proposés.
   - Vérifier la cohérence avec le reste du code.
   - Lancer les tests/linters.
   - Si KO : relancer jusqu'à 3 fois.

5. **Intégration** manuelle si nécessaire après échecs.

6. **Rapport** :
   - Job, prompt, résultat, problèmes rencontrés, corrections apportées.
   - À consigner dans `docs/talos-reports.md` ou un fichier équivalent.

## Exemple de prompt

```
Crée le fichier backend/sentarr/models/movies.py contenant les modèles SQLModel suivants :
- Library
- Movie
- MovieTask

Contraintes :
- Utilise SQLModel.
- Types Python 3.12 avec annotations optionnelles.
- Colonne status de type enum interne (MovieTaskStatus).
- Pas de logique métier, uniquement les modèles.
- Suit le style du projet Sentarr (voir docs/development.md).

Validation : python -m py_compile backend/sentarr/models/movies.py
```

## Batchs suggérés pour le démarrage du projet

### Batch « socle backend »

- Modèles SQLModel (`models/base.py`, `models/movies.py`, `models/shows.py`).
- Configuration Pydantic (`config.py`).
- Début du module FastAPI (`main.py`) avec health endpoint.

### Batch « composants UI de base »

- `StatusBadge.tsx`
- `ProgressBar.tsx`
- `LoadingIndicator.tsx`
- `Timeline.tsx`

### Batch « parsing logs Plex »

- Patterns regex pour quelques événements clés (scan, matching, BIF).
- Tests sur un échantillon de logs réel fourni.

## Rapports Talos

Les rapports sont stockés dans `docs/talos-reports.md` (à créer au premier usage).
Chaque entrée contient :
- Date et job ID.
- Description du job.
- Prompt utilisé (résumé).
- Évaluation : réussi / partiel / échoué.
- Problèmes constatés et corrections.
- Apprentissages pour les prochains prompts.
