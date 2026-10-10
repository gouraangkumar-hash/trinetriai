"""Trinetri Multi-Agent Astrological Orchestration Engine.

Orchestrates the Three Eyes (Parashara, KP, Jaimini) concurrent evaluations
via asyncio.gather and streams the synthesized consensus to the client via SSE.
"""

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from prompts.parashari_prompt import (
    EYE_1_PARASHARI_SYSTEM_PROMPT,
    build_parashari_prompt,
)
from prompts.kp_prompt import (
    EYE_2_KP_SYSTEM_PROMPT,
    build_kp_prompt,
)
from prompts.jaimini_prompt import (
    EYE_3_JAIMINI_SYSTEM_PROMPT,
    build_jaimini_prompt,
)
from prompts.synthesizer_prompt import (
    MAHA_SYNTHESIZER_SYSTEM_PROMPT,
    build_synthesizer_prompt,
)
from prompts.chat_prompt import build_chat_system_instruction
from services.llm import gemini_service

logger = logging.getLogger("trinetri.orchestrator")


PILLAR_TITLES = {
    "comprehensive": "1. Comprehensive Life Synthesis (Macro Karma, Purpose & Evolution)",
    "career": "2. Career, Wealth & Professional Rise (10th/2nd/11th Cusps, D10 & AmK)",
    "relationships": "3. Relationships, Marriage & Soul Compatibility (7th Cusp, D9 & Darakaraka)",
    "dasha": "4. Current Dasha & Timing of Upcoming Shifts (Vimshottari, Chara & Transits)",
    "custom": "Custom Consultation Query",
}


