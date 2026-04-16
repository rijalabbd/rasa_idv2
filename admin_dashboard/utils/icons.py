"""
Lucide icon helper for Streamlit.

Usage:
    from utils.icons import icon_html, icon_label

    # Inline SVG in st.markdown
    st.markdown(icon_html("refresh-cw") + " Refresh", unsafe_allow_html=True)

    # Button label with icon (text-only fallback if needed)
    if st.button(icon_label("save", "Simpan")):
        ...
"""

# ---------------------------------------------------------------------------
# SVG path data – sourced from Lucide v0.475 (MIT)
# Each value is a tuple of (viewBox, path_d_list)
# We use stroke-based icons (stroke="currentColor", fill="none")
# ---------------------------------------------------------------------------

_ICONS: dict[str, tuple[str, list[str]]] = {
    # Navigation / general
    "layout-dashboard": (
        "0 0 24 24",
        [
            "M3 3h7v7H3z",
            "M14 3h7v7h-7z",
            "M14 14h7v7h-7z",
            "M3 14h7v7H3z",
        ],
    ),
    "link": (
        "0 0 24 24",
        [
            "M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71",
            "M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71",
        ],
    ),
    "database": (
        "0 0 24 24",
        [
            "M12 2C8.13 2 5 3.34 5 5v14c0 1.66 3.13 3 7 3s7-1.34 7-3V5c0-1.66-3.13-3-7-3z",
            "M5 5c0 1.66 3.13 3 7 3s7-1.34 7-3",
            "M5 12c0 1.66 3.13 3 7 3s7-1.34 7-3",
        ],
    ),
    "package": (
        "0 0 24 24",
        [
            "M16.5 9.4 7.55 4.24",
            "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z",
            "M3.27 6.96 12 12.01l8.73-5.05",
            "M12 22.08V12",
        ],
    ),
    "bar-chart-2": (
        "0 0 24 24",
        [
            "M18 20V10",
            "M12 20V4",
            "M6 20v-6",
        ],
    ),
    "monitor": (
        "0 0 24 24",
        [
            "M20 3H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1z",
            "M8 21h8",
            "M12 17v4",
        ],
    ),

    # Actions
    "refresh-cw": (
        "0 0 24 24",
        [
            "M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8",
            "M21 3v5h-5",
            "M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16",
            "M8 16H3v5",
        ],
    ),
    "save": (
        "0 0 24 24",
        [
            "M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z",
            "M17 21v-8H7v8",
            "M7 3v5h8",
        ],
    ),
    "trash-2": (
        "0 0 24 24",
        [
            "M3 6h18",
            "M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6",
            "M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2",
            "M10 11v6",
            "M14 11v6",
        ],
    ),
    "pencil": (
        "0 0 24 24",
        [
            "M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z",
        ],
    ),
    "plus": (
        "0 0 24 24",
        ["M12 5v14", "M5 12h14"],
    ),
    "x": (
        "0 0 24 24",
        ["M18 6 6 18", "M6 6l12 12"],
    ),
    "upload": (
        "0 0 24 24",
        [
            "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4",
            "M17 8l-5-5-5 5",
            "M12 3v12",
        ],
    ),
    "download": (
        "0 0 24 24",
        [
            "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4",
            "M7 10l5 5 5-5",
            "M12 15V3",
        ],
    ),

    # Status / info
    "check-circle": (
        "0 0 24 24",
        ["M22 11.08V12a10 10 0 1 1-5.93-9.14", "M22 4 12 14.01l-3-3"],
    ),
    "x-circle": (
        "0 0 24 24",
        ["M12 22c5.52 0 10-4.48 10-10S17.52 2 12 2 2 6.48 2 12s4.48 10 10 10z", "M15 9l-6 6", "M9 9l6 6"],
    ),
    "alert-triangle": (
        "0 0 24 24",
        [
            "M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z",
            "M12 9v4",
            "M12 17h.01",
        ],
    ),
    "info": (
        "0 0 24 24",
        [
            "M12 22c5.52 0 10-4.48 10-10S17.52 2 12 2 2 6.48 2 12s4.48 10 10 10z",
            "M12 16v-4",
            "M12 8h.01",
        ],
    ),
    "clock": (
        "0 0 24 24",
        [
            "M12 22c5.52 0 10-4.48 10-10S17.52 2 12 2 2 6.48 2 12s4.48 10 10 10z",
            "M12 6v6l4 2",
        ],
    ),

    # Tools / wrench
    "wrench": (
        "0 0 24 24",
        [
            "M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z",
        ],
    ),
    "search": (
        "0 0 24 24",
        [
            "M21 21l-4.35-4.35",
            "M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z",
        ],
    ),
    "cpu": (
        "0 0 24 24",
        [
            "M18 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z",
            "M9 9h6v6H9z",
            "M9 1v3", "M15 1v3", "M9 20v3", "M15 20v3",
            "M1 9h3", "M1 15h3", "M20 9h3", "M20 15h3",
        ],
    ),
    "file-text": (
        "0 0 24 24",
        [
            "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z",
            "M14 2v6h6",
            "M16 13H8", "M16 17H8", "M10 9H8",
        ],
    ),
    "folder-open": (
        "0 0 24 24",
        [
            "M6 14l1.45-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.55 6a2 2 0 0 1-1.94 1.5H4a2 2 0 0 1-2-2V5c0-1.1.9-2 2-2h3.93a2 2 0 0 1 1.66.9l.82 1.2a2 2 0 0 0 1.66.9H18a2 2 0 0 1 2 2v2",
        ],
    ),
    "image": (
        "0 0 24 24",
        [
            "M21 3H3a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z",
            "M8.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z",
            "M21 15l-5-5L5 21",
        ],
    ),
    "tag": (
        "0 0 24 24",
        [
            "M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z",
            "M7 7h.01",
        ],
    ),
    "file-down": (
        "0 0 24 24",
        [
            "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z",
            "M14 2v6h6",
            "M12 18v-6",
            "M9 15l3 3 3-3",
        ],
    ),
    "activity": (
        "0 0 24 24",
        ["M22 12h-4l-3 9L9 3l-3 9H2"],
    ),
    "map-pin": (
        "0 0 24 24",
        [
            "M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z",
            "M12 10a1 1 0 1 0 0-2 1 1 0 0 0 0 2z",
        ],
    ),
    "list": (
        "0 0 24 24",
        ["M8 6h13", "M8 12h13", "M8 18h13", "M3 6h.01", "M3 12h.01", "M3 18h.01"],
    ),
    "eye": (
        "0 0 24 24",
        [
            "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z",
            "M12 12a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
        ],
    ),
}


