import styles from './ProgressBar.module.css';

type Props = { value: number; label?: string; indeterminate?: boolean };

export function ProgressBar({ value, label, indeterminate = false }: Props) {
  const safe = Math.max(0, Math.min(100, Number.isFinite(value) ? value : 0));
  const text = label ?? `${safe}%`;
  return (
    <div className={styles.progress}>
      <div
        className={styles.track}
        role="progressbar"
        aria-label={label ?? 'Progression'}
        aria-valuemin={0}
        aria-valuemax={100}
        {...(indeterminate ? {} : { 'aria-valuenow': safe })}
      >
        <div className={styles.value} style={indeterminate ? { width: '40%' } : { width: `${safe}%` }} />
      </div>
      <span>{text}</span>
    </div>
  );
}
