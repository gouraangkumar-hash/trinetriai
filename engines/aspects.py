"""Classical Parashari Graha Drishti (Planetary Aspects) Engine.

Computes canonical Vedic aspects:
- 100% Full Aspect (Purna Drishti) on the 7th house for all 9 Grahas
- Vishesha Purna Drishti (Special Full Aspects):
  * Mars (Mangal): 4th, 7th, 8th houses
  * Jupiter (Guru): 5th, 7th, 9th houses
  * Saturn (Shani): 3rd, 7th, 10th houses
  * Rahu & Ketu: 5th, 7th, 9th houses
- Graha-to-Graha Aspects with angular distance
- 12 Bhavas (House) Aspect Influences (Benefic vs Malefic tally)
- Mutual Aspects (Paraspara Drishti) and Conjunctions (Yuti)
- Coordinates for North and South Indian visual aspect rays
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from core.constants import PlanetEnum, ZODIAC_SIGNS
from schemas.models import UnifiedChartData


# =============================================================================
# Classical Parashari Aspect Rules
# =============================================================================

# Houses aspected counting inclusively from the planet's house (1-based)
PARASHARI_FULL_ASPECTS: Dict[PlanetEnum, List[int]] = {
    PlanetEnum.SUN:     [7],
    PlanetEnum.MOON:    [7],
    PlanetEnum.MARS:    [4, 7, 8],
    PlanetEnum.MERCURY: [7],
    PlanetEnum.JUPITER: [5, 7, 9],
    PlanetEnum.VENUS:   [7],
    PlanetEnum.SATURN:  [3, 7, 10],
    PlanetEnum.RAHU:    [5, 7, 9],
    PlanetEnum.KETU:    [5, 7, 9],
}

NATURAL_BENEFICS: Set[PlanetEnum] = {
    PlanetEnum.JUPITER,
    PlanetEnum.VENUS,
    PlanetEnum.MERCURY,
    PlanetEnum.MOON,
}

NATURAL_MALEFICS: Set[PlanetEnum] = {
    PlanetEnum.SATURN,
    PlanetEnum.MARS,
    PlanetEnum.RAHU,
    PlanetEnum.KETU,
    PlanetEnum.SUN,
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

# Ray visual styling colors
RAY_COLORS_LIGHT: Dict[str, str] = {
    "Sun": "#B45309",
    "Moon": "#1C1917",
    "Mars": "#B91C1C",
    "Mercury": "#047857",
    "Jupiter": "#CA8A04",
    "Venus": "#92400E",
    "Saturn": "#57534E",
    "Rahu": "#6B21A8",
    "Ketu": "#C2410C",
}

RAY_COLORS_DARK: Dict[str, str] = {
    "Sun": "#FBBF24",
    "Moon": "#F5F2EB",
    "Mars": "#F87171",
    "Mercury": "#34D399",
    "Jupiter": "#FDE047",
    "Venus": "#FCD34D",
    "Saturn": "#D6D3D1",
    "Rahu": "#D8B4FE",
    "Ketu": "#FB923C",
}


# =============================================================================
# Pydantic Schemas
# =============================================================================

class GrahaAspectCast(BaseModel):
    target_house: int = Field(..., ge=1, le=12, description="Target house number (1-12)")
    target_sign_id: int = Field(..., ge=1, le=12, description="Target zodiac sign ID (1-12)")
    target_sign_name: str
    aspect_offset: int = Field(..., description="House offset e.g. 7, 4, 8, 5, 9, 3, 10")
    aspect_type: str = Field(..., description="e.g. '7th (100%)', '4th (Vishesha)'")
    is_special: bool = Field(default=False)
    aspected_planets: List[str] = Field(default_factory=list, description="Planets in target house")


class GrahaAspectReceived(BaseModel):
    from_planet: str
    from_house: int
    aspect_offset: int
    aspect_type: str
    is_benefic: bool


class GrahaAspectDetail(BaseModel):
    planet: str
    glyph: str
    natal_house: int
    natal_sign_id: int
    natal_sign_name: str
    longitude: float
    degree_formatted: str
    is_benefic: bool
    aspects_cast: List[GrahaAspectCast]
    aspects_received: List[GrahaAspectReceived]
    conjunctions: List[str]
    mutual_aspects: List[str]
    summary_badges: List[Dict[str, Any]]
    ray_color_light: str
    ray_color_dark: str


class BhavaAspectDetail(BaseModel):
    house_number: int
    sign_id: int
    sign_name: str
    lord: str
    occupants: List[str]
    benefics_aspecting: List[str]
    malefics_aspecting: List[str]
    total_aspects_count: int
    net_influence: str  # 'Fortified (Benefic)', 'Afflicted (Malefic)', 'Mixed Influences', 'Neutral'


class MutualAspectPair(BaseModel):
    planet1: str
    planet2: str
    relation: str  # e.g. "Opposite 7th-7th", "Mars 4th ↔ Saturn 10th"


class AspectsReport(BaseModel):
    planets_aspects: Dict[str, GrahaAspectDetail]
    bhava_aspects: List[BhavaAspectDetail]
    mutual_aspects: List[MutualAspectPair]
    conjunctions: List[Dict[str, Any]]


def _format_ordinal(n: int) -> str:
    if n == 1:
        return "1st"
    elif n == 2:
        return "2nd"
    elif n == 3:
        return "3rd"
    return f"{n}th"


# =============================================================================
# Aspect Engine Implementation
# =============================================================================

class AspectsEngine:
    """Evaluates canonical Vedic Graha Drishti and Bhava aspects."""

    @classmethod
    def evaluate(cls, chart: UnifiedChartData, sign_mode: str = "sanskrit") -> AspectsReport:
        """Computes all planetary aspects, house aspects, and mutual relationships."""
        asc_sign_id = chart.angles.ascendant_sign.id

        # 1. Map planets to their natal houses (Whole Sign from Ascendant)
        planet_houses: Dict[PlanetEnum, int] = {}
        house_occupants: Dict[int, List[PlanetEnum]] = {h: [] for h in range(1, 13)}

        for p_enum, p_pos in chart.planets.items():
            h = ((p_pos.sign.id - asc_sign_id) % 12) + 1
            planet_houses[p_enum] = h
            house_occupants[h].append(p_enum)

        # 2. Compute Aspects Cast for each planet
        planets_cast_map: Dict[PlanetEnum, List[GrahaAspectCast]] = {}
        planets_received_map: Dict[PlanetEnum, List[GrahaAspectReceived]] = {p: [] for p in chart.planets.keys()}
        bhava_benefics_map: Dict[int, List[str]] = {h: [] for h in range(1, 13)}
        bhava_malefics_map: Dict[int, List[str]] = {h: [] for h in range(1, 13)}

        for p_enum, p_pos in chart.planets.items():
            p_name = p_enum.value
            p_house = planet_houses[p_enum]
            offsets = PARASHARI_FULL_ASPECTS.get(p_enum, [7])
            casts: List[GrahaAspectCast] = []

            for offset in offsets:
                # Target house: ((p_house + offset - 2) % 12) + 1
                target_h = ((p_house + offset - 2) % 12) + 1
                target_sign_id = ((asc_sign_id - 1 + target_h - 1) % 12) + 1
                sign_meta = ZODIAC_SIGNS[target_sign_id]
                target_sign_name = sign_meta["english_name"] if sign_mode == "english" else sign_meta["sanskrit_name"]

                ord_str = _format_ordinal(offset)
                is_special = (offset != 7)
                aspect_type = f"{ord_str} (100%)" if not is_special else f"{ord_str} (Vishesha)"

                # Grahas residing in the target house
                aspected_grahas = [g.value for g in house_occupants[target_h]]

                cast_item = GrahaAspectCast(
                    target_house=target_h,
                    target_sign_id=target_sign_id,
                    target_sign_name=target_sign_name,
                    aspect_offset=offset,
                    aspect_type=aspect_type,
                    is_special=is_special,
                    aspected_planets=aspected_grahas,
                )
                casts.append(cast_item)

                # Register aspect received on target grahas
                is_benefic = p_enum in NATURAL_BENEFICS
                for target_graha in house_occupants[target_h]:
                    planets_received_map[target_graha].append(
                        GrahaAspectReceived(
                            from_planet=p_name,
                            from_house=p_house,
                            aspect_offset=offset,
                            aspect_type=aspect_type,
                            is_benefic=is_benefic,
                        )
                    )

                # Register aspect on the house itself
                aspect_tag = f"{p_name} ({ord_str})"
                if is_benefic:
                    bhava_benefics_map[target_h].append(aspect_tag)
                else:
                    bhava_malefics_map[target_h].append(aspect_tag)

            planets_cast_map[p_enum] = casts

        # 3. Detect Mutual Aspects (Paraspara Drishti) & Conjunctions (Yuti)
        mutual_aspects_list: List[MutualAspectPair] = []
        processed_pairs: Set[Tuple[str, str]] = set()

        for p1_enum, p1_casts in planets_cast_map.items():
            for p2_enum, p2_casts in planets_cast_map.items():
                if p1_enum == p2_enum:
                    continue
                pair_key = tuple(sorted([p1_enum.value, p2_enum.value]))
                if pair_key in processed_pairs:
                    continue

                # Check if p1 aspects p2's house AND p2 aspects p1's house
                p1_house = planet_houses[p1_enum]
                p2_house = planet_houses[p2_enum]

                p1_aspects_p2 = any(c.target_house == p2_house for c in p1_casts)
                p2_aspects_p1 = any(c.target_house == p1_house for c in p2_casts)

                if p1_aspects_p2 and p2_aspects_p1:
                    processed_pairs.add(pair_key)
                    off1 = next(c.aspect_offset for c in p1_casts if c.target_house == p2_house)
                    off2 = next(c.aspect_offset for c in p2_casts if c.target_house == p1_house)
                    rel_str = f"Opposite 7th-7th" if off1 == 7 and off2 == 7 else f"{p1_enum.value} {off1}th ↔ {p2_enum.value} {off2}th"
                    mutual_aspects_list.append(
                        MutualAspectPair(
                            planet1=pair_key[0],
                            planet2=pair_key[1],
                            relation=rel_str,
                        )
                    )

        # Conjunctions (co-presence in same house)
        conjunctions_list: List[Dict[str, Any]] = []
        for h, occupants in house_occupants.items():
            if len(occupants) >= 2:
                sign_id = ((asc_sign_id - 1 + h - 1) % 12) + 1
                sign_meta = ZODIAC_SIGNS[sign_id]
                s_name = sign_meta["english_name"] if sign_mode == "english" else sign_meta["sanskrit_name"]
                graha_names = [g.value for g in occupants]
                conjunctions_list.append({
                    "house": h,
                    "sign": s_name,
                    "planets": graha_names,
                    "count": len(graha_names),
                })

        # 4. Construct GrahaAspectDetail for each planet
        planets_aspects_dict: Dict[str, GrahaAspectDetail] = {}
        for p_enum, p_pos in chart.planets.items():
            p_name = p_enum.value
            p_house = planet_houses[p_enum]
            casts = planets_cast_map[p_enum]
            received = planets_received_map[p_enum]

            # Conjunctions for this planet
            other_conjuncts = [g.value for g in house_occupants[p_house] if g != p_enum]

            # Mutual aspect partners for this planet
            mutuals = [
                m.planet2 if m.planet1 == p_name else m.planet1
                for m in mutual_aspects_list
                if m.planet1 == p_name or m.planet2 == p_name
            ]

            # Badges for UI table display: e.g. [{"target_house": 4, "label": "H4 (4th)", "is_special": True, "aspected_planets": ["Moon"]}]
            badges: List[Dict[str, Any]] = []
            for c in casts:
                graha_suffix = f": {', '.join(c.aspected_planets)}" if c.aspected_planets else ""
                badges.append({
                    "target_house": c.target_house,
                    "target_sign": c.target_sign_name,
                    "offset": c.aspect_offset,
                    "label": f"H{c.target_house} ({_format_ordinal(c.aspect_offset)})",
                    "title": f"Aspects House {c.target_house} ({c.target_sign_name}) via {c.aspect_type}{graha_suffix}",
                    "is_special": c.is_special,
                    "aspected_planets": c.aspected_planets,
                })

            sign_meta = ZODIAC_SIGNS[p_pos.sign.id]
            sign_name = sign_meta["english_name"] if sign_mode == "english" else sign_meta["sanskrit_name"]

            planets_aspects_dict[p_name] = GrahaAspectDetail(
                planet=p_name,
                glyph=PLANET_GLYPHS.get(p_name, "✧"),
                natal_house=p_house,
                natal_sign_id=p_pos.sign.id,
                natal_sign_name=sign_name,
                longitude=p_pos.longitude,
                degree_formatted=p_pos.sign.dms.formatted,
                is_benefic=(p_enum in NATURAL_BENEFICS),
                aspects_cast=casts,
                aspects_received=received,
                conjunctions=other_conjuncts,
                mutual_aspects=mutuals,
                summary_badges=badges,
                ray_color_light=RAY_COLORS_LIGHT.get(p_name, "#B45309"),
                ray_color_dark=RAY_COLORS_DARK.get(p_name, "#FBBF24"),
            )

        # 5. Construct BhavaAspectDetail for all 12 houses
        bhava_aspects_list: List[BhavaAspectDetail] = []
        for h in range(1, 13):
            sign_id = ((asc_sign_id - 1 + h - 1) % 12) + 1
            sign_meta = ZODIAC_SIGNS[sign_id]
            sign_name = sign_meta["english_name"] if sign_mode == "english" else sign_meta["sanskrit_name"]
            lord = sign_meta["lord"].value
            occupants = [g.value for g in house_occupants[h]]

            benefics = bhava_benefics_map[h]
            malefics = bhava_malefics_map[h]
            total_count = len(benefics) + len(malefics)

            # Net qualitative judgment
            if len(benefics) > 0 and len(malefics) == 0:
                net_inf = "Fortified (Benefic)"
            elif len(malefics) > 0 and len(benefics) == 0:
                net_inf = "Afflicted (Malefic)"
            elif len(benefics) > 0 and len(malefics) > 0:
                net_inf = "Mixed Influences"
            else:
                net_inf = "Neutral"

            bhava_aspects_list.append(
                BhavaAspectDetail(
                    house_number=h,
                    sign_id=sign_id,
                    sign_name=sign_name,
                    lord=lord,
                    occupants=occupants,
                    benefics_aspecting=benefics,
                    malefics_aspecting=malefics,
                    total_aspects_count=total_count,
                    net_influence=net_inf,
                )
            )

        return AspectsReport(
            planets_aspects=planets_aspects_dict,
            bhava_aspects=bhava_aspects_list,
            mutual_aspects=mutual_aspects_list,
            conjunctions=conjunctions_list,
        )
