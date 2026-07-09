import json
import logging
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

def _get_settings_file_path() -> Path:
    """Get absolute path to settings.json inside storage directory."""
    storage_dir = Path(settings.STORAGE_PATH)
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir / "settings.json"

def get_settings() -> dict:
    """Load settings from settings.json. Defaults to YOLO detection mode."""
    path = _get_settings_file_path()
    if not path.exists():
        return {"detection_mode": "YOLO"}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure valid mode
            if not isinstance(data, dict):
                data = {}
            mode = data.get("detection_mode")
            if mode in ("CLAUDE", "MIMO"):
                mode = "MISTRAL"
            if mode not in ("YOLO", "GEMINI", "MISTRAL"):
                mode = "YOLO"
            data["detection_mode"] = mode
            return data
    except Exception as e:
        logger.warning(f"Failed to read settings file: {e}. Falling back to default.")
        return {"detection_mode": "YOLO"}

def save_settings(data: dict) -> None:
    """Save configuration settings to settings.json."""
    path = _get_settings_file_path()
    # Normalize input
    detection_mode = data.get("detection_mode", "YOLO")
    if detection_mode in ("CLAUDE", "MIMO"):
        detection_mode = "MISTRAL"
    if detection_mode not in ("YOLO", "GEMINI", "MISTRAL"):
        detection_mode = "YOLO"
        
    payload = {
        "detection_mode": detection_mode
    }
    
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)
        logger.info(f"Saved configuration settings: {payload}")
    except Exception as e:
        logger.error(f"Failed to write settings file: {e}")
        raise
