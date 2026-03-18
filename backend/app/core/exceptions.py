from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any


class ErrorResponse(BaseModel):
    """Standardized error response body."""
    detail: str
    code: str
    context: Dict[str, Any] = Field(default_factory=dict)


class AppException(StarletteHTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        code: str = "ERROR",
        context: Dict[str, Any] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code
        self.context = context or {}

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            code=exc.code,
            context=exc.context
        ).model_dump()
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle standard HTTP exceptions."""
    
    # Check if detail is already a structured dict (e.g. from security.py)
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )

    # Try to extract code from detail string (legacy support for simple raises)
    # Format: "Some message (Code: SOME_CODE)"
    detail_str = str(exc.detail)
    code = "ERROR"
    context = {}
    
    import re
    match = re.search(r"\(Code: ([A-Z_]+)\)", detail_str)
    if match:
        code = match.group(1)
        # clean detail
        detail_str = detail_str.replace(f" (Code: {code})", "").strip()
    else:
        # Default mapping
        if exc.status_code == 400: code = "BAD_REQUEST"
        elif exc.status_code == 401: code = "UNAUTHORIZED"
        elif exc.status_code == 403: code = "FORBIDDEN"
        elif exc.status_code == 404: code = "NOT_FOUND"
        elif exc.status_code == 408: code = "TIMEOUT"
        elif exc.status_code == 429: code = "TOO_MANY_REQUESTS"
        elif exc.status_code == 500: code = "INTERNAL_ERROR"
        elif exc.status_code == 503: code = "SERVER_BUSY"
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=detail_str,
            code=code,
            context=context
        ).model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle 422 validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            detail="Invalid request parameters",
            code="VALIDATION_ERROR",
            context={"errors": exc.errors()}
        ).model_dump()
    )


async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected 500 errors."""
    # Log the full error here in a real app
    print(f"Unhandled error: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            detail="An internal server error occurred",
            code="INTERNAL_ERROR",
            context={}
        ).model_dump()
    )
