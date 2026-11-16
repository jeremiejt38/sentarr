import type { AcquisitionStatus, Status } from '../../lib/arr.types';
import styles from './StatusBadge.module.css';

type Props = { status: Status | AcquisitionStatus; label?: string };

const labels: Record<Status | AcquisitionStatus, string> = {
  pending: 'En attente', in_progress: 'En cours', completed: 'Terminé',
  error: 'Erreur', not_applicable: 'N/A', queued: 'En file',
  downloading: 'Téléchargement', imported: 'Importé', failed: 'Échec', unmatched: 'Non corrélé',
};

const tone: Record<Status | AcquisitionStatus, keyof typeof styles> = {
  completed: 'completed', imported: 'completed',
  in_progress: 'inProgress', downloading: 'inProgress',
  error: 'error', failed: 'error',
  pending: 'pending', queued: 'pending',
  not_applicable: 'na', unmatched: 'unmatched',
};

export function StatusBadge({ status, label }: Props) {
  return <span className={`${styles.badge} ${styles[tone[status]]}`}>{label ?? labels[status]}</span>;
}
