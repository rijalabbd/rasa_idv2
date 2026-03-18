import DetectionItem from './DetectionItem';

export default function DetectionList({ detections = [] }) {
  if (detections.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Belum ada hasil deteksi</p>
        <p className="text-sm mt-2">Upload foto untuk memulai analisis</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {detections.map((detection, index) => (
        <DetectionItem 
          key={index} 
          detection={detection}
          index={index}
        />
      ))}
    </div>
  );
}
