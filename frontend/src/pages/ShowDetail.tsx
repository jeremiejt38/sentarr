import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../lib/api.client';
import { StatusBadge } from '../components/StatusBadge/StatusBadge';
import { ProgressBar } from '../components/ProgressBar/ProgressBar';
import { Timeline } from '../components/Timeline/Timeline';
import { TreeView } from '../components/TreeView/TreeView';
import type { TimelineStep, TreeNode } from '../lib/arr.types';

interface ShowDetailData {
  id: number;
  title: string;
  year: number | null;
  overall_status: string;
  progress_percent: number;
  tasks: { type: string; status: string }[];
  seasons: Season[];
}

interface Season {
  id: number;
  season_number: number;
  overall_status: string;
  progress_percent: number;
  episodes: Episode[];
}

interface Episode {
  id: number;
  episode_number: number;
  title: string | null;
  overall_status: string;
  progress_percent: number;
}

export function ShowDetail() {
  const { id } = useParams<{ id: string }>();
  const [show, setShow] = useState<ShowDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api
      .get<ShowDetailData>(`/api/shows/${id}`)
      .then(setShow)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [id]);

  if (error) return <div className="error">{error}</div>;
  if (!show) return <div className="loading">Chargement…</div>;

  const steps: TimelineStep[] = show.tasks.map((task) => ({
    key: task.type,
    label: task.type,
    status: task.status as never,
  }));

  const nodes: TreeNode[] = show.seasons.map((season) => ({
    id: season.id,
    label: `Saison ${season.season_number}`,
    status: season.overall_status as never,
    progress: season.progress_percent,
    children: season.episodes.map((episode) => ({
      id: episode.id,
      label: `E${episode.episode_number} ${episode.title ?? ''}`,
      status: episode.overall_status as never,
      progress: episode.progress_percent,
    })),
  }));

  return (
    <div className="page">
      <h1>{show.title}</h1>
      <div className="detail-meta">
        <span>Année : {show.year ?? '-'}</span>
        <StatusBadge status={show.overall_status as never} />
        <ProgressBar value={show.progress_percent} />
      </div>
      <h2>Pipeline</h2>
      <Timeline steps={steps} />
      <h2>Saisons</h2>
      <TreeView nodes={nodes} />
    </div>
  );
}
