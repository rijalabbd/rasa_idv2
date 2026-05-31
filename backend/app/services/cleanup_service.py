import os
import time
import logging
import threading
from pathlib import Path
from app.core.paths import UPLOADS_DIR

logger = logging.getLogger(__name__)

def run_storage_cleanup(max_age_days: int = 90):
    """
    Remove uploaded files from storage/uploads/ that are older than max_age_days.
    Also removes empty directories in the uploads tree.
    """
    logger.info(f"Starting storage cleanup task (max_age_days={max_age_days})...")
    if not UPLOADS_DIR.exists():
        logger.warning(f"Uploads directory {UPLOADS_DIR} does not exist. Cleanup skipped.")
        return

    now = time.time()
    cutoff_time = now - (max_age_days * 24 * 60 * 60)
    files_deleted = 0
    bytes_freed = 0
    dirs_removed = 0

    # 1. Delete old files
    for root, dirs, files in os.walk(UPLOADS_DIR):
        for file in files:
            file_path = Path(root) / file
            try:
                stat = file_path.stat()
                mtime = stat.st_mtime
                if mtime < cutoff_time:
                    size = stat.st_size
                    file_path.unlink()
                    files_deleted += 1
                    bytes_freed += size
            except Exception as e:
                logger.error(f"Failed to delete file {file_path}: {e}")

    # 2. Delete empty folders (walk bottom-up to delete nested empty dirs)
    for root, dirs, files in os.walk(UPLOADS_DIR, topdown=False):
        for d in dirs:
            dir_path = Path(root) / d
            try:
                # check if directory is empty
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    dirs_removed += 1
            except Exception as e:
                logger.error(f"Failed to remove directory {dir_path}: {e}")

    logger.info(
        f"Storage cleanup completed: deleted {files_deleted} files "
        f"({bytes_freed / (1024 * 1024):.2f} MB freed), removed {dirs_removed} empty directories."
    )


def start_cleanup_scheduler(max_age_days: int = 90):
    """Start the periodic storage cleanup thread."""
    def worker():
        # Sleep for 1 minute initially to let application startup settle
        time.sleep(60)
        while True:
            try:
                run_storage_cleanup(max_age_days=max_age_days)
            except Exception as e:
                logger.error(f"Error in storage cleanup worker: {e}")
            # Run once every 24 hours (86400 seconds)
            time.sleep(86400)
    
    t = threading.Thread(target=worker, daemon=True, name="storage-cleanup-thread")
    t.start()
    logger.info("Storage cleanup scheduler started.")
