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
