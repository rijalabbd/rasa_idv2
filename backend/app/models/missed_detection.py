from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class MissedDetection(Base):
    """
    Records when user manually adds a food that the model SHOULD have detected
    but didn't. Used to collect training data for model improvement.
    """

    __tablename__ = "missed_detections"

    id = Column(Integer, primary_key=True)
    analysis_id = Column(
        Integer,
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The YOLO label the model SHOULD have detected (e.g. "tahu_goreng")
    missed_label = Column(String(100), nullable=False, index=True)

    # TKPI food selected by user
    tkpi_food_id = Column(
        Integer,
        ForeignKey("tkpi_foods.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Optional note from user
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    analysis = relationship("Analysis")
    tkpi_food = relationship("TKPIFood")

    def __repr__(self) -> str:
        return f"<MissedDetection(id={self.id}, label='{self.missed_label}', analysis={self.analysis_id})>"
