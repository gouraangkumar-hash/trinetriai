"""Parashari Classical Vedic Astrology Computational Engine.

Provides:
- Harmonic Divisional Chart Generator (Shodashavarga) for D1, D2, D3, D7, D9, D10, D12, D30, and D60
  following Brihat Parashara Hora Shastra (BPHS) sign-assignment algorithms.
- 120-Year Recursive Vimshottari Dasha Engine calculating Mahadasha (MD), Antardasha (AD/Bhukti),
  and Pratyantardasha (PD) timeline hierarchies down to exact calendar timestamps.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from core.astro_utils import decimal_to_dms, get_nakshatra_placement, normalize_degrees
from core.constants import (
    TOTAL_VIMSHOTTARI_YEARS,
    VIMSHOTTARI_DASHA_ORDER,
    ZODIAC_SIGNS,
    PlanetEnum,
    ZodiacSignEnum,
)
from schemas.models import DMSModel, SignPlacementModel, UnifiedChartData


class VargaType(str, Enum):
    D1 = "D1"      # Rashi (Natal Chart)
    D2 = "D2"      # Hora (Wealth, Sun/Moon)
    D3 = "D3"      # Drekkana (Siblings, Courage)
    D7 = "D7"      # Saptamsha (Children, Progeny)
    D9 = "D9"      # Navamsha (Dharma, Spouse, Soul)
    D10 = "D10"    # Dashamsha (Career, Profession)
    D12 = "D12"    # Dvadashamsha (Parents, Lineage)
    D30 = "D30"    # Trimsamsha (Misfortunes, Evils)
    D60 = "D60"    # Shashtyamsha (Past Karma, Fine Detail)


class VargaPlacement(BaseModel):
    """Placement of a celestial body within a specific divisional chart."""
    model_config = ConfigDict(frozen=True)

    varga: VargaType
    planet: Optional[PlanetEnum] = None
    is_ascendant: bool = False
    sign_id: int = Field(..., ge=1, le=12)
    sign_name: str
    sign_lord: PlanetEnum
    intra_sign_degree: float = Field(..., ge=0.0, lt=30.0)
    dms: DMSModel


class VargaChart(BaseModel):
    """Complete divisional chart containing Ascendant and 9 Grahas."""
    model_config = ConfigDict(frozen=True)

    varga: VargaType
    ascendant: VargaPlacement
    planets: dict[PlanetEnum, VargaPlacement]


class PratyantardashaNode(BaseModel):
    """Level 3: Pratyantardasha (PD)."""
    model_config = ConfigDict(frozen=True)

    lord: PlanetEnum
    start_date: datetime
    end_date: datetime
    duration_days: float


class AntardashaNode(BaseModel):
    """Level 2: Antardasha (AD / Bhukti)."""
    model_config = ConfigDict(frozen=True)

    lord: PlanetEnum
    start_date: datetime
    end_date: datetime
    duration_days: float
    pratyantardashas: list[PratyantardashaNode]


class MahadashaNode(BaseModel):
    """Level 1: Mahadasha (MD)."""
    model_config = ConfigDict(frozen=True)

    lord: PlanetEnum
    start_date: datetime
    end_date: datetime
    duration_days: float
    antardashas: list[AntardashaNode]


class VimshottariDashaTree(BaseModel):
    """Full 120-year Vimshottari Dasha timeline."""
    model_config = ConfigDict(frozen=True)

    birth_datetime: datetime
    moon_nakshatra_id: int
    moon_nakshatra_name: str
    birth_mahadasha_lord: PlanetEnum
    birth_balance_fraction: float
    birth_balance_years: float
    mahadashas: list[MahadashaNode]


# =========================================================================
# Varga Chart Engine
# =========================================================================

class VargaChartEngine:
    """Calculates classical BPHS divisional charts."""

    @staticmethod
    def _build_dms(degrees: float) -> DMSModel:
        d, m, s, formatted = decimal_to_dms(degrees)
        return DMSModel(degrees=d, minutes=m, seconds=s, formatted=formatted)

    @classmethod
    def calculate_point_varga(
        cls,
        longitude: float,
        varga: VargaType,
        planet: Optional[PlanetEnum] = None,
        is_ascendant: bool = False,
    ) -> VargaPlacement:
        """Calculates the varga sign and intra-varga degree for a single celestial point.

        Args:
            longitude: Absolute sidereal longitude (0° to 360°).
            varga: Target divisional chart type.
            planet: Optional PlanetEnum name.
            is_ascendant: True if calculating for Ascendant (Lagna).

        Returns:
            VargaPlacement model.
        """
        lon_norm = normalize_degrees(longitude)
        rashi_sign = int(lon_norm // 30.0) + 1  # 1 to 12
        intra_deg = lon_norm % 30.0
        is_odd = (rashi_sign % 2) != 0

        target_sign_id: int
        target_intra_deg: float

        if varga == VargaType.D1:
            target_sign_id = rashi_sign
            target_intra_deg = intra_deg

        elif varga == VargaType.D2:
            # Hora (15° each)
            part = int(intra_deg // 15.0)
            if is_odd:
                target_sign_id = 5 if part == 0 else 4  # Leo / Cancer
            else:
                target_sign_id = 4 if part == 0 else 5  # Cancer / Leo
            target_intra_deg = (intra_deg % 15.0) * 2.0

        elif varga == VargaType.D3:
            # Drekkana (10° each: 1st=Same, 2nd=5th from it, 3rd=9th from it)
            part = int(intra_deg // 10.0)
            offset = part * 4  # 0, 4, 8 signs
            target_sign_id = ((rashi_sign - 1 + offset) % 12) + 1
            target_intra_deg = (intra_deg % 10.0) * 3.0

        elif varga == VargaType.D7:
            # Saptamsha (30/7 deg each)
            step = 30.0 / 7.0
            part = min(int(intra_deg / step), 6)
            if is_odd:
                target_sign_id = ((rashi_sign - 1 + part) % 12) + 1
            else:
                # Even signs start from 7th from the sign
                target_sign_id = ((rashi_sign - 1 + 6 + part) % 12) + 1
            target_intra_deg = (intra_deg % step) * 7.0

        elif varga == VargaType.D9:
            # Navamsha (3°20' = 3.33333333° each)
            step = 30.0 / 9.0
            part = min(int(intra_deg / step), 8)
            # Fiery: 1,5,9 -> Aries (1)
            # Earthy: 2,6,10 -> Capricorn (10)
            # Airy: 3,7,11 -> Libra (7)
            # Watery: 4,8,12 -> Cancer (4)
            if rashi_sign in (1, 5, 9):
                start_sign = 1
            elif rashi_sign in (2, 6, 10):
                start_sign = 10
            elif rashi_sign in (3, 7, 11):
                start_sign = 7
            else:
                start_sign = 4
            target_sign_id = ((start_sign - 1 + part) % 12) + 1
            target_intra_deg = (intra_deg % step) * 9.0

        elif varga == VargaType.D10:
            # Dashamsha (3° each)
            part = min(int(intra_deg / 3.0), 9)
            if is_odd:
                target_sign_id = ((rashi_sign - 1 + part) % 12) + 1
            else:
                # Even signs start from 9th from the sign
                target_sign_id = ((rashi_sign - 1 + 8 + part) % 12) + 1
            target_intra_deg = (intra_deg % 3.0) * 10.0

        elif varga == VargaType.D12:
            # Dvadashamsha (2.5° each: starts from the same sign)
            part = min(int(intra_deg / 2.5), 11)
            target_sign_id = ((rashi_sign - 1 + part) % 12) + 1
            target_intra_deg = (intra_deg % 2.5) * 12.0

        elif varga == VargaType.D30:
            # Trimsamsha (BPHS unequal divisions)
            if is_odd:
                if intra_deg < 5.0:
                    target_sign_id = 1  # Aries (Mars)
                    target_intra_deg = (intra_deg / 5.0) * 30.0
                elif intra_deg < 10.0:
                    target_sign_id = 11  # Aquarius (Saturn)
                    target_intra_deg = ((intra_deg - 5.0) / 5.0) * 30.0
                elif intra_deg < 18.0:
                    target_sign_id = 9  # Sagittarius (Jupiter)
                    target_intra_deg = ((intra_deg - 10.0) / 8.0) * 30.0
                elif intra_deg < 25.0:
                    target_sign_id = 3  # Gemini (Mercury)
                    target_intra_deg = ((intra_deg - 18.0) / 7.0) * 30.0
                else:
                    target_sign_id = 7  # Libra (Venus)
                    target_intra_deg = ((intra_deg - 25.0) / 5.0) * 30.0
            else:
                if intra_deg < 5.0:
                    target_sign_id = 2  # Taurus (Venus)
                    target_intra_deg = (intra_deg / 5.0) * 30.0
                elif intra_deg < 12.0:
                    target_sign_id = 6  # Virgo (Mercury)
                    target_intra_deg = ((intra_deg - 5.0) / 7.0) * 30.0
                elif intra_deg < 20.0:
                    target_sign_id = 12  # Pisces (Jupiter)
                    target_intra_deg = ((intra_deg - 12.0) / 8.0) * 30.0
                elif intra_deg < 25.0:
                    target_sign_id = 10  # Capricorn (Saturn)
                    target_intra_deg = ((intra_deg - 20.0) / 5.0) * 30.0
                else:
                    target_sign_id = 8  # Scorpio (Mars)
                    target_intra_deg = ((intra_deg - 25.0) / 5.0) * 30.0

        elif varga == VargaType.D60:
            # Shashtyamsha (0.5° each: starts from the same sign)
            part = min(int(intra_deg / 0.5), 59)
            target_sign_id = ((rashi_sign - 1 + part) % 12) + 1
            target_intra_deg = (intra_deg % 0.5) * 60.0

        else:
            raise ValueError(f"Unsupported VargaType: {varga}")

        sign_info = ZODIAC_SIGNS[target_sign_id]
        return VargaPlacement(
            varga=varga,
            planet=planet,
            is_ascendant=is_ascendant,
            sign_id=target_sign_id,
            sign_name=sign_info["sanskrit_name"],
            sign_lord=sign_info["lord"],
            intra_sign_degree=target_intra_deg,
            dms=cls._build_dms(target_intra_deg),
        )

    @classmethod
    def generate_varga_chart(
        cls,
        chart: UnifiedChartData,
        varga: VargaType,
    ) -> VargaChart:
        """Generates a complete divisional chart for Ascendant and all 9 Grahas."""
        asc_placement = cls.calculate_point_varga(
            longitude=chart.angles.ascendant,
            varga=varga,
            is_ascendant=True,
        )

        planets_placement: dict[PlanetEnum, VargaPlacement] = {}
        for p_name, p_pos in chart.planets.items():
            planets_placement[p_name] = cls.calculate_point_varga(
                longitude=p_pos.longitude,
                varga=varga,
                planet=p_name,
                is_ascendant=False,
            )

        return VargaChart(
            varga=varga,
            ascendant=asc_placement,
            planets=planets_placement,
        )


# =========================================================================
# Vimshottari Dasha Engine
# =========================================================================

DAYS_PER_SOLAR_YEAR = 365.2425


class VimshottariDashaEngine:
    """Computes the 120-year hierarchical Vimshottari Dasha timeline."""

    @classmethod
    def generate_dasha_tree(
        cls,
        birth_datetime: datetime,
        moon_longitude: float,
        num_cycles: int = 1,
    ) -> VimshottariDashaTree:
        """Generates full Mahadasha -> Antardasha -> Pratyantardasha tree.

        Args:
            birth_datetime: Birth datetime (UTC or local with timezone).
            moon_longitude: Moon's sidereal longitude in degrees.
            num_cycles: Number of 120-year cycles to generate (default: 1).

        Returns:
            VimshottariDashaTree model.
        """
        nak_placement = get_nakshatra_placement(moon_longitude)
        nak_id = nak_placement["id"]
        nak_name = nak_placement["sanskrit_name"]
        elapsed_fraction = nak_placement["elapsed_fraction"]
        birth_md_lord = nak_placement["lord"]
        birth_md_total_years = nak_placement["dasha_years"]

        # Balance remaining at birth
        balance_fraction = 1.0 - elapsed_fraction
        balance_years = birth_md_total_years * balance_fraction

        # Find starting index in standard Vimshottari sequence
        order_lords = [entry[0] for entry in VIMSHOTTARI_DASHA_ORDER]
        order_years = {entry[0]: entry[1] for entry in VIMSHOTTARI_DASHA_ORDER}
        start_idx = order_lords.index(birth_md_lord)

        mahadashas: list[MahadashaNode] = []
        current_time = birth_datetime

        total_mds_to_generate = 9 * num_cycles
        for i in range(total_mds_to_generate):
            lord = order_lords[(start_idx + i) % 9]
            full_years = order_years[lord]

            if i == 0:
                # First Mahadasha is proportional to remaining balance
                effective_years = balance_years
                # Theoretical full start time if uninterrupted
                elapsed_days = elapsed_fraction * full_years * DAYS_PER_SOLAR_YEAR
                theoretical_start = birth_datetime - timedelta(days=elapsed_days)
            else:
                effective_years = full_years
                theoretical_start = current_time

            md_duration_days = effective_years * DAYS_PER_SOLAR_YEAR
            md_end_time = current_time + timedelta(days=md_duration_days)

            # Generate 9 Antardashas within this Mahadasha
            antardashas = cls._generate_antardashas(
                md_lord=lord,
                md_start=current_time,
                md_end=md_end_time,
                theoretical_md_start=theoretical_start,
                is_birth_md=(i == 0),
                elapsed_fraction=elapsed_fraction if i == 0 else 0.0,
            )

            mahadashas.append(
                MahadashaNode(
                    lord=lord,
                    start_date=current_time,
                    end_date=md_end_time,
                    duration_days=md_duration_days,
                    antardashas=antardashas,
                )
            )
            current_time = md_end_time

        return VimshottariDashaTree(
            birth_datetime=birth_datetime,
            moon_nakshatra_id=nak_id,
            moon_nakshatra_name=nak_name,
            birth_mahadasha_lord=birth_md_lord,
            birth_balance_fraction=balance_fraction,
            birth_balance_years=balance_years,
            mahadashas=mahadashas,
        )

    @classmethod
    def _generate_antardashas(
        cls,
        md_lord: PlanetEnum,
        md_start: datetime,
        md_end: datetime,
        theoretical_md_start: datetime,
        is_birth_md: bool,
        elapsed_fraction: float,
    ) -> list[AntardashaNode]:
        """Generates 9 Antardashas (and their nested Pratyantardashas) for a Mahadasha."""
        order_lords = [entry[0] for entry in VIMSHOTTARI_DASHA_ORDER]
        order_years = {entry[0]: entry[1] for entry in VIMSHOTTARI_DASHA_ORDER}

        md_start_idx = order_lords.index(md_lord)
        md_full_years = order_years[md_lord]

        antardashas: list[AntardashaNode] = []
        cur_ad_start = theoretical_md_start

        for j in range(9):
            ad_lord = order_lords[(md_start_idx + j) % 9]
            ad_lord_years = order_years[ad_lord]

            # Standard AD duration = (MD_years * AD_years / 120) years
            ad_duration_years = (md_full_years * ad_lord_years) / TOTAL_VIMSHOTTARI_YEARS
            ad_duration_days = ad_duration_years * DAYS_PER_SOLAR_YEAR
            cur_ad_end = cur_ad_start + timedelta(days=ad_duration_days)

            if is_birth_md:
                # If this AD finished before birth, skip it
                if cur_ad_end <= md_start:
                    cur_ad_start = cur_ad_end
                    continue

                # If this AD spans across the birth moment, clip its start to birth time
                effective_start = max(cur_ad_start, md_start)
            else:
                effective_start = cur_ad_start

            effective_end = min(cur_ad_end, md_end)
            effective_duration_days = (effective_end - effective_start).total_seconds() / 86400.0

            # Generate Pratyantardashas
            pratyantardashas = cls._generate_pratyantardashas(
                md_lord=md_lord,
                ad_lord=ad_lord,
                ad_start=effective_start,
                ad_end=effective_end,
                theoretical_ad_start=cur_ad_start,
                is_birth_ad=is_birth_md and (cur_ad_start < md_start),
            )

            antardashas.append(
                AntardashaNode(
                    lord=ad_lord,
                    start_date=effective_start,
                    end_date=effective_end,
                    duration_days=effective_duration_days,
                    pratyantardashas=pratyantardashas,
                )
            )
            cur_ad_start = cur_ad_end

        return antardashas

    @classmethod
    def _generate_pratyantardashas(
        cls,
        md_lord: PlanetEnum,
        ad_lord: PlanetEnum,
        ad_start: datetime,
        ad_end: datetime,
        theoretical_ad_start: datetime,
        is_birth_ad: bool,
    ) -> list[PratyantardashaNode]:
        """Generates 9 Pratyantardashas for an Antardasha."""
        order_lords = [entry[0] for entry in VIMSHOTTARI_DASHA_ORDER]
        order_years = {entry[0]: entry[1] for entry in VIMSHOTTARI_DASHA_ORDER}

        md_years = order_years[md_lord]
        ad_years = order_years[ad_lord]
        ad_start_idx = order_lords.index(ad_lord)

        pratyantardashas: list[PratyantardashaNode] = []
        cur_pd_start = theoretical_ad_start

        for k in range(9):
            pd_lord = order_lords[(ad_start_idx + k) % 9]
            pd_years = order_years[pd_lord]

            # PD duration = (MD_years * AD_years * PD_years / (120 * 120)) years
            pd_duration_years = (md_years * ad_years * pd_years) / (TOTAL_VIMSHOTTARI_YEARS * TOTAL_VIMSHOTTARI_YEARS)
            pd_duration_days = pd_duration_years * DAYS_PER_SOLAR_YEAR
            cur_pd_end = cur_pd_start + timedelta(days=pd_duration_days)

            if is_birth_ad:
                if cur_pd_end <= ad_start:
                    cur_pd_start = cur_pd_end
                    continue
                effective_start = max(cur_pd_start, ad_start)
            else:
                effective_start = cur_pd_start

            effective_end = min(cur_pd_end, ad_end)
            effective_duration_days = (effective_end - effective_start).total_seconds() / 86400.0

            pratyantardashas.append(
                PratyantardashaNode(
                    lord=pd_lord,
                    start_date=effective_start,
                    end_date=effective_end,
                    duration_days=effective_duration_days,
                )
            )
            cur_pd_start = cur_pd_end

        return pratyantardashas

    @classmethod
    def get_current_dasha(
        cls,
        dasha_tree: VimshottariDashaTree,
        target_date: datetime,
    ) -> Optional[tuple[MahadashaNode, AntardashaNode, PratyantardashaNode]]:
        """Finds the active (MD, AD, PD) triplet for any target timestamp."""
        for md in dasha_tree.mahadashas:
            if md.start_date <= target_date <= md.end_date:
                for ad in md.antardashas:
                    if ad.start_date <= target_date <= ad.end_date:
                        for pd in ad.pratyantardashas:
                            if pd.start_date <= target_date <= pd.end_date:
                                return md, ad, pd
                        return md, ad, ad.pratyantardashas[-1]
                return md, md.antardashas[-1], md.antardashas[-1].pratyantardashas[-1]
        return None
