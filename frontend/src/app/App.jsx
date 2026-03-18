import { Routes, Route, Navigate } from 'react-router-dom';
import Home from '../pages/Home';
import AnalyzePhoto from '../pages/AnalyzePhoto';
import ManualSearch from '../pages/ManualSearch';
import { ROUTES } from '../constants/routes';

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path={ROUTES.HOME} element={<Home />} />
        <Route path={ROUTES.ANALYZE} element={<AnalyzePhoto />} />
        <Route path={ROUTES.SEARCH} element={<ManualSearch />} />
        {/* Fallback: redirect unknown routes to home */}
        <Route path="*" element={<Navigate to={ROUTES.HOME} replace />} />
      </Routes>
    </div>
  );
}

