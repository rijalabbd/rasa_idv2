import streamlit as st
from utils.api import api_request, format_datetime
from utils.icons import h1, h2, labeled_section, icon_md, icon_html

# =============================================================================
# Functions: Mappings API
# =============================================================================

def fetch_mappings(q: str = ""):
    """Fetch mappings from API."""
    params = {"limit": 100}
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
    """Save/update mapping via upsert."""
    payload = {
        "yolo_label": yolo_label.lower().strip(),
        "tkpi_food_id": tkpi_food_id,
        "ui_status": ui_status,
        "ui_note": ui_note if ui_note.strip() else None
    }
    with st.spinner("Saving class mapping..."):
        data, status, _, _ = api_request("POST", "/admin/mappings", json=payload)
    if status == 200:
        st.toast(f"Successfully saved class mapping: {yolo_label}")
        fetch_mappings(st.session_state.get("mapping_search_q", ""))
        return True
    else:
        st.toast("Failed to save class mapping.")
        return False


def delete_mapping_api(mapping_id: int, label: str):
    """Delete a mapping."""
    with st.spinner(f"Deleting class mapping '{label}'..."):
        _, status, _, _ = api_request("DELETE", f"/admin/mappings/{mapping_id}")
    if status == 200:
        st.toast(f"Class mapping '{label}' successfully deleted.")
        fetch_mappings(st.session_state.get("mapping_search_q", ""))
    else:
        st.toast(f"Failed to delete class mapping '{label}'. HTTP {status}")


# =============================================================================
# Helpers: Form State
# =============================================================================

def _clear_form():
    """Reset form fields to default/empty state."""
    st.session_state.mf_yolo_label = ""
    st.session_state.mf_status = "COCOK"
    st.session_state.mf_note = ""
    st.session_state.mf_tkpi_id = None
    st.session_state.mf_tkpi_name = ""
    st.session_state.mf_edit_id = None
    st.session_state.mf_edit_label = None
    st.session_state.mf_tkpi_search_q = ""
    st.session_state.mf_tkpi_results = []
    st.session_state.confirm_delete_id = None
    st.session_state.show_form = False


def _load_form_from_mapping(mapping: dict):
    """Populate form fields from an existing mapping."""
    st.session_state.mf_yolo_label = mapping["yolo_label"]
    st.session_state.mf_status = mapping.get("ui_status", "COCOK")
    st.session_state.mf_note = mapping.get("ui_note") or ""
    st.session_state.mf_tkpi_id = mapping["tkpi_food_id"]
    st.session_state.mf_tkpi_name = mapping.get("tkpi_food_name", "")
    st.session_state.mf_edit_id = mapping["id"]
    st.session_state.mf_edit_label = mapping["yolo_label"]
    st.session_state.mf_tkpi_search_q = ""
    st.session_state.mf_tkpi_results = []
    st.session_state.confirm_delete_id = None
    st.session_state.show_form = True


