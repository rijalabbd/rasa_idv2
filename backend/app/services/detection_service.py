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

import threading
import gc

# Setup logger
logger = logging.getLogger(__name__)

# Thread lock to guarantee sequential YOLO inference and prevent race conditions
inference_lock = threading.Lock()

def run_yolo_inference(image_path: str, request_id: str) -> tuple[List[Dict[str, Any]], float]:
    """Run actual YOLO inference using Ultralytics."""
    import time
    
    # Resolve absolute path for image
    absolute_image_path = str(STORAGE_DIR / image_path)
    
    model, meta = model_manager.get_model()
    
    start_time = time.perf_counter()
    
    # Acquire lock to prevent race conditions on shared YOLO model object
    with inference_lock:
        results = model.predict(
            absolute_image_path, 
            conf=settings.CONF_THRESHOLD, 
            iou=settings.IOU_THRESHOLD,
            verbose=False,
            save=False,       # Prevent saving runs/predict image files to disk
            save_txt=False,   # Prevent saving label files to disk
            save_conf=False   # Prevent saving confidence values to disk
        )
        
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
        
        # Explicitly clear cached state of YOLO predictor if it exists
        try:
            if hasattr(model, 'predictor') and model.predictor is not None:
                model.predictor.results = None
        except Exception:
            pass
            
        # Explicitly free memory and collect garbage
        del results
        gc.collect()

    inference_time_ms = (time.perf_counter() - start_time) * 1000
    
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

def run_gemini_inference(image_path: str, request_id: str) -> tuple[List[Dict[str, Any]], float]:
    """Run multimodal food detection using Google Gemini API."""
    import base64
    import requests
    import json
    import time
    from PIL import Image
    
    # 1. Resolve absolute path
    absolute_image_path = str(STORAGE_DIR / image_path)
    
    # 2. Get image size (width, height)
    try:
        with Image.open(absolute_image_path) as img:
            width, height = img.size
    except Exception as e:
        logger.error(f"Failed to open image to read dimensions: {e}")
        raise AppException(
            status_code=400,
            detail="Gagal membaca dimensi file gambar.",
            code="IMAGE_READ_ERROR"
        )
        
    # 3. Read and encode image to Base64
    try:
        with open(absolute_image_path, "rb") as f:
            img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to read image bytes: {e}")
        raise AppException(
            status_code=500,
            detail="Gagal memproses file gambar.",
            code="IMAGE_PROCESSING_ERROR"
        )
        
    # 4. Check GEMINI_API_KEY
    if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.strip():
        raise AppException(
            status_code=400,
            detail="GEMINI_API_KEY tidak dikonfigurasi di file .env server.",
            code="GEMINI_API_KEY_MISSING"
        )
        
    # 5. Build Gemini API Structured generation payload
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Identify all food items present in this image. For each food item, detect: "
                            "1. A short label in Indonesian lowercase with underscores (e.g. 'nasi_putih', 'ayam_goreng', 'telur_dadar'). "
                            "2. A confidence score between 0.0 and 1.0. "
                            "3. A bounding box [ymin, xmin, ymax, xmax] normalized to 0-1000 integers. "
                            "Return ONLY a JSON list of objects: [{\"label\": \"...\", \"confidence\": ..., \"bbox\": [ymin, xmin, ymax, xmax]}]. "
                            "Return [] if no food items are detected."
                        )
                    },
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": img_b64
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    start_time = time.perf_counter()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=settings.DETECT_TIMEOUT_SECONDS or 30)
    except requests.exceptions.RequestException as e:
        logger.error(f"Gemini API request failed: {e}")
        raise AppException(
            status_code=502,
            detail="Koneksi ke Gemini API gagal atau mengalami timeout.",
            code="GEMINI_CONNECTION_TIMEOUT"
        )
        
    if response.status_code != 200:
        logger.error(f"Gemini API returned status code {response.status_code}: {response.text}")
        raise AppException(
            status_code=502,
            detail=f"Gagal memanggil Gemini API (HTTP {response.status_code}).",
            code="GEMINI_API_ERROR"
        )
        
    inference_time_ms = (time.perf_counter() - start_time) * 1000
    
    # 6. Parse structured JSON from response
    try:
        res_json = response.json()
        text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Clean markdown json indicators if present
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            
        raw_items = json.loads(text)
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Failed to parse Gemini response: {e}. Raw response: {response.text}")
        raise AppException(
            status_code=502,
            detail="Format respons dari Gemini API tidak valid.",
            code="GEMINI_RESPONSE_PARSE_ERROR"
        )
        
    # 7. Convert coordinates [ymin, xmin, ymax, xmax] (0-1000) -> [x1, y1, x2, y2] (pixels)
    detections = []
    if isinstance(raw_items, list):
        for item in raw_items:
            try:
                label = str(item.get("label", "")).strip().lower()
                confidence = float(item.get("confidence", 0.8))
                bbox = item.get("bbox", [])
                
                if len(bbox) == 4:
                    ymin, xmin, ymax, xmax = bbox
                    
                    x1 = (xmin / 1000.0) * width
                    y1 = (ymin / 1000.0) * height
                    x2 = (xmax / 1000.0) * width
                    y2 = (ymax / 1000.0) * height
                    
                    # Bound checking
                    x1 = max(0.0, min(x1, float(width)))
                    y1 = max(0.0, min(y1, float(height)))
                    x2 = max(0.0, min(x2, float(width)))
                    y2 = max(0.0, min(y2, float(height)))
                    
                    detections.append({
                        "label": label,
                        "confidence": confidence,
                        "bbox": [x1, y1, x2, y2]
                    })
            except Exception as ex:
                logger.warning(f"Error processing single detection item {item}: {ex}")
                continue
                
    # Structured Log
    log_payload = {
        "event": "gemini_inference_complete",
        "request_id": request_id,
        "inference_ms": round(inference_time_ms, 2),
        "num_items": len(detections),
        "model_version": "gemini-1.5-flash"
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
    2. Run inference (YOLO or Gemini based on active setting)
    3. Map detections to TKPI
    4. Save detection records
    5. Commit and return STRICT response
    """
    from app.services import settings_service
    curr_settings = settings_service.get_settings()
    det_mode = curr_settings.get("detection_mode", "YOLO")

    # Get active model status (for YOLO version fallback)
    model_status = model_manager.get_status()

    # Create analysis record
    if det_mode == "GEMINI":
        model_version_str = "gemini-1.5-flash"
    else:
        model_version_str = model_status.get("active_model") or "unknown"

    analysis = Analysis(
        image_path=image_path,
        model_version=model_version_str,
        conf_threshold=settings.CONF_THRESHOLD
    )
    db.add(analysis)
    db.flush()  # Get analysis.id

    # Run inference depending on mode
    if det_mode == "GEMINI":
        raw_detections, inference_ms = run_gemini_inference(image_path, request_id)
    else:
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