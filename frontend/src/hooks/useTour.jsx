// frontend/src/hooks/useTour.js
// ─── Tour State Management ──────────────────────────────────────────────────
// Custom hook + React Context untuk state tour lintas halaman.
// State tour dipisah dari komponen UI agar mudah di-maintain dan di-test.
// ─────────────────────────────────────────────────────────────────────────────

import { createContext, useContext, useState, useCallback, useMemo } from 'react';

const STORAGE_KEY = 'rasa_tour_done';
const TOTAL_STEPS = 8; // 0..7

// ─── Context ────────────────────────────────────────────────────────────────
const TourContext = createContext(null);

/**
 * TourProvider — wrap di App.jsx agar semua page bisa akses tour state.
 */
export function TourProvider({ children }) {
  const [isTourActive, setIsTourActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [isReplay, setIsReplay] = useState(false);

  /**
   * Mulai tour.
   * @param {boolean} replay - Jika true, tandai sebagai replay (tampilkan "Lewati ke Hasil")
   */
  const startTour = useCallback((replay = false) => {
    setIsReplay(replay);
    setCurrentStep(0);
    setIsTourActive(true);
  }, []);

  /**
   * Lanjut ke step berikutnya.
   * Jika sudah di step terakhir, panggil completeTour().
   */
  const nextStep = useCallback(() => {
    setCurrentStep((prev) => {
      const next = prev + 1;
      if (next >= TOTAL_STEPS) {
        // Akan di-handle oleh completeTour, tapi safety guard
        return prev;
      }
      return next;
    });
  }, []);

  /**
   * Kembali ke step sebelumnya (min 0).
   */
  const prevStep = useCallback(() => {
    setCurrentStep((prev) => Math.max(0, prev - 1));
  }, []);

  /**
   * Loncat ke step tertentu.
   */
  const goToStep = useCallback((step) => {
    if (step >= 0 && step < TOTAL_STEPS) {
      setCurrentStep(step);
    }
  }, []);

  /**
   * Skip tour — tutup tanpa menandai selesai di localStorage.
   */
  const skipTour = useCallback(() => {
    setIsTourActive(false);
    setCurrentStep(0);
    // Tetap set localStorage agar tidak muncul auto lagi
    localStorage.setItem(STORAGE_KEY, 'true');
  }, []);

  /**
   * Tour selesai — simpan ke localStorage dan reset state.
   */
  const completeTour = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, 'true');
    setIsTourActive(false);
    setCurrentStep(0);
  }, []);

  /**
   * Cek apakah tour harus auto-show (first-time visitor).
   */
  const shouldAutoStart = useCallback(() => {
    return localStorage.getItem(STORAGE_KEY) !== 'true';
  }, []);

  const value = useMemo(
    () => ({
      // State
      isTourActive,
      currentStep,
      isReplay,
      totalSteps: TOTAL_STEPS,

      // Actions
      startTour,
      nextStep,
      prevStep,
      goToStep,
      skipTour,
      completeTour,
      shouldAutoStart,
    }),
    [isTourActive, currentStep, isReplay, startTour, nextStep, prevStep, goToStep, skipTour, completeTour, shouldAutoStart]
  );

  return <TourContext.Provider value={value}>{children}</TourContext.Provider>;
}

/**
 * Hook untuk mengakses tour state dari komponen manapun.
 * @returns {Object} Tour state dan actions
 */
export function useTour() {
  const context = useContext(TourContext);
  if (!context) {
    throw new Error('useTour() must be used within a <TourProvider>');
  }
  return context;
}
