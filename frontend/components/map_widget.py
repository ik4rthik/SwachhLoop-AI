import streamlit as st


# Priority / type → color mapping
MARKER_COLORS = {
    "CRITICAL": "#c62828",
    "HIGH":     "#e65100",
    "MEDIUM":   "#f57f17",
    "LOW":      "#2d6a4f",
    "RESOLVED": "#9090a8",
    "CLEANER":  "#1565c0",
    "USER":     "#6B2737",
}


def _build_svg_map(markers: list[dict], width: int = 600, height: int = 260) -> str:
    """Build a simple SVG placeholder map with positioned markers."""
    BASE_LAT, BASE_LON = 10.5273, 76.2144
    SCALE_LAT, SCALE_LON = 2000, 2000  # degrees to pixels

    def project(lat: float, lon: float) -> tuple[float, float]:
        x = (lon - BASE_LON) * SCALE_LON + width / 2
        y = -(lat - BASE_LAT) * SCALE_LAT + height / 2
        return x, y

    marker_svgs = []
    for m in markers:
        try:
            x, y = project(m["lat"], m["lon"])
            color = MARKER_COLORS.get(m.get("type", "LOW"), "#9090a8")
            label = m.get("label", "")
            marker_svgs.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="{color}" stroke="white" stroke-width="2" opacity="0.9"/>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="{color}" opacity="0.15"/>'
                f'<title>{label}</title>'
            )
        except Exception:
            pass

    markers_svg = "".join(marker_svgs)

    grid_lines = []
    for i in range(0, width, 60):
        grid_lines.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{height}" stroke="#d0e8f0" stroke-width="0.5"/>')
    for j in range(0, height, 45):
        grid_lines.append(f'<line x1="0" y1="{j}" x2="{width}" y2="{j}" stroke="#d0e8f0" stroke-width="0.5"/>')
    grid = "".join(grid_lines)

    svg = (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:{height}px;border-radius:12px;">'
        f'<rect width="{width}" height="{height}" fill="#e8f4f8"/>'
        f'{grid}'
        f'<line x1="{width//2}" y1="0" x2="{width//2}" y2="{height}" stroke="#cfdde8" stroke-width="3"/>'
        f'<line x1="0" y1="{height//2}" x2="{width}" y2="{height//2}" stroke="#cfdde8" stroke-width="3"/>'
        f'<line x1="80" y1="0" x2="{width-80}" y2="{height}" stroke="#cfdde8" stroke-width="1.5" opacity="0.6"/>'
        f'{markers_svg}'
        f'<text x="{width-4}" y="{height-4}" text-anchor="end" font-size="9" fill="#9090a8" opacity="0.7">Phase 2 · Prototype Map · Real map in Phase 3/4</text>'
        f'</svg>'
    )
    return svg


def render_map(
    markers: list[dict],
    height: int = 260,
    title: str | None = None,
    show_legend: bool = True,
) -> None:
    if title:
        st.markdown(f'<div class="section-title">🗺️ {title}</div>', unsafe_allow_html=True)

    svg = _build_svg_map(markers, height=height)
    st.markdown(f'<div class="map-card" style="padding:0.5rem;">{svg}</div>', unsafe_allow_html=True)

    if show_legend and markers:
        legend_items = []
        seen = set()
        for m in markers:
            t = m.get("type", "LOW")
            if t not in seen:
                seen.add(t)
                color = MARKER_COLORS.get(t, "#9090a8")
                legend_items.append(
                    f'<span style="display:inline-flex;align-items:center;gap:4px;margin-right:12px;font-size:0.75rem;color:#5a5a7a;">'
                    f'<span style="width:10px;height:10px;border-radius:50%;background:{color};display:inline-block;"></span>'
                    f'{t.title()}</span>'
                )
        st.markdown(f'<div style="padding:0.4rem 0;display:flex;flex-wrap:wrap;">{"".join(legend_items)}</div>', unsafe_allow_html=True)
