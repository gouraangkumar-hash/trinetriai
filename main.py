"""TrinetriAI Vedic Studio - FastAPI High-Performance Backend.

Exposes REST endpoints for Swiss Ephemeris calculations, Parashari Vargas,
Vimshottari Dashas, KP System, and Jaimini Sutras, serving a lightweight
pure HTML/CSS/Vanilla JS frontend with zero Node.js dependencies.
"""

from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.astro_utils import decimal_to_dms
from core.constants import (
    AyanamshaType,
    HouseSystemType,
    NodeType,
    PlanetEnum,
    ZODIAC_SIGNS,
)
from core.ephemeris import EphemerisEngine
from core.geo import GeoResolver, to_utc_datetime
from engines.ashtakavarga import AshtakavargaEngine
from engines.jaimini import JaiminiEngine
from engines.kp import KPEngine
from engines.parashari import (
    VargaChartEngine,
    VargaType,
    VimshottariDashaEngine,
)
from engines.yogas import YogaDetectorEngine
from schemas.models import BirthInput, GeoLocationModel, UnifiedChartData
from visualizers.ashtakavarga_svg import generate_ashtakavarga_svg
from visualizers.north_indian_svg import generate_north_indian_svg
from visualizers.south_indian_svg import generate_south_indian_svg

app = FastAPI(
    title="TrinetriAI Vedic Studio API",
    description="High-precision DE431 astronomical and Vedic astrological calculation engine.",
    version="2.0.0",
)

# CORS middleware for local frontend development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Initialize computational engines
ephemeris_engine = EphemerisEngine()
geo_resolver = GeoResolver()


# =============================================================================
# Request / Response Schemas
# =============================================================================

class ChartCalculationRequest(BaseModel):
    year: int = Field(default=1995, ge=1, le=9999)
    month: int = Field(default=10, ge=1, le=12)
    day: int = Field(default=15, ge=1, le=31)
    hour: int = Field(default=14, ge=0, le=23)
    minute: int = Field(default=30, ge=0, le=59)
    second: float = Field(default=0.0, ge=0.0, lt=60.0)
    city: str = Field(default="Jaipur, India")
    latitude: float = Field(default=26.9124, ge=-90.0, le=90.0)
    longitude: float = Field(default=75.7873, ge=-180.0, le=180.0)
    timezone_str: str = Field(default="Asia/Kolkata")
    time_offset_seconds: int = Field(default=0)
    ayanamsha: str = Field(default="Lahiri")
    node_type: str = Field(default="True")
    chart_style: str = Field(default="north")  # "north" or "south"
    sign_mode: str = Field(default="sanskrit")  # "sanskrit" or "english"
    theme_mode: str = Field(default="light")  # "light" or "dark"
    selected_varga: str = Field(default="D1")


class VargaCalculationRequest(BaseModel):
    varga: str = Field(default="D9")
    chart_params: ChartCalculationRequest


# =============================================================================
# Core Calculation Pipeline Helpers
# =============================================================================

