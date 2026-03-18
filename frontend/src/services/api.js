// frontend/src/services/api.js

import { TIMEOUTS } from '../constants/app';

// Base API configuration - normalized to prevent double slashes
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000')
  .replace(/\/$/, '');

/**
 * Helper: Normalize path to always start with /
 */
function normalizePath(path) {
  return path.startsWith('/') ? path : `/${path}`;
}

/**
 * Helper: Build full URL with normalized path
 */
function buildUrl(path) {
  return `${API_BASE_URL}${normalizePath(path)}`;
}

/**
 * Parse error response and return standardized error object
 * @returns {Promise<{message: string, code: string, detail: string, context: object, requestId: string}>}
 */
async function parseErrorResponse(response) {
  const requestId = response.headers.get('x-request-id');
  let errorData = {
    message: `Error ${response.status}: ${response.statusText}`,
    code: 'UNKNOWN_ERROR',
    detail: response.statusText,
    context: {},
    requestId
  };

  try {
    const data = await response.json();
    // Contract: { detail, code, context }
    if (data.detail) {
      errorData.message = data.detail;
      errorData.detail = data.detail;
    }
    if (data.code) errorData.code = data.code;
    if (data.context) errorData.context = data.context;
  } catch (e) {
    // Non-JSON response (e.g. 500 HTML or network error handled differently)
  }
  
  return errorData;
}

/**
 * Helper to throw standardized error
 */
function throwApiError(errorData) {
  const error = new Error(errorData.message);
  error.code = errorData.code;
  error.detail = errorData.detail;
  error.context = errorData.context;
  error.requestId = errorData.requestId;
  throw error;
}

/**
 * Handle fetch errors (network, timeout)
 */
function handleFetchError(error) {
  if (error?.name === 'AbortError') {
    const e = new Error('Proses terlalu lama (timeout). Silakan coba lagi.');
    e.code = 'TIMEOUT';
    throw e;
  }
  if (error instanceof TypeError) {
    const e = new Error('Gagal terhubung ke server. Periksa koneksi internet Anda.');
    e.code = 'NETWORK_ERROR';
    throw e;
  }
  throw error;
}

/**
 * GET request
 */
export async function apiGet(path) {
  const url = buildUrl(path);
  // Default GET timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUTS.DEFAULT || 10000);

  try {
    const response = await fetch(url, {
      method: 'GET',
      signal: controller.signal
      // Intentionally no Content-Type header → avoids preflight
    });

    if (!response.ok) {
      const errorData = await parseErrorResponse(response);
      throwApiError(errorData);
    }

    return await response.json();
  } catch (error) {
    handleFetchError(error);
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Legacy compatibility - conditional Content-Type to avoid unnecessary preflight on GET
 */
export async function apiRequest(endpoint, options = {}) {
  const url = buildUrl(endpoint);

  const headers = { ...(options.headers || {}) };
  const method = (options.method || 'GET').toUpperCase();

  // Only set Content-Type if not a simple GET request (has body or non-GET method)
  if (method !== 'GET' || options.body) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(url, {
      ...options,
      method,
      headers,
    });

    if (!response.ok) {
        const errorData = await parseErrorResponse(response);
        throwApiError(errorData);
    }

    return await response.json();
  } catch (error) {
    handleFetchError(error);
    throw error;
  }
}

export async function uploadFile(endpoint, file, additionalData = {}) {
  const formData = new FormData();
  formData.append('file', file);

  Object.entries(additionalData).forEach(([key, value]) => {
    formData.append(key, value);
  });

  return apiPostMultipart(endpoint, formData);
}

export async function apiPostMultipart(endpoint, formData) {
  const url = buildUrl(endpoint);
  // Upload might take longer
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUTS.UPLOAD || 30000);

  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
      headers: {
          // Let browser set Content-Type with boundary
      }
    });

    if (!response.ok) {
      const errorData = await parseErrorResponse(response);
      throwApiError(errorData);
    }

    return await response.json();
  } catch (error) {
    handleFetchError(error);
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function apiPostJson(endpoint, data) {
  const url = buildUrl(endpoint); 
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUTS.DEFAULT || 10000);

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      signal: controller.signal
    });

    if (!response.ok) {
        const errorData = await parseErrorResponse(response);
        throwApiError(errorData);
    }

    return await response.json();
  } catch (error) {
    handleFetchError(error);
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function submitClassRequest(payload) {
  // Ensure payload matches strict backend contract
  const data = {
    analysis_id: payload.analysis_id,
    requested_label: payload.requested_label,
    bbox: payload.bbox || null,
    note: payload.note || ''
  };
  return apiPostJson('/api/v1/class-request', data);
}
