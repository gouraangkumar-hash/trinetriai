"""State management and computational pipeline orchestrator for the UI Dashboard."""

from datetime import datetime
from typing import Literal, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from core.constants import AyanamshaType, HouseSystemType, NodeType, PlanetEnum
from core.ephemeris import EphemerisEngine
from core.geo import GeoResolver
from engines.jaimini import (
    ArudhaPadasResult,
    CharaKarakaSchemeResult,
    JaiminiEngine,
    RashiDrishtiAspects,
)
from engines.kp import KP4FoldSignificatorsMatrix, KPEngine, KPSubDivisionResult
from engines.parashari import (
    VargaChart,
    VargaChartEngine,
    VargaType,
    VimshottariDashaEngine,
    VimshottariDashaTree,
)
from schemas.models import BirthInput, GeoLocationModel, UnifiedChartData
from visualizers.north_indian_svg import generate_north_indian_svg
from visualizers.south_indian_svg import generate_south_indian_svg


class DashboardState(BaseModel):
    """Complete computed state for the dashboard UI."""

    # Inputs
    city_query: str = "Jaipur, India"
    birth_date_str: str = "1995-10-15"
    birth_time_str: str = "14:30:00"
    ayanamsha: AyanamshaType = AyanamshaType.LAHIRI
    chart_style: Literal["north", "south"] = "north"
    selected_varga: VargaType = VargaType.D1
    node_type: NodeType = NodeType.TRUE

    # Resolved Geo
    latitude: float = 26.9124
    longitude: float = 75.7873
    timezone_str: str = "Asia/Kolkata"
    resolved_location_label: str = "Jaipur, Rajasthan, India"

    # Computed Engine Results
    chart_data: Optional[UnifiedChartData] = None
    varga_charts: dict[VargaType, VargaChart] = Field(default_factory=dict)
    dasha_tree: Optional[VimshottariDashaTree] = None
    active_dasha_triplet: Optional[tuple] = None
    kp_matrix: Optional[KP4FoldSignificatorsMatrix] = None
    kp_planet_subs: dict[PlanetEnum, KPSubDivisionResult] = Field(default_factory=dict)
    kp_cusp_subs: dict[int, KPSubDivisionResult] = Field(default_factory=dict)
    jaimini_7_karakas: Optional[CharaKarakaSchemeResult] = None
    jaimini_8_karakas: Optional[CharaKarakaSchemeResult] = None
    arudha_padas: Optional[ArudhaPadasResult] = None
    rashi_drishti: Optional[RashiDrishtiAspects] = None

    # Rendered SVGs
    north_svg: str = ""
    south_svg: str = ""
    active_svg: str = ""
    error_message: Optional[str] = None


class EngineOrchestrator:
    """Singleton engine orchestrator for computing dashboard state."""

    def __init__(self) -> None:
        self.ephemeris = EphemerisEngine()
        self.geo = GeoResolver()

    def run_pipeline(self, state: DashboardState) -> DashboardState:
        """Executes full multi-system pipeline (Astronomical -> Parashari -> KP -> Jaimini -> Visualizers)."""
        try:
            # 1. Parse Date and Time
            dt_str = f"{state.birth_date_str.strip()} {state.birth_time_str.strip()}"
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

            # 2. Geocode if city changed
            # (Use cached coords if present or resolve query)
            lat = state.latitude
            lon = state.longitude
            tz_str = state.timezone_str

            # 3. Create BirthInput
            birth_input = BirthInput(
                year=dt.year,
                month=dt.month,
                day=dt.day,
                hour=dt.hour,
                minute=dt.minute,
                second=float(dt.second),
                location=GeoLocationModel(
                    latitude=lat,
                    longitude=lon,
                    city=state.city_query,
                    timezone_str=tz_str,
                ),
                ayanamsha=state.ayanamsha,
                node_type=state.node_type,
                house_system=HouseSystemType.PLACIDUS,
            )

            # 4. Astronomical & Core Pipeline (Phase 1)
            chart = self.ephemeris.calculate_chart(birth_input)
            state.chart_data = chart

            # 5. Parashari Divisional Charts (Phase 2)
            vargas: dict[VargaType, VargaChart] = {}
            for vt in [VargaType.D1, VargaType.D2, VargaType.D3, VargaType.D7, VargaType.D9, VargaType.D10, VargaType.D12, VargaType.D30, VargaType.D60]:
                vargas[vt] = VargaChartEngine.generate_varga_chart(chart, vt)
            state.varga_charts = vargas

            # 6. Vimshottari Dasha Engine (Phase 2)
            moon_lon = chart.planets[PlanetEnum.MOON].longitude
            dasha_tree = VimshottariDashaEngine.generate_dasha_tree(chart.utc_datetime, moon_lon)
            state.dasha_tree = dasha_tree

            now_utc = datetime.now(ZoneInfo("UTC"))
            state.active_dasha_triplet = VimshottariDashaEngine.get_current_dasha(dasha_tree, now_utc)

            # 7. KP System Engine (Phase 2)
            kp_matrix = KPEngine.calculate_4fold_significators(chart)
            state.kp_matrix = kp_matrix

            planet_subs: dict[PlanetEnum, KPSubDivisionResult] = {}
            for p_name, p_pos in chart.planets.items():
                planet_subs[p_name] = KPEngine.resolve_kp_sub(p_pos.longitude)
            state.kp_planet_subs = planet_subs

            cusp_subs: dict[int, KPSubDivisionResult] = {}
            for cusp in chart.placidus_houses:
                cusp_subs[cusp.house_number] = KPEngine.resolve_kp_sub(cusp.cusp_longitude)
            state.kp_cusp_subs = cusp_subs

            # 8. Jaimini Engine (Phase 2)
            state.jaimini_7_karakas = JaiminiEngine.calculate_chara_karakas(chart, scheme=7)
            state.jaimini_8_karakas = JaiminiEngine.calculate_chara_karakas(chart, scheme=8)
            state.arudha_padas = JaiminiEngine.calculate_arudha_padas(chart)
            state.rashi_drishti = JaiminiEngine.calculate_rashi_drishti(chart)

            # 9. Render Visualizer SVGs (Phase 3)
            active_varga_chart = None if state.selected_varga == VargaType.D1 else vargas.get(state.selected_varga)
            varga_title = f"{state.selected_varga.value} Chart"

            state.north_svg = generate_north_indian_svg(
                chart=chart,
                varga_chart=active_varga_chart,
                title=varga_title,
            )
            state.south_svg = generate_south_indian_svg(
                chart=chart,
                varga_chart=active_varga_chart,
                title=varga_title,
            )

            state.active_svg = state.north_svg if state.chart_style == "north" else state.south_svg
            state.error_message = None

        except Exception as exc:
            state.error_message = str(exc)

        return state
