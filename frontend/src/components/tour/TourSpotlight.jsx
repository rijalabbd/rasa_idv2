// frontend/src/components/tour/TourSpotlight.jsx
// ─── Spotlight component ────────────────────────────────────────────────────
// Menyorot elemen DOM tertentu dengan overlay gelap + "lubang" transparan.
// Jika elemen target tidak ditemukan → graceful fallback (tooltip di tengah).
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect, useCallback, useRef } from 'react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import { useTour } from '../../hooks/useTour';
import TOUR_STEPS from './tourSteps';
import './TourSpotlight.css';

const PADDING = 12; // px padding around highlighted element
const TOOLTIP_GAP = 16; // px gap between element and tooltip

export default function TourSpotlight() {
  const {
    isTourActive, currentStep, totalSteps,
    nextStep, prevStep, skipTour,
  } = useTour();

  const [targetRect, setTargetRect] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ top: 0, left: 0 });
  const [animClass, setAnimClass] = useState('');
  const [overlayState, setOverlayState] = useState('entering');
  const observerRef = useRef(null);
  const animFrameRef = useRef(null);

  const step = TOUR_STEPS[currentStep];

  // Skip non-spotlight steps (fullscreen steps handled by TourWelcome)
  const isSpotlightStep = step?.type === 'spotlight';

  // ── Find target element ────────────────────────────────────────────────────
  const findTarget = useCallback(() => {
    if (!isSpotlightStep || !step?.target) return null;
    return document.querySelector(`[data-tour="${step.target}"]`);
  }, [isSpotlightStep, step?.target]);

  // ── Update rect + tooltip position ─────────────────────────────────────────
  const updatePosition = useCallback(() => {
    const el = findTarget();
    if (!el) {
      setTargetRect(null);
      return;
    }

    const rect = el.getBoundingClientRect();
    setTargetRect({
      top: rect.top - PADDING,
      left: rect.left - PADDING,
      width: rect.width + PADDING * 2,
      height: rect.height + PADDING * 2,
    });

    // Calculate tooltip position dynamically to prevent overlap
    const pos = step?.position || 'bottom';
    const vpW = window.innerWidth;
    const vpH = window.innerHeight;
    const tooltipH = tooltipRef.current ? tooltipRef.current.offsetHeight : 220;
    const tooltipW = tooltipRef.current ? tooltipRef.current.offsetWidth : 350;

    let top, left;

    // Center horizontally relative to target
    left = Math.max(16, Math.min(rect.left + (rect.width / 2) - (tooltipW / 2), vpW - tooltipW - 16));

    if (pos === 'bottom') {
      top = rect.bottom + TOOLTIP_GAP;
      // If tooltip would go off-screen bottom, flip to top
      if (top + tooltipH > vpH - 16) {
        top = rect.top - TOOLTIP_GAP - tooltipH;
      }
    } else { // 'top'
      top = rect.top - TOOLTIP_GAP - tooltipH;
      // If tooltip would go off-screen top, flip to bottom
      if (top < 16) {
        top = rect.bottom + TOOLTIP_GAP;
      }
    }

    setTooltipPos({ top: Math.max(16, top), left });
  }, [findTarget, step?.position]);

  // ── Auto-scroll + Retry finding target ─────────────────────────────────────
  useEffect(() => {
    if (!isTourActive || !isSpotlightStep) return;

    let attempts = 0;
    const maxAttempts = 10; // retry for ~3 seconds
    let retryTimer = null;

    const tryFind = () => {
      const el = findTarget();
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Wait for scroll to finish, then update position
        setTimeout(updatePosition, 400);
      } else if (attempts < maxAttempts) {
        attempts++;
        retryTimer = setTimeout(tryFind, 300);
      } else {
        setTargetRect(null); // fallback
      }
    };

    tryFind();

    return () => {
      if (retryTimer) clearTimeout(retryTimer);
      // Reset z-index of target element
      const el = findTarget();
      if (el) {
        el.style.position = '';
        el.style.zIndex = '';
        el.style.pointerEvents = '';
      }
    };
  }, [isTourActive, isSpotlightStep, currentStep, findTarget, updatePosition]);

  // ── Elevate target element above overlay ────────────────────────────────────
  useEffect(() => {
    if (!isTourActive || !isSpotlightStep || !targetRect) return;
    const el = findTarget();
    if (el) {
      el.style.position = 'relative';
      el.style.zIndex = '9991';
      el.style.pointerEvents = 'auto';
    }
    return () => {
      if (el) {
        el.style.position = '';
        el.style.zIndex = '';
        el.style.pointerEvents = '';
      }
    };
  }, [isTourActive, isSpotlightStep, targetRect, findTarget]);

  // ── Observe resize/scroll for position updates ─────────────────────────────
  useEffect(() => {
    if (!isTourActive || !isSpotlightStep) return;

    const handleUpdate = () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = requestAnimationFrame(updatePosition);
    };

    window.addEventListener('resize', handleUpdate);
    window.addEventListener('scroll', handleUpdate, true);

    // Initial position update
    handleUpdate();

    return () => {
      window.removeEventListener('resize', handleUpdate);
      window.removeEventListener('scroll', handleUpdate, true);
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isTourActive, isSpotlightStep, currentStep, updatePosition]);

  // ── Animation class on step change ─────────────────────────────────────────
  useEffect(() => {
    if (!isTourActive || !isSpotlightStep) return;
    setAnimClass('');
    requestAnimationFrame(() => {
      const pos = step?.position || 'bottom';
      setAnimClass(targetRect ? `animate-in-${pos}` : 'animate-in-center');
    });
    setOverlayState('entering');
  }, [currentStep, isTourActive, isSpotlightStep, targetRect]);

  // ── Auto-advance polling & Manual Next checking ────────────────────────────
  const checkActionFulfilled = useCallback(() => {
    if (!step?.waitForAction) return true; // no action needed
    if (step.waitForAction === 'upload') {
      return !!document.querySelector('[data-tour="detect-button"]');
    }
    if (step.waitForAction === 'detect') {
      return !!document.querySelector('[data-tour="summary-card"]');
    }
    return true;
  }, [step?.waitForAction]);

  useEffect(() => {
    if (!isTourActive || !isSpotlightStep || !step?.waitForAction) return;

    // If initially fulfilled (e.g. replay), DONT auto-advance, just let them click 'Lanjut'
    if (checkActionFulfilled()) return;

    let advanceTimer;
    const interval = setInterval(() => {
      if (checkActionFulfilled()) {
        clearInterval(interval);
        // Add a slight delay for better UX before advancing
        advanceTimer = setTimeout(() => nextStep(), 800);
      }
    }, 500);

    return () => {
      clearInterval(interval);
      if (advanceTimer) clearTimeout(advanceTimer);
    };
  }, [isTourActive, isSpotlightStep, step?.waitForAction, currentStep, nextStep, checkActionFulfilled]);

  // ── Keyboard navigation ────────────────────────────────────────────────────
  useEffect(() => {
    if (!isTourActive || !isSpotlightStep) return;

    const handleKey = (e) => {
      if (e.key === 'Escape') skipTour();
      else if (e.key === 'ArrowRight' && (!step?.waitForAction || checkActionFulfilled())) nextStep();
      else if (e.key === 'ArrowLeft') prevStep();
    };

    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isTourActive, isSpotlightStep, currentStep, nextStep, prevStep, skipTour, step?.waitForAction, checkActionFulfilled]);

  // ── Don't render for non-spotlight steps or when tour inactive ──────────────
  if (!isTourActive || !isSpotlightStep) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) skipTour();
  };
  const showManualNext = checkActionFulfilled() || !targetRect;

  // Fallback mode: element not found
  const isFallback = !targetRect;

  return (
    <>
      {/* ── Overlay with SVG hole ──────────────────────────── */}
      <div
        className={`tour-spotlight-overlay ${overlayState}`}
        onClick={handleBackdropClick}
      >
        <svg className="tour-spotlight-svg" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <mask id="tour-mask">
              <rect width="100%" height="100%" fill="white" />
              {targetRect && (
                <rect
                  x={targetRect.left}
                  y={targetRect.top}
                  width={targetRect.width}
                  height={targetRect.height}
                  rx="14"
                  ry="14"
                  fill="black"
                />
              )}
            </mask>
          </defs>
          <rect
            width="100%"
            height="100%"
            fill="rgba(0,0,0,0.6)"
            mask="url(#tour-mask)"
          />
        </svg>
      </div>

      {/* ── Click-through area over highlighted element ──────── */}
      {targetRect && (
        <div
          style={{
            position: 'fixed',
            top: targetRect.top,
            left: targetRect.left,
            width: targetRect.width,
            height: targetRect.height,
            zIndex: 9991,
            pointerEvents: 'none', // let clicks pass through to actual elements
            borderRadius: 14,
          }}
        />
      )}

      {/* ── Pulse ring around target ───────────────────────── */}
      {targetRect && (
        <div
          className="tour-pulse-ring"
          style={{
            top: targetRect.top,
            left: targetRect.left,
            width: targetRect.width,
            height: targetRect.height,
          }}
        />
      )}

      {/* ── Tooltip card ───────────────────────────────────── */}
      <div
        className={`tour-tooltip ${animClass}`}
        style={
          isFallback
            ? {
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
              }
            : {
                top: tooltipPos.top,
                left: tooltipPos.left,
              }
        }
        onClick={(e) => e.stopPropagation()}
      >
        {/* Arrow (only when not fallback) */}
        {!isFallback && step?.position === 'bottom' && (
          <div className="tour-tooltip-arrow arrow-top" />
        )}
        {!isFallback && step?.position === 'top' && (
          <div className="tour-tooltip-arrow arrow-bottom" />
        )}

        {/* Skip button */}
        <button
          className="tour-tooltip-skip"
          onClick={skipTour}
          title="Lewati panduan"
          aria-label="Lewati panduan"
        >
          <X size={16} strokeWidth={2.5} />
        </button>

        {/* Title */}
        <h3 className="tour-tooltip-title">
          {isFallback ? step?.fallbackTitle || step?.title : step?.title}
        </h3>

        {/* Description */}
        <p className="tour-tooltip-desc">
          {isFallback ? step?.fallbackDesc || step?.description : step?.description}
        </p>

        {/* Tip */}
        {step?.tip && !isFallback && (
          <div className="tour-tooltip-tip">{step.tip}</div>
        )}

        {/* Features list (step 6) */}
        {step?.features && !isFallback && (
          <div className="tour-tooltip-features">
            {step.features.map((f, i) => (
              <div className="tour-tooltip-feature" key={i}>
                <span className="tour-tooltip-feature-icon">{f.icon}</span>
                {f.label}
              </div>
            ))}
          </div>
        )}

        {/* Waiting indicator */}
        {step?.waitForAction && !showManualNext && !isFallback && (
          <div className="tour-waiting-indicator">
            <span className="tour-waiting-dot" />
            Menunggu kamu melakukan aksi di atas...
          </div>
        )}

        {/* Navigation */}
        <div className="tour-tooltip-nav">
          {currentStep > 1 && (
            <button className="tour-tooltip-btn tour-tooltip-btn-back" onClick={prevStep}>
              <ChevronLeft size={15} /> Kembali
            </button>
          )}
          {(showManualNext || isFallback) && (
            <button
              className="tour-tooltip-btn tour-tooltip-btn-next"
              onClick={nextStep}
              style={currentStep <= 1 ? { flex: 1 } : { flex: 2 }}
            >
              Lanjut <ChevronRight size={15} />
            </button>
          )}
        </div>

        {/* Progress bar */}
        <div className="tour-progress-bar">
          {Array.from({ length: totalSteps }).map((_, i) => (
            <div
              key={i}
              className={`tour-progress-segment ${
                i < currentStep ? 'filled' : i === currentStep ? 'current' : ''
              }`}
            />
          ))}
        </div>
      </div>
    </>
  );
}
