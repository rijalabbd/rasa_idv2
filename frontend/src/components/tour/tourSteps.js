// frontend/src/components/tour/tourSteps.js
// ─── Tour Step Configuration ────────────────────────────────────────────────
// Semua 10 step dikonfigurasi di sini. Edit konten tour tanpa sentuh komponen.
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

  // ─── STEP 6: Koreksi / Edit ───────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'edit-button',
    title: '✏️ Koreksi Makanan',
    description: 'AI salah menebak? Klik "Edit" lalu ketik nama makanan yang benar. Koreksimu membantu AI belajar!',
    waitForAction: null,
    fallbackTitle: 'Koreksi Makanan',
    fallbackDesc: 'Gunakan tombol Edit di kartu makanan untuk mengganti nama yang salah.',
  },

  // ─── STEP 7: Tambah / Missed Detection ────────────────────────────────────
  {
    type: 'spotlight',
    target: 'add-food-area',
    title: '➕ Tambah Makanan',
    description: 'Ada makanan di piringmu yang tidak terdeteksi? Cari secara manual dengan mengetik namanya di sini.',
    waitForAction: null,
    fallbackTitle: 'Tambah Manual',
    fallbackDesc: 'Makanan tidak terdeteksi? Cari manual dengan nama.',
  },

  // ─── STEP 8: Ajukan Kelas Baru / Request Class ────────────────────────────
  {
    type: 'spotlight',
    target: 'request-class',
    title: '📝 Ajukan Makanan Baru',
    description: 'Makanan khasmu belum dikenal sama sekali? Ajukan namanya agar bisa kami latih untuk dikenali di masa depan.',
    waitForAction: null,
    fallbackTitle: 'Request Kelas Baru',
    fallbackDesc: 'Ajukan makanan baru agar dilatih oleh AI kami.',
  },

  // ─── STEP 9: Selesai! ─────────────────────────────────────────────────────
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
