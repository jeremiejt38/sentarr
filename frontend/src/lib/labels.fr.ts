/** Libellés français centralisés (D-11) — point d'entrée unique pour une i18n future. */

/** task_type (data-model.md) : 9 tâches film/épisode + variantes série/saison. */
export const TASK_TYPE_LABELS: Record<string, string> = {
  scan: 'Scan',
  identification: 'Identification',
  metadata: 'Métadonnées',
  artwork: 'Artworks',
  bif: 'BIF',
  intro_markers: 'Marqueurs d\u2019intro',
  chapters: 'Chapitres',
  streams: 'Flux',
  overall: 'Global',
  artwork_show: 'Artworks (série)',
  artwork_season: 'Artworks (saison)',
  metadata_season: 'Métadonnées (saison)',
};

/** Étapes d'acquisition (acquisition_events.step, 1–7 → étapes 1–6 + plex_detected). */
export const ACQUISITION_STEP_LABELS: Record<number, string> = {
  1: 'Recherche',
  2: 'Sélection',
  3: 'Envoi au client',
  4: 'Téléchargement',
  5: 'Import',
  6: 'Vérification',
  7: 'Détection Plex',
};

export function taskTypeLabel(taskType: string): string {
  return TASK_TYPE_LABELS[taskType] ?? taskType;
}

export function acquisitionStepLabel(step: number): string {
  return ACQUISITION_STEP_LABELS[step] ?? `Étape ${step}`;
}
