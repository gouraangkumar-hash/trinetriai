"""Pytest Test Suite for SVG Visualizers and UI State Pipeline."""

import pytest

from core.constants import AyanamshaType, HouseSystemType, NodeType
from core.ephemeris import EphemerisEngine
from engines.parashari import VargaChartEngine, VargaType
from schemas.models import BirthInput, GeoLocationModel
from ui.state import DashboardState, EngineOrchestrator
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
        assert 'viewBox="0 0 600 600"' in svg
        assert "D1 RASHI CHART" in svg
        assert "Asc:" in svg
        assert "Su " in svg  # Sun badge
        assert "Mo " in svg  # Moon badge
        assert "<polygon points=" in svg  # Central Diamond

    def test_north_indian_varga_svg(self, reference_chart) -> None:
        """Validates rendering a divisional chart (D9 Navamsha) in North Indian style."""
        d9 = VargaChartEngine.generate_varga_chart(reference_chart, VargaType.D9)
        svg_d9 = generate_north_indian_svg(reference_chart, varga_chart=d9, title="D9 Navamsha")
        assert svg_d9.startswith("<svg")
        assert "D9 NAVAMSHA" in svg_d9
        # In D9, Ascendant is Gemini (Mithuna)
        assert "Mith" in svg_d9

    def test_south_indian_svg_structure(self, reference_chart) -> None:
        """Validates South Indian fixed grid SVG generation."""
        svg = generate_south_indian_svg(reference_chart, title="Rashi Chart (D1)")
        assert svg.startswith("<svg")
        assert svg.strip().endswith("</svg>")
        assert 'viewBox="0 0 600 600"' in svg
        assert "Rashi Chart (D1)" in svg
        assert "Meena" in svg
        assert "Mesha" in svg
        assert "Vrishabha" in svg
        assert "ASC" in svg  # Rising sign highlight
        assert "Su " in svg

    def test_dashboard_orchestrator_pipeline(self) -> None:
        """Validates the full UI state orchestrator pipeline."""
        orchestrator = EngineOrchestrator()
        initial_state = DashboardState(
            city_query="Jaipur, India",
            birth_date_str="1995-10-15",
            birth_time_str="14:30:00",
        )
        computed_state = orchestrator.run_pipeline(initial_state)

        assert computed_state.error_message is None
        assert computed_state.chart_data is not None
        assert len(computed_state.varga_charts) >= 9
        assert computed_state.dasha_tree is not None
        assert computed_state.kp_matrix is not None
        assert computed_state.jaimini_7_karakas is not None
        assert computed_state.north_svg.startswith("<svg")
        assert computed_state.south_svg.startswith("<svg")
