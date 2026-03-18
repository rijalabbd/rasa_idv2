// frontend/src/pages/AnalyzePhoto.jsx

import { useState, useRef, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import BoundingBoxOverlay from '../components/BoundingBoxOverlay';
import Spinner from '../components/ui/Spinner';
import Input from '../components/ui/Input';
import { detectFood } from '../services/detection';
import { getTkpiDetail } from '../services/tkpi';
import { submitFeedback } from '../services/feedback';
import { reportMissedDetection } from '../services/missedDetection';
import { submitClassRequest } from '../services/api';
import { ROUTES } from '../constants/routes';
import { ANIMATION_DELAYS, TOAST_MESSAGES } from '../constants/app';
import { useTkpiSearch } from '../hooks/useTkpiSearch';
import { multiplyNutrition, calculateTotalNutrition, getNutritionBadge } from '../utils/nutrition';

// ✅ TOAST constants now imported from constants/app.js

export default function AnalyzePhoto() {
  const navigate = useNavigate();
  // DEBUG: Verify HMR
  useEffect(() => console.log('AnalyzePhoto v2.1 loaded - Patch Verified'), []);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Detection results
  const [analysisId, setAnalysisId] = useState(null);
  const [detectionItems, setDetectionItems] = useState([]);
  // ✅ P0-3: Derived state for total nutrition (prevents sync bugs)
  const totalNutrition = useMemo(() => 
    detectionItems.length > 0 ? calculateTotalNutrition(detectionItems) : null,
  [detectionItems]);

  // ✅ PHASE 0: Replace 3x duplicate TKPI search logic with reusable hook
  // ✅ PHASE 0: Replace 3x duplicate TKPI search logic with reusable hook
  const editSearch = useTkpiSearch(20);  // Edit correction search
  const addSearch = useTkpiSearch(20);   // Manual add search
  // requestSearch removed - class request is free text

  // Edit/Koreksi state (simplified - search moved to hook)
  const [editingCardIndex, setEditingCardIndex] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editError, setEditError] = useState('');

  // Tambah makanan manual state (simplified - search moved to hook)
  const [addingFoodIndex, setAddingFoodIndex] = useState(null);
  const [addError, setAddError] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  // Delete loading
  const [deletingIndex, setDeletingIndex] = useState(null);

  // Training request state (simplified - search moved to hook)
  const [showTrainingRequest, setShowTrainingRequest] = useState(false);
  const [requestedLabelInput, setRequestedLabelInput] = useState(''); // Free text for new class
  const [requestNote, setRequestNote] = useState('');
  const [requestMsg, setRequestMsg] = useState('');
  const [isRequesting, setIsRequesting] = useState(false);

  // Busy state hanya untuk aksi server (detect / submit / request / delete)
  const isBusyAction =
    loading || isSubmitting || isAdding || isRequesting || deletingIndex !== null;

  // Toast notification state
  const [toast, setToast] = useState(null); // {type:'success'|'error', text:''}
  const toastTimerRef = useRef(null);

  // Refs for image input (upload + camera)
  const uploadRef = useRef(null);
  const cameraRef = useRef(null);

  // ✅ PHASE 0: Remove duplicate - use utils/nutrition.js as single source of truth

  const resetInlineStates = () => {
    // ✅ PHASE 0: Use hook reset methods
    editSearch.reset();
    addSearch.reset();
    // requestSearch removed

    // Reset UI states
    setEditingCardIndex(null);
    setEditError('');
    setAddingFoodIndex(null);
    setAddError('');
    setShowTrainingRequest(false);
    setRequestedLabelInput('');
    setRequestNote('');
    setRequestMsg('');
  };

  const showToast = (type, text) => {
    setToast({ type, text });

    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);

    toastTimerRef.current = setTimeout(() => {
      setToast(null);
      toastTimerRef.current = null;
    }, ANIMATION_DELAYS.TOAST); // ✅ Use constant instead of magic number
  };

  const handleImageUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      showToast('error', '❌ File harus berupa gambar (JPG, PNG)');
      setError('File harus berupa gambar');
      return;
    }

    // Validate file size (max 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      showToast('error', '❌ Ukuran file maksimal 5MB');
      setError('Ukuran file maksimal 5MB');
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));

    // Reset analysis state
    setDetectionItems([]);
    setAnalysisId(null);
    // setTotalNutrition removed (derived)
    setError(null);
    resetInlineStates();

    // Reset input value so same file can be selected again
    e.target.value = '';
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);

    try {
      const result = await detectFood(selectedFile);

      const newAnalysisId = result?.analysis_id ?? null;
      setAnalysisId(newAnalysisId);

      // ✅ PHASE 0 CRITICAL: Strict schema validation - NO FALLBACKS
      if (!Array.isArray(result?.items)) {
        throw new Error(TOAST_MESSAGES.INVALID_SCHEMA);
      }

      const rawItems = result.items;

      if (rawItems.length === 0) {
        // Tetap lanjut: user bisa tambah manual
        console.warn('Empty detection items:', result);
        showToast('error', TOAST_MESSAGES.EMPTY_DETECTION);
      }

      const items = rawItems.map((item) => ({
        ...item,
        corrected: false,
        portion: 1,
        // Auto-disable selection for BELUM_ADA items (check status + label + tkpi null)
        selected: item.nutrition_status !== 'BELUM_ADA' 
          && item.nutrition_status_label !== 'Belum ada datanya'
          && item.tkpi !== null,
        baseNutrition: item.tkpi?.nutrition || {
          energi_kal: 0,
          protein_g: 0,
          lemak_g: 0,
          karbo_g: 0,
          serat_g: 0,
        },
        currentName: item.tkpi?.name || item.label,
      }));

      setDetectionItems(items);
      // setTotalNutrition removed (derived)
      resetInlineStates();
    } catch (err) {
      let errorMsg;
      const refId = err?.requestId ? ` (Ref: ${err.requestId})` : '';

      switch (err?.code) {
        case 'MODEL_NOT_READY':
          errorMsg = `Model belum siap. Upload model di Admin lalu coba lagi.${refId}`;
          break;
        case 'SERVER_BUSY':
          errorMsg = `Server sedang sibuk. Silakan coba beberapa saat lagi.${refId}`;
          break;
        case 'TIMEOUT':
          errorMsg = `Proses terlalu lama (timeout). Silakan coba lagi.${refId}`;
          break;
        default:
          errorMsg = (err?.message || 'Gagal melakukan deteksi. Silakan coba lagi.') + refId;
      }

      setError(errorMsg);
      showToast('error', errorMsg);
      console.error('Detection error:', err);
    } finally {
      setLoading(false);
    }
  };

  // ========== CARD ACTIONS ==========
  const handleDeleteCard = (index) => {
    if (isBusyAction) return;

    setDeletingIndex(index);

    // Brief delay for visual feedback
    setTimeout(() => {
      const updated = detectionItems.filter((_, i) => i !== index);

      // Reset/shift pointers if needed
      if (editingCardIndex === index) setEditingCardIndex(null);
      if (addingFoodIndex === index) setAddingFoodIndex(null);

      if (editingCardIndex !== null && index < editingCardIndex) {
        setEditingCardIndex(editingCardIndex - 1);
      }
      if (addingFoodIndex !== null && index < addingFoodIndex) {
        setAddingFoodIndex(addingFoodIndex - 1);
      }

      setDetectionItems(updated);
      // setTotalNutrition removed (derived)
      setDeletingIndex(null);
      showToast('success', TOAST_MESSAGES.DELETE_SUCCESS); // ✅ Use constant
    }, ANIMATION_DELAYS.DELETE); // ✅ Use constant instead of magic 200
  };

  const handleToggleSelected = (index) => {
    const updatedItems = [...detectionItems];
    updatedItems[index].selected = !updatedItems[index].selected;
    setDetectionItems(updatedItems);
    // setTotalNutrition removed (derived)
  };

  const handlePortionChange = (index, newPortion) => {
    let portion = parseFloat(newPortion);
    if (isNaN(portion) || portion < 0.1) portion = 0.1;

    const updatedItems = [...detectionItems];
    updatedItems[index].portion = portion;

    setDetectionItems(updatedItems);
    // setTotalNutrition removed (derived)
  };

  // ========== EDIT / KOREKSI ==========
  // ✅ PHASE 0: Simplified using editSearch hook
  const handleEditCard = (index) => {
    if (isBusyAction) return;

    setEditingCardIndex(index);
    setAddingFoodIndex(null);
    setShowTrainingRequest(false);
    setEditError('');

    // Reset search via hook
    editSearch.reset();
  };

  const handleCancelEdit = () => {
    setEditingCardIndex(null);
    setEditError('');
    editSearch.reset();
  };

  // ✅ PHASE 0: Search and select now handled by editSearch hook
  // Hook provides: query, results, isSearching, selected, error, handleSearch, handleSelect, reset

  const handleConfirmEdit = async () => {
    if (!editSearch.selected || editingCardIndex === null) return;

    setIsSubmitting(true);
    setEditError('');

    const item = detectionItems[editingCardIndex];

    try {
      // Send feedback ONLY for detected items, not manual additions
      if (!item.is_manual) {
        // Contract matches FeedbackRequest: { analysis_id, items: [...] }
        const feedbackPayload = {
          analysis_id: analysisId,
          items: [{
            bbox: item.bbox,
            predicted_label: item.label,
            corrected_tkpi_id: editSearch.selected.id,
            note: ''
          }]
        };

        await submitFeedback(feedbackPayload);
      }
      const tkpiDetail = await getTkpiDetail(editSearch.selected.id);

      const updatedItems = [...detectionItems];
      updatedItems[editingCardIndex] = {
        ...item,
        corrected: true,
        currentName: tkpiDetail.name,
        baseNutrition: tkpiDetail.nutrition, // portion tetap
        tkpi: {
          id: tkpiDetail.id,
          name: tkpiDetail.name,
          nutrition: tkpiDetail.nutrition,
        },
      };

      setDetectionItems(updatedItems);
      // setTotalNutrition removed (derived)
      showToast('success', `✅ "${tkpiDetail.name}" berhasil dikoreksi dan dilaporkan untuk pelatihan AI. Terima kasih!`);
      handleCancelEdit();
    } catch (err) {
      // Friendly error handling
      let msg = TOAST_MESSAGES.GENERIC_ERROR;
      if (err.code === 'TIMEOUT') msg = 'Proses terlalu lama. Coba lagi.';
      else if (err.code === 'SERVER_BUSY') msg = 'Server sedang sibuk. Coba lagi sebentar.';
      else if (err.message) msg = err.message;
      
      if (err.requestId) console.log(`Request ID: ${err.requestId}`);
      
      setEditError(msg);
      showToast('error', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // ========== TAMBAH MAKANAN MANUAL (untuk analisis saat ini) ==========
  const handleOpenAddFood = () => {
    if (isBusyAction) return;

    setAddingFoodIndex('standalone');
    setEditingCardIndex(null);

    addSearch.reset();
    setAddError('');
  };

  const handleCancelAddFood = () => {
    setAddingFoodIndex(null);
    addSearch.reset();
    setAddError('');
  };

  // IMPORTANT: manual add -> add new card to detectionItems (affects total)
  const handleConfirmAddFood = async () => {
    if (!addSearch.selected) {
      setAddError(TOAST_MESSAGES.SELECT_FOOD);
      showToast('error', TOAST_MESSAGES.SELECT_FOOD);
      return;
    }

    setIsAdding(true);
    setAddError('');

    try {
      const tkpiDetail = await getTkpiDetail(addSearch.selected.id);

      const newItem = {
        // unify shape with other items
        is_manual: true,
        label: 'manual',
        confidence: 1,
        bbox: null,

        corrected: false,
        portion: 1,
        selected: true,

        currentName: tkpiDetail.name,
        baseNutrition: tkpiDetail.nutrition,
        tkpi: {
          id: tkpiDetail.id,
          name: tkpiDetail.name,
          nutrition: tkpiDetail.nutrition,
        },
      };

      const updated = [...detectionItems, newItem];
      setDetectionItems(updated);
      
      // Fire and forget API call to report missed detection
      if (analysisId) {
        reportMissedDetection({
          analysis_id: analysisId,
          missed_label: tkpiDetail.name,
          tkpi_food_id: tkpiDetail.id,
          note: 'Ditambahkan manual oleh user'
        }).catch(err => console.error("Report missed detection skipped/failed:", err));
      }
      // setTotalNutrition removed (derived)

      showToast('success', `✅ "${tkpiDetail.name}" berhasil ditambahkan ke perhitungan gizi, dan otomatis dilaporkan ke sistem untuk diperbaiki.`);
      handleCancelAddFood();
    } catch (err) {
      let msg = TOAST_MESSAGES.GENERIC_ERROR;
      if (err.message) msg = err.message;
      setAddError(msg);
      showToast('error', msg);
    } finally {
      setIsAdding(false);
    }
  };

  // ========== TRAINING REQUEST (secondary) ==========
  const handleOpenTrainingRequest = () => {
    setShowTrainingRequest(true);
    setRequestMsg('');
    setRequestNote('');
    setRequestedLabelInput('');
  };

  const handleCancelTrainingRequest = () => {
    setShowTrainingRequest(false);
    setRequestMsg('');
    setRequestNote('');
    setRequestedLabelInput('');
  };

  // Request search functions now handled by requestSearch hook (removed old duplicate code)

  const handleSubmitTrainingRequest = async () => {
    // training request depends on analysis_id (per backend contract)
    if (!analysisId) {
      const msg = '❌ Tidak ada analysis_id. Silakan deteksi foto terlebih dahulu.';
      setRequestMsg(msg);
      showToast('error', msg);
      return;
    }
    if (!requestedLabelInput.trim()) {
       // FE-only validation
      const msg = '❌ Masukkan nama label/makanan yang ingin diajukan.';
      setRequestMsg(msg);
      showToast('error', msg);
      return;
    }

    setIsRequesting(true);
    setRequestMsg('');

    try {
      // Contract: { analysis_id, requested_label, bbox, note }
      await submitClassRequest({
        analysis_id: analysisId,
        requested_label: requestedLabelInput.trim(),
        bbox: null, // Optional in contract
        note: requestNote || '',
      });

      const successMsg = `${TOAST_MESSAGES.TRAINING_REQUEST_SUCCESS} (Kelas: ${requestedLabelInput})`;
      setRequestMsg(successMsg);
      showToast('success', successMsg);

      // reset form
      setRequestedLabelInput('');
      setRequestNote('');
    } catch (err) {
      let msg = TOAST_MESSAGES.GENERIC_ERROR;
      if (err.code === 'TIMEOUT') msg = 'Proses terlalu lama. Coba lagi.';
      else if (err.code === 'SERVER_BUSY') msg = 'Server sedang sibuk. Coba lagi sebentar.';
      else if (err.message) msg = err.message;
      
      if (err.requestId) console.log(`Request ID: ${err.requestId}`);
      
      setRequestMsg(msg);
      showToast('error', msg);
    } finally {
      setIsRequesting(false);
    }
  };

  // Cleanup timers (search timers now handled by useTkpiSearch hooks)
  useEffect(() => {
    return () => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    };
  }, []);

  // Cleanup object URL untuk preview
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const shouldShowResultsSection = analysisId !== null || detectionItems.length > 0;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Toast Notification */}
      {toast && (
        <div
          data-testid="toast"
          className={`fixed top-4 right-4 z-50 max-w-sm px-4 py-3 rounded shadow-lg border ${
            toast.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          {toast.text}
        </div>
      )}

      <div className="mb-6">
        <Button onClick={() => navigate(ROUTES.HOME)} variant="secondary" size="sm" disabled={isBusyAction}>
          ← Kembali
        </Button>
      </div>

      <h1 className="text-3xl font-bold text-gray-900 mb-8">Analisis Foto Makanan</h1>

      {/* Upload Section */}
      <Card className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Upload Foto</h2>

        <div className="space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            {previewUrl ? (
              detectionItems.length > 0 ? (
                <BoundingBoxOverlay imageUrl={previewUrl} detections={detectionItems} />
              ) : (
                <img src={previewUrl} alt="Preview" className="max-h-96 mx-auto rounded" />
              )
            ) : (
              <div className="text-gray-500">
                <p className="mb-2">Pilih foto makanan</p>
                <p className="text-sm">JPG, PNG (max 5MB)</p>
              </div>
            )}
          </div>

          {/* Dual input buttons: Upload + Camera */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => uploadRef.current?.click()}
              disabled={isBusyAction}
              data-testid="file-upload"
              className="flex-1 px-4 py-3 text-sm font-medium rounded-lg border-2 border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              📁 Unggah Gambar
            </button>
            <button
              type="button"
              onClick={() => cameraRef.current?.click()}
              disabled={isBusyAction}
              data-testid="camera-upload"
              className="flex-1 px-4 py-3 text-sm font-medium rounded-lg border-2 border-green-300 bg-green-50 text-green-700 hover:bg-green-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              📷 Ambil Foto
            </button>
          </div>

          {/* Hidden file inputs */}
          <input
            ref={uploadRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />
          <input
            ref={cameraRef}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleImageUpload}
            className="hidden"
          />

          <Button onClick={handleAnalyze} disabled={!selectedFile || isBusyAction} variant="primary" className="w-full" data-testid="analyze-button">
            {loading ? (
              <>
                <Spinner size="sm" /> Menganalisis...
              </>
            ) : (
              'Deteksi Makanan'
            )}
          </Button>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded" data-testid="error-banner">
              {error}
            </div>
          )}
        </div>
      </Card>

      {/* Results / Manual add (even if detection empty) */}
      {/* Results / Manual add (even if detection empty) */}
      {shouldShowResultsSection && (
        <div data-testid="results-section">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Hasil Analisis</h2>

          {detectionItems.length === 0 && (
            <div className="mb-4 bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded">
              Tidak ada makanan terdeteksi. Kamu bisa <b>Tambah Makanan Manual</b> untuk menghitung nutrisi.
            </div>
          )}

          {/* Total Nutrition */}
          {totalNutrition && detectionItems.length > 0 && (
            <Card className="mb-6" data-testid="total-nutrition">
              <h2 className="text-xl font-semibold mb-4">Total Nutrisi</h2>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-orange-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-orange-600">{totalNutrition.energi_kal.toFixed(0)}</p>
                  <p className="text-sm text-gray-600">Energi (kal)</p>
                </div>
                <div className="bg-red-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-red-600">{totalNutrition.protein_g.toFixed(1)}</p>
                  <p className="text-sm text-gray-600">Protein (g)</p>
                </div>
                <div className="bg-yellow-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-yellow-600">{totalNutrition.lemak_g.toFixed(1)}</p>
                  <p className="text-sm text-gray-600">Lemak (g)</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-blue-600">{totalNutrition.karbo_g.toFixed(1)}</p>
                  <p className="text-sm text-gray-600">Karbo (g)</p>
                </div>
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-green-600">{totalNutrition.serat_g?.toFixed(1) || '0.0'}</p>
                  <p className="text-sm text-gray-600">Serat (g)</p>
                </div>
              </div>
            </Card>
          )}

          {/* Cards */}
          {detectionItems.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {detectionItems.map((item, index) => {
                const displayNutrition = multiplyNutrition(item.baseNutrition, item.portion || 1);
                const isBelumAda = item.nutrition_status === 'BELUM_ADA' 
                  || item.nutrition_status_label === 'Belum ada datanya'
                  || (!item.nutrition_status && !item.tkpi);

                return (
                  <Card key={index} className="relative" data-testid="detection-card">
                    {item.corrected && (
                      <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded">
                        ✓ Dikoreksi
                      </div>
                    )}

                    {item.is_manual && (
                      <div className="absolute top-2 left-2 bg-blue-600 text-white text-xs px-2 py-1 rounded">
                        manual
                      </div>
                    )}

                    <div className="mb-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900">{item.currentName}</h3>
                          <p className="text-sm text-gray-500">
                            Confidence:{' '}
                            {typeof item.confidence === 'number'
                              ? (item.confidence * 100).toFixed(1)
                              : '100.0'}
                            %
                          </p>
                          {/* Nutrition Status Badge */}
                          {(() => {
                            const badge = getNutritionBadge(item);
                            return (
                              <div className="mt-2 mb-1">
                                <span className={`inline-block text-xs px-2 py-1 rounded-full font-medium ${badge.className}`}>
                                  {badge.label}
                                </span>
                                {badge.note && (
                                  <p className="text-xs text-gray-500 mt-2 italic leading-relaxed">
                                    {badge.note}
                                  </p>
                                )}
                              </div>
                            );
                          })()}
                        </div>
                        <label 
                          className={`flex items-center gap-2 ${isBelumAda ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
                          title={isBelumAda ? 'Belum ada data gizi' : ''}
                        >
                          <input
                            type="checkbox"
                            checked={item.selected !== false}
                            onChange={() => handleToggleSelected(index)}
                            disabled={isBusyAction || isBelumAda}
                            className="w-4 h-4 text-blue-600 rounded"
                          />
                          <span className="text-sm text-gray-700">Hitung</span>
                        </label>
                      </div>
                    </div>

                    {/* Nutrition Display */}
                    {isBelumAda ? (
                      <div className="bg-gray-50 rounded-lg p-3 mb-3">
                        <p className="text-sm text-gray-500 text-center italic">
                          Data gizi belum tersedia
                        </p>
                      </div>
                    ) : (
                      <div className="bg-gray-50 rounded-lg p-3 mb-3">
                        <p className="text-xs text-gray-600 mb-2 font-semibold">Nutrisi (per 100g):</p>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-gray-600">Energi:</span>{' '}
                            <span className="ml-1 font-medium">{displayNutrition.energi_kal.toFixed(0)} kal</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Protein:</span>{' '}
                            <span className="ml-1 font-medium">{displayNutrition.protein_g.toFixed(1)} g</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Lemak:</span>{' '}
                            <span className="ml-1 font-medium">{displayNutrition.lemak_g.toFixed(1)} g</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Karbo:</span>{' '}
                            <span className="ml-1 font-medium">{displayNutrition.karbo_g.toFixed(1)} g</span>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="mb-3 pb-3 border-b">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Porsi</label>
                      <div className="flex items-center gap-2">
                        {[0.5, 1, 1.5, 2].map((p) => (
                          <button
                            key={p}
                            type="button"
                            onClick={() => handlePortionChange(index, p)}
                            disabled={isBusyAction}
                            className={`px-3 py-1 text-sm rounded ${
                              item.portion === p ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                          >
                            {p}x
                          </button>
                        ))}
                        <input
                          type="number"
                          min="0.1"
                          step="0.1"
                          value={item.portion || 1}
                          onChange={(e) => handlePortionChange(index, e.target.value)}
                          disabled={isBusyAction}
                          className="w-20 px-2 py-1 text-sm border rounded"
                        />
                      </div>
                    </div>

                    {/* EDIT MODE */}
                    {editingCardIndex === index && (
                      <div className="space-y-3 border-t pt-3">
                        <div className="flex items-start justify-between">
                          <p className="text-sm font-medium text-gray-700">Koreksi Salah Deteksi:</p>
                        </div>
                        <p className="text-xs text-gray-500 mb-2 leading-relaxed">
                          Sistem keliru mengenali makanan ini? Ganti dengan makanan yang benar. Koreksi Anda sangat berharga dan akan dikirim ke Admin untuk melatih AI kami.
                        </p>

                        <div className="relative">
                          <Input
                            type="text"
                            placeholder="Ketik nama makanan..."
                            value={editSearch.query}
                            onChange={(e) => editSearch.handleSearch(e.target.value)}
                            className="w-full"
                            data-testid="edit-search-input"
                          />

                          {editSearch.isSearching && (
                            <div className="absolute right-3 top-3">
                              <Spinner size="sm" />
                            </div>
                          )}

                          {editSearch.results.length > 0 && (
                            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                              {editSearch.results.map((r) => (
                                <button
                                  key={r.id}
                                  type="button"
                                  onClick={() => editSearch.handleSelect(r)}
                                  disabled={isBusyAction}
                                  className="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-gray-100 last:border-b-0"
                                >
                                  <p className="text-sm font-medium text-gray-900">{r.name}</p>
                                  <p className="text-xs text-gray-500">ID: {r.id}</p>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>

                        {editSearch.selected && (
                          <div className="bg-green-50 border border-green-200 rounded px-3 py-2">
                            <p className="text-sm text-green-800">✓ Dipilih: {editSearch.selected.name}</p>
                          </div>
                        )}

                        {editError && (
                          <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                            {editError}
                          </div>
                        )}

                        <div className="flex gap-2">
                          <Button
                            onClick={handleConfirmEdit}
                            disabled={!editSearch.selected || isSubmitting || isBusyAction}
                            variant="primary"
                            size="sm"
                            className="flex-1"
                            data-testid="submit-feedback-button"
                          >
                            {isSubmitting ? 'Menyimpan...' : 'Ganti'}
                          </Button>
                          <Button
                            onClick={handleCancelEdit}
                            disabled={isBusyAction}
                            variant="secondary"
                            size="sm"
                            className="flex-1"
                          >
                            Batal
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* BOTTOM BUTTONS (DEFAULT) */}
                    {editingCardIndex !== index && (
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => handleEditCard(index)}
                          disabled={isBusyAction}
                          className="flex-1 px-3 py-2 text-sm rounded bg-gray-100 text-gray-800 hover:bg-gray-200 disabled:opacity-50"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteCard(index)}
                          disabled={isBusyAction}
                          className="px-3 py-2 text-sm rounded bg-white text-red-600 border border-red-200 hover:bg-red-50 disabled:opacity-50"
                          title="Hapus card ini"
                        >
                          {deletingIndex === index ? 'Menghapus...' : 'Hapus'}
                        </button>
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          )}


          {/* ===== MANUAL ADD (PRIMARY) ===== */}
          {addingFoodIndex === null && (
            <div className="mb-4 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-5">
                <div className="flex items-start gap-4">
                  <div className="bg-blue-100 p-3 flex items-center justify-center rounded-lg">
                    <span className="text-xl">🔍</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900">Ada Makanan yang Terlewat?</h3>
                    <p className="text-sm text-gray-600 mt-1 mb-4 leading-relaxed">
                      Sistem AI kami mungkin belum mengenali semua makanan. Jika ada makanan di piring Anda yang <b>tidak terdeteksi</b> oleh sistem, Anda bisa menambahkannya secara manual agar total kalori tetap akurat. <b>Data ini juga akan kami gunakan untuk melatih AI kami ke depannya.</b>
                    </p>
                    <button
                      type="button"
                      onClick={handleOpenAddFood}
                      disabled={isBusyAction}
                      data-testid="add-manual-button"
                      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 shadow-sm"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
                      Tambah Makanan Manual
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {addingFoodIndex === 'standalone' && (
            <Card className="mb-4 border-blue-200 bg-blue-50/30">
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b border-blue-100 pb-3">
                  <h3 className="font-semibold text-blue-900 flex items-center gap-2">
                    <span className="bg-blue-200 text-blue-800 w-6 h-6 flex items-center justify-center rounded-full text-sm">1</span>
                    Cari Makanan di Database TKPI
                  </h3>
                  <button onClick={handleCancelAddFood} className="text-gray-400 hover:text-gray-600">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                  </button>
                </div>
                
                <p className="text-sm text-gray-600">
                  Makanan yang Anda tambahkan di bawah ini akan memunculkan kartu baru dan kalorinya akan ditambahkan ke <b>Total Nutrisi</b> di atas.
                </p>

                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                  </div>
                  <input
                    type="text"
                    value={addSearch.query}
                    onChange={(e) => addSearch.handleSearch(e.target.value)}
                    placeholder="Ketik nama makanan (contoh: Nasi Goreng)..."
                    className="w-full pl-10 pr-3 py-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm transition-all"
                    data-testid="add-search-input"
                    autoFocus
                  />

                  {addSearch.isSearching && (
                    <div className="absolute right-3 top-3">
                      <Spinner size="sm" />
                    </div>
                  )}

                  {addSearch.results.length > 0 && (
                    <div className="absolute z-20 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-xl max-h-60 overflow-y-auto">
                      {addSearch.results.map((r, i) => (
                        <button
                          key={r.id}
                          type="button"
                          onClick={() => addSearch.handleSelect(r)}
                          disabled={isBusyAction}
                          className={`w-full text-left px-4 py-3 hover:bg-blue-50 transition-colors ${i !== addSearch.results.length - 1 ? 'border-b border-gray-100' : ''}`}
                        >
                          <p className="font-medium text-gray-900">{r.name}</p>
                          <p className="text-xs text-gray-500 mt-0.5">Kode TKPI: {r.id}</p>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {addSearch.selected && (
                  <div className="bg-green-50 border border-green-300 rounded-lg px-4 py-3 flex items-start gap-3">
                    <svg className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    <div>
                      <p className="text-sm font-medium text-green-900">Siap ditambahkan:</p>
                      <p className="text-sm text-green-800">{addSearch.selected.name}</p>
                    </div>
                  </div>
                )}

                {addError && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm flex gap-2">
                    <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    <span>{addError}</span>
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={handleConfirmAddFood}
                    disabled={!addSearch.selected || isAdding || isBusyAction}
                    className="flex-[2] px-4 py-2.5 text-sm font-medium rounded-lg bg-blue-600 text-white shadow-sm hover:bg-blue-700 focus:ring-4 focus:ring-blue-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    {isAdding ? (
                      <span className="flex items-center justify-center gap-2"><Spinner size="sm" /> Memproses...</span>
                    ) : 'Terapkan & Hitung Kalori'}
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelAddFood}
                    disabled={isBusyAction}
                    className="flex-1 px-4 py-2.5 text-sm font-medium rounded-lg bg-white text-gray-700 border border-gray-300 shadow-sm hover:bg-gray-50 focus:ring-4 focus:ring-gray-100 disabled:opacity-50 transition-all"
                  >
                    Batal
                  </button>
                </div>

              </div>
              
              {/* Secondary link to training request */}
              <div className="mt-6 pt-4 border-t border-blue-200">
                {!showTrainingRequest ? (
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <p className="text-sm text-gray-600">
                      Makanan yang Anda cari tidak ada di *database* TKPI?
                    </p>
                    <button
                      type="button"
                      onClick={handleOpenTrainingRequest}
                      disabled={isBusyAction}
                      className="text-sm text-blue-700 font-medium hover:text-blue-800 hover:underline disabled:opacity-50 flex items-center gap-1"
                    >
                      Ajukan Kelas Baru <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                    </button>
                  </div>
                ) : null}
              </div>
            </Card>
          )}

          {/* ===== TRAINING REQUEST (SECONDARY) ===== */}
          {showTrainingRequest && (
            <Card className="mb-6 border-amber-200 bg-amber-50/30">
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-amber-100 pb-3">
                  <h3 className="text-base font-semibold text-amber-900 flex items-center gap-2">
                    <span className="text-xl">👩‍🔬</span> Ajukan Pelatihan AI (Training)
                  </h3>
                  <button
                    type="button"
                    onClick={handleCancelTrainingRequest}
                    disabled={isBusyAction}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                  </button>
                </div>

                <div className="bg-amber-100/50 p-3 rounded-lg border border-amber-200">
                  <p className="text-sm text-amber-800 leading-relaxed">
                    <b>Perhatian:</b> Form ini hanya digunakan untuk mengusulkan makanan baru agar dipelajari oleh Robot AI kami ke depannya. Memasukkan data di sini <b>tidak akan memunculkan nilai kalori</b> pada analisis Anda saat ini.
                  </p>
                </div>

                <div className="space-y-3">
                  <label className="block text-sm font-medium text-gray-800">
                    Nama Makanan Baru <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={requestedLabelInput}
                    onChange={(e) => setRequestedLabelInput(e.target.value)}
                    placeholder="Ketik nama makanan (contoh: Gudeg Jogja, Tahu Gimbal)..."
                    className="w-full px-4 py-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 shadow-sm transition-all"
                    data-testid="request-label-input"
                  />
                  <p className="text-xs text-gray-500 mt-1.5 ml-1 flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    Semakin spesifik nama ini, semakin mudah bagi Admin untuk melatih AI kami kelak.
                  </p>
                </div>

                <div className="space-y-1">
                  <label className="block text-sm font-medium text-gray-800">
                    Catatan/Deskripsi <span className="text-gray-400 font-normal">(opsional)</span>
                  </label>
                  <textarea
                    value={requestNote}
                    onChange={(e) => setRequestNote(e.target.value)}
                    placeholder="Beri tahu fitur khas makanan ini (misalnya: 'bentuknya panjang, sering ada di pecel lele', 'mirip tempe tipis')..."
                    className="w-full px-4 py-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 shadow-sm transition-all min-h-[100px] resize-y"
                  />
                </div>

                {requestMsg && (
                  <div className={`${requestMsg.includes('Berhasil') || requestMsg.includes('✅') ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'} border px-4 py-3 rounded-lg text-sm flex gap-2`}>
                    <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    <span>{requestMsg}</span>
                  </div>
                )}

                <div className="flex gap-3 pt-4 border-t border-amber-100">
                  <button
                    type="button"
                    onClick={handleSubmitTrainingRequest}
                    disabled={isRequesting || isBusyAction}
                    className="flex-[2] px-4 py-2.5 text-sm font-medium rounded-lg bg-amber-600 text-white shadow-sm hover:bg-amber-700 focus:ring-4 focus:ring-amber-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    data-testid="submit-training-request-button"
                  >
                    {isRequesting ? (
                      <span className="flex items-center justify-center gap-2"><Spinner size="sm" /> Mengirim Pengajuan...</span>
                    ) : 'Kirim Pengajuan Pelatihan AI'}
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelTrainingRequest}
                    disabled={isBusyAction}
                    className="flex-1 px-4 py-2.5 text-sm font-medium rounded-lg bg-white text-gray-700 border border-gray-300 shadow-sm hover:bg-gray-50 focus:ring-4 focus:ring-gray-100 disabled:opacity-50 transition-all"
                  >
                    Batal
                  </button>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
