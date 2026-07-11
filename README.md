# 🍚 RASA-ID v2 — Sistem Analisis Gizi Makanan Indonesia

> **Proyek Akhir** — Sistem Deteksi Makanan Indonesia menggunakan Model YOLOv8, Pemetaan Komposisi Gizi Terintegrasi Database TKPI, dan Active Learning Loop melalui Feedback Pengguna.

---

## 📋 Fitur Utama Sistem

1. **Deteksi Makanan Real-Time** — Menggunakan model **YOLOv8** lokal yang berjalan di server backend untuk mendeteksi berbagai jenis makanan Indonesia serta lokasinya secara instan.
2. **Kalkulasi Nilai Gizi Otomatis** — Hasil identifikasi objek makanan dipetakan secara real-time ke database gizi **TKPI (Tabel Komposisi Pangan Indonesia)** untuk menyajikan informasi kalori, karbohidrat, protein, lemak, dan serat.
3. **Active Learning (Feedback Loop)** — Memungkinkan pengguna memberikan koreksi (*feedback*) jika terdapat kesalahan klasifikasi oleh model YOLOv8. Koreksi ini disimpan dan dikonversi menjadi label format YOLO untuk retraining model.
4. **Dashboard Admin Terintegrasi** — Admin portal untuk memantau performa sistem, memetakan kelas YOLO ke kode TKPI, mengunduh dataset feedback untuk retraining model, serta mengunggah model YOLO baru.
5. **Hot-Reload Model Runtime** — Admin dapat memperbarui model YOLO (`active.pt`) melalui dashboard tanpa downtime. Sistem memvalidasi model baru secara otomatis sebelum melakukan *atomic hot swap* di memori.
6. **Manajemen Data Gizi TKPI** — Modul untuk melakukan import massal data gizi TKPI dari format CSV lengkap dengan validasi integritas data (dry-run & commit).

---

## 🏗️ Arsitektur Sistem

Sistem RASA-ID dibangun menggunakan arsitektur modular yang dideploy secara lokal menggunakan Docker Compose:

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Frontend    │────▶│    Backend API   │────▶│  PostgreSQL  │
│  (React)     │     │   (FastAPI)      │     │  (Database)  │
│  Port: 5173  │     │   Port: 8000     │     │  Port: 5432  │
└─────────────┘     └──────────────────┘     └──────────────┘
                           │
                    ┌──────┴──────┐
                    │  YOLOv8     │  <-- Deteksi Objek Lokal
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

## ⚡ Petunjuk Cepat (Quick Start)

