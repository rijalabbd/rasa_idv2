"""YOLO-ready raw detection export service.

Produces a ZIP with:
  raw_detections_dataset/
    images/     — original uploaded analysis images
    labels/     — YOLO annotation .txt files (including empty files for background)
    classes.txt  — class names
    metadata.json — details of export
"""

import io
import json
import logging
import zipfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.analysis import Analysis
from app.models.detection import Detection
from app.core.paths import STORAGE_DIR

from app.services.feedback_service import (
    _pixel_bbox_to_yolo,
    _get_image_dimensions,
    generate_classes_txt,
    get_dynamic_class_map,
)
from app.services.export_tracking_service import (
    get_unexported_ids,
    get_all_ids,
    mark_exported,
    generate_batch_id,
)

logger = logging.getLogger(__name__)


def build_yolo_raw_zip(
    db: Session,
    only_new: bool = True,
    min_confidence: float = 0.50,
    include_background: bool = True,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Tuple[io.BytesIO, int, int, str]:
    """
    Build a YOLO-ready ZIP from raw analyses and detections.
    Returns (zip_buffer, exported_count, skipped_count, batch_id).
    """
    batch_id = generate_batch_id()

    if only_new:
        target_ids = get_unexported_ids(db, "raw_detection")
    else:
        target_ids = get_all_ids(db, "raw_detection")

    if not target_ids:
        return io.BytesIO(), 0, 0, batch_id

    # Base query
    stmt = select(Analysis).where(Analysis.id.in_(target_ids))

    # Apply date filters if provided
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            stmt = stmt.where(Analysis.created_at >= start_dt)
        except ValueError:
            logger.warning(f"Invalid start_date format: {start_date}")
            
    if end_date:
        try:
            end_dt = datetime.strptime(f"{end_date} 23:59:59", "%Y-%m-%d %H:%M:%S")
            stmt = stmt.where(Analysis.created_at <= end_dt)
        except ValueError:
            logger.warning(f"Invalid end_date format: {end_date}")

    analyses = db.execute(stmt.order_by(Analysis.created_at)).scalars().all()

    if not analyses:
        return io.BytesIO(), 0, 0, batch_id

    zip_buffer = io.BytesIO()
    exported = 0
    skipped = 0
    metadata = {}
    class_map = get_dynamic_class_map()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("images/", "")
        zipf.writestr("labels/", "")

        for analysis in analyses:
            if not analysis.image_path:
                skipped += 1
                continue

            image_path = STORAGE_DIR / analysis.image_path
            if not image_path.exists():
                skipped += 1
                logger.info(f"Skipped analysis {analysis.id}: image file missing: {analysis.image_path}")
                continue

            try:
                img_w, img_h = _get_image_dimensions(image_path)
            except Exception as e:
                logger.warning(f"Failed to get dimensions for {image_path.name}: {e}")
                skipped += 1
                continue

            if img_w == 0 or img_h == 0:
                skipped += 1
                continue

            # Process detections for this analysis
            label_lines = []
            valid_detections_count = 0
            detected_items_meta = []

            for det in analysis.detections:
                if det.confidence < min_confidence:
                    continue

                label_lower = det.label.lower().strip()
                if label_lower in class_map:
                    c_id = class_map[label_lower]
                    y_coords = _pixel_bbox_to_yolo((det.bbox_x1, det.bbox_y1, det.bbox_x2, det.bbox_y2), img_w, img_h)
                    label_lines.append(f"{c_id} {y_coords}\n")
                    valid_detections_count += 1
                    detected_items_meta.append({
                        "label": det.label,
                        "confidence": float(det.confidence),
                        "bbox": [det.bbox_x1, det.bbox_y1, det.bbox_x2, det.bbox_y2]
                    })
                else:
                    logger.warning(f"Analysis {analysis.id}: Detection label '{det.label}' not in class map.")

            # Determine whether to include this image
            if valid_detections_count == 0 and not include_background:
                skipped += 1
                continue

            # Add image to ZIP
            img_filename = image_path.name
            zipf.write(image_path, f"images/{img_filename}")

            # Add label file (even if empty, for background samples)
            label_filename = f"{image_path.stem}.txt"
            zipf.writestr(f"labels/{label_filename}", "".join(label_lines))

            # Store metadata
            metadata[img_filename] = {
                "analysis_id": analysis.id,
                "model_version": analysis.model_version,
                "confidence_threshold_used": min_confidence,
                "detected_items": detected_items_meta,
                "created_at": analysis.created_at.isoformat() if analysis.created_at else "",
            }

            exported += 1

        # Add classes.txt and metadata.json to root
        zipf.writestr("classes.txt", generate_classes_txt())
        zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

    zip_buffer.seek(0)

    # Mark as exported after successful build
    if exported > 0:
        exported_analysis_ids = [meta_val["analysis_id"] for meta_val in metadata.values()]
        mark_exported(db, "raw_detection", exported_analysis_ids, batch_id)

    logger.info(f"YOLO raw detection export: {exported} exported, {skipped} skipped (batch {batch_id})")
    return zip_buffer, exported, skipped, batch_id
