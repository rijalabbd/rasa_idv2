import sys
import os
sys.path.append('/root/rasa_idv2/backend')

from app.core.config import settings
from app.services.detection_service import refresh_gemini_health_pool, _healthy_gemini_keys

print("Reading configured keys...")
refresh_gemini_health_pool()

print("\n--- HEALTH CHECK RESULTS ---")
print(f"Total Healthy Keys: {len(_healthy_gemini_keys)}")
for idx, key in enumerate(_healthy_gemini_keys):
    print(f" - Key Index {idx}: {key[:10]}...")
