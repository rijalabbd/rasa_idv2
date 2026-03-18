/**
 * Reusable hook for TKPI (Indonesian Food Composition) search
 * Provides debounced search with state management
 * 
 * Used in:
 * - Edit correction flow
 * - Manual food addition flow  
 * - Training request flow
 */

import { useState, useRef, useEffect } from 'react';
import { searchTkpi } from '../services/tkpi';
import { DEBOUNCE_DELAYS } from '../constants/app';

/**
 * Custom hook for TKPI search with debouncing
 * @param {number} limit - Maximum number of search results (default: 10)
 * @returns {Object} Search state and handlers
 */
export function useTkpiSearch(limit = 10) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');
  const timerRef = useRef(null);
  const aliveRef = useRef(true);
  const reqIdRef = useRef(0);

  // Track component mount status
  useEffect(() => {
    aliveRef.current = true;
    return () => {
      aliveRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  /**
   * Handle search input change with debouncing
   * @param {string} value - Search query value
   */
  const handleSearch = (value) => {
    setQuery(value);
    setSelected(null);
    setError('');
    
    // Increment request ID to invalidate previous pending requests
    const currentReqId = ++reqIdRef.current;

    // ✅ FIX: Clear timeout BEFORE early return to prevent stale requests
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    
    if (!value.trim()) {
      setResults([]);
      return;
    }

    // Debounce search
    timerRef.current = setTimeout(async () => {
      if (!aliveRef.current) return; // Prevent execution if unmounted

      setIsSearching(true);
      try {
        const data = await searchTkpi(value, limit);
        
        // Prevent race condition: only update if this is the latest request and still mounted
        if (aliveRef.current && reqIdRef.current === currentReqId) {
          setResults(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        if (aliveRef.current && reqIdRef.current === currentReqId) {
          setError(err?.message || 'Pencarian gagal');
          setResults([]);
        }
      } finally {
        if (aliveRef.current && reqIdRef.current === currentReqId) {
          setIsSearching(false);
        }
      }
    }, DEBOUNCE_DELAYS.SEARCH);
  };

  /**
   * Handle TKPI selection from search results
   * @param {Object} tkpi - Selected TKPI food item
   */
  const handleSelect = (tkpi) => {
    setSelected(tkpi);
    setError('');
    // ✅ FIX: Update query to selected food name and clear results to hide dropdown
    setQuery(tkpi.name);
    setResults([]);
  };

  /**
   * Reset all search state
   */
  const reset = () => {
    // Invalidate any pending requests
    reqIdRef.current++;
    
    setQuery('');
    setResults([]);
    setSelected(null);
    setError('');
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  // Cleanup on unmount to prevent memory leaks (handled by main effect, redundant removed)

  return {
    query,
    results,
    isSearching,
    selected,
    error,
    handleSearch,
    handleSelect,
    reset,
  };
}
