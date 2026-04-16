import { useState, useEffect, useRef } from 'react';
import Button from '../ui/Button';
import Input from '../ui/Input';
import { searchTkpi } from '../../services/tkpi';
import { submitFeedback } from '../../services/feedback';

export default function CorrectionForm({ analysisId, items = [] }) {
  const [corrections, setCorrections] = useState({});
  const [searchQueries, setSearchQueries] = useState({});
  const [searchResults, setSearchResults] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [error, setError] = useState('');
  
  // Refs for debounce timers
  const debounceTimers = useRef({});

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      Object.values(debounceTimers.current).forEach(timer => clearTimeout(timer));
    };
  }, []);

  const handleSearchChange = (index, query) => {
    setSearchQueries(prev => ({ ...prev, [index]: query }));
    
    // Clear previous timer
    if (debounceTimers.current[index]) {
      clearTimeout(debounceTimers.current[index]);
    }

    // Set new timer for debounced search
    if (query.trim().length > 0) {
      debounceTimers.current[index] = setTimeout(async () => {
        try {
          const results = await searchTkpi(query, 10);
          setSearchResults(prev => ({ ...prev, [index]: results }));
        } catch (err) {
          console.error('Search error:', err);
          setSearchResults(prev => ({ ...prev, [index]: [] }));
        }
      }, 300);
    } else {
      setSearchResults(prev => ({ ...prev, [index]: [] }));
    }
  };

  const handleSelectTkpi = (index, tkpiId, tkpiName) => {
    setCorrections(prev => ({
      ...prev,
      [index]: {
        ...prev[index],
        corrected_tkpi_id: tkpiId,
        corrected_tkpi_name: tkpiName,
      }
    }));
    
    // Clear search results after selection
    setSearchResults(prev => ({ ...prev, [index]: [] }));
    setSearchQueries(prev => ({ ...prev, [index]: tkpiName }));
  };

  const handleNoteChange = (index, note) => {
    setCorrections(prev => ({
      ...prev,
      [index]: {
        ...prev[index],
        note,
      }
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');
    setSuccessMessage('');

    try {
      // Build feedback payload
      const feedbackItems = Object.entries(corrections)
        .filter(([_, correction]) => correction.corrected_tkpi_id || correction.note)
        .map(([index, correction]) => {
          const item = items[parseInt(index)];
          return {
            bbox: item.bbox,
            predicted_label: item.label,
            corrected_tkpi_id: correction.corrected_tkpi_id || null,
            note: correction.note || null,
          };
        });

      if (feedbackItems.length === 0) {
        setError('Tidak ada koreksi untuk dikirim');
        setIsSubmitting(false);
        return;
      }

      const payload = {
        analysis_id: analysisId,
        items: feedbackItems,
      };

      const result = await submitFeedback(payload);
      setSuccessMessage(result.message || `Berhasil menyimpan ${result.saved} koreksi!`);
      
      // Reset form after 3 seconds
      setTimeout(() => {
        setCorrections({});
        setSearchQueries({});
        setSearchResults({});
        setSuccessMessage('');
      }, 3000);
      
    } catch (err) {
      setError(err.message || 'Gagal mengirim koreksi. Silakan coba lagi.');
      console.error('Feedback submission error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          Bantu kami meningkatkan akurasi deteksi dengan memberikan koreksi jika ada kesalahan.
        </p>
      </div>

      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
          {successMessage}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {items.map((item, index) => (
        <div key={index} className="border border-gray-200 rounded-lg p-4 space-y-3">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-700">
                Deteksi #{index + 1}: <span className="text-gray-900">{item.label}</span>
              </p>
              <p className="text-xs text-gray-500">
                Confidence: {(item.confidence * 100).toFixed(1)}%
              </p>
              {item.tkpi && (
                <p className="text-xs text-green-600 mt-1">
                  Mapped: {item.tkpi.name}
                </p>
              )}
            </div>
          </div>

          {/* TKPI Search */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Koreksi TKPI (opsional):
            </label>
            <Input
              type="text"
              placeholder="Cari makanan yang benar..."
              value={searchQueries[index] || ''}
              onChange={(e) => handleSearchChange(index, e.target.value)}
              className="w-full"
            />
            
            {/* Search Results Dropdown */}
            {searchResults[index] && searchResults[index].length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                {searchResults[index].map((result) => (
                  <button
                    key={result.id}
                    type="button"
                    onClick={() => handleSelectTkpi(index, result.id, result.name)}
                    className="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-gray-100 last:border-b-0"
                  >
                    <p className="text-sm font-medium text-gray-900">{result.name}</p>
                    <p className="text-xs text-gray-500">ID: {result.id}</p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Selected TKPI */}
          {corrections[index]?.corrected_tkpi_id && (
            <div className="bg-green-50 border border-green-200 rounded px-3 py-2">
              <p className="text-sm text-green-800">
                Dipilih: {corrections[index].corrected_tkpi_name}
              </p>
            </div>
          )}

          {/* Note */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Catatan (opsional):
            </label>
            <Input
              type="text"
              placeholder="Tambahkan catatan..."
              value={corrections[index]?.note || ''}
              onChange={(e) => handleNoteChange(index, e.target.value)}
              className="w-full"
            />
          </div>
        </div>
      ))}

      <Button 
        type="submit" 
        variant="primary" 
        disabled={isSubmitting}
        className="w-full"
      >
        {isSubmitting ? 'Mengirim...' : 'Kirim Koreksi'}
      </Button>
    </form>
  );
}
