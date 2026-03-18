import streamlit as st
from utils.api import api_request, format_datetime

# =============================================================================
# Functions: Mappings Logic
# =============================================================================

def fetch_mappings(q: str = ""):
    """Fetch mappings from API."""
    params = {"limit": 50}
    if q.strip():
        params["q"] = q.strip()
    
    data, status, _, _ = api_request("GET", "/admin/mappings", params=params)
    if status == 200 and data:
        st.session_state.mapping_list = data
        st.session_state.mapping_list_error = None
    else:
        st.session_state.mapping_list = None
        st.session_state.mapping_list_error = f"HTTP {status}" if status > 0 else "Request failed"


def search_tkpi_api(q: str):
    """Search TKPI foods."""
    if not q.strip():
        return []
        
    data, status, _, _ = api_request("GET", "/tkpi/search", params={"q": q, "limit": 10})
    if status == 200 and isinstance(data, list):
        return data
    return []


def save_mapping(yolo_label: str, tkpi_food_id: int, ui_status: str, ui_note: str):
    """Save/update mapping."""
    st.session_state.mapping_save_message = None
    st.session_state.mapping_save_error = None
    
    payload = {
        "yolo_label": yolo_label.lower().strip(),
        "tkpi_food_id": tkpi_food_id,
        "ui_status": ui_status,
        "ui_note": ui_note if ui_note.strip() else None
    }
    
    with st.spinner("Saving mapping..."):
        data, status, _, _ = api_request("POST", "/admin/mappings", json=payload)
    if status == 200:
        st.session_state.mapping_save_message = f"✅ Berhasil menyimpan mapping: {yolo_label}"
        fetch_mappings()  # Refresh list
    else:
        st.session_state.mapping_save_error = f"HTTP {status}" if status > 0 else "Request failed"


def delete_mapping_api(mapping_id: int, label: str):
    """Delete a mapping."""
    with st.spinner(f"Deleting mapping '{label}'..."):
        _, status, _, _ = api_request("DELETE", f"/admin/mappings/{mapping_id}")
    if status == 200:
        st.session_state.mapping_save_message = f"🗑️ Mapping '{label}' dihapus"
        fetch_mappings()
    else:
        st.session_state.mapping_save_error = f"Gagal hapus: HTTP {status}"


