from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ClassRequestCreate(BaseModel):
    analysis_id: int
    requested_label: str = Field(..., min_length=1, max_length=255)
    bbox: Optional[list[float]] = None
    note: Optional[str] = None

class ClassRequestResponse(BaseModel):
    ok: bool
    id: int
    image_path: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
