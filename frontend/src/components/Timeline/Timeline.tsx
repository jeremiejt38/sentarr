import { StatusBadge } from '../StatusBadge/StatusBadge';
import type { TimelineStep } from '../../lib/arr.types';
import './timeline.css';

interface TimelineProps {
  steps: TimelineStep[];
}

export function Timeline({ steps }: TimelineProps) {
  return (
    <ol className="timeline">
      {steps.map((step) => (
        <li key={step.key} className={`timeline__step timeline__step--${step.status}`}>
          <div className="timeline__dot" />
          <div className="timeline__content">
            <div className="timeline__header">
              <span className="timeline__label">{step.label}</span>
              <StatusBadge status={step.status} />
            </div>
            {step.errorMessage ? (
              <p className="timeline__error">{step.errorMessage}</p>
            ) : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
