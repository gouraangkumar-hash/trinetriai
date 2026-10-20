"""Trinetri Multi-Agent Astrological Orchestration Engine.

Orchestrates the Three Eyes (Parashara, KP, Jaimini) concurrent evaluations
via asyncio.gather and streams the synthesized consensus to the client via SSE.
"""

import asyncio
import hashlib
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from core.constants import ZODIAC_SIGNS, PlanetEnum
from prompts.parashari_prompt import (
    EYE_1_PARASHARI_SYSTEM_PROMPT,
    EYE_1_PARASHARI_WWH_SYSTEM_PROMPT,
    EYE_1_PARASHARI_CAREER_SYSTEM_PROMPT,
    build_parashari_prompt,
)
from prompts.kp_prompt import (
    EYE_2_KP_SYSTEM_PROMPT,
    EYE_2_KP_WWH_SYSTEM_PROMPT,
    EYE_2_KP_CAREER_SYSTEM_PROMPT,
    build_kp_prompt,
)
from prompts.jaimini_prompt import (
    EYE_3_JAIMINI_SYSTEM_PROMPT,
    EYE_3_JAIMINI_WWH_SYSTEM_PROMPT,
    EYE_3_JAIMINI_CAREER_SYSTEM_PROMPT,
    build_jaimini_prompt,
)
from prompts.synthesizer_prompt import (
    MAHA_SYNTHESIZER_SYSTEM_PROMPT,
    WHAT_WHY_HOW_SYSTEM_PROMPT,
    CRAFT_WEALTH_CALLING_SYSTEM_PROMPT,
    build_synthesizer_prompt,
)
from prompts.chat_prompt import build_chat_system_instruction
from prompts.safety import MAX_CHAT_MESSAGE_CHARS, sanitize_evidence, sanitize_user_text
from services.llm import gemini_service

logger = logging.getLogger("trinetri.orchestrator")

# In-memory LRU cache for Three Eyes macro evaluations per chart fingerprint
# Key: f"{chart_fingerprint}_{pillar}_{clean_query}"
_THREE_EYES_CACHE: Dict[str, Dict[str, str]] = {}
_MAX_CACHE_ENTRIES = 64
_EYES_SEMAPHORE = asyncio.Semaphore(2)


PILLAR_TITLES = {
    "comprehensive": "1. What, Why and How You Are",
    "career": "2. Craft, Wealth & Public Calling (10th/2nd/11th Cusps, D10 & AmK)",
    "relationships": "3. Relationships, Marriage & Soul Compatibility (7th Cusp, D9 & Darakaraka)",
    "dasha": "4. Current Dasha & Timing of Upcoming Shifts (Vimshottari, Chara & Transits)",
    "custom": "Custom Consultation Query",
}

HOUSE_PORTFOLIOS: Dict[int, str] = {
    1: "Self, Vitality, Dharma, Physical Body, Head",
    2: "Wealth, Family, Speech, Liquid Assets, Food",
    3: "Courage, Siblings, Communication, Short Travel, Initiative",
    4: "Mother, Home, Conveyances, Emotional Peace, Fixed Assets",
    5: "Intellect, Purva Punya, Children, Creativity, Discernment",
    6: "Obstacles, Debts, Disease, Enemies, Daily Service, Digestion",
    7: "Marriage, Spouse, Long-Term Partnerships, Contracts, Public Realm",
    8: "Longevity, Transformation, Occult/Secrets, Sudden Shifts, Joint Assets",
    9: "Dharma, Father, Guru, Higher Wisdom, Luck, Fortune, Long Journeys",
    10: "Karma, Career, Public Status, Authority, Ambition, Leadership",
    11: "Gains (Labha), Networks, Elder Siblings, Aspirations, Fulfillment",
    12: "Moksha, Expenditure (Vyaya), Solitude, Foreign Residence, Subconscious",
}

ELEMENT_MAP: Dict[int, str] = {
    1: "Fire", 2: "Earth", 3: "Air", 4: "Water",
    5: "Fire", 6: "Earth", 7: "Air", 8: "Water",
    9: "Fire", 10: "Earth", 11: "Air", 12: "Water",
}

SIGN_DOSHA_MAP: Dict[int, Dict[str, float]] = {
    1: {"pitta": 1.0, "vata": 0.0, "kapha": 0.0},
    2: {"kapha": 0.8, "vata": 0.2, "pitta": 0.0},
    3: {"vata": 0.8, "pitta": 0.2, "kapha": 0.0},
    4: {"kapha": 1.0, "pitta": 0.0, "vata": 0.0},
    5: {"pitta": 1.0, "vata": 0.0, "kapha": 0.0},
    6: {"vata": 0.6, "pitta": 0.4, "kapha": 0.0},
    7: {"vata": 0.7, "kapha": 0.3, "pitta": 0.0},
    8: {"pitta": 0.7, "kapha": 0.3, "vata": 0.0},
    9: {"pitta": 0.7, "vata": 0.3, "kapha": 0.0},
    10: {"vata": 0.6, "kapha": 0.4, "pitta": 0.0},
    11: {"vata": 0.9, "pitta": 0.1, "kapha": 0.0},
    12: {"kapha": 0.8, "vata": 0.2, "pitta": 0.0},
}

PLANET_NATURAL_DOSHA: Dict[str, Dict[str, float]] = {
    "Sun": {"pitta": 1.0, "vata": 0.0, "kapha": 0.0},
    "Moon": {"kapha": 0.75, "vata": 0.25, "pitta": 0.0},
    "Mars": {"pitta": 1.0, "vata": 0.0, "kapha": 0.0},
    "Mercury": {"vata": 0.6, "pitta": 0.4, "kapha": 0.0},
    "Jupiter": {"kapha": 0.8, "pitta": 0.2, "vata": 0.0},
    "Venus": {"kapha": 0.7, "vata": 0.3, "pitta": 0.0},
    "Saturn": {"vata": 1.0, "pitta": 0.0, "kapha": 0.0},
    "Rahu": {"vata": 1.0, "pitta": 0.0, "kapha": 0.0},
    "Ketu": {"pitta": 1.0, "vata": 0.0, "kapha": 0.0},
}

KARMIC_COMFORT_MAP: Dict[int, str] = {
    1: "Defaulting to solo isolation and resisting constructive collaboration.",
    2: "Hoarding familiar material security, predictable comfort, and family dogma.",
    3: "Reactive tactical hustle and getting lost in busywork micro-details.",
    4: "Retreating into emotional insularity, private domestic comfort, and familiar security.",
    5: "Solitary creative projects and demanding individual ego validation.",
    6: "Micromanaging everyday friction, chronic anxiety, and constant battle readiness.",
    7: "Over-adapting to partner expectations and hiding within committee consensus.",
    8: "Extreme privacy, withholding feelings, and suspecting hidden negative motives.",
    9: "Relying on abstract theory, advice from others, or waiting passively for luck.",
    10: "Equating entire human worth with work output, external titles, and public status.",
    11: "Seeking safety in crowd consensus and prioritizing peer group approval.",
    12: "Escapist withdrawal, excessive surrender, and avoiding concrete worldly engagement.",
}

KARMIC_GROWTH_MAP: Dict[int, str] = {
    1: "Claiming personal sovereignty, trusting your solo instinct, and leading unapologetically.",
    2: "Articulating clear personal values, building tangible stewardship, and speaking transparent truth.",
    3: "Rolling up sleeves for direct initiative, courageous daily communication, and hands-on execution.",
    4: "Cultivating unshakeable internal sanctuary, emotional grounding, and domestic peace.",
    5: "Authentic creative courage, joyful self-expression, and romantic vulnerability.",
    6: "Disciplined daily mastery, solving grounded problems, and defending healthy work boundaries.",
    7: "True collaborative partnership, co-creation, and deep commitment to an equal counterpart.",
    8: "Surrendering control to deep psychological intimacy, joint transformation, and shared truth.",
    9: "Stepping into long-range visionary wisdom, mentorship, and faith in higher life trajectory.",
    10: "Stepping onto the public stage, claiming professional authority, and building an enduring worldly mark.",
    11: "Building large-scale networks, serving collective goals, and expanding philanthropic reach.",
    12: "Conscious decompression, spiritual surrender, creative solitude, and letting go of control.",
}


