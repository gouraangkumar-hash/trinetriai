"""Classical Parashari Functional Nature Engine (Brihat Parashara Hora Shastra Chapter 34).

Evaluates the functional beneficence or maleficence of planets for all 12 Lagnas:
1. Yogakaraka: Single planet simultaneously owning a Kendra (1, 4, 7, 10) and a Trikona (5, 9).
2. Functional Benefics (Shubha Grahas): Trikona lords (1, 5, 9), natural benefics without Kendradhipati Dosha.
3. Functional Malefics (Ashubha / Papi Grahas): Trishadaya lords (3, 6, 11), 8th and 12th lords under Parashari rules.
4. Maraka Lords (Death/Vulnerability Inflicting): Lords of 2nd and 7th houses.
5. Badhaka Lord & Badhaka Sthana (Obstruction Principle):
   - Movable Lagnas (Chara: Aries, Cancer, Libra, Capricorn) -> 11th House & Lord
   - Fixed Lagnas (Sthira: Taurus, Leo, Scorpio, Aquarius) -> 9th House & Lord
   - Dual Lagnas (Dvisvabhava: Gemini, Virgo, Sagittarius, Pisces) -> 7th House & Lord
6. Kendradhipati Dosha: Natural benefics owning kendras lose pure beneficence unless co-ruling a trikona.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from core.constants import PlanetEnum, ZODIAC_SIGNS
from schemas.models import UnifiedChartData


class FunctionalNatureEnum(str, Enum):
    YOGAKARAKA = "Yogakaraka"
    FUNCTIONAL_BENEFIC = "Functional Benefic"
    NEUTRAL = "Neutral"
    FUNCTIONAL_MALEFIC = "Functional Malefic"
    MARAKA = "Maraka"


class PlanetFunctionalProfile(BaseModel):
    """Detailed functional role of a graha for the chart's specific Ascendant (Lagna)."""
    planet: str
    houses_ruled: List[int] = Field(default_factory=list)
    is_yogakaraka: bool = False
    is_maraka: bool = False
    is_badhaka: bool = False
    has_kendradhipati_dosha: bool = False
    primary_role: FunctionalNatureEnum = FunctionalNatureEnum.NEUTRAL
    role_sanskrit: str = "सम"
    role_description: str = ""
    badges: List[str] = Field(default_factory=list)


class FunctionalReport(BaseModel):
    """Complete chart functional nature assessment according to BPHS Chapter 34."""
    lagna_sign_id: int
    lagna_sign_name: str
    lagna_modality: str  # Movable, Fixed, Dual
    badhaka_house: int
    badhaka_lord: str
    yogakaraka_planets: List[str] = Field(default_factory=list)
    maraka_planets: List[str] = Field(default_factory=list)
    profiles: Dict[str, PlanetFunctionalProfile] = Field(default_factory=dict)


