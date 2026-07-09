import base64
import json
import requests
import time

img_path = '/root/rasa_idv2/backend/storage/uploads/2026/05/31/2c230875b5ee4fb79c7958fcb5586fb8.jpg'
with open(img_path, 'rb') as f:
    img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')

key = "sk-9bafa945-19c3-46ac-bbd3-ce57a69301ad"

url = "https://router-api.0g.ai/v1/chat/completions"

system_prompt = "You are a food detection AI. Identify food. Reply strictly in JSON array of objects: [{'label': 'Nasi Putih', 'confidence': 0.9, 'bbox': [100, 200, 300, 400]}]"

payload = {
  "model": "minimax-m3",
  "max_tokens": 1000,
  "messages": [
    {
      "role": "user",
      "content": [
        { "type": "text", "text": system_prompt + "\nIdentify food items in the image. Return strictly raw JSON array." },
        { "type": "image_url", "image_url": { "url": f"data:image/jpeg;base64,{img_b64}" } }
      ]
    }
  ]
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {key}"
}

print("Pinging minimax-m3 on 0g.ai router...")
t0 = time.perf_counter()
try:
    res = requests.post(url, json=payload, headers=headers, timeout=25)
    dt = (time.perf_counter() - t0) * 1000
    print(f"Status: {res.status_code}")
    print(f"Latency: {dt:.2f}ms")
    print(f"Response: {res.text}")
except Exception as e:
    print(f"Request failed: {e}")
