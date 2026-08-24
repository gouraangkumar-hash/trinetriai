"""Modern Dark-Mode Interactive UI Dashboard for Unified Vedic, KP & Jaimini Computational Engine."""

from datetime import datetime
from pathlib import Path
import sys
from typing import Optional
from zoneinfo import ZoneInfo

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fasthtml.common import (
    A,
    Button,
    Div,
    Form,
    H1,
    H2,
    H3,
    Header,
    Input,
    Main,
    Nav,
    NotStr,
    Option,
    P,
    Section,
    Select,
    Small,
    Span,
    Table,
    Tbody,
    Td,
    Th,
    Thead,
    Title,
    Tr,
    fast_app,
    serve,
)

from core.constants import AyanamshaType, NodeType, PlanetEnum
from engines.parashari import VargaType
from ui.state import DashboardState, EngineOrchestrator

# FastHTML app initialization with modern dark theme CSS
app, rt = fast_app(
    pico=False,
    hdrs=[
        Title("TrinetriAI — Unified Vedic, KP & Jaimini Computational Engine"),
        NotStr("""
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {
                darkMode: 'class',
                theme: {
                    extend: {
                        colors: {
                            gold: { 400: '#fbbf24', 500: '#f59e0b', 600: '#d97706', 700: '#b45309' },
                            slate: { 850: '#0f172a', 900: '#0b0f19', 950: '#030712' }
                        }
                    }
                }
            }
        </script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
            body { font-family: 'Inter', sans-serif; }
            .font-cinzel { font-family: 'Cinzel', serif; }
            .font-mono { font-family: 'JetBrains Mono', monospace; }
            .gold-border { border-color: rgba(212, 175, 55, 0.3); }
            .gold-glow { box-shadow: 0 0 20px rgba(245, 158, 11, 0.15); }
            .gold-text-glow { text-shadow: 0 0 12px rgba(251, 191, 36, 0.4); }
            /* Custom Scrollbars */
            ::-webkit-scrollbar { width: 6px; height: 6px; }
            ::-webkit-scrollbar-track { background: #0f172a; }
            ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
            ::-webkit-scrollbar-thumb:hover { background: #475569; }
        </style>
        """),
    ],
)

orchestrator = EngineOrchestrator()
current_state = orchestrator.run_pipeline(DashboardState())


# =========================================================================
# UI Component Helpers
# =========================================================================

