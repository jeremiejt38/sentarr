import { useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api.client';
import { StatusBadge } from '../components/StatusBadge/StatusBadge';
import { ProgressBar } from '../components/ProgressBar/ProgressBar';

interface Torrent {
  name: string;
  hash: string;
  progress: number;
  status: string;
  download_speed: number;
  eta_seconds: number | null;
  save_path: string | null;
  labels: string[] | null;
}

const BYTES_PER_MB = 1024 * 1024;

export function DownloadPage() {
  const [torrents, setTorrents] = useState<Torrent[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Torrent[]>('/api/v1/download')
      .then(setTorrents)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  const filtered = useMemo(() => {
    return torrents.sort((a, b) => b.progress - a.progress);
  }, [torrents]);

  if (error) return <div className="error">{error}</div>;

  return (
    <div className="page">
      <h1>Téléchargements</h1>
      <table className="table">
        <thead>
          <tr>
            <th>Nom</th>
            <th>Statut</th>
            <th>Progression</th>
            <th>Vitesse</th>
            <th>ETA</th>
            <th>Chemin</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((torrent) => (
            <tr key={torrent.hash}>
              <td>{torrent.name}</td>
              <td>
                <StatusBadge status={torrent.status as never} />
              </td>
              <td>
                <ProgressBar value={torrent.progress} />
              </td>
              <td>{(torrent.download_speed / BYTES_PER_MB).toFixed(1)} MB/s</td>
              <td>{torrent.eta_seconds ? `${Math.round(torrent.eta_seconds / 60)} min` : '-'}</td>
              <td>{torrent.save_path ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
