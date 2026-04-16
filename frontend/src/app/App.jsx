import { Routes, Route, Navigate } from 'react-router-dom';
import Home from '../pages/Home';
import AnalyzePhoto from '../pages/AnalyzePhoto';
import ManualSearch from '../pages/ManualSearch';
import { ROUTES } from '../constants/routes';
import { TourProvider } from '../hooks/useTour';
import TourWelcome from '../components/tour/TourWelcome';
import TourSpotlight from '../components/tour/TourSpotlight';

export default function App() {
  return (
    <TourProvider>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path={ROUTES.HOME} element={<Home />} />
          <Route path={ROUTES.ANALYZE} element={<AnalyzePhoto />} />
          <Route path={ROUTES.SEARCH} element={<ManualSearch />} />
          {/* Fallback: redirect unknown routes to home */}
          <Route path="*" element={<Navigate to={ROUTES.HOME} replace />} />
        </Routes>

        {/* Tour overlays — rendered at app level so they persist across routes */}
        <TourWelcome />
        <TourSpotlight />
      </div>
    </TourProvider>
  );
}
