"""Export tracking log model.

Tracks which records have been exported, when, and in which batch.
One central table for all source types: feedback, class_request, missed_detection.
"""

from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, Index
from sqlalchemy.sql import func

from app.db.base import Base


class ExportLog(Base):
    """Log of exported records for deduplication across download sessions."""

    __tablename__ = "export_log"

    id = Column(Integer, primary_key=True)
    batch_id = Column(String(36), nullable=False, index=True)
    source_type = Column(String(30), nullable=False)  # 'feedback' | 'class_request' | 'missed_detection' | 'combined'
    source_id = Column(Integer, nullable=False)
    exported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("source_type", "source_id", "batch_id", name="uq_export_log_source_batch"),
        Index("ix_export_log_source", "source_type", "source_id"),
        Index("ix_export_log_exported_at", "exported_at"),
    )

    def __repr__(self) -> str:
        return f"<ExportLog(batch={self.batch_id[:8]}…, type={self.source_type}, id={self.source_id})>"
