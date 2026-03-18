"""YOLO to TKPI food mapping model."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class NutritionStatus(str, enum.Enum):
    """Nutrition matching status (internal values)."""
    COCOK = "COCOK"          # Exact match
    MENDEKATI = "MENDEKATI"  # Approximate match (proxy)


class YoloTkpiMapping(Base):
    """
    Mapping between YOLO detection labels and TKPI food entries.
    
    Attributes:
        yolo_label: The label from YOLO detection (e.g., "ayam_goreng")
        tkpi_food_id: FK to tkpi_foods table
        ui_status: Status shown in UI ("COCOK" or "MENDEKATI")
        ui_note: Optional note for UI (e.g., "Angka gizi belum termasuk minyak/bumbu.")
    """
    
    __tablename__ = "yolo_tkpi_mapping"
    
    id = Column(Integer, primary_key=True)
    yolo_label = Column(String(100), unique=True, nullable=False, index=True)
    tkpi_food_id = Column(Integer, ForeignKey("tkpi_foods.id", ondelete="RESTRICT"), nullable=False)
    ui_status = Column(
        Enum(NutritionStatus, name="nutrition_status_enum"),
        nullable=False,
        default=NutritionStatus.COCOK
    )
    ui_note = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    tkpi_food = relationship("TKPIFood", backref="yolo_mappings")
    
    def __repr__(self) -> str:
        return f"<YoloTkpiMapping(yolo_label='{self.yolo_label}', status='{self.ui_status}')>"
    
    @property
    def ui_status_label(self) -> str:
        """Get UI-friendly status label."""
        labels = {
            NutritionStatus.COCOK: "Cocok",
            NutritionStatus.MENDEKATI: "Mendekati",
        }
        return labels.get(self.ui_status, "Belum ada datanya")
