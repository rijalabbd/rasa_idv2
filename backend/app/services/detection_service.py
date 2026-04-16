from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import time
import logging
from app.models.analysis import Analysis
from app.models.detection import Detection
from app.services.mapping_service import find_mapping_by_label
from app.services import model_manager
from app.schemas.common import NutritionInfo
from app.schemas.detection import DetectionItem, DetectionTKPIInfo, DetectionResponse
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.paths import STORAGE_DIR

# Setup logger
logger = logging.getLogger(__name__)

def run_yolo_inference(image_path: str, request_id: str) -> tuple[List[Dict[str, Any]], float]:
    """Run actual YOLO inference using Ultralytics."""
    import time
    
    # Resolve absolute path for image
    absolute_image_path = str(STORAGE_DIR / image_path)
    
    model, meta = model_manager.get_model()
    
    start_time = time.perf_counter()
    results = model.predict(
        absolute_image_path, 
        conf=settings.CONF_THRESHOLD, 
        iou=settings.IOU_THRESHOLD,
        verbose=False
    )
    inference_time_ms = (time.perf_counter() - start_time) * 1000
    
    detections = []
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            confidence = float(box.conf[0])
            bbox = box.xyxy[0].tolist() # [x1, y1, x2, y2]
            
            detections.append({
                "label": label,
                "confidence": confidence,
                "bbox": bbox
            })
    
    # Structured Log — includes sha256 + loaded_at for hot-reload tracing
    log_payload = {
        "event": "inference_complete",
        "request_id": request_id,
        "inference_ms": round(inference_time_ms, 2),
        "num_items": len(detections),
        "model_path": meta.get("active_model", "active.pt"),
        "sha256": meta.get("sha256", "")[:12],
        "loaded_at": meta.get("loaded_at"),
        "conf": settings.CONF_THRESHOLD,
        "iou": settings.IOU_THRESHOLD
    }
    logger.info(str(log_payload))
    
    return detections, inference_time_ms

def empty_nutrition() -> NutritionInfo:
    """Return default empty nutrition object (all zeros)."""
    return NutritionInfo(
        energi_kal=0,
        protein_g=0,
        lemak_g=0,
        karbo_g=0,
        serat_g=0
    )


def process_detection(
    db: Session,
    image_path: str,
    request_id: str
) -> DetectionResponse:
    """
    Main detection pipeline:
    1. Create analysis record
    2. Run YOLO inference
    3. Map detections to TKPI
    4. Save detection records
    5. Commit and return STRICT response
    """
    # Create analysis record
    model_status = model_manager.get_status()
    analysis = Analysis(
        image_path=image_path,
        model_version=model_status.get("active_model") or "unknown",
        conf_threshold=settings.CONF_THRESHOLD
    )
    db.add(analysis)
    db.flush()  # Get analysis.id

    # Run YOLO inference
    raw_detections, inference_ms = run_yolo_inference(image_path, request_id)

    # Process each detection
    detection_items = []

    for det in raw_detections:
        # Use mapping table to find TKPI (Business Logic)
        tkpi_food, nutrition_status, nutrition_status_label, nutrition_note = find_mapping_by_label(
            db, det["label"]
        )

        detection = Detection(
            analysis_id=analysis.id,
            label=det["label"],
            confidence=det["confidence"],
            bbox_x1=det["bbox"][0],
            bbox_y1=det["bbox"][1],
            bbox_x2=det["bbox"][2],
            bbox_y2=det["bbox"][3],
            tkpi_food_id=tkpi_food.id if tkpi_food else None
        )
        db.add(detection)
        
        # Output formatting (Round bbox only for response)
        rounded_bbox = [round(x, 2) for x in det["bbox"]]

        detection_items.append(DetectionItem(
            label=det["label"],
            confidence=det["confidence"],
            bbox=rounded_bbox,
            tkpi=DetectionTKPIInfo(
                id=tkpi_food.id,
                name=tkpi_food.name,
                nutrition=NutritionInfo(
                    energi_kal=tkpi_food.energi_kal or 0,
                    protein_g=tkpi_food.protein_g or 0,
                    lemak_g=tkpi_food.lemak_g or 0,
                    karbo_g=tkpi_food.karbo_g or 0,
                    # serat_g uses `or 0` like other fields for frontend consistency
                    # (schema allows Optional, but we normalize to 0 for uniform handling)
                    serat_g=tkpi_food.serat_g or 0,
                ),
            ) if tkpi_food else None,
            nutrition_status=nutrition_status,
            nutrition_status_label=nutrition_status_label,
            nutrition_note=nutrition_note,
        ))

    # Commit all records
    db.commit()

    return DetectionResponse(
        analysis_id=analysis.id,
        inference_time_ms=round(inference_ms, 2),
        items=detection_items
    )


def calculate_total_nutrition(items: List[DetectionItem]) -> Optional[NutritionInfo]:
    """Sum up nutrition from all items that have TKPI mapping."""
    total_energi = 0.0
    total_protein = 0.0
    total_lemak = 0.0
    total_karbo = 0.0
    total_serat = 0.0
    has_nutrition = False

    for item in items:
        if item.tkpi and item.tkpi.nutrition:
            has_nutrition = True
            total_energi += item.tkpi.nutrition.energi_kal
            total_protein += item.tkpi.nutrition.protein_g
            total_lemak += item.tkpi.nutrition.lemak_g
            total_karbo += item.tkpi.nutrition.karbo_g
            # ✅ perbaikan: cek None, bukan truthy
            if item.tkpi.nutrition.serat_g is not None:
                total_serat += item.tkpi.nutrition.serat_g

    if not has_nutrition:
        return None

    return NutritionInfo(
        energi_kal=round(total_energi, 1),
        protein_g=round(total_protein, 1),
        lemak_g=round(total_lemak, 1),
        karbo_g=round(total_karbo, 1),
        serat_g=round(total_serat, 1)
    )