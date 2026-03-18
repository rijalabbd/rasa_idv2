from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Analysis(Base):
    """Analysis record for each detection session."""
    
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True)
    image_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    model_version = Column(String(100), nullable=False, default="best.pt")
    conf_threshold = Column(Float, nullable=False, default=0.5)
    
    # Relationships
    detections = relationship("Detection", back_populates="analysis", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="analysis", cascade="all, delete-orphan")
    missed_detections = relationship("MissedDetection", back_populates="analysis", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, image='{self.image_path}')>"
