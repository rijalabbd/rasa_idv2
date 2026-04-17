// frontend/src/components/tour/tourSteps.js
// ─── Tour Step Configuration ────────────────────────────────────────────────
// Semua 8 step dikonfigurasi di sini. Edit konten tour tanpa sentuh komponen.
//
// Fields:
//   type          : 'fullscreen' | 'spotlight'
//   target        : data-tour attribute value (untuk spotlight)
//   title         : Judul step
//   description   : Penjelasan singkat
//   tip           : (opsional) Tips tambahan
//   waitForAction : 'upload' | 'detect' | null — auto-advance setelah aksi ini
//   features      : (opsional) List fitur untuk step gabungan
//   fallbackTitle : Judul jika elemen target tidak ditemukan
//   fallbackDesc  : Deskripsi jika elemen target tidak ditemukan
// ─────────────────────────────────────────────────────────────────────────────

const TOUR_STEPS = [
  // ─── STEP 0: Welcome ──────────────────────────────────────────────────────
  {
    type: 'fullscreen',
    icon: '🍽️',
    iconBg: 'linear-gradient(135deg, #22c55e 0%, #15803d 100%)',
    title: 'Selamat Datang di RASA-ID!',
    description: 'Yuk, coba langsung cara kerjanya! Kamu akan dipandu langkah demi langkah mengenal semua fitur.',
    tip: 'Tour ini memandu kamu menggunakan sistem sesungguhnya.',
  },

  // ─── STEP 1: Upload ───────────────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'upload-zone',
    title: 'Foto Makananmu',
    description: 'Ambil foto piring makananmu atau pilih dari galeri. Belum punya? Pakai foto contoh kami.',
    tip: '💡 Tips: Foto dari atas dengan cahaya terang untuk hasil akurat.',
    waitForAction: 'upload',
    fallbackTitle: 'Upload Foto Makanan',
    fallbackDesc: 'Buka halaman Analisis untuk mulai memfoto.',
  },

  // ─── STEP 2: Deteksi ──────────────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'detect-button',
    title: 'Mulai Deteksi!',
    description: 'Klik tombol ini agar AI mulai menganalisis foto makanan kamu.',
    waitForAction: 'detect',
    fallbackTitle: 'Proses Deteksi AI',
    fallbackDesc: 'Klik tombol Proses Deteksi untuk memulai.',
  },

  // ─── STEP 3: Ringkasan Deteksi ────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'summary-card',
    title: 'Hasil Deteksi AI',
    description: 'Lihat jumlah makanan yang dikenali, tingkat akurasi, dan kotak penanda posisinya di sini.',
    waitForAction: null,
    fallbackTitle: 'Ringkasan Deteksi',
    fallbackDesc: 'Cek ringkasan makanan yang berhasil ditandai.',
  },

  // ─── STEP 4: Ranking & Nutrisi ────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'ranking-card',
    title: 'Ranking Kalori & Nutrisi',
    description: 'Makanan diurutkan dari kalori tertinggi. Total gizi harianmu juga dihitung otomatis.',
    waitForAction: null,
    fallbackTitle: 'Ranking & Nutrisi',
    fallbackDesc: 'Lihat ranking kalori dan total nutrisi keseluruhan.',
  },

  // ─── STEP 5: Detail Makanan ───────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'food-card',
    title: 'Detail Makanan',
    description: 'Cek kalori spesifik dan atur porsi (1/2, 1, 2) agar hitungan lebih pas dengan piringmu.',
    waitForAction: null,
    fallbackTitle: 'Detail Makanan',
    fallbackDesc: 'Atur porsi pada tiap kartu makanan.',
  },

  // ─── STEP 6: Edit, Tambah & Request ───────────────────────────────────────
  {
    type: 'spotlight',
    target: 'add-food-area',
    title: 'Koreksi & Tambah Data',
    description: 'AI salah tebak? Bantu kami jadi lebih pintar!',
    waitForAction: null,
    features: [
      { icon: '✏️', label: 'Edit — ganti nama makanan yang salah' },
      { icon: '➕', label: 'Tambah — cari manual ke database' },
      { icon: '📝', label: 'Ajukan — request ke kami jika belum ada' },
    ],
    fallbackTitle: 'Koreksi & Kontribusi',
    fallbackDesc: 'Edit, tambah, atau ajukan makanan baru ke AI.',
  },

  // ─── STEP 7: Selesai! ─────────────────────────────────────────────────────
  {
    type: 'fullscreen',
    icon: '🎉',
    iconBg: 'linear-gradient(135deg, #22c55e 0%, #059669 100%)',
    title: 'Bagus Sekali!',
    description: 'Sekarang kamu siap menganalisis makanan sendiri. Partisipasimu melatih AI kami makin cerdas.',
    tip: 'Buka panduan ini lagi lewat tombol "Panduan" di menu utama.',
  },
];

export default TOUR_STEPS;
