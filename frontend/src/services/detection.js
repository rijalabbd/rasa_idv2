import { apiPostMultipart } from './api';

/**
 * Detect food items from uploaded image
 * @param {File} imageFile - The image file to analyze
 * @returns {Promise<Object>} Detection results
 * Response format (matches DetectionResponse schema):
 * {
 *   analysis_id: number,
 *   inference_time_ms: number,
 *   items: [{
 *     label: string,
 *     confidence: number,
 *     bbox: [x1, y1, x2, y2],
 *     tkpi: { id, name, nutrition: {energi_kal, protein_g, lemak_g, karbo_g, serat_g} } | null,
 *     nutrition_status: "COCOK" | "MENDEKATI" | "BELUM_ADA",
 *     nutrition_status_label: string,
 *     nutrition_note: string | null
 *   }]
 * }
 */
export async function detectFood(imageFile) {
  const formData = new FormData();
  formData.append('file', imageFile);
  
  return apiPostMultipart('/api/v1/detect', formData);
}
