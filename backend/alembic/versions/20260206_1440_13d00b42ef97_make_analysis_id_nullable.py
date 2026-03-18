"""make_analysis_id_nullable

Revision ID: 13d00b42ef97
Revises: f08db2b62193
Create Date: 2026-02-06 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13d00b42ef97'
down_revision: Union[str, None] = 'f08db2b62193'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('class_requests', 'analysis_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade() -> None:
    op.alter_column('class_requests', 'analysis_id',
               existing_type=sa.INTEGER(),
               nullable=False)
