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
