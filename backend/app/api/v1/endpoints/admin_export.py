from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.combined_export_service import build_combined_export_zip
from datetime import datetime
from app.services.audit_service import AuditService
from app.core.security import get_admin_api_key

router = APIRouter()

@router.get("/export-zip")
async def export_combined_data(
    request: Request,
    mode: str = "new",
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key)
):
    """
    Export all data (Feedback + Class Requests) as JSONL in a ZIP file.
    Core requirement for Phase 1A.
    """
    audit = AuditService(db)
    audit.log_action(f"ADMIN_EXPORT_COMBINED_MODE_{mode.upper()}", request, admin_key)
    
    only_new = (mode == "new")
    zip_buffer, batch_id = build_combined_export_zip(db, only_new=only_new)
    
    filename = f"rasa_id_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Batch-ID": batch_id
        }
    )
