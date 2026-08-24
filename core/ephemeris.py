"""Swiss Ephemeris High-Precision Astronomical Computational Engine.

Provides:
- Julian Day (UT & ET) computation
- Dynamic Ayanamsha configuration (Lahiri, Krishnamurti/KP New, Raman, Yukteshwar, etc.)
- 9 Grahas computation with sidereal positions, speeds, retrogrades, and combustion checks
- Ketu derived exactly at 180° opposition to Rahu
- Placidus and Whole Sign house cusp calculations with polar latitude fallback
- End-to-end unified chart generation
"""

from datetime import datetime
import os
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import swisseph as swe

from core.astro_utils import (
    angular_distance,
    decimal_to_dms,
    get_nakshatra_placement,
    get_sign_placement,
    normalize_degrees,
)
from core.constants import (
    COMBUSTION_THRESHOLDS,
    SWE_FLG_SIDEREAL,
    SWE_FLG_SPEED,
    SWE_FLG_SWIEPH,
    SWE_HOUSES_PLACIDUS,
    SWE_HOUSES_PORPHYRY,
    SWE_HOUSES_WHOLE_SIGN,
    SWE_JUPITER,
    SWE_MARS,
    SWE_MEAN_NODE,
    SWE_MERCURY,
    SWE_MOON,
    SWE_NEPTUNE,
    SWE_PLUTO,
    SWE_SATURN,
    SWE_SIDM_FAGAN_BRADLEY,
    SWE_SIDM_KRISHNAMURTI,
    SWE_SIDM_LAHIRI,
    SWE_SIDM_RAMAN,
    SWE_SIDM_YUKTESHWAR,
    SWE_SUN,
    SWE_TRUE_NODE,
    SWE_URANUS,
    SWE_VENUS,
    AyanamshaType,
    HouseSystemType,
    NodeType,
    PlanetEnum,
)
from core.geo import to_utc_datetime
from schemas.models import (
    AscendantMCModel,
    BirthInput,
    DMSModel,
    HouseCuspModel,
    NakshatraPlacementModel,
    PlanetPositionModel,
    SignPlacementModel,
    UnifiedChartData,
)


