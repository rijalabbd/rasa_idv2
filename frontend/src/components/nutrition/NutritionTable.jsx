import { useMemo } from 'react';
import { calculateTotalNutrition } from '../../utils/nutrition';

/**
 * Display total nutrition summary table
 * @param {Array} items - Detection items with baseNutrition, portion, and selected fields
 */
export default function NutritionTable({ items = [] }) {
  const total = useMemo(() => calculateTotalNutrition(items), [items]);

  const nutritionRows = [
    { label: 'Kalori', value: total.energi_kal, unit: 'kkal' },
    { label: 'Protein', value: total.protein_g, unit: 'g' },
    { label: 'Lemak', value: total.lemak_g, unit: 'g' },
    { label: 'Karbohidrat', value: total.karbo_g, unit: 'g' },
    { label: 'Serat', value: total.serat_g, unit: 'g' },
  ];

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Nutrisi
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Total
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {nutritionRows.map((row) => (
            <tr key={row.label}>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {row.label}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                {row.value.toFixed(1)} {row.unit}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-3 text-xs text-gray-400 text-right italic">
        *Sumber Data Referensi: Tabel Komposisi Pangan Indonesia (TKPI) 2020
      </div>
    </div>
  );
}
