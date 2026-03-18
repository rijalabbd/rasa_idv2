import { apiGet } from './api';

/**
 * Search TKPI database for food items
 * @param {string} query - Search query
 * @param {number} limit - Maximum results (default: 10)
 * @returns {Promise<Array>} Search results [{id, name}]
 */
export async function searchTkpi(query, limit = 10) {
  if (!query || query.trim().length === 0) {
    return [];
  }
  
  return apiGet(`/api/v1/tkpi/search?q=${encodeURIComponent(query)}&limit=${limit}`);
}

/**
 * Get detailed nutrition info from TKPI by ID
 * @param {number} foodId - TKPI food ID
 * @returns {Promise<Object>} Detailed nutrition information
 * Response format:
 * {
 *   id: number,
 *   name: string,
 *   nutrition: {energi_kal, protein_g, lemak_g, karbo_g, serat_g}
 * }
 */
export async function getTkpiDetail(foodId) {
  return apiGet(`/api/v1/tkpi/${foodId}`);
}
