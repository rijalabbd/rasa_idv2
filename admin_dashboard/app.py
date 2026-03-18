"""
RASA-ID Admin Dashboard MVP
Single-file Streamlit application for admin operations.

Features:
- View summary counts (feedback & class request)
- Download dataset ZIPs (feedback/class request)
- Upload and activate new model
- View current model status

Run with: streamlit run app.py
"""

import streamlit as st
from utils.api import api_request
from views.dashboard import render_dashboard
from views.mappings import render_mappings
from views.export import render_export
from views.tkpi_import import render_tkpi_import

# =============================================================================
# Page Configuration (MUST BE FIRST)
# # =============================================================================

st.set_page_config(
    page_title="RASA-ID Admin Dashboard",
    page_icon="🍚",
    layout="wide"
)

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

# YOLO feedback export
for key in ("yolo_feedback_zip", "yolo_feedback_msg", "yolo_feedback_err", "yolo_feedback_files"):
    if key not in st.session_state:
        st.session_state[key] = [] if key.endswith("_files") else None

# YOLO class-request export
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

# TKPI Import
for key in ("tkpi_import_result", "tkpi_import_ref", "tkpi_commit_result", "tkpi_commit_ref", "tkpi_validated_hash", "tkpi_preview_data"):
    if key not in st.session_state:
        st.session_state[key] = None

# =============================================================================
# Sidebar Logic
# =============================================================================

def do_ping_api():
    """Ping the API health endpoint."""
    _, status, _, _ = api_request("GET", "/health", timeout=10)
    if status == 200:
        st.session_state.ping_message = "✅ API online"
        st.session_state.ping_error = None
    else:
        st.session_state.ping_message = None
        st.session_state.ping_error = f"API responded with status {status}"

with st.sidebar:
    st.title("🍚 RASA-ID")
    
    # Navigation
    st.markdown("### Menu")
    selected_page = st.radio(
        "Go to",
        ["Dashboard", "Mappings", "TKPI Import", "Export Dataset"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    st.header("🔧 Tools")
    
    # Quick Health Check
    if st.button("Ping API Health", use_container_width=True):
        do_ping_api()
        
    if st.session_state.ping_message:
        st.success(st.session_state.ping_message, icon="✅")
    if st.session_state.ping_error:
        st.error(st.session_state.ping_error, icon="❌")
        
    # Request Debugger
    with st.expander("🔍 Request Debugger"):
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

# Footer on every page
st.divider()
st.caption("RASA-ID Admin Dashboard MVP • No authentication required")
