"""Admin dashboard API endpoints for summary, model status, and model upload."""

from fastapi import APIRouter, Depends, File, UploadFile, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.admin_summary_service import get_admin_summary
from app.services.admin_model_service import save_uploaded_model
from app.services import model_manager
from app.services.audit_service import AuditService
from app.core.security import get_admin_api_key
from app.core.rate_limit import rate_limit_upload

router = APIRouter()

# ---------------------------------------------------------------------------
# Model Classes Endpoint
# ---------------------------------------------------------------------------

@router.get("/model/classes")
def get_model_classes():
    """Return list of YOLO class IDs and names from the active model.
    Returns a JSON with a loaded flag, source identifier, and classes array.
    """
    from app.services.model_manager import get_class_names
    classes = get_class_names()
    return {
        "loaded": len(classes) > 0,
        "source": "active.pt",
        "classes": classes,
    }


@router.get("/summary")
async def get_summary(db: Session = Depends(get_db)):
    """
    Get admin dashboard summary counts.

    Returns:
        JSON: {
            "feedback_total": int,
            "feedback_pending": int,
            "class_requests_total": int,
            "class_requests_pending": int
        }
    """
    return get_admin_summary(db)


@router.get("/model/status")
async def get_model_status():
    """
    Get current active model status.

    Returns:
        JSON: {
            "active_model": str or null,
            "sha256": str or null,
            "size_bytes": int or null,
            "loaded_at": str or null (ISO),
            "ready": bool
        }
    """
    return model_manager.get_status()


@router.post("/model/upload", dependencies=[Depends(rate_limit_upload)])
async def upload_model(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key)
):
    """
    Upload and activate a new YOLO model.

    Performs atomic swap: write to active.pt.tmp then os.replace -> active.pt.
    Validates extension (.pt) and size (1 MB – 200 MB).
    """
    audit = AuditService(db)
    request_id = getattr(request.state, "request_id", "")
    try:
        result = save_uploaded_model(file, request_id=request_id)
        audit.log_action(
            action="MODEL_UPLOAD",
            request=request,
            admin_key=admin_key,
            meta={
                "filename": result.get("filename", file.filename),
                "size_bytes": result.get("size_bytes"),
                "loaded_at": result.get("loaded_at"),
                "sha256": result.get("sha256"),
                "result": "success",
            },
        )
        return result
    except Exception as e:
        audit.log_action(
            action="MODEL_UPLOAD",
            request=request,
            admin_key=admin_key,
            meta={
                "filename": file.filename,
                "result": "failed",
                "error": str(e),
            },
            status_code=getattr(e, "status_code", 500),
            error_code="UPLOAD_FAILED",
        )
        raise
