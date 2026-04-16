"""Script untuk membersihkan data Feedback lama yang predicted_label-nya tidak canonical."""
import sys
from pathlib import Path

# Setup path agar bisa import backend module
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from app.db.session import SessionLocal

# Import ALL models to avoid SQLAlchemy relationship mapper cascading errors
from app.models.feedback import Feedback
from app.models.analysis import Analysis
from app.models.tkpi_food import TKPIFood
from app.models.detection import Detection
from app.models.class_request import ClassRequest
from app.models.missed_detection import MissedDetection
from app.models.export_log import ExportLog

from sqlalchemy import text


def main():
    db = SessionLocal()
    try:
        print("🔍 Mencari data lama dengan predicted_label 'nasi' atau 'tempe'...")
        
        # Cek data
        legacy_data = db.query(Feedback).filter(Feedback.predicted_label.in_(['nasi', 'tempe'])).all()
        
        if not legacy_data:
            print("✅ Bersih! Tidak ada data lama yang menggunakan label non-canonical.")
            return

        print(f"⚠️ Ditemukan {len(legacy_data)} data lama.")
        
        # UPDATE opsi (Lebih direkomendasikan daripada hapus)
        # Nasi -> Nasi Putih
        # Tempe -> Tempe Goreng
        updated_nasi = db.query(Feedback).filter(Feedback.predicted_label == 'nasi').update({"predicted_label": "nasi_putih"})
        updated_tempe = db.query(Feedback).filter(Feedback.predicted_label == 'tempe').update({"predicted_label": "tempe_goreng"})
        
        # Jika benar-benar ingin HAPUS, uncomment baris di bawah dan comment update di atas:
        # deleted = db.query(Feedback).filter(Feedback.predicted_label.in_(['nasi', 'tempe'])).delete()
        
        db.commit()
        
        print(f"✅ Selesai! Berhasil memperbaiki (update) {updated_nasi + updated_tempe} data lama ke standar yang benar.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
