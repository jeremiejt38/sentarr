import { useEffect, useRef, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { emitToast, REFRESH_EVENT, TOAST_EVENT, useWebSocket } from '../lib/websocket';
import styles from './Layout.module.css';

const LINKS: [string, string][] = [
  ['/', "Vue d'ensemble"],
  ['/movies', 'Films'],
  ['/shows', 'Séries'],
  ['/acquisition', 'Acquisition'],
  ['/download', 'Téléchargements'],
  ['/alerts', 'Alertes'],
  ['/indexers', 'Indexeurs'],
  ['/subtitles', 'Sous-titres'],
  ['/settings', 'Paramètres'],
];

const COLLAPSED_KEY = 'sentarr:sidebar-collapsed';

type Toast = { id: number; title: string; body?: string };
let toastId = 0;

const CONN_LABELS = {
  connected: 'Connecté',
  reconnecting: 'Reconnexion…',
  offline: 'Hors-ligne',
} as const;

export function Layout() {
  const refreshTimer = useRef<number | undefined>(undefined);
  const { status } = useWebSocket((message) => {
    const type = (message as { type?: string }).type;
    if (type === 'new_alert') {
      setAlertCount((c) => c + 1);
      emitToast({ title: 'Nouvelle alerte' });
    }
    // WS-07 : patch local puis refetch débattu (≤ 1 requête / 2 s / entité, ici fenêtre globale).
    window.clearTimeout(refreshTimer.current);
    refreshTimer.current = window.setTimeout(() => {
      window.dispatchEvent(new CustomEvent(REFRESH_EVENT, { detail: message }));
    }, 2000);
  });
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(COLLAPSED_KEY) === '1');
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<{ title: string; body?: string }>).detail;
      const id = ++toastId;
      setToasts((t) => [...t, { id, ...detail }]);
      window.setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 5000);
    };
    window.addEventListener(TOAST_EVENT, handler);
    return () => window.removeEventListener(TOAST_EVENT, handler);
  }, []);

  const toggle = () => {
    setCollapsed((c) => {
      localStorage.setItem(COLLAPSED_KEY, c ? '0' : '1');
      return !c;
    });
  };

  const dotClass =
    status === 'connected' ? styles.dotConnected : status === 'offline' ? styles.dotOffline : styles.dotReconnecting;

  return (
    <div className={styles.shell}>
      <aside className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}>
        <div className={styles.brand}>
          <span className={styles.navLabel}>Sentarr</span>
          <button
            type="button"
            className={styles.toggle}
            onClick={toggle}
            aria-expanded={!collapsed}
            aria-label={collapsed ? 'Déplier la navigation' : 'Replier la navigation'}
          >
            {collapsed ? '»' : '«'}
          </button>
        </div>
        <nav className={styles.nav} aria-label="Navigation principale">
          {LINKS.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => (isActive ? styles.active : undefined)}
              aria-label={collapsed ? label : undefined}
              onClick={to === '/alerts' ? () => setAlertCount(0) : undefined}
            >
              <span className={styles.navLabel}>{label}</span>
              {to === '/alerts' && alertCount > 0 && (
                <span className={styles.alertBadge} aria-label={`${alertCount} nouvelle(s) alerte(s)`}>
                  {alertCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className={styles.content}>
        <header className={styles.topbar}>
          <span className={styles.connIndicator} role="status">
            <span className={`${styles.dot} ${dotClass}`} aria-hidden="true" />
            {CONN_LABELS[status]}
          </span>
        </header>
        {status === 'offline' && (
          <div className={styles.offlineBanner} role="alert">
            Connexion perdue — les données affichées peuvent être obsolètes.
          </div>
        )}
        <main className={styles.main}>
          <Outlet />
        </main>
      </div>
      <div className={styles.toastHost} aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={styles.toast}>
            <div className={styles.toastTitle}>{t.title}</div>
            {t.body && <div className={styles.toastBody}>{t.body}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
