"""Service to export missed detection data as a YOLO-ready dataset ZIP."""

import io
import os
import zipfile
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.missed_detection import MissedDetection
from app.core.paths import UPLOADS_DIR
from app.services.feedback_service import get_yolo_class_id


def build_yolo_missed_detection_zip(db: Session) -> tuple[io.BytesIO, int, int]:
    """
    Builds a ZIP file containing images and YOLO format txt labels
    for all missed detections.

    Returns:
        tuple: (BytesIO_buffer, exported_count, skipped_count)
    """
    exported = 0
    skipped = 0

    missed_records = db.execute(select(MissedDetection)).scalars().all()

    # Group by analysis_id so we don't duplicate images if there are multiple missed objects per image
    grouped = {}
    for md in missed_records:
        if md.analysis_id not in grouped:
            grouped[md.analysis_id] = []
        grouped[md.analysis_id].append(md)

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Create dataset structure
        zip_file.writestr("images/", "")
        zip_file.writestr("labels/", "")

        for analysis_id, reports in grouped.items():
            # Get analysis from the first report
            analysis = reports[0].analysis
            if not analysis or not analysis.image_path:
                skipped += len(reports)
                continue

            orig_img_path = Path(analysis.image_path)
            if not orig_img_path.is_absolute():
                orig_img_path = UPLOADS_DIR / orig_img_path.name

            if not orig_img_path.exists():
                skipped += len(reports)
                continue

            # Base name for this group's files
            base_name = f"missed_{analysis_id}_{orig_img_path.stem}"

            # 1) Add Image
            try:
                zip_file.write(
                    orig_img_path,
                    arcname=f"images/{base_name}{orig_img_path.suffix}",
                )
            except Exception as e:
                print(f"Skipping missed detection {analysis_id} image read err: {e}")
                skipped += len(reports)
                continue

            # 2) Create YOLO txt file (one per analysis, but handles multiple missed labels safely)
            # Since missed detections DO NOT have bounding boxes, we output a blank box (0.5 0.5 1.0 1.0 or similar)
            # OR typically for classification/detection missed augmentation, we might supply no bbox. 
            # But YOLO format REQUIRES a bbox.
            # Best practice for object detection missed bounding boxes is to manually label later, 
            # so we'll provide the class_id with dummy bbox (0.5 0.5 0.1 0.1) that acts as a placeholder.
            # We'll use a very small center box to indicate it needs manual bounding box sizing.
            label_lines = []
            for rep in reports:
                class_id = get_yolo_class_id(rep.missed_label)
                # Format: class_id x_center y_center width height
                # Using dummy center point (0.5, 0.5) with tiny box (0.01, 0.01)
                label_lines.append(f"{class_id} 0.500000 0.500000 0.010000 0.010000\n")

            label_content = "".join(label_lines)
            zip_file.writestr(f"labels/{base_name}.txt", label_content)

            exported += len(reports)

    zip_buffer.seek(0)
    return zip_buffer, exported, skipped
