"""Admin endpoint: TKPI CSV Import (dry-run + commit) + List.

POST /admin/tkpi/import-csv
  - Auth: X-ADMIN-KEY
  - Input: multipart/form-data, field "file"
  - Query: dry_run=true|false (default true)
  - Response: JSON summary with counts, errors, warnings

GET /admin/tkpi/list
  - Auth: X-ADMIN-KEY
  - Query: limit (default 500), offset (default 0)
  - Response: JSON {total, items: [...]}
"""

import logging
from fastapi import APIRouter, Depends, Request, UploadFile, File, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_admin_api_key
from app.services.audit_service import AuditService
from app.services.tkpi_import_service import import_csv_from_text
from app.models.tkpi_food import TKPIFood
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/tkpi/import-csv")
async def import_tkpi_csv(
    request: Request,
    file: UploadFile = File(...),
    dry_run: bool = Query(True, description="If true, validate only without writing to DB"),
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key),
):
    """Import TKPI data from CSV file.

    - dry_run=true (default): parse, validate, estimate insert/update counts. No DB writes.
    - dry_run=false: parse, validate, UPSERT into tkpi_foods.
    """
    audit = AuditService(db)

    # ── Validate file ────────────────────────────────────────────────────
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be .csv")

    # Read content
    raw_bytes = await file.read()

    if len(raw_bytes) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    if len(raw_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(raw_bytes):,} bytes). Max: {MAX_FILE_SIZE:,} bytes"
        )

    # Decode UTF-8 (handle BOM)
    try:
        csv_text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not valid UTF-8")

    # ── Run import ───────────────────────────────────────────────────────
    result = import_csv_from_text(
        csv_text,
        db,
        filename=file.filename,
        dry_run=dry_run,
    )

    # ── Audit log ────────────────────────────────────────────────────────
    meta = result.audit_meta()
    meta["file_size"] = len(raw_bytes)
    audit.log_action("TKPI_IMPORT_CSV", request, admin_key, meta=meta)

    return result.to_dict()


@router.get("/tkpi/list")
async def list_tkpi_foods(
    limit: int = Query(500, ge=1, le=2000, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    admin_key: str = Depends(get_admin_api_key),
):
    """List all TKPI foods with pagination."""
    total = db.execute(select(func.count(TKPIFood.id))).scalar()

    rows = db.execute(
        select(TKPIFood)
        .order_by(TKPIFood.tkpi_code.asc())
        .offset(offset)
        .limit(limit)
    ).scalars().all()

    items = [
        {
            "id": r.id,
            "tkpi_code": r.tkpi_code,
            "name": r.name,
            "energi_kal": r.energi_kal,
            "protein_g": r.protein_g,
            "lemak_g": r.lemak_g,
            "karbo_g": r.karbo_g,
            "serat_g": r.serat_g,
        }
        for r in rows
    ]

    return {"total": total, "items": items}
