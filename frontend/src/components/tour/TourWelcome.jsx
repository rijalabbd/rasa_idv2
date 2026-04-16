// frontend/src/components/tour/TourWelcome.jsx
// ─── Welcome & Completion overlay ───────────────────────────────────────────
// Handles fullscreen steps: Step 0 (Welcome) and Step 7 (Selesai).
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Rocket, ChevronRight } from 'lucide-react';
import { useTour } from '../../hooks/useTour';
import { ROUTES } from '../../constants/routes';
import TOUR_STEPS from './tourSteps';
import './TourWelcome.css';

export default function TourWelcome() {
  const navigate = useNavigate();
  const {
    isTourActive, currentStep, isReplay,
    nextStep, skipTour, completeTour, goToStep,
  } = useTour();

  const [overlayState, setOverlayState] = useState('entering');

  const step = TOUR_STEPS[currentStep];
  const isFullscreenStep = step?.type === 'fullscreen';
  const isWelcomeStep = currentStep === 0;
  const isCompleteStep = currentStep === TOUR_STEPS.length - 1;

  // Reset overlay state when step changes
  useEffect(() => {
    if (isTourActive && isFullscreenStep) {
      setOverlayState('entering');
    }
  }, [isTourActive, isFullscreenStep, currentStep]);

  if (!isTourActive || !isFullscreenStep) return null;

  const handleClose = () => {
    setOverlayState('exiting');
    setTimeout(() => {
      if (isCompleteStep) {
        completeTour();
      } else {
        skipTour();
      }
    }, 300);
  };

  const handleStartTour = () => {
    // Navigate to analyze page and advance to step 1
    nextStep();
    navigate(ROUTES.ANALYZE + '?tour=1');
  };

  const handleSkipToResults = () => {
    // Jump to step 3 (results) — only available on replay
    goToStep(3);
    navigate(ROUTES.ANALYZE + '?tour=1');
  };

  const handleComplete = () => {
    setOverlayState('exiting');
    setTimeout(() => completeTour(), 300);
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) handleClose();
  };

  return (
    <div
      className={`tour-welcome-overlay ${overlayState}`}
      onClick={handleBackdropClick}
    >
      <div className="tour-welcome-card" onClick={(e) => e.stopPropagation()}>
        {/* Close button */}
        <button
          className="tour-welcome-close"
          onClick={handleClose}
          aria-label="Tutup"
        >
          <X size={18} strokeWidth={2.5} />
        </button>

        {/* Icon */}
        <div
          className="tour-welcome-icon"
          style={{ background: step.iconBg }}
        >
          <span role="img" aria-hidden="true">
            {step.icon}
          </span>
        </div>

        {/* Title */}
        <h2 className="tour-welcome-title">{step.title}</h2>

        {/* Description */}
        <p className="tour-welcome-desc">{step.description}</p>

        {/* Tip */}
        {step.tip && <div className="tour-welcome-tip">{step.tip}</div>}

        {/* Actions */}
        <div className="tour-welcome-actions">
          {isWelcomeStep && (
            <>
              <button className="tour-welcome-btn-primary" onClick={handleStartTour}>
                Mulai Tour <ChevronRight size={18} />
              </button>

              {isReplay && (
                <button className="tour-welcome-btn-secondary" onClick={handleSkipToResults}>
                  Lewati ke Hasil →
                </button>
              )}

              <button className="tour-welcome-btn-skip" onClick={handleClose}>
                Lewati panduan
              </button>
            </>
          )}

          {isCompleteStep && (
            <button className="tour-welcome-btn-primary" onClick={handleComplete}>
              Mulai Sendiri! <Rocket size={18} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
