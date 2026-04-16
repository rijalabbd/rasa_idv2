"""Public endpoint: list foods the system can currently detect.

GET /api/v1/detectable-foods
  - No auth required (public info)
  - Returns list of YOLO-detectable foods with their TKPI food names
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.yolo_tkpi_mapping import YoloTkpiMapping
from app.models.tkpi_food import TKPIFood

router = APIRouter()


@router.get("/detectable-foods")
async def get_detectable_foods(db: Session = Depends(get_db)):
    """
    Return a list of food names the YOLO model can currently detect.
    Derived from active YOLO-TKPI mappings.
    """
    rows = db.execute(
        select(
            YoloTkpiMapping.yolo_label,
            TKPIFood.id.label("tkpi_food_id"),
            TKPIFood.name,
            TKPIFood.tkpi_code,
        )
        .join(TKPIFood, YoloTkpiMapping.tkpi_food_id == TKPIFood.id)
        .order_by(TKPIFood.name.asc())
    ).all()

    foods = [
        {
            "yolo_label": row.yolo_label,
            "tkpi_food_id": row.tkpi_food_id,
            "name": row.name,
            "tkpi_code": row.tkpi_code,
        }
        for row in rows
    ]

    return {
        "total": len(foods),
        "foods": foods,
    }
