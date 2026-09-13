"""Classical Vedic Ashtakavarga Calculation Engine.

Adheres to Brihat Parashara Hora Shastra (BPHS Chapters 66–72) and Phaladeepika:
- 8 Contribution sources (7 Grahas + Lagna)
- 7 Individual Bhinnashtakavarga (BAV) tables (Sun: 48, Moon: 49, Mars: 39,
  Mercury: 54, Jupiter: 56, Venus: 52, Saturn: 39)
- Master Sarvashtakavarga (SAV) with cosmic invariant sum of strictly 337 bindus
- Bhavashtakavarga (house-wise distribution relative to natal Lagna)
- Trikona Shodhana (Triplicity Reduction across Agni, Prithvi, Vayu, Jala trines)
- Ekadhipatya Shodhana (Dual-ownership Reduction with planetary occupancy rules)
- Pinda Sadhana: Rashi Pinda, Graha Pinda, and Yoga Pinda (Shodya Pinda)
"""

from typing import Any, Dict, List, Set, Tuple
from pydantic import BaseModel, Field

from core.constants import PlanetEnum, ZODIAC_SIGNS
from schemas.models import UnifiedChartData


# =============================================================================
# Classical BPHS Bindu Contribution Matrix (7 Grahas from 8 Reference Sources)
# =============================================================================

BPHS_CONTRIBUTIONS: Dict[PlanetEnum, Dict[Any, Set[int]]] = {
    PlanetEnum.SUN: {
        PlanetEnum.SUN: {1, 2, 4, 7, 8, 9, 10, 11},
        PlanetEnum.MOON: {3, 6, 10, 11},
        PlanetEnum.MARS: {1, 2, 4, 7, 8, 9, 10, 11},
        PlanetEnum.MERCURY: {3, 5, 6, 9, 10, 11, 12},
        PlanetEnum.JUPITER: {5, 6, 9, 11},
        PlanetEnum.VENUS: {6, 7, 12},
        PlanetEnum.SATURN: {1, 2, 4, 7, 8, 9, 10, 11},
        "LAGNA": {3, 4, 6, 10, 11, 12},
    },
    PlanetEnum.MOON: {
        PlanetEnum.SUN: {3, 6, 7, 8, 10, 11},
        PlanetEnum.MOON: {1, 3, 6, 7, 10, 11},
        PlanetEnum.MARS: {2, 3, 5, 6, 9, 10, 11},
        PlanetEnum.MERCURY: {1, 3, 4, 5, 7, 8, 10, 11},
        PlanetEnum.JUPITER: {1, 4, 7, 8, 10, 11, 12},
        PlanetEnum.VENUS: {3, 4, 5, 7, 9, 10, 11},
        PlanetEnum.SATURN: {3, 5, 6, 11},
        "LAGNA": {3, 6, 10, 11},
    },
    PlanetEnum.MARS: {
        PlanetEnum.SUN: {3, 5, 6, 10, 11},
        PlanetEnum.MOON: {3, 6, 11},
        PlanetEnum.MARS: {1, 2, 4, 7, 8, 10, 11},
        PlanetEnum.MERCURY: {3, 5, 6, 11},
        PlanetEnum.JUPITER: {6, 10, 11, 12},
        PlanetEnum.VENUS: {6, 8, 11, 12},
        PlanetEnum.SATURN: {1, 4, 7, 8, 9, 10, 11},
        "LAGNA": {1, 3, 6, 10, 11},
    },
    PlanetEnum.MERCURY: {
        PlanetEnum.SUN: {5, 6, 9, 11, 12},
        PlanetEnum.MOON: {2, 4, 6, 8, 10, 11},
        PlanetEnum.MARS: {1, 2, 4, 7, 8, 9, 10, 11},
        PlanetEnum.MERCURY: {1, 3, 5, 6, 9, 10, 11, 12},
        PlanetEnum.JUPITER: {6, 8, 11, 12},
        PlanetEnum.VENUS: {1, 2, 3, 4, 5, 8, 9, 11},
        PlanetEnum.SATURN: {1, 2, 4, 7, 8, 9, 10, 11},
        "LAGNA": {1, 2, 4, 6, 8, 10, 11},
    },
    PlanetEnum.JUPITER: {
        PlanetEnum.SUN: {1, 2, 3, 4, 7, 8, 9, 10, 11},
        PlanetEnum.MOON: {2, 5, 7, 9, 11},
        PlanetEnum.MARS: {1, 2, 4, 7, 8, 10, 11},
        PlanetEnum.MERCURY: {1, 2, 4, 5, 6, 9, 10, 11},
        PlanetEnum.JUPITER: {1, 2, 3, 4, 7, 8, 10, 11},
        PlanetEnum.VENUS: {2, 5, 6, 9, 10, 11},
        PlanetEnum.SATURN: {3, 5, 6, 12},
        "LAGNA": {1, 2, 4, 5, 6, 7, 9, 10, 11},
    },
    PlanetEnum.VENUS: {
        PlanetEnum.SUN: {8, 11, 12},
        PlanetEnum.MOON: {1, 2, 3, 4, 5, 8, 9, 11, 12},
        PlanetEnum.MARS: {3, 5, 6, 9, 11, 12},
        PlanetEnum.MERCURY: {3, 5, 6, 9, 11},
        PlanetEnum.JUPITER: {5, 8, 9, 10, 11},
        PlanetEnum.VENUS: {1, 2, 3, 4, 5, 8, 9, 10, 11},
        PlanetEnum.SATURN: {3, 4, 5, 8, 9, 10, 11},
        "LAGNA": {1, 2, 3, 4, 5, 8, 9, 11},
    },
    PlanetEnum.SATURN: {
        PlanetEnum.SUN: {1, 2, 4, 7, 8, 10, 11},
        PlanetEnum.MOON: {3, 6, 11},
        PlanetEnum.MARS: {3, 5, 6, 10, 11, 12},
        PlanetEnum.MERCURY: {6, 8, 9, 10, 11, 12},
        PlanetEnum.JUPITER: {5, 6, 11, 12},
        PlanetEnum.VENUS: {6, 11, 12},
        PlanetEnum.SATURN: {3, 5, 6, 11},
        "LAGNA": {1, 3, 4, 6, 10, 11},
    },
}

