import pandas as pd
import streamlit as st
from utils.api import api_request, format_datetime
from utils.icons import h1, h2, labeled_section, icon_md

# =============================================================================
# Functions: Dashboard Data Fetching
# =============================================================================

def fetch_summary():
    """Fetch summary data and store in session_state."""
    data, status, _, _ = api_request("GET", "/admin/summary")
    if status == 200 and data:
        st.session_state.summary_data = data
        st.session_state.summary_error = None
    else:
        st.session_state.summary_data = None
        st.session_state.summary_error = f"HTTP {status}" if status > 0 else "Request failed"


def fetch_model_classes():
    """Fetch YOLO class list from backend and store in session_state."""
    data, status, _, _ = api_request("GET", "/admin/model/classes")
    if status == 200 and data:
        st.session_state.model_classes = data.get("classes", [])
        st.session_state.model_classes_loaded = data.get("loaded", False)
        st.session_state.model_classes_error = None
    else:
        st.session_state.model_classes = []
        st.session_state.model_classes_loaded = False
        st.session_state.model_classes_error = f"HTTP {status}" if status > 0 else "Request failed"


def fetch_model_status():
    """Fetch model status and store in session_state."""
    data, status, _, _ = api_request("GET", "/admin/model/status")
    if status == 200 and data:
        st.session_state.model_status = data
        st.session_state.model_status_error = None
    else:
        st.session_state.model_status = None
        st.session_state.model_status_error = f"HTTP {status}" if status > 0 else "Request failed"


def fetch_settings():
    """Fetch admin settings (detection mode and Gemini API Key configuration)."""
    data, status, _, _ = api_request("GET", "/admin/settings")
    if status == 200 and data:
        st.session_state.settings_data = data
        st.session_state.settings_error = None
    else:
        st.session_state.settings_data = None
        st.session_state.settings_error = f"HTTP {status}" if status > 0 else "Request failed"


def save_settings(detection_mode: str):
    """Save active detection mode to backend."""
    payload = {"detection_mode": detection_mode}
    data, status, _, _ = api_request("POST", "/admin/settings", json=payload)
    if status == 200:
        st.toast("Pengaturan berhasil disimpan!")
        fetch_settings()
        st.rerun()
    else:
        st.error(f"Gagal menyimpan pengaturan: {data.get('detail') if isinstance(data, dict) else data}")


def _fmt_size(b: int | None) -> str:
    """Format bytes to human-readable string."""
    if b is None:
        return "N/A"
    if b < 1024:
        return f"{b} B"
    if b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    return f"{b / (1024 * 1024):.2f} MB"


def do_upload_model(uploaded_file):
    """Upload model file and store result in session_state."""
    st.session_state.upload_message = None
    st.session_state.upload_error = None

    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}

    with st.spinner("Uploading & validating model..."):
        data, status, headers, _ = api_request("POST", "/admin/model/upload", files=files, timeout=120)

    req_id = ""
    if hasattr(headers, "get"):
        req_id = headers.get("x-request-id", "")

    if status == 200 and data:
        size_str = _fmt_size(data.get('size_bytes'))
        sha = data.get('sha256', '')[:12]
        msg = (
            f"Model `{data.get('active_model')}` hot-reloaded! "
            f"Size: {size_str} | SHA256: {sha}... | "
            f"Loaded: {format_datetime(data.get('loaded_at'))}"
        )
        if req_id:
            msg += f" (Ref: {req_id})"
        st.session_state.upload_message = msg
        fetch_model_status()
        fetch_model_classes()
    else:
        detail = ''
        code = ''
        if isinstance(data, dict):
            detail = data.get('detail', '')
            code = data.get('code', '')

        err_parts = []
        if status > 0:
            err_parts.append(f"HTTP {status}")
        if code:
            err_parts.append(code)
        if detail:
            err_parts.append(detail)
        if req_id:
            err_parts.append(f"(Ref: {req_id})")

        st.session_state.upload_error = " — ".join(err_parts) if err_parts else "Request failed"