def render_top_bar(state: DashboardState):
    """Renders the top interactive input bar for birth data and engine settings."""
    ayanamsha_options = [
        Option(
            a.value,
            value=a.value,
            selected=(a == state.ayanamsha),
        )
        for a in [AyanamshaType.LAHIRI, AyanamshaType.KRISHNAMURTI, AyanamshaType.RAMAN, AyanamshaType.YUKTESHWAR]
    ]

    varga_options = [
        Option(
            vt.value + (" (Rashi)" if vt == VargaType.D1 else " (Navamsha)" if vt == VargaType.D9 else ""),
            value=vt.value,
            selected=(vt == state.selected_varga),
        )
        for vt in [VargaType.D1, VargaType.D2, VargaType.D3, VargaType.D7, VargaType.D9, VargaType.D10, VargaType.D12, VargaType.D30, VargaType.D60]
    ]

    return Form(
        hx_post="/calculate",
        hx_target="#dashboard-content",
        hx_swap="innerHTML",
        cls="bg-slate-900 border-b gold-border px-6 py-4 shadow-xl",
    )(
        Div(cls="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4")(
            # Left: Brand Title
            Div(cls="flex items-center gap-3")(
                Div(cls="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-600 to-amber-400 flex items-center justify-center shadow-lg shadow-amber-500/20")(
                    Span(cls="text-slate-950 font-cinzel font-black text-xl")("ॐ")
                ),
                Div(
                    H1(cls="font-cinzel text-xl font-bold text-amber-400 gold-text-glow")("TRINETRI AI"),
                    P(cls="text-xs text-slate-400")("Unified Vedic, KP & Jaimini Computational Engine"),
                ),
            ),

            # Right: Inputs Form
            Div(cls="flex flex-wrap items-center gap-3")(
                # City Input
                Div(cls="flex flex-col")(
                    Small(cls="text-[10px] text-slate-400 font-semibold uppercase tracking-wider mb-1")("City / Location"),
                    Input(
                        type="text",
                        name="city",
                        value=state.city_query,
                        placeholder="e.g. Jaipur, India",
                        cls="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 w-36 focus:outline-none focus:border-amber-400 font-medium",
                    ),
                ),
                # Date Input
                Div(cls="flex flex-col")(
                    Small(cls="text-[10px] text-slate-400 font-semibold uppercase tracking-wider mb-1")("Birth Date"),
                    Input(
                        type="date",
                        name="birth_date",
                        value=state.birth_date_str,
                        cls="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-amber-400 font-mono",
                    ),
                ),
                # Time Input
                Div(cls="flex flex-col")(
                    Small(cls="text-[10px] text-slate-400 font-semibold uppercase tracking-wider mb-1")("Birth Time (Local)"),
                    Input(
                        type="text",
                        name="birth_time",
                        value=state.birth_time_str,
                        placeholder="HH:MM:SS",
                        cls="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 w-24 focus:outline-none focus:border-amber-400 font-mono",
                    ),
                ),
                # Ayanamsha
                Div(cls="flex flex-col")(
                    Small(cls="text-[10px] text-slate-400 font-semibold uppercase tracking-wider mb-1")("Ayanamsha"),
                    Select(
                        name="ayanamsha",
                        cls="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-amber-400 font-medium",
                    )(*ayanamsha_options),
                ),
                # Chart Style Toggle
                Div(cls="flex flex-col")(
                    Small(cls="text-[10px] text-slate-400 font-semibold uppercase tracking-wider mb-1")("Style"),
                    Select(
                        name="chart_style",
                        cls="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-amber-400 font-medium",
                    )(
                        Option("North Diamond", value="north", selected=(state.chart_style == "north")),
                        Option("South Grid", value="south", selected=(state.chart_style == "south")),
                    ),
                ),
                # Varga Selector
                Div(cls="flex flex-col")(
                    Small(cls="text-[10px] text-slate-400 font-semibold uppercase tracking-wider mb-1")("Varga (Divisional)"),
                    Select(
                        name="varga",
                        cls="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-amber-400 font-medium",
                    )(*varga_options),
                ),
                # Submit Action
                Div(cls="flex flex-col justify-end")(
                    Button(
                        type="submit",
                        cls="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-bold text-xs px-4 py-2 rounded-lg transition-all shadow-md shadow-amber-500/20 active:scale-95 cursor-pointer mt-4",
                    )("Recalculate ⚡"),
                ),
            ),
        )
    )


def render_chart_panel(state: DashboardState):
    """Panel 1: SVG Visualizer with Metadata Badges."""
    chart = state.chart_data
    if not chart:
        return Div("No chart data available.")

    asc_sign = chart.angles.ascendant_sign
    asc_nak = chart.angles.ascendant_nakshatra

    return Div(cls="bg-slate-900 border gold-border rounded-2xl p-5 shadow-2xl flex flex-col items-center")(
        # Metadata Header Bar
        Div(cls="w-full flex flex-wrap items-center justify-between border-b border-slate-800 pb-3 mb-4 gap-2")(
            Div(cls="flex items-center gap-2")(
                Span(cls="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"),
                Span(cls="text-xs font-semibold text-slate-300")("Local Sidereal Engine"),
                Span(cls="text-xs px-2 py-0.5 rounded bg-slate-800 text-amber-400 border border-slate-700 font-mono")(
                    f"JD {chart.julian_day_ut:.4f}"
                ),
            ),
            Div(cls="flex items-center gap-2 text-xs text-slate-400")(
                Span(f"Ayanamsha: {chart.ayanamsha_name.value}"),
                Span(cls="text-amber-400 font-mono font-medium")(chart.ayanamsha_dms.formatted),
            ),
        ),

        # SVG Container
        Div(cls="w-full max-w-[540px] aspect-square relative my-2")(
            NotStr(state.active_svg)
        ),

        # Bottom Angles Pill Bar
        Div(cls="w-full grid grid-cols-2 gap-3 mt-4 pt-3 border-t border-slate-800 text-xs")(
            Div(cls="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700/60 flex items-center justify-between")(
                Span(cls="text-slate-400 font-medium")("Lagna (Ascendant)"),
                Span(cls="text-sky-400 font-semibold font-mono")(
                    f"{asc_sign.sanskrit_name} {asc_sign.dms.formatted} ({asc_nak.sanskrit_name} P{asc_nak.pada})"
                ),
            ),
            Div(cls="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700/60 flex items-center justify-between")(
                Span(cls="text-slate-400 font-medium")("Midheaven (MC)"),
                Span(cls="text-amber-400 font-semibold font-mono")(
                    f"{chart.angles.mc_sign.sanskrit_name} {chart.angles.mc_dms.formatted}"
                ),
            ),
        ),
    )


