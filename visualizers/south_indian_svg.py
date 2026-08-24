"""South Indian Fixed Grid SVG Chart Visualizer.

Generates a responsive, modern dark-mode SVG string of the traditional
South Indian 4x4 fixed-sign grid chart layout with rising sign highlights,
house number tags, planet glyph badges, and central chart summary.
"""

from typing import Optional

from core.constants import ZODIAC_SIGNS, PlanetEnum
from engines.parashari import VargaChart
from schemas.models import UnifiedChartData


# Fixed mapping of Zodiac Sign ID (1 to 12) to (col, row) grid coordinates in 4x4 layout
# Clockwise from Pisces at (0,0) and Aries at (1,0)
SOUTH_SIGN_GRID = {
    12: {"col": 0, "row": 0, "name": "Meena", "en": "Pisces"},
    1:  {"col": 1, "row": 0, "name": "Mesha", "en": "Aries"},
    2:  {"col": 2, "row": 0, "name": "Vrishabha", "en": "Taurus"},
    3:  {"col": 3, "row": 0, "name": "Mithuna", "en": "Gemini"},
    4:  {"col": 3, "row": 1, "name": "Karka", "en": "Cancer"},
    5:  {"col": 3, "row": 2, "name": "Simha", "en": "Leo"},
    6:  {"col": 3, "row": 3, "name": "Kanya", "en": "Virgo"},
    7:  {"col": 2, "row": 3, "name": "Tula", "en": "Libra"},
    8:  {"col": 1, "row": 3, "name": "Vrishchika", "en": "Scorpio"},
    9:  {"col": 0, "row": 3, "name": "Dhanu", "en": "Sagittarius"},
    10: {"col": 0, "row": 2, "name": "Makara", "en": "Capricorn"},
    11: {"col": 0, "row": 1, "name": "Kumbha", "en": "Aquarius"},
}

SHORT_PLANET_NAMES = {
    PlanetEnum.SUN: "Su",
    PlanetEnum.MOON: "Mo",
    PlanetEnum.MARS: "Ma",
    PlanetEnum.MERCURY: "Me",
    PlanetEnum.JUPITER: "Ju",
    PlanetEnum.VENUS: "Ve",
    PlanetEnum.SATURN: "Sa",
    PlanetEnum.RAHU: "Ra",
    PlanetEnum.KETU: "Ke",
    PlanetEnum.URANUS: "Ur",
    PlanetEnum.NEPTUNE: "Ne",
    PlanetEnum.PLUTO: "Pl",
}


