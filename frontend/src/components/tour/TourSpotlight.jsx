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
  const [tooltipPos, setTooltipPos] = useState({ top: -999, left: -999, arrowPos: 'hidden' });
  const [animClass, setAnimClass] = useState('');
  const [overlayState, setOverlayState] = useState('entering');
  const tooltipRef = useRef(null);
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
    const vpW = window.innerWidth;
    const vpH = window.innerHeight;

    setTargetRect({
      top: rect.top - PADDING,
      left: rect.left - PADDING,
      width: rect.width + PADDING * 2,
      height: rect.height + PADDING * 2,
    });

    const isMobile = vpW <= 640;
    const tooltipElem = tooltipRef.current;
    
    const tooltipH = tooltipElem ? tooltipElem.offsetHeight : 220;
    const tooltipW = tooltipElem ? tooltipElem.offsetWidth : Math.min(vpW - 32, 380);

    let top, left, arrowPos;

    if (isMobile) {
      // Mobile bottom-sheet style
      left = 16;
      top = vpH - tooltipH - 24; // slight padding from bottom edge
      
      // If the spotlight is at the very bottom, shift the tooltip up so it doesn't overlap the spotlight!
      if (rect.bottom > top - TOOLTIP_GAP) {
        top = rect.top - tooltipH - TOOLTIP_GAP;
        // If it also overflows top, just fallback
        if (top < 16) top = 16;
      }
      arrowPos = 'hidden'; 
    } else {
      // Smart Positioning (Desktop/Tablet)
      // ── Calculate available space in all 4 directions ──
      const spaceAbove = rect.top - 16;
      const spaceBelow = vpH - rect.bottom - 16;
      const spaceRight = vpW - rect.right - 16;
      const spaceLeft  = rect.left - 16;

      // ── Try side placement first for tall elements ──
      const isTargetTall = rect.height > vpH * 0.35;

      if (isTargetTall && spaceRight >= tooltipW + TOOLTIP_GAP) {
        // Place to the RIGHT of the target
        left = rect.right + TOOLTIP_GAP;
        top = rect.top + Math.min(40, (rect.height - tooltipH) / 2);
        top = Math.max(16, Math.min(top, vpH - tooltipH - 16));
        arrowPos = 'hidden';
      } else if (isTargetTall && spaceLeft >= tooltipW + TOOLTIP_GAP) {
        // Place to the LEFT of the target
        left = rect.left - tooltipW - TOOLTIP_GAP;
        top = rect.top + Math.min(40, (rect.height - tooltipH) / 2);
        top = Math.max(16, Math.min(top, vpH - tooltipH - 16));
        arrowPos = 'hidden';
      } else if (spaceBelow >= tooltipH + TOOLTIP_GAP) {
        // Place below — enough room without overlapping
        left = rect.left + (rect.width / 2) - (tooltipW / 2);
        left = Math.max(16, Math.min(left, vpW - tooltipW - 16));
        top = rect.bottom + TOOLTIP_GAP;
        arrowPos = 'top';
      } else if (spaceAbove >= tooltipH + TOOLTIP_GAP) {
        // Place above
        left = rect.left + (rect.width / 2) - (tooltipW / 2);
        left = Math.max(16, Math.min(left, vpW - tooltipW - 16));
        top = rect.top - TOOLTIP_GAP - tooltipH;
        arrowPos = 'bottom';
      } else {
        // Fallback: fixed bottom-right corner (guaranteed no overlap)
        left = vpW - tooltipW - 24;
        top = vpH - tooltipH - 24;
        arrowPos = 'hidden';
      }

      // Final viewport clamp
      top = Math.max(16, Math.min(top, vpH - tooltipH - 16));
      left = Math.max(16, Math.min(left, vpW - tooltipW - 16));
    }

    setTooltipPos({ top, left, arrowPos });
  }, [findTarget]);

  // ── Auto-click, auto-scroll + Retry finding target ──────────────────────────
  useEffect(() => {
    if (!isTourActive || !isSpotlightStep) return;

    let attempts = 0;
    const maxAttempts = 15; // retry for ~4.5 seconds
    let retryTimer = null;
    let didAutoClick = false;

    const tryFind = () => {
      // Step 1: If this step requires auto-clicking a button first, do it
      if (step?.autoClick && !didAutoClick) {
        const clickEl = document.querySelector(`[data-tour="${step.autoClick}"]`);
        if (clickEl) {
          clickEl.click();
          didAutoClick = true;
          // Wait for React to render the form
          retryTimer = setTimeout(tryFind, 500);
          return;
        }
        // If click target not found yet, keep retrying
        if (attempts < maxAttempts) {
          attempts++;
          retryTimer = setTimeout(tryFind, 300);
          return;
        }
      }

      // Step 2: Find the spotlight target element
      const el = findTarget();
      if (el) {
        const rect = el.getBoundingClientRect();
        const vpH = window.innerHeight;
        const blockPos = rect.height < (vpH / 2) ? 'center' : 'start';
        el.scrollIntoView({ behavior: 'smooth', block: blockPos });
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
      // Cleanup: close any form that was auto-opened
      if (step?.autoClick) {
        // Find and click any cancel/close button inside the spotlighted form
        const formEl = document.querySelector(`[data-tour="${step.target}"]`);
        if (formEl) {
          const closeBtn = formEl.querySelector('button[class*="cancel"], button[class*="Batal"]')
            || formEl.querySelector('button:has(svg)'); // the X close button
          // Use a more reliable approach: look for buttons with "Batal" text or X icon
          const allBtns = formEl.querySelectorAll('button');
          for (const btn of allBtns) {
            if (btn.textContent.includes('Batal') || btn.querySelector('svg.lucide-x')) {
              btn.click();
              break;
            }
          }
        }
      }
    };
  }, [isTourActive, isSpotlightStep, currentStep, findTarget, updatePosition, step?.autoClick, step?.target]);

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

  // ── Handle Overlay State ─────────────────────────────────────────────
  useEffect(() => {
    if (!isTourActive || !isSpotlightStep) return;
    setOverlayState('entering');
  }, [currentStep, isTourActive, isSpotlightStep]);

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
        ref={tooltipRef}
        className={`tour-tooltip`}
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
        {!isFallback && tooltipPos.arrowPos === 'top' && (
          <div className="tour-tooltip-arrow arrow-top" />
        )}
        {!isFallback && tooltipPos.arrowPos === 'bottom' && (
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
