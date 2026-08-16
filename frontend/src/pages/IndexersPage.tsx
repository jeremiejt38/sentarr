import { useEffect, useState } from 'react';
import { api } from '../lib/api.client';

interface Indexer {
  id: number;
  name: string;
  enabled: boolean;
  protocol: string;
  status: { mostRecentFailure?: string } | null;
  source: string;
}

interface IndexerStats {
  source: string;
  stats: {
    indexers?: Array<{
      indexerName: string;
      numberOfQueries: number;
      numberOfGrabs: number;
      numberOfFailedQueries: number;
      numberOfFailedGrabs: number;
    }>;
  };
}

export function IndexersPage() {
  const [indexers, setIndexers] = useState<Indexer[]>([]);
  const [stats, setStats] = useState<IndexerStats[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<{ items: Indexer[] }>('/api/indexers')
      .then((d) => setIndexers(d.items))
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
    api
      .get<{ sources: IndexerStats[] }>('/api/indexers/stats')
      .then((d) => setStats(d.sources))
      .catch(() => {});
  }, []);

  if (error) return <div className="error">{error}</div>;

  return (
    <div className="page">
      <h1>Indexeurs</h1>

      <section>
        <h2>Status</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Source</th>
              <th>Protocole</th>
              <th>Actif</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {indexers.map((idx) => (
              <tr key={`${idx.source}-${idx.id}`}>
                <td>{idx.name}</td>
                <td>{idx.source}</td>
                <td>{idx.protocol}</td>
                <td>{idx.enabled ? 'Oui' : 'Non'}</td>
                <td>{idx.status?.mostRecentFailure ? 'Erreur' : 'OK'}</td>
              </tr>
            ))}
            {indexers.length === 0 && (
              <tr>
                <td colSpan={5}>Aucun indexeur configuré</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      {stats.length > 0 && (
        <section>
          <h2>Statistiques</h2>
          {stats.map((src) => (
            <div key={src.source}>
              <h3>{src.source}</h3>
              <table className="table">
                <thead>
                  <tr>
                    <th>Indexeur</th>
                    <th>Requêtes</th>
                    <th>Grabs</th>
                    <th>Échecs requêtes</th>
                    <th>Échecs grabs</th>
                  </tr>
                </thead>
                <tbody>
                  {(src.stats.indexers || []).map((s) => (
                    <tr key={s.indexerName}>
                      <td>{s.indexerName}</td>
                      <td>{s.numberOfQueries}</td>
                      <td>{s.numberOfGrabs}</td>
                      <td>{s.numberOfFailedQueries}</td>
                      <td>{s.numberOfFailedGrabs}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
