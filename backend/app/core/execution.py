import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Optional

from app.core.config import settings

# Global execution resources
detection_executor: Optional[ThreadPoolExecutor] = None
detection_semaphore: Optional[asyncio.Semaphore] = None

def init_execution_resources():
    """Initialize global execution resources (executor, semaphore)."""
    global detection_executor, detection_semaphore
    
    # Dedicated executor for CPU-bound detection tasks
    detection_executor = ThreadPoolExecutor(
        max_workers=settings.DETECT_MAX_CONCURRENCY,
        thread_name_prefix="detection_worker"
    )
    
    # Semaphore to strictly limit concurrent requests
    detection_semaphore = asyncio.Semaphore(settings.DETECT_MAX_CONCURRENCY)
    print(f"🔒 Detection resources initialized: Max Concurrency={settings.DETECT_MAX_CONCURRENCY}")

def shutdown_execution_resources():
    """Shutdown execution resources."""
    global detection_executor
    if detection_executor:
        detection_executor.shutdown(wait=True)
        print("🔒 Detection executor shutdown complete.")

def get_detection_semaphore() -> asyncio.Semaphore:
    """Get the global detection semaphore."""
    if detection_semaphore is None:
        raise RuntimeError("Detection resources not initialized. Call init_execution_resources() first.")
    return detection_semaphore

def get_detection_executor() -> ThreadPoolExecutor:
    """Get the global detection executor."""
    if detection_executor is None:
        raise RuntimeError("Detection resources not initialized. Call init_execution_resources() first.")
    return detection_executor
