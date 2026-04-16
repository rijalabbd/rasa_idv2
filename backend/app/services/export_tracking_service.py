"""Export tracking service.

Provides shared logic for tracking which records have been exported,
preventing duplicate data when uploading to Roboflow.

Uses LEFT JOIN ... IS NULL pattern (not NOT IN) to avoid silent failures
when subquery contains NULLs.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_, delete
from sqlalchemy.orm import Session

from app.models.export_log import ExportLog
from app.models.feedback import Feedback
from app.models.class_request import ClassRequest
from app.models.missed_detection import MissedDetection

logger = logging.getLogger(__name__)

# Valid source types
SOURCE_TYPES = ("feedback", "class_request", "missed_detection", "combined")

# Map source_type -> model class + ID column
_SOURCE_MAP = {
    "feedback": (Feedback, Feedback.id),
    "class_request": (ClassRequest, ClassRequest.id),
    "missed_detection": (MissedDetection, MissedDetection.id),
}


def _validate_source_type(source_type: str) -> None:
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"Invalid source_type: {source_type}. Must be one of {SOURCE_TYPES}")


def get_unexported_ids(db: Session, source_type: str) -> list[int]:
    """Return IDs of records that have NEVER been exported.

    Uses LEFT JOIN ... IS NULL pattern to avoid NOT IN pitfalls.
    """
    _validate_source_type(source_type)

    if source_type == "combined":
        # Combined tracks feedback + class_request separately
        return []

    model_cls, id_col = _SOURCE_MAP[source_type]

    # LEFT JOIN export_log ON (source_type match AND source_id match)
    # WHERE export_log.id IS NULL → never exported
    stmt = (
        select(id_col)
        .outerjoin(
            ExportLog,
            and_(
                ExportLog.source_type == source_type,
                ExportLog.source_id == id_col,
            ),
        )
        .where(ExportLog.id.is_(None))
        .order_by(id_col)
    )

    return [row[0] for row in db.execute(stmt).all()]


def get_all_ids(db: Session, source_type: str) -> list[int]:
    """Return all record IDs for a source type."""
    _validate_source_type(source_type)

    if source_type == "combined":
        return []

    _, id_col = _SOURCE_MAP[source_type]
    return [row[0] for row in db.execute(select(id_col).order_by(id_col)).all()]


def generate_batch_id() -> str:
    """Generate a unique batch ID for an export session."""
    return str(uuid.uuid4())


def mark_exported(
    db: Session,
    source_type: str,
    source_ids: list[int],
    batch_id: str,
) -> int:
    """Log exported record IDs after ZIP is successfully built.

    Returns the number of records marked.
    """
    _validate_source_type(source_type)

    if not source_ids:
        return 0

    now = datetime.now(timezone.utc)
    entries = [
        ExportLog(
            batch_id=batch_id,
            source_type=source_type,
            source_id=sid,
            exported_at=now,
        )
        for sid in source_ids
    ]

    db.bulk_save_objects(entries)
    db.commit()

    logger.info(f"Marked {len(entries)} {source_type} records as exported (batch {batch_id[:8]}…)")
    return len(entries)


def undo_last_export(db: Session, source_type: str) -> dict:
    """Delete the most recent export batch for a source type.

    Returns dict with batch_id and count of reverted records.
    """
    _validate_source_type(source_type)

    # Find the latest batch_id for this source_type
    latest = db.execute(
        select(ExportLog.batch_id)
        .where(ExportLog.source_type == source_type)
        .order_by(ExportLog.exported_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not latest:
        return {"batch_id": None, "reverted": 0}

    # Delete all entries for that batch
    result = db.execute(
        delete(ExportLog).where(
            and_(
                ExportLog.source_type == source_type,
                ExportLog.batch_id == latest,
            )
        )
    )
    db.commit()

    count = result.rowcount
    logger.info(f"Undid export batch {latest[:8]}… for {source_type}: {count} records reverted")
    return {"batch_id": latest, "reverted": count}


def get_export_summary(db: Session) -> dict:
    """Return per-source export counts for dashboard badges.

    Returns:
        {
            "feedback":         {"new": 23, "total": 150, "last_exported_at": "..."},
            "class_request":    {"new": 5,  "total": 40,  "last_exported_at": "..."},
            "missed_detection": {"new": 12, "total": 30,  "last_exported_at": null},
        }
    """
    summary = {}

    for source_type, (model_cls, id_col) in _SOURCE_MAP.items():
        total = db.execute(select(func.count(id_col))).scalar() or 0

        new_count = len(get_unexported_ids(db, source_type))

        last_exported = db.execute(
            select(ExportLog.exported_at)
            .where(ExportLog.source_type == source_type)
            .order_by(ExportLog.exported_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        summary[source_type] = {
            "new": new_count,
            "total": total,
            "last_exported_at": last_exported.isoformat() if last_exported else None,
        }

    return summary
