const fs = require('fs');
const http = require('https');

const imgBytes = fs.readFileSync('/root/rasa_idv2/backend/storage/uploads/2026/05/31/2c230875b5ee4fb79c7958fcb5586fb8.jpg');
const base64Image = imgBytes.toString('base64');

const key = "fcYO0tntB5orwmu2Z6s4WmIgxap0MVLi";

const payload = JSON.stringify({
  model: "pixtral-12b-2409",
  max_tokens: 1000,
  messages: [
    {
      role: "user",
      content: [
        { type: "text", text: "Identify food items in the image. Return strictly in JSON array of objects: [{'label': 'Nasi Putih', 'confidence': 0.9, 'bbox': [ymin, xmin, ymax, xmax]}]. Bbox values should be normalized on a 0-1000 scale." },
        { type: "image_url", image_url: { url: `data:image/jpeg;base64,${base64Image}` } }
      ]
    }
  ]
});

const req = http.request({
  hostname: 'api.mistral.ai',
  path: '/v1/chat/completions',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${key}`
  }
}, (res) => {
  let body = '';
  res.on('data', (chunk) => body += chunk);
  res.on('end', () => {
    console.log(`Status: ${res.statusCode}`);
    console.log(`Response: ${body}`);
  });
});

req.on('error', (err) => console.error(err));
req.write(payload);
req.end();