class TrinetriOrchestrator:
    """Manages multi-agent parallel execution, fact sheet slicing, and streaming synthesis."""

    @classmethod
    def slice_parashari_facts(cls, data: Dict[str, Any]) -> str:
        """Extracts facts relevant specifically to BPHS Parashari school."""
        lines = []
        summary = data.get("summary", {})
        asc = summary.get("ascendant", {})
        moon = summary.get("moon", {})
        sun = summary.get("sun", {})

        lines.append(f"- **Lagna (Ascendant)**: {asc.get('sign')} at {asc.get('degree')} (Lord: {asc.get('lord')}, Nakshatra: {asc.get('nakshatra')})")
        lines.append(f"- **Moon (Chandra)**: {moon.get('sign')} at {moon.get('degree')} (Lord: {moon.get('lord')}, Nakshatra: {moon.get('nakshatra')})")
        lines.append(f"- **Sun (Surya)**: {sun.get('sign')} at {sun.get('degree')} (Lord: {sun.get('lord')})")

        # Functional nature
        func = data.get("functional_nature", {})
        if func:
            yk = ", ".join(func.get("yogakaraka_planets", [])) or "None"
            mar = ", ".join(func.get("maraka_planets", [])) or "None"
            lines.append(f"- **Yogakaraka Graha(s)**: {yk} | **Maraka Graha(s)**: {mar}")
            lines.append(f"- **Badhaka House**: House {func.get('badhaka_house')} (Lord: {func.get('badhaka_lord')})")

        # Planets summary with D9 & Dignity & Strength
        lines.append("\n**Planetary D1/D9 Dignities & Strengths:**")
        planets_table = data.get("planets_table", [])
        for p in planets_table:
            pl_name = p.get("planet")
            d1_sign = p.get("sign")
            deg = p.get("degree")
            house = p.get("natal_house")
            d9_sign = p.get("d9_sign")
            varg = " (Vargottama)" if "Yes" in p.get("vargottama_status", "") else ""
            dig = p.get("dignity_label", "")
            nb = " [Neechabhanga Cancelled]" if p.get("has_neechabhanga") else ""
            str_pct = p.get("strength_percentage", "-")
            str_grade = p.get("strength_grade", "-")
            func_role = p.get("functional_role", "")
            lines.append(
                f"- **{pl_name}**: in {d1_sign} {deg} (House {house}) | D9: {d9_sign}{varg} | "
                f"Dignity: {dig}{nb} | Functional: {func_role} | Bala: {str_pct} ({str_grade})"
            )

        # Active Yogas
        yogas_summary = data.get("yogas_summary", {})
        lines.append(f"\n**Vedic Yogas Summary**: Total: {yogas_summary.get('total_yogas')}, Raja: {yogas_summary.get('raja_count')}, Dhana: {yogas_summary.get('dhana_count')}")
        lines.append(f"- Sade Sati: {yogas_summary.get('sade_sati_status')} | Kuja Dosha: {yogas_summary.get('kuja_dosha_status')}")
        yogas_list = data.get("yogas_list", [])
        active_yogas = [y for y in yogas_list if y.get("is_active")]
        if active_yogas:
            lines.append("**Key Formations:**")
            for y in active_yogas[:8]:
                lines.append(f"- {y.get('name')} ({y.get('category')}): {y.get('description')}")

        # Dasha summary
        ds = data.get("dasha_summary", {})
        lines.append(f"\n**Active Vimshottari Period**: MD: {ds.get('md')} ({ds.get('md_range')}) -> AD: {ds.get('ad')} ({ds.get('ad_range')}) -> PD: {ds.get('pd')} ({ds.get('pd_range')})")

        return "\n".join(lines)

    @classmethod
    def slice_kp_facts(cls, data: Dict[str, Any]) -> str:
        """Extracts facts relevant specifically to Krishnamurti Paddhati (KP)."""
        lines = []

        # Cusps with Sub-Lords
        lines.append("**12 Placidus House Cusps & Cuspal Sub-Lords (1–249):**")
        cusps_table = data.get("cusps_table", [])
        for c in cusps_table:
            h_num = c.get("cusp")
            sign = c.get("sign")
            deg = c.get("degree")
            sl = c.get("sign_lord")
            nl = c.get("star_lord")
            sub = c.get("sub_lord")
            lines.append(f"- **Cusp {h_num}**: {sign} {deg} | Sign Lord: {sl} | Star Lord: {nl} | **Sub-Lord (CSL): {sub}**")

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
        for k in karakas:
            lines.append(f"- **{k.get('karaka_name')} ({k.get('karaka')})**: {k.get('planet')} ({k.get('sign')} {k.get('degree')})")

        # 12 Arudha Padas
        lines.append("\n**12 Arudha Padas (Manifested World / Maya):**")
        padas = data.get("arudha_padas", [])
        for ap in padas:
            ex = f" [{ap.get('exception')}]" if ap.get("exception") != "Standard" else ""
            lines.append(f"- **{ap.get('pada')}** ({ap.get('name')}): {ap.get('sign')} (House {ap.get('house_from_lagna')}){ex}")

        # Chara Dasha
        cs = data.get("chara_dasha_summary", {})
        if cs:
            lines.append("\n**Jaimini Chara Dasha Progression:**")
            lines.append(f"- **Progression Order**: {cs.get('order')}")
            lines.append(f"- **Current Mahadasha**: {cs.get('active_md')} (Lord: {cs.get('active_md_lord')}) -> Dates: {cs.get('md_range')}")
            lines.append(f"- **Active Antardasha**: {cs.get('active_ad')} (Lord: {cs.get('active_ad_lord')}) -> Dates: {cs.get('ad_range')}")

        return "\n".join(lines)

    @classmethod
    async def run_three_eyes(
        cls,
        data: Dict[str, Any],
        pillar: str = "comprehensive",
        custom_query: str = "",
        api_key: Optional[str] = None,
    ) -> Dict[str, str]:
        """Runs Eye 1, Eye 2, and Eye 3 concurrently using asyncio.gather."""
        pillar_title = PILLAR_TITLES.get(pillar, PILLAR_TITLES["comprehensive"])

        p_facts = cls.slice_parashari_facts(data)
        kp_facts = cls.slice_kp_facts(data)
        j_facts = cls.slice_jaimini_facts(data)

        p_prompt = build_parashari_prompt(pillar_title, p_facts, custom_query)
        kp_prompt = build_kp_prompt(pillar_title, kp_facts, custom_query)
        j_prompt = build_jaimini_prompt(pillar_title, j_facts, custom_query)

        # Dispatch all three concurrently
        t1 = gemini_service.generate_content(
            system_instruction=EYE_1_PARASHARI_SYSTEM_PROMPT,
            user_prompt=p_prompt,
            api_key=api_key,
            temperature=0.3,
            max_output_tokens=1500,
        )
        t2 = gemini_service.generate_content(
            system_instruction=EYE_2_KP_SYSTEM_PROMPT,
            user_prompt=kp_prompt,
            api_key=api_key,
            temperature=0.3,
            max_output_tokens=1500,
        )
        t3 = gemini_service.generate_content(
            system_instruction=EYE_3_JAIMINI_SYSTEM_PROMPT,
            user_prompt=j_prompt,
            api_key=api_key,
            temperature=0.3,
            max_output_tokens=1500,
        )

        res_p, res_kp, res_j = await asyncio.gather(t1, t2, t3)

        return {
            "parashari": res_p,
            "kp": res_kp,
            "jaimini": res_j,
        }

    @classmethod
    async def stream_synthesis(
        cls,
        data: Dict[str, Any],
        pillar: str = "comprehensive",
        custom_query: str = "",
        api_key: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Orchestrates 3-Eye evaluation and streams the final synthesis over SSE."""
        pillar_title = PILLAR_TITLES.get(pillar, PILLAR_TITLES["comprehensive"])

        # 1. Emit start event
        yield f"event: status\ndata: {json.dumps({'message': 'Awakening the Three Eyes (Parashara, KP, Jaimini)...', 'stage': 'three_eyes'})}\n\n"

        # 2. Run 3 eyes in parallel
        try:
            eyes_verdicts = await cls.run_three_eyes(data, pillar=pillar, custom_query=custom_query, api_key=api_key)
        except Exception as exc:
            logger.error("Three Eyes evaluation error: %s", exc)
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
            return

        # 3. Emit individual eye results so UI cards light up immediately
        yield f"event: eyes_ready\ndata: {json.dumps(eyes_verdicts)}\n\n"
        yield f"event: status\ndata: {json.dumps({'message': 'Three Eyes evaluated. Synthesizing unified reading...', 'stage': 'synthesis'})}\n\n"

        # 4. Prepare Maha-Synthesizer Prompt
        natal_summary = cls.slice_parashari_facts(data)
        synth_prompt = build_synthesizer_prompt(
            pillar_title=pillar_title,
            parashari_verdict=eyes_verdicts["parashari"],
            kp_verdict=eyes_verdicts["kp"],
            jaimini_verdict=eyes_verdicts["jaimini"],
            natal_summary=natal_summary,
            custom_query=custom_query,
        )

        contents = [{"role": "user", "parts": [{"text": synth_prompt}]}]

        # 5. Stream final synthesis tokens
        try:
            async for token in gemini_service.stream_generate_content(
                system_instruction=MAHA_SYNTHESIZER_SYSTEM_PROMPT,
                contents=contents,
                api_key=api_key,
                temperature=0.4,
                max_output_tokens=3500,
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
    ) -> AsyncIterator[str]:
        """Streams conversation replies with ground truth dossier anchored in system_instruction."""
        ai_dossier = data.get("ai_dossier", {})
        dossier_md = ai_dossier.get("markdown_dossier", "")
        if not dossier_md:
            dossier_md = cls.slice_parashari_facts(data)

        system_instruction = build_chat_system_instruction(dossier_md)

        # Convert conversation messages to Gemini format
        contents = []
        for msg in messages:
            role = "model" if msg.get("role") in ["assistant", "model"] else "user"
            contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}],
            })

        if not contents:
            contents.append({"role": "user", "parts": [{"text": "Hello, please review my chart."}]})

        try:
            async for token in gemini_service.stream_generate_content(
                system_instruction=system_instruction,
                contents=contents,
                api_key=api_key,
                temperature=0.5,
                max_output_tokens=2500,
            ):
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

            yield f"event: complete\ndata: {json.dumps({'status': 'finished'})}\n\n"
        except Exception as exc:
            logger.error("Chat streaming error: %s", exc)
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
