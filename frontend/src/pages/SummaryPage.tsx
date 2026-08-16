import { useEffect, useState } from 'react';
import { api } from '../lib/api.client';

interface SummaryData {
  total_movies: number;
  total_shows: number;
  movies_in_progress: number;
  shows_in_progress: number;
  errors: number;
}

export function SummaryPage() {
  const [data, setData] = useState<SummaryData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<SummaryData>('/api/v1/summary')
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="loading">Chargement…</div>;

  return (
    <div className="page">
      <h1>Vue d'ensemble</h1>
      <div className="cards">
        <div className="card">
          <h3>Films</h3>
          <p>{data.total_movies}</p>
          <small>{data.movies_in_progress} en cours</small>
        </div>
        <div className="card">
          <h3>Séries</h3>
          <p>{data.total_shows}</p>
          <small>{data.shows_in_progress} en cours</small>
        </div>
        <div className="card card--error">
          <h3>Erreurs</h3>
          <p>{data.errors}</p>
        </div>
      </div>
    </div>
  );
}