class TrinetriOrchestrator:
    """Manages multi-agent parallel execution, fact sheet slicing, and streaming synthesis."""

    @classmethod
    def compute_constitutional_blueprint(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministically computes elemental percentages, Ayurvedic Prakriti, and natal paradoxes."""
        planets_table = data.get("planets_table", [])
        
        # 1. Elemental Balance
        elem_weights = {"Fire": 0.0, "Earth": 0.0, "Air": 0.0, "Water": 0.0}
        total_elem_w = 0.0

        for p in planets_table:
            pl_name = p.get("planet", "")
            s_id = p.get("sign_id")
            if not s_id or s_id not in ELEMENT_MAP:
                continue
            if "Ascendant" in pl_name or "Lagna" in pl_name:
                w = 2.5
            elif "Moon" in pl_name:
                w = 2.5
            elif "Sun" in pl_name:
                w = 1.5
            elif any(k in pl_name for k in ["Rahu", "Ketu"]):
                w = 0.5
            else:
                w = 1.0
            elem_weights[ELEMENT_MAP[s_id]] += w
            total_elem_w += w

        elem_pcts = {k: round((v / (total_elem_w or 1.0)) * 100) for k, v in elem_weights.items()}
        sorted_elems = sorted(elem_pcts.items(), key=lambda x: x[1], reverse=True)
        top1_elem, top1_val = sorted_elems[0]
        top2_elem, top2_val = sorted_elems[1]

        if top1_val - top2_val <= 6:
            element_label = f"{top1_elem}-{top2_elem} Balance ({top1_elem} {top1_val}%, {top2_elem} {top2_val}%)"
        else:
            element_label = f"{top1_elem} Dominant ({top1_val}%) with Secondary {top2_elem} ({top2_val}%)"

        # 2. Ayurvedic Doshas (Prakriti)
        dosha_scores = {"vata": 0.0, "pitta": 0.0, "kapha": 0.0}
        tot_dosha_w = 0.0

        for p in planets_table:
            pl_name = p.get("planet", "")
            s_id = p.get("sign_id")
            if not s_id or s_id not in SIGN_DOSHA_MAP:
                continue
            s_d = SIGN_DOSHA_MAP[s_id]

            if "Ascendant" in pl_name or "Lagna" in pl_name:
                w = 2.5
                for k in dosha_scores:
                    dosha_scores[k] += w * s_d.get(k, 0.0)
                tot_dosha_w += w
            else:
                matched_pl = next((pk for pk in PLANET_NATURAL_DOSHA if pk in pl_name), None)
                if not matched_pl:
                    continue
                w = 2.5 if matched_pl == "Moon" else (1.5 if matched_pl == "Sun" else (0.5 if matched_pl in ["Rahu", "Ketu"] else 1.0))
                p_d = PLANET_NATURAL_DOSHA[matched_pl]
                for k in dosha_scores:
                    dosha_scores[k] += w * (0.5 * s_d.get(k, 0.0) + 0.5 * p_d.get(k, 0.0))
                tot_dosha_w += w

        dosha_pcts = {k: round((v / (tot_dosha_w or 1.0)) * 100) for k, v in dosha_scores.items()}
        sorted_doshas = sorted(dosha_pcts.items(), key=lambda x: x[1], reverse=True)
        d1_name, d1_pct = sorted_doshas[0]
        d2_name, d2_pct = sorted_doshas[1]
        d3_name, d3_pct = sorted_doshas[2]

        if d1_pct - d2_pct <= 5 and d2_pct - d3_pct <= 5:
            prakriti_label = f"Tridoshic Balanced (Vata {dosha_pcts['vata']}%, Pitta {dosha_pcts['pitta']}%, Kapha {dosha_pcts['kapha']}%)"
        else:
            prakriti_label = f"{d1_name.capitalize()}-{d2_name.capitalize()} Predominant ({d1_name.capitalize()} {d1_pct}%, {d2_name.capitalize()} {d2_pct}%)"

        # 3. Psychological Paradox Signatures (Lagna vs Moon vs Rahu-Ketu)
        summary = data.get("summary", {})
        asc = summary.get("ascendant", {})
        moon = summary.get("moon", {})
        asc_sign_name = asc.get("sign", "")
        moon_sign_name = moon.get("sign", "")
        
        asc_sid = next((p.get("sign_id") for p in planets_table if "Ascendant" in p.get("planet", "")), 1)
        moon_row = next((p for p in planets_table if "Moon" in p.get("planet", "")), {})
        moon_sid = moon_row.get("sign_id", 1)
        moon_nakshatra = moon_row.get("nakshatra") or moon.get("nakshatra", "")

        asc_elem = ELEMENT_MAP.get(asc_sid, "Earth")
        moon_elem = ELEMENT_MAP.get(moon_sid, "Air")

        # Moon distance from Lagna
        moon_house_from_lagna = ((moon_sid - asc_sid) % 12) + 1

        # Identify planets conjunct Ascendant or Moon
        planets_on_lagna = [p.get("planet") for p in planets_table if p.get("natal_house") == 1 and "Ascendant" not in p.get("planet", "")]
        planets_with_moon = [p.get("planet") for p in planets_table if p.get("natal_house") == moon_house_from_lagna and "Moon" not in p.get("planet", "")]
        
        lagna_influence = f" with {', '.join(planets_on_lagna)}" if planets_on_lagna else ""
        moon_influence = f" alongside {', '.join(planets_with_moon)}" if planets_with_moon else ""

        # Rich elemental paradoxes
        if asc_elem in ["Earth", "Water"] and moon_elem in ["Fire", "Air"]:
            paradox_headline = f"Grounded Exterior Composure ({asc_sign_name}{lagna_influence}) vs. High-Velocity Inner Mind ({moon_sign_name} Moon in {moon_nakshatra}{moon_influence}, House {moon_house_from_lagna})"
            paradox_narrative = (
                f"Outwardly you project deliberate patience, composure, and grounded dependability ({asc_sign_name}). "
                f"Inwardly, your mind ({moon_sign_name} in {moon_nakshatra}) operates at high speed, leaving you privately impatient "
                f"with friction, delays, or people who take too long to arrive at the point."
            )
        elif asc_elem in ["Fire", "Air"] and moon_elem in ["Earth", "Water"]:
            paradox_headline = f"Spontaneous Outward Spark ({asc_sign_name}{lagna_influence}) vs. Deeply Guarded Emotional Sanctuary ({moon_sign_name} Moon in {moon_nakshatra}{moon_influence}, House {moon_house_from_lagna})"
            paradox_narrative = (
                f"You step into rooms and initiate action with natural ease and expressive spark ({asc_sign_name}), "
                f"yet your emotional core ({moon_sign_name} in {moon_nakshatra}) is deeply private, vulnerable, and slow to trust, "
                f"requiring genuine emotional safety before letting anyone see behind your armor."
            )
        elif asc_elem == "Fire" and moon_elem == "Fire":
            paradox_headline = f"Double Fire Catalyst ({asc_sign_name} Rising, {moon_sign_name} Moon in {moon_nakshatra}, House {moon_house_from_lagna})"
            paradox_narrative = (
                f"Your outer instinct and inner emotional rhythm both operate on passion, creative urgency, and immediate truth. "
                f"Your primary paradox is learning the difference between genuine urgency and restless exhaustion—giving yourself permission to slow down without feeling like you are stagnating."
            )
        elif asc_elem == "Earth" and moon_elem == "Earth":
            paradox_headline = f"Double Earth Steadfastness ({asc_sign_name} Rising, {moon_sign_name} Moon in {moon_nakshatra}, House {moon_house_from_lagna})"
            paradox_narrative = (
                f"Both your presentation and emotional anchor are deeply pragmatic, tangible, and steady. "
                f"Your paradox lies in unshakeable reliability vs. carrying unexpressed burdens—you become the load-bearing pillar for everyone else while denying yourself the space to ask for help."
            )
        elif asc_elem == "Air" and moon_elem == "Air":
            paradox_headline = f"Double Air Intellectual Mobility ({asc_sign_name} Rising, {moon_sign_name} Moon in {moon_nakshatra}, House {moon_house_from_lagna})"
            paradox_narrative = (
                f"Your mind and persona thrive on ideas, nuance, and continuous synthesis. "
                f"Your inner paradox is living so intensely in concepts, foresight, and possibility that grounding into the present physical body and quiet emotional stillness feels like an unfamiliar discipline."
            )
        elif asc_elem == "Water" and moon_elem == "Water":
            paradox_headline = f"Double Water Empathic Depth ({asc_sign_name} Rising, {moon_sign_name} Moon in {moon_nakshatra}, House {moon_house_from_lagna})"
            paradox_narrative = (
                f"You perceive atmospheres, unspoken tensions, and emotional shifts before anyone says a word. "
                f"Your core paradox is an oceanic capacity to absorb others' emotional weather while struggling to maintain clear energetic boundaries between what belongs to you and what belongs to the world."
            )
        else:
            if moon_house_from_lagna in [6, 8, 12]:
                paradox_headline = f"Worldly Role ({asc_sign_name}) vs. Solitary Soul Need (House {moon_house_from_lagna} Moon in {moon_sign_name} / {moon_nakshatra})"
                paradox_narrative = (
                    f"The external demands that bring you worldly success and recognition ({asc_sign_name}) frequently run counter "
                    f"to the quiet, solitary conditions your nervous system ({moon_sign_name} in House {moon_house_from_lagna}) actually needs to feel rested and psychologically safe."
                )
            else:
                paradox_headline = f"Unified Purpose with Latent Over-Functioning ({asc_sign_name} Rising, {moon_sign_name} Moon in {moon_nakshatra})"
                paradox_narrative = (
                    f"Your outer demeanor and inner mind share purposeful harmony, giving you strong focus, but your primary vulnerability is "
                    f"an inability to downshift or pause, frequently mistaking necessary recovery for wasted time."
                )

        # 4. Karmic Axis (Comfort Zone vs Growth Edge)
        rahu_row = next((p for p in planets_table if "Rahu" in p.get("planet", "")), {})
        ketu_row = next((p for p in planets_table if "Ketu" in p.get("planet", "")), {})
        rahu_h = rahu_row.get("natal_house", 10)
        ketu_h = ketu_row.get("natal_house", 4)
        rahu_sign = rahu_row.get("sign", "")
        ketu_sign = ketu_row.get("sign", "")

        comfort_desc = KARMIC_COMFORT_MAP.get(ketu_h, f"Defaulting to habits of House {ketu_h} ({ketu_sign}).")
        growth_desc = KARMIC_GROWTH_MAP.get(rahu_h, f"Expanding into the potential of House {rahu_h} ({rahu_sign}).")

        return {
            "element_pcts": elem_pcts,
            "element_label": element_label,
            "dosha_pcts": dosha_pcts,
            "prakriti_label": prakriti_label,
            "paradox": {
                "headline": paradox_headline,
                "narrative": paradox_narrative,
            },
            "karmic_axis": {
                "headline": f"Comfort Zone (House {ketu_h}) vs. Growth Edge (House {rahu_h})",
                "comfort_zone": comfort_desc,
                "growth_edge": growth_desc,
            },
        }

    @classmethod
    def build_constitutional_ground_truth(cls, data: Dict[str, Any]) -> str:
        """Formats the computed constitutional blueprint into an unambiguous ground-truth block for LLM synthesis."""
        prof = cls.compute_constitutional_blueprint(data)
        lines = [
            "### COMPUTED CONSTITUTIONAL BLUEPRINT & PSYCHOLOGICAL PARADOXES (GROUND TRUTH):",
            f"- **Elemental Balance (Exact Math)**: {prof['element_label']} [Fire: {prof['element_pcts']['Fire']}%, Earth: {prof['element_pcts']['Earth']}%, Air: {prof['element_pcts']['Air']}%, Water: {prof['element_pcts']['Water']}%]",
            f"- **Ayurvedic Prakriti (Exact Math)**: {prof['prakriti_label']} [Vata: {prof['dosha_pcts']['vata']}%, Pitta: {prof['dosha_pcts']['pitta']}%, Kapha: {prof['dosha_pcts']['kapha']}%]",
            f"- **Core Inner Paradox (Primary Tension)**: {prof['paradox']['headline']}",
            f"  *Psychological Dynamic*: {prof['paradox']['narrative']}",
            f"- **Karmic Axis (Soul Evolution)**: {prof['karmic_axis']['headline']}",
            f"  *Default Comfort Zone (When Tired/Cornered)*: {prof['karmic_axis']['comfort_zone']}",
            f"  *Active Growth Edge (Unlock Next Level)*: {prof['karmic_axis']['growth_edge']}",
            "(CRITICAL INSTRUCTION: In your JSON output, use these exact computed constitutional labels and weave the native's specific Lagna, Moon, Nakshatra, and Karmic Axis houses into 'the_why.inner_paradox' and 'the_why.comfort_zone_vs_growth_edge' so the reading speaks directly to this unique human being!)",
        ]
        return "\n".join(lines)

    @classmethod
    def build_houses_matrix(cls, data: Dict[str, Any]) -> str:
        """Constructs an unambiguous 12-house ground-truth table with Sign, Lord, Occupants, Aspects, and SAV."""
        lines = []
        lines.append("### 12 Bhavas (Houses) Ground-Truth Rulership & Occupancy Matrix:")
        lines.append("| House | Sign (Rashi) | Rashi Lord | Resident Grahas | Aspecting Grahas | SAV Bindus | House Portfolio |")
        lines.append("|---|---|---|---|---|---|---|")

        # Lookup SAV bindus by house
        sav_by_house: Dict[int, int] = {}
        for entry in data.get("ashtakavarga", {}).get("sarvashtakavarga", []):
            h = entry.get("house_from_lagna")
            if h is not None:
                sav_by_house[h] = entry.get("total_bindus", 28)

        # 1. Prefer bhava_aspects if available in aspects report
        bhava_aspects = data.get("aspects", {}).get("bhava_aspects", [])
        if bhava_aspects:
            for b in bhava_aspects:
                h_num = b.get("house_number")
                sign_name = b.get("sign_name", "")
                lord = b.get("lord", "")
                occupants = ", ".join(b.get("occupants", [])) or "Vacant"
                aspects = ", ".join(b.get("benefics_aspecting", []) + b.get("malefics_aspecting", [])) or "-"
                bindus = sav_by_house.get(h_num, 28)
                bindu_str = f"{bindus} [Strong]" if bindus >= 30 else (f"{bindus} [Challenging]" if bindus < 26 else f"{bindus} [Average]")
                portfolio = HOUSE_PORTFOLIOS.get(h_num, "")
                lines.append(f"| **H{h_num}** | {sign_name} | **{lord}** | {occupants} | {aspects} | {bindu_str} | {portfolio} |")
            return "\n".join(lines)

        # 2. Fallback if bhava_aspects is not populated
        planets_table = data.get("planets_table", [])
        occupants_map: Dict[int, List[str]] = {h: [] for h in range(1, 13)}
        for p in planets_table:
            pl_name = p.get("planet")
            h_natal = p.get("natal_house")
            if h_natal and pl_name and "Ascendant" not in pl_name:
                occupants_map.setdefault(h_natal, []).append(pl_name)

        asc_sign_id = 1
        for p in planets_table:
            if "Ascendant" in p.get("planet", ""):
                asc_sign_id = p.get("sign_id", 1)
                break

        for h_num in range(1, 13):
            s_id = ((asc_sign_id - 1 + h_num - 1) % 12) + 1
            s_meta = ZODIAC_SIGNS.get(s_id, {})
            sign_name = s_meta.get("sanskrit_name", "")
            lord = s_meta.get("lord", "")
            if hasattr(lord, "value"):
                lord = lord.value
            occupants = ", ".join(occupants_map.get(h_num, [])) or "Vacant"
            bindus = sav_by_house.get(h_num, 28)
            bindu_str = f"{bindus} [Strong]" if bindus >= 30 else (f"{bindus} [Challenging]" if bindus < 26 else f"{bindus} [Average]")
            portfolio = HOUSE_PORTFOLIOS.get(h_num, "")
            lines.append(f"| **H{h_num}** | {sign_name} | **{lord}** | {occupants} | - | {bindu_str} | {portfolio} |")

        return "\n".join(lines)

    @classmethod
    def build_dasha_timeline(cls, data: Dict[str, Any], count: int = 5) -> str:
        """Extracts the 3-tier Vimshottari timeline: macro eras, seasonal AD timeline, and tactical PD micro-dial."""
        lines = []
        ds = data.get("dasha_summary", {})
        mahadashas = data.get("mahadashas", [])

        lines.append("### Vimshottari Dasha Chronology & Running Periods:")
        lines.append(
            f"- **Current Active Running Period**: Mahadasha **{ds.get('md', '-')}** ({ds.get('md_range', '-')}) → "
            f"Antardasha **{ds.get('ad', '-')}** ({ds.get('ad_range', '-')}) → "
            f"Pratyantardasha **{ds.get('pd', '-')}** ({ds.get('pd_range', '-')})"
        )

        active_md_lord = ds.get("md")
        active_ad_lord = ds.get("ad")
        active_pd_lord = ds.get("pd")

        # 1. Macro Era Horizon (Mahadasha Eras: Previous -> Current -> Next)
        active_md_idx = next(
            (i for i, m in enumerate(mahadashas) if m.get("is_active") or m.get("lord") == active_md_lord),
            None
        )
        if active_md_idx is not None and mahadashas:
            lines.append("\n**Macro Era Horizon (Mahadasha Eras):**")
            if active_md_idx > 0:
                pm = mahadashas[active_md_idx - 1]
                lines.append(f"- **Previous Era (Concluded)**: {pm.get('lord')} ({pm.get('start')} → {pm.get('end')})")
            cm = mahadashas[active_md_idx]
            lines.append(f"- **Current Operating Era (ACTIVE)**: {cm.get('lord')} ({cm.get('start')} → {cm.get('end')})")
            if active_md_idx + 1 < len(mahadashas):
                nm = mahadashas[active_md_idx + 1]
                lines.append(f"- **Next Horizon Era (Upcoming)**: {nm.get('lord')} ({nm.get('start')} → {nm.get('end')})")

        # Flatten Antardashas across all Mahadashas
        all_ads = []
        active_ad_dict = None
        for md in mahadashas:
            md_lord = md.get("lord", "")
            for ad in md.get("antardashas", []):
                ad_lord = ad.get("lord", "")
                is_active = bool(ad.get("is_active") or (md_lord == active_md_lord and ad_lord == active_ad_lord))
                ad_item = {
                    "period": f"{md_lord}-{ad_lord}",
                    "md_lord": md_lord,
                    "ad_lord": ad_lord,
                    "start": ad.get("start", ""),
                    "end": ad.get("end", ""),
                    "duration": ad.get("duration", ""),
                    "is_active": is_active,
                    "status": ad.get("status", ""),
                    "pratyantardashas": ad.get("pratyantardashas", []),
                }
                if is_active:
                    active_ad_dict = ad_item
                all_ads.append(ad_item)

        # 2. Seasonal Strategic Timeline: Antardashas (Recent Past -> Current -> Upcoming)
        active_ad_idx = next((i for i, a in enumerate(all_ads) if a["is_active"]), None)
        if active_ad_idx is not None:
            lines.append("\n**Seasonal Strategic Timeline: Antardashas (Recent Past → Current → Upcoming):**")
            lines.append("| Period (MD-AD) | Start Date | End Date | Duration | Operational Status |")
            lines.append("|---|---|---|---|---|")
            start_ad = max(0, active_ad_idx - 2)
            end_ad = min(len(all_ads), active_ad_idx + 5)
            for idx in range(start_ad, end_ad):
                a_item = all_ads[idx]
                if a_item["is_active"]:
                    badge = "**CURRENT ACTIVE**"
                elif idx < active_ad_idx:
                    badge = "Recently Concluded" if idx == active_ad_idx - 1 else "Concluded"
                elif idx == active_ad_idx + 1:
                    badge = "Upcoming (Next Chapter)"
                else:
                    badge = "Upcoming"
                lines.append(
                    f"| **{a_item['period']}** | {a_item['start']} | {a_item['end']} | {a_item['duration']} | {badge} |"
                )

        # 3. Tactical Micro-Dial: Pratyantardashas (PD) for Active Antardasha
        if active_ad_dict and active_ad_dict.get("pratyantardashas"):
            pds = active_ad_dict["pratyantardashas"]
            active_pd_idx = next(
                (i for i, p in enumerate(pds) if p.get("is_active") or p.get("lord") == active_pd_lord),
                None
            )
            if active_pd_idx is not None:
                md_name = active_ad_dict["md_lord"]
                ad_name = active_ad_dict["ad_lord"]
                lines.append(f"\n**Tactical Micro-Dial: Pratyantardasha (PD) Timeline (Immediate 3–6 Months):**")
                lines.append(f"*Active tactical sub-cycles within Mahadasha {md_name} → Antardasha {ad_name}:*")
                lines.append("| Level (MD-AD-PD) | Start Date | End Date | Duration | Tactical Timing |")
                lines.append("|---|---|---|---|---|")
                start_pd = max(0, active_pd_idx - 1)
                end_pd = min(len(pds), active_pd_idx + 4)
                for p_idx in range(start_pd, end_pd):
                    pd_item = pds[p_idx]
                    if p_idx == active_pd_idx:
                        pst = "**CURRENT ACTIVE**"
                    elif p_idx < active_pd_idx:
                        pst = "Recently Concluded"
                    elif p_idx == active_pd_idx + 1:
                        pst = "Upcoming (Next 30–60d)"
                    else:
                        pst = "Upcoming"
                    level_str = f"{md_name}-{ad_name}-{pd_item.get('lord', '')}"
                    lines.append(
                        f"| **{level_str}** | {pd_item.get('start', '')} | {pd_item.get('end', '')} | {pd_item.get('duration', '')} | {pst} |"
                    )

        return "\n".join(lines)

    @classmethod
    def build_transits_summary(cls, data: Dict[str, Any]) -> str:
        """Extracts live planetary transit coordinates and house alignments from Gochar engine."""
        lines = []
        gochar = data.get("gochar", {})
        transits = gochar.get("transits", [])
        summary = gochar.get("summary", {})
        transit_date = summary.get("transit_date_formatted", "Current Ephemeris")

        if transits:
            lines.append(f"### Real-Time Live Transits in the Sky (Gochar as of {transit_date}):")
            lines.append("| Transit Graha | Sky Sign & Degree | House from Lagna | House from Moon | SAV Bindus | Classical Impact |")
            lines.append("|---|---|---|---|---|---|")
            for t in transits:
                pl = t.get("planet", "")
                sign = t.get("sign_name", "")
                deg = t.get("degree_formatted", "")
                h_lagna = t.get("house_from_lagna", "-")
                h_moon = t.get("house_from_moon", "-")
                sav = t.get("sav_bindus", "-")
                status = t.get("classical_status", "")
                lines.append(f"| **{pl}** | {sign} {deg} | House {h_lagna} | House {h_moon} | {sav} bindus | {status} |")

        return "\n".join(lines)

    @classmethod
    def build_aspects_summary(cls, data: Dict[str, Any]) -> str:
        """Extracts verified Graha Drishti, mutual aspects, and conjunctions."""
        lines = []
        aspects = data.get("aspects", {})
        planets_aspects = aspects.get("planets_aspects", {})
        if planets_aspects:
            lines.append("### Verified Planetary Aspects (Graha Drishti):")
            for pl_name, p_detail in planets_aspects.items():
                casts = p_detail.get("aspects_cast", [])
                if casts:
                    cast_strs = []
                    for c in casts:
                        tgt_h = c.get("target_house")
                        asp_type = c.get("aspect_type")
                        aspected_pls = c.get("aspected_planets", [])
                        occ_str = f" [hits {', '.join(aspected_pls)}]" if aspected_pls else ""
                        cast_strs.append(f"House {tgt_h} ({asp_type}){occ_str}")
                    lines.append(f"- **{pl_name}** (House {p_detail.get('natal_house')}): Aspects {'; '.join(cast_strs)}")

        mutuals = aspects.get("mutual_aspects", [])
        if mutuals:
            lines.append("\n**Mutual Aspect Connections (Paraspara Drishti):**")
            for m in mutuals:
                lines.append(f"- **{m.get('planet1')} ↔ {m.get('planet2')}**: {m.get('relation')}")

        conjs = aspects.get("conjunctions", [])
        if conjs:
            lines.append("\n**Key House Conjunctions (Yuti):**")
            for c in conjs:
                lines.append(f"- House {c.get('house')} ({c.get('sign')}): {', '.join(c.get('planets', []))}")

        return "\n".join(lines)

    @classmethod
    def build_full_ground_truth_matrix(cls, data: Dict[str, Any]) -> str:
        """Assembles a unified, zero-hallucination ground-truth reference matrix."""
        sections = []

        # 0. Deterministic Constitutional Blueprint & Psychological Paradoxes
        sections.append(cls.build_constitutional_ground_truth(data))

        # 1. Core Angles & Functional Nature
        lines_core = ["### Natal Baseline & Functional Roles:"]
        summary = data.get("summary", {})
        asc = summary.get("ascendant", {})
        moon = summary.get("moon", {})
        sun = summary.get("sun", {})
        gender = data.get("gender") or summary.get("gender") or "male"
        rel_karaka = "Venus (Kalatrakaraka - Wife/Partner)" if gender.lower() == "male" else ("Jupiter (Patikaraka - Husband/Partner, with Mars for attraction)" if gender.lower() == "female" else "Venus & Jupiter (Primary Relationship Significators)")

        eff_date = summary.get("effective_date", "")
        age_str = ""
        if eff_date:
            try:
                b_year = int(eff_date.split("-")[0])
                from datetime import date
                cur_yr = date.today().year
                age_val = max(0, cur_yr - b_year)
                age_str = f" | **Native Age**: ~{age_val} years (Operating Cycle: {cur_yr})"
            except Exception:
                pass

        lines_core.append(f"- **Native Gender**: {gender.capitalize()}{age_str} | **Primary Natural Relationship Karaka**: {rel_karaka}")
        lines_core.append(f"- **Lagna (Ascendant)**: {asc.get('sign')} at {asc.get('degree')} (Lord: **{asc.get('lord')}**, Nakshatra: {asc.get('nakshatra')})")
        lines_core.append(f"- **Moon (Chandra)**: {moon.get('sign')} at {moon.get('degree')} (Lord: **{moon.get('lord')}**, Nakshatra: {moon.get('nakshatra')})")
        lines_core.append(f"- **Sun (Surya)**: {sun.get('sign')} at {sun.get('degree')} (Lord: **{sun.get('lord')}**)")

        func = data.get("functional_nature", {})
        if func:
            yk = ", ".join(func.get("yogakaraka_planets", [])) or "-"
            mar = ", ".join(func.get("maraka_planets", [])) or "-"
            lines_core.append(f"- **Yogakaraka Graha(s)**: {yk} | **Maraka Graha(s)**: {mar}")
            lines_core.append(f"- **Badhaka House**: House {func.get('badhaka_house')} (Lord: {func.get('badhaka_lord')})")
        sections.append("\n".join(lines_core))

        # 2. 12 Houses Matrix
        sections.append(cls.build_houses_matrix(data))

        # 3. Planetary Placements & Strengths
        lines_planets = ["### Natal Planetary Placements, Dignities & Strengths:"]
        lines_planets.append("| Graha | Sign | Degree | House | D9 Sign | D10 Dashamsha | Dignity | Functional Role | Bala (%) | Grade |")
        lines_planets.append("|---|---|---|---|---|---|---|---|---|---|")
        for p in data.get("planets_table", []):
            pl_name = p.get("planet")
            d1_sign = p.get("sign")
            deg = p.get("degree")
            house = p.get("natal_house")
            d9_sign = p.get("d9_sign", "-")
            d10_sign = p.get("d10_sign", "-")
            varg = " [V]" if bool(p.get("is_vargottama")) or p.get("vargottama_status", "").startswith("Vargottama") else ""
            dig = p.get("dignity_label", "")
            nb = " [Neechabhanga]" if p.get("has_neechabhanga") else ""
            str_pct = p.get("strength_percentage", "-")
            str_grade = p.get("strength_grade", "-")
            func_role = p.get("functional_role", "")
            lines_planets.append(
                f"| **{pl_name}** | {d1_sign} | {deg} | H{house} | {d9_sign}{varg} | {d10_sign} | {dig}{nb} | {func_role} | {str_pct} | {str_grade} |"
            )
        sections.append("\n".join(lines_planets))

        # 4. Aspects Summary
        asp_str = cls.build_aspects_summary(data)
        if asp_str:
            sections.append(asp_str)

        # 5. Vimshottari Dasha Timeline
        sections.append(cls.build_dasha_timeline(data, count=5))

        # 6. Real-Time Transits
        transit_str = cls.build_transits_summary(data)
        if transit_str:
            sections.append(transit_str)

        # 7. Jaimini Karakas & Padas
        lines_jaimini = ["### Jaimini Chara Karakas & Key Arudha Padas:"]
        karakas = data.get("chara_karakas_7", [])
        if karakas:
            k_strs = [f"**{k.get('role', k.get('karaka_name', ''))} ({k.get('code', k.get('karaka', ''))})**: {k.get('planet')} ({k.get('sign')})" for k in karakas]
            lines_jaimini.append("- **7 Chara Karakas**: " + " | ".join(k_strs))

        padas = data.get("arudha_padas", [])
        if padas:
            p_strs = [f"**{p.get('pada_name', p.get('pada', ''))}**: {p.get('sign')} ({p.get('house', '')})" for p in padas if p.get("pada_name", p.get("pada", "")) in ("AL (A1)", "UL (A12)", "AL", "UL", "A10", "A7", "A11")]
            lines_jaimini.append("- **Key Arudha Padas**: " + " | ".join(p_strs))

        cs = data.get("chara_dasha_summary", {})
        if cs:
            lines_jaimini.append(f"- **Chara Dasha**: Active MD **{cs.get('active_md')}** ({cs.get('md_range')}) → Active AD **{cs.get('active_ad')}** ({cs.get('ad_range')})")
        sections.append("\n".join(lines_jaimini))

        # 8. KP Cusps
        lines_kp = ["### KP Cuspal Sub-Lords (CSL) Table:"]
        lines_kp.append("| Cusp | Sign | Degree | Sign Lord | Star Lord | Cuspal Sub-Lord (CSL) |")
        lines_kp.append("|---|---|---|---|---|---|")
        for c in data.get("cusps_table", []):
            h_name = c.get("house") or f"House {c.get('cusp', '')}"
            sign = c.get("sign", "")
            deg = c.get("degree", "")
            sl = c.get("sign_lord", "")
            nl = c.get("star_lord", "")
            sub = c.get("sub_lord", "")
            lines_kp.append(f"| **{h_name}** | {sign} | {deg} | {sl} | {nl} | **{sub}** |")
        sections.append("\n".join(lines_kp))

        return "\n\n".join(sections)

    @classmethod
    def slice_parashari_facts(cls, data: Dict[str, Any]) -> str:
        """Extracts facts relevant specifically to BPHS Parashari school."""
        lines = []
        summary = data.get("summary", {})
        asc = summary.get("ascendant", {})
        moon = summary.get("moon", {})
        sun = summary.get("sun", {})
        gender = data.get("gender") or summary.get("gender") or "male"
        rel_karaka = "Venus (Kalatrakaraka - Wife/Partner)" if gender.lower() == "male" else ("Jupiter (Patikaraka - Husband/Partner, with Mars for attraction)" if gender.lower() == "female" else "Venus & Jupiter (Primary Relationship Significators)")

        eff_date = summary.get("effective_date", "")
        age_str = ""
        if eff_date:
            try:
                b_year = int(eff_date.split("-")[0])
                from datetime import date
                cur_yr = date.today().year
                age_val = max(0, cur_yr - b_year)
                age_str = f" | **Native Age**: ~{age_val} years (Operating Cycle: {cur_yr})"
            except Exception:
                pass

        lines.append(f"- **Native Gender**: {gender.capitalize()}{age_str} | **Relationship Karaka**: {rel_karaka}")
        lines.append(f"- **Lagna (Ascendant)**: {asc.get('sign')} at {asc.get('degree')} (Lord: {asc.get('lord')}, Nakshatra: {asc.get('nakshatra')})")
        asc_d10_sign = data.get("planet_details", {}).get("Ascendant (Lagna)", {}).get("d10_sign")
        if asc_d10_sign:
            lines.append(f"- **D10 Dashamsha Lagna (Career Ascendant)**: {asc_d10_sign}")
        lines.append(f"- **Moon (Chandra)**: {moon.get('sign')} at {moon.get('degree')} (Lord: {moon.get('lord')}, Nakshatra: {moon.get('nakshatra')})")
        lines.append(f"- **Sun (Surya)**: {sun.get('sign')} at {sun.get('degree')} (Lord: {sun.get('lord')})")

        # Functional nature
        func = data.get("functional_nature", {})
        if func:
            yk = ", ".join(func.get("yogakaraka_planets", [])) or "-"
            mar = ", ".join(func.get("maraka_planets", [])) or "-"
            lines.append(f"- **Yogakaraka Graha(s)**: {yk} | **Maraka Graha(s)**: {mar}")
            lines.append(f"- **Badhaka House**: House {func.get('badhaka_house')} (Lord: {func.get('badhaka_lord')})")

        # 12 Bhavas Rulership & Occupancy Matrix
        lines.append(f"\n{cls.build_houses_matrix(data)}")

        # Planets summary with D9 & D10 Dignity & Strength
        lines.append("\n**Planetary D1/D9/D10 Dignities & Strengths:**")
        planets_table = data.get("planets_table", [])
        for p in planets_table:
            pl_name = p.get("planet")
            d1_sign = p.get("sign")
            deg = p.get("degree")
            house = p.get("natal_house")
            d9_sign = p.get("d9_sign")
            varg = " (Vargottama)" if bool(p.get("is_vargottama")) or p.get("vargottama_status", "").startswith("Vargottama") else ""
            d10_sign = p.get("d10_sign", "-")
            dig = p.get("dignity_label", "")
            nb = " [Neechabhanga Cancelled]" if p.get("has_neechabhanga") else ""
            str_pct = p.get("strength_percentage", "-")
            str_grade = p.get("strength_grade", "-")
            func_role = p.get("functional_role", "")
            lines.append(
                f"- **{pl_name}**: in {d1_sign} {deg} (House {house}) | D9: {d9_sign}{varg} | D10 Dashamsha: {d10_sign} | "
                f"Dignity: {dig}{nb} | Functional: {func_role} | Bala: {str_pct} ({str_grade})"
            )

        # Aspects summary
        asp_summary = cls.build_aspects_summary(data)
        if asp_summary:
            lines.append(f"\n{asp_summary}")

        # Active Yogas
        yogas_summary = data.get("yogas_summary", {})
        live_sade = data.get("gochar", {}).get("summary", {}).get("sade_sati")
        sade_sati_str = f"Live Transit: {live_sade}" if live_sade else f"Natal: {yogas_summary.get('sade_sati_status')}"
        lines.append(f"\n**Vedic Yogas Summary**: Total: {yogas_summary.get('total_yogas')}, Raja: {yogas_summary.get('raja_count')}, Dhana: {yogas_summary.get('dhana_count')}")
        lines.append(f"- Sade Sati: {sade_sati_str} | Kuja Dosha: {yogas_summary.get('kuja_dosha_status')}")
        yogas_list = data.get("yogas_list", [])
        active_yogas = [y for y in yogas_list if y.get("is_active")]
        if active_yogas:
            lines.append("**Key Formations:**")
            for y in active_yogas[:8]:
                lines.append(f"- {y.get('name')} ({y.get('category')}): {y.get('description')}")

        # Dasha summary & upcoming timeline
        lines.append(f"\n{cls.build_dasha_timeline(data, count=4)}")

        # Live transits
        transit_summary = cls.build_transits_summary(data)
        if transit_summary:
            lines.append(f"\n{transit_summary}")

        return "\n".join(lines)

    @classmethod
    def slice_kp_facts(cls, data: Dict[str, Any]) -> str:
        """Extracts facts relevant specifically to Krishnamurti Paddhati (KP)."""
        lines = []

        # Cusps with Sub-Lords
        lines.append("**12 Placidus House Cusps & Cuspal Sub-Lords (1–249):**")
        cusps_table = data.get("cusps_table", [])
        for c in cusps_table:
            h_name = c.get("house") or f"House {c.get('cusp')}"
            sign = c.get("sign")
            deg = c.get("degree")
            sl = c.get("sign_lord")
            nl = c.get("star_lord")
            sub = c.get("sub_lord")
            lines.append(f"- **{h_name}**: {sign} {deg} | Sign Lord: {sl} | Star Lord: {nl} | **Sub-Lord (CSL): {sub}**")

        # Planets Star & Sub-Lord Placements + 4-Fold Significators
        lines.append("\n**Planetary KP Sub-Lord Placements & 4-Fold Significators:**")
        planets_table = data.get("planets_table", [])
        for p in planets_table:
            pl_name = p.get("planet")
            nl = p.get("star_lord")
            sub = p.get("sub_lord")
            sig_a = p.get("sig_a") or "-"
            sig_b = p.get("sig_b") or "-"
            sig_c = p.get("sig_c") or "-"
            sig_d = p.get("sig_d") or "-"
            lines.append(
                f"- **{pl_name}**: Star: {nl}, Sub: **{sub}** | Significator Levels: "
                f"A: [{sig_a}], B: [{sig_b}], C: [{sig_c}], D: [{sig_d}]"
            )

        # Active Dasha Significators
        ds = data.get("dasha_summary", {})
        lines.append(f"\n**Active Vimshottari Dasha Activation**: MD {ds.get('md')}, AD {ds.get('ad')}, PD {ds.get('pd')}")

        return "\n".join(lines)

    @classmethod
    def slice_jaimini_facts(cls, data: Dict[str, Any]) -> str:
        """Extracts facts relevant specifically to Jaimini Upadesha Sutras."""
        lines = []

        # Chara Karakas (7 and 8)
        lines.append("**7 Chara Karakas (BPHS / Jaimini Classical):**")
        karakas = data.get("chara_karakas_7", [])
        planets_details = data.get("planet_details", {})
        for k in karakas:
            role = k.get("role") or k.get("karaka_name")
            code = k.get("code") or k.get("karaka")
            pl_name = k.get("planet")
            pl_meta = planets_details.get(pl_name, {})
            d9_sign = pl_meta.get("d9_sign", "-")
            d10_sign = pl_meta.get("d10_sign", "-")
            extra = ""
            if code == "AK":
                extra = f" | Karakamsha (D9): {d9_sign} | D10: {d10_sign}"
            elif code == "AmK":
                extra = f" | D9: {d9_sign} | D10 Dashamsha: {d10_sign}"
            lines.append(f"- **{role} ({code})**: {pl_name} ({k.get('sign')} {k.get('degree')}){extra}")

        # 12 Arudha Padas
        lines.append("\n**12 Arudha Padas (Manifested World / Maya):**")
        padas = data.get("arudha_padas", [])
        for ap in padas:
            ex = f" [{ap.get('exception')}]" if ap.get("exception") != "Standard" else ""
            pada_name = ap.get("pada_name") or ap.get("pada")
            house_str = ap.get("house") or f"House {ap.get('house_from_lagna')}"
            lines.append(f"- **{pada_name}**: {ap.get('sign')} ({house_str}){ex}")

        # Chara Dasha
        cs = data.get("chara_dasha_summary", {})
        if cs:
            lines.append("\n**Jaimini Chara Dasha Progression:**")
            lines.append(f"- **Progression Order**: {cs.get('order')}")
            lines.append(f"- **Current Mahadasha**: {cs.get('active_md')} (Lord: {cs.get('active_md_lord')}) -> Dates: {cs.get('md_range')}")
            lines.append(f"- **Active Antardasha**: {cs.get('active_ad')} (Lord: {cs.get('active_ad_lord')}) -> Dates: {cs.get('ad_range')}")

        return "\n".join(lines)

    @classmethod
    def get_chart_fingerprint(cls, data: Dict[str, Any]) -> str:
        """Generates a stable SHA-256 fingerprint from immutable astrological factsheet."""
        dossier = data.get("ai_dossier", {}).get("markdown_dossier", "")
        if not dossier:
            dossier = cls.build_full_ground_truth_matrix(data)
        return hashlib.sha256(dossier.encode("utf-8")).hexdigest()[:20]

    @classmethod
    def clear_three_eyes_cache(cls) -> None:
        """Clears the Three Eyes in-memory cache (useful for tests and memory cleanup)."""
        _THREE_EYES_CACHE.clear()

    @classmethod
    async def run_three_eyes(
        cls,
        data: Dict[str, Any],
        pillar: str = "comprehensive",
        custom_query: str = "",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Dict[str, str]:
        """Runs Eye 1, Eye 2, and Eye 3 with chart-level caching and concurrency throttling."""
        chart_fp = cls.get_chart_fingerprint(data)
        clean_query = (custom_query or "").strip()
        cache_key = f"{chart_fp}_{pillar}_{clean_query}"
        macro_key = f"{chart_fp}_comprehensive_"

        if not force_refresh:
            # Exact match hit (per-chart, per-pillar, per-query)
            if cache_key in _THREE_EYES_CACHE:
                logger.info("Three Eyes cache HIT (exact): %s", cache_key)
                return _THREE_EYES_CACHE[cache_key]

        pillar_title = PILLAR_TITLES.get(pillar, PILLAR_TITLES["comprehensive"])

        p_facts = cls.slice_parashari_facts(data)
        kp_facts = cls.slice_kp_facts(data)
        j_facts = cls.slice_jaimini_facts(data)

        p_prompt = build_parashari_prompt(pillar_title, p_facts, custom_query)
        kp_prompt = build_kp_prompt(pillar_title, kp_facts, custom_query)
        j_prompt = build_jaimini_prompt(pillar_title, j_facts, custom_query)

        # Throttled execution via semaphore + stagger to avoid burst concurrency 429
        async def _throttled_generate(sys_instruction: str, user_prompt: str, stagger_delay: float) -> str:
            if stagger_delay > 0:
                await asyncio.sleep(stagger_delay)
            async with _EYES_SEMAPHORE:
                return await gemini_service.generate_content(
                    system_instruction=sys_instruction,
                    user_prompt=user_prompt,
                    api_key=api_key,
                    model=model,
                    temperature=0.3,
                    max_output_tokens=3000,
                )

        if pillar == "comprehensive":
            p_sys = EYE_1_PARASHARI_WWH_SYSTEM_PROMPT
            kp_sys = EYE_2_KP_WWH_SYSTEM_PROMPT
            j_sys = EYE_3_JAIMINI_WWH_SYSTEM_PROMPT
        elif pillar == "career":
            p_sys = EYE_1_PARASHARI_CAREER_SYSTEM_PROMPT
            kp_sys = EYE_2_KP_CAREER_SYSTEM_PROMPT
            j_sys = EYE_3_JAIMINI_CAREER_SYSTEM_PROMPT
        else:
            p_sys = EYE_1_PARASHARI_SYSTEM_PROMPT
            kp_sys = EYE_2_KP_SYSTEM_PROMPT
            j_sys = EYE_3_JAIMINI_SYSTEM_PROMPT

        t1 = _throttled_generate(p_sys, p_prompt, 0.0)
        t2 = _throttled_generate(kp_sys, kp_prompt, 0.4)
        t3 = _throttled_generate(j_sys, j_prompt, 0.8)

        results = await asyncio.gather(t1, t2, t3, return_exceptions=True)
        res_p = results[0] if isinstance(results[0], str) else f"*(Parashari analysis note: {results[0]})*"
        res_kp = results[1] if isinstance(results[1], str) else f"*(KP analysis note: {results[1]})*"
        res_j = results[2] if isinstance(results[2], str) else f"*(Jaimini analysis note: {results[2]})*"

        # If all three failed with exceptions, raise the primary error
        if all(isinstance(r, Exception) for r in results):
            raise results[0]

        verdicts = {
            "parashari": res_p,
            "kp": res_kp,
            "jaimini": res_j,
        }

        # Store in LRU cache
        if len(_THREE_EYES_CACHE) >= _MAX_CACHE_ENTRIES:
            _THREE_EYES_CACHE.pop(next(iter(_THREE_EYES_CACHE)))
        _THREE_EYES_CACHE[cache_key] = verdicts
        if pillar == "comprehensive" and not clean_query:
            _THREE_EYES_CACHE[macro_key] = verdicts

        return verdicts

    @classmethod
    def calculate_triangulated_confluence(
        cls,
        data: Dict[str, Any],
        pillar: str = "comprehensive",
    ) -> Dict[str, Any]:
        """Calculates deterministic mathematical confluence (0-100%) across Parashara, KP, and Jaimini."""
        # 1. Parashari Score (0-100)
        p_score = 68.0
        func = data.get("functional_nature", {})
        yogas = data.get("yogas_summary", {})
        ds = data.get("dasha_summary", {})
        md_lord = ds.get("md", "")
        yks = func.get("yogakaraka_planets", [])
        marakas = func.get("maraka_planets", [])
        badhaka_lord = func.get("badhaka_lord", "")

        if md_lord in yks:
            p_score += 15.0
        elif md_lord in marakas or md_lord == badhaka_lord:
            p_score -= 10.0

        raja_cnt = yogas.get("raja_count", 0)
        dhana_cnt = yogas.get("dhana_count", 0)
        p_score += min(raja_cnt * 3.0 + dhana_cnt * 2.0, 15.0)

        live_sade = data.get("gochar", {}).get("summary", {}).get("sade_sati", "")
        if live_sade:
            if live_sade not in ("Inactive", "Inactive (Clear)", "No", "None", "") and "Not Active" not in live_sade:
                p_score -= 8.0
        elif yogas.get("sade_sati_status") not in ("Inactive", "Inactive (Clear)", "No", "None", "", None):
            p_score -= 8.0

        if pillar == "relationships":
            gender = (data.get("gender") or data.get("summary", {}).get("gender") or "male").lower()
            rel_graha = "Venus" if gender == "male" else ("Jupiter" if gender == "female" else None)
            if rel_graha:
                pl_obj = next((p for p in data.get("planets_table", []) if p.get("planet") == rel_graha), None)
                if pl_obj:
                    if pl_obj.get("is_exalted") or pl_obj.get("is_own_sign") or pl_obj.get("is_moolatrikona") or "Exalted" in pl_obj.get("dignity_label", "") or "Own" in pl_obj.get("dignity_label", ""):
                        p_score += 8.0
                    elif (pl_obj.get("is_debilitated") or "Debilitated" in pl_obj.get("dignity_label", "")) and not pl_obj.get("has_neechabhanga"):
                        p_score -= 8.0

        p_score = max(35.0, min(95.0, p_score))

        # 2. KP Score (0-100)
        kp_score = 70.0
        cusps = data.get("cusps_table", [])
        target_cusp_num = 10 if pillar == "career" else (7 if pillar == "relationships" else 1)
        target_cusp = next((c for c in cusps if c.get("cusp") == target_cusp_num or c.get("house") == f"House {target_cusp_num:02d}"), None)
        if target_cusp:
            csl = target_cusp.get("sub_lord", "")
            csl_planet = next((p for p in data.get("planets_table", []) if p.get("planet") == csl), None)
            if csl_planet:
                str_pct = csl_planet.get("strength_score", 60.0)
                if isinstance(str_pct, (int, float)):
                    kp_score = 45.0 + (str_pct * 0.45)

        kp_score = max(35.0, min(95.0, kp_score))

        # 3. Jaimini Score (0-100)
        j_score = 68.0
        karakas = data.get("chara_karakas_7", [])
        target_karaka_code = "AmK" if pillar == "career" else ("DK" if pillar == "relationships" else "AK")
        k_entry = next((k for k in karakas if (k.get("code") or k.get("karaka")) == target_karaka_code), None)
        if k_entry:
            k_planet = next((p for p in data.get("planets_table", []) if p.get("planet") == k_entry.get("planet")), None)
            if k_planet:
                h = k_planet.get("natal_house", 1)
                if h in (1, 4, 7, 10, 5, 9, 11):
                    j_score += 12.0
                elif h in (6, 8, 12):
                    j_score -= 10.0

        j_score = max(35.0, min(95.0, j_score))

        total_score = int(round((p_score * 0.4) + (kp_score * 0.3) + (j_score * 0.3)))
        total_score = max(40, min(98, total_score))
        level = "Triple Confluence" if total_score >= 82 else ("Double Confluence" if total_score >= 65 else "Karmic Tension")

        return {
            "score": total_score,
            "level": level,
            "components": {
                "parashari": int(round(p_score)),
                "kp": int(round(kp_score)),
                "jaimini": int(round(j_score)),
            },
        }

    @classmethod
    async def stream_synthesis(
        cls,
        data: Dict[str, Any],
        pillar: str = "comprehensive",
        custom_query: str = "",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        force_refresh: bool = False,
    ) -> AsyncIterator[str]:
        """Orchestrates 3-Eye evaluation and streams the final synthesis over SSE."""
        pillar_title = PILLAR_TITLES.get(pillar, PILLAR_TITLES["comprehensive"])

        # 1. Emit start event
        yield f"event: status\ndata: {json.dumps({'message': 'Awakening the Three Eyes (Parashara, KP, Jaimini)...', 'stage': 'three_eyes'})}\n\n"

        # 2. Run 3 eyes in parallel (cached by chart fingerprint)
        try:
            eyes_verdicts = await cls.run_three_eyes(
                data,
                pillar=pillar,
                custom_query=custom_query,
                api_key=api_key,
                model=model,
                force_refresh=force_refresh,
            )
        except Exception as exc:
            logger.error("Three Eyes evaluation error: %s", exc)
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
            return

        # 3. Calculate deterministic mathematical confluence
        confluence_meta = cls.calculate_triangulated_confluence(data, pillar=pillar)

        # 4. Emit individual eye results and confluence gauge so UI lights up immediately
        yield f"event: eyes_ready\ndata: {json.dumps(eyes_verdicts)}\n\n"
        yield f"event: confluence\ndata: {json.dumps(confluence_meta)}\n\n"
        yield f"event: status\ndata: {json.dumps({'message': 'Three Eyes evaluated. Synthesizing unified reading...', 'stage': 'synthesis'})}\n\n"

        # 5. Prepare Maha-Synthesizer Prompt
        natal_summary = cls.build_full_ground_truth_matrix(data)
        synth_prompt = build_synthesizer_prompt(
            pillar_title=pillar_title,
            parashari_verdict=eyes_verdicts["parashari"],
            kp_verdict=eyes_verdicts["kp"],
            jaimini_verdict=eyes_verdicts["jaimini"],
            natal_summary=natal_summary,
            custom_query=custom_query,
            confluence_meta=confluence_meta,
            pillar_key=pillar,
        )

        contents = [{"role": "user", "parts": [{"text": synth_prompt}]}]
        active_system_prompt = (
            WHAT_WHY_HOW_SYSTEM_PROMPT
            if pillar == "comprehensive"
            else CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
            if pillar == "career"
            else MAHA_SYNTHESIZER_SYSTEM_PROMPT
        )

        # 6. Stream final synthesis tokens
        try:
            async for token in gemini_service.stream_generate_content(
                system_instruction=active_system_prompt,
                contents=contents,
                api_key=api_key,
                model=model,
                temperature=0.4,
                max_output_tokens=6000,
            ):
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

            yield f"event: complete\ndata: {json.dumps({'status': 'finished'})}\n\n"
        except Exception as exc:
            logger.error("Synthesis streaming error: %s", exc)
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"

    @classmethod
    async def stream_chat(
        cls,
        data: Dict[str, Any],
        messages: List[Dict[str, str]],
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        active_reading_summary: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Streams conversation replies with ground truth dossier anchored in system_instruction."""
        ai_dossier = data.get("ai_dossier", {})
        dossier_md = ai_dossier.get("markdown_dossier") or cls.build_full_ground_truth_matrix(data)

        sanitized_summary = None
        if active_reading_summary:
            sanitized_summary = sanitize_evidence(active_reading_summary, max_chars=4000)

        system_instruction = build_chat_system_instruction(dossier_md, active_reading_summary=sanitized_summary)

        # Sliding window of last 12 messages to keep token usage lean and avoid context bloat
        recent_messages = messages[-12:] if len(messages) > 12 else messages

        # Convert conversation messages to Gemini format, ensuring alternating roles
        contents = []
        for msg in recent_messages:
            role = "model" if msg.get("role") in ["assistant", "model"] else "user"
            content_text = sanitize_user_text(msg.get("content") or "", MAX_CHAT_MESSAGE_CHARS)
            if not content_text:
                continue
            # Ensure alternating turn requirement for Gemini API
            if contents and contents[-1]["role"] == role:
                contents[-1]["parts"][0]["text"] += f"\n\n{content_text}"
            else:
                contents.append({
                    "role": role,
                    "parts": [{"text": content_text}],
                })

        # Gemini requires first turn to be 'user'
        if not contents or contents[0]["role"] != "user":
            contents.insert(0, {"role": "user", "parts": [{"text": "Hello, please review my horoscope blueprint."}]})

        try:
            async for token in gemini_service.stream_generate_content(
                system_instruction=system_instruction,
                contents=contents,
                api_key=api_key,
                model=model,
                temperature=0.5,
                max_output_tokens=4000,
            ):
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

            yield f"event: complete\ndata: {json.dumps({'status': 'finished'})}\n\n"
        except Exception as exc:
            logger.error("Chat streaming error: %s", exc)
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
