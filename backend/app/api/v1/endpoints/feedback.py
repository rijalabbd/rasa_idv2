from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.feedback_service import save_feedback
from app.schemas.feedback import FeedbackRequest, FeedbackResponse


router = APIRouter()


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Submit user feedback for detection corrections.
    
    Process:
    1. Validate analysis exists
    2. Save feedback records to database
    3. Copy analysis image to feedback directory
    4. Generate YOLO label files for training
    """
    return save_feedback(db, request)
