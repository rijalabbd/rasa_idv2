import streamlit as st
import io
import zipfile
from utils.api import api_request
from utils.icons import h1, h2, icon_md

# =============================================================================
# Functions: Export Logic
# =============================================================================

def get_export_summary():
    """Fetch export tracking summary for badges."""
    summary, status, _, _ = api_request("GET", "/admin/export/summary")
    if status == 200:
        return summary
    return {}


def do_undo_export(source_type: str):
    """Call undo endpoint for a source type."""
    res, status, _, _ = api_request("POST", f"/admin/export/undo/{source_type}")
    if status == 200:
        st.toast(f"Rollback successful: Restored {res.get('reverted', 0)} records.")
        return True
    else:
        st.error(f"Rollback failed: {res}")
        return False


def do_generate_export(export_type: str, only_new: bool):
    """Generate export ZIP and store in session_state."""
    st.session_state.export_zip_bytes = None
    st.session_state.export_filename = None
    st.session_state.export_message = None
    st.session_state.export_error = None
    st.session_state.export_file_list = []

    mode = "new" if only_new else "all"
    endpoint = f"/admin/export-zip?mode={mode}"
    filename = "rasa_id_export.zip"

    with st.spinner("Generating export package..."):
        content, status, headers, _ = api_request("GET", endpoint, timeout=60)

    if status == 200 and content:
        st.session_state.export_zip_bytes = content
        st.session_state.export_filename = filename

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                namelist = z.namelist()
                st.session_state.export_file_list = namelist
                st.session_state.export_message = f"ZIP successfully generated ({len(content):,} bytes)"
        except Exception as e:
            st.session_state.export_message = f"ZIP generated but invalid? {e}"

    else:
        st.session_state.export_error = f"Export failed with status code {status}"


def do_yolo_export(kind: str, only_new: bool = True):
    """Generate YOLO dataset ZIP for feedback or class-requests."""
    key = f"yolo_{kind}"
    st.session_state[f"{key}_zip"] = None
    st.session_state[f"{key}_msg"] = None
    st.session_state[f"{key}_err"] = None
    st.session_state[f"{key}_files"] = []

    mode = "new" if only_new else "all"
    endpoint = f"/admin/export/yolo/{kind}?mode={mode}"

    with st.spinner(f"Generating YOLO {kind} dataset..."):
        content, status, headers, _ = api_request("GET", endpoint, timeout=120)

    # Capture Request ID from session state
    req_id = st.session_state.get("last_request_id", "")
    ref = f" (Ref: {req_id})" if req_id else ""

    if status == 200:
        # Check export count from headers
        exported = "0"
        if headers:
            exported = headers.get("x-export-count") or headers.get("X-Export-Count") or "0"
            
        if exported == "0" or not content:
            st.session_state[f"{key}_msg"] = "No data available for export."
            return

        st.session_state[f"{key}_zip"] = content

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                namelist = z.namelist()
                st.session_state[f"{key}_files"] = namelist
                skipped = "0"
                if headers:
                    skipped = headers.get("x-skip-count") or headers.get("X-Skip-Count") or "0"
                st.session_state[f"{key}_msg"] = (
                    f"ZIP successfully generated ({len(content):,} bytes) — "
                    f"{exported} items exported, {skipped} skipped"
                )
        except Exception as e:
            st.session_state[f"{key}_msg"] = f"ZIP generated but invalid: {e}{ref}"
    else:
        err_detail = ""
        if isinstance(content, dict):
            err_detail = f" — {content.get('code', '')}: {content.get('detail', '')}"
        st.session_state[f"{key}_err"] = f"Export failed with status code {status}{err_detail}{ref}"


def _render_zip_contents(files: list[str], key_prefix: str):
    """Render ZIP file list with file-type icons."""
    with st.expander(f"ZIP Content Preview ({len(files)} files)", expanded=False):
        for f in files:
            if "/images/" in f:
                icon = icon_md("image", f"`{f}`", size=14)
            elif "/labels/" in f:
                icon = icon_md("tag", f"`{f}`", size=14)
            else:
                icon = icon_md("file-text", f"`{f}`", size=14)
            st.markdown(f"- {icon}", unsafe_allow_html=True)


