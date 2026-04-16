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


def search_tkpi_foods(
    db: Session,
    query: str,
    limit: int = 10,
    fuzzy: bool = False,
) -> List[TKPIFood]:
    """
    Search TKPI foods by name OR tkpi_code (case-insensitive).

    Args:
        db: Database session.
        query: Search string from the user.
        limit: Maximum number of results (capped at 50).
        fuzzy: When True, the query is split into whitespace-separated tokens
               and each token is matched independently (OR logic). This helps
               when the user types e.g. "tumis kangkung" but the DB only has
               "kangkung, dimasak" — the token "kangkung" will still match.
               When False (default), the original single-phrase ILIKE is used.

    Feature flag: controlled via settings.TKPI_FUZZY_SEARCH. Can also be
    overridden per-request through the API query param `?fuzzy=true/false`.
    """
    if query is None:
        return []

    clean_query = query.strip()
    if not clean_query:
        return []

    # Cap results
    safe_limit = max(1, min(int(limit or 10), 50))

    if fuzzy:
        # --- Fuzzy / token-based mode ---
        # Split into tokens, ignore very short tokens (< 2 chars)
        tokens = [t for t in clean_query.split() if len(t) >= 2]
        if not tokens:
            # Fallback: treat whole query as single token
            tokens = [clean_query]

        # Build OR condition: any token appearing in name or tkpi_code counts
        token_conditions = []
        for token in tokens:
            escaped_token = _escape_like(token)
            pat = f"%{escaped_token}%"
            token_conditions.append(
                or_(
                    TKPIFood.name.ilike(pat, escape="\\"),
                    func.coalesce(TKPIFood.tkpi_code, "").ilike(pat, escape="\\"),
                )
            )

        stmt = (
            select(TKPIFood)
            .where(or_(*token_conditions))
            .order_by(TKPIFood.name.asc())
            .limit(safe_limit)
        )
    else:
        # --- Original single-phrase mode ---
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
