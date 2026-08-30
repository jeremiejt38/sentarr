import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { MoviesPage } from './MoviesPage';
import { api } from '../lib/api.client';

vi.mock('../lib/api.client', () => ({
  api: {
    get: vi.fn(),
  },
}));

describe('MoviesPage', () => {
  it('renders the movie list', async () => {
    vi.mocked(api.get).mockResolvedValueOnce([
      {
        id: 1,
        title: 'Inception',
        year: 2010,
        overall_status: 'completed',
        progress_percent: 100,
        health_score: 90,
      },
    ]);

    render(
      <MemoryRouter>
        <MoviesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Inception')).toBeInTheDocument();
    });

    expect(screen.getByText('2010')).toBeInTheDocument();
  });
});
