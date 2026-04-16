import os
import uuid
from datetime import datetime
from pathlib import Path
from app.core.paths import (
    STORAGE_DIR, UPLOADS_DIR, FEEDBACK_DIR, FEEDBACK_IMAGES_DIR, 
    FEEDBACK_LABELS_DIR, CLASS_REQUESTS_DIR, CLASS_REQUESTS_IMAGES_DIR,
    MISSED_DETECTION_IMAGES_DIR
)


def get_upload_path(extension: str = "jpg") -> tuple[str, str]:
    """
    Generate upload path: storage/uploads/YYYY/MM/DD/<uuid>.ext
    Returns: (relative_path, absolute_path)
    """
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    
    filename = f"{uuid.uuid4().hex}.{extension}"
    relative_path = os.path.join("uploads", year, month, day, filename)
    absolute_path = str(UPLOADS_DIR / year / month / day / filename)
    
    # Ensure directory exists
    Path(absolute_path).parent.mkdir(parents=True, exist_ok=True)
    
    return relative_path, absolute_path


def get_feedback_image_path(extension: str = "jpg") -> tuple[str, str]:
    """
    Generate feedback image path: storage/feedback/images/<uuid>.ext
    Returns: (relative_path, absolute_path)
    """
    filename = f"{uuid.uuid4().hex}.{extension}"
    relative_path = os.path.join("feedback", "images", filename)
    absolute_path = str(FEEDBACK_IMAGES_DIR / filename)
    
    # Ensure directory exists
    Path(absolute_path).parent.mkdir(parents=True, exist_ok=True)
    
    return relative_path, absolute_path


def get_feedback_label_path(image_filename: str) -> tuple[str, str]:
    """
    Generate feedback label path: storage/feedback/labels/<uuid>.txt
    Returns: (relative_path, absolute_path)
    """
    # Use same UUID as image but with .txt extension
    base_name = Path(image_filename).stem
    filename = f"{base_name}.txt"
    relative_path = os.path.join("feedback", "labels", filename)
    absolute_path = str(FEEDBACK_LABELS_DIR / filename)
    
    # Ensure directory exists
    Path(absolute_path).parent.mkdir(parents=True, exist_ok=True)
    
    return relative_path, absolute_path


def get_class_request_image_path(extension: str = "jpg") -> tuple[str, str]:
    """
    Generate class request image path: storage/class_requests/images/<uuid>.ext
    Returns: (relative_path, absolute_path)
    """
    filename = f"{uuid.uuid4().hex}.{extension}"
    relative_path = os.path.join("class_requests", "images", filename)
    absolute_path = str(CLASS_REQUESTS_IMAGES_DIR / filename)
    
    Path(absolute_path).parent.mkdir(parents=True, exist_ok=True)
    
    return relative_path, absolute_path


def get_class_request_label_path(image_filename: str) -> tuple[str, str]:
    """
    Generate class request label path: storage/class_requests/labels/<uuid>.txt
    Returns: (relative_path, absolute_path)
    """
    base_name = Path(image_filename).stem
    filename = f"{base_name}.txt"
    relative_path = os.path.join("class_requests", "labels", filename)
    absolute_path = str(CLASS_REQUESTS_DIR / "labels" / filename)
    
    Path(absolute_path).parent.mkdir(parents=True, exist_ok=True)

    return relative_path, absolute_path


def get_missed_detection_image_path(extension: str = "jpg") -> tuple[str, str]:
    """
    Generate missed detection image path: storage/missed_detection/images/<uuid>.ext
    Returns: (relative_path, absolute_path)
    """
    filename = f"{uuid.uuid4().hex}.{extension}"
    relative_path = os.path.join("missed_detection", "images", filename)
    absolute_path = str(MISSED_DETECTION_IMAGES_DIR / filename)

    Path(absolute_path).parent.mkdir(parents=True, exist_ok=True)

    return relative_path, absolute_path
