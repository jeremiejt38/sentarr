import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api.client';
import { useRefreshOnWebSocket } from '../lib/websocket';
import { ProgressBar } from '../components/ProgressBar/ProgressBar';
import { StatusBadge } from '../components/StatusBadge/StatusBadge';

interface Show {
  id: number;
  title: string;
  year: number | null;
  overall_status: string;
  progress_percent: number;
  health_score: number;
}

export function ShowsPage() {
  const [shows, setShows] = useState<Show[]>([]);
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    const params = new URLSearchParams();
    if (query) params.set('q', query);
    if (statusFilter) params.set('status', statusFilter);
    api
      .get<Show[]>(`/api/v1/shows?${params.toString()}`)
      .then(setShows)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [query, statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  useRefreshOnWebSocket(load);

  const statuses = useMemo(
    () => ['pending', 'in_progress', 'completed', 'error', 'not_applicable'],
    []
  );

  if (error) return <div className="error">{error}</div>;

  return (
    <div className="page">
      <h1>Séries</h1>
      <div className="filters">
        <input
          type="text"
          placeholder="Rechercher..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Tous les statuts</option>
          {statuses.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Titre</th>
            <th>Année</th>
            <th>Statut</th>
            <th>Progression</th>
            <th>Santé</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {shows.map((show) => (
            <tr key={show.id}>
              <td>{show.title}</td>
              <td>{show.year ?? '-'}</td>
              <td>
                <StatusBadge status={show.overall_status as never} />
              </td>
              <td>
                <ProgressBar value={show.progress_percent} />
              </td>
              <td>{show.health_score}%</td>
              <td>
                <Link to={`/shows/${show.id}`}>Détails</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
