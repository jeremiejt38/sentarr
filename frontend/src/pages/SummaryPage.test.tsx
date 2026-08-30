import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { SummaryPage } from './SummaryPage';
import { api } from '../lib/api.client';

vi.mock('../lib/api.client', () => ({
  api: {
    get: vi.fn(),
  },
}));

describe('SummaryPage', () => {
  it('renders summary cards once data loads', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({
        total_movies: 10,
        total_shows: 5,
        movies_in_progress: 2,
        shows_in_progress: 1,
        errors: 0,
      })
      .mockResolvedValueOnce({
        score: 85,
        total: 15,
        completed: 12,
        in_progress: 3,
        errors: 0,
        active_alerts_count: 0,
        active_alerts: [],
      });

    render(<SummaryPage />);

    await waitFor(() => {
      expect(screen.getByText('Films')).toBeInTheDocument();
    });

    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('Series')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });
});
