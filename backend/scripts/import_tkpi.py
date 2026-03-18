#!/usr/bin/env python3
"""CLI wrapper for TKPI CSV import using shared service.

Usage:
    python scripts/import_tkpi.py data/tkpi_seed.csv
    python scripts/import_tkpi.py data/tkpi_seed.csv --dry-run
"""

import sys
from pathlib import Path

# Add backend root to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.services.tkpi_import_service import import_csv_from_text


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_tkpi.py <path/to/tkpi.csv> [--dry-run]")
        print("Example: python scripts/import_tkpi.py data/tkpi_seed.csv")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    if not csv_path.exists():
        print(f"❌ File not found: {csv_path}")
        sys.exit(1)

    # Read file
    csv_text = csv_path.read_text(encoding="utf-8-sig")

    print(f"📥 Importing TKPI data from: {csv_path}")
    if dry_run:
        print("🔍 DRY-RUN mode — no DB writes")

    db = SessionLocal()
    try:
        result = import_csv_from_text(
            csv_text, db, filename=csv_path.name, dry_run=dry_run
        )

        # Print summary
        mode = "DRY-RUN" if result.dry_run else "COMMIT"
        print(f"\n{'='*50}")
        print(f"✅ Import complete ({mode})")
        print(f"   Rows total   : {result.rows_total}")
        print(f"   Processed    : {result.processed_count}")
        print(f"   Inserted     : {result.inserted_count}")
        print(f"   Updated      : {result.updated_count}")
        print(f"   Skipped      : {result.skipped_count}")
        print(f"   Errors       : {result.errors_count}")
        print(f"   Warnings     : {result.warnings_count}")

        if result.errors:
            print(f"\n❌ ERRORS:")
            for e in result.errors[:50]:
                code = e.get("tkpi_code") or "?"
                print(f"   Row {e['row_number']}: [{code}] {e['message']}")

        if result.warnings:
            print(f"\n⚠️  WARNINGS:")
            for w in result.warnings[:50]:
                print(f"   Row {w['row_number']}: [{w['tkpi_code']}] {w['message']}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Import failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
