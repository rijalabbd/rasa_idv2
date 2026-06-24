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


def do_yolo_raw_export(
    only_new: bool = True,
    min_confidence: float = 0.50,
    include_background: bool = True,
    start_date = None,
    end_date = None
):
    """Generate YOLO raw detections dataset ZIP with advanced filters."""
    key = "yolo_raw"
    st.session_state[f"{key}_zip"] = None
    st.session_state[f"{key}_msg"] = None
    st.session_state[f"{key}_err"] = None
    st.session_state[f"{key}_files"] = []

    mode = "new" if only_new else "all"
    
    endpoint = f"/admin/export/yolo/raw?mode={mode}&min_confidence={min_confidence}&include_background={str(include_background).lower()}"
    if start_date:
        endpoint += f"&start_date={start_date}"
    if end_date:
        endpoint += f"&end_date={end_date}"

    with st.spinner("Membuat dataset YOLO Raw Detections..."):
        content, status, headers, _ = api_request("GET", endpoint, timeout=180)

    req_id = st.session_state.get("last_request_id", "")
    ref = f" (Ref: {req_id})" if req_id else ""

    if status == 200:
        exported = "0"
        if headers:
            exported = headers.get("x-export-count") or headers.get("X-Export-Count") or "0"
            
        if exported == "0" or not content:
            st.session_state[f"{key}_msg"] = "Tidak ada data untuk diekspor."
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
                    f"ZIP berhasil dibuat ({len(content):,} bytes) — "
                    f"{exported} item diekspor, {skipped} dilewati"
                )
        except Exception as e:
            st.session_state[f"{key}_msg"] = f"ZIP dibuat tetapi tidak valid: {e}{ref}"
    else:
        err_detail = ""
        if isinstance(content, dict):
            err_detail = f" — {content.get('code', '')}: {content.get('detail', '')}"
        st.session_state[f"{key}_err"] = f"Ekspor gagal dengan kode status {status}{err_detail}{ref}"


