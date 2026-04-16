from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.cors import setup_cors
from app.core.execution import init_execution_resources, shutdown_execution_resources
from app.core.paths import ensure_storage_dirs
from app.services.model_manager import load_initial as load_model_initial


# ---------------------------------------------------------------------------
# Lifespan — replaces deprecated @app.on_event("startup") / ("shutdown")
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup → yield → shutdown."""
    # ── STARTUP ──
    # 1. Create all storage directories (must be first)
    ensure_storage_dirs()

    # 2. Initialize execution resources (Executor, Semaphore)
    init_execution_resources()

    # 3. Preload YOLO model via ModelManager
    load_model_initial()

    print("🚀 RASA-ID API starting up...")
    print("📚 API Documentation: http://localhost:8000/docs")

    yield  # ← application is running

    # ── SHUTDOWN ──
    shutdown_execution_resources()
    print("👋 RASA-ID API shutting down...")


# ---------------------------------------------------------------------------
# Create FastAPI application (with lifespan)
# ---------------------------------------------------------------------------

app = FastAPI(
    title="RASA-ID API",
    description="Backend API for Indonesian Food Detection and Nutrition Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Setup CORS
setup_cors(app)

# Middleware
from app.core.middleware import RequestIDMiddleware, StructuredLogMiddleware
app.add_middleware(StructuredLogMiddleware)
app.add_middleware(RequestIDMiddleware)

# Include API routers
from app.api.v1.router import router as api_v1_router
app.include_router(api_v1_router, prefix="/api/v1")


# Exception Handlers
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import http_exception_handler, validation_exception_handler, global_exception_handler, AppException, app_exception_handler

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
