import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api.client';
import { useRefreshOnWebSocket } from '../lib/websocket';

interface Alert {
  id: number;
  target_type: string;
  target_id: number;
  severity: string;
  rule: string;
  message: string;
  resolved: boolean;
  created_at: string;
  resolved_at: string | null;
}

export function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [resolved, setResolved] = useState(false);
  const [severity, setSeverity] = useState('');
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    const params = new URLSearchParams();
    params.set('resolved', String(resolved));
    if (severity) params.set('severity', severity);
    api
      .get<{ items: Alert[] }>(`/api/v1/alerts?${params.toString()}`)
      .then((data) => setAlerts(data.items))
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [resolved, severity]);

  useEffect(() => {
    load();
  }, [load]);

  useRefreshOnWebSocket(load);

  const resolve = async (id: number) => {
    await api.post(`/api/v1/alerts/${id}/resolve`, {});
    load();
  };

  const filtered = useMemo(() => {
    return alerts;
  }, [alerts]);

  if (error) return <div className="error">{error}</div>;

  return (
    <div className="page">
      <h1>Alertes</h1>
      <div className="filters">
        <label>
          <input
            type="checkbox"
            checked={resolved}
            onChange={(e) => setResolved(e.target.checked)}
          />
          Résolues
        </label>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="">Toutes sévérités</option>
          <option value="info">Info</option>
          <option value="warning">Avertissement</option>
          <option value="error">Erreur</option>
        </select>
      </div>
      <ul className="alerts-list">
        {filtered.map((alert) => (
          <li key={alert.id} className={`alert alert-${alert.severity}`}>
            <strong>[{alert.rule}]</strong> {alert.message}
            <span className="alert-meta">
              {new Date(alert.created_at).toLocaleString()}
            </span>
            {!alert.resolved && (
              <button type="button" onClick={() => resolve(alert.id)}>
                Résoudre
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
