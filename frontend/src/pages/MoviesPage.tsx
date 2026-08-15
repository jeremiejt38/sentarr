import { useEffect, useState } from 'react';
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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Movie[]>('/api/movies')
      .then(setMovies)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  if (error) return <div className="error">{error}</div>;

  return (
    <div className="page">
      <h1>Films</h1>
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
