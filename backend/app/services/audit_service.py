from datetime import datetime
from typing import Optional, Any
from sqlalchemy.orm import Session
from fastapi import Request
from app.models.admin_audit_log import AdminAuditLog
import hashlib
import json

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        action: str,
        request: Request,
        admin_key: str,
        meta: dict[str, Any] = None,
        request_id: Optional[str] = None,
        status_code: int = 200,
        error_code: Optional[str] = None
    ):
        """
        Logs an admin action to the database.
        """
        if meta is None:
            meta = {}

        # Enrich meta
        meta["path"] = request.url.path
        meta["method"] = request.method
        meta["status_code"] = status_code
        meta["client_ip"] = request.client.host if request.client else "unknown"
        meta["user_agent"] = request.headers.get("user-agent", "unknown")
        
        # Capture query params if any (useful for export)
        if request.query_params:
             meta["query_params"] = dict(request.query_params)

        if error_code:
            meta["error_code"] = error_code

        # Fingerprint admin key (SHA256 first 8 chars)
        if admin_key:
            hashed = hashlib.sha256(admin_key.encode()).hexdigest()
            meta["admin_key_fingerprint"] = hashed[:8]

        audit_entry = AdminAuditLog(
            action=action,
            meta=meta,
            request_id=request_id or request.headers.get("x-request-id"),
            created_at=datetime.utcnow()
        )
        
        self.db.add(audit_entry)
        self.db.commit()
