from pathlib import Path
from typing import Optional
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.feedback import Feedback
from app.models.analysis import Analysis
from app.models.tkpi_food import TKPIFood
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.storage.files import copy_image_for_feedback, write_yolo_label_file
from app.core.paths import STORAGE_DIR

logger = logging.getLogger(__name__)

def _load_label_aliases() -> dict[str, str]:
    """Load label aliases from external config file.

    File: data/label_aliases.json
    Structure: { "aliases": { "old_label": "new_label", ... } }

    These map deprecated/short YOLO labels (from older models) to their
    current canonical names. Update the JSON file when model class names
    change — no code change required.
    """
    import json
    from pathlib import Path

    config_path = Path(__file__).resolve().parent.parent.parent / "data" / "label_aliases.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        aliases = data.get("aliases", {})
        logger.info("Loaded %d label aliases from %s", len(aliases), config_path.name)
        return aliases
    except FileNotFoundError:
        logger.warning("Label aliases config not found at %s, using empty aliases.", config_path)
        return {}
    except Exception as e:
        logger.warning("Failed to load label aliases: %s, using empty aliases.", e)
        return {}


# Loaded once at module import time (cached)
LEGACY_ALIASES = _load_label_aliases()


def get_dynamic_class_map() -> dict[str, int]:
    """
    Returns { 'roti_putih': 0, 'ayam_goreng': 1, ... } 
    dynamically loaded from the active YOLO model in model_manager.
    """
    try:
        from app.services.model_manager import get_model
        model, _ = get_model()
        return {name: idx for idx, name in model.names.items()}
    except Exception as e:
        logger.warning("Unable to load dynamic class map: %s", e)
        return {}


def get_yolo_class_id(predicted_label: str) -> int:
    """Resolve a predicted label to its YOLO class ID from the active model.

    Raises:
        ValueError: if the label (after alias resolution) is not present
                    in the current model's class map.
    """
    label_lower = (predicted_label or "").lower().strip()
    
    # Check alias first
    if label_lower in LEGACY_ALIASES:
        label_lower = LEGACY_ALIASES[label_lower]
        
    class_map = get_dynamic_class_map()

    if label_lower not in class_map:
        raise ValueError(
            f"Label '{predicted_label}' (resolved: '{label_lower}') "
            f"not found in active model class map. "
            f"Available classes: {list(class_map.keys())}"
        )

    return class_map[label_lower]


def generate_classes_txt() -> str:
    """Generate YOLO-compatible classes.txt content dynamically from active model."""
    class_map = get_dynamic_class_map()
    if not class_map:
        return ""
    max_class_id = max(class_map.values())
    class_names = ["unknown"] * (max_class_id + 1)
    
    for label, class_id in class_map.items():
        if class_names[class_id] == "unknown":
            class_names[class_id] = label
            
    return "\n".join(class_names)


def _pixel_bbox_to_yolo(bbox: tuple, img_w: int, img_h: int) -> str:
    """Convert pixel bbox (x1,y1,x2,y2) to YOLO format (x_center, y_center, w, h) normalized."""
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


def _get_image_dimensions(path: Path) -> tuple[int, int]:
    """Return (width, height) of an image."""
    from PIL import Image
    with Image.open(path) as img:
        return img.size


def _calculate_iou(box1: tuple[float, float, float, float], box2: tuple[float, float, float, float]) -> float:
    """Calculate Intersection over Union (IoU) of two bounding boxes (x1, y1, x2, y2)."""
    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    iou = intersection_area / float(box1_area + box2_area - intersection_area)
    return iou



def save_feedback(db: Session, request: FeedbackRequest) -> FeedbackResponse:
    """
    Transaction-safe feedback save:
    - copy image
    - db.add() feedback rows (NO commit yet)
    - create label (must succeed)
    - commit
    If any error after image copy -> rollback DB + cleanup image+label
    """
    # 1) Validate analysis
    analysis = db.execute(
        select(Analysis).where(Analysis.id == request.analysis_id)
    ).scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {request.analysis_id} not found")

    feedback_image_relpath: Optional[str] = None
    created_label_relpath: Optional[str] = None
    feedback_image_filename: Optional[str] = None

    # 2) Copy image
    try:
        feedback_image_relpath = copy_image_for_feedback(analysis.image_path)
        feedback_image_filename = Path(feedback_image_relpath).name
        logger.info("Feedback image copied: %s", feedback_image_relpath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to copy image: {str(e)}")

    # 3) Prepare YOLO items + DB rows (no commit yet)
    yolo_items = []
    saved_count = 0

    try:
        for idx, item in enumerate(request.items, 1):
            # Validate corrected_tkpi_id if provided
            if item.corrected_tkpi_id:
                tkpi = db.execute(
                    select(TKPIFood).where(TKPIFood.id == item.corrected_tkpi_id)
                ).scalar_one_or_none()
                if not tkpi:
                    raise HTTPException(
                        status_code=404,
                        detail=f"TKPI food {item.corrected_tkpi_id} not found",
                    )

            # Basic bbox validation
            if not item.bbox or len(item.bbox) < 4:
                raise HTTPException(status_code=400, detail=f"Invalid bbox for item #{idx}")

            feedback = Feedback(
                analysis_id=request.analysis_id,
                predicted_label=item.predicted_label,
                corrected_tkpi_food_id=item.corrected_tkpi_id,
                bbox_x1=item.bbox[0],
                bbox_y1=item.bbox[1],
                bbox_x2=item.bbox[2],
                bbox_y2=item.bbox[3],
                note=item.note or "",
                image_filename=feedback_image_filename,
                is_processed=False,
            )
            db.add(feedback)

            try:
                class_id = get_yolo_class_id(item.predicted_label)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Label '{item.predicted_label}' tidak dikenali oleh model aktif. "
                        f"Pastikan label sesuai dengan class yang tersedia."
                    ),
                )
            yolo_items.append((class_id, item.bbox))
            saved_count += 1

        # 4) Create label (MUST succeed)
        created_label_relpath = write_yolo_label_file(feedback_image_relpath, yolo_items)
        logger.info("Label file created: %s (%d items)", created_label_relpath, len(yolo_items))

        # 5) Commit
        db.commit()
        logger.info("Saved %d feedback items to database", saved_count)

        return FeedbackResponse(ok=True, saved=saved_count, message=f"Successfully saved {saved_count} feedback items")

    except HTTPException:
        db.rollback()
        _cleanup_feedback_files(feedback_image_relpath, created_label_relpath)
        raise

    except Exception as e:
        db.rollback()
        _cleanup_feedback_files(feedback_image_relpath, created_label_relpath)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create label file: {str(e)}. Feedback not saved.",
        )


def _cleanup_feedback_files(feedback_image_relpath: Optional[str], label_relpath: Optional[str]) -> None:
    """
    Delete feedback image + label if exist.
    """
    import os

    def safe_remove(relpath: Optional[str], desc: str):
        if not relpath:
            return
        try:
            abs_path = STORAGE_DIR / relpath
            if abs_path.exists():
                os.remove(abs_path)
                logger.info("Cleaned up feedback %s: %s", desc, relpath)
        except Exception as e:
            logger.error("Failed to cleanup %s %s: %s", desc, relpath, e)

    safe_remove(label_relpath, "label")
    safe_remove(feedback_image_relpath, "image")
