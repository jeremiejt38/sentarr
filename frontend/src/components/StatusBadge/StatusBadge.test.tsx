import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { StatusBadge } from './StatusBadge';

describe('StatusBadge', () => {
  it('renders the status label', () => {
    render(<StatusBadge status="completed" />);
    expect(screen.getByText('Terminé')).toBeInTheDocument();
  });

  it('renders a custom label', () => {
    render(<StatusBadge status="in_progress" label="Custom" />);
    expect(screen.getByText('Custom')).toBeInTheDocument();
  });
});

import { STATUS, type AnyStatus } from '../../lib/status';

const ALL: AnyStatus[] = [
  'pending', 'in_progress', 'completed', 'error', 'not_applicable',
  'queued', 'downloading', 'imported', 'failed', 'unmatched',
  'searching', 'found', 'missing', 'healthy', 'degraded', 'failing',
];

describe('StatusBadge — les 16 statuts (CMP-SB-01)', () => {
  it.each(ALL)('affiche libellé + icône pour %s', (status) => {
    const meta = STATUS[status];
    render(<StatusBadge status={status} />);
    expect(screen.getByText(meta.label)).toBeInTheDocument();
    expect(screen.getByText(meta.icon)).toBeInTheDocument();
  });
});
