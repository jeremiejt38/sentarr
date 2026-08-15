# Informations opérationnelles Sentarr

> Ce document résume l'infrastructure et les accès nécessaires au projet. **Aucun secret (token, clé API, mot de passe) n'est inscrit ici** : ils sont passés par variables d'environnement ou Docker secrets.

## Source de vérité infrastructure

Les détails complets du réseau, des hôtes et des services se trouvent dans le repo **Atlas** (`/home/jerem/workspace/atlas`) :

- `docs/network.md` : topologie VPN, DNS, routes.
- `docs/hosts.md` : profils SSH et caractéristiques des hôtes.
- `docs/services.md` : mapping domaine → hôte → port.
- `docs/traefik.md` : conventions de routage sur Unraid.

## Serveur principal : Unraid (Akasha)

| Attribut | Valeur |
|----------|--------|
| Hôte | `unraid` (alias SSH) |
| IP LAN | `192.168.100.133` |
| Rôle | Docker, Traefik, Plex, Radarr, Sonarr, Bazarr, Prowlarr, etc. |
| Réseau Docker principal | `plex-backend` |
| Accès SSH | Préconfiguré via clé/agent, pas de mot de passe interactif |

## Plex

| Attribut | Valeur |
|----------|--------|
| Conteneur Docker | `plex` |
| Image | `lscr.io/linuxserver/plex` |
| URL interne (Docker) | `http://plex:32400` |
| URL LAN | `http://192.168.100.133:32400` |
| Domaine Traefik | `plex.drac-lab.fr` |
| Volume config hôte | `/mnt/user/appdata/plex` → `/config` dans le conteneur |
| Fichier de log principal | `/mnt/user/appdata/plex/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log` |
| État constaté | Up healthy (44+ heures au moment de la collecte) |

### Obtenir le token Plex

Le `PlexOnlineToken` se trouve dans le fichier `Preferences.xml` du conteneur/config Plex. Il doit être extrait et passé via la variable `PLEX_TOKEN` au déploiement. Ne jamais le commiter.

Commande indicative (à adapter pour ne pas exposer la valeur) :

```bash
ssh unraid "docker exec plex grep -oE 'PlexOnlineToken=\"[^\"]+' /config/Library/Application\\ Support/Plex\\ Media\\ Server/Preferences.xml | head -1 | cut -d'=' -f2"
```

## *arr stack (Unraid)

Tous les conteneurs ci-dessous tournent sur Unraid dans le réseau `plex-backend`.

| Service | Conteneur | Port interne | Fichier config clé API |
|---------|-----------|--------------|------------------------|
| Radarr | `radarr` | `7878` | `/config/config.xml` (`ApiKey`) |
| Sonarr | `sonarr` | `8989` | `/config/config.xml` (`ApiKey`) |
| Bazarr | `bazarr` | `6767` | `/config/config/config.yaml` (`apikey`) |
| Prowlarr | `prowlarr` | `9696` | `/config/config.xml` (`ApiKey`) |
| qBittorrent Radarr | `qbittorrent-radarr` | `6881/6882` | — |
| qBittorrent Sonarr | `qbittorrent-sonarr` | `6883/6884` | — |

Les clés API doivent être extraites au moment du déploiement V2/V3 et passées via variables d'environnement. Ne pas les versionner.

## Traefik sur Unraid

| Attribut | Valeur |
|----------|--------|
| Conteneur | `traefik` |
| Ports exposés | `80`, `443`, `8183→8080` (dashboard), `32401→32400` |
| Config statique | `/mnt/user/appdata/traefik/traefik.yml` |
| Config dynamique | `/mnt/user/appdata/traefik/dynamic/*.yml` |
| Provider Docker | Réseau `plex-backend` |
| Middleware privé | `private-network` (`ipAllowList` LAN/VPN/Docker) |

## Domaine prévu pour Sentarr

| Attribut | Valeur |
|----------|--------|
| Domaine | `sentarr.drac-lab.fr` |
| Type d'accès | Privé (LAN/VPN via OPNsense Unbound) |
| Middlewares prévus | `private-network` (éventuellement `authelia` plus tard) |
| Backend | `http://sentarr:8000` sur le réseau `plex-backend` |

Aucune entrée DNS publique n'est nécessaire : le wildcard `*.drac-lab.fr` est géré par l'override Unbound d'OPNsense.

## Volumétrie du stockage média

| Métrique | Valeur constatée |
|----------|------------------|
| Chemin | `/mnt/user/plex/data` |
| Taille totale | ~58 To |
| Nombre de fichiers | ~49 800 |
| Bibliothèques observées | `tv`, `movies`, `documentary`, `music`, `shows`, `pre-roll`, `animes`, `cartoons`, `annimation`, `emissions`, `docu-series` |

> Le nombre d'items Plex (films, séries, épisodes) est inférieur au nombre total de fichiers car ce dernier inclut les fichiers secondaires (sous-titres, extras, métadonnées, etc.).

## Réseau et sécurité

- `sentarr.drac-lab.fr` ne sera accessible que depuis le LAN maison ou le VPN AkashaVPN.
- Aucune exposition publique WAN prévue en V1.
- En V3, si ouverture communautaire du repo, aucune URL, IP, token ou credential spécifique à cette infrastructure ne doit apparaître dans le code ou la documentation publique.

## Commandes de diagnostic utiles

```bash
# État des conteneurs média
ssh unraid "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'plex|radarr|sonarr|bazarr|prowlarr|sentarr'"

# Logs de Plex (dans le conteneur)
ssh unraid "docker exec plex tail -n 50 '/config/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log'"

# Redémarrer Traefik après ajout de route
ssh unraid "docker restart traefik"

# Vérifier la route Sentarr
ssh unraid "docker logs --tail 30 traefik"
```

## Points de vigilance

- Le fichier de log Plex est sur un volume FAT32 exposé via Unraid (`/boot` pour les scripts). Les scripts Atlas utilisent `TERM=dumb` et `bash script.sh` pour cette raison. Sentarr ne touche pas à `/boot`.
- Le parsing des logs Plex peut dépendre de la version exacte de Plex Media Server. Les patterns doivent être versionnés et testés.
- La taille importante du stockage média justifie d'utiliser des requêtes incrémentales (`updatedAt`) quand Plex le permet, afin de limiter la charge.