# The 4 Trikona Triplicities (1-based sign IDs)
TRIKONAS: List[Tuple[int, int, int]] = [
    (1, 5, 9),    # Agni (Fire): Aries, Leo, Sagittarius
    (2, 6, 10),   # Prithvi (Earth): Taurus, Virgo, Capricorn
    (3, 7, 11),   # Vayu (Air): Gemini, Libra, Aquarius
    (4, 8, 12),   # Jala (Water): Cancer, Scorpio, Pisces
]

# Dual ownership pairs (Mars, Venus, Mercury, Jupiter, Saturn)
DUAL_PAIRS: List[Tuple[PlanetEnum, int, int]] = [
    (PlanetEnum.MARS, 1, 8),      # Aries & Scorpio
    (PlanetEnum.VENUS, 2, 7),     # Taurus & Libra
    (PlanetEnum.MERCURY, 3, 6),   # Gemini & Virgo
    (PlanetEnum.JUPITER, 9, 12),  # Sagittarius & Pisces
    (PlanetEnum.SATURN, 10, 11),  # Capricorn & Aquarius
]

# Rashi Multipliers (Rashi Gunakara) for Pinda Sadhana
RASHI_GUNAKARA: Dict[int, int] = {
    1: 7, 2: 10, 3: 8, 4: 4, 5: 10, 6: 5,
    7: 7, 8: 8, 9: 9, 10: 5, 11: 11, 12: 12,
}

# Graha Multipliers (Graha Gunakara) for Pinda Sadhana
GRAHA_GUNAKARA: Dict[PlanetEnum, int] = {
    PlanetEnum.SUN: 5,
    PlanetEnum.MOON: 5,
    PlanetEnum.MARS: 8,
    PlanetEnum.MERCURY: 5,
    PlanetEnum.JUPITER: 10,
    PlanetEnum.VENUS: 7,
    PlanetEnum.SATURN: 5,
}