def _ensure_form_state():
    """Initialize form session state keys if not present."""
    defaults = {
        "mf_yolo_label": "",
        "mf_status": "COCOK",
        "mf_note": "",
        "mf_tkpi_id": None,
        "mf_tkpi_name": "",
        "mf_edit_id": None,
        "mf_edit_label": None,
        "mf_tkpi_search_q": "",
        "mf_tkpi_results": [],
        "confirm_delete_id": None,
        "mapping_search_q": "",
        "show_form": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# =============================================================================
# Sub-renders
# =============================================================================

def _render_list_tab():
    """Render the mapping list with inline Edit / Delete actions."""

    # --- Search bar + Refresh ---
    search_col, refresh_col = st.columns([4, 1])
    with search_col:
        q_input = st.text_input(
            "Search YOLO labels",
            value=st.session_state.mapping_search_q,
            placeholder="Search YOLO label (e.g. nasi_goreng)...",
            label_visibility="collapsed",
            key="mapping_search_input"
        )
    with refresh_col:
        if st.button("Refresh", use_container_width=True):
            st.session_state.mapping_search_q = q_input
            fetch_mappings(q_input)
            st.rerun()

    st.session_state.mapping_search_q = q_input

    # --- Load state ---
    if st.session_state.mapping_list is None and st.session_state.mapping_list_error is None:
        fetch_mappings()

    if st.session_state.mapping_list_error:
        st.error(f"Failed to load class mappings: {st.session_state.mapping_list_error}")
        return

    items = (st.session_state.mapping_list or {}).get("items", [])

    if not items:
        st.info("Mappings list is empty. Click 'Add New Mapping' to get started.")
        return

    st.caption(f"Displaying {len(items)} Class Mappings")

    # --- Header row ---
    col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([2, 3, 1.5, 2.5, 1.5])
    col_h1.markdown("**YOLO Label**")
    col_h2.markdown("**TKPI Food Name**")
    col_h3.markdown("**Match Type**")
    col_h4.markdown("**Last Updated**")
    col_h5.markdown("**Actions**")
    st.divider()

    # --- Data rows ---
    for item in items:
        is_confirm_delete = st.session_state.confirm_delete_id == item["id"]

        if is_confirm_delete:
            # Confirmation row
            st.warning(
                f"Are you sure you want to delete the mapping for YOLO label **{item['yolo_label']}**? This action cannot be undone."
            )
            yes_col, no_col, _ = st.columns([1.5, 1, 4])
            with yes_col:
                if st.button("Yes, Delete Permanently", key=f"confirm_yes_{item['id']}", type="primary"):
                    delete_mapping_api(item["id"], item["yolo_label"])
                    st.session_state.confirm_delete_id = None
                    st.rerun()
            with no_col:
                if st.button("Cancel", key=f"confirm_no_{item['id']}"):
                    st.session_state.confirm_delete_id = None
                    st.rerun()
        else:
            c1, c2, c3, c4, c5 = st.columns([2, 3, 1.5, 2.5, 1.5])
            c1.code(item["yolo_label"], language=None)
            c2.write(item.get("tkpi_food_name", "-"))

            # Status badge using colored text
            status_val = item.get("ui_status", "")
            if status_val in ["COCOK", "EXACT"]:
                c3.markdown(
                    icon_md("check-circle", "Exact Match", size=14, color="#10b981"),
                    unsafe_allow_html=True
                )
            else:
                c3.markdown(
                    icon_md("alert-triangle", "Close Match", size=14, color="#f97316"),
                    unsafe_allow_html=True
                )

            c4.caption(format_datetime(item.get("updated_at")))

            with c5:
                action_a, action_b = st.columns(2)
                with action_a:
                    if st.button("Edit", key=f"edit_{item['id']}", use_container_width=True):
                        _load_form_from_mapping(item)
                        st.rerun()
                with action_b:
                    if st.button("Delete", key=f"del_{item['id']}", use_container_width=True):
                        st.session_state.confirm_delete_id = item["id"]
                        st.rerun()

        st.divider()


def _render_form_tab():
    """Render the Add / Edit form."""
    is_edit = st.session_state.mf_edit_id is not None

    # --- Form header ---
    if is_edit:
        st.markdown(
            labeled_section("pencil", f"Edit Class Mapping for Label: {st.session_state.mf_edit_label}"),
            unsafe_allow_html=True
        )
        st.markdown(
            icon_md("map-pin",
                    f"Selected TKPI Food: **{st.session_state.mf_tkpi_name}** (ID: {st.session_state.mf_tkpi_id})",
                    size=14),
            unsafe_allow_html=True
        )
    else:
        st.caption("Fill in the form below to map a new YOLO model label to TKPI food nutrition data.")

    form_col1, form_col2 = st.columns(2)

    # --- Kolom kiri: YOLO Label + Status + Catatan ---
    with form_col1:
        if is_edit:
            st.text_input(
                "YOLO Label Name",
                value=st.session_state.mf_edit_label,
                disabled=True,
                help="Label name cannot be modified in edit mode"
            )
        else:
            st.session_state.mf_yolo_label = st.text_input(
                "YOLO Label Name",
                value=st.session_state.mf_yolo_label,
                placeholder="e.g. nasi_goreng",
                help="Label output from the YOLO model (lowercase with underscores, e.g. nasi_putih)"
            )

        status_options = ["COCOK", "MENDEKATI"]
        status_labels = ["Exact Match", "Close Match"]
        cur_idx = status_options.index(st.session_state.mf_status) if st.session_state.mf_status in status_options else 0
        selected_status_label = st.radio(
            "Match Accuracy",
            options=status_labels,
            index=cur_idx,
            horizontal=True,
            help="Exact: Identical nutritional values. Close: Approximate values (e.g. cooked dish mapped to raw ingredients)."
        )
        st.session_state.mf_status = status_options[status_labels.index(selected_status_label)]

        default_note = st.session_state.mf_note
        if selected_status_label == "Close Match" and not default_note:
            default_note = "Nilai gizi adalah estimasi rata-rata porsi olahan."

        st.session_state.mf_note = st.text_input(
            "Optional Note",
            value=default_note,
            help="Note displayed to end-users on the client web when nutrition is an approximation."
        )

    # --- Kolom kanan: TKPI Search ---
    with form_col2:
        tkpi_search_q = st.text_input(
            "Search TKPI Foods" + (" (to replace)" if is_edit else ""),
            value=st.session_state.mf_tkpi_search_q,
            placeholder="Search food name...",
            key="mf_tkpi_search_input"
        )
        st.session_state.mf_tkpi_search_q = tkpi_search_q

        if tkpi_search_q and len(tkpi_search_q) >= 2:
            st.session_state.mf_tkpi_results = search_tkpi_api(tkpi_search_q)

        if st.session_state.mf_tkpi_results:
            tkpi_options = {
                f"{t['name']} (ID: {t['id']})": t
                for t in st.session_state.mf_tkpi_results
            }
            selected_tkpi_option = st.selectbox(
                "Select TKPI Search Result",
                options=list(tkpi_options.keys()),
                key="mf_tkpi_select"
            )
            if selected_tkpi_option:
                selected_t = tkpi_options[selected_tkpi_option]
                st.session_state.mf_tkpi_id = selected_t["id"]
                st.session_state.mf_tkpi_name = selected_t["name"]
        elif not is_edit:
            st.caption("Type at least 2 characters to search the TKPI database.")

        # Show currently selected TKPI
        if st.session_state.mf_tkpi_id:
            st.success(
                f"Selected TKPI Food: **{st.session_state.mf_tkpi_name}** (ID: {st.session_state.mf_tkpi_id})"
            )

    st.divider()

    # --- Action buttons ---
    save_col, cancel_col, _ = st.columns([1.5, 1, 3])

    with save_col:
        save_label = "Save Changes" if is_edit else "Save Mapping"
        if st.button(save_label, type="primary", use_container_width=True):
            label_to_save = st.session_state.mf_edit_label if is_edit else st.session_state.mf_yolo_label
            if not label_to_save or not label_to_save.strip():
                st.error("YOLO label is required.")
            elif not st.session_state.mf_tkpi_id:
                st.error("Please search and select a TKPI food first.")
            else:
                ok = save_mapping(
                    label_to_save,
                    st.session_state.mf_tkpi_id,
                    st.session_state.mf_status,
                    st.session_state.mf_note,
                )
                if ok:
                    _clear_form()
                    st.rerun()

    with cancel_col:
        if st.button("Cancel", use_container_width=True):
            _clear_form()
            st.rerun()


# =============================================================================
# Main Render
# =============================================================================

def render_mappings():
    """Render the Mappings Management view."""
    _ensure_form_state()

    st.markdown(h1("link", "Class Mappings (YOLO ↔ TKPI)"), unsafe_allow_html=True)
    st.caption("Manage mapping of YOLO model labels to TKPI food nutrition composition data.")
    st.divider()

    if st.session_state.show_form:
        # ── Form view (Add / Edit) ──────────────────────────────────────────
        is_edit = st.session_state.mf_edit_id is not None
        mode_label = "Edit Class Mapping" if is_edit else "Add New Mapping"
        icon_name = "pencil" if is_edit else "plus"
        st.markdown(h2(icon_name, mode_label), unsafe_allow_html=True)
        _render_form_tab()
    else:
        # ── List view ───────────────────────────────────────────────────────
        if st.button("Add New Mapping", type="primary"):
            _clear_form()
            st.session_state.show_form = True
            st.rerun()
        st.divider()
        _render_list_tab()
