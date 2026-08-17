# Questionnaire de cadrage — Sentarr

Ce document reprend les questionnaires des cahiers des charges V1, V2 et V3, avec les réponses déjà obtenues. Les questions encore ouvertes sont marquées **À confirmer**.

---

## V1 — Accès et comportement

### 1. Accès Plex

**Question** : URL/IP et port du serveur Plex Media Server, et méthode d'obtention du token.

**Réponse** :
- URL interne Docker : `http://plex:32400` (même réseau `plex-backend`).
- URL LAN : `http://192.168.100.133:32400`.
- Domaine Traefik : `https://plex.drac-lab.fr`.
- Token : `PlexOnlineToken` extrait de `/config/Library/Application Support/Plex Media Server/Preferences.xml` dans le conteneur `plex`.
- Livraison : variable d'environnement `PLEX_TOKEN` au déploiement, jamais versionnée.

### 2. Logs Plex

**Question** : Chemin exact du fichier de log Plex et version exacte de Plex Media Server.

**Réponse** :
- Chemin hôte : `/mnt/user/appdata/plex/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log`.
- Chemin conteneur : `/config/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log`.
- Image : `lscr.io/linuxserver/plex`, conteneur créé le 2026-08-09.

### 3. Bibliothèques à surveiller

**Question** : Toutes, ou une sélection précise ?

**Réponse** : Toutes les bibliothèques de type `movie` et `show` découvertes automatiquement.

### 4. Fréquence de rafraîchissement

**Question** : Fréquence de rafraîchissement souhaitée pour le polling API.

**Réponse** : 60 secondes par défaut, configurable via `POLL_INTERVAL_SECONDS`.

### 5. Durée de rétention de l'historique

**Question** : Durée de rétention souhaitée pour l'historique des tâches terminées.

**Réponse** : 30 jours par défaut, configurable via `HISTORY_RETENTION_DAYS`.

### 6. Rétro-scan initial

**Question** : Rétro-scan des items déjà présents, ou uniquement les nouveaux ajouts ?

**Réponse** : Rétro-scan complet dès le premier démarrage (`RETRO_SCAN=true`).

### 7. Déploiement

**Question** : Réseau Docker et sous-domaine Traefik souhaités.

**Réponse** :
- Sous-domaine : `sentarr.drac-lab.fr`.
- Réseau Docker : `plex-backend`.
- Middleware Traefik : `private-network`.

### 8. Base de données

**Question** : SQLite suffisant, ou PostgreSQL dès la V1 ?

**Réponse** : SQLite par défaut en V1. PostgreSQL supporté via `DATABASE_URL` si le volume justifie le changement (V2/V3).

### 9. Style visuel

**Question** : Thème sombre *arr ou style spécifique ?

**Réponse** : Thème sombre standard façon *arr (Radarr/Sonarr/Bazarr) pour la familiarité.

### 10. Niveau de détail des erreurs

**Question** : Message simplifié ou log brut accessible en un clic ?

**Réponse** : Message simplifié dans l'interface, avec accès au log brut en un clic.

### 11. Tâches non applicables

**Question** : Comment gérer les tâches non applicables (ex: marqueurs intro sans Plex Pass) ?

**Réponse** :
- Affichées avec le statut `not_applicable` (badge grisé).
- Détection automatique de Plex Pass : si non détecté, les tâches `intro_markers` passent à `not_applicable`.

---

## V2 — Acquisition Radarr/Sonarr

### 1. Instances Radarr/Sonarr

**Question** : URLs et clés API des instances Radarr et Sonarr existantes.

**Réponse partielle** :
- Radarr : `http://radarr:7878`.
- Sonarr : `http://sonarr:8989`.
- Prowlarr : `http://prowlarr:9696`.
- Les clés API seront extraites des configs et passées par variables d'environnement au déploiement.

### 2. Distinction des instances

**Question** : Comment distinguer les items provenant d'instances différentes (1080p / 4K) ?

**Réponse** : Badge `profile_label` sur chaque item d'acquisition (ex: `1080p`, `4K`).

### 3. Seuils d'alerte

**Question** : Seuils de temps par défaut pour le déclenchement des alertes.

