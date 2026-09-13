"""Pytest Test Suite for Phase 2 Domain Logic Engines (Parashari, KP, and Jaimini).

Validates:
- BPHS Divisional Charts (D1, D2, D3, D7, D9, D10, D12, D30, D60)
- Recursive Vimshottari Dasha generation with exact calendar end-dates
- KP 1–249 Sub-Lord table generation and Sub/Sub-Sub resolution
- KP 4-Fold Significators Matrix (Levels A, B, C, D)
- Jaimini 7 and 8 Chara Karaka rankings with Rahu degree inversion
- Arudha Padas calculation with BPHS 1st/7th shift exceptions
- Rashi Drishti sign aspect matrix
"""

from datetime import datetime
import pytest
from zoneinfo import ZoneInfo

from core.constants import AyanamshaType, HouseSystemType, NodeType, PlanetEnum
from core.ephemeris import EphemerisEngine
from engines.jaimini import JaiminiEngine, JaiminiKarakaRole
from engines.kp import KPEngine
from engines.parashari import (
    VargaChartEngine,
    VargaType,
    VimshottariDashaEngine,
)
from engines.aspects import AspectsEngine
from engines.ashtakavarga import AshtakavargaEngine
from engines.gochar import GocharEngine
from engines.yogas import YogaDetectorEngine, YogaNature
from schemas.models import BirthInput, GeoLocationModel


