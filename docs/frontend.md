# Spécifications Frontend Sentarr

## Stack

- React 18+
- Vite
- TypeScript
- React Router (ou équivalent)
- WebSocket native
- PWA (Progressive Web App) : service worker, manifeste, icône, mode hors-ligne partiel
- CSS Modules ou Tailwind (à valider)
- Composants de base maison (thème *arr sombre)

## Cas d'usage couverts

Le dashboard doit permettre de répondre aux questions suivantes :

1. **"Ce film que je viens d'ajouter, Plex a-t-il fini de le traiter ou c'est encore en cours ?"**
   - Page Films / détail film → timeline des 9 étapes.
2. **"Cette série a 10 saisons, laquelle a des épisodes encore en cours de traitement ?"**
   - Page Séries → liste des séries avec barre de progression globale → dépliage par saison.
3. **"Cette saison affiche 22/24 épisodes prêts — que se passe-t-il pour les 2 restants ?"**
   - Dépliage de la saison → vue épisodes avec statuts individuels.
4. **"Pourquoi ce film n'a toujours pas d'affiche 3 heures après l'ajout ?"**
   - Détail film → étape `artwork` en `error` ou `in_progress` avec message/log brut.
5. **"Combien de fichiers sont actuellement en erreur de métadonnées dans ma bibliothèque ?"**
   - Page d'accueil / synthèse → compteur d'items en erreur par domaine.
6. **"Un épisode a-t-il été mal identifié (mauvaise saison/numéro) ?"**
   - Vue détail épisode ou indicateur d'erreur de matching, visible comme cas d'erreur distinct.

## Principes UX

- Thème sombre cohérent avec Radarr/Sonarr/Bazarr.
- Pas de rechargement de page : navigation client + mises à jour temps réel via WebSocket.
- Distinction claire entre Films et Séries : les deux domaines n'ont pas la même structure mentale.
- Indication de chargement ronde/spinner sur les tâches en cours, comme demandé pour les épisodes en cours de traitement.

## Pages

### Page d'accueil / synthèse

Deux blocs côte à côte : **Films** et **Séries**.
Chaque bloc affiche :
- Nombre total d'items.
- Compteurs : `pending`, `in_progress`, `completed`, `error`, `not_applicable`.
- Liste des items les plus anciens encore en cours (candidats au blocage).
- Nombre de lignes de log non reconnues (audit).

Accès rapide aux pages Films, Séries, Acquisition (V2), Alertes (V2).

### Page Films

- Grille/liste de cartes.
- Chaque carte : poster, titre, année, badge de statut global.
- Filtres : bibliothèque, statut global, recherche textuelle.
- Clic → vue détail film.

### Page Séries

- Liste de séries (poster + titre + barre de progression globale + pourcentage).
- Clic sur une série → dépliage des saisons.
- Clic sur une saison → dépliage des épisodes.
- Chaque niveau a sa propre barre de progression et son résumé (ex: "22/24 épisodes prêts").
- Indicateur de chargement rond/spinner sur un épisode dont au moins une tâche est `in_progress`.
- Filtres : bibliothèque, statut global de série, recherche textuelle.

### Vue détail film

- Informations du film (poster, titre, année, chemin du fichier).
- Timeline verticale des 9 étapes du pipeline.
- Chaque étape : icône de statut, nom, dates `started_at`/`completed_at`, message d'erreur si `error`.
- Si erreur : bouton pour afficher le log brut lié.

### Vue détail épisode

- Informations de l'épisode (vignette, titre, numéro, saison, série).
- Timeline verticale des étapes du pipeline épisode.
- Contexte de la saison et de la série.

### Vue Acquisition (V2)

- Liste des items en cours d'acquisition.
- Colonnes : titre, instance/badge qualité, étape courante, progression, health score, durée dans l'étape.
- Clic → timeline unifiée (étapes 1–16).

### Vue Alertes (V2)

- Liste des alertes actives.
- Filtres : étape, type (acquisition/plex), sévérité.
- Lien direct vers l'item concerné.
- Indication automatique de résolution.

### Vue Recherche cross-domaine

- Barre de recherche globale.
- Résultats groupés par Films et Séries.
- Clic → navigation vers le détail.

## Composants réutilisables

- `StatusBadge` : badge de statut avec couleur.
- `ProgressBar` : barre de progression avec pourcentage et label.
- `LoadingIndicator` : spinner rond pour indiquer une tâche en cours.
- `Timeline` : timeline verticale des étapes.
- `TreeView` : arborescence dépliable (Série → Saison → Épisode).
- `ItemCard` : carte poster + titre + badge.
- `FilterBar` : filtres et recherche.

## Palette de couleurs (thème *arr sombre)

- Fond principal : `#1a1a1a` ou équivalent.
- Surface : `#252525`.
- Texte : `#eeeeee`.
- Texte secondaire : `#888888`.
- Succès (`completed`) : `#4caf50`.
- En cours (`in_progress`) : `#2196f3`.
- Erreur (`error`) : `#f44336`.
- En attente (`pending`) : `#9e9e9e`.
- Non applicable (`not_applicable`) : `#616161`.

## PWA (Progressive Web App)

L'application V1 doit être déployable comme PWA.

- `vite-plugin-pwa` pour générer le service worker.
- Manifeste `manifest.json` avec nom, icône (à créer), couleur thème sombre.
- Mise en cache des assets et des dernières données de synthèse pour un mode hors-ligne partiel.
- Pas de notifications push natives en V1 (notifications push via Apprise en V3).

## WebSocket

- Connexion unique à `/ws` au démarrage de l'application.
- Réconciliation locale des messages `task_update` et `summary_update`.
- Reconnexion automatique en cas de coupure.
