import { STATUS, type AnyStatus, type StatusTone } from '../../lib/status';
import styles from './StatusBadge.module.css';

type Props = { status: AnyStatus; label?: string };

const toneClass: Record<StatusTone, keyof typeof styles> = {
  completed: 'completed',
  in_progress: 'inProgress',
  error: 'error',
  pending: 'pending',
  not_applicable: 'na',
  unmatched: 'unmatched',
};

export function StatusBadge({ status, label }: Props) {
  const meta = STATUS[status] ?? STATUS.pending;
  return (
    <span className={`${styles.badge} ${styles[toneClass[meta.tone]]}`}>
      <span aria-hidden="true">{meta.icon}</span> {label ?? meta.label}
    </span>
  );
}
