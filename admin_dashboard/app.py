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
# Session State Initialization
# =============================================================================

if "summary_data" not in st.session_state:
    st.session_state.summary_data = None
if "summary_error" not in st.session_state:
    st.session_state.summary_error = None

if "export_zip_bytes" not in st.session_state:
    st.session_state.export_zip_bytes = None
if "export_filename" not in st.session_state:
    st.session_state.export_filename = None
if "export_message" not in st.session_state:
    st.session_state.export_message = None
if "export_error" not in st.session_state:
    st.session_state.export_error = None
if "export_file_list" not in st.session_state:
    st.session_state.export_file_list = []

for key in ("yolo_feedback_zip", "yolo_feedback_msg", "yolo_feedback_err", "yolo_feedback_files"):
    if key not in st.session_state:
        st.session_state[key] = [] if key.endswith("_files") else None

for key in ("yolo_class-requests_zip", "yolo_class-requests_msg", "yolo_class-requests_err", "yolo_class-requests_files"):
    if key not in st.session_state:
        st.session_state[key] = [] if key.endswith("_files") else None

if "model_status" not in st.session_state:
    st.session_state.model_status = None
if "model_status_error" not in st.session_state:
    st.session_state.model_status_error = None
if "upload_message" not in st.session_state:
    st.session_state.upload_message = None
if "upload_error" not in st.session_state:
    st.session_state.upload_error = None

if "ping_message" not in st.session_state:
    st.session_state.ping_message = None
if "ping_error" not in st.session_state:
    st.session_state.ping_error = None

if "last_request_info" not in st.session_state:
    st.session_state.last_request_info = None
if "last_request_id" not in st.session_state:
    st.session_state.last_request_id = None

if "mapping_list" not in st.session_state:
    st.session_state.mapping_list = None
if "mapping_list_error" not in st.session_state:
    st.session_state.mapping_list_error = None
if "mapping_save_message" not in st.session_state:
    st.session_state.mapping_save_message = None
if "mapping_save_error" not in st.session_state:
    st.session_state.mapping_save_error = None
if "tkpi_search_results" not in st.session_state:
    st.session_state.tkpi_search_results = []

for key in ("tkpi_import_result", "tkpi_import_ref", "tkpi_commit_result", "tkpi_commit_ref", "tkpi_validated_hash", "tkpi_preview_data"):
    if key not in st.session_state:
        st.session_state[key] = None

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
        "Dashboard":       "activity",
        "Mappings":        "link",
        "TKPI Import":     "database",
        "Export Dataset":  "package",
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
        icon_md("wrench", "**Tools**", size=14),
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
    with st.expander("Request Debugger"):
        st.markdown(
            icon_md("search", "Last Request", size=13),
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
            st.caption("No requests made yet.")


# =============================================================================
# Main Content Router
# =============================================================================

if selected_page == "Dashboard":
    render_dashboard()
elif selected_page == "Mappings":
    render_mappings()
elif selected_page == "TKPI Import":
    render_tkpi_import()
elif selected_page == "Export Dataset":
    render_export()

# Footer
st.divider()
st.caption("RASA-ID Admin Dashboard")
