# Sentarr — Cahier des charges V1
### Dashboard de suivi des tâches de traitement de contenu Plex

---

## 1. Contexte et objectif

Plex ne fournit aucune visibilité sur l'avancement des tâches internes qu'il exécute pour chaque film ou épisode ajouté à une bibliothèque (scan, identification, récupération de métadonnées, artworks, génération de vignettes, etc.). Ces tâches peuvent être longues, silencieuses, et échouer sans notification claire. Il n'existe à ce jour aucun outil de l'écosystème *arr qui couvre ce besoin — les outils existants (Trackarr, Monitarr, Scoutarr, Tautulli) surveillent soit les files de téléchargement Radarr/Sonarr, soit l'activité des utilisateurs, mais jamais le pipeline de traitement interne de Plex sur le contenu.

**Objectif de la V1** : construire un dashboard autonome, self-hosted, qui donne une vue claire et centralisée de l'état d'avancement de chaque tâche de traitement Plex, pour chaque film et chaque épisode de série, **avec un traitement différencié entre films et séries** — un film est un objet unique et plat, une série est une hiérarchie (Série → Saison → Épisode) où chaque niveau porte ses propres métadonnées et son propre artwork, et où l'état global d'une série doit s'agréger depuis ses épisodes.

## 2. Périmètre

### Inclus dans la V1
- Suivi des tâches liées **uniquement au contenu** (films et séries), catégorie par catégorie
- Une seule instance Plex Media Server
- Toutes les bibliothèques Films et Séries configurées par l'utilisateur (sélection possible)
- **Modèle de suivi distinct et adapté pour les films (plat) et pour les séries (hiérarchique à 3 niveaux)**
- Vue dashboard en lecture seule (aucune action déclenchée sur Plex depuis l'outil)
- Historique des tâches terminées sur une durée configurable

### Exclu de la V1 (renvoyé en V2/V3)
- Toute donnée ou activité liée aux utilisateurs (lecture, visionnage, sessions) — hors périmètre définitivement
- Intégration Radarr/Sonarr/Bazarr/Prowlarr et suivi de la chaîne d'acquisition (V2)
- Notifications push (Discord, Telegram, email) (V2)
- Authentification multi-utilisateur (V3)
- Support multi-serveur Plex (V3)

## 3. Public cible et cas d'usage

Utilisateur unique, administrateur de son propre serveur Plex (homelab), qui veut répondre à des questions comme :
- "Ce film que je viens d'ajouter, Plex a-t-il fini de le traiter ou c'est encore en cours ?"
- "Cette série a 10 saisons, laquelle a des épisodes encore en cours de traitement ?"
- "Cette saison affiche 22/24 épisodes prêts — que se passe-t-il pour les 2 restants ?"
- "Pourquoi ce film n'a toujours pas d'affiche 3 heures après l'ajout ?"
- "Combien de fichiers sont actuellement en erreur de métadonnées dans ma bibliothèque ?"

---

## 4. Modèle fonctionnel — la distinction Films / Séries

C'est le point structurant de toute la V1 : **les films et les séries ne suivent pas le même pipeline ni la même hiérarchie d'affichage**, et l'outil doit les traiter comme deux domaines fonctionnels distincts partageant la même infrastructure technique.

### 4.1 Domaine Films (modèle plat)

Un film = un seul objet = un seul fichier = un seul jeu de métadonnées/artworks. Pipeline linéaire à 9 étapes (identique à la V1 initiale) :

| # | Étape | Détail |
|---|---|---|
| 1 | Détection / Scan | Fichier détecté par Plex, scan lancé, scan terminé |
| 2 | Identification | Recherche de correspondance TMDb, résultat trouvé / ambigu / échoué |
| 3 | Métadonnées | Synopsis, casting, réalisateur, genres, notes |
| 4 | Artworks | Poster, fanart/background |
| 5 | Vignettes de prévisualisation (BIF) | Timeline miniature pour la barre de progression |
| 6 | Marqueurs intro/générique | Si applicable/activé |
| 7 | Chapitres | Extraction/génération |
| 8 | Flux audio/sous-titres | Inventaire des pistes disponibles |
| 9 | Statut global | Agrégat des 8 étapes précédentes |

### 4.2 Domaine Séries (modèle hiérarchique à 3 niveaux)

Une série n'est pas un objet unique : c'est une arborescence **Série → Saison → Épisode**, et **chaque niveau a ses propres tâches Plex**, distinctes de celles des épisodes qu'il contient :

```
SÉRIE (ex: "Breaking Bad")
 ├─ Identification de la série (TheTVDB), métadonnées série (synopsis, réseau, statut, genres)
 ├─ Artworks série (poster série, banner, background, thème musical si applicable)
 │
 ├─ SAISON 1
 │   ├─ Artwork de saison (poster de saison — distinct du poster de série)
 │   ├─ Métadonnées de saison (rares mais existantes : résumé de saison si dispo)
 │   │
 │   ├─ ÉPISODE 1
 │   │   ├─ Détection / scan du fichier
 │   │   ├─ Identification (matching sur le bon numéro de saison/épisode — source d'erreurs fréquente)
 │   │   ├─ Métadonnées épisode (titre, synopsis, date de diffusion, guest cast)
 │   │   ├─ Artwork épisode (vignette/still de l'épisode — distinct de l'artwork de saison/série)
 │   │   ├─ Vignettes de prévisualisation (BIF)
 │   │   ├─ Marqueurs intro/générique
 │   │   ├─ Chapitres (rares sur les épisodes)
 │   │   ├─ Flux audio/sous-titres
 │   │   └─ Statut global épisode
 │   ├─ ÉPISODE 2
 │   │   └─ (même pipeline)
 │   └─ ... (statut de la saison = agrégat des épisodes de la saison)
 │
 └─ SAISON 2 ...
     (statut de la série = agrégat de toutes les saisons)
```

**Règles d'agrégation** (à implémenter explicitement, pas laissées à l'appréciation du frontend) :
- Le statut d'une **saison** = fonction du statut de ses épisodes (ex : "22/24 épisodes prêts", statut global "en cours" tant qu'au moins un épisode n'est pas prêt, "erreur" si au moins un épisode est en erreur même si les autres sont prêts)
- Le statut d'une **série** = fonction du statut de ses saisons + de son propre pipeline série (identification/métadonnées/artwork série)
- Une série peut être "en cours d'ajout" (nouvelle saison en cours de scan) sans que les saisons précédentes soient affectées — les statuts ne doivent jamais se propager vers le bas (le statut d'une saison n'affecte pas ses épisodes) mais toujours remonter vers le haut (le statut des épisodes détermine celui de la saison, celui des saisons détermine celui de la série)