class EphemerisEngine:
    """Core Swiss Ephemeris wrapper and astronomical calculation pipeline."""

    AYANAMSHA_MAP = {
        AyanamshaType.LAHIRI: SWE_SIDM_LAHIRI,
        AyanamshaType.KRISHNAMURTI: SWE_SIDM_KRISHNAMURTI,
        AyanamshaType.RAMAN: SWE_SIDM_RAMAN,
        AyanamshaType.YUKTESHWAR: SWE_SIDM_YUKTESHWAR,
        AyanamshaType.FAGAN_BRADLEY: SWE_SIDM_FAGAN_BRADLEY,
    }

    CLASSICAL_PLANETS = [
        (PlanetEnum.SUN, SWE_SUN),
        (PlanetEnum.MOON, SWE_MOON),
        (PlanetEnum.MARS, SWE_MARS),
        (PlanetEnum.MERCURY, SWE_MERCURY),
        (PlanetEnum.JUPITER, SWE_JUPITER),
        (PlanetEnum.VENUS, SWE_VENUS),
        (PlanetEnum.SATURN, SWE_SATURN),
        (PlanetEnum.URANUS, SWE_URANUS),
        (PlanetEnum.NEPTUNE, SWE_NEPTUNE),
        (PlanetEnum.PLUTO, SWE_PLUTO),
    ]

    def __init__(self, ephe_path: Optional[str] = None) -> None:
        """Initializes Swiss Ephemeris with local ephemeris path if available."""
        if ephe_path and Path(ephe_path).is_dir():
            swe.set_ephe_path(str(Path(ephe_path).resolve()))
        else:
            default_ephe = Path(__file__).parent.parent / "ephe"
            if default_ephe.is_dir():
                swe.set_ephe_path(str(default_ephe.resolve()))
            else:
                # Built-in Moshier analytical ephemeris mode
                swe.set_ephe_path("")

    def calculate_julian_day(self, dt_utc: datetime) -> tuple[float, float]:
        """Calculates Julian Day for Universal Time (UT) and Ephemeris Time (ET).

        Args:
            dt_utc: Timezone-aware UTC datetime.

        Returns:
            Tuple of (julian_day_ut, julian_day_et).
        """
        hour_decimal = (
            dt_utc.hour
            + (dt_utc.minute / 60.0)
            + (dt_utc.second / 3600.0)
            + (dt_utc.microsecond / 3_600_000_000.0)
        )
        jd_ut = swe.julday(
            dt_utc.year,
            dt_utc.month,
            dt_utc.day,
            hour_decimal,
            swe.GREG_CAL,
        )
        delta_t = swe.deltat(jd_ut)  # delta T in days
        jd_et = jd_ut + delta_t
        return jd_ut, jd_et

    def configure_ayanamsha(self, ayanamsha: AyanamshaType) -> None:
        """Configures the sidereal mode in Swiss Ephemeris."""
        if ayanamsha == AyanamshaType.TROPICAL:
            return
        sidm_code = self.AYANAMSHA_MAP.get(ayanamsha, SWE_SIDM_LAHIRI)
        swe.set_sid_mode(sidm_code, 0, 0)

    def get_ayanamsha_value(self, jd_ut: float, ayanamsha: AyanamshaType) -> float:
        """Computes the Ayanamsha value for a given Julian Day UT in decimal degrees."""
        if ayanamsha == AyanamshaType.TROPICAL:
            return 0.0
        self.configure_ayanamsha(ayanamsha)
        return float(swe.get_ayanamsa_ut(jd_ut))

    def _build_dms_model(self, degrees: float) -> DMSModel:
        deg, m, s, formatted = decimal_to_dms(degrees)
        return DMSModel(
            degrees=deg,
            minutes=m,
            seconds=s,
            formatted=formatted,
        )

    def _build_sign_model(self, longitude: float) -> SignPlacementModel:
        raw = get_sign_placement(longitude)
        dms_dict = raw["dms"]
        return SignPlacementModel(
            id=raw["id"],
            sanskrit_name=raw["sanskrit_name"],
            english_name=raw["english_name"],
            lord=raw["lord"],
            element=raw["element"],
            modality=raw["modality"],
            intra_sign_degree=raw["intra_sign_degree"],
            dms=DMSModel(**dms_dict),
        )

    def _build_nakshatra_model(self, longitude: float) -> NakshatraPlacementModel:
        raw = get_nakshatra_placement(longitude)
        return NakshatraPlacementModel(
            id=raw["id"],
            sanskrit_name=raw["sanskrit_name"],
            lord=raw["lord"],
            dasha_years=raw["dasha_years"],
            pada=raw["pada"],
            elapsed_degrees=raw["elapsed_degrees"],
            elapsed_fraction=raw["elapsed_fraction"],
            pada_start_deg=raw["pada_start_deg"],
            pada_end_deg=raw["pada_end_deg"],
        )

    def is_combust(
        self,
        planet: PlanetEnum,
        planet_longitude: float,
        sun_longitude: float,
        is_retrograde: bool,
    ) -> bool:
        """Determines if a planet is in combustion (Astangata) relative to Sun."""
        if planet in (PlanetEnum.SUN, PlanetEnum.RAHU, PlanetEnum.KETU, PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
            return False

        dist = angular_distance(planet_longitude, sun_longitude)
        threshold_entry = COMBUSTION_THRESHOLDS.get(planet)

        if threshold_entry is None:
            return False

        if isinstance(threshold_entry, dict):
            threshold = threshold_entry["retrograde"] if is_retrograde else threshold_entry["direct"]
        else:
            threshold = float(threshold_entry)

        return dist <= threshold

    def calculate_planets(
        self,
        jd_ut: float,
        ayanamsha: AyanamshaType = AyanamshaType.LAHIRI,
        node_type: NodeType = NodeType.TRUE,
    ) -> dict[PlanetEnum, PlanetPositionModel]:
        """Calculates 9 Grahas (Sun through Ketu) and outer planets."""
        self.configure_ayanamsha(ayanamsha)

        flags = SWE_FLG_SWIEPH | SWE_FLG_SPEED
        if ayanamsha != AyanamshaType.TROPICAL:
            flags |= SWE_FLG_SIDEREAL

        # 1. Compute Sun first for combustion evaluations
        sun_res, _ = swe.calc_ut(jd_ut, SWE_SUN, flags)
        sun_lon = normalize_degrees(sun_res[0])
        sun_speed = sun_res[3]

        planets_data: dict[PlanetEnum, PlanetPositionModel] = {}

        # 2. Compute 7 Classical Planets + Outers
        for p_enum, p_id in self.CLASSICAL_PLANETS:
            res, _ = swe.calc_ut(jd_ut, p_id, flags)
            lon = normalize_degrees(res[0])
            lat = res[1]
            dist = res[2]
            speed = res[3]
            is_retro = speed < 0.0

            combust = self.is_combust(
                planet=p_enum,
                planet_longitude=lon,
                sun_longitude=sun_lon,
                is_retrograde=is_retro,
            )

            planets_data[p_enum] = PlanetPositionModel(
                name=p_enum,
                planet_id=p_id,
                longitude=lon,
                latitude=lat,
                speed=speed,
                distance=dist,
                sign=self._build_sign_model(lon),
                nakshatra=self._build_nakshatra_model(lon),
                is_retrograde=is_retro,
                is_combust=combust,
                dms=self._build_dms_model(lon),
            )

        # 3. Compute Lunar Node (Rahu)
        rahu_swe_id = SWE_TRUE_NODE if node_type == NodeType.TRUE else SWE_MEAN_NODE
        rahu_res, _ = swe.calc_ut(jd_ut, rahu_swe_id, flags)
        rahu_lon = normalize_degrees(rahu_res[0])
        rahu_lat = rahu_res[1]
        rahu_dist = rahu_res[2]
        rahu_speed = rahu_res[3]
        rahu_retro = rahu_speed < 0.0

        planets_data[PlanetEnum.RAHU] = PlanetPositionModel(
            name=PlanetEnum.RAHU,
            planet_id=rahu_swe_id,
            longitude=rahu_lon,
            latitude=rahu_lat,
            speed=rahu_speed,
            distance=rahu_dist,
            sign=self._build_sign_model(rahu_lon),
            nakshatra=self._build_nakshatra_model(rahu_lon),
            is_retrograde=rahu_retro,
            is_combust=False,
            dms=self._build_dms_model(rahu_lon),
        )

        # 4. Derive Ketu strictly at 180° opposition to Rahu
        ketu_lon = normalize_degrees(rahu_lon + 180.0)
        ketu_lat = -rahu_lat
        ketu_dist = rahu_dist
        ketu_speed = rahu_speed
        ketu_retro = rahu_retro

        planets_data[PlanetEnum.KETU] = PlanetPositionModel(
            name=PlanetEnum.KETU,
            planet_id=-1,  # Derived
            longitude=ketu_lon,
            latitude=ketu_lat,
            speed=ketu_speed,
            distance=ketu_dist,
            sign=self._build_sign_model(ketu_lon),
            nakshatra=self._build_nakshatra_model(ketu_lon),
            is_retrograde=ketu_retro,
            is_combust=False,
            dms=self._build_dms_model(ketu_lon),
        )

        return planets_data

    def calculate_houses_and_angles(
        self,
        jd_ut: float,
        latitude: float,
        longitude: float,
        ayanamsha: AyanamshaType = AyanamshaType.LAHIRI,
        hsys: HouseSystemType = HouseSystemType.PLACIDUS,
    ) -> tuple[AscendantMCModel, list[HouseCuspModel], list[HouseCuspModel], HouseSystemType, bool]:
        """Calculates Ascendant, MC, Placidus house cusps, and Whole Sign house cusps."""
        self.configure_ayanamsha(ayanamsha)
        flags = SWE_FLG_SIDEREAL if ayanamsha != AyanamshaType.TROPICAL else 0

        is_polar_fallback = False
        hsys_used = hsys

        # Primary Placidus / requested house calculation
        try:
            cusps, ascmc = swe.houses_ex(
                jd_ut,
                latitude,
                longitude,
                SWE_HOUSES_PLACIDUS,
                flags,
            )
        except Exception:
            # Polar latitude fallback to Porphyry
            cusps, ascmc = swe.houses_ex(
                jd_ut,
                latitude,
                longitude,
                SWE_HOUSES_PORPHYRY,
                flags,
            )
            is_polar_fallback = True
            hsys_used = HouseSystemType.PORPHYRY

        asc_lon = normalize_degrees(ascmc[0])
        mc_lon = normalize_degrees(ascmc[1])
        armc = ascmc[2]
        vertex = normalize_degrees(ascmc[3])

        angles = AscendantMCModel(
            ascendant=asc_lon,
            ascendant_sign=self._build_sign_model(asc_lon),
            ascendant_nakshatra=self._build_nakshatra_model(asc_lon),
            ascendant_dms=self._build_dms_model(asc_lon),
            mc=mc_lon,
            mc_sign=self._build_sign_model(mc_lon),
            mc_nakshatra=self._build_nakshatra_model(mc_lon),
            mc_dms=self._build_dms_model(mc_lon),
            armc=armc,
            vertex=vertex,
        )

        # 12 Placidus / Cuspal houses
        placidus_houses: list[HouseCuspModel] = []
        for i in range(1, 13):
            cusp_lon = normalize_degrees(cusps[i - 1])
            placidus_houses.append(
                HouseCuspModel(
                    house_number=i,
                    cusp_longitude=cusp_lon,
                    sign=self._build_sign_model(cusp_lon),
                    nakshatra=self._build_nakshatra_model(cusp_lon),
                    dms=self._build_dms_model(cusp_lon),
                )
            )

        # 12 Whole Sign Houses (Rashi Bhava)
        # In Vedic Whole Sign, 1st House starts at 0° of the Ascendant sign
        asc_sign_index = int(asc_lon // 30.0)  # 0 to 11
        whole_sign_houses: list[HouseCuspModel] = []
        for h in range(1, 13):
            target_sign_idx = (asc_sign_index + (h - 1)) % 12
            cusp_lon = target_sign_idx * 30.0
            whole_sign_houses.append(
                HouseCuspModel(
                    house_number=h,
                    cusp_longitude=cusp_lon,
                    sign=self._build_sign_model(cusp_lon),
                    nakshatra=self._build_nakshatra_model(cusp_lon),
                    dms=self._build_dms_model(cusp_lon),
                )
            )

        return angles, placidus_houses, whole_sign_houses, hsys_used, is_polar_fallback

    def calculate_chart(self, birth_input: BirthInput) -> UnifiedChartData:
        """Executes full astronomical calculation pipeline for a given birth input.

        Args:
            birth_input: Validated BirthInput Pydantic model.

        Returns:
            UnifiedChartData model with all planetary, angular, and cuspal data.
        """
        # 1. Resolve local datetime to UTC
        local_dt = datetime(
            year=birth_input.year,
            month=birth_input.month,
            day=birth_input.day,
            hour=birth_input.hour,
            minute=birth_input.minute,
            second=int(birth_input.second),
            microsecond=int((birth_input.second % 1.0) * 1_000_000),
        )
        utc_dt = to_utc_datetime(local_dt, birth_input.location.timezone_str)

        # 2. Julian Day computation
        jd_ut, jd_et = self.calculate_julian_day(utc_dt)

        # 3. Ayanamsha calculation
        ayan_val = self.get_ayanamsha_value(jd_ut, birth_input.ayanamsha)
        ayan_dms = self._build_dms_model(ayan_val)

        # 4. Planets calculation
        planets = self.calculate_planets(
            jd_ut=jd_ut,
            ayanamsha=birth_input.ayanamsha,
            node_type=birth_input.node_type,
        )

        # 5. Houses and Angles calculation
        angles, placidus_houses, whole_sign_houses, hsys_used, is_polar = self.calculate_houses_and_angles(
            jd_ut=jd_ut,
            latitude=birth_input.location.latitude,
            longitude=birth_input.location.longitude,
            ayanamsha=birth_input.ayanamsha,
            hsys=birth_input.house_system,
        )

        return UnifiedChartData(
            input_data=birth_input,
            utc_datetime=utc_dt,
            julian_day_ut=jd_ut,
            julian_day_et=jd_et,
            ayanamsha_name=birth_input.ayanamsha,
            ayanamsha_value=ayan_val,
            ayanamsha_dms=ayan_dms,
            angles=angles,
            planets=planets,
            placidus_houses=placidus_houses,
            whole_sign_houses=whole_sign_houses,
            house_system_used=hsys_used,
            is_polar_fallback=is_polar,
        )
