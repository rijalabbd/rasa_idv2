"""Add tkpi_code to tkpi_foods

Revision ID: 7b8c9d0e1f2a
Revises: 5a4b3c2d1e0f
Create Date: 2026-02-15 11:22:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b8c9d0e1f2a'
down_revision: Union[str, None] = '5a4b3c2d1e0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add column (nullable for now — NOT NULL after all rows are filled)
    op.add_column('tkpi_foods', sa.Column('tkpi_code', sa.String(32), nullable=True))

    # 2. Index for fast lookup
    op.create_index('ix_tkpi_foods_tkpi_code', 'tkpi_foods', ['tkpi_code'], unique=False)

    # 3. Unique constraint (allows upsert ON CONFLICT)
    op.create_unique_constraint('uq_tkpi_foods_tkpi_code', 'tkpi_foods', ['tkpi_code'])


def downgrade() -> None:
    op.drop_constraint('uq_tkpi_foods_tkpi_code', 'tkpi_foods', type_='unique')
    op.drop_index('ix_tkpi_foods_tkpi_code', table_name='tkpi_foods')
    op.drop_column('tkpi_foods', 'tkpi_code')