def icon_html(name: str, size: int = 16, color: str = "currentColor", extra_style: str = "") -> str:
    """
    Return an inline SVG string for the given Lucide icon name.

    Args:
        name: Lucide icon name (e.g. "trash-2", "refresh-cw")
        size: Width/height in pixels (default 16)
        color: SVG stroke color (default "currentColor" – follows text color)
        extra_style: Additional CSS style added to the <svg> element

    Returns:
        HTML string with the SVG icon, ready for use in st.markdown(..., unsafe_allow_html=True)
    """
    if name not in _ICONS:
        return ""

    viewbox, paths = _ICONS[name]
    path_elements = "\n  ".join(
        f'<path d="{d}" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
        for d in paths
    )

    style = (
        f"display:inline-block;vertical-align:middle;"
        f"margin-right:4px;{extra_style}"
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="{viewbox}" style="{style}">\n  {path_elements}\n</svg>'
    )


def icon_md(name: str, label: str = "", size: int = 16, color: str = "currentColor") -> str:
    """
    Return a markdown-safe HTML string combining icon + optional text label.

    Example:
        st.markdown(icon_md("refresh-cw", "Refresh"), unsafe_allow_html=True)
    """
    svg = icon_html(name, size=size, color=color)
    if label:
        return f'{svg}<span style="vertical-align:middle;">{label}</span>'
    return svg


# ---------------------------------------------------------------------------
# Heading helpers (produce full HTML heading elements with icon)
# Usage: st.markdown(h1("activity", "Dashboard"), unsafe_allow_html=True)
# ---------------------------------------------------------------------------

def _heading(tag: str, icon_name: str, text: str, icon_size: int = 22) -> str:
    """Internal: build an HTML heading element with an icon."""
    tag_styles = {
        "h1": "font-size:2rem;font-weight:700;",
        "h2": "font-size:1.5rem;font-weight:600;",
        "h3": "font-size:1.15rem;font-weight:600;",
    }
    style = f"display:flex;align-items:center;gap:10px;{tag_styles.get(tag, '')}"
    svg = icon_html(icon_name, size=icon_size, extra_style="margin-right:0;flex-shrink:0;")
    return f'<{tag} style="{style}">{svg}<span>{text}</span></{tag}>'


def h1(icon_name: str, text: str) -> str:
    """Return HTML for a page title (<h1>) with a Lucide icon."""
    return _heading("h1", icon_name, text, icon_size=28)


def h2(icon_name: str, text: str) -> str:
    """Return HTML for a section heading (<h2>) with a Lucide icon."""
    return _heading("h2", icon_name, text, icon_size=22)


def h3(icon_name: str, text: str) -> str:
    """Return HTML for a subsection heading (<h3>) with a Lucide icon."""
    return _heading("h3", icon_name, text, icon_size=18)


def labeled_section(icon_name: str, text: str) -> str:
    """
    Return HTML for a bold inline label with icon (e.g. panel section title).
    Rendered as a <p> with bold text.
    """
    svg = icon_html(icon_name, size=16, extra_style="margin-right:0;flex-shrink:0;")
    return (
        f'<p style="display:flex;align-items:center;gap:6px;font-weight:600;margin:0 0 4px 0;">'
        f'{svg}<span>{text}</span></p>'
    )

