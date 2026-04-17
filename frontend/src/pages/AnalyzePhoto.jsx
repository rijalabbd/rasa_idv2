// frontend/src/pages/AnalyzePhoto.jsx
import { useState, useRef, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Camera, Image as ImageIcon, Search, Edit, Trash2, Home, X, Plus, 
  CheckCircle2, BarChart2, Check, Flame, Utensils, Database, ChevronDown, ChevronUp, AlertCircle, AlertTriangle, Sun, Focus, Crop, Layers, Target, Tag, TrendingUp, Info, Send
} from 'lucide-react';

import BoundingBoxOverlay from '../components/BoundingBoxOverlay';
import Spinner from '../components/ui/Spinner';
import { detectFood } from '../services/detection';
import { getTkpiDetail, getDetectableFoodIds } from '../services/tkpi';
import { submitFeedback } from '../services/feedback';
import { reportMissedDetection } from '../services/missedDetection';
import { submitClassRequest } from '../services/api';
import { ROUTES } from '../constants/routes';
import { ANIMATION_DELAYS, TOAST_MESSAGES } from '../constants/app';
import { useTkpiSearch } from '../hooks/useTkpiSearch';
import { multiplyNutrition, calculateTotalNutrition, getNutritionBadge } from '../utils/nutrition';
import { useTour } from '../hooks/useTour';

// â”€â”€â”€ Reusable styled sub-components â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function NutriTile({ icon: Icon, label, value, unit, colorVariant }) {
  const variants = {
    blue: "bg-blue-50 text-blue-600",
    yellow: "bg-yellow-50 text-yellow-600",
    green: "bg-green-50 text-green-600",
  };
  const iconColors = {
    blue: "#3b82f6",
    yellow: "#eab308",
    green: "#22c55e",
  };
  
  return (
    <div className={`${variants[colorVariant]} rounded-xl py-3 px-2 text-center flex-1 flex flex-col items-center justify-center`}>
      {Icon && <Icon size={16} color={iconColors[colorVariant]} className="mb-1 opacity-70" />}
      <div className="text-base font-bold text-slate-800">
        {value}<span className="text-xs font-semibold ml-0.5">{unit}</span>
      </div>
      <div className="text-xs font-medium text-slate-500 mt-0.5">{label}</div>
    </div>
  );
}

