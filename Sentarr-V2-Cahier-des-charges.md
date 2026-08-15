# Sentarr — Cahier des charges V2
### Extension : suivi complet de la chaîne d'acquisition (recherche → téléchargement → import) et pipeline unifié jusqu'à Plex

*Prérequis : V1 complète, déployée et validée en conditions réelles avant de démarrer cette phase.*

---

## 1. Contexte et objectif

La V1 couvre ce qui se passe **une fois le fichier arrivé sur le disque et détecté par Plex**. Mais avant cela, une chaîne complète et souvent opaque s'est déjà déroulée : Radarr/Sonarr a cherché une release, l'a envoyée à un client de téléchargement, a suivi sa progression, puis l'a importée. C'est exactement le terrain occupé aujourd'hui par des outils comme **Monitarr** (vue simple des téléchargements en cours) et **Trackarr** (health score et détection de blocage sur les items en cours d'acquisition) — mais aucun des deux ne va jusqu'à relier cette chaîne à ce qui se passe *ensuite* dans Plex.

**Objectif de la V2** : réimplémenter, à l'intérieur de Sentarr, un niveau de suivi de la chaîne d'acquisition comparable à ce que proposent Monitarr et Trackarr (recherche, grab, téléchargement, stall, import), **mais en le reliant nativement au pipeline de traitement Plex de la V1** pour obtenir une vue de bout en bout qu'aucun outil existant ne propose aujourd'hui : de la recherche d'une release jusqu'à la disponibilité complète dans Plex, en un seul dashboard.

## 2. Périmètre

### Inclus dans la V2
- Connexion en lecture seule aux API Radarr et Sonarr (multi-instance : ex. profils 1080p / 4K séparés)
- Suivi complet de la chaîne d'acquisition, étape par étape, pour chaque film/épisode recherché :
  Recherché → Release trouvée → Grab (envoyé au client de téléchargement) → Téléchargement en cours (avec progression) → Terminé → Importé
- Détection de blocage (stall) à chaque étape de cette chaîne, avec un score de santé, sur le modèle de ce que fait Trackarr
- Corrélation automatique entre l'item d'acquisition (Radarr/Sonarr) et l'item Plex correspondant (V1), pour obtenir la timeline unifiée complète
- Système d'alertes configurables sur seuils de temps, à n'importe quelle étape de la chaîne (acquisition ou traitement Plex)
- Vue dashboard dédiée à la chaîne d'acquisition, distincte mais reliée à la vue Films/Séries de la V1

### Exclu de la V2 (renvoyé en V3)
- Bazarr, Prowlarr et autres outils *arr
- Notifications multi-canal avancées (webhook simple prévu, intégrations riches en V3)
- Authentification multi-utilisateur
- Support multi-serveur Plex

## 3. Modèle fonctionnel — la chaîne d'acquisition comme pipeline à part entière

Sur le modèle de Monitarr/Trackarr, chaque item recherché par Radarr/Sonarr suit un pipeline propre, indépendant du pipeline Plex de la V1 mais chaîné avec lui :

```
[CHAÎNE D'ACQUISITION — Radarr/Sonarr]
 1. Recherché           (une recherche a été lancée pour cet item)
 2. Release trouvée      (une ou plusieurs releases correspondent aux critères)
 3. Grab                (une release a été envoyée au client de téléchargement)
 4. Téléchargement       (en cours, avec % de progression si disponible via l'API du client)
 5. Terminé              (téléchargement fini côté client)
 6. Importé              (Radarr/Sonarr a déplacé/renommé le fichier dans la bibliothèque)
        │
        │  ── corrélation par chemin de fichier ──
        ▼
[PIPELINE DE TRAITEMENT PLEX — V1]
 7. Détecté par Plex → 8. Scanné → 9. Identifié → 10. Métadonnées → 11. Artworks →
 12. Vignettes → 13. Marqueurs → 14. Chapitres → 15. Flux audio/sous-titres → 16. Prêt
```

Chaque étape 1 à 6 est horodatée indépendamment. La chaîne complète (1 à 16) constitue la "timeline de bout en bout" d'un item, affichée dans une vue dédiée.

**Point d'attention particulier** (identifié comme angle mort commun aux outils existants) : l'écart entre l'étape 6 (Importé côté Radarr/Sonarr) et l'étape 7 (Détecté côté Plex) est souvent invisible dans les outils actuels — c'est précisément l'écart que Sentarr doit rendre visible en premier lieu, puisqu'aucun outil ne relie aujourd'hui ces deux mondes.

## 4. Modules — architecture fonctionnelle détaillée

### Module 1 — Connecteurs Radarr / Sonarr
**Rôle** : interroger les API Radarr et Sonarr pour suivre la chaîne d'acquisition de chaque item, à la manière de Monitarr.

**Fonctionnalités** :
- Support multi-instance (plusieurs Radarr et/ou Sonarr simultanément, ex. instances séparées par profil qualité)
- Récupération de la file d'attente (`/api/v3/queue`) : items en cours de recherche, de grab, de téléchargement, avec leur statut natif (downloading, stalled, importing, etc.)
- Récupération de l'historique (`/api/v3/history`) pour reconstituer les étapes déjà passées (recherché, grab) même après qu'un item ait quitté la file active
- Association de chaque item à son instance d'origine (badge "1080p" / "4K" par exemple)

