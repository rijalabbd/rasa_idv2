from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.feedback import Feedback
from app.models.analysis import Analysis
from app.models.tkpi_food import TKPIFood
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.storage.files import copy_image_for_feedback, write_yolo_label_file
from app.core.paths import STORAGE_DIR


# YOLO class mapping: predicted_label -> class_id
YOLO_CLASS_MAP = {
    "nasi": 0,
    "ayam": 1,
    "ikan": 2,
    "tempe": 3,
    "tahu": 4,
    "sayur": 5,
    "telur": 6,
    "daging": 7,
    "udang": 8,
    "cumi": 9,
    # Add more mappings as needed
}


def get_yolo_class_id(predicted_label: str) -> int:
    label_lower = (predicted_label or "").lower().strip()
    class_id = YOLO_CLASS_MAP.get(label_lower, 0)

    if class_id == 0 and label_lower not in YOLO_CLASS_MAP:
        print(f"⚠️  Warning: Label '{predicted_label}' not in YOLO_CLASS_MAP, using class_id=0")

    return class_id


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
        print(f"✅ Feedback image copied: {feedback_image_relpath}")
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

            class_id = get_yolo_class_id(item.predicted_label)
            yolo_items.append((class_id, item.bbox))
            saved_count += 1

        # 4) Create label (MUST succeed)
        created_label_relpath = write_yolo_label_file(feedback_image_relpath, yolo_items)
        print(f"✅ Label file created: {created_label_relpath} ({len(yolo_items)} items)")

        # 5) Commit
        db.commit()
        print(f"✅ Saved {saved_count} feedback items to database")

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
                print(f"🗑️  Cleaned up feedback {desc}: {relpath}")
        except Exception as e:
            print(f"⚠️  Failed to cleanup {desc} {relpath}: {e}")

    safe_remove(label_relpath, "label")
    safe_remove(feedback_image_relpath, "image")
