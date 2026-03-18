from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.admin_export_service import build_yolo_dataset_zip

router = APIRouter()


@router.get("/feedback/export")
async def export_feedback_dataset(
    only_unprocessed: bool = Query(True, description="Only export unprocessed feedback"),
    db: Session = Depends(get_db)
):
    """
    Export feedback as YOLOv8-ready dataset ZIP.
    
    Returns a ZIP file containing:
    - dataset/images/ - feedback images
    - dataset/labels/ - YOLO format labels
    - dataset/data.yaml - YOLOv8 configuration
    - dataset/metadata.csv - feedback metadata
    
    Query Parameters:
    - only_unprocessed: If True (default), only export feedback where is_processed=False
                       and mark them as processed after export.
    
    Response:
    - ZIP file download with Content-Disposition: attachment
    """
    # TODO: Add authentication check
    # Example: X-ADMIN-KEY header validation
    # if request.headers.get("X-ADMIN-KEY") != settings.ADMIN_KEY:
    #     raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Build ZIP dataset
    zip_buffer, feedback_rows, unique_images = build_yolo_dataset_zip(db, only_unprocessed)
    
    # ✅ FIX 2: More informative filename
    filename = f"feedback_dataset_{feedback_rows}rows_{unique_images}images.zip"
    
    # Return as streaming response
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


from app.models.feedback import Feedback
from pydantic import BaseModel
from fastapi import HTTPException, status

class FeedbackUpdate(BaseModel):
    is_processed: bool

@router.patch("/feedback/{feedback_id}")
async def update_feedback_status(
    feedback_id: int,
    update_data: FeedbackUpdate,
    db: Session = Depends(get_db)
):
    """
    Update feedback processed status.
    """
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
        
    fb.is_processed = update_data.is_processed
    db.commit()
    db.refresh(fb)
    
    return {"ok": True, "feedback": {"id": fb.id, "is_processed": fb.is_processed}}
