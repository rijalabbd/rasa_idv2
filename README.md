# 🍚 RASA-ID v2 — Sistem Analisis Gizi Makanan Indonesia

> **Proyek Akhir** — Deteksi makanan Indonesia menggunakan YOLOv8, pemetaan ke data gizi TKPI, dan active learning loop melalui feedback pengguna.

---

## 📋 Apa yang Dilakukan Sistem Ini?

1. **Deteksi Makanan** — Upload foto → AI mengenali jenis makanan dengan YOLOv8
2. **Info Gizi Otomatis** — Hasil deteksi dipetakan ke database TKPI (Tabel Komposisi Pangan Indonesia)
3. **Feedback & Koreksi** — Pengguna bisa koreksi label jika salah → meningkatkan model
4. **Admin Dashboard** — Kelola mapping, export dataset, upload model baru (hot reload tanpa restart)
5. **TKPI Import** — Upload CSV data gizi TKPI via API atau Streamlit UI (dry-run + commit)

---

## 🏗️ Arsitektur

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Frontend    │────▶│    Backend API   │────▶│  PostgreSQL  │
│  (React)     │     │   (FastAPI)      │     │              │
│  Port: 5173  │     │   Port: 8000     │     │  Port: 5432  │
└─────────────┘     └──────────────────┘     └──────────────┘
                           │
                    ┌──────┴──────┐
                    │  YOLOv8     │
                    │  ModelManager│
                    │  (active.pt)│
                    └─────────────┘
┌─────────────┐
│  Admin       │───▶ Backend API
│  (Streamlit) │
│  Port: 8501  │
└─────────────┘
```

---

## � Quick Start

```bash
# Jalankan semua service
docker compose up -d

# Akses
# Frontend:  http://localhost:5173
# Backend:   http://localhost:8000/docs
# Admin:     http://localhost:8501
```

### Environment Variables (Backend)

| Variable | Deskripsi | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | (set di docker-compose) |
| `CORS_ORIGINS` | Allowed frontend origins | `http://localhost:5173` |
| `ADMIN_KEY` | API key untuk admin | — |
| `CONF_THRESHOLD` | YOLO confidence threshold | `0.25` |

---

## 📂 Struktur Proyek

```
rasa_id_v2/
├── backend/             # FastAPI Backend (API, services, models)
│   └── app/
│       ├── api/v1/      # Endpoints (detect, feedback, admin)
│       ├── services/    # Business logic + ModelManager
│       ├── models/      # SQLAlchemy database models
│       └── core/        # Config, middleware, security
├── frontend/            # React + Vite (halaman user)
│   └── src/
│       ├── pages/       # Home, AnalyzePhoto, ManualSearch
│       └── components/  # UI components reusable
├── admin_dashboard/     # Streamlit (dashboard admin)
│   └── views/           # Dashboard, Mappings, TKPI Import, Export
├── ml/                  # Training & dataset YOLO
│   ├── export_model.py  # Script export best.pt → active.pt
│   └── runs/            # Training runs & weights
└── docker-compose.yml
```

---

## 🔄 Alur Kerja

### Deteksi Makanan (User)
```
Upload foto → YOLOv8 inference → Mapping ke TKPI → Tampilkan info gizi
```

### Feedback (Active Learning)
```
User koreksi label → Simpan ke DB + generate YOLO label
→ Admin export dataset ZIP → Retrain model → Upload model baru
```

### Upload Model (Admin — Hot Reload)
```
Admin upload .pt → Validasi YOLO + dummy predict
  ✅ → Backup old active.pt → Atomic swap → Model langsung aktif (tanpa restart)
  ❌ → Reject, model lama tetap jalan
```

---

## 🤖 Model Management

| Istilah | Penjelasan |
|---|---|
| `best.pt` | Output dari training YOLO (di `ml/runs/`) |
| `active.pt` | Model runtime yang dipakai backend (di `storage/models/`) |
| `ModelManager` | Singleton thread-safe yang mengelola model di memory |

