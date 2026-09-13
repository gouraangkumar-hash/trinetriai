"""Classical Vedic Gochar (Planetary Transits) Engine.

Adheres to classical Phaladeepika (Chapter 26) and Brihat Samhita:
- Real-time Sidereal Transits for 9 Grahas (Sun, Moon, Mars, Mercury, Jupiter,
  Venus, Saturn, Rahu, Ketu)
- Dual-reference house placements:
  * House from Natal Lagna (Ascendant)
  * House from Natal Moon (Janma Rashi - classical primary transit reference)
- Phaladeepika Gochar Benefic/Malefic evaluation from Janma Rashi:
  * Sun: 3, 6, 10, 11
  * Moon: 1, 3, 6, 7, 10, 11 (8th is Chandrashtama)
  * Mars: 3, 6, 11
  * Mercury: 2, 4, 6, 8, 10, 11
  * Jupiter: 2, 5, 7, 9, 11
  * Venus: 1, 2, 3, 4, 5, 8, 9, 11, 12
  * Saturn: 3, 6, 11 (Sade Sati in 12, 1, 2; Kantaka in 4; Ashtama in 8)
  * Rahu / Ketu: 3, 6, 10, 11
- Integration with Sarvashtakavarga (SAV) bindu strength and Bhinnashtakavarga (BAV)
- Kaksha subdivision tracking at transit longitude
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field

from core.constants import AyanamshaType, NodeType, HouseSystemType, PlanetEnum, ZODIAC_SIGNS
from core.ephemeris import EphemerisEngine
from schemas.models import BirthInput, GeoLocationModel, UnifiedChartData
from engines.ashtakavarga import AshtakavargaEngine, AshtakavargaFullReport, KAKSHA_LORDS, KAKSHA_LORDS_SANSKRIT


# =============================================================================
# Classical Phaladeepika Chapter 26 Benefic Houses from Janma Rashi (Natal Moon)
# =============================================================================

PHALADEEPIKA_BENEFIC_HOUSES: Dict[PlanetEnum, Set[int]] = {
    PlanetEnum.SUN: {3, 6, 10, 11},
    PlanetEnum.MOON: {1, 3, 6, 7, 10, 11},
    PlanetEnum.MARS: {3, 6, 11},
    PlanetEnum.MERCURY: {2, 4, 6, 8, 10, 11},
    PlanetEnum.JUPITER: {2, 5, 7, 9, 11},
    PlanetEnum.VENUS: {1, 2, 3, 4, 5, 8, 9, 11, 12},
    PlanetEnum.SATURN: {3, 6, 11},
    PlanetEnum.RAHU: {3, 6, 10, 11},
    PlanetEnum.KETU: {3, 6, 10, 11},
}

PLANET_GLYPHS: Dict[str, str] = {
    "Sun": "☉",
    "Moon": "☽",
    "Mars": "♂",
    "Mercury": "☿",
    "Jupiter": "♃",
    "Venus": "♀",
    "Saturn": "♄",
    "Rahu": "☊",
    "Ketu": "☋",
}


# =============================================================================
# Pydantic Output Schemas
# =============================================================================

class GocharGrahaDetail(BaseModel):
    planet: str
    glyph: str
    sign_id: int
    sign_name: str
    sign_sanskrit: str
    intra_sign_degree: float
    degree_formatted: str
    nakshatra: str
    pada: int
    is_retrograde: bool
    is_combust: bool
    speed: float
    house_from_lagna: int
    house_from_moon: int
    is_benefic_from_moon: bool
    classical_status: str
    transit_phala: str
    sav_bindus: int
    bav_bindus: int
    kaksha_number: int
    kaksha_lord: str
    kaksha_lord_sanskrit: str
    is_special_alert: bool = False
    alert_message: Optional[str] = None


class GocharSummary(BaseModel):
    transit_utc: str
    transit_date_formatted: str
    natal_moon_sign: str
    natal_lagna_sign: str
    benefic_count: int
    challenging_count: int
    sade_sati_phase: str
    is_chandrashtama: bool
    guru_gochar_summary: str
    rahu_ketu_summary: str


class GocharReport(BaseModel):
    summary: GocharSummary
    transits: List[GocharGrahaDetail]
    transit_chart: Optional[Any] = None


# =============================================================================
# Core Gochar Engine
# =============================================================================

class GocharEngine:
    """Evaluates real-time planetary transits against natal chart."""

    _ephemeris = EphemerisEngine()

    @classmethod
    def calculate_transit_chart(
        cls,
        natal_chart: UnifiedChartData,
        transit_dt: Optional[datetime] = None,
    ) -> UnifiedChartData:
        """Calculates sidereal positions of transiting planets for the given datetime."""
        if transit_dt is None:
            transit_dt = datetime.now(ZoneInfo("UTC"))
        elif transit_dt.tzinfo is None:
            transit_dt = transit_dt.replace(tzinfo=ZoneInfo("UTC"))

        loc = natal_chart.input_data.location
        transit_input = BirthInput(
            year=transit_dt.year,
            month=transit_dt.month,
            day=transit_dt.day,
            hour=transit_dt.hour,
            minute=transit_dt.minute,
            second=float(transit_dt.second) + (transit_dt.microsecond / 1_000_000.0),
            location=loc,
            ayanamsha=natal_chart.input_data.ayanamsha,
            node_type=natal_chart.input_data.node_type,
            house_system=HouseSystemType.PLACIDUS,
        )
        return cls._ephemeris.calculate_chart(transit_input)

    @classmethod
    def evaluate(
        cls,
        natal_chart: UnifiedChartData,
        av_report: Optional[AshtakavargaFullReport] = None,
        transit_dt: Optional[datetime] = None,
        sign_mode: str = "sanskrit",
    ) -> GocharReport:
        """Runs complete Gochar evaluation against natal chart."""
        transit_chart = cls.calculate_transit_chart(natal_chart, transit_dt)

        if av_report is None:
            av_report = AshtakavargaEngine.evaluate(natal_chart, sign_mode=sign_mode)

        natal_lagna_sign = natal_chart.angles.ascendant_sign.id
        natal_moon_sign = natal_chart.planets[PlanetEnum.MOON].sign.id

        sav_map = {sd.sign_id: sd.total_bindus for sd in av_report.sarvashtakavarga}

        transits_list: List[GocharGrahaDetail] = []
        benefic_count = 0
        challenging_count = 0
        is_chandrashtama = False
        sade_sati_phase = "Inactive"

        # Check Saturn transit for Sade Sati
        saturn_pos = transit_chart.planets[PlanetEnum.SATURN]
        saturn_h_moon = ((saturn_pos.sign.id - natal_moon_sign) % 12) + 1
        if saturn_h_moon == 12:
            sade_sati_phase = "Rising Phase (12th from Moon)"
        elif saturn_h_moon == 1:
            sade_sati_phase = "Peak Core Phase (Janma Shani)"
        elif saturn_h_moon == 2:
            sade_sati_phase = "Setting Phase (2nd from Moon)"
        elif saturn_h_moon == 4:
            sade_sati_phase = "Kantaka Shani (4th from Moon)"
        elif saturn_h_moon == 8:
            sade_sati_phase = "Ashtama Shani (8th from Moon)"

        # Check Moon transit for Chandrashtama
        moon_pos = transit_chart.planets[PlanetEnum.MOON]
        moon_h_moon = ((moon_pos.sign.id - natal_moon_sign) % 12) + 1
        if moon_h_moon == 8:
            is_chandrashtama = True

        ordered_grahas = [
            PlanetEnum.SUN,
            PlanetEnum.MOON,
            PlanetEnum.MARS,
            PlanetEnum.MERCURY,
            PlanetEnum.JUPITER,
            PlanetEnum.VENUS,
            PlanetEnum.SATURN,
            PlanetEnum.RAHU,
            PlanetEnum.KETU,
        ]

        for p_enum in ordered_grahas:
            p_pos = transit_chart.planets[p_enum]
            p_name = p_enum.value
            glyph = PLANET_GLYPHS.get(p_name, "✧")

            s_id = p_pos.sign.id
            s_name = ZODIAC_SIGNS[s_id]["english_name"] if sign_mode == "english" else ZODIAC_SIGNS[s_id]["sanskrit_name"]
            s_sans = ZODIAC_SIGNS[s_id]["sanskrit_name"]

            h_lagna = ((s_id - natal_lagna_sign) % 12) + 1
            h_moon = ((s_id - natal_moon_sign) % 12) + 1

            benefic_houses = PHALADEEPIKA_BENEFIC_HOUSES.get(p_enum, set())
            is_benefic = (h_moon in benefic_houses)

            if is_benefic:
                benefic_count += 1
                status_str = "Auspicious (Benefic)"
            else:
                challenging_count += 1
                status_str = "Challenging (Sensitive)"

            # Classical phala descriptions
            phala = cls._get_transit_phala(p_enum, h_moon, is_benefic)

            # SAV and BAV bindus
            sav_b = sav_map.get(s_id, 28)
            bav_b = 0
            if p_name in av_report.bhinna:
                p_bhinna = av_report.bhinna[p_name]
                for sd in p_bhinna.signs:
                    if sd.sign_id == s_id:
                        bav_b = sd.raw_bindus
                        break

            # Kaksha subdivision
            deg = p_pos.sign.intra_sign_degree
            k_idx = min(7, max(0, int(deg / 3.75)))
            k_num = k_idx + 1
            k_lord = KAKSHA_LORDS[k_idx]
            k_lord_sans = KAKSHA_LORDS_SANSKRIT[k_idx]

            # Special alerts
            is_special = False
            alert_msg = None
            if p_enum == PlanetEnum.MOON and h_moon == 8:
                is_special = True
                alert_msg = "⚠️ Chandrashtama: Transit Moon in 8th from Janma Rashi. Exercise mental calm and avoid hasty decisions."
            elif p_enum == PlanetEnum.SATURN and h_moon in (12, 1, 2):
                is_special = True
                alert_msg = f"♄ Shani Sade Sati ({sade_sati_phase}): Saturn transiting Janma Rashi axis."
            elif p_enum == PlanetEnum.SATURN and h_moon == 8:
                is_special = True
                alert_msg = "♄ Ashtama Shani: Saturn transiting 8th from Moon. Heightened discipline and health focus advised."

            transits_list.append(
                GocharGrahaDetail(
                    planet=p_name,
                    glyph=glyph,
                    sign_id=s_id,
                    sign_name=s_name,
                    sign_sanskrit=s_sans,
                    intra_sign_degree=round(deg, 4),
                    degree_formatted=p_pos.sign.dms.formatted,
                    nakshatra=p_pos.nakshatra.sanskrit_name,
                    pada=p_pos.nakshatra.pada,
                    is_retrograde=p_pos.is_retrograde,
                    is_combust=p_pos.is_combust,
                    speed=round(p_pos.speed, 4),
                    house_from_lagna=h_lagna,
                    house_from_moon=h_moon,
                    is_benefic_from_moon=is_benefic,
                    classical_status=status_str,
                    transit_phala=phala,
                    sav_bindus=sav_b,
                    bav_bindus=bav_b,
                    kaksha_number=k_num,
                    kaksha_lord=k_lord,
                    kaksha_lord_sanskrit=k_lord_sans,
                    is_special_alert=is_special,
                    alert_message=alert_msg,
                )
            )

        # Build Jupiter and Rahu-Ketu summaries
        jup_detail = next((t for t in transits_list if t.planet == "Jupiter"), None)
        guru_str = (
            f"Jupiter in House {jup_detail.house_from_moon} from Moon ({jup_detail.sign_name}): {jup_detail.transit_phala}"
            if jup_detail else "-"
        )

        rahu_detail = next((t for t in transits_list if t.planet == "Rahu"), None)
        ketu_detail = next((t for t in transits_list if t.planet == "Ketu"), None)
        rk_str = (
            f"Rahu in H{rahu_detail.house_from_moon} ({rahu_detail.sign_name}) • Ketu in H{ketu_detail.house_from_moon} ({ketu_detail.sign_name})"
            if (rahu_detail and ketu_detail) else "-"
        )

        dt_now = transit_chart.utc_datetime
        summary = GocharSummary(
            transit_utc=dt_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            transit_date_formatted=dt_now.strftime("%d %b %Y, %H:%M:%S"),
            natal_moon_sign=ZODIAC_SIGNS[natal_moon_sign]["english_name"] if sign_mode == "english" else ZODIAC_SIGNS[natal_moon_sign]["sanskrit_name"],
            natal_lagna_sign=ZODIAC_SIGNS[natal_lagna_sign]["english_name"] if sign_mode == "english" else ZODIAC_SIGNS[natal_lagna_sign]["sanskrit_name"],
            benefic_count=benefic_count,
            challenging_count=challenging_count,
            sade_sati_phase=sade_sati_phase,
            is_chandrashtama=is_chandrashtama,
            guru_gochar_summary=guru_str,
            rahu_ketu_summary=rk_str,
        )

        return GocharReport(
            summary=summary,
            transits=transits_list,
            transit_chart=transit_chart,
        )

    @classmethod
    def _get_transit_phala(cls, planet: PlanetEnum, h_moon: int, is_benefic: bool) -> str:
        """Classical Phaladeepika Chapter 26 transit effects."""
        phala_map: Dict[PlanetEnum, Dict[int, str]] = {
            PlanetEnum.SUN: {
                3: "Victory, courage, respect from superiors, financial gain",
                6: "Overcoming adversaries, alleviation of debts, robust health",
                10: "Career triumph, elevated social status, administrative recognition",
                11: "Inflow of prosperity, achievement of objectives, domestic joy",
            },
            PlanetEnum.MOON: {
                1: "Joy, nutritious sustenance, sensory pleasures",
                3: "Courage, acquisition of fine garments, good fortune",
                6: "Suppression of adversaries, relief from ailments",
                7: "Honor, companionship, happy alliances",
                10: "Professional respect, successful undertakings",
                11: "Prosperity, joyful reunions with loved ones",
            },
            PlanetEnum.MARS: {
                3: "Triumph over challenges, courage, financial acquisition",
                6: "Complete vanquishing of competitors, energy and drive",
                11: "Material gains, land and property benefits, authority",
            },
            PlanetEnum.MERCURY: {
                2: "Wealth accumulation, sweet speech, scholarly advancement",
                4: "Domestic happiness, academic success, family harmony",
                6: "Success in debates, suppression of opponents, mental brilliance",
                8: "Unexpected gains, scholarly illumination, victory",
                10: "Professional acclaim, business expansion, prestige",
                11: "Financial growth, joyous celebration, thriving friendships",
            },
            PlanetEnum.JUPITER: {
                2: "Wealth and prosperity, family expansion, sweet speech",
                5: "Birth of noble progeny, intellectual honors, divine grace",
                7: "Marital happiness, auspicious partnerships, respected standing",
                9: "Spiritual pilgrimage, luck, patron support, righteous acts",
                11: "Supreme wealth, honors, fulfillment of deep ambitions",
            },
            PlanetEnum.VENUS: {
                1: "Sensory bliss, fragrance, fine apparel, romantic happiness",
                2: "Financial prosperity, sweet diet, domestic bliss",
                3: "Courage, artistic achievements, pleasant short journeys",
                4: "Domestic comfort, vehicle acquisition, maternal happiness",
                5: "Romantic joy, creative inspiration, happiness from children",
                8: "Gifts, unexpected comfort, sensual gratification",
                9: "Fortune, righteous inclinations, joyous celebrations",
                11: "Financial gains, social prestige, romantic delight",
                12: "Expenditure on noble luxuries, peaceful sleep, pleasures",
            },
            PlanetEnum.SATURN: {
                3: "Valor, freedom from foes, unexpected financial rewards",
                6: "Total destruction of opposition, robust recovery, authority",
                11: "Enduring prosperity, leadership honors, mastery of enterprises",
            },
            PlanetEnum.RAHU: {
                3: "Unflinching bravery, defeat of adversaries, worldly acclaim",
                6: "Freedom from obstacles, monetary gains, high stamina",
                10: "Professional dynamism, unconventional success",
                11: "Abundant worldly gains, foreign connections, honors",
            },
            PlanetEnum.KETU: {
                3: "Courage, spiritual determination, triumph over obstacles",
                6: "Victory over internal and external adversaries, relief",
                10: "Renown, intense focus on karmic duty",
                11: "Spiritual elevation, unexpected wealth, detachment from trivialities",
            },
        }

        specific = phala_map.get(planet, {}).get(h_moon)
        if specific:
            return specific
        if is_benefic:
            return f"Harmonious transit in house {h_moon} from Janma Rashi fostering positive momentum."
        return f"Sensitive transit in house {h_moon} from Janma Rashi; demands patience, prudence, and steady effort."
