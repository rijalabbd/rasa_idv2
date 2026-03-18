"""DB hardening: FK rules, indexes, audit_log types

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6g7h8i9
Create Date: 2026-02-20 15:10:00

Fixes:
  1) class_requests.analysis_id → ON DELETE SET NULL
  2) yolo_tkpi_mapping.tkpi_food_id → ON DELETE RESTRICT
  3) Add indexes on class_requests (analysis_id, status, is_exported)
  4) admin_audit_log.meta: json → jsonb
  5) admin_audit_log.created_at: timestamp → timestamptz
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1) Fix FK: class_requests.analysis_id → ON DELETE SET NULL ────────
    op.execute("""
        ALTER TABLE class_requests
        DROP CONSTRAINT IF EXISTS class_requests_analysis_id_fkey
    """)
    op.execute("""
        ALTER TABLE class_requests
        ADD CONSTRAINT class_requests_analysis_id_fkey
        FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE SET NULL
    """)

    # ── 2) Fix FK: yolo_tkpi_mapping.tkpi_food_id → ON DELETE RESTRICT ───
    op.execute("""
        ALTER TABLE yolo_tkpi_mapping
        DROP CONSTRAINT IF EXISTS yolo_tkpi_mapping_tkpi_food_id_fkey
    """)
    op.execute("""
        ALTER TABLE yolo_tkpi_mapping
        ADD CONSTRAINT yolo_tkpi_mapping_tkpi_food_id_fkey
        FOREIGN KEY (tkpi_food_id) REFERENCES tkpi_foods(id) ON DELETE RESTRICT
    """)

    # ── 3) Add missing indexes on class_requests ─────────────────────────
    op.create_index("ix_class_requests_analysis_id", "class_requests", ["analysis_id"])
    op.create_index("ix_class_requests_status", "class_requests", ["status"])
    op.create_index("ix_class_requests_is_exported", "class_requests", ["is_exported"])

    # ── 4) admin_audit_log.meta: json → jsonb ────────────────────────────
    op.execute("""
        ALTER TABLE admin_audit_log
        ALTER COLUMN meta TYPE jsonb USING meta::jsonb
    """)

    # ── 5) admin_audit_log.created_at: timestamp → timestamptz ───────────
    op.execute("""
        ALTER TABLE admin_audit_log
        ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC'
    """)


def downgrade() -> None:
    # 5) Revert created_at to timestamp
    op.execute("""
        ALTER TABLE admin_audit_log
        ALTER COLUMN created_at TYPE timestamp USING created_at AT TIME ZONE 'UTC'
    """)

    # 4) Revert meta to json
    op.execute("""
        ALTER TABLE admin_audit_log
        ALTER COLUMN meta TYPE json USING meta::json
    """)

    # 3) Drop indexes
    op.drop_index("ix_class_requests_is_exported", "class_requests")
    op.drop_index("ix_class_requests_status", "class_requests")
    op.drop_index("ix_class_requests_analysis_id", "class_requests")

    # 2) Revert yolo_tkpi_mapping FK to NO ACTION
    op.execute("ALTER TABLE yolo_tkpi_mapping DROP CONSTRAINT IF EXISTS yolo_tkpi_mapping_tkpi_food_id_fkey")
    op.execute("""
        ALTER TABLE yolo_tkpi_mapping
        ADD CONSTRAINT yolo_tkpi_mapping_tkpi_food_id_fkey
        FOREIGN KEY (tkpi_food_id) REFERENCES tkpi_foods(id)
    """)

    # 1) Revert class_requests FK to NO ACTION
    op.execute("ALTER TABLE class_requests DROP CONSTRAINT IF EXISTS class_requests_analysis_id_fkey")
    op.execute("""
        ALTER TABLE class_requests
        ADD CONSTRAINT class_requests_analysis_id_fkey
        FOREIGN KEY (analysis_id) REFERENCES analyses(id)
    """)
