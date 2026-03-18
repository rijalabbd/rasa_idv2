"""add_image_filename_to_feedback

Revision ID: a1b2c3d4e5f6
Revises: 9f507186c225
Create Date: 2026-01-19 18:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9f507186c225'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add image_filename column to feedback table
    op.add_column('feedback', sa.Column('image_filename', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('feedback', 'image_filename')