**Réponse** :
- Recherche bloquée (`searched`) : 60 min.
- Téléchargement bloqué (`downloading`) : 30 min.
- Import bloqué (`importing`) : 15 min.
- Traitement Plex bloqué (`overall`) : 60 min.

**Statut** : Implémenté. Valeurs par défaut : 60/30/15/60 minutes. Configurable via `GET/POST /api/v1/alerts/thresholds` et la page Paramètres du WebUI.

### 4. Canal de notification V2

**Question** : Dashboard uniquement, ou webhook Discord dès cette version ?

**Réponse** : Webhook générique en V2 pour permettre n'importe quel canal ; Apprise en V3.

### 5. Historique des alertes résolues

**Question** : Faut-il conserver un historique des alertes résolues ?

**Réponse** : Oui, conserver 90 jours dans `alerts_active`/`alerts_history`.

### 6. Score de santé global

**Question** : Le score de santé doit-il être visible uniquement par item, ou aussi agrégé globalement ?

**Réponse** : Les deux. Score par item + indicateur global de santé de la bibliothèque sur le dashboard de synthèse.

### 7. Client de téléchargement

**Question** : Le client de téléchargement expose-t-il une API accessible pour affiner la progression ? Faut-il se limiter aux infos Radarr/Sonarr ?

**Réponse** : Connecter directement les clients de téléchargement courants (qBittorrent, Transmission, etc.) via une abstraction `DownloadClientConnector` pour obtenir une progression plus fine et un état natif.

---

## V3 — Extensions

### 1. Priorisation des blocs

**Question** : Parmi les blocs A à G, lesquels sont réellement souhaités ?

**Réponse** : Tous les blocs sont souhaités à terme.

### 2. Intégrations Bazarr/Prowlarr

**Question** : URL/clé API de Bazarr et Prowlarr si retenus.

**Réponse partielle** :
- Prowlarr : `http://prowlarr:9696`.
- Bazarr : `http://bazarr:6767` (clé API à extraire de `/config/config/config.yaml`).

### 3. Analytics — rétention des events bruts

**Question** : Durée de rétention souhaitée pour les événements bruts avant agrégation/purge.

**Réponse** : 90 jours, puis agrégation + purge.

### 4. PostgreSQL

**Question** : Le passage à PostgreSQL est-il anticipé comme nécessaire ?

**Réponse** : Non obligatoire en V1. L'ORM reste compatible PostgreSQL pour une migration transparente si le volume le justifie.

### 5. Multi-serveur Plex

**Question** : Le support multi-serveur Plex correspond-il à une évolution d'infrastructure réellement prévue ?

**Réponse** : Oui, prioritaire en V3. Le modèle de données (`plex_servers`) est préparé pour et les tables `libraries`/`movies`/`shows` porteront une clé `plex_server_id`.

### 6. Authelia

**Question** : Authelia est-il déjà en place devant Traefik ? Doit-il être réutilisé ?

**Réponse** : Authelia est en place dans l'infrastructure (voir Atlas `docs/services.md`), mais il reste optionnel côté Sentarr. En V3, le mode `external` permettra de déléguer l'authentification à Authelia/Traefik sans imposer d'auth applicative.

### 7. Nombre de rôles

**Question** : Si multi-utilisateur retenu, combien de rôles distincts sont nécessaires ?

**Réponse** : 2 rôles : `admin` et `readonly`.

### 8. Canaux de notification

**Question** : Canaux de notification à couvrir en priorité.

**Réponse** : Tous via Apprise : Discord, Telegram, Matrix, Slack, Mattermost, XMPP/Jabber, ntfy, Pushover, Pushbullet, Gotify, Boxcar, email SMTP, Twilio, custom webhook.

### 9. Export Prometheus / Grafana

**Question** : Méthode d'exposition des métriques et dashboards souhaitée.

**Réponse** : Exporter des métriques au format Prometheus sur un endpoint `/metrics`, avec plusieurs dashboards Grafana pré-configurés. Home Assistant n'est pas souhaité dans Sentarr.

### 10. PWA

**Question** : L'application frontend doit-elle être une Progressive Web App ?

**Réponse** : Oui, dès la V1 : service worker, manifeste, icône, mode hors-ligne partiel.

### 11. Publication communautaire

**Question** : Volonté confirmée de publier le projet publiquement ?

**Réponse** : Oui en V3, avec documentation anglaise et template Unraid CA.
