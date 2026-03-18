from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.admin_class_request_export_service import build_class_request_zip

router = APIRouter()

@router.get("/class-requests/export")
async def export_class_requests_dataset(
    only_unexported: bool = Query(True, description="Only export unexported requests"),
    db: Session = Depends(get_db)
):
    """Export class requests as YOLOv8-ready dataset ZIP."""
    zip_buffer, request_count, unique_images = build_class_request_zip(db, only_unexported)
    
    filename = f"class_requests_{request_count}requests_{unique_images}images.zip"
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


from app.models.class_request import ClassRequest
from pydantic import BaseModel
from typing import Optional
from fastapi import HTTPException, status

class ClassRequestUpdate(BaseModel):
    status: str
    admin_note: Optional[str] = None

@router.patch("/class-requests/{request_id}")
async def update_class_request_status(
    request_id: int,
    update_data: ClassRequestUpdate,
    db: Session = Depends(get_db)
):
    """
    Update class request status (APPROVED/REJECTED) and note.
    """
    req = db.query(ClassRequest).filter(ClassRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if update_data.status not in ["pending", "APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    req.status = update_data.status
    if update_data.admin_note is not None:
        req.note = update_data.admin_note
        
    db.commit()
    db.refresh(req)
    
    return {"ok": True, "request": {"id": req.id, "status": req.status, "note": req.note}}
