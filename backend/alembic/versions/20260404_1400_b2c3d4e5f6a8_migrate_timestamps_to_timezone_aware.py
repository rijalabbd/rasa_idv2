"""migrate_timestamps_to_timezone_aware

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-04-04 14:00:00.000000

Migrates created_at columns in analyses, feedback, and missed_detections
from DateTime (naive) with Python-side default=datetime.utcnow to
DateTime(timezone=True) with server_default=func.now().

This ensures:
  - All timestamps are timezone-aware (UTC)
  - Defaults are handled by PostgreSQL, not Python
  - Consistent with other tables (class_requests, export_log, etc.)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a8'
down_revision: Union[str, None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables and columns to migrate
_TARGETS = [
    ("analyses", "created_at"),
    ("feedback", "created_at"),
    ("missed_detections", "created_at"),
]


def upgrade() -> None:
    """
    For each target table:
      1. ALTER column type from TIMESTAMP → TIMESTAMPTZ (timezone-aware)
      2. SET server_default to now() so new rows get UTC timestamps from DB
    
    Existing data is preserved. PostgreSQL interprets existing naive timestamps
    as UTC when casting to TIMESTAMPTZ.
    """
    for table, column in _TARGETS:
        # Step 1: Change column type to timezone-aware
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=False,
            # PostgreSQL will treat existing TIMESTAMP values as UTC
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )

        # Step 2: Set server_default (replaces Python-side default)
        op.alter_column(
            table,
            column,
            server_default=sa.func.now(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )


def downgrade() -> None:
    """
    Revert: TIMESTAMPTZ → TIMESTAMP, remove server_default.
    Note: downgrade loses timezone info from any timestamps stored after upgrade.
    """
    for table, column in _TARGETS:
        # Step 1: Remove server_default
        op.alter_column(
            table,
            column,
            server_default=None,
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )

        # Step 2: Revert column type to naive DateTime
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