# 8 Classical Kakshas of 3° 45' each (BPHS Ch. 68 - Prastarashtakavarga)
# Ordered by orbital speed from slowest to fastest graha, ending with Lagna:
KAKSHA_LORDS: List[str] = [
    "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna"
]
KAKSHA_LORDS_SANSKRIT: List[str] = [
    "Shani", "Guru", "Mangala", "Surya", "Shukra", "Budha", "Chandra", "Lagna"
]


# =============================================================================
# Pydantic Output Schemas
# =============================================================================

class KakshaItem(BaseModel):
    kaksha_number: int
    lord: str
    lord_sanskrit: str
    start_deg: float
    end_deg: float
    range_str: str
    is_current: bool
    bindu_contributions_count: int
    contributed_planets: List[str]


class LagnaKakshaReport(BaseModel):
    lagna_sign_id: int
    lagna_sign_name: str
    lagna_sign_sanskrit: str
    lagna_degree_formatted: str
    intra_sign_degree: float
    active_kaksha_number: int
    active_kaksha_lord: str
    active_kaksha_lord_sanskrit: str
    active_kaksha_range: str
    kaksha_progress_pct: float
    active_kaksha_bindus: int
    kakshas: List[KakshaItem]


class BAVSignDetail(BaseModel):
    sign_id: int
    sign_name: str
    sign_sanskrit: str
    house_from_lagna: int
    raw_bindus: int
    trikona_reduced: int
    ekadhipatya_reduced: int
    contributions: Dict[str, int]


class PlanetBAVReport(BaseModel):
    planet: str
    total_raw_bindus: int
    total_trikona_reduced: int
    total_ekadhipatya_reduced: int
    rashi_pinda: int
    graha_pinda: int
    yoga_pinda: int
    signs: List[BAVSignDetail]


class SAVSignDetail(BaseModel):
    sign_id: int
    sign_name: str
    sign_sanskrit: str
    house_from_lagna: int
    total_bindus: int
    breakdown: Dict[str, int]
    evaluation: str  # "Strong (>=30)", "Average (26-29)", "Challenging (<26)"


class SAVSummary(BaseModel):
    total_bindus: int = 337
    average_bindus_per_sign: float = 28.08
    strongest_sign: str
    strongest_sign_bindus: int
    weakest_sign: str
    weakest_sign_bindus: int
    strongest_house: int
    strongest_house_bindus: int
    weakest_house: int
    weakest_house_bindus: int
    benefic_signs_count: int
    challenging_signs_count: int


class AshtakavargaFullReport(BaseModel):
    summary: SAVSummary
    sarvashtakavarga: List[SAVSignDetail]
    bhinna: Dict[str, PlanetBAVReport]
    lagna_kaksha: LagnaKakshaReport


# =============================================================================
# Classical Calculation Engine
# =============================================================================

