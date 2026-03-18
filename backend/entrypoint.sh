#!/bin/bash
# =============================================================================
# Backend Entrypoint Script
# =============================================================================
# This script runs before the main application starts.
# It handles database migrations and then starts uvicorn.
# =============================================================================

set -e

echo "🚀 Starting RASA-ID Backend..."

# Wait for database to be ready (optional extra safety)
echo "⏳ Waiting for database connection..."

# Ensure storage directories and symlink (Permanent Fix)
echo "📂 Ensuring storage directories..."
mkdir -p /app/storage/uploads
# Force symlink creation/update (-sf: s=symlink, f=force/overwrite)
# logic: /app/uploads -> /app/storage/uploads
# This ensures that any code referencing "uploads/file.jpg" finds it in storage
ln -sfn /app/storage/uploads /app/uploads
echo "✅ Storage symlink verified: /app/uploads -> /app/storage/uploads"
python -c "
from app.core.config import settings
from sqlalchemy import create_engine
import time

max_retries = 30
for i in range(max_retries):
    try:
        engine = create_engine(settings.DATABASE_URL)
        conn = engine.connect()
        conn.close()
        print('✅ Database connection successful!')
        break
    except Exception as e:
        if i < max_retries - 1:
            print(f'⏳ Attempt {i+1}/{max_retries}: Waiting for database...')
            time.sleep(2)
        else:
            print(f'❌ Could not connect to database: {e}')
            exit(1)
"

# Run database migrations
echo "📦 Running database migrations..."
alembic upgrade head
echo "✅ Migrations complete!"

# Start the application
echo "🌐 Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