### Export Model untuk Deploy
```bash
python ml/export_model.py
# Output: ml/deploy/active.pt + SHA256 + ukuran
# Siap diupload via Admin Dashboard
```

### Fitur Hot Reload
- Upload model baru → validasi → swap tanpa downtime
- Model lama tetap melayani request selama proses reload
- File corrupt otomatis ditolak (`MODEL_RELOAD_FAILED`)
- Backup otomatis: `active_<timestamp>.pt`
- Status endpoint: `GET /api/v1/admin/model/status` → `{sha256, loaded_at, ready}`

---

## � API Endpoints Utama

| Method | Path | Deskripsi |
|---|---|---|
| POST | `/api/v1/detect` | Upload foto → deteksi + info gizi |
| POST | `/api/v1/feedback` | Koreksi label dari user |
| POST | `/api/v1/class-requests` | Request kelas makanan baru |
| POST | `/api/v1/missed-detections` | Laporan deteksi makanan yang terlewat oleh model |
| GET | `/api/v1/tkpi/search` | Cari data gizi TKPI (name + tkpi_code, trigram) |
| GET | `/api/v1/health` | Health check |
| **Admin** | | |
| GET | `/api/v1/admin/model/status` | Status model (sha256, loaded_at, ready) |
| POST | `/api/v1/admin/model/upload` | Upload & activate model baru |
| GET | `/api/v1/admin/summary` | Statistik dashboard |
| * | `/api/v1/admin/mappings` | CRUD mapping YOLO ↔ TKPI |
| POST | `/api/v1/admin/tkpi/import-csv` | Import CSV TKPI (dry-run / commit) |
| GET | `/api/v1/admin/tkpi/list` | List semua data TKPI (paginated) |
| GET | `/api/v1/admin/export-zip` | Export JSONL (feedback + class requests) |
| GET | `/api/v1/admin/export/yolo/feedback` | Export YOLO dataset dari feedback (ZIP + gambar) |
| GET | `/api/v1/admin/export/yolo/class-requests` | Export YOLO dataset dari class request (ZIP + gambar) |
| GET | `/api/v1/admin/export/yolo/missed` | Export YOLO dataset laporan missed detections (ZIP + gambar) |

> Admin endpoints memerlukan header `X-ADMIN-KEY`.

---

## ✅ Progress

| Phase | Status | Deskripsi |
|---|---|---|
| Phase 1 | ✅ | Stabilization & Admin Dashboard |
| Phase 2 | ✅ | Security (Auth, Audit, Rate Limiting) |
| Phase 3 | ✅ | ML Training + Backend Integration |
| Phase 4 | ✅ | Hot Reload ModelManager + Export Script |
| Phase 5 | ✅ | TKPI Data Layer + YOLO Export + DB Hardening |
| Phase 6 | ✅ | TKPI CSV Import API + Streamlit UI |
| Phase 7 | ✅ | Active Learning Loop Refinement & System Audits |

### Phase 7 Detail

| Fitur | Status | Deskripsi |
|---|---|---|
| Missed Detections | ✅ | Endpoint + Frontend support untuk mencatat makanan yang pelacakan YOLO-nya terliput/gagal terdeteksi |
| YOLO Export Fixes | ✅ | Pencegahan duplikasi ZIP label dan penanganan `bbox: null` (fallback ke koordinat dummy) untuk Class Requests |
| Backend & DB Audit | ✅ | Relasi SQLAlchemy Cascade yang solid pada `Analysis` → `MissedDetections`, dan `Feedback`. Termasuk perbaikan Alembic Migration Crash (Hotfix: 500 Dashboard Error). |
| Zero-Data Edge Cases | ✅ | Semua endpoint export (`export/yolo/*`) kebal terhadap database kosong (no HTTP 500 crash). |
| Admin Dashboard UI | ✅ | Audit Streamlit yang memperbaiki parser respons API (500 Error Handler ditangkap sempurna). |
| Path Traversal Defense| ✅ | Modul `save_upload_file` menggunakan sistem auto-generate UUID yang mencegah input path berbahaya. |
| UI/UX Active Learning | ✅ | Rombak UI bagian *Tambah Makanan Manual* & *Ajukan Pelatihan AI* di frontend `AnalyzePhoto.jsx` agar lebih intuitif, informatif (penjelasan implikasi training AI), dan user-friendly (card design, toast notifications). |
| BBox Crash Defense | ✅ | Penanganan fallback (Null check) saat destructuring bounding box (`bbox`) dari manual detect yang memicu *white screen crash* di `BoundingBoxOverlay.jsx`. |
| Presisi Confidence | ✅ | Sentralisasi format decimal point (1 digit) untuk Confidence score antara deteksi Bounding box dan Detection Cards agar akurat dan konsisten. |

