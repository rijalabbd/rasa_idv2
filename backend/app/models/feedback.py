from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Feedback(Base):
    """User feedback for detection corrections."""
    
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Feedback data
    predicted_label = Column(String(100), nullable=False)
    corrected_tkpi_food_id = Column(Integer, ForeignKey("tkpi_foods.id", ondelete="SET NULL"), nullable=True)
    
    # Bounding box from user (may be adjusted)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    
    # Optional note from user
    note = Column(Text, nullable=True)
    
    # Feedback image filename (stored separately from analysis)
    image_filename = Column(String(255), nullable=True)
    
    # Processing status
    is_processed = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="feedbacks")
    corrected_tkpi = relationship("TKPIFood")
    
    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, predicted='{self.predicted_label}', processed={self.is_processed})>"
