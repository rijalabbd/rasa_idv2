"""create admin_audit_log table

Revision ID: 5a4b3c2d1e0f
Revises: 13d00b42ef97
Create Date: 2026-02-07 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5a4b3c2d1e0f'
down_revision = '13d00b42ef97'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('admin_audit_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(), nullable=False),
    sa.Column('meta', sa.JSON(), nullable=False),
    sa.Column('request_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_audit_log_id'), 'admin_audit_log', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_admin_audit_log_id'), table_name='admin_audit_log')
    op.drop_table('admin_audit_log')