class AshtakavargaEngine:
    """Core BPHS Classical Ashtakavarga Calculation Engine."""

    @classmethod
    def evaluate(cls, chart: UnifiedChartData, sign_mode: str = "sanskrit") -> AshtakavargaFullReport:
        lagna_sign = chart.angles.ascendant_sign.id

        # 1. Resolve 8 Reference Signs
        ref_signs: Dict[Any, int] = {
            PlanetEnum.SUN: chart.planets[PlanetEnum.SUN].sign.id,
            PlanetEnum.MOON: chart.planets[PlanetEnum.MOON].sign.id,
            PlanetEnum.MARS: chart.planets[PlanetEnum.MARS].sign.id,
            PlanetEnum.MERCURY: chart.planets[PlanetEnum.MERCURY].sign.id,
            PlanetEnum.JUPITER: chart.planets[PlanetEnum.JUPITER].sign.id,
            PlanetEnum.VENUS: chart.planets[PlanetEnum.VENUS].sign.id,
            PlanetEnum.SATURN: chart.planets[PlanetEnum.SATURN].sign.id,
            "LAGNA": lagna_sign,
        }

        # Track signs occupied by the 7 classical planets
        planet_signs: Dict[PlanetEnum, int] = {
            p: chart.planets[p].sign.id
            for p in GRAHA_GUNAKARA
        }
        occupied_signs: Set[int] = set(planet_signs.values())

        # 2. Compute Raw Bhinnashtakavarga (BAV) for each of the 7 planets
        raw_bav_maps: Dict[PlanetEnum, Dict[int, int]] = {}
        sources_breakdown: Dict[PlanetEnum, Dict[int, Dict[str, int]]] = {}

        for planet, rules in BPHS_CONTRIBUTIONS.items():
            p_map = {s: 0 for s in range(1, 13)}
            s_map: Dict[int, Dict[str, int]] = {s: {} for s in range(1, 13)}

            for ref_source, allowed_houses in rules.items():
                r_sign = ref_signs[ref_source]
                source_label = ref_source.value if isinstance(ref_source, PlanetEnum) else "Lagna"
                for s in range(1, 13):
                    h_from_r = ((s - r_sign) % 12) + 1
                    has_bindu = 1 if h_from_r in allowed_houses else 0
                    p_map[s] += has_bindu
                    s_map[s][source_label] = has_bindu

            raw_bav_maps[planet] = p_map
            sources_breakdown[planet] = s_map

        # 3. Compute Sarvashtakavarga (SAV) by summing all 7 BAVs
        sav_totals: Dict[int, int] = {s: 0 for s in range(1, 13)}
        sav_breakdowns: Dict[int, Dict[str, int]] = {s: {} for s in range(1, 13)}

        for planet, p_map in raw_bav_maps.items():
            for s in range(1, 13):
                sav_totals[s] += p_map[s]
                sav_breakdowns[s][planet.value] = p_map[s]

        # 4. Perform Trikona & Ekadhipatya Shodhana and Pinda Sadhana
        bhinna_reports: Dict[str, PlanetBAVReport] = {}

        for planet, raw_map in raw_bav_maps.items():
            trikona_map = cls._trikona_shodhana(raw_map)
            ekadh_map = cls._ekadhipatya_shodhana(trikona_map, occupied_signs)
            rp, gp, yp = cls._calculate_shodya_pinda(ekadh_map, planet_signs)

            sign_details: List[BAVSignDetail] = []
            for s in range(1, 13):
                h_lagna = ((s - lagna_sign) % 12) + 1
                s_name = ZODIAC_SIGNS[s]["english_name"] if sign_mode == "english" else ZODIAC_SIGNS[s]["sanskrit_name"]
                sign_details.append(
                    BAVSignDetail(
                        sign_id=s,
                        sign_name=s_name,
                        sign_sanskrit=ZODIAC_SIGNS[s]["sanskrit_name"],
                        house_from_lagna=h_lagna,
                        raw_bindus=raw_map[s],
                        trikona_reduced=trikona_map[s],
                        ekadhipatya_reduced=ekadh_map[s],
                        contributions=sources_breakdown[planet][s],
                    )
                )

            bhinna_reports[planet.value] = PlanetBAVReport(
                planet=planet.value,
                total_raw_bindus=sum(raw_map.values()),
                total_trikona_reduced=sum(trikona_map.values()),
                total_ekadhipatya_reduced=sum(ekadh_map.values()),
                rashi_pinda=rp,
                graha_pinda=gp,
                yoga_pinda=yp,
                signs=sign_details,
            )

        # 5. Build Sarvashtakavarga (SAV) Sign Details
        sav_sign_details: List[SAVSignDetail] = []
        house_sav_map: Dict[int, int] = {}

        for s in range(1, 13):
            h_lagna = ((s - lagna_sign) % 12) + 1
            tot = sav_totals[s]
            house_sav_map[h_lagna] = tot

            eval_str = "Strong (≥30)" if tot >= 30 else ("Average (26–29)" if tot >= 26 else "Challenging (<26)")
            s_name = ZODIAC_SIGNS[s]["english_name"] if sign_mode == "english" else ZODIAC_SIGNS[s]["sanskrit_name"]
            sav_sign_details.append(
                SAVSignDetail(
                    sign_id=s,
                    sign_name=s_name,
                    sign_sanskrit=ZODIAC_SIGNS[s]["sanskrit_name"],
                    house_from_lagna=h_lagna,
                    total_bindus=tot,
                    breakdown=sav_breakdowns[s],
                    evaluation=eval_str,
                )
            )

        # 6. Build Summary Metrics
        sorted_signs = sorted(sav_totals.items(), key=lambda item: item[1])
        weakest_s_id, weakest_s_val = sorted_signs[0]
        strongest_s_id, strongest_s_val = sorted_signs[-1]

        sorted_houses = sorted(house_sav_map.items(), key=lambda item: item[1])
        weakest_h_id, weakest_h_val = sorted_houses[0]
        strongest_h_id, strongest_h_val = sorted_houses[-1]

        weakest_s_name = ZODIAC_SIGNS[weakest_s_id]["english_name"] if sign_mode == "english" else ZODIAC_SIGNS[weakest_s_id]["sanskrit_name"]
        strongest_s_name = ZODIAC_SIGNS[strongest_s_id]["english_name"] if sign_mode == "english" else ZODIAC_SIGNS[strongest_s_id]["sanskrit_name"]

        summary = SAVSummary(
            total_bindus=sum(sav_totals.values()),
            average_bindus_per_sign=round(sum(sav_totals.values()) / 12.0, 2),
            strongest_sign=strongest_s_name,
            strongest_sign_bindus=strongest_s_val,
            weakest_sign=weakest_s_name,
            weakest_sign_bindus=weakest_s_val,
            strongest_house=strongest_h_id,
            strongest_house_bindus=strongest_h_val,
            weakest_house=weakest_h_id,
            weakest_house_bindus=weakest_h_val,
            benefic_signs_count=sum(1 for v in sav_totals.values() if v >= 28),
            challenging_signs_count=sum(1 for v in sav_totals.values() if v < 28),
        )

        # 7. Compute Lagna Kaksha (Prastarashtakavarga 8 Subdivisions - BPHS Ch. 68)
        lagna_deg = chart.angles.ascendant_sign.intra_sign_degree
        active_k_idx = min(7, max(0, int(lagna_deg / 3.75)))
        active_k_num = active_k_idx + 1
        active_k_lord = KAKSHA_LORDS[active_k_idx]
        active_k_lord_sanskrit = KAKSHA_LORDS_SANSKRIT[active_k_idx]

        active_k_start = active_k_idx * 3.75
        kaksha_progress = round(max(0.0, min(100.0, ((lagna_deg - active_k_start) / 3.75) * 100.0)), 1)

        kaksha_items: List[KakshaItem] = []
        for k_idx in range(8):
            k_start = k_idx * 3.75
            k_end = (k_idx + 1) * 3.75
            s_deg_int = int(k_start)
            s_min_int = int(round((k_start % 1) * 60))
            e_deg_int = int(k_end)
            e_min_int = int(round((k_end % 1) * 60))
            if e_min_int == 60:
                e_deg_int += 1
                e_min_int = 0
            range_str = f"{s_deg_int:02d}°{s_min_int:02d}' – {e_deg_int:02d}°{e_min_int:02d}'"

            k_lord = KAKSHA_LORDS[k_idx]
            k_lord_sans = KAKSHA_LORDS_SANSKRIT[k_idx]
            is_curr = (k_idx == active_k_idx)

            # Determine which Grahas received a bindu from this Kaksha Lord in Lagna sign
            contributed_grahas: List[str] = []
            for p in PlanetEnum:
                if p in sources_breakdown:
                    if sources_breakdown[p][lagna_sign].get(k_lord, 0) == 1:
                        contributed_grahas.append(p.value)

            kaksha_items.append(
                KakshaItem(
                    kaksha_number=k_idx + 1,
                    lord=k_lord,
                    lord_sanskrit=k_lord_sans,
                    start_deg=k_start,
                    end_deg=k_end,
                    range_str=range_str,
                    is_current=is_curr,
                    bindu_contributions_count=len(contributed_grahas),
                    contributed_planets=contributed_grahas,
                )
            )

        active_kaksha_bindus = kaksha_items[active_k_idx].bindu_contributions_count
        active_kaksha_range = kaksha_items[active_k_idx].range_str
        lagna_s_name = ZODIAC_SIGNS[lagna_sign]["english_name"] if sign_mode == "english" else ZODIAC_SIGNS[lagna_sign]["sanskrit_name"]

        lagna_kaksha_report = LagnaKakshaReport(
            lagna_sign_id=lagna_sign,
            lagna_sign_name=lagna_s_name,
            lagna_sign_sanskrit=ZODIAC_SIGNS[lagna_sign]["sanskrit_name"],
            lagna_degree_formatted=chart.angles.ascendant_sign.dms.formatted,
            intra_sign_degree=round(lagna_deg, 4),
            active_kaksha_number=active_k_num,
            active_kaksha_lord=active_k_lord,
            active_kaksha_lord_sanskrit=active_k_lord_sanskrit,
            active_kaksha_range=active_kaksha_range,
            kaksha_progress_pct=kaksha_progress,
            active_kaksha_bindus=active_kaksha_bindus,
            kakshas=kaksha_items,
        )

        return AshtakavargaFullReport(
            summary=summary,
            sarvashtakavarga=sav_sign_details,
            bhinna=bhinna_reports,
            lagna_kaksha=lagna_kaksha_report,
        )

    @classmethod
    def _trikona_shodhana(cls, bav_map: Dict[int, int]) -> Dict[int, int]:
        """Performs classical BPHS Trikona Shodhana (Triplicity Reduction)."""
        res = dict(bav_map)
        for s1, s2, s3 in TRIKONAS:
            b1, b2, b3 = res[s1], res[s2], res[s3]
            # 1. If all three are equal, make all 0
            if b1 == b2 == b3:
                res[s1] = res[s2] = res[s3] = 0
            # 2. If all three are non-zero, subtract the minimum from all three
            elif b1 > 0 and b2 > 0 and b3 > 0:
                m = min(b1, b2, b3)
                res[s1] -= m
                res[s2] -= m
                res[s3] -= m
            # 3. If one is 0 and two are non-zero, subtract the minimum of the two from both
            elif sum(1 for x in (b1, b2, b3) if x > 0) == 2:
                non_zeros = [x for x in (b1, b2, b3) if x > 0]
                m = min(non_zeros)
                if res[s1] > 0:
                    res[s1] -= m
                if res[s2] > 0:
                    res[s2] -= m
                if res[s3] > 0:
                    res[s3] -= m
            # 4. If two are 0, the one non-zero remains unchanged (no reduction)

        return res

    @classmethod
    def _ekadhipatya_shodhana(cls, trikona_map: Dict[int, int], occupied_signs: Set[int]) -> Dict[int, int]:
        """Performs classical BPHS Ekadhipatya Shodhana (Dual Ownership Reduction)."""
        res = dict(trikona_map)
        for _, s1, s2 in DUAL_PAIRS:
            b1, b2 = res[s1], res[s2]
            # If both are 0 or one is 0, no reduction is done
            if b1 == 0 or b2 == 0:
                continue

            occ1 = s1 in occupied_signs
            occ2 = s2 in occupied_signs

            # Case 1: Both signs occupied by planets -> No reduction
            if occ1 and occ2:
                continue
            # Case 2: Neither sign occupied by planets
            elif not occ1 and not occ2:
                if b1 == b2:
                    res[s1] = res[s2] = 0
                else:
                    m = min(b1, b2)
                    res[s1] = m
                    res[s2] = m
            # Case 3: One sign occupied, one unoccupied
            else:
                unocc = s1 if not occ1 else s2
                occ = s2 if not occ1 else s1
                b_unocc = res[unocc]
                b_occ = res[occ]

                if b_unocc >= b_occ:
                    res[unocc] = 0
                else:
                    res[unocc] = 0
                    res[occ] = b_occ - b_unocc

        return res

    @classmethod
    def _calculate_shodya_pinda(cls, reduced_map: Dict[int, int], planet_signs: Dict[PlanetEnum, int]) -> Tuple[int, int, int]:
        """Calculates Rashi Pinda, Graha Pinda, and Yoga Pinda."""
        rashi_pinda = sum(reduced_map[s] * RASHI_GUNAKARA[s] for s in range(1, 13))

        graha_pinda = 0
        for p, mult in GRAHA_GUNAKARA.items():
            occ_sign = planet_signs.get(p)
            if occ_sign:
                graha_pinda += reduced_map[occ_sign] * mult

        yoga_pinda = rashi_pinda + graha_pinda
        return rashi_pinda, graha_pinda, yoga_pinda
