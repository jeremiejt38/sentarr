import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api.client';
import { ProgressBar } from '../components/ProgressBar/ProgressBar';
import { StatusBadge } from '../components/StatusBadge/StatusBadge';

interface Movie {
  id: number;
  title: string;
  year: number | null;
  overall_status: string;
  progress_percent: number;
}

export function MoviesPage() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams();
    if (query) params.set('q', query);
    if (statusFilter) params.set('status', statusFilter);
    api
      .get<Movie[]>(`/api/movies?${params.toString()}`)
      .then(setMovies)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [query, statusFilter]);

  const statuses = useMemo(
    () => ['pending', 'in_progress', 'completed', 'error', 'not_applicable'],
    []
  );

  if (error) return <div className="error">{error}</div>;

  return (
    <div className="page">
      <h1>Films</h1>
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
            <th />
          </tr>
        </thead>
        <tbody>
          {movies.map((movie) => (
            <tr key={movie.id}>
              <td>{movie.title}</td>
              <td>{movie.year ?? '-'}</td>
              <td>
                <StatusBadge status={movie.overall_status as never} />
              </td>
              <td>
                <ProgressBar value={movie.progress_percent} />
              </td>
              <td>
                <Link to={`/movies/${movie.id}`}>Détails</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