def render_dashboard():
    """Render the Main Dashboard view."""

    # Page title with icon
    st.markdown(h1("activity", "Ringkasan Dashboard"), unsafe_allow_html=True)
    st.divider()

    # Initial Data Load
    if "settings_data" not in st.session_state:
        st.session_state.settings_data = None
        st.session_state.settings_error = None

    if st.session_state.summary_data is None and st.session_state.summary_error is None:
        fetch_summary()

    if st.session_state.model_status is None and st.session_state.model_status_error is None:
        fetch_model_status()
        fetch_model_classes()

    if st.session_state.settings_data is None and st.session_state.settings_error is None:
        fetch_settings()

    # -------------------------------------------------------------------------
    # Summary Section
    # -------------------------------------------------------------------------

    st.markdown(h2("bar-chart-2", "Statistik Ringkasan"), unsafe_allow_html=True)

    if st.button("🔄 Perbarui Data", key="refresh_all_btn"):
        fetch_summary()
        fetch_model_status()
        fetch_model_classes()
        fetch_settings()
        st.rerun()

    col1, col2, col3, col4, col5 = st.columns(5)

    summary = st.session_state.summary_data

    with col1:
        st.metric(
            label="Total Feedback",
            value=summary.get("feedback_total", 0) if summary else "-"
        )

    with col2:
        st.metric(
            label="Feedback Tertunda",
            value=summary.get("feedback_pending", 0) if summary else "-",
            help="Total feedback koreksi makanan dari pengguna yang belum diekspor."
        )

    with col3:
        st.metric(
            label="Total Class Requests",
            value=summary.get("class_requests_total", 0) if summary else "-"
        )

    with col4:
        st.metric(
            label="Class Requests Tertunda",
            value=summary.get("class_requests_pending", 0) if summary else "-",
            help="Total usulan kelas makanan baru yang belum diekspor."
        )

    with col5:
        st.metric(
            label="Missed Detections",
            value=summary.get("missed_detections_total", 0) if summary else "-",
            help="Makanan yang terlewat oleh AI, ditambahkan secara manual oleh pengguna."
        )

    if st.session_state.summary_error:
        st.warning(f"Gagal memuat statistik ringkasan: {st.session_state.summary_error}")

    st.divider()

    # -------------------------------------------------------------------------
    # Model Management Section
    # -------------------------------------------------------------------------

    st.markdown(h2("cpu", "Manajemen Model YOLO"), unsafe_allow_html=True)

    model_col1, model_col2 = st.columns(2)

    # Model Status Panel
    with model_col1:
        st.markdown(labeled_section("monitor", "Status Model Aktif"), unsafe_allow_html=True)

        if st.button("Segarkan Status", key="refresh_model_btn"):
            fetch_model_status()
            st.rerun()

        status = st.session_state.model_status

        if status:
            active_model = status.get("active_model")
            loaded_at = status.get("loaded_at")
            size_bytes = status.get("size_bytes")
            sha256 = status.get("sha256", "") or ""
            ready = status.get("ready", False)

            if active_model and ready:
                st.info(f"**Model YOLO Aktif:** `{active_model}`")
                st.caption(
                    f"Ukuran: {_fmt_size(size_bytes)} | "
                    f"SHA256: {sha256[:12]}... | "
                    f"Dimuat Pada: {format_datetime(loaded_at)}"
                )
            elif active_model and not ready:
                st.warning(f"Model `{active_model}` terdeteksi tetapi tidak aktif.")
            else:
                st.warning("File model aktif tidak ditemukan (active.pt tidak ada).")
                st.caption("Silakan unggah file model .pt baru di panel unggahan.")
        elif st.session_state.model_status_error:
            st.error(st.session_state.model_status_error)
        else:
            st.info("Memuat status model...")

    # Model Upload Panel
    with model_col2:
        st.markdown(labeled_section("upload", "Unggah Model Baru"), unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Pilih file model (.pt)",
            type=["pt"],
            key="model_uploader",
            help="Unggah file model PyTorch YOLO (.pt) hasil retraining."
        )

        if uploaded_file is not None:
            st.caption(f"Terpilih: `{uploaded_file.name}` ({uploaded_file.size:,} bytes)")

            if st.button("Unggah & Aktifkan Model", key="upload_model_btn", type="primary"):
                do_upload_model(uploaded_file)
                st.rerun()

        if st.session_state.upload_message:
            st.success(st.session_state.upload_message)
        if st.session_state.upload_error:
            st.error(st.session_state.upload_error)

    # -------------------------------------------------------------------------
    # Detection Mode Configuration Section (Hidden behind secret unlock)
    # -------------------------------------------------------------------------
    st.divider()
    
    # Initialize secret counter in session state
    if "secret_mode_clicks" not in st.session_state:
        st.session_state.secret_mode_clicks = 0
    if "secret_mode_unlocked" not in st.session_state:
        st.session_state.secret_mode_unlocked = False
    
    # Secret unlock: clicking the version label 5 times reveals the panel
    ver_col1, ver_col2 = st.columns([4, 1])
    with ver_col1:
        st.caption("Sistem Deteksi: Model Lokal v2.0")
    with ver_col2:
        if st.button("ℹ️", key="secret_mode_toggle", help="Informasi versi"):
            st.session_state.secret_mode_clicks += 1
            if st.session_state.secret_mode_clicks >= 5:
                st.session_state.secret_mode_unlocked = not st.session_state.secret_mode_unlocked
                st.session_state.secret_mode_clicks = 0
            st.rerun()
    
    if st.session_state.secret_mode_unlocked:
        st.markdown(h2("settings", "Pengaturan Mode Deteksi"), unsafe_allow_html=True)
        
        settings_data = st.session_state.settings_data
        
        if settings_data:
            curr_mode = settings_data.get("detection_mode", "YOLO")
            has_key = settings_data.get("has_gemini_key", False)
            
            mode_col1, mode_col2 = st.columns([3, 1])
            
            with mode_col1:
                mode_options = {
                    "YOLO": "YOLO (Model Lokal - Cepat & Luring)",
                    "GEMINI": "Cloud API (Multimodal - Dinamis & Cerdas)"
                }
                idx = 0 if curr_mode == "YOLO" else 1
                
                selected_mode = st.radio(
                    "Pilih Mode Deteksi Aktif:",
                    options=list(mode_options.keys()),
                    format_func=lambda m: mode_options[m],
                    index=idx,
                    horizontal=True,
                    key="active_detection_mode_radio"
                )
                
                if selected_mode == "GEMINI":
                    if not has_key:
                        st.error("⚠️ **Peringatan:** Kunci API Cloud tidak terdeteksi di server. Mode ini tidak akan berfungsi sebelum kunci API ditambahkan.")
                    else:
                        st.success("✅ Kunci API Cloud terkonfigurasi di server. Siap digunakan.")
                else:
                    st.info("ℹ️ Mode YOLO menggunakan model lokal `active.pt` yang diunggah di atas.")
                    
            with mode_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Simpan Mode Deteksi", key="save_settings_btn", use_container_width=True, type="primary"):
                    save_settings(selected_mode)
                    
        elif st.session_state.settings_error:
            st.error(f"Gagal memuat pengaturan mode deteksi: {st.session_state.settings_error}")
        else:
            st.info("Memuat pengaturan...")

    # -------------------------------------------------------------------------
    # Active Model Classes Table
    # -------------------------------------------------------------------------
    st.divider()
    st.markdown(h2("list", "Kelas Makanan Aktif"), unsafe_allow_html=True)
    
    col_classes_1, col_classes_2 = st.columns([3, 1])
    with col_classes_1:
        st.markdown("Daftar kelas makanan yang saat ini dapat dideteksi oleh model YOLO aktif:")
    with col_classes_2:
        if st.button("Perbarui Daftar Kelas", key="refresh_classes_btn"):
            fetch_model_classes()
            st.rerun()

    if getattr(st.session_state, "model_classes_error", None):
        st.error(f"Gagal memuat kelas model: {st.session_state.model_classes_error}")
    elif not getattr(st.session_state, "model_classes_loaded", False) and not getattr(st.session_state, "model_classes", []):
        st.info("Kelas tidak ditemukan. Pastikan file model aktif (active.pt) sudah diunggah.")
    else:
        classes = getattr(st.session_state, "model_classes", [])
        if classes:
            df = pd.DataFrame(classes)
            if 'id' in df.columns and 'name' in df.columns:
                df = df[['id', 'name']]
                df.columns = ["ID Kelas", "Nama Kelas"]
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Active model does not have any classes.")
