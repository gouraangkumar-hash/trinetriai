"""Classical Vedic Planetary Dignity Engine (Brihat Parashara Hora Shastra Standards).

Evaluates planetary dignity states:
- Exalted (Uccha / Param Uccha)
- Debilitated (Neecha / Param Neecha)
- Moolatrikona
- Own Sign (Swa Kshetra)
- Neutral / Sama
Integrates Neechabhanga cancellation recognition.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from core.constants import PlanetEnum, ZODIAC_SIGNS


# =============================================================================
# Classical Dignity Tables (BPHS Canonical Rules)
# =============================================================================

# Zodiac Sign IDs (1 = Mesha / Aries, 12 = Meena / Pisces)
EXALTATION_SIGNS: Dict[PlanetEnum, int] = {
    PlanetEnum.SUN: 1,       # Aries / Mesha
    PlanetEnum.MOON: 2,      # Taurus / Vrishabha
    PlanetEnum.MARS: 10,     # Capricorn / Makara
    PlanetEnum.MERCURY: 6,   # Virgo / Kanya
    PlanetEnum.JUPITER: 4,   # Cancer / Karka
    PlanetEnum.VENUS: 12,    # Pisces / Meena
    PlanetEnum.SATURN: 7,    # Libra / Tula
    PlanetEnum.RAHU: 2,      # Taurus / Vrishabha (Classical Parashari)
    PlanetEnum.KETU: 8,      # Scorpio / Vrishchika (Classical Parashari)
}

DEBILITATION_SIGNS: Dict[PlanetEnum, int] = {
    PlanetEnum.SUN: 7,       # Libra / Tula
    PlanetEnum.MOON: 8,      # Scorpio / Vrishchika
    PlanetEnum.MARS: 4,      # Cancer / Karka
    PlanetEnum.MERCURY: 12,  # Pisces / Meena
    PlanetEnum.JUPITER: 10,  # Capricorn / Makara
    PlanetEnum.VENUS: 6,     # Virgo / Kanya
    PlanetEnum.SATURN: 1,    # Aries / Mesha
    PlanetEnum.RAHU: 8,      # Scorpio / Vrishchika
    PlanetEnum.KETU: 2,      # Taurus / Vrishabha
}

OWN_SIGNS: Dict[PlanetEnum, List[int]] = {
    PlanetEnum.SUN: [5],           # Leo
    PlanetEnum.MOON: [4],          # Cancer
    PlanetEnum.MARS: [1, 8],       # Aries, Scorpio
    PlanetEnum.MERCURY: [3, 6],    # Gemini, Virgo
    PlanetEnum.JUPITER: [9, 12],   # Sagittarius, Pisces
    PlanetEnum.VENUS: [2, 7],      # Taurus, Libra
    PlanetEnum.SATURN: [10, 11],   # Capricorn, Aquarius
    PlanetEnum.RAHU: [11],         # Aquarius (Classical co-ruler)
    PlanetEnum.KETU: [8],          # Scorpio (Classical co-ruler)
}

# Exact Deep Exaltation & Debilitation Degrees (BPHS Ch. 3, Sloka 49-50)
DEEP_EXALTATION_DEGREES: Dict[PlanetEnum, float] = {
    PlanetEnum.SUN: 10.0,       # 10° Aries
    PlanetEnum.MOON: 3.0,       # 3° Taurus
    PlanetEnum.MARS: 28.0,      # 28° Capricorn
    PlanetEnum.MERCURY: 15.0,   # 15° Virgo
    PlanetEnum.JUPITER: 5.0,    # 5° Cancer
    PlanetEnum.VENUS: 27.0,     # 27° Pisces
    PlanetEnum.SATURN: 20.0,    # 20° Libra
    PlanetEnum.RAHU: 15.0,      # 15° Taurus
    PlanetEnum.KETU: 15.0,      # 15° Scorpio
}

DEEP_DEBILITATION_DEGREES: Dict[PlanetEnum, float] = {
    PlanetEnum.SUN: 10.0,       # 10° Libra
    PlanetEnum.MOON: 3.0,       # 3° Scorpio
    PlanetEnum.MARS: 28.0,      # 28° Cancer
    PlanetEnum.MERCURY: 15.0,   # 15° Pisces
    PlanetEnum.JUPITER: 5.0,    # 5° Capricorn
    PlanetEnum.VENUS: 27.0,     # 27° Virgo
    PlanetEnum.SATURN: 20.0,    # 20° Aries
    PlanetEnum.RAHU: 15.0,      # 15° Scorpio
    PlanetEnum.KETU: 15.0,      # 15° Taurus
}

# Moolatrikona Sign & Degree Ranges (BPHS)
# Tuple: (Sign ID, Min Degree, Max Degree)
MOOLATRIKONA_RANGES: Dict[PlanetEnum, Tuple[int, float, float]] = {
    PlanetEnum.SUN: (5, 0.0, 20.0),         # Leo 0°-20°
    PlanetEnum.MOON: (2, 3.0, 30.0),        # Taurus 3°-30°
    PlanetEnum.MARS: (1, 0.0, 12.0),        # Aries 0°-12°
    PlanetEnum.MERCURY: (6, 15.0, 20.0),    # Virgo 15°-20°
    PlanetEnum.JUPITER: (9, 0.0, 10.0),     # Sagittarius 0°-10°
    PlanetEnum.VENUS: (7, 0.0, 15.0),       # Libra 0°-15°
    PlanetEnum.SATURN: (11, 0.0, 20.0),     # Aquarius 0°-20°
}


class DignityState(str, Enum):
    EXALTED = "Exalted"
    DEBILITATED = "Debilitated"
    MOOLATRIKONA = "Moolatrikona"
    OWN_SIGN = "Own Sign"
    NEUTRAL = "Neutral"


class PlanetDignityReport(BaseModel):
    """Structured report of a planet's classical sign dignity."""
    planet: str
    sign_id: int
    sign_name: str
    degree_in_sign: float
    is_exalted: bool
    is_debilitated: bool
    is_own_sign: bool
    is_moolatrikona: bool
    dignity: DignityState
    dignity_label: str
    dignity_short: str
    dignity_sanskrit: str
    dignity_desc: str
    has_neechabhanga: bool = False
    neechabhanga_notes: str = ""


