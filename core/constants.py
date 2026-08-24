"""Astronomical and Astrological Constants for Vedic, KP & Jaimini Computational Engine.

Provides complete typed dictionaries, enumerations, and metadata for:
- 12 Zodiac signs (Rashi) with Sanskrit/English names, lords, elements, and modalities
- 27 Nakshatras with Vimshottari lords, dasha periods, and pada boundaries
- Combustion degree thresholds (Astangata) relative to Sun
- Swiss Ephemeris ID mappings for planets, ayanamshas, and house systems
"""

from enum import Enum, IntEnum
from typing import Final, TypedDict


class PlanetEnum(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    RAHU = "Rahu"
    KETU = "Ketu"
    URANUS = "Uranus"
    NEPTUNE = "Neptune"
    PLUTO = "Pluto"


class ZodiacSignEnum(IntEnum):
    ARIES = 1
    TAURUS = 2
    GEMINI = 3
    CANCER = 4
    LEO = 5
    VIRGO = 6
    LIBRA = 7
    SCORPIO = 8
    SAGITTARIUS = 9
    CAPRICORN = 10
    AQUARIUS = 11
    PISCES = 12


class AyanamshaType(str, Enum):
    LAHIRI = "Lahiri"
    KRISHNAMURTI = "Krishnamurti"
    RAMAN = "Raman"
    YUKTESHWAR = "Yukteshwar"
    FAGAN_BRADLEY = "Fagan_Bradley"
    TROPICAL = "Tropical"


class NodeType(str, Enum):
    TRUE = "True"
    MEAN = "Mean"


class HouseSystemType(str, Enum):
    PLACIDUS = "Placidus"
    WHOLE_SIGN = "Whole_Sign"
    EQUAL = "Equal"
    PORPHYRY = "Porphyry"
    SRIPATHI = "Sripathi"
    KOCH = "Koch"
    CAMPANUS = "Campanus"
    REGIOMONTANUS = "Regiomontanus"


# ==========================================
# Typed Dictionaries for Detailed Metadata
# ==========================================

class ZodiacSignInfo(TypedDict):
    id: int
    sanskrit_name: str
    english_name: str
    lord: PlanetEnum
    element: str
    modality: str
    start_deg: float
    end_deg: float


class NakshatraInfo(TypedDict):
    id: int
    sanskrit_name: str
    lord: PlanetEnum
    dasha_years: int
    start_deg: float
    end_deg: float


# ==========================================
# 12 Zodiac Signs (Rashi) Metadata Table
# ==========================================

ZODIAC_SIGNS: Final[dict[int, ZodiacSignInfo]] = {
    1: {
        "id": 1,
        "sanskrit_name": "Mesha",
        "english_name": "Aries",
        "lord": PlanetEnum.MARS,
        "element": "Fire",
        "modality": "Movable",
        "start_deg": 0.0,
        "end_deg": 30.0,
    },
    2: {
        "id": 2,
        "sanskrit_name": "Vrishabha",
        "english_name": "Taurus",
        "lord": PlanetEnum.VENUS,
        "element": "Earth",
        "modality": "Fixed",
        "start_deg": 30.0,
        "end_deg": 60.0,
    },
    3: {
        "id": 3,
        "sanskrit_name": "Mithuna",
        "english_name": "Gemini",
        "lord": PlanetEnum.MERCURY,
        "element": "Air",
        "modality": "Dual",
        "start_deg": 60.0,
        "end_deg": 90.0,
    },
    4: {
        "id": 4,
        "sanskrit_name": "Karka",
        "english_name": "Cancer",
        "lord": PlanetEnum.MOON,
        "element": "Water",
        "modality": "Movable",
        "start_deg": 90.0,
        "end_deg": 120.0,
    },
    5: {
        "id": 5,
        "sanskrit_name": "Simha",
        "english_name": "Leo",
        "lord": PlanetEnum.SUN,
        "element": "Fire",
        "modality": "Fixed",
        "start_deg": 120.0,
        "end_deg": 150.0,
    },
    6: {
        "id": 6,
        "sanskrit_name": "Kanya",
        "english_name": "Virgo",
        "lord": PlanetEnum.MERCURY,
        "element": "Earth",
        "modality": "Dual",
        "start_deg": 150.0,
        "end_deg": 180.0,
    },
    7: {
        "id": 7,
        "sanskrit_name": "Tula",
        "english_name": "Libra",
        "lord": PlanetEnum.VENUS,
        "element": "Air",
        "modality": "Movable",
        "start_deg": 180.0,
        "end_deg": 210.0,
    },
    8: {
        "id": 8,
        "sanskrit_name": "Vrishchika",
        "english_name": "Scorpio",
        "lord": PlanetEnum.MARS,
        "element": "Water",
        "modality": "Fixed",
        "start_deg": 210.0,
        "end_deg": 240.0,
    },
    9: {
        "id": 9,
        "sanskrit_name": "Dhanu",
        "english_name": "Sagittarius",
        "lord": PlanetEnum.JUPITER,
        "element": "Fire",
        "modality": "Dual",
        "start_deg": 240.0,
        "end_deg": 270.0,
    },
    10: {
        "id": 10,
        "sanskrit_name": "Makara",
        "english_name": "Capricorn",
        "lord": PlanetEnum.SATURN,
        "element": "Earth",
        "modality": "Movable",
        "start_deg": 270.0,
        "end_deg": 300.0,
    },
    11: {
        "id": 11,
        "sanskrit_name": "Kumbha",
        "english_name": "Aquarius",
        "lord": PlanetEnum.SATURN,
        "element": "Air",
        "modality": "Fixed",
        "start_deg": 300.0,
        "end_deg": 330.0,
    },
    12: {
        "id": 12,
        "sanskrit_name": "Meena",
        "english_name": "Pisces",
        "lord": PlanetEnum.JUPITER,
        "element": "Water",
        "modality": "Dual",
        "start_deg": 330.0,
        "end_deg": 360.0,
    },
}

# ==========================================
# 27 Nakshatras Metadata Table
# ==========================================
# 1 Nakshatra = 13° 20' = 800 arcminutes = 13.333333333333334 degrees
# 1 Pada = 3° 20' = 200 arcminutes = 3.3333333333333335 degrees

NAKSHATRA_ARC_DEG: Final[float] = 360.0 / 27.0  # 13.333333333333334 degrees (13°20')
PADA_ARC_DEG: Final[float] = NAKSHATRA_ARC_DEG / 4.0  # 3.3333333333333335 degrees (3°20')

NAKSHATRAS: Final[dict[int, NakshatraInfo]] = {
    1: {
        "id": 1,
        "sanskrit_name": "Ashwini",
        "lord": PlanetEnum.KETU,
        "dasha_years": 7,
        "start_deg": 0.0,
        "end_deg": NAKSHATRA_ARC_DEG * 1,
    },
    2: {
        "id": 2,
        "sanskrit_name": "Bharani",
        "lord": PlanetEnum.VENUS,
        "dasha_years": 20,
        "start_deg": NAKSHATRA_ARC_DEG * 1,
        "end_deg": NAKSHATRA_ARC_DEG * 2,
    },
    3: {
        "id": 3,
        "sanskrit_name": "Krittika",
        "lord": PlanetEnum.SUN,
        "dasha_years": 6,
        "start_deg": NAKSHATRA_ARC_DEG * 2,
        "end_deg": NAKSHATRA_ARC_DEG * 3,
    },
    4: {
        "id": 4,
        "sanskrit_name": "Rohini",
        "lord": PlanetEnum.MOON,
        "dasha_years": 10,
        "start_deg": NAKSHATRA_ARC_DEG * 3,
        "end_deg": NAKSHATRA_ARC_DEG * 4,
    },
    5: {
        "id": 5,
        "sanskrit_name": "Mrigashira",
        "lord": PlanetEnum.MARS,
        "dasha_years": 7,
        "start_deg": NAKSHATRA_ARC_DEG * 4,
        "end_deg": NAKSHATRA_ARC_DEG * 5,
    },
    6: {
        "id": 6,
        "sanskrit_name": "Ardra",
        "lord": PlanetEnum.RAHU,
        "dasha_years": 18,
        "start_deg": NAKSHATRA_ARC_DEG * 5,
        "end_deg": NAKSHATRA_ARC_DEG * 6,
    },
    7: {
        "id": 7,
        "sanskrit_name": "Punarvasu",
        "lord": PlanetEnum.JUPITER,
        "dasha_years": 16,
        "start_deg": NAKSHATRA_ARC_DEG * 6,
        "end_deg": NAKSHATRA_ARC_DEG * 7,
    },
    8: {
        "id": 8,
        "sanskrit_name": "Pushya",
        "lord": PlanetEnum.SATURN,
        "dasha_years": 19,
        "start_deg": NAKSHATRA_ARC_DEG * 7,
        "end_deg": NAKSHATRA_ARC_DEG * 8,
    },
    9: {
        "id": 9,
        "sanskrit_name": "Ashlesha",
        "lord": PlanetEnum.MERCURY,
        "dasha_years": 17,
        "start_deg": NAKSHATRA_ARC_DEG * 8,
        "end_deg": NAKSHATRA_ARC_DEG * 9,
    },
    10: {
        "id": 10,
        "sanskrit_name": "Magha",
        "lord": PlanetEnum.KETU,
        "dasha_years": 7,
        "start_deg": NAKSHATRA_ARC_DEG * 9,
        "end_deg": NAKSHATRA_ARC_DEG * 10,
    },
    11: {
        "id": 11,
        "sanskrit_name": "Purva Phalguni",
        "lord": PlanetEnum.VENUS,
        "dasha_years": 20,
        "start_deg": NAKSHATRA_ARC_DEG * 10,
        "end_deg": NAKSHATRA_ARC_DEG * 11,
    },
    12: {
        "id": 12,
        "sanskrit_name": "Uttara Phalguni",
        "lord": PlanetEnum.SUN,
        "dasha_years": 6,
        "start_deg": NAKSHATRA_ARC_DEG * 11,
        "end_deg": NAKSHATRA_ARC_DEG * 12,
    },
    13: {
        "id": 13,
        "sanskrit_name": "Hasta",
        "lord": PlanetEnum.MOON,
        "dasha_years": 10,
        "start_deg": NAKSHATRA_ARC_DEG * 12,
        "end_deg": NAKSHATRA_ARC_DEG * 13,
    },
    14: {
        "id": 14,
        "sanskrit_name": "Chitra",
        "lord": PlanetEnum.MARS,
        "dasha_years": 7,
        "start_deg": NAKSHATRA_ARC_DEG * 13,
        "end_deg": NAKSHATRA_ARC_DEG * 14,
    },
    15: {
        "id": 15,
        "sanskrit_name": "Swati",
        "lord": PlanetEnum.RAHU,
        "dasha_years": 18,
        "start_deg": NAKSHATRA_ARC_DEG * 14,
        "end_deg": NAKSHATRA_ARC_DEG * 15,
    },
    16: {
        "id": 16,
        "sanskrit_name": "Vishakha",
        "lord": PlanetEnum.JUPITER,
        "dasha_years": 16,
        "start_deg": NAKSHATRA_ARC_DEG * 15,
        "end_deg": NAKSHATRA_ARC_DEG * 16,
    },
    17: {
        "id": 17,
        "sanskrit_name": "Anuradha",
        "lord": PlanetEnum.SATURN,
        "dasha_years": 19,
        "start_deg": NAKSHATRA_ARC_DEG * 16,
        "end_deg": NAKSHATRA_ARC_DEG * 17,
    },
    18: {
        "id": 18,
        "sanskrit_name": "Jyeshtha",
        "lord": PlanetEnum.MERCURY,
        "dasha_years": 17,
        "start_deg": NAKSHATRA_ARC_DEG * 17,
        "end_deg": NAKSHATRA_ARC_DEG * 18,
    },
    19: {
        "id": 19,
        "sanskrit_name": "Mula",
        "lord": PlanetEnum.KETU,
        "dasha_years": 7,
        "start_deg": NAKSHATRA_ARC_DEG * 18,
        "end_deg": NAKSHATRA_ARC_DEG * 19,
    },
    20: {
        "id": 20,
        "sanskrit_name": "Purva Ashadha",
        "lord": PlanetEnum.VENUS,
        "dasha_years": 20,
        "start_deg": NAKSHATRA_ARC_DEG * 19,
        "end_deg": NAKSHATRA_ARC_DEG * 20,
    },
    21: {
        "id": 21,
        "sanskrit_name": "Uttara Ashadha",
        "lord": PlanetEnum.SUN,
        "dasha_years": 6,
        "start_deg": NAKSHATRA_ARC_DEG * 20,
        "end_deg": NAKSHATRA_ARC_DEG * 21,
    },
    22: {
        "id": 22,
        "sanskrit_name": "Shravana",
        "lord": PlanetEnum.MOON,
        "dasha_years": 10,
        "start_deg": NAKSHATRA_ARC_DEG * 21,
        "end_deg": NAKSHATRA_ARC_DEG * 22,
    },
    23: {
        "id": 23,
        "sanskrit_name": "Dhanishta",
        "lord": PlanetEnum.MARS,
        "dasha_years": 7,
        "start_deg": NAKSHATRA_ARC_DEG * 22,
        "end_deg": NAKSHATRA_ARC_DEG * 23,
    },
    24: {
        "id": 24,
        "sanskrit_name": "Shatabhisha",
        "lord": PlanetEnum.RAHU,
        "dasha_years": 18,
        "start_deg": NAKSHATRA_ARC_DEG * 23,
        "end_deg": NAKSHATRA_ARC_DEG * 24,
    },
    25: {
        "id": 25,
        "sanskrit_name": "Purva Bhadrapada",
        "lord": PlanetEnum.JUPITER,
        "dasha_years": 16,
        "start_deg": NAKSHATRA_ARC_DEG * 24,
        "end_deg": NAKSHATRA_ARC_DEG * 25,
    },
    26: {
        "id": 26,
        "sanskrit_name": "Uttara Bhadrapada",
        "lord": PlanetEnum.SATURN,
        "dasha_years": 19,
        "start_deg": NAKSHATRA_ARC_DEG * 25,
        "end_deg": NAKSHATRA_ARC_DEG * 26,
    },
    27: {
        "id": 27,
        "sanskrit_name": "Revati",
        "lord": PlanetEnum.MERCURY,
        "dasha_years": 17,
        "start_deg": NAKSHATRA_ARC_DEG * 26,
        "end_deg": 360.0,
    },
}

# ==========================================
# Vimshottari Mahadasha Sequence
# ==========================================
VIMSHOTTARI_DASHA_ORDER: Final[list[tuple[PlanetEnum, int]]] = [
    (PlanetEnum.KETU, 7),
    (PlanetEnum.VENUS, 20),
    (PlanetEnum.SUN, 6),
    (PlanetEnum.MOON, 10),
    (PlanetEnum.MARS, 7),
    (PlanetEnum.RAHU, 18),
    (PlanetEnum.JUPITER, 16),
    (PlanetEnum.SATURN, 19),
    (PlanetEnum.MERCURY, 17),
]

TOTAL_VIMSHOTTARI_YEARS: Final[int] = 120

# ==========================================
# Planetary Combustion Thresholds (Astangata)
# ==========================================
# Distances from Sun within which a planet is considered combust (in degrees)
COMBUSTION_THRESHOLDS: Final[dict[PlanetEnum, float | dict[str, float]]] = {
    PlanetEnum.MOON: 12.0,
    PlanetEnum.MARS: 17.0,
    PlanetEnum.MERCURY: {
        "direct": 14.0,
        "retrograde": 12.0,
    },
    PlanetEnum.JUPITER: 11.0,
    PlanetEnum.VENUS: {
        "direct": 10.0,
        "retrograde": 8.0,
    },
    PlanetEnum.SATURN: 15.0,
}

# ==========================================
# Swiss Ephemeris IDs & Sidereal Mode Constants
# ==========================================
# Swiss Ephemeris standard constants (matching C sweph library)
SWE_SUN: Final[int] = 0
SWE_MOON: Final[int] = 1
SWE_MERCURY: Final[int] = 2
SWE_VENUS: Final[int] = 3
SWE_MARS: Final[int] = 4
SWE_JUPITER: Final[int] = 5
SWE_SATURN: Final[int] = 6
SWE_URANUS: Final[int] = 7
SWE_NEPTUNE: Final[int] = 8
SWE_PLUTO: Final[int] = 9
SWE_MEAN_NODE: Final[int] = 10
SWE_TRUE_NODE: Final[int] = 11

# Ayanamsha IDs in Swiss Ephemeris
SWE_SIDM_FAGAN_BRADLEY: Final[int] = 0
SWE_SIDM_LAHIRI: Final[int] = 1
SWE_SIDM_RAMAN: Final[int] = 3
SWE_SIDM_KRISHNAMURTI: Final[int] = 5
SWE_SIDM_YUKTESHWAR: Final[int] = 7

# House system characters for swe_houses
SWE_HOUSES_PLACIDUS: Final[bytes] = b'P'
SWE_HOUSES_WHOLE_SIGN: Final[bytes] = b'W'
SWE_HOUSES_EQUAL: Final[bytes] = b'E'
SWE_HOUSES_PORPHYRY: Final[bytes] = b'O'
SWE_HOUSES_KOCH: Final[bytes] = b'K'
SWE_HOUSES_CAMPANUS: Final[bytes] = b'C'
SWE_HOUSES_REGIOMONTANUS: Final[bytes] = b'R'

# Calculation flags
SWE_FLG_SWIEPH: Final[int] = 2
SWE_FLG_SPEED: Final[int] = 256
SWE_FLG_SIDEREAL: Final[int] = 64 * 1024  # 65536
