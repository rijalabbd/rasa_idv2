// BoundingBoxOverlay.jsx
// Draws bounding boxes with labels and confidence on top of the uploaded image.

import { useRef, useEffect, useState } from 'react';

// Color palette for different classes (vibrant, high contrast)
const CLASS_COLORS = [
  '#FF3B30', // red
  '#FF9500', // orange
  '#FFCC00', // yellow
  '#34C759', // green
  '#00C7BE', // teal
  '#007AFF', // blue
  '#5856D6', // purple
  '#AF52DE', // magenta
  '#FF2D55', // pink
  '#A2845E', // brown
];

function getColorForLabel(label, allLabels) {
  const idx = allLabels.indexOf(label);
  return CLASS_COLORS[idx >= 0 ? idx % CLASS_COLORS.length : 0];
}

export default function BoundingBoxOverlay({ imageUrl, detections }) {
  const canvasRef = useRef(null);
  const imgRef = useRef(null);
  const containerRef = useRef(null);
  const [imgLoaded, setImgLoaded] = useState(false);

  // Unique labels for consistent coloring
  const uniqueLabels = [...new Set((detections || []).map(d => d.label))];

  useEffect(() => {
    if (!imgLoaded || !canvasRef.current || !imgRef.current) return;

    const img = imgRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Match canvas size to displayed image size
    const displayW = img.clientWidth;
    const displayH = img.clientHeight;
    canvas.width = displayW;
    canvas.height = displayH;

    // Scale factors (original image size → displayed size)
    const scaleX = displayW / img.naturalWidth;
    const scaleY = displayH / img.naturalHeight;

    ctx.clearRect(0, 0, displayW, displayH);

    if (!detections || detections.length === 0) return;

    detections.forEach((det) => {
      if (!det.bbox) return; // Skip if no bbox

      const [x1, y1, x2, y2] = det.bbox;
      const color = getColorForLabel(det.label, uniqueLabels);

      // Scale bbox coordinates to display size
      const sx1 = x1 * scaleX;
      const sy1 = y1 * scaleY;
      const sw = (x2 - x1) * scaleX;
      const sh = (y2 - y1) * scaleY;

      // Draw bounding box
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
      ctx.strokeRect(sx1, sy1, sw, sh);

      // Label text
      const conf = (det.confidence * 100).toFixed(1);
      const labelText = `${det.label} ${conf}%`;

      // Measure text
      ctx.font = 'bold 13px Inter, system-ui, sans-serif';
      const metrics = ctx.measureText(labelText);
      const textW = metrics.width + 10;
      const textH = 20;

      // Position label above bbox (or inside if near top edge)
      let labelY = sy1 - textH - 2;
      if (labelY < 0) labelY = sy1 + 2;

      // Draw label background
      ctx.fillStyle = color;
      ctx.fillRect(sx1, labelY, textW, textH);

      // Draw label text
      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 13px Inter, system-ui, sans-serif';
      ctx.fillText(labelText, sx1 + 5, labelY + 14);
    });
  }, [imgLoaded, detections, uniqueLabels]);

  // Redraw on window resize
  useEffect(() => {
    const handleResize = () => {
      if (imgLoaded) {
        setImgLoaded(false);
        requestAnimationFrame(() => setImgLoaded(true));
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [imgLoaded]);

  return (
    <div ref={containerRef} style={{ position: 'relative', display: 'inline-block', width: '100%' }}>
      <img
        ref={imgRef}
        src={imageUrl}
        alt="Detection result"
        onLoad={() => setImgLoaded(true)}
        style={{
          display: 'block',
          maxHeight: '24rem',
          margin: '0 auto',
          borderRadius: '0.5rem',
          width: 'auto',
          maxWidth: '100%',
        }}
      />
      <canvas
        ref={canvasRef}
        style={{
          position: 'absolute',
          top: 0,
          left: '50%',
          transform: 'translateX(-50%)',
          pointerEvents: 'none',
          maxHeight: '24rem',
          width: 'auto',
          maxWidth: '100%',
        }}
      />
    </div>
  );
}
