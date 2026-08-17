import { useEffect, useState } from 'react';
import { api } from '../lib/api.client';

interface SummaryData {
  total_movies: number;
  total_shows: number;
  movies_in_progress: number;
  shows_in_progress: number;
  errors: number;
}

interface HealthData {
  score: number;
  total: number;
  completed: number;
  in_progress: number;
  errors: number;
  active_alerts_count: number;
  active_alerts: { id: number; severity: string; message: string }[];
}

export function SummaryPage() {
  const [data, setData] = useState<SummaryData | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<SummaryData>('/api/v1/summary')
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
    api
      .get<HealthData>('/api/v1/health')
      .then(setHealth)
      .catch(() => {});
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="loading">Chargement...</div>;

  const scoreClass = health
    ? health.score >= 80
      ? 'card--success'
      : health.score >= 50
        ? 'card--warning'
        : 'card--error'
    : '';

  return (
    <div className="page">
      <h1>Vue d'ensemble</h1>
      <div className="cards">
        {health && (
          <div className={`card ${scoreClass}`}>
            <h3>Score de sante</h3>
            <p className="score-value">{health.score}%</p>
            <small>
              {health.completed}/{health.total} items termines
            </small>
          </div>
        )}
        <div className="card">
          <h3>Films</h3>
          <p>{data.total_movies}</p>
          <small>{data.movies_in_progress} en cours</small>
        </div>
        <div className="card">
          <h3>Series</h3>
          <p>{data.total_shows}</p>
          <small>{data.shows_in_progress} en cours</small>
        </div>
        <div className="card card--error">
          <h3>Erreurs</h3>
          <p>{data.errors}</p>
        </div>
        {health && health.active_alerts_count > 0 && (
          <div className="card card--warning">
            <h3>Alertes actives</h3>
            <p>{health.active_alerts_count}</p>
          </div>
        )}
      </div>
      {health && health.active_alerts.length > 0 && (
        <section>
          <h2>Alertes recentes</h2>
          <ul className="alert-list">
            {health.active_alerts.slice(0, 5).map((alert) => (
              <li key={alert.id} className={`alert-item alert-item--${alert.severity}`}>
                {alert.message}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
