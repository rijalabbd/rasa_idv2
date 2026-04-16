import io
import json
import logging
import zipfile
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select

logger = logging.getLogger(__name__)

from app.models.missed_detection import MissedDetection
from app.core.paths import UPLOADS_DIR, MISSED_DETECTION_IMAGES_DIR
from app.services.feedback_service import (
    get_yolo_class_id,
    generate_classes_txt,
    _get_image_dimensions,
    _pixel_bbox_to_yolo,
)
from app.services.export_tracking_service import (
    get_unexported_ids,
    get_all_ids,
    mark_exported,
    generate_batch_id,
)


def _resolve_image_path(md: MissedDetection) -> Path | None:
    """
    Resolve image path for a missed detection record.
    Priority:
      1. missed_detection/images/<image_filename>  (dedicated copy — preferred)
      2. uploads/<date>/<filename>                 (original upload — legacy fallback)
    Returns None if no image found.
    """
    if md.image_filename:
        p = MISSED_DETECTION_IMAGES_DIR / md.image_filename
        if p.exists():
            return p

    if md.analysis and md.analysis.image_path:
        orig = Path(md.analysis.image_path)
        if not orig.is_absolute():
            orig = UPLOADS_DIR.parent / orig
        if orig.exists():
            return orig

    return None


def _safe_get_class_id(label: str):
    """Resolve class_id without crashing. Returns None if label not in model."""
    try:
        return get_yolo_class_id(label)
    except ValueError:
        return None

def build_yolo_missed_detection_zip(db: Session, only_new: bool = True) -> tuple[io.BytesIO, int, int, str]:
    """
    Builds a ZIP file containing missed detection data:
      - missed/images/
      - missed/labels/ (BBox 1.0 1.0 full frame)
      - classes.txt
      - metadata.json

    Returns:
        tuple: (BytesIO_buffer, exported_count, skipped_count, batch_id)
    """
    batch_id = generate_batch_id()
    
    if only_new:
        target_ids = get_unexported_ids(db, "missed_detection")
    else:
        target_ids = get_all_ids(db, "missed_detection")

    if not target_ids:
        return io.BytesIO(), 0, 0, batch_id

    exported = 0
    skipped = 0

    missed_records = db.execute(
        select(MissedDetection).where(MissedDetection.id.in_(target_ids)).order_by(MissedDetection.created_at)
    ).scalars().all()

    # Group by analysis_id so we don't duplicate images
    grouped: dict = {}
    for md in missed_records:
        key = md.analysis_id
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(md)

    zip_buffer = io.BytesIO()
    metadata = {}

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("missed/images/", "")
        zip_file.writestr("missed/labels/", "")

        for analysis_id, reports in grouped.items():
            img_path = _resolve_image_path(reports[0])

            if not img_path:
                skipped += len(reports)
                continue

            base_name = f"missed_{analysis_id}_{img_path.stem}"

            # 1) Add image to ZIP
            try:
                zip_file.write(
                    img_path,
                    arcname=f"missed/images/{base_name}{img_path.suffix}",
                )
            except Exception as e:
                logger.warning("Skipping missed detection %d: image read err: %s", analysis_id, e)
                skipped += len(reports)
                continue

            # 2) Build YOLO label
            label_lines = []
            detected_classes = []
            
            # --- INCLUDE ALREADY DETECTED OBJECTS ---

            img_w, img_h = 0, 0
            try:
                img_w, img_h = _get_image_dimensions(img_path)
            except Exception as e:
                logger.warning("Dimension read failed for %s: %s", img_path, e)
                
            if img_w > 0 and img_h > 0 and reports[0].analysis:
                for det in reports[0].analysis.detections:
                    try:
                        c_id = get_yolo_class_id(det.label)
                    except ValueError:
                        logger.warning(
                            "Skipping detection label '%s' (analysis_id=%d): not in active model class map",
                            det.label, analysis_id,
                        )
                        continue
                    yolo_c = _pixel_bbox_to_yolo((det.bbox_x1, det.bbox_y1, det.bbox_x2, det.bbox_y2), img_w, img_h)
                    label_lines.append(f"{c_id} {yolo_c}\n")
                    detected_classes.append(det.label)

            # --- INCLUDE MISSED OBJECTS (Full frame 1.0 1.0 because it needs manual relabel) ---
            for rep in reports:
                try:
                    class_id = get_yolo_class_id(rep.missed_label)
                except ValueError:
                    logger.warning(
                        "Skipping missed detection label '%s' (record_id=%d): not in active model class map",
                        rep.missed_label, rep.id,
                    )
                    skipped += 1
                    continue
                label_lines.append(f"{class_id} 0.500000 0.500000 1.000000 1.000000\n")

            zip_file.writestr(f"missed/labels/{base_name}.txt", "".join(label_lines))
            
            # 3) Collect metadata
            metadata[base_name] = {
                "feedback_id": reports[0].id,
                "analysis_id": analysis_id,
                "reported_class": reports[0].missed_label,
                "detected_classes": list(set(detected_classes)),
                "class_id": _safe_get_class_id(reports[0].missed_label),
                "submitted_at": reports[0].created_at.isoformat() if reports[0].created_at else "",
                "user_note": reports[0].note or ""
            }
            
            exported += len(reports)

        # 4) Add classes.txt and metadata.json to root
        zip_file.writestr("classes.txt", generate_classes_txt())
        zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))

    zip_buffer.seek(0)
    
    # Mark as exported after successful build
    exported_ids = [m.id for m in missed_records]
    mark_exported(db, "missed_detection", exported_ids, batch_id)
    
    return zip_buffer, exported, skipped, batch_id