def generate_south_indian_svg(
    chart: UnifiedChartData,
    varga_chart: Optional[VargaChart] = None,
    title: str = "Rashi Chart (D1)",
    width: int = 600,
    height: int = 600,
) -> str:
    """Generates a responsive SVG string representing the South Indian fixed grid chart.

    Args:
        chart: UnifiedChartData object.
        varga_chart: Optional VargaChart (e.g. D9 Navamsha) to render instead of D1.
        title: Title banner in the center.
        width: Viewport width in pixels.
        height: Viewport height in pixels.

    Returns:
        Clean SVG XML string.
    """
    cell_w = width / 4.0
    cell_h = height / 4.0

    # 1. Determine Ascendant sign ID (1-12)
    if varga_chart is not None:
        asc_sign_id = varga_chart.ascendant.sign_id
        asc_dms = varga_chart.ascendant.dms.formatted
        asc_sign_name = varga_chart.ascendant.sign_name
    else:
        asc_sign_id = chart.angles.ascendant_sign.id
        asc_dms = chart.angles.ascendant_dms.formatted
        asc_sign_name = chart.angles.ascendant_sign.sanskrit_name

    # 2. Group planets by sign ID
    sign_planets: dict[int, list[dict]] = {s: [] for s in range(1, 13)}

    if varga_chart is not None:
        for p_name, p_varga in varga_chart.planets.items():
            if p_name in (PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
                continue
            is_retro = chart.planets[p_name].is_retrograde
            is_combust = chart.planets[p_name].is_combust
            sign_planets[p_varga.sign_id].append({
                "name": p_name,
                "short": SHORT_PLANET_NAMES.get(p_name, p_name.value[:2]),
                "intra_deg_dms": p_varga.dms.formatted,
                "intra_deg_str": f"{int(p_varga.intra_sign_degree)}°{int((p_varga.intra_sign_degree%1)*60):02d}'",
                "is_retro": is_retro,
                "is_combust": is_combust,
                "nak_name": chart.planets[p_name].nakshatra.sanskrit_name,
                "pada": chart.planets[p_name].nakshatra.pada,
                "sign_name": p_varga.sign_name,
            })
    else:
        for p_name, p_pos in chart.planets.items():
            if p_name in (PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
                continue
            sign_planets[p_pos.sign.id].append({
                "name": p_name,
                "short": SHORT_PLANET_NAMES.get(p_name, p_name.value[:2]),
                "intra_deg_dms": p_pos.sign.dms.formatted,
                "intra_deg_str": f"{int(p_pos.sign.intra_sign_degree)}°{int((p_pos.sign.intra_sign_degree%1)*60):02d}'",
                "is_retro": p_pos.is_retrograde,
                "is_combust": p_pos.is_combust,
                "nak_name": p_pos.nakshatra.sanskrit_name,
                "pada": p_pos.nakshatra.pada,
                "sign_name": p_pos.sign.sanskrit_name,
            })

    # 3. Generate SVG elements
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="100%" height="100%" class="vedic-chart south-chart rounded-xl shadow-2xl overflow-hidden">',
        """
        <defs>
            <linearGradient id="southBg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#0b0f19" />
                <stop offset="100%" stop-color="#1e293b" />
            </linearGradient>
            <linearGradient id="southCenter" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#111827" />
                <stop offset="100%" stop-color="#0f172a" />
            </linearGradient>
            <linearGradient id="goldStroke" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#fbbf24" />
                <stop offset="100%" stop-color="#d97706" />
            </linearGradient>
        </defs>
        """,
        f'<rect width="{width}" height="{height}" fill="url(#southBg)" rx="16" />',
    ]

    # Grid outer & cell borders
    for row in range(4):
        for col in range(4):
            # Skip the 2x2 center block
            if (row in (1, 2)) and (col in (1, 2)):
                continue

            x = col * cell_w
            y = row * cell_h
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" '
                f'fill="#1e293b" fill-opacity="0.5" stroke="#d4af37" stroke-width="1.5" />'
            )

    # Central 2x2 Summary Box
    center_x = cell_w
    center_y = cell_h
    center_w = cell_w * 2
    center_h = cell_h * 2
    svg_parts.append(
        f'<rect x="{center_x}" y="{center_y}" width="{center_w}" height="{center_h}" '
        f'fill="url(#southCenter)" stroke="#d4af37" stroke-width="2" rx="4" />'
    )
    svg_parts.append(
        f'<text x="{center_x + center_w/2}" y="{center_y + 45}" fill="#fbbf24" '
        f'font-family="system-ui, sans-serif" font-size="16" font-weight="700" text-anchor="middle">{title}</text>'
    )
    svg_parts.append(
        f'<text x="{center_x + center_w/2}" y="{center_y + 85}" fill="#38bdf8" '
        f'font-family="system-ui, sans-serif" font-size="13" font-weight="600" text-anchor="middle">'
        f'Ascendant: {asc_sign_name} ({asc_dms})</text>'
    )
    svg_parts.append(
        f'<text x="{center_x + center_w/2}" y="{center_y + 120}" fill="#94a3b8" '
        f'font-family="system-ui, sans-serif" font-size="12" text-anchor="middle">'
        f'Ayanamsha: {chart.ayanamsha_name.value} {chart.ayanamsha_dms.formatted}</text>'
    )
    svg_parts.append(
        f'<text x="{center_x + center_w/2}" y="{center_y + 155}" fill="#64748b" '
        f'font-family="ui-monospace, monospace" font-size="11" text-anchor="middle">'
        f'Birth: {chart.input_data.year}-{chart.input_data.month:02d}-{chart.input_data.day:02d} '
        f'{chart.input_data.hour:02d}:{chart.input_data.minute:02d}</text>'
    )
    if chart.input_data.location.city:
        svg_parts.append(
            f'<text x="{center_x + center_w/2}" y="{center_y + 185}" fill="#64748b" '
            f'font-family="system-ui, sans-serif" font-size="11" text-anchor="middle">'
            f'Loc: {chart.input_data.location.city}, {chart.input_data.location.country or ""}</text>'
        )

    # 4. Render Signs and Planets in the 12 Grid Cells
    for sign_id, grid_info in SOUTH_SIGN_GRID.items():
        col = grid_info["col"]
        row = grid_info["row"]
        x = col * cell_w
        y = row * cell_h
        s_name = grid_info["name"]
        s_en = grid_info["en"]

        # Calculate house number relative to Ascendant (1 to 12)
        house_num = ((sign_id - asc_sign_id) % 12) + 1
        is_asc_sign = (sign_id == asc_sign_id)

        # Highlight Ascendant cell
        if is_asc_sign:
            svg_parts.append(
                f'<rect x="{x+2}" y="{y+2}" width="{cell_w-4}" height="{cell_h-4}" '
                f'fill="#0369a1" fill-opacity="0.2" stroke="#38bdf8" stroke-width="2" />'
            )
            # Diagonal corner slash for Lagna
            svg_parts.append(
                f'<line x1="{x}" y1="{y+35}" x2="{x+35}" y2="{y}" stroke="#38bdf8" stroke-width="2" />'
            )
            svg_parts.append(
                f'<text x="{x+10}" y="{y+18}" fill="#38bdf8" font-family="system-ui, sans-serif" '
                f'font-size="10" font-weight="800">ASC</text>'
            )

        # Sign Label (Top left or top right)
        sign_label_x = x + (40 if is_asc_sign else 8)
        svg_parts.append(
            f'<g class="south-sign-header">'
            f'<title>{sign_id}. {s_name} ({s_en}) - House {house_num}</title>'
            f'<text x="{sign_label_x}" y="{y+16}" fill="#94a3b8" font-family="system-ui, sans-serif" '
            f'font-size="11" font-weight="600">{s_name}</text>'
            f'<text x="{x + cell_w - 8}" y="{y+16}" fill="#64748b" font-family="system-ui, sans-serif" '
            f'font-size="10" font-weight="500" text-anchor="end">H{house_num}</text>'
            f'</g>'
        )

        # Render Planets in this sign
        planets_in_sign = sign_planets[sign_id]
        if planets_in_sign:
            line_height = 17
            start_py = y + 36

            for idx, p in enumerate(planets_in_sign):
                py = start_py + (idx * line_height)

                status_flag = ""
                flag_color = "#f8fafc"
                if p["is_retro"] and p["is_combust"]:
                    status_flag = " (R,C)"
                    flag_color = "#f87171"
                elif p["is_retro"]:
                    status_flag = " (R)"
                    flag_color = "#f43f5e"
                elif p["is_combust"]:
                    status_flag = " (C)"
                    flag_color = "#fb923c"

                badge_text = f"{p['short']} {p['intra_deg_str']}{status_flag}"
                tooltip = (
                    f"{p['name'].value} in {p['sign_name']} ({p['intra_deg_dms']})\n"
                    f"Nakshatra: {p['nak_name']} Pada {p['pada']}\n"
                    f"Status: {'Retrograde' if p['is_retro'] else 'Direct'}"
                    f"{', Combust' if p['is_combust'] else ''}"
                )

                svg_parts.append(
                    f'<g class="planet-glyph cursor-pointer">'
                    f'<title>{tooltip}</title>'
                    f'<text x="{x + cell_w/2}" y="{py}" fill="{flag_color}" '
                    f'font-family="ui-monospace, monospace" font-size="11" font-weight="600" text-anchor="middle">'
                    f'{badge_text}</text>'
                    f'</g>'
                )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)
