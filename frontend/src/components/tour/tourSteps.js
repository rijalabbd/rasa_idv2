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
//   position      : 'bottom' | 'top' — posisi tooltip relatif terhadap target
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
    description:
      'Yuk, coba langsung cara kerjanya! Kamu akan dipandu langkah demi langkah mengenal semua fitur.',
    tip: 'Tour ini akan memandu kamu menggunakan sistem sesungguhnya.',
  },

  // ─── STEP 1: Upload ───────────────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'upload-zone',
    title: 'Foto Makananmu',
    description:
      'Mulai dari sini! Ambil foto piring makananmu atau pilih dari galeri. Kalau belum punya, coba pakai foto contoh kami.',
    tip: '💡 Tips: Foto dari atas dengan pencahayaan yang terang supaya hasilnya lebih akurat.',
    position: 'top',
    waitForAction: 'upload',
    fallbackTitle: 'Upload Foto Makanan',
    fallbackDesc:
      'Buka halaman Analisis untuk mulai. Kamu bisa ambil foto baru atau pilih dari galeri.',
  },

  // ─── STEP 2: Deteksi ──────────────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'detect-button',
    title: 'Mulai Deteksi!',
    description:
      'Foto sudah siap? Klik tombol ini untuk mulai deteksi. AI kami akan menganalisis makanan di foto kamu.',
    position: 'top',
    waitForAction: 'detect',
    fallbackTitle: 'Proses Deteksi AI',
    fallbackDesc:
      'Setelah foto di-upload, klik tombol Proses Deteksi untuk memulai analisis AI.',
  },

  // ─── STEP 3: Ringkasan Deteksi ────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'summary-card',
    title: 'Hasil Deteksi AI',
    description:
      'Di sini kamu bisa lihat berapa makanan yang berhasil dikenali, tingkat keyakinan AI, dan foto dengan kotak penanda posisi makanan.',
    position: 'bottom',
    waitForAction: null,
    fallbackTitle: 'Ringkasan Deteksi',
    fallbackDesc:
      'Setelah deteksi selesai, kamu akan melihat ringkasan berapa makanan yang dikenali beserta foto yang sudah ditandai.',
  },

  // ─── STEP 4: Ranking & Nutrisi ────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'ranking-card',
    title: 'Ranking Kalori & Nutrisi',
    description:
      'Makanan diurutkan dari yang paling tinggi kalorinya. Total protein, lemak, dan karbohidrat juga dihitung otomatis.',
    position: 'top',
    waitForAction: null,
    fallbackTitle: 'Ranking & Nutrisi',
    fallbackDesc:
      'Sistem akan menampilkan ranking kalori dan total nutrisi dari semua makanan yang terdeteksi.',
  },

  // ─── STEP 5: Detail Makanan ───────────────────────────────────────────────
  {
    type: 'spotlight',
    target: 'food-card',
    title: 'Detail Tiap Makanan',
    description:
      'Setiap makanan punya info nutrisi lengkap. Kamu bisa atur porsi (½, 1, 1½, 2 porsi) untuk hitungan lebih akurat, dan centang makanan yang kamu makan.',
    position: 'top',
    waitForAction: null,
    fallbackTitle: 'Detail Makanan',
    fallbackDesc:
      'Setiap makanan terdeteksi akan punya card dengan info nutrisi lengkap dan pengaturan porsi.',
  },

  // ─── STEP 6: Edit, Tambah & Request (gabungan) ────────────────────────────
  {
    type: 'spotlight',
    target: 'add-food-area',
    title: 'Edit, Tambah & Ajukan Baru',
    description:
      'Deteksi salah? Klik Edit untuk koreksi. Ada yang terlewat? Tambah manual dari database. Makanan belum dikenali? Ajukan kelas baru agar model kami belajar!',
    position: 'top',
    waitForAction: null,
    features: [
      { icon: '✏️', label: 'Edit — koreksi nama makanan yang salah' },
      { icon: '➕', label: 'Tambah — cari makanan dari database TKPI' },
      { icon: '📝', label: 'Ajukan Baru — request makanan untuk dilatih' },
    ],
    fallbackTitle: 'Koreksi & Kontribusi',
    fallbackDesc:
      'Kamu bisa mengedit, menambah, atau mengajukan makanan baru. Setiap koreksi membantu meningkatkan akurasi AI.',
  },

  // ─── STEP 7: Selesai! ─────────────────────────────────────────────────────
  {
    type: 'fullscreen',
    icon: '🎉',
    iconBg: 'linear-gradient(135deg, #22c55e 0%, #059669 100%)',
    title: 'Kamu Sudah Siap!',
    description:
      'Sekarang coba sendiri! Setiap koreksi yang kamu berikan membantu sistem kami jadi lebih pintar untuk semua pengguna.',
    tip: 'Kamu bisa buka panduan ini lagi kapan saja lewat tombol "Panduan" di halaman utama.',
  },
];

export default TOUR_STEPS;
