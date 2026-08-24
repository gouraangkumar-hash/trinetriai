"""Jaimini Upadesha Sutras Computational Engine.

Provides:
- 7 and 8 Chara Karaka Ranking Engine (Atmakaraka AK down to Darakaraka DK)
  with Rahu degree inversion for the 8-karaka scheme.
- Arudha Pada Calculation Engine (A1–A12, AL, UL) with standard BPHS 1st/7th shift exceptions.
- Rashi Drishti (Sign Aspect) Matrix and Planetary Sign Aspects.
"""

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from core.astro_utils import decimal_to_dms
from core.constants import ZODIAC_SIGNS, PlanetEnum, ZodiacSignEnum
from schemas.models import DMSModel, UnifiedChartData


class JaiminiKarakaRole(str, Enum):
    AK = "Atmakaraka"        # Soul
    AmK = "Amatyakaraka"     # Career / Minister
    BK = "Bhratrikaraka"     # Siblings / Father (in 7-karaka)
    MK = "Matrikaraka"       # Mother / Education
    PiK = "Pitrikaraka"      # Father (in 8-karaka)
    PK = "Putrakaraka"       # Children / Intellect
    GK = "Gnatikaraka"       # Relatives / Obstacles
    DK = "Darakaraka"        # Spouse / Partner


class CharaKarakaItem(BaseModel):
    """A single planetary Chara Karaka assignment."""
    model_config = ConfigDict(frozen=True)

    role_code: str = Field(..., description="Short role code (AK, AmK, BK, MK, PiK, PK, GK, DK)")
    role_name: JaiminiKarakaRole
    planet: PlanetEnum
    sign_id: int = Field(..., ge=1, le=12)
    sign_name: str
    intra_sign_degree: float
    effective_ranking_degree: float = Field(
        description="Effective degree used for ranking (inverted 30-deg for Rahu in 8-karaka)"
    )
    dms: DMSModel


class CharaKarakaSchemeResult(BaseModel):
    """Complete Chara Karaka scheme assignment result."""
    model_config = ConfigDict(frozen=True)

    scheme: Literal[7, 8]
    karakas: list[CharaKarakaItem]
    by_planet: dict[PlanetEnum, CharaKarakaItem]
    by_role: dict[str, CharaKarakaItem]


class ArudhaPadaItem(BaseModel):
    """Arudha Pada for a single house."""
    model_config = ConfigDict(frozen=True)

    house_number: int = Field(..., ge=1, le=12)
    pada_name: str = Field(description="A1 to A12, with AL for A1 and UL for A12")
    raw_house: int = Field(description="Raw calculated house before exception check")
    final_house: int = Field(description="Final house after 1st/7th shift exception")
    is_exception_applied: bool
    sign_id: int = Field(..., ge=1, le=12)
    sign_name: str
    sign_lord: PlanetEnum


class ArudhaPadasResult(BaseModel):
    """Complete 12 Arudha Padas for a chart."""
    model_config = ConfigDict(frozen=True)

    arudha_lagna: ArudhaPadaItem = Field(description="Arudha Lagna (AL / A1)")
    upapada_lagna: ArudhaPadaItem = Field(description="Upapada Lagna (UL / A12)")
    padas: list[ArudhaPadaItem]
    by_house: dict[int, ArudhaPadaItem]


class RashiDrishtiAspects(BaseModel):
    """Sign aspects (Rashi Drishti) for all 12 zodiac signs."""
    model_config = ConfigDict(frozen=True)

    sign_aspects_map: dict[int, list[int]] = Field(
        description="Maps each sign ID (1-12) to the list of sign IDs it aspects"
    )
    planets_aspecting_signs: dict[PlanetEnum, list[int]] = Field(
        description="List of sign IDs aspected by each planet via Rashi Drishti"
    )


# =========================================================================
# Jaimini Computational Engine
# =========================================================================

