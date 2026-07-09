import base64
import json
import time
import requests
import os
import random

# Load API keys from .env
gemini_keys = []
claude_key = ""
mimo_key = ""

env_path = '/root/rasa_idv2/.env'
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('GEMINI_API_KEY='):
                gemini_keys = line.strip().split('=')[1].split(',')
            elif line.startswith('CLAUDE_API_KEY='):
                claude_key = line.strip().split('=')[1]
            elif line.startswith('MIMO_API_KEY='):
                mimo_key = line.strip().split('=')[1]

img_path = '/root/rasa_idv2/backend/storage/uploads/2026/05/31/2c230875b5ee4fb79c7958fcb5586fb8.jpg'
with open(img_path, 'rb') as f:
    img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')

# Mock system prompt
system_prompt = "You are a food detection AI. Identify food. Reply strictly in JSON array of objects: [{'label': 'Nasi Putih', 'confidence': 0.9, 'bbox': [100, 200, 300, 400]}]"

def test_gemini(key):
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
        # Only print error if it fails
        if res.status_code != 200:
            err_msg = ""
            try:
                err_msg = res.json().get("error", {}).get("message", "")
            except:
                err_msg = res.text[:200]
            return dt, f"Error {res.status_code}: {err_msg}"
        return dt, "200 OK"
    except Exception as e:
        return (time.perf_counter() - t0) * 1000, str(e)

def test_claude(key):
    url = "https://ai.livscene.com/v1/chat/completions"
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Identify food items in the image and return JSON coordinates."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }
        ]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    t0 = time.perf_counter()
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        dt = (time.perf_counter() - t0) * 1000
        if res.status_code != 200:
            return dt, f"Error {res.status_code}: {res.text[:200]}"
        return dt, "200 OK"
    except Exception as e:
        return (time.perf_counter() - t0) * 1000, str(e)

# Run Gemini benchmark on all keys
print("=== Running Gemini Latency Benchmark on All Keys ===")
for idx, key in enumerate(gemini_keys):
    print(f"Testing Key Index {idx} ({key[:10]}...)...")
    dt, status = test_gemini(key)
    print(f"  Duration: {dt:.2f}ms, Result: {status}")
    time.sleep(1.0)

# Run Claude benchmark (3 Runs)
print("\n=== Running Claude Latency Benchmark (3 Runs, 2s gap) ===")
claude_results = []
for i in range(3):
    print(f"Run {i+1}...")
    dt, status = test_claude(claude_key)
    claude_results.append(dt)
    print(f"  Duration: {dt:.2f}ms, Result: {status}")
    if i < 2:
        time.sleep(2.0)

# Run simulated Fallback Chain (1 Run)
print("\n=== Running Fallback Chain Simulation ===")
print("Simulating Gemini connection error, falling back to Claude...")
t_gemini_fail = 50.0 
dt_claude, status_claude = test_claude(claude_key)
total_fallback_ms = t_gemini_fail + dt_claude
print(f"Fallback path GEMINI -> CLAUDE completed in {total_fallback_ms:.2f}ms (Claude Result: {status_claude})")