def render_kp_matrix_panel(state: DashboardState):
    """Panel 2: KP Cuspal & Planetary Matrix Table with 4-Fold Significators."""
    chart = state.chart_data
    if not chart or not state.kp_matrix:
        return Div("KP data unavailable.")

    kp_matrix = state.kp_matrix

    # Planet Rows
    planet_rows = []
    for p_name, p_pos in chart.planets.items():
        if p_name in (PlanetEnum.URANUS, PlanetEnum.NEPTUNE, PlanetEnum.PLUTO):
            continue

        kp_res = state.kp_planet_subs.get(p_name)
        signif = kp_matrix.planets_significations.get(p_name, {})

        a_str = ",".join(map(str, signif.get("A", []))) or "-"
        b_str = ",".join(map(str, signif.get("B", []))) or "-"
        c_str = ",".join(map(str, signif.get("C", []))) or "-"
        d_str = ",".join(map(str, signif.get("D", []))) or "-"

        status = ""
        if p_pos.is_retrograde:
            status += " (R)"
        if p_pos.is_combust:
            status += " (C)"

        planet_rows.append(
            Tr(cls="border-b border-slate-800/60 hover:bg-slate-800/50 transition-colors text-xs font-mono")(
                Td(cls="py-2 px-2.5 font-sans font-semibold text-slate-200 flex items-center gap-1.5")(
                    p_name.value,
                    Span(cls="text-[10px] text-rose-400 font-bold")(status) if status else "",
                ),
                Td(cls="py-2 px-2.5 text-slate-300")(f"{p_pos.sign.sanskrit_name[:4]} {p_pos.sign.dms.formatted}"),
                Td(cls="py-2 px-2.5 text-amber-400")(kp_res.star_lord.value if kp_res else "-"),
                Td(cls="py-2 px-2.5 text-sky-400 font-bold")(kp_res.sub_lord.value if kp_res else "-"),
                Td(cls="py-2 px-2.5 text-slate-400")(kp_res.sub_sub_lord.value if kp_res else "-"),
                Td(cls="py-2 px-2.5 text-emerald-400 font-semibold font-sans")(a_str),
                Td(cls="py-2 px-2.5 text-cyan-400 font-semibold font-sans")(b_str),
                Td(cls="py-2 px-2.5 text-amber-300 font-semibold font-sans")(c_str),
                Td(cls="py-2 px-2.5 text-purple-400 font-semibold font-sans")(d_str),
            )
        )

    # Cusps Rows
    cusp_rows = []
    for cusp in chart.placidus_houses:
        h_num = cusp.house_number
        kp_res = state.kp_cusp_subs.get(h_num)
        h_signifs = kp_matrix.houses.get(h_num)

        a_planets = ",".join(p.value[:2] for p in h_signifs.level_a) if h_signifs and h_signifs.level_a else "-"
        b_planets = ",".join(p.value[:2] for p in h_signifs.level_b) if h_signifs and h_signifs.level_b else "-"
        c_planets = ",".join(p.value[:2] for p in h_signifs.level_c) if h_signifs and h_signifs.level_c else "-"
        d_planets = ",".join(p.value[:2] for p in h_signifs.level_d) if h_signifs and h_signifs.level_d else "-"

        cusp_rows.append(
            Tr(cls="border-b border-slate-800/60 hover:bg-slate-800/50 transition-colors text-xs font-mono")(
                Td(cls="py-2 px-2.5 font-sans font-semibold text-slate-200")(f"House {h_num:02d}"),
                Td(cls="py-2 px-2.5 text-slate-300")(f"{cusp.sign.sanskrit_name[:4]} {cusp.dms.formatted}"),
                Td(cls="py-2 px-2.5 text-amber-400")(kp_res.star_lord.value if kp_res else "-"),
                Td(cls="py-2 px-2.5 text-sky-400 font-bold")(kp_res.sub_lord.value if kp_res else "-"),
                Td(cls="py-2 px-2.5 text-slate-400")(kp_res.sub_sub_lord.value if kp_res else "-"),
                Td(cls="py-2 px-2.5 text-emerald-400 font-semibold font-sans")(a_planets),
                Td(cls="py-2 px-2.5 text-cyan-400 font-semibold font-sans")(b_planets),
                Td(cls="py-2 px-2.5 text-amber-300 font-semibold font-sans")(c_planets),
                Td(cls="py-2 px-2.5 text-purple-400 font-semibold font-sans")(d_planets),
            )
        )

    return Div(cls="bg-slate-900 border gold-border rounded-2xl p-5 shadow-2xl flex flex-col")(
        Div(cls="flex items-center justify-between border-b border-slate-800 pb-3 mb-3")(
            H2(cls="font-cinzel text-base font-bold text-amber-400 flex items-center gap-2")(
                Span("✧"), "KP Planetary & Cuspal Matrix"
            ),
            Span(cls="text-[11px] text-slate-400 font-mono")("4-Fold ABCD Significators"),
        ),
        # Planetary Matrix Table
        Div(cls="overflow-x-auto mb-4 border border-slate-800 rounded-xl")(
            Table(cls="w-full text-left border-collapse")(
                Thead(cls="bg-slate-800 text-[11px] text-slate-300 font-semibold uppercase tracking-wider")(
                    Tr(
                        Th(cls="py-2 px-2.5")("Planet"),
                        Th(cls="py-2 px-2.5")("Longitude"),
                        Th(cls="py-2 px-2.5")("Star"),
                        Th(cls="py-2 px-2.5")("Sub"),
                        Th(cls="py-2 px-2.5")("Sub-Sub"),
                        Th(cls="py-2 px-2.5 text-emerald-400")("A"),
                        Th(cls="py-2 px-2.5 text-cyan-400")("B"),
                        Th(cls="py-2 px-2.5 text-amber-300")("C"),
                        Th(cls="py-2 px-2.5 text-purple-400")("D"),
                    )
                ),
                Tbody(*planet_rows),
            )
        ),
        # Cuspal Matrix Table
        Div(cls="overflow-x-auto border border-slate-800 rounded-xl")(
            Table(cls="w-full text-left border-collapse")(
                Thead(cls="bg-slate-800 text-[11px] text-slate-300 font-semibold uppercase tracking-wider")(
                    Tr(
                        Th(cls="py-2 px-2.5")("Cusp"),
                        Th(cls="py-2 px-2.5")("Degree"),
                        Th(cls="py-2 px-2.5")("Star"),
                        Th(cls="py-2 px-2.5")("Sub"),
                        Th(cls="py-2 px-2.5")("Sub-Sub"),
                        Th(cls="py-2 px-2.5 text-emerald-400")("Sig A"),
                        Th(cls="py-2 px-2.5 text-cyan-400")("Sig B"),
                        Th(cls="py-2 px-2.5 text-amber-300")("Sig C"),
                        Th(cls="py-2 px-2.5 text-purple-400")("Sig D"),
                    )
                ),
                Tbody(*cusp_rows),
            )
        ),
    )


