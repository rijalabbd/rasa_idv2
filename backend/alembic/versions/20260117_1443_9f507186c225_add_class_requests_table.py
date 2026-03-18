"""add_class_requests_table

Revision ID: 9f507186c225
Revises: 36d9e6337e27
Create Date: 2026-01-17 14:43:22.727563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f507186c225'
down_revision: Union[str, None] = '36d9e6337e27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'class_requests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('analysis_id', sa.Integer(), sa.ForeignKey('analyses.id'), nullable=False),
        sa.Column('requested_label', sa.String(255), nullable=False),
        sa.Column('bbox_x1', sa.Float(), nullable=True),
        sa.Column('bbox_y1', sa.Float(), nullable=True),
        sa.Column('bbox_x2', sa.Float(), nullable=True),
        sa.Column('bbox_y2', sa.Float(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default=sa.text("'pending'"), nullable=False),
        sa.Column('is_exported', sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column('image_path', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('class_requests')
