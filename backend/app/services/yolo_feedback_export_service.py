"""YOLO-ready feedback export service.

Produces a ZIP with:
  feedback_dataset/
    images/     — original feedback images
    labels/     — YOLO annotation .txt files
    data.yaml   — class names + config
    metadata.csv — tracking info
"""

import io
import csv
import logging
import zipfile
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Tuple, Optional

from PIL import Image
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.feedback import Feedback
from app.models.analysis import Analysis
from app.models.yolo_tkpi_mapping import YoloTkpiMapping
from app.core.paths import FEEDBACK_IMAGES_DIR, FEEDBACK_LABELS_DIR

logger = logging.getLogger(__name__)

PREFIX = "feedback_dataset"


# ── helpers ──────────────────────────────────────────────────────────────

def _find_image(stem: str, directory: Path) -> Path | None:
    """Find image file by stem, trying common extensions."""
    for ext in ("jpg", "jpeg", "png", "JPG", "JPEG", "PNG"):
        p = directory / f"{stem}.{ext}"
        if p.exists():
            return p
    matches = list(directory.glob(f"{stem}.*"))
    return matches[0] if matches else None

import json

from app.services.feedback_service import (
    _pixel_bbox_to_yolo,
    _get_image_dimensions,
    _calculate_iou,
    generate_classes_txt,
    get_yolo_class_id,
    get_dynamic_class_map,
)
from app.services.export_tracking_service import (
    get_unexported_ids,
    get_all_ids,
    mark_exported,
    generate_batch_id,
)


