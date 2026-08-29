import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { api } from './lib/api.client';
import { Layout } from './pages/Layout';
import { LoginPage } from './pages/LoginPage';
import { SummaryPage } from './pages/SummaryPage';
import { MoviesPage } from './pages/MoviesPage';
import { MovieDetail } from './pages/MovieDetail';
import { ShowsPage } from './pages/ShowsPage';
import { ShowDetail } from './pages/ShowDetail';
import { AcquisitionPage } from './pages/AcquisitionPage';
import { AlertsPage } from './pages/AlertsPage';
import { DownloadPage } from './pages/DownloadPage';
import { IndexersPage } from './pages/IndexersPage';
import { SubtitlesPage } from './pages/SubtitlesPage';
import { SettingsPage } from './pages/SettingsPage';
import './styles/theme.css';
import './app.css';

function App() {
  const [authRequired, setAuthRequired] = useState<boolean | null>(null);
  const isLoggedIn = Boolean(localStorage.getItem('sentarr_token'));

  useEffect(() => {
    api.get<{ required: boolean }>('/api/v1/auth/config')
      .then(({ required }) => setAuthRequired(required))
      .catch(() => setAuthRequired(true));
  }, []);

  if (authRequired === null) return null;

  const hasAccess = !authRequired || isLoggedIn;
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={authRequired ? <LoginPage /> : <Navigate to="/" replace />} />
        <Route
          path="/"
          element={hasAccess ? <Layout /> : <Navigate to="/login" replace />}
        >
          <Route index element={<SummaryPage />} />
          <Route path="movies" element={<MoviesPage />} />
          <Route path="movies/:id" element={<MovieDetail />} />
          <Route path="shows" element={<ShowsPage />} />
          <Route path="shows/:id" element={<ShowDetail />} />
          <Route path="acquisition" element={<AcquisitionPage />} />
          <Route path="download" element={<DownloadPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="indexers" element={<IndexersPage />} />
          <Route path="subtitles" element={<SubtitlesPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
