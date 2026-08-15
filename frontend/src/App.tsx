import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './pages/Layout';
import { SummaryPage } from './pages/SummaryPage';
import { MoviesPage } from './pages/MoviesPage';
import { ShowsPage } from './pages/ShowsPage';
import { AcquisitionPage } from './pages/AcquisitionPage';
import { AlertsPage } from './pages/AlertsPage';
import './styles/theme.css';
import './app.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<SummaryPage />} />
          <Route path="movies" element={<MoviesPage />} />
          <Route path="shows" element={<ShowsPage />} />
          <Route path="acquisition" element={<AcquisitionPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
