import base64
import json
import time
import requests
import os
import concurrent.futures

# Load API keys from .env
gemini_keys = []
env_path = '/root/rasa_idv2/.env'
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('GEMINI_API_KEY='):
                gemini_keys = line.strip().split('=')[1].split(',')

img_path = '/root/rasa_idv2/backend/storage/uploads/2026/05/31/2c230875b5ee4fb79c7958fcb5586fb8.jpg'
with open(img_path, 'rb') as f:
    img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')

system_prompt = "You are a food detection AI. Identify food. Reply strictly in JSON array of objects: [{'label': 'Nasi Putih', 'confidence': 0.9, 'bbox': [100, 200, 300, 400]}]"

def test_gemini(key, label=""):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": system_prompt + "\nIdentify food items in the image and return JSON coordinates."},
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": img_b64
                        }
                    }
                ]
            }
        ]
    }
    t0 = time.perf_counter()
    try:
        res = requests.post(url, json=payload, timeout=20)
        dt = (time.perf_counter() - t0) * 1000
        return dt, res.status_code, label
    except Exception as e:
        return (time.perf_counter() - t0) * 1000, str(e), label

# We'll use two working keys for concurrent requests to simulate two different users
k1 = gemini_keys[1] if len(gemini_keys) > 1 else gemini_keys[0]
k2 = gemini_keys[3] if len(gemini_keys) > 3 else gemini_keys[0]

print("=== STARTING CONCURRENCY AND SEQUENTIAL BENCHMARK (5 RUNS) ===")

# Test Phase 1: 2 Concurrent Requests
print("\n--- PHASE 1: 2 Concurrent Detections (Simultaneous Users) ---")
print("Launching Request 1 and Request 2 at the exact same time...")
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    futures = [
        executor.submit(test_gemini, k1, "Concurrent User A"),
        executor.submit(test_gemini, k2, "Concurrent User B")
    ]
    results = [f.result() for f in futures]

for dt, status, label in results:
    print(f"  [{label}] Duration: {dt/1000:.2f}s, Status: {status}")

# Test Phase 2: 2 Sequential Requests (Immediate Consecutive Call)
print("\n--- PHASE 2: 2 Sequential Detections (Immediate Recall) ---")
print("Launching Request 3 (Initial)...")
dt3, status3, _ = test_gemini(k1, "Sequential 1")
print(f"  [Sequential 1 (Initial)] Duration: {dt3/1000:.2f}s, Status: {status3}")

print("Launching Request 4 (Immediate consecutive recall)...")
dt4, status4, _ = test_gemini(k1, "Sequential 2")
print(f"  [Sequential 2 (Consecutive)] Duration: {dt4/1000:.2f}s, Status: {status4}")

# Test Phase 3: 1 Single Request (Simulated Real POV)
print("\n--- PHASE 3: 1 Single Independent Detection (Real User POV) ---")
print("Sleeping for 5 seconds to clear rates...")
time.sleep(5.0)
print("Launching Request 5 (Fresh User POV)...")
dt5, status5, _ = test_gemini(k1, "Real User POV")
print(f"  [Real User POV] Duration: {dt5/1000:.2f}s, Status: {status5}")

print("\n=== BENCHMARK COMPLETED ===")
