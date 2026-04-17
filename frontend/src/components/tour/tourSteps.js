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
    description: 'Yuk, coba langsung! Kamu akan dipandu langkah demi langkah mengenal semua fitur.',
    tip: 'Tour ini memandu kamu menggunakan sistem sesungguhnya.',
  },

  // ─── STEP 1: Upload ───────────────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'upload-zone',
    title: '📸 Upload Foto',
    description: 'Ambil foto makananmu atau pilih dari galeri. Belum punya? Pakai foto contoh dari kami.',
    tip: '💡 Foto dari atas, cahaya terang = hasil lebih akurat!',
    waitForAction: 'upload',
    fallbackTitle: 'Upload Foto Makanan',
    fallbackDesc: 'Buka halaman Analisis untuk mulai.',
  },

  // ─── STEP 2: Deteksi ──────────────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'detect-button',
    title: '🔍 Mulai Deteksi',
    description: 'Klik tombol ini dan AI akan langsung mengenali makanan di fotomu.',
    waitForAction: 'detect',
    fallbackTitle: 'Proses Deteksi AI',
    fallbackDesc: 'Klik tombol Proses Deteksi untuk memulai.',
  },

  // ─── STEP 3: Ringkasan Deteksi ────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'summary-card',
    title: '📊 Hasil Deteksi',
    description: 'Lihat jumlah makanan yang terdeteksi dan tingkat akurasi AI di sini.',
    waitForAction: null,
    fallbackTitle: 'Ringkasan Deteksi',
    fallbackDesc: 'Ringkasan makanan yang berhasil dikenali.',
  },

  // ─── STEP 4: Ranking & Nutrisi ────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'ranking-card',
    title: '🏆 Ranking Kalori',
    description: 'Makanan diurutkan dari kalori terbesar. Total protein, lemak, dan karbo juga ditampilkan.',
    waitForAction: null,
    fallbackTitle: 'Ranking & Nutrisi',
    fallbackDesc: 'Lihat urutan kalori dan total nutrisi.',
  },

  // ─── STEP 5: Detail Makanan ───────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'food-card',
    title: '🍛 Detail Makanan',
    description: 'Tiap makanan punya info nutrisi lengkap. Atur porsi (½–2) agar hitungan lebih sesuai piringmu.',
    waitForAction: null,
    fallbackTitle: 'Detail Makanan',
    fallbackDesc: 'Cek dan atur porsi di tiap kartu makanan.',
  },

  // ─── STEP 6: Koreksi, Tambah & Request ────────────────────────────────────
  {
    type: 'spotlight',
    target: 'add-food-area',
    title: '✏️ Koreksi & Tambah',
    description: 'AI tidak sempurna! Bantu kami belajar dari koreksimu:',
    waitForAction: null,
    features: [
      { icon: '✏️', label: 'Edit — AI salah tebak? Ganti ke nama yang benar' },
      { icon: '➕', label: 'Tambah — makanan tidak terdeteksi? Cari manual dengan nama' },
      { icon: '📝', label: 'Ajukan — belum ada di sistem? Minta kami tambahkan' },
    ],
    fallbackTitle: 'Koreksi & Kontribusi',
    fallbackDesc: 'Edit atau tambah makanan agar AI makin pintar.',
  },

  // ─── STEP 7: Selesai! ─────────────────────────────────────────────────────
  {
    type: 'fullscreen',
    icon: '🎉',
    iconBg: 'linear-gradient(135deg, #22c55e 0%, #059669 100%)',
    title: 'Kamu Sudah Siap!',
    description: 'Sekarang coba sendiri! Setiap koreksimu membantu AI kami jadi lebih cerdas.',
    tip: 'Buka panduan ini lagi lewat tombol "Panduan" di menu utama.',
  },
];

export default TOUR_STEPS;
