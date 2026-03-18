import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.detection_service import process_detection
from app.schemas.detection import DetectionResponse
from app.storage.files import save_upload_file
from app.core.config import settings
from app.core.execution import get_detection_semaphore, get_detection_executor
from app.core.exceptions import AppException

router = APIRouter()

# Current prefix in router.py is "/detect". So path="" becomes "/api/v1/detect"
@router.post("", response_model=DetectionResponse, status_code=status.HTTP_200_OK)
async def detect_food(
    request: Request,
    file: UploadFile = File(..., description="Food image to analyze"),
    db: Session = Depends(get_db)
):
    """
    Detect food items in uploaded image.
    
    Reliability features:
    - Max concurrency limit (503 if busy)
    - Timeout protection
    - Strict file validation
    """
    # 1. Validation
    # File type
    if file.content_type not in ["image/jpeg", "image/jpg", "image/png"]:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG and PNG images are supported.",
            code="INVALID_FILE_TYPE"
        )
    
    # File size (Check content-length header approx, or read chunks)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size is {settings.MAX_UPLOAD_SIZE/1024/1024}MB.",
            code="FILE_TOO_LARGE"
        )
        
    if file_size == 0:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty.",
            code="EMPTY_FILE"
        )

    # 2. Concurrency Guard
    semaphore = get_detection_semaphore()
    if semaphore.locked():
        raise AppException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server is busy processing other requests. Please try again later.",
            code="SERVER_BUSY"
        )

    async with semaphore:
        try:
            # Save uploaded filePersistence 
            image_path = await save_upload_file(file)
            
            # 3. Execution with Timeout & Dedicated ThreadPool
            loop = asyncio.get_event_loop()
            executor = get_detection_executor()
            
            # process_detection handles DB persistence of Analysis + Items
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    executor, 
                    process_detection, 
                    db, 
                    image_path,
                    request.state.request_id
                ),
                timeout=settings.DETECT_TIMEOUT_SECONDS
            )
            
            return result
            
        except asyncio.TimeoutError:
            raise AppException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Detection timed out after {settings.DETECT_TIMEOUT_SECONDS}s.",
                code="TIMEOUT"
            )
        except AppException:
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Detection failed: {str(e)}",
                code="INTERNAL_ERROR"
            )
