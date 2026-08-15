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

## 2026-08-15 — Test d'appel via MCP

- **Job ID** : `248859a1`
- **Label** : `talos-mcp-test`
- **Fichiers concernés** : `/tmp/talos-mcp-test/utils.py`, `test_utils.py` (sandbox)
- **Provider** : `ollama/qwen2.5-coder:14b`
- **Validation** : `/home/jerem/workspace/talos/.venv/bin/python3 -m pytest test_utils.py -q` ❌
- **Résultat** : la fonction `slugify` laissait des tirets en début/fin de chaîne ; l'auto-fix n'a pas corrigé en un seul essai.

### Évaluation

⚠️ Partiel — le MCP fonctionne (soumission + retour de statut), mais le modèle fait encore des erreurs de logique sur les cas de bord.

## Synthèse — Préparation aux gros travaux

### Ce qui fonctionne ✅

- Daemon Talos démarre et communique via CLI et MCP.
- Ollama distant (`10.20.0.4`) est joignable via VPN.
- `qwen2.5-coder:14b` rentre dans 12 Go de VRAM avec 32 768 tokens de contexte.
- Format d'édition SEARCH/REPLACE activé (`edit-format: diff` dans `~/.aider.conf.yml`).
- Sandbox actif par défaut, pas d'écriture directe sur le repo (`TALOS_AUTO_APPLY=false`).

### Ce qui reste à surveiller ⚠️

- Le `python3` par défaut du daemon n'a pas pytest : il faut utiliser le venv du projet dans `validate_cmd` ou installer les dépendances dans l'environnement du daemon.
- L'auto-fix avec `TALOS_MAX_FIX_ATTEMPTS=1` ne suffit pas toujours ; les cas de bord (négatifs, espaces) peuvent échapper au modèle.
- Le provider affiché par `talos providers` indique `ollama/qwen3-coder:latest` (fallback `DEFAULT_MODEL`) alors que les jobs utilisent réellement `qwen2.5-coder:14b` — affichage cosmétique.
- Le serveur MCP a chargé l'ancienne `.env` en mémoire : il faut le redémarrer pour que `talos_list_providers` reflète la nouvelle config.

### Verdict

**Feu vert conditionnel.** Talos est prêt pour des travaux supervisés de refactoring et de génération de code modulaire. Il n'est pas encore autonome pour des tâches complexes sans revue humaine.
