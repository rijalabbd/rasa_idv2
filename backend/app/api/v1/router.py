from fastapi import APIRouter, Depends
from app.api.v1.endpoints import (
    health, tkpi, detection, feedback, missed_detection,
    admin_feedback, class_requests, admin_class_requests, 
    admin_dashboard, admin_mappings, admin_export, admin_yolo_export,
    admin_tkpi_import
)
from app.core.security import get_admin_api_key
from app.core.rate_limit import rate_limit_detect, rate_limit_feedback

router = APIRouter()

router.include_router(health.router, tags=["Health"])
router.include_router(tkpi.router, prefix="/tkpi", tags=["TKPI"])
router.include_router(detection.router, prefix="/detect", tags=["Detection"], dependencies=[Depends(rate_limit_detect)])
router.include_router(feedback.router, prefix="/feedback", tags=["Feedback"], dependencies=[Depends(rate_limit_feedback)])
router.include_router(missed_detection.router, prefix="/missed-detection", tags=["Feedback"])
router.include_router(class_requests.router, prefix="/class-request", tags=["Class Requests"])
# Normalized path alias
router.include_router(class_requests.router, prefix="/class-requests", tags=["Class Requests"])

# Admin Routes (Protected)
router.include_router(admin_feedback.router, prefix="/admin", tags=["Admin"], dependencies=[Depends(get_admin_api_key)])
router.include_router(admin_class_requests.router, prefix="/admin", tags=["Admin"], dependencies=[Depends(get_admin_api_key)])
router.include_router(admin_dashboard.router, prefix="/admin", tags=["Admin"], dependencies=[Depends(get_admin_api_key)])
router.include_router(admin_mappings.router, prefix="/admin", tags=["Admin"], dependencies=[Depends(get_admin_api_key)])
router.include_router(admin_export.router, prefix="/admin", tags=["Admin"], dependencies=[Depends(get_admin_api_key)])
router.include_router(admin_yolo_export.router, prefix="/admin", tags=["Admin"], dependencies=[Depends(get_admin_api_key)])
router.include_router(admin_tkpi_import.router, prefix="/admin", tags=["Admin"], dependencies=[Depends(get_admin_api_key)])

