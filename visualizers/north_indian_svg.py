"""Minimalist Architectural North Indian Diamond SVG Visualizer.

Renders pure geometry and high-contrast typography on Ivory (Light)
and Deep Espresso (Dark) canvas without blues or flashy colors.
Supports Sanskrit and English sign name toggling.
"""

from typing import Optional

from core.constants import ZODIAC_SIGNS, PlanetEnum
from engines.parashari import VargaChart
from schemas.models import UnifiedChartData

# Dark Mode Palette: Warm Gold, Terracotta, Sage, and Muted Earth Tones on Espresso Canvas
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

# Light Mode Palette: Deep High-Contrast Earthy & Warm Gold Colors on Ivory Canvas
PLANET_THEMES_LIGHT = {
    PlanetEnum.SUN:     {"glyph": "☉", "short": "Su", "color": "#B45309", "name": "Sun"},      # Amber Gold
    PlanetEnum.MOON:    {"glyph": "☽", "short": "Mo", "color": "#1C1917", "name": "Moon"},     # Deep Charcoal
    PlanetEnum.MARS:    {"glyph": "♂", "short": "Ma", "color": "#B91C1C", "name": "Mars"},     # Terracotta Crimson
    PlanetEnum.MERCURY: {"glyph": "☿", "short": "Me", "color": "#047857", "name": "Mercury"},  # Forest Jade
    PlanetEnum.JUPITER: {"glyph": "♃", "short": "Ju", "color": "#CA8A04", "name": "Jupiter"},  # Royal Amber Gold
    PlanetEnum.VENUS:   {"glyph": "♀", "short": "Ve", "color": "#92400E", "name": "Venus"},    # Warm Bronze
    PlanetEnum.SATURN:  {"glyph": "♄", "short": "Sa", "color": "#57534E", "name": "Saturn"},   # Deep Warm Slate
    PlanetEnum.RAHU:    {"glyph": "☊", "short": "Ra", "color": "#6B21A8", "name": "Rahu"},     # Deep Amethyst
    PlanetEnum.KETU:    {"glyph": "☋", "short": "Ke", "color": "#C2410C", "name": "Ketu"},     # Burnt Sienna
    PlanetEnum.URANUS:  {"glyph": "♅", "short": "Ur", "color": "#0F766E", "name": "Uranus"},
    PlanetEnum.NEPTUNE: {"glyph": "♆", "short": "Ne", "color": "#475569", "name": "Neptune"},
    PlanetEnum.PLUTO:   {"glyph": "♇", "short": "Pl", "color": "#831843", "name": "Pluto"},
}

# Dedicated Non-Overlapping Coordinates for Sign Numbers and Planet Text
HOUSE_CONFIG = {
    1:  {"center": (400, 200), "sign_pos": (400, 365), "type": "diamond"},
    2:  {"center": (200, 115), "sign_pos": (200, 32),  "type": "triangle"},
    3:  {"center": (115, 200), "sign_pos": (32, 200),  "type": "triangle"},
    4:  {"center": (190, 400), "sign_pos": (365, 400), "type": "diamond"},
    5:  {"center": (115, 600), "sign_pos": (32, 600),  "type": "triangle"},
    6:  {"center": (200, 685), "sign_pos": (200, 770), "type": "triangle"},
    7:  {"center": (400, 600), "sign_pos": (400, 435), "type": "diamond"},
    8:  {"center": (600, 685), "sign_pos": (600, 770), "type": "triangle"},
    9:  {"center": (685, 600), "sign_pos": (768, 600), "type": "triangle"},
    10: {"center": (610, 400), "sign_pos": (435, 400), "type": "diamond"},
    11: {"center": (685, 200), "sign_pos": (768, 200), "type": "triangle"},
    12: {"center": (600, 115), "sign_pos": (600, 32),  "type": "triangle"},
}


