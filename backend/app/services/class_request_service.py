from sqlalchemy.orm import Session
from sqlalchemy import select
from pathlib import Path
from pathlib import Path
import datetime
from fastapi import HTTPException

from app.models.class_request import ClassRequest
from app.models.analysis import Analysis
from app.schemas.class_request import ClassRequestCreate, ClassRequestResponse
from app.storage.files import copy_image_for_class_request

def create_class_request(db: Session, request: ClassRequestCreate) -> ClassRequestResponse:
    """Create new class request."""
    try:
        stmt = select(Analysis).where(Analysis.id == request.analysis_id)
        analysis = db.execute(stmt).scalar_one_or_none()
        
        if not analysis:
            print(f"⚠️ [WARNING] Analysis {request.analysis_id} not found. Saving as ORPHAN request (Phase 1 Resilience).")
            # Set to None for orphan request
            request.analysis_id = None 
            image_path = "" # No image available for orphan
        else:
             try:
                image_path = copy_image_for_class_request(analysis.image_path)
                print(f"✅ Class request image copied: {image_path}")
             except Exception as e:
                print(f"❌ Failed to copy image: {e}")
                image_path = analysis.image_path

        class_request = ClassRequest(
            analysis_id=request.analysis_id,
            requested_label=request.requested_label,
            bbox_x1=request.bbox[0] if request.bbox and len(request.bbox) >= 4 else None,
            bbox_y1=request.bbox[1] if request.bbox and len(request.bbox) >= 4 else None,
            bbox_x2=request.bbox[2] if request.bbox and len(request.bbox) >= 4 else None,
            bbox_y2=request.bbox[3] if request.bbox and len(request.bbox) >= 4 else None,
            note=request.note or "",
            status="pending",
            is_exported=False,
            image_path=image_path
        )
        
        db.add(class_request)
        db.commit()
        db.refresh(class_request)
        
        print(f"✅ Class request created: ID={class_request.id}, label='{request.requested_label}'")
        
        return ClassRequestResponse(
            ok=True,
            id=class_request.id,
            image_path=image_path,
            status=class_request.status,
            created_at=class_request.created_at
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"🔥 CRITICAL ERROR in create_class_request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
