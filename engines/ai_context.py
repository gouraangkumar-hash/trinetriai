"""AI Ground-Truth Context Engine (Vedic Dossier & Prompt Serializer).

Compiles exhaustive, deterministic astronomical and astrological facts from all domain
engines into a dense, token-optimized Markdown dossier and structured JSON payload.
Enables external LLMs (Gemini, Claude, GPT) to perform authoritative, non-hallucinatory
Vedic astrological synthesis.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.constants import PlanetEnum, ZODIAC_SIGNS
from engines.ashtakavarga import AshtakavargaFullReport
from engines.aspects import AspectsReport
from engines.friendships import PanchaDhaMaitriReport
from engines.functional import FunctionalReport
from engines.gochar import GocharReport
from engines.parashari import VimshottariDashaTree
from engines.strength import PlanetaryStrengthReport
from engines.yogas import YogaEvaluationReport
from schemas.models import UnifiedChartData


class AIDossierReport(BaseModel):
    """Complete serialized AI context payload and system prompt recommendation."""
    markdown_dossier: str
    system_prompt_recommendation: str
    structured_payload: Dict[str, Any]


class AIContextEngine:
    """Serializes complete multi-engine astrological state into zero-hallucination AI prompts."""

    @classmethod
    def generate(
        cls,
        chart: UnifiedChartData,
        yogas_report: YogaEvaluationReport,
        ashtakavarga_report: AshtakavargaFullReport,
        dashas: VimshottariDashaTree,
        gochar_report: GocharReport,
        aspects_report: AspectsReport,
        friendships_report: PanchaDhaMaitriReport,
        functional_report: FunctionalReport,
        strength_report: PlanetaryStrengthReport,
        dasha_summary: Dict[str, Any],
        birth_city: str = "Jaipur, India",
        effective_time_str: str = "14:30:00",
        effective_date_str: str = "1995-10-15",
    ) -> AIDossierReport:
        asc = chart.angles.ascendant_sign
        asc_nak = chart.angles.ascendant_nakshatra
        asc_sign_id = asc.id
        loc = chart.input_data.location

        # 1. Build Markdown Dossier
        lines: List[str] = []
        lines.append("# TRINETRIAI VEDIC ASTROLOGICAL DOSSIER (GROUND-TRUTH EPHEMERIS)")
        lines.append("")
        lines.append("## 1. NATAL BASELINE & ASTRONOMICAL ANCHORS")
        lines.append(f"- **Birth Location**: {birth_city} ({loc.latitude:.4f}°N, {loc.longitude:.4f}°E)")
        lines.append(f"- **Effective Date & Time**: {effective_date_str} {effective_time_str} ({loc.timezone_str})")
        lines.append(f"- **Ayanamsha**: {chart.ayanamsha_name.value} ({chart.ayanamsha_dms.formatted})")
        lines.append(f"- **Julian Day (UT)**: {chart.julian_day_ut:.6f} | **Julian Day (ET)**: {chart.julian_day_et:.6f}")
        lines.append(f"- **Lagna (Ascendant)**: {asc.sanskrit_name} ({asc.english_name}) at {asc.dms.formatted} | Nakshatra: {asc_nak.sanskrit_name} Pada {asc_nak.pada} (Lord: {asc_nak.lord.value})")
        lines.append(f"- **MC (Midheaven / 10th Cusp)**: {chart.angles.mc_sign.sanskrit_name} at {chart.angles.mc_dms.formatted}")
        lines.append(f"- **Lagna Modality**: {functional_report.lagna_modality} | **Badhaka House**: House {functional_report.badhaka_house} (Lord: {functional_report.badhaka_lord})")
        yk_str = ", ".join(functional_report.yogakaraka_planets) if functional_report.yogakaraka_planets else "None (Single graha rules Kendra+Trikona)"
        mar_str = ", ".join(functional_report.maraka_planets) if functional_report.maraka_planets else "None"
        lines.append(f"- **Yogakaraka Graha(s)**: {yk_str}")
        lines.append(f"- **Maraka Graha(s)**: {mar_str}")
        lines.append("")

        # 2. Planetary Placements & Composite Strength Table
        lines.append("## 2. PLANETARY PLACEMENTS & VEDIC STRENGTH MATRIX")
        lines.append("| Graha | Sign | Degree | House | Nakshatra | Motion | Dignity | Pancha-Dha Kshetra | Functional Role | Bala (%) | Grade |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|")

        classical_planets = [
            PlanetEnum.SUN, PlanetEnum.MOON, PlanetEnum.MARS, PlanetEnum.MERCURY,
            PlanetEnum.JUPITER, PlanetEnum.VENUS, PlanetEnum.SATURN, PlanetEnum.RAHU, PlanetEnum.KETU
        ]

        structured_planets = []
        for p_enum in classical_planets:
            if p_enum not in chart.planets:
                continue
            p = chart.planets[p_enum]
            h_num = ((p.sign.id - asc_sign_id) % 12) + 1
            mot = "Retrograde" if p.is_retrograde else "Direct"
            comb = " [Combust]" if p.is_combust else ""

            # Dignity
            maitri = friendships_report.profiles.get(p_enum.value)
            kshetra = maitri.dispositor_kshetra if maitri else "-"

            # Functional
            func = functional_report.profiles.get(p_enum.value)
            func_role = func.primary_role.value if func else "Neutral"
            if func and func.is_yogakaraka:
                func_role = "Yogakaraka"
            elif func and func.is_badhaka:
                func_role += " (Badhaka)"

            # Strength
            str_prof = strength_report.profiles.get(p_enum.value)
            bala_pct = str_prof.percentage_str if str_prof else "-"
            bala_grade = str_prof.grade if str_prof else "-"

            dignity_str = "Neutral"
            if p_enum in chart.planets:
                # Basic dignity label from maitri or dignity
                if "Own" in kshetra:
                    dignity_str = "Own Sign"
                elif "Adhi Mitra" in kshetra:
                    dignity_str = "Adhi Mitra Kshetra"
                elif "Shatru" in kshetra:
                    dignity_str = "Shatru Kshetra"
                elif "Mitra" in kshetra:
                    dignity_str = "Mitra Kshetra"

            row_line = (
                f"| **{p_enum.value}** | {p.sign.sanskrit_name} | {p.sign.dms.formatted} | House {h_num} | "
                f"{p.nakshatra.sanskrit_name} P{p.nakshatra.pada} | {mot}{comb} | {dignity_str} | "
                f"{kshetra} | {func_role} | {bala_pct} | {bala_grade} |"
            )
            lines.append(row_line)

            structured_planets.append({
                "planet": p_enum.value,
                "sign": p.sign.sanskrit_name,
                "sign_id": p.sign.id,
                "degree": p.sign.dms.formatted,
                "house": h_num,
                "nakshatra": f"{p.nakshatra.sanskrit_name} P{p.nakshatra.pada}",
                "nakshatra_lord": p.nakshatra.lord.value,
                "is_retrograde": p.is_retrograde,
                "is_combust": p.is_combust,
                "functional_nature": func_role,
                "dispositor_kshetra": kshetra,
                "strength_score": str_prof.total_score if str_prof else 0.0,
                "strength_grade": bala_grade,
            })

        lines.append("")

        # 3. Active Parashari Yogas & Doshas
        lines.append("## 3. ACTIVE CLASSICAL YOGAS & DOSHAS")
        lines.append(f"- **Total Yogas Identified**: {yogas_report.summary.total_yogas}")
        lines.append(f"- **Raja Yogas**: {yogas_report.summary.raja_count} | **Dhana Yogas**: {yogas_report.summary.dhana_count}")
        lines.append(f"- **Shani Sade Sati Status**: {yogas_report.summary.sade_sati_status}")
        lines.append(f"- **Kuja Dosha (Manglik)**: {yogas_report.summary.kuja_dosha_status}")
        lines.append("")
        lines.append("### Key Active Yogas:")
        for y in yogas_report.yogas:
            if y.is_active:
                lines.append(f"- **{y.name}** ({y.category}): {y.description} *(Planets: {', '.join(y.planets_involved)})*")
        lines.append("")

        # 4. 12 Bhavas (Houses) Energetics & Ashtakavarga
        lines.append("## 4. 12 BHAVAS (HOUSES) ASHTAKAVARGA & ENERGETIC MATRIX")
        lines.append("| House | Sign | Lord | SAV Bindus | Strength Status | Occupants | Aspecting Grahas |")
        lines.append("|---|---|---|---|---|---|---|")

        # Map occupants and aspects per house
        house_occupants: Dict[int, List[str]] = {h: [] for h in range(1, 13)}
        for p_enum in classical_planets:
            if p_enum in chart.planets:
                h = ((chart.planets[p_enum].sign.id - asc_sign_id) % 12) + 1
                house_occupants[h].append(p_enum.value)

        # Build SAV and Bhava Aspects lookup by house
        sav_by_house: Dict[int, int] = {s.house_from_lagna: s.total_bindus for s in ashtakavarga_report.sarvashtakavarga}
        bhava_aspects_by_house = {b.house_number: b for b in aspects_report.bhava_aspects}

        for h in range(1, 13):
            s_id = ((asc_sign_id + h - 2) % 12) + 1
            s_info = ZODIAC_SIGNS[s_id]
            s_lord = s_info["lord"].value
            bindus = sav_by_house.get(h, 28)
            status = "Strong (≥30)" if bindus >= 30 else ("Challenging (<26)" if bindus < 26 else "Average (26-29)")
            occ = ", ".join(house_occupants[h]) or "Vacant"

            # Check grahas aspecting this house
            b_asp = bhava_aspects_by_house.get(h)
            aspecting = []
            if b_asp:
                aspecting = b_asp.benefics_aspecting + b_asp.malefics_aspecting
            asp_str = ", ".join(aspecting) or "None"

            lines.append(f"| House {h} | {s_info['sanskrit_name']} | {s_lord} | **{bindus}** | {status} | {occ} | {asp_str} |")

        lines.append("")

        # 5. Running Vimshottari Dasha Hierarchy
        lines.append("## 5. VIMSHOTTARI DASHA CHRONOLOGY & RUNNING PERIOD")
        lines.append(f"- **Current Mahadasha (MD)**: {dasha_summary.get('md', '-')} ({dasha_summary.get('md_range', '-')})")
        lines.append(f"- **Current Antardasha (AD)**: {dasha_summary.get('ad', '-')} ({dasha_summary.get('ad_range', '-')})")
        lines.append(f"- **Current Pratyantardasha (PD)**: {dasha_summary.get('pd', '-')} ({dasha_summary.get('pd_range', '-')})")
        lines.append("")

        # 6. Real-Time Planetary Transits (Gochar)
        lines.append("## 6. ACTIVE REAL-TIME TRANSITS (GOCHAR)")
        lines.append(f"- **Transit Ephemeris Reference**: {gochar_report.summary.transit_date_formatted}")
        for t in gochar_report.transits:
            lines.append(
                f"- **Transit {t.planet}**: in {t.sign_name} ({t.degree_formatted}) -> House {t.house_from_lagna} from Lagna, "
                f"House {t.house_from_moon} from Natal Moon | SAV Bindus: {t.sav_bindus} ({t.classical_status})"
            )
        lines.append("")

        markdown_dossier = "\n".join(lines)

        # System Prompt Recommendation
        system_prompt = (
            "You are an expert, highly authoritative Vedic Astrologer (Jyotishi) trained in Brihat Parashara Hora Shastra, "
            "Jaimini Upadesha Sutras, and classical Phaladeepika principles.\n"
            "Below is the verified astronomical and astrological ground-truth fact sheet for a client's natal chart.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Adhere STRICTLY to the planetary signs, houses, nakshatras, dignities, yogas, and dasha periods specified in the dossier. "
            "DO NOT hallucinate or alter any planetary coordinates or house placements.\n"
            "2. Always analyze planetary actions through their Lagna-specific FUNCTIONAL NATURE (e.g. Yogakaraka, Maraka, Badhaka) "
            "rather than treating grahas as generically good or bad.\n"
            "3. Ground all predictions in the active Mahadasha/Antardasha/Pratyantardasha timeline and corroborate with Ashtakavarga bindu strengths.\n"
            "4. Provide constructive, spiritually sound, and psychologically empowering counseling with authentic classical remedies (Upayas) when afflicted periods are detected."
        )

        structured_payload = {
            "baseline": {
                "city": birth_city,
                "date": effective_date_str,
                "time": effective_time_str,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "timezone": loc.timezone_str,
                "ayanamsha": chart.ayanamsha_name.value,
                "lagna": asc.sanskrit_name,
                "lagna_degree": asc.dms.formatted,
                "lagna_nakshatra": f"{asc_nak.sanskrit_name} P{asc_nak.pada}",
                "badhaka_house": functional_report.badhaka_house,
                "badhaka_lord": functional_report.badhaka_lord,
                "yogakarakas": functional_report.yogakaraka_planets,
                "marakas": functional_report.maraka_planets,
            },
            "planets": structured_planets,
            "yogas": [y.model_dump() for y in yogas_report.yogas if y.is_active],
            "dasha_summary": dasha_summary,
            "ashtakavarga_summary": ashtakavarga_report.summary.model_dump(),
            "gochar_transits": [t.model_dump() for t in gochar_report.transits],
        }

        return AIDossierReport(
            markdown_dossier=markdown_dossier,
            system_prompt_recommendation=system_prompt,
            structured_payload=structured_payload,
        )
