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

ASC_ARCHETYPE_PREFIX: Dict[int, str] = {
    1: "Pioneering Catalyst",
    2: "Grounded Realist",
    3: "Curious Synthesizer",
    4: "Intuitive Protector",
    5: "Sovereign Anchor",
    6: "Discerning Craftsman",
    7: "Harmonious Architect",
    8: "Unflinching Realist",
    9: "Visionary Seeker",
    10: "Stoic Foundation",
    11: "Unconventional Systems-Thinker",
    12: "Oceanic Mystic",
}

AK_ARCHETYPE_NOUN: Dict[str, str] = {
    "Sun": "Sovereign Truth-Teller",
    "Moon": "Empathetic Anchor",
    "Mars": "Action Pioneer",
    "Mercury": "Perceptive Analyst",
    "Jupiter": "Ethical Mentor",
    "Venus": "Creative Peacemaker",
    "Saturn": "Patient Pillar of Endurance",
    "Rahu": "Transformative Visionary",
    "Ketu": "Transcendent Realist",
}

ASC_NATURAL_INSTINCT: Dict[int, str] = {
    1: "Direct, action-oriented initiator who moves on instinct and cuts through hesitation",
    2: "Patient, deliberate presence who takes time before speaking and anchors everyone around them",
    3: "Quick-witted, perceptive observer who reads the room instantly and connects ideas effortlessly",
    4: "Protective, receptive presence with an instinctive emotional radar that senses unspoken undercurrents",
    5: "Warm, dignified natural presence who carries quiet authority and values honesty above all",
    6: "Sharp, observant perfectionist who spots details others miss and brings immediate practical order",
    7: "Diplomatic, gracious listener who seeks balance and defuses tension before conflict erupts",
    8: "Intense, watchful guardian who keeps cards close to the chest and tests trust thoroughly",
    9: "Direct, open-hearted truth-teller who seeks higher meaning and resists being constrained",
    10: "Pragmatic, reserved builder who measures actions carefully and values competence over talk",
    11: "Independent, unconventional thinker who evaluates things objectively and charts their own course",
    12: "Gentle, imaginative soul who absorbs atmospheres deeply and moves by instinct rather than rigid logic",
}

MOON_HOUSE_EMOTIONAL_ANCHOR: Dict[int, str] = {
    1: "Autonomous emotional compass needing personal breathing room and authentic self-expression to feel centered",
    2: "Grounded domestic anchor that settles through material stability, familiar comforts, and quiet loyalty",
    3: "Curious, agile emotional rhythm that processes feelings through mental exploration, writing, and direct dialogue",
    4: "Deeply rooted private heart that requires a peaceful, undisturbed home sanctuary to recharge",
    5: "Warm, expressive emotional core craving authentic joy, creative flow, and reciprocal appreciation",
    6: "Conscientious, duty-driven nervous system that finds emotional relief through productive order and solving practical problems",
    7: "Devoted, relational heart that needs mutual transparency, equality, and deep partnership to feel truly safe",
    8: "Intense, subterranean emotional core that guards vulnerabilities fiercely and requires absolute trust before opening",
    9: "Expansive, philosophically minded spirit that finds emotional calm in higher principles, travel, and perspective",
    10: "Dignified, purpose-driven emotional compass that needs worldly competence and public self-respect to rest easy",
    11: "Egalitarian, community-minded heart that feels calmest when contributing to shared ideals with trusted allies",
    12: "Solitary, reflective soul sanctuary that requires deep sensory retreat, stillness, and emotional decompression to reset",
}

SUN_HOUSE_CORE_DRIVE: Dict[int, str] = {
    1: "Claiming complete self-determination and building a life directed entirely by personal vision",
    2: "Securing tangible enduring wealth and protecting the long-term well-being of family and lineage",
    3: "Testing courage through hands-on mastery, persuasive initiative, and fearless personal enterprise",
    4: "Cultivating unshakeable emotional peace, domestic security, and enduring personal roots",
    5: "Leaving a distinct creative mark, exercising sovereign intellect, and mentoring future potential",
    6: "Overcoming tangible obstacles through disciplined daily craft, resilience, and problem-solving mastery",
    7: "Forging high-trust partnerships, earning public credibility, and excelling in the public arena",
    8: "Mastering life's hidden levers, navigating high-stakes transformation, and achieving profound self-mastery",
    9: "Living in unwavering alignment with higher wisdom, truth, and leaving behind an ethical legacy",
    10: "Building recognized worldly achievement, institutional authority, and an enduring mark on your field",
    11: "Realizing ambitious collective aspirations and mobilizing networks of mutual advancement",
    12: "Transcending conventional ambition, seeking spiritual liberation, and serving a quiet purpose beyond ego",
}

