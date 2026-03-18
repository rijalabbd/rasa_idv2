"""Make nutrisi columns nullable in tkpi_foods

Revision ID: 8c9d0e1f2a3b
Revises: 7b8c9d0e1f2a
Create Date: 2026-02-15 11:29:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c9d0e1f2a3b'
down_revision: Union[str, None] = '7b8c9d0e1f2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('tkpi_foods', 'energi_kal', existing_type=sa.Float(), nullable=True)
    op.alter_column('tkpi_foods', 'protein_g', existing_type=sa.Float(), nullable=True)
    op.alter_column('tkpi_foods', 'lemak_g', existing_type=sa.Float(), nullable=True)
    op.alter_column('tkpi_foods', 'karbo_g', existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    # Set NULL values to 0.0 before re-adding NOT NULL
    op.execute("UPDATE tkpi_foods SET energi_kal = 0.0 WHERE energi_kal IS NULL")
    op.execute("UPDATE tkpi_foods SET protein_g = 0.0 WHERE protein_g IS NULL")
    op.execute("UPDATE tkpi_foods SET lemak_g = 0.0 WHERE lemak_g IS NULL")
    op.execute("UPDATE tkpi_foods SET karbo_g = 0.0 WHERE karbo_g IS NULL")

    op.alter_column('tkpi_foods', 'energi_kal', existing_type=sa.Float(), nullable=False)
    op.alter_column('tkpi_foods', 'protein_g', existing_type=sa.Float(), nullable=False)
    op.alter_column('tkpi_foods', 'lemak_g', existing_type=sa.Float(), nullable=False)
    op.alter_column('tkpi_foods', 'karbo_g', existing_type=sa.Float(), nullable=False)
