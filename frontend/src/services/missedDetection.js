import { apiPostJson } from './api';

/**
 * Report a missed detection — when user manually adds a food
 * that the model should have detected but didn't.
 * 
 * This is fire-and-forget: we don't block the UI on this call.
 * 
 * @param {Object} data - { analysis_id, missed_label, tkpi_food_id?, note? }
 * @returns {Promise<Object>} Response { ok, message }
 */
export async function reportMissedDetection(data) {
  return apiPostJson('/api/v1/missed-detection', data);
}
