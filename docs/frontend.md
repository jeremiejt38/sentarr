# Spécifications Frontend Sentarr

## Stack

- React 18+
- Vite + PWA (`vite-plugin-pwa`)
- TypeScript
- React Router
- WebSocket native
- CSS Modules (un fichier de style par composant/page)
- Composants de base maison (thème *arr sombre)

## Direction visuelle

Sentarr reprend les repères familiers des interfaces *arr : thème sombre dense, surfaces anthracite, accent bleu pour l'activité, vert pour l'état prêt, orange pour l'attention et rouge pour l'erreur. Aucun asset de marque Radarr/Sonarr n'est réutilisé.

```css
/* frontend/src/styles/theme.css */
:root {
  --arr-bg: #1f1f1f;
  --arr-surface: #2b2b2b;
  --arr-surface-raised: #353535;
  --arr-border: #454545;
  --arr-text: #f1f1f1;
  --arr-muted: #a6a6a6;
  --arr-blue: #3b9eff;
  --arr-green: #49b675;
  --arr-orange: #e5a23c;
  --arr-red: #e05d5d;
  --arr-gray: #777;
  --radius-sm: 4px;
  --focus-ring: 0 0 0 3px rgb(59 158 255 / 35%);
}
body { margin: 0; background: var(--arr-bg); color: var(--arr-text); font: 14px/1.45 system-ui, sans-serif; }
button, input, select { font: inherit; }
:focus-visible { outline: none; box-shadow: var(--focus-ring); }
```

## Contrats TypeScript

```ts
// frontend/src/lib/arr.types.ts
export type Status = 'pending' | 'in_progress' | 'completed' | 'error' | 'not_applicable';
export type AcquisitionStatus = 'queued' | 'downloading' | 'completed' | 'imported' | 'failed' | 'unmatched';
export type ArrItem = {
  id: number;
  title: string;
  profileLabel?: string;
  status: AcquisitionStatus;
  progress?: number;
};
```

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

### `StatusBadge`

```tsx
// frontend/src/components/StatusBadge/StatusBadge.tsx
import type { Status, AcquisitionStatus } from '../../lib/arr.types';
import './status-badge.css';

type Props = { status: Status | AcquisitionStatus; label?: string };
const labels: Record<Props['status'], string> = {
  pending: 'En attente', in_progress: 'En cours', completed: 'Terminé', error: 'Erreur',
  not_applicable: 'N/A', queued: 'En file', downloading: 'Téléchargement', imported: 'Importé',
  failed: 'Échec', unmatched: 'Non corrélé',
};
export function StatusBadge({ status, label }: Props) {
  return <span className={`status-badge status-badge--${status}`} role="status">{label ?? labels[status]}</span>;
}
```

```css
/* frontend/src/components/StatusBadge/status-badge.css */
.status-badge { display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:3px 9px; font-size:12px; font-weight:600; }
.status-badge::before { width:7px; height:7px; border-radius:50%; background:currentColor; content:""; }
.status-badge--completed, .status-badge--imported { color:var(--arr-green); background:#214a35; }
.status-badge--in_progress, .status-badge--downloading { color:var(--arr-blue); background:#173d60; }
.status-badge--error, .status-badge--failed { color:var(--arr-red); background:#552b2b; }
.status-badge--pending, .status-badge--queued { color:var(--arr-muted); background:#414141; }
.status-badge--not_applicable { color:var(--arr-gray); background:#303030; }
.status-badge--unmatched { color:var(--arr-orange); background:#55421f; }
```

### `ProgressBar`

```tsx
// frontend/src/components/ProgressBar/ProgressBar.tsx
export function ProgressBar({ value, label }: { value: number; label?: string }) {
  const safe = Math.max(0, Math.min(100, value));
  return <div className="progress" aria-label={label ?? `${safe}%`}>
    <div className="progress__track"><div className="progress__value" style={{ width: `${safe}%` }} /></div>
    <span>{label ?? `${safe}%`}</span>
  </div>;
}
```

```css
.progress { display:flex; align-items:center; gap:8px; color:var(--arr-muted); min-width:150px; }
.progress__track { flex:1; height:6px; overflow:hidden; border-radius:3px; background:#444; }
.progress__value { height:100%; border-radius:inherit; background:var(--arr-blue); transition:width .25s ease; }
```

### `LoadingIndicator`

Spinner rond rendu uniquement quand au moins une tâche est `in_progress`.

### `TreeView`

Reçoit des nœuds `{id, label, status, progress, children}` ; ouverture locale, navigation clavier (flèches/Entrée), `aria-expanded`. Affiche `Show → Season → Episode` sans changer de page.

### `Timeline`

Reçoit des étapes `{key, label, status, startedAt, completedAt, errorMessage}` ; concatène acquisition (1–6) et Plex (7–16). L'étape `plex_detected` est affichée séparément pour rendre visible le délai Importé → Détecté.

### `ItemCard`

Carte poster + titre + badge + progression, réutilisée dans les listes Films/Séries/Acquisition.

### `FilterBar`

Filtres texte, statut, bibliothèque, instance, `profileLabel`.

## Palette de couleurs (thème *arr sombre)

- Fond principal : `#1f1f1f`.
- Surface : `#2b2b2b`.
- Surface raised : `#353535`.
- Bordure : `#454545`.
- Texte : `#f1f1f1`.
- Texte secondaire : `#a6a6a6`.
- Bleu (`in_progress`/`downloading`) : `#3b9eff`.
- Vert (`completed`/`imported`) : `#49b675`.
- Orange (`attention`/`unmatched`) : `#e5a23c`.
- Rouge (`error`/`failed`) : `#e05d5d`.
- Gris (`not_applicable`) : `#777`.

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