# Canonical BPHS Chapter 34 Lagna-wise Rulership & Functional Nature Table
# Format: lagna_id -> {planet: (primary_role, role_sanskrit, description, is_yogakaraka, is_maraka)}
BPHS_CH34_RULES = {
    1: {  # Aries (Mesha) - Movable. Badhaka = 11th (Saturn)
        PlanetEnum.SUN: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "शुभ (Trikona Lord)", "5th house Trikona ruler; auspicious intelligence and dharma.", False, False),
        PlanetEnum.MOON: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "शुभ (Kendra Lord)", "4th house Kendra ruler; mother, happiness, and mental peace.", False, False),
        PlanetEnum.MARS: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "लग्नेश (Lagna Lord)", "1st & 8th lord; moolatrikona in 1st house confers vitality; protects life.", False, False),
        PlanetEnum.MERCURY: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अशुभ (Trishadaya Lord)", "3rd & 6th lord; pure Trishadaya functional malefic; obstacles and conflicts.", False, False),
        PlanetEnum.JUPITER: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "भाग्येश (Bhagyesh)", "9th & 12th lord; moolatrikona in 9th house yields supreme auspiciousness.", False, False),
        PlanetEnum.VENUS: (FunctionalNatureEnum.MARAKA, "मारक (Maraka Lord)", "2nd & 7th lord; prime Maraka ruler and natural enemy of Mars.", False, True),
        PlanetEnum.SATURN: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "बाधक / त्रिषडाय", "10th & 11th lord; Badhaka lord (11th) for movable sign; creates impediments.", False, False),
        PlanetEnum.RAHU: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "पाप", "Shadow planet acting through dispositor; malefic propensity for Aries.", False, False),
        PlanetEnum.KETU: (FunctionalNatureEnum.NEUTRAL, "तटस्थ / मोक्ष", "Spiritualizer; acts through Mars/Jupiter dispositors.", False, False),
    },
    2: {  # Taurus (Vrishabha) - Fixed. Badhaka = 9th (Saturn)
        PlanetEnum.SUN: (FunctionalNatureEnum.NEUTRAL, "सम (Kendra Lord)", "4th house Kendra ruler; natural friend to Lagna lord Venus.", False, False),
        PlanetEnum.MOON: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अशुभ (3rd Lord)", "3rd house Trishadaya ruler; short journeys and efforts.", False, False),
        PlanetEnum.MARS: (FunctionalNatureEnum.MARAKA, "मारक (Maraka Lord)", "7th & 12th lord; vital Maraka planet.", False, True),
        PlanetEnum.MERCURY: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "शुभ (Trikona Lord)", "2nd & 5th lord; 5th Trikona confers wealth and education.", False, False),
        PlanetEnum.JUPITER: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अति अशुभ", "8th & 11th lord; Trishadaya + Randhra lord; prime malefic for Taurus.", False, False),
        PlanetEnum.VENUS: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "लग्नेश (Lagna Lord)", "1st & 6th lord; 1st house lordship overrides 6th house blemish.", False, False),
        PlanetEnum.SATURN: (FunctionalNatureEnum.YOGAKARAKA, "योगकारक (Yogakaraka)", "9th Trikona & 10th Kendra ruler; supreme Yogakaraka for Taurus.", True, False),
        PlanetEnum.RAHU: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "शुभ (Co-ruler)", "Acts through Venus and Saturn; favorable in Kendra/Trikona.", False, False),
        PlanetEnum.KETU: (FunctionalNatureEnum.NEUTRAL, "तटस्थ", "Acts through dispositors; spiritual detachment.", False, False),
    },
    3: {  # Gemini (Mithuna) - Dual. Badhaka = 7th (Jupiter)
        PlanetEnum.SUN: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अशुभ (3rd Lord)", "3rd house Upachaya ruler; aggression and self-effort.", False, False),
        PlanetEnum.MOON: (FunctionalNatureEnum.MARAKA, "मारक (2nd Lord)", "2nd house Maraka ruler; liquid wealth and family speech.", False, True),
        PlanetEnum.MARS: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अति अशुभ (Trishadaya)", "6th & 11th lord; acute functional malefic for Gemini.", False, False),
        PlanetEnum.MERCURY: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "लग्नेश (Lagna Lord)", "1st & 4th lord; Lagna lord dominance cancels Kendradhipati Dosha.", False, False),
        PlanetEnum.JUPITER: (FunctionalNatureEnum.MARAKA, "केन्द्राधिपति / मारक", "7th & 10th lord; dual Kendra dosha, prime Maraka and Badhaka.", False, True),
        PlanetEnum.VENUS: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "शुभ (5th Lord)", "5th Trikona & 12th lord; supreme intellect and creative fruition.", False, False),
        PlanetEnum.SATURN: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "भाग्येश (Bhagyesh)", "8th & 9th lord; moolatrikona in 9th house confers fortune.", False, False),
        PlanetEnum.RAHU: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "शुभ (Mitra)", "Exalted/Friendly in Gemini; highly intellectual and opportunistic.", False, False),
        PlanetEnum.KETU: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "पाप", "Adverse to Mercury's rational intellect unless well-aspected.", False, False),
    },
    4: {  # Cancer (Karka) - Movable. Badhaka = 11th (Venus)
        PlanetEnum.SUN: (FunctionalNatureEnum.MARAKA, "धन / मारक (2nd Lord)", "2nd house Maraka ruler; friendly royal dispositor of soul.", False, True),
        PlanetEnum.MOON: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "लग्नेश (Lagna Lord)", "1st house Lagnesh; core mind and constitutional vitality.", False, False),
        PlanetEnum.MARS: (FunctionalNatureEnum.YOGAKARAKA, "परम योगकारक", "5th Trikona & 10th Kendra ruler; quintessential Yogakaraka.", True, False),
        PlanetEnum.MERCURY: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अशुभ (3rd & 12th)", "3rd & 12th lord; expendable efforts and financial leakage.", False, False),
        PlanetEnum.JUPITER: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "भाग्येश (9th Lord)", "6th & 9th lord; moolatrikona in 9th house Bestows dharma and grace.", False, False),
        PlanetEnum.VENUS: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "बाधक / त्रिषडाय", "4th & 11th lord; Badhaka (11th) for movable Cancer; creates worldly obstructions.", False, False),
        PlanetEnum.SATURN: (FunctionalNatureEnum.MARAKA, "मारक (7th & 8th)", "7th & 8th lord; prime Maraka and heavy karmic taskmaster.", False, True),
        PlanetEnum.RAHU: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "पाप", "Challenging for sensitive emotional Cancer lunar psyche.", False, False),
        PlanetEnum.KETU: (FunctionalNatureEnum.NEUTRAL, "तटस्थ", "Spiritual liberation catalyst for Cancerians.", False, False),
    },
    5: {  # Leo (Simha) - Fixed. Badhaka = 9th (Mars)
        PlanetEnum.SUN: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "लग्नेश (Lagna Lord)", "1st house sovereign ruler; vitality, leadership, and nobility.", False, False),
        PlanetEnum.MOON: (FunctionalNatureEnum.NEUTRAL, "व्ययेश (12th Lord)", "12th house Moksha ruler; neutral disposition.", False, False),
        PlanetEnum.MARS: (FunctionalNatureEnum.YOGAKARAKA, "योगकारक (4th & 9th)", "4th Kendra & 9th Trikona ruler; supreme Yogakaraka (also Badhaka for fixed sign).", True, False),
        PlanetEnum.MERCURY: (FunctionalNatureEnum.MARAKA, "धन / मारक (2nd & 11th)", "2nd & 11th house ruler; wealth builder with secondary Maraka capacity.", False, True),
        PlanetEnum.JUPITER: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "पंचमेश (5th & 8th)", "5th Trikona & 8th lord; moolatrikona in 5th yields genius and intuition.", False, False),
        PlanetEnum.VENUS: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अशुभ (3rd & 10th)", "3rd & 10th lord; enemy of Sun; creates professional friction.", False, False),
        PlanetEnum.SATURN: (FunctionalNatureEnum.MARAKA, "शत्रु / मारक (6th & 7th)", "6th & 7th lord; formidable enemy to Sun and prime Maraka.", False, True),
        PlanetEnum.RAHU: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "शत्रु", "Eclipses Sun; produces ungrounded ambition and rebellion.", False, False),
        PlanetEnum.KETU: (FunctionalNatureEnum.NEUTRAL, "तटस्थ", "Spiritual warrior energy aligned with Sun's fiery core.", False, False),
    },
    6: {  # Virgo (Kanya) - Dual. Badhaka = 7th (Jupiter)
        PlanetEnum.SUN: (FunctionalNatureEnum.NEUTRAL, "व्ययेश (12th Lord)", "12th house ruler; expenditure and foreign connection.", False, False),
        PlanetEnum.MOON: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "त्रिषडाय (11th Lord)", "11th house Trishadaya lord; desire fulfillment with material blemish.", False, False),
        PlanetEnum.MARS: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अति अशुभ (3rd & 8th)", "3rd & 8th house ruler; most destructive functional malefic for Virgo.", False, False),
        PlanetEnum.MERCURY: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "लग्नेश (1st & 10th)", "1st & 10th lord; Lagnesh status eliminates Kendradhipati Dosha.", False, False),
        PlanetEnum.JUPITER: (FunctionalNatureEnum.MARAKA, "केन्द्राधिपति / मारक", "4th & 7th lord; dual Kendra dosha, prime Maraka and Badhaka.", False, True),
        PlanetEnum.VENUS: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "भाग्येश (2nd & 9th)", "2nd & 9th lord; 9th Trikona lordship Bestows fortune and grace.", False, False),
        PlanetEnum.SATURN: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "पंचमेश (5th & 6th)", "5th Trikona & 6th lord; friendly strategist and hard-won victory.", False, False),
        PlanetEnum.RAHU: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "मित्र", "Co-rules Virgo; grants exceptional analytical prowess.", False, False),
        PlanetEnum.KETU: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "पाप", "Creates detachment and critical overthinking.", False, False),
    },
    7: {  # Libra (Tula) - Movable. Badhaka = 11th (Sun)
        PlanetEnum.SUN: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "बाधक (11th Lord)", "11th house Badhaka lord for movable Libra; creates egoic obstructions.", False, False),
        PlanetEnum.MOON: (FunctionalNatureEnum.NEUTRAL, "कर्मेश (10th Lord)", "10th house Kendra ruler; public status and career sensitivity.", False, False),
        PlanetEnum.MARS: (FunctionalNatureEnum.MARAKA, "परम मारक (2nd & 7th)", "2nd & 7th lord; dual Maraka house ownership.", False, True),
        PlanetEnum.MERCURY: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "भाग्येश (9th & 12th)", "9th Trikona & 12th lord; auspicious fortune and higher studies.", False, False),
        PlanetEnum.JUPITER: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अति अशुभ (3rd & 6th)", "3rd & 6th lord; Trishadaya malefic creating litigation and debt.", False, False),
        PlanetEnum.VENUS: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "लग्नेश (1st & 8th)", "1st & 8th lord; moolatrikona in 1st house confers beauty and charm.", False, False),
        PlanetEnum.SATURN: (FunctionalNatureEnum.YOGAKARAKA, "परम योगकारक (4th & 5th)", "4th Kendra & 5th Trikona ruler; supreme Yogakaraka for Libra.", True, False),
        PlanetEnum.RAHU: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "मित्र", "Friendly to Venus and Saturn; bestows diplomacy and trade success.", False, False),
        PlanetEnum.KETU: (FunctionalNatureEnum.NEUTRAL, "तटस्थ", "Detachment from worldly luxury and relationships.", False, False),
    },
    8: {  # Scorpio (Vrishchika) - Fixed. Badhaka = 9th (Moon)
        PlanetEnum.SUN: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "कर्मेश (10th Lord)", "10th house Kendra ruler; royal patron of authority and power.", False, False),
        PlanetEnum.MOON: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "भाग्येश / बाधक (9th)", "9th Trikona lord (also Badhaka for fixed Scorpio); deep emotional dharma.", False, False),
        PlanetEnum.MARS: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "लग्नेश (1st & 6th)", "1st & 6th lord; 1st house lordship overrides 6th house blemish.", False, False),
        PlanetEnum.MERCURY: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अति अशुभ (8th & 11th)", "8th & 11th house ruler; most dangerous functional malefic for Scorpio.", False, False),
        PlanetEnum.JUPITER: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "पंचमेश (2nd & 5th)", "2nd & 5th lord; 5th Trikona Bestows exceptional intellect and wealth.", False, False),
        PlanetEnum.VENUS: (FunctionalNatureEnum.MARAKA, "मारक (7th & 12th)", "7th & 12th lord; prime Maraka and source of emotional turbulence.", False, True),
        PlanetEnum.SATURN: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अशुभ (3rd & 4th)", "3rd & 4th lord; enemy to Mars; brings heavy burdens and labor.", False, False),
        PlanetEnum.RAHU: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "पाप", "Debilitated in Scorpio; triggers paranoia and sudden upheavals.", False, False),
        PlanetEnum.KETU: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "शुभ (Exalted)", "Exalted in Scorpio; supreme mystical and occult insight.", False, False),
    },
    9: {  # Sagittarius (Dhanu) - Dual. Badhaka = 7th (Mercury)
        PlanetEnum.SUN: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "भाग्येश (9th Lord)", "9th house Trikona ruler; supreme patron of righteousness and truth.", False, False),
        PlanetEnum.MOON: (FunctionalNatureEnum.NEUTRAL, "अष्टमेश (8th Lord)", "8th house ruler; friendly to Jupiter; transforms through occult wisdom.", False, False),
        PlanetEnum.MARS: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "पंचमेश (5th & 12th)", "5th Trikona & 12th lord; creative vitality and spiritual courage.", False, False),
        PlanetEnum.MERCURY: (FunctionalNatureEnum.MARAKA, "केन्द्राधिपति / मारक", "7th & 10th lord; Kendradhipati Dosha, prime Maraka and Badhaka.", False, True),
        PlanetEnum.JUPITER: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "लग्नेश (1st & 4th)", "1st & 4th lord; Lagna lordship eliminates Kendradhipati Dosha.", False, False),
        PlanetEnum.VENUS: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अति अशुभ (6th & 11th)", "6th & 11th Trishadaya lord; foremost enemy to Jupiter.", False, False),
        PlanetEnum.SATURN: (FunctionalNatureEnum.MARAKA, "मारक (2nd & 3rd)", "2nd Maraka & 3rd Upachaya lord; material discipline.", False, True),
        PlanetEnum.RAHU: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "पाप", "Foreign philosophies and unrighteous distractions.", False, False),
        PlanetEnum.KETU: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "शुभ", "Auspicious in Jupiter's fiery sign; deep spiritual realization.", False, False),
    },
    10: {  # Capricorn (Makara) - Movable. Badhaka = 11th (Mars)
        PlanetEnum.SUN: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अष्टमेश (8th Lord)", "8th house ruler; arch-enemy of Saturn; brings structural obstacles.", False, False),
        PlanetEnum.MOON: (FunctionalNatureEnum.MARAKA, "मारक (7th Lord)", "7th house Maraka ruler; emotional partnerships.", False, True),
        PlanetEnum.MARS: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "बाधक / मारक (4th & 11th)", "4th Kendra & 11th Badhaka ruler; creates domestic and physical friction.", False, False),
        PlanetEnum.MERCURY: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "भाग्येश (6th & 9th)", "6th & 9th lord; 9th Trikona Bestows executive intellect and success.", False, False),
        PlanetEnum.JUPITER: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अति अशुभ (3rd & 12th)", "3rd & 12th house ruler; unnecessary expenses and losses.", False, False),
        PlanetEnum.VENUS: (FunctionalNatureEnum.YOGAKARAKA, "परम योगकारक (5th & 10th)", "5th Trikona & 10th Kendra ruler; supreme Yogakaraka for Capricorn.", True, False),
        PlanetEnum.SATURN: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "लग्नेश (1st & 2nd)", "1st Lagna & 2nd Dhana lord; foundations of perseverance and longevity.", False, False),
        PlanetEnum.RAHU: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "मित्र", "Friendly to Saturn; grants ambition and organizational dominance.", False, False),
        PlanetEnum.KETU: (FunctionalNatureEnum.NEUTRAL, "तटस्थ", "Detachment from societal structures.", False, False),
    },
    11: {  # Aquarius (Kumbha) - Fixed. Badhaka = 9th (Venus)
        PlanetEnum.SUN: (FunctionalNatureEnum.MARAKA, "मारक (7th Lord)", "7th house Maraka ruler; ego encounters in partnerships.", False, True),
        PlanetEnum.MOON: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "षष्ठेश (6th Lord)", "6th house ruler; health challenges and mental agitation.", False, False),
        PlanetEnum.MARS: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अशुभ (3rd & 10th)", "3rd & 10th house ruler; aggressive professional conflicts.", False, False),
        PlanetEnum.MERCURY: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "पंचमेश (5th & 8th)", "5th Trikona & 8th lord; profound research intellect and intuition.", False, False),
        PlanetEnum.JUPITER: (FunctionalNatureEnum.MARAKA, "धन / मारक (2nd & 11th)", "2nd & 11th house ruler; financial accumulator with secondary Maraka role.", False, True),
        PlanetEnum.VENUS: (FunctionalNatureEnum.YOGAKARAKA, "योगकारक / बाधक (4th & 9th)", "4th Kendra & 9th Trikona ruler; supreme Yogakaraka (also Badhaka for fixed Aquarius).", True, False),
        PlanetEnum.SATURN: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "लग्नेश (1st & 12th)", "1st Lagna & 12th Moksha lord; humanitarian wisdom and endurance.", False, False),
        PlanetEnum.RAHU: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "सह-लग्नेश", "Co-ruler of Aquarius; extraordinary visionary and scientific intellect.", False, False),
        PlanetEnum.KETU: (FunctionalNatureEnum.NEUTRAL, "तटस्थ", "Universal consciousness and ego-dissolution.", False, False),
    },
    12: {  # Pisces (Meena) - Dual. Badhaka = 7th (Mercury)
        PlanetEnum.SUN: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "षष्ठेश (6th Lord)", "6th house ruler; health vulnerabilities and systemic disputes.", False, False),
        PlanetEnum.MOON: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "पंचमेश (5th Lord)", "5th house Trikona ruler; devotional heart, intuition, and children.", False, False),
        PlanetEnum.MARS: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "भाग्येश (2nd & 9th)", "2nd & 9th lord; 9th Trikona lordship Bestows immense fortune and valor.", False, False),
        PlanetEnum.MERCURY: (FunctionalNatureEnum.MARAKA, "केन्द्राधिपति / मारक", "4th & 7th lord; Kendradhipati Dosha, prime Maraka and Badhaka.", False, True),
        PlanetEnum.JUPITER: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "लग्नेश (1st & 10th)", "1st & 10th lord; Lagnesh status cancels Kendradhipati Dosha.", False, False),
        PlanetEnum.VENUS: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अति अशुभ (3rd & 8th)", "3rd & 8th house ruler; most dangerous functional malefic for Pisces.", False, False),
        PlanetEnum.SATURN: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "अशुभ (11th & 12th)", "11th Trishadaya & 12th Vyaya lord; discipline through isolation.", False, False),
        PlanetEnum.RAHU: (FunctionalNatureEnum.FUNCTIONAL_MALEFIC, "पाप", "Illusion and psychic vulnerabilities in the cosmic ocean.", False, False),
        PlanetEnum.KETU: (FunctionalNatureEnum.FUNCTIONAL_BENEFIC, "मोक्षकारक", "Exalted in watery Pisces; ultimate liberation and spiritual enlightenment.", False, False),
    },
}


