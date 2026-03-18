from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from app.models.tkpi_food import TKPIFood


def _escape_like(term: str) -> str:
    """
    Escape % and _ for SQL LIKE/ILIKE patterns.
    We use backslash as escape char.
    """
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search_tkpi_foods(db: Session, query: str, limit: int = 10) -> List[TKPIFood]:
    """
    Search TKPI foods by name OR tkpi_code (case-insensitive).
    Uses ILIKE with escaped patterns and bound parameters.
    """
    if query is None:
        return []

    clean_query = query.strip()
    if not clean_query:
        return []

    # Limit max results to 50 for safety; ensure positive
    safe_limit = max(1, min(int(limit or 10), 50))

    escaped = _escape_like(clean_query)
    pattern = f"%{escaped}%"

    # tkpi_code is nullable => coalesce to empty string to avoid null issues
    stmt = (
        select(TKPIFood)
        .where(
            or_(
                TKPIFood.name.ilike(pattern, escape="\\"),
                func.coalesce(TKPIFood.tkpi_code, "").ilike(pattern, escape="\\"),
            )
        )
        .order_by(TKPIFood.name.asc())
        .limit(safe_limit)
    )

    result = db.execute(stmt)
    return list(result.scalars().all())


def get_tkpi_food_by_id(db: Session, food_id: int) -> Optional[TKPIFood]:
    """
    Get TKPI food by ID.
    """
    stmt = select(TKPIFood).where(TKPIFood.id == food_id)
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def find_tkpi_by_label(db: Session, label: str) -> Optional[TKPIFood]:
    """
    Find TKPI food by detection label (simple name matching).
    Basic implementation; returns first match.
    """
    if label is None:
        return None

    clean_label = label.strip()
    if not clean_label:
        return None

    escaped = _escape_like(clean_label)
    pattern = f"%{escaped}%"

    stmt = (
        select(TKPIFood)
        .where(TKPIFood.name.ilike(pattern, escape="\\"))
        .order_by(TKPIFood.name.asc())
        .limit(1)
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()