### 4.3 Conséquence sur le modèle de données

Le schéma doit représenter explicitement cette hiérarchie plutôt que de forcer les séries dans le même modèle plat que les films — voir section 6.

---

## 5. Modules — architecture fonctionnelle détaillée

### Module 1 — Collecteur Plex API
**Rôle** : interroger périodiquement l'API Plex Media Server pour obtenir l'état déclaratif de chaque item (films, séries, saisons, épisodes).

**Fonctionnalités** :
- Lister les bibliothèques configurées et leur type (movie/show)
- Pour les films : récupérer la liste des items avec leurs champs (`thumb`, `art`, `summary`, `duration`, présence de chapitres, flux disponibles)
- Pour les séries : récupérer la structure complète série → saisons → épisodes via les endpoints hiérarchiques de l'API Plex (`/library/metadata/{ratingKey}/children`), avec les champs propres à chaque niveau
- Déduire l'état de certaines tâches à partir de la simple présence/absence de champs (ex : `thumb` renseigné = artwork récupéré)

**Comportement** : polling à intervalle configurable (voir questionnaire section 9), avec limitation de charge pour ne pas solliciter excessivement le serveur Plex (requêtes incrémentales basées sur `updatedAt` quand disponible plutôt que re-scan complet à chaque cycle).

**Implémentation** : service Python utilisant `plexapi`, exécuté comme tâche planifiée (scheduler interne, type `APScheduler`), écrit dans le modèle de données via le Module 3 (moteur de corrélation).

---

### Module 2 — Parseur de logs Plex
**Rôle** : lire en continu le fichier de log de Plex Media Server pour capturer les événements précis que l'API seule ne fournit pas (début de scan, tentative de matching échouée, génération de vignettes en cours, erreurs détaillées).

