import { Link, Outlet } from 'react-router-dom';
import './layout.css';

export function Layout() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar__brand">Sentarr</div>
        <nav className="sidebar__nav">
          <Link to="/">Vue d'ensemble</Link>
          <Link to="/movies">Films</Link>
          <Link to="/shows">Séries</Link>
          <Link to="/acquisition">Acquisition</Link>
          <Link to="/alerts">Alertes</Link>
        </nav>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