class FunctionalNatureEngine:
    """Evaluates BPHS Chapter 34 Functional Nature, Yogakaraka, Maraka, and Badhaka for any chart."""

    @classmethod
    def evaluate(cls, chart: UnifiedChartData) -> FunctionalReport:
        asc_sign_id = chart.angles.ascendant_sign.id
        sign_info = ZODIAC_SIGNS.get(asc_sign_id, {})
        modality = sign_info.get("modality", "Movable")
        sign_name = chart.angles.ascendant_sign.sanskrit_name

        # Badhaka House calculation based on Lagna Modality:
        # Movable (Chara) -> 11th House
        # Fixed (Sthira) -> 9th House
        # Dual (Dvisvabhava) -> 7th House
        if modality == "Movable":
            badhaka_house = 11
        elif modality == "Fixed":
            badhaka_house = 9
        else:
            badhaka_house = 7

        # Identify sign on Badhaka house and its lord
        badhaka_sign_id = ((asc_sign_id + badhaka_house - 2) % 12) + 1
        badhaka_lord_enum = ZODIAC_SIGNS[badhaka_sign_id]["lord"]
        badhaka_lord = badhaka_lord_enum.value

        # Calculate houses owned by each planet from Lagna
        house_rulers: Dict[PlanetEnum, List[int]] = {p: [] for p in PlanetEnum}
        for h in range(1, 13):
            s_id = ((asc_sign_id + h - 2) % 12) + 1
            lord = ZODIAC_SIGNS[s_id]["lord"]
            house_rulers[lord].append(h)

        lagna_rules = BPHS_CH34_RULES.get(asc_sign_id, {})
        profiles: Dict[str, PlanetFunctionalProfile] = {}
        yogakarakas: List[str] = []
        marakas: List[str] = []

        classical_planets = [
            PlanetEnum.SUN, PlanetEnum.MOON, PlanetEnum.MARS, PlanetEnum.MERCURY,
            PlanetEnum.JUPITER, PlanetEnum.VENUS, PlanetEnum.SATURN, PlanetEnum.RAHU, PlanetEnum.KETU
        ]

        for p_enum in classical_planets:
            rule_tuple = lagna_rules.get(
                p_enum,
                (FunctionalNatureEnum.NEUTRAL, "सम", "Neutral disposition.", False, False)
            )
            prim_role, sanskrit, desc, is_yk, is_mar = rule_tuple
            is_badh = (p_enum == badhaka_lord_enum)
            owned_houses = house_rulers.get(p_enum, [])

            # Detect Kendradhipati Dosha: Natural benefics (Ju, Ve, Me, Mo) owning kendras (4, 7, 10)
            # without trikona (1, 5, 9) lordship
            has_kd = False
            if p_enum in (PlanetEnum.JUPITER, PlanetEnum.VENUS, PlanetEnum.MERCURY):
                owns_kendra = any(h in (4, 7, 10) for h in owned_houses)
                owns_trikona = any(h in (1, 5, 9) for h in owned_houses)
                if owns_kendra and not owns_trikona:
                    has_kd = True

            badges: List[str] = []
            if is_yk:
                badges.append("Yogakaraka")
                yogakarakas.append(p_enum.value)
            elif prim_role == FunctionalNatureEnum.FUNCTIONAL_BENEFIC:
                badges.append("Benefic")
            elif prim_role == FunctionalNatureEnum.FUNCTIONAL_MALEFIC:
                badges.append("Malefic")

            if is_mar:
                badges.append("Maraka")
                marakas.append(p_enum.value)

            if is_badh:
                badges.append("Badhaka")

            if has_kd:
                badges.append("Kendra Dosha")

            profiles[p_enum.value] = PlanetFunctionalProfile(
                planet=p_enum.value,
                houses_ruled=owned_houses,
                is_yogakaraka=is_yk,
                is_maraka=is_mar,
                is_badhaka=is_badh,
                has_kendradhipati_dosha=has_kd,
                primary_role=prim_role,
                role_sanskrit=sanskrit,
                role_description=desc,
                badges=badges,
            )

        return FunctionalReport(
            lagna_sign_id=asc_sign_id,
            lagna_sign_name=sign_name,
            lagna_modality=modality,
            badhaka_house=badhaka_house,
            badhaka_lord=badhaka_lord,
            yogakaraka_planets=yogakarakas,
            maraka_planets=marakas,
            profiles=profiles,
        )
