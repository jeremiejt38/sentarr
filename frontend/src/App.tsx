import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './pages/Layout';
import { SummaryPage } from './pages/SummaryPage';
import { MoviesPage } from './pages/MoviesPage';
import { MovieDetail } from './pages/MovieDetail';
import { ShowsPage } from './pages/ShowsPage';
import { ShowDetail } from './pages/ShowDetail';
import { AcquisitionPage } from './pages/AcquisitionPage';
import { AlertsPage } from './pages/AlertsPage';
import { DownloadPage } from './pages/DownloadPage';
import { SettingsPage } from './pages/SettingsPage';
import './styles/theme.css';
import './app.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<SummaryPage />} />
          <Route path="movies" element={<MoviesPage />} />
          <Route path="movies/:id" element={<MovieDetail />} />
          <Route path="shows" element={<ShowsPage />} />
          <Route path="shows/:id" element={<ShowDetail />} />
          <Route path="acquisition" element={<AcquisitionPage />} />
          <Route path="download" element={<DownloadPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
