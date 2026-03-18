from pydantic import BaseModel
from typing import List, Optional
from app.schemas.common import NutritionInfo


class DetectionTKPIInfo(BaseModel):
    """TKPI information for a detected item."""
    id: int
    name: str
    nutrition: NutritionInfo


class DetectionItem(BaseModel):
    """Single detection result with TKPI mapping and nutrition status."""
    label: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    tkpi: Optional[DetectionTKPIInfo] = None
    
    # Nutrition status for UI display
    nutrition_status: str = "BELUM_ADA"  # "COCOK" | "MENDEKATI" | "BELUM_ADA"
    nutrition_status_label: str = "Belum ada datanya"  # "Cocok" | "Mendekati" | "Belum ada datanya"
    nutrition_note: Optional[str] = None  # Note for MENDEKATI status


class DetectionResponse(BaseModel):
    """Complete detection response."""
    analysis_id: int
    inference_time_ms: float
    items: List[DetectionItem] = []  # Always list, default empty
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": 1,
                "inference_time_ms": 120.5,
                "items": [
                    {
                        "label": "nasi",
                        "confidence": 0.92,
                        "bbox": [100.0, 150.0, 300.0, 400.0],
                        "tkpi": {
                            "id": 1,
                            "name": "Nasi Putih",
                            "nutrition": {
                                "energi_kal": 180.0,
                                "protein_g": 3.5,
                                "lemak_g": 0.3,
                                "karbo_g": 40.0,
                                "serat_g": 0.3
                            }
                        },
                        "nutrition_status": "COCOK",
                        "nutrition_status_label": "Cocok",
                        "nutrition_note": None
                    }
                ]
            }
        }
