import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Input from '../components/ui/Input';
import Spinner from '../components/ui/Spinner';
import { searchTkpi, getTkpiDetail } from '../services/tkpi';
import { ROUTES } from '../constants/routes';

export default function ManualSearch() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedFood, setSelectedFood] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  // ── Fuzzy search toggle ──────────────────────────────────────────────────
  // true  = token-based (e.g. "nasi goreng" matches "goreng nasi, dimasak")
  // false = exact-phrase ILIKE (original behaviour)
  const [fuzzyEnabled, setFuzzyEnabled] = useState(true);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Masukkan kata kunci pencarian');
      return;
    }

    setLoading(true);
    setError(null);
    setSelectedFood(null);

    try {
      const results = await searchTkpi(query, 20, fuzzyEnabled);
      setSearchResults(results);
      
      if (results.length === 0) {
        setError('Tidak ada hasil ditemukan');
      }
    } catch (err) {
      setError(err.message || 'Gagal melakukan pencarian');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectFood = async (foodId) => {
    setLoading(true);
    setError(null);

    try {
      const detail = await getTkpiDetail(foodId);
      setSelectedFood(detail);
    } catch (err) {
      setError(err.message || 'Gagal mengambil detail makanan');
      console.error('Detail error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Button onClick={() => navigate(ROUTES.HOME)} variant="secondary" size="sm">
          ← Kembali
        </Button>
      </div>

      <h1 className="text-3xl font-bold text-gray-900 mb-8">Pencarian Manual TKPI</h1>

      <Card>
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex gap-2 items-center">
            <Input 
              type="text"
              placeholder="Cari makanan di database TKPI..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1"
            />
            <Button 
              type="submit" 
              variant="primary"
              disabled={loading}
            >
              {loading ? <Spinner size="sm" /> : 'Cari'}
            </Button>
          </div>

          {/* ── Fuzzy toggle ─────────────────────────────────────────── */}
          <div className="flex items-center gap-3 pt-1">
            <button
              type="button"
              id="fuzzy-toggle"
              onClick={() => setFuzzyEnabled(prev => !prev)}
              aria-pressed={fuzzyEnabled}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 transition-colors duration-200 focus:outline-none ${
                fuzzyEnabled
                  ? 'bg-blue-600 border-blue-600'
                  : 'bg-gray-200 border-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform duration-200 ${
                  fuzzyEnabled ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </button>
            <label
              htmlFor="fuzzy-toggle"
              className="text-sm text-gray-600 select-none cursor-pointer"
            >
              <span className="font-semibold text-gray-800">Fuzzy Search</span>
              {' '}—{' '}
              {fuzzyEnabled
                ? <span className="text-blue-600 font-medium">Aktif (token-based)</span>
                : <span className="text-gray-500 font-medium">Nonaktif (exact-phrase)</span>
              }
            </label>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
        </form>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mt-6">
            <h3 className="font-semibold text-gray-700 mb-3">
              Hasil Pencarian ({searchResults.length}):
            </h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {searchResults.map((food) => (
                <button
                  key={food.id}
                  onClick={() => handleSelectFood(food.id)}
                  className="w-full text-left px-4 py-3 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
                >
                  <p className="font-medium text-gray-900">{food.name}</p>
                  <p className="text-sm text-gray-500">ID: {food.id}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Food Detail */}
        {selectedFood && (
          <div className="mt-6 border-t pt-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              {selectedFood.name}
            </h3>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-semibold text-gray-700 mb-3">Informasi Nutrisi (per 100g):</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <p className="text-2xl font-bold text-orange-600">
                    {selectedFood.nutrition.energi_kal.toFixed(0)}
                  </p>
                  <p className="text-sm text-gray-600">Energi (kal)</p>
                </div>
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <p className="text-2xl font-bold text-red-600">
                    {selectedFood.nutrition.protein_g.toFixed(1)}
                  </p>
                  <p className="text-sm text-gray-600">Protein (g)</p>
                </div>
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <p className="text-2xl font-bold text-yellow-600">
                    {selectedFood.nutrition.lemak_g.toFixed(1)}
                  </p>
                  <p className="text-sm text-gray-600">Lemak (g)</p>
                </div>
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <p className="text-2xl font-bold text-blue-600">
                    {selectedFood.nutrition.karbo_g.toFixed(1)}
                  </p>
                  <p className="text-sm text-gray-600">Karbohidrat (g)</p>
                </div>
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <p className="text-2xl font-bold text-green-600">
                    {selectedFood.nutrition.serat_g?.toFixed(1) || '0.0'}
                  </p>
                  <p className="text-sm text-gray-600">Serat (g)</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
