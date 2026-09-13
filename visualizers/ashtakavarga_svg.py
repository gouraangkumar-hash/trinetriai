"""Minimalist Architectural Sarvashtakavarga (SAV) SVG Visualizer.

Generates high-contrast, publication-quality North Indian Diamond and
South Indian Fixed Grid SVGs for Sarvashtakavarga (SAV) macro-zodiac
bindu distribution (strictly 337 bindus).
"""

from typing import Dict
from core.constants import ZODIAC_SIGNS
from engines.ashtakavarga import AshtakavargaFullReport
from schemas.models import UnifiedChartData


# Coordinates for North Indian Diamond Layout (800x800)
NORTH_HOUSE_CONFIG = {
    1:  {"center": (400, 200), "sign_pos": (400, 365)},
    2:  {"center": (200, 115), "sign_pos": (200, 32)},
    3:  {"center": (115, 200), "sign_pos": (32, 200)},
    4:  {"center": (190, 400), "sign_pos": (365, 400)},
    5:  {"center": (115, 600), "sign_pos": (32, 600)},
    6:  {"center": (200, 685), "sign_pos": (200, 770)},
    7:  {"center": (400, 600), "sign_pos": (400, 435)},
    8:  {"center": (600, 685), "sign_pos": (600, 770)},
    9:  {"center": (685, 600), "sign_pos": (768, 600)},
    10: {"center": (610, 400), "sign_pos": (435, 400)},
    11: {"center": (685, 200), "sign_pos": (768, 200)},
    12: {"center": (600, 115), "sign_pos": (600, 32)},
}

# Grid mapping for South Indian fixed chart (12 signs clockwise around perimeter)
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


def generate_ashtakavarga_svg(
    chart: UnifiedChartData,
    av_report: AshtakavargaFullReport,
    chart_style: str = "north",
    sign_mode: str = "sanskrit",
    theme_mode: str = "light",
    width: int = 800,
    height: int = 800,
) -> str:
    """Generates an architectural SVG chart displaying the 337 Sarvashtakavarga bindus."""
    if chart_style == "south":
        return _render_south_sav_svg(chart, av_report, sign_mode, theme_mode, width, height)
    return _render_north_sav_svg(chart, av_report, sign_mode, theme_mode, width, height)