**Fonctionnalités** :
- Suivi du fichier de log en continu (tail -f applicatif, avec gestion de la rotation de logs)
- Bibliothèque de règles de parsing (regex/patterns) par type d'événement, organisée pour être facilement étendue si le format de log change entre versions de Plex Media Server
- Extraction du chemin de fichier et/ou de l'identifiant Plex (`ratingKey`) présent dans la ligne de log, utilisé comme clé de corrélation

**Comportement** : chaque ligne parsée avec succès génère un événement horodaté stocké en base (`log_events_raw`), puis transmis au moteur de corrélation. Les lignes non reconnues sont ignorées silencieusement (pas d'erreur bloquante) mais comptabilisées pour audit (voir Module 6).

**Implémentation** : service Python dédié, utilisant `watchdog` pour la détection de changement de fichier, thread séparé du collecteur API pour ne pas bloquer le polling.

---

### Module 3 — Moteur de corrélation et modèle Films/Séries
**Rôle** : cœur fonctionnel de l'outil. Fusionne les données du Module 1 (API) et du Module 2 (logs) dans le modèle de données différencié Films/Séries, et calcule les statuts agrégés.

**Fonctionnalités** :
- Résolution de la clé de corrélation (par `ratingKey` en priorité, par chemin de fichier en secours)
- Application du pipeline approprié selon le type d'item (film = pipeline plat à 9 étapes ; épisode = pipeline propre à l'épisode + propagation vers saison/série)
- Calcul et mise à jour continue des statuts agrégés (saison, série) à chaque changement d'état d'un épisode
- Détection des cas particuliers : épisode sans saison identifiée (mal classé), item détecté deux fois (doublon), tâche "non applicable" selon le contexte (voir section 9, point 11)

**Comportement** : s'exécute en réaction aux événements entrants (API ou logs), pas en polling séparé — c'est un composant réactif au centre du flux de données.

**Implémentation** : module Python pur (pas de dépendance externe lourde), avec une suite de règles unitaires testables indépendamment (une règle = un type d'événement en entrée → une mise à jour d'état en sortie), pour faciliter la maintenance et l'ajout de nouvelles règles.

---

### Module 4 — Persistance (base de données)
**Rôle** : stocker durablement l'état de tous les items suivis, leur historique de tâches, et les événements bruts.

**Fonctionnalités** : voir schéma détaillé section 6.

**Comportement** : SQLite en V1 (usage mono-utilisateur, charge faible), avec migrations gérées via un outil léger (`alembic` ou équivalent) pour permettre l'évolution du schéma sans perte de données lors des futures versions.

**Implémentation** : accès via un ORM léger (`SQLModel` ou `SQLAlchemy`) pour garder la possibilité de migrer vers PostgreSQL en V2/V3 sans réécriture complète de la couche d'accès aux données.

---

### Module 5 — API backend
**Rôle** : exposer les données du modèle aux clients (frontend), en lecture seule.

**Fonctionnalités** :
- Endpoints REST distincts pour le domaine Films (`/api/movies`, `/api/movies/{id}`) et le domaine Séries (`/api/shows`, `/api/shows/{id}`, `/api/shows/{id}/seasons/{n}`, `/api/shows/{id}/seasons/{n}/episodes/{m}`)
- Filtres (bibliothèque, statut, texte libre) appliqués sur les deux domaines
- Canal WebSocket poussant les mises à jour de statut en temps réel vers le frontend, sans que celui-ci ait à re-solliciter l'API en polling
- Endpoint de synthèse globale (compteurs agrégés tous domaines confondus)

**Comportement** : API strictement en lecture — aucun endpoint de mutation n'existe en V1, conformément à la contrainte de sécurité (section 8).

**Implémentation** : FastAPI, avec schémas Pydantic distincts pour les objets Film et Série/Saison/Épisode (pas de modèle générique unique forcé — cohérent avec le choix fonctionnel de la section 4).

---

### Module 6 — Frontend Dashboard
**Rôle** : interface utilisateur, avec des vues volontairement différentes pour les deux domaines.

