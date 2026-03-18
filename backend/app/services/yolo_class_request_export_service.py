"""YOLO-ready class request export service.

Produces a ZIP with:
  class_requests_dataset/
    images/     — original class request images
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

from app.models.class_request import ClassRequest
from app.core.paths import STORAGE_DIR

logger = logging.getLogger(__name__)

PREFIX = "class_requests_dataset"


# ── helpers ──────────────────────────────────────────────────────────────

def _pixel_bbox_to_yolo(bbox: tuple, img_w: int, img_h: int) -> str:
    """Convert pixel bbox (x1,y1,x2,y2) to YOLO format normalized."""
    x1, y1, x2, y2 = bbox
    x_center = ((x1 + x2) / 2) / img_w
    y_center = ((y1 + y2) / 2) / img_h
    w = abs(x2 - x1) / img_w
    h = abs(y2 - y1) / img_h
    x_center = max(0.0, min(1.0, x_center))
    y_center = max(0.0, min(1.0, y_center))
    w = max(0.0, min(1.0, w))
    h = max(0.0, min(1.0, h))
    return f"{x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}"


def _get_image_dimensions(path: Path) -> Tuple[int, int]:
    """Return (width, height) of an image."""
    with Image.open(path) as img:
        return img.size


# ── main export ──────────────────────────────────────────────────────────

def build_yolo_class_request_zip(db: Session) -> Tuple[io.BytesIO, int, int]:
    """
    Build a YOLO-ready ZIP from class request data.
    Returns (zip_buffer, exported_count, skipped_count).
    """
    requests = db.execute(
        select(ClassRequest).order_by(ClassRequest.created_at)
    ).scalars().all()

    # Build dynamic class map
    unique_labels = sorted(set(
        r.requested_label for r in requests if r.requested_label
    ))
    label_to_id = {label: idx for idx, label in enumerate(unique_labels)}

    zip_buffer = io.BytesIO()
    exported = 0
    skipped = 0
    metadata_rows: List[dict] = []

    # Aggregate by image to avoid duplicate ZIP entry errors
    grouped = {}
    for req in requests:
        if not req.image_path:
            skipped += 1
            metadata_rows.append({
                "id": req.id, "label": req.requested_label or "",
                "image_filename": "",
                "skipped_reason": "no image_path",
            })
            continue

        image_path = STORAGE_DIR / req.image_path
        stem = image_path.stem
        if stem not in grouped:
            grouped[stem] = {"image_path": image_path, "items": []}
        grouped[stem]["items"].append(req)

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for stem, data in grouped.items():
            image_path = data["image_path"]
            reqs = data["items"]

            if not image_path.exists():
                skipped += len(reqs)
                for r in reqs:
                    metadata_rows.append({
                        "id": r.id, "label": r.requested_label or "",
                        "image_filename": image_path.name,
                        "skipped_reason": f"image file missing: {image_path.name}",
                    })
                continue

            try:
                img_w, img_h = _get_image_dimensions(image_path)
            except Exception as e:
                skipped += len(reqs)
                continue

            if img_w == 0 or img_h == 0:
                skipped += len(reqs)
                continue
            
            label_lines = []
            img_exported = 0
            
            for req in reqs:
                if not req.requested_label:
                    continue
                    
                class_id = label_to_id.get(req.requested_label, 0)
                
                # Use dummy bbox if null (common for full image class requests)
                if req.bbox_x1 is None or req.bbox_y1 is None or req.bbox_x2 is None or req.bbox_y2 is None:
                    yolo_coords = "0.500000 0.500000 0.010000 0.010000"
                else:
                    yolo_coords = _pixel_bbox_to_yolo(
                        (req.bbox_x1, req.bbox_y1, req.bbox_x2, req.bbox_y2), img_w, img_h
                    )
                    
                label_lines.append(f"{class_id} {yolo_coords}\n")
                img_exported += 1
                metadata_rows.append({
                    "id": req.id, "label": req.requested_label,
                    "image_filename": image_path.name,
                    "skipped_reason": "",
                })

            if img_exported == 0:
                skipped += len(reqs)
                continue

            # Add image
            img_key = image_path.name
            zipf.write(image_path, f"{PREFIX}/images/{img_key}")

            # Add labels
            label_key = f"{stem}.txt"
            zipf.writestr(f"{PREFIX}/labels/{label_key}", "".join(label_lines))
            
            exported += img_exported

        zipf.writestr(f"{PREFIX}/data.yaml", _build_data_yaml(unique_labels))
        zipf.writestr(f"{PREFIX}/metadata.csv", _build_metadata_csv(metadata_rows))

    zip_buffer.seek(0)
    logger.info(f"YOLO class request export: {exported} exported, {skipped} skipped")
    return zip_buffer, exported, skipped


# ── generators ───────────────────────────────────────────────────────────

def _build_data_yaml(class_names: list) -> str:
    lines = [
        f"# YOLO Class Requests Dataset — Generated {datetime.now().isoformat()}",
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