def _compute_chart_and_visuals(req: ChartCalculationRequest) -> dict[str, Any]:
    """Runs complete end-to-end calculations and serializes data for frontend consumption."""
    base_dt = datetime(
        year=req.year,
        month=req.month,
        day=req.day,
        hour=req.hour,
        minute=req.minute,
        second=int(req.second),
        microsecond=int((req.second % 1.0) * 1_000_000),
    )
    # Apply time rectification offset
    effective_dt = base_dt + timedelta(seconds=req.time_offset_seconds)

    ayan_enum = AyanamshaType(req.ayanamsha)
    node_enum = NodeType.TRUE if req.node_type == "True" else NodeType.MEAN

    birth_input = BirthInput(
        year=effective_dt.year,
        month=effective_dt.month,
        day=effective_dt.day,
        hour=effective_dt.hour,
        minute=effective_dt.minute,
        second=float(effective_dt.second),
        location=GeoLocationModel(
            latitude=req.latitude,
            longitude=req.longitude,
            city=req.city,
            timezone_str=req.timezone_str,
        ),
        ayanamsha=ayan_enum,
        node_type=node_enum,
        house_system=HouseSystemType.PLACIDUS,
    )

    chart = ephemeris_engine.calculate_chart(birth_input)

    # Varga Chart calculation
    varga_enum = VargaType(req.selected_varga)
    varga_chart = None
    if varga_enum != VargaType.D1:
        varga_chart = VargaChartEngine.generate_varga_chart(chart, varga_enum)

    # KP Sub-Lords and 4-Fold Significators
    kp_matrix = KPEngine.calculate_4fold_significators(chart)

    # Jaimini Sutras
    karakas_7 = JaiminiEngine.calculate_chara_karakas(chart, scheme=7)
    karakas_8 = JaiminiEngine.calculate_chara_karakas(chart, scheme=8)
    arudhas = JaiminiEngine.calculate_arudha_padas(chart)

    # Vimshottari Dashas
    moon_lon = chart.planets[PlanetEnum.MOON].longitude
    dashas = VimshottariDashaEngine.generate_dasha_tree(chart.utc_datetime, moon_lon)

    # Classical Yogas & Doshas Evaluation
    yogas_report = YogaDetectorEngine.evaluate(chart, sign_mode=req.sign_mode)

    # Classical Ashtakavarga Evaluation
    ashtakavarga_report = AshtakavargaEngine.evaluate(chart, sign_mode=req.sign_mode)

    # 1. Primary Angles Summary
    asc_sign = chart.angles.ascendant_sign
    asc_nak = chart.angles.ascendant_nakshatra
    mc_sign = chart.angles.mc_sign
    moon_pos = chart.planets[PlanetEnum.MOON]
    sun_pos = chart.planets[PlanetEnum.SUN]

    asc_sign_name = asc_sign.english_name if req.sign_mode == "english" else asc_sign.sanskrit_name
    mc_sign_name = mc_sign.english_name if req.sign_mode == "english" else mc_sign.sanskrit_name
    moon_sign_name = moon_pos.sign.english_name if req.sign_mode == "english" else moon_pos.sign.sanskrit_name
    sun_sign_name = sun_pos.sign.english_name if req.sign_mode == "english" else sun_pos.sign.sanskrit_name

    summary = {
        "ascendant": {
            "sign": asc_sign_name,
            "degree": asc_sign.dms.formatted,
            "nakshatra": f"{asc_nak.sanskrit_name} (Pada {asc_nak.pada})",
            "lord": asc_sign.lord.value,
        },
        "moon": {
            "sign": moon_sign_name,
            "degree": moon_pos.sign.dms.formatted,
            "nakshatra": f"{moon_pos.nakshatra.sanskrit_name} (Pada {moon_pos.nakshatra.pada})",
            "lord": moon_pos.sign.lord.value,
        },
        "sun": {
            "sign": sun_sign_name,
            "degree": sun_pos.sign.dms.formatted,
            "nakshatra": f"{sun_pos.nakshatra.sanskrit_name} (Pada {sun_pos.nakshatra.pada})",
            "lord": sun_pos.sign.lord.value,
        },
        "mc": {
            "sign": mc_sign_name,
            "degree": mc_sign.dms.formatted,
            "nakshatra": f"{chart.angles.mc_nakshatra.sanskrit_name} (Pada {chart.angles.mc_nakshatra.pada})",
            "lord": mc_sign.lord.value,
        },
        "julian_day_ut": round(chart.julian_day_ut, 6),
        "julian_day_et": round(chart.julian_day_et, 6),
        "ayanamsha_name": chart.ayanamsha_name.value,
        "ayanamsha_degree": chart.ayanamsha_dms.formatted,
        "effective_time": effective_dt.strftime("%H:%M:%S"),
        "effective_date": effective_dt.strftime("%Y-%m-%d"),
        "birth_profile": f"{req.city} • {effective_dt.strftime('%d %b %Y, %H:%M:%S')} • {req.ayanamsha}",
    }

    # 2. Planetary Positions Table (9 classical + nodes)
    planets_table = []
    planet_details = {}
    for p_name, p_pos in chart.planets.items():
        if p_name in (PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
            continue
        kp_res = KPEngine.resolve_kp_sub(p_pos.longitude)
        signifs = kp_matrix.planets_significations.get(p_name, {})
        s_name = p_pos.sign.english_name if req.sign_mode == "english" else p_pos.sign.sanskrit_name

        sig_a = ",".join(map(str, signifs.get("A", []))) or "-"
        sig_b = ",".join(map(str, signifs.get("B", []))) or "-"
        sig_c = ",".join(map(str, signifs.get("C", []))) or "-"
        sig_d = ",".join(map(str, signifs.get("D", []))) or "-"

        # Find Karaka role if assigned
        karaka_role = "None"
        for k_item in karakas_7.karakas:
            if k_item.planet == p_name:
                karaka_role = f"{k_item.role_code} ({k_item.role_name.value})"
                break

        # Vargottama dignity check (D1 Rashi sign == D9 Navamsha sign)
        d9_placement = VargaChartEngine.calculate_point_varga(
            longitude=p_pos.longitude,
            varga=VargaType.D9,
            planet=p_name,
            is_ascendant=False,
        )
        is_vargottama = bool(p_pos.sign.id == d9_placement.sign_id)
        d9_sign_name = ZODIAC_SIGNS[d9_placement.sign_id]["english_name"] if req.sign_mode == "english" else d9_placement.sign_name
        vargottama_status = f"Vargottama (D1 & D9 in {s_name})" if is_vargottama else f"No (D9 in {d9_sign_name})"

        p_dict = {
            "planet": p_name.value,
            "sign": s_name,
            "sign_id": p_pos.sign.id,
            "degree": p_pos.sign.dms.formatted,
            "absolute_longitude": round(p_pos.longitude, 4),
            "speed": f"{p_pos.speed:.4f}°/d",
            "nakshatra": f"{p_pos.nakshatra.sanskrit_name} (Pada {p_pos.nakshatra.pada})",
            "star_lord": kp_res.star_lord.value,
            "sub_lord": kp_res.sub_lord.value,
            "sub_sub_lord": kp_res.sub_sub_lord.value,
            "sig_a": sig_a,
            "sig_b": sig_b,
            "sig_c": sig_c,
            "sig_d": sig_d,
            "is_retro": p_pos.is_retrograde,
            "is_combust": p_pos.is_combust,
            "karaka_role": karaka_role,
            "is_vargottama": is_vargottama,
            "vargottama_status": vargottama_status,
            "d9_sign": d9_sign_name,
            "d9_degree": d9_placement.dms.formatted,
        }
        planets_table.append(p_dict)
        planet_details[p_name.value] = p_dict

    # 3. Varga Table Data for current selected varga
    varga_table = []
    if varga_chart is not None:
        asc_v = varga_chart.ascendant
        asc_v_sign = ZODIAC_SIGNS[asc_v.sign_id]["english_name"] if req.sign_mode == "english" else asc_v.sign_name
        varga_table.append({
            "planet": "Ascendant (Lagna)",
            "sign": asc_v_sign,
            "degree": asc_v.dms.formatted,
            "sign_lord": asc_v.sign_lord.value,
            "house": "House 1 (Lagna)",
            "is_retro": False,
            "is_combust": False,
        })
        asc_sign_id = asc_v.sign_id
        for p_enum, v_pos in varga_chart.planets.items():
            if p_enum in (PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
                continue
            s_name = ZODIAC_SIGNS[v_pos.sign_id]["english_name"] if req.sign_mode == "english" else v_pos.sign_name
            house_num = ((v_pos.sign_id - asc_sign_id) % 12) + 1
            is_retro = chart.planets[p_enum].is_retrograde if p_enum in chart.planets else False
            is_combust = chart.planets[p_enum].is_combust if p_enum in chart.planets else False
            varga_table.append({
                "planet": p_enum.value,
                "sign": s_name,
                "degree": v_pos.dms.formatted,
                "sign_lord": v_pos.sign_lord.value,
                "house": f"House {house_num}",
                "is_retro": is_retro,
                "is_combust": is_combust,
            })
    else:
        # D1 fallback
        asc_name = asc_sign.english_name if req.sign_mode == "english" else asc_sign.sanskrit_name
        varga_table.append({
            "planet": "Ascendant (Lagna)",
            "sign": asc_name,
            "degree": asc_sign.dms.formatted,
            "sign_lord": asc_sign.lord.value,
            "house": "House 1 (Lagna)",
            "is_retro": False,
            "is_combust": False,
        })
        asc_id = asc_sign.id
        for p_enum, p_pos in chart.planets.items():
            if p_enum in (PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
                continue
            s_name = p_pos.sign.english_name if req.sign_mode == "english" else p_pos.sign.sanskrit_name
            house_num = ((p_pos.sign.id - asc_id) % 12) + 1
            varga_table.append({
                "planet": p_enum.value,
                "sign": s_name,
                "degree": p_pos.sign.dms.formatted,
                "sign_lord": p_pos.sign.lord.value,
                "house": f"House {house_num}",
                "is_retro": p_pos.is_retrograde,
                "is_combust": p_pos.is_combust,
            })

    # 4. Placidus House Cusps & KP Table
    cusps_table = []
    for cusp in chart.placidus_houses:
        h_num = cusp.house_number
        kp_res = KPEngine.resolve_kp_sub(cusp.cusp_longitude)
        h_signifs = kp_matrix.houses.get(h_num)

        a_p = ",".join(p.value[:2] for p in h_signifs.level_a) if h_signifs and h_signifs.level_a else "-"
        b_p = ",".join(p.value[:2] for p in h_signifs.level_b) if h_signifs and h_signifs.level_b else "-"
        c_p = ",".join(p.value[:2] for p in h_signifs.level_c) if h_signifs and h_signifs.level_c else "-"
        d_p = ",".join(p.value[:2] for p in h_signifs.level_d) if h_signifs and h_signifs.level_d else "-"
        s_name = cusp.sign.english_name if req.sign_mode == "english" else cusp.sign.sanskrit_name

        cusps_table.append({
            "house": f"House {h_num:02d}",
            "sign": s_name,
            "degree": cusp.dms.formatted,
            "star_lord": kp_res.star_lord.value,
            "sub_lord": kp_res.sub_lord.value,
            "sub_sub_lord": kp_res.sub_sub_lord.value,
            "sig_a": a_p,
            "sig_b": b_p,
            "sig_c": c_p,
            "sig_d": d_p,
        })

    # 5. Jaimini Karakas (7 and 8 schemes) and Arudha Padas
    chara_karakas_7 = [
        {
            "code": item.role_code,
            "role": item.role_name.value,
            "planet": item.planet.value,
            "sign": ZODIAC_SIGNS[item.sign_id]["english_name"] if req.sign_mode == "english" else item.sign_name,
            "degree": item.dms.formatted,
        }
        for item in karakas_7.karakas
    ]

    chara_karakas_8 = [
        {
            "code": item.role_code,
            "role": item.role_name.value,
            "planet": item.planet.value,
            "sign": ZODIAC_SIGNS[item.sign_id]["english_name"] if req.sign_mode == "english" else item.sign_name,
            "degree": item.dms.formatted,
        }
        for item in karakas_8.karakas
    ]

    arudha_padas = [
        {
            "pada_name": item.pada_name,
            "house": f"House {item.final_house}",
            "sign": ZODIAC_SIGNS[item.sign_id]["english_name"] if req.sign_mode == "english" else item.sign_name,
            "exception": "10-House Shift" if item.is_exception_applied else "Standard",
            "is_special": item.house_number in (1, 12),
        }
        for item in arudhas.padas
    ]

    # 6. Vimshottari Dashas with 120-year tree
    now_utc = datetime.now(ZoneInfo("UTC"))
    active_dasha = VimshottariDashaEngine.get_current_dasha(dashas, now_utc)

    dasha_summary = {
        "md": active_dasha[0].lord.value if active_dasha else "-",
        "ad": active_dasha[1].lord.value if active_dasha else "-",
        "pd": active_dasha[2].lord.value if active_dasha else "-",
        "md_range": f"{active_dasha[0].start_date.strftime('%b %Y')} → {active_dasha[0].end_date.strftime('%b %Y')}" if active_dasha else "-",
        "ad_range": f"{active_dasha[1].start_date.strftime('%d %b %Y')} → {active_dasha[1].end_date.strftime('%d %b %Y')}" if active_dasha else "-",
        "pd_range": f"{active_dasha[2].start_date.strftime('%d %b %Y')} → {active_dasha[2].end_date.strftime('%d %b %Y')}" if active_dasha else "-",
    }

    mahadashas = []
    for md in dashas.mahadashas:
        is_active_md = md.start_date <= now_utc <= md.end_date
        md_status = "ACTIVE" if is_active_md else ("COMPLETED" if md.end_date < now_utc else "UPCOMING")
        md_duration_years = md.duration_days / 365.2425

        antardashas = []
        for ad in md.antardashas:
            is_active_ad = ad.start_date <= now_utc <= ad.end_date
            ad_status = "ACTIVE" if is_active_ad else ("COMPLETED" if ad.end_date < now_utc else "UPCOMING")
            ad_months = ad.duration_days / 30.4375
            ad_duration_str = f"{ad_months:.1f}m" if ad_months >= 1 else f"{int(ad.duration_days)}d"

            antardashas.append({
                "lord": ad.lord.value,
                "start": ad.start_date.strftime("%d %b %Y"),
                "end": ad.end_date.strftime("%d %b %Y"),
                "duration": ad_duration_str,
                "is_active": is_active_ad,
                "status": ad_status,
            })

        mahadashas.append({
            "lord": md.lord.value,
            "start": md.start_date.strftime("%d %b %Y"),
            "end": md.end_date.strftime("%d %b %Y"),
            "duration": f"{md_duration_years:.1f} Yrs",
            "is_active": is_active_md,
            "status": md_status,
            "antardashas": antardashas,
        })

    # 7. Render Chart SVG
    varga_title = f"{req.selected_varga} Chart"
    if req.chart_style == "north":
        svg_str = generate_north_indian_svg(
            chart=chart,
            varga_chart=varga_chart,
            title=varga_title,
            sign_mode=req.sign_mode,
            theme_mode=req.theme_mode,
        )
    else:
        svg_str = generate_south_indian_svg(
            chart=chart,
            varga_chart=varga_chart,
            title=varga_title,
            sign_mode=req.sign_mode,
            theme_mode=req.theme_mode,
        )

    # 8. Render Sarvashtakavarga (SAV) Visual Chart
    sav_chart_svg = generate_ashtakavarga_svg(
        chart=chart,
        av_report=ashtakavarga_report,
        chart_style=req.chart_style,
        sign_mode=req.sign_mode,
        theme_mode=req.theme_mode,
    )

    return {
        "status": "success",
        "summary": summary,
        "chart_svg": svg_str,
        "sav_chart_svg": sav_chart_svg,
        "selected_varga": req.selected_varga,
        "chart_style": req.chart_style,
        "sign_mode": req.sign_mode,
        "theme_mode": req.theme_mode,
        "planets_table": planets_table,
        "planet_details": planet_details,
        "varga_table": varga_table,
        "cusps_table": cusps_table,
        "chara_karakas_7": chara_karakas_7,
        "chara_karakas_8": chara_karakas_8,
        "arudha_padas": arudha_padas,
        "dasha_summary": dasha_summary,
        "mahadashas": mahadashas,
        "yogas_summary": yogas_report.summary.model_dump(),
        "yogas_list": [y.model_dump() for y in yogas_report.yogas],
        "ashtakavarga": ashtakavarga_report.model_dump(),
    }


# =============================================================================
# API Endpoints
# =============================================================================

@app.post("/api/calculate")
def calculate_chart(req: ChartCalculationRequest):
    """Calculates all chart features and returns formatted data with active SVG."""
    try:
        return _compute_chart_and_visuals(req)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/vargas")
def calculate_vargas(req: VargaCalculationRequest):
    """Calculates a specific harmonic Varga chart and returns updated SVG and table."""
    try:
        req.chart_params.selected_varga = req.varga
        data = _compute_chart_and_visuals(req.chart_params)
        return {
            "status": "success",
            "varga": req.varga,
            "chart_svg": data["chart_svg"],
            "varga_table": data["varga_table"],
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/geocode")
def geocode_city(query: str = Query(..., min_length=2)):
    """Geocodes a city or location query, returning coordinates and IANA timezone."""
    try:
        lat, lon, city, country = geo_resolver.geocode(query)
        tz = geo_resolver.get_timezone_for_coordinates(lat, lon)
        return {
            "status": "success",
            "city": city or query,
            "country": country or "",
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "timezone_str": tz,
            "display_name": f"{city or query}, {country}" if country else (city or query),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Location lookup failed: {str(exc)}")


# =============================================================================
# Static Files & SPA Frontend Serving
# =============================================================================

if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    """Serves the main application HTML page."""
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse(
            status_code=404,
            content={"message": "Frontend index.html not yet created."},
        )
    return FileResponse(str(index_file))
