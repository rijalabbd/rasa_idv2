import io
import csv
import logging
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.feedback import Feedback
from app.models.analysis import Analysis
from app.core.paths import FEEDBACK_IMAGES_DIR, FEEDBACK_LABELS_DIR
from app.services.feedback_service import get_dynamic_class_map

logger = logging.getLogger(__name__)


def collect_feedback_data(db: Session, only_unprocessed: bool = True) -> List[Feedback]:
    stmt = select(Feedback).join(Analysis, Feedback.analysis_id == Analysis.id)

    if only_unprocessed:
        stmt = stmt.where(Feedback.is_processed == False)  # noqa: E712

    stmt = stmt.order_by(Feedback.created_at)

    result = db.execute(stmt)
    return list(result.scalars().all())


def generate_data_yaml() -> str:
    class_map = get_dynamic_class_map()
    max_class_id = max(class_map.values()) if class_map else 0
    class_names = ["unknown"] * (max_class_id + 1)

    for label, class_id in class_map.items():
        if class_names[class_id] == "unknown":
            class_names[class_id] = label

    yaml_content = f"""# YOLOv8 Dataset Configuration
# Generated: {datetime.now().isoformat()}

path: .
train: images
val: images

nc: {len(class_names)}
names:
"""
    for name in class_names:
        yaml_content += f"  - {name}\n"

    return yaml_content


def find_feedback_image(stem: str, feedback_images_dir: Path) -> Path | None:
    for ext in ["jpg", "jpeg", "png", "JPG", "JPEG", "PNG"]:
        p = feedback_images_dir / f"{stem}.{ext}"
        if p.exists():
            return p

    matches = list(feedback_images_dir.glob(f"{stem}.*"))
    return matches[0] if matches else None


def generate_metadata_csv(feedbacks: List[Feedback], analyses_map: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "feedback_id",
        "analysis_id",
        "image_relpath",
        "label_relpath",
        "predicted_label",
        "corrected_tkpi_food_id",
        "bbox_x1",
        "bbox_y1",
        "bbox_x2",
        "bbox_y2",
        "note",
        "created_at",
        "is_processed",
    ])

    for feedback in feedbacks:
        analysis = analyses_map.get(feedback.analysis_id)
        if not analysis:
            continue

        if feedback.image_filename:
            image_stem = Path(feedback.image_filename).stem
            feedback_image_path = f"feedback/images/{feedback.image_filename}"
            feedback_label_path = f"feedback/labels/{image_stem}.txt"
        elif analysis.image_path:
            image_stem = Path(analysis.image_path).stem
            image_ext = Path(analysis.image_path).suffix
            feedback_image_path = f"feedback/images/{image_stem}{image_ext}"
            feedback_label_path = f"feedback/labels/{image_stem}.txt"
        else:
            feedback_image_path = ""
            feedback_label_path = ""

        writer.writerow([
            feedback.id,
            feedback.analysis_id,
            feedback_image_path,
            feedback_label_path,
            feedback.predicted_label,
            feedback.corrected_tkpi_food_id or "",
            feedback.bbox_x1,
            feedback.bbox_y1,
            feedback.bbox_x2,
            feedback.bbox_y2,
            feedback.note or "",
            feedback.created_at.isoformat() if feedback.created_at else "",
            feedback.is_processed,
        ])

    return output.getvalue()


def build_yolo_dataset_zip(db: Session, only_unprocessed: bool = True) -> Tuple[io.BytesIO, int, int]:
    feedbacks = collect_feedback_data(db, only_unprocessed)
    logger.info("Exporting %d feedback records...", len(feedbacks))

    analysis_ids = list(set(f.analysis_id for f in feedbacks))
    analyses = db.execute(
        select(Analysis).where(Analysis.id.in_(analysis_ids))
    ).scalars().all()
    analyses_map = {a.id: a for a in analyses}

    feedback_images_dir = FEEDBACK_IMAGES_DIR
    feedback_labels_dir = FEEDBACK_LABELS_DIR

    zip_buffer = io.BytesIO()
    feedback_rows_count = 0
    exported_feedback_ids: List[int] = []
    exported_feedbacks: List[Feedback] = []

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        added_keys = set()

        for feedback in feedbacks:
            # Resolve image+label paths
            if feedback.image_filename:
                image_filename = feedback.image_filename
                image_stem = Path(image_filename).stem
                feedback_image_path = feedback_images_dir / image_filename
                feedback_label_path = feedback_labels_dir / f"{image_stem}.txt"
            else:
                analysis = analyses_map.get(feedback.analysis_id)
                if not analysis or not analysis.image_path:
                    logger.warning("Skipping feedback %d: no image_filename and no analysis image", feedback.id)
                    continue

                image_stem = Path(analysis.image_path).stem
                feedback_image_path = find_feedback_image(image_stem, feedback_images_dir)
                feedback_label_path = feedback_labels_dir / f"{image_stem}.txt"

                if not feedback_image_path:
                    logger.warning("Skipping feedback %d: image not found for stem '%s'", feedback.id, image_stem)
                    continue

            # Existence checks
            if not feedback_image_path.exists():
                logger.warning("Skipping feedback %d: image not found at %s", feedback.id, feedback_image_path)
                continue

            if not feedback_label_path.exists():
                logger.warning("Skipping feedback %d: label not found at %s", feedback.id, feedback_label_path)
                continue

            # Add image once
            img_key = feedback_image_path.name
            if img_key not in added_keys:
                zipf.write(feedback_image_path, f"dataset/images/{feedback_image_path.name}")
                added_keys.add(img_key)
                logger.debug("Added image: %s", feedback_image_path.name)

            # Add label once
            label_key = f"{image_stem}.txt"
            if label_key not in added_keys:
                zipf.write(feedback_label_path, f"dataset/labels/{image_stem}.txt")
                added_keys.add(label_key)
                logger.debug("Added label: %s.txt", image_stem)

            # Only now mark as exported in memory lists
            exported_feedback_ids.append(feedback.id)
            exported_feedbacks.append(feedback)
            feedback_rows_count += 1

        zipf.writestr("dataset/data.yaml", generate_data_yaml())
        logger.debug("Added data.yaml")

        # IMPORTANT: metadata only for exported feedbacks
        zipf.writestr("dataset/metadata.csv", generate_metadata_csv(exported_feedbacks, analyses_map))
        logger.debug("Added metadata.csv")

    unique_images_count = len([k for k in added_keys if not str(k).endswith(".txt")])

    if feedback_rows_count > 0 and only_unprocessed:
        mark_as_processed(db, exported_feedback_ids)

    zip_buffer.seek(0)
    logger.info("Export complete: %d feedback rows, %d unique images", feedback_rows_count, unique_images_count)

    return zip_buffer, feedback_rows_count, unique_images_count


def mark_as_processed(db: Session, feedback_ids: List[int]) -> None:
    if not feedback_ids:
        return

    feedbacks = db.execute(
        select(Feedback).where(Feedback.id.in_(feedback_ids))
    ).scalars().all()

    for f in feedbacks:
        f.is_processed = True

    db.commit()
    logger.info("Marked %d feedback records as processed", len(feedback_ids))
