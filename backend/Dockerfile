# =============================================================================
# RASA-ID Backend Dockerfile
# =============================================================================
# Base: Python 3.11 slim
# =============================================================================

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Upgrade pip tools
RUN pip install --upgrade pip setuptools wheel

# Install torch CPU wheels from official index first (more reliable)
RUN pip install --no-cache-dir --default-timeout=180 \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.2.2 torchvision==0.17.2

# install requirements (includes opencv-python-headless)
RUN pip install --no-cache-dir --default-timeout=180 -r requirements.txt

# install ultralytics WITHOUT deps (prevents opencv-python GUI)
RUN pip install --no-cache-dir --default-timeout=180 --no-deps "ultralytics>=8.0.0"

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 8000

# Run entrypoint script
CMD ["./entrypoint.sh"]
