# Sentarr — Cahier des charges V3
### Extension : monitoring de contenu étendu à l'écosystème *arr complet, analytics, accès multi-utilisateur, ouverture communautaire

*Prérequis : V1 et V2 complètes, déployées et validées en conditions réelles avant de démarrer cette phase.*

---

## 1. Contexte et objectif

Les V1 et V2 couvrent le cœur du besoin : le pipeline de traitement Plex (V1) et la chaîne d'acquisition Radarr/Sonarr (V2), reliées en une timeline unique. Sentarr occupe déjà, à ce stade, une position que ne couvre aucun outil existant. La V3 vise à élargir cette couverture au reste de l'écosystème *arr (Bazarr, Prowlarr), tout en conservant la ligne directrice qui distingue Sentarr des outils similaires : **le suivi de l'avancement du contenu**, pas la gestion des utilisateurs ni le pilotage manuel des applications *arr elles-mêmes.

**Positionnement V3** : des outils comme Homarr ou Organizr proposent des dashboards généralistes de l'écosystème *arr (liens, statuts de service basiques). Sentarr V3 ne cherche pas à les remplacer, mais à apporter ce qu'ils ne font pas : un suivi fin, au niveau de chaque fichier, de son avancement à travers *tout* l'écosystème — de la recherche d'indexeur jusqu'aux sous-titres, en passant par le traitement Plex.

**Cette version reste volontairement modulaire** : plusieurs blocs sont proposés ci-dessous, mais tous ne sont pas nécessairement à développer — la priorisation est tranchée via le questionnaire de cadrage (section 6) avant de démarrer.

## 2. Blocs de fonctionnalités et modules associés

### Bloc A — Intégration Bazarr (sous-titres)

**Module A1 — Connecteur Bazarr**
- **Fonctionnalités** : interrogation de l'API Bazarr pour l'état de recherche/téléchargement de sous-titres par langue et par item (film ou épisode)
- **Comportement** : complète la catégorie "flux audio/sous-titres" de la V1, qui ne faisait qu'un inventaire statique — avec Bazarr, Sentarr suit désormais la *recherche active* (en cours, trouvé, échoué, langue manquante) plutôt qu'un simple constat
- **Implémentation** : nouveau connecteur implémentant l'interface `AcquisitionConnector` posée en V2, réutilisant le moteur de corrélation existant (chemin de fichier)

### Bloc B — Intégration Prowlarr (indexeurs)

