"""Pydantic v2 Data Models for Astronomical and Vedic/KP/Jaimini Chart Calculations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from core.constants import (
    AyanamshaType,
    HouseSystemType,
    NodeType,
    PlanetEnum,
)


class DMSModel(BaseModel):
    """Degrees, Minutes, Seconds representation."""
    model_config = ConfigDict(frozen=True)

    degrees: int = Field(..., description="Integer degrees")
    minutes: int = Field(..., ge=0, lt=60, description="Integer arcminutes")
    seconds: float = Field(..., ge=0.0, lt=60.0, description="Float arcseconds")
    formatted: str = Field(..., description="Formatted string e.g. 124° 34' 04.08\"")


class SignPlacementModel(BaseModel):
    """Zodiac Sign placement details."""
    model_config = ConfigDict(frozen=True)

    id: int = Field(..., ge=1, le=12, description="Sign index 1 to 12")
    sanskrit_name: str = Field(..., description="Sanskrit name of Rashi (e.g. Mesha)")
    english_name: str = Field(..., description="Western sign name (e.g. Aries)")
    lord: PlanetEnum = Field(..., description="Ruling planet of the sign")
    element: str = Field(..., description="Element: Fire, Earth, Air, Water")
    modality: str = Field(..., description="Modality: Movable, Fixed, Dual")
    intra_sign_degree: float = Field(..., ge=0.0, lt=30.0, description="Position within sign (0° to 30°)")
    dms: DMSModel = Field(..., description="DMS formatting of intra-sign degree")


class NakshatraPlacementModel(BaseModel):
    """Nakshatra and Pada placement details."""
    model_config = ConfigDict(frozen=True)

    id: int = Field(..., ge=1, le=27, description="Nakshatra index 1 to 27")
    sanskrit_name: str = Field(..., description="Sanskrit name of Nakshatra (e.g. Ashwini)")
    lord: PlanetEnum = Field(..., description="Vimshottari Dasha lord")
    dasha_years: int = Field(..., gt=0, description="Total Vimshottari Mahadasha years for this lord")
    pada: int = Field(..., ge=1, le=4, description="Pada / quarter (1 to 4)")
    elapsed_degrees: float = Field(..., ge=0.0, description="Elapsed degrees inside this nakshatra")
    elapsed_fraction: float = Field(..., ge=0.0, le=1.0, description="Elapsed fractional progress (0.0 to 1.0)")
    pada_start_deg: float = Field(..., ge=0.0, le=360.0, description="Absolute starting degree of the pada")
    pada_end_deg: float = Field(..., ge=0.0, le=360.0, description="Absolute ending degree of the pada")


class GeoLocationModel(BaseModel):
    """Geographical location details."""
    model_config = ConfigDict(frozen=True)

    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (+ North, - South)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (+ East, - West)")
    altitude: float = Field(default=0.0, description="Altitude above sea level in meters")
    city: Optional[str] = Field(default=None, description="City or locality name")
    country: Optional[str] = Field(default=None, description="Country name")
    timezone_str: str = Field(..., description="IANA timezone name, e.g. 'Asia/Kolkata'")


class BirthInput(BaseModel):
    """Raw birth inputs for chart generation."""
    model_config = ConfigDict(frozen=True)

    year: int = Field(..., ge=1, le=9999, description="Birth year (e.g. 1995)")
    month: int = Field(..., ge=1, le=12, description="Birth month (1 to 12)")
    day: int = Field(..., ge=1, le=31, description="Birth day (1 to 31)")
    hour: int = Field(..., ge=0, le=23, description="Birth hour (0 to 23)")
    minute: int = Field(..., ge=0, le=59, description="Birth minute (0 to 59)")
    second: float = Field(default=0.0, ge=0.0, lt=60.0, description="Birth second (0 to 59.999)")
    location: GeoLocationModel = Field(..., description="Geographical birth location")
    ayanamsha: AyanamshaType = Field(default=AyanamshaType.LAHIRI, description="Ayanamsha system")
    node_type: NodeType = Field(default=NodeType.TRUE, description="Lunar node calculation mode (True or Mean)")
    house_system: HouseSystemType = Field(default=HouseSystemType.PLACIDUS, description="Primary house system")


class PlanetPositionModel(BaseModel):
    """Calculated planetary position and astronomical properties."""
    model_config = ConfigDict(frozen=True)

    name: PlanetEnum = Field(..., description="Planet name")
    planet_id: int = Field(..., description="Swiss Ephemeris internal ID or derived code")
    longitude: float = Field(..., ge=0.0, lt=360.0, description="Absolute sidereal longitude (0° to 360°)")
    latitude: float = Field(..., description="Ecliptic latitude in decimal degrees")
    speed: float = Field(..., description="Daily longitudinal motion in degrees/day")
    distance: float = Field(..., ge=0.0, description="Distance from Earth in AU")
    sign: SignPlacementModel = Field(..., description="Zodiac sign details")
    nakshatra: NakshatraPlacementModel = Field(..., description="Nakshatra details")
    is_retrograde: bool = Field(..., description="True if planet is in retrograde motion (speed < 0)")
    is_combust: bool = Field(..., description="True if planet is combust (Astangata) relative to Sun")
    dms: DMSModel = Field(..., description="DMS formatting of absolute longitude")


class HouseCuspModel(BaseModel):
    """House cusp calculation model."""
    model_config = ConfigDict(frozen=True)

    house_number: int = Field(..., ge=1, le=12, description="House number 1 to 12")
    cusp_longitude: float = Field(..., ge=0.0, lt=360.0, description="Sidereal cusp longitude (0° to 360°)")
    sign: SignPlacementModel = Field(..., description="Zodiac sign at the cusp")
    nakshatra: NakshatraPlacementModel = Field(..., description="Nakshatra at the cusp")
    dms: DMSModel = Field(..., description="DMS formatting of cusp longitude")


class AscendantMCModel(BaseModel):
    """Ascendant (Lagna) and Midheaven (MC) properties."""
    model_config = ConfigDict(frozen=True)

    ascendant: float = Field(..., ge=0.0, lt=360.0, description="Sidereal Ascendant / Lagna longitude")
    ascendant_sign: SignPlacementModel = Field(..., description="Ascendant sign")
    ascendant_nakshatra: NakshatraPlacementModel = Field(..., description="Ascendant nakshatra")
    ascendant_dms: DMSModel = Field(..., description="Ascendant DMS")
    mc: float = Field(..., ge=0.0, lt=360.0, description="Sidereal Midheaven (MC) longitude")
    mc_sign: SignPlacementModel = Field(..., description="MC sign")
    mc_nakshatra: NakshatraPlacementModel = Field(..., description="MC nakshatra")
    mc_dms: DMSModel = Field(..., description="MC DMS")
    armc: float = Field(..., description="Sidereal Time / Right Ascension of Midheaven in degrees")
    vertex: float = Field(..., description="Sidereal Vertex longitude")


class UnifiedChartData(BaseModel):
    """Complete unified astronomical and sidereal chart representation."""
    model_config = ConfigDict(frozen=True)

    input_data: BirthInput = Field(..., description="Original input metadata")
    utc_datetime: datetime = Field(..., description="UTC normalized datetime of birth")
    julian_day_ut: float = Field(..., description="Julian Day Universal Time (UT)")
    julian_day_et: float = Field(..., description="Julian Day Ephemeris Time (ET)")
    ayanamsha_name: AyanamshaType = Field(..., description="Ayanamsha system name")
    ayanamsha_value: float = Field(..., description="Calculated Ayanamsha value in decimal degrees")
    ayanamsha_dms: DMSModel = Field(..., description="Ayanamsha in DMS")
    angles: AscendantMCModel = Field(..., description="Ascendant and MC angles")
    planets: dict[PlanetEnum, PlanetPositionModel] = Field(..., description="Computed 9 Grahas positions")
    placidus_houses: list[HouseCuspModel] = Field(..., description="12 Placidus house cusps")
    whole_sign_houses: list[HouseCuspModel] = Field(..., description="12 Whole Sign house cusps")
    house_system_used: HouseSystemType = Field(..., description="Primary house system calculated")
    is_polar_fallback: bool = Field(default=False, description="True if polar fallback house system was applied")