AK_DEEPEST_HUNGER: Dict[str, str] = {
    "Sun": "Living in uncompromising alignment with your inner truth without ever wearing a mask or seeking permission",
    "Moon": "Experiencing unconditional emotional sanctuary and being truly seen and understood for who you are",
    "Mars": "Channeling fierce purposeful drive into tangible victories without burning out on battles that do not matter",
    "Mercury": "Achieving unclouded intellectual clarity, uncovering fundamental truths, and communicating with precision",
    "Jupiter": "Anchoring life to deep spiritual wisdom, living with integrity, and guiding others toward higher understanding",
    "Venus": "Experiencing profound devoted connection and bringing beauty, grace, and harmony into an imperfect world",
    "Saturn": "Fulfilling your life's duty with unflinching integrity and leaving behind a foundation that outlasts you",
    "Rahu": "Breaking past ancestral limitations, shattering stale conventions, and exploring uncharted frontiers",
    "Ketu": "Releasing worldly attachments, achieving inner stillness, and resting in complete spiritual freedom",
}

LAGNA_LORD_GOLDEN_LEVER: Dict[str, str] = {
    "Saturn": "Protecting one uninterrupted block of deep focus daily and trusting gradual, incremental compounding over rushed quick fixes.",
    "Jupiter": "Anchoring major choices to your highest ethical standard and refusing compromises that trade peace of mind for quick approval.",
    "Mars": "Channeling raw physical initiative into one decisive constructive action each morning before over-deliberation creates friction.",
    "Venus": "Protecting your energetic boundaries and curating harmonious surroundings before people-pleasing drains your reservoir.",
    "Mercury": "Externalizing mental clutter into written checklists and closing open cognitive tabs rather than holding everything in memory.",
    "Sun": "Stepping into quiet authority without waiting for external permission, while mentoring others rather than carrying the whole burden alone.",
    "Moon": "Honoring your natural emotional tides as valuable data rather than criticizing yourself for needing time to rest and reset.",
}

ELEMENT_GROUNDING_PRACTICE: Dict[str, str] = {
    "Earth": "Daily tactile grounding: walking barefoot on grass, handling natural materials, keeping fixed meal and sleep hours, and completing one physical task.",
    "Water": "Emotional hydration: warm evening baths, intentional daily hydration, listening to calming instrumental music, and releasing unexpressed grief.",
    "Fire": "Morning vitality activation: brisk cardiovascular movement at sunrise, exposure to direct sunlight, and eating warm, lightly spiced nourishing meals.",
    "Air": "Conscious breath and quiet space: uncluttering your immediate physical workspace, practicing 10 minutes of slow pranayama, and turning off screens.",
}

ASC_PARADOX_TRAITS: Dict[int, tuple] = {
    1: ("Assertive Initiator", "direct urgency, pioneering momentum, and immediate candor"),
    2: ("Grounded Realist", "deliberate patience, composure, and sensory steadiness"),
    3: ("Curious Synthesizer", "quick agility, conversational charm, and mental adaptability"),
    4: ("Protective Receptive Presence", "gentle empathy, instinctive sensitivity, and protective warmth"),
    5: ("Dignified Sovereign", "natural poise, calm self-assurance, and quiet authority"),
    6: ("Discerning Perfectionist", "analytical precision, observant modesty, and practical competence"),
    7: ("Diplomatic Connector", "graceful diplomacy, balanced charm, and social poise"),
    8: ("Watchful Guardian", "penetrating focus, intense composure, and guarded reserve"),
    9: ("Visionary Seeker", "open-hearted optimism, philosophical candor, and enthusiastic reach"),
    10: ("Pragmatic Builder", "deliberate composure, unshakeable patience, and pragmatic dependability"),
    11: ("Unconventional Thinker", "objective detachment, intellectual uniqueness, and calm equality"),
    12: ("Gentle Mystic", "fluid empathy, adaptable tolerance, and gentle intuition"),
}

