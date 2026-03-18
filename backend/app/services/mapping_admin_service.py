"""Admin service for managing YOLO-TKPI mappings."""

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional, List

from app.models.yolo_tkpi_mapping import YoloTkpiMapping, NutritionStatus
from app.models.tkpi_food import TKPIFood
from app.schemas.admin_mapping import MappingResponse, MappingUpsertRequest


# UI status labels
UI_STATUS_LABELS = {
    "COCOK": "Cocok",
    "MENDEKATI": "Mendekati",
}


def list_mappings(
    db: Session,
    q: Optional[str] = None,
    limit: int = 50
) -> tuple[List[MappingResponse], int]:
    """
    List mappings with optional search.
    
    Args:
        db: Database session
        q: Optional search query for yolo_label (ilike)
        limit: Maximum results to return
    
    Returns:
        Tuple of (list of MappingResponse, total count)
    """
    # Base query with join
    stmt = (
        select(YoloTkpiMapping, TKPIFood.name)
        .join(TKPIFood, YoloTkpiMapping.tkpi_food_id == TKPIFood.id)
    )
    
    # Count query
    count_stmt = select(func.count(YoloTkpiMapping.id))
    
    # Apply search filter
    if q and q.strip():
        q_lower = f"%{q.lower().strip()}%"
        stmt = stmt.where(YoloTkpiMapping.yolo_label.ilike(q_lower))
        count_stmt = count_stmt.where(YoloTkpiMapping.yolo_label.ilike(q_lower))
    
    # Order and limit
    stmt = stmt.order_by(YoloTkpiMapping.yolo_label).limit(limit)
    
    # Execute
    results = db.execute(stmt).all()
    total = db.execute(count_stmt).scalar() or 0
    
    # Convert to response
    items = []
    for mapping, tkpi_name in results:
        items.append(MappingResponse(
            id=mapping.id,
            yolo_label=mapping.yolo_label,
            tkpi_food_id=mapping.tkpi_food_id,
            tkpi_food_name=tkpi_name,
            ui_status=mapping.ui_status.value,
            ui_status_label=UI_STATUS_LABELS.get(mapping.ui_status.value, "?"),
            ui_note=mapping.ui_note,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
        ))
    
    return items, total


def upsert_mapping(
    db: Session,
    request: MappingUpsertRequest
) -> tuple[MappingResponse, bool]:
    """
    Create or update a mapping by yolo_label.
    
    Args:
        db: Database session
        request: Upsert request data
    
    Returns:
        Tuple of (MappingResponse, is_new) - is_new=True if created, False if updated
    """
    # Check if mapping exists
    existing = db.execute(
        select(YoloTkpiMapping).where(
            YoloTkpiMapping.yolo_label == request.yolo_label
        )
    ).scalar_one_or_none()
    
    is_new = existing is None
    
    if existing:
        # Update existing
        existing.tkpi_food_id = request.tkpi_food_id
        existing.ui_status = NutritionStatus(request.ui_status)
        existing.ui_note = request.ui_note
        mapping = existing
    else:
        # Create new
        mapping = YoloTkpiMapping(
            yolo_label=request.yolo_label,
            tkpi_food_id=request.tkpi_food_id,
            ui_status=NutritionStatus(request.ui_status),
            ui_note=request.ui_note,
        )
        db.add(mapping)
    
    db.commit()
    db.refresh(mapping)
    
    # Get TKPI name
    tkpi = db.execute(
        select(TKPIFood).where(TKPIFood.id == mapping.tkpi_food_id)
    ).scalar_one_or_none()
    
    response = MappingResponse(
        id=mapping.id,
        yolo_label=mapping.yolo_label,
        tkpi_food_id=mapping.tkpi_food_id,
        tkpi_food_name=tkpi.name if tkpi else None,
        ui_status=mapping.ui_status.value,
        ui_status_label=UI_STATUS_LABELS.get(mapping.ui_status.value, "?"),
        ui_note=mapping.ui_note,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )
    
    return response, is_new


def get_mapping_by_label(db: Session, yolo_label: str) -> Optional[MappingResponse]:
    """
    Get a single mapping by yolo_label.
    
    Args:
        db: Database session
        yolo_label: The YOLO label to search for
    
    Returns:
        MappingResponse if found, None otherwise
    """
    label_lower = yolo_label.lower().strip()
    
    result = db.execute(
        select(YoloTkpiMapping, TKPIFood.name)
        .join(TKPIFood, YoloTkpiMapping.tkpi_food_id == TKPIFood.id)
        .where(YoloTkpiMapping.yolo_label == label_lower)
    ).first()
    
    if not result:
        return None
    
    mapping, tkpi_name = result
    
    return MappingResponse(
        id=mapping.id,
        yolo_label=mapping.yolo_label,
        tkpi_food_id=mapping.tkpi_food_id,
        tkpi_food_name=tkpi_name,
        ui_status=mapping.ui_status.value,
        ui_status_label=UI_STATUS_LABELS.get(mapping.ui_status.value, "?"),
        ui_note=mapping.ui_note,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )


def delete_mapping(db: Session, mapping_id: int) -> Optional[tuple[int, str]]:
    """
    Delete a mapping by ID.
    
    Args:
        db: Database session
        mapping_id: ID of the mapping to delete
    
    Returns:
        Tuple of (deleted_id, yolo_label) if found, None otherwise
    """
    mapping = db.execute(
        select(YoloTkpiMapping).where(YoloTkpiMapping.id == mapping_id)
    ).scalar_one_or_none()
    
    if not mapping:
        return None
    
    deleted_id = mapping.id
    yolo_label = mapping.yolo_label
    
    db.delete(mapping)
    db.commit()
    
    return (deleted_id, yolo_label)