**Fonctionnalités** :
- **Vue Films** : grille/liste plate, un item = une ligne/carte, badge de statut global, filtres et recherche
- **Vue Séries** : arborescence dépliable (Série → Saisons → Épisodes), avec barres de progression agrégées à chaque niveau (ex : série "87 % prêt — 7/8 saisons complètes", saison "22/24 épisodes prêts") ; possibilité de déplier une saison pour voir le détail épisode par épisode sans changer de page
- **Vue détail** (film ou épisode) : timeline complète des étapes du pipeline avec horodatages et erreurs
- **Vue synthèse globale** : compteurs croisés films/séries (en cours / terminé / en erreur / en attente), liste des tâches les plus anciennes non terminées (candidates au blocage), et un compteur de lignes de log non reconnues (audit du Module 2)
- Recherche par titre, cross-domaine (films et séries dans la même barre de recherche)

**Comportement** : mise à jour en temps réel via le WebSocket du Module 5, sans rechargement de page.

**Implémentation** : application web React/Vite, thème sombre cohérent avec l'écosystème *arr, composant d'arborescence dépliable réutilisable entre la vue Séries et la vue détail.

---

### Module 7 — Configuration et déploiement
**Rôle** : rendre l'outil facilement déployable et configurable dans l'infrastructure existante.

**Fonctionnalités** :
- Configuration via variables d'environnement (token Plex, URL, chemin des logs, bibliothèques à surveiller, fréquence de polling)
- Healthcheck Docker exposant l'état interne du service (collecteur actif, dernier scan réussi)

**Comportement** : démarrage résilient — si le fichier de log n'est pas accessible au démarrage, le Module 1 (API) continue de fonctionner en mode dégradé plutôt que de faire crasher tout le service.

**Implémentation** : conteneur Docker unique packageant backend + frontend (ou deux conteneurs légers via docker-compose selon simplicité de maintenance), volumes dédiés pour la base de données et pour le montage en lecture seule du fichier de log Plex.

---

## 6. Modèle de données détaillé

```
libraries         (id, plex_library_id, name, type[movie/show])

-- Domaine Films (plat)
movies            (id, plex_rating_key, library_id, title, year, file_path, added_at)
movie_tasks       (id, movie_id, task_type[enum 9 catégories], status, progress_percent,
                    started_at, completed_at, error_message, last_checked_at)

-- Domaine Séries (hiérarchique)
shows             (id, plex_rating_key, library_id, title, year, added_at)
show_tasks        (id, show_id, task_type[identification/metadata/artwork_show], status,
                    started_at, completed_at, error_message)
seasons           (id, show_id, plex_rating_key, season_number)
season_tasks      (id, season_id, task_type[artwork_season/metadata_season], status,
                    started_at, completed_at, error_message)
episodes          (id, season_id, plex_rating_key, episode_number, title, file_path, added_at)
episode_tasks     (id, episode_id, task_type[enum 9 catégories], status, progress_percent,
                    started_at, completed_at, error_message, last_checked_at)

-- Commun
log_events_raw    (id, timestamp, raw_line, parsed[bool], correlated_to_type, correlated_to_id)
```

Le choix de **tables séparées `movie_tasks` / `episode_tasks`** plutôt qu'une table `tasks` générique polymorphe est délibéré : les deux domaines ont des cycles de vie et des règles d'agrégation différents, et cette séparation évite les colonnes nullable en pagaille et les requêtes conditionnelles complexes.

---

## 7. Dashboard — maquette fonctionnelle (description)

- **Page d'accueil / synthèse** : deux blocs côte à côte, "Films" et "Séries", chacun avec ses propres compteurs (en cours / prêt / erreur)
- **Page Films** : grille de cartes (poster + titre + badge de statut), clic → vue détail
- **Page Séries** : liste de séries (poster + titre + barre de progression globale), clic → dépliage des saisons → dépliage des épisodes, chaque niveau affichant sa propre barre de progression
- **Vue détail film/épisode** : timeline verticale des étapes du pipeline avec icônes de statut et horodatages

---

## 8. Contraintes techniques et sécurité