def build_yolo_feedback_zip(db: Session, only_new: bool = True) -> Tuple[io.BytesIO, int, int, str]:
    """
    Build a YOLO-ready ZIP from feedback data.
    Separates into wrong_class/ and false_positive/.
    Returns (zip_buffer, exported_count, skipped_count, batch_id).
    """
    batch_id = generate_batch_id()
    
    if only_new:
        target_ids = get_unexported_ids(db, "feedback")
    else:
        target_ids = get_all_ids(db, "feedback")

    if not target_ids:
        return io.BytesIO(), 0, 0, batch_id

    feedbacks = db.execute(
        select(Feedback).where(Feedback.id.in_(target_ids)).order_by(Feedback.created_at)
    ).scalars().all()

    # Load related analyses
    analysis_ids = list(set(f.analysis_id for f in feedbacks if f.analysis_id))
    analyses = db.execute(
        select(Analysis).where(Analysis.id.in_(analysis_ids))
    ).scalars().all() if analysis_ids else []
    analyses_map = {a.id: a for a in analyses}

    zip_buffer = io.BytesIO()
    exported = 0
    skipped = 0
    metadata = {}

    grouped = {}
    for fb in feedbacks:
        if fb.image_filename:
            image_stem = Path(fb.image_filename).stem
            image_path = FEEDBACK_IMAGES_DIR / fb.image_filename
        else:
            analysis = analyses_map.get(fb.analysis_id)
            if not analysis or not analysis.image_path:
                skipped += 1
                logger.info(f"Skipped feedback {fb.id}: no image_filename and no analysis image")
                continue
            image_stem = Path(analysis.image_path).stem
            image_path = _find_image(image_stem, FEEDBACK_IMAGES_DIR)
            if not image_path:
                skipped += 1
                logger.info(f"Skipped feedback {fb.id}: image not found for stem '{image_stem}'")
                continue
                
        if image_stem not in grouped:
            grouped[image_stem] = {"image_path": image_path, "items": []}
        grouped[image_stem]["items"].append(fb)

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("wrong_class/images/", "")
        zipf.writestr("wrong_class/labels/", "")
        zipf.writestr("false_positive/images/", "")
        zipf.writestr("false_positive/labels/", "")

        for stem, data in grouped.items():
            image_path = data["image_path"]
            fbs = data["items"]
            
            if not image_path.exists():
                skipped += len(fbs)
                logger.info(f"Skipped {len(fbs)} feedbacks: image file missing: {image_path.name}")
                continue

            try:
                img_w, img_h = _get_image_dimensions(image_path)
            except Exception as e:
                skipped += len(fbs)
                continue

            if img_w == 0 or img_h == 0:
                skipped += len(fbs)
                continue

            has_wrong_class = False
            img_exported = 0
            label_lines = []
            detected_classes_canonical = []
            
            # Use the first feedback item for metadata identity
            primary_fb = fbs[0]
            
            # --- 1) INCLUDE ALREADY DETECTED OBJECTS ---

            analysis = analyses_map.get(primary_fb.analysis_id)
            if analysis and analysis.detections:
                for det in analysis.detections:
                    det_box = (det.bbox_x1, det.bbox_y1, det.bbox_x2, det.bbox_y2)
                    is_overlap = False
                    for fb in fbs:
                        if fb.bbox_x1 is not None and fb.bbox_y1 is not None and fb.bbox_x2 is not None and fb.bbox_y2 is not None:
                            fb_box = (fb.bbox_x1, fb.bbox_y1, fb.bbox_x2, fb.bbox_y2)
                            if _calculate_iou(det_box, fb_box) > 0.5:
                                is_overlap = True
                                break
                    
                    if not is_overlap:
                        class_map = get_dynamic_class_map()
                        label_lower = det.label.lower().strip()
                        if label_lower in class_map:
                            c_id = class_map[label_lower]
                            y_c = _pixel_bbox_to_yolo((det.bbox_x1, det.bbox_y1, det.bbox_x2, det.bbox_y2), img_w, img_h)
                            label_lines.append(f"{c_id} {y_c}\n")
                            detected_classes_canonical.append(label_lower)
                            img_exported += 1
                        else:
                            logger.warning(f"Analysis {analysis.id}: Original detection label '{det.label}' not in current model map. Skipping box.")

            # --- 2) INCLUDE USER FEEDBACK BBOXES ---
            for fb in fbs:
                if fb.bbox_x1 is None or fb.bbox_y1 is None or fb.bbox_x2 is None or fb.bbox_y2 is None:
                    continue

                coords = (fb.bbox_x1, fb.bbox_y1, fb.bbox_x2, fb.bbox_y2)
                yolo_coords = _pixel_bbox_to_yolo(coords, img_w, img_h)
                if fb.corrected_tkpi_food_id:
                    # Resolve correction to canonical YOLO label
                    mapping = db.execute(
                        select(YoloTkpiMapping).where(YoloTkpiMapping.tkpi_food_id == fb.corrected_tkpi_food_id)
                    ).scalar_one_or_none()
                    
                    if mapping:
                        class_map = get_dynamic_class_map()
                        mapped_label = mapping.yolo_label.lower().strip()
                        
                        if mapped_label in class_map:
                            class_id = class_map[mapped_label]
                            label_lines.append(f"{class_id} {yolo_coords}\n")
                            detected_classes_canonical.append(mapped_label)
                            has_wrong_class = True
                            img_exported += 1
                        else:
                            logger.warning(f"Feedback {fb.id}: Corrected label '{mapped_label}' not in current model map. Skipping box.")
                    else:
                        logger.warning(f"Feedback {fb.id}: No YoloTkpiMapping for TKPI ID {fb.corrected_tkpi_food_id}. Skipping box.")
                else:
                    # False Positive - intentional omit from label file
                    # We still treat the image as "exported" but this specific box is gone
                    pass

            folder_category = "wrong_class" if has_wrong_class else "false_positive"

            if img_exported == 0 and not label_lines and folder_category == "false_positive":
                # Special case: Image with ONLY False Positives.
                # Export as background (empty .txt)
                img_exported = 1
            
            if img_exported == 0:
                skipped += len(fbs)
                continue

            # Add image
            img_key = image_path.name
            zipf.write(image_path, f"{folder_category}/images/{img_key}")

            # Add label
            label_key = f"{stem}.txt"
            zipf.writestr(f"{folder_category}/labels/{label_key}", "".join(label_lines))
            
            # Collection metadata
            metadata[img_key] = {
                "feedback_id": primary_fb.id,
                "analysis_id": primary_fb.analysis_id,
                "folder": folder_category,
                "reported_class": primary_fb.predicted_label,
                "detected_classes": list(set(detected_classes_canonical)),
                "submitted_at": primary_fb.created_at.isoformat() if primary_fb.created_at else "",
                "user_note": primary_fb.note or ""
            }

            exported += img_exported

        # Add classes.txt and metadata.json to root
        zipf.writestr("classes.txt", generate_classes_txt())
        zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

    zip_buffer.seek(0)
    
    # Mark as exported after successful build
    exported_ids = [fb.id for fb in feedbacks] # All records that were part of this batch
    mark_exported(db, "feedback", exported_ids, batch_id)
    
    logger.info(f"YOLO feedback export: {exported} exported, {skipped} skipped (batch {batch_id})")
    return zip_buffer, exported, skipped, batch_id
