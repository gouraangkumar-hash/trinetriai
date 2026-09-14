"""Jaimini Upadesha Sutras Computational Engine.

Provides:
- 7 and 8 Chara Karaka Ranking Engine (Atmakaraka AK down to Darakaraka DK)
  with Rahu degree inversion for the 8-karaka scheme.
- Arudha Pada Calculation Engine (A1–A12, AL, UL) with standard BPHS 1st/7th shift exceptions.
- Rashi Drishti (Sign Aspect) Matrix and Planetary Sign Aspects.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Final, Literal, Optional

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


class CharaAntardashaItem(BaseModel):
    """Sub-period (Antardasha) within a Chara Mahadasha."""
    model_config = ConfigDict(frozen=True)

    sign_id: int = Field(..., ge=1, le=12)
    sign_name: str
    sign_english: str
    sign_lord: str
    duration_months: float
    start_date: datetime
    end_date: datetime
    is_active: bool = False


class CharaMahadashaItem(BaseModel):
    """Major period (Mahadasha) of a zodiac sign in Jaimini Chara Dasha."""
    model_config = ConfigDict(frozen=True)

    cycle: int = Field(1, description="Cycle number (1 or 2)")
    sign_id: int = Field(..., ge=1, le=12)
    sign_name: str
    sign_english: str
    sign_lord: str
    duration_years: int
    start_date: datetime
    end_date: datetime
    is_active: bool = False
    antardashas: list[CharaAntardashaItem] = Field(default_factory=list)


class CharaDashaResult(BaseModel):
    """Complete Jaimini Chara Dasha timeline and active period calculation (K.N. Rao System)."""
    model_config = ConfigDict(frozen=True)

    lagna_sign_id: int
    lagna_sign_name: str
    lagna_sign_english: str
    ninth_sign_id: int
    ninth_sign_name: str
    ninth_sign_english: str
    is_direct_order: bool = Field(
        description="True if 9th from Lagna is in Savya group (Direct), False if Apasavya (Reverse)"
    )
    progression_signs: list[int]
    mahadashas: list[CharaMahadashaItem]
    active_mahadasha: Optional[CharaMahadashaItem] = None
    active_antardasha: Optional[CharaAntardashaItem] = None


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

    # =========================================================================
    # 4. Jaimini Chara Dasha Engine (K.N. Rao System)
    # =========================================================================

    DAYS_PER_SOLAR_YEAR: float = 365.2425
    SAVYA_SIGNS: Final[set[int]] = {1, 2, 3, 7, 8, 9}
    APASAVYA_SIGNS: Final[set[int]] = {4, 5, 6, 10, 11, 12}

    @classmethod
    def _resolve_dual_lord(cls, chart: UnifiedChartData, sign_id: int) -> tuple[PlanetEnum, int]:
        """Resolves ruling lord and its occupied sign for dual-lord signs Scorpio (8) and Aquarius (11).

        Rules (K.N. Rao / Jaimini):
        1. If one lord is in the sign itself and the other is outside, pick the one OUTSIDE.
        2. If both are in the sign itself, pick Mars for Scorpio / Saturn for Aquarius (giving 12 years).
        3. If both are outside, determine the stronger lord:
           a) Associated with a greater number of planets (conjunctions).
           b) If tied, lord in its sign of exaltation (Mars in 10, Ketu in 9; Saturn in 7, Rahu in 2).
           c) If still tied, lord with higher intra-sign degree.
        """
        if sign_id == 8:  # Scorpio: Mars vs Ketu
            p1, p2 = PlanetEnum.MARS, PlanetEnum.KETU
            s1 = chart.planets[p1].sign.id
            s2 = chart.planets[p2].sign.id

            if s1 == 8 and s2 != 8:
                return p2, s2
            if s2 == 8 and s1 != 8:
                return p1, s1
            if s1 == 8 and s2 == 8:
                return p1, 8

            # Both outside: compare conjunctions
            c1 = sum(1 for p, pos in chart.planets.items() if p != p1 and pos.sign.id == s1)
            c2 = sum(1 for p, pos in chart.planets.items() if p != p2 and pos.sign.id == s2)
            if c1 > c2:
                return p1, s1
            if c2 > c1:
                return p2, s2

            # Exaltation check
            if s1 == 10 and s2 != 9:
                return p1, s1
            if s2 == 9 and s1 != 10:
                return p2, s2

            # Intra-sign degree check
            d1 = chart.planets[p1].sign.intra_sign_degree
            d2 = chart.planets[p2].sign.intra_sign_degree
            return (p1, s1) if d1 >= d2 else (p2, s2)

        elif sign_id == 11:  # Aquarius: Saturn vs Rahu
            p1, p2 = PlanetEnum.SATURN, PlanetEnum.RAHU
            s1 = chart.planets[p1].sign.id
            s2 = chart.planets[p2].sign.id

            if s1 == 11 and s2 != 11:
                return p2, s2
            if s2 == 11 and s1 != 11:
                return p1, s1
            if s1 == 11 and s2 == 11:
                return p1, 11

            # Both outside: compare conjunctions
            c1 = sum(1 for p, pos in chart.planets.items() if p != p1 and pos.sign.id == s1)
            c2 = sum(1 for p, pos in chart.planets.items() if p != p2 and pos.sign.id == s2)
            if c1 > c2:
                return p1, s1
            if c2 > c1:
                return p2, s2

            # Exaltation check
            if s1 == 7 and s2 != 2:
                return p1, s1
            if s2 == 2 and s1 != 7:
                return p2, s2

            # Intra-sign degree check
            d1 = chart.planets[p1].sign.intra_sign_degree
            d2 = chart.planets[p2].sign.intra_sign_degree
            return (p1, s1) if d1 >= d2 else (p2, s2)

        else:
            lord = ZODIAC_SIGNS[sign_id]["lord"]
            return lord, chart.planets[lord].sign.id

    @classmethod
    def _calculate_sign_duration(cls, chart: UnifiedChartData, sign_id: int) -> tuple[int, PlanetEnum]:
        """Calculates Mahadasha duration (1-12 years) and ruling lord for a sign in Chara Dasha.

        Rules:
        - If lord is in the sign itself: 12 years.
        - If sign is Savya (1, 2, 3, 7, 8, 9): count forward from sign to lord sign, subtract 1.
        - If sign is Apasavya (4, 5, 6, 10, 11, 12): count backward from sign to lord sign, subtract 1.
        """
        lord_planet, lord_sign_id = cls._resolve_dual_lord(chart, sign_id)
        if lord_sign_id == sign_id:
            return 12, lord_planet

        if sign_id in cls.SAVYA_SIGNS:
            count = ((lord_sign_id - sign_id) % 12) + 1
        else:
            count = ((sign_id - lord_sign_id) % 12) + 1

        duration = count - 1
        if duration <= 0:
            duration = 12
        return duration, lord_planet

    @classmethod
    def _generate_antardashas(
        cls,
        chart: UnifiedChartData,
        md_sign_id: int,
        md_years: int,
        md_start: datetime,
        md_end: datetime,
        target_date: datetime,
    ) -> list[CharaAntardashaItem]:
        """Generates the 12 Antardashas for a Mahadasha sign according to K.N. Rao rules.

        Rules:
        - Direction determined by 9th house from Mahadasha sign.
        - If 9th is Savya: forward sequence.
        - If 9th is Apasavya: reverse sequence.
        - The Mahadasha sign itself is placed LAST in the sequence!
        - Each Antardasha duration = md_years months.
        """
        ninth_from_md = ((md_sign_id - 1 + 8) % 12) + 1
        is_ad_direct = ninth_from_md in cls.SAVYA_SIGNS

        if is_ad_direct:
            ad_signs = [((md_sign_id - 1 + i) % 12) + 1 for i in range(1, 13)]
        else:
            ad_signs = [((md_sign_id - 1 - i) % 12) + 1 for i in range(1, 13)]

        total_md_seconds = (md_end - md_start).total_seconds()
        ad_seconds = total_md_seconds / 12.0

        antardashas: list[CharaAntardashaItem] = []
        cur_start = md_start

        for idx, s_id in enumerate(ad_signs):
            if idx == 11:
                cur_end = md_end
            else:
                cur_end = cur_start + timedelta(seconds=ad_seconds)

            is_active = cur_start <= target_date <= cur_end
            sign_info = ZODIAC_SIGNS[s_id]
            lord_planet, _ = cls._resolve_dual_lord(chart, s_id)

            antardashas.append(
                CharaAntardashaItem(
                    sign_id=s_id,
                    sign_name=sign_info["sanskrit_name"],
                    sign_english=sign_info["english_name"],
                    sign_lord=lord_planet.value,
                    duration_months=float(md_years),
                    start_date=cur_start,
                    end_date=cur_end,
                    is_active=is_active,
                )
            )
            cur_start = cur_end

        return antardashas

    @classmethod
    def calculate_chara_dasha(
        cls,
        chart: UnifiedChartData,
        target_date: Optional[datetime] = None,
        cycles: int = 2,
    ) -> CharaDashaResult:
        """Calculates the complete Jaimini Chara Dasha timeline (Cycles 1 & 2) and active periods.

        Args:
            chart: UnifiedChartData containing birth details and planetary positions.
            target_date: Timestamp to determine active Mahadasha and Antardasha. Defaults to chart birth date if None.
            cycles: Number of 12-sign cycles to calculate (default 2, spanning ~150-180 years).

        Returns:
            CharaDashaResult with complete timeline and active status.
        """
        if target_date is None:
            target_date = chart.utc_datetime

        lagna_sign_id = chart.angles.ascendant_sign.id
        lagna_info = ZODIAC_SIGNS[lagna_sign_id]

        ninth_sign_id = ((lagna_sign_id - 1 + 8) % 12) + 1
        ninth_info = ZODIAC_SIGNS[ninth_sign_id]

        is_direct_order = ninth_sign_id in cls.SAVYA_SIGNS

        if is_direct_order:
            progression_signs = [((lagna_sign_id - 1 + i) % 12) + 1 for i in range(12)]
        else:
            progression_signs = [((lagna_sign_id - 1 - i) % 12) + 1 for i in range(12)]

        mahadashas: list[CharaMahadashaItem] = []
        active_md: Optional[CharaMahadashaItem] = None
        active_ad: Optional[CharaAntardashaItem] = None

        cur_start = chart.utc_datetime

        for cycle in range(1, cycles + 1):
            for s_id in progression_signs:
                dur_years, lord_planet = cls._calculate_sign_duration(chart, s_id)
                dur_days = dur_years * cls.DAYS_PER_SOLAR_YEAR
                cur_end = cur_start + timedelta(days=dur_days)

                is_md_active = cur_start <= target_date <= cur_end

                sign_info = ZODIAC_SIGNS[s_id]
                ad_list = cls._generate_antardashas(
                    chart=chart,
                    md_sign_id=s_id,
                    md_years=dur_years,
                    md_start=cur_start,
                    md_end=cur_end,
                    target_date=target_date,
                )

                md_item = CharaMahadashaItem(
                    cycle=cycle,
                    sign_id=s_id,
                    sign_name=sign_info["sanskrit_name"],
                    sign_english=sign_info["english_name"],
                    sign_lord=lord_planet.value,
                    duration_years=dur_years,
                    start_date=cur_start,
                    end_date=cur_end,
                    is_active=is_md_active,
                    antardashas=ad_list,
                )

                if is_md_active:
                    active_md = md_item
                    for ad in ad_list:
                        if ad.is_active:
                            active_ad = ad
                            break

                mahadashas.append(md_item)
                cur_start = cur_end

        return CharaDashaResult(
            lagna_sign_id=lagna_sign_id,
            lagna_sign_name=lagna_info["sanskrit_name"],
            lagna_sign_english=lagna_info["english_name"],
            ninth_sign_id=ninth_sign_id,
            ninth_sign_name=ninth_info["sanskrit_name"],
            ninth_sign_english=ninth_info["english_name"],
            is_direct_order=is_direct_order,
            progression_signs=progression_signs,
            mahadashas=mahadashas,
            active_mahadasha=active_md,
            active_antardasha=active_ad,
        )
