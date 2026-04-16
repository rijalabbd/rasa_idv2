// Centralized application constants
// Prevents magic numbers scattered across codebase

export const TIMEOUTS = {
  DETECT: 30000,      // 30s for food detection API
  SEARCH: 10000,      // 10s for TKPI search
  DEFAULT: 20000,     // 20s default timeout
};

export const DEBOUNCE_DELAYS = {
  SEARCH: 500,        // 500ms debounce for search inputs
};

export const ANIMATION_DELAYS = {
  DELETE: 300,        // Animation delay before delete
  TOAST: 4000,        // Toast notification display duration
};

// Toast message constants for consistent user feedback
export const TOAST_MESSAGES = {
  EDIT_SUCCESS: 'Makanan berhasil dikoreksi',
  DELETE_SUCCESS: 'Item berhasil dihapus',
  MANUAL_ADD_SUCCESS: 'Makanan berhasil ditambahkan ke analisis',
  TRAINING_REQUEST_SUCCESS: 'Pengajuan pelatihan berhasil dikirim',
  GENERIC_ERROR: 'Terjadi kesalahan. Silakan coba lagi',
  SELECT_FOOD: 'Pilih makanan dari hasil pencarian terlebih dahulu',
  EMPTY_DETECTION: 'Tidak ada makanan terdeteksi. Coba foto dari sudut lain atau pencahayaan yang lebih baik.',
  INVALID_SCHEMA: 'Respon server tidak valid. Silakan coba lagi.',
  TIMEOUT_ERROR: 'Server tidak merespon. Silakan coba beberapa saat lagi.',
  NETWORK_ERROR: 'Gagal terhubung ke server. Periksa koneksi internet Anda.',
};
