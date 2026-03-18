import { apiPostJson } from './api';

/**
 * Submit user correction/feedback for detection results
 * @param {Object} feedbackData - Correction data
 * Format:
 * {
 *   analysis_id: number,
 *   items: [{
 *     bbox: [x1, y1, x2, y2],
 *     predicted_label: string,
 *     corrected_tkpi_id: number (optional),
 *     note: string (optional)
 *   }]
 * }
 * @returns {Promise<Object>} Submission response {ok, saved, message}
 */
export async function submitFeedback(feedbackData) {
  return apiPostJson('/api/v1/feedback', feedbackData);
}
