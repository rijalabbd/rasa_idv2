"""Hardening TKPI: trgm index and check constraint

Revision ID: 3c4d5e6f7a8b
Revises: 8c9d0e1f2a3b
Create Date: 2026-02-15 11:51:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c4d5e6f7a8b'
down_revision: Union[str, None] = '8c9d0e1f2a3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pg_trgm extension for similarity search (ILIKE)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # 2. Add GIN index on name using trgm ops
    # Note: postgresql_ops={"name": "gin_trgm_ops"} is the SQLAlchemy way, but raw SQL is safer for op.execute
    op.execute("CREATE INDEX IF NOT EXISTS ix_tkpi_foods_name_trgm ON tkpi_foods USING gin (name gin_trgm_ops)")

    # 3. Add CHECK constraint: tkpi_code must not be empty string
    op.execute("ALTER TABLE tkpi_foods ADD CONSTRAINT ck_tkpi_code_not_empty CHECK (tkpi_code IS NULL OR tkpi_code <> '')")


def downgrade() -> None:
    op.execute("ALTER TABLE tkpi_foods DROP CONSTRAINT ck_tkpi_code_not_empty")
    op.execute("DROP INDEX IF EXISTS ix_tkpi_foods_name_trgm")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