def render_jaimini_drawer_panel(state: DashboardState):
    """Panel 3: Jaimini Drawer with 7 & 8 Chara Karakas, Arudha Padas, and Sign Aspects."""
    k7 = state.jaimini_7_karakas
    k8 = state.jaimini_8_karakas
    arudhas = state.arudha_padas

    if not k7 or not k8 or not arudhas:
        return Div("Jaimini data unavailable.")

    # 7-Karaka badges
    karaka_badges_7 = []
    for item in k7.karakas:
        karaka_badges_7.append(
            Div(cls="bg-slate-800/80 border border-slate-700/60 rounded-xl p-2.5 flex items-center justify-between")(
                Div(cls="flex items-center gap-2")(
                    Span(cls="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono")(
                        item.role_code
                    ),
                    Span(cls="text-xs text-slate-300 font-medium")(item.role_name.value),
                ),
                Div(cls="text-right")(
                    Span(cls="text-xs font-semibold text-slate-100")(item.planet.value),
                    Small(cls="block text-[10px] text-slate-400 font-mono")(f"{item.sign_name[:4]} {item.dms.formatted}"),
                ),
            )
        )

    # Arudha Pada badges
    arudha_badges = []
    for item in arudhas.padas:
        is_special = item.house_number in (1, 12)
        bg_cls = "bg-amber-500/10 border-amber-500/40 text-amber-300" if is_special else "bg-slate-800 border-slate-700/60 text-slate-300"
        arudha_badges.append(
            Div(cls=f"p-2 rounded-xl border flex flex-col justify-between {bg_cls}")(
                Div(cls="flex items-center justify-between mb-1")(
                    Span(cls="font-bold text-xs font-mono")(item.pada_name),
                    Span(cls="text-[10px] text-slate-400")(f"H{item.final_house}"),
                ),
                Div(cls="text-[11px] font-medium text-slate-200")(item.sign_name),
                Small(cls="text-[9px] text-slate-500")("Shift 10" if item.is_exception_applied else "Standard"),
            )
        )

    return Div(cls="bg-slate-900 border gold-border rounded-2xl p-5 shadow-2xl flex flex-col")(
        # Header
        Div(cls="flex items-center justify-between border-b border-slate-800 pb-3 mb-4")(
            H2(cls="font-cinzel text-base font-bold text-amber-400 flex items-center gap-2")(
                Span("✧"), "Jaimini Sutras Computational Core"
            ),
            Span(cls="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-sky-400 border border-slate-700 font-mono")(
                "Chara Karakas & Arudhas"
            ),
        ),

        # Section 1: 7-Karaka Scheme
        Small(cls="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5")(
            Span(cls="w-1.5 h-1.5 rounded-full bg-amber-400"),
            "Chara Karakas (7-Karaka System)",
        ),
        Div(cls="grid grid-cols-1 md:grid-cols-2 gap-2.5 mb-5")(
            *karaka_badges_7
        ),

        # Section 2: Arudha Padas
        Small(cls="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5")(
            Span(cls="w-1.5 h-1.5 rounded-full bg-sky-400"),
            "Arudha Padas (A1 to A12 with 1st/7th Shift Exceptions)",
        ),
        Div(cls="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2")(
            *arudha_badges
        ),
    )


