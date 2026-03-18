"""Admin API endpoints for managing YOLO-TKPI mappings."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.admin_mapping import (
    MappingUpsertRequest,
    MappingResponse,
    MappingListResponse,
    MappingDeleteResponse,
)
from app.services.mapping_admin_service import (
    list_mappings,
    upsert_mapping,
    delete_mapping,
    get_mapping_by_label,
)
from app.services.audit_service import AuditService
from app.core.security import get_admin_api_key

router = APIRouter()


@router.get("/mappings", response_model=MappingListResponse)
async def get_mappings(
    q: str = Query(None, description="Search yolo_label (ilike)"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    db: Session = Depends(get_db),
):
    """
    List YOLO-TKPI mappings with optional search.
    
    - **q**: Optional search query for yolo_label
    - **limit**: Maximum results (1-200, default 50)
    """
    items, total = list_mappings(db, q=q, limit=limit)
    return MappingListResponse(items=items, total=total)


@router.get("/mappings/by-label/{yolo_label}", response_model=MappingResponse)
async def get_mapping_by_label_endpoint(
    yolo_label: str = Path(..., description="YOLO label to lookup"),
    db: Session = Depends(get_db),
):
    """
    Get a single mapping by yolo_label.
    
    Useful for loading existing mapping data into edit form.
    """
    mapping = get_mapping_by_label(db, yolo_label)
    
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping untuk label '{yolo_label}' tidak ditemukan")
    
    return mapping


@router.post("/mappings", response_model=dict)
async def create_or_update_mapping(
    request: Request,
    request_body: MappingUpsertRequest,
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key)
):
    """
    Create or update a YOLO-TKPI mapping (UPSERT).
    
    If yolo_label already exists, the mapping is UPDATED.
    If not, a new mapping is CREATED.
    
    Body:
    - **yolo_label**: YOLO detection label (will be normalized to lowercase)
    - **tkpi_food_id**: ID of the TKPI food entry
    - **ui_status**: "COCOK" or "MENDEKATI"
    - **ui_note**: Optional note for UI display
    """
    try:
        mapping, is_new = upsert_mapping(db, request_body)
        action_type = "CREATED" if is_new else "UPDATED"
        
        AuditService(db).log_action(
            "ADMIN_MAPPING_UPSERT", 
            request, 
            admin_key, 
            meta={"label": request_body.yolo_label, "action": action_type}
        )
        action = "ditambahkan" if is_new else "diperbarui"
        return {
            "ok": True,
            "is_new": is_new,
            "message": f"Mapping berhasil {action}",
            "mapping": mapping.model_dump(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/mappings/{mapping_id}", response_model=MappingDeleteResponse)
async def remove_mapping(
    request: Request,
    mapping_id: int,
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key)
):
    """
    """
    result = delete_mapping(db, mapping_id)
    
    audit = AuditService(db)
    
    if not result:
        audit.log_action("ADMIN_MAPPING_DELETE", request, admin_key, meta={"mapping_id": mapping_id, "result": "not_found"}, status_code=404)
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    deleted_id, yolo_label = result
    audit.log_action("ADMIN_MAPPING_DELETE", request, admin_key, meta={"mapping_id": mapping_id, "label": yolo_label, "result": "success"})
    return MappingDeleteResponse(
        ok=True,
        deleted_id=deleted_id,
        yolo_label=yolo_label,
    )

