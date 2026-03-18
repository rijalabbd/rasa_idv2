import { apiPostMultipart } from './api';

/**
 * Detect food items from uploaded image
 * @param {File} imageFile - The image file to analyze
 * @returns {Promise<Object>} Detection results
 * Response format:
 * {
 *   analysis_id: number,
 *   image_path: string,
 *   model_version: string,
 *   avg_confidence: number,
 *   items: [{label, confidence, bbox, tkpi: {id, name, nutrition}}],
 *   total_nutrition: {energi_kal, protein_g, lemak_g, karbo_g, serat_g}
 * }
 */
export async function detectFood(imageFile) {
  const formData = new FormData();
  formData.append('file', imageFile);
  
  return apiPostMultipart('/api/v1/detect', formData);
}