MOON_HOUSE_PARADOX: Dict[int, tuple] = {
    1: ("Autonomous Emotional Intensity", "needs complete personal autonomy and authentic expression, struggling whenever others try to dictate how you should feel"),
    2: ("Deeply Guarded Material & Family Anchor", "is deeply anchored in material predictability and family safety, craving enduring emotional security behind your external interface"),
    3: ("Restless Mental Processing & Active Inquiry", "operates at high intellectual speed—processing feelings through mental dialogue, writing, or debate, privately impatient with vague communication"),
    4: ("Deep Private Sanctuary & Domestic Retreat", "craves an inviolable private home sanctuary to decompress, feeling deeply vulnerable whenever domestic harmony or emotional roots are disturbed"),
    5: ("Creative Heart & Hunger for Authentic Joy", "carries intense creative passion and romantic vulnerability, feeling deeply stifled by dry bureaucratic routine or lack of heartfelt appreciation"),
    6: ("High-Friction Troubleshooter & Duty-Driven Inspector", "operates as a relentless analytical troubleshooter—privately cataloging flaws, impatient with inefficiency, and quietly carrying the burden of solving messy friction"),
    7: ("Relational Mirror & Craving for Equal Partnership", "is intensely attuned to partnership dynamics—feeling incomplete without mutual transparency and respect, yet vulnerable to over-absorbing a partner's mood"),
    8: ("Subterranean Depths & Private Psychological Vault", "navigates intense, subterranean psychological currents—guarding vulnerabilities with fierce secrecy, demanding raw authenticity, and needing private space to process heavy transitions"),
    9: ("Philosophical Seeker & Long-Range Idealist", "finds peace only in higher principles, freedom of movement, and long-range vision, feeling suffocated by small-minded pettiness or narrow dogmas"),
    10: ("Severe Conscience & Public Accountability", "holds yourself to severe internal standards of competence and dignity, feeling privately uneasy unless your worldly contributions are undeniable and respected"),
    11: ("Collective Visionary & Network Anchor", "feels called to large-scale ideals and group camaraderie, yet privately fears losing individual sovereignty within the crowd"),
    12: ("Solitary Decompression & Sensory Retreat", "carries an acute need for solitary decompression and sensory silence—feeling chronically drained by everyday noise and needing regular retreat to restore peace"),
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

        # 3. Core Identity, Character Archetype & Triad Tags
        summary = data.get("summary", {})
        asc = summary.get("ascendant", {})
        moon = summary.get("moon", {})
        sun = summary.get("sun", {})
        asc_sign_name = asc.get("sign", "")
        moon_sign_name = moon.get("sign", "")
        sun_sign_name = sun.get("sign", "")
        
        asc_sid = next((p.get("sign_id") for p in planets_table if "Ascendant" in p.get("planet", "")), 1)
        moon_row = next((p for p in planets_table if "Moon" in p.get("planet", "")), {})
        moon_sid = moon_row.get("sign_id", 1)
        moon_nakshatra = moon_row.get("nakshatra") or moon.get("nakshatra", "")
        sun_row = next((p for p in planets_table if "Sun" in p.get("planet", "")), {})
        sun_sid = sun_row.get("sign_id", 1)
        sun_house = sun_row.get("natal_house") or (((sun_sid - asc_sid) % 12) + 1)

        # Karakas (AK)
        karakas = data.get("chara_karakas_7") or data.get("karakas") or data.get("jaimini", {}).get("chara_karakas", [])
        ak_entry = next((k for k in karakas if (k.get("code") or k.get("karaka")) == "AK"), {})
        ak_graha = ak_entry.get("planet") or "Sun"

        # Ascendant Lord
        asc_lord = asc.get("lord") or ZODIAC_SIGNS.get(asc_sid, {}).get("lord", "Saturn")
        asc_lord_str = asc_lord.value if hasattr(asc_lord, "value") else str(asc_lord)

        # 4. Core Character Archetype
        arch_prefix = ASC_ARCHETYPE_PREFIX.get(asc_sid, "Grounded Realist")
        arch_noun = AK_ARCHETYPE_NOUN.get(ak_graha, "Sovereign Truth-Teller")
        character_archetype = f"The {arch_prefix} & {arch_noun}"

        # 5. Triad Tags (Lagna, Moon, Sun, AK)
        natural_instinct_tag = ASC_NATURAL_INSTINCT.get(asc_sid, "Patient, deliberate presence who takes time before speaking")
        moon_house_from_lagna = ((moon_sid - asc_sid) % 12) + 1
        emotional_anchor_tag = MOON_HOUSE_EMOTIONAL_ANCHOR.get(moon_house_from_lagna, "Private emotional sanctuary requiring space to recharge")
        core_drive_tag = SUN_HOUSE_CORE_DRIVE.get(sun_house, "Building unshakeable personal stability and purpose")
        deepest_hunger_tag = AK_DEEPEST_HUNGER.get(ak_graha, "Living in uncompromising alignment with your inner truth")

        # 6. Dynamic Inner Paradox (Lagna vs Moon House)
        asc_title, asc_stance = ASC_PARADOX_TRAITS.get(asc_sid, ("Steadfast Presence", "deliberate composure and grounded dependability"))
        moon_title, moon_need = MOON_HOUSE_PARADOX.get(moon_house_from_lagna, ("Private Inner World", "craves emotional safety and undisturbed peace"))
        
        planets_on_lagna = [p.get("planet") for p in planets_table if p.get("natal_house") == 1 and "Ascendant" not in p.get("planet", "")]
        lagna_influence = f" with {', '.join(planets_on_lagna)}" if planets_on_lagna else ""

        paradox_headline = f"{asc_title} ({asc_sign_name}{lagna_influence}) vs. {moon_title} ({moon_sign_name} Moon in House {moon_house_from_lagna})"
        paradox_narrative = (
            f"Outwardly, you project {asc_stance} ({asc_sign_name}). "
            f"Inwardly, however, your emotional center ({moon_sign_name} Moon in {moon_nakshatra}, House {moon_house_from_lagna}) {moon_need}."
        )

        # 7. Karmic Axis (Comfort Zone vs Growth Edge)
        rahu_row = next((p for p in planets_table if "Rahu" in p.get("planet", "")), {})
        ketu_row = next((p for p in planets_table if "Ketu" in p.get("planet", "")), {})
        rahu_h = rahu_row.get("natal_house", 10)
        ketu_h = ketu_row.get("natal_house", 4)
        rahu_sign = rahu_row.get("sign", "")
        ketu_sign = ketu_row.get("sign", "")

        comfort_desc = KARMIC_COMFORT_MAP.get(ketu_h, f"Defaulting to habits of House {ketu_h} ({ketu_sign}).")
        growth_desc = KARMIC_GROWTH_MAP.get(rahu_h, f"Expanding into the potential of House {rahu_h} ({rahu_sign}).")

        # 8. Deterministic Stress & Recovery Profile
        dominant_dosha = sorted_doshas[0][0]
        if dominant_dosha == "vata":
            stress_trigger = "Unpredictable schedule disruptions, sensory clutter, rushed multi-tasking, and being forced into split-second commitments."
            stress_reaction = "Mental scatter, shallow breathing, racing anxiety loops, and an urge to isolate or run away."
        elif dominant_dosha == "pitta":
            stress_trigger = "Incompetence or sloppiness in collaborators, avoidable procedural delays, and feeling micro-managed or stripped of control."
            stress_reaction = "Sharp irritability, physical heat, biting sarcasm, and an urge to aggressively take over the whole task."
        else:
            stress_trigger = "Sudden unexpected disruptions to routine, emotional hostility, feeling taken for granted, and sensory stagnation."
            stress_reaction = "Emotional shutdown, heavy lethargy, passive stubbornness, and retreating behind complete silence."

        # Lowest element for antidote
        sorted_elems_asc = sorted(elem_pcts.items(), key=lambda x: x[1])
        lowest_elem = sorted_elems_asc[0][0]
        stress_recovery = ELEMENT_GROUNDING_PRACTICE.get(lowest_elem, "Quiet stillness and intentional rest.")

        # 9. Growth Levers
        golden_lever = LAGNA_LORD_GOLDEN_LEVER.get(
            asc_lord_str,
            "Protecting one dedicated block of focused effort daily and prioritizing steady compounding over rushed quick fixes."
        )
        grounding_practice = ELEMENT_GROUNDING_PRACTICE.get(
            lowest_elem,
            "Daily quiet reflection and consistent routines to steady your vital energy."
        )

        return {
            "element_pcts": elem_pcts,
            "element_label": element_label,
            "dosha_pcts": dosha_pcts,
            "prakriti_label": prakriti_label,
            "character_archetype": character_archetype,
            "triad_tags": {
                "natural_instinct_tag": natural_instinct_tag,
                "emotional_anchor_tag": emotional_anchor_tag,
                "core_drive_tag": core_drive_tag,
                "deepest_hunger_tag": deepest_hunger_tag,
            },
            "paradox": {
                "headline": paradox_headline,
                "narrative": paradox_narrative,
            },
            "karmic_axis": {
                "headline": f"Comfort Zone (House {ketu_h}) vs. Growth Edge (House {rahu_h})",
                "comfort_zone": comfort_desc,
                "growth_edge": growth_desc,
            },
            "stress_response": {
                "trigger": stress_trigger,
                "reaction": stress_reaction,
                "recovery": stress_recovery,
            },
            "growth_levers": {
                "golden_lever": golden_lever,
                "habit_to_unlearn": comfort_desc,
                "grounding_practice": grounding_practice,
            },
        }

    @classmethod
    def build_constitutional_ground_truth(cls, data: Dict[str, Any]) -> str:
        """Formats the computed constitutional blueprint into an unambiguous ground-truth block for LLM synthesis."""
        prof = cls.compute_constitutional_blueprint(data)
        triad = prof["triad_tags"]
        stress = prof["stress_response"]
        levers = prof["growth_levers"]
        lines = [
            "### COMPUTED CONSTITUTIONAL ENGINE & CHARACTER GROUND TRUTH (MATHEMATICAL FACT):",
            f"- **Core Character Archetype (Immutable Identity)**: {prof['character_archetype']}",
            f"- **Elemental Balance (Exact Math)**: {prof['element_label']} [Fire: {prof['element_pcts']['Fire']}%, Earth: {prof['element_pcts']['Earth']}%, Air: {prof['element_pcts']['Air']}%, Water: {prof['element_pcts']['Water']}%]",
            f"- **Ayurvedic Prakriti (Exact Math)**: {prof['prakriti_label']} [Vata: {prof['dosha_pcts']['vata']}%, Pitta: {prof['dosha_pcts']['pitta']}%, Kapha: {prof['dosha_pcts']['kapha']}%]",
            f"- **Outer Instinct (Lagna)**: {triad['natural_instinct_tag']}",
            f"- **Emotional Core (Chandra)**: {triad['emotional_anchor_tag']}",
            f"- **Core Drive (Surya)**: {triad['core_drive_tag']}",
            f"- **Deepest Hunger (Atmakaraka)**: {triad['deepest_hunger_tag']}",
            f"- **Core Inner Paradox (Primary Tension)**: {prof['paradox']['headline']}",
            f"  *Psychological Dynamic*: {prof['paradox']['narrative']}",
            f"- **Karmic Axis (Soul Evolution)**: {prof['karmic_axis']['headline']}",
            f"  *Default Comfort Zone (When Tired/Cornered)*: {prof['karmic_axis']['comfort_zone']}",
            f"  *Active Growth Edge (Unlock Next Level)*: {prof['karmic_axis']['growth_edge']}",
            f"- **Stress & Nervous System Dynamics**:",
            f"  *Stress Trigger*: {stress['trigger']}",
            f"  *Stress Reaction*: {stress['reaction']}",
            f"  *Nervous System Reset*: {stress['recovery']}",
            f"- **Daily Growth & Grounding Anchors**:",
            f"  *Golden Habit Lever*: {levers['golden_lever']}",
            f"  *Habit to Catch & Let Go*: {levers['habit_to_unlearn']}",
            f"  *Elemental Grounding Practice*: {levers['grounding_practice']}",
            "(CRITICAL INSTRUCTION: In your JSON output, you MUST adopt this computed 'character_archetype' into 'archetype', use the exact elemental/prakriti labels, and anchor 'constitution.natural_instinct_tag', 'constitution.emotional_anchor_tag', 'constitution.core_drive_tag', and 'constitution.deepest_hunger_tag' directly into the computed ground-truth tags. Weave the dynamic paradox into 'the_why.inner_paradox' without copying prompt examples!)",
        ]
        return "\n".join(lines)

    @classmethod
    def compute_vocational_blueprint(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates deterministic vocational, enterprise, wealth, and authority alignments."""
        planets_table = data.get("planets_table", [])
        ashtakavarga = data.get("ashtakavarga", {})
        sav_list = ashtakavarga.get("sarvashtakavarga", [])
        sav_map = {entry.get("house_from_lagna"): entry.get("total_bindus", 28) for entry in sav_list if entry.get("house_from_lagna") is not None}

        # 1. Ascendant & House Rulers
        asc_sid = next((p.get("sign_id", 1) for p in planets_table if "Ascendant" in p.get("planet", "")), 1)

        def house_sign_id(h_num: int) -> int:
            return ((asc_sid - 1 + h_num - 1) % 12) + 1

        def house_lord_name(h_num: int) -> str:
            s_id = house_sign_id(h_num)
            l = ZODIAC_SIGNS.get(s_id, {}).get("lord", "")
            return l.value if hasattr(l, "value") else str(l)

        lord_10 = house_lord_name(10)
        lord_6 = house_lord_name(6)
        lord_7 = house_lord_name(7)
        lord_2 = house_lord_name(2)
        lord_11 = house_lord_name(11)

        pl_by_name = {p.get("planet"): p for p in planets_table}
        pl_in_house: Dict[int, List[str]] = {h: [] for h in range(1, 13)}
        for p in planets_table:
            h = p.get("natal_house")
            pl_name = p.get("planet")
            if h and pl_name and "Ascendant" not in pl_name:
                pl_in_house.setdefault(h, []).append(pl_name)

        karakas = data.get("chara_karakas_7", []) or data.get("chara_karakas_8", [])
        amk_entry = next((k for k in karakas if (k.get("code") or k.get("karaka")) == "AmK"), None)
        amk_planet = amk_entry.get("planet", "") if amk_entry else lord_10

        b3 = sav_map.get(3, 28)
        b6 = sav_map.get(6, 28)
        b7 = sav_map.get(7, 28)
        b10 = sav_map.get(10, 28)
        b11 = sav_map.get(11, 28)

        h_lord10 = pl_by_name.get(lord_10, {}).get("natal_house", 0)
        h_lord6 = pl_by_name.get(lord_6, {}).get("natal_house", 0)
        h_lord7 = pl_by_name.get(lord_7, {}).get("natal_house", 0)
        h_amk = pl_by_name.get(amk_planet, {}).get("natal_house", 0)

        # 2. Score 3 Distinct Career Paths
        # Track A: Independent Venture / Founder / Business Operator
        score_venture = 50.0
        if b7 >= 30: score_venture += 12.0
        if b10 >= 30: score_venture += 10.0
        if b3 >= 28: score_venture += 8.0
        if b7 > b6: score_venture += 10.0
        if len(pl_in_house.get(7, [])) > len(pl_in_house.get(6, [])): score_venture += 8.0
        if h_lord10 in (1, 7, 10, 11): score_venture += 16.0
        sun_h = pl_by_name.get("Sun", {}).get("natal_house", 0)
        mars_h = pl_by_name.get("Mars", {}).get("natal_house", 0)
        if sun_h == 10 or mars_h == 10: score_venture += 16.0
        if sun_h == 1 or mars_h == 1: score_venture += 10.0
        if "Rahu" in pl_in_house.get(10, []) or "Rahu" in pl_in_house.get(11, []) or "Rahu" in pl_in_house.get(3, []):
            score_venture += 10.0
        if h_amk in (1, 7, 10, 11): score_venture += 10.0

        # Track B: Leading Within an Established Organization / Institutional Pillar
        score_employment = 50.0
        if b6 >= 30: score_employment += 15.0
        if b6 > b7: score_employment += 12.0
        if len(pl_in_house.get(6, [])) > len(pl_in_house.get(7, [])): score_employment += 8.0
        if h_lord10 in (6, 2, 12): score_employment += 16.0
        if h_lord6 in (10, 1): score_employment += 14.0
        saturn_h = pl_by_name.get("Saturn", {}).get("natal_house", 0)
        if saturn_h in (1, 4, 7, 10, 3, 6, 11): score_employment += 12.0
        if h_amk == 6: score_employment += 14.0
        if lord_10 == "Saturn" or amk_planet == "Saturn": score_employment += 10.0
        if "Saturn" in pl_in_house.get(10, []) or "Saturn" in pl_in_house.get(6, []): score_employment += 10.0

        # Track C: Specialized Independent Practice & Expert Advisory
        score_advisory = 50.0
        if h_lord10 in (9, 5, 8): score_advisory += 18.0
        lord_9 = house_lord_name(9)
        lord_5 = house_lord_name(5)
        h_lord9 = pl_by_name.get(lord_9, {}).get("natal_house", 0)
        h_lord5 = pl_by_name.get(lord_5, {}).get("natal_house", 0)
        if h_lord9 == 10 or h_lord5 == 10: score_advisory += 16.0
        if lord_10 in ("Jupiter", "Mercury") or amk_planet in ("Jupiter", "Mercury"): score_advisory += 16.0
        jup_h = pl_by_name.get("Jupiter", {}).get("natal_house", 0)
        merc_h = pl_by_name.get("Mercury", {}).get("natal_house", 0)
        if jup_h in (10, 9, 1, 5) or merc_h in (10, 9, 1, 5): score_advisory += 12.0
        if "Ketu" in pl_in_house.get(10, []) or "Ketu" in pl_in_house.get(9, []) or "Ketu" in pl_in_house.get(8, []):
            score_advisory += 12.0

        scores = [
            ("venture", score_venture),
            ("employment", score_employment),
            ("advisory", score_advisory),
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        top_track = scores[0][0]

        if top_track == "venture":
            rec_path = "Building Your Own Independent Venture (Founder / Business Operator)"
            optimal_vehicle = "Independent enterprise, boutique founder, direct B2B venture, or commercial ownership"
            rationale = (
                f"Your 7th/10th houses of sovereignty and commerce (SAV: H7 {b7}, H10 {b10}) dominate over service sectors (H6 {b6}), "
                f"with 10th lord {lord_10} placed in House {h_lord10}. You produce peak output when you have ultimate ownership "
                f"of decisions; working under corporate bureaucracy or risk-averse managers suffocates your momentum."
            )
        elif top_track == "employment":
            rec_path = "Leading Within an Established Organization (Executive / Institutional Pillar)"
            optimal_vehicle = "Senior executive leadership, operational director, or mission-critical institutional pillar"
            rationale = (
                f"Your 6th house of competitive service and institutional stamina holds {b6} SAV bindus, with 10th lord {lord_10} "
                f"anchoring organizational impact. You thrive when leveraging large organizational resources, scaling existing teams, "
                f"and exercising authority within a structured corporate or institutional ecosystem."
            )
        else:
            rec_path = "Specialized Independent Practice & Expert Advisory (Boutique Specialist / High-Trust Advisor)"
            optimal_vehicle = "Boutique advisory practice, specialized expert consulting, intellectual property, or autonomous partner"
            rationale = (
                f"Your chart anchors career impact in dharmic and knowledge houses (House 9/5/8) with {amk_planet} and {lord_10} "
                f"directing professional wisdom. You flourish when monetizing deep proprietary expertise and autonomy, rather than "
                f"managing mass corporate bureaucracies or standard retail operations."
            )

        primary_carrier = amk_planet or lord_10
        if primary_carrier == "Mars":
            vocation_archetype = "The High-Impact Operator & Turnaround Leader"
            craft_essence = "Cutting through organizational confusion, fixing broken execution pipelines under pressure, and delivering tangible results where others stall."
            leadership_style = "Decisive command, leading from the front lines, setting a fast pace, and demanding concrete accountability."
        elif primary_carrier == "Sun":
            vocation_archetype = "The Sovereign Strategist & Institutional Commander"
            craft_essence = "Setting high-level strategic direction, holding ultimate responsibility for vision and culture, and building enduring organizational reputation."
            leadership_style = "Sovereign executive presence, leading by clear standards and integrity, and refusing to tolerate petty micromanagement."
        elif primary_carrier == "Mercury":
            vocation_archetype = "The Commercial Architect & Systems Dealmaker"
            craft_essence = "Structuring complex commercial deals, analyzing information asymmetry, and designing scalable automated workflows."
            leadership_style = "Agile collaboration, rapid problem-solving, transparent data-driven decisions, and sharp negotiations."
        elif primary_carrier == "Jupiter":
            vocation_archetype = "The Strategic Counselor & Governance Lead"
            craft_essence = "Guiding complex operations with ethical foresight, long-term capital preservation, and mentoring high-calibre specialists."
            leadership_style = "Wisdom-anchored guidance, building consensus through trust, and holding high moral authority."
        elif primary_carrier == "Venus":
            vocation_archetype = "The Creative Director & High-Trust Client Partner"
            craft_essence = "Curating elite client relationships, designing high-value aesthetic and commercial offerings, and mastering the psychology of persuasion."
            leadership_style = "Diplomatic mediation, inspiring creative brilliance, and elevating team morale through empathy and high standards."
        elif primary_carrier == "Saturn":
            vocation_archetype = "The Master Infrastructure Builder & Operational Anchor"
            craft_essence = "Constructing durable, unshakeable operating systems, enduring unglamorous groundwork, and compounding value through patient discipline."
            leadership_style = "Quiet technical competence, leading by example, unyielding quality control, and zero tolerance for superficial shortcuts."
        else:
            vocation_archetype = "The Intuitive Custodian & Public Impact Leader"
            craft_essence = "Reading collective market and consumer needs instinctively, building emotionally resonant offerings, and fostering deep public loyalty."
            leadership_style = "Empathetic leadership, community alignment, and attuning organizational goals to real human needs."

        h_lord2 = pl_by_name.get(lord_2, {}).get("natal_house", 0)
        h_lord11 = pl_by_name.get(lord_11, {}).get("natal_house", 0)
        if h_lord2 in (1, 10) or h_lord11 in (1, 10):
            wealth_channel = "Direct Profit-Sharing & Equity Value Creation"
            wealth_desc = f"Wealth flows most cleanly through equity ownership, profit-sharing, and sovereign control of high-impact ventures (2nd/11th lords in H{h_lord2}/H{h_lord11})."
        elif h_lord2 in (7, 3) or h_lord11 in (7, 3):
            wealth_channel = "Direct Commercial Dealmaking & Client Contracts"
            wealth_desc = f"Wealth flows through closing client deals, B2B commercial partnerships, and transaction-based trade (2nd/11th lords in H{h_lord2}/H{h_lord11})."
        elif h_lord2 == 6 or h_lord11 == 6:
            wealth_channel = "High-Tier Executive Compensation & Performance Bonuses"
            wealth_desc = f"Wealth flows through competitive organizational compensation, performance bonuses, and solving high-value institutional problems (2nd/11th lords in H6)."
        elif h_lord2 in (9, 5) or h_lord11 in (9, 5):
            wealth_channel = "Advisory Retainers, Intellectual Property & Royalties"
            wealth_desc = f"Wealth flows through proprietary expertise, high-ticket advisory retainers, and intellectual capital monetization (2nd/11th lords in H{h_lord2}/H{h_lord11})."
        else:
            wealth_channel = "Tangible Asset Holdings & Long-Term Compounding"
            wealth_desc = f"Wealth flows through physical asset accumulation, real estate development, and patient capital compounding (2nd/11th lords in H{h_lord2}/H{h_lord11})."

        s_12 = house_sign_id(12)
        elem_12 = ELEMENT_MAP.get(s_12, "Earth")
        if elem_12 == "Fire":
            leak_headline = "Impetuous Capital Deployment & Speculative Rushes"
            leak_pattern = "Deploying money impulsively into speculative ideas or high-risk ventures without rigorous due diligence."
            leak_antidote = "Enforce a mandatory 72-hour cooling-off rule on capital allocations above a defined threshold."
        elif elem_12 == "Air":
            leak_headline = "Scattered Venture Bets & Unmonetized Diversions"
            leak_pattern = "Spreading resources thin across multiple shiny new ideas, software, or unmonetized experiments."
            leak_antidote = "Prune secondary projects; refuse to fund new ventures until the core engine hits its profit target."
        elif elem_12 == "Water":
            leak_headline = "Emotional Lending & Boundary Slippage"
            leak_pattern = "Lending money out of emotional guilt or over-giving to peers, family, or partners without clear repayment terms."
            leak_antidote = "Separate personal empathy from financial capital; never lend money expecting it back."
        else:
            leak_headline = "Underpricing Expertise & Excessive Self-Sacrifice"
            leak_pattern = "Undercharging for specialized expertise, absorbing unexpected project costs yourself, or hesitating to demand premium compensation."
            leak_antidote = "Anchor pricing directly to the economic value generated for the client, never to the hours worked."

        return {
            "recommended_path": rec_path,
            "optimal_vehicle": optimal_vehicle,
            "strategic_rationale": rationale,
            "vocation_archetype": vocation_archetype,
            "craft_essence": craft_essence,
            "leadership_style": leadership_style,
            "primary_carrier": primary_carrier,
            "wealth_channel": wealth_channel,
            "wealth_desc": wealth_desc,
            "leak_headline": leak_headline,
            "leak_pattern": leak_pattern,
            "leak_antidote": leak_antidote,
            "scores": {
                "venture": round(score_venture),
                "employment": round(score_employment),
                "advisory": round(score_advisory),
            },
        }

    @classmethod
    def build_vocational_ground_truth(cls, data: Dict[str, Any]) -> str:
        """Formats the computed vocational blueprint into an unambiguous ground-truth block for LLM synthesis."""
        prof = cls.compute_vocational_blueprint(data)
        lines = [
            "### COMPUTED VOCATIONAL ENGINE & CAREER GROUND TRUTH (MATHEMATICAL FACT):",
            f"- **Enterprise vs. Employment Verdict**: {prof['recommended_path']} [Scores: Venture {prof['scores']['venture']}, Employment {prof['scores']['employment']}, Advisory {prof['scores']['advisory']}]",
            f"- **Strategic Vocational Rationale**: {prof['strategic_rationale']}",
            f"- **Optimal Real-World Vehicle**: {prof['optimal_vehicle']}",
            f"- **Primary Vocational Archetype (Derived from {prof['primary_carrier']})**: {prof['vocation_archetype']}",
            f"- **Primary Craft Essence**: {prof['craft_essence']}",
            f"- **Natural Leadership Stance**: {prof['leadership_style']}",
            f"- **Primary Wealth Inflow Channel**: {prof['wealth_channel']} ({prof['wealth_desc']})",
            f"- **Unconscious Financial Leak**: {prof['leak_headline']} — Pattern: {prof['leak_pattern']} | Antidote: {prof['leak_antidote']}",
            f"(CRITICAL MANDATE: In your JSON output, you MUST set 'enterprise_vs_employment.recommended_path' to '{prof['recommended_path']}'. NEVER output 'Hybrid Path' or any generic compromise. In 'vocation_archetype', use '{prof['vocation_archetype']}' or a fresh bespoke variation matching {prof['primary_carrier']}. In 'work_genius', weave '{prof['craft_essence']}'. In 'wealth_engine.primary_inflow_channel', weave '{prof['wealth_channel']}'!)",
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

        # 0b. Deterministic Vocational Engine & Career Ground Truth
        sections.append(cls.build_vocational_ground_truth(data))

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

        # Constitutional & Vocational Ground Truth
        lines.append(f"\n{cls.build_constitutional_ground_truth(data)}")
        lines.append(f"\n{cls.build_vocational_ground_truth(data)}")

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

        # Constitutional & Vocational Ground Truth
        lines.append(f"\n{cls.build_constitutional_ground_truth(data)}")
        lines.append(f"\n{cls.build_vocational_ground_truth(data)}")

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

        # Constitutional & Vocational Ground Truth
        lines.append(f"\n{cls.build_constitutional_ground_truth(data)}")
        lines.append(f"\n{cls.build_vocational_ground_truth(data)}")

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
                    temperature=0.5,
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
                temperature=0.6,
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
                temperature=0.6,
                max_output_tokens=4000,
            ):
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

            yield f"event: complete\ndata: {json.dumps({'status': 'finished'})}\n\n"
        except Exception as exc:
            logger.error("Chat streaming error: %s", exc)
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
