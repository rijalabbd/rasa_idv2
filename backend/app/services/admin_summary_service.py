"""Admin summary service for dashboard statistics."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.models.class_request import ClassRequest


def get_admin_summary(db: Session) -> dict:
    """
    Get admin dashboard summary counts.
    
    Returns:
        dict: {
            "feedback_total": int,
            "feedback_pending": int,  # is_processed = false
            "class_requests_total": int,
            "class_requests_pending": int  # is_exported = false
        }
    """
    # Feedback counts
    feedback_total = db.query(func.count(Feedback.id)).scalar() or 0
    feedback_pending = db.query(func.count(Feedback.id)).filter(
        Feedback.is_processed == False
    ).scalar() or 0
    
    # Class request counts
    class_requests_total = db.query(func.count(ClassRequest.id)).scalar() or 0
    class_requests_pending = db.query(func.count(ClassRequest.id)).filter(
        ClassRequest.is_exported == False
    ).scalar() or 0
    
    # Missed detection counts (all are exportable right away)
    from app.models.missed_detection import MissedDetection
    missed_detections_total = db.query(func.count(MissedDetection.id)).scalar() or 0
    
    return {
        "feedback_total": feedback_total,
        "feedback_pending": feedback_pending,
        "class_requests_total": class_requests_total,
        "class_requests_pending": class_requests_pending,
        "missed_detections_total": missed_detections_total
    }
