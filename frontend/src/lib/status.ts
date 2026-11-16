/**
 * Registre unique des statuts (D-07) : statut → libellé, icône, tokens, urgence.
 * Les paires --status-<tone>-fg / --status-<tone>-bg sont définies dans theme.css (§5.2).
 */

export type Status = 'pending' | 'in_progress' | 'completed' | 'error' | 'not_applicable';
export type AcquisitionStatus =
  | 'queued'
  | 'downloading'
  | 'completed'
  | 'imported'
  | 'failed'
  | 'unmatched';
export type SubtitleStatus = 'searching' | 'found' | 'missing';
export type IndexerHealth = 'healthy' | 'degraded' | 'failing';

export type AnyStatus =
  | Status
  | Exclude<AcquisitionStatus, 'completed'>
  | SubtitleStatus
  | IndexerHealth;

export type StatusTone =
  | 'completed'
  | 'in_progress'
  | 'error'
  | 'pending'
  | 'not_applicable'
  | 'unmatched';

export interface StatusMeta {
  /** Libellé français affiché. */
  label: string;
  /** Glyphe affiché dans le badge (texte — jamais seul porteur d'info). */
  icon: string;
  /** Paire de tokens --status-<tone>-fg / --status-<tone>-bg. */
  tone: StatusTone;
  /** Ordre d'urgence pour le tri (0 = le plus urgent). */
  urgency: number;
}

export const STATUS: Record<AnyStatus, StatusMeta> = {
  error: { label: 'Erreur', icon: '✕', tone: 'error', urgency: 0 },
  failed: { label: 'Échec', icon: '✕', tone: 'error', urgency: 1 },
  failing: { label: 'En panne', icon: '✕', tone: 'error', urgency: 2 },
  missing: { label: 'Manquant', icon: '!', tone: 'unmatched', urgency: 3 },
  unmatched: { label: 'Non associé', icon: '?', tone: 'unmatched', urgency: 4 },
  degraded: { label: 'Dégradé', icon: '⚠', tone: 'unmatched', urgency: 5 },
  in_progress: { label: 'En cours', icon: '…', tone: 'in_progress', urgency: 6 },
  downloading: { label: 'Téléchargement', icon: '↓', tone: 'in_progress', urgency: 7 },
  searching: { label: 'Recherche', icon: '…', tone: 'in_progress', urgency: 8 },
  queued: { label: 'En file', icon: '•', tone: 'pending', urgency: 9 },
  pending: { label: 'En attente', icon: '•', tone: 'pending', urgency: 10 },
  found: { label: 'Trouvé', icon: '✓', tone: 'completed', urgency: 11 },
  imported: { label: 'Importé', icon: '✓', tone: 'completed', urgency: 12 },
  completed: { label: 'Terminé', icon: '✓', tone: 'completed', urgency: 13 },
  healthy: { label: 'Sain', icon: '✓', tone: 'completed', urgency: 14 },
  not_applicable: { label: 'N/A', icon: '—', tone: 'not_applicable', urgency: 15 },
};

export function statusMeta(status: AnyStatus): StatusMeta {
  return STATUS[status] ?? STATUS.pending;
}

export function statusLabel(status: AnyStatus): string {
  return statusMeta(status).label;
}

/** Tri par urgence (erreurs d'abord), puis par libellé. */
export function compareByUrgency(a: AnyStatus, b: AnyStatus): number {
  return statusMeta(a).urgency - statusMeta(b).urgency;
}
