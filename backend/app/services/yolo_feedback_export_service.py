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
from datetime import datetime
from typing import List, Tuple

from PIL import Image
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.feedback import Feedback
from app.models.analysis import Analysis
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


def _pixel_bbox_to_yolo(bbox: tuple, img_w: int, img_h: int) -> str:
    """Convert pixel bbox (x1,y1,x2,y2) to YOLO format (x_center, y_center, w, h) normalized."""
    x1, y1, x2, y2 = bbox
    x_center = ((x1 + x2) / 2) / img_w
    y_center = ((y1 + y2) / 2) / img_h
    w = abs(x2 - x1) / img_w
    h = abs(y2 - y1) / img_h
    # Clamp to [0, 1]
    x_center = max(0.0, min(1.0, x_center))
    y_center = max(0.0, min(1.0, y_center))
    w = max(0.0, min(1.0, w))
    h = max(0.0, min(1.0, h))
    return f"{x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}"


def _get_image_dimensions(path: Path) -> Tuple[int, int]:
    """Return (width, height) of an image."""
    with Image.open(path) as img:
        return img.size  # (width, height)


# ── main export ──────────────────────────────────────────────────────────

def build_yolo_feedback_zip(db: Session) -> Tuple[io.BytesIO, int, int]:
    """
    Build a YOLO-ready ZIP from feedback data.
    Returns (zip_buffer, exported_count, skipped_count).
    """
    feedbacks = db.execute(
        select(Feedback).order_by(Feedback.created_at)
    ).scalars().all()

    # Load related analyses
    analysis_ids = list(set(f.analysis_id for f in feedbacks if f.analysis_id))
    analyses = db.execute(
        select(Analysis).where(Analysis.id.in_(analysis_ids))
    ).scalars().all() if analysis_ids else []
    analyses_map = {a.id: a for a in analyses}

    # Build dynamic class map from dataset
    unique_labels = sorted(set(f.predicted_label for f in feedbacks if f.predicted_label))
    label_to_id = {label: idx for idx, label in enumerate(unique_labels)}

    zip_buffer = io.BytesIO()
    exported = 0
    skipped = 0
    metadata_rows: List[dict] = []

    # Aggregate feedbacks by image to avoid writing the same file twice
    # grouped_by_image: { image_stem: [feedback_items_tuple, ... ] }
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
        for stem, data in grouped.items():
            image_path = data["image_path"]
            fbs = data["items"]
            
            # 2. File exists?
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

            # Build label content
            label_lines = []
            img_exported = 0
            for fb in fbs:
                # 3. Must have label
                if not fb.predicted_label:
                    continue
                # 4. Must have bbox
                if fb.bbox_x1 is None or fb.bbox_y1 is None or fb.bbox_x2 is None or fb.bbox_y2 is None:
                    continue

                class_id = label_to_id.get(fb.predicted_label, 0)
                yolo_coords = _pixel_bbox_to_yolo(
                    (fb.bbox_x1, fb.bbox_y1, fb.bbox_x2, fb.bbox_y2), img_w, img_h
                )
                label_lines.append(f"{class_id} {yolo_coords}\n")
                img_exported += 1
                metadata_rows.append({
                    "id": fb.id, "label": fb.predicted_label,
                    "image_filename": fb.image_filename or "",
                    "skipped_reason": "",
                })

            if img_exported == 0:
                skipped += len(fbs)
                continue

            # Add image
            img_key = image_path.name
            zipf.write(image_path, f"{PREFIX}/images/{img_key}")

            # Add label
            label_key = f"{stem}.txt"
            zipf.writestr(f"{PREFIX}/labels/{label_key}", "".join(label_lines))
            
            exported += img_exported

        # data.yaml
        zipf.writestr(f"{PREFIX}/data.yaml", _build_data_yaml(unique_labels))

        # metadata.csv
        zipf.writestr(f"{PREFIX}/metadata.csv", _build_metadata_csv(metadata_rows))

    zip_buffer.seek(0)
    logger.info(f"YOLO feedback export: {exported} exported, {skipped} skipped")
    return zip_buffer, exported, skipped


# ── generators ───────────────────────────────────────────────────────────

def _build_data_yaml(class_names: list) -> str:
    lines = [
        f"# YOLO Feedback Dataset — Generated {datetime.now().isoformat()}",
        "",
        "path: .",
        "train: images",
        "val: images",
        "",
        f"nc: {len(class_names)}",
        "names:",
    ]
    for name in class_names:
        lines.append(f"  - {name}")
    return "\n".join(lines) + "\n"


def _build_metadata_csv(rows: list) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["id", "label", "image_filename", "skipped_reason"])
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()
