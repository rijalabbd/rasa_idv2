"""Service for looking up YOLO-TKPI mappings."""

from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, Tuple

from app.models.yolo_tkpi_mapping import YoloTkpiMapping, NutritionStatus
from app.models.tkpi_food import TKPIFood


# Default note for MENDEKATI status
DEFAULT_MENDEKATI_NOTE = "Angka gizi belum termasuk minyak/bumbu."

# UI status labels
UI_STATUS_LABELS = {
    "COCOK": "Cocok",
    "MENDEKATI": "Mendekati",
    "BELUM_ADA": "Belum ada datanya",
}


def find_mapping_by_label(
    db: Session, 
    yolo_label: str
) -> Tuple[Optional[TKPIFood], str, str, Optional[str]]:
    """
    Find TKPI food and status by YOLO label using the mapping table.
    
    Args:
        db: Database session
        yolo_label: Label from YOLO detection (e.g., "ayam_goreng")
    
    Returns:
        Tuple of (tkpi_food, nutrition_status, nutrition_status_label, nutrition_note)
        
        If mapping found:
          - tkpi_food: TKPIFood object
          - nutrition_status: "COCOK" or "MENDEKATI"
          - nutrition_status_label: "Cocok" or "Mendekati"
          - nutrition_note: Note for UI (or None for COCOK)
        
        If mapping not found:
          - tkpi_food: None
          - nutrition_status: "BELUM_ADA"
          - nutrition_status_label: "Belum ada datanya"
          - nutrition_note: None
    """
    # Lookup mapping by label (case-insensitive)
    label_lower = yolo_label.lower().strip()
    
    stmt = (
        select(YoloTkpiMapping)
        .where(YoloTkpiMapping.yolo_label == label_lower)
    )
    mapping = db.execute(stmt).scalar_one_or_none()
    
    if not mapping:
        # No mapping found
        return (
            None,
            "BELUM_ADA",
            UI_STATUS_LABELS["BELUM_ADA"],
            None
        )
    
    # Get TKPI food
    tkpi_food = db.execute(
        select(TKPIFood).where(TKPIFood.id == mapping.tkpi_food_id)
    ).scalar_one_or_none()
    
    if not tkpi_food:
        # Mapping exists but TKPI food deleted (shouldn't happen)
        return (
            None,
            "BELUM_ADA",
            UI_STATUS_LABELS["BELUM_ADA"],
            None
        )
    
    # Get status values
    status = mapping.ui_status.value  # "COCOK" or "MENDEKATI"
    status_label = UI_STATUS_LABELS.get(status, "Belum ada datanya")
    
    # Get note (use default for MENDEKATI if not set)
    note = None
    if status == "MENDEKATI":
        note = mapping.ui_note or DEFAULT_MENDEKATI_NOTE
    
    return (tkpi_food, status, status_label, note)
