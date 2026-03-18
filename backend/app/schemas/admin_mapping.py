"""Pydantic schemas for admin mapping CRUD."""

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class MappingUpsertRequest(BaseModel):
    """Request schema for creating/updating a mapping."""
    yolo_label: str
    tkpi_food_id: int
    ui_status: str = "COCOK"  # "COCOK" or "MENDEKATI"
    ui_note: Optional[str] = None
    
    @field_validator('yolo_label')
    @classmethod
    def normalize_label(cls, v: str) -> str:
        """Normalize yolo_label: lowercase + strip."""
        return v.lower().strip()
    
    @field_validator('ui_status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate ui_status is valid."""
        valid = ['COCOK', 'MENDEKATI']
        v_upper = v.upper()
        if v_upper not in valid:
            raise ValueError(f'ui_status must be one of: {valid}')
        return v_upper


class MappingResponse(BaseModel):
    """Response schema for a mapping."""
    id: int
    yolo_label: str
    tkpi_food_id: int
    tkpi_food_name: Optional[str] = None
    ui_status: str
    ui_status_label: str  # UI-friendly: "Cocok" / "Mendekati"
    ui_note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MappingListResponse(BaseModel):
    """Response schema for list of mappings."""
    items: list[MappingResponse]
    total: int


class MappingDeleteResponse(BaseModel):
    """Response schema for delete operation."""
    ok: bool
    deleted_id: int
    yolo_label: str
