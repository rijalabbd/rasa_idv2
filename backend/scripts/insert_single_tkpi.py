import sys
from pathlib import Path

# Add backend root to path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from app.db.session import SessionLocal
from app.models.tkpi_food import TKPIFood

def main():
    db = SessionLocal()
    try:
        # Check if already exists
        code = "DP003"
        existing = db.query(TKPIFood).filter(TKPIFood.tkpi_code == code).first()
        if existing:
            print(f"⚠️  Data with code {code} already exists: {existing.name}")
            return

        new_food = TKPIFood(
            tkpi_code=code,
            name="Buncis, rebus",
            energi_kal=30.0,
            protein_g=2.2,
            lemak_g=0.2,
            karbo_g=6.4,
            serat_g=1.5
        )
        db.add(new_food)
        db.commit()
        print(f"✅ Successfully inserted: {new_food.name} ({code})")
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to insert data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