class DignityEngine:
    """Evaluates planetary dignities according to classical BPHS rules."""

    @classmethod
    def evaluate_planet_dignity(
        cls,
        planet: PlanetEnum,
        sign_id: int,
        sign_name: str,
        degree_in_sign: float,
        neechabhanga_planets: Optional[Set[str]] = None,
    ) -> PlanetDignityReport:
        """Evaluates whether a planet is Exalted, Debilitated, Moolatrikona, or in Own Sign."""
        p_val = planet.value
        nb_planets = neechabhanga_planets or set()
        has_nb = p_val in nb_planets

        is_ex = bool(sign_id == EXALTATION_SIGNS.get(planet))
        is_deb = bool(sign_id == DEBILITATION_SIGNS.get(planet))

        # Check Moolatrikona range
        is_mt = False
        if planet in MOOLATRIKONA_RANGES:
            mt_sign, mt_min, mt_max = MOOLATRIKONA_RANGES[planet]
            if sign_id == mt_sign and mt_min <= degree_in_sign <= mt_max:
                is_mt = True

        # Check Own Sign
        is_own = bool(sign_id in OWN_SIGNS.get(planet, []))

        # Priority resolution
        if is_ex:
            deep_deg = DEEP_EXALTATION_DEGREES.get(planet, 0.0)
            is_deep = abs(degree_in_sign - deep_deg) <= 3.0
            deep_note = f" (Near Deep Exaltation point {deep_deg:g}°)" if is_deep else f" (Deep point {deep_deg:g}°)"
            return PlanetDignityReport(
                planet=p_val,
                sign_id=sign_id,
                sign_name=sign_name,
                degree_in_sign=round(degree_in_sign, 2),
                is_exalted=True,
                is_debilitated=False,
                is_own_sign=is_own,
                is_moolatrikona=is_mt,
                dignity=DignityState.EXALTED,
                dignity_label="Exalted (Uccha)",
                dignity_short="Ex",
                dignity_sanskrit="उच्च (Uccha)",
                dignity_desc=f"Exalted in {sign_name}{deep_note}",
                has_neechabhanga=False,
            )

        if is_deb:
            deep_deg = DEEP_DEBILITATION_DEGREES.get(planet, 0.0)
            is_deep = abs(degree_in_sign - deep_deg) <= 3.0
            deep_note = f" (Near Deep Debilitation point {deep_deg:g}°)" if is_deep else f" (Deep point {deep_deg:g}°)"
            nb_suffix = " — Neechabhanga Cancelled" if has_nb else ""
            return PlanetDignityReport(
                planet=p_val,
                sign_id=sign_id,
                sign_name=sign_name,
                degree_in_sign=round(degree_in_sign, 2),
                is_exalted=False,
                is_debilitated=True,
                is_own_sign=False,
                is_moolatrikona=False,
                dignity=DignityState.DEBILITATED,
                dignity_label="Debilitated (Neecha) [Cancelled]" if has_nb else "Debilitated (Neecha)",
                dignity_short="Deb",
                dignity_sanskrit="नीच (Neecha)",
                dignity_desc=f"Debilitated in {sign_name}{deep_note}{nb_suffix}",
                has_neechabhanga=has_nb,
                neechabhanga_notes="Structural debility cancelled by classical Neechabhanga Raja Yoga rules." if has_nb else "",
            )

        if is_mt:
            return PlanetDignityReport(
                planet=p_val,
                sign_id=sign_id,
                sign_name=sign_name,
                degree_in_sign=round(degree_in_sign, 2),
                is_exalted=False,
                is_debilitated=False,
                is_own_sign=is_own,
                is_moolatrikona=True,
                dignity=DignityState.MOOLATRIKONA,
                dignity_label="Moolatrikona",
                dignity_short="MT",
                dignity_sanskrit="मूलत्रिकोण (Moolatrikona)",
                dignity_desc=f"Moolatrikona dignity in {sign_name}",
                has_neechabhanga=False,
            )

        if is_own:
            return PlanetDignityReport(
                planet=p_val,
                sign_id=sign_id,
                sign_name=sign_name,
                degree_in_sign=round(degree_in_sign, 2),
                is_exalted=False,
                is_debilitated=False,
                is_own_sign=True,
                is_moolatrikona=False,
                dignity=DignityState.OWN_SIGN,
                dignity_label="Own Sign (Swa Kshetra)",
                dignity_short="Own",
                dignity_sanskrit="स्वक्षेत्र (Swa Kshetra)",
                dignity_desc=f"Own sign in {sign_name}",
                has_neechabhanga=False,
            )

        return PlanetDignityReport(
            planet=p_val,
            sign_id=sign_id,
            sign_name=sign_name,
            degree_in_sign=round(degree_in_sign, 2),
            is_exalted=False,
            is_debilitated=False,
            is_own_sign=False,
            is_moolatrikona=False,
            dignity=DignityState.NEUTRAL,
            dignity_label="Neutral (Sama)",
            dignity_short="",
            dignity_sanskrit="सम (Sama)",
            dignity_desc=f"Neutral sign placement in {sign_name}",
            has_neechabhanga=False,
        )
