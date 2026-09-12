"""Pytest Test Suite for SVG Visualizers and UI State Pipeline."""

import pytest

from core.constants import AyanamshaType, HouseSystemType, NodeType
from core.ephemeris import EphemerisEngine
from engines.ashtakavarga import AshtakavargaEngine
from engines.parashari import VargaChartEngine, VargaType
from schemas.models import BirthInput, GeoLocationModel
from visualizers.ashtakavarga_svg import generate_ashtakavarga_svg
from visualizers.north_indian_svg import generate_north_indian_svg
from visualizers.south_indian_svg import generate_south_indian_svg


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


class TestVisualizers:
    def test_north_indian_svg_structure(self, reference_chart) -> None:
        """Validates North Indian diamond SVG generation."""
        svg = generate_north_indian_svg(reference_chart, title="D1 Rashi Chart")
        assert svg.startswith("<svg")
        assert svg.strip().endswith("</svg>")
        assert 'viewBox="0 0 800 800"' in svg
        assert "D1 RASHI CHART" in svg
        assert "Asc:" in svg
        assert "Su " in svg  # Sun badge
        assert "Mo " in svg  # Moon badge
        assert "As " in svg  # Ascendant badge
        assert "LAGNA 10 • 19°02'" in svg  # House 1 Lagna badge with exact intra-sign degree
        assert "<polygon points=" in svg  # Central Diamond

    def test_north_indian_varga_svg(self, reference_chart) -> None:
        """Validates rendering a divisional chart (D9 Navamsha) in North Indian style."""
        d9 = VargaChartEngine.generate_varga_chart(reference_chart, VargaType.D9)
        svg_d9 = generate_north_indian_svg(reference_chart, varga_chart=d9, title="D9 Navamsha")
        assert svg_d9.startswith("<svg")
        assert "D9 NAVAMSHA" in svg_d9
        # In D9, Ascendant is Gemini (Mithuna)
        assert "Mith" in svg_d9
        assert "As " in svg_d9

    def test_south_indian_svg_structure(self, reference_chart) -> None:
        """Validates South Indian fixed grid SVG generation."""
        svg = generate_south_indian_svg(reference_chart, title="Rashi Chart (D1)")
        assert svg.startswith("<svg")
        assert svg.strip().endswith("</svg>")
        assert 'viewBox="0 0 800 800"' in svg
        assert "RASHI CHART (D1)" in svg.upper()
        assert "Meena" in svg
        assert "Mesha" in svg
        assert "Vrishabha" in svg
        assert "ASC" in svg  # Rising sign highlight
        assert "LAGNA 19°02'" in svg  # South Indian Lagna indicator badge
        assert "As " in svg  # Ascendant row in rising sign
        assert "Su " in svg

    def test_dashboard_orchestrator_pipeline(self, reference_chart) -> None:
        """Validates the full SVG generation pipeline across chart styles and themes."""
        # North Indian Light & Dark
        svg_north_light = generate_north_indian_svg(reference_chart, title="D1 Rashi", theme_mode="light")
        assert svg_north_light.startswith("<svg")
        assert "</svg>" in svg_north_light

        svg_north_dark = generate_north_indian_svg(reference_chart, title="D1 Rashi", theme_mode="dark")
        assert svg_north_dark.startswith("<svg")
        assert "</svg>" in svg_north_dark

        # South Indian Light & Dark
        svg_south_light = generate_south_indian_svg(reference_chart, title="D1 Rashi", theme_mode="light")
        assert svg_south_light.startswith("<svg")
        assert "</svg>" in svg_south_light

        svg_south_dark = generate_south_indian_svg(reference_chart, title="D1 Rashi", theme_mode="dark")
        assert svg_south_dark.startswith("<svg")
        assert "</svg>" in svg_south_dark

    def test_ashtakavarga_svg_north_and_south(self, reference_chart) -> None:
        """Validates generation of Sarvashtakavarga (SAV) visual charts."""
        av_report = AshtakavargaEngine.evaluate(reference_chart)

        # North Indian Light
        svg_north = generate_ashtakavarga_svg(reference_chart, av_report, chart_style="north", theme_mode="light")
        assert svg_north.startswith("<svg")
        assert "</svg>" in svg_north
        assert "SARVASHTAKAVARGA" in svg_north
        assert "337" in svg_north
        assert "LAGNA" in svg_north

        # North Indian Dark
        svg_north_dark = generate_ashtakavarga_svg(reference_chart, av_report, chart_style="north", theme_mode="dark")
        assert svg_north_dark.startswith("<svg")
        assert "</svg>" in svg_north_dark

        # South Indian Light
        svg_south = generate_ashtakavarga_svg(reference_chart, av_report, chart_style="south", theme_mode="light")
        assert svg_south.startswith("<svg")
        assert "</svg>" in svg_south
        assert "SARVASHTAKAVARGA" in svg_south
        assert "337" in svg_south
        assert "LAGNA" in svg_south

        # South Indian Dark & English Sign Names
        svg_south_dark = generate_ashtakavarga_svg(reference_chart, av_report, chart_style="south", sign_mode="english", theme_mode="dark")
        assert svg_south_dark.startswith("<svg")
        assert "</svg>" in svg_south_dark
        assert "Pisces" in svg_south_dark
