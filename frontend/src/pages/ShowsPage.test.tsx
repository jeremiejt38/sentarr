import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ShowsPage } from './ShowsPage';
import { api } from '../lib/api.client';

vi.mock('../lib/api.client', () => ({
  api: {
    get: vi.fn(),
  },
}));

describe('ShowsPage', () => {
  it('renders the shows list', async () => {
    vi.mocked(api.get).mockResolvedValueOnce([
      {
        id: 1,
        title: 'Breaking Bad',
        year: 2008,
        overall_status: 'in_progress',
        progress_percent: 50,
        health_score: 75,
      },
    ]);

    render(
      <MemoryRouter>
        <ShowsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Breaking Bad')).toBeInTheDocument();
    });

    expect(screen.getByText('2008')).toBeInTheDocument();
  });
});
