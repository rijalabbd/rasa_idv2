import { apiGet } from './api';

/**
 * Search TKPI database for food items
 * @param {string} query - Search query
 * @param {number} limit - Maximum results (default: 10)
 * @param {boolean|null} fuzzy - Override fuzzy mode:
 *   true  → force token-based fuzzy search
 *   false → force exact-phrase match
 *   null/undefined → use server-side TKPI_FUZZY_SEARCH feature flag
 * @returns {Promise<Array>} Search results [{id, name}]
 */
export async function searchTkpi(query, limit = 10, fuzzy = null) {
  if (!query || query.trim().length === 0) {
    return [];
  }

  let url = `/api/v1/tkpi/search?q=${encodeURIComponent(query)}&limit=${limit}`;
  if (fuzzy !== null && fuzzy !== undefined) {
    url += `&fuzzy=${fuzzy ? 'true' : 'false'}`;
  }

  return apiGet(url);
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

/**
 * Fetch list of foods the YOLO model can currently detect.
 * Returns { total, foods: [{ yolo_label, tkpi_food_id, name, tkpi_code }] }
 */
export async function fetchDetectableFoods() {
  return apiGet('/api/v1/detectable-foods');
}

/**
 * Fetch detectable foods and return a Set of TKPI food IDs for fast lookup.
 * @returns {Promise<Set<number>>}
 */
export async function getDetectableFoodIds() {
  const data = await fetchDetectableFoods();
  return new Set((data.foods || []).map(f => f.tkpi_food_id));
}
