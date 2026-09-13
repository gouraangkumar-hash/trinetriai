"""Minimalist Architectural South Indian Fixed Grid SVG Visualizer.

Generates an expansive, high-contrast SVG on an 800x800 canvas with large typography,
crisp 200x200 grid cells, center HUD, and high-visibility planet details on Ivory (Light)
and Deep Espresso (Dark) canvas without blues or flashy colors.
Supports Sanskrit and English sign name toggling.
"""

from typing import Optional

from core.constants import PlanetEnum
from engines.dignity import EXALTATION_SIGNS, DEBILITATION_SIGNS
from engines.parashari import VargaChart
from schemas.models import UnifiedChartData

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

PLANET_THEMES_DARK = {
    PlanetEnum.SUN:     {"glyph": "☉", "short": "Su", "color": "#FBBF24", "name": "Sun"},
    PlanetEnum.MOON:    {"glyph": "☽", "short": "Mo", "color": "#F5F2EB", "name": "Moon"},
    PlanetEnum.MARS:    {"glyph": "♂", "short": "Ma", "color": "#F87171", "name": "Mars"},
    PlanetEnum.MERCURY: {"glyph": "☿", "short": "Me", "color": "#34D399", "name": "Mercury"},
    PlanetEnum.JUPITER: {"glyph": "♃", "short": "Ju", "color": "#FDE047", "name": "Jupiter"},
    PlanetEnum.VENUS:   {"glyph": "♀", "short": "Ve", "color": "#FCD34D", "name": "Venus"},
    PlanetEnum.SATURN:  {"glyph": "♄", "short": "Sa", "color": "#D6D3D1", "name": "Saturn"},
    PlanetEnum.RAHU:    {"glyph": "☊", "short": "Ra", "color": "#D8B4FE", "name": "Rahu"},
    PlanetEnum.KETU:    {"glyph": "☋", "short": "Ke", "color": "#FB923C", "name": "Ketu"},
    PlanetEnum.URANUS:  {"glyph": "♅", "short": "Ur", "color": "#2DD4BF", "name": "Uranus"},
    PlanetEnum.NEPTUNE: {"glyph": "♆", "short": "Ne", "color": "#94A3B8", "name": "Neptune"},
    PlanetEnum.PLUTO:   {"glyph": "♇", "short": "Pl", "color": "#F472B6", "name": "Pluto"},
}

PLANET_THEMES_LIGHT = {
    PlanetEnum.SUN:     {"glyph": "☉", "short": "Su", "color": "#B45309", "name": "Sun"},
    PlanetEnum.MOON:    {"glyph": "☽", "short": "Mo", "color": "#1C1917", "name": "Moon"},
    PlanetEnum.MARS:    {"glyph": "♂", "short": "Ma", "color": "#B91C1C", "name": "Mars"},
    PlanetEnum.MERCURY: {"glyph": "☿", "short": "Me", "color": "#047857", "name": "Mercury"},
    PlanetEnum.JUPITER: {"glyph": "♃", "short": "Ju", "color": "#CA8A04", "name": "Jupiter"},
    PlanetEnum.VENUS:   {"glyph": "♀", "short": "Ve", "color": "#92400E", "name": "Venus"},
    PlanetEnum.SATURN:  {"glyph": "♄", "short": "Sa", "color": "#57534E", "name": "Saturn"},
    PlanetEnum.RAHU:    {"glyph": "☊", "short": "Ra", "color": "#6B21A8", "name": "Rahu"},
    PlanetEnum.KETU:    {"glyph": "☋", "short": "Ke", "color": "#C2410C", "name": "Ketu"},
    PlanetEnum.URANUS:  {"glyph": "♅", "short": "Ur", "color": "#0F766E", "name": "Uranus"},
    PlanetEnum.NEPTUNE: {"glyph": "♆", "short": "Ne", "color": "#475569", "name": "Neptune"},
    PlanetEnum.PLUTO:   {"glyph": "♇", "short": "Pl", "color": "#831843", "name": "Pluto"},
}


