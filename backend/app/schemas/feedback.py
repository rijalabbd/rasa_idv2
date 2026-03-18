from pydantic import BaseModel
from typing import List, Optional


class FeedbackItemRequest(BaseModel):
    """Single feedback item."""
    bbox: List[float]  # [x1, y1, x2, y2]
    predicted_label: str
    corrected_tkpi_id: Optional[int] = None
    note: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Batch feedback submission."""
    analysis_id: int
    items: List[FeedbackItemRequest]
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": 1,
                "items": [
                    {
                        "bbox": [100, 150, 300, 400],
                        "predicted_label": "nasi",
                        "corrected_tkpi_id": 5,
                        "note": "Should be nasi goreng, not nasi putih"
                    }
                ]
            }
        }


class FeedbackResponse(BaseModel):
    """Feedback submission response."""
    ok: bool
    saved: int
    message: str = "Feedback saved successfully"