def _render_north_sav_svg(
    chart: UnifiedChartData,
    av_report: AshtakavargaFullReport,
    sign_mode: str,
    theme_mode: str,
    width: int,
    height: int,
) -> str:
    is_dark = (theme_mode == "dark")
    bg_color = "#121110" if is_dark else "#FAF8F5"
    frame_color = "#3E3731" if is_dark else "#D8D1C5"
    outer_border = "#B45309" if not is_dark else "#F59E0B"
    text_primary = "#F5F2EB" if is_dark else "#1C1917"
    text_muted = "#A8A29E" if is_dark else "#78716C"
    high_color = "#F59E0B" if is_dark else "#B45309"
    low_color = "#F87171" if is_dark else "#B91C1C"
    avg_color = text_primary
    pill_bg = "#2D2312" if is_dark else "#FEF3C7"
    pill_stroke = "#F59E0B" if is_dark else "#B45309"

    lagna_sign_id = chart.angles.ascendant_sign.id
    asc_deg_str = f"{chart.angles.ascendant_sign.dms.degrees}°{chart.angles.ascendant_sign.dms.minutes:02d}'"
    asc_s_name = ZODIAC_SIGNS[lagna_sign_id]["english_name"] if sign_mode == "english" else ZODIAC_SIGNS[lagna_sign_id]["sanskrit_name"]

    # Build sign bindu map from SAV report
    sign_bindu_map: Dict[int, int] = {sd.sign_id: sd.total_bindus for sd in av_report.sarvashtakavarga}

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="100%" height="100%" style="background-color: {bg_color}; border-radius: 14px; '
        f'box-shadow: 0 4px 20px rgba(0,0,0,0.06); font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">',

        # Background
        f'<rect width="{width}" height="{height}" fill="{bg_color}" />',

        # Subtle Decorative Canvas Border
        f'<rect x="8" y="8" width="784" height="784" fill="none" stroke="{frame_color}" stroke-width="1" />',
        f'<rect x="14" y="14" width="772" height="772" fill="none" stroke="{outer_border}" stroke-width="1.8" />',

        # Architectural North Diamond Geometry
        f'<rect x="20" y="20" width="760" height="760" fill="none" stroke="{frame_color}" stroke-width="1.8" />',
        f'<line x1="20" y1="20" x2="780" y2="780" stroke="{frame_color}" stroke-width="1.8" />',
        f'<line x1="780" y1="20" x2="20" y2="780" stroke="{frame_color}" stroke-width="1.8" />',
        f'<polygon points="400,20 780,400 400,780 20,400" fill="none" stroke="{frame_color}" stroke-width="1.8" />',

        # Subtle diamond crosshairs
        f'<line x1="400" y1="365" x2="400" y2="435" stroke="{frame_color}" stroke-width="1" stroke-dasharray="2,2" />',
        f'<line x1="365" y1="400" x2="435" y2="400" stroke="{frame_color}" stroke-width="1" stroke-dasharray="2,2" />',
    ]

    # Center Brand Emblem
    svg_parts.append(
        f'<g transform="translate(400, 400)">'
        f'<circle cx="0" cy="0" r="44" fill="{pill_bg}" stroke="{pill_stroke}" stroke-width="1.2" opacity="0.9" />'
        f'<text x="0" y="-12" fill="{outer_border}" font-family="Cinzel, serif" font-size="7" font-weight="900" text-anchor="middle" letter-spacing="0.5">SARVASHTAKAVARGA</text>'
        f'<text x="0" y="8" fill="{text_primary}" font-family="JetBrains Mono, monospace" font-size="16" font-weight="900" text-anchor="middle">337</text>'
        f'<text x="0" y="21" fill="{text_muted}" font-size="8" font-weight="700" text-anchor="middle" letter-spacing="0.5">BINDUS</text>'
        f'<text x="0" y="32" fill="{outer_border}" font-family="JetBrains Mono, monospace" font-size="7.5" font-weight="700" text-anchor="middle">{asc_s_name} {asc_deg_str}</text>'
        f'</g>'
    )

    # Render each of the 12 houses
    for h_num in range(1, 13):
        sign_id = ((lagna_sign_id - 1 + h_num - 1) % 12) + 1
        bindus = sign_bindu_map.get(sign_id, 0)
        s_name = ZODIAC_SIGNS[sign_id]["english_name"] if sign_mode == "english" else ZODIAC_SIGNS[sign_id]["sanskrit_name"]

        # Corner sign number & Lagna badge
        sx, sy = NORTH_HOUSE_CONFIG[h_num]["sign_pos"]
        if h_num == 1:
            svg_parts.append(
                f'<rect x="335" y="347" width="130" height="24" rx="5" fill="{pill_bg}" stroke="{pill_stroke}" stroke-width="1.2" />'
                f'<text x="400" y="363" fill="{outer_border}" font-family="Cinzel, serif" font-size="10" font-weight="900" text-anchor="middle" letter-spacing="0.4">LAGNA {sign_id} • {asc_deg_str}</text>'
            )
        else:
            svg_parts.append(
                f'<text x="{sx}" y="{sy}" fill="{text_muted}" font-family="JetBrains Mono, monospace" font-size="14" font-weight="700" text-anchor="middle" dominant-baseline="central">{sign_id}</text>'
            )

        # Center SAV Bindus & Sign Label
        cx, cy = NORTH_HOUSE_CONFIG[h_num]["center"]
        color = high_color if bindus >= 30 else (low_color if bindus < 26 else avg_color)

        # Badge pill behind high-bindu houses
        if bindus >= 30:
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy - 4}" r="26" fill="{pill_bg}" stroke="{pill_stroke}" stroke-width="1.2" />'
            )
        elif bindus < 26:
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy - 4}" r="24" fill="{low_color}" fill-opacity="0.12" stroke="{low_color}" stroke-width="1" />'
            )

        # Large Bindu typography
        svg_parts.append(
            f'<text x="{cx}" y="{cy + 2}" fill="{color}" font-family="JetBrains Mono, monospace" font-size="27" font-weight="900" text-anchor="middle" dominant-baseline="central">{bindus}</text>'
            f'<text x="{cx}" y="{cy + 28}" fill="{text_muted}" font-size="11" font-weight="600" text-anchor="middle">{s_name}</text>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def _render_south_sav_svg(
    chart: UnifiedChartData,
    av_report: AshtakavargaFullReport,
    sign_mode: str,
    theme_mode: str,
    width: int,
    height: int,
) -> str:
    cell_w = width / 4.0   # 200px
    cell_h = height / 4.0  # 200px
    is_dark = (theme_mode == "dark")
    bg_color = "#121110" if is_dark else "#FAF8F5"
    frame_color = "#3E3731" if is_dark else "#D8D1C5"
    outer_border = "#F59E0B" if is_dark else "#B45309"
    text_primary = "#F5F2EB" if is_dark else "#1C1917"
    text_muted = "#A8A29E" if is_dark else "#78716C"
    high_color = "#F59E0B" if is_dark else "#B45309"
    low_color = "#F87171" if is_dark else "#B91C1C"
    avg_color = text_primary
    pill_bg = "#2D2312" if is_dark else "#FEF3C7"
    pill_stroke = "#F59E0B" if is_dark else "#B45309"

    lagna_sign_id = chart.angles.ascendant_sign.id
    sign_bindu_map: Dict[int, int] = {sd.sign_id: sd.total_bindus for sd in av_report.sarvashtakavarga}

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="100%" height="100%" style="background-color: {bg_color}; border-radius: 14px; '
        f'box-shadow: 0 4px 20px rgba(0,0,0,0.06); font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">',

        # Background
        f'<rect width="{width}" height="{height}" fill="{bg_color}" />',

        # Outer border
        f'<rect x="6" y="6" width="788" height="788" fill="none" stroke="{outer_border}" stroke-width="2.5" />',
        f'<rect x="12" y="12" width="776" height="776" fill="none" stroke="{frame_color}" stroke-width="1" />',

        # 4x4 Grid Outer Lines
        f'<line x1="200" y1="12" x2="200" y2="788" stroke="{frame_color}" stroke-width="1.8" />',
        f'<line x1="400" y1="12" x2="400" y2="200" stroke="{frame_color}" stroke-width="1.8" />',
        f'<line x1="400" y1="600" x2="400" y2="788" stroke="{frame_color}" stroke-width="1.8" />',
        f'<line x1="600" y1="12" x2="600" y2="788" stroke="{frame_color}" stroke-width="1.8" />',

        f'<line x1="12" y1="200" x2="788" y2="200" stroke="{frame_color}" stroke-width="1.8" />',
        f'<line x1="12" y1="400" x2="200" y2="400" stroke="{frame_color}" stroke-width="1.8" />',
        f'<line x1="600" y1="400" x2="788" y2="400" stroke="{frame_color}" stroke-width="1.8" />',
        f'<line x1="12" y1="600" x2="788" y2="600" stroke="{frame_color}" stroke-width="1.8" />',
    ]

    # Center 2x2 HUD Summary Panel
    s_rep = av_report.summary
    asc_deg_str = f"{chart.angles.ascendant_sign.dms.degrees}°{chart.angles.ascendant_sign.dms.minutes:02d}'"
    asc_s_name = ZODIAC_SIGNS[lagna_sign_id]["english_name"] if sign_mode == "english" else ZODIAC_SIGNS[lagna_sign_id]["sanskrit_name"]

    svg_parts.append(
        f'<g transform="translate(215, 215)">'
        f'<rect width="370" height="370" rx="12" fill="{bg_color}" stroke="{pill_stroke}" stroke-width="1.2" />'
        f'<text x="185" y="42" fill="{outer_border}" font-family="Cinzel, serif" font-size="17" font-weight="900" text-anchor="middle" letter-spacing="1">SARVASHTAKAVARGA</text>'
        f'<text x="185" y="62" fill="{text_muted}" font-size="11" font-weight="600" text-anchor="middle" letter-spacing="0.5">BPHS 337 BINDUS</text>'
        f'<line x1="40" y1="76" x2="330" y2="76" stroke="{frame_color}" stroke-width="1" />'
        # Total Bindus
        f'<text x="185" y="128" fill="{text_primary}" font-family="JetBrains Mono, monospace" font-size="44" font-weight="900" text-anchor="middle">337</text>'
        f'<text x="185" y="152" fill="{text_muted}" font-size="12" font-weight="700" text-anchor="middle" letter-spacing="1">TOTAL BINDUS (SAV)</text>'
        f'<line x1="40" y1="168" x2="330" y2="168" stroke="{frame_color}" stroke-width="1" />'
        # Stats row
        f'<text x="65" y="200" fill="{text_muted}" font-size="11" font-weight="600">Ascendant:</text>'
        f'<text x="305" y="200" fill="{outer_border}" font-family="JetBrains Mono, monospace" font-size="12" font-weight="700" text-anchor="end">{asc_s_name} {chart.angles.ascendant_sign.dms.formatted}</text>'
        f'<text x="65" y="235" fill="{text_muted}" font-size="11" font-weight="600">Avg / Sign:</text>'
        f'<text x="305" y="235" fill="{text_primary}" font-family="JetBrains Mono, monospace" font-size="13" font-weight="700" text-anchor="end">{s_rep.average_bindus_per_sign}</text>'
        f'<text x="65" y="270" fill="{text_muted}" font-size="11" font-weight="600">Strongest Rashi:</text>'
        f'<text x="305" y="270" fill="{high_color}" font-family="JetBrains Mono, monospace" font-size="13" font-weight="700" text-anchor="end">{s_rep.strongest_sign} ({s_rep.strongest_sign_bindus}b)</text>'
        f'<text x="65" y="305" fill="{text_muted}" font-size="11" font-weight="600">Sensitive Rashi:</text>'
        f'<text x="305" y="305" fill="{low_color}" font-family="JetBrains Mono, monospace" font-size="13" font-weight="700" text-anchor="end">{s_rep.weakest_sign} ({s_rep.weakest_sign_bindus}b)</text>'
        f'<text x="65" y="340" fill="{text_muted}" font-size="11" font-weight="600">Benefic Signs (≥28):</text>'
        f'<text x="305" y="340" fill="{outer_border}" font-family="JetBrains Mono, monospace" font-size="13" font-weight="700" text-anchor="end">{s_rep.benefic_signs_count} / 12</text>'
        f'</g>'
    )

    # Render each perimeter sign cell
    for sign_id, info in SOUTH_SIGN_GRID.items():
        gx = info["col"] * cell_w
        gy = info["row"] * cell_h

        bindus = sign_bindu_map.get(sign_id, 0)
        h_num = ((sign_id - lagna_sign_id) % 12) + 1
        is_lagna = (sign_id == lagna_sign_id)
        s_name = info["en"] if sign_mode == "english" else info["name"]

        color = high_color if bindus >= 30 else (low_color if bindus < 26 else avg_color)

        # Header bar for the cell
        svg_parts.append(
            f'<text x="{gx + 12}" y="{gy + 28}" fill="{text_muted}" font-size="12" font-weight="700">{s_name}</text>'
        )

        if is_lagna:
            svg_parts.append(
                f'<rect x="{gx + cell_w - 92}" y="{gy + 14}" width="82" height="20" rx="4" fill="{pill_bg}" stroke="{pill_stroke}" stroke-width="1.2" />'
                f'<text x="{gx + cell_w - 51}" y="{gy + 28}" fill="{outer_border}" font-family="Cinzel, serif" font-size="9" font-weight="900" text-anchor="middle">LAGNA {asc_deg_str}</text>'
            )
        else:
            svg_parts.append(
                f'<text x="{gx + cell_w - 14}" y="{gy + 28}" fill="{text_muted}" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" text-anchor="end">H{h_num}</text>'
            )

        # Large Bindu typography in center
        cx = gx + (cell_w / 2.0)
        cy = gy + (cell_h / 2.0) + 10

        if bindus >= 30:
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy - 4}" r="28" fill="{pill_bg}" stroke="{pill_stroke}" stroke-width="1.2" />'
            )
        elif bindus < 26:
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy - 4}" r="26" fill="{low_color}" fill-opacity="0.12" stroke="{low_color}" stroke-width="1" />'
            )

        svg_parts.append(
            f'<text x="{cx}" y="{cy + 2}" fill="{color}" font-family="JetBrains Mono, monospace" font-size="30" font-weight="900" text-anchor="middle" dominant-baseline="central">{bindus}</text>'
            f'<text x="{cx}" y="{cy + 34}" fill="{text_muted}" font-size="10.5" font-weight="600" text-anchor="middle">BINDUS</text>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)