def render_dasha_accordion_panel(state: DashboardState):
    """Panel 4: Hierarchical Vimshottari Dasha Tree Accordion."""
    tree = state.dasha_tree
    if not tree:
        return Div("Dasha data unavailable.")

    now_utc = datetime.now(ZoneInfo("UTC"))
    active_triplet = state.active_dasha_triplet

    # Render Mahadashas list
    md_items = []
    for md in tree.mahadashas:
        is_active_md = (md.start_date <= now_utc <= md.end_date)
        md_border = "border-amber-400/80 bg-slate-800/90 shadow-md shadow-amber-500/10" if is_active_md else "border-slate-800 bg-slate-800/40"

        # Antardashas within MD
        ad_rows = []
        for ad in md.antardashas:
            is_active_ad = (ad.start_date <= now_utc <= ad.end_date)
            ad_border = "border-sky-400/80 bg-slate-900 text-sky-300 font-semibold" if is_active_ad else "border-slate-800/60 text-slate-300"

            ad_rows.append(
                Div(cls=f"p-2 rounded-lg border text-xs flex items-center justify-between mb-1.5 {ad_border}")(
                    Span(cls="flex items-center gap-2")(
                        Span(cls="w-2 h-2 rounded-full " + ("bg-sky-400 animate-ping" if is_active_ad else "bg-slate-600")),
                        f"AD: {ad.lord.value}",
                    ),
                    Span(cls="font-mono text-[11px] text-slate-400")(
                        f"{ad.start_date.strftime('%b %Y')} → {ad.end_date.strftime('%b %Y')}"
                    ),
                )
            )

        md_items.append(
            Div(cls=f"p-3.5 rounded-xl border mb-3 transition-all {md_border}")(
                Div(cls="flex items-center justify-between mb-2.5")(
                    Div(cls="flex items-center gap-2")(
                        Span(cls="font-bold text-sm text-slate-100")(f"MD: {md.lord.value}"),
                        Span(cls="text-xs px-2 py-0.5 rounded font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30")(
                            "ACTIVE NOW"
                        ) if is_active_md else "",
                    ),
                    Span(cls="text-xs text-slate-400 font-mono")(
                        f"{md.start_date.strftime('%Y-%m-%d')} → {md.end_date.strftime('%Y-%m-%d')}"
                    ),
                ),
                # Nested ADs
                Div(cls="pl-3 border-l-2 border-slate-700/60 pt-1")(
                    *ad_rows
                ),
            )
        )

    active_summary = ""
    if active_triplet:
        amd, aad, apd = active_triplet
        active_summary = Div(cls="bg-gradient-to-r from-amber-950/40 to-slate-900 border border-amber-500/40 rounded-xl p-3.5 mb-4 shadow-lg")(
            Small(cls="text-[10px] text-amber-400 font-bold uppercase tracking-wider block mb-1")("Currently Running Dasha Period"),
            Div(cls="flex items-center gap-3 text-sm font-semibold text-slate-100")(
                Span(cls="text-amber-400")(f"MD: {amd.lord.value}"),
                Span("→"),
                Span(cls="text-sky-400")(f"AD: {aad.lord.value}"),
                Span("→"),
                Span(cls="text-emerald-400")(f"PD: {apd.lord.value}"),
            ),
            Small(cls="text-xs text-slate-400 font-mono block mt-1")(
                f"PD Ends: {apd.end_date.strftime('%Y-%m-%d')}"
            ),
        )

    return Div(cls="bg-slate-900 border gold-border rounded-2xl p-5 shadow-2xl flex flex-col")(
        Div(cls="flex items-center justify-between border-b border-slate-800 pb-3 mb-4")(
            H2(cls="font-cinzel text-base font-bold text-amber-400 flex items-center gap-2")(
                Span("✧"), "120-Year Vimshottari Dasha Hierarchy"
            ),
            Span(cls="text-xs text-slate-400 font-mono")(
                f"Birth Balance: {tree.birth_balance_years:.2f} yrs ({tree.birth_mahadasha_lord.value})"
            ),
        ),
        active_summary,
        Div(cls="max-h-[500px] overflow-y-auto pr-1")(
            *md_items
        ),
    )


