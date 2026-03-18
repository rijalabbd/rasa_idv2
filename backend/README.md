# RASA-ID Backend

Backend API untuk sistem deteksi makanan Indonesia dengan analisis nutrisi menggunakan TKPI (Tabel Komposisi Pangan Indonesia).

## 🚀 Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy 2.x** - ORM with modern async support
- **Alembic** - Database migrations
- **Pydantic** - Data validation and settings
- **Uvicorn** - ASGI server

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Virtual environment (venv/virtualenv)

## 🛠️ Installation

### 1. Create Virtual Environment

```bash
cd c:\laragon\www\rasa_id_v2\backend
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and update values:

```bash
copy .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=postgresql+psycopg2://postgres:your_password@localhost:5432/rasa_id_db
STORAGE_PATH=./storage
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
MODEL_PATH=./storage/models/best.pt
CONF_THRESHOLD=0.5
```

### 5. Create Database

In PostgreSQL:
```sql
CREATE DATABASE rasa_id_db;
```

### 6. Run Migrations

```bash
alembic upgrade head
```

### 7. Start Development Server

```bash
uvicorn app.main:app --reload
```

Server will start at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/v1/
│   │   ├── router.py           # API v1 router
│   │   └── endpoints/
│   │       ├── health.py       # Health check
│   │       ├── detection.py    # Food detection
│   │       ├── tkpi.py         # TKPI search/detail
│   │       └── feedback.py     # User feedback
│   ├── core/
│   │   ├── config.py           # Settings & configuration
│   │   └── cors.py             # CORS middleware
│   ├── db/
│   │   ├── base.py             # SQLAlchemy base
│   │   └── session.py          # Database session
│   ├── models/                 # SQLAlchemy models
│   │   ├── tkpi_food.py
│   │   ├── analysis.py
│   │   ├── detection.py
│   │   └── feedback.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── common.py
│   │   ├── tkpi.py
│   │   ├── detection.py
│   │   └── feedback.py
│   ├── services/               # Business logic
│   │   ├── detection_service.py
│   │   ├── tkpi_service.py
│   │   └── feedback_service.py
│   └── storage/                # File handling
│       ├── paths.py
│       └── files.py
├── alembic/                    # Database migrations
├── storage/                    # File storage (auto-created)
│   ├── uploads/               # Uploaded images
│   ├── feedback/              # Feedback data
│   └── models/                # YOLO models
├── requirements.txt
├── .env.example
└── README.md
```

## 🔌 API Endpoints

### Health Check
```bash
GET /api/v1/health
```

Response:
```json
{"status": "ok"}
```

### TKPI Search
```bash
GET /api/v1/tkpi/search?q=nasi&limit=10
```

Response:
```json
[
  {"id": 1, "name": "Nasi Putih"},
  {"id": 2, "name": "Nasi Goreng"}
]
```

### TKPI Detail
```bash
GET /api/v1/tkpi/1
```

Response:
```json
{
  "id": 1,
  "name": "Nasi Putih",
  "nutrition": {
    "energi_kal": 180.0,
    "protein_g": 3.5,
    "lemak_g": 0.3,
    "karbo_g": 40.0,
    "serat_g": 0.3
  }
}
```

### Food Detection
```bash
POST /api/v1/detection/photo
Content-Type: multipart/form-data

file: <image_file>
```

Response:
```json
{
  "analysis_id": 1,
  "image_path": "uploads/2026/01/17/abc123.jpg",
  "model_version": "best.pt",
  "avg_confidence": 0.85,
  "items": [
    {
      "label": "nasi",
      "confidence": 0.92,
      "bbox": [100, 150, 300, 400],
      "tkpi": {
        "id": 1,
        "name": "Nasi Putih",
        "nutrition": {
          "energi_kal": 180.0,
          "protein_g": 3.5,
          "lemak_g": 0.3,
          "karbo_g": 40.0,
          "serat_g": 0.3
        }
      }
    }
  ],
  "total_nutrition": {
    "energi_kal": 180.0,
    "protein_g": 3.5,
    "lemak_g": 0.3,
    "karbo_g": 40.0,
    "serat_g": 0.3
  }
}
```

### Submit Feedback
```bash
POST /api/v1/feedback
Content-Type: application/json

{
  "analysis_id": 1,
  "items": [
    {
      "bbox": [100, 150, 300, 400],
      "predicted_label": "nasi",
      "corrected_tkpi_id": 5,
      "note": "Should be nasi goreng"
    }
  ]
}
```

Response:
```json
{
  "ok": true,
  "saved": 1,
  "message": "Successfully saved 1 feedback items"
}
```

## 🧪 Testing with cURL

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Search TKPI
```bash
curl "http://localhost:8000/api/v1/tkpi/search?q=nasi&limit=5"
```

### Upload Image for Detection
```bash
curl -X POST -F "file=@path/to/image.jpg" http://localhost:8000/api/v1/detection/photo
```

### Submit Feedback
```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": 1,
    "items": [{
      "bbox": [100, 150, 300, 400],
      "predicted_label": "nasi",
      "corrected_tkpi_id": 1
    }]
  }'
```

## 📊 Database Schema

### Tables

- **tkpi_foods** - Indonesian food composition data
- **analyses** - Detection analysis records
- **detections** - Individual detection results
- **feedback** - User correction feedback

### Relationships

```
analyses (1) ──< (N) detections
analyses (1) ──< (N) feedback
tkpi_foods (1) ──< (N) detections
tkpi_foods (1) ──< (N) feedback
```

## 🔄 Database Migrations

### Create New Migration
```bash
alembic revision --autogenerate -m "description"
```

### Apply Migrations
```bash
alembic upgrade head
```

### Rollback Migration
```bash
alembic downgrade -1
```

### Check Current Version
```bash
alembic current
```

## ⚠️ Important Notes

### YOLO Detection
Currently using **dummy/placeholder** detection. To integrate real YOLOv8:

1. Place trained model at `storage/models/best.pt`
2. Update `app/services/detection_service.py`:
   ```python
   from ultralytics import YOLO
   
   def run_yolo_inference(image_path: str):
       model = YOLO(settings.MODEL_PATH)
       results = model(image_path, conf=settings.CONF_THRESHOLD)
       # Process results...
   ```

### TKPI Data
Database starts empty. You need to:
- Import TKPI data manually, OR
- Create a seeding script (not included in MVP)

### Storage Directories
Automatically created on first use:
- `storage/uploads/YYYY/MM/DD/` - Uploaded images
- `storage/feedback/images/` - Feedback images
- `storage/feedback/labels/` - YOLO label files

## 🐛 Troubleshooting

### Database Connection Error
- Verify PostgreSQL is running
- Check DATABASE_URL in `.env`
- Ensure database exists

### Import Errors
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

### CORS Issues
- Update CORS_ORIGINS in `.env`
- Restart server after changes

## 📝 License

MIT License - RASA-ID Project

## 👥 Contributors

Tugas Akhir - RASA-ID Team
