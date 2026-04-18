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
        st.toast(f"Pembatalan berhasil: Mengembalikan {res.get('reverted', 0)} data.")
        return True
    else:
        st.error(f"Pembatalan gagal: {res}")
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

    with st.spinner("Sedang membuat paket ekspor..."):
        content, status, headers, _ = api_request("GET", endpoint, timeout=60)

    if status == 200 and content:
        st.session_state.export_zip_bytes = content
        st.session_state.export_filename = filename

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                namelist = z.namelist()
                st.session_state.export_file_list = namelist
                st.session_state.export_message = f"ZIP berhasil dibuat ({len(content):,} byte)"
        except Exception as e:
            st.session_state.export_message = f"ZIP dibuat tetapi tidak valid? {e}"

    else:
        st.session_state.export_error = f"Ekspor gagal dengan kode status {status}"


def do_yolo_export(kind: str, only_new: bool = True):
    """Generate YOLO dataset ZIP for feedback or class-requests."""
    key = f"yolo_{kind}"
    st.session_state[f"{key}_zip"] = None
    st.session_state[f"{key}_msg"] = None
    st.session_state[f"{key}_err"] = None
    st.session_state[f"{key}_files"] = []

    mode = "new" if only_new else "all"
    endpoint = f"/admin/export/yolo/{kind}?mode={mode}"

    with st.spinner(f"Sedang membuat dataset YOLO {kind}..."):
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
                    f"ZIP berhasil dibuat ({len(content):,} byte) — "
                    f"{exported} data diekspor, {skipped} dilewati"
                )
        except Exception as e:
            st.session_state[f"{key}_msg"] = f"ZIP dibuat tetapi tidak valid: {e}"
    else:
        err_detail = ""
        if isinstance(content, dict):
            err_detail = f" — {content.get('code', '')}: {content.get('detail', '')}"
        ref = f" (Ref: {ref_id})" if ref_id else ""
        st.session_state[f"{key}_err"] = f"Ekspor gagal dengan kode status {status}{err_detail}{ref}"