@pytest.fixture(scope="module")
def reference_chart():
    """Generates the verified reference birth chart (Jaipur, India: Oct 15, 1995 14:30 IST)."""
    engine = EphemerisEngine()
    birth_input = BirthInput(
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
    return engine.calculate_chart(birth_input)


# =========================================================================
# 1. Parashari Varga Charts Tests
# =========================================================================

class TestParashariVargas:
    def test_d9_navamsha_calculations(self, reference_chart) -> None:
        """Validates Navamsha (D9) calculation for Sun and Ascendant."""
        d9_chart = VargaChartEngine.generate_varga_chart(reference_chart, VargaType.D9)

        # Sun is at 177.73° (Virgo / Kanya 27°43' 57")
        # Virgo is Earthy sign (starts from Capricorn 10).
        # Intra-deg = 27.7325 / 3.333333 = part 8 -> (10 + 8 - 1) % 12 + 1 = 6 (Virgo / Kanya)
        sun_d9 = d9_chart.planets[PlanetEnum.SUN]
        assert sun_d9.sign_name == "Kanya"
        assert sun_d9.sign_id == 6

        # Ascendant is at 289.048° (Capricorn / Makara 19°02' 52")
        # Capricorn is Earthy sign (starts from Capricorn 10).
        # Intra-deg = 19.048 / 3.333333 = part 5 -> (10 + 5 - 1) % 12 + 1 = 3 (Gemini / Mithuna)
        asc_d9 = d9_chart.ascendant
        assert asc_d9.sign_name == "Mithuna"
        assert asc_d9.sign_id == 3

    def test_all_supported_vargas(self, reference_chart) -> None:
        """Ensures all 9 required vargas calculate without errors."""
        vargas = [
            VargaType.D1,
            VargaType.D2,
            VargaType.D3,
            VargaType.D7,
            VargaType.D9,
            VargaType.D10,
            VargaType.D12,
            VargaType.D30,
            VargaType.D60,
        ]
        for v in vargas:
            chart = VargaChartEngine.generate_varga_chart(reference_chart, v)
            assert chart.varga == v
            assert 1 <= chart.ascendant.sign_id <= 12
            assert len(chart.planets) == 12  # 9 Grahas + 3 Outers


# =========================================================================
# 2. Vimshottari Dasha Engine Tests
# =========================================================================

class TestVimshottariDasha:
    def test_birth_dasha_balance(self, reference_chart) -> None:
        """Validates Moon's birth dasha balance calculation."""
        moon_lon = reference_chart.planets[PlanetEnum.MOON].longitude
        birth_dt = reference_chart.utc_datetime

        tree = VimshottariDashaEngine.generate_dasha_tree(birth_dt, moon_lon)

        # Moon is in Ardra (Lord: Rahu, 18 years)
        assert tree.moon_nakshatra_name == "Ardra"
        assert tree.birth_mahadasha_lord == PlanetEnum.RAHU

        # 0.0 < balance < 18.0 years
        assert 0.0 < tree.birth_balance_years < 18.0

        # First Mahadasha should end at birth + balance_years
        first_md = tree.mahadashas[0]
        assert first_md.lord == PlanetEnum.RAHU
        assert first_md.start_date == birth_dt
        assert len(first_md.antardashas) >= 1

        # Second Mahadasha must be Jupiter (16 years)
        second_md = tree.mahadashas[1]
        assert second_md.lord == PlanetEnum.JUPITER
        assert abs(second_md.duration_days - (16 * 365.2425)) < 1.0

    def test_current_dasha_lookup(self, reference_chart) -> None:
        """Validates resolving active MD, AD, PD for a specific date."""
        moon_lon = reference_chart.planets[PlanetEnum.MOON].longitude
        birth_dt = reference_chart.utc_datetime

        tree = VimshottariDashaEngine.generate_dasha_tree(birth_dt, moon_lon)
        target_date = datetime(2026, 8, 25, 0, 0, 0, tzinfo=ZoneInfo("UTC"))

        res = VimshottariDashaEngine.get_current_dasha(tree, target_date)
        assert res is not None
        md, ad, pd = res
        assert md.start_date <= target_date <= md.end_date
        assert ad.start_date <= target_date <= ad.end_date
        assert pd.start_date <= target_date <= pd.end_date


# =========================================================================
# 3. KP System Engine Tests
# =========================================================================

class TestKPEngine:
    def test_kp_249_table_generation(self) -> None:
        """Validates canonical 249-entry table integrity and boundaries."""
        table = KPEngine.get_kp_249_table()
        assert len(table) == 249

        # Row 1 must start at 0.0° (Aries, Ashwini, Ketu star, Ketu sub)
        first = table[0]
        assert first.sub_number == 1
        assert first.sign_id == 1
        assert first.star_lord == PlanetEnum.KETU
        assert first.sub_lord == PlanetEnum.KETU
        assert first.start_longitude == 0.0

        # Row 249 must end at 360.0° (Pisces, Revati, Mercury star, Saturn sub)
        last = table[-1]
        assert last.sub_number == 249
        assert last.sign_id == 12
        assert abs(last.end_longitude - 360.0) < 1e-6

        # Check continuity (no gaps between consecutive subs)
        for i in range(len(table) - 1):
            assert abs(table[i].end_longitude - table[i + 1].start_longitude) < 1e-6

    def test_kp_sub_resolution(self) -> None:
        """Validates resolving a known longitude to 4-tier KP lords."""
        # 177.7325° (Virgo / Kanya, Chitra Nakshatra)
        res = KPEngine.resolve_kp_sub(177.7325)
        assert res.sign_name == "Kanya"
        assert res.sign_lord == PlanetEnum.MERCURY
        assert res.nakshatra_name == "Chitra"
        assert res.star_lord == PlanetEnum.MARS
        assert 1 <= res.sub_number <= 249
        assert res.sub_start_deg <= 177.7325 <= res.sub_end_deg
        assert res.sub_sub_start_deg <= 177.7325 <= res.sub_sub_end_deg

    def test_kp_4fold_significators(self, reference_chart) -> None:
        """Validates 4-Fold Significators Matrix across all 12 houses."""
        matrix = KPEngine.calculate_4fold_significators(reference_chart)
        assert len(matrix.houses) == 12

        # House 1 should have Level D as Capricorn lord (Saturn)
        h1 = matrix.houses[1]
        assert h1.level_d == [PlanetEnum.SATURN]

        # Verify planets significations dictionary structure
        for p in reference_chart.planets.keys():
            assert p in matrix.planets_significations
            assert "A" in matrix.planets_significations[p]
            assert "B" in matrix.planets_significations[p]
            assert "C" in matrix.planets_significations[p]
            assert "D" in matrix.planets_significations[p]


# =========================================================================
# 4. Jaimini Engine Tests
# =========================================================================

class TestJaiminiEngine:
    def test_7_chara_karakas(self, reference_chart) -> None:
        """Validates classical 7 Chara Karaka ranking (AK down to DK)."""
        result = JaiminiEngine.calculate_chara_karakas(reference_chart, scheme=7)
        assert len(result.karakas) == 7

        # Ensure degrees are strictly descending
        degrees = [k.effective_ranking_degree for k in result.karakas]
        for i in range(len(degrees) - 1):
            assert degrees[i] >= degrees[i + 1]

        # In reference chart: Sun is at 27.73° (highest) -> AK
        assert result.by_role["AK"].planet == PlanetEnum.SUN
        assert result.by_role["AK"].role_name == JaiminiKarakaRole.AK

    def test_8_chara_karakas_rahu_inversion(self, reference_chart) -> None:
        """Validates 8 Chara Karaka ranking with Rahu reverse-degree mathematics."""
        result = JaiminiEngine.calculate_chara_karakas(reference_chart, scheme=8)
        assert len(result.karakas) == 8

        # Rahu is at Libra 2°43' -> Intra deg is 2.72° -> Inverted is 30.0 - 2.72 = 27.28°
        rahu_item = result.by_planet[PlanetEnum.RAHU]
        assert abs(rahu_item.effective_ranking_degree - (30.0 - rahu_item.intra_sign_degree)) < 1e-4

        # Degrees must be strictly sorted descending
        degrees = [k.effective_ranking_degree for k in result.karakas]
        for i in range(len(degrees) - 1):
            assert degrees[i] >= degrees[i + 1]

    def test_arudha_padas_with_exceptions(self, reference_chart) -> None:
        """Validates Arudha Padas and 1st/7th shift exceptions."""
        result = JaiminiEngine.calculate_arudha_padas(reference_chart)
        assert len(result.padas) == 12

        # Verify no Arudha Pada falls in the 1st or 7th house from its source house
        for pada in result.padas:
            h = pada.house_number
            seventh = ((h - 1 + 6) % 12) + 1
            assert pada.final_house != h
            assert pada.final_house != seventh

        # AL (Arudha Lagna) and UL (Upapada Lagna) must be defined
        assert result.arudha_lagna.pada_name == "AL (A1)"
        assert result.upapada_lagna.pada_name == "UL (A12)"

    def test_rashi_drishti_aspects(self, reference_chart) -> None:
        """Validates Jaimini Rashi Drishti sign aspect matrix."""
        aspects = JaiminiEngine.calculate_rashi_drishti(reference_chart)

        # Aries (1, Movable) aspects Scorpio (8), Aquarius (11), Leo (5)
        assert aspects.sign_aspects_map[1] == [8, 11, 5]

        # Taurus (2, Fixed) aspects Cancer (4), Libra (7), Capricorn (10)
        assert aspects.sign_aspects_map[2] == [4, 7, 10]

        # Gemini (3, Dual) aspects Virgo (6), Sagittarius (9), Pisces (12)
        assert aspects.sign_aspects_map[3] == [6, 9, 12]


# =========================================================================
# 5. Classical Yogas & Doshas Engine Tests
# =========================================================================

class TestYogaEngine:
    def test_yoga_evaluation_structure(self, reference_chart) -> None:
        """Validates complete evaluation report, counts, and active status."""
        report = YogaDetectorEngine.evaluate(reference_chart)
        assert report.summary.total_yogas > 0
        assert report.summary.auspicious_count > 0
        assert len(report.yogas) == report.summary.total_yogas

    def test_pancha_mahapurusha_malavya(self, reference_chart) -> None:
        """Validates Malavya Mahapurusha detection (Venus in Libra 10th house Kendra)."""
        report = YogaDetectorEngine.evaluate(reference_chart)
        malavya = next((y for y in report.yogas if y.id == "mahapurusha_venus"), None)
        assert malavya is not None
        assert malavya.nature == YogaNature.MAHAPURUSHA
        assert malavya.is_active is True
        assert "Venus" in malavya.planets_involved

    def test_budhaditya_and_amala_yogas(self, reference_chart) -> None:
        """Validates Budhaditya and Amala Yogas in reference chart."""
        report = YogaDetectorEngine.evaluate(reference_chart)
        budhaditya = next((y for y in report.yogas if y.id == "budhaditya_yoga"), None)
        assert budhaditya is not None
        assert "Sun" in budhaditya.planets_involved
        assert "Mercury" in budhaditya.planets_involved

        amala = next((y for y in report.yogas if y.id == "amala_yoga"), None)
        assert amala is not None
        assert amala.nature == YogaNature.RAJA

    def test_kuja_dosha_cancellation_apavada(self, reference_chart) -> None:
        """Validates Kuja Dosha detection with classical cancellation rule applied."""
        report = YogaDetectorEngine.evaluate(reference_chart)
        kuja = next((y for y in report.yogas if y.id == "kuja_dosha"), None)
        assert kuja is not None
        assert kuja.is_cancelled is True
        assert "Cancelled" in kuja.intensity or kuja.intensity == "Cancelled"
        assert kuja.cancellation_reason is not None
        assert "Vrishchika" in kuja.cancellation_reason

    def test_neechabhanga_7_rules_multi_cancellation(self) -> None:
        """Validates 7-rule Neechabhanga Raja Yoga detection on Sun in Libra chart."""
        engine = EphemerisEngine()
        inp = BirthInput(
            year=1995,
            month=10,
            day=24,
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
        chart = engine.calculate_chart(inp)
        report = YogaDetectorEngine.evaluate(chart)
        nb_sun = next((y for y in report.yogas if y.id == "neechabhanga_sun"), None)
        assert nb_sun is not None
        assert "Neechabhanga Raja Yoga" in nb_sun.name
        assert nb_sun.intensity == "Strong"
        assert nb_sun.nature == YogaNature.RAJA
        assert "Venus" in nb_sun.planets_involved
        assert "Dispositor" in nb_sun.description

    def test_shani_sade_sati_card_both_active_and_inactive(self, reference_chart) -> None:
        """Validates that Shani Sade Sati info card is reliably generated for both active and clear charts."""
        # 1. Inactive case (reference chart: Moon in Gemini, Saturn in Aquarius -> 9th from Moon)
        rep = YogaDetectorEngine.evaluate(reference_chart)
        sade = next((y for y in rep.yogas if y.id == "sade_sati"), None)
        assert sade is not None
        assert sade.is_active is False
        assert sade.is_cancelled is True
        assert "Inactive" in sade.intensity
        assert "9th house from natal Moon" in sade.description
        assert sade.cancellation_reason is not None
        assert rep.summary.sade_sati_status == "Inactive"

        # 2. Active 1st phase case (Nov 5 1995: Moon in Pisces, Saturn in Aquarius -> 12th from Moon)
        engine = EphemerisEngine()
        inp_active = BirthInput(
            year=1995,
            month=11,
            day=5,
            hour=12,
            minute=0,
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
        chart_active = engine.calculate_chart(inp_active)
        rep_active = YogaDetectorEngine.evaluate(chart_active)
        sade_active = next((y for y in rep_active.yogas if y.id == "sade_sati"), None)
        assert sade_active is not None
        assert sade_active.is_active is True
        assert sade_active.is_cancelled is False
        assert sade_active.intensity == "Rising (12th)"
        assert "12th house from natal Moon" in sade_active.description
        assert rep_active.summary.sade_sati_status == "Rising (12th)"


# =========================================================================
# 6. Classical Ashtakavarga Engine Tests
# =========================================================================

class TestAshtakavargaEngine:
    def test_sav_337_bindus_invariant(self, reference_chart) -> None:
        """Validates that Sarvashtakavarga (SAV) strictly sums to the classical 337 bindus."""
        report = AshtakavargaEngine.evaluate(reference_chart)
        assert report.summary.total_bindus == 337
        assert sum(sd.total_bindus for sd in report.sarvashtakavarga) == 337
        assert len(report.sarvashtakavarga) == 12

    def test_all_7_planets_bav_totals(self, reference_chart) -> None:
        """Validates individual Bhinnashtakavarga (BAV) classical totals for all 7 planets."""
        report = AshtakavargaEngine.evaluate(reference_chart)
        expected_totals = {
            "Sun": 48,
            "Moon": 49,
            "Mars": 39,
            "Mercury": 54,
            "Jupiter": 56,
            "Venus": 52,
            "Saturn": 39,
        }
        for planet, expected in expected_totals.items():
            assert planet in report.bhinna
            assert report.bhinna[planet].total_raw_bindus == expected
            assert len(report.bhinna[planet].signs) == 12

        # Sum of all 7 planet BAV totals must equal 337
        assert sum(report.bhinna[p].total_raw_bindus for p in expected_totals) == 337

    def test_shodhana_and_shodya_pinda_reductions(self, reference_chart) -> None:
        """Validates Trikona Shodhana, Ekadhipatya Shodhana, and Shodya Pinda calculations."""
        report = AshtakavargaEngine.evaluate(reference_chart)
        for planet, p_rep in report.bhinna.items():
            # Invariant: Reductions can only decrease or maintain bindu totals
            assert p_rep.total_trikona_reduced <= p_rep.total_raw_bindus
            assert p_rep.total_ekadhipatya_reduced <= p_rep.total_trikona_reduced
            # Shodya Pinda
            assert p_rep.rashi_pinda > 0
            assert p_rep.graha_pinda >= 0
            assert p_rep.yoga_pinda == p_rep.rashi_pinda + p_rep.graha_pinda

    def test_lagna_kaksha_calculation(self, reference_chart) -> None:
        """Validates BPHS Chapter 68 Lagna Kaksha subdivision and Lord assignment."""
        report = AshtakavargaEngine.evaluate(reference_chart)
        assert report.lagna_kaksha is not None
        lk = report.lagna_kaksha
        assert lk.lagna_sign_id == 10  # Makara
        assert lk.active_kaksha_number == 6
        assert lk.active_kaksha_lord == "Mercury"
        assert lk.active_kaksha_lord_sanskrit == "Budha"
        assert lk.active_kaksha_range == "18°45' – 22°30'"
        assert len(lk.kakshas) == 8
        assert lk.kakshas[5].is_current is True
        assert lk.kakshas[0].lord == "Saturn"
        assert lk.kakshas[7].lord == "Lagna"
        assert 0.0 <= lk.kaksha_progress_pct <= 100.0

    def test_kaksha_time_rectification_shift(self) -> None:
        """Validates that scrubbing birth time by -5m shifts Lagna into preceding Kaksha."""
        from datetime import datetime, timedelta
        engine = EphemerisEngine()
        base_dt = datetime(1995, 10, 15, 14, 30, 0)
        dt_minus_5m = base_dt - timedelta(minutes=5)

        inp_base = BirthInput(
            year=base_dt.year, month=base_dt.month, day=base_dt.day,
            hour=base_dt.hour, minute=base_dt.minute, second=float(base_dt.second),
            location=GeoLocationModel(latitude=26.9124, longitude=75.7873, city="Jaipur", timezone_str="Asia/Kolkata"),
            ayanamsha=AyanamshaType.LAHIRI, node_type=NodeType.TRUE, house_system=HouseSystemType.PLACIDUS,
        )
        inp_minus_5m = BirthInput(
            year=dt_minus_5m.year, month=dt_minus_5m.month, day=dt_minus_5m.day,
            hour=dt_minus_5m.hour, minute=dt_minus_5m.minute, second=float(dt_minus_5m.second),
            location=GeoLocationModel(latitude=26.9124, longitude=75.7873, city="Jaipur", timezone_str="Asia/Kolkata"),
            ayanamsha=AyanamshaType.LAHIRI, node_type=NodeType.TRUE, house_system=HouseSystemType.PLACIDUS,
        )

        chart_base = engine.calculate_chart(inp_base)
        chart_minus_5m = engine.calculate_chart(inp_minus_5m)

        rep_base = AshtakavargaEngine.evaluate(chart_base)
        rep_minus_5m = AshtakavargaEngine.evaluate(chart_minus_5m)

        assert rep_base.lagna_kaksha.active_kaksha_number == 6
        assert rep_base.lagna_kaksha.active_kaksha_lord == "Mercury"

        # -5 minutes shifts ~1.25° back from 19°02' to ~17°47', entering Kaksha 5 (Venus: 15°00' - 18°45')
        assert rep_minus_5m.lagna_kaksha.active_kaksha_number == 5
        assert rep_minus_5m.lagna_kaksha.active_kaksha_lord == "Venus"
        assert rep_minus_5m.lagna_kaksha.active_kaksha_lord_sanskrit == "Shukra"


# =========================================================================
# 7. Classical Gochar (Planetary Transits) Engine Tests
# =========================================================================

class TestGocharEngine:
    def test_gochar_evaluation(self, reference_chart) -> None:
        """Validates real-time Gochar evaluation for 9 classical Grahas."""
        av_report = AshtakavargaEngine.evaluate(reference_chart)
        gochar_report = GocharEngine.evaluate(reference_chart, av_report)

        assert gochar_report.summary is not None
        s = gochar_report.summary
        assert s.transit_utc != ""
        assert s.transit_date_formatted != ""
        assert s.natal_moon_sign == "Mithuna"
        assert s.natal_lagna_sign == "Makara"
        assert s.benefic_count >= 0
        assert s.challenging_count >= 0
        assert s.benefic_count + s.challenging_count == 9  # All 9 classical Grahas (Sun..Ketu)

        # 9 Transits
        assert len(gochar_report.transits) == 9
        planet_names = [t.planet for t in gochar_report.transits]
        for expected in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
            assert expected in planet_names

        for t in gochar_report.transits:
            assert 1 <= t.sign_id <= 12
            assert 1 <= t.house_from_lagna <= 12
            assert 1 <= t.house_from_moon <= 12
            assert t.sav_bindus > 0
            assert t.kaksha_lord != ""
            assert t.transit_phala != ""
            assert t.glyph != ""

        # Transit chart is populated
        assert gochar_report.transit_chart is not None
        assert len(gochar_report.transit_chart.planets) >= 9

    def test_gochar_deterministic_positions(self, reference_chart) -> None:
        """Validates Gochar calculations for a fixed historic transit date."""
        av_report = AshtakavargaEngine.evaluate(reference_chart)
        fixed_dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        gochar_report = GocharEngine.evaluate(reference_chart, av_report, transit_dt=fixed_dt)

        # On 2024-06-01:
        # Jupiter was in Taurus (Vrishabha, sign 2)
        # Saturn was in Aquarius (Kumbha, sign 11)
        # Rahu was in Pisces (Meena, sign 12)
        transits_by_planet = {t.planet: t for t in gochar_report.transits}

        assert transits_by_planet["Jupiter"].sign_id == 2  # Taurus
        assert transits_by_planet["Jupiter"].sign_sanskrit == "Vrishabha"
        # From natal Moon (Mithuna, sign 3): Taurus is house 12
        assert transits_by_planet["Jupiter"].house_from_moon == 12

        assert transits_by_planet["Saturn"].sign_id == 11  # Aquarius
        assert transits_by_planet["Saturn"].sign_sanskrit == "Kumbha"
        # From natal Moon (sign 3): Aquarius is house 9
        assert transits_by_planet["Saturn"].house_from_moon == 9
        # House 9 Saturn is challenging per Phaladeepika (benefic in 3, 6, 11)
        assert transits_by_planet["Saturn"].is_benefic_from_moon is False


class TestAspectsEngine:
    """Validates Parashari Graha Drishti, Vishesha Drishti, and Bhava aspects."""

    def test_parashari_full_aspects_rules(self, reference_chart) -> None:
        """Validates that Mars (4, 7, 8), Jupiter (5, 7, 9), Saturn (3, 7, 10), Rahu/Ketu (5, 7, 9) and others (7) are cast."""
        aspects_report = AspectsEngine.evaluate(reference_chart)
        planets = aspects_report.planets_aspects

        # 1. Mars special aspects: 4th, 7th, 8th
        mars_casts = planets["Mars"].aspects_cast
        mars_offsets = [c.aspect_offset for c in mars_casts]
        assert mars_offsets == [4, 7, 8]
        assert any(c.is_special for c in mars_casts if c.aspect_offset in (4, 8))

        # 2. Jupiter special aspects: 5th, 7th, 9th
        jupiter_casts = planets["Jupiter"].aspects_cast
        jupiter_offsets = [c.aspect_offset for c in jupiter_casts]
        assert jupiter_offsets == [5, 7, 9]

        # 3. Saturn special aspects: 3rd, 7th, 10th
        saturn_casts = planets["Saturn"].aspects_cast
        saturn_offsets = [c.aspect_offset for c in saturn_casts]
        assert saturn_offsets == [3, 7, 10]

        # 4. Rahu & Ketu special aspects: 5th, 7th, 9th
        rahu_casts = planets["Rahu"].aspects_cast
        rahu_offsets = [c.aspect_offset for c in rahu_casts]
        assert rahu_offsets == [5, 7, 9]

        ketu_casts = planets["Ketu"].aspects_cast
        ketu_offsets = [c.aspect_offset for c in ketu_casts]
        assert ketu_offsets == [5, 7, 9]

        # 5. Sun, Moon, Mercury, Venus: only 7th
        for p in ["Sun", "Moon", "Mercury", "Venus"]:
            casts = planets[p].aspects_cast
            assert [c.aspect_offset for c in casts] == [7]
            assert casts[0].is_special is False

    def test_bhava_aspects_coverage(self, reference_chart) -> None:
        """Validates all 12 Bhavas have aspect evaluations."""
        aspects_report = AspectsEngine.evaluate(reference_chart)
        assert len(aspects_report.bhava_aspects) == 12
        for b in aspects_report.bhava_aspects:
            assert 1 <= b.house_number <= 12
            assert b.lord != ""
            assert b.sign_name != ""
            assert b.net_influence in ("Fortified (Benefic)", "Afflicted (Malefic)", "Mixed Influences", "Neutral")


# =========================================================================
# 9. Classical Planetary Dignity Engine Tests
# =========================================================================

class TestDignityEngine:
    """Validates classical Parashari planetary dignities (Exaltation, Debilitation, Own Sign, Moolatrikona)."""

    def test_all_9_planets_exaltations(self) -> None:
        """Validates that all 9 planets correctly detect their classical exaltation signs."""
        from engines.dignity import DignityEngine, EXALTATION_SIGNS, DEEP_EXALTATION_DEGREES, DignityState
        from core.constants import PlanetEnum

        for planet, ex_sign in EXALTATION_SIGNS.items():
            deep_deg = DEEP_EXALTATION_DEGREES[planet]
            rep = DignityEngine.evaluate_planet_dignity(
                planet=planet,
                sign_id=ex_sign,
                sign_name="TestSign",
                degree_in_sign=deep_deg,
            )
            assert rep.is_exalted is True
            assert rep.is_debilitated is False
            assert rep.dignity == DignityState.EXALTED
            assert rep.dignity_short == "Ex"
            assert "Exalted" in rep.dignity_label
            assert "Deep Exaltation" in rep.dignity_desc or "Exalted in" in rep.dignity_desc

    def test_all_9_planets_debilitations(self) -> None:
        """Validates that all 9 planets correctly detect their classical debilitation signs."""
        from engines.dignity import DignityEngine, DEBILITATION_SIGNS, DEEP_DEBILITATION_DEGREES, DignityState
        from core.constants import PlanetEnum

        for planet, deb_sign in DEBILITATION_SIGNS.items():
            deep_deg = DEEP_DEBILITATION_DEGREES[planet]
            rep = DignityEngine.evaluate_planet_dignity(
                planet=planet,
                sign_id=deb_sign,
                sign_name="TestSign",
                degree_in_sign=deep_deg,
            )
            assert rep.is_debilitated is True
            assert rep.is_exalted is False
            assert rep.dignity == DignityState.DEBILITATED
            assert rep.dignity_short == "Deb"
            assert "Debilitated" in rep.dignity_label

    def test_neechabhanga_integration(self) -> None:
        """Validates that Neechabhanga cancellation is flagged on debilitated planets."""
        from engines.dignity import DignityEngine, DignityState
        from core.constants import PlanetEnum

        # Saturn in Aries (Sign 1) with Neechabhanga
        rep_nb = DignityEngine.evaluate_planet_dignity(
            planet=PlanetEnum.SATURN,
            sign_id=1,
            sign_name="Mesha",
            degree_in_sign=20.0,
            neechabhanga_planets={"Saturn"},
        )
        assert rep_nb.is_debilitated is True
        assert rep_nb.has_neechabhanga is True
        assert "[Cancelled]" in rep_nb.dignity_label
        assert "Neechabhanga" in rep_nb.dignity_desc

        # Saturn in Aries without Neechabhanga
        rep_plain = DignityEngine.evaluate_planet_dignity(
            planet=PlanetEnum.SATURN,
            sign_id=1,
            sign_name="Mesha",
            degree_in_sign=20.0,
            neechabhanga_planets=set(),
        )
        assert rep_plain.is_debilitated is True
        assert rep_plain.has_neechabhanga is False
        assert "[Cancelled]" not in rep_plain.dignity_label

    def test_own_sign_and_moolatrikona(self) -> None:
        """Validates Moolatrikona vs Own Sign distinction."""
        from engines.dignity import DignityEngine, DignityState
        from core.constants import PlanetEnum

        # Sun in Leo 10° is Moolatrikona (0°-20°)
        rep_sun_mt = DignityEngine.evaluate_planet_dignity(
            planet=PlanetEnum.SUN,
            sign_id=5,
            sign_name="Simha",
            degree_in_sign=10.0,
        )
        assert rep_sun_mt.is_moolatrikona is True
        assert rep_sun_mt.dignity == DignityState.MOOLATRIKONA
        assert rep_sun_mt.dignity_short == "MT"

        # Sun in Leo 25° is Own Sign (20°-30°)
        rep_sun_own = DignityEngine.evaluate_planet_dignity(
            planet=PlanetEnum.SUN,
            sign_id=5,
            sign_name="Simha",
            degree_in_sign=25.0,
        )
        assert rep_sun_own.is_own_sign is True
        assert rep_sun_own.dignity == DignityState.OWN_SIGN
        assert rep_sun_own.dignity_short == "Own"

    def test_reference_chart_dignities(self, reference_chart) -> None:
        """Validates dignities of planets in the standard reference chart."""
        from engines.dignity import DignityEngine, DignityState
        from core.constants import PlanetEnum

        mercury_pos = reference_chart.planets[PlanetEnum.MERCURY]
        rep_merc = DignityEngine.evaluate_planet_dignity(
            planet=PlanetEnum.MERCURY,
            sign_id=mercury_pos.sign.id,
            sign_name=mercury_pos.sign.sanskrit_name,
            degree_in_sign=mercury_pos.longitude % 30.0,
        )
        # Mercury in Virgo (Kanya, 6) is Exalted
        assert rep_merc.is_exalted is True
        assert rep_merc.dignity == DignityState.EXALTED
        assert rep_merc.dignity_short == "Ex"

    def test_naisargika_maitri_canonical_rules(self) -> None:
        """Validates canonical BPHS Chapter 3 natural friendships rules."""
        from engines.friendships import FriendshipEngine
        from core.constants import PlanetEnum

        # Sun perspective
        rel, score = FriendshipEngine.get_natural_relationship(PlanetEnum.SUN, PlanetEnum.MOON)
        assert rel == "Friend" and score == 1
        rel, score = FriendshipEngine.get_natural_relationship(PlanetEnum.SUN, PlanetEnum.MERCURY)
        assert rel == "Neutral" and score == 0
        rel, score = FriendshipEngine.get_natural_relationship(PlanetEnum.SUN, PlanetEnum.SATURN)
        assert rel == "Enemy" and score == -1

        # Moon perspective: Moon has NO natural enemies
        for p in [PlanetEnum.MARS, PlanetEnum.JUPITER, PlanetEnum.VENUS, PlanetEnum.SATURN]:
            rel, score = FriendshipEngine.get_natural_relationship(PlanetEnum.MOON, p)
            assert rel == "Neutral" and score == 0
        rel, score = FriendshipEngine.get_natural_relationship(PlanetEnum.MOON, PlanetEnum.MERCURY)
        assert rel == "Friend" and score == 1

        # Asymmetric relationship: Mercury considers Moon enemy, but Moon considers Mercury friend
        rel_merc_to_moon, score_merc = FriendshipEngine.get_natural_relationship(PlanetEnum.MERCURY, PlanetEnum.MOON)
        assert rel_merc_to_moon == "Enemy" and score_merc == -1

    def test_tatkalika_and_compound_maitri(self) -> None:
        """Validates temporal (Tatkalika) and compound 5-fold (Pancha-Dha) rules."""
        from engines.friendships import FriendshipEngine, RelationshipType

        # Temporal friends: houses 2, 3, 4, 10, 11, 12
        for h in [2, 3, 4, 10, 11, 12]:
            rel, score = FriendshipEngine.get_temporal_relationship(h)
            assert rel == "Friend" and score == 1

        # Temporal enemies: houses 1, 5, 6, 7, 8, 9
        for h in [1, 5, 6, 7, 8, 9]:
            rel, score = FriendshipEngine.get_temporal_relationship(h)
            assert rel == "Enemy" and score == -1

        # Compound rules:
        # +1 + 1 = +2 (Great Friend / Adhi Mitra)
        rel_comp, sc = FriendshipEngine.compute_compound(1, 1)
        assert rel_comp == RelationshipType.GREAT_FRIEND and sc == 2

        # 0 + 1 = +1 (Friend / Mitra)
        rel_comp, sc = FriendshipEngine.compute_compound(0, 1)
        assert rel_comp == RelationshipType.FRIEND and sc == 1

        # -1 + 1 = 0 (Neutral / Sama)
        rel_comp, sc = FriendshipEngine.compute_compound(-1, 1)
        assert rel_comp == RelationshipType.NEUTRAL and sc == 0

        # 0 + (-1) = -1 (Enemy / Shatru)
        rel_comp, sc = FriendshipEngine.compute_compound(0, -1)
        assert rel_comp == RelationshipType.ENEMY and sc == -1

        # -1 + (-1) = -2 (Great Enemy / Adhi Shatru)
        rel_comp, sc = FriendshipEngine.compute_compound(-1, -1)
        assert rel_comp == RelationshipType.GREAT_ENEMY and sc == -2

    def test_pancha_dha_maitri_reference_chart(self, reference_chart) -> None:
        """Validates evaluation of full chart planetary friendships on reference chart."""
        from engines.friendships import FriendshipEngine

        report = FriendshipEngine.evaluate(reference_chart)
        assert len(report.profiles) == 9

        sun_profile = report.profiles["Sun"]
        assert sun_profile.planet == "Sun"
        assert len(sun_profile.relationships) == 8
        # Sun is in Virgo with Mercury (dispositor in same sign, offset 1 -> temporal enemy)
        # Natural: Sun to Mercury is Neutral (0). Temporal: -1. Compound: -1 (Shatru)
        assert "Shatru" in sun_profile.dispositor_kshetra

        moon_profile = report.profiles["Moon"]
        assert moon_profile.planet == "Moon"
        # Moon in Gemini (3) with dispositor Mercury in Virgo (6): offset 4 (temporal friend +1)
        # Natural: Moon to Mercury is Friend (+1). Temporal: +1. Compound: +2 (Adhi Mitra)
        assert "Adhi Mitra" in moon_profile.dispositor_kshetra