function PortionBtn({ label, active, onClick, disabled }) {
  return (
    <button 
      onClick={onClick} 
      disabled={disabled}
      className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-colors border-2 
        ${active 
          ? 'border-green-500 bg-green-500 text-white' 
          : 'border-green-400 bg-white text-green-600 hover:bg-green-50'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      {label}
    </button>
  );
}

// â”€â”€â”€ Main component â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export default function AnalyzePhoto() {
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [analysisId, setAnalysisId] = useState(null);
  const [detectionItems, setDetectionItems] = useState([]);
  const [detailsOpen, setDetailsOpen] = useState({}); // To mock the "Lihat Detail" toggle
  
  const totalNutrition = useMemo(() =>
    detectionItems.length > 0 ? calculateTotalNutrition(detectionItems) : null,
  [detectionItems]);

  const editSearch = useTkpiSearch(20);
  const addSearch = useTkpiSearch(20);
  const smartSearch = useTkpiSearch(10, { fuzzy: true });

  const [editingCardIndex, setEditingCardIndex] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editError, setEditError] = useState('');

  const [addingFoodIndex, setAddingFoodIndex] = useState(null);
  const [addError, setAddError] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const [deletingIndex, setDeletingIndex] = useState(null);

  // Smart Search states (unified form for zero-detection)
  const [showSmartSearch, setShowSmartSearch] = useState(false);
  const [detectableIds, setDetectableIds] = useState(new Set());
  const [smartSearchLoading, setSmartSearchLoading] = useState(false);

  const [showTrainingRequest, setShowTrainingRequest] = useState(false);
  // ... (Training request states)
  const [requestedLabelInput, setRequestedLabelInput] = useState('');
  const [requestNote, setRequestNote] = useState('');
  const [requestMsg, setRequestMsg] = useState('');
  const [isRequesting, setIsRequesting] = useState(false);

  const isBusyAction = loading || isSubmitting || isAdding || isRequesting || deletingIndex !== null;

  // â”€â”€ Tour integration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const { isTourActive, currentStep, nextStep } = useTour();

  // Auto-advance: if tour is on step 1 (upload) but photo already exists (replay)
  // provide a manual "Lanjut" instead of waiting
  const tourUploadFulfilled = isTourActive && currentStep === 1 && selectedFile !== null;
  // Auto-advance: if tour is on step 2 (detect) but results already exist
  const tourDetectFulfilled = isTourActive && currentStep === 2 && analysisId !== null;

  // "Pakai Foto Contoh" for tour â€” loads a sample image
  const handleUseSampleImage = async () => {
    try {
      const response = await fetch('/sample_food.jpg');
      const blob = await response.blob();
      const file = new File([blob], 'sample_food.jpg', { type: 'image/jpeg' });
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setDetectionItems([]); setAnalysisId(null); setError(null);
      setDetailsOpen({});
      resetInlineStates();
    } catch {
      showToast('error', 'Gagal memuat foto contoh');
    }
  };

  const [toast, setToast] = useState(null);
  const toastTimerRef = useRef(null);
  const uploadRef = useRef(null);
  const cameraRef = useRef(null);

  // â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const resetInlineStates = () => {
    editSearch.reset(); addSearch.reset();
    setEditingCardIndex(null); setEditError('');
    setAddingFoodIndex(null); setAddError('');
    setShowTrainingRequest(false); setRequestedLabelInput('');
    setRequestNote(''); setRequestMsg('');
  };

  const showToast = (type, text) => {
    setToast({ type, text });
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(() => { setToast(null); }, ANIMATION_DELAYS.TOAST);
  };

  useEffect(() => () => { if (toastTimerRef.current) clearTimeout(toastTimerRef.current); }, []);
  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  // â”€â”€ Handlers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const handleImageUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) { showToast('error', 'File harus berupa gambar (JPG, PNG)'); return; }
    if (file.size > 5 * 1024 * 1024) { showToast('error', 'Ukuran file maksimal 5MB'); return; }
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setDetectionItems([]); setAnalysisId(null); setError(null);
    setDetailsOpen({});
    resetInlineStates();
    e.target.value = '';
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setLoading(true); setError(null);
    try {
      const result = await detectFood(selectedFile);
      const newAnalysisId = result?.analysis_id ?? null;
      setAnalysisId(newAnalysisId);
      if (!Array.isArray(result?.items)) throw new Error(TOAST_MESSAGES.INVALID_SCHEMA);
      
      const items = result.items.map(item => ({
        ...item, corrected: false, portion: 1,
        selected: item.nutrition_status !== 'BELUM_ADA' && item.nutrition_status_label !== 'Belum ada datanya' && item.tkpi !== null,
        baseNutrition: item.tkpi?.nutrition || { energi_kal: 0, protein_g: 0, lemak_g: 0, karbo_g: 0, serat_g: 0 },
        currentName: item.tkpi?.name || item.label,
      }));
      setDetectionItems(items);
      
      // Auto-open details
      const defaultDetails = {};
      items.forEach((_, i) => defaultDetails[i] = true);
      setDetailsOpen(defaultDetails);
      
      resetInlineStates();
    } catch (err) {
      // (Error handling remains unchanged for backend consistency)
      let msg;
      const ref = err?.requestId ? ` (Ref: ${err.requestId})` : '';
      if (err?.code === 'MODEL_NOT_READY') msg = `Model belum siap.${ref}`;
      else if (err?.code === 'SERVER_BUSY') msg = `Server sedang sibuk.${ref}`;
      else if (err?.code === 'TIMEOUT') msg = `Proses timeout. Coba lagi.${ref}`;
      else msg = (err?.message || 'Gagal melakukan deteksi.') + ref;
      setError(msg); showToast('error', msg);
    } finally { setLoading(false); }
  };

  const handleDeleteCard = (index) => {
    if (isBusyAction) return;
    setDeletingIndex(index);
    setTimeout(() => {
      const updated = detectionItems.filter((_, i) => i !== index);
      // Re-map indices for toggles
      const newDetails = {};
      updated.forEach((_, i) => newDetails[i] = true);
      setDetailsOpen(newDetails);

      if (editingCardIndex === index) setEditingCardIndex(null);
      if (addingFoodIndex === index) setAddingFoodIndex(null);
      if (editingCardIndex !== null && index < editingCardIndex) setEditingCardIndex(editingCardIndex - 1);
      if (addingFoodIndex !== null && index < addingFoodIndex) setAddingFoodIndex(addingFoodIndex - 1);
      
      setDetectionItems(updated); setDeletingIndex(null);
      showToast('success', TOAST_MESSAGES.DELETE_SUCCESS);
    }, ANIMATION_DELAYS.DELETE);
  };

  const handleToggleSelected = (index) => {
    const u = [...detectionItems]; u[index].selected = !u[index].selected; setDetectionItems(u);
  };

  const handlePortionChange = (index, val) => {
    let p = parseFloat(val); if (isNaN(p) || p < 0.1) p = 0.1;
    const u = [...detectionItems]; u[index].portion = p; setDetectionItems(u);
  };

  const toggleDetail = (index) => {
    setDetailsOpen(prev => ({ ...prev, [index]: !prev[index] }));
  };

  const handleEditCard = (index) => {
    if (isBusyAction) return;
    setEditingCardIndex(index); setAddingFoodIndex(null); setShowTrainingRequest(false); setEditError(''); editSearch.reset();
    setTimeout(() => {
      document.getElementById(`edit-panel-${index}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
  };
  const handleCancelEdit = () => { setEditingCardIndex(null); setEditError(''); editSearch.reset(); };

  const handleConfirmEdit = async () => {
    if (!editSearch.selected || editingCardIndex === null) return;
    setIsSubmitting(true); setEditError('');
    const item = detectionItems[editingCardIndex];
    try {
      if (!item.is_manual) await submitFeedback({ analysis_id: analysisId, items: [{ bbox: item.bbox, predicted_label: item.label, corrected_tkpi_id: editSearch.selected.id, note: '' }] });
      const detail = await getTkpiDetail(editSearch.selected.id);
      const u = [...detectionItems];
      u[editingCardIndex] = { ...item, corrected: true, currentName: detail.name, baseNutrition: detail.nutrition, tkpi: { id: detail.id, name: detail.name, nutrition: detail.nutrition } };
      setDetectionItems(u);
      showToast('success', `"${detail.name}" berhasil dikoreksi.`);
      handleCancelEdit();
    } catch (err) {
      const msg = err?.code === 'TIMEOUT' ? 'Proses terlalu lama.' : err?.code === 'SERVER_BUSY' ? 'Server sedang sibuk.' : err?.message || TOAST_MESSAGES.GENERIC_ERROR;
      setEditError(msg); showToast('error', msg);
    } finally { setIsSubmitting(false); }
  };

  const handleOpenAddFood = () => { 
    if (isBusyAction) return; 
    setAddingFoodIndex('standalone'); setEditingCardIndex(null); addSearch.reset(); setAddError(''); 
    setTimeout(() => {
      document.getElementById('add-food-panel')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
  };
  const handleCancelAddFood = () => { setAddingFoodIndex(null); addSearch.reset(); setAddError(''); };

  const handleConfirmAddFood = async () => {
    if (!addSearch.selected) { setAddError(TOAST_MESSAGES.SELECT_FOOD); return; }
    setIsAdding(true); setAddError('');
    try {
      const detail = await getTkpiDetail(addSearch.selected.id);
      const newItem = { is_manual: true, label: 'manual', confidence: 1, bbox: null, corrected: false, portion: 1, selected: true, currentName: detail.name, baseNutrition: detail.nutrition, tkpi: { id: detail.id, name: detail.name, nutrition: detail.nutrition } };
      setDetectionItems([...detectionItems, newItem]);
      setDetailsOpen(prev => ({ ...prev, [detectionItems.length]: true }));
      if (analysisId) reportMissedDetection({ analysis_id: analysisId, missed_label: detail.name, tkpi_food_id: detail.id, note: 'Ditambahkan manual' }).catch(() => {});
      showToast('success', `"${detail.name}" berhasil ditambahkan.`);
      handleCancelAddFood();
    } catch (err) { const msg = err?.message || TOAST_MESSAGES.GENERIC_ERROR; setAddError(msg); showToast('error', msg); }
    finally { setIsAdding(false); }
  };

  const handleOpenTrainingRequest = () => { setShowTrainingRequest(true); setRequestMsg(''); setRequestNote(''); setRequestedLabelInput(''); };
  const handleCancelTrainingRequest = () => { setShowTrainingRequest(false); setRequestMsg(''); setRequestNote(''); setRequestedLabelInput(''); };

  // -- Smart Search: unified zero-detection form ----------------------
  const handleOpenSmartSearch = async () => {
    setShowSmartSearch(true);
    smartSearch.reset();
    setRequestMsg('');
    setRequestNote('');
    setRequestedLabelInput('');
    setSmartSearchLoading(true);
    try {
      const ids = await getDetectableFoodIds();
      setDetectableIds(ids);
    } catch {
      setDetectableIds(new Set());
    } finally {
      setSmartSearchLoading(false);
    }
  };

  const handleCloseSmartSearch = () => {
    setShowSmartSearch(false);
    smartSearch.reset();
    setRequestMsg('');
    setRequestNote('');
    setRequestedLabelInput('');
  };

  const handleSmartAddFood = async (tkpiItem) => {
    if (isBusyAction) return;
    setIsAdding(true);
    try {
      const detail = await getTkpiDetail(tkpiItem.id);
      const newItem = { is_manual: true, label: 'manual', confidence: 1, bbox: null, corrected: false, portion: 1, selected: true, currentName: detail.name, baseNutrition: detail.nutrition, tkpi: { id: detail.id, name: detail.name, nutrition: detail.nutrition } };
      setDetectionItems(prev => [...prev, newItem]);
      setDetailsOpen(prev => ({ ...prev, [detectionItems.length]: true }));
      if (analysisId) reportMissedDetection({ analysis_id: analysisId, missed_label: detail.name, tkpi_food_id: detail.id, note: 'Ditambahkan via smart search' }).catch(() => {});
      showToast('success', `"${detail.name}" berhasil ditambahkan.`);
      handleCloseSmartSearch();
    } catch (err) {
      showToast('error', err?.message || TOAST_MESSAGES.GENERIC_ERROR);
    } finally {
      setIsAdding(false);
    }
  };

  // -- Unified class request handler ----------------------------------
  // Bug fix 1: handleSubmitTrainingRequest was missing reportMissedDetection
  // Bug fix 2: handleSmartClassRequest was missing SERVER_BUSY error handling
  const handleSubmitClassRequest = async (label, note = '') => {
    const trimmedLabel = label?.trim();
    if (!analysisId) { const m = 'Silakan deteksi foto terlebih dahulu.'; setRequestMsg(m); showToast('error', m); return; }
    if (!trimmedLabel) { const m = 'Masukkan nama makanan yang ingin diajukan.'; setRequestMsg(m); showToast('error', m); return; }
    setIsRequesting(true); setRequestMsg('');
    try {
      await submitClassRequest({ analysis_id: analysisId, requested_label: trimmedLabel, bbox: null, note: note || '' });
      reportMissedDetection({ analysis_id: analysisId, missed_label: trimmedLabel, note: 'Makanan belum ada di database - class request' }).catch(() => {});
      const msg = `Laporan berhasil dikirim! Makanan "${trimmedLabel}" akan kami pertimbangkan.`;
      setRequestMsg(msg); showToast('success', msg);
      setRequestedLabelInput(''); setRequestNote('');
    } catch (err) {
      const msg = err?.code === 'TIMEOUT' ? 'Proses terlalu lama.'
        : err?.code === 'SERVER_BUSY' ? 'Server sedang sibuk.'
        : err?.message || TOAST_MESSAGES.GENERIC_ERROR;
      setRequestMsg(msg); showToast('error', msg);
    } finally { setIsRequesting(false); }
  };

    const shouldShowResults = analysisId !== null || detectionItems.length > 0;

  // â”€â”€ Derived State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const calorieRanked = useMemo(() => {
    const selected = detectionItems.filter(it => it.selected && it.baseNutrition);
    const withCal = selected.map(it => ({ name: it.currentName, kal: Math.round((it.baseNutrition.energi_kal || 0) * (it.portion || 1)) }));
    return withCal.sort((a, b) => b.kal - a.kal);
  }, [detectionItems]);

  const avgConf = useMemo(() => {
    const auto = detectionItems.filter(it => !it.is_manual && typeof it.confidence === 'number');
    if (!auto.length) return null;
    return Math.round(auto.reduce((s, it) => s + it.confidence, 0) / auto.length * 100);
  }, [detectionItems]);

  // Pill badge colors sequence
  const getPillColors = (index) => {
    const sequence = [
      "border-blue-400 text-blue-600 bg-blue-50",
      "border-amber-400 text-amber-600 bg-amber-50",
      "border-green-400 text-green-600 bg-green-50",
      "border-purple-400 text-purple-600 bg-purple-50",
      "border-pink-400 text-pink-600 bg-pink-50"
    ];
    return sequence[index % sequence.length];
  };

  const getRankColors = (index) => {
    const bgs = ["bg-blue-500", "bg-amber-500", "bg-green-500", "bg-purple-500", "bg-pink-500"];
    return bgs[index % bgs.length];
  };

  // â”€â”€ RENDER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  return (
    <div className="font-sans min-h-screen bg-[#f0fdf8] text-slate-800 pb-16">
      
      {/* Toast Notification */}
      {toast && (
        <div className={`toast-wrap fixed top-4 right-4 z-[9999] max-w-sm p-4 rounded-xl shadow-lg border text-sm font-semibold flex items-start gap-3
          ${toast.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
          {toast.type === 'success' ? <CheckCircle2 size={18} className="text-emerald-500 mt-0.5" /> : <AlertCircle size={18} className="text-red-500 mt-0.5" />}
          <div>{toast.text}</div>
        </div>
      )}

      {/* â”€â”€ Header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      {!shouldShowResults ? (
        <div className="bg-transparent px-6 py-6 flex items-center">
          <button 
            onClick={() => navigate(ROUTES.HOME)} 
            disabled={isBusyAction} 
            className="flex items-center gap-2 text-slate-500 hover:text-[#10b981] font-semibold text-sm group transition-all"
          >
            <Home size={16} /> <span className="group-hover:underline">Kembali</span>
          </button>
        </div>
      ) : (
        <div className="bg-white/90 border-b border-slate-100 px-5 py-4 shadow-sm flex items-center justify-between">
          <div className="flex flex-col">
            <h1 className="text-base font-bold text-slate-900 leading-tight">Hasil Deteksi</h1>
            <p className="text-[11px] text-slate-400 font-medium">Analisis gizi makanan Anda</p>
          </div>
          <button 
            onClick={() => { setDetectionItems([]); setAnalysisId(null); setPreviewUrl(null); setSelectedFile(null); setError(null); resetInlineStates(); }}
            disabled={isBusyAction} 
            className="flex items-center gap-1.5 text-slate-500 hover:text-[#10b981] font-semibold text-xs bg-slate-50 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-300 px-3 py-2 rounded-xl transition-all"
          >
            <Camera size={14} /> Foto Baru
          </button>
        </div>
      )}

      <div className={`mx-auto p-4 sm:p-6 lg:p-8 transition-all ${shouldShowResults ? 'max-w-7xl' : 'max-w-3xl'}`}>

        {/* â”€â”€ CSS untuk Animasi Form â”€â”€ */}
        <style>{`
          @keyframes cameraBounce { 
            0%, 100% { transform: translateY(0); } 
            50% { transform: translateY(-8px); } 
          }
          @keyframes pulseRing {
            0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
            70% { box-shadow: 0 0 0 16px rgba(16, 185, 129, 0); }
            100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
          }
          @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
          }
          .anim-camera { animation: cameraBounce 3s ease-in-out infinite; }
          .anim-pulse-ring { animation: pulseRing 2s infinite cubic-bezier(0.4, 0, 0.2, 1); }
          .btn-shimmer {
            background-size: 200% auto;
            background-image: linear-gradient(90deg, #10b981 0%, #34d399 20%, #10b981 40%, #10b981 100%);
            animation: shimmer 2.5s linear infinite;
          }

          /* â”€â”€ Mobile Responsive: AnalyzePhoto â”€â”€ */
          @media (max-width: 640px) {
            /* Results two-column â†’ single column */
            .results-layout { flex-direction: column !important; }
            
            /* Left sticky col: remove sticky on mobile */
            .left-col { 
              width: 100% !important; 
              position: static !important; 
              top: auto !important;
            }

            /* Ranking card header: wrap on small screens */
            .ranking-header { flex-wrap: wrap; gap: 8px !important; }
            .ranking-total { text-align: left !important; }
            .ranking-total .text-3xl { font-size: 1.5rem !important; }

            /* Nutrition tiles: compact text */
            .nutri-value { font-size: 0.9rem !important; }

            /* Detection card: reduce padding */
            .detection-card { padding: 16px !important; border-radius: 16px !important; }

            /* Portion buttons: make them smaller */
            .portion-btn-group { gap: 4px !important; flex-wrap: wrap !important; }

            /* Summary card: smaller font */
            .summary-count { font-size: 2rem !important; }

            /* Upload card: tighter padding on small phones */
            .upload-card { padding: 20px 16px !important; }
            .upload-card h1 { font-size: 1.35rem !important; }

            /* Toast: full width on mobile */
            .toast-wrap { right: 12px !important; left: 12px !important; max-width: 100% !important; }
          }

          @media (max-width: 400px) {
            .left-col { width: 100% !important; }
            .detection-card { padding: 12px !important; }
            .summary-count { font-size: 1.75rem !important; }
          }
        `}</style>


        {/* â”€â”€ Upload Section Redesigned â”€â”€ */}
        {!shouldShowResults && (
          <div className="upload-card bg-white rounded-[24px] shadow-[0_4px_24px_rgba(0,0,0,0.06)] p-6 md:p-10 text-center relative overflow-hidden max-w-[560px] mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h1 className="text-2xl md:text-3xl font-extrabold text-[#0f172a] mb-2 tracking-tight">Upload Foto Makanan</h1>
            <p className="text-slate-500 text-sm md:text-base font-medium mb-8">AI kami akan menganalisis kandungan gizi secara otomatis</p>

            <div data-tour="upload-zone">
            {/* Drop zone */}
            <div
              onClick={() => { if(!previewUrl) uploadRef.current?.click() }}
              className={`relative rounded-[20px] transition-all duration-200 w-full min-h-[320px] flex flex-col items-center justify-center p-6 border-2
                ${previewUrl 
                  ? 'border-transparent bg-slate-900/5 shadow-inner' 
                  : 'border-dashed border-emerald-300 bg-emerald-50/50 hover:bg-[#10b981]/10 border-solid hover:border-[#10b981] cursor-pointer'
                }
              `}
            >
              {previewUrl ? (
                <>
                  <div className="absolute inset-0 rounded-[18px] overflow-hidden">
                    <img src={previewUrl} alt="Preview" className="w-full h-full object-contain" />
                  </div>
                  <div className="absolute inset-0 bg-black/10 opacity-0 hover:opacity-100 transition-opacity flex items-start justify-end p-4 rounded-[18px]">
                    <button 
                      onClick={(e) => { e.stopPropagation(); setSelectedFile(null); setPreviewUrl(null); }}
                      className="bg-white hover:bg-red-500 hover:text-white text-slate-700 p-2 rounded-full shadow-lg transition-transform hover:scale-105 active:scale-95"
                      title="Hapus Foto"
                    >
                      <X size={20} strokeWidth={3} />
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className="anim-pulse-ring bg-white p-5 rounded-full shadow-sm border border-emerald-100 mb-6">
                    <Camera size={44} className="text-[#10b981] anim-camera" strokeWidth={1.5} />
                  </div>
                  <h3 className="text-slate-700 font-bold text-base mb-1">Ambil atau pilih dari galeri</h3>
                  <p className="text-slate-400 text-xs font-medium mb-3">Drag & drop foto ke sini</p>
                  <p className="text-slate-400 text-[10px] uppercase tracking-widest font-bold">Format: JPG, PNG â€” Maks. 10MB</p>
                </>
              )}
            </div>

            {/* Buttons Row (Only shows if NO image selected) */}
            {!previewUrl && (
              <div data-tour="upload-buttons" className="flex flex-col sm:flex-row gap-3 mt-8">
                <button 
                  onClick={() => cameraRef.current?.click()} 
                  disabled={isBusyAction}
                  className="flex-1 bg-[#10b981] hover:bg-emerald-600 active:scale-[0.98] text-white font-bold py-3.5 px-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-md shadow-emerald-500/20"
                >
                  <Camera size={18} /> Ambil Foto Baru
                </button>
                <button 
                  onClick={() => uploadRef.current?.click()} 
                  disabled={isBusyAction}
                  className="flex-1 bg-transparent hover:bg-emerald-50 border-2 border-[#10b981] active:scale-[0.98] text-[#10b981] font-bold py-3.5 px-4 rounded-xl flex items-center justify-center gap-2 transition-all"
                >
                  <ImageIcon size={18} /> Pilih dari Galeri
                </button>
              </div>
            )}

            {/* "Pakai Foto Contoh" â€” only visible during tour */}
            {isTourActive && !selectedFile && (
              <button
                onClick={handleUseSampleImage}
                disabled={isBusyAction}
                className="w-full mt-4 bg-amber-50 hover:bg-amber-100 border-2 border-amber-200 text-amber-700 font-bold py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-colors"
              >
                <ImageIcon size={18} /> Pakai Foto Contoh
              </button>
            )}

            {/* Process Button (Only shows if image IS selected) */}
            {previewUrl && (
              <button 
                data-tour="detect-button"
                onClick={handleAnalyze} 
                disabled={isBusyAction}
                className={`w-full mt-6 text-white font-bold py-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg hover:-translate-y-1 active:translate-y-0
                  ${isBusyAction ? 'opacity-70 cursor-not-allowed bg-slate-400 shadow-none hover:translate-y-0' : 'btn-shimmer shadow-emerald-500/30'}
                `}
              >
                {loading ? <><Spinner size="sm" /> Memproses...</> : 'Analisis Sekarang'}
              </button>
            )}
            </div>{/* close data-tour="upload-zone" wrapper */}

            {error && (
              <div className="mt-6 bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 text-sm font-medium flex items-center justify-center gap-2 animate-in slide-in-from-top-2">
                <AlertCircle size={18} /> {error}
              </div>
            )}
          </div>
        )}

        {/* â”€â”€ Results Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        {shouldShowResults && (
          <div className="results-layout flex flex-col lg:flex-row gap-6 lg:gap-8 items-start">
            
            {/* === KOLOM KIRI: Foto & Ringkasan (Sticky) === */}
            <div className="left-col w-full lg:w-[400px] xl:w-[450px] shrink-0 lg:sticky lg:top-28 space-y-6">

            {/* Detection Summary Card */}
            <div data-tour="summary-card" className={`border rounded-3xl p-6 text-left shadow-sm relative overflow-hidden transition-colors ${detectionItems.length === 0 ? 'bg-[#FFFBEB] border-amber-200' : 'bg-gradient-to-b from-teal-50 to-white border-teal-100'}`}>
              
              <div className="flex items-start justify-between mb-4">
                <div className={`rounded-2xl p-3.5 shadow-md relative w-fit ${detectionItems.length === 0 ? 'bg-[#F59E0B]' : 'bg-[#10B981]'}`}>
                  <Camera size={26} className="text-white" />
                  <div className={`absolute -top-2 -right-2 bg-white text-[9px] font-bold px-1.5 py-0.5 rounded shadow-sm border ${detectionItems.length === 0 ? 'text-amber-600 border-amber-100' : 'text-[#10b981] border-emerald-100'}`}>AI</div>
                </div>
                
                {detectionItems.length === 0 && (
                  <div className="bg-amber-100 text-amber-700 text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-wider">
                    Perhatian
                  </div>
                )}
              </div>
              
              <div className={`inline-block border text-[10px] font-bold px-3 py-1 rounded-full mb-3 uppercase tracking-wide ${detectionItems.length === 0 ? 'bg-white border-amber-200 text-amber-600' : 'bg-emerald-50 border-emerald-200 text-[#10b981]'}`}>
                Model YOLOv8-Indonesian
              </div>
              
              <div className={`summary-count text-4xl font-extrabold mb-1 tracking-tight ${detectionItems.length === 0 ? 'text-[#0f172a]' : 'text-[#10b981]'}`}>
                <span className={detectionItems.length === 0 ? 'text-[#F59E0B]' : ''}>{detectionItems.length}</span> Makanan
              </div>
              <div className="text-sm font-medium text-slate-500 mb-5">Berhasil Terdeteksi</div>
              
              {avgConf !== null && detectionItems.length > 0 && (
                <div className="flex items-center justify-start gap-1.5 text-sm font-medium text-slate-600 mb-6">
                  Confidence rata-rata <span className="text-emerald-500 font-bold ml-1">{avgConf}%</span> <CheckCircle2 size={16} className="text-emerald-500" />
                </div>
              )}

              {/* Bounding box image / Preview */}
              {previewUrl && (
                <div className={`mt-4 rounded-[20px] overflow-hidden shadow-sm relative border-[6px] ${detectionItems.length === 0 ? 'border-white bg-slate-100' : 'border-white bg-slate-900'}`}>
                  {detectionItems.length > 0 ? (
                    <BoundingBoxOverlay imageUrl={previewUrl} detections={detectionItems} />
                  ) : (
                    <img src={previewUrl} alt="Uploaded preview" className="w-full object-cover" />
                  )}
                  <div className={`absolute bottom-2 left-2 backdrop-blur-md text-white text-[9px] uppercase font-bold px-2 py-1 rounded ${detectionItems.length === 0 ? 'bg-black/40' : 'bg-black/60'}`}>Foto Anda</div>
                  {detectionItems.length > 0 && <div className="absolute bottom-2 right-2 bg-emerald-500 text-white text-[9px] uppercase font-bold px-2 py-1 rounded">{detectionItems.length} objek</div>}
                </div>
              )}
            </div>

            </div>
            {/* === AKHIR KOLOM KIRI === */}

            {/* === KOLOM KANAN: Ranking & Detail Makanan === */}
            <div className="flex-1 w-full min-w-0 space-y-6">

            {/* Calorie Ranking Card (Matches Gambar 3.8) */}
            {totalNutrition && calorieRanked.length > 0 && (
              <div data-tour="ranking-card" className="bg-white rounded-[24px] p-6 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)] border border-slate-100">
                <div className="ranking-header flex justify-between items-start mb-8">
                  <div className="flex items-center gap-3">
                    <div className="bg-orange-500 rounded-xl p-2.5 shadow-sm shadow-orange-200">
                      <BarChart2 size={24} className="text-white" />
                    </div>
                    <div>
                      <div className="font-extrabold text-slate-800 text-lg">Ranking Kalori</div>
                      <div className="text-xs font-medium text-slate-400">Urutan tertinggi ke terendah</div>
                    </div>
                  </div>
                  <div className="ranking-total text-right">
                    <div className="text-3xl font-black text-orange-500 leading-tight">{totalNutrition.energi_kal.toFixed(0)}</div>
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Total kalori</div>
                  </div>
                </div>

                {/* Bars */}
                <div className="space-y-4 mb-8">
                  {calorieRanked.map((item, i) => {
                    const maxKal = calorieRanked[0]?.kal || 1;
                    const pct = Math.round((item.kal / maxKal) * 100);
                    const rankBgColor = getRankColors(i);
                    return (
                      <div key={i} className="flex items-center gap-4">
                        <div className={`w-7 h-7 shrink-0 rounded-full ${rankBgColor} text-white text-sm font-bold flex items-center justify-center shadow-sm`}>
                          {i + 1}
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between items-end mb-1.5">
                            <span className="text-sm font-bold text-slate-700">{item.name}</span>
                            <span className="text-xs font-semibold text-slate-400">
                              <span className="text-orange-500">{item.kal}</span> kalori
                              <span className="ml-2 font-black">{pct}%</span>
                            </span>
                          </div>
                          <div className="bg-slate-100 rounded-full h-2.5 overflow-hidden">
                            <div className={`h-full rounded-full ${rankBgColor} transition-all duration-700 ease-out`} style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Macro tiles */}
                <div className="flex gap-3 pt-2">
                  <NutriTile colorVariant="blue" label="Protein" value={totalNutrition.protein_g.toFixed(1)} unit="g" />
                  <NutriTile colorVariant="yellow" label="Lemak" value={totalNutrition.lemak_g.toFixed(1)} unit="g" />
                  <NutriTile colorVariant="green" label="Karbo" value={totalNutrition.karbo_g.toFixed(1)} unit="g" />
                </div>

                {/* Timestamp */}
                <div className="mt-6 pt-4 border-t border-slate-100 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Terdeteksi pada: {new Date().toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })}
                </div>
              </div>
            )}

            {/* ðŸ”´ ZERO DETECTION â€” UNIFIED SMART SEARCH ðŸ”´ */}
            {detectionItems.length === 0 && (
              <div className="space-y-6">
                
                {/* 1. Alert */}
                <div className="bg-amber-50 border-2 border-amber-200 rounded-[20px] p-6 shadow-sm relative overflow-hidden">
                  <div className="flex items-start gap-4 mb-6">
                    <div className="bg-amber-100 p-2.5 rounded-2xl shrink-0 border border-amber-200/50">
                      <AlertTriangle size={24} className="text-amber-600" />
                    </div>
                    <div>
                      <h3 className="text-amber-900 font-bold text-base md:text-lg mb-1 tracking-tight">Makanan Tidak Terdeteksi</h3>
                      <p className="text-sm font-medium text-amber-800/80 leading-relaxed">
                        Bisa terjadi karena foto kurang optimal atau makanan belum dikenali oleh sistem AI kami.
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row gap-3 mt-4">
                    <button 
                      onClick={() => { setSelectedFile(null); setPreviewUrl(null); setAnalysisId(null); setDetectionItems([]); setShowSmartSearch(false); uploadRef.current?.click(); }}
                      className="flex-1 bg-[#F59E0B] hover:bg-amber-600 text-white font-bold py-3.5 px-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-sm active:scale-95 border border-amber-600"
                    >
                      <Camera size={18} /> Foto Ulang
                    </button>
                    <button 
                      onClick={handleOpenSmartSearch}
                      disabled={isBusyAction || showSmartSearch}
                      className="flex-1 bg-white hover:bg-emerald-50 border-2 border-emerald-400 text-emerald-700 font-bold py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-all active:scale-95 shadow-sm disabled:opacity-60"
                    >
                      <Search size={18} /> Cari & Tambah Makanan
                    </button>
                  </div>
                </div>

                {/* 2. Unified Smart Search Form */}
                {showSmartSearch && (
                  <div className="bg-white border-2 border-emerald-300 rounded-[20px] p-6 shadow-lg relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400" />
                    
                    <div className="flex justify-between items-center mb-4 mt-1">
                      <h3 className="font-extrabold text-slate-800 text-sm flex items-center gap-2">
                        <Search size={16} className="text-emerald-500" /> Cari & Tambah Makanan
                      </h3>
                      <button onClick={handleCloseSmartSearch} className="text-slate-400 hover:text-slate-600 p-1.5 bg-slate-50 rounded-full transition-colors hover:bg-slate-100">
                        <X size={16} strokeWidth={3} />
                      </button>
                    </div>

                    {/* Search Input */}
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search size={16} className="text-slate-400" />
                      </div>
                      <input 
                        type="text" 
                        value={smartSearch.query} 
                        onChange={e => { smartSearch.handleSearch(e.target.value); setRequestedLabelInput(e.target.value); }}
                        placeholder="Ketik nama makanan (contoh: Stroberi, Gudeg, Papeda)..."
                        className="w-full pl-10 pr-10 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 outline-none transition-all shadow-inner" 
                        autoFocus
                      />
                      {(smartSearch.isSearching || smartSearchLoading) && <div className="absolute right-3 top-3"><Spinner size="sm" /></div>}
                    </div>

                    {/* Dynamic Results Area */}
                    {smartSearch.query.trim().length > 0 && !smartSearch.isSearching && (
                      <div className="mt-4">
                        {smartSearch.results.length > 0 ? (
                          /* === RESULTS FOUND: Show tagged food list === */
                          <div className="space-y-2">
                            {smartSearch.results.slice(0, 5).map(r => {
                              const isDetectable = detectableIds.has(r.id);
                              return (
                                <div key={r.id} className={`flex items-center justify-between p-3 rounded-xl border transition-all hover:shadow-sm ${
                                  isDetectable 
                                    ? 'bg-emerald-50/50 border-emerald-200 hover:bg-emerald-50' 
                                    : 'bg-blue-50/50 border-blue-200 hover:bg-blue-50'
                                }`}>
                                  <div className="flex items-center gap-3 min-w-0">
                                    <div className={`shrink-0 p-1.5 rounded-lg ${isDetectable ? 'bg-emerald-100' : 'bg-blue-100'}`}>
                                      {isDetectable 
                                        ? <CheckCircle2 size={16} className="text-emerald-600" /> 
                                        : <Database size={16} className="text-blue-600" />
                                      }
                                    </div>
                                    <div className="min-w-0">
                                      <div className="text-sm font-bold text-slate-800 truncate">{r.name}</div>
                                      <div className="flex items-center gap-2 mt-0.5">
                                        {r.nutrition?.energi_kal && (
                                          <span className="text-[11px] font-semibold text-slate-400">{r.nutrition.energi_kal} kal</span>
                                        )}
                                        <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                                          isDetectable 
                                            ? 'bg-emerald-100 text-emerald-700' 
                                            : 'bg-blue-100 text-blue-700'
                                        }`}>
                                          {isDetectable ? 'Kelas Deteksi' : 'Database Gizi'}
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                  <button 
                                    onClick={() => handleSmartAddFood(r)}
                                    disabled={isBusyAction}
                                    className={`shrink-0 p-2 rounded-xl font-bold text-white transition-all active:scale-90 shadow-sm ${
                                      isDetectable
                                        ? 'bg-emerald-500 hover:bg-emerald-600'
                                        : 'bg-blue-500 hover:bg-blue-600'
                                    }`}
                                    title="Tambahkan ke hasil"
                                  >
                                    <Plus size={18} strokeWidth={3} />
                                  </button>
                                </div>
                              );
                            })}

                            {/* Fallback: food not in the list */}
                            <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
                              <span className="text-[11px] font-semibold text-slate-500">
                                Bukan yang Anda cari?
                              </span>
                              <button 
                                onClick={() => { setRequestedLabelInput(smartSearch.query); setShowSmartSearch(false); handleOpenTrainingRequest(); }}
                                className="text-[11px] font-bold text-orange-500 hover:text-orange-600 flex items-center gap-1 transition-colors"
                              >
                                <Send size={12} /> Laporkan sebagai makanan baru
                              </button>
                            </div>
                          </div>
                        ) : (
                          /* === NOT FOUND: Class Request Form === */
                          <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
                            <div className="flex items-start gap-3 mb-4">
                              <AlertCircle size={18} className="text-orange-500 shrink-0 mt-0.5" />
                              <div>
                                <div className="text-sm font-bold text-orange-800 mb-1">
                                  "{smartSearch.query}" belum ada di database kami
                                </div>
                                <div className="text-xs font-medium text-orange-700/80 leading-relaxed">
                                  Makanan ini belum tersedia di database gizi maupun sistem deteksi. Masukkan nama dan deskripsi singkat, kami akan mempertimbangkan untuk menambahkannya.
                                </div>
                              </div>
                            </div>
                            
                            <textarea 
                              value={requestNote} 
                              onChange={e => setRequestNote(e.target.value)} 
                              placeholder="Deskripsi singkat (opsional, contoh: buah segar, makanan khas Jogja)..."
                              className="w-full px-4 py-2.5 bg-white border border-orange-200 rounded-xl text-sm font-medium focus:border-orange-500 focus:ring-2 focus:ring-orange-100 outline-none transition-all min-h-[60px] resize-y mb-3" 
                            />

                            {requestMsg && (
                              <div className={`mb-3 p-3 rounded-xl text-xs font-bold flex items-center gap-2 ${requestMsg.includes('berhasil') ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' : 'bg-red-100 text-red-800 border border-red-200'}`}>
                                {requestMsg.includes('berhasil') ? <CheckCircle2 size={14} className="shrink-0" /> : <AlertCircle size={14} className="shrink-0" />}
                                {requestMsg}
                              </div>
                            )}

                            <button 
                              onClick={() => handleSubmitClassRequest(smartSearch.query, requestNote)}
                              disabled={isRequesting || isBusyAction}
                              className="w-full py-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-sm shadow-sm transition-colors disabled:opacity-50 flex justify-center items-center gap-2"
                            >
                              {isRequesting ? <Spinner size="sm" /> : <Send size={16} />}
                              {isRequesting ? 'Mengirim...' : 'Kirim Laporan Makanan Baru'}
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* 3. Tips Reminder Strip */}
                <div>
                  <h4 className="text-[11px] uppercase tracking-wider font-bold text-slate-400 mb-3 ml-1">Tips untuk hasil terbaik:</h4>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { icon: Sun, label: 'Pencahayaan Terang' },
                      { icon: Layers, label: 'Hindari Tertumpuk' },
                      { icon: Target, label: 'Foto dari Tengah Atas' }
                    ].map((tip, idx) => (
                      <div key={idx} className="bg-white border text-center border-slate-200 rounded-2xl p-4 shadow-sm flex flex-col items-center gap-3">
                        <tip.icon size={22} className="text-[#10b981]" strokeWidth={2} />
                        <span className="text-[10px] md:text-xs font-bold text-slate-600 leading-tight">{tip.label}</span>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            )}

            {/* â”€â”€ Pilih semua / Kosongkan (Matches Gambar 3.9 top) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
            {detectionItems.length > 0 && (
              <div className="flex gap-3 px-1">
                <button 
                  onClick={() => setDetectionItems(detectionItems.map(it => ({ ...it, selected: true })))} 
                  disabled={isBusyAction}
                  className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-600 active:scale-95 transition-all text-white text-sm font-bold rounded-full shadow-sm"
                >
                  Pilih semua
                </button>
                <button 
                  onClick={() => setDetectionItems(detectionItems.map(it => ({ ...it, selected: false })))} 
                  disabled={isBusyAction}
                  className="px-5 py-2.5 bg-white border-2 border-emerald-400 hover:bg-emerald-50 active:scale-95 transition-all text-emerald-600 text-sm font-bold rounded-full shadow-sm"
                >
                  Kosongkan semua
                </button>
              </div>
            )}

            {/* â”€â”€ Food Detail Cards (Matches Gambar 3.9) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
            <div className="space-y-4">
              {detectionItems.map((item, index) => {
                const displayNutrition = multiplyNutrition(item.baseNutrition, item.portion || 1);
                const isBelumAda = item.nutrition_status === 'BELUM_ADA' || item.nutrition_status_label === 'Belum ada datanya' || (!item.nutrition_status && !item.tkpi);
                const badge = getNutritionBadge(item);
                const isEditing = editingCardIndex === index;
                const isSelected = item.selected !== false;
                const isDetailsOpen = detailsOpen[index];

                const originalDetectedName = (item.label && item.label !== 'manual') ? item.label : item.currentName;
                const displayTitle = (originalDetectedName || '').replace(/_/g, ' ');
                const displaySubtitle = (item.currentName && item.currentName !== originalDetectedName) ? item.currentName : null;

                return (
                  <div key={index} data-tour={index === 0 ? 'food-card' : undefined} className={`bg-white rounded-[20px] p-4 sm:p-6 shadow-sm border transition-all duration-200 w-full ${isSelected ? 'border-emerald-200 ring-1 ring-emerald-50' : 'border-[#E5E7EB]'} ${isBelumAda ? 'opacity-80' : ''}`}>
                    
                    {/* Header row */}
                    <div className="flex justify-between items-start gap-2 mb-2">
                       <div className="flex gap-2 sm:gap-3 items-center min-w-0">
                          <div 
                            className={`shrink-0 cursor-pointer transition-transform hover:scale-105 active:scale-95 ${isBelumAda ? 'opacity-50 cursor-not-allowed' : ''}`}
                            onClick={() => !isBelumAda && !isBusyAction && handleToggleSelected(index)}
                          >
                             {isSelected ? <CheckCircle2 size={24} className="text-[#10b981]" fill="#ecfdf5" /> : <div className="w-[24px] h-[24px] rounded-full border-2 border-slate-300" />}
                          </div>
                          <span className="font-bold text-slate-800 text-[17px] sm:text-[20px] capitalize leading-snug tracking-tight">{displayTitle}</span>
                       </div>
                       
                       {/* Calories Pill */}
                       {!isBelumAda && (
                         <div className="bg-[#FFF7ED] px-[10px] py-[5px] rounded-full flex items-center gap-1 shrink-0">
                            <Flame size={14} className="text-orange-500 mt-0.5" />
                            <span className="font-semibold text-orange-600 text-[13px] tracking-tight">{displayNutrition.energi_kal.toFixed(0)} <span className="text-[10px] font-extrabold uppercase opacity-90 ml-0.5">KAL</span></span>
                         </div>
                       )}
                    </div>

                    {/* Meta row */}
                    <div className="flex flex-wrap items-center gap-2 mb-3 pl-[36px]">
                       {displaySubtitle && (
                         <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-50 text-gray-500 text-[13px] font-medium border border-[#E5E7EB]">
                           <Tag size={13} className="text-gray-400" />
                           {displaySubtitle}
                         </span>
                       )}
                       
                       {!item.is_manual && typeof item.confidence === 'number' && (
                         <span className="inline-flex items-center gap-1.5 text-slate-500 text-[13px] font-medium">
                           <TrendingUp size={13} className="text-[#10b981]" />
                           {(item.confidence * 100).toFixed(0)}%
                         </span>
                       )}
                       
                       {item.corrected && (
                         <span className="text-emerald-500 text-[11px] font-bold uppercase tracking-wider before:content-['â€¢'] before:mr-1 before:text-emerald-300">
                           Dikoreksi
                         </span>
                       )}
                       
                       {/* Accuracy flag (Cocok/Mendekati) */}
                       {!isBelumAda && badge.label && (
                         <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-widest border ${
                           badge.label.toUpperCase() === 'COCOK' || badge.className?.includes('green')
                             ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                             : 'bg-amber-50 text-amber-600 border-amber-200'
                         }`}>
                           {badge.label}
                         </span>
                       )}
                    </div>
                    
                    {/* Inline disclaimer / Note */}
                    {!isBelumAda && badge.note && (
                       <div className="ml-[36px] mb-5 bg-slate-50 border border-slate-200/60 rounded-[10px] p-2.5 flex items-start gap-2 shadow-sm">
                         <Info size={15} className="shrink-0 mt-[1px] text-slate-500" />
                         <span className="text-[12px] font-semibold text-slate-600 leading-snug">Angka gizi belum termasuk minyak, saus, dan bumbu pelengkap.</span>
                       </div>
                    )}
                    
                    {!isBelumAda && (
                      <div className="pl-[36px]">
                        {/* Serving Selector */}
                        <div className="mb-5">
                           <div className="flex items-center gap-1.5 mb-2.5">
                              <Utensils size={13} className="text-gray-400" />
                              <span className="text-[11px] uppercase tracking-wider font-bold text-gray-400">PORSI</span>
                           </div>
                           <div className="flex flex-col gap-2.5">
                             <div className="flex flex-wrap gap-2">
                               {[0.5, 1, 1.5, 2].map(p => (
                                 <button 
                                   key={p}
                                   onClick={() => handlePortionChange(index, p)} 
                                   disabled={isBusyAction}
                                   className={`h-[34px] px-3 rounded-full text-[12px] font-semibold transition-all border outline-none focus:ring-2 focus:ring-emerald-200 ${item.portion === p ? 'bg-[#10b981] text-white border-[#10b981] shadow-sm shadow-emerald-200/50' : 'bg-white text-gray-600 border-[#E5E7EB] hover:bg-gray-50'}`}
                                 >
                                   {p === 0.5 ? '1/2 Porsi' : p === 1 ? '1 Porsi' : p === 1.5 ? '1 1/2 Porsi' : '2 Porsi'}
                                 </button>
                               ))}
                             </div>
                             
                             <div className="flex items-center gap-2">
                               <span className="text-[13px] font-medium text-gray-400">atau</span>
                               <input 
                                 type="number" min="0.1" step="0.1" 
                                 value={item.portion || 1} 
                                 onChange={e => handlePortionChange(index, e.target.value)} 
                                 disabled={isBusyAction}
                                 className="w-[56px] h-[36px] border border-[#E5E7EB] rounded-lg text-[14px] font-bold text-center text-slate-800 focus:border-[#10b981] focus:ring-1 focus:ring-[#10b981] outline-none transition-colors" 
                               />
                               <span className="text-[13px] font-medium text-gray-500">porsi</span>
                             </div>
                           </div>
                        </div>
                        
                        {/* Nutrition Grid */}
                        <div className="grid grid-cols-3 gap-2 mb-3">
                           {/* Protein */}
                           <div className="bg-[#EFF6FF] rounded-[12px] p-2 sm:p-4 flex flex-col items-center text-center">
                              <div className="mb-0.5">
                                <span className="font-bold text-[22px] text-slate-800 tracking-tight">{displayNutrition.protein_g.toFixed(1)}</span>
                                <span className="text-[12px] font-semibold text-slate-500 ml-1 uppercase">g</span>
                              </div>
                              <div className="text-[13px] font-medium text-slate-500">Protein</div>
                           </div>
                           {/* Lemak */}
                           <div className="bg-[#FFFBEB] rounded-[12px] p-2 sm:p-4 flex flex-col items-center text-center">
                              <div className="mb-0.5">
                                <span className="font-bold text-[22px] text-slate-800 tracking-tight">{displayNutrition.lemak_g.toFixed(1)}</span>
                                <span className="text-[12px] font-semibold text-slate-500 ml-1 uppercase">g</span>
                              </div>
                              <div className="text-[13px] font-medium text-slate-500">Lemak</div>
                           </div>
                           {/* Karbo */}
                           <div className="bg-[#F0FDF4] rounded-[12px] p-2 sm:p-4 flex flex-col items-center text-center">
                              <div className="mb-0.5">
                                <span className="font-bold text-[22px] text-slate-800 tracking-tight">{displayNutrition.karbo_g.toFixed(1)}</span>
                                <span className="text-[12px] font-semibold text-slate-500 ml-1 uppercase">g</span>
                              </div>
                              <div className="text-[13px] font-medium text-slate-500">Karbo</div>
                           </div>
                        </div>
                      </div>
                    )}
                    
                    {isBelumAda && (
                      <div className="pl-[36px] mb-4 text-[13px] font-medium text-gray-400 italic">
                        Data gizi belum tersedia.
                      </div>
                    )}

                    {/* Edit panel (Matches Gambar 4.1 Form Koreksi) */}
                        {isEditing && (
                          <div id={`edit-panel-${index}`} className="bg-blue-50/50 rounded-2xl p-4 mb-4 border border-blue-100 shadow-inner">
                            <div className="flex justify-between items-center mb-4">
                              <div className="text-sm font-bold text-slate-800 flex items-center gap-2">
                                <Edit size={16} className="text-blue-500" /> Koreksi Makanan
                              </div>
                              <button onClick={handleCancelEdit} className="text-slate-400 hover:text-slate-600 bg-white rounded-full p-1 shadow-sm border border-slate-100">
                                <X size={14} strokeWidth={3} />
                              </button>
                            </div>
                            
                            <div className="relative mb-3">
                              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Search size={16} className="text-slate-400" />
                              </div>
                              <input 
                                type="text" placeholder="Ketik nama makanan yang benar..." 
                                value={editSearch.query} 
                                onChange={e => editSearch.handleSearch(e.target.value)}
                                onFocus={(e) => { setTimeout(() => e.target.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300); }}
                                className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-300 rounded-xl text-sm font-medium focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none transition-all shadow-sm" 
                                autoFocus
                              />
                              {editSearch.isSearching && <div className="absolute right-3 top-3"><Spinner size="sm" /></div>}
                              
                              {editSearch.results.length > 0 && (
                                <div className="absolute z-20 w-full bg-white border border-slate-200 rounded-xl shadow-xl max-h-48 overflow-y-auto mt-2 py-1">
                                  {editSearch.results.map(r => (
                                    <button 
                                      key={r.id} type="button" 
                                      onClick={() => editSearch.handleSelect(r)} 
                                      disabled={isBusyAction}
                                      className="w-full text-left px-4 py-2.5 hover:bg-blue-50 focus:bg-blue-50 border-b border-slate-50 last:border-0 transition-colors"
                                    >
                                      <div className="text-sm font-bold text-slate-700">{r.name}</div>
                                      <div className="text-xs text-slate-400">{r.nutrition?.energi_kal} kalori â€¢ {r.nutrition?.protein_g}g protein</div>
                                    </button>
                                  ))}
                                </div>
                              )}
                            </div>

                            {editSearch.selected && (
                              <div className="bg-emerald-50 border border-emerald-400 rounded-xl p-3 flex items-center gap-3 text-emerald-800 shadow-sm mb-4">
                                <CheckCircle2 size={20} className="text-emerald-500 shrink-0" />
                                <div>
                                  <div className="text-sm font-bold">{editSearch.selected.name}</div>
                                  <div className="text-xs font-medium opacity-80">{editSearch.selected.nutrition?.energi_kal} kalori</div>
                                </div>
                              </div>
                            )}

                            {editError && <div className="mb-4 text-red-600 text-xs font-semibold bg-red-50 p-2 rounded-lg border border-red-100">{editError}</div>}
                            
                            <div className="flex gap-3">
                              <button 
                                onClick={handleCancelEdit} 
                                disabled={isBusyAction} 
                                className="flex-1 py-2.5 rounded-xl bg-white border-2 border-slate-200 text-slate-600 font-bold text-sm hover:bg-slate-50 transition-colors"
                              >
                                Batal
                              </button>
                              <button 
                                onClick={handleConfirmEdit} 
                                disabled={!editSearch.selected || isSubmitting || isBusyAction} 
                                className="flex-[2] py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-sm shadow-sm transition-colors disabled:opacity-50"
                              >
                                {isSubmitting ? 'Menyimpan...' : 'Ganti'}
                              </button>
                            </div>
                          </div>
                        )}

                        {/* Action row (Edit / Hapus) */}
                        {!isEditing && (
                          <div className="flex justify-end gap-2 mt-4 pt-2 relative z-10 pl-[36px]">
                            <button 
                              onClick={() => handleEditCard(index)} 
                              disabled={isBusyAction}
                              className="flex items-center justify-center gap-1.5 px-[16px] py-[8px] rounded-[10px] bg-white border border-[#E5E7EB] text-gray-600 hover:text-slate-800 hover:bg-gray-50 font-semibold text-[13px] transition-colors"
                            >
                              <Edit size={14} /> Edit
                            </button>
                            <button 
                              onClick={() => handleDeleteCard(index)} 
                              disabled={isBusyAction}
                              className="flex items-center justify-center gap-1.5 px-[16px] py-[8px] rounded-[10px] bg-[#FEF2F2] hover:bg-red-100 text-red-500 font-semibold text-[13px] transition-colors"
                            >
                              <Trash2 size={14} /> {deletingIndex === index ? 'Menghapus...' : 'Hapus'}
                            </button>
                          </div>
                        )}
                  </div>
                );
              })}
            </div>

            {/* â”€â”€ Tambah Makanan Manual â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
            
            {/* â”€â”€ Tombol Ulangi Deteksi â”€â”€ */}
            {detectionItems.length > 0 && addingFoodIndex === null && (
              <div className="mt-6 flex flex-col sm:flex-row items-center gap-3">
                <button
                  onClick={() => { setDetectionItems([]); setAnalysisId(null); setPreviewUrl(null); setSelectedFile(null); setError(null); resetInlineStates(); uploadRef.current?.click(); }}
                  disabled={isBusyAction}
                  className="w-full sm:w-auto flex-1 flex items-center justify-center gap-2 bg-white border-2 border-[#10b981] text-[#10b981] hover:bg-emerald-50 active:scale-95 font-bold py-3.5 rounded-2xl text-sm transition-all shadow-sm"
                >
                  <Camera size={18} /> Foto Makanan Baru
                </button>
                <button
                  onClick={() => navigate(ROUTES.HOME)}
                  disabled={isBusyAction}
                  className="w-full sm:w-auto flex-1 flex items-center justify-center gap-2 bg-[#0f172a] hover:bg-slate-800 active:scale-95 text-white font-bold py-3.5 rounded-2xl text-sm transition-all shadow-sm"
                >
                  <Home size={18} /> Kembali ke Beranda
                </button>
              </div>
            )}

            {addingFoodIndex === null && detectionItems.length > 0 && (
              <div data-tour="add-food-area" className="bg-white border-2 border-slate-100 rounded-[20px] p-5 flex items-center justify-between shadow-sm mt-6">
                <div className="flex items-center gap-4">
                  <div className="bg-blue-50 rounded-xl p-3 shrink-0">
                    <Search size={20} className="text-blue-500" />
                  </div>
                  <div>
                    <h3 className="font-extrabold text-slate-800 text-sm">Ada Makanan yang Terlewat?</h3>
                    <p className="text-xs font-medium text-slate-500 mt-0.5">Tambah manual agar kalori akurat</p>
                  </div>
                </div>
                <button 
                  onClick={handleOpenAddFood} 
                  disabled={isBusyAction} 
                  className="bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2.5 rounded-xl text-sm font-bold shadow-sm transition-colors flex items-center gap-1 shrink-0"
                >
                  <Plus size={16} strokeWidth={3} /> Tambah
                </button>
              </div>
            )}

            {addingFoodIndex === 'standalone' && detectionItems.length > 0 && (
              <div id="add-food-panel" className="bg-white border-2 border-emerald-400 rounded-[20px] p-5 shadow-emerald-100/50 shadow-lg mt-6 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 to-teal-400" />
                <div className="flex justify-between items-center mb-4 mt-1">
                  <h3 className="font-extrabold text-slate-800 text-sm flex items-center gap-2">
                    <Search size={16} className="text-emerald-500" /> Cari Makanan di Database
                  </h3>
                  <button onClick={handleCancelAddFood} className="text-slate-400 hover:text-slate-600 p-1 bg-slate-50 rounded-full transition-colors">
                    <X size={16} strokeWidth={3} />
                  </button>
                </div>
                
                <div className="relative">
                  <input 
                    type="text" 
                    value={addSearch.query} 
                    onChange={e => addSearch.handleSearch(e.target.value)} 
                    onFocus={(e) => { setTimeout(() => e.target.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300); }}
                    placeholder="Contoh: Nasi Goreng Spesial..."
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 outline-none transition-all shadow-inner" 
                    autoFocus 
                  />
                  {addSearch.isSearching && <div className="absolute right-3 top-3.5"><Spinner size="sm" /></div>}
                  
                  {addSearch.results.length > 0 && (
                    <div className="absolute z-20 w-full bg-white border border-slate-200 rounded-xl shadow-xl max-h-56 overflow-y-auto mt-2 py-1">
                      {addSearch.results.map((r) => (
                        <button 
                          key={r.id} type="button" 
                          onClick={() => addSearch.handleSelect(r)} 
                          disabled={isBusyAction}
                          className="w-full text-left px-4 py-3 border-b border-slate-50 hover:bg-emerald-50 focus:bg-emerald-50 transition-colors"
                        >
                          <div className="text-sm font-bold text-slate-800">{r.name}</div>
                          <div className="text-xs font-semibold text-slate-400 mt-0.5">ID: {r.id}</div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {addSearch.selected && (
                  <div className="mt-4 bg-emerald-50 border border-emerald-400 rounded-xl p-3 flex items-center gap-3 text-emerald-800 shadow-sm">
                    <CheckCircle2 size={20} className="text-emerald-500 shrink-0" />
                    <div>
                      <div className="text-[10px] font-bold uppercase tracking-wide opacity-70 mb-0.5">Siap ditambahkan</div>
                      <div className="text-sm font-bold">{addSearch.selected.name}</div>
                    </div>
                  </div>
                )}
                
                {addError && <div className="mt-3 text-red-600 text-xs font-semibold bg-red-50 p-2 rounded-lg border border-red-100">{addError}</div>}
                
                <div className="flex gap-3 mt-5">
                  <button 
                    onClick={handleCancelAddFood} 
                    disabled={isBusyAction} 
                    className="flex-1 py-3 rounded-xl bg-white border-2 border-slate-200 text-slate-600 font-bold text-sm hover:bg-slate-50 transition-colors"
                  >
                    Batal
                  </button>
                  <button 
                    onClick={handleConfirmAddFood} 
                    disabled={!addSearch.selected || isAdding || isBusyAction}
                    className="flex-[2] py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-sm shadow-sm transition-colors disabled:opacity-50 flex justify-center items-center gap-2"
                  >
                    {isAdding ? <Spinner size="sm" /> : <Plus size={16} strokeWidth={3} />}
                    {isAdding ? 'Memproses...' : 'Tambahkan'}
                  </button>
                </div>

                {!showTrainingRequest && (
                  <div className="mt-5 pt-4 border-t border-slate-100 flex justify-between items-center text-xs font-semibold text-slate-500">
                    <span>Makanan tidak ditemukan?</span>
                    <button 
                      onClick={handleOpenTrainingRequest} 
                      disabled={isBusyAction} 
                      className="text-orange-500 hover:text-orange-600 font-bold"
                    >
                      Ajukan Kelas Baru
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* â”€â”€ Training Request â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
            {showTrainingRequest && (
              <div className="bg-orange-50 border-2 border-orange-200 rounded-[20px] p-5 shadow-sm mt-4">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-extrabold text-orange-800 text-sm flex items-center gap-2">
                    <Database size={16} /> Ajukan Kelas Makanan Baru
                  </h3>
                  <button onClick={handleCancelTrainingRequest} className="text-orange-400 hover:text-orange-600 p-1 transition-colors">
                    <X size={16} strokeWidth={3} />
                  </button>
                </div>
                
                <p className="text-xs font-medium text-orange-700 mb-4 bg-orange-100/50 p-3 rounded-xl">
                  Bantu kami menambah database! Makanan yang diusulkan akan dilatih agar dikenali otomatis di masa depan.
                </p>
                
                <input 
                  type="text" 
                  value={requestedLabelInput} 
                  onChange={e => setRequestedLabelInput(e.target.value)} 
                  onFocus={(e) => { setTimeout(() => e.target.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300); }}
                  placeholder="Nama makanan (contoh: Gudeg, Papeda)..."
                  className="w-full px-4 py-2.5 bg-white border border-orange-200 rounded-xl text-sm font-medium focus:border-orange-500 focus:ring-2 focus:ring-orange-100 outline-none transition-all mb-3" 
                />
                
                <textarea 
                  value={requestNote} 
                  onChange={e => setRequestNote(e.target.value)} 
                  placeholder="Deskripsi singkat atau komposisi (opsional)..."
                  className="w-full px-4 py-2.5 bg-white border border-orange-200 rounded-xl text-sm font-medium focus:border-orange-500 focus:ring-2 focus:ring-orange-100 outline-none transition-all min-h-[80px] resize-y" 
                />
                
                {requestMsg && (
                  <div className={`mt-3 p-3 rounded-xl text-xs font-bold ${requestMsg.includes('berhasil') ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                    {requestMsg}
                  </div>
                )}
                
                <div className="flex gap-3 mt-4">
                  <button 
                    onClick={() => handleSubmitClassRequest(requestedLabelInput, requestNote)} 
                    disabled={isRequesting || isBusyAction}
                    className="flex-1 py-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-sm shadow-sm transition-colors disabled:opacity-50 flex justify-center items-center gap-2"
                  >
                    {isRequesting ? <Spinner size="sm" /> : null}
                    {isRequesting ? 'Mengirim...' : 'Kirim Pengajuan'}
                  </button>
                </div>
              </div>
            )}
            
            </div>
            {/* === AKHIR KOLOM KANAN === */}
            
          </div>
        )}

        {/* Hidden file inputs */}
        <input ref={uploadRef} type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
        <input ref={cameraRef} type="file" accept="image/*" capture="environment" onChange={handleImageUpload} className="hidden" />
      </div>
    </div>
  );
}
