import shutil
from pathlib import Path
from typing import List, Tuple

from fastapi import UploadFile

from app.storage.paths import (
    get_upload_path,
    get_feedback_image_path,
    get_feedback_label_path,
    get_class_request_image_path,
)
from app.core.paths import STORAGE_DIR


async def save_upload_file(file: UploadFile) -> str:
    """
    Save uploaded file to storage/uploads/YYYY/MM/DD/<uuid>.<ext>
    Returns: relative path to the saved file (POSIX-style)
    """
    extension = "jpg"
    if file.filename:
        ext = file.filename.split(".")[-1].lower()
        if ext in ["jpg", "jpeg", "png"]:
            extension = ext

    relative_path, absolute_path = get_upload_path(extension)

    with open(absolute_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return Path(relative_path).as_posix()


def copy_image_for_feedback(source_path: str) -> str:
    """
    Copy analysis image to feedback/images directory.
    Returns: relative path to the copied file (POSIX-style)
    
    Raises:
        FileNotFoundError: if source file doesn't exist
        Exception: if copy fails or copied file is invalid
    """
    extension = Path(source_path).suffix.lstrip(".").lower()
    if extension not in ["jpg", "jpeg", "png"]:
        extension = "jpg"

    relative_path, absolute_path = get_feedback_image_path(extension)
    source_absolute = STORAGE_DIR / source_path
    
    # Verify source file exists
    if not source_absolute.exists():
        raise FileNotFoundError(f"Source image not found: {source_absolute}")
    
    # Verify source file is readable and has content
    source_size = source_absolute.stat().st_size
    if source_size == 0:
        raise Exception(f"Source image is empty (0 bytes): {source_absolute}")
    
    # Copy file
    shutil.copy2(source_absolute, absolute_path)
    
    # Verify copied file exists and has same size
    dest_path = Path(absolute_path)
    if not dest_path.exists():
        raise Exception(f"Copy failed: destination file not created: {absolute_path}")
    
    dest_size = dest_path.stat().st_size
    if dest_size != source_size:
        raise Exception(f"Copy failed: size mismatch (source={source_size}, dest={dest_size})")
    
    print(f"✅ Image copied: {source_absolute} -> {absolute_path} ({source_size} bytes)")
    
    return Path(relative_path).as_posix()



def write_yolo_label_file(
    feedback_image_path: str,
    items: List[Tuple[int, List[float]]],
) -> str:
    """
    Create YOLO label file for feedback with multiple items.
    One file per image, multiple lines (one per bbox).

    Args:
        feedback_image_path: relpath "feedback/images/<uuid>.jpg"
        items: List of (class_id, bbox) where bbox is [x1,y1,x2,y2]
               bbox can be pixel coords OR normalized coords.

    Returns:
        relpath label file, e.g. "feedback/labels/<uuid>.txt"

    Raises:
        Exception if image can't be read / label can't be written / all bbox invalid
    """
    from PIL import Image  # pillow

    image_filename = Path(feedback_image_path).name
    relative_label_path, absolute_label_path = get_feedback_label_path(image_filename)

    feedback_image_absolute = STORAGE_DIR / feedback_image_path

    # Read image dimensions
    try:
        with Image.open(feedback_image_absolute) as img:
            img_width, img_height = img.size
    except Exception as e:
        raise Exception(
            f"Failed to read image dimensions from {feedback_image_absolute}: {str(e)}"
        )

    if img_width <= 0 or img_height <= 0:
        raise Exception(f"Invalid image dimensions: {img_width}x{img_height}")

    lines: List[str] = []

    for class_id, bbox in items:
        if not bbox or len(bbox) < 4:
            print(f"⚠️ Skipping bbox invalid (len<4): {bbox}")
            continue

        x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]

        # Heuristic: if ALL coords in [0..1], treat as normalized coords.
        # Otherwise assume pixels.
        is_normalized = (
            0.0 <= float(x1) <= 1.0
            and 0.0 <= float(y1) <= 1.0
            and 0.0 <= float(x2) <= 1.0
            and 0.0 <= float(y2) <= 1.0
        )

        # Convert to pixel if normalized
        if is_normalized:
            x1, x2 = float(x1) * img_width, float(x2) * img_width
            y1, y2 = float(y1) * img_height, float(y2) * img_height
        else:
            x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)

        # Order coords
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        # Clamp to image bounds (MVP robustness)
        x1 = max(0.0, min(float(img_width), x1))
        x2 = max(0.0, min(float(img_width), x2))
        y1 = max(0.0, min(float(img_height), y1))
        y2 = max(0.0, min(float(img_height), y2))

        # Re-order after clamp
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        # Skip invalid bbox (too small / zero)
        if (x2 - x1) <= 1.0 or (y2 - y1) <= 1.0:
            print(f"⚠️ Skipping bbox too small/invalid: {[x1,y1,x2,y2]}")
            continue

        # YOLO normalized values
        x_center = ((x1 + x2) / 2.0) / img_width
        y_center = ((y1 + y2) / 2.0) / img_height
        width = (x2 - x1) / img_width
        height = (y2 - y1) / img_height

        # Clamp to [0..1]
        x_center = max(0.0, min(1.0, x_center))
        y_center = max(0.0, min(1.0, y_center))
        width = max(0.0, min(1.0, width))
        height = max(0.0, min(1.0, height))

        lines.append(f"{int(class_id)} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    if not lines:
        raise Exception("No valid bbox lines generated; abort writing label.")

    content = "\n".join(lines) + "\n"

    try:
        with open(absolute_label_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        raise Exception(f"Failed to write label file {absolute_label_path}: {str(e)}")

    return Path(relative_label_path).as_posix()


def copy_image_for_class_request(source_path: str) -> str:
    """
    Copy analysis image to class_requests/images directory.
    Returns: relative path to the copied file (POSIX-style)
    """
    extension = Path(source_path).suffix.lstrip(".").lower()
    if extension not in ["jpg", "jpeg", "png"]:
        extension = "jpg"

    relative_path, absolute_path = get_class_request_image_path(extension)
    source_absolute = STORAGE_DIR / source_path

    shutil.copy2(source_absolute, absolute_path)
    return Path(relative_path).as_posix()
