"""Add trigram index for tkpi_code

Revision ID: d4e5f6g7h8i9
Revises: 3c4d5e6f7a8b
Create Date: 2026-02-15 11:55:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, None] = '3c4d5e6f7a8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add GIN index on tkpi_code using trgm ops for fast ILIKE search
    op.execute("CREATE INDEX IF NOT EXISTS ix_tkpi_foods_tkpi_code_trgm ON tkpi_foods USING gin (tkpi_code gin_trgm_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tkpi_foods_tkpi_code_trgm")