**Comportement** : polling à intervalle configurable, indépendant du polling Plex de la V1 (les deux mondes ont des rythmes différents — un téléchargement évolue plus vite qu'un scan de métadonnées).

**Implémentation** : client HTTP dédié par service (`RadarrConnector`, `SonarrConnector`) implémentant une interface commune `AcquisitionConnector`, posée dès la V2 pour permettre l'ajout facile d'autres connecteurs en V3 (Bazarr, Prowlarr) sans refonte.

---

### Module 2 — Suivi de la chaîne d'acquisition et détection de blocage
**Rôle** : transformer les données brutes des connecteurs en un pipeline d'étapes horodatées (comme décrit section 3), et détecter les blocages — c'est la fonctionnalité centrale reprise du positionnement de Trackarr.

**Fonctionnalités** :
- Construction de la timeline d'acquisition (étapes 1 à 6) pour chaque item
- Détection de stall : absence de progression du téléchargement au-delà d'un seuil configurable → statut "bloqué"
- Historique des tentatives (si une release échoue et qu'une nouvelle recherche est relancée, l'historique des tentatives précédentes reste visible plutôt qu'écrasé)

**Comportement** : réévalué à chaque cycle de polling du Module 1 ; toute absence de changement de progression pendant N cycles consécutifs déclenche l'état "bloqué".

**Implémentation** : module de règles Python, indépendant du moteur de corrélation Plex de la V1 mais partageant la même infrastructure de stockage (Module 4).

---

### Module 3 — Corrélation Acquisition ↔ Plex (chaînage de bout en bout)
**Rôle** : relier un item d'acquisition (Radarr/Sonarr) à l'item Plex correspondant créé en V1, pour produire la timeline unifiée complète (étapes 1 à 16).

**Fonctionnalités** :
- Résolution de la correspondance par chemin de fichier (le chemin final donné par Radarr/Sonarr après import doit correspondre au `file_path` stocké côté V1)
- Gestion des cas de non-correspondance (item importé mais jamais détecté côté Plex après un délai anormal → signalé comme anomalie, pas silencieusement ignoré)
- Calcul de la métrique clé : délai entre "Importé" (étape 6) et "Détecté par Plex" (étape 7)

**Comportement** : s'exécute en réaction à tout nouvel événement d'import détecté par le Module 1, tente une corrélation immédiate puis retente périodiquement tant que la correspondance côté Plex n'est pas trouvée.

**Implémentation** : extension du moteur de corrélation de la V1 (Module 3 du cahier des charges V1), sans dupliquer sa logique — un seul moteur de corrélation gère désormais les deux mondes.

---

### Module 4 — Persistance étendue
**Rôle** : stocker les données de la chaîne d'acquisition en cohérence avec le modèle V1.

**Schéma additionnel** :
```
external_sources     (id, type[radarr/sonarr], instance_name, base_url, profile_label)
acquisition_items    (id, source_id, external_id, movie_id (FK nullable), episode_id (FK nullable),
                       file_path_target)
acquisition_events   (id, acquisition_item_id, step[searched/release_found/grabbed/
                       downloading/completed/imported], timestamp, progress_percent (nullable))
health_scores        (id, acquisition_item_id (nullable), movie_id (nullable), episode_id (nullable),
                       score, last_calculated_at, reason)
alert_rules          (id, name, pipeline_step, threshold_minutes, enabled, applies_to[acquisition/plex/both])
alerts_active        (id, rule_id, target_type, target_id, triggered_at, resolved_at (nullable))
```

**Implémentation** : SQLite conservé en V2 sauf si le questionnaire de cadrage (section 8) indique un besoin de migration vers PostgreSQL.

---

### Module 5 — Score de santé (health score)
**Rôle** : donner en un coup d'œil un indicateur de santé 0–100 par item, sur toute la chaîne (acquisition + traitement Plex), reprenant le principe déjà éprouvé par Trackarr mais étendu à la chaîne complète plutôt qu'au seul téléchargement.

**Fonctionnalités** :
- Score calculé à partir : du temps écoulé sans progression à l'étape courante (acquisition ou Plex), de la présence d'erreurs explicites, du nombre de tentatives infructueuses
- Le score se recalcule automatiquement à chaque nouvel événement ; il remonte dès qu'une progression est de nouveau détectée
- Représentation visuelle par couleur (vert/orange/rouge) dans toutes les vues où l'item apparaît (Films, Séries, Acquisition)

**Comportement** : recalcul déclenché par événement, pas par polling séparé (cohérent avec l'approche réactive du Module 3 de la V1).

**Implémentation** : fonction de scoring isolée et testable indépendamment, avec seuils configurables (pas de constantes codées en dur).

---

### Module 6 — Alertes
**Rôle** : signaler activement les blocages plutôt que de laisser l'utilisateur les découvrir en consultant le dashboard.

**Fonctionnalités** :
- Règles configurables par seuil de temps et par étape (acquisition ou Plex), avec granularité "s'applique à toutes les étapes" ou "étape spécifique"
- Vue dédiée listant les alertes actives, avec lien direct vers l'item concerné
- Résolution automatique d'une alerte dès que la situation se débloque (pas de fermeture manuelle nécessaire)
- Sortie via webhook générique (URL configurable) — permet de brancher un canal Discord existant sans développer d'intégration spécifique à ce stade

**Comportement** : évaluation des règles à chaque recalcul de score de santé (Module 5), pas de boucle de vérification séparée.

**Implémentation** : moteur de règles simple (liste de conditions évaluées séquentiellement), webhook déclenché via une tâche asynchrone pour ne pas bloquer le flux principal en cas de latence réseau du service de notification.

---

### Module 7 — Frontend — vue Acquisition et pipeline unifié
**Rôle** : donner une vue de la chaîne d'acquisition, distincte des vues Films/Séries de la V1 mais reliée à elles.

**Fonctionnalités** :
- **Vue Acquisition** : liste des items actuellement en cours d'acquisition (recherche/grab/téléchargement), avec statut natif Radarr/Sonarr, progression, badge d'instance (1080p/4K), score de santé
- **Vue pipeline unifié** (extension de la vue détail film/épisode de la V1) : la timeline affiche désormais les 16 étapes de bout en bout plutôt que les 9 seules étapes Plex, avec le délai "Importé → Détecté" mis en évidence visuellement
- **Vue Alertes** : liste des alertes actives, filtrable par étape/type

**Comportement** : mise à jour temps réel via WebSocket, cohérent avec l'approche de la V1.

**Implémentation** : nouveaux composants frontend réutilisant la timeline verticale déjà construite en V1, étendue plutôt que redéveloppée.

---

## 5. Plan de développement — phases (V2)

- **Phase 0 — Cadrage V2** : réponses au questionnaire (section 8) obtenues
- **Phase 1 — Connecteurs Radarr/Sonarr** (Module 1) : lecture de la file d'attente et de l'historique, validée sur l'infrastructure réelle
- **Phase 2 — Chaîne d'acquisition et détection de blocage** (Module 2)
- **Phase 3 — Corrélation Acquisition ↔ Plex** (Module 3) : extension du moteur de corrélation V1
- **Phase 4 — Persistance étendue** (Module 4)
- **Phase 5 — Score de santé** (Module 5)
- **Phase 6 — Alertes** (Module 6)
- **Phase 7 — Frontend Acquisition et pipeline unifié** (Module 7)
- **Phase 8 — Validation** : déploiement réel, vérification sur des cas de blocage réels ou simulés (ex. arrêt volontaire d'un client de téléchargement pour tester la détection de stall)

## 6. Critères d'acceptation / Definition of Done V2

- [ ] Chaque item recherché par Radarr/Sonarr est visible dans la vue Acquisition avec son statut réel et sa progression
- [ ] Chaque item importé apparaît automatiquement relié à son item Plex correspondant, sans intervention manuelle
- [ ] Le délai entre import et détection Plex est visible et mis en évidence
- [ ] Un score de santé cohérent est affiché pour chaque item, sur l'ensemble de la chaîne
- [ ] Une alerte se déclenche correctement au dépassement d'un seuil configuré, et se résout automatiquement
- [ ] Aucune action d'écriture n'est effectuée sur Radarr, Sonarr ou Plex

## 7. Positionnement par rapport aux outils existants

| Fonctionnalité | Monitarr | Trackarr | Sentarr V2 |
|---|---|---|---|
| Vue file de téléchargement Radarr/Sonarr | ✅ | ✅ | ✅ |
| Score de santé / détection de blocage | ❌ | ✅ | ✅ |
| Suivi du traitement Plex après import | ❌ | ❌ | ✅ |
| Pipeline unifié de bout en bout (acquisition + Plex) | ❌ | ❌ | ✅ (différenciateur principal) |
| Distinction films/séries hiérarchique | ❌ | ❌ | ✅ (hérité de la V1) |

## 8. Questionnaire de cadrage V2 — à poser avant développement

1. URLs et clés API des instances Radarr et Sonarr existantes (une par instance si plusieurs profils qualité)
2. Comment distinguer dans l'interface les items provenant d'instances différentes (badge "4K" vs "1080p" ou autre convention déjà utilisée) ?
3. Seuils de temps par défaut souhaités pour le déclenchement des alertes, étape par étape (ou valeur unique appliquée partout au départ, ajustable ensuite) ?
4. Canal de notification prioritaire pour les alertes en V2 : dashboard uniquement, ou webhook Discord dès cette version (et dans quel salon de l'infrastructure Discord existante) ?
5. Faut-il conserver un historique des alertes résolues (pour analyse a posteriori) ou seulement les alertes actives ?
6. Le score de santé doit-il être visible uniquement par item, ou aussi agrégé en indicateur global de "santé de la bibliothèque" sur le dashboard de synthèse ?
7. Le client de téléchargement (qBittorrent) expose-t-il une API accessible pour affiner la progression du téléchargement, ou faut-il se limiter aux informations fournies par Radarr/Sonarr ?
