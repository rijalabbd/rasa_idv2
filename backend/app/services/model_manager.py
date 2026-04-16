"""Thread-safe YOLO model manager with hot-reload support.

Singleton state:
    _state = (yolo_model, meta_dict)      # atomic read via tuple
    _reload_lock = threading.Lock()        # serialises reloads

Design rules:
    - Never set model to None during reload (zero downtime).
    - Inference reads _state without lock (Python GIL makes tuple
      assignment atomic for pointer swap).
    - reload / swap always acquires _reload_lock.
"""

import hashlib
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, Any

from ultralytics import YOLO
from typing import List, Dict, Any

from app.core.exceptions import AppException
from app.core.paths import MODELS_DIR

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ACTIVE_MODEL_NAME = "active.pt"
MIN_MODEL_SIZE = 1 * 1024 * 1024        # 1 MB
MAX_MODEL_SIZE = 200 * 1024 * 1024      # 200 MB

# ---------------------------------------------------------------------------
# Module-level singleton state
# ---------------------------------------------------------------------------
_state: Tuple[Optional[Any], dict] = (None, {
    "active_model": None,
    "sha256": None,
    "size_bytes": None,
    "loaded_at": None,
    "ready": False,
})
_reload_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_sha256(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _active_path() -> Path:
    return MODELS_DIR / ACTIVE_MODEL_NAME


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_initial() -> None:
    """Load active.pt at startup (if it exists).

    Called once from ``main.py`` startup event.
    """
    global _state

    path = _active_path()
    if not path.exists():
        logger.warning("⚠️ No active.pt found. Service will return 503 MODEL_NOT_READY.")
        return

    logger.info(f"Loading YOLO model from {path}...")
    try:
        model = YOLO(str(path))
    except Exception as e:
        logger.error(f"Failed to load model at startup: {e}")
        return

    sha256 = _compute_sha256(path)
    size_bytes = path.stat().st_size
    loaded_at = _now_iso()

    _state = (model, {
        "active_model": ACTIVE_MODEL_NAME,
        "sha256": sha256,
        "size_bytes": size_bytes,
        "loaded_at": loaded_at,
        "ready": True,
    })
    logger.info("✅ YOLO model loaded successfully.")
    logger.info(f"Model meta: sha256={sha256[:12]}… size={size_bytes} loaded_at={loaded_at}")


def get_model():
    """Return ``(YOLO, meta_dict)`` or raise 503.

    Safe to call from any thread without lock — tuple read is atomic
    under CPython GIL.
    """
    model, meta = _state
    if model is None:
        raise AppException(
            status_code=503,
            detail="YOLO model is not ready or missing.",
            code="MODEL_NOT_READY",
        )
    return model, meta


def get_status() -> dict:
    """Return a *copy* of current model metadata (read-only)."""
    _, meta = _state
    return dict(meta)


def swap_model(new_model, meta: dict) -> None:
    """Atomically swap the in-memory model + metadata.

    Called by ``admin_model_service.save_uploaded_model`` after the new
    model has been validated, loaded, and the disk file has been replaced.
    """
    global _state
    with _reload_lock:
        _state = (new_model, meta)
        logger.info({
            "event": "model_reload_success",
            "sha256": meta.get("sha256"),
            "size_bytes": meta.get("size_bytes"),
            "loaded_at": meta.get("loaded_at"),
        })

# ---------------------------------------------------------------------------
# Helper to expose class names
# ---------------------------------------------------------------------------

def get_class_names() -> List[Dict[str, Any]]:
    """Return class ID‑name mapping from the active YOLO model.
    Handles both dict and list formats of ``model.names``.
    """
    try:
        model, _ = get_model()
    except Exception:
        active_path = _active_path()
        if not active_path.exists():
            return []
        model = YOLO(str(active_path))

    names = model.names
    if isinstance(names, dict):
        return [{"id": int(k), "name": str(v)} for k, v in names.items()]
    elif isinstance(names, list):
        return [{"id": i, "name": str(v)} for i, v in enumerate(names)]
    return []
