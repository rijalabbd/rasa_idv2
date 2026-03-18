"""Admin model management service — upload, validate, and hot-reload active.pt.

Upload flow (P0-safe):
    1. Save upload → active.pt.tmp
    2. Validate size (1 MB – 200 MB)
    3. Load YOLO from tmp (proves file is valid before touching disk)
    4. Compute SHA-256
    5. Backup old active.pt → active_<YYYYMMDD_HHMMSS>.pt
    6. os.replace(tmp, active.pt)  — atomic disk swap
    7. model_manager.swap_model(new_model, meta) — atomic in-memory swap
    
    If step 3 fails → delete tmp, keep old active.pt + old model → return 500.
"""

import hashlib
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from ultralytics import YOLO

from app.core.exceptions import AppException
from app.core.paths import MODELS_DIR
from app.services import model_manager

logger = logging.getLogger(__name__)

# --- Constants ---
ACTIVE_MODEL_NAME = "active.pt"
TMP_MODEL_NAME = "active_upload.pt"
MIN_MODEL_SIZE = 1 * 1024 * 1024       # 1 MB
MAX_MODEL_SIZE = 200 * 1024 * 1024     # 200 MB


def _get_models_dir() -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _backup_old_model(models_dir: Path) -> None:
    """Rename existing active.pt → active_<YYYYMMDD_HHMMSS>.pt."""
    active_path = models_dir / ACTIVE_MODEL_NAME
    if not active_path.exists():
        return
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"active_{ts}.pt"
    backup_path = models_dir / backup_name
    try:
        os.rename(str(active_path), str(backup_path))
        logger.info(f"Backed up old model → {backup_name}")
    except OSError as e:
        logger.warning(f"Backup rename failed (non-fatal): {e}")


# ---------------------------------------------------------------------------
# Public: read status (delegates to model_manager)
# ---------------------------------------------------------------------------

def read_model_status() -> dict:
    """Return current model status from in-memory model manager."""
    return model_manager.get_status()


# ---------------------------------------------------------------------------
# Public: upload + validate + hot-reload
# ---------------------------------------------------------------------------

def save_uploaded_model(file: UploadFile, request_id: str = "") -> dict:
    """Validate, pre-load, atomic-swap, and hot-reload uploaded model.

    Returns dict consumed directly by the endpoint response.
    Raises AppException on validation / load / IO failure.
    """
    # --- Extension check ---
    filename = file.filename or ""
    if not filename.lower().endswith(".pt"):
        raise AppException(
            status_code=400,
            detail="Only .pt model files are allowed.",
            code="INVALID_FILE_TYPE",
        )

    models_dir = _get_models_dir()
    tmp_path = models_dir / TMP_MODEL_NAME
    final_path = models_dir / ACTIVE_MODEL_NAME

    # ------------------------------------------------------------------
    # Step 1 + 2: Write upload to temp + size validation
    # ------------------------------------------------------------------
    try:
        written = 0
        with open(tmp_path, "wb") as out:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                written += len(chunk)

                if written > MAX_MODEL_SIZE:
                    out.close()
                    tmp_path.unlink(missing_ok=True)
                    raise AppException(
                        status_code=400,
                        detail=f"Model file too large. Maximum is {MAX_MODEL_SIZE // (1024*1024)} MB.",
                        code="FILE_TOO_LARGE",
                    )
    except AppException:
        raise
    except IOError as e:
        tmp_path.unlink(missing_ok=True)
        raise AppException(
            status_code=500,
            detail=f"Failed to write model file: {e}",
            code="IO_ERROR",
        )
    finally:
        file.file.close()

    if written < MIN_MODEL_SIZE:
        tmp_path.unlink(missing_ok=True)
        raise AppException(
            status_code=400,
            detail=f"Model file too small ({written} bytes). Minimum is {MIN_MODEL_SIZE // (1024*1024)} MB.",
            code="FILE_TOO_SMALL",
        )

    # ------------------------------------------------------------------
    # Step 3: Load YOLO from TEMP file (P0 — validates before disk swap)
    # ------------------------------------------------------------------
    try:
        import numpy as np
        new_model = YOLO(str(tmp_path))

        # Smoke test: verify the model has class names and can actually infer
        if not hasattr(new_model, "names") or not isinstance(new_model.names, dict) or len(new_model.names) == 0:
            raise ValueError("Model has no valid class names — likely corrupt or not a detection model.")

        # Run a tiny dummy predict to prove inference works
        dummy_img = np.zeros((32, 32, 3), dtype=np.uint8)
        new_model.predict(dummy_img, verbose=False)

        logger.info(f"✅ Pre-swap YOLO validation passed for uploaded file ({written} bytes, {len(new_model.names)} classes)")
    except AppException:
        raise
    except Exception as e:
        tmp_path.unlink(missing_ok=True)
        logger.error(f"❌ Uploaded model failed YOLO validation: {e}")
        raise AppException(
            status_code=500,
            detail=f"Uploaded model is invalid and could not be loaded: {e}",
            code="MODEL_RELOAD_FAILED",
        )

    # ------------------------------------------------------------------
    # Step 4: Compute SHA-256 of validated temp file
    # ------------------------------------------------------------------
    sha256_hex = _compute_sha256(tmp_path)

    # ------------------------------------------------------------------
    # Step 5: Backup old active.pt
    # ------------------------------------------------------------------
    _backup_old_model(models_dir)

    # ------------------------------------------------------------------
    # Step 6: Atomic disk swap (tmp → active.pt)
    # ------------------------------------------------------------------
    try:
        os.replace(str(tmp_path), str(final_path))
    except OSError as e:
        tmp_path.unlink(missing_ok=True)
        raise AppException(
            status_code=500,
            detail=f"Atomic swap failed: {e}",
            code="SWAP_FAILED",
        )

    # ------------------------------------------------------------------
    # Step 7: Atomic in-memory swap (zero downtime)
    # ------------------------------------------------------------------
    loaded_at = _now_iso()
    meta = {
        "active_model": ACTIVE_MODEL_NAME,
        "sha256": sha256_hex,
        "size_bytes": written,
        "loaded_at": loaded_at,
        "ready": True,
    }
    model_manager.swap_model(new_model, meta)

    return {
        "ok": True,
        "active_model": ACTIVE_MODEL_NAME,
        "loaded_at": loaded_at,
        "size_bytes": written,
        "sha256": sha256_hex,
        "filename": filename,
    }
