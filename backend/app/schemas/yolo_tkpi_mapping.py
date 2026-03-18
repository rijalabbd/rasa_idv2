"""Pydantic schemas for YOLO-TKPI mapping."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NutritionStatusResponse(BaseModel):
    """Nutrition status for UI display."""
    nutrition_status: str  # "COCOK" | "MENDEKATI" | "BELUM_ADA"
    nutrition_status_label: str  # "Cocok" | "Mendekati" | "Belum ada datanya"
    nutrition_note: Optional[str] = None


class YoloTkpiMappingBase(BaseModel):
    """Base schema for mapping."""
    yolo_label: str
    tkpi_food_id: int
    ui_status: str = "COCOK"
    ui_note: Optional[str] = None


class YoloTkpiMappingCreate(YoloTkpiMappingBase):
    """Schema for creating a mapping."""
    pass


class YoloTkpiMappingUpdate(BaseModel):
    """Schema for updating a mapping."""
    tkpi_food_id: Optional[int] = None
    ui_status: Optional[str] = None
    ui_note: Optional[str] = None


class YoloTkpiMappingResponse(YoloTkpiMappingBase):
    """Schema for mapping response."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # UI-friendly fields
    nutrition_status_label: Optional[str] = None
    tkpi_food_name: Optional[str] = None
    
    class Config:
        from_attributes = True
