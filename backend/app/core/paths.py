"""
Centralized storage path constants.

All services should import paths from here instead of constructing paths manually.
This ensures consistency and makes path updates easier.
"""
from pathlib import Path
from app.core.config import settings


# Base storage directory
STORAGE_DIR = Path(settings.STORAGE_PATH).resolve()

# Runtime directories - used by application during normal operation
UPLOADS_DIR = STORAGE_DIR / "uploads"
MODELS_DIR = STORAGE_DIR / "models"

# Feedback dataset
FEEDBACK_DIR = STORAGE_DIR / "feedback"
FEEDBACK_IMAGES_DIR = FEEDBACK_DIR / "images"
FEEDBACK_LABELS_DIR = FEEDBACK_DIR / "labels"

# Class requests dataset
CLASS_REQUESTS_DIR = STORAGE_DIR / "class_requests"
CLASS_REQUESTS_IMAGES_DIR = CLASS_REQUESTS_DIR / "images"

# Missed detection dataset
MISSED_DETECTION_DIR = STORAGE_DIR / "missed_detection"
MISSED_DETECTION_IMAGES_DIR = MISSED_DETECTION_DIR / "images"

# Export output directories - production exports from admin endpoints
EXPORTS_DIR = STORAGE_DIR / "exports"
EXPORTS_FEEDBACK_DIR = EXPORTS_DIR / "feedback"
EXPORTS_CLASS_REQUESTS_DIR = EXPORTS_DIR / "class_requests"

# Temporary directories - for testing/debugging only
TEMP_DIR = STORAGE_DIR / "temp"
TEMP_TEST_DATA_DIR = TEMP_DIR / "test_data"
TEMP_MANUAL_EXPORTS_DIR = TEMP_DIR / "manual_exports"
QUARANTINE_DIR = TEMP_DIR / "quarantine"


def ensure_storage_dirs():
    """Create all storage directories if they don't exist."""
    dirs = [
        UPLOADS_DIR,
        MODELS_DIR,
        FEEDBACK_IMAGES_DIR,
        FEEDBACK_LABELS_DIR,
        CLASS_REQUESTS_IMAGES_DIR,
        MISSED_DETECTION_IMAGES_DIR,
        EXPORTS_FEEDBACK_DIR,
        EXPORTS_CLASS_REQUESTS_DIR,
        TEMP_TEST_DATA_DIR,
        TEMP_MANUAL_EXPORTS_DIR,
        QUARANTINE_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