def generate_south_indian_svg(
    chart: UnifiedChartData,
    varga_chart: Optional[VargaChart] = None,
    transit_chart: Optional[UnifiedChartData] = None,
    title: str = "D1 Rashi Chart",
    width: int = 800,
    height: int = 800,
    sign_mode: str = "sanskrit",
    theme_mode: str = "light",
) -> str:
    """Generates an Architectural South Indian Fixed Grid SVG."""
    cell_w = width / 4.0   # 200px
    cell_h = height / 4.0  # 200px
    is_dark = (theme_mode == "dark")
    palette = PLANET_THEMES_DARK if is_dark else PLANET_THEMES_LIGHT

    # 1. Determine Ascendant sign ID (1-12)
    if varga_chart is not None:
        asc_sign_id = varga_chart.ascendant.sign_id
        asc_dms = varga_chart.ascendant.dms.formatted
        asc_intra_deg = varga_chart.ascendant.intra_sign_degree
        asc_sign_name = (
            SOUTH_SIGN_GRID[asc_sign_id]["en"]
            if sign_mode == "english"
            else varga_chart.ascendant.sign_name
        )
    else:
        asc_sign_id = chart.angles.ascendant_sign.id
        asc_dms = chart.angles.ascendant_dms.formatted
        asc_intra_deg = chart.angles.ascendant_sign.intra_sign_degree
        asc_sign_name = (
            chart.angles.ascendant_sign.english_name
            if sign_mode == "english"
            else chart.angles.ascendant_sign.sanskrit_name
        )
    asc_intra_deg_str = f"{int(asc_intra_deg)}°{int((asc_intra_deg%1)*60):02d}'"

    # 2. Group planets by sign ID
    sign_planets: dict[int, list[dict]] = {s: [] for s in range(1, 13)}

    if varga_chart is not None:
        for p_name, p_varga in varga_chart.planets.items():
            if p_name in (PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
                continue
            theme = palette.get(p_name, {"glyph": "", "short": p_name.value[:2], "color": "#1C1917" if not is_dark else "#F5F2EB", "name": p_name.value})
            s_name = (
                SOUTH_SIGN_GRID[p_varga.sign_id]["en"]
                if sign_mode == "english"
                else p_varga.sign_name
            )
            is_retro = chart.planets[p_name].is_retrograde if chart and p_name in chart.planets else False
            is_ex = bool(p_varga.sign_id == EXALTATION_SIGNS.get(p_name))
            is_deb = bool(p_varga.sign_id == DEBILITATION_SIGNS.get(p_name))
            sign_planets[p_varga.sign_id].append({
                "name": p_name,
                "glyph": theme["glyph"],
                "short": theme["short"],
                "color": theme["color"],
                "intra_deg_dms": p_varga.dms.formatted,
                "intra_deg_str": f"{int(p_varga.intra_sign_degree)}°{int((p_varga.intra_sign_degree%1)*60):02d}'",
                "is_retro": is_retro,
                "is_combust": False,
                "is_exalted": is_ex,
                "is_debilitated": is_deb,
                "nak_name": "",
                "pada": 0,
                "sign_name": s_name,
            })
    else:
        for p_name, p_pos in chart.planets.items():
            if p_name in (PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
                continue
            theme = palette.get(p_name, {"glyph": "", "short": p_name.value[:2], "color": "#1C1917" if not is_dark else "#F5F2EB", "name": p_name.value})
            s_name = (
                SOUTH_SIGN_GRID[p_pos.sign.id]["en"]
                if sign_mode == "english"
                else p_pos.sign.sanskrit_name
            )
            is_ex = bool(p_pos.sign.id == EXALTATION_SIGNS.get(p_name))
            is_deb = bool(p_pos.sign.id == DEBILITATION_SIGNS.get(p_name))
            sign_planets[p_pos.sign.id].append({
                "name": p_name,
                "glyph": theme["glyph"],
                "short": theme["short"],
                "color": theme["color"],
                "intra_deg_dms": p_pos.sign.dms.formatted,
                "intra_deg_str": f"{int(p_pos.sign.intra_sign_degree)}°{int((p_pos.sign.intra_sign_degree%1)*60):02d}'",
                "is_retro": p_pos.is_retrograde,
                "is_combust": p_pos.is_combust,
                "is_exalted": is_ex,
                "is_debilitated": is_deb,
                "nak_name": p_pos.nakshatra.sanskrit_name,
                "pada": p_pos.nakshatra.pada,
                "sign_name": s_name,
            })

    # Always include Ascendant (Lagna) point with exact intra-sign degree
    sign_planets[asc_sign_id].insert(0, {
        "name": "Ascendant",
        "glyph": "✧",
        "short": "As",
        "color": "#D97706" if not is_dark else "#F59E0B",
        "intra_deg_dms": asc_dms,
        "intra_deg_str": asc_intra_deg_str,
        "is_retro": False,
        "is_combust": False,
        "is_exalted": False,
        "is_debilitated": False,
        "nak_name": chart.angles.ascendant_nakshatra.sanskrit_name if varga_chart is None else "",
        "pada": chart.angles.ascendant_nakshatra.pada if varga_chart is None else 0,
        "sign_name": asc_sign_name,
    })

    # 2b. Overlay Transit Planets if Gochar is enabled
    transit_color = "#059669" if not is_dark else "#34D399"
    transit_badge_bg = "#064E3B" if is_dark else "#ECFDF5"
    if transit_chart is not None:
        for p_name, p_pos in transit_chart.planets.items():
            if p_name in (PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
                continue
            t_sign_id = p_pos.sign.id
            t_theme = palette.get(p_name, {"glyph": "", "short": p_name.value[:2]})
            sign_planets[t_sign_id].append({
                "name": f"{p_name.value} (Transit)",
                "glyph": t_theme["glyph"],
                "short": f"{t_theme['short']}(T)",
                "color": transit_color,
                "intra_deg_dms": p_pos.sign.dms.formatted,
                "intra_deg_str": f"{int(p_pos.sign.intra_sign_degree)}°{int((p_pos.sign.intra_sign_degree%1)*60):02d}'",
                "is_retro": p_pos.is_retrograde,
                "is_combust": p_pos.is_combust,
                "is_transit": True,
            })

    # Theme parameters
    if is_dark:
        bg_fill = "url(#southEspressoBg)"
        bg_border = "#38332E"
        cell_fill = "#1A1715"
        cell_stroke = "#2A2622"
        hud_fill = "url(#southCenterHudDark)"
        hud_stroke = "#F59E0B"
        hud_title_color = "#FBBF24"
        hud_text_color = "#F5F2EB"
        hud_sub_color = "#A8A29E"
        hud_jd_color = "#78716C"
        sign_label_color = "#D6D3D1"
        house_label_color = "#78716C"
        asc_fill = "#292524"
        asc_stroke = "#F59E0B"
        asc_text = "#FDE68A"
    else:
        bg_fill = "url(#southIvoryBg)"
        bg_border = "#DDD6C9"
        cell_fill = "#FFFFFF"
        cell_stroke = "#E7E1D7"
        hud_fill = "url(#southCenterHudLight)"
        hud_stroke = "#D97706"
        hud_title_color = "#B45309"
        hud_text_color = "#1C1917"
        hud_sub_color = "#57534E"
        hud_jd_color = "#78716C"
        sign_label_color = "#292524"
        house_label_color = "#78716C"
        asc_fill = "#FEF3C7"
        asc_stroke = "#D97706"
        asc_text = "#92400E"

    # 3. Generate SVG elements
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'style="width:100%;height:100%;max-width:100%;display:block;" class="vedic-chart south-chart select-none">',
        f"""
        <defs>
            <radialGradient id="southEspressoBg" cx="50%" cy="50%" r="70%">
                <stop offset="0%" stop-color="#1E1B18" />
                <stop offset="60%" stop-color="#161412" />
                <stop offset="100%" stop-color="#100E0D" />
            </radialGradient>
            <radialGradient id="southOnyxBg" cx="50%" cy="50%" r="70%">
                <stop offset="0%" stop-color="#1E1B18" />
                <stop offset="60%" stop-color="#161412" />
                <stop offset="100%" stop-color="#100E0D" />
            </radialGradient>
            <radialGradient id="southIvoryBg" cx="50%" cy="50%" r="70%">
                <stop offset="0%" stop-color="#FFFDF9" />
                <stop offset="60%" stop-color="#FAF7F2" />
                <stop offset="100%" stop-color="#F5F2EB" />
            </radialGradient>
            <radialGradient id="southPorcelainBg" cx="50%" cy="50%" r="70%">
                <stop offset="0%" stop-color="#FFFDF9" />
                <stop offset="60%" stop-color="#FAF7F2" />
                <stop offset="100%" stop-color="#F5F2EB" />
            </radialGradient>
            <radialGradient id="southCenterHudDark" cx="50%" cy="50%" r="65%">
                <stop offset="0%" stop-color="#26221E" stop-opacity="0.8" />
                <stop offset="100%" stop-color="#161412" stop-opacity="0.5" />
            </radialGradient>
            <radialGradient id="southCenterHudLight" cx="50%" cy="50%" r="65%">
                <stop offset="0%" stop-color="#FEF9C3" stop-opacity="0.3" />
                <stop offset="100%" stop-color="#FAF7F2" stop-opacity="0.1" />
            </radialGradient>
        </defs>
        """,
        # Canvas Background
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="16" fill="{bg_fill}" />',
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="16" fill="none" stroke="{bg_border}" stroke-width="2" />',
    ]

    # 4. Draw 12 Fixed Sign Cells
    for s_id, grid_info in SOUTH_SIGN_GRID.items():
        col = grid_info["col"]
        row = grid_info["row"]
        x = col * cell_w
        y = row * cell_h

        is_asc = (s_id == asc_sign_id)
        house_num = ((s_id - asc_sign_id) % 12) + 1

        sign_name_str = grid_info["en"] if sign_mode == "english" else grid_info["name"]

        # Cell background & border
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" '
            f'fill="{cell_fill}" stroke="{cell_stroke}" stroke-width="1.5" />'
        )

        # Subtle corner accent for Ascendant house
        if is_asc:
            svg_parts.append(
                f'<polygon points="{x},{y} {x+36},{y} {x},{y+36}" fill="{hud_stroke}" fill-opacity="0.25" />'
            )

        # Header bar with Sign Name & House Number
        svg_parts.append(
            f'<text x="{x + 10}" y="{y + 20}" fill="{sign_label_color}" font-family="Cinzel, serif" '
            f'font-size="13" font-weight="800" letter-spacing="0.5">{sign_name_str}</text>'
            f'<text x="{x + cell_w - 10}" y="{y + 20}" fill="{house_label_color}" font-family="JetBrains Mono, monospace" '
            f'font-size="12" font-weight="700" text-anchor="end">H{house_num}</text>'
        )

        # Ascendant indicator badge
        if is_asc:
            svg_parts.append(
                f'<rect x="{x + 10}" y="{y + 28}" width="62" height="20" rx="4" '
                f'fill="{asc_fill}" stroke="{asc_stroke}" stroke-width="1.2" />'
                f'<text x="{x + 41}" y="{y + 42}" fill="{asc_text}" font-family="Cinzel, serif" '
                f'font-size="10" font-weight="900" text-anchor="middle" letter-spacing="0.5">LAGNA</text>'
            )

        # Render Planets in this sign
        planets = sign_planets[s_id]
        if planets:
            p_start_y = y + (52 if is_asc else 38)
            count = len(planets)
            if count <= 2:
                line_height = 22.0
                font_size = 13.0
                deg_font_size = 12.0
            elif count <= 4:
                line_height = 17.0
                font_size = 11.0
                deg_font_size = 10.0
            elif count <= 6:
                line_height = 14.0
                font_size = 9.5
                deg_font_size = 8.5
            else:
                line_height = 12.0
                font_size = 8.5
                deg_font_size = 7.5

            for idx, p in enumerate(planets):
                if idx >= 8:
                    break
                py = p_start_y + (idx * line_height)
                cx = x + (cell_w / 2.0)

                retro_str = "(R)" if p["is_retro"] else ""
                comb_str = "[C]" if p["is_combust"] else ""
                dignity_str = "(E)" if p.get("is_exalted") else ("(D)" if p.get("is_debilitated") else "")
                status_flags = f" {retro_str}" if retro_str else ""
                if comb_str:
                    status_flags += f" {comb_str}"
                if dignity_str:
                    status_flags += f" {dignity_str}"
                is_tr = p.get("is_transit", False)
                deg_col = transit_color if is_tr else sign_label_color

                p_name_str = p["name"].value if hasattr(p["name"], "value") else str(p["name"])
                click_attr = f'onclick="window.togglePlanetAspectRays && window.togglePlanetAspectRays(\'{p_name_str}\', event)"' if p_name_str != "Ascendant" and not is_tr else ""
                title_attr = f'<title>Click to view {p_name_str} aspect rays</title>' if p_name_str != "Ascendant" and not is_tr else ""

                svg_parts.append(
                    f'<g class="planet-row cursor-pointer" {click_attr}>'
                    f'{title_attr}'
                    f'<text x="{cx - 4}" y="{py}" fill="{p["color"]}" font-family="JetBrains Mono, monospace" '
                    f'font-size="{font_size}" font-weight="{"800" if is_tr else "700"}" text-anchor="end" dominant-baseline="central">'
                    f'{p["short"]}{status_flags}'
                    f'</text>'
                    f'<text x="{cx + 4}" y="{py}" fill="{deg_col}" font-family="JetBrains Mono, monospace" '
                    f'font-size="{deg_font_size}" font-weight="{"700" if is_tr else "600"}" text-anchor="start" dominant-baseline="central">'
                    f'{p["intra_deg_str"]}'
                    f'</text>'
                    f'</g>'
                )

    # 5. Center Luxury 2x2 Telemetry HUD (400x400)
    hud_x = cell_w
    hud_y = cell_h
    hud_w = cell_w * 2
    hud_h = cell_h * 2

    jd_val = getattr(chart, "julian_day_ut", getattr(chart, "julian_day", 0.0))

    svg_parts.append(
        f'<rect x="{hud_x}" y="{hud_y}" width="{hud_w}" height="{hud_h}" '
        f'fill="{hud_fill}" stroke="{hud_stroke}" stroke-width="1.5" />'
        f'<rect x="{hud_x+8}" y="{hud_y+8}" width="{hud_w-16}" height="{hud_h-16}" '
        f'fill="none" stroke="{cell_stroke}" stroke-width="1" stroke-dasharray="3,3" />'
    )

    if transit_chart is not None:
        svg_parts.append(
            f'<g transform="translate({hud_x + hud_w/2 - 56}, {hud_y + 35})">'
            f'<rect width="112" height="22" rx="4" fill="{transit_badge_bg}" stroke="{transit_color}" stroke-width="1.2" />'
            f'<text x="56" y="15" fill="{transit_color}" font-family="Cinzel, serif" font-size="9.5" font-weight="900" text-anchor="middle" letter-spacing="0.5">✦ GOCHAR ON</text>'
            f'</g>'
        )

    # Center Content
    svg_parts.append(
        f'<g text-anchor="middle">'
        f'<text x="{hud_x + hud_w/2}" y="{hud_y + 115}" fill="{hud_title_color}" font-family="Cinzel, serif" '
        f'font-size="20" font-weight="900" letter-spacing="3">{title.upper()}</text>'
        f'<line x1="{hud_x + 80}" y1="{hud_y + 135}" x2="{hud_x + hud_w - 80}" y2="{hud_y + 135}" stroke="{hud_stroke}" stroke-width="1.2" stroke-opacity="0.5" />'
        f'<text x="{hud_x + hud_w/2}" y="{hud_y + 175}" fill="{hud_text_color}" font-family="Cinzel, serif" '
        f'font-size="14" font-weight="700">ASC: {asc_sign_name.upper()}</text>'
        f'<text x="{hud_x + hud_w/2}" y="{hud_y + 205}" fill="{hud_title_color}" font-family="JetBrains Mono, monospace" '
        f'font-size="16" font-weight="800">{asc_dms}</text>'
        f'<text x="{hud_x + hud_w/2}" y="{hud_y + 250}" fill="{hud_sub_color}" font-family="Inter, sans-serif" '
        f'font-size="11" font-weight="600" letter-spacing="0.5">SWISS EPHEMERIS LOCAL PRECISION</text>'
        f'<text x="{hud_x + hud_w/2}" y="{hud_y + 275}" fill="{hud_jd_color}" font-family="JetBrains Mono, monospace" '
        f'font-size="10">JD {jd_val:.4f}</text>'
        f'</g>'
    )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)