class JaiminiEngine:
    """Core Jaimini astrological algorithms."""

    @staticmethod
    def _build_dms(degrees: float) -> DMSModel:
        d, m, s, formatted = decimal_to_dms(degrees)
        return DMSModel(degrees=d, minutes=m, seconds=s, formatted=formatted)

    # =========================================================================
    # 1. Chara Karaka Engine
    # =========================================================================

    @classmethod
    def calculate_chara_karakas(
        cls,
        chart: UnifiedChartData,
        scheme: Literal[7, 8] = 7,
    ) -> CharaKarakaSchemeResult:
        """Calculates 7 or 8 Chara Karaka rankings sorted by intra-sign degree (30° down to 0°).

        Args:
            chart: UnifiedChartData containing calculated planetary positions.
            scheme: 7 for classical 7-Karaka, 8 for Rahu-inclusive 8-Karaka.

        Returns:
            CharaKarakaSchemeResult.
        """
        eligible_planets = [
            PlanetEnum.SUN,
            PlanetEnum.MOON,
            PlanetEnum.MARS,
            PlanetEnum.MERCURY,
            PlanetEnum.JUPITER,
            PlanetEnum.VENUS,
            PlanetEnum.SATURN,
        ]
        if scheme == 8:
            eligible_planets.append(PlanetEnum.RAHU)

        # Build candidate list with intra-sign degrees
        candidates: list[dict] = []
        for p_name in eligible_planets:
            p_pos = chart.planets[p_name]
            intra_deg = p_pos.sign.intra_sign_degree

            # In 8-karaka scheme, Rahu moves retrograde so its degree is inverted
            if scheme == 8 and p_name == PlanetEnum.RAHU:
                effective_deg = 30.0 - intra_deg
            else:
                effective_deg = intra_deg

            candidates.append({
                "planet": p_name,
                "sign_id": p_pos.sign.id,
                "sign_name": p_pos.sign.sanskrit_name,
                "intra_sign_degree": intra_deg,
                "effective_deg": effective_deg,
            })

        # Sort descending by effective degree (highest degree gets AK)
        candidates.sort(key=lambda x: x["effective_deg"], reverse=True)

        if scheme == 7:
            role_order = [
                ("AK", JaiminiKarakaRole.AK),
                ("AmK", JaiminiKarakaRole.AmK),
                ("BK", JaiminiKarakaRole.BK),
                ("MK", JaiminiKarakaRole.MK),
                ("PK", JaiminiKarakaRole.PK),
                ("GK", JaiminiKarakaRole.GK),
                ("DK", JaiminiKarakaRole.DK),
            ]
        else:
            role_order = [
                ("AK", JaiminiKarakaRole.AK),
                ("AmK", JaiminiKarakaRole.AmK),
                ("BK", JaiminiKarakaRole.BK),
                ("MK", JaiminiKarakaRole.MK),
                ("PiK", JaiminiKarakaRole.PiK),
                ("PK", JaiminiKarakaRole.PK),
                ("GK", JaiminiKarakaRole.GK),
                ("DK", JaiminiKarakaRole.DK),
            ]

        karakas: list[CharaKarakaItem] = []
        by_planet: dict[PlanetEnum, CharaKarakaItem] = {}
        by_role: dict[str, CharaKarakaItem] = {}

        for idx, (code, role_enum) in enumerate(role_order):
            c = candidates[idx]
            item = CharaKarakaItem(
                role_code=code,
                role_name=role_enum,
                planet=c["planet"],
                sign_id=c["sign_id"],
                sign_name=c["sign_name"],
                intra_sign_degree=c["intra_sign_degree"],
                effective_ranking_degree=c["effective_deg"],
                dms=cls._build_dms(c["intra_sign_degree"]),
            )
            karakas.append(item)
            by_planet[c["planet"]] = item
            by_role[code] = item

        return CharaKarakaSchemeResult(
            scheme=scheme,
            karakas=karakas,
            by_planet=by_planet,
            by_role=by_role,
        )

    # =========================================================================
    # 2. Arudha Padas Engine
    # =========================================================================

    @classmethod
    def calculate_arudha_padas(cls, chart: UnifiedChartData) -> ArudhaPadasResult:
        """Calculates 12 Arudha Padas (A1 to A12, AL, UL) with standard BPHS 1st/7th shift exceptions.

        Rules (Brihat Parashara Hora Shastra Ch. 29 / Jaimini Sutras):
        1. For House H (Sign S_H), locate its ruling lord in House P_L.
        2. Distance d = (P_L - H) mod 12. If d == 0, d = 12.
        3. Raw Pada P_raw = (P_L + d) = (H + 2*d) mod 12.
        4. Exceptions:
           - If P_raw == H (Lord in 1st or 7th): Pada shifts to 10th house from H.
           - If P_raw == 7th from H: Pada shifts to 10th house from P_raw (which is 4th from H).
        """
        # Ascendant sign in Whole Sign system
        asc_sign_id = chart.angles.ascendant_sign.id  # 1 to 12

        # Map Whole Sign house numbers to sign IDs
        # House 1 = asc_sign_id, House 2 = asc_sign_id + 1, etc.
        house_to_sign: dict[int, int] = {}
        sign_to_house: dict[int, int] = {}
        for h in range(1, 13):
            s_id = ((asc_sign_id - 1 + (h - 1)) % 12) + 1
            house_to_sign[h] = s_id
            sign_to_house[s_id] = h

        # Map each planet to its Whole Sign house
        planet_houses: dict[PlanetEnum, int] = {}
        for p_name, p_pos in chart.planets.items():
            p_sign_id = p_pos.sign.id
            planet_houses[p_name] = sign_to_house[p_sign_id]

        padas_list: list[ArudhaPadaItem] = []
        by_house: dict[int, ArudhaPadaItem] = {}

        for h in range(1, 13):
            sign_id = house_to_sign[h]
            sign_lord = ZODIAC_SIGNS[sign_id]["lord"]

            # Locate lord's house
            lord_house = planet_houses[sign_lord]

            # Distance from house h to lord's house
            dist = (lord_house - h) % 12
            if dist == 0:
                dist = 12

            # Raw pada house = lord_house + dist
            raw_house = ((lord_house - 1 + dist) % 12) + 1

            # Classical BPHS Exception Check:
            # An Arudha cannot fall in the 1st or 7th house from the source house 'h'
            seventh_from_h = ((h - 1 + 6) % 12) + 1
            is_exception = False
            final_house = raw_house

            if raw_house == h:
                # Lord in 1st or 7th -> shift 10 houses forward from h (10th from h)
                final_house = ((h - 1 + 9) % 12) + 1
                is_exception = True
            elif raw_house == seventh_from_h:
                # Shifts 10 houses forward from 7th -> 4th house from h
                final_house = ((raw_house - 1 + 9) % 12) + 1
                is_exception = True

            final_sign_id = house_to_sign[final_house]
            final_sign_info = ZODIAC_SIGNS[final_sign_id]

            pada_code = f"A{h}"
            if h == 1:
                pada_label = "AL (A1)"
            elif h == 12:
                pada_label = "UL (A12)"
            else:
                pada_label = pada_code

            item = ArudhaPadaItem(
                house_number=h,
                pada_name=pada_label,
                raw_house=raw_house,
                final_house=final_house,
                is_exception_applied=is_exception,
                sign_id=final_sign_id,
                sign_name=final_sign_info["sanskrit_name"],
                sign_lord=final_sign_info["lord"],
            )
            padas_list.append(item)
            by_house[h] = item

        return ArudhaPadasResult(
            arudha_lagna=by_house[1],
            upapada_lagna=by_house[12],
            padas=padas_list,
            by_house=by_house,
        )

    # =========================================================================
    # 3. Rashi Drishti (Sign Aspects)
    # =========================================================================

    @classmethod
    def calculate_rashi_drishti(cls, chart: Optional[UnifiedChartData] = None) -> RashiDrishtiAspects:
        """Calculates the canonical Jaimini Rashi Drishti (Sign Aspects) matrix.

        Rules:
        - Movable (1, 4, 7, 10) aspects all Fixed (2, 5, 8, 11) EXCEPT adjacent.
        - Fixed (2, 5, 8, 11) aspects all Movable (1, 4, 7, 10) EXCEPT adjacent.
        - Dual (3, 6, 9, 12) aspects all other Dual signs.
        """
        aspects_map: dict[int, list[int]] = {
            # Movable Signs (Aries, Cancer, Libra, Capricorn)
            1: [8, 11, 5],    # Aries aspects Scorpio, Aquarius, Leo (not Taurus 2)
            4: [11, 2, 8],    # Cancer aspects Aquarius, Taurus, Scorpio (not Leo 5)
            7: [2, 5, 11],    # Libra aspects Taurus, Leo, Aquarius (not Scorpio 8)
            10: [5, 8, 2],    # Capricorn aspects Leo, Scorpio, Taurus (not Aquarius 11)

            # Fixed Signs (Taurus, Leo, Scorpio, Aquarius)
            2: [4, 7, 10],    # Taurus aspects Cancer, Libra, Capricorn (not Aries 1)
            5: [7, 10, 1],    # Leo aspects Libra, Capricorn, Aries (not Cancer 4)
            8: [10, 1, 4],    # Scorpio aspects Capricorn, Aries, Cancer (not Libra 7)
            11: [1, 4, 7],    # Aquarius aspects Aries, Cancer, Libra (not Capricorn 10)

            # Dual Signs (Gemini, Virgo, Sagittarius, Pisces)
            3: [6, 9, 12],    # Gemini aspects Virgo, Sagittarius, Pisces
            6: [3, 9, 12],    # Virgo aspects Gemini, Sagittarius, Pisces
            9: [3, 6, 12],    # Sagittarius aspects Gemini, Virgo, Pisces
            12: [3, 6, 9],    # Pisces aspects Gemini, Virgo, Sagittarius
        }

        planets_aspecting_signs: dict[PlanetEnum, list[int]] = {}
        if chart is not None:
            for p_name, p_pos in chart.planets.items():
                p_sign_id = p_pos.sign.id
                planets_aspecting_signs[p_name] = aspects_map.get(p_sign_id, [])

        return RashiDrishtiAspects(
            sign_aspects_map=aspects_map,
            planets_aspecting_signs=planets_aspecting_signs,
        )
