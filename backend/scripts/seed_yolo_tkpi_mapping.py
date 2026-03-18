"""
Seed script for YOLO-TKPI mapping.

Run from backend directory:
    python scripts/seed_yolo_tkpi_mapping.py

Logic:
- COCOK: Label is an exact ingredient match in TKPI
- MENDEKATI: Label is processed food, maps to base ingredient + note
- If TKPI not found: skip (will show "Belum ada datanya" in UI)
"""

import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models.yolo_tkpi_mapping import YoloTkpiMapping, NutritionStatus
from app.models.tkpi_food import TKPIFood
from sqlalchemy import select, delete


DEFAULT_NOTE = "Angka gizi belum termasuk minyak/bumbu."


def seed_yolo_tkpi_mappings():
    """Insert/update YOLO-TKPI mappings."""
    
    db = SessionLocal()
    
    # Correct mappings following the pattern:
    # - Bahan langsung -> TKPI bahan = COCOK (no note)
    # - Olahan -> TKPI bahan dasar = MENDEKATI (with note)
    mappings = [
        # COCOK (exact ingredient match)
        ("nasi", "Nasi Putih", "COCOK", None),
        ("tempe", "Tempe", "COCOK", None),
        ("tahu", "Tahu", "COCOK", None),
        ("kangkung", "Kangkung", "COCOK", None),
        ("telur", "Telur Ayam", "COCOK", None),
        
        # MENDEKATI (processed food -> base ingredient)
        ("ayam", "Daging Ayam", "MENDEKATI", DEFAULT_NOTE),
        ("ayam_goreng", "Daging Ayam", "MENDEKATI", DEFAULT_NOTE),
        ("tumis_kangkung", "Kangkung", "MENDEKATI", DEFAULT_NOTE),
        ("sayur", "Sayur (Umum)", "MENDEKATI", DEFAULT_NOTE),
        ("ikan", "Ikan", "MENDEKATI", DEFAULT_NOTE),
        ("daging", "Daging Sapi", "MENDEKATI", DEFAULT_NOTE),
    ]
    
    # Build TKPI lookup
    tkpi_foods = {}
    for food in db.execute(select(TKPIFood)).scalars():
        tkpi_foods[food.name] = food.id
    
    # Clear existing and insert fresh
    deleted = db.execute(delete(YoloTkpiMapping))
    print(f"Deleted {deleted.rowcount} old mappings")
    
    inserted = 0
    skipped = 0
    
    for yolo_label, tkpi_name, status, note in mappings:
        tkpi_id = tkpi_foods.get(tkpi_name)
        if not tkpi_id:
            print(f"⚠️  SKIP {yolo_label}: TKPI '{tkpi_name}' not found")
            skipped += 1
            continue
        
        m = YoloTkpiMapping(
            yolo_label=yolo_label,
            tkpi_food_id=tkpi_id,
            ui_status=NutritionStatus(status),
            ui_note=note
        )
        db.add(m)
        print(f"✅ {yolo_label} -> {tkpi_name} ({status})")
        inserted += 1
    
    db.commit()
    db.close()
    
    print(f"\n📊 Summary: {inserted} inserted, {skipped} skipped")


if __name__ == "__main__":
    seed_yolo_tkpi_mappings()
