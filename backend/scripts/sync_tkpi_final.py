import csv
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, delete
from app.db.session import SessionLocal
from app.models.tkpi_food import TKPIFood
from app.models.yolo_tkpi_mapping import YoloTkpiMapping

def sync_tkpi_final():
    db = SessionLocal()
    csv_file = Path("data/tkpi_final.csv")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        final_data = list(reader)
        
    final_codes = [row['tkpi_code'] for row in final_data]
    
    print("=== SYNCING TKPI FOODS ===")
    print(f"Total data in CSV: {len(final_data)}")
    
    processed_ids = []
    
    for row in final_data:
        code = row['tkpi_code'].strip()
        name = row['name'].strip()
        energi = float(row['energi_kal'])
        protein = float(row['protein_g'])
        lemak = float(row['lemak_g'])
        karbo = float(row['karbo_g'])
        serat = float(row['serat_g'])
        
        # 1) Cari berdasarkan tkpi_code
        existing = db.execute(select(TKPIFood).where(TKPIFood.tkpi_code == code)).scalar_one_or_none()
        
        # 2) Kalau tidak ketemu by code, cari by name persis
        if not existing:
            existing = db.execute(select(TKPIFood).where(TKPIFood.name == name)).scalar_one_or_none()
            
        if existing:
            existing.tkpi_code = code
            existing.name = name
            existing.energi_kal = energi
            existing.protein_g = protein
            existing.lemak_g = lemak
            existing.karbo_g = karbo
            existing.serat_g = serat
            processed_ids.append(existing.id)
            print(f"[UPDATE] {code} - {name}")
        else:
            food = TKPIFood(
                tkpi_code=code,
                name=name,
                energi_kal=energi,
                protein_g=protein,
                lemak_g=lemak,
                karbo_g=karbo,
                serat_g=serat
            )
            db.add(food)
            db.flush()  # get ID
            processed_ids.append(food.id)
            print(f"[INSERT] {code} - {name}")
            
    db.commit()
    
    # SEKARANG: Hapus semua TKPI yang bukan dari 15 data final
    print("\n=== CLEANUP OLD/GARBAGE DATA ===")
    all_tkpi = db.execute(select(TKPIFood)).scalars().all()
    deleted_count = 0
    
    for t in all_tkpi:
        if t.id not in processed_ids:
            # Periksa apakah dipakai di yolo_mapping
            mappings = db.execute(select(YoloTkpiMapping).where(YoloTkpiMapping.tkpi_food_id == t.id)).scalars().all()
            for m in mappings:
                print(f"⚠️  Menghapus Mapping YOLO '{m.yolo_label}' karena '{t.name}' dihapus.")
                db.delete(m)  # Hapus secara manual untuk menghindari NotNullViolation
                
            db.delete(t)
            deleted_count += 1
            print(f"[DELETE] Hapus data lama: {t.name} (ID: {t.id}, Code: {t.tkpi_code})")
            
    db.commit()
    print(f"\n✅ Selesai. Total valid TKPI: {len(processed_ids)}, Dihapus: {deleted_count}")

if __name__ == '__main__':
    sync_tkpi_final()
