import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api.client';
import { useRefreshOnWebSocket } from '../lib/websocket';
import { StatusBadge } from '../components/StatusBadge/StatusBadge';
import { ProgressBar } from '../components/ProgressBar/ProgressBar';
import { Timeline } from '../components/Timeline/Timeline';
import type { TimelineStep } from '../lib/arr.types';

interface AcquisitionItem {
  id: number;
  title: string;
  year: number | null;
  status: string;
  client_type: string;
  source_id: number;
  download_id: string | null;
  download_progress: number | null;
  correlated_to_type: string | null;
  correlated_to_id: number | null;
  updated_at: string;
}

interface PipelineStep {
  step: number;
  key: string;
  label: string;
  phase: 'acquisition' | 'plex';
  status: string;
  occurred_at: string | null;
}

interface UnifiedPipeline {
  item_id: number;
  title: string;
  correlated_to_type: string | null;
  correlated_to_id: number | null;
  steps: PipelineStep[];
  total_steps: number;
  import_to_detect_seconds: number | null;
}

const STATUS_PROGRESS: Record<string, number> = {
  monitored: 10,
  grabbed: 40,
  downloading: 60,
  imported: 100,
  failed: 100,
  unknown: 0,
};

export function AcquisitionPage() {
  const [items, setItems] = useState<AcquisitionItem[]>([]);
  const [sources, setSources] = useState<Record<number, string>>({});
  const [statusFilter, setStatusFilter] = useState('');
  const [query, setQuery] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<AcquisitionItem | null>(null);
  const [pipeline, setPipeline] = useState<UnifiedPipeline | null>(null);

  const loadItems = useCallback(() => {
    api
      .get<AcquisitionItem[]>('/api/v1/acquisition')
      .then(setItems)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  useRefreshOnWebSocket(loadItems);

  useEffect(() => {
    api
      .get<{ id: number; name: string }[]>('/api/v1/acquisition/sources')
      .then((data) => setSources(Object.fromEntries(data.map((s) => [s.id, s.name]))));
  }, []);

  useEffect(() => {
    if (!selectedItem) {
      setPipeline(null);
      return;
    }
    api
      .get<UnifiedPipeline>(`/api/v1/acquisition/${selectedItem.id}/pipeline`)
      .then(setPipeline)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [selectedItem]);

  const timelineSteps = useMemo((): TimelineStep[] => {
    if (!pipeline) return [];
    return pipeline.steps.map((s) => ({
      key: s.key,
      label: `${s.step}. ${s.label}`,
      status: s.status as TimelineStep['status'],
      startedAt: s.occurred_at ?? undefined,
    }));
  }, [pipeline]);

  const filtered = useMemo(() => {
    return items.filter((item) => {
      if (statusFilter && item.status !== statusFilter) return false;
      if (query && !item.title.toLowerCase().includes(query.toLowerCase())) return false;
      return true;
    });
  }, [items, statusFilter, query]);

  if (error) return <div className="error">{error}</div>;

  return (
    <div className="page">
      <h1>Acquisition</h1>
      <div className="filters">
        <input
          type="text"
          placeholder="Rechercher..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Tous les statuts</option>
          <option value="monitored">Surveillé</option>
          <option value="grabbed">Récupéré</option>
          <option value="downloading">Téléchargement</option>
          <option value="imported">Importé</option>
          <option value="failed">Échoué</option>
        </select>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Titre</th>
            <th>Source</th>
            <th>Type</th>
            <th>Statut</th>
            <th>Progression</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((item) => (
            <tr
              key={item.id}
              className={selectedItem?.id === item.id ? 'selected' : ''}
              onClick={() => setSelectedItem(item)}
            >
              <td>
                {item.title} {item.year ? `(${item.year})` : ''}
              </td>
              <td>{sources[item.source_id] ?? item.source_id}</td>
              <td>{item.client_type}</td>
              <td>
                <StatusBadge status={item.status as never} />
              </td>
              <td>
                <ProgressBar value={item.download_progress ?? STATUS_PROGRESS[item.status] ?? 0} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {selectedItem && pipeline && (
        <div className="detail-panel">
          <h2>
            Pipeline unifié : {selectedItem.title} {selectedItem.year ? `(${selectedItem.year})` : ''}
          </h2>
          {pipeline.import_to_detect_seconds !== null && (
            <p className="delay-info">
              Délai Importé → Détecté Plex :{' '}
              <strong>
                {pipeline.import_to_detect_seconds < 60
                  ? `${Math.round(pipeline.import_to_detect_seconds)}s`
                  : `${Math.round(pipeline.import_to_detect_seconds / 60)} min`}
              </strong>
            </p>
          )}
          <div className="pipeline-phases">
            <span className="phase-label phase-label--acq">Acquisition (1-6)</span>
            <span className="phase-label phase-label--plex">Plex (7-16)</span>
          </div>
          <Timeline steps={timelineSteps} />
        </div>
      )}
    </div>
  );
}
