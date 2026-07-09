import base64
import json
import time
import requests
import os

# Load API keys from .env
gemini_keys = []
mistral_key = ""
env_path = '/root/rasa_idv2/.env'
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('GEMINI_API_KEY='):
                gemini_keys = line.strip().split('=')[1].split(',')
            elif line.startswith('MISTRAL_API_KEY='):
                mistral_key = line.strip().split('=')[1]

img_path = '/root/rasa_idv2/backend/storage/uploads/2026/05/31/2c230875b5ee4fb79c7958fcb5586fb8.jpg'
with open(img_path, 'rb') as f:
    img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')

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
        return dt, res.status_code
    except Exception as e:
        return (time.perf_counter() - t0) * 1000, str(e)

def test_mistral(key):
    url = "https://api.mistral.ai/v1/chat/completions"
    payload = {
      "model": "pixtral-12b-2409",
      "max_tokens": 1000,
      "messages": [
        {
          "role": "user",
          "content": [
            { "type": "text", "text": system_prompt + "\nIdentify food items in the image and return JSON coordinates." },
            { "type": "image_url", "image_url": { "url": f"data:image/jpeg;base64,{img_b64}" } }
          ]
        }
      ]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }
    t0 = time.perf_counter()
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=25)
        dt = (time.perf_counter() - t0) * 1000
        return dt, res.status_code
    except Exception as e:
        return (time.perf_counter() - t0) * 1000, str(e)

print("=== STARTING MISTRAL VS GEMINI BENCHMARK (3 RUNS EACH) ===")

working_gemini_key = gemini_keys[1] if len(gemini_keys) > 1 else gemini_keys[0]

# Run Gemini 3 times
gemini_dts = []
for i in range(3):
    print(f"Gemini Run {i+1}...")
    dt, status = test_gemini(working_gemini_key)
    if status == 200:
        gemini_dts.append(dt)
        print(f"  Gemini Success: {dt/1000:.2f}s")
    else:
        print(f"  Gemini Failed: {status}")
    time.sleep(2.0)

# Run Mistral 3 times
mistral_dts = []
for i in range(3):
    print(f"Mistral Run {i+1}...")
    dt, status = test_mistral(mistral_key)
    if status == 200:
        mistral_dts.append(dt)
        print(f"  Mistral Success: {dt/1000:.2f}s")
    else:
        print(f"  Mistral Failed: {status}")
    time.sleep(2.0)

print("\n=== BENCHMARK RESULT SUMMARY ===")
if gemini_dts:
    print(f"Gemini Average Latency: {sum(gemini_dts)/len(gemini_dts)/1000:.2f}s")
else:
    print("Gemini Average Latency: N/A")

if mistral_dts:
    print(f"Mistral Average Latency: {sum(mistral_dts)/len(mistral_dts)/1000:.2f}s")
else:
    print("Mistral Average Latency: N/A")
