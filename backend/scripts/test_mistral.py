import base64
import json
import requests

img_path = '/root/rasa_idv2/backend/storage/uploads/2026/05/31/2c230875b5ee4fb79c7958fcb5586fb8.jpg'
with open(img_path, 'rb') as f:
    img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')

key = "fcYO0tntB5orwmu2Z6s4WmIgxap0MVLi"

url = "https://api.mistral.ai/v1/chat/completions"
payload = {
  "model": "pixtral-12b-2409",
  "max_tokens": 1000,
  "messages": [
    {
      "role": "user",
      "content": [
        { "type": "text", "text": "Identify food items in the image. Return strictly in JSON array of objects: [{'label': 'Nasi Putih', 'confidence': 0.9, 'bbox': [ymin, xmin, ymax, xmax]}]. Bbox values should be normalized on a 0-1000 scale." },
        { "type": "image_url", "image_url": { "url": f"data:image/jpeg;base64,{img_b64}" } }
      ]
    }
  ]
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {key}"
}

res = requests.post(url, json=payload, headers=headers)
print(f"Status: {res.status_code}")
print(f"Response: {res.text}")
