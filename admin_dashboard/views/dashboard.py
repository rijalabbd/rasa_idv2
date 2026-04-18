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
    st.markdown(h1("activity", "Dashboard Overview"), unsafe_allow_html=True)
    st.divider()

    # Initial Data Load
    if st.session_state.summary_data is None and st.session_state.summary_error is None:
        fetch_summary()

    if st.session_state.model_status is None and st.session_state.model_status_error is None:
        fetch_model_status()
        fetch_model_classes()

    # -------------------------------------------------------------------------
    # Summary Section
    # -------------------------------------------------------------------------

    st.markdown(h2("bar-chart-2", "Summary Statistics"), unsafe_allow_html=True)

    if st.button("Refresh Summary", key="refresh_summary_btn"):
        fetch_summary()
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
            label="Pending Feedback",
            value=summary.get("feedback_pending", 0) if summary else "-",
            help="is_processed = false"
        )

    with col3:
        st.metric(
            label="Total Class Requests",
            value=summary.get("class_requests_total", 0) if summary else "-"
        )

    with col4:
        st.metric(
            label="Pending Class Requests",
            value=summary.get("class_requests_pending", 0) if summary else "-",
            help="is_exported = false"
        )

    with col5:
        st.metric(
            label="Missed Detections",
            value=summary.get("missed_detections_total", 0) if summary else "-",
            help="Model failed to detect, user added manually"
        )

    if st.session_state.summary_error:
        st.warning(f"Summary fetch error: {st.session_state.summary_error}")

    st.divider()

    # -------------------------------------------------------------------------
    # Model Management Section
    # -------------------------------------------------------------------------

    st.markdown(h2("cpu", "Model Management"), unsafe_allow_html=True)

    model_col1, model_col2 = st.columns(2)

    # Model Status Panel
    with model_col1:
        st.markdown(labeled_section("monitor", "Current Model Status"), unsafe_allow_html=True)

        if st.button("Refresh Status", key="refresh_model_btn"):
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
                st.info(f"**Active Model:** `{active_model}`")
                st.caption(
                    f"Size: {_fmt_size(size_bytes)} | "
                    f"SHA256: {sha256[:12]}... | "
                    f"Loaded: {format_datetime(loaded_at)}"
                )
            elif active_model and not ready:
                st.warning(f"Model `{active_model}` found but not loaded yet")
            else:
                st.warning("No active model file found (active.pt missing)")
                st.caption("Upload a .pt model to activate it")
        elif st.session_state.model_status_error:
            st.error(st.session_state.model_status_error)
        else:
            st.info("Loading status...")

    # Model Upload Panel
    with model_col2:
        st.markdown(labeled_section("upload", "Upload New Model"), unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Choose a .pt file",
            type=["pt"],
            key="model_uploader",
            help="Upload a PyTorch model file (.pt)"
        )

        if uploaded_file is not None:
            st.caption(f"Selected: `{uploaded_file.name}` ({uploaded_file.size:,} bytes)")

            if st.button("Upload & Activate Model", key="upload_model_btn", type="primary"):
                do_upload_model(uploaded_file)
                st.rerun()

        if st.session_state.upload_message:
            st.success(st.session_state.upload_message)
        if st.session_state.upload_error:
            st.error(st.session_state.upload_error)

    # -------------------------------------------------------------------------
    # Active Model Classes Table
    # -------------------------------------------------------------------------
    st.divider()
    st.markdown(h2("list", "Active Model Classes"), unsafe_allow_html=True)
    
    col_classes_1, col_classes_2 = st.columns([3, 1])
    with col_classes_1:
        st.markdown("Class IDs and Names extracted from the currently active YOLO model.")
    with col_classes_2:
        if st.button("Refresh Classes", key="refresh_classes_btn"):
            fetch_model_classes()
            st.rerun()

    if getattr(st.session_state, "model_classes_error", None):
        st.error(f"Failed to load model classes: {st.session_state.model_classes_error}")
    elif not getattr(st.session_state, "model_classes_loaded", False) and not getattr(st.session_state, "model_classes", []):
        st.info("No classes found. Please ensure an active model is loaded.")
    else:
        classes = getattr(st.session_state, "model_classes", [])
        if classes:
            # Format list of dicts into a clean display
            import pandas as pd
            df = pd.DataFrame(classes)
            if 'id' in df.columns and 'name' in df.columns:
                df = df[['id', 'name']]
                df.columns = ["Class ID", "Class Name"]
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("The active model has no classes defined.")
