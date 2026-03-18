import io
import csv
import zipfile
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.class_request import ClassRequest
from app.core.paths import STORAGE_DIR

def collect_class_requests(db: Session, only_unexported: bool = True) -> list[ClassRequest]:
    stmt = select(ClassRequest)
    if only_unexported:
        stmt = stmt.where(ClassRequest.is_exported == False)
    stmt = stmt.order_by(ClassRequest.created_at)
    result = db.execute(stmt)
    return list(result.scalars().all())

def generate_data_yaml(class_names: list[str]) -> str:
    yaml_content = f"""# YOLOv8 Dataset Configuration - Class Requests
# Generated: {datetime.now().isoformat()}

path: .
train: images
val: images

nc: {len(class_names)}
names:
"""
    for name in class_names:
        yaml_content += f"  - {name}\n"
    return yaml_content

def generate_metadata_csv(requests: list[ClassRequest]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "request_id", "analysis_id", "requested_label",
        "image_path", "label_path",
        "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2",
        "note", "status", "is_exported", "created_at"
    ])
    
    for req in requests:
        if req.image_path:
            stem = Path(req.image_path).stem
            label_path = f"class_requests/labels/{stem}.txt"
        else:
            label_path = ""
        
        writer.writerow([
            req.id, req.analysis_id, req.requested_label,
            req.image_path or "", label_path,
            req.bbox_x1 or "", req.bbox_y1 or "", req.bbox_x2 or "", req.bbox_y2 or "",
            req.note or "", req.status, req.is_exported,
            req.created_at.isoformat() if req.created_at else ""
        ])
    
    return output.getvalue()

def generate_label_content(req: ClassRequest, label_to_class_id: dict) -> str:
    class_id = label_to_class_id.get(req.requested_label, 0)
    
    lines = []
    lines.append("# Class Request Label")
    lines.append(f"# Requested: {req.requested_label}")
    lines.append(f"# Class ID: {class_id}")
    
    if req.bbox_x1 is not None and req.bbox_y1 is not None:
        lines.append(f"# Raw bbox: {req.bbox_x1} {req.bbox_y1} {req.bbox_x2} {req.bbox_y2}")
        lines.append("# TODO: Normalize bbox with actual image dimensions")
        lines.append("# (No YOLO line written - requires proper normalization)")
    else:
        lines.append("# No bbox provided")
    
    return "\n".join(lines) + "\n"

def build_class_request_zip(db: Session, only_unexported: bool = True) -> tuple[io.BytesIO, int, int]:
    requests = collect_class_requests(db, only_unexported)
    print(f"📦 Exporting {len(requests)} class requests...")
    
    unique_labels = sorted(set(req.requested_label for req in requests))
    label_to_class_id = {label: idx for idx, label in enumerate(unique_labels)}
    print(f"📋 Class mapping: {label_to_class_id}")
    
    zip_buffer = io.BytesIO()
    exported_count = 0
    exported_ids = []
    added_images = set()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for req in requests:
            if not req.image_path:
                print(f"⚠️  Skipping request {req.id}: no image_path")
                continue
            
            image_path = STORAGE_DIR / req.image_path
            if not image_path.exists():
                print(f"⚠️  Skipping request {req.id}: image not found at {image_path}")
                continue
            
            stem = image_path.stem
            ext = image_path.suffix
            image_key = f"{stem}{ext}"
            
            if image_key not in added_images:
                zipf.write(image_path, f"dataset/images/{image_key}")
                added_images.add(image_key)
                print(f"  ✅ Added image: {image_key}")
            
            label_key = f"{stem}.txt"
            if label_key not in added_images:
                label_content = generate_label_content(req, label_to_class_id)
                zipf.writestr(f"dataset/labels/{label_key}", label_content)
                added_images.add(label_key)
                print(f"  ✅ Added label: {label_key}")
            
            exported_ids.append(req.id)
            exported_count += 1
        
        yaml_content = generate_data_yaml(unique_labels)
        zipf.writestr("dataset/data.yaml", yaml_content)
        print(f"✅ Added data.yaml")
        
        csv_content = generate_metadata_csv(requests)
        zipf.writestr("dataset/metadata.csv", csv_content)
        print(f"✅ Added metadata.csv")
    
    unique_images = len([k for k in added_images if not k.endswith('.txt')])
    if exported_count > 0 and only_unexported:
        mark_as_exported(db, exported_ids)
    
    zip_buffer.seek(0)
    print(f"✅ Export complete: {exported_count} requests, {unique_images} unique images")
    
    return zip_buffer, exported_count, unique_images

def mark_as_exported(db: Session, request_ids: list[int]):
    if not request_ids:
        return
    
    requests = db.execute(
        select(ClassRequest).where(ClassRequest.id.in_(request_ids))
    ).scalars().all()
    
    for req in requests:
        req.is_exported = True
    
    db.commit()
    print(f"✅ Marked {len(request_ids)} class requests as exported")