def _render_zip_contents(files: list[str], key_prefix: str):
    """Render ZIP file list with file-type icons."""
    with st.expander(f"Isi ZIP ({len(files)} file)", expanded=False):
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

    st.markdown(h1("package", "Ekspor Dataset"), unsafe_allow_html=True)
    st.divider()

    summary = get_export_summary()

    # ── Section 1: Combined JSONL export ─────────────────────────────────
    st.markdown(h2("file-text", "Ekspor Gabungan JSONL"), unsafe_allow_html=True)
    st.caption("Ekspor `feedback.jsonl` + `class_requests.jsonl` (tanpa gambar)")

    c1, c2 = st.columns([1, 1])
    with c1:
        only_new_combined = st.toggle("Hanya data yang belum diekspor", value=True, key="only_new_combined")
    with c2:
        if st.button("Batalkan Ekspor Gabungan Terakhir", key="undo_combined"):
            # Combined affects both feedback and class_request, we use 'combined' type
            if do_undo_export("feedback"): # Combined currently marks logs as individual types
                get_export_summary() # Refresh
                st.rerun()

    btn_col, result_col = st.columns([1, 2])

    with btn_col:
        if st.button("Buat ZIP Gabungan", key="generate_zip_btn", type="secondary"):
            do_generate_export("Combined", only_new_combined)
            st.rerun()

    with result_col:
        if st.session_state.export_message:
            st.success(st.session_state.export_message)
        if st.session_state.export_error:
            st.error(st.session_state.export_error)

    if st.session_state.export_zip_bytes and st.session_state.export_filename:
        st.download_button(
            label=f"Unduh {st.session_state.export_filename}",
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
    fb_label = f"Feedback Baru: {fb_sum.get('new', 0)} / Total: {fb_sum.get('total', 0)}"
    st.markdown(h2("tag", f"Dataset Feedback YOLO"), unsafe_allow_html=True)
    st.info(fb_label)
    if fb_sum.get("last_exported_at"):
        st.caption(f"Export Terakhir: {fb_sum.get('last_exported_at')}")

    fb_t1, fb_t2 = st.columns([1, 1])
    with fb_t1:
        only_new_fb = st.toggle("Hanya data Feedback yang belum diekspor", value=True, key="only_new_fb")
    with fb_t2:
        if st.button("Batalkan Ekspor Feedback Terakhir", key="undo_fb"):
            if do_undo_export("feedback"):
                st.rerun()

    fb_col1, fb_col2 = st.columns([1, 2])
    with fb_col1:
        if st.button("Ekspor Feedback YOLO", key="yolo_fb_btn", type="primary"):
            do_yolo_export("feedback", only_new_fb)
            st.rerun()

    with fb_col2:
        if st.session_state.get("yolo_feedback_msg"):
            st.success(st.session_state.yolo_feedback_msg)
        if st.session_state.get("yolo_feedback_err"):
            st.error(st.session_state.yolo_feedback_err)

    if st.session_state.get("yolo_feedback_zip"):
        st.download_button(
            label="Unduh feedback_dataset.zip",
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
    cr_label = f"Class Request Baru: {cr_sum.get('new', 0)} / Total: {cr_sum.get('total', 0)}"
    st.markdown(h2("tag", "Dataset Class Request YOLO"), unsafe_allow_html=True)
    st.info(cr_label)
    if cr_sum.get("last_exported_at"):
        st.caption(f"Export Terakhir: {cr_sum.get('last_exported_at')}")

    cr_t1, cr_t2 = st.columns([1, 1])
    with cr_t1:
        only_new_cr = st.toggle("Hanya data Class Request yang belum diekspor", value=True, key="only_new_cr")
    with cr_t2:
        if st.button("Batalkan Ekspor Class Request Terakhir", key="undo_cr"):
            if do_undo_export("class_request"):
                st.rerun()

    cr_col1, cr_col2 = st.columns([1, 2])
    with cr_col1:
        if st.button("Ekspor Class Request YOLO", key="yolo_cr_btn", type="primary"):
            do_yolo_export("class-requests", only_new_cr)
            st.rerun()

    with cr_col2:
        if st.session_state.get("yolo_class-requests_msg"):
            st.success(st.session_state['yolo_class-requests_msg'])
        if st.session_state.get("yolo_class-requests_err"):
            st.error(st.session_state['yolo_class-requests_err'])

    if st.session_state.get("yolo_class-requests_zip"):
        st.download_button(
            label="Unduh class_requests_dataset.zip",
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
    md_label = f"Missed Detection Baru: {md_sum.get('new', 0)} / Total: {md_sum.get('total', 0)}"
    st.markdown(h2("eye", "Dataset Missed Detection YOLO"), unsafe_allow_html=True)
    st.info(md_label)
    if md_sum.get("last_exported_at"):
        st.caption(f"Export Terakhir: {md_sum.get('last_exported_at')}")

    md_t1, md_t2 = st.columns([1, 1])
    with md_t1:
        only_new_md = st.toggle("Hanya data Missed Detection yang belum diekspor", value=True, key="only_new_md")
    with md_t2:
        if st.button("Batalkan Ekspor Missed Detection Terakhir", key="undo_md"):
            if do_undo_export("missed_detection"):
                st.rerun()

    md_col1, md_col2 = st.columns([1, 2])
    with md_col1:
        if st.button("Ekspor Missed Detection YOLO", key="yolo_md_btn", type="primary"):
            do_yolo_export("missed", only_new_md)
            st.rerun()

    with md_col2:
        if st.session_state.get("yolo_missed_msg"):
            st.success(st.session_state.get('yolo_missed_msg'))
        if st.session_state.get("yolo_missed_err"):
            st.error(st.session_state.get('yolo_missed_err'))

    if st.session_state.get("yolo_missed_zip"):
        st.download_button(
            label="Unduh missed_detections_dataset.zip",
            data=st.session_state.get("yolo_missed_zip"),
            file_name="missed_detections_dataset.zip",
            mime="application/zip",
            key="dl_yolo_md"
        )
        files = st.session_state.get("yolo_missed_files", [])
        if files:
            _render_zip_contents(files, "missed")