### Phase 6 Detail

| Fitur | Status | Deskripsi |
|---|---|---|
| Import CSV API | ✅ | `POST /admin/tkpi/import-csv` — dry-run + commit, UPSERT by `tkpi_code` |
| Streamlit UI | ✅ | Halaman "TKPI Import" — upload, validate, commit, preview data |
| Shared service | ✅ | `tkpi_import_service.py` digunakan oleh API dan CLI script |
| Safety: SHA256 | ✅ | Deteksi file berubah setelah validasi, blokir commit jika hash berbeda |
| Safety: Checkbox | ✅ | Konfirmasi "I understand this will write to the database" sebelum commit |
| Thousand-sep guard | ✅ | Format `1.234,5` ditolak (ERROR), bukan diam-diam di-parse salah |
| Blank row skip | ✅ | Baris kosong (`;;;;;`) di-skip otomatis, tidak dihitung sebagai error |
| Error banner | ✅ | HTTP status + detail + Ref ID ditampilkan saat API gagal |
| Data preview | ✅ | Tabel TKPI di bawah halaman import + tombol Refresh |
| Audit log | ✅ | Setiap import (termasuk dry-run) tercatat di `admin_audit_log` |

### Phase 5 Detail

| Fitur | Status | Deskripsi |
|---|---|---|
| TKPI `tkpi_code` | ✅ | Kolom unik (VARCHAR 32) + CHECK not empty + GIN trigram index |
| Nutrisi nullable | ✅ | `energi_kal`, `protein_g`, `lemak_g`, `karbo_g` bisa NULL |
| Search optimization | ✅ | OR query pada `name` + `tkpi_code` (ILIKE), limit & sanitize |
| Import script | ✅ | CSV upsert `ON CONFLICT (tkpi_code)`, batch 500, normalize |
| YOLO export (feedback) | ✅ | ZIP: images/ + labels/ (normalized bbox) + data.yaml + metadata.csv |
| YOLO export (class req) | ✅ | ZIP: images/ + labels/ + data.yaml, skip rows tanpa bbox |
| FK delete rules | ✅ | `class_requests` → SET NULL, `yolo_tkpi_mapping` → RESTRICT |
| Indexes | ✅ | `class_requests`: analysis_id, status, is_exported |
| Audit log types | ✅ | `meta` json→jsonb, `created_at` timestamp→timestamptz |

---

## 🧪 Testing

```bash
# E2E test (Playwright)
npx playwright test frontend/e2e/

# Verifikasi model
python ml/verify_model_refined.py

# Manual API test
curl -F "file=@foto.jpg" http://localhost:8000/api/v1/detect
```

---

## 📊 TKPI CSV Import Contract

### Format CSV
| Item | Spec |
|---|---|
| **Encoding** | UTF-8 (BOM handled otomatis) |
| **Delimiter** | Auto-detect: comma (`,`) atau semicolon (`;`) |
| **Desimal** | Mendukung dot (`0.3`) dan comma (`0,3`) |
| **Thousand sep** | ⚠️ **TIDAK didukung.** Format `1.234,5` akan ditolak (ERROR). Gunakan `1234.5` atau `1234,5` |

### Kolom

