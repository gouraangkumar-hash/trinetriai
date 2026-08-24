"""North Indian Diamond (Kundali) SVG Chart Visualizer.

Generates a responsive, modern dark-mode SVG string of the traditional
North Indian chart layout with fixed geometric houses, dynamic zodiac sign
numbers, planet glyph badges, and rich SVG hover tooltips.
"""

from typing import Optional

from core.constants import ZODIAC_SIGNS, PlanetEnum
from engines.parashari import VargaChart
from schemas.models import UnifiedChartData


# Coordinate centers and sign label positions for the 12 houses (600x600 canvas)
NORTH_HOUSE_GEOMETRY = {
    1: {"center": (300, 160), "sign_pos": (300, 265), "name": "1st (Lagna / Tanu)"},
    2: {"center": (150, 75), "sign_pos": (205, 125), "name": "2nd (Dhana)"},
    3: {"center": (65, 150), "sign_pos": (115, 195), "name": "3rd (Sahaja)"},
    4: {"center": (150, 300), "sign_pos": (265, 300), "name": "4th (Sukha)"},
    5: {"center": (65, 450), "sign_pos": (115, 405), "name": "5th (Putra)"},
    6: {"center": (150, 525), "sign_pos": (205, 475), "name": "6th (Ari / Rina)"},
    7: {"center": (300, 440), "sign_pos": (300, 335), "name": "7th (Kalatra / Yuvati)"},
    8: {"center": (450, 525), "sign_pos": (395, 475), "name": "8th (Randhra / Ayu)"},
    9: {"center": (535, 450), "sign_pos": (485, 405), "name": "9th (Dharma / Bhagya)"},
    10: {"center": (450, 300), "sign_pos": (335, 300), "name": "10th (Karma)"},
    11: {"center": (535, 150), "sign_pos": (485, 195), "name": "11th (Labha)"},
    12: {"center": (450, 75), "sign_pos": (395, 125), "name": "12th (Vyaya)"},
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


def generate_north_indian_svg(
    chart: UnifiedChartData,
    varga_chart: Optional[VargaChart] = None,
    title: str = "Rashi Chart (D1)",
    width: int = 600,
    height: int = 600,
) -> str:
    """Generates a responsive SVG string representing the North Indian diamond chart.

    Args:
        chart: UnifiedChartData object.
        varga_chart: Optional VargaChart (e.g. D9 Navamsha) to render instead of D1.
        title: Title banner on top of the chart.
        width: Viewport width in pixels.
        height: Viewport height in pixels.

    Returns:
        Clean SVG XML string.
    """
    # 1. Determine Ascendant sign ID (1-12)
    if varga_chart is not None:
        asc_sign_id = varga_chart.ascendant.sign_id
        asc_dms = varga_chart.ascendant.dms.formatted
        asc_nak_name = ""
        asc_pada = ""
    else:
        asc_sign_id = chart.angles.ascendant_sign.id
        asc_dms = chart.angles.ascendant_dms.formatted
        asc_nak_name = chart.angles.ascendant_nakshatra.sanskrit_name
        asc_pada = str(chart.angles.ascendant_nakshatra.pada)

    # 2. Map signs to houses: House 1 has asc_sign_id, House 2 has asc_sign_id + 1, etc.
    house_to_sign: dict[int, int] = {}
    sign_to_house: dict[int, int] = {}
    for h in range(1, 13):
        s_id = ((asc_sign_id - 1 + (h - 1)) % 12) + 1
        house_to_sign[h] = s_id
        sign_to_house[s_id] = h

    # 3. Group planets by house
    house_planets: dict[int, list[dict]] = {h: [] for h in range(1, 13)}

    if varga_chart is not None:
        for p_name, p_varga in varga_chart.planets.items():
            if p_name in (PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
                continue  # focus on 9 Grahas for visual clarity
            target_house = sign_to_house[p_varga.sign_id]
            is_retro = chart.planets[p_name].is_retrograde
            is_combust = chart.planets[p_name].is_combust
            house_planets[target_house].append({
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
            target_house = sign_to_house[p_pos.sign.id]
            house_planets[target_house].append({
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

    # 4. Generate SVG elements
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="100%" height="100%" class="vedic-chart north-chart rounded-xl shadow-2xl overflow-hidden">',
        # Styles and defs
        """
        <defs>
            <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#0b0f19" />
                <stop offset="100%" stop-color="#1e293b" />
            </linearGradient>
            <linearGradient id="goldLine" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#fbbf24" />
                <stop offset="100%" stop-color="#d97706" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        """,
        # Background
        f'<rect width="{width}" height="{height}" fill="url(#bgGrad)" rx="16" />',
        # Outer Border
        f'<rect x="20" y="20" width="{width-40}" height="{height-40}" fill="none" stroke="url(#goldLine)" stroke-width="2.5" rx="8" />',
        # Inner lines & Diamond structure
        # Main Diagonals
        '<line x1="20" y1="20" x2="580" y2="580" stroke="#d4af37" stroke-width="1.8" stroke-opacity="0.85" />',
        '<line x1="580" y1="20" x2="20" y2="580" stroke="#d4af37" stroke-width="1.8" stroke-opacity="0.85" />',
        # Central Diamond
        '<polygon points="300,20 580,300 300,580 20,300" fill="none" stroke="#d4af37" stroke-width="2.2" />',
    ]

    # Chart Title Header
    svg_parts.append(
        f'<text x="300" y="45" fill="#f59e0b" font-family="system-ui, -apple-system, sans-serif" '
        f'font-size="14" font-weight="700" letter-spacing="1" text-anchor="middle" '
        f'filter="url(#glow)">{title.upper()}</text>'
    )

    # 5. Render Sign Numbers and Planet Badges for each house
    for h in range(1, 13):
        geo = NORTH_HOUSE_GEOMETRY[h]
        s_id = house_to_sign[h]
        s_name = ZODIAC_SIGNS[s_id]["sanskrit_name"]
        sign_x, sign_y = geo["sign_pos"]

        # Sign number tag
        svg_parts.append(
            f'<g class="house-sign-tag">'
            f'<title>House {h} ({geo["name"]}): {s_name} (Sign {s_id})</title>'
            f'<text x="{sign_x}" y="{sign_y}" fill="#94a3b8" font-family="system-ui, sans-serif" '
            f'font-size="12" font-weight="600" text-anchor="middle">{s_id}</text>'
            f'</g>'
        )

        # Ascendant badge in 1st House
        if h == 1:
            svg_parts.append(
                f'<g class="lagna-badge">'
                f'<title>Ascendant (Lagna): {s_name} {asc_dms} - {asc_nak_name} (Pada {asc_pada})</title>'
                f'<rect x="255" y="65" width="90" height="20" rx="4" fill="#0284c7" fill-opacity="0.25" stroke="#38bdf8" stroke-width="1" />'
                f'<text x="300" y="79" fill="#38bdf8" font-family="system-ui, sans-serif" font-size="11" font-weight="700" text-anchor="middle">Asc: {s_name[:4]}</text>'
                f'</g>'
            )

        # Planet Badges in this house
        planets_in_h = house_planets[h]
        if planets_in_h:
            cx, cy = geo["center"]
            num_p = len(planets_in_h)
            line_height = 18

            # Stagger vertical offsets if multiple planets
            start_y = cy - ((num_p - 1) * line_height) / 2.0
            if h == 1:
                start_y += 18  # adjust for Asc badge

            for idx, p in enumerate(planets_in_h):
                py = start_y + (idx * line_height)

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
                    f'<text x="{cx}" y="{py}" fill="{flag_color}" font-family="ui-monospace, monospace" '
                    f'font-size="11" font-weight="600" text-anchor="middle">{badge_text}</text>'
                    f'</g>'
                )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)
