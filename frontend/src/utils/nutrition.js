/**
 * Nutrition calculation utilities
 * Single source of truth for nutrition operations
 */

/**
 * Multiply nutrition values by a portion factor
 * @param {Object} nutrition - Base nutrition object with energi_kal, protein_g, lemak_g, karbo_g, serat_g
 * @param {number} factor - Multiplication factor (e.g., portion size)
 * @returns {Object} Multiplied nutrition values, rounded appropriately
 */
export function multiplyNutrition(nutrition, factor) {
  if (!nutrition || isNaN(factor) || factor <= 0) {
    return {
      energi_kal: 0,
      protein_g: 0,
      lemak_g: 0,
      karbo_g: 0,
      serat_g: 0,
    };
  }

  return {
    energi_kal: Math.round((nutrition.energi_kal || 0) * factor),
    protein_g: Math.round((nutrition.protein_g || 0) * factor * 10) / 10,
    lemak_g: Math.round((nutrition.lemak_g || 0) * factor * 10) / 10,
    karbo_g: Math.round((nutrition.karbo_g || 0) * factor * 10) / 10,
    serat_g: Math.round((nutrition.serat_g || 0) * factor * 10) / 10,
  };
}

/**
 * Calculate total nutrition from multiple food items
 * @param {Array} items - Array of food items with baseNutrition, portion, and selected fields
 * @returns {Object} Total nutrition summed across all selected items
 */
export function calculateTotalNutrition(items = []) {
  const total = {
    energi_kal: 0,
    protein_g: 0,
    lemak_g: 0,
    karbo_g: 0,
    serat_g: 0,
  };

  items.forEach((item) => {
    // Only sum selected items (user can deselect items from total)
    if (item.selected !== false && item.baseNutrition) {
      const multiplied = multiplyNutrition(item.baseNutrition, item.portion || 1);
      total.energi_kal += multiplied.energi_kal || 0;
      total.protein_g += multiplied.protein_g || 0;
      total.lemak_g += multiplied.lemak_g || 0;
      total.karbo_g += multiplied.karbo_g || 0;
      total.serat_g += multiplied.serat_g || 0;
    }
  });

  return total;
}

/**
 * Get nutrition status badge styling and text
 * @param {Object} item - Detection item with nutrition_status, nutrition_status_label, nutrition_note, tkpi fields
 * @returns {Object} Badge configuration with label, className, and note
 */
export function getNutritionBadge(item) {
  const statusLabel = item.nutrition_status_label;
  const status = item.nutrition_status;
  
  // Fallback logic if backend doesn't send status fields
  if (!statusLabel && !status) {
    if (item.tkpi) {
      return {
        label: 'Cocok',
        className: 'bg-green-100 text-green-800 border border-green-200',
        note: null,
      };
    }
    return {
      label: 'Belum ada datanya',
      className: 'bg-gray-100 text-gray-700 border border-gray-200',
      note: 'Data gizi belum tersedia.',
    };
  }
  
  // Use backend values
  if (status === 'COCOK' || statusLabel === 'Cocok') {
    return {
      label: 'Cocok',
      className: 'bg-green-100 text-green-800 border border-green-200',
      note: null,
    };
  }
  
  if (status === 'MENDEKATI' || statusLabel === 'Mendekati') {
    return {
      label: 'Mendekati',
      className: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
      note: item.nutrition_note || 'Angka gizi belum termasuk minyak/bumbu.',
    };
  }
  
  // BELUM_ADA or unknown
  return {
    label: statusLabel || 'Belum ada datanya',
    className: 'bg-gray-100 text-gray-700 border border-gray-200',
    note: 'Data gizi belum tersedia.',
  };
}
