import Badge from '../ui/Badge';
import PortionSelector from '../nutrition/PortionSelector';

export default function DetectionItem({ detection, index }) {
  // detection shape: { name, confidence, portion, nutrition }
  const { name = 'Unknown', confidence = 0, portion = 100 } = detection;

  const getConfidenceBadge = (conf) => {
    if (conf >= 0.8) return 'success';
    if (conf >= 0.5) return 'warning';
    return 'danger';
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900">{name}</h3>
          <Badge variant={getConfidenceBadge(confidence)} className="mt-1">
            Confidence: {(confidence * 100).toFixed(1)}%
          </Badge>
        </div>
      </div>

      <PortionSelector 
        portion={portion}
        onChange={(newPortion) => {
          // TODO: Update portion in parent state
          console.log('New portion:', newPortion);
        }}
      />
    </div>
  );
}
