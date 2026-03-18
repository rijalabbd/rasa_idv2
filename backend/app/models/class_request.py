from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class ClassRequest(Base):
    __tablename__ = "class_requests"
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    requested_label = Column(String(255), nullable=False)
    bbox_x1 = Column(Float, nullable=True)
    bbox_y1 = Column(Float, nullable=True)
    bbox_x2 = Column(Float, nullable=True)
    bbox_y2 = Column(Float, nullable=True)
    note = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False, index=True)
    is_exported = Column(Boolean, default=False, nullable=False, index=True)
    image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
