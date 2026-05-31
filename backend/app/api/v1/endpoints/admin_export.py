from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.combined_export_service import build_combined_export_zip
from datetime import datetime
from app.services.audit_service import AuditService
from app.core.security import get_admin_api_key

router = APIRouter()

import io
import asyncio
from typing import Tuple

def export_combined_data_threadsafe(only_new: bool) -> Tuple[bytes, str]:
    """Threadsafe wrapper to run ZIP building in its own DB session."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        zip_buffer, batch_id = build_combined_export_zip(db, only_new=only_new)
        return zip_buffer.getvalue(), batch_id
    finally:
        db.close()


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
    
    loop = asyncio.get_running_loop()
    zip_bytes, batch_id = await loop.run_in_executor(
        None,
        export_combined_data_threadsafe,
        only_new
    )
    zip_buffer = io.BytesIO(zip_bytes)
    
    filename = f"rasa_id_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Batch-ID": batch_id
        }
    )
