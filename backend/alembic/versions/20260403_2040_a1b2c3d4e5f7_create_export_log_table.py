"""create_export_log_table

Revision ID: a1b2c3d4e5f7
Revises: d1e2f3a4b5c6
Create Date: 2026-04-03 20:40:00.000000

Adds export_log table for tracking which records have been exported
to prevent duplicate data when uploading to Roboflow.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'export_log' not in existing_tables:
        op.create_table(
            'export_log',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('batch_id', sa.String(36), nullable=False),
            sa.Column('source_type', sa.String(30), nullable=False),
            sa.Column('source_id', sa.Integer(), nullable=False),
            sa.Column('exported_at', sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint('source_type', 'source_id', 'batch_id',
                                name='uq_export_log_source_batch'),
        )
        op.create_index('ix_export_log_batch', 'export_log', ['batch_id'])
        op.create_index('ix_export_log_source', 'export_log', ['source_type', 'source_id'])
        op.create_index('ix_export_log_exported_at', 'export_log', ['exported_at'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'export_log' in inspector.get_table_names():
        op.drop_table('export_log')