def render_dashboard_content(state: DashboardState):
    """Renders the 4-panel grid layout."""
    if state.error_message:
        return Div(cls="p-6 bg-rose-950/50 border border-rose-500 rounded-2xl text-rose-300")(
            H3(cls="font-bold text-lg mb-2")("Calculation Error"),
            P(state.error_message),
        )

    return Div(cls="max-w-7xl mx-auto px-6 py-6")(
        # 2x2 Responsive Grid
        Div(cls="grid grid-cols-1 lg:grid-cols-2 gap-6")(
            # Panel 1: SVG Chart Visualizer
            render_chart_panel(state),
            # Panel 2: KP Cuspal & Planetary Matrix
            render_kp_matrix_panel(state),
            # Panel 3: Jaimini Drawer
            render_jaimini_drawer_panel(state),
            # Panel 4: Vimshottari Dasha Accordion
            render_dasha_accordion_panel(state),
        )
    )


# =========================================================================
# FastHTML Route Handlers
# =========================================================================

@rt("/")
def get():
    """Main dashboard page handler."""
    return Main(cls="min-h-screen bg-slate-950 text-slate-100 flex flex-col")(
        # Top Bar
        render_top_bar(current_state),
        # Dynamic Content Container
        Div(id="dashboard-content", cls="flex-1")(
            render_dashboard_content(current_state)
        ),
        # Footer
        Div(cls="border-t border-slate-900 bg-slate-950/80 py-4 text-center text-xs text-slate-500 font-mono")(
            "TrinetriAI Astrology Engine — Swiss Ephemeris C-Bindings • FastHTML • 100% Local Math"
        ),
    )


@rt("/calculate")
def post(
    city: str = "Jaipur, India",
    birth_date: str = "1995-10-15",
    birth_time: str = "14:30:00",
    ayanamsha: str = "Lahiri",
    chart_style: str = "north",
    varga: str = "D1",
):
    """HTMX endpoint for live recalculation."""
    global current_state

    # Update input parameters in state
    current_state.city_query = city
    current_state.birth_date_str = birth_date
    current_state.birth_time_str = birth_time
    current_state.ayanamsha = AyanamshaType(ayanamsha)
    current_state.chart_style = chart_style
    current_state.selected_varga = VargaType(varga)

    # Re-run pipeline
    current_state = orchestrator.run_pipeline(current_state)

    # Return updated dashboard content fragment
    return render_dashboard_content(current_state)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5001)
