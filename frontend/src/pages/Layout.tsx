import { Link, Outlet } from 'react-router-dom';
import { useWebSocket } from '../lib/websocket';
import './layout.css';

export function Layout() {
  const { connected } = useWebSocket((message) => {
    // eslint-disable-next-line no-console
    console.debug('WS message:', message);
  });

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar__brand">
          Sentarr
          <span
            className={`ws-indicator ws-indicator--${connected ? 'on' : 'off'}`}
            aria-label={connected ? 'Connecté' : 'Déconnecté'}
          />
        </div>
        <nav className="sidebar__nav">
          <Link to="/">Vue d'ensemble</Link>
          <Link to="/movies">Films</Link>
          <Link to="/shows">Séries</Link>
          <Link to="/acquisition">Acquisition</Link>
          <Link to="/download">Téléchargements</Link>
          <Link to="/alerts">Alertes</Link>
          <Link to="/settings">Paramètres</Link>
        </nav>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
