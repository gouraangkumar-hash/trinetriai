"""Classical Vedic Planetary Friendships Engine (Brihat Parashara Hora Shastra Standards).

Computes:
1. Natural Relationships (Naisargika Sambandha / Maitri)
2. Temporal Relationships (Tatkalika Sambandha / Maitri)
3. Five-Fold Compound Relationships (Pancha-Dha Maitri):
   - Great Friend (Adhi Mitra, +2)
   - Friend (Mitra, +1)
   - Neutral (Sama, 0)
   - Enemy (Shatru, -1)
   - Great Enemy (Adhi Shatru, -2)
4. Dispositor Sign Kshetra Placement Analysis
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from core.constants import PlanetEnum, ZODIAC_SIGNS
from schemas.models import UnifiedChartData


# =============================================================================
# Classical Natural Relationships (Naisargika Maitri - BPHS Ch. 3)
# =============================================================================

class RelationshipType(str, Enum):
    GREAT_FRIEND = "Great Friend"      # Adhi Mitra (+2)
    FRIEND = "Friend"                  # Mitra (+1)
    NEUTRAL = "Neutral"                # Sama (0)
    ENEMY = "Enemy"                    # Shatru (-1)
    GREAT_ENEMY = "Great Enemy"        # Adhi Shatru (-2)


# Canonical Natural Relationships (BPHS Chapter 3, Slokas 55-60)
NAISARGIKA_MAITRI: Dict[PlanetEnum, Dict[str, List[PlanetEnum]]] = {
    PlanetEnum.SUN: {
        "friends": [PlanetEnum.MOON, PlanetEnum.MARS, PlanetEnum.JUPITER],
        "neutrals": [PlanetEnum.MERCURY],
        "enemies": [PlanetEnum.VENUS, PlanetEnum.SATURN, PlanetEnum.RAHU, PlanetEnum.KETU],
    },
    PlanetEnum.MOON: {
        "friends": [PlanetEnum.SUN, PlanetEnum.MERCURY],
        "neutrals": [PlanetEnum.MARS, PlanetEnum.JUPITER, PlanetEnum.VENUS, PlanetEnum.SATURN],
        "enemies": [],  # Moon considers no planet a natural enemy
    },
    PlanetEnum.MARS: {
        "friends": [PlanetEnum.SUN, PlanetEnum.MOON, PlanetEnum.JUPITER],
        "neutrals": [PlanetEnum.VENUS, PlanetEnum.SATURN],
        "enemies": [PlanetEnum.MERCURY, PlanetEnum.RAHU],
    },
    PlanetEnum.MERCURY: {
        "friends": [PlanetEnum.SUN, PlanetEnum.VENUS],
        "neutrals": [PlanetEnum.MARS, PlanetEnum.JUPITER, PlanetEnum.SATURN],
        "enemies": [PlanetEnum.MOON],
    },
    PlanetEnum.JUPITER: {
        "friends": [PlanetEnum.SUN, PlanetEnum.MOON, PlanetEnum.MARS],
        "neutrals": [PlanetEnum.SATURN],
        "enemies": [PlanetEnum.MERCURY, PlanetEnum.VENUS],
    },
    PlanetEnum.VENUS: {
        "friends": [PlanetEnum.MERCURY, PlanetEnum.SATURN],
        "neutrals": [PlanetEnum.MARS, PlanetEnum.JUPITER],
        "enemies": [PlanetEnum.SUN, PlanetEnum.MOON],
    },
    PlanetEnum.SATURN: {
        "friends": [PlanetEnum.MERCURY, PlanetEnum.VENUS],
        "neutrals": [PlanetEnum.JUPITER],
        "enemies": [PlanetEnum.SUN, PlanetEnum.MOON, PlanetEnum.MARS],
    },
    PlanetEnum.RAHU: {
        "friends": [PlanetEnum.MERCURY, PlanetEnum.VENUS, PlanetEnum.SATURN],
        "neutrals": [PlanetEnum.JUPITER],
        "enemies": [PlanetEnum.SUN, PlanetEnum.MOON, PlanetEnum.MARS],
    },
    PlanetEnum.KETU: {
        "friends": [PlanetEnum.MARS, PlanetEnum.VENUS, PlanetEnum.SATURN],
        "neutrals": [PlanetEnum.JUPITER, PlanetEnum.MERCURY],
        "enemies": [PlanetEnum.SUN, PlanetEnum.MOON],
    },
}

TEMPORAL_FRIEND_HOUSES = {2, 3, 4, 10, 11, 12}
TEMPORAL_ENEMY_HOUSES = {1, 5, 6, 7, 8, 9}


class PlanetFriendshipPair(BaseModel):
    """Detailed bilateral relationship between source planet and target planet."""
    target_planet: str
    target_glyph: str
    target_sign: str
    house_offset_from_source: int
    natural_relationship: str          # Friend, Neutral, Enemy
    natural_score: int                 # +1, 0, -1
    temporal_relationship: str         # Friend (+1), Enemy (-1)
    temporal_score: int                # +1, -1
    pancha_dha_relationship: str       # Great Friend, Friend, Neutral, Enemy, Great Enemy
    pancha_dha_score: int              # +2, +1, 0, -1, -2
    pancha_dha_sanskrit: str           # अधि मित्र, मित्र, सम, शत्रु, अधि शत्रु


class PlanetMaitriProfile(BaseModel):
    """Complete friendship profile for a single planet."""
    planet: str
    sign_id: int
    sign_name: str
    dispositor: str
    dispositor_relationship: str       # Own Sign, Great Friend, Friend, Neutral, Enemy, Great Enemy
    dispositor_kshetra: str            # e.g. "Adhi Mitra Kshetra", "Swa Kshetra"
    dispositor_sanskrit: str
    relationships: List[PlanetFriendshipPair]


class PanchaDhaMaitriReport(BaseModel):
    """Full chart planetary friendships report."""
    profiles: Dict[str, PlanetMaitriProfile]


class FriendshipEngine:
    """Evaluates classical Parashari planetary friendships."""

    PLANET_GLYPHS: Dict[PlanetEnum, str] = {
        PlanetEnum.SUN: "☉",
        PlanetEnum.MOON: "☽",
        PlanetEnum.MARS: "♂",
        PlanetEnum.MERCURY: "☿",
        PlanetEnum.JUPITER: "♃",
        PlanetEnum.VENUS: "♀",
        PlanetEnum.SATURN: "♄",
        PlanetEnum.RAHU: "☊",
        PlanetEnum.KETU: "☋",
    }

    SANSKRIT_LABELS = {
        RelationshipType.GREAT_FRIEND: "अधि मित्र (Adhi Mitra)",
        RelationshipType.FRIEND: "मित्र (Mitra)",
        RelationshipType.NEUTRAL: "सम (Sama)",
        RelationshipType.ENEMY: "शत्रु (Shatru)",
        RelationshipType.GREAT_ENEMY: "अधि शत्रु (Adhi Shatru)",
    }

    @classmethod
    def get_natural_relationship(cls, p1: PlanetEnum, p2: PlanetEnum) -> Tuple[str, int]:
        """Returns (relationship_str, score) from p1's perspective to p2."""
        if p1 == p2:
            return "Self", 0
        rules = NAISARGIKA_MAITRI.get(p1, {})
        if p2 in rules.get("friends", []):
            return "Friend", 1
        elif p2 in rules.get("enemies", []):
            return "Enemy", -1
        else:
            return "Neutral", 0

    @classmethod
    def get_temporal_relationship(cls, house_offset: int) -> Tuple[str, int]:
        """Determines temporal relationship based on house offset (1-12 inclusive)."""
        if house_offset in TEMPORAL_FRIEND_HOUSES:
            return "Friend", 1
        else:
            return "Enemy", -1

    @classmethod
    def compute_compound(cls, nat_score: int, temp_score: int) -> Tuple[RelationshipType, int]:
        """Calculates Pancha-Dha combined score and relationship enum."""
        combined = nat_score + temp_score
        if combined >= 2:
            return RelationshipType.GREAT_FRIEND, 2
        elif combined == 1:
            return RelationshipType.FRIEND, 1
        elif combined == 0:
            return RelationshipType.NEUTRAL, 0
        elif combined == -1:
            return RelationshipType.ENEMY, -1
        else:
            return RelationshipType.GREAT_ENEMY, -2

    @classmethod
    def evaluate(cls, chart: UnifiedChartData) -> PanchaDhaMaitriReport:
        """Evaluates Pancha-Dha Maitri for all classical planets in the chart."""
        profiles: Dict[str, PlanetMaitriProfile] = {}

        classical_planets = [
            PlanetEnum.SUN, PlanetEnum.MOON, PlanetEnum.MARS, PlanetEnum.MERCURY,
            PlanetEnum.JUPITER, PlanetEnum.VENUS, PlanetEnum.SATURN, PlanetEnum.RAHU, PlanetEnum.KETU
        ]

        # Map planet signs
        planet_signs: Dict[PlanetEnum, int] = {}
        for p in classical_planets:
            if p in chart.planets:
                planet_signs[p] = chart.planets[p].sign.id

        for src_p in classical_planets:
            if src_p not in chart.planets:
                continue
            src_pos = chart.planets[src_p]
            src_sign = src_pos.sign.id
            dispositor = src_pos.sign.lord

            pairs: List[PlanetFriendshipPair] = []
            for tgt_p in classical_planets:
                if tgt_p == src_p or tgt_p not in chart.planets:
                    continue
                tgt_pos = chart.planets[tgt_p]
                tgt_sign = tgt_pos.sign.id

                # House offset from src_p (1 to 12)
                offset = ((tgt_sign - src_sign) % 12) + 1

                nat_rel, nat_score = cls.get_natural_relationship(src_p, tgt_p)
                temp_rel, temp_score = cls.get_temporal_relationship(offset)
                compound_enum, compound_score = cls.compute_compound(nat_score, temp_score)

                pairs.append(
                    PlanetFriendshipPair(
                        target_planet=tgt_p.value,
                        target_glyph=cls.PLANET_GLYPHS.get(tgt_p, "✧"),
                        target_sign=tgt_pos.sign.sanskrit_name,
                        house_offset_from_source=offset,
                        natural_relationship=nat_rel,
                        natural_score=nat_score,
                        temporal_relationship=temp_rel,
                        temporal_score=temp_score,
                        pancha_dha_relationship=compound_enum.value,
                        pancha_dha_score=compound_score,
                        pancha_dha_sanskrit=cls.SANSKRIT_LABELS[compound_enum],
                    )
                )

            # Dispositor Kshetra calculation
            if dispositor == src_p:
                disp_rel = "Own Sign"
                disp_kshetra = "Swa Kshetra (Own Sign)"
                disp_sanskrit = "स्वक्षेत्र (Swa Kshetra)"
            else:
                disp_offset = ((planet_signs.get(dispositor, 1) - src_sign) % 12) + 1
                nat_disp, n_sc = cls.get_natural_relationship(src_p, dispositor)
                temp_disp, t_sc = cls.get_temporal_relationship(disp_offset)
                disp_comp, _ = cls.compute_compound(n_sc, t_sc)
                disp_rel = disp_comp.value

                kshetra_map = {
                    RelationshipType.GREAT_FRIEND: ("Adhi Mitra Kshetra (Great Friend)", "अधिमित्र क्षेत्र"),
                    RelationshipType.FRIEND: ("Mitra Kshetra (Friend)", "मित्र क्षेत्र"),
                    RelationshipType.NEUTRAL: ("Sama Kshetra (Neutral)", "सम क्षेत्र"),
                    RelationshipType.ENEMY: ("Shatru Kshetra (Enemy)", "शत्रु क्षेत्र"),
                    RelationshipType.GREAT_ENEMY: ("Adhi Shatru Kshetra (Great Enemy)", "अधिशत्रु क्षेत्र"),
                }
                disp_kshetra, disp_sanskrit = kshetra_map.get(disp_comp, ("Sama Kshetra", "सम क्षेत्र"))

            profiles[src_p.value] = PlanetMaitriProfile(
                planet=src_p.value,
                sign_id=src_sign,
                sign_name=src_pos.sign.sanskrit_name,
                dispositor=dispositor.value,
                dispositor_relationship=disp_rel,
                dispositor_kshetra=disp_kshetra,
                dispositor_sanskrit=disp_sanskrit,
                relationships=pairs,
            )

        return PanchaDhaMaitriReport(profiles=profiles)
