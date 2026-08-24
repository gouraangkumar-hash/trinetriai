"""Krishnamurti Paddhati (KP) Astrology Computational Engine.

Provides:
- Generation of the canonical 1–249 KP Sub-Lord boundary table with sign cusp splitting.
- High-precision Sub-Lord and Sub-Sub-Lord resolution functions for any given longitude.
- 4-Fold Significator Matrix (Level A: Planet in Star of Occupant, Level B: Occupant,
  Level C: Planet in Star of Owner, Level D: Owner).
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from core.astro_utils import decimal_to_dms, normalize_degrees
from core.constants import (
    NAKSHATRA_ARC_DEG,
    NAKSHATRAS,
    TOTAL_VIMSHOTTARI_YEARS,
    VIMSHOTTARI_DASHA_ORDER,
    ZODIAC_SIGNS,
    PlanetEnum,
)
from schemas.models import DMSModel, UnifiedChartData


class KPSubTableEntry(BaseModel):
    """A single row in the canonical 1–249 KP Sub-Lord Table."""
    model_config = ConfigDict(frozen=True)

    sub_number: int = Field(..., ge=1, le=249, description="KP Sub Index (1 to 249)")
    sign_id: int = Field(..., ge=1, le=12)
    sign_name: str
    sign_lord: PlanetEnum
    nakshatra_id: int = Field(..., ge=1, le=27)
    nakshatra_name: str
    star_lord: PlanetEnum
    sub_lord: PlanetEnum
    start_longitude: float
    end_longitude: float
    start_dms: DMSModel
    end_dms: DMSModel


class KPSubDivisionResult(BaseModel):
    """Detailed KP 4-tier subdivision for a celestial longitude."""
    model_config = ConfigDict(frozen=True)

    longitude: float
    sign_id: int
    sign_name: str
    sign_lord: PlanetEnum
    nakshatra_id: int
    nakshatra_name: str
    star_lord: PlanetEnum
    sub_number: int = Field(..., ge=1, le=249)
    sub_lord: PlanetEnum
    sub_start_deg: float
    sub_end_deg: float
    sub_sub_lord: PlanetEnum
    sub_sub_start_deg: float
    sub_sub_end_deg: float
    dms: DMSModel


class HouseSignificatorsModel(BaseModel):
    """4-Fold Significators for a single house."""
    model_config = ConfigDict(frozen=True)

    house_number: int
    level_a: list[PlanetEnum] = Field(description="Level A: Planets in star of occupant")
    level_b: list[PlanetEnum] = Field(description="Level B: Occupants of house")
    level_c: list[PlanetEnum] = Field(description="Level C: Planets in star of lord")
    level_d: list[PlanetEnum] = Field(description="Level D: Lord (owner) of house")


class KP4FoldSignificatorsMatrix(BaseModel):
    """Complete 12-house 4-Fold Significators Matrix."""
    model_config = ConfigDict(frozen=True)

    houses: dict[int, HouseSignificatorsModel]
    planets_significations: dict[PlanetEnum, dict[str, list[int]]] = Field(
        description="Houses signified by each planet categorized by levels A, B, C, D"
    )


# =========================================================================
# KP Sub Table & Resolver Engine
# =========================================================================

class KPEngine:
    """Core Krishnamurti Paddhati (KP) computation engine."""

    _sub_table_cache: Optional[list[KPSubTableEntry]] = None

    @classmethod
    def _build_dms(cls, degrees: float) -> DMSModel:
        d, m, s, formatted = decimal_to_dms(degrees)
        return DMSModel(degrees=d, minutes=m, seconds=s, formatted=formatted)

    @classmethod
    def get_kp_249_table(cls) -> list[KPSubTableEntry]:
        """Generates or retrieves the cached 1–249 KP Sub-Lord boundary table."""
        if cls._sub_table_cache is not None:
            return cls._sub_table_cache

        order_lords = [entry[0] for entry in VIMSHOTTARI_DASHA_ORDER]
        order_years = {entry[0]: entry[1] for entry in VIMSHOTTARI_DASHA_ORDER}

        table: list[KPSubTableEntry] = []
        sub_counter = 1

        for nak_id in range(1, 28):
            nak_info = NAKSHATRAS[nak_id]
            star_lord = nak_info["lord"]
            nak_start_deg = nak_info["start_deg"]

            start_idx = order_lords.index(star_lord)
            current_sub_start = nak_start_deg

            for j in range(9):
                sub_lord = order_lords[(start_idx + j) % 9]
                sub_years = order_years[sub_lord]

                # Arc length in degrees = (sub_years / 120) * 13°20' = sub_years / 9.0 degrees
                sub_arc_length = sub_years / 9.0
                current_sub_end = current_sub_start + sub_arc_length

                # Check if this sub spans across a 30° zodiac sign boundary
                sign_start_id = int(current_sub_start // 30.0) + 1
                sign_end_id = int((current_sub_end - 1e-9) // 30.0) + 1

                if sign_start_id != sign_end_id:
                    # Boundary crossing: split into two distinct sub entries
                    sign_boundary = sign_start_id * 30.0

                    # Part 1 (in starting sign)
                    table.append(
                        KPSubTableEntry(
                            sub_number=sub_counter,
                            sign_id=sign_start_id,
                            sign_name=ZODIAC_SIGNS[sign_start_id]["sanskrit_name"],
                            sign_lord=ZODIAC_SIGNS[sign_start_id]["lord"],
                            nakshatra_id=nak_id,
                            nakshatra_name=nak_info["sanskrit_name"],
                            star_lord=star_lord,
                            sub_lord=sub_lord,
                            start_longitude=current_sub_start,
                            end_longitude=sign_boundary,
                            start_dms=cls._build_dms(current_sub_start),
                            end_dms=cls._build_dms(sign_boundary),
                        )
                    )
                    sub_counter += 1

                    # Part 2 (in next sign)
                    table.append(
                        KPSubTableEntry(
                            sub_number=sub_counter,
                            sign_id=sign_end_id,
                            sign_name=ZODIAC_SIGNS[sign_end_id]["sanskrit_name"],
                            sign_lord=ZODIAC_SIGNS[sign_end_id]["lord"],
                            nakshatra_id=nak_id,
                            nakshatra_name=nak_info["sanskrit_name"],
                            star_lord=star_lord,
                            sub_lord=sub_lord,
                            start_longitude=sign_boundary,
                            end_longitude=current_sub_end,
                            start_dms=cls._build_dms(sign_boundary),
                            end_dms=cls._build_dms(current_sub_end),
                        )
                    )
                    sub_counter += 1
                else:
                    # Single entry within the same sign
                    table.append(
                        KPSubTableEntry(
                            sub_number=sub_counter,
                            sign_id=sign_start_id,
                            sign_name=ZODIAC_SIGNS[sign_start_id]["sanskrit_name"],
                            sign_lord=ZODIAC_SIGNS[sign_start_id]["lord"],
                            nakshatra_id=nak_id,
                            nakshatra_name=nak_info["sanskrit_name"],
                            star_lord=star_lord,
                            sub_lord=sub_lord,
                            start_longitude=current_sub_start,
                            end_longitude=current_sub_end,
                            start_dms=cls._build_dms(current_sub_start),
                            end_dms=cls._build_dms(current_sub_end),
                        )
                    )
                    sub_counter += 1

                current_sub_start = current_sub_end

        cls._sub_table_cache = table
        return table

    @classmethod
    def resolve_kp_sub(cls, longitude: float) -> KPSubDivisionResult:
        """Resolves Sign Lord, Star Lord, Sub Lord, and Sub-Sub Lord for a longitude.

        Args:
            longitude: Absolute sidereal longitude (0° to 360°).

        Returns:
            KPSubDivisionResult with full 4-tier hierarchy and boundary coordinates.
        """
        lon_norm = normalize_degrees(longitude)
        sub_table = cls.get_kp_249_table()

        # Binary or linear match in the 249 table
        matched_entry: Optional[KPSubTableEntry] = None
        for entry in sub_table:
            # Handle boundary inclusive start, exclusive end (with edge case for 360°)
            if entry.start_longitude <= lon_norm < entry.end_longitude or (
                entry.sub_number == 249 and lon_norm >= entry.start_longitude
            ):
                matched_entry = entry
                break

        if matched_entry is None:
            matched_entry = sub_table[-1]

        # Calculate Sub-Sub Lord
        # Sub-Sub is proportional to Vimshottari periods within the original unsplit sub segment
        order_lords = [entry[0] for entry in VIMSHOTTARI_DASHA_ORDER]
        order_years = {entry[0]: entry[1] for entry in VIMSHOTTARI_DASHA_ORDER}

        sub_lord = matched_entry.sub_lord
        sub_start_idx = order_lords.index(sub_lord)
        total_sub_span = matched_entry.end_longitude - matched_entry.start_longitude

        # Find position within this sub entry
        pos_in_sub = lon_norm - matched_entry.start_longitude
        accumulated_sub_sub = 0.0
        sub_sub_lord = sub_lord
        ss_start_deg = matched_entry.start_longitude
        ss_end_deg = matched_entry.end_longitude

        for k in range(9):
            candidate_ss_lord = order_lords[(sub_start_idx + k) % 9]
            candidate_years = order_years[candidate_ss_lord]
            ss_span = total_sub_span * (candidate_years / TOTAL_VIMSHOTTARI_YEARS)

            seg_start = matched_entry.start_longitude + accumulated_sub_sub
            seg_end = seg_start + ss_span

            if seg_start <= lon_norm < seg_end or (k == 8 and lon_norm >= seg_start):
                sub_sub_lord = candidate_ss_lord
                ss_start_deg = seg_start
                ss_end_deg = seg_end
                break

            accumulated_sub_sub += ss_span

        return KPSubDivisionResult(
            longitude=lon_norm,
            sign_id=matched_entry.sign_id,
            sign_name=matched_entry.sign_name,
            sign_lord=matched_entry.sign_lord,
            nakshatra_id=matched_entry.nakshatra_id,
            nakshatra_name=matched_entry.nakshatra_name,
            star_lord=matched_entry.star_lord,
            sub_number=matched_entry.sub_number,
            sub_lord=matched_entry.sub_lord,
            sub_start_deg=matched_entry.start_longitude,
            sub_end_deg=matched_entry.end_longitude,
            sub_sub_lord=sub_sub_lord,
            sub_sub_start_deg=ss_start_deg,
            sub_sub_end_deg=ss_end_deg,
            dms=cls._build_dms(lon_norm),
        )

    # =========================================================================
    # 4-Fold Significators (ABCD Matrix)
    # =========================================================================

    @classmethod
    def calculate_4fold_significators(cls, chart: UnifiedChartData) -> KP4FoldSignificatorsMatrix:
        """Calculates 4-Fold Significators (Levels A, B, C, D) for all 12 Placidus houses.

        Level A: Planets in the Star of an Occupant.
        Level B: Planets occupying the House.
        Level C: Planets in the Star of the House Owner (Lord).
        Level D: Planet owning (ruling) the House Cusp sign.
        """
        # 1. Determine Star Lords for all planets
        planet_star_lords: dict[PlanetEnum, PlanetEnum] = {}
        for p_name, p_pos in chart.planets.items():
            star_lord = p_pos.nakshatra.lord
            planet_star_lords[p_name] = star_lord

        # 2. Determine House Cusp boundaries and House Owners
        cusps = chart.placidus_houses
        house_owners: dict[int, PlanetEnum] = {}
        house_occupants: dict[int, list[PlanetEnum]] = {h: [] for h in range(1, 13)}

        for h in range(1, 13):
            cusp = cusps[h - 1]
            house_owners[h] = cusp.sign.lord

        # 3. Determine House Occupants for each planet
        for p_name, p_pos in chart.planets.items():
            p_lon = p_pos.longitude
            assigned_house = 12  # fallback

            for h in range(1, 13):
                h_start = cusps[h - 1].cusp_longitude
                next_idx = h % 12
                h_end = cusps[next_idx].cusp_longitude

                if h_start < h_end:
                    if h_start <= p_lon < h_end:
                        assigned_house = h
                        break
                else:
                    # Spans across 0° Aries
                    if p_lon >= h_start or p_lon < h_end:
                        assigned_house = h
                        break

            house_occupants[assigned_house].append(p_name)

        # 4. Compute 4-Fold Significators per house
        house_significators: dict[int, HouseSignificatorsModel] = {}
        planet_significations: dict[PlanetEnum, dict[str, list[int]]] = {
            p: {"A": [], "B": [], "C": [], "D": []} for p in chart.planets.keys()
        }

        for h in range(1, 13):
            occupants = house_occupants[h]
            owner = house_owners[h]

            # Level A: Planets in star of occupants
            level_a: list[PlanetEnum] = []
            for p_name, s_lord in planet_star_lords.items():
                if s_lord in occupants:
                    level_a.append(p_name)
                    if h not in planet_significations[p_name]["A"]:
                        planet_significations[p_name]["A"].append(h)

            # Level B: Occupants of the house
            level_b = list(occupants)
            for p_name in level_b:
                if h not in planet_significations[p_name]["B"]:
                    planet_significations[p_name]["B"].append(h)

            # Level C: Planets in star of house owner
            level_c: list[PlanetEnum] = []
            for p_name, s_lord in planet_star_lords.items():
                if s_lord == owner:
                    level_c.append(p_name)
                    if h not in planet_significations[p_name]["C"]:
                        planet_significations[p_name]["C"].append(h)

            # Level D: House Owner
            level_d = [owner]
            if h not in planet_significations[owner]["D"]:
                planet_significations[owner]["D"].append(h)

            house_significators[h] = HouseSignificatorsModel(
                house_number=h,
                level_a=level_a,
                level_b=level_b,
                level_c=level_c,
                level_d=level_d,
            )

        return KP4FoldSignificatorsMatrix(
            houses=house_significators,
            planets_significations=planet_significations,
        )
