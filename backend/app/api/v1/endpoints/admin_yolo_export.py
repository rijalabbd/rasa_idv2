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
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key),
):
    """Export feedback data as YOLO-ready dataset ZIP."""
    audit = AuditService(db)
    audit.log_action("ADMIN_EXPORT_YOLO_FEEDBACK", request, admin_key)

    zip_buffer, exported, skipped = build_yolo_feedback_zip(db)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"feedback_dataset_{ts}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Count": str(exported),
            "X-Skip-Count": str(skipped),
        },
    )


@router.get("/export/yolo/class-requests")
async def export_yolo_class_requests(
    request: Request,
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key),
):
    """Export class request data as YOLO-ready dataset ZIP."""
    audit = AuditService(db)
    audit.log_action("ADMIN_EXPORT_YOLO_CLASS_REQUESTS", request, admin_key)

    zip_buffer, exported, skipped = build_yolo_class_request_zip(db)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"class_requests_dataset_{ts}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Count": str(exported),
            "X-Skip-Count": str(skipped),
        },
    )


from app.services.yolo_missed_detection_export_service import build_yolo_missed_detection_zip

@router.get("/export/yolo/missed")
async def export_yolo_missed_detections(
    request: Request,
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key),
):
    """Export missed detection data as YOLO-ready dataset ZIP."""
    audit = AuditService(db)
    audit.log_action("ADMIN_EXPORT_YOLO_MISSED", request, admin_key)

    zip_buffer, exported, skipped = build_yolo_missed_detection_zip(db)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"missed_detections_dataset_{ts}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Count": str(exported),
            "X-Skip-Count": str(skipped),
        },
    )

