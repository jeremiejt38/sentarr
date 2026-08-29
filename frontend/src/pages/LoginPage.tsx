import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api.client';

interface LoginResponse {
  token: string;
  user: {
    id: number;
    username: string;
    role: string;
  };
}

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const data = await api.post<LoginResponse>('/api/v1/users/login', {
        username,
        password,
      });
      localStorage.setItem('sentarr_token', data.token);
      navigate('/');
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de connexion');
    }
  }

  return (
    <div className="login-page">
      <form className="login-form" onSubmit={handleSubmit}>
        <h1>Sentarr</h1>
        {error && <div className="error">{error}</div>}
        <input
          type="text"
          placeholder="Nom d'utilisateur"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Mot de passe"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit">Connexion</button>
      </form>
    </div>
  );
}