- Conteneur Docker déployable sur Unraid, intégré au réseau Traefik existant
- Accès en **lecture seule** au token Plex — aucune action d'écriture possible sur le serveur Plex depuis Sentarr
- Accès en lecture au fichier de log Plex via volume Docker monté en lecture seule
- Aucune dépendance à un compte cloud tiers — 100 % local/self-hosted
- Pas d'authentification applicative en V1 — protection via le réseau local/reverse proxy existant
- Token Plex fourni via variable d'environnement, jamais exposé côté frontend

---

## 9. Plan de développement — phases (V1)

*Aucune tâche n'est estimée en durée : chaque phase se termine quand son livrable est validé, pas à une date.*

- **Phase 0 — Cadrage** : réponses au questionnaire opérationnel (section 11) obtenues
- **Phase 1 — Socle technique** : structure du repo, squelette Docker/docker-compose, connexion API Plex basique (Module 1), listant bibliothèques + items plats (films) uniquement
- **Phase 2 — Modèle Séries** : extension du Module 1 pour la hiérarchie série/saison/épisode, mise en place du schéma hiérarchique (Module 4)
- **Phase 3 — Parseur de logs** : Module 2 complet, validé sur un échantillon réel de logs fourni par l'utilisateur
- **Phase 4 — Moteur de corrélation** : Module 3 complet, y compris les règles d'agrégation saison/série
- **Phase 5 — API backend** : Module 5, endpoints REST distincts films/séries + WebSocket
- **Phase 6 — Frontend** : Module 6, vue Films (grille plate) puis vue Séries (arborescence dépliable) puis vue détail et synthèse
- **Phase 7 — Gestion des erreurs et cas limites** : items mal classés, doublons, tâches non applicables, redémarrage sans perte d'état
- **Phase 8 — Packaging final** : Module 7, Dockerfile, docker-compose.yml, documentation d'installation
- **Phase 9 — Validation** : déploiement réel sur l'infrastructure de l'utilisateur, vérification sur la bibliothèque complète (films et séries) en conditions réelles

---

## 10. Critères d'acceptation / Definition of Done V1

- [ ] Le dashboard affiche tous les films avec le statut des 9 catégories de tâches, en vue plate
- [ ] Le dashboard affiche toutes les séries en arborescence Série → Saison → Épisode, avec statuts agrégés cohérents à chaque niveau
- [ ] Un épisode mal identifié (mauvaise saison/numéro) est visible comme cas d'erreur distinct
- [ ] Les statuts se mettent à jour sans intervention manuelle (polling + logs en continu)
- [ ] Le service redémarre proprement sans perdre l'historique déjà collecté
- [ ] L'outil tourne en conteneur Docker unique, intégré au reverse proxy existant
- [ ] Aucune action d'écriture n'est possible sur le serveur Plex depuis l'outil

---

## 11. Questionnaire de cadrage — à poser à l'utilisateur AVANT tout développement

**Accès et environnement Plex**
1. URL/IP et port du serveur Plex Media Server, et méthode d'obtention du token
2. Chemin exact du fichier de log Plex Media Server sur l'hôte, et version exacte de Plex Media Server utilisée
3. Bibliothèques à surveiller : toutes, ou une sélection précise (noms) ?

**Comportement et fréquence**
4. Fréquence de rafraîchissement souhaitée pour le polling API
5. Durée de rétention souhaitée pour l'historique des tâches terminées
6. Rétro-scan initial des items déjà présents avant l'installation de Sentarr, ou uniquement les nouveaux ajouts à partir du déploiement ?

**Déploiement**
7. Réseau Docker et sous-domaine Traefik souhaités pour l'exposition
8. SQLite suffisant, ou préférence pour PostgreSQL dès la V1 ?

**Interface**
9. Préférence de style visuel : thème sombre standard façon *arr, ou style spécifique déjà utilisé ailleurs (ex. glassmorphism) ?
10. Niveau de détail voulu pour les erreurs affichées : message simplifié, ou log brut disponible en un clic ?

**Cas particuliers**
11. Comment gérer les tâches "non applicables" selon le contexte (ex. marqueurs intro non disponibles sans Plex Pass) — affichées comme "ignoré" ou masquées de la vue ?
12. Pour les séries : faut-il afficher une saison "vide" (annoncée mais sans aucun épisode encore ajouté) dans l'arborescence, ou seulement les saisons ayant au moins un fichier ?
