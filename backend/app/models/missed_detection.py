from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
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

    # Filename of the copied image in missed_detection/images/ (added for export independence)
    image_filename = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    analysis = relationship("Analysis", back_populates="missed_detections")
    tkpi_food = relationship("TKPIFood")

    def __repr__(self) -> str:
        return f"<MissedDetection(id={self.id}, label='{self.missed_label}', analysis={self.analysis_id})>"
