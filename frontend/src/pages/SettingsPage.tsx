import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api.client';

interface PlexServer {
  id: number;
  name: string;
  base_url: string;
  log_path: string | null;
  is_active: boolean;
}

interface ApiKeyItem {
  id: number;
  name: string;
  key_prefix: string;
  role: string;
  is_active: boolean;
  last_used_at: string | null;
}

export function SettingsPage() {
  const [servers, setServers] = useState<PlexServer[]>([]);
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([]);
  const [newServer, setNewServer] = useState({ name: '', base_url: '', token: '', log_path: '' });
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyRole, setNewKeyRole] = useState('readonly');
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadServers = useCallback(() => {
    api.get<{ items: PlexServer[] }>('/api/servers').then((d) => setServers(d.items)).catch(() => {});
  }, []);

  const loadKeys = useCallback(() => {
    api.get<{ items: ApiKeyItem[] }>('/api/auth/keys').then((d) => setApiKeys(d.items)).catch(() => {});
  }, []);

  useEffect(() => {
    loadServers();
    loadKeys();
  }, [loadServers, loadKeys]);

  const addServer = () => {
    if (!newServer.name || !newServer.base_url || !newServer.token) return;
    api
      .post<PlexServer>('/api/servers', newServer)
      .then(() => {
        setNewServer({ name: '', base_url: '', token: '', log_path: '' });
        loadServers();
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  };

  const createKey = () => {
    if (!newKeyName) return;
    api
      .post<ApiKeyItem & { raw_key: string }>('/api/auth/keys', { name: newKeyName, role: newKeyRole })
      .then((data) => {
        setCreatedKey(data.raw_key);
        setNewKeyName('');
        loadKeys();
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  };

  return (
    <div className="page">
      <h1>Paramètres</h1>
      {error && <div className="error">{error}</div>}

      <section>
        <h2>Serveurs Plex</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>URL</th>
              <th>Logs</th>
              <th>Actif</th>
            </tr>
          </thead>
          <tbody>
            {servers.map((s) => (
              <tr key={s.id}>
                <td>{s.name}</td>
                <td>{s.base_url}</td>
                <td>{s.log_path || '—'}</td>
                <td>{s.is_active ? 'Oui' : 'Non'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="form-row">
          <input placeholder="Nom" value={newServer.name} onChange={(e) => setNewServer({ ...newServer, name: e.target.value })} />
          <input placeholder="URL (http://plex:32400)" value={newServer.base_url} onChange={(e) => setNewServer({ ...newServer, base_url: e.target.value })} />
          <input placeholder="Token" type="password" value={newServer.token} onChange={(e) => setNewServer({ ...newServer, token: e.target.value })} />
          <input placeholder="Log path (optionnel)" value={newServer.log_path} onChange={(e) => setNewServer({ ...newServer, log_path: e.target.value })} />
          <button onClick={addServer}>Ajouter</button>
        </div>
      </section>

      <section>
        <h2>Clés API</h2>
        {createdKey && (
          <div className="card card--success">
            <strong>Nouvelle clé créée :</strong> <code>{createdKey}</code>
            <br />
            <small>Copiez-la maintenant, elle ne sera plus affichée.</small>
          </div>
        )}
        <table className="table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Préfixe</th>
              <th>Rôle</th>
              <th>Active</th>
              <th>Dernière utilisation</th>
            </tr>
          </thead>
          <tbody>
            {apiKeys.map((k) => (
              <tr key={k.id}>
                <td>{k.name}</td>
                <td><code>{k.key_prefix}</code></td>
                <td>{k.role}</td>
                <td>{k.is_active ? 'Oui' : 'Non'}</td>
                <td>{k.last_used_at || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="form-row">
          <input placeholder="Nom de la clé" value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} />
          <select value={newKeyRole} onChange={(e) => setNewKeyRole(e.target.value)}>
            <option value="readonly">Lecture seule</option>
            <option value="admin">Admin</option>
          </select>
          <button onClick={createKey}>Créer</button>
        </div>
      </section>
    </div>
  );
}
