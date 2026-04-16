"""Admin YOLO dataset export endpoints.

GET /admin/export/yolo/feedback       → feedback_dataset.zip
GET /admin/export/yolo/class-requests → class_requests_dataset.zip
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.services.audit_service import AuditService
from app.core.security import get_admin_api_key
from app.services.yolo_feedback_export_service import build_yolo_feedback_zip
from app.services.yolo_class_request_export_service import build_yolo_class_request_zip

router = APIRouter()


@router.get("/export/yolo/feedback")
async def export_yolo_feedback(
    request: Request,
    mode: str = "new",
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key),
):
    """Export feedback data as YOLO-ready dataset ZIP."""
    audit = AuditService(db)
    audit.log_action(f"ADMIN_EXPORT_YOLO_FEEDBACK_MODE_{mode.upper()}", request, admin_key)

    only_new = (mode == "new")
    zip_buffer, exported, skipped, batch_id = build_yolo_feedback_zip(db, only_new=only_new)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"feedback_dataset_{ts}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Count": str(exported),
            "X-Skip-Count": str(skipped),
            "X-Export-Batch-ID": batch_id,
        },
    )


@router.get("/export/yolo/class-requests")
async def export_yolo_class_requests(
    request: Request,
    mode: str = "new",
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key),
):
    """Export class request data as YOLO-ready dataset ZIP."""
    audit = AuditService(db)
    audit.log_action(f"ADMIN_EXPORT_YOLO_CLASS_REQUESTS_MODE_{mode.upper()}", request, admin_key)

    only_new = (mode == "new")
    zip_buffer, exported, skipped, batch_id = build_yolo_class_request_zip(db, only_new=only_new)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"class_requests_dataset_{ts}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Count": str(exported),
            "X-Skip-Count": str(skipped),
            "X-Export-Batch-ID": batch_id,
        },
    )


from app.services.yolo_missed_detection_export_service import build_yolo_missed_detection_zip

@router.get("/export/yolo/missed")
async def export_yolo_missed_detections(
    request: Request,
    mode: str = "new",
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key),
):
    """Export missed detection data as YOLO-ready dataset ZIP."""
    audit = AuditService(db)
    audit.log_action(f"ADMIN_EXPORT_YOLO_MISSED_MODE_{mode.upper()}", request, admin_key)

    only_new = (mode == "new")
    zip_buffer, exported, skipped, batch_id = build_yolo_missed_detection_zip(db, only_new=only_new)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"missed_detections_dataset_{ts}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Count": str(exported),
            "X-Skip-Count": str(skipped),
            "X-Export-Batch-ID": batch_id,
        },
    )


@router.get("/export/summary")
async def get_export_summary_api(
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key),
):
    """Get per-source export counts for dashboard badges."""
    from app.services.export_tracking_service import get_export_summary
    return get_export_summary(db)


@router.post("/export/undo/{source_type}")
async def undo_export_api(
    source_type: str,
    request: Request,
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key),
):
    """Reverts the last export batch for the given source type."""
    from app.services.export_tracking_service import undo_last_export
    audit = AuditService(db)
    audit.log_action(f"ADMIN_EXPORT_UNDO_{source_type.upper()}", request, admin_key)
    
    return undo_last_export(db, source_type)
