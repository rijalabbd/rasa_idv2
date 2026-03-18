import streamlit as st
import io
import zipfile
from utils.api import api_request

# =============================================================================
# Functions: Export Logic
# =============================================================================

def do_generate_export(export_type: str, only_pending: bool):
    """Generate export ZIP and store in session_state."""
    # Clear previous state
    st.session_state.export_zip_bytes = None
    st.session_state.export_filename = None
    st.session_state.export_message = None
    st.session_state.export_error = None
    st.session_state.export_file_list = []
    
    endpoint = "/admin/export-zip"
    filename = "rasa_id_export.zip"
    
    with st.spinner("Generating export package..."):
        content, status, _, _ = api_request("GET", endpoint, timeout=60)
    
    if status == 200 and content:
        st.session_state.export_zip_bytes = content
        st.session_state.export_filename = filename
        
        # Analyze ZIP content
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                namelist = z.namelist()
                st.session_state.export_file_list = namelist
                st.session_state.export_message = f"ZIP generated ({len(content):,} bytes)"
        except Exception as e:
            st.session_state.export_message = f"ZIP generated but invalid? {e}"
            
    else:
        st.session_state.export_error = f"Export failed with status {status}"


def do_yolo_export(kind: str):
    """Generate YOLO dataset ZIP for feedback or class-requests."""
    key = f"yolo_{kind}"
    st.session_state[f"{key}_zip"] = None
    st.session_state[f"{key}_msg"] = None
    st.session_state[f"{key}_err"] = None
    st.session_state[f"{key}_files"] = []

    endpoint = f"/admin/export/yolo/{kind}"
    
    with st.spinner(f"Generating YOLO {kind} dataset..."):
        content, status, headers, ref_id = api_request("GET", endpoint, timeout=120)
    
    if status == 200 and content:
        exported = headers.get("x-export-count", "?") if headers else "?"
        skipped = headers.get("x-skip-count", "?") if headers else "?"

        st.session_state[f"{key}_zip"] = content
        
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                namelist = z.namelist()
                st.session_state[f"{key}_files"] = namelist
                st.session_state[f"{key}_msg"] = (
                    f"ZIP generated ({len(content):,} bytes) — "
                    f"{exported} exported, {skipped} skipped"
                )
        except Exception as e:
            st.session_state[f"{key}_msg"] = f"ZIP generated but invalid: {e}"
    else:
        err_detail = ""
        if isinstance(content, dict):
            err_detail = f" — {content.get('code', '')}: {content.get('detail', '')}"
        ref = f" (Ref: {ref_id})" if ref_id else ""
        st.session_state[f"{key}_err"] = f"Export failed with status {status}{err_detail}{ref}"


