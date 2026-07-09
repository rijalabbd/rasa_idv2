import sys
import os
import time

sys.path.append('/app')
sys.path.append('/root/rasa_idv2/backend')

from app.db.session import SessionLocal
# Dynamically import all model modules to register SQLAlchemy classes
import importlib
import pkgutil
import app.models

for _, module_name, _ in pkgutil.iter_modules(app.models.__path__):
    importlib.import_module(f"app.models.{module_name}")

from app.services import settings_service
from app.services.detection_service import process_detection

# Set active mode to GEMINI
print("Setting active detection mode to GEMINI...")
settings_service.save_settings({"detection_mode": "GEMINI"})

db = SessionLocal()

image_path = 'uploads/2026/05/31/2c230875b5ee4fb79c7958fcb5586fb8.jpg'

print("\n=== RUNNING 5 SEQUENTIAL E2E REAL-USECASE GEMINI DETECTIONS ===")
print("Our new Parallel Health Pool is enabled.")

latencies = []

for i in range(5):
    print(f"\n[Run {i+1}/5] Processing food detection...")
    t0 = time.perf_counter()
    try:
        # Calls the actual E2E process_detection pipeline (inference + db mapping + transaction commit)
        res = process_detection(db, image_path, f"benchmark_req_{i+1}")
        dt = (time.perf_counter() - t0) * 1000
        latencies.append(dt)
        print(f" -> SUCCESS: Processed in {dt/1000:.2f}s")
        print(f" -> Model Version: {res.model_version}")
        print(f" -> Found {len(res.items)} food items.")
    except Exception as e:
        print(f" -> FAILED on Run {i+1}: {e}")
    time.sleep(1.5)

db.close()

print("\n=== REAL-USECASE BENCHMARK RESULTS ===")
for idx, lat in enumerate(latencies):
    print(f" Run {idx+1}: {lat/1000:.2f} seconds")

print(f"\nAverage E2E Latency: {sum(latencies)/len(latencies)/1000:.2f} seconds")