### 1. Prasyarat Sistem
Pastikan perangkat Anda sudah menginstal:
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (dengan Docker Compose)
* [Git](https://git-scm.com/)

### 2. Kloning Repositori
```bash
git clone https://github.com/rijalabbd/rasa_idv2.git
cd rasa_idv2
```

### 3. Konfigurasi Variabel Lingkungan (.env)
Salin berkas `.env.example` menjadi `.env` di root direktori proyek Anda:
```bash
cp .env.example .env
```
Sesuaikan konfigurasi kunci admin (`ADMIN_KEY`) dan password database sesuai kebutuhan Anda.

### 4. Menjalankan Layanan (Docker Compose)
Bangun dan jalankan semua container secara background:
```bash
docker compose up -d --build
```

Setelah seluruh kontainer berstatus *Healthy*, Anda dapat mengakses aplikasi pada browser:
* **Aplikasi Pengguna (Frontend):** `http://localhost:5173`
* **Dokumentasi API (Swagger docs):** `http://localhost:8000/docs`
* **Dashboard Admin (Streamlit):** `http://localhost:8501`

---

## 📂 Struktur Repositori

```
rasa_idv2/
├── backend/             # FastAPI Backend (Logika API & Model Manager)
│   └── app/
│       ├── api/v1/      # Endpoint Deteksi, Feedback, dan Admin
│       ├── services/    # Manajemen Model YOLOv8 & Pencarian Gizi
│       ├── models/      # Definisi Tabel Database PostgreSQL (SQLAlchemy)
│       └── core/        # Middleware, Konfigurasi, dan Pengamanan
├── frontend/            # React + Vite (Aplikasi Web Klien)
│   └── src/
│       ├── pages/       # Analisis Foto, Tambah Manual, Laporan Harian
│       └── components/  # Komponen UI Interaktif & Overlay Bounding Box
├── admin_dashboard/     # Streamlit (Aplikasi Manajemen Admin)
│   └── views/           # Halaman Statistik, Mapping YOLO-TKPI, Import CSV
├── ml/                  # Ruang Kerja Model & Pelatihan YOLOv8
│   ├── export_model.py  # Skrip validasi weights model YOLOv8 (.pt)
│   └── runs/            # File hasil training & weights model
└── docker-compose.yml   # Konfigurasi orkestrasi kontainer Docker
```

---

## 🔄 Alur Proses Utama

### A. Deteksi Makanan Lokal & Pencarian Gizi
1. Pengguna mengunggah foto makanan melalui antarmuka web React.
2. Backend menerima file gambar dan mengirimkannya ke `ModelManager` (YOLOv8).
3. Model YOLOv8 melangsungkan inferensi lokal untuk menghasilkan klasifikasi nama makanan dan koordinat batas (*bounding box*).
4. Backend mencari kecocokan nama kelas makanan ke database gizi lokal **TKPI** melalui `yolo_tkpi_mapping`.
5. Nilai kalori dan nutrisi makro dihitung proporsional terhadap luas wilayah porsi makanan, kemudian dikembalikan ke frontend.

### B. Siklus Active Learning (Retraining Model)
1. Jika hasil klasifikasi YOLOv8 kurang tepat, pengguna memberikan koreksi manual (misal: "telur rebus" seharusnya "nasi putih").
2. Koreksi disimpan di database, lalu dikonversi secara otomatis menjadi berkas anotasi format YOLO (koordinat normalized `0-1` dan ID kelas).
3. Melalui Dashboard Admin, peneliti dapat mengunduh kumpulan gambar koreksi baru beserta berkas `.txt` labelnya sebagai format berkas **ZIP**.
4. Dataset ini digunakan untuk melatih ulang (*fine-tuning*) model YOLOv8 di lingkungan lokal komputer.
5. Model YOLOv8 hasil latih ulang baru diunggah kembali ke sistem untuk meningkatkan akurasi secara berkelanjutan.

---

## 📊 Manajemen Data Gizi TKPI (CSV Import)

Sistem menyertakan modul khusus untuk mengunggah ratusan data gizi pangan Indonesia langsung dari file spreadsheet CSV.

### Format Standar CSV TKPI
Berkas CSV harus menggunakan encoding UTF-8, pemisah tanda koma (`,`) atau titik koma (`;`), serta format desimal yang menggunakan tanda titik (`0.5`) atau koma (`0,5`).

| Kolom | Tipe Data | Status | Deskripsi |
|---|---|---|---|
| `tkpi_code` | TEXT | **Wajib** | Kode unik bahan makanan dari buku TKPI (misal: "G001") |
| `name` | TEXT | **Wajib** | Nama bahan makanan (misal: "Nasi Putih Giling") |
| `energi_kal` | FLOAT | Opsional | Nilai energi (Kalori) per 100 gram |
| `protein_g` | FLOAT | Opsional | Kandungan protein (Gram) per 100 gram |
| `lemak_g` | FLOAT | Opsional | Kandungan lemak (Gram) per 100 gram |
| `karbo_g` | FLOAT | Opsional | Kandungan karbohidrat (Gram) per 100 gram |
| `serat_g` | FLOAT | Opsional | Kandungan serat (Gram) per 100 gram |

### Langkah Melakukan Import:
1. Buka dashboard admin di browser, lalu navigasikan ke halaman **TKPI Import**.
2. Pilih file CSV data gizi Anda.
3. Klik tombol **Validate (Dry-run)** untuk memastikan format data valid tanpa ada kesalahan input.
4. Jika validasi berhasil (0 baris bermasalah), beri centang pada persetujuan database, kemudian klik tombol **Commit Import** untuk menyimpan permanen ke PostgreSQL.

---

## 🧪 Metode Pengujian Sistem

```bash
# Menjalankan pengujian fungsionalitas UI secara otomatis (Playwright)
npx playwright test frontend/e2e/

# Menjalankan uji performa inferensi YOLOv8 lokal backend
python ml/verify_model_refined.py

# Melakukan uji deteksi gambar mentah via command line (cURL)
curl -F "file=@foto_makanan.jpg" http://localhost:8000/api/v1/detect
```

---

## 📝 Catatan Teknis Runtime

* **Hot Reload Keamanan Tinggi:** Proses unggah model baru (`.pt`) melalu uji validasi format dengan mendeteksi file korup dan menguji prediksi dummy. Model lama akan terus melayani request selama proses reload berlangsung.
* **Pembatasan Sumber Daya (Concurrency Guard):** Inferensi YOLOv8 lokal backend dibatasi menggunakan `Semaphore` (maksimal 2 inferensi simultan) untuk menghemat beban kerja RAM/CPU pada server lokal.
* **Optimasi Pencarian Database:** Pencarian bahan pangan TKPI menggunakan indeks **GIN Trigram** untuk pencarian string cepat (*fuzzy search*), mempermudah pemetaan label koreksi makanan secara presisi.

---
*Terakhir diperbarui: 11 Juli 2026*
