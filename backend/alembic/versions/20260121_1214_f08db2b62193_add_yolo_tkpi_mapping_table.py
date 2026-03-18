"""add yolo_tkpi_mapping table

Revision ID: f08db2b62193
Revises: a1b2c3d4e5f6
Create Date: 2026-01-21 12:14:44.963181

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f08db2b62193'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create yolo_tkpi_mapping table
    op.create_table('yolo_tkpi_mapping',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('yolo_label', sa.String(length=100), nullable=False),
        sa.Column('tkpi_food_id', sa.Integer(), nullable=False),
        sa.Column('ui_status', sa.Enum('COCOK', 'MENDEKATI', name='nutrition_status_enum'), nullable=False),
        sa.Column('ui_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tkpi_food_id'], ['tkpi_foods.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_yolo_tkpi_mapping_id'), 'yolo_tkpi_mapping', ['id'], unique=False)
    op.create_index(op.f('ix_yolo_tkpi_mapping_yolo_label'), 'yolo_tkpi_mapping', ['yolo_label'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_yolo_tkpi_mapping_yolo_label'), table_name='yolo_tkpi_mapping')
    op.drop_index(op.f('ix_yolo_tkpi_mapping_id'), table_name='yolo_tkpi_mapping')
    op.drop_table('yolo_tkpi_mapping')
    op.execute("DROP TYPE IF EXISTS nutrition_status_enum")
