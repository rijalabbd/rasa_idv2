"""TKPI CSV Import view — upload, dry-run, commit.

Safety features:
  - SHA256 file-change detection (prevents committing different file than validated)
  - Confirmation checkbox gate before commit
  - Enhanced error banners with HTTP status + body + Ref ID
"""

import io
import csv
import hashlib
import streamlit as st
from utils.api import api_request
from utils.icons import h1, h2, icon_md


def _file_sha256(file_bytes: bytes) -> str:
    """Compute SHA256 hex digest of file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def _call_import(uploaded_file, dry_run: bool) -> tuple[dict | None, int, str | None]:
    """Call the TKPI import endpoint. Returns (data, http_status, ref_id)."""
    uploaded_file.seek(0)
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
    params = {"dry_run": str(dry_run).lower()}

    data, status, headers, _ = api_request(
        "POST", "/admin/tkpi/import-csv", files=files, params=params, timeout=120
    )

    ref_id = None
    if headers:
        ref_id = headers.get("x-request-id") or st.session_state.get("last_request_id")

    return data, status, ref_id


def _show_error_banner(data, status: int, ref_id: str | None, action: str):
    """Show detailed error banner for failed API calls."""
    ref_part = f" (Ref: `{ref_id}`)" if ref_id else ""

    if isinstance(data, dict):
        detail = data.get("detail", "Unknown error")
        code = data.get("code", "ERROR")
        st.error(f"{action} failed — HTTP {status} · {code}: {detail}{ref_part}")
    elif isinstance(data, (str, bytes)):
        body = data[:200] if isinstance(data, str) else data.decode("utf-8", errors="replace")[:200]
        st.error(f"{action} failed — HTTP {status}: {body}{ref_part}")
    else:
        st.error(f"{action} failed — HTTP {status}{ref_part}")


def _show_summary(result: dict, ref_id: str | None):
    """Display import summary metrics."""
    dry_run = result.get("dry_run", True)
    mode_label = "Hasil Uji Coba" if dry_run else "Hasil Penerapan"

    st.markdown(h2("search" if dry_run else "check-circle", mode_label), unsafe_allow_html=True)

    if ref_id:
        st.caption(f"Ref: `{ref_id}`")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Baris", result.get("rows_total", 0))
    c2.metric("Diproses", result.get("processed_count", 0))
    c3.metric("Dilewati", result.get("skipped_count", 0))
    c4.metric("Error", result.get("errors_count", 0))

    c5, c6, c7, c8 = st.columns(4)
    if dry_run:
        c5.metric("Baru (akan ditambahkan)", result.get("new_count", 0))
        c6.metric("Sudah Ada (akan diperbarui)", result.get("existing_count", 0))
    else:
        c5.metric("Ditambahkan", result.get("inserted_count", 0))
        c6.metric("Diperbarui", result.get("updated_count", 0))
    c7.metric("Peringatan", result.get("warnings_count", 0))
    if dry_run:
        c8.metric("Sudah Ada di DB", result.get("existing_count", 0))
    else:
        c8.metric("Baru (ditambahkan)", result.get("new_count", 0))


def _show_issues(result: dict, kind: str):
    """Show errors or warnings table + optional CSV download."""
    items = result.get(kind, [])
    count = result.get(f"{kind}_count", 0)
    truncated = result.get(f"{kind}_truncated", False)

    if count == 0:
        return

    label = "Errors" if kind == "errors" else "Warnings"
    expander_icon = "x-circle" if kind == "errors" else "alert-triangle"

    with st.expander(
        f"{label} ({count})",
        expanded=(kind == "errors")
    ):
        st.markdown(
            icon_md(expander_icon, f"{count} {label}", size=14),
            unsafe_allow_html=True
        )
        if truncated:
            st.info(f"Showing first {len(items)} of {count} {kind}.")

        display = items[:20]
        table_data = [
            {
                "Row": item.get("row_number", ""),
                "TKPI Code": item.get("tkpi_code") or "—",
                "Message": item.get("message", ""),
            }
            for item in display
        ]

        if table_data:
            st.dataframe(table_data, use_container_width=True, hide_index=True)

        if len(items) > 20:
            st.caption(f"... and {len(items) - 20} more (download CSV for full list)")

        if items:
            csv_buf = io.StringIO()
            writer = csv.DictWriter(csv_buf, fieldnames=["row_number", "tkpi_code", "message"])
            writer.writeheader()
            for item in items:
                writer.writerow({
                    "row_number": item.get("row_number", ""),
                    "tkpi_code": item.get("tkpi_code", ""),
                    "message": item.get("message", ""),
                })
            st.download_button(
                f"Download {label} CSV",
                csv_buf.getvalue(),
                file_name=f"tkpi_import_{kind}.csv",
                mime="text/csv",
                key=f"dl_{kind}",
            )


def render_tkpi_import():
    """Render the TKPI CSV Import view."""
    st.markdown(h1("database", "Import CSV TKPI"), unsafe_allow_html=True)
    st.caption("Unggah CSV → Validasi (Uji Coba) → Tinjau → Terapkan")
    st.divider()

    # ── File uploader ────────────────────────────────────────────────
    uploaded_file = st.file_uploader(
        "Unggah file CSV TKPI",
        type=["csv"],
        help="UTF-8, pemisah koma atau titik koma. Kolom wajib: tkpi_code, name",
        key="tkpi_csv_file",
    )

    current_hash = None
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        size_kb = len(file_bytes) / 1024
        current_hash = _file_sha256(file_bytes)
        st.markdown(
            icon_md("file-text", f"**{uploaded_file.name}** — {size_kb:.1f} KB", size=16),
            unsafe_allow_html=True
        )
    else:
        st.session_state.tkpi_import_result = None
        st.session_state.tkpi_import_ref = None
        st.session_state.tkpi_commit_result = None
        st.session_state.tkpi_commit_ref = None
        st.session_state.tkpi_validated_hash = None

    st.divider()

    # ── Dry-run + Commit buttons ─────────────────────────────────────
    col_dry, col_commit = st.columns(2)

    with col_dry:
        dry_disabled = uploaded_file is None
        if st.button(
            "Validasi (Uji Coba)",
            disabled=dry_disabled,
            use_container_width=True,
            type="primary",
        ):
            st.session_state.tkpi_import_result = None
            st.session_state.tkpi_import_ref = None
            st.session_state.tkpi_commit_result = None
            st.session_state.tkpi_commit_ref = None
            st.session_state.tkpi_validated_hash = None

            with st.spinner("Memvalidasi CSV..."):
                data, status, ref = _call_import(uploaded_file, dry_run=True)

            if status == 200 and data:
                st.session_state.tkpi_import_result = data
                st.session_state.tkpi_import_ref = ref
                st.session_state.tkpi_validated_hash = current_hash
            else:
                st.session_state.tkpi_import_result = None
                _show_error_banner(data, status, ref, "Dry-run")

            st.rerun()

    # ── File change detection ────────────────────────────────────────
    dry_result = st.session_state.get("tkpi_import_result")
    validated_hash = st.session_state.get("tkpi_validated_hash")
    file_changed = (
        current_hash is not None
        and validated_hash is not None
        and current_hash != validated_hash
    )

    if file_changed:
        st.warning("File berubah sejak validasi. Jalankan **Validasi (Uji Coba)** ulang.")

    # ── Commit gate ──────────────────────────────────────────────────
    has_dry_run = dry_result is not None
    has_zero_errors = has_dry_run and dry_result.get("errors_count", 1) == 0
    hash_matches = not file_changed and validated_hash is not None
    file_present = uploaded_file is not None

    confirm_checked = False
    if has_dry_run and has_zero_errors and file_present and hash_matches:
        confirm_checked = st.checkbox(
            "Saya paham ini akan menulis ke database",
            key="tkpi_commit_confirm",
        )

    can_commit = (
        file_present
        and has_dry_run
        and has_zero_errors
        and hash_matches
        and confirm_checked
    )

    with col_commit:
        if st.button(
            "Terapkan Import",
            disabled=not can_commit,
            use_container_width=True,
            type="secondary",
        ):
            st.session_state.tkpi_commit_result = None
            st.session_state.tkpi_commit_ref = None

            with st.spinner("Mengimpor ke database..."):
                data, status, ref = _call_import(uploaded_file, dry_run=False)

            if status == 200 and data:
                st.session_state.tkpi_commit_result = data
                st.session_state.tkpi_commit_ref = ref
                st.toast("Import berhasil diterapkan!")
            else:
                _show_error_banner(data, status, ref, "Commit")

            st.rerun()

    if not can_commit and has_dry_run and not has_zero_errors:
        st.warning("Tidak bisa menerapkan: perbaiki error CSV terlebih dahulu, lalu validasi ulang.")

    st.divider()

    # ── Display results ──────────────────────────────────────────────
    commit_result = st.session_state.get("tkpi_commit_result")
    commit_ref = st.session_state.get("tkpi_commit_ref")

    if commit_result:
        _show_summary(commit_result, commit_ref)
        _show_issues(commit_result, "errors")
        _show_issues(commit_result, "warnings")
        st.success(
            f"Import committed: "
            f"{commit_result.get('inserted_count', 0)} inserted, "
            f"{commit_result.get('updated_count', 0)} updated"
        )

    elif dry_result:
        dry_ref = st.session_state.get("tkpi_import_ref")
        _show_summary(dry_result, dry_ref)
        _show_issues(dry_result, "errors")
        _show_issues(dry_result, "warnings")

    # ── Current TKPI Data Preview ────────────────────────────────────
    st.divider()
    st.markdown(h2("list", "Data TKPI Saat Ini"), unsafe_allow_html=True)

    if st.button("Muat Ulang Data", key="tkpi_refresh"):
        st.session_state.tkpi_preview_data = None
        st.rerun()

    if st.session_state.get("tkpi_preview_data") is None:
        data, status, _, _ = api_request("GET", "/admin/tkpi/list", params={"limit": 500})
        if status == 200 and isinstance(data, dict):
            st.session_state.tkpi_preview_data = data
        else:
            st.session_state.tkpi_preview_data = {"total": 0, "items": []}

    preview = st.session_state.get("tkpi_preview_data", {})
    total = preview.get("total", 0)
    items = preview.get("items", [])

    st.caption(f"Total: **{total}** item dalam database")

    if items:
        table = [
            {
                "Kode": item.get("tkpi_code", ""),
                "Nama": item.get("name", ""),
                "Energi (kcal)": item.get("energi_kal") or "—",
                "Protein (g)": item.get("protein_g") or "—",
                "Lemak (g)": item.get("lemak_g") or "—",
                "Karbo (g)": item.get("karbo_g") or "—",
                "Serat (g)": item.get("serat_g") or "—",
            }
            for item in items
        ]
        st.dataframe(table, use_container_width=True, hide_index=True, height=400)
    else:
        st.info("Belum ada data TKPI. Upload CSV untuk memulai.")
