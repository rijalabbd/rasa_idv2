from fastapi import FastAPI
from app.core.cors import setup_cors
from app.api.v1.router import router as api_v1_router


# Create FastAPI application
app = FastAPI(
    title="RASA-ID API",
    description="Backend API for Indonesian Food Detection and Nutrition Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup CORS
setup_cors(app)

# Middleware
from app.core.middleware import RequestIDMiddleware, StructuredLogMiddleware
app.add_middleware(StructuredLogMiddleware)
app.add_middleware(RequestIDMiddleware)

# Include API routers
app.include_router(api_v1_router, prefix="/api/v1")


# Exception Handlers
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import http_exception_handler, validation_exception_handler, global_exception_handler, AppException, app_exception_handler

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


from app.core.execution import init_execution_resources, shutdown_execution_resources
from app.services.model_manager import load_initial as load_model_initial

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    # Initialize execution resources (Executor, Semaphore)
    init_execution_resources()
    
    # Preload YOLO model via ModelManager
    load_model_initial()
    
    print("🚀 RASA-ID API starting up...")
    print("📚 API Documentation: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    # Shutdown execution resources
    shutdown_execution_resources()
    
    print("👋 RASA-ID API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
