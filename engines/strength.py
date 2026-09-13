"""Algorithmic Planetary Strength Engine (Composite Vedic Bala Index).

Synthesizes classical Parashari principles into a normalized 0-100% composite strength score:
1. Sthana Bala / Sign Dignity & Placement (0-35 points):
   - Exaltation (35), Moolatrikona (30), Own Sign (26), Great Friend (21), Friend (17),
     Neutral (13), Enemy (8), Great Enemy (4), Debilitation (0 or 18 with Neechabhanga).
   - Vargottama bonus (+5 pts, capped at 35).
2. Dik Bala / Directional Strength (0-25 points):
   - Sun & Mars peak in 10th House (South / Zenith)
   - Jupiter & Mercury peak in 1st House (East / Lagna)
   - Venus & Moon peak in 4th House (North / Nadir)
   - Saturn peaks in 7th House (West / Setting)
   - Linear attenuation across intervening houses to 0 at opposite house.
3. Ashtakavarga BAV Strength (0-25 points):
   - 0 to 8 bindus scaled proportionally (8 bindus = 25.0 pts, 4 bindus = 12.5 pts).
4. Drishti Bala / Aspect Balance (0-15 points):
   - Baseline 7.5 points.
   - Benefic aspects received (+2.5 pts per benefic aspect from Jupiter, Venus, Mercury).
   - Malefic aspects received (-2.0 pts per malefic aspect from Saturn, Mars, Rahu, Ketu, Sun).
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field

from core.constants import PlanetEnum
from engines.ashtakavarga import AshtakavargaFullReport
from engines.aspects import AspectsReport
from engines.dignity import DignityEngine, DignityState
from engines.friendships import PanchaDhaMaitriReport
from schemas.models import UnifiedChartData


class StrengthBreakdown(BaseModel):
    sthana_score: float = Field(ge=0.0, le=35.0, description="Dignity and Kshetra points (max 35)")
    dik_score: float = Field(ge=0.0, le=25.0, description="Directional strength points (max 25)")
    bav_score: float = Field(ge=0.0, le=25.0, description="Ashtakavarga bindu strength points (max 25)")
    drishti_score: float = Field(ge=0.0, le=15.0, description="Aspect influence points (max 15)")


class PlanetaryStrengthProfile(BaseModel):
    planet: str
    total_score: float = Field(ge=0.0, le=100.0, description="Composite Vedic Strength (0-100%)")
    percentage_str: str
    grade: str  # Very Strong, Strong, Moderate, Weak, Afflicted
    grade_color: str
    breakdown: StrengthBreakdown
    dik_bala_peak_house: int
    current_house: int


class PlanetaryStrengthReport(BaseModel):
    profiles: Dict[str, PlanetaryStrengthProfile] = Field(default_factory=dict)
    strongest_planet: str = ""
    weakest_planet: str = ""


# Peak houses for directional strength (BPHS Chapter 27)
DIK_BALA_PEAKS: Dict[PlanetEnum, int] = {
    PlanetEnum.SUN: 10,
    PlanetEnum.MARS: 10,
    PlanetEnum.JUPITER: 1,
    PlanetEnum.MERCURY: 1,
    PlanetEnum.VENUS: 4,
    PlanetEnum.MOON: 4,
    PlanetEnum.SATURN: 7,
}


class PlanetaryStrengthEngine:
    """Computes normalized composite Vedic strength index for all natal planets."""

    @classmethod
    def evaluate(
        cls,
        chart: UnifiedChartData,
        ashtakavarga_report: AshtakavargaFullReport,
        aspects_report: AspectsReport,
        friendships_report: PanchaDhaMaitriReport,
        neechabhanga_planets: Optional[set] = None,
    ) -> PlanetaryStrengthReport:
        if neechabhanga_planets is None:
            neechabhanga_planets = set()

        asc_sign_id = chart.angles.ascendant_sign.id
        profiles: Dict[str, PlanetaryStrengthProfile] = {}

        classical_planets = [
            PlanetEnum.SUN, PlanetEnum.MOON, PlanetEnum.MARS, PlanetEnum.MERCURY,
            PlanetEnum.JUPITER, PlanetEnum.VENUS, PlanetEnum.SATURN, PlanetEnum.RAHU, PlanetEnum.KETU
        ]

        for p_enum in classical_planets:
            if p_enum not in chart.planets:
                continue

            p_pos = chart.planets[p_enum]
            p_sign_id = p_pos.sign.id
            house_num = ((p_sign_id - asc_sign_id) % 12) + 1

            # 1. Sthana Bala / Dignity (0 - 35 pts)
            intra_deg = p_pos.sign.intra_sign_degree
            dig_rep = DignityEngine.evaluate_planet_dignity(
                planet=p_enum,
                sign_id=p_sign_id,
                sign_name=p_pos.sign.sanskrit_name,
                degree_in_sign=intra_deg,
                neechabhanga_planets=neechabhanga_planets,
            )

            # Check Kshetra from PanchaDhaMaitri
            maitri_prof = friendships_report.profiles.get(p_enum.value)
            disp_rel = maitri_prof.dispositor_relationship if maitri_prof else "Neutral"

            if dig_rep.is_exalted:
                sthana_pts = 35.0
            elif dig_rep.is_moolatrikona:
                sthana_pts = 30.0
            elif dig_rep.is_own_sign:
                sthana_pts = 26.0
            elif dig_rep.is_debilitated:
                sthana_pts = 18.0 if dig_rep.has_neechabhanga else 0.0
            elif "Great Friend" in disp_rel:
                sthana_pts = 21.0
            elif "Friend" in disp_rel:
                sthana_pts = 17.0
            elif "Enemy" in disp_rel and "Great" not in disp_rel:
                sthana_pts = 8.0
            elif "Great Enemy" in disp_rel:
                sthana_pts = 4.0
            else:
                sthana_pts = 13.0  # Neutral / Sama

            # 2. Dik Bala / Directional Strength (0 - 25 pts)
            peak_house = DIK_BALA_PEAKS.get(p_enum, 1)
            if p_enum in (PlanetEnum.RAHU, PlanetEnum.KETU):
                dik_pts = 12.5  # Shadow nodes are directionally neutral
            else:
                raw_diff = abs(house_num - peak_house)
                shortest_dist = min(raw_diff, 12 - raw_diff)  # 0 to 6
                # 0 diff = 25 pts, 6 diff = 0 pts
                dik_pts = round(25.0 * (1.0 - (shortest_dist / 6.0)), 1)

            # 3. Ashtakavarga BAV Strength (0 - 25 pts)
            if p_enum.value in ashtakavarga_report.bhinna:
                bav_data = ashtakavarga_report.bhinna[p_enum.value]
                # Find bindus for this sign
                bindus = 4  # fallback average
                for sign_b in bav_data.signs:
                    if sign_b.sign_id == p_sign_id:
                        bindus = sign_b.raw_bindus
                        break
                bav_pts = min(25.0, round((bindus / 8.0) * 25.0, 1))
            else:
                # Nodes use SAV total of sign scaled
                sav_signs = ashtakavarga_report.sarvashtakavarga
                sav_bindus = 28
                for s in sav_signs:
                    if s.sign_id == p_sign_id:
                        sav_bindus = s.total_bindus
                        break
                bav_pts = min(25.0, round((sav_bindus / 56.0) * 25.0, 1))

            # 4. Drishti Bala / Aspect Balance (0 - 15 pts)
            # Baseline: 7.5 pts
            drishti_pts = 7.5
            graha_aspect = aspects_report.planets_aspects.get(p_enum.value)
            if graha_aspect and graha_aspect.aspects_received:
                for asp in graha_aspect.aspects_received:
                    if asp.is_benefic:
                        drishti_pts += 2.5
                    else:
                        drishti_pts -= 2.0
            drishti_pts = max(0.0, min(15.0, round(drishti_pts, 1)))

            # Total Composite Score
            total_score = round(sthana_pts + dik_pts + bav_pts + drishti_pts, 1)
            total_score = max(0.0, min(100.0, total_score))

            if total_score >= 80.0:
                grade = "Very Strong"
                color = "#059669"  # Emerald
            elif total_score >= 65.0:
                grade = "Strong"
                color = "#16A34A"  # Green
            elif total_score >= 50.0:
                grade = "Moderate"
                color = "#CA8A04"  # Amber/Gold
            elif total_score >= 35.0:
                grade = "Weak"
                color = "#EA580C"  # Orange
            else:
                grade = "Afflicted"
                color = "#DC2626"  # Red

            profiles[p_enum.value] = PlanetaryStrengthProfile(
                planet=p_enum.value,
                total_score=total_score,
                percentage_str=f"{int(round(total_score))}%",
                grade=grade,
                grade_color=color,
                breakdown=StrengthBreakdown(
                    sthana_score=sthana_pts,
                    dik_score=dik_pts,
                    bav_score=bav_pts,
                    drishti_score=drishti_pts,
                ),
                dik_bala_peak_house=peak_house,
                current_house=house_num,
            )

        # Identify strongest and weakest planets
        sorted_planets = sorted(profiles.items(), key=lambda x: x[1].total_score, reverse=True)
        strongest = sorted_planets[0][0] if sorted_planets else ""
        weakest = sorted_planets[-1][0] if sorted_planets else ""

        return PlanetaryStrengthReport(
            profiles=profiles,
            strongest_planet=strongest,
            weakest_planet=weakest,
        )
