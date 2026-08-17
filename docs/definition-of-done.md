# Definition of Done — Sentarr

## V1 — Pipeline Plex Films/Séries

- [ ] Le dashboard affiche tous les films de toutes les bibliothèques `movie` configurées, avec le statut des 9 catégories de tâches, en vue plate.
- [ ] Le dashboard affiche toutes les séries de toutes les bibliothèques `show` configurées, en arborescence Série → Saison → Épisode.
- [ ] Les statuts agrégés saison/série sont cohérents avec les statuts des épisodes (propagation ascendante uniquement).
- [ ] Un épisode mal identifié (mauvaise saison/numéro) est visible comme cas d'erreur distinct.
- [ ] Les statuts se mettent à jour sans intervention manuelle (polling API Plex + lecture continue des logs).
- [ ] Le service redémarre proprement sans perdre l'historique déjà collecté (SQLite/PostgreSQL persistant via volume).
- [ ] L'outil tourne en conteneur Docker intégré au reverse proxy Traefik existant sur `sentarr.drac-lab.fr`.
- [ ] Aucune action d'écriture n'est possible sur le serveur Plex depuis Sentarr (lecture seule API + logs).
- [ ] Les tâches non applicables sont marquées comme `not_applicable` et affichées comme telles (non masquées par défaut).
- [ ] Les lignes de log Plex non reconnues sont comptabilisées et accessibles dans la vue synthèse.
- [ ] L'interface respecte le thème sombre *arr et affiche un indicateur de chargement sur les items dont une tâche est `in_progress`.

## V2 — Chaîne d'acquisition Radarr/Sonarr

- [ ] Deux instances Radarr/Sonarr peuvent être configurées sans collision d'ID.
- [ ] Chaque item recherché par Radarr/Sonarr est visible dans la vue Acquisition avec son statut réel et sa progression.
- [ ] Le support multi-instance est fonctionnel (badge qualité `1080p`, `4K`, etc.).
- [ ] Chaque item importé apparaît automatiquement relié à son item Plex correspondant, sans intervention manuelle.
- [ ] Le délai entre "Importé" (étape 6) et "Détecté par Plex" (étape 7) est visible et mis en évidence dans la timeline unifiée.
- [ ] Un score de santé cohérent (0–100) est affiché pour chaque item, sur l'ensemble de la chaîne acquisition + Plex.
- [ ] Une alerte se déclenche correctement au dépassement d'un seuil configuré, et se résout automatiquement dès que la situation se débloque.
- [ ] Le système de notifications Apprise déclenche une notification multi-canaux (Discord, ntfy, etc.) lors de l'apparition/résolution d'une alerte.
- [ ] Aucune action d'écriture n'est effectuée sur Radarr, Sonarr ou Plex.
- [ ] L'historique des tentatives d'acquisition (release échouée puis nouvelle recherche) reste visible.
- [ ] Panne d'une instance *arr isolée et visible dans `/api/v1/health` ; le reste de l'application continue de fonctionner.
- [ ] Aucun secret, URL interne d'infrastructure ou token n'est commité.
- [ ] Migration réversible et compatibilité des endpoints Sentarr V1 vérifiée.

## V3 — Extensions

Critères à évaluer uniquement sur les blocs retenus lors du cadrage V3.

- [ ] Chaque bloc retenu fonctionne de façon autonome sans dégrader les fonctionnalités V1/V2 existantes.
- [ ] Aucune action d'écriture n'est introduite sur Plex, Radarr, Sonarr, Bazarr ou Prowlarr par les nouveaux modules.
- [ ] Si Bloc C (Analytics) retenu : les calculs d'analytics n'impactent pas les temps de réponse du dashboard temps réel (tâche de fond planifiée).
- [ ] Si Bloc D (Multi-serveur) retenu : plusieurs serveurs Plex peuvent être suivis dans un même dashboard avec vue consolidée.
- [ ] Si Bloc E (Auth) retenu : l'accès en lecture seule reste possible pour les rôles non-admin, sans exposer de fonction de mutation.
- [ ] Si Bloc F (Notifications avancées) retenu : au moins 3 canaux distincts (Discord, ntfy, email) sont opérationnels via Apprise.
- [ ] Si Bloc G (Ouverture communautaire) retenu : le projet est publiable sans exposer d'information sensible de l'infrastructure (tokens, URLs internes) dans le code ou la documentation publique.
- [ ] Si API publique retenue : la documentation OpenAPI est disponible et versionnée (`/api/v1/`).
