import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api.client';
import { ProgressBar } from '../components/ProgressBar/ProgressBar';
import { StatusBadge } from '../components/StatusBadge/StatusBadge';

interface Show {
  id: number;
  title: string;
  year: number | null;
  overall_status: string;
  progress_percent: number;
}

export function ShowsPage() {
  const [shows, setShows] = useState<Show[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Show[]>('/api/shows')
      .then(setShows)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  if (error) return <div className="error">{error}</div>;

  return (
    <div className="page">
      <h1>Séries</h1>
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
