from pydantic import BaseModel
from typing import Optional, List


class NutritionInfo(BaseModel):
    """Nutrition information (macronutrients only)."""
    energi_kal: float
    protein_g: float
    lemak_g: float
    karbo_g: float
    serat_g: Optional[float] = None


class BoundingBox(BaseModel):
    """Bounding box coordinates [x1, y1, x2, y2]."""
    bbox: List[float]  # [x1, y1, x2, y2]
    
    class Config:
        json_schema_extra = {
            "example": {
                "bbox": [100.0, 150.0, 300.0, 400.0]
            }
        }
