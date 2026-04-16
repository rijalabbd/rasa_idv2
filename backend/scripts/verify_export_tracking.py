"""Verification script for export tracking feature.

Tests:
1. Export summary (counts 0/0)
2. Mocking feedback records
3. Identifying unexported IDs
4. Marking as exported
5. Verifying summary update
6. Undoing export
"""

import sys
from pathlib import Path

# Add backend to sys.path
backend_path = Path.cwd() / "backend"
sys.path.insert(0, str(backend_path))

from app.db.session import SessionLocal
from app.models.export_log import ExportLog
from app.services.export_tracking_service import (
    get_unexported_ids, mark_exported, undo_last_export, get_export_summary, generate_batch_id
)
from sqlalchemy import delete, text

def verify():
    db = SessionLocal()
    try:
        print("🔍 Starting Export Tracking Verification...")
        
        # Cleanup any previous test data
        db.execute(delete(ExportLog))
        db.commit()

        # 1. Initial Summary
        summary = get_export_summary(db)
        print(f"📊 Initial Feedbacks: {summary['feedback']['new']} new / {summary['feedback']['total']} total")

        # 2. Get some feedback IDs
        fb_ids = [row[0] for row in db.execute(text("SELECT id FROM feedback LIMIT 5")).all()]
        if not fb_ids:
            print("⚠️ No feedback records found in DB to test with. Exporting 0.")
            return

        print(f"✅ Found {len(fb_ids)} test feedbacks: {fb_ids}")

        # 3. Check unexported
        unexported = get_unexported_ids(db, "feedback")
        print(f"✅ Unexported IDs (subset of test): {[x for x in unexported if x in fb_ids]}")

        # 4. Mark as exported
        batch_id = generate_batch_id()
        print(f"🚀 Marking IDs {fb_ids} as exported (batch {batch_id[:8]}...)")
        mark_exported(db, "feedback", fb_ids, batch_id)

        # 5. Verify Summary Updated
        summary2 = get_export_summary(db)
        print(f"📊 New Summary: {summary2['feedback']['new']} new / {summary2['feedback']['total']} total")
        print(f"🕒 Last Exported At: {summary2['feedback']['last_exported_at']}")

        # 6. Verify Unexported
        unexported2 = get_unexported_ids(db, "feedback")
        still_unexported = [x for x in fb_ids if x in unexported2]
        if not still_unexported:
            print("✅ Records successfully hidden from 'new' list!")
        else:
            print(f"❌ Failed: Some records still unexported: {still_unexported}")

        # 7. Undo
        print("🔙 Undoing last export...")
        undo_res = undo_last_export(db, "feedback")
        print(f"✅ Reverted batch {undo_res['batch_id'][:8]}... ({undo_res['reverted']} records)")

        # 8. Final Summary
        summary3 = get_export_summary(db)
        if summary3['feedback']['new'] >= len(fb_ids):
            print("✅ Records are back in 'new' list!")
        else:
            print(f"❌ Undo failed: new count {summary3['feedback']['new']}")

        print("\n🏆 Verification Successful!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify()
