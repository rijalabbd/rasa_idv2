import os
import time
import requests
import concurrent.futures

env_path = '/root/rasa_idv2/.env'
gemini_keys = []

if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('GEMINI_API_KEY='):
                gemini_keys = [k.strip() for k in line.strip().split('=')[1].split(',') if k.strip()]

print(f"Loaded {len(gemini_keys)} Gemini API keys from .env.")

def ping_key(key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    payload = {"contents": [{"parts": [{"text": "say ok"}]}], "generationConfig": {"maxOutputTokens": 2}}
    try:
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=3.0)
        return key, res.status_code, res.text
    except Exception as e:
        return key, 0, str(e)

healthy_keys = []
print("Pinging all keys in parallel...")

with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(gemini_keys))) as executor:
    futures = [executor.submit(ping_key, k) for k in gemini_keys]
    for idx, f in enumerate(concurrent.futures.as_completed(futures)):
        k, status, text = f.result()
        if status == 200:
            healthy_keys.append(k)
            print(f" Key {idx} ({k[:10]}...): Healthy (200 OK)")
        else:
            print(f" Key {idx} ({k[:10]}...): Unhealthy (Status: {status}, Err: {text[:100]})")

print("\n--- SUMMARY ---")
print(f"Total Configured Keys: {len(gemini_keys)}")
print(f"Total Healthy/Ready Keys: {len(healthy_keys)}")
