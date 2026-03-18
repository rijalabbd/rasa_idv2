"""
Generic TKPI Foods CSV Importer Script.

Imports TKPI food data from CSV file into tkpi_foods table.
Performs UPSERT: updates existing records, inserts new ones.

Usage:
    python scripts/import_tkpi_foods_csv.py --file data/tkpi_sample.csv

CSV Format (required columns):
    kode_pangan,nama_bahan,energi_kal,protein_g,lemak_g,karbo_g,serat_g

Run from backend directory:
    cd backend
    python scripts/import_tkpi_foods_csv.py --file data/tkpi_sample.csv
"""

import argparse
import csv
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.tkpi_food import TKPIFood


def import_tkpi_from_csv(csv_path: str, dry_run: bool = False) -> dict:
    """
    Import TKPI foods from CSV file.
    
    Args:
        csv_path: Path to CSV file
        dry_run: If True, don't commit changes
    
    Returns:
        dict with counts: inserted, updated, skipped, errors
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Required columns
    required_cols = ['nama_bahan', 'energi_kal', 'protein_g', 'lemak_g', 'karbo_g']
    optional_cols = ['kode_pangan', 'serat_g']
    
    results = {
        'inserted': 0,
        'updated': 0,
        'skipped': 0,
        'errors': []
    }
    
    db = SessionLocal()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            # Skip comment lines at the beginning
            lines = f.readlines()
            data_lines = [l for l in lines if not l.strip().startswith('#') and l.strip()]
            
        if not data_lines:
            raise ValueError("CSV file is empty or contains only comments")
        
        # Parse CSV from filtered lines
        reader = csv.DictReader(data_lines)
        
        # Validate columns
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        
        missing_cols = [c for c in required_cols if c not in reader.fieldnames]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        print(f"📂 Reading {csv_path}")
        print(f"📋 Columns found: {reader.fieldnames}")
        print("-" * 50)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
            try:
                nama = row['nama_bahan'].strip()
                if not nama:
                    results['skipped'] += 1
                    continue
                
                # Parse numeric values
                energi = float(row['energi_kal'] or 0)
                protein = float(row['protein_g'] or 0)
                lemak = float(row['lemak_g'] or 0)
                karbo = float(row['karbo_g'] or 0)
                serat = float(row.get('serat_g') or 0)
                
                # Check if exists (by name - primary unique key)
                existing = db.execute(
                    select(TKPIFood).where(TKPIFood.name == nama)
                ).scalar_one_or_none()
                
                if existing:
                    # Update existing record
                    existing.energi_kal = energi
                    existing.protein_g = protein
                    existing.lemak_g = lemak
                    existing.karbo_g = karbo
                    existing.serat_g = serat
                    results['updated'] += 1
                    print(f"🔄 Updated: {nama}")
                else:
                    # Insert new record
                    food = TKPIFood(
                        name=nama,
                        energi_kal=energi,
                        protein_g=protein,
                        lemak_g=lemak,
                        karbo_g=karbo,
                        serat_g=serat
                    )
                    db.add(food)
                    results['inserted'] += 1
                    print(f"✅ Inserted: {nama}")
                    
            except Exception as e:
                results['errors'].append(f"Row {row_num}: {str(e)}")
                print(f"❌ Error row {row_num}: {e}")
        
        if dry_run:
            print("\n⚠️  DRY RUN - Changes NOT committed")
            db.rollback()
        else:
            db.commit()
            print("\n💾 Changes committed to database")
            
    finally:
        db.close()
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Import TKPI foods from CSV file'
    )
    parser.add_argument(
        '--file', '-f',
        required=True,
        help='Path to CSV file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without committing'
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("🍚 TKPI Foods CSV Importer")
    print("=" * 50)
    
    try:
        results = import_tkpi_from_csv(args.file, args.dry_run)
        
        print("\n" + "=" * 50)
        print("📊 Import Summary")
        print("=" * 50)
        print(f"✅ Inserted: {results['inserted']}")
        print(f"🔄 Updated:  {results['updated']}")
        print(f"⏭️  Skipped:  {results['skipped']}")
        print(f"❌ Errors:   {len(results['errors'])}")
        
        if results['errors']:
            print("\nErrors:")
            for err in results['errors']:
                print(f"  - {err}")
                
        total = results['inserted'] + results['updated']
        print(f"\n🎉 Total records processed: {total}")
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