def render_export():
    """Render the Export Dataset view."""

    st.markdown(h1("package", "Export Dataset & Activity Logs"), unsafe_allow_html=True)
    st.divider()

    summary = get_export_summary()

    # ── Section 1: Combined JSONL export ─────────────────────────────────
    st.markdown(h2("file-text", "Combined Activity Log Export (JSONL)"), unsafe_allow_html=True)
    st.caption("Exports log files feedback.jsonl and class_requests.jsonl inside a single ZIP package (excluding image files).")

    c1, c2 = st.columns([1.2, 1])
    with c1:
        only_new_combined = st.toggle("Export only new data (unexported)", value=True, key="only_new_combined")
    with c2:
        if st.button("Reset Last Combined Export Status", key="undo_combined"):
            # Combined affects both feedback and class_request, we use 'combined' type
            if do_undo_export("feedback"): # Combined currently marks logs as individual types
                get_export_summary() # Refresh
                st.rerun()

    btn_col, result_col = st.columns([1.2, 2])

    with btn_col:
        if st.button("Process & Generate Combined ZIP", key="generate_zip_btn", type="secondary", use_container_width=True):
            do_generate_export("Combined", only_new_combined)
            st.rerun()

    with result_col:
        if st.session_state.export_message:
            st.success(st.session_state.export_message)
        if st.session_state.export_error:
            st.error(st.session_state.export_error)

    if st.session_state.export_zip_bytes and st.session_state.export_filename:
        st.download_button(
            label=f"Download {st.session_state.export_filename}",
            data=st.session_state.export_zip_bytes,
            file_name=st.session_state.export_filename,
            mime="application/zip",
            key="download_zip_btn"
        )
        if st.session_state.export_file_list:
            _render_zip_contents(st.session_state.export_file_list, "combined")

    st.divider()

    # ── Section 2: YOLO Feedback Dataset ─────────────────────────────────
    fb_sum = summary.get("feedback", {})
    st.markdown(h2("tag", "YOLO Feedback Dataset (Food Correction)"), unsafe_allow_html=True)
    fb_m1, fb_m2, fb_m3 = st.columns(3)
    fb_m1.metric("Total Submissions", fb_sum.get('total', 0))
    fb_m2.metric("Pending Export", fb_sum.get('new', 0), delta=f"{fb_sum.get('new', 0)} new" if fb_sum.get('new', 0) > 0 else None)
    fb_m3.metric("Last Export", fb_sum.get('last_exported_at', 'Never')[:10] if fb_sum.get('last_exported_at') else 'Never')

    fb_t1, fb_t2 = st.columns([1.2, 1])
    with fb_t1:
        only_new_fb = st.toggle("Export only new feedback data", value=True, key="only_new_fb")
    with fb_t2:
        if st.button("Reset Last Feedback Export Status", key="undo_fb"):
            if do_undo_export("feedback"):
                st.rerun()

    fb_col1, fb_col2 = st.columns([1.2, 2])
    with fb_col1:
        if st.button("Process Feedback Dataset", key="yolo_fb_btn", type="primary", use_container_width=True):
            do_yolo_export("feedback", only_new_fb)
            st.rerun()

    with fb_col2:
        if st.session_state.get("yolo_feedback_msg"):
            st.success(st.session_state.yolo_feedback_msg)
        if st.session_state.get("yolo_feedback_err"):
            st.error(st.session_state.yolo_feedback_err)

    if st.session_state.get("yolo_feedback_zip"):
        st.download_button(
            label="Download feedback_dataset.zip",
            data=st.session_state.yolo_feedback_zip,
            file_name="feedback_dataset.zip",
            mime="application/zip",
            key="dl_yolo_fb"
        )
        files = st.session_state.get("yolo_feedback_files", [])
        if files:
            _render_zip_contents(files, "feedback")

    st.divider()

    # ── Section 3: YOLO Class Request Dataset ────────────────────────────
    cr_sum = summary.get("class_request", {})
    st.markdown(h2("tag", "YOLO Class Request Dataset"), unsafe_allow_html=True)
    cr_m1, cr_m2, cr_m3 = st.columns(3)
    cr_m1.metric("Total Requests", cr_sum.get('total', 0))
    cr_m2.metric("Pending Export", cr_sum.get('new', 0), delta=f"{cr_sum.get('new', 0)} new" if cr_sum.get('new', 0) > 0 else None)
    cr_m3.metric("Last Export", cr_sum.get('last_exported_at', 'Never')[:10] if cr_sum.get('last_exported_at') else 'Never')

    cr_t1, cr_t2 = st.columns([1.2, 1])
    with cr_t1:
        only_new_cr = st.toggle("Export only new request data", value=True, key="only_new_cr")
    with cr_t2:
        if st.button("Reset Last Class Request Export Status", key="undo_cr"):
            if do_undo_export("class_request"):
                st.rerun()

    cr_col1, cr_col2 = st.columns([1.2, 2])
    with cr_col1:
        if st.button("Process Class Request Dataset", key="yolo_cr_btn", type="primary", use_container_width=True):
            do_yolo_export("class-requests", only_new_cr)
            st.rerun()

    with cr_col2:
        if st.session_state.get("yolo_class-requests_msg"):
            st.success(st.session_state['yolo_class-requests_msg'])
        if st.session_state.get("yolo_class-requests_err"):
            st.error(st.session_state['yolo_class-requests_err'])

    if st.session_state.get("yolo_class-requests_zip"):
        st.download_button(
            label="Download class_requests_dataset.zip",
            data=st.session_state["yolo_class-requests_zip"],
            file_name="class_requests_dataset.zip",
            mime="application/zip",
            key="dl_yolo_cr"
        )
        files = st.session_state.get("yolo_class-requests_files", [])
        if files:
            _render_zip_contents(files, "class-requests")

    st.divider()

    # ── Section 4: YOLO Missed Detections Dataset ────────────────────────
    md_sum = summary.get("missed_detection", {})
    st.markdown(h2("eye", "YOLO Missed Detection Dataset"), unsafe_allow_html=True)
    md_m1, md_m2, md_m3 = st.columns(3)
    md_m1.metric("Total Missed", md_sum.get('total', 0))
    md_m2.metric("Pending Export", md_sum.get('new', 0), delta=f"{md_sum.get('new', 0)} new" if md_sum.get('new', 0) > 0 else None)
    md_m3.metric("Last Export", md_sum.get('last_exported_at', 'Never')[:10] if md_sum.get('last_exported_at') else 'Never')

    md_t1, md_t2 = st.columns([1.2, 1])
    with md_t1:
        only_new_md = st.toggle("Export only new missed detections", value=True, key="only_new_md")
    with md_t2:
        if st.button("Reset Last Missed Export Status", key="undo_md"):
            if do_undo_export("missed_detection"):
                st.rerun()

    md_col1, md_col2 = st.columns([1.2, 2])
    with md_col1:
        if st.button("Process Missed Detection Dataset", key="yolo_md_btn", type="primary", use_container_width=True):
            do_yolo_export("missed", only_new_md)
            st.rerun()

    with md_col2:
        if st.session_state.get("yolo_missed_msg"):
            st.success(st.session_state.get('yolo_missed_msg'))
        if st.session_state.get("yolo_missed_err"):
            st.error(st.session_state.get('yolo_missed_err'))

    if st.session_state.get("yolo_missed_zip"):
        st.download_button(
            label="Download missed_detections_dataset.zip",
            data=st.session_state.get("yolo_missed_zip"),
            file_name="missed_detections_dataset.zip",
            mime="application/zip",
            key="dl_yolo_md"
        )
        files = st.session_state.get("yolo_missed_files", [])
        if files:
            _render_zip_contents(files, "missed")
