// frontend/src/pages/AnalyzePhoto.jsx
import { useState, useRef, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Camera, Image as ImageIcon, Search, Edit, Trash2, Home, X, Plus, 
  CheckCircle2, BarChart2, Check, Flame, Utensils, Database, ChevronDown, ChevronUp, AlertCircle, AlertTriangle, Sun, Focus, Crop, Layers, Target, Tag, TrendingUp, Info, Send,
  ShieldCheck, ShieldAlert, Zap, Wheat, Droplets, Leaf
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
    blue: "bg-gradient-to-br from-blue-50/80 to-blue-100/50 text-blue-700 border border-blue-100 shadow-[0_2px_10px_-4px_rgba(59,130,246,0.1)]",
    yellow: "bg-gradient-to-br from-amber-50/80 to-amber-100/50 text-amber-700 border border-amber-100 shadow-[0_2px_10px_-4px_rgba(245,158,11,0.1)]",
    green: "bg-gradient-to-br from-emerald-50/80 to-emerald-100/50 text-emerald-700 border border-emerald-100 shadow-[0_2px_10px_-4px_rgba(16,185,129,0.1)]",
    purple: "bg-gradient-to-br from-purple-50/80 to-purple-100/50 text-purple-700 border border-purple-100 shadow-[0_2px_10px_-4px_rgba(168,85,247,0.1)]",
  };
  const iconColors = { blue: "#3b82f6", yellow: "#eab308", green: "#10b981", purple: "#a855f7" };
  
  return (
    <div className={`${variants[colorVariant]} rounded-[14px] py-3.5 px-2 text-center flex-1 flex flex-col items-center justify-center transition-transform hover:-translate-y-0.5 duration-300`}>
      {Icon && <Icon size={16} color={iconColors[colorVariant]} className="mb-1.5 opacity-70" />}
      <div className="text-lg leading-none font-black text-slate-800 mb-1">
        {value}<span className="text-xs font-bold text-slate-500 ml-0.5">{unit}</span>
      </div>
      <div className="text-[11px] font-bold uppercase tracking-wider opacity-80">{label}</div>
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
  
  // -- Untuk animasi load progress bar bar --
  const [isMounted, setIsMounted] = useState(false);
  useEffect(() => { setIsMounted(true); }, []);

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
    // Use YOLO detection label (with underscores replaced by spaces) for display name
    const withCal = selected.map(it => {
      const yoloName = (it.label && it.label !== 'manual') 
        ? it.label.replace(/_/g, ' ') 
        : it.currentName;
      return { name: yoloName, kal: Math.round((it.baseNutrition.energi_kal || 0) * (it.portion || 1)) };
    });
    return withCal.sort((a, b) => b.kal - a.kal);
  }, [detectionItems]);

  // Nutrition assessment against Indonesian AKG (Angka Kecukupan Gizi)
  // Reference: AKG 2019 for adults (average male/female 19-29 tahun)
  const nutritionAssessment = useMemo(() => {
    if (!totalNutrition) return null;
    
    // AKG daily reference values (per meal ~ 33% of daily)
    const perMealRef = {
      energi_kal: 700,  // ~2100 daily / 3
      protein_g: 20,    // ~60g daily / 3
      lemak_g: 23,      // ~70g daily / 3
      karbo_g: 108,     // ~325g daily / 3
      serat_g: 8,       // ~25g daily / 3
    };
    
    const getLevel = (val, ref) => {
      const pct = (val / ref) * 100;
      if (pct < 50) return { status: 'kurang', color: 'amber', pct: Math.round(pct) };
      if (pct <= 120) return { status: 'cukup', color: 'emerald', pct: Math.round(pct) };
      return { status: 'berlebih', color: 'red', pct: Math.round(pct) };
    };
    
    const energi = getLevel(totalNutrition.energi_kal, perMealRef.energi_kal);
    const protein = getLevel(totalNutrition.protein_g, perMealRef.protein_g);
    const lemak = getLevel(totalNutrition.lemak_g, perMealRef.lemak_g);
    const karbo = getLevel(totalNutrition.karbo_g, perMealRef.karbo_g);
    const serat = getLevel(totalNutrition.serat_g || 0, perMealRef.serat_g);
    
    // Overall score: count how many are "cukup"
    const nutrients = [energi, protein, lemak, karbo];
    const cukupCount = nutrients.filter(n => n.status === 'cukup').length;
    const berlebihCount = nutrients.filter(n => n.status === 'berlebih').length;
    
    let overallStatus, overallMessage, overallColor, overallIcon;
    if (cukupCount >= 3 && berlebihCount === 0) {
      overallStatus = 'Seimbang';
      overallMessage = 'Komposisi gizi makanan Anda sudah baik dan seimbang untuk satu kali makan.';
      overallColor = 'emerald';
      overallIcon = 'shield-check';
    } else if (berlebihCount >= 2) {
      overallStatus = 'Berlebih';
      overallMessage = 'Beberapa nutrisi melebihi kebutuhan per porsi makan. Pertimbangkan untuk mengurangi porsi.';
      overallColor = 'red';
      overallIcon = 'shield-alert';
    } else {
      overallStatus = 'Perlu Perhatian';
      overallMessage = 'Sebagian nutrisi belum mencukupi kebutuhan per porsi makan. Tambahkan variasi makanan.';
      overallColor = 'amber';
      overallIcon = 'shield-alert';
    }
    
    return {
      energi, protein, lemak, karbo, serat,
      overallStatus, overallMessage, overallColor, overallIcon,
      perMealRef
    };
  }, [totalNutrition]);

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
              max-height: none !important;
              overflow: visible !important;
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

          /* Hidden scrollbar for left sticky col */
          .left-col-scroll::-webkit-scrollbar { display: none; }
          .left-col-scroll { -ms-overflow-style: none; scrollbar-width: none; }
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
            <div className="left-col left-col-scroll w-full lg:w-[400px] xl:w-[450px] shrink-0 lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] lg:overflow-y-auto space-y-6 animate-slide-up-fade opacity-0" style={{ animationDelay: '0ms' }}>

            {/* Detection Summary Card — Balanced White Card */}
            <div data-tour="summary-card" className={`bg-white rounded-[24px] p-5 sm:p-6 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)] border border-slate-100 transition-all duration-500 ${detectionItems.length === 0 ? 'bg-[#FFFBEB] border-amber-200' : ''}`}>
              
              {/* Card Header */}
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                  <div className={`rounded-xl p-2.5 shadow-sm ${detectionItems.length === 0 ? 'bg-amber-500 shadow-amber-200' : 'bg-emerald-500 shadow-emerald-200'}`}>
                    <Camera size={22} className="text-white" />
                  </div>
                  <div>
                    <div className="font-extrabold text-slate-800 text-base sm:text-lg leading-tight">
                      {detectionItems.length > 0 ? 'Hasil Deteksi' : 'Tidak Terdeteksi'}
                    </div>
                    <div className="text-xs font-medium text-slate-400">
                      {detectionItems.length > 0 ? `${detectionItems.length} makanan ditemukan` : 'Coba foto ulang atau tambah manual'}
                    </div>
                  </div>
                </div>
                {detectionItems.length === 0 && (
                  <div className="bg-amber-100 text-amber-700 text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider animate-pulse">
                    Perhatian
                  </div>
                )}
              </div>

              {/* Image with Bounding Boxes */}
              {previewUrl && (
                <div className="group relative rounded-2xl overflow-hidden bg-slate-900 mb-5">
                  <div className="relative w-full flex justify-center transition-transform duration-700 ease-out group-hover:scale-[1.02]">
                    {detectionItems.length > 0 ? (
                      <BoundingBoxOverlay imageUrl={previewUrl} detections={detectionItems} />
                    ) : (
                      <img src={previewUrl} alt="Uploaded preview" className="block max-h-[22rem] w-auto max-w-full object-contain" />
                    )}
                  </div>
                  {/* Floating bottom gradient */}
                  <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-black/60 to-transparent pointer-events-none" />
                  {/* Bottom floating badges */}
                  <div className="absolute bottom-3 left-3 right-3 flex justify-between items-end z-10 pointer-events-none">
                    {detectionItems.length > 0 && avgConf !== null && (
                      <div className="bg-white/20 backdrop-blur-md text-white text-xs font-bold px-2.5 py-1.5 rounded-lg border border-white/20 flex items-center gap-1.5 animate-in slide-in-from-bottom-2 duration-500 fade-in">
                        <Target size={12} /> {avgConf}% akurasi
                      </div>
                    )}
                    <div className="bg-black/40 backdrop-blur-md text-white/70 text-[9px] font-bold px-2 py-1 rounded-md border border-white/10 uppercase tracking-widest">
                      {detectionItems.length > 0 ? `${detectionItems.length} objek` : 'Foto Asli'}
                    </div>
                  </div>
                </div>
              )}

              {/* Stat Tiles Row */}
              {detectionItems.length > 0 && (
                <div className="flex gap-3 mb-5">
                  <div className="flex-1 bg-gradient-to-br from-emerald-50/80 to-emerald-100/50 border border-emerald-100 rounded-2xl py-3 px-2 text-center shadow-sm">
                    <div className="text-xl font-black text-slate-800 leading-none mb-1">{detectionItems.length}</div>
                    <div className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">Objek</div>
                  </div>
                  <div className="flex-1 bg-gradient-to-br from-blue-50/80 to-blue-100/50 border border-blue-100 rounded-2xl py-3 px-2 text-center shadow-sm">
                    <div className="text-xl font-black text-slate-800 leading-none mb-1">{avgConf ?? '-'}<span className="text-xs font-bold text-slate-400">%</span></div>
                    <div className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">Akurasi AI</div>
                  </div>
                  {totalNutrition && (
                    <div className="flex-1 bg-gradient-to-br from-orange-50/80 to-orange-100/50 border border-orange-100 rounded-2xl py-3 px-2 text-center shadow-sm">
                      <div className="text-xl font-black text-slate-800 leading-none mb-1">{totalNutrition.energi_kal.toFixed(0)}</div>
                      <div className="text-[10px] font-bold text-orange-600 uppercase tracking-wider">Total kal</div>
                    </div>
                  )}
                </div>
              )}

              {/* Action Button */}
              <div className="flex gap-2.5">
                <button 
                  onClick={() => { setDetectionItems([]); setAnalysisId(null); setPreviewUrl(null); setSelectedFile(null); setError(null); resetInlineStates(); }}
                  disabled={isBusyAction} 
                  className={`w-full font-bold py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-all text-sm active:scale-95 border-2 ${detectionItems.length === 0 ? 'bg-amber-500 hover:bg-amber-600 text-white border-amber-500 shadow-sm shadow-amber-200' : 'bg-white hover:bg-slate-50 hover:border-slate-300 text-slate-700 border-slate-200'}`}
                >
                  <Camera size={18} /> Ambil Foto Baru
                </button>
              </div>

              {/* Timestamp */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Terdeteksi pada: {new Date().toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })}
              </div>
            </div>


            </div>
            {/* === AKHIR KOLOM KIRI === */}

            {/* === KOLOM KANAN: Ranking & Detail Makanan === */}
            <div className="flex-1 w-full min-w-0 space-y-6">

            {/* Calorie Ranking Card (Matches Gambar 3.8) */}
            {totalNutrition && calorieRanked.length > 0 && (
              <div data-tour="ranking-card" className="bg-white rounded-[24px] p-6 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)] border border-slate-100 animate-slide-up-fade opacity-0">
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
                      <div key={i} className="group flex items-center gap-4 p-2.5 -mx-2.5 hover:bg-slate-50/80 rounded-2xl transition-all duration-300 cursor-default">
                        <div className={`w-8 h-8 shrink-0 rounded-full ${rankBgColor} text-white text-xs font-extrabold flex items-center justify-center shadow-md ring-4 ring-white group-hover:scale-110 transition-transform duration-300`}>
                          {i + 1}
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between items-end mb-2">
                            <span className="text-sm font-bold text-slate-700 group-hover:text-slate-900 transition-colors">{item.name}</span>
                            <span className="text-xs font-semibold flex items-center gap-1.5">
                              <span className="text-orange-600 bg-orange-50 px-2 py-0.5 rounded-md border border-orange-100">{item.kal} <span className="text-[10px] font-medium text-orange-400">kal</span></span>
                              <span className="text-slate-400 font-bold bg-slate-100 px-1.5 py-0.5 rounded-md">{pct}%</span>
                            </span>
                          </div>
                          <div className="bg-slate-100/80 rounded-full h-2.5 overflow-hidden ring-1 ring-inset ring-slate-200/50">
                            <div className={`h-full rounded-full ${rankBgColor} transition-all duration-1000 ease-out relative overflow-hidden`} style={{ width: isMounted ? `${pct}%` : '0%' }}>
                              <div className="absolute inset-0 bg-white/20 w-full animate-[shimmer_2s_infinite]" style={{backgroundImage: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)', transform: 'skewX(-20deg)'}} />
                            </div>
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

                {/* === Nutrition Assessment Panel === */}
                {nutritionAssessment && (
                  <div className="mt-6 pt-5 border-t border-slate-100">
                    {/* Overall Status Header */}
                    <div className={`flex items-center gap-3 p-4 rounded-2xl mb-4 border ${
                      nutritionAssessment.overallColor === 'emerald' 
                        ? 'bg-emerald-50/80 border-emerald-200' 
                        : nutritionAssessment.overallColor === 'red'
                        ? 'bg-red-50/80 border-red-200'
                        : 'bg-amber-50/80 border-amber-200'
                    }`}>
                      <div className={`shrink-0 p-2 rounded-xl ${
                        nutritionAssessment.overallColor === 'emerald' ? 'bg-emerald-100' 
                        : nutritionAssessment.overallColor === 'red' ? 'bg-red-100'
                        : 'bg-amber-100'
                      }`}>
                        {nutritionAssessment.overallIcon === 'shield-check' 
                          ? <ShieldCheck size={22} className="text-emerald-600" />
                          : <ShieldAlert size={22} className={nutritionAssessment.overallColor === 'red' ? 'text-red-600' : 'text-amber-600'} />
                        }
                      </div>
                      <div className="min-w-0">
                        <div className={`font-extrabold text-sm ${
                          nutritionAssessment.overallColor === 'emerald' ? 'text-emerald-800'
                          : nutritionAssessment.overallColor === 'red' ? 'text-red-800'
                          : 'text-amber-800'
                        }`}>
                          Gizi {nutritionAssessment.overallStatus}
                        </div>
                        <div className={`text-xs font-medium leading-snug mt-0.5 ${
                          nutritionAssessment.overallColor === 'emerald' ? 'text-emerald-700/80'
                          : nutritionAssessment.overallColor === 'red' ? 'text-red-700/80'
                          : 'text-amber-700/80'
                        }`}>
                          {nutritionAssessment.overallMessage}
                        </div>
                      </div>
                    </div>

                    {/* Nutrient Detail Bars */}
                    <div className="space-y-3">
                      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Info size={12} className="text-slate-400" />
                        Pemenuhan Gizi Per Porsi Makan (AKG)
                      </div>
                      {[
                        { key: 'energi', label: 'Kalori', icon: Zap, data: nutritionAssessment.energi, value: `${totalNutrition.energi_kal.toFixed(0)} kal`, ref: `${nutritionAssessment.perMealRef.energi_kal} kal` },
                        { key: 'protein', label: 'Protein', icon: Droplets, data: nutritionAssessment.protein, value: `${totalNutrition.protein_g.toFixed(1)}g`, ref: `${nutritionAssessment.perMealRef.protein_g}g` },
                        { key: 'lemak', label: 'Lemak', icon: Flame, data: nutritionAssessment.lemak, value: `${totalNutrition.lemak_g.toFixed(1)}g`, ref: `${nutritionAssessment.perMealRef.lemak_g}g` },
                        { key: 'karbo', label: 'Karbohidrat', icon: Wheat, data: nutritionAssessment.karbo, value: `${totalNutrition.karbo_g.toFixed(1)}g`, ref: `${nutritionAssessment.perMealRef.karbo_g}g` },
                        { key: 'serat', label: 'Serat', icon: Leaf, data: nutritionAssessment.serat, value: `${(totalNutrition.serat_g || 0).toFixed(1)}g`, ref: `${nutritionAssessment.perMealRef.serat_g}g` },
                      ].map(nutrient => {
                        const statusColors = {
                          kurang: { bg: 'bg-amber-500', text: 'text-amber-700', bgLight: 'bg-amber-50', border: 'border-amber-200' },
                          cukup: { bg: 'bg-emerald-500', text: 'text-emerald-700', bgLight: 'bg-emerald-50', border: 'border-emerald-200' },
                          berlebih: { bg: 'bg-red-500', text: 'text-red-700', bgLight: 'bg-red-50', border: 'border-red-200' },
                        };
                        const colors = statusColors[nutrient.data.status];
                        const barWidth = Math.min(nutrient.data.pct, 150); // Cap visual at 150%
                        
                        return (
                          <div key={nutrient.key} className="group">
                            <div className="flex items-center justify-between mb-1.5">
                              <div className="flex items-center gap-2">
                                <nutrient.icon size={14} className={colors.text} />
                                <span className="text-xs font-bold text-slate-700">{nutrient.label}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-[11px] font-semibold text-slate-500">{nutrient.value} / {nutrient.ref}</span>
                                <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-md border ${colors.bgLight} ${colors.text} ${colors.border}`}>
                                  {nutrient.data.pct}%
                                </span>
                              </div>
                            </div>
                            <div className="bg-slate-100/80 rounded-full h-2 overflow-hidden ring-1 ring-inset ring-slate-200/50">
                              <div 
                                className={`h-full rounded-full ${colors.bg} transition-all duration-1000 ease-out`} 
                                style={{ width: isMounted ? `${(barWidth / 150) * 100}%` : '0%' }} 
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Reference note */}
                    <div className="mt-4 bg-slate-50 border border-slate-200/60 rounded-xl p-3 flex items-start gap-2">
                      <Info size={14} className="shrink-0 mt-0.5 text-slate-400" />
                      <span className="text-[11px] font-medium text-slate-500 leading-snug">
                        Berdasarkan AKG 2019 untuk dewasa (19-29 tahun). Kebutuhan per porsi makan dihitung ~33% dari kebutuhan harian. Angka dapat berbeda tergantung usia, jenis kelamin, dan aktivitas fisik.
                      </span>
                    </div>
                  </div>
                )}

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
                    
                    <div className="flex justify-between items-start mb-5 mt-1">
                      <div>
                        <h3 className="font-extrabold text-slate-800 text-base flex items-center gap-2 mb-1.5">
                          <Search size={18} className="text-emerald-500" /> Tambah Makanan Manual
                        </h3>
                        <p className="text-xs text-slate-500 font-medium leading-relaxed pr-4">
                          Gunakan pencarian ini untuk menambahkan informasi gizi makanan jika tidak terdeteksi otomatis oleh AI di dalam foto Anda.
                        </p>
                      </div>
                      <button onClick={handleCloseSmartSearch} className="mt-0.5 shrink-0 text-slate-400 hover:text-slate-600 p-2 bg-slate-50 hover:bg-slate-100 rounded-full transition-colors shadow-sm border border-slate-100">
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
                  <div key={index} data-tour={index === 0 ? 'food-card' : undefined} className={`bg-white rounded-[20px] p-4 sm:p-6 shadow-sm border transition-all duration-200 w-full ${isSelected ? 'border-emerald-200 ring-1 ring-emerald-50' : 'border-[#E5E7EB]'} ${isBelumAda ? 'opacity-80' : ''} animate-slide-up-fade opacity-0`} style={{ animationDelay: `${300 + (index * 100)}ms` }}>
                    
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
                          <div id={`edit-panel-${index}`} data-tour={index === 0 ? 'correction-form' : undefined} className="bg-blue-50/50 rounded-2xl p-4 mb-4 border border-blue-100 shadow-inner">
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
                          <div data-tour={index === 0 ? 'edit-button' : undefined} className="flex justify-end gap-2 mt-4 pt-2 relative z-10 pl-[36px]">
                            <button 
                              data-tour={index === 0 ? 'edit-btn' : undefined}
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
                  data-tour="add-food-btn"
                  onClick={handleOpenAddFood} 
                  disabled={isBusyAction} 
                  className="bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2.5 rounded-xl text-sm font-bold shadow-sm transition-colors flex items-center gap-1 shrink-0"
                >
                  <Plus size={16} strokeWidth={3} /> Tambah
                </button>
              </div>
            )}

            {addingFoodIndex === 'standalone' && detectionItems.length > 0 && (
              <div id="add-food-panel" data-tour="add-food-form" className="bg-white border-2 border-emerald-400 rounded-[20px] p-5 shadow-emerald-100/50 shadow-lg mt-6 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 to-teal-400" />
                <div className="flex justify-between items-start mb-5 mt-1">
                  <div>
                    <h3 className="font-extrabold text-slate-800 text-base flex items-center gap-2 mb-1.5">
                      <Search size={18} className="text-emerald-500" /> Tambah Makanan Manual
                    </h3>
                    <p className="text-xs text-slate-500 font-medium leading-relaxed pr-4">
                      Gunakan pencarian ini untuk menambahkan informasi gizi makanan jika tidak terdeteksi otomatis oleh AI di dalam foto Anda.
                    </p>
                  </div>
                  <button onClick={handleCancelAddFood} className="mt-0.5 shrink-0 text-slate-400 hover:text-slate-600 p-2 bg-slate-50 hover:bg-slate-100 rounded-full transition-colors shadow-sm border border-slate-100">
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
                  <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-slate-500">
                      Bukan yang Anda cari?
                    </span>
                    <button 
                      data-tour="request-link"
                      onClick={handleOpenTrainingRequest} 
                      disabled={isBusyAction} 
                      className="text-[11px] font-bold text-orange-500 hover:text-orange-600 flex items-center gap-1 transition-colors"
                    >
                      Laporkan sebagai makanan baru
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* â”€â”€ Training Request â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
            {showTrainingRequest && (
              <div data-tour="request-class" className="bg-orange-50 border-2 border-orange-200 rounded-[20px] p-5 shadow-sm mt-4">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-extrabold text-orange-800 text-sm flex items-center gap-2">
                    <Database size={16} /> Laporkan Makanan Baru
                  </h3>
                  <button onClick={handleCancelTrainingRequest} className="text-orange-400 hover:text-orange-600 p-1 transition-colors">
                    <X size={16} strokeWidth={3} />
                  </button>
                </div>
                
                <p className="text-xs font-medium text-orange-700/80 mb-4 bg-white/50 p-3 rounded-xl border border-orange-100">
                  Makanan yang Anda cari belum ada di daftar kami? Masukkan nama dan deskripsi singkatnya di sini agar dapat kami tambahkan ke database gizi di masa mendatang.
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
