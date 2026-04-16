"""API endpoint for missed detection reports.

POST /api/v1/missed-detection
  - Input: JSON {analysis_id, missed_label, tkpi_food_id?, note?}
  - Response: {ok, message}
"""

import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.missed_detection import MissedDetection
from app.models.yolo_tkpi_mapping import YoloTkpiMapping
from app.storage.files import copy_image_for_missed_detection

logger = logging.getLogger(__name__)

router = APIRouter()


class MissedDetectionRequest(BaseModel):
    analysis_id: int
    missed_label: str  # YOLO label that was missed
    tkpi_food_id: Optional[int] = None
    note: Optional[str] = None


class MissedDetectionResponse(BaseModel):
    ok: bool
    message: str = "Missed detection reported"


@router.post("", response_model=MissedDetectionResponse)
async def report_missed_detection(
    request: MissedDetectionRequest,
    db: Session = Depends(get_db),
):
    """
    Report that the model failed to detect a food item that was manually added.
    Only records if the missed_label matches a known YOLO class in the mapping table.
    """
    # 1) Validate analysis exists
    analysis = db.execute(
        select(Analysis).where(Analysis.id == request.analysis_id)
    ).scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {request.analysis_id} not found")

    # 2) Check if label is a known YOLO class
    label_lower = request.missed_label.lower().strip()
    
    # Auto-resolve YOLO label if the user selected a TKPI food that maps to one
    if request.tkpi_food_id:
        mapping_by_tkpi = db.execute(
            select(YoloTkpiMapping).where(YoloTkpiMapping.tkpi_food_id == request.tkpi_food_id)
        ).scalars().first()
        if mapping_by_tkpi:
            label_lower = mapping_by_tkpi.yolo_label

    mapping = db.execute(
        select(YoloTkpiMapping).where(YoloTkpiMapping.yolo_label == label_lower)
    ).scalar_one_or_none()

    if not mapping:
        # Not a known YOLO class — skip silently (user added something not in model)
        return MissedDetectionResponse(
            ok=True,
            message=f"Label '{label_lower}' or TKPI ID '{request.tkpi_food_id}' is not a known YOLO class, skipped"
        )

    # 3) Avoid duplicates: same analysis + same label
    existing = db.execute(
        select(MissedDetection).where(
            MissedDetection.analysis_id == request.analysis_id,
            MissedDetection.missed_label == label_lower,
        )
    ).scalar_one_or_none()

    if existing:
        return MissedDetectionResponse(
            ok=True,
            message=f"Already reported '{label_lower}' for analysis {request.analysis_id}"
        )

    # 4) Copy image dan save
    image_filename = None
    if analysis.image_path:
        try:
            copied_path = copy_image_for_missed_detection(analysis.image_path)
            image_filename = Path(copied_path).name
            logger.info(f"Missed detection image copied: {copied_path}")
        except Exception as e:
            # Gambar tidak wajib — log warning tapi tetap lanjut
            logger.warning(f"Could not copy image for missed detection (analysis={request.analysis_id}): {e}")

    record = MissedDetection(
        analysis_id=request.analysis_id,
        missed_label=label_lower,
        tkpi_food_id=request.tkpi_food_id,
        note=request.note,
        image_filename=image_filename,
    )
    db.add(record)
    db.commit()

    logger.info(
        f"Missed detection reported: analysis={request.analysis_id}, "
        f"label={label_lower}, image={'yes' if image_filename else 'no'}"
    )

    return MissedDetectionResponse(
        ok=True,
        message=f"Reported missed detection: '{label_lower}'"
    )