| Kolom | Tipe | Wajib | NULL jika kosong? |
|---|---|---|---|
| `tkpi_code` | TEXT | ✅ | ❌ (ERROR → row di-skip) |
| `name` | TEXT | ✅ | ❌ (ERROR → row di-skip) |
| `energi_kal` | FLOAT | ❌ | ✅ |
| `protein_g` | FLOAT | ❌ | ✅ |
| `lemak_g` | FLOAT | ❌ | ✅ |
| `karbo_g` | FLOAT | ❌ | ✅ |
| `serat_g` | FLOAT | ❌ | ✅ |

### Normalisasi
- `tkpi_code` → trim + UPPERCASE
- `name` → trim + collapse double space

### Validasi

**ERROR (row ditolak):**
- `tkpi_code` kosong (kecuali baris sepenuhnya kosong → di-skip otomatis)
- `name` kosong
- Angka negatif (contoh: `-2.5`)
- Angka tidak bisa di-parse (contoh: `abc`)
- Thousand separator terdeteksi (contoh: `1.234,5`) → gunakan `1234.5`

**SKIP (baris diabaikan, bukan error):**
- Baris sepenuhnya kosong (semua kolom kosong/whitespace) → `skipped_blank_rows`

**WARNING (row diterima, ditandai):**
- `energi_kal == 0` (kecuali nama mengandung "air")
- `protein_g + lemak_g + karbo_g` semua `== 0` (kecuali "air")

### Upsert
- Key: `ON CONFLICT (tkpi_code) DO UPDATE`
- Batch: 500 rows per commit

### Cara Pakai

**Via Streamlit UI (recommended):**
1. Buka `http://localhost:8501` → klik **TKPI Import**
2. Upload file `.csv`
3. Klik **🔍 Validate (Dry-run)** — review summary, errors, warnings
4. Jika 0 errors → centang checkbox → klik **✅ Commit Import**
5. Scroll ke bawah untuk lihat tabel **📋 Data TKPI Saat Ini**

**Via API (curl):**
```bash
# Dry-run (validasi saja)
curl -X POST "http://localhost:8000/api/v1/admin/tkpi/import-csv?dry_run=true" \
  -H "X-ADMIN-KEY: <key>" -F "file=@data.csv"

# Commit (tulis ke DB)
curl -X POST "http://localhost:8000/api/v1/admin/tkpi/import-csv?dry_run=false" \
  -H "X-ADMIN-KEY: <key>" -F "file=@data.csv"
```

**Via CLI script:**
```bash
docker exec rasa_id_backend python scripts/import_tkpi.py data/tkpi_seed.csv
docker exec rasa_id_backend python scripts/import_tkpi.py data/tkpi_seed.csv --dry-run
```

### Sample Files
- `backend/data/tkpi_seed.csv` — data TKPI produksi (15 rows)
- `backend/data/tkpi_valid_sample.csv` — contoh data valid untuk testing
- `backend/data/tkpi_invalid_sample.csv` — contoh error & warning cases

---

## 📝 Catatan Teknis

- **Model Runtime**: `active.pt` di-load via `ModelManager` (thread-safe, atomic swap)
- **Tanpa Model**: API return `503 MODEL_NOT_READY`
- **Concurrency**: Detection dibatasi `Semaphore` (default: 2 concurrent)
- **Logging**: Setiap request punya `x-request-id` + structured log
- **Error Format**: `{detail, code, context}` + `x-request-id` header
- **TKPI Identifier**: `tkpi_code` (bukan `name`) sebagai kunci unik TKPI
- **YOLO Export**: Bbox dinormalisasi 0-1, class names dinamis dari dataset

---

## 🗄️ Alembic Migrations

| Revision | Deskripsi |
|---|---|
| `7b8c9d0e1f2a` | Tambah kolom `tkpi_code` |
| `8c9d0e1f2a3b` | Nullable nutrisi columns |
| `3c4d5e6f7a8b` | CHECK constraint + GIN index name |
| `d4e5f6g7h8i9` | GIN trigram index on `tkpi_code` |
| `e5f6a7b8c9d0` | FK rules + class_requests idx + audit_log types |

---

*Terakhir diperbarui: 11 Maret 2026*
```
