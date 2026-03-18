import time
import uuid
import logging
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

# Configure basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_access")

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to ensure every request has a Request ID.
    Reads 'X-Request-Id' header or generates a new UUID.
    Sets 'request.state.request_id' and adds it to Response headers.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-Id")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        response.headers["X-Request-Id"] = request_id
        return response

class StructuredLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log request details in a structured format (JSON).
    Logs: timestamps, method, path, status, latency, request_id.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # If an unhandled exception occurs before response
            status_code = 500
            raise e
        finally:
            process_time = (time.time() - start_time) * 1000  # ms
            
            # Safe access to request_id (in case RequestIDMiddleware didn't run or failed)
            request_id = getattr(request.state, "request_id", "unknown")
            
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "latency_ms": round(process_time, 2),
                "ip": request.client.host if request.client else "unknown"
            }
            
            # Log as JSON string for easy parsing by observability tools
            logger.info(json.dumps(log_data))
            
        return response
