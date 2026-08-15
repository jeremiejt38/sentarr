import { useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api.client';
import { StatusBadge } from '../components/StatusBadge/StatusBadge';
import { ProgressBar } from '../components/ProgressBar/ProgressBar';

interface AcquisitionItem {
  id: number;
  title: string;
  year: number | null;
  status: string;
  client_type: string;
  source_id: number;
  correlated_to_type: string | null;
  correlated_to_id: number | null;
  updated_at: string;
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

  useEffect(() => {
    api
      .get<AcquisitionItem[]>('/api/acquisition')
      .then(setItems)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  useEffect(() => {
    api
      .get<{ id: number; name: string }[]>('/api/acquisition/sources')
      .then((data) => setSources(Object.fromEntries(data.map((s) => [s.id, s.name]))));
  }, []);

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
            <tr key={item.id}>
              <td>
                {item.title} {item.year ? `(${item.year})` : ''}
              </td>
              <td>{sources[item.source_id] ?? item.source_id}</td>
              <td>{item.client_type}</td>
              <td>
                <StatusBadge status={item.status as never} />
              </td>
              <td>
                <ProgressBar value={STATUS_PROGRESS[item.status] ?? 0} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
