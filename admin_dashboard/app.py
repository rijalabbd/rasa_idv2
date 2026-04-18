"""
RASA-ID Admin Dashboard
Single-file Streamlit application for admin operations.

Run with: streamlit run app.py
"""

import os
import hashlib
import streamlit as st
from utils.api import api_request
from utils.icons import icon_md, icon_html
from views.dashboard import render_dashboard
from views.mappings import render_mappings
from views.export import render_export
from views.tkpi_import import render_tkpi_import
import extra_streamlit_components as stx

def get_cookie_manager():
    return stx.CookieManager(key="admin_cookie_manager")

# =============================================================================
# Page Configuration (MUST BE FIRST)
# =============================================================================

st.set_page_config(
    page_title="RASA-ID Admin Dashboard",
    page_icon=":material/admin_panel_settings:",
    layout="wide"
)

# =============================================================================
# Login Gate
# =============================================================================

def _check_password(input_password: str) -> bool:
    """
    Bandingkan password yang diinput dengan DASHBOARD_PASSWORD di env.
    Pakai perbandingan hash agar aman dari timing attack.
    """
    correct = os.environ.get("DASHBOARD_PASSWORD", "").replace('"', '').replace("'", "").strip()
    if not correct:
        st.error(
            "⚠️ **`DASHBOARD_PASSWORD` belum di-set di server.** "
            "Tambahkan ke file `.env` lalu restart dashboard."
        )
        st.stop()
    # Hash keduanya agar tidak bisa ditebak dari waktu respons
    input_hash   = hashlib.sha256(input_password.encode()).hexdigest()
    correct_hash = hashlib.sha256(correct.encode()).hexdigest()
    return input_hash == correct_hash


def _render_login_page():
    """Tampilkan halaman login."""
    col_left, col_center, col_right = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<h2 style='text-align:center;'>🔐 RASA-ID Admin</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:gray;'>Masukkan password untuk melanjutkan</p>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=True):
            password = st.text_input(
                "Password Admin",
                type="password",
                placeholder="Masukkan password...",
            )
            submitted = st.form_submit_button("Masuk", use_container_width=True)

        if submitted:
            if _check_password(password):
                # Set cookie that expires in 1 day
                cookie_manager.set("admin_auth", "true", max_age=86400)
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Password salah. Coba lagi.")


cookie_manager = get_cookie_manager()

# Cek autentikasi dari session atau cookie
if "authenticated" not in st.session_state:
    # Try reading from cookie manager. If it returns "true", the user is auth'd.
    # Note: on first render, cookie_manager might return None for a fraction of a second.
    cookie_val = cookie_manager.get("admin_auth")
    if cookie_val == "true":
        st.session_state["authenticated"] = True
    else:
        st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    # Check again if cookie is just being loaded to prevent flash of login screen
    if cookie_manager.get("admin_auth") == "true":
        st.session_state["authenticated"] = True
        st.rerun()
    else:
        _render_login_page()
        st.stop()  # Hentikan eksekusi — konten dashboard tidak akan dirender

# =============================================================================
# Session State Initialization (compact)
# =============================================================================

_SESSION_DEFAULTS = {
    # Dashboard
    "summary_data": None, "summary_error": None,
    "model_status": None, "model_status_error": None,
    "upload_message": None, "upload_error": None,
    # Export
    "export_zip_bytes": None, "export_filename": None,
    "export_message": None, "export_error": None,
    "export_file_list": [],
    "yolo_feedback_zip": None, "yolo_feedback_msg": None,
    "yolo_feedback_err": None, "yolo_feedback_files": [],
    "yolo_class-requests_zip": None, "yolo_class-requests_msg": None,
    "yolo_class-requests_err": None, "yolo_class-requests_files": [],
    "yolo_missed_zip": None, "yolo_missed_msg": None,
    "yolo_missed_err": None, "yolo_missed_files": [],
    # Sidebar / debug
    "ping_message": None, "ping_error": None,
    "last_request_info": None, "last_request_id": None,
    # Mappings
    "mapping_list": None, "mapping_list_error": None,
    "mapping_save_message": None, "mapping_save_error": None,
    "tkpi_search_results": [],
    # TKPI Import
    "tkpi_import_result": None, "tkpi_import_ref": None,
    "tkpi_commit_result": None, "tkpi_commit_ref": None,
    "tkpi_validated_hash": None, "tkpi_preview_data": None,
}

for _k, _v in _SESSION_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# =============================================================================
# Sidebar
# =============================================================================

def do_ping_api():
    """Ping the API health endpoint."""
    _, status, _, _ = api_request("GET", "/health", timeout=10)
    if status == 200:
        st.session_state.ping_message = "API online"
        st.session_state.ping_error = None
    else:
        st.session_state.ping_message = None
        st.session_state.ping_error = f"API responded with status {status}"

with st.sidebar:
    # Brand
    st.markdown(
        icon_md("activity", "**RASA-ID**", size=20),
        unsafe_allow_html=True,
    )

    # Tombol Logout
    if st.button("🔓 Logout", use_container_width=True):
        cookie_manager.delete("admin_auth")
        st.session_state["authenticated"] = False
        st.rerun()

    st.markdown("---")

    # Navigation label with icon
    st.markdown(
        icon_md("layout-dashboard", "Menu", size=14),
        unsafe_allow_html=True,
    )

    # Page navigation
    _nav_icons = {
        "Dashboard":         "activity",
        "Pencocokan":        "link",
        "Import TKPI":       "database",
        "Ekspor Dataset":    "package",
    }
    selected_page = st.radio(
        "Go to",
        list(_nav_icons.keys()),
        label_visibility="collapsed",
        format_func=lambda p: p,
    )

    st.divider()

    # Tools section
    st.markdown(
        icon_md("wrench", "**Alat**", size=14),
        unsafe_allow_html=True,
    )

    if st.button("Ping API Health", use_container_width=True):
        do_ping_api()

    if st.session_state.ping_message:
        st.markdown(
            icon_md("check-circle", st.session_state.ping_message, size=14, color="#2e7d32"),
            unsafe_allow_html=True,
        )
    if st.session_state.ping_error:
        st.markdown(
            icon_md("x-circle", st.session_state.ping_error, size=14, color="#c62828"),
            unsafe_allow_html=True,
        )

    # Request Debugger
    with st.expander("Debug Request"):
        st.markdown(
            icon_md("search", "Request Terakhir", size=13),
            unsafe_allow_html=True,
        )
        if st.session_state.last_request_info:
            info = st.session_state.last_request_info
            st.markdown(f"**Method**: `{info['method']}`")
            st.markdown(f"**URL**: `{info['url']}`")
            st.caption(f"Time: {info['time']}")
            req_id = st.session_state.last_request_id
            if req_id:
                st.code(req_id, language=None)
                st.caption("Request ID (Header)")
        else:
            st.caption("Belum ada request.")


# =============================================================================
# Main Content Router
# =============================================================================

if selected_page == "Dashboard":
    render_dashboard()
elif selected_page == "Pencocokan":
    render_mappings()
elif selected_page == "Import TKPI":
    render_tkpi_import()
elif selected_page == "Ekspor Dataset":
    render_export()

# Footer
st.divider()
st.caption("RASA-ID Admin Dashboard")
