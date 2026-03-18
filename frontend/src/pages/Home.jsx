import { useNavigate } from 'react-router-dom';
import Button from '../components/ui/Button';
import { ROUTES } from '../constants/routes';

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Analisis Nutrisi Makanan
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          Deteksi makanan dari foto dan dapatkan informasi nutrisi lengkap
        </p>
        
        <div className="space-y-4">
          <Button 
            onClick={() => navigate(ROUTES.ANALYZE)}
            variant="primary"
            size="lg"
            className="w-full sm:w-auto"
          >
            Mulai Analisis Foto
          </Button>
          
          <div className="text-sm text-gray-500">atau</div>
          
          <Button 
            onClick={() => navigate(ROUTES.SEARCH)}
            variant="secondary"
            size="lg"
            className="w-full sm:w-auto"
          >
            Cari Manual di TKPI
          </Button>
        </div>
      </div>
    </div>
  );
}


