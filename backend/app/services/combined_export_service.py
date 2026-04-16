import io
import json
import zipfile
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.feedback import Feedback
from app.models.class_request import ClassRequest
from app.models.analysis import Analysis
from typing import IO, Tuple

def dump_jsonl(items, fp):
    for item in items:
        fp.write(json.dumps(item) + "\n")

def build_combined_export_zip(db: Session, include_images: bool = False, only_new: bool = True) -> Tuple[IO[bytes], str]:
    """
    Build a ZIP file containing:
    - feedback.jsonl
    - class_requests.jsonl
    - (Optional) Images folder
    """
    from app.services.export_tracking_service import get_unexported_ids, get_all_ids, mark_exported, generate_batch_id
    batch_id = generate_batch_id()
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        # 1. Feedback
        if only_new:
            fb_ids = get_unexported_ids(db, "feedback")
        else:
            fb_ids = get_all_ids(db, "feedback")
            
        feedbacks = []
        if fb_ids:
            feedbacks = db.execute(
                select(Feedback).join(Analysis).where(Feedback.id.in_(fb_ids))
            ).scalars().all()
        feedback_list = []
        for f in feedbacks:
            feedback_list.append({
                "id": f.id,
                "analysis_id": f.analysis_id,
                "predicted_label": f.predicted_label,
                "corrected_tkpi_id": f.corrected_tkpi_food_id,
                "bbox": [f.bbox_x1, f.bbox_y1, f.bbox_x2, f.bbox_y2],
                "note": f.note,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "is_processed": f.is_processed,
                "image_filename": f.image_filename  # might be useful if images are included
            })
        
        feedback_str = io.StringIO()
        dump_jsonl(feedback_list, feedback_str)
        zipf.writestr("feedback.jsonl", feedback_str.getvalue())
        
        # 2. Class Requests
        if only_new:
            cr_ids = get_unexported_ids(db, "class_request")
        else:
            cr_ids = get_all_ids(db, "class_request")

        requests = []
        if cr_ids:
            requests = db.execute(
                select(ClassRequest).where(ClassRequest.id.in_(cr_ids))
            ).scalars().all()
        request_list = []
        for r in requests:
            bbox = None
            if r.bbox_x1 is not None:
                bbox = [r.bbox_x1, r.bbox_y1, r.bbox_x2, r.bbox_y2]
                
            request_list.append({
                "id": r.id,
                "analysis_id": r.analysis_id,
                "requested_label": r.requested_label,
                "bbox": bbox,
                "note": r.note,
                "status": r.status,
                "is_exported": r.is_exported,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "image_path": r.image_path
            })
            
        request_str = io.StringIO()
        dump_jsonl(request_list, request_str)
        zipf.writestr("class_requests.jsonl", request_str.getvalue())
        
        # TODO: Include images if feasible/requested. 
        # User said "optional: copy images". For minimal MVP jsonl is enough.
        
    zip_buffer.seek(0)
    
    # Mark as exported after successful build
    if feedbacks:
        mark_exported(db, "feedback", [f.id for f in feedbacks], batch_id)
    if requests:
        mark_exported(db, "class_request", [r.id for r in requests], batch_id)
    
    return zip_buffer, batch_id
