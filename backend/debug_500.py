from app.db.session import SessionLocal
from app.services.admin_summary_service import get_admin_summary
import traceback

try:
    db = SessionLocal()
    print("Executing get_admin_summary...")
    result = get_admin_summary(db)
    print("Success:", result)
except Exception as e:
    print("Exception occurred:")
    traceback.print_exc()
