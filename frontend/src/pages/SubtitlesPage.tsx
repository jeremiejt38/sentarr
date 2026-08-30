import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api.client';
import { useRefreshOnWebSocket } from '../lib/websocket';

interface SubtitleTrack {
  id: number;
  episode_id: number | null;
  language: string;
  hearing_impaired: boolean;
  forced: boolean;
  path: string | null;
  provider: string | null;
  source: string;
  downloaded_at: string | null;
}

export function SubtitlesPage() {
  const [tracks, setTracks] = useState<SubtitleTrack[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api
      .get<{ items: SubtitleTrack[] }>('/api/v1/subtitles')
      .then((d) => setTracks(d.items))
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useRefreshOnWebSocket(load);

  if (error) return <div className="error">{error}</div>;

  return (
    <div className="page">
      <h1>Sous-titres</h1>
      <table className="table">
        <thead>
          <tr>
            <th>Langue</th>
            <th>Source</th>
            <th>Provider</th>
            <th>HI</th>
            <th>Forcé</th>
            <th>Épisode</th>
          </tr>
        </thead>
        <tbody>
          {tracks.map((t) => (
            <tr key={t.id}>
              <td>{t.language}</td>
              <td>{t.source}</td>
              <td>{t.provider || '—'}</td>
              <td>{t.hearing_impaired ? 'Oui' : 'Non'}</td>
              <td>{t.forced ? 'Oui' : 'Non'}</td>
              <td>{t.episode_id ?? '—'}</td>
            </tr>
          ))}
          {tracks.length === 0 && (
            <tr>
              <td colSpan={6}>Aucun sous-titre synchronisé</td>
            </tr>
          )}
        </tbody>
      </table>
      <p className="muted">{tracks.length} sous-titre(s) au total</p>
    </div>
  );
}