**Module B1 — Connecteur Prowlarr**
- **Fonctionnalités** : état de santé et de latence des indexeurs utilisés par Radarr/Sonarr lors des recherches de la V2
- **Comportement** : permet de contextualiser un blocage détecté en V2 ("aucune release trouvée" peut s'expliquer par un indexeur en panne, visible ici plutôt que dans un outil séparé)
- **Implémentation** : connecteur en lecture seule, affichage croisé avec les alertes du Module 6 de la V2 (une alerte d'acquisition peut désormais afficher "indexeur X en erreur" comme cause probable)

### Bloc C — Analytics et historique

**Module C1 — Agrégation et tendances**
- **Fonctionnalités** : temps moyen de traitement par étape (V1 et V2) sur une période donnée, évolution dans le temps, export CSV/JSON
- **Comportement** : calculs effectués en tâche de fond planifiée (pas en temps réel), pour ne jamais ralentir le dashboard principal
- **Implémentation** : table de snapshots périodiques agrégés, distincte des tables d'événements bruts, avec purge automatique des événements bruts anciens une fois agrégés (pour maîtriser la croissance de la base)

**Module C2 — Détection d'anomalies**
- **Fonctionnalités** : signalement des tâches dont la durée dépasse significativement la moyenne historique observée pour ce type de contenu et cette étape
- **Comportement** : s'appuie sur les données du Module C1 comme référence ; ne remplace pas les alertes à seuil fixe de la V2 mais les complète avec un seuil dynamique
- **Implémentation** : calcul statistique simple (écart par rapport à la moyenne/médiane historique), pas de machine learning — cohérent avec l'objectif de rester un outil léger et compréhensible

### Bloc D — Multi-serveur et scalabilité

**Module D1 — Support multi-serveur Plex**
- **Fonctionnalités** : rattachement de plusieurs instances Plex Media Server distinctes à un seul dashboard Sentarr
- **Comportement** : chaque serveur reste cloisonné dans son propre espace de données, avec une vue de synthèse consolidée en plus des vues par serveur
- **Implémentation** : ajout d'une clé `plex_server_id` sur les tables `libraries`/`movies`/`shows` existantes ; nécessite une migration mais pas de refonte du modèle

**Module D2 — Migration PostgreSQL**
- **Fonctionnalités** : bascule de SQLite vers PostgreSQL si le volume de données (historique + analytics + multi-serveur) le justifie
- **Comportement** : transparente pour les modules fonctionnels grâce à l'usage de l'ORM déjà posé en V1
- **Implémentation** : script de migration de données, mise à jour de la configuration de déploiement (conteneur PostgreSQL additionnel dans le docker-compose)

### Bloc E — Accès et sécurité

**Module E1 — Authentification multi-utilisateur**
- **Fonctionnalités** : comptes utilisateurs avec rôles (admin / lecture seule)
- **Comportement** : n'affecte que l'accès au dashboard — aucune notion de "propriétaire de contenu" n'est introduite, cohérent avec le principe que Sentarr ne gère jamais de données utilisateur côté Plex
- **Implémentation** : couche d'authentification (JWT ou session) ajoutée en frontal de l'API existante, sans modification des modules fonctionnels sous-jacents ; option d'intégration SSO via Authelia si déjà en place devant Traefik dans l'infrastructure existante

**Module E2 — API publique documentée**
- **Fonctionnalités** : documentation OpenAPI/Swagger de l'API de lecture, versionnée (`/api/v1/`)
- **Comportement** : permet à d'autres outils personnels (scripts, dashboards Home Assistant) de consommer les données de Sentarr sans passer par le frontend
- **Implémentation** : génération automatique de la documentation via FastAPI, versionnement explicite pour ne pas casser les consommateurs externes lors de futures évolutions

### Bloc F — Notifications et intégrations domotiques

**Module F1 — Notifications multi-canal avancées**
- **Fonctionnalités** : construction sur le système de webhook générique posé en V2 pour proposer des intégrations riches (embed Discord avec poster/statut, message Telegram, email)
- **Comportement** : configurable par canal et par type d'alerte (ex : erreurs uniquement sur Discord, résumé quotidien par email)
- **Implémentation** : adaptateurs de sortie par canal, branchés sur le même événement d'alerte que le webhook générique de la V2

**Module F2 — Intégration Home Assistant**
- **Fonctionnalités** : exposition de capteurs/entités (ex : nombre de fichiers en erreur, dernier item traité, santé globale de la bibliothèque)
- **Comportement** : mise à jour périodique des entités, cohérente avec le rythme de rafraîchissement du dashboard principal
- **Implémentation** : intégration REST générique Home Assistant (endpoint dédié exposant les valeurs au format attendu) ou MQTT selon préférence exprimée dans le questionnaire de cadrage

### Bloc G — Ouverture communautaire (optionnel)

**Module G1 — Publication et packaging communautaire**
- **Fonctionnalités** : passage du dépôt en public, documentation en anglais, template Unraid Community Applications
- **Comportement** : n'affecte aucun module fonctionnel — c'est un effort de packaging et de documentation, pas de développement
- **Implémentation** : suit le même schéma que la contribution déjà réalisée sur un autre projet personnel (template Unraid CA avec documentation publique complète)

**Module G2 — Système de plugins**
- **Fonctionnalités** : interface simple permettant à des tiers d'ajouter leurs propres connecteurs (autres outils *arr non prévus initialement, autres sources de logs)
- **Comportement** : un plugin déclare quelles étapes de pipeline il alimente et via quelle interface de connecteur ; le cœur de Sentarr n'a pas besoin d'être modifié pour accueillir un nouveau plugin
- **Implémentation** : formalisation de l'interface `AcquisitionConnector` posée en V2 comme point d'extension public, avec chargement dynamique des plugins au démarrage

## 3. Modèle de données — extensions par bloc

```
-- Bloc A
subtitle_events      (id, movie_id (nullable), episode_id (nullable), language,
                       status, provider, timestamp)

-- Bloc B
indexer_status       (id, indexer_name, health, last_checked_at)

-- Bloc C
analytics_snapshots  (id, period_start, period_end, avg_duration_by_step JSON,
                       anomalies JSON, scope[movie/episode])

-- Bloc D
plex_servers         (id, name, base_url, token_ref)
-- + colonne plex_server_id ajoutée sur libraries/movies/shows

-- Bloc E
users                (id, username, role, auth_ref)

-- Bloc G
plugins              (id, name, type, config JSON, enabled)
```

## 4. Plan de développement — phases (V3)

*Les phases correspondent aux blocs A à G et sont indépendantes les unes des autres — elles peuvent être réordonnées ou partiellement écartées selon la priorisation issue du questionnaire.*

- **Phase 0 — Cadrage V3** : priorisation des blocs A à G (section 6), tous ne sont pas obligatoires
- **Phase 1 — Bloc A (Bazarr)** si retenu
- **Phase 2 — Bloc B (Prowlarr)** si retenu
- **Phase 3 — Bloc C (Analytics)**
- **Phase 4 — Bloc D (Multi-serveur / PostgreSQL)** si retenu
- **Phase 5 — Bloc E (Auth / API publique)** si retenu
- **Phase 6 — Bloc F (Notifications avancées / Home Assistant)** si retenu
- **Phase 7 — Bloc G (Ouverture communautaire)** si retenu
- **Phase 8 — Validation finale** : déploiement complet en conditions réelles sur l'ensemble des blocs retenus

## 5. Critères d'acceptation / Definition of Done V3

*À évaluer uniquement sur les blocs effectivement retenus lors du cadrage (section 6, point 1).*

- [ ] Chaque bloc retenu fonctionne de façon autonome sans dégrader les fonctionnalités V1/V2 existantes
- [ ] Aucune action d'écriture n'est introduite sur Plex, Radarr, Sonarr, Bazarr ou Prowlarr par les nouveaux modules
- [ ] Si Bloc C retenu : les calculs d'analytics n'impactent pas les temps de réponse du dashboard temps réel
- [ ] Si Bloc E retenu : l'accès en lecture seule reste possible pour les rôles non-admin, sans exposer de fonction de mutation
- [ ] Si Bloc G retenu : le projet est publiable sans exposer d'information sensible de l'infrastructure de l'utilisateur (tokens, URLs internes) dans le code ou la documentation publique

## 6. Questionnaire de cadrage V3 — à poser avant développement

**Priorisation**
1. Parmi les blocs A à G, lesquels sont réellement souhaités pour cette version, et lesquels peuvent être écartés ou reportés indéfiniment ?

**Intégrations (blocs A, B)**
2. URL/clé API de Bazarr et Prowlarr si ces intégrations sont retenues

**Analytics (bloc C)**
3. Durée de rétention souhaitée pour les événements bruts avant agrégation/purge

**Scalabilité (bloc D)**
4. Le passage à PostgreSQL est-il anticipé comme nécessaire, ou SQLite reste-t-il suffisant à ce stade ?
5. Le support multi-serveur Plex correspond-il à une évolution d'infrastructure réellement prévue, ou est-ce une fonctionnalité "au cas où" ?

**Accès et sécurité (bloc E)**
6. Authelia est-il déjà en place devant Traefik pour le reste de l'infrastructure ? Doit-il être réutilisé pour Sentarr ou une solution d'auth indépendante est-elle préférée ?
7. Si multi-utilisateur retenu : combien de rôles distincts sont réellement nécessaires ?

**Notifications et domotique (bloc F)**
8. Canaux de notification à couvrir en priorité (Discord riche, Telegram, email) et dans quel(s) salon(s)/destinataires
9. Pour Home Assistant : méthode d'intégration préférée (MQTT ou REST générique) et entités/capteurs souhaités

**Ouverture communautaire (bloc G)**
10. Volonté confirmée ou non de publier le projet publiquement, avec quel niveau d'implication dans la maintenance communautaire ?
