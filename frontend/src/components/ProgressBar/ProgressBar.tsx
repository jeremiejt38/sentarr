import './progress-bar.css';

export function ProgressBar({ value, label }: { value: number; label?: string }) {
  const safe = Math.max(0, Math.min(100, value));
  return (
    <div className="progress" aria-label={label ?? `${safe}%`}>
      <div className="progress__track">
        <div className="progress__value" style={{ width: `${safe}%` }} />
      </div>
      <span>{label ?? `${safe}%`}</span>
    </div>
  );
}
