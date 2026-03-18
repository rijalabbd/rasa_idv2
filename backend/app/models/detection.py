from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Detection(Base):
    """Individual detection result from YOLO model."""
    
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Detection data
    label = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Bounding box coordinates (absolute pixels)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    
    # TKPI mapping (nullable if no match found)
    tkpi_food_id = Column(Integer, ForeignKey("tkpi_foods.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="detections")
    tkpi_food = relationship("TKPIFood")
    
    def __repr__(self) -> str:
        return f"<Detection(id={self.id}, label='{self.label}', conf={self.confidence:.2f})>"
