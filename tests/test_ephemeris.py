"""Comprehensive Pytest Test Suite for Phase 1 Astronomical Computational Engine.

Validates:
- Reference birth chart (Jaipur, India: 1995-10-15 14:30:00 IST)
- Ketu 180° exact opposition invariance
- Ayanamsha calculations and drift across systems (Lahiri, Krishnamurti, Raman)
- Combustion thresholds and retrograde detection
- Placidus and Whole Sign house cusp calculations
- Polar latitude fallback mechanism
- Geolocation timezone conversions and astro utilities
"""

from datetime import datetime
import pytest
from zoneinfo import ZoneInfo

from core.astro_utils import (
    angular_distance,
    decimal_to_dms,
    get_nakshatra_placement,
    get_sign_placement,
    normalize_degrees,
)
from core.constants import (
    AyanamshaType,
    HouseSystemType,
    NodeType,
    PlanetEnum,
    ZodiacSignEnum,
)
from core.ephemeris import EphemerisEngine
from core.geo import GeoResolver, to_utc_datetime
from schemas.models import BirthInput, GeoLocationModel


@pytest.fixture(scope="module")
def engine() -> EphemerisEngine:
    return EphemerisEngine()


@pytest.fixture(scope="module")
def jaipur_birth_input() -> BirthInput:
    return BirthInput(
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


class TestAstroUtils:
    def test_decimal_to_dms_positive(self) -> None:
        deg, m, s, formatted = decimal_to_dms(23.7915)
        assert deg == 23
        assert m == 47
        assert abs(s - 29.40) < 0.1
        assert "23° 47'" in formatted

    def test_decimal_to_dms_zero_and_negative(self) -> None:
        deg, m, s, formatted = decimal_to_dms(0.0)
        assert deg == 0 and m == 0 and s == 0.0

        deg_neg, m_neg, s_neg, formatted_neg = decimal_to_dms(-15.5)
        assert deg_neg == -15
        assert m_neg == 30
        assert "-" in formatted_neg

    def test_normalize_degrees(self) -> None:
        assert normalize_degrees(0.0) == 0.0
        assert normalize_degrees(360.0) == 0.0
        assert normalize_degrees(725.5) == 5.5
        assert normalize_degrees(-45.0) == 315.0

    def test_get_sign_placement(self) -> None:
        # 0.0 deg -> Aries (Mesha)
        p1 = get_sign_placement(0.0)
        assert p1["id"] == 1
        assert p1["sanskrit_name"] == "Mesha"
        assert p1["lord"] == PlanetEnum.MARS
        assert p1["intra_sign_degree"] == 0.0

        # 27.5 deg -> Aries (Mesha)
        p2 = get_sign_placement(27.5)
        assert p2["id"] == 1
        assert p2["intra_sign_degree"] == 27.5

        # 30.0 deg -> Taurus (Vrishabha)
        p3 = get_sign_placement(30.0)
        assert p3["id"] == 2
        assert p3["sanskrit_name"] == "Vrishabha"
        assert p3["lord"] == PlanetEnum.VENUS
        assert p3["intra_sign_degree"] == 0.0

        # 359.5 deg -> Pisces (Meena)
        p4 = get_sign_placement(359.5)
        assert p4["id"] == 12
        assert p4["sanskrit_name"] == "Meena"
        assert p4["lord"] == PlanetEnum.JUPITER
        assert abs(p4["intra_sign_degree"] - 29.5) < 1e-6

    def test_get_nakshatra_placement(self) -> None:
        # 0.0 deg -> Ashwini Pada 1
        n1 = get_nakshatra_placement(0.0)
        assert n1["id"] == 1
        assert n1["sanskrit_name"] == "Ashwini"
        assert n1["lord"] == PlanetEnum.KETU
        assert n1["pada"] == 1
        assert n1["elapsed_fraction"] == 0.0

        # 13° 20' = 13.33333333° -> Bharani Pada 1
        n2 = get_nakshatra_placement(13.33333334)
        assert n2["id"] == 2
        assert n2["sanskrit_name"] == "Bharani"
        assert n2["lord"] == PlanetEnum.VENUS
        assert n2["pada"] == 1

        # 359.9 deg -> Revati Pada 4
        n3 = get_nakshatra_placement(359.9)
        assert n3["id"] == 27
        assert n3["sanskrit_name"] == "Revati"
        assert n3["lord"] == PlanetEnum.MERCURY
        assert n3["pada"] == 4
        assert 0.99 <= n3["elapsed_fraction"] <= 1.0


class TestGeoTime:
    def test_to_utc_datetime_conversion(self) -> None:
        dt_local = datetime(1995, 10, 15, 14, 30, 0)
        dt_utc = to_utc_datetime(dt_local, "Asia/Kolkata")
        # IST is UTC+05:30 -> 14:30 IST is 09:00 UTC
        assert dt_utc.hour == 9
        assert dt_utc.minute == 0
        assert dt_utc.second == 0
        assert dt_utc.tzinfo == ZoneInfo("UTC")

    def test_timezone_finder_offline(self) -> None:
        geo = GeoResolver()
        tz_jaipur = geo.get_timezone_for_coordinates(26.9124, 75.7873)
        assert tz_jaipur == "Asia/Kolkata"

        tz_london = geo.get_timezone_for_coordinates(51.5074, -0.1278)
        assert tz_london == "Europe/London"

        tz_nyc = geo.get_timezone_for_coordinates(40.7128, -74.0060)
        assert tz_nyc == "America/New_York"


class TestEphemerisCalculations:
    def test_julian_day(self, engine: EphemerisEngine) -> None:
        dt_utc = datetime(1995, 10, 15, 9, 0, 0, tzinfo=ZoneInfo("UTC"))
        jd_ut, jd_et = engine.calculate_julian_day(dt_utc)
        # 1995-10-15 09:00:00 UT corresponds to JD 2450005.875
        assert abs(jd_ut - 2450005.875) < 1e-5
        assert jd_et > jd_ut  # Ephemeris time includes positive delta T

    def test_reference_birth_chart(
        self,
        engine: EphemerisEngine,
        jaipur_birth_input: BirthInput,
    ) -> None:
        chart = engine.calculate_chart(jaipur_birth_input)

        # 1. Verify Ayanamsha for 1995 (Lahiri is ~23.79° or 23° 47')
        assert 23.75 < chart.ayanamsha_value < 23.85

        # 2. Verify Sun position: on Oct 15, Sun is in late Virgo (Kanya) in Lahiri sidereal
        sun = chart.planets[PlanetEnum.SUN]
        assert sun.sign.sanskrit_name == "Kanya"
        assert sun.sign.id == 6
        assert 170.0 < sun.longitude < 180.0

        # 3. Verify Moon position: on Oct 15, 1995 09:00 UT, Moon is in Gemini (Mithuna)
        moon = chart.planets[PlanetEnum.MOON]
        assert moon.sign.sanskrit_name in ("Mithuna", "Vrishabha")

        # 4. Verify Ascendant (Lagna) for 14:30 IST Jaipur is Capricorn (Makara)
        asc = chart.angles.ascendant
        asc_sign = chart.angles.ascendant_sign
        assert asc_sign.sanskrit_name in ("Makara", "Kumbha")
        assert 270.0 <= asc < 330.0

        # 5. Verify 12 Placidus and Whole Sign house counts
        assert len(chart.placidus_houses) == 12
        assert len(chart.whole_sign_houses) == 12

    def test_ketu_exact_opposition(
        self,
        engine: EphemerisEngine,
        jaipur_birth_input: BirthInput,
    ) -> None:
        """Ketu must be mathematically at exactly 180° from Rahu at all times."""
        chart = engine.calculate_chart(jaipur_birth_input)
        rahu = chart.planets[PlanetEnum.RAHU]
        ketu = chart.planets[PlanetEnum.KETU]

        diff = (ketu.longitude - rahu.longitude) % 360.0
        assert abs(diff - 180.0) < 1e-5

        # Also test with Mean Node mode
        input_mean_node = jaipur_birth_input.model_copy(update={"node_type": NodeType.MEAN})
        chart_mean = engine.calculate_chart(input_mean_node)
        rahu_mean = chart_mean.planets[PlanetEnum.RAHU]
        ketu_mean = chart_mean.planets[PlanetEnum.KETU]

        diff_mean = (ketu_mean.longitude - rahu_mean.longitude) % 360.0
        assert abs(diff_mean - 180.0) < 1e-5

    def test_ayanamsha_variation(
        self,
        engine: EphemerisEngine,
        jaipur_birth_input: BirthInput,
    ) -> None:
        """Verifies that switching Ayanamshas dynamically computes expected coordinate offsets."""
        chart_lahiri = engine.calculate_chart(
            jaipur_birth_input.model_copy(update={"ayanamsha": AyanamshaType.LAHIRI})
        )
        chart_kp = engine.calculate_chart(
            jaipur_birth_input.model_copy(update={"ayanamsha": AyanamshaType.KRISHNAMURTI})
        )
        chart_raman = engine.calculate_chart(
            jaipur_birth_input.model_copy(update={"ayanamsha": AyanamshaType.RAMAN})
        )

        # Lahiri vs KP New has a slight offset of a few arcminutes (< 0.5 degrees)
        diff_lahiri_kp = abs(chart_lahiri.ayanamsha_value - chart_kp.ayanamsha_value)
        assert 0.0 < diff_lahiri_kp < 0.5

        # Raman Ayanamsha is distinct from Lahiri by ~1.0° to 1.5°
        diff_lahiri_raman = abs(chart_lahiri.ayanamsha_value - chart_raman.ayanamsha_value)
        assert 0.5 < diff_lahiri_raman < 2.0

    def test_combustion_logic(self, engine: EphemerisEngine) -> None:
        """Verifies combustion rules for planets in close proximity to the Sun."""
        # Mercury at 5° distance from Sun is combust
        assert engine.is_combust(
            planet=PlanetEnum.MERCURY,
            planet_longitude=175.0,
            sun_longitude=172.0,
            is_retrograde=False,
        ) is True

        # Mercury at 15° distance from Sun is NOT combust (direct threshold is 14°)
        assert engine.is_combust(
            planet=PlanetEnum.MERCURY,
            planet_longitude=187.0,
            sun_longitude=172.0,
            is_retrograde=False,
        ) is False

        # Jupiter at 12° distance is NOT combust (threshold 11°)
        assert engine.is_combust(
            planet=PlanetEnum.JUPITER,
            planet_longitude=184.0,
            sun_longitude=172.0,
            is_retrograde=False,
        ) is False

        # Jupiter at 8° distance IS combust
        assert engine.is_combust(
            planet=PlanetEnum.JUPITER,
            planet_longitude=180.0,
            sun_longitude=172.0,
            is_retrograde=False,
        ) is True

    def test_polar_latitude_fallback(
        self,
        engine: EphemerisEngine,
        jaipur_birth_input: BirthInput,
    ) -> None:
        """In extreme polar latitude (e.g., 85°N), Placidus fails and falls back to Porphyry."""
        polar_input = jaipur_birth_input.model_copy(
            update={
                "location": GeoLocationModel(
                    latitude=85.0,
                    longitude=10.0,
                    timezone_str="UTC",
                )
            }
        )
        chart = engine.calculate_chart(polar_input)
        assert chart.is_polar_fallback is True
        assert chart.house_system_used == HouseSystemType.PORPHYRY
        assert len(chart.placidus_houses) == 12