def render_mappings():
    """Render the Mappings Management view."""
    
    st.title("🔗 Pencocokan Data Gizi")
    st.caption("Kelola mapping antara label YOLO dan data TKPI")
    st.divider()

    # Initial Data Load
    if st.session_state.mapping_list is None and st.session_state.mapping_list_error is None:
        fetch_mappings()

    # List Data Mappings (Table)
    st.markdown("### 📋 Daftar Mapping")
    
    if st.session_state.mapping_list and "items" in st.session_state.mapping_list:
        items = st.session_state.mapping_list["items"]
        
        # Prepare data for dataframe
        table_data = []
        for item in items:
            table_data.append({
                "YOLO Label": item["yolo_label"],
                "TKPI Name": item["tkpi_food_name"],
                "Status": item["ui_status"],
                "Note": item["ui_note"] or "-",
                "Last Updated": format_datetime(item.get("updated_at"))
            })
        
        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "YOLO Label": st.column_config.TextColumn("Label YOLO (Model)", help="Label yang dideteksi oleh YOLO"),
                "TKPI Name": st.column_config.TextColumn("Nama Data Gizi (TKPI)", help="Data gizi yang dipetakan"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Note": st.column_config.TextColumn("Catatan", width="medium"),
                "Last Updated": st.column_config.TextColumn("Updated", width="small")
            }
        )
        st.caption(f"Total: {len(items)} mapping")
    
    elif st.session_state.mapping_list_error:
        st.error(st.session_state.mapping_list_error)
    else:
        st.info("Belum ada data mapping.")
    
    st.divider()
    
    # Form for add/edit mapping
    st.markdown("**Tambah / Ubah Mapping**")
    
    # Session state for form values
    if "form_yolo_label" not in st.session_state:
        st.session_state.form_yolo_label = ""
    if "form_status" not in st.session_state:
        st.session_state.form_status = "Cocok"
    if "form_note" not in st.session_state:
        st.session_state.form_note = ""
    if "last_selected_edit_key" not in st.session_state:
        st.session_state.last_selected_edit_key = None
    
    # Edit mode dropdown - select existing mapping to edit
    edit_options = {"➕ Tambah mapping baru": None}
    
    if st.session_state.mapping_list is None:
        st.info("Loading mappings...")
    elif st.session_state.mapping_list_error:
        st.warning(f"Mapping fetch error: {st.session_state.mapping_list_error}")
    else:
        for m in st.session_state.mapping_list.get("items", []):
            edit_options[f"✏️ {m['yolo_label']} → {m['tkpi_food_name']}"] = m
    
    selected_edit_option = st.selectbox(
        "Mode",
        options=list(edit_options.keys()),
        key="edit_mode_select",
        help="Pilih mapping untuk diedit, atau tambah baru"
    )
    selected_mapping = edit_options[selected_edit_option]
    is_edit_mode = selected_mapping is not None
    
    # Auto-fill form when selection changes
    if selected_edit_option != st.session_state.last_selected_edit_key:
        st.session_state.last_selected_edit_key = selected_edit_option
        if is_edit_mode:
            st.session_state.form_yolo_label = selected_mapping["yolo_label"]
            st.session_state.form_status = "Cocok" if selected_mapping.get("ui_status") == "COCOK" else "Mendekati"
            st.session_state.form_note = selected_mapping.get("ui_note") or ""
        else:
            st.session_state.form_yolo_label = ""
            st.session_state.form_status = "Cocok"
            st.session_state.form_note = ""
    
    # Status explanation
    st.markdown("""
    <small style="color: #666;">
    <b>Cocok</b>: Sama persis dengan data TKPI. <br>
    <b>Mendekati</b>: Perkiraan (olahan → bahan dasar). Minyak/bumbu belum dihitung.
    </small>
    """, unsafe_allow_html=True)
    
    form_col1, form_col2 = st.columns(2)
    
    with form_col1:
        # Label YOLO - show value in edit mode (disabled)
        if is_edit_mode:
            st.text_input(
                "Label YOLO",
                value=st.session_state.form_yolo_label,
                disabled=True,
                help="Label tidak bisa diubah saat mode edit"
            )
        else:
            st.session_state.form_yolo_label = st.text_input(
                "Label YOLO",
                value=st.session_state.form_yolo_label,
                placeholder="contoh: unknown_food",
                help="Label dari deteksi YOLO (huruf kecil, underscore)"
            )
        
        # Status radio
        status_idx = 0 if st.session_state.form_status == "Cocok" else 1
        new_ui_status = st.radio(
            "Status Pencocokan",
            options=["Cocok", "Mendekati"],
            index=status_idx,
            horizontal=True
        )
        st.session_state.form_status = new_ui_status
        
        # Note input - auto-fill default for Mendekati
        default_note = st.session_state.form_note
        if new_ui_status == "Mendekati" and not default_note:
            default_note = "Angka gizi belum termasuk minyak/bumbu."
        
        new_ui_note = st.text_input(
            "Catatan (opsional)",
            value=default_note,
            help="Tampil di UI untuk status Mendekati"
        )
        st.session_state.form_note = new_ui_note
        
        # Show current TKPI when editing
        if is_edit_mode:
            st.info(f"📌 TKPI saat ini: **{selected_mapping['tkpi_food_name']}** (ID: {selected_mapping['tkpi_food_id']})")
    
    with form_col2:
        # TKPI search
        tkpi_search_q = st.text_input(
            "Cari TKPI" + (" (untuk ganti)" if is_edit_mode else ""),
            placeholder="Ketik nama makanan...",
            key="tkpi_search_q_input"
        )
        
        if tkpi_search_q and len(tkpi_search_q) >= 2:
            st.session_state.tkpi_search_results = search_tkpi_api(tkpi_search_q)
        
        # TKPI selection
        selected_tkpi_id = selected_mapping["tkpi_food_id"] if is_edit_mode else None
        selected_tkpi_name = selected_mapping["tkpi_food_name"] if is_edit_mode else None
        
        if st.session_state.tkpi_search_results:
            tkpi_options = {f"{t['name']} (ID: {t['id']})": t['id'] for t in st.session_state.tkpi_search_results}
            selected_option = st.selectbox(
                "Pilih TKPI",
                options=list(tkpi_options.keys()),
                key="tkpi_select_dropdown"
            )
            if selected_option:
                selected_tkpi_id = tkpi_options[selected_option]
                selected_tkpi_name = selected_option.split(" (ID:")[0]
        elif not is_edit_mode:
            st.info("Ketik minimal 2 karakter untuk mencari TKPI")
    
    # Action buttons
    save_col, delete_col = st.columns([1, 1])
    
    with save_col:
        save_label = "💾 Perbarui Mapping" if is_edit_mode else "💾 Simpan Pencocokan"
        if st.button(save_label, type="primary"):
            label_to_save = st.session_state.form_yolo_label
            if not label_to_save.strip():
                st.error("Label YOLO wajib diisi")
            elif not selected_tkpi_id:
                st.error("Pilih TKPI terlebih dahulu")
            else:
                ui_status_val = "COCOK" if st.session_state.form_status == "Cocok" else "MENDEKATI"
                save_mapping(label_to_save, selected_tkpi_id, ui_status_val, st.session_state.form_note)
                # Reset form after save
                st.session_state.form_yolo_label = ""
                st.session_state.form_status = "Cocok"
                st.session_state.form_note = ""
                st.session_state.last_selected_edit_key = None
                st.rerun()
    
    with delete_col:
        if is_edit_mode:
            if st.button("🗑️ Hapus Mapping"):
                delete_mapping_api(selected_mapping["id"], selected_mapping["yolo_label"])
                st.session_state.last_selected_edit_key = None
                st.rerun()
