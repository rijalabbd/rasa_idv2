"""create_missed_detections_and_add_image_filename

Revision ID: d1e2f3a4b5c6
Revises: c48c7e7159e4
Create Date: 2026-03-26 15:35:00.000000

Perbaikan:
1. CREATE TABLE missed_detections jika belum ada (migration c48c7e7159e4 tidak melakukannya)
2. Tambah kolom image_filename ke tabel missed_detections agar gambar tersimpan secara independen

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c48c7e7159e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Buat tabel missed_detections jika belum ada
    # (pada DB lama tabel mungkin sudah ada karena dibuat manual via SQL)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'missed_detections' not in existing_tables:
        op.create_table(
            'missed_detections',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('analysis_id', sa.Integer(),
                      sa.ForeignKey('analyses.id', ondelete='CASCADE'),
                      nullable=False, index=True),
            sa.Column('missed_label', sa.String(100), nullable=False, index=True),
            sa.Column('tkpi_food_id', sa.Integer(),
                      sa.ForeignKey('tkpi_foods.id', ondelete='SET NULL'),
                      nullable=True),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('image_filename', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
        )
    else:
        # 2) Tabel sudah ada — hanya tambah kolom image_filename jika belum ada
        existing_cols = {c['name'] for c in inspector.get_columns('missed_detections')}
        if 'image_filename' not in existing_cols:
            op.add_column(
                'missed_detections',
                sa.Column('image_filename', sa.String(500), nullable=True)
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'missed_detections' in existing_tables:
        existing_cols = {c['name'] for c in inspector.get_columns('missed_detections')}
        if 'image_filename' in existing_cols:
            op.drop_column('missed_detections', 'image_filename')
