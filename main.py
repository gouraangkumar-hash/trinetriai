"""Astrology Engine Demonstration Script: Unified Vedic, KP & Jaimini Computational Engine."""

from datetime import datetime
import sys
from zoneinfo import ZoneInfo

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.constants import AyanamshaType, HouseSystemType, NodeType, PlanetEnum
from core.ephemeris import EphemerisEngine
from engines.jaimini import JaiminiEngine
from engines.kp import KPEngine
from engines.parashari import VargaChartEngine, VargaType, VimshottariDashaEngine
from schemas.models import BirthInput, GeoLocationModel


def main() -> None:
    print("=" * 80)
    print("Unified Vedic, KP & Jaimini Computational Engine (Phase 1 & Phase 2)")
    print("=" * 80)

    engine = EphemerisEngine()

    # Reference Birth: Jaipur, India (Oct 15, 1995 14:30:00 IST)
    birth = BirthInput(
        year=1995,
        month=10,
        day=15,
        hour=14,
        minute=30,
        second=0.0,
        location=GeoLocationModel(
            latitude=26.9124,
            longitude=75.7873,
            city="Jaipur",
            country="India",
            timezone_str="Asia/Kolkata",
        ),
        ayanamsha=AyanamshaType.LAHIRI,
        node_type=NodeType.TRUE,
        house_system=HouseSystemType.PLACIDUS,
    )

    chart = engine.calculate_chart(birth)

    print(f"\n[1] ASTRONOMICAL CORE")
    print(f"  Birth (Local) : {birth.year}-{birth.month:02d}-{birth.day:02d} {birth.hour:02d}:{birth.minute:02d}:{birth.second:02.0f} ({birth.location.city})")
    print(f"  Birth (UTC)   : {chart.utc_datetime.isoformat()}")
    print(f"  Julian Day    : {chart.julian_day_ut:.6f} UT")
    print(f"  Ayanamsha     : {chart.ayanamsha_name.value} {chart.ayanamsha_dms.formatted} ({chart.ayanamsha_value:.4f}°)")
    print(f"  Ascendant     : {chart.angles.ascendant_sign.sanskrit_name} ({chart.angles.ascendant_dms.formatted}) - {chart.angles.ascendant_nakshatra.sanskrit_name} (Pada {chart.angles.ascendant_nakshatra.pada})")
    print(f"  Midheaven     : {chart.angles.mc_sign.sanskrit_name} ({chart.angles.mc_dms.formatted})")

    # =========================================================================
    # Parashari Varga Charts
    # =========================================================================
    print(f"\n[2] PARASHARI DIVISIONAL CHARTS (D1 & D9 Navamsha)")
    d9_chart = VargaChartEngine.generate_varga_chart(chart, VargaType.D9)
    print(f"  Ascendant D9  : {d9_chart.ascendant.sign_name} ({d9_chart.ascendant.dms.formatted})")
    print("-" * 80)
    print(f"{'Planet':<10} | {'D1 Rashi':<22} | {'Nakshatra (Pada)':<22} | {'D9 Navamsha':<18}")
    print("-" * 80)
    for p_name, p_pos in chart.planets.items():
        d1_str = f"{p_pos.sign.sanskrit_name} ({p_pos.sign.dms.formatted})"
        nak_str = f"{p_pos.nakshatra.sanskrit_name} (Pada {p_pos.nakshatra.pada})"
        d9_str = f"{d9_chart.planets[p_name].sign_name} ({d9_chart.planets[p_name].dms.formatted})"
        print(f"{p_name.value:<10} | {d1_str:<22} | {nak_str:<22} | {d9_str:<18}")
    print("-" * 80)

    # =========================================================================
    # Vimshottari Dasha
    # =========================================================================
    print(f"\n[3] VIMSHOTTARI DASHA TIMELINE")
    moon_lon = chart.planets[PlanetEnum.MOON].longitude
    dasha_tree = VimshottariDashaEngine.generate_dasha_tree(chart.utc_datetime, moon_lon)
    print(f"  Birth Moon Nakshatra : {dasha_tree.moon_nakshatra_name} (Lord: {dasha_tree.birth_mahadasha_lord.value})")
    print(f"  Balance of Dasha     : {dasha_tree.birth_balance_years:.2f} Years ({dasha_tree.birth_balance_fraction*100:.1f}%)")

    now_utc = datetime.now(ZoneInfo("UTC"))
    active_dasha = VimshottariDashaEngine.get_current_dasha(dasha_tree, now_utc)
    if active_dasha:
        md, ad, pd = active_dasha
        print(f"  Current Period ({now_utc.strftime('%Y-%m-%d')}) : MD {md.lord.value} -> AD {ad.lord.value} -> PD {pd.lord.value}")
        print(f"    - Mahadasha     : {md.lord.value} ({md.start_date.strftime('%Y-%m-%d')} to {md.end_date.strftime('%Y-%m-%d')})")
        print(f"    - Antardasha    : {ad.lord.value} ({ad.start_date.strftime('%Y-%m-%d')} to {ad.end_date.strftime('%Y-%m-%d')})")
        print(f"    - Pratyantardasha: {pd.lord.value} ({pd.start_date.strftime('%Y-%m-%d')} to {pd.end_date.strftime('%Y-%m-%d')})")

    # =========================================================================
    # KP System
    # =========================================================================
    print(f"\n[4] KRISHNAMURTI PADDHATI (KP) 4-TIER SUB-LORDS")
    print("-" * 80)
    print(f"{'Planet':<10} | {'Longitude':<16} | {'Sign Lord':<10} | {'Star Lord':<10} | {'Sub Lord':<10} | {'Sub-Sub':<10}")
    print("-" * 80)
    for p_name, p_pos in chart.planets.items():
        kp_res = KPEngine.resolve_kp_sub(p_pos.longitude)
        print(f"{p_name.value:<10} | {p_pos.dms.formatted:<16} | {kp_res.sign_lord.value:<10} | {kp_res.star_lord.value:<10} | {kp_res.sub_lord.value:<10} | {kp_res.sub_sub_lord.value:<10}")
    print("-" * 80)

    # =========================================================================
    # Jaimini System
    # =========================================================================
    print(f"\n[5] JAIMINI CHARA KARAKAS (7 & 8 Karaka Schemes)")
    karakas_7 = JaiminiEngine.calculate_chara_karakas(chart, scheme=7)
    karakas_8 = JaiminiEngine.calculate_chara_karakas(chart, scheme=8)

    print("  7-Karaka Scheme:")
    for k in karakas_7.karakas:
        print(f"    - {k.role_code:<4} ({k.role_name.value:<14}): {k.planet.value:<8} in {k.sign_name} ({k.dms.formatted})")

    print("\n  8-Karaka Scheme (Rahu included with inverted degrees):")
    for k in karakas_8.karakas:
        print(f"    - {k.role_code:<4} ({k.role_name.value:<14}): {k.planet.value:<8} [Rank Deg: {k.effective_ranking_degree:.2f}°]")

    print(f"\n[6] JAIMINI ARUDHA PADAS (with 1st/7th Shift Exceptions)")
    arudhas = JaiminiEngine.calculate_arudha_padas(chart)
    print(f"  Arudha Lagna (AL / A1)  : House {arudhas.arudha_lagna.final_house} ({arudhas.arudha_lagna.sign_name}) [Exception: {arudhas.arudha_lagna.is_exception_applied}]")
    print(f"  Upapada Lagna (UL / A12): House {arudhas.upapada_lagna.final_house} ({arudhas.upapada_lagna.sign_name}) [Exception: {arudhas.upapada_lagna.is_exception_applied}]")
    print("=" * 80)


if __name__ == "__main__":
    main()
