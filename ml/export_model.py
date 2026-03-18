#!/usr/bin/env python3
"""Export trained model as deploy-ready active.pt with metadata.

Naming convention:
    best.pt   = training output (from YOLO training runs)
    active.pt = runtime artifact (loaded by backend ModelManager)

Usage:
    python ml/export_model.py                         # uses default best.pt path
    python ml/export_model.py path/to/custom/best.pt  # uses custom path
"""

import hashlib
import shutil
import sys
from pathlib import Path

# ── Defaults ──────────────────────────────────────────────────────────
DEFAULT_SRC = Path("ml/runs/train_refined/weights/best.pt")
DEPLOY_DIR = Path("ml/deploy")
DEPLOY_NAME = "active.pt"
MIN_SIZE = 1 * 1024 * 1024  # 1 MB — same as backend validation


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC

    if not src.exists():
        print(f"❌ Source not found: {src}")
        sys.exit(1)

    size = src.stat().st_size
    if size < MIN_SIZE:
        print(f"❌ File too small ({size} bytes). Expected ≥ {MIN_SIZE // (1024*1024)} MB.")
        sys.exit(1)

    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    dst = DEPLOY_DIR / DEPLOY_NAME

    shutil.copy2(src, dst)
    h = sha256(dst)

    # Use forward slashes for cross-OS curl compatibility
    dst_posix = dst.as_posix()

    print(f"✅ Exported: {dst_posix}")
    print(f"   Source : {src.as_posix()}")
    print(f"   Size   : {size:,} bytes ({size / (1024*1024):.2f} MB)")
    print(f"   SHA256 : {h}")
    print()
    print(f"Ready to upload via Admin Dashboard or:")
    print(f'   curl -X POST http://localhost:8000/api/v1/admin/model/upload \\')
    print(f'     -H "X-ADMIN-KEY: $ADMIN_KEY" \\')
    print(f'     -F "file=@{dst_posix}"')


if __name__ == "__main__":
    main()