def _render_zip_contents(files: list[str], key_prefix: str):
    """Render ZIP file list with file-type icons."""
    with st.expander(f"Pratinjau Isi ZIP ({len(files)} file)", expanded=False):
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

    st.markdown(h1("package", "Ekspor Dataset & Log Aktivitas"), unsafe_allow_html=True)
    st.divider()

    summary = get_export_summary()

    # ── Section 1: Combined JSONL export ─────────────────────────────────
    st.markdown(h2("file-text", "Ekspor Gabungan Log Aktivitas (JSONL)"), unsafe_allow_html=True)
    st.caption("Mengekspor file log feedback.jsonl and class_requests.jsonl ke dalam satu paket ZIP (tidak termasuk file gambar).")

    c1, c2 = st.columns([1.2, 1])
    with c1:
        only_new_combined = st.toggle("Ekspor hanya data baru (belum diekspor)", value=True, key="only_new_combined")
    with c2:
        if st.button("Reset Status Ekspor Gabungan Terakhir", key="undo_combined"):
            # Combined affects both feedback and class_request, we use 'combined' type
            if do_undo_export("feedback"): # Combined currently marks logs as individual types
                get_export_summary() # Refresh
                st.rerun()

    btn_col, result_col = st.columns([1.2, 2])

    with btn_col:
        if st.button("Proses & Buat ZIP Gabungan", key="generate_zip_btn", type="secondary", use_container_width=True):
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
    st.markdown(h2("tag", "YOLO Feedback Dataset (Koreksi Makanan)"), unsafe_allow_html=True)
    fb_m1, fb_m2, fb_m3 = st.columns(3)
    fb_m1.metric("Total Feedback", fb_sum.get('total', 0))
    fb_m2.metric("Belum Diekspor", fb_sum.get('new', 0), delta=f"{fb_sum.get('new', 0)} baru" if fb_sum.get('new', 0) > 0 else None)
    fb_m3.metric("Ekspor Terakhir", fb_sum.get('last_exported_at', 'Belum Pernah')[:10] if fb_sum.get('last_exported_at') else 'Belum Pernah')

    fb_t1, fb_t2 = st.columns([1.2, 1])
    with fb_t1:
        only_new_fb = st.toggle("Ekspor hanya data feedback baru", value=True, key="only_new_fb")
    with fb_t2:
        if st.button("Reset Status Ekspor Feedback Terakhir", key="undo_fb"):
            if do_undo_export("feedback"):
                st.rerun()

    fb_col1, fb_col2 = st.columns([1.2, 2])
    with fb_col1:
        if st.button("Proses Dataset Feedback", key="yolo_fb_btn", type="primary", use_container_width=True):
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
    st.markdown(h2("tag", "YOLO Class Request Dataset"), unsafe_allow_html=True)
    cr_m1, cr_m2, cr_m3 = st.columns(3)
    cr_m1.metric("Total Usulan", cr_sum.get('total', 0))
    cr_m2.metric("Belum Diekspor", cr_sum.get('new', 0), delta=f"{cr_sum.get('new', 0)} baru" if cr_sum.get('new', 0) > 0 else None)
    cr_m3.metric("Ekspor Terakhir", cr_sum.get('last_exported_at', 'Belum Pernah')[:10] if cr_sum.get('last_exported_at') else 'Belum Pernah')

    cr_t1, cr_t2 = st.columns([1.2, 1])
    with cr_t1:
        only_new_cr = st.toggle("Ekspor hanya data usulan baru", value=True, key="only_new_cr")
    with cr_t2:
        if st.button("Reset Status Ekspor Class Request Terakhir", key="undo_cr"):
            if do_undo_export("class_request"):
                st.rerun()

    cr_col1, cr_col2 = st.columns([1.2, 2])
    with cr_col1:
        if st.button("Proses Dataset Class Request", key="yolo_cr_btn", type="primary", use_container_width=True):
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
    st.markdown(h2("eye", "YOLO Missed Detection Dataset"), unsafe_allow_html=True)
    md_m1, md_m2, md_m3 = st.columns(3)
    md_m1.metric("Total Terlewat", md_sum.get('total', 0))
    md_m2.metric("Belum Diekspor", md_sum.get('new', 0), delta=f"{md_sum.get('new', 0)} baru" if md_sum.get('new', 0) > 0 else None)
    md_m3.metric("Ekspor Terakhir", md_sum.get('last_exported_at', 'Belum Pernah')[:10] if md_sum.get('last_exported_at') else 'Belum Pernah')

    md_t1, md_t2 = st.columns([1.2, 1])
    with md_t1:
        only_new_md = st.toggle("Ekspor hanya data missed detections baru", value=True, key="only_new_md")
    with md_t2:
        if st.button("Reset Status Ekspor Missed Detection Terakhir", key="undo_md"):
            if do_undo_export("missed_detection"):
                st.rerun()

    md_col1, md_col2 = st.columns([1.2, 2])
    with md_col1:
        if st.button("Proses Dataset Missed Detection", key="yolo_md_btn", type="primary", use_container_width=True):
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

    st.divider()

    # ── Section 5: YOLO Raw Detections Dataset ────────────────────────
    raw_sum = summary.get("raw_detection", {})
    st.markdown(h2("image", "YOLO Raw Detections Dataset (Dataset Deteksi Otomatis)"), unsafe_allow_html=True)
    raw_m1, raw_m2, raw_m3 = st.columns(3)
    raw_m1.metric("Total Deteksi", raw_sum.get('total', 0))
    raw_m2.metric("Belum Diekspor", raw_sum.get('new', 0), delta=f"{raw_sum.get('new', 0)} baru" if raw_sum.get('new', 0) > 0 else None)
    raw_m3.metric("Ekspor Terakhir", raw_sum.get('last_exported_at', 'Belum Pernah')[:10] if raw_sum.get('last_exported_at') else 'Belum Pernah')

    # Advanced options layout
    st.markdown("##### ⚙️ Filter Ekspor Tingkat Lanjut")
    set1, set2 = st.columns(2)
    with set1:
        only_new_raw = st.toggle("Ekspor hanya data deteksi baru", value=True, key="only_new_raw")
        include_bg_raw = st.toggle("Sertakan gambar tanpa deteksi (Background)", value=True, key="include_bg_raw")
    with set2:
        min_conf_raw = st.slider("Batas Minimal Confidence Score", min_value=0.0, max_value=1.0, value=0.50, step=0.05, key="min_conf_raw")
        
        # Date Preset Dropdown
        import datetime as dt_lib
        preset = st.selectbox(
            "Filter Rentang Tanggal",
            options=["All Time (Semua Waktu)", "Last 30 Days (1 Bulan)", "Last 60 Days (2 Bulan)", "Custom (Pilih Manual)"],
            index=0,
            key="raw_date_preset"
        )
        
        start_date_str = None
        end_date_str = None
        
        if preset == "Custom (Pilih Manual)":
            date_range = st.date_input("Pilih Rentang Tanggal Kustom", value=(), key="date_range_raw")
            if len(date_range) == 2:
                start_date_str = date_range[0].strftime("%Y-%m-%d")
                end_date_str = date_range[1].strftime("%Y-%m-%d")
            elif len(date_range) == 1:
                start_date_str = date_range[0].strftime("%Y-%m-%d")
        elif preset == "Last 30 Days (1 Bulan)":
            today = dt_lib.date.today()
            start_date_str = (today - dt_lib.timedelta(days=30)).strftime("%Y-%m-%d")
            end_date_str = today.strftime("%Y-%m-%d")
        elif preset == "Last 60 Days (2 Bulan)":
            today = dt_lib.date.today()
            start_date_str = (today - dt_lib.timedelta(days=60)).strftime("%Y-%m-%d")
            end_date_str = today.strftime("%Y-%m-%d")

    raw_t1, raw_t2 = st.columns([1.2, 1])
    with raw_t1:
        pass # placeholder to keep layout consistent
    with raw_t2:
        if st.button("Reset Status Ekspor Deteksi Otomatis Terakhir", key="undo_raw"):
            if do_undo_export("raw_detection"):
                st.rerun()

    raw_col1, raw_col2 = st.columns([1.2, 2])
    with raw_col1:
        if st.button("Proses Deteksi Otomatis", key="yolo_raw_btn", type="primary", use_container_width=True):
            do_yolo_raw_export(
                only_new=only_new_raw,
                min_confidence=min_conf_raw,
                include_background=include_bg_raw,
                start_date=start_date_str,
                end_date=end_date_str
            )
            st.rerun()

    with raw_col2:
        if st.session_state.get("yolo_raw_msg"):
            st.success(st.session_state.get('yolo_raw_msg'))
        if st.session_state.get("yolo_raw_err"):
            st.error(st.session_state.get('yolo_raw_err'))

    if st.session_state.get("yolo_raw_zip"):
        st.download_button(
            label="Unduh raw_detections_dataset.zip",
            data=st.session_state.get("yolo_raw_zip"),
            file_name="raw_detections_dataset.zip",
            mime="application/zip",
            key="dl_yolo_raw"
        )
        files = st.session_state.get("yolo_raw_files", [])
        if files:
            _render_zip_contents(files, "raw")