def generate_north_indian_svg(
    chart: UnifiedChartData,
    varga_chart: Optional[VargaChart] = None,
    title: str = "D1 Rashi Chart",
    width: int = 800,
    height: int = 800,
    sign_mode: str = "sanskrit",
    theme_mode: str = "light",
) -> str:
    """Generates a clean North Indian Diamond Kundali SVG with Ivory and Amber theme support."""
    is_dark = (theme_mode == "dark")
    palette = PLANET_THEMES_DARK if is_dark else PLANET_THEMES_LIGHT

    # 1. Determine Ascendant Sign ID (1 to 12)
    if varga_chart is not None:
        asc_sign_id = varga_chart.ascendant.sign_id
        asc_dms = varga_chart.ascendant.dms.formatted
        asc_intra_deg = varga_chart.ascendant.intra_sign_degree
        asc_sign_name = (
            ZODIAC_SIGNS[asc_sign_id]["english_name"]
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

    # 2. Map Houses (1 to 12) to Sign IDs
    house_signs = {h: ((asc_sign_id + h - 2) % 12) + 1 for h in range(1, 13)}
    sign_to_house = {s: h for h, s in house_signs.items()}

    # 3. Group Planets by House
    house_planets: dict[int, list[dict]] = {h: [] for h in range(1, 13)}

    if varga_chart is not None:
        for p_name, p_varga in varga_chart.planets.items():
            if p_name in (PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
                continue
            h_num = sign_to_house[p_varga.sign_id]
            theme = palette.get(p_name, {"glyph": "", "short": p_name.value[:2], "color": "#1C1917" if not is_dark else "#F5F2EB", "name": p_name.value})
            s_name = (
                ZODIAC_SIGNS[p_varga.sign_id]["english_name"]
                if sign_mode == "english"
                else p_varga.sign_name
            )
            is_retro = chart.planets[p_name].is_retrograde if chart and p_name in chart.planets else False
            house_planets[h_num].append({
                "name": p_name,
                "glyph": theme["glyph"],
                "short": theme["short"],
                "color": theme["color"],
                "intra_deg_dms": p_varga.dms.formatted,
                "intra_deg_str": f"{int(p_varga.intra_sign_degree)}°{int((p_varga.intra_sign_degree%1)*60):02d}'",
                "is_retro": is_retro,
                "is_combust": False,
                "nak_name": "",
                "pada": 0,
                "sign_name": s_name,
            })
    else:
        for p_name, p_pos in chart.planets.items():
            if p_name in (PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
                continue
            h_num = sign_to_house[p_pos.sign.id]
            theme = palette.get(p_name, {"glyph": "", "short": p_name.value[:2], "color": "#1C1917" if not is_dark else "#F5F2EB", "name": p_name.value})
            s_name = (
                p_pos.sign.english_name
                if sign_mode == "english"
                else p_pos.sign.sanskrit_name
            )
            house_planets[h_num].append({
                "name": p_name,
                "glyph": theme["glyph"],
                "short": theme["short"],
                "color": theme["color"],
                "intra_deg_dms": p_pos.sign.dms.formatted,
                "intra_deg_str": f"{int(p_pos.sign.intra_sign_degree)}°{int((p_pos.sign.intra_sign_degree%1)*60):02d}'",
                "is_retro": p_pos.is_retrograde,
                "is_combust": p_pos.is_combust,
                "nak_name": p_pos.nakshatra.sanskrit_name,
                "pada": p_pos.nakshatra.pada,
                "sign_name": s_name,
            })

    # Always include Ascendant (Lagna) point with exact intra-sign degree
    house_planets[1].insert(0, {
        "name": "Ascendant",
        "glyph": "✧",
        "short": "As",
        "color": "#D97706" if not is_dark else "#F59E0B",
        "intra_deg_dms": asc_dms,
        "intra_deg_str": asc_intra_deg_str,
        "is_retro": False,
        "is_combust": False,
        "nak_name": chart.angles.ascendant_nakshatra.sanskrit_name if varga_chart is None else "",
        "pada": chart.angles.ascendant_nakshatra.pada if varga_chart is None else 0,
        "sign_name": asc_sign_name,
    })

    # Theme-specific color parameters (Warm Ivory vs Deep Espresso)
    if is_dark:
        bg_fill = "url(#espressoBg)"
        bg_border = "#38332E"
        kendra_stroke = "#F59E0B"
        diag_stroke = "#78716C"
        cross_stroke = "#292524"
        guide_stroke1 = "#292524"
        guide_stroke2 = "#3D3731"
        sign_color = "#A8A29E"
        lagna_bg = "#292524"
        lagna_stroke = "#F59E0B"
        lagna_text = "#FDE68A"
    else:
        bg_fill = "url(#ivoryBg)"
        bg_border = "#DDD6C9"
        kendra_stroke = "#D97706"
        diag_stroke = "#A8A29E"
        cross_stroke = "#E7E1D7"
        guide_stroke1 = "#EFECE4"
        guide_stroke2 = "#DDD6C9"
        sign_color = "#78716C"
        lagna_bg = "#FEF3C7"
        lagna_stroke = "#D97706"
        lagna_text = "#92400E"

    # 4. Generate SVG Elements (Canvas 800x800)
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" '
        f'width="100%" height="100%" style="width:100%;height:100%;max-width:100%;display:block;" class="vedic-chart north-chart select-none">',
        f'<title>{title.upper()} - Asc: {asc_sign_name} ({asc_dms})</title>',
        f'<desc>{title.upper()} Asc: {asc_sign_name} {asc_dms} D1 RASHI CHART</desc>',
        f"""
        <defs>
            <radialGradient id="espressoBg" cx="50%" cy="50%" r="70%">
                <stop offset="0%" stop-color="#1E1B18" />
                <stop offset="60%" stop-color="#161412" />
                <stop offset="100%" stop-color="#100E0D" />
            </radialGradient>
            <radialGradient id="swissOnyxBg" cx="50%" cy="50%" r="70%">
                <stop offset="0%" stop-color="#1E1B18" />
                <stop offset="60%" stop-color="#161412" />
                <stop offset="100%" stop-color="#100E0D" />
            </radialGradient>

            <radialGradient id="ivoryBg" cx="50%" cy="50%" r="70%">
                <stop offset="0%" stop-color="#FFFDF9" />
                <stop offset="60%" stop-color="#FAF7F2" />
                <stop offset="100%" stop-color="#F5F2EB" />
            </radialGradient>
            <radialGradient id="swissPorcelainBg" cx="50%" cy="50%" r="70%">
                <stop offset="0%" stop-color="#FFFDF9" />
                <stop offset="60%" stop-color="#FAF7F2" />
                <stop offset="100%" stop-color="#F5F2EB" />
            </radialGradient>
            
            <radialGradient id="kendraShadeDark" cx="50%" cy="50%" r="60%">
                <stop offset="0%" stop-color="#26221E" stop-opacity="0.6" />
                <stop offset="100%" stop-color="#181513" stop-opacity="0.2" />
            </radialGradient>

            <radialGradient id="kendraShadeLight" cx="50%" cy="50%" r="60%">
                <stop offset="0%" stop-color="#FEF9C3" stop-opacity="0.25" />
                <stop offset="100%" stop-color="#FAF7F2" stop-opacity="0.05" />
            </radialGradient>

        </defs>
        """,
        # Background
        f'<rect x="0" y="0" width="800" height="800" rx="16" fill="{bg_fill}" />',
        f'<rect x="0" y="0" width="800" height="800" rx="16" fill="none" stroke="{bg_border}" stroke-width="2" />',

        # Soft Central Kendra Shading (Houses 1, 4, 7, 10)
        f'<polygon points="400,0 800,400 400,800 0,400" fill="url({"#kendraShadeDark" if is_dark else "#kendraShadeLight"})" />',

        # Outer Square Boundary
        f'<rect x="0" y="0" width="800" height="800" fill="none" stroke="{cross_stroke}" stroke-width="2" />',

        # Diagonal Lines (Cross Corners)
        f'<line x1="0" y1="0" x2="800" y2="800" stroke="{diag_stroke}" stroke-width="1.8" />',
        f'<line x1="800" y1="0" x2="0" y2="800" stroke="{diag_stroke}" stroke-width="1.8" />',

        # Inner Central Diamond (The 4 Kendras: H1, H4, H7, H10)
        f'<polygon points="400,0 800,400 400,800 0,400" fill="none" stroke="{kendra_stroke}" stroke-width="2.5" />',

        # Subdivision Diamond Cross Lines (Triangles: H2/H12, H3/H5, H6/H8, H9/H11)
        f'<line x1="200" y1="200" x2="600" y2="200" stroke="{guide_stroke1}" stroke-width="1.2" stroke-dasharray="3,3" />',
        f'<line x1="600" y1="200" x2="600" y2="600" stroke="{guide_stroke1}" stroke-width="1.2" stroke-dasharray="3,3" />',
        f'<line x1="600" y1="600" x2="200" y2="600" stroke="{guide_stroke1}" stroke-width="1.2" stroke-dasharray="3,3" />',
        f'<line x1="200" y1="600" x2="200" y2="200" stroke="{guide_stroke1}" stroke-width="1.2" stroke-dasharray="3,3" />',

        # Center subtle crosshair guides
        f'<line x1="400" y1="360" x2="400" y2="440" stroke="{guide_stroke2}" stroke-width="1" stroke-dasharray="2,2" />',
        f'<line x1="360" y1="400" x2="440" y2="400" stroke="{guide_stroke2}" stroke-width="1" stroke-dasharray="2,2" />',
    ]

    # 5. Render House Numbers and Ascendant / Lagna Badge
    for h_num in range(1, 13):
        sign_id = house_signs[h_num]
        sx, sy = HOUSE_CONFIG[h_num]["sign_pos"]

        # If House 1, render subtle luxury Lagna badge
        if h_num == 1:
            svg_parts.append(
                f'<rect x="342" y="347" width="116" height="26" rx="6" '
                f'fill="{lagna_bg}" stroke="{lagna_stroke}" stroke-width="1.2" />'
                f'<text x="400" y="364" fill="{lagna_text}" font-family="Cinzel, serif" '
                f'font-size="11.5" font-weight="900" text-anchor="middle" letter-spacing="0.5">LAGNA {sign_id} • {asc_intra_deg_str}</text>'
            )
        else:
            svg_parts.append(
                f'<text x="{sx}" y="{sy}" fill="{sign_color}" font-family="JetBrains Mono, monospace" '
                f'font-size="15" font-weight="700" text-anchor="middle" dominant-baseline="central">{sign_id}</text>'
            )

    # 6. Render High-Density Clean Planet Labels
    for h_num, planets in house_planets.items():
        if not planets:
            continue

        cx, cy = HOUSE_CONFIG[h_num]["center"]
        count = len(planets)
        line_height = 25
        start_y = cy - ((count - 1) * line_height / 2.0)

        for idx, p in enumerate(planets):
            py = start_y + (idx * line_height)

            retro_str = " (R)" if p["is_retro"] else ""
            comb_str = " [C]" if p["is_combust"] else ""
            status_flags = f"{retro_str}{comb_str}"

            # Left/Right 2-column formatting per line
            svg_parts.append(
                f'<g class="planet-row cursor-pointer">'
                f'<text x="{cx - 6}" y="{py}" fill="{p["color"]}" font-family="JetBrains Mono, monospace" '
                f'font-size="14" font-weight="800" text-anchor="end" dominant-baseline="central">'
                f'{p["short"]} {status_flags}'
                f'</text>'
                f'<text x="{cx + 6}" y="{py}" fill="{sign_color}" font-family="JetBrains Mono, monospace" '
                f'font-size="13" font-weight="600" text-anchor="start" dominant-baseline="central">'
                f'{p["intra_deg_str"]}'
                f'</text>'
                f'</g>'
            )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)
