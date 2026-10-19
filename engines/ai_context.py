"""AI context serialization engine.

Compiles calculated astrological factors across all engines into a structured markdown dossier
and JSON dictionary for AI synthesis and report generation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.constants import PlanetEnum, ZODIAC_SIGNS
from engines.ashtakavarga import AshtakavargaFullReport
from engines.aspects import AspectsReport
from engines.dignity import (
    DignityEngine,
    DignityState,
    EXALTATION_SIGNS,
    DEBILITATION_SIGNS,
    OWN_SIGNS,
)
from engines.friendships import PanchaDhaMaitriReport
from engines.functional import FunctionalReport
from engines.gochar import GocharReport
from engines.jaimini import CharaDashaResult
from engines.kp import KPEngine
from engines.parashari import VargaChartEngine, VargaType, VimshottariDashaTree
from engines.strength import PlanetaryStrengthReport
from engines.yogas import YogaEvaluationReport
from prompts.safety import sanitize_single_line
from schemas.models import UnifiedChartData


class AIDossierReport(BaseModel):
    """Serialized context payload and recommended system prompt."""
    markdown_dossier: str
    system_prompt_recommendation: str
    structured_payload: Dict[str, Any]


class AIContextEngine:
    """Builds structured Markdown and JSON summaries for LLM consumption."""

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
        chara_dasha: Optional[CharaDashaResult] = None,
        gender: str = "male",
    ) -> AIDossierReport:
        birth_city = sanitize_single_line(birth_city)
        asc = chart.angles.ascendant_sign
        asc_nak = chart.angles.ascendant_nakshatra
        asc_sign_id = asc.id
        loc = chart.input_data.location
        gender = getattr(chart.input_data, "gender", gender) or "male"
        rel_karaka = "Venus (Kalatrakaraka - Wife/Partner)" if gender.lower() == "male" else ("Jupiter (Patikaraka - Husband/Partner, with Mars for attraction)" if gender.lower() == "female" else "Venus & Jupiter (Primary Relationship Significators)")

        from datetime import date
        today = date.today()
        birth_year = getattr(chart.input_data, "year", None)
        birth_month = getattr(chart.input_data, "month", 1)
        birth_day = getattr(chart.input_data, "day", 1)
        if birth_year is None:
            try:
                parts = effective_date_str.split("-")
                birth_year = int(parts[0])
                birth_month = int(parts[1])
                birth_day = int(parts[2])
            except Exception:
                birth_year = 1995
                birth_month = 10
                birth_day = 15

        age = today.year - birth_year - ((today.month, today.day) < (birth_month, birth_day))
        age = max(0, age)

        lines: List[str] = []
        lines.append("# TRINETRIAI VEDIC ASTROLOGICAL DOSSIER")
        lines.append("")
        lines.append("## 1. NATAL BASELINE & ASTRONOMICAL ANCHORS")
        lines.append(f"- **Native Age**: ~{age} years (Operating Cycle: {today.year})")
        lines.append(f"- **Native Gender**: {gender.capitalize()}")
        lines.append(f"- **Primary Natural Relationship Karaka**: {rel_karaka}")
        lines.append(f"- **Ayanamsha**: {chart.ayanamsha_name.value} ({chart.ayanamsha_dms.formatted})")
        lines.append(f"- **Lagna (Ascendant)**: {asc.sanskrit_name} ({asc.english_name}) at {asc.dms.formatted} | Nakshatra: {asc_nak.sanskrit_name} Pada {asc_nak.pada} (Lord: {asc_nak.lord.value})")

        # D10 Dashamsha Lagna (Career Ascendant)
        d10_asc = VargaChartEngine.calculate_point_varga(chart.angles.ascendant, VargaType.D10, is_ascendant=True)
        d10_asc_sign_id = d10_asc.sign_id
        d10_asc_sign_name = d10_asc.sign_name
        lines.append(f"- **D10 Dashamsha Lagna (Career Ascendant)**: {d10_asc_sign_name} ({ZODIAC_SIGNS[d10_asc_sign_id]['english_name']}) at {d10_asc.dms.formatted} (Lord: {d10_asc.sign_lord.value})")
        lines.append(f"- **MC (Midheaven / 10th Cusp)**: {chart.angles.mc_sign.sanskrit_name} at {chart.angles.mc_dms.formatted}")
        lines.append(f"- **Lagna Modality**: {functional_report.lagna_modality} | **Badhaka House**: House {functional_report.badhaka_house} (Lord: {functional_report.badhaka_lord})")
        yk_str = ", ".join(functional_report.yogakaraka_planets) if functional_report.yogakaraka_planets else "None (Single graha rules Kendra+Trikona)"
        mar_str = ", ".join(functional_report.maraka_planets) if functional_report.maraka_planets else "None"
        lines.append(f"- **Yogakaraka Graha(s)**: {yk_str}")
        lines.append(f"- **Maraka Graha(s)**: {mar_str}")
        lines.append("")

        # 2. Planetary Placements & Composite Strength Table
        lines.append("## 2. PLANETARY PLACEMENTS & VEDIC STRENGTH MATRIX")
        lines.append("| Graha | Sign | Degree | House | D9 Navamsha | D10 Dashamsha | Nakshatra | Motion | Dignity | Pancha-Dha Kshetra | Functional Role | Bala (%) | Grade |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")

        classical_planets = [
            PlanetEnum.SUN, PlanetEnum.MOON, PlanetEnum.MARS, PlanetEnum.MERCURY,
            PlanetEnum.JUPITER, PlanetEnum.VENUS, PlanetEnum.SATURN, PlanetEnum.RAHU, PlanetEnum.KETU
        ]

        # Identify planets with classical Neechabhanga cancellation
        neechabhanga_planets = set()
        for y in yogas_report.yogas:
            if y.id.startswith("neechabhanga_") or "Neechabhanga" in y.name:
                for p_inv in y.planets_involved:
                    neechabhanga_planets.add(p_inv)

        structured_planets = []
        for p_enum in classical_planets:
            if p_enum not in chart.planets:
                continue
            p = chart.planets[p_enum]
            h_num = ((p.sign.id - asc_sign_id) % 12) + 1
            mot = "Retrograde" if p.is_retrograde else "Direct"
            comb = " [Combust]" if p.is_combust else ""

            # D9 Navamsha and Vargottama
            d9_plc = VargaChartEngine.calculate_point_varga(p.longitude, VargaType.D9, planet=p_enum)
            d9_sign = d9_plc.sign_name
            is_vargottama = (p.sign.id == d9_plc.sign_id)
            varg_str = " [Vargottama]" if is_vargottama else ""

            # D10 Dashamsha Placement & Dignity
            d10_plc = VargaChartEngine.calculate_point_varga(p.longitude, VargaType.D10, planet=p_enum)
            d10_sign = d10_plc.sign_name
            d10_h_num = ((d10_plc.sign_id - d10_asc_sign_id) % 12) + 1
            if d10_plc.sign_id == EXALTATION_SIGNS.get(p_enum):
                d10_dig_tag = " [Exalted]"
            elif d10_plc.sign_id == DEBILITATION_SIGNS.get(p_enum):
                d10_dig_tag = " [Debilitated]"
            elif d10_plc.sign_id in OWN_SIGNS.get(p_enum, []):
                d10_dig_tag = " [Own Sign]"
            else:
                d10_dig_tag = ""
            d10_str = f"{d10_sign} (H{d10_h_num}){d10_dig_tag}"

            # Dignity via DignityEngine
            dignity_rep = DignityEngine.evaluate_planet_dignity(
                planet=p_enum,
                sign_id=p.sign.id,
                sign_name=p.sign.sanskrit_name,
                degree_in_sign=p.sign.intra_sign_degree,
                neechabhanga_planets=neechabhanga_planets,
            )
            if dignity_rep.is_exalted:
                dignity_str = "Exalted (Uccha)"
            elif dignity_rep.is_debilitated:
                dignity_str = "Debilitated (Neecha) [Cancelled]" if dignity_rep.has_neechabhanga else "Debilitated (Neecha)"
            elif dignity_rep.is_moolatrikona:
                dignity_str = "Moolatrikona"
            elif dignity_rep.is_own_sign:
                dignity_str = "Own Sign"
            else:
                dignity_str = "Neutral"

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

            row_line = (
                f"| **{p_enum.value}** | {p.sign.sanskrit_name} | {p.sign.dms.formatted} | House {h_num} | "
                f"{d9_sign}{varg_str} | {d10_str} | {p.nakshatra.sanskrit_name} P{p.nakshatra.pada} | {mot}{comb} | {dignity_str} | "
                f"{kshetra} | {func_role} | {bala_pct} | {bala_grade} |"
            )
            lines.append(row_line)

            structured_planets.append({
                "planet": p_enum.value,
                "sign": p.sign.sanskrit_name,
                "sign_id": p.sign.id,
                "degree": p.sign.dms.formatted,
                "house": h_num,
                "d9_sign": d9_sign,
                "is_vargottama": is_vargottama,
                "d10_sign": d10_sign,
                "d10_sign_id": d10_plc.sign_id,
                "d10_house": d10_h_num,
                "d10_dignity": d10_dig_tag.strip(" []") or "Neutral",
                "nakshatra": f"{p.nakshatra.sanskrit_name} P{p.nakshatra.pada}",
                "nakshatra_lord": p.nakshatra.lord.value,
                "is_retrograde": p.is_retrograde,
                "is_combust": p.is_combust,
                "dignity": dignity_str,
                "dignity_label": dignity_rep.dignity_label,
                "is_exalted": dignity_rep.is_exalted,
                "is_debilitated": dignity_rep.is_debilitated,
                "is_own_sign": dignity_rep.is_own_sign,
                "is_moolatrikona": dignity_rep.is_moolatrikona,
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

        # 5.1 Macro Mahadasha Eras
        active_md_lord = dasha_summary.get("md")
        active_md_idx = next((i for i, m in enumerate(dashas.mahadashas) if m.lord.value == active_md_lord), None)
        if active_md_idx is not None and dashas.mahadashas:
            lines.append("\n### Macro Era Horizon (Mahadasha Eras):")
            if active_md_idx > 0:
                pm = dashas.mahadashas[active_md_idx - 1]
                lines.append(f"- **Previous Era (Concluded)**: {pm.lord.value} ({pm.start_date.strftime('%b %Y')} → {pm.end_date.strftime('%b %Y')})")
            cm = dashas.mahadashas[active_md_idx]
            lines.append(f"- **Current Operating Era (ACTIVE)**: {cm.lord.value} ({cm.start_date.strftime('%b %Y')} → {cm.end_date.strftime('%b %Y')})")
            if active_md_idx + 1 < len(dashas.mahadashas):
                nm = dashas.mahadashas[active_md_idx + 1]
                lines.append(f"- **Next Horizon Era (Upcoming)**: {nm.lord.value} ({nm.start_date.strftime('%b %Y')} → {nm.end_date.strftime('%b %Y')})")

        # 5.2 Antardashas timeline (Past 2 + Active + Next 4)
        all_ads = []
        active_ad_node = None
        for md in dashas.mahadashas:
            for ad in md.antardashas:
                is_active = (md.lord.value == dasha_summary.get("md") and ad.lord.value == dasha_summary.get("ad"))
                if is_active:
                    active_ad_node = ad
                ad_months = ad.duration_days / 30.4375
                dur_str = f"{ad_months:.1f}m" if ad_months >= 1 else f"{int(ad.duration_days)}d"
                all_ads.append({
                    "period": f"{md.lord.value}-{ad.lord.value}",
                    "md_lord": md.lord.value,
                    "ad_lord": ad.lord.value,
                    "start": ad.start_date.strftime("%d %b %Y"),
                    "end": ad.end_date.strftime("%d %b %Y"),
                    "duration": dur_str,
                    "is_active": is_active,
                })

        active_ad_idx = next((i for i, a in enumerate(all_ads) if a["is_active"]), None)
        if active_ad_idx is not None:
            lines.append("\n### Seasonal Strategic Timeline: Antardashas (Recent Past → Current → Upcoming):")
            lines.append("| Period (MD-AD) | Start Date | End Date | Duration | Operational Status |")
            lines.append("|---|---|---|---|---|")
            start_ad = max(0, active_ad_idx - 2)
            end_ad = min(len(all_ads), active_ad_idx + 5)
            for idx in range(start_ad, end_ad):
                a_item = all_ads[idx]
                if a_item["is_active"]:
                    st = "**CURRENT ACTIVE**"
                elif idx < active_ad_idx:
                    st = "Recently Concluded" if idx == active_ad_idx - 1 else "Concluded"
                else:
                    st = "Upcoming (Next Chapter)" if idx == active_ad_idx + 1 else "Upcoming"
                lines.append(f"| **{a_item['period']}** | {a_item['start']} | {a_item['end']} | {a_item['duration']} | {st} |")

        # 5.3 Tactical Micro-Dial: Pratyantardashas (PD) for Active Antardasha
        if active_ad_node and active_ad_node.pratyantardashas:
            active_pd_lord = dasha_summary.get("pd")
            pds = active_ad_node.pratyantardashas
            active_pd_idx = next((i for i, p in enumerate(pds) if p.lord.value == active_pd_lord), None)
            if active_pd_idx is not None:
                md_name = dasha_summary.get("md")
                ad_name = dasha_summary.get("ad")
                lines.append(f"\n### Tactical Micro-Dial: Pratyantardasha (PD) Timeline (Immediate 3–6 Months):")
                lines.append(f"*Active tactical sub-cycles within Mahadasha {md_name} → Antardasha {ad_name}:*")
                lines.append("| Level (MD-AD-PD) | Start Date | End Date | Duration | Tactical Timing |")
                lines.append("|---|---|---|---|---|")
                start_pd = max(0, active_pd_idx - 1)
                end_pd = min(len(pds), active_pd_idx + 4)
                for p_idx in range(start_pd, end_pd):
                    pd_item = pds[p_idx]
                    dur_days = pd_item.duration_days
                    dur_str = f"{dur_days:.0f}d" if dur_days >= 1 else f"{dur_days * 24:.0f}h"
                    if p_idx == active_pd_idx:
                        pst = "**CURRENT ACTIVE**"
                    elif p_idx < active_pd_idx:
                        pst = "Recently Concluded"
                    elif p_idx == active_pd_idx + 1:
                        pst = "Upcoming (Next 30–60d)"
                    else:
                        pst = "Upcoming"
                    lines.append(
                        f"| **{md_name}-{ad_name}-{pd_item.lord.value}** | {pd_item.start_date.strftime('%d %b %Y')} | "
                        f"{pd_item.end_date.strftime('%d %b %Y')} | {dur_str} | {pst} |"
                    )
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

        # 7. Jaimini Chara Dasha & Rashi Chronology
        if chara_dasha:
            order_str = "Direct (Savya)" if chara_dasha.is_direct_order else "Reverse (Apasavya)"
            active_md_str = (
                f"{chara_dasha.active_mahadasha.sign_name} ({chara_dasha.active_mahadasha.sign_english}) "
                f"[Lord: {chara_dasha.active_mahadasha.sign_lord}] "
                f"from {chara_dasha.active_mahadasha.start_date.strftime('%b %Y')} to {chara_dasha.active_mahadasha.end_date.strftime('%b %Y')}"
            ) if chara_dasha.active_mahadasha else "N/A"
            active_ad_str = (
                f"{chara_dasha.active_antardasha.sign_name} ({chara_dasha.active_antardasha.sign_english}) "
                f"[Lord: {chara_dasha.active_antardasha.sign_lord}] "
                f"from {chara_dasha.active_antardasha.start_date.strftime('%d %b %Y')} to {chara_dasha.active_antardasha.end_date.strftime('%d %b %Y')}"
            ) if chara_dasha.active_antardasha else "N/A"

            lines.append("## 7. JAIMINI CHARA DASHA & RASHI CHRONOLOGY")
            lines.append(f"- **Lagna Rashi**: {chara_dasha.lagna_sign_name} ({chara_dasha.lagna_sign_english}) | **9th Rashi from Lagna**: {chara_dasha.ninth_sign_name} ({chara_dasha.ninth_sign_english})")
            lines.append(f"- **Dasha Progression Sequence**: {order_str}")
            lines.append(f"- **Active Chara Mahadasha**: {active_md_str}")
            lines.append(f"- **Active Chara Antardasha**: {active_ad_str}")
            lines.append("")

        # 8. KP 12 Placidus House Cusps & Cuspal Sub-Lords (1–249)
        lines.append("## 8. KP 12 PLACIDUS HOUSE CUSPS & CUSPAL SUB-LORDS (1–249)")
        lines.append("| Cusp | Sign | Degree | Star Lord | Sub-Lord (CSL) | Sub-Sub-Lord |")
        lines.append("|---|---|---|---|---|---|")
        for cusp in chart.placidus_houses:
            kp_res = KPEngine.resolve_kp_sub(cusp.cusp_longitude)
            lines.append(f"| House {cusp.house_number:02d} | {cusp.sign.sanskrit_name} | {cusp.dms.formatted} | {kp_res.star_lord.value} | **{kp_res.sub_lord.value}** | {kp_res.sub_sub_lord.value} |")
        lines.append("")

        # KP 4-Fold Planetary Significators
        kp_matrix = KPEngine.calculate_4fold_significators(chart)
        lines.append("### KP 4-Fold Planetary Significators (Levels A, B, C, D):")
        lines.append("| Graha | Star Lord | Sub-Lord (CSL) | Level A (In Star of Occupant) | Level B (Occupant) | Level C (In Star of Lord) | Level D (House Lord) |")
        lines.append("|---|---|---|---|---|---|---|")
        for p_enum in classical_planets:
            if p_enum not in chart.planets:
                continue
            p = chart.planets[p_enum]
            kp_res = KPEngine.resolve_kp_sub(p.longitude)
            signifs = kp_matrix.planets_significations.get(p_enum, {})
            sig_a = ", ".join(map(str, signifs.get("A", []))) or "-"
            sig_b = ", ".join(map(str, signifs.get("B", []))) or "-"
            sig_c = ", ".join(map(str, signifs.get("C", []))) or "-"
            sig_d = ", ".join(map(str, signifs.get("D", []))) or "-"
            lines.append(f"| **{p_enum.value}** | {kp_res.star_lord.value} | **{kp_res.sub_lord.value}** | {sig_a} | {sig_b} | {sig_c} | {sig_d} |")
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
                "age": age,
                "gender": gender,
                "operating_cycle": today.year,
                "ayanamsha": chart.ayanamsha_name.value,
                "lagna": asc.sanskrit_name,
                "lagna_degree": asc.dms.formatted,
                "lagna_nakshatra": f"{asc_nak.sanskrit_name} P{asc_nak.pada}",
                "d10_lagna": d10_asc_sign_name,
                "d10_lagna_english": ZODIAC_SIGNS[d10_asc_sign_id]["english_name"],
                "d10_lagna_lord": d10_asc.sign_lord.value,
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

        if chara_dasha:
            structured_payload["jaimini_chara_dasha"] = {
                "lagna_sign": chara_dasha.lagna_sign_english,
                "ninth_sign": chara_dasha.ninth_sign_english,
                "is_direct": chara_dasha.is_direct_order,
                "active_mahadasha": chara_dasha.active_mahadasha.sign_english if chara_dasha.active_mahadasha else None,
                "active_mahadasha_lord": chara_dasha.active_mahadasha.sign_lord if chara_dasha.active_mahadasha else None,
                "active_antardasha": chara_dasha.active_antardasha.sign_english if chara_dasha.active_antardasha else None,
                "active_antardasha_lord": chara_dasha.active_antardasha.sign_lord if chara_dasha.active_antardasha else None,
            }

        return AIDossierReport(
            markdown_dossier=markdown_dossier,
            system_prompt_recommendation=system_prompt,
            structured_payload=structured_payload,
        )