def render_export():
    """Render the Export Dataset view."""
    
    st.title("📦 Export Dataset")
    st.divider()

    # ── Section 1: Combined JSONL export (existing) ──────────────────────
    st.subheader("📄 Combined JSONL Export")
    st.caption("Exports `feedback.jsonl` + `class_requests.jsonl` (no images)")

    btn_col, result_col = st.columns([1, 2])
    
    with btn_col:
        if st.button("🔄 Generate Combined ZIP", key="generate_zip_btn", type="secondary"):
            do_generate_export("Combined", True)
            st.rerun()
    
    with result_col:
        if st.session_state.export_message:
            st.success(f"✅ {st.session_state.export_message}")
        if st.session_state.export_error:
            st.error(f"❌ {st.session_state.export_error}")
    
    if st.session_state.export_zip_bytes and st.session_state.export_filename:
        st.download_button(
            label=f"⬇️ Download {st.session_state.export_filename}",
            data=st.session_state.export_zip_bytes,
            file_name=st.session_state.export_filename,
            mime="application/zip",
            key="download_zip_btn"
        )
        
        if st.session_state.export_file_list:
            with st.expander("📂 View ZIP Contents", expanded=False):
                for fname in st.session_state.export_file_list:
                    if fname in ["feedback.jsonl", "class_requests.jsonl"]:
                         st.markdown(f"- ✅ `{fname}`")
                    else:
                         st.markdown(f"- 📄 `{fname}`")

    st.divider()

    # ── Section 2: YOLO Feedback Dataset ─────────────────────────────────
    st.subheader("🏷️ YOLO Feedback Dataset")
    st.caption("Images + YOLO labels from user feedback corrections (ready for Roboflow/training)")

    fb_col1, fb_col2 = st.columns([1, 2])
    with fb_col1:
        if st.button("📦 Export YOLO Feedback", key="yolo_fb_btn", type="primary"):
            do_yolo_export("feedback")
            st.rerun()

    with fb_col2:
        if st.session_state.get("yolo_feedback_msg"):
            st.success(f"✅ {st.session_state.yolo_feedback_msg}")
        if st.session_state.get("yolo_feedback_err"):
            st.error(f"❌ {st.session_state.yolo_feedback_err}")

    if st.session_state.get("yolo_feedback_zip"):
        st.download_button(
            label="⬇️ Download feedback_dataset.zip",
            data=st.session_state.yolo_feedback_zip,
            file_name="feedback_dataset.zip",
            mime="application/zip",
            key="dl_yolo_fb"
        )
        files = st.session_state.get("yolo_feedback_files", [])
        if files:
            with st.expander(f"📂 ZIP Contents ({len(files)} files)", expanded=False):
                for f in files:
                    icon = "🖼️" if "/images/" in f else "📝" if "/labels/" in f else "📄"
                    st.markdown(f"- {icon} `{f}`")

    st.divider()

    # ── Section 3: YOLO Class Request Dataset ────────────────────────────
    st.subheader("🆕 YOLO Class Request Dataset")
    st.caption("Images + YOLO labels from new class requests (ready for Roboflow/training)")

    cr_col1, cr_col2 = st.columns([1, 2])
    with cr_col1:
        if st.button("📦 Export YOLO Class Requests", key="yolo_cr_btn", type="primary"):
            do_yolo_export("class-requests")
            st.rerun()

    with cr_col2:
        if st.session_state.get("yolo_class-requests_msg"):
            st.success(f"✅ {st.session_state['yolo_class-requests_msg']}")
        if st.session_state.get("yolo_class-requests_err"):
            st.error(f"❌ {st.session_state['yolo_class-requests_err']}")

    if st.session_state.get("yolo_class-requests_zip"):
        st.download_button(
            label="⬇️ Download class_requests_dataset.zip",
            data=st.session_state["yolo_class-requests_zip"],
            file_name="class_requests_dataset.zip",
            mime="application/zip",
            key="dl_yolo_cr"
        )
        files = st.session_state.get("yolo_class-requests_files", [])
        if files:
            with st.expander(f"📂 ZIP Contents ({len(files)} files)", expanded=False):
                for f in files:
                    icon = "🖼️" if "/images/" in f else "📝" if "/labels/" in f else "📄"
                    st.markdown(f"- {icon} `{f}`")

    st.divider()

    # ── Section 4: YOLO Missed Detections Dataset ────────────────────────
    st.subheader("🕵️ YOLO Missed Detections Dataset")
    st.caption("Images + YOLO labels from missed detections (user manually added item model failed to see)")

    md_col1, md_col2 = st.columns([1, 2])
    with md_col1:
        if st.button("📦 Export YOLO Missed Detections", key="yolo_md_btn", type="primary"):
            do_yolo_export("missed")
            st.rerun()

    with md_col2:
        if st.session_state.get("yolo_missed_msg"):
            st.success(f"✅ {st.session_state.get('yolo_missed_msg')}")
        if st.session_state.get("yolo_missed_err"):
            st.error(f"❌ {st.session_state.get('yolo_missed_err')}")

    if st.session_state.get("yolo_missed_zip"):
        st.download_button(
            label="⬇️ Download missed_detections_dataset.zip",
            data=st.session_state.get("yolo_missed_zip"),
            file_name="missed_detections_dataset.zip",
            mime="application/zip",
            key="dl_yolo_md"
        )
        files = st.session_state.get("yolo_missed_files", [])
        if files:
            with st.expander(f"📂 ZIP Contents ({len(files)} files)", expanded=False):
                for f in files:
                    icon = "🖼️" if "/images/" in f else "📝" if "/labels/" in f else "📄"
                    st.markdown(f"- {icon} `{f}`")
