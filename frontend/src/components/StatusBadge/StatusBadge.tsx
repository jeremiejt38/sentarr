import type { AcquisitionStatus, Status } from '../../lib/arr.types';
import './status-badge.css';

type Props = { status: Status | AcquisitionStatus; label?: string };

const labels: Record<Status | AcquisitionStatus, string> = {
  pending: 'En attente',
  in_progress: 'En cours',
  completed: 'Terminé',
  error: 'Erreur',
  not_applicable: 'N/A',
  queued: 'En file',
  downloading: 'Téléchargement',
  imported: 'Importé',
  failed: 'Échec',
  unmatched: 'Non corrélé',
};

export function StatusBadge({ status, label }: Props) {
  return (
    <span className={`status-badge status-badge--${status}`} role="status">
      {label ?? labels[status]}
    </span>
  );
}
