from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.class_request import ClassRequestCreate, ClassRequestResponse
from app.services.class_request_service import create_class_request

router = APIRouter()

@router.post("", response_model=ClassRequestResponse)
async def request_new_class(
    request: ClassRequestCreate,
    db: Session = Depends(get_db)
):
    """Request a new food class not in YOLO model."""
    return create_class_request(db, request)
