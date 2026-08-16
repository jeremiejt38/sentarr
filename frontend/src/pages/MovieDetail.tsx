import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../lib/api.client';
import { StatusBadge } from '../components/StatusBadge/StatusBadge';
import { ProgressBar } from '../components/ProgressBar/ProgressBar';
import { Timeline } from '../components/Timeline/Timeline';
import type { TimelineStep } from '../lib/arr.types';

interface Task {
  type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

interface MovieDetailData {
  id: number;
  title: string;
  year: number | null;
  path: string | null;
  overall_status: string;
  progress_percent: number;
  tasks: Task[];
}

export function MovieDetail() {
  const { id } = useParams<{ id: string }>();
  const [movie, setMovie] = useState<MovieDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api
      .get<MovieDetailData>(`/api/v1/movies/${id}`)
      .then(setMovie)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [id]);

  if (error) return <div className="error">{error}</div>;
  if (!movie) return <div className="loading">Chargement…</div>;

  const steps: TimelineStep[] = movie.tasks.map((task) => ({
    key: task.type,
    label: task.type,
    status: task.status as never,
    startedAt: task.started_at ?? undefined,
    completedAt: task.completed_at ?? undefined,
    errorMessage: task.error_message ?? undefined,
  }));

  return (
    <div className="page">
      <h1>{movie.title}</h1>
      <div className="detail-meta">
        <span>Année : {movie.year ?? '-'}</span>
        <StatusBadge status={movie.overall_status as never} />
        <ProgressBar value={movie.progress_percent} />
      </div>
      {movie.path ? <div className="detail-path">{movie.path}</div> : null}
      <h2>Pipeline</h2>
      <Timeline steps={steps} />
    </div>
  );
}
