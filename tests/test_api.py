"""Integration Tests for FastAPI Backend API Endpoints."""

import pytest
from starlette.testclient import TestClient

from engines.trinetri_orchestrator import TrinetriOrchestrator
from main import app

client = TestClient(app)


def test_calculate_endpoint_default():
    """Test POST /api/calculate with default parameters."""
    payload = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Jaipur, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
        "time_offset_seconds": 0,
        "ayanamsha": "Lahiri",
        "node_type": "True",
        "chart_style": "north",
        "sign_mode": "sanskrit",
        "theme_mode": "light",
        "selected_varga": "D1",
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "summary" in data
    assert "ascendant" in data["summary"]
    assert "moon" in data["summary"]
    assert "sun" in data["summary"]
    assert "mc" in data["summary"]
    assert "chart_svg" in data
    assert "<svg" in data["chart_svg"]
    assert len(data["planets_table"]) >= 10
    asc_row = data["planets_table"][0]
    assert asc_row["planet"] == "Ascendant (Lagna)"
    assert asc_row["degree"] == '19° 02\' 52.49"'
    assert asc_row["sign"] == "Makara"
    assert asc_row["star_lord"] != ""
    assert asc_row["sub_lord"] != ""
    assert "planet_details" in data
    # Verify Sun is Vargottama in reference chart (Kanya in D1 and D9)
    sun_detail = data["planet_details"]["Sun"]
    assert sun_detail["is_vargottama"] is True
    assert "Vargottama" in sun_detail["vargottama_status"]
    assert sun_detail["d9_sign"] == "Kanya"
    assert sun_detail["d10_sign"] == "Kumbha"
    asc_detail = data["planet_details"]["Ascendant (Lagna)"]
    assert asc_detail["d10_sign"] == "Meena"

    # Verify Mercury is Exalted in reference chart (Virgo / Kanya)
    merc_detail = data["planet_details"]["Mercury"]
    assert merc_detail["is_exalted"] is True
    assert merc_detail["is_debilitated"] is False
    assert merc_detail["dignity"] == "Exalted"
    assert "Exalted" in merc_detail["dignity_label"]
    assert merc_detail["dignity_short"] == "Ex"

    assert len(data["varga_table"]) >= 10  # Ascendant + 9 planets
    assert len(data["cusps_table"]) == 12
    assert len(data["chara_karakas_7"]) == 7
    assert len(data["chara_karakas_8"]) == 8
    assert len(data["arudha_padas"]) == 12
    assert len(data["mahadashas"]) == 9
    assert "dasha_summary" in data
    assert "current_pratyantardashas" in data["dasha_summary"]
    assert len(data["dasha_summary"]["current_pratyantardashas"]) == 9
    assert any(pd["is_active"] for pd in data["dasha_summary"]["current_pratyantardashas"])
    first_md = data["mahadashas"][0]
    assert len(first_md["antardashas"]) > 0
    assert "pratyantardashas" in first_md["antardashas"][0]
    assert len(first_md["antardashas"][0]["pratyantardashas"]) > 0
    assert "yogas_summary" in data
    assert "yogas_list" in data
    assert data["yogas_summary"]["total_yogas"] > 0
    assert "ashtakavarga" in data
    assert data["ashtakavarga"]["summary"]["total_bindus"] == 337
    assert "aspects" in data
    assert "planets_aspects" in data["aspects"]
    assert "bhava_aspects" in data["aspects"]
    mars_row = next(p for p in data["planets_table"] if p["planet"] == "Mars")
    assert len(mars_row["drishti_badges"]) == 3
    assert any(b["label"] == "H2 (4th)" for b in mars_row["drishti_badges"])
    assert len(data["ashtakavarga"]["sarvashtakavarga"]) == 12
    assert "Jupiter" in data["ashtakavarga"]["bhinna"]
    assert "lagna_kaksha" in data["ashtakavarga"]
    assert data["ashtakavarga"]["lagna_kaksha"]["active_kaksha_lord"] == "Mercury"
    assert data["ashtakavarga"]["lagna_kaksha"]["active_kaksha_number"] == 6
    assert len(data["ashtakavarga"]["lagna_kaksha"]["kakshas"]) == 8
    assert "sav_chart_svg" in data
    assert "<svg" in data["sav_chart_svg"]
    assert "SARVASHTAKAVARGA" in data["sav_chart_svg"]

    # Verify Jaimini Chara Dasha in response
    assert "chara_dasha_summary" in data
    assert "chara_dasha_periods" in data
    assert "Reverse (Apasavya)" in data["chara_dasha_summary"]["order"]
    assert len(data["chara_dasha_periods"]) == 24
    assert len(data["chara_dasha_periods"][0]["antardashas"]) == 12

    # Verify Lagna box has clean "LAGNA 10" with degrees removed (as "As" already displays degrees)
    assert "LAGNA 10" in data["chart_svg"]
    assert "LAGNA 10 • 19°" not in data["chart_svg"]


def test_calculate_endpoint_gochar_toggle():
    """Test POST /api/calculate with show_gochar=True generates Gochar report and overlay."""
    payload = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Jaipur, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
        "show_gochar": True,
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["show_gochar"] is True
    assert "gochar" in data
    assert "summary" in data["gochar"]
    assert len(data["gochar"]["transits"]) == 9
    assert data["gochar"]["summary"]["benefic_count"] + data["gochar"]["summary"]["challenging_count"] == 9

    # Chart SVG must contain the active Gochar overlay badge and transit planet indicators
    svg = data["chart_svg"]
    assert "GOCHAR ON" in svg
    assert "(T)" in svg





def test_calculate_endpoint_south_indian_dark_mode():
    """Test POST /api/calculate with South Indian style and dark mode."""
    payload = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Jaipur, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
        "time_offset_seconds": 60,
        "ayanamsha": "Lahiri",
        "node_type": "True",
        "chart_style": "south",
        "sign_mode": "english",
        "theme_mode": "dark",
        "selected_varga": "D9",
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["chart_style"] == "south"
    assert data["theme_mode"] == "dark"
    assert "<svg" in data["chart_svg"]
    assert "sav_chart_svg" in data
    assert "<svg" in data["sav_chart_svg"]
    assert "SARVASHTAKAVARGA" in data["sav_chart_svg"]


def test_vargas_endpoint():
    """Test POST /api/vargas for harmonic switching."""
    payload = {
        "varga": "D10",
        "chart_params": {
            "year": 1995,
            "month": 10,
            "day": 15,
            "hour": 14,
            "minute": 30,
            "second": 0.0,
            "city": "Jaipur, India",
            "latitude": 26.9124,
            "longitude": 75.7873,
            "timezone_str": "Asia/Kolkata",
            "time_offset_seconds": 0,
            "ayanamsha": "Lahiri",
            "node_type": "True",
            "chart_style": "north",
            "sign_mode": "sanskrit",
            "theme_mode": "light",
            "selected_varga": "D10",
        },
    }
    response = client.post("/api/vargas", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["varga"] == "D10"
    assert "<svg" in data["chart_svg"]
    assert len(data["varga_table"]) >= 10


def test_ai_dossier_endpoint():
    """Test POST /api/ai/dossier for ground-truth LLM prompt dossier generation."""
    payload = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Jaipur, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
    }
    response = client.post("/api/ai/dossier", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "ai_dossier" in data
    dossier = data["ai_dossier"]
    assert "TRINETRIAI VEDIC ASTROLOGICAL DOSSIER" in dossier["markdown_dossier"]
    assert "system_prompt_recommendation" in dossier
    assert "structured_payload" in dossier


def test_serve_index_and_static():
    """Test GET / returns HTML and static files exist."""
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "TRINETRI AI" in response.text
    assert "app.js" in response.text

    # Test static files cache headers
    static_res = client.get("/static/js/app.js?v=2.5.0")
    assert static_res.status_code == 200
    assert "no-cache" in static_res.headers.get("cache-control", "")


def test_favicon_endpoint():
    """Test GET /favicon.ico returns the website logo."""
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert "image/png" in response.headers.get("content-type", "")
    assert "max-age=" in response.headers.get("cache-control", "")



def test_geocode_endpoint():
    """Test GET /api/geocode for location lookup across multiple tiers."""
    # 1. Primary Indian city
    response = client.get("/api/geocode?query=Jaipur")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "latitude" in data
    assert "longitude" in data
    assert "Asia/Kolkata" in data["timezone_str"]
    assert data["city"] == "Jaipur"

    # 2. Sacred Vedic city (Ujjain)
    res_uj = client.get("/api/geocode?query=Ujjain")
    assert res_uj.status_code == 200
    d_uj = res_uj.json()
    assert d_uj["city"] == "Ujjain"
    assert "Asia/Kolkata" in d_uj["timezone_str"]

    # 3. Global metro (New York)
    res_ny = client.get("/api/geocode?query=New York")
    assert res_ny.status_code == 200
    d_ny = res_ny.json()
    assert "America/New_York" in d_ny["timezone_str"]

    # 4. Direct coordinate input
    res_coord = client.get("/api/geocode?query=26.9124,%2075.7873")
    assert res_coord.status_code == 200
    d_coord = res_coord.json()
    assert abs(d_coord["latitude"] - 26.9124) < 1e-3
    assert abs(d_coord["longitude"] - 75.7873) < 1e-3
    assert d_coord["timezone_str"] == "Asia/Kolkata"

    # 5. Invalid gibberish returns 400 with descriptive detail
    res_err = client.get("/api/geocode?query=qwertyuiopasdfghjklzxcvbnm99999")
    assert res_err.status_code == 400
    assert "Location lookup failed" in res_err.json()["detail"]


def test_frontend_markup_and_scripts():
    """Test index.html, style.css, and app.js contain expected elements and rules."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "Madhya Lagna (MC)" in html
    assert "overview-hero-layout" in html
    assert "overview-chart-col" in html
    assert "overview-angles-col" in html
    assert "select-birth-day" in html
    assert "select-birth-month" in html
    assert "select-birth-year" in html
    assert "select-birth-hour" in html
    assert "select-birth-minute" in html
    assert "select-birth-second" in html

    # Check Landing View and Quick Birth Form markup
    assert "landing-view" in html
    assert "landing-hero" in html
    assert "hero-badge" in html
    assert "quick-birth-form" in html
    assert "select-quick-day" in html
    assert "select-quick-month" in html
    assert "select-quick-year" in html
    assert "select-quick-hour" in html
    assert "select-quick-minute" in html
    assert "select-quick-second" in html
    assert "btn-hero-primary" in html
    assert "btn-hero-secondary" in html
    assert "bento-features-grid" in html
    assert "bento-card" in html
    assert "landing-methodology" in html
    assert "methodology-grid" in html
    assert "studio-view" in html
    assert "nav-view-toggle-btn" in html
    assert "brand-home-btn" in html

    # Check anti-caching headers on root response
    assert response.headers.get("cache-control") == "no-cache, no-store, must-revalidate"

    # Check cache-busting query strings on static assets
    assert "/static/css/style.css?v=2.5.0" in html
    assert "/static/js/app.js?v=2.5.0" in html

    # Check clickable overview dasha strip to jump to dasha tab
    assert "overview-dasha-strip" in html
    assert "data-tab=\\'dasha\\'" in html
    assert "current-pd-card" not in html
    assert "dasha-cards-container" in html

    # Check Ashtakavarga subtitle, Kaksha card and 5m scrubber controls
    assert "sav-chart-subtitle" in html
    assert "av-kaksha-card" in html
    assert "scrub-minus-5m" in html
    # Check Gochar controls, hidden state by default, and intelligence card
    assert "gochar-toggle-btn" in html
    assert "gochar-card" in html
    assert 'id="gochar-card" class="card gochar-card" style="display: none;' in html
    assert "gochar-table" in html
    assert "col-phala" in html

    # Check favicon and brand logo
    assert "favicon.png" in html
    assert "brand-logo" in html

    # Check Aspects and Visual Rays markup
    assert "Drishti Cast" in html
    assert "Planetary Positions & Graha Drishti" in html
    assert "bhava-aspects-card" in html
    assert "clear-rays-btn" in html
    assert "drawer-aspects-section" in html

    # Check Planetary Dignity markup in drawer
    assert "box-dignity" in html
    assert "drawer-dignity" in html
    assert "drawer-dignity-badge" in html

    css_res = client.get("/static/css/style.css")
    assert css_res.status_code == 200
    css = css_res.text
    assert ".landing-view" in css
    assert ".landing-hero" in css
    assert ".hero-form-container" in css
    assert ".quick-form-grid" in css
    assert ".bento-features-grid" in css
    assert ".bento-card" in css
    assert ".methodology-grid" in css
    assert ".primary-action-pill" in css
    assert ".overview-hero-layout" in css
    assert ".brand-logo" in css
    assert ".aspect-pill" in css
    assert ".aspect-ray-path" in css
    assert ".planet-name-link" in css
    assert ".bhava-card" in css
    assert ".ad-dates-cell" in css
    assert "min-width: 0" in css
    assert ".pd-nested-table" in css
    assert "pd-panel-row" in css
    assert ".kaksha-grid" in css
    assert ".kaksha-cell" in css
    assert ".gochar-pill" in css
    assert ".gochar-card" in css
    assert ".gochar-badge-benefic" in css
    assert ".col-phala" in css
    assert "min-width: 320px" in css
    assert ".dignity-badge" in css
    assert ".dignity-ex" in css
    assert ".dignity-deb" in css
    assert ".dignity-v" in css

    js_res = client.get("/static/js/app.js")
    assert js_res.status_code == 200
    js = js_res.text
    assert "populateDateTimeSelects" in js
    assert "syncQuickFormWithState" in js
    assert "geocodeLocationQuick" in js
    assert "showLandingView" in js
    assert "showStudioView" in js
    assert "loadSampleChartAndEnterStudio" in js
    assert "initDateTimeDropdowns" in js
    assert "syncModalWithState" in js
    assert "select-birth-year" in js
    assert "drawer-vargottama" in js
    assert "p.is_vargottama" in js
    assert "p.is_exalted" in js
    assert "p.is_debilitated" in js
    assert "dignityBadges" in js
    assert "dignity-ex" in js
    assert "dignity-deb" in js
    assert "dignity-v" in js
    assert "togglePratyantardashaRow" in js
    assert "openAiDossierModal" in js
    assert "copyAiDossier" in js
    assert "downloadAiDossier" in js
    assert "getFuncBadgeClass" in js

    # Check AI Dossier & Functional markup
    assert "btn-ai-dossier" in html
    assert "ai-dossier-modal" in html
    assert "drawer-functional-strength-section" in html
    assert ".func-badge" in css
    assert ".strength-meter-wrap" in css
    assert ".ai-dossier-container" in css
    assert "window.togglePratyantardashaRow" in js
    assert "window.toggleMahadashaCard" in js
    assert "togglePlanetAspectRays" in js
    assert "clearAspectRays" in js
    assert "renderBhavaAspectsWorkspace" in js
    assert "scrub-minus-5m" in js
    assert "scrub-plus-5m" in js
    assert "updateGocharButtonStates" in js
    assert "renderGocharWorkspace" in js
    assert "col-phala" in js

    # Check Jaimini Chara Dasha markup and scripts
    assert "chara-dasha-table" in html
    assert "chara-dasha-tbody" in html
    assert "chara-dasha-order-badge" in html
    assert ".chara-dasha-table" in css
    assert ".chara-ad-nested-row" in css
    assert "toggleCharaAntardashaRow" in js
    assert "window.toggleCharaAntardashaRow" in js

    # Check Trinetri Multi-Agent AI Reading & Chat Drawer markup and scripts
    assert "tab-ai-consult" in html
    assert "ai-pillars-grid" in html
    assert "ai-confluence-card" in html
    assert "trinetri-floating-chat-btn" in html
    assert "trinetri-chat-drawer" in html
    assert "api-key-modal" not in html
    assert ".ai-consult-header-card" in css
    assert ".floating-chat-btn" in css
    assert ".trinetri-chat-drawer" in css
    assert "triggerAiSynthesis" in js
    assert "sendChatMessage" in js
    assert "toggleChatDrawer" in js



def test_calculate_endpoint_target_date():
    """Test POST /api/calculate with a historic target_date parameter."""
    payload = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Jaipur, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
        "selected_varga": "D1",
        "target_date": "2020-01-01T00:00:00Z",
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # Dasha summary should resolve for 2020
    dasha_summary = data["dasha_summary"]
    assert dasha_summary["md"] != "-"
    # Jaimini Chara Dasha should have an active MD for 2020
    chara_summary = data["chara_dasha_summary"]
    assert chara_summary["active_md"] != "-"


def test_vargas_endpoint_vargottama_restricted_to_d9():
    """Test POST /api/vargas to ensure Vargottama is strictly restricted to D9 Navamsha."""
    base_params = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Jaipur, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
        "selected_varga": "D10",
    }

    # Request D10 (Dasamsha)
    payload_d10 = {
        "varga": "D10",
        "chart_params": base_params,
    }
    resp_d10 = client.post("/api/vargas", json=payload_d10)
    assert resp_d10.status_code == 200
    data_d10 = resp_d10.json()
    # No row in D10 should have is_vargottama=True
    for row in data_d10["varga_table"]:
        assert row["is_vargottama"] is False
        assert "[V]" not in row["dignity_short"]

    # Request D9 (Navamsha)
    base_params["selected_varga"] = "D9"
    payload_d9 = {
        "varga": "D9",
        "chart_params": base_params,
    }
    resp_d9 = client.post("/api/vargas", json=payload_d9)
    assert resp_d9.status_code == 200
    data_d9 = resp_d9.json()
    # In reference chart, Sun is Vargottama in D9 (Virgo in both D1 and D9)
    sun_row = next(r for r in data_d9["varga_table"] if r["planet"] == "Sun")
    assert sun_row["is_vargottama"] is True
    assert "[V]" in sun_row["dignity_short"]


def test_ai_config_endpoint():
    """Test GET /api/ai/config returns configuration info."""
    response = client.get("/api/ai/config")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "has_server_key" in data
    assert data["default_model"] == "gemini-3.5-flash-lite"
    assert data["fallback_model"] == "gemini-3.8-flash"
    assert "preferred_models" in data
    assert "gemini-3.5-flash-lite" in data["preferred_models"]
    assert "gemini-3.8-flash" in data["preferred_models"]
    assert len(data["preferred_models"]) == 2
    assert "available_models" in data


def test_orchestrator_fact_slicers():
    """Test TrinetriOrchestrator domain fact slicing for the Three Eyes."""
    from engines.trinetri_orchestrator import TrinetriOrchestrator

    payload = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Jaipur, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
    }
    resp = client.post("/api/calculate", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Eye 1: Parashari slicing
    p_facts = TrinetriOrchestrator.slice_parashari_facts(data)
    assert "Lagna (Ascendant)" in p_facts
    assert "D10 Dashamsha" in p_facts
    assert "Vedic Yogas Summary" in p_facts
    assert "Vimshottari" in p_facts

    # Eye 2: KP slicing
    kp_facts = TrinetriOrchestrator.slice_kp_facts(data)
    assert "Placidus House Cusps" in kp_facts
    assert "Sub-Lord (CSL)" in kp_facts
    assert "Significator Levels" in kp_facts

    # Eye 3: Jaimini slicing
    j_facts = TrinetriOrchestrator.slice_jaimini_facts(data)
    assert "Chara Karakas" in j_facts
    assert "Karakamsha (D9)" in j_facts
    assert "D10 Dashamsha" in j_facts
    assert "Arudha Padas" in j_facts
    assert "Chara Dasha" in j_facts

    # Ground-truth matrix methods
    houses_matrix = TrinetriOrchestrator.build_houses_matrix(data)
    assert "12 Bhavas (Houses) Ground-Truth" in houses_matrix
    assert "H1" in houses_matrix and "H12" in houses_matrix

    dasha_timeline = TrinetriOrchestrator.build_dasha_timeline(data)
    assert "Vimshottari Dasha Chronology" in dasha_timeline

    transits_summary = TrinetriOrchestrator.build_transits_summary(data)
    assert "Real-Time Live Transits in the Sky" in transits_summary
    assert "Saturn" in transits_summary

    aspects_summary = TrinetriOrchestrator.build_aspects_summary(data)
    assert "Verified Planetary Aspects" in aspects_summary

    full_matrix = TrinetriOrchestrator.build_full_ground_truth_matrix(data)
    assert "Natal Baseline & Functional Roles" in full_matrix
    assert "12 Bhavas (Houses) Ground-Truth" in full_matrix
    assert "Natal Planetary Placements, Dignities & Strengths" in full_matrix
    assert "KP Cuspal Sub-Lords (CSL) Table" in full_matrix

    # Assert that "None" is NOT present in p_facts, kp_facts, j_facts, or full_matrix
    assert "None" not in p_facts
    assert "None" not in kp_facts
    assert "None" not in j_facts
    assert "None" not in full_matrix

    # Assert that "AL (A1)" and "UL (A12)" are present in j_facts and full_matrix
    assert "AL (A1)" in j_facts
    assert "UL (A12)" in j_facts
    assert "AL (A1)" in full_matrix
    assert "UL (A12)" in full_matrix


def test_ai_synthesize_endpoint_validation():
    """Test POST /api/ai/synthesize returns SSE stream."""
    payload = {
        "chart_params": {
            "year": 1995,
            "month": 10,
            "day": 15,
            "hour": 14,
            "minute": 30,
            "second": 0.0,
            "city": "Jaipur, India",
            "latitude": 26.9124,
            "longitude": 75.7873,
            "timezone_str": "Asia/Kolkata",
        },
        "pillar": "comprehensive",
    }
    response = client.post("/api/ai/synthesize", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    content = response.text
    # When no key is set in test env, stream emits awakening status or error event
    assert "event:" in content


def test_ai_chat_endpoint_validation():
    """Test POST /api/ai/chat returns SSE stream."""
    payload = {
        "chart_params": {
            "year": 1995,
            "month": 10,
            "day": 15,
            "hour": 14,
            "minute": 30,
            "second": 0.0,
            "city": "Jaipur, India",
            "latitude": 26.9124,
            "longitude": 75.7873,
            "timezone_str": "Asia/Kolkata",
        },
        "messages": [
            {"role": "user", "content": "What are my main strengths?"}
        ],
    }
    response = client.post("/api/ai/chat", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    content = response.text
    assert "event:" in content


def test_api_key_modal_and_entry_points():
    """Verify that client-side Gemini API Key modal and entry points are removed so server key is used."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    # Client-side key entry points must NOT be present
    assert "btn-header-api-key" not in html
    assert "header-api-dot" not in html
    assert "chat-api-key-btn" not in html
    assert "btn-open-api-key-modal" not in html
    assert "api-key-modal" not in html
    assert "input-custom-gemini-key" not in html


def test_dossier_includes_d9_and_kp_significators():
    """Verify that AIDossierReport includes D9 Navamsha and KP 4-fold significators."""
    payload = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Jaipur, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
    }
    resp = client.post("/api/ai/dossier", json=payload)
    assert resp.status_code == 200
    dossier = resp.json()["ai_dossier"]
    md = dossier["markdown_dossier"]
    assert "D9 Navamsha" in md
    assert "D10 Dashamsha" in md
    assert "D10 Dashamsha Lagna (Career Ascendant)" in md
    assert "Vargottama" in md
    assert "KP 4-Fold Planetary Significators" in md
    assert "Level A" in md and "Level B" in md and "Level C" in md and "Level D" in md

    # Check structured payload
    structured_planets = dossier["structured_payload"]["planets"]
    sun_data = next(p for p in structured_planets if p["planet"] == "Sun")
    assert "d9_sign" in sun_data
    assert "d10_sign" in sun_data
    assert sun_data["d10_sign"] == "Kumbha"
    assert "d10_lagna" in dossier["structured_payload"]["baseline"]
    assert dossier["structured_payload"]["baseline"]["d10_lagna"] == "Meena"
    assert sun_data["is_vargottama"] is True


def test_deterministic_confluence_scoring():
    """Verify that TrinetriOrchestrator computes deterministic confluence across the three eyes."""
    from engines.trinetri_orchestrator import TrinetriOrchestrator

    payload = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Jaipur, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
    }
    resp = client.post("/api/calculate", json=payload)
    assert resp.status_code == 200
    chart_data = resp.json()

    confluence = TrinetriOrchestrator.calculate_triangulated_confluence(chart_data, pillar="career")
    assert "score" in confluence
    assert 40 <= confluence["score"] <= 98
    assert confluence["level"] in ("Triple Confluence", "Double Confluence", "Karmic Tension")
    assert "components" in confluence
    assert "parashari" in confluence["components"]
    assert "kp" in confluence["components"]
    assert "jaimini" in confluence["components"]

    # Verify that KP and Jaimini dynamically reflect the chart's actual CSL and Karaka placements
    # 1. Career pillar (Cusp 10 CSL is calculated dynamically, not static default 70):
    assert confluence["components"]["kp"] != 70
    assert confluence["components"]["kp"] == 64

    # 2. Comprehensive pillar (Cusp 1 CSL & Atmakaraka):
    conf_comp = TrinetriOrchestrator.calculate_triangulated_confluence(chart_data, pillar="comprehensive")
    # CSL of Cusp 1 is dynamically evaluated from planet strength (score 75, not static default 70)
    assert conf_comp["components"]["kp"] != 70
    assert conf_comp["components"]["kp"] == 75
    # AK (Sun) is in House 9, boosting Jaimini score to 80 (68 + 12), not static default 68
    assert conf_comp["components"]["jaimini"] != 68
    assert conf_comp["components"]["jaimini"] == 80
    # Parashari score is 76 (no false -8 penalty from inactive Sade Sati)
    assert conf_comp["components"]["parashari"] == 76


def test_three_eyes_wwh_deck_assets_and_prompts():
    """Verify that Three Eyes WWH system prompts and frontend renderers are fully configured."""
    from prompts.parashari_prompt import EYE_1_PARASHARI_WWH_SYSTEM_PROMPT
    from prompts.kp_prompt import EYE_2_KP_WWH_SYSTEM_PROMPT
    from prompts.jaimini_prompt import EYE_3_JAIMINI_WWH_SYSTEM_PROMPT
    import re

    # 1. Prompts existence and key directives
    for prompt_text in [EYE_1_PARASHARI_WWH_SYSTEM_PROMPT, EYE_2_KP_WWH_SYSTEM_PROMPT, EYE_3_JAIMINI_WWH_SYSTEM_PROMPT]:
        assert "ZERO EMOJIS" in prompt_text
        assert "TUESDAY MORNING TEST" in prompt_text
        assert '"archetype":' in prompt_text
        assert '"summary_verdict":' in prompt_text
        assert '"metrics":' in prompt_text
        assert '"what_you_are":' in prompt_text
        assert '"why_you_are":' in prompt_text
        assert '"how_you_operate":' in prompt_text
        assert '"astrological_proof":' in prompt_text
        # Ensure zero emoji characters in prompt text
        emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
        assert not emoji_pattern.search(prompt_text), "Found emoji in system prompt!"

    # 2. Check app.js exports and functions
    with open("frontend/js/app.js", "r", encoding="utf-8") as f:
        js = f.read()
    assert "function renderSchoolEyeDeck(" in js
    assert "function renderSchoolEyeOutput(" in js
    assert "function buildSchoolEyeMarkdown(" in js
    assert "updateEyesRendered" in js

    # 3. Check style.css school accent classes
    with open("frontend/css/style.css", "r", encoding="utf-8") as f:
        css = f.read()
    assert ".what-why-how-container.school-parashari" in css
    assert ".what-why-how-container.school-kp" in css
    assert ".what-why-how-container.school-jaimini" in css


def test_interactive_polarity_and_arena_switcher():
    """Verify Phase A interactive assets: Polarity Spectrum and Arena Switcher."""
    from prompts.synthesizer_prompt import WHAT_WHY_HOW_SYSTEM_PROMPT
    import re

    # 1. Synthesizer prompt contains arenas schema and has 0 emojis
    assert '"arenas":' in WHAT_WHY_HOW_SYSTEM_PROMPT
    assert '"work":' in WHAT_WHY_HOW_SYSTEM_PROMPT
    assert '"relationships":' in WHAT_WHY_HOW_SYSTEM_PROMPT
    assert '"crisis":' in WHAT_WHY_HOW_SYSTEM_PROMPT
    assert '"solo":' in WHAT_WHY_HOW_SYSTEM_PROMPT
    assert '"defuser":' in WHAT_WHY_HOW_SYSTEM_PROMPT
    emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
    assert not emoji_pattern.search(WHAT_WHY_HOW_SYSTEM_PROMPT), "Found emoji in WHAT_WHY_HOW_SYSTEM_PROMPT!"

    # 2. Check app.js functions
    with open("frontend/js/app.js", "r", encoding="utf-8") as f:
        js = f.read()
    assert "function calculatePolaritySpectrum(" in js
    assert "function togglePolarityCard(" in js
    assert "function renderPolaritySpectrum(" in js
    assert "function getArenaData(" in js
    assert "function renderArenaPanel(" in js
    assert "function switchWwhArena(" in js
    assert "function renderArenaSwitcher(" in js
    assert "[HOW YOU'RE WIRED]" in js
    assert "[HOW YOU SHOW UP]" in js
    assert "[WHERE YOU STAND TODAY]" in js
    assert "[YOUR GREATEST STRENGTH]" in js
    assert "[THE GOLDEN RULE]" in js

    # 3. Check style.css classes
    with open("frontend/css/style.css", "r", encoding="utf-8") as f:
        css = f.read()
    assert ".wwh-polarity-grid" in css
    assert ".wwh-polarity-card" in css
    assert ".wwh-polarity-marker" in css
    assert ".wwh-arena-switcher-box" in css
    assert ".wwh-arena-pill" in css
    assert ".wwh-season-card" in css
    assert ".wwh-season-headline" in css
    assert ".wwh-dilemma-card" in css
    assert ".wwh-dilemma-verdict-box" in css
    assert ".wwh-dilemma-timing-grid" in css
    assert ".wwh-dilemma-direct-box" in css

    # 4. Prompt contains current_life_season and human counselor instructions
    assert '"current_life_season":' in WHAT_WHY_HOW_SYSTEM_PROMPT
    assert '"dilemma_counsel":' in WHAT_WHY_HOW_SYSTEM_PROMPT
    assert '"exact_timeline":' in WHAT_WHY_HOW_SYSTEM_PROMPT
    assert '"direct_answer":' in WHAT_WHY_HOW_SYSTEM_PROMPT
    assert "GROUNDED HUMAN COUNSELOR" in WHAT_WHY_HOW_SYSTEM_PROMPT
    assert "BANNED VOCABULARY" in WHAT_WHY_HOW_SYSTEM_PROMPT
    assert "SEEKER'S CURRENT QUERY & EXACT EVENT TIMING" in WHAT_WHY_HOW_SYSTEM_PROMPT


def test_fagan_bradley_ayanamsha_and_dignity_in_dossier():
    """Verify /api/calculate succeeds with ayanamsha='Fagan_Bradley' and reports Exalted Mercury in ai_dossier."""
    payload = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Jaipur, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
        "ayanamsha": "Fagan_Bradley",
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["summary"]["ayanamsha_name"] == "Fagan_Bradley"

    # Also verify reference chart (Lahiri standard) reports Exalted Mercury in ai_dossier
    ref_payload = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Jaipur, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
    }
    ref_resp = client.post("/api/calculate", json=ref_payload)
    assert ref_resp.status_code == 200
    ref_data = ref_resp.json()
    assert "ai_dossier" in ref_data
    ai_dossier = ref_data["ai_dossier"]
    md = ai_dossier["markdown_dossier"]
    assert "Exalted" in md
    mercury_line = next(line for line in md.split("\n") if "**Mercury**" in line)
    assert "Exalted" in mercury_line

    # Also verify frontend options contain Fagan_Bradley
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    assert '<option value="Fagan_Bradley">' in html
    assert '<option value="Fagan-Bradley">' not in html


def test_craft_wealth_public_calling_deck_and_prompts():
    """Verify Pillar 2 (Craft, Wealth & Public Calling) Bento Deck assets, prompt schemas, and titles."""
    import re
    from prompts.synthesizer_prompt import CRAFT_WEALTH_CALLING_SYSTEM_PROMPT, build_synthesizer_prompt
    from engines.trinetri_orchestrator import PILLAR_TITLES

    # 1. PILLAR_TITLES check
    assert PILLAR_TITLES["career"] == "2. Craft, Wealth & Public Calling (10th/2nd/11th Cusps, D10 & AmK)"

    # 2. System prompt schema checks
    assert '"work_genius":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"craft_essence":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"autonomy_vs_hierarchy":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"flow_state_trigger":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"ideal_work_environment":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"leadership_and_authority":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"leadership_stance":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"office_politics_reflex":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"delegation_tripwire":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"wealth_engine":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"wealth_archetype":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"primary_inflow_channel":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"unconscious_financial_leak":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"monetization_rule":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"enterprise_vs_employment":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"recommended_path":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"optimal_vehicle":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"timing_weather":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"current_season_headline":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"tactical_levers":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"golden_career_lever":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"negotiation_mantra":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"astrological_proof":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"dilemma_counsel":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"exact_timeline":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert '"direct_answer":' in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert "SEEKER'S CURRENT VOCATIONAL / FINANCIAL CROSSROADS & TIMELINE:" in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT

    # 2.1 Grounded mentor tone & banned vocabulary invariant checks
    assert "GROUNDED VOCATIONAL MENTOR" in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert "BANNED VOCABULARY" in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert "ANCHORING IN NATIVE AGE & CURRENT CAREER CHAPTER:" in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT
    assert "High-Velocity Monopolist" not in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT

    # 2.2 Dedicated Career Prompts for the Three Eyes
    from prompts.parashari_prompt import EYE_1_PARASHARI_CAREER_SYSTEM_PROMPT
    from prompts.kp_prompt import EYE_2_KP_CAREER_SYSTEM_PROMPT
    from prompts.jaimini_prompt import EYE_3_JAIMINI_CAREER_SYSTEM_PROMPT

    assert "EYE 1 of TRINETRI AI — the Brihat Parashara Hora Shastra (BPHS) Classical Master evaluating Pillar 2" in EYE_1_PARASHARI_CAREER_SYSTEM_PROMPT
    assert '"tenth_house_lord":' in EYE_1_PARASHARI_CAREER_SYSTEM_PROMPT
    assert '"d10_dashamsha_dignity":' in EYE_1_PARASHARI_CAREER_SYSTEM_PROMPT
    assert '"dhana_raja_yogas":' in EYE_1_PARASHARI_CAREER_SYSTEM_PROMPT
    assert '"career_dasha_impact":' in EYE_1_PARASHARI_CAREER_SYSTEM_PROMPT
    assert "GROUNDED VOCATIONAL MENTOR" in EYE_1_PARASHARI_CAREER_SYSTEM_PROMPT

    assert "EYE 2 of TRINETRI AI — the Krishnamurti Paddhati (KP Stellar System) Master evaluating Pillar 2" in EYE_2_KP_CAREER_SYSTEM_PROMPT
    assert '"cusp_10_sub_lord":' in EYE_2_KP_CAREER_SYSTEM_PROMPT
    assert '"cusp_2_sub_lord":' in EYE_2_KP_CAREER_SYSTEM_PROMPT
    assert '"elevation_significators":' in EYE_2_KP_CAREER_SYSTEM_PROMPT
    assert '"drainage_houses":' in EYE_2_KP_CAREER_SYSTEM_PROMPT
    assert "GROUNDED VOCATIONAL MENTOR" in EYE_2_KP_CAREER_SYSTEM_PROMPT

    assert "EYE 3 of TRINETRI AI — the Jaimini Upadesha Sutras Master evaluating Pillar 2" in EYE_3_JAIMINI_CAREER_SYSTEM_PROMPT
    assert '"amatyakaraka_work":' in EYE_3_JAIMINI_CAREER_SYSTEM_PROMPT
    assert '"atmakaraka_soul":' in EYE_3_JAIMINI_CAREER_SYSTEM_PROMPT
    assert '"rajya_pada_a10":' in EYE_3_JAIMINI_CAREER_SYSTEM_PROMPT
    assert '"career_chara_dasha":' in EYE_3_JAIMINI_CAREER_SYSTEM_PROMPT
    assert "GROUNDED VOCATIONAL MENTOR" in EYE_3_JAIMINI_CAREER_SYSTEM_PROMPT

    # 3. Emoji invariant across all Pillar 2 prompts
    emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
    assert not emoji_pattern.search(CRAFT_WEALTH_CALLING_SYSTEM_PROMPT), "Found emoji in CRAFT_WEALTH_CALLING_SYSTEM_PROMPT!"
    assert not emoji_pattern.search(EYE_1_PARASHARI_CAREER_SYSTEM_PROMPT), "Found emoji in EYE_1_PARASHARI_CAREER_SYSTEM_PROMPT!"
    assert not emoji_pattern.search(EYE_2_KP_CAREER_SYSTEM_PROMPT), "Found emoji in EYE_2_KP_CAREER_SYSTEM_PROMPT!"
    assert not emoji_pattern.search(EYE_3_JAIMINI_CAREER_SYSTEM_PROMPT), "Found emoji in EYE_3_JAIMINI_CAREER_SYSTEM_PROMPT!"

    # 4. build_synthesizer_prompt instruction for career pillar
    prompt = build_synthesizer_prompt(
        pillar_title=PILLAR_TITLES["career"],
        parashari_verdict="P evidence",
        kp_verdict="KP evidence",
        jaimini_verdict="J evidence",
        natal_summary="Ground truth summary",
        pillar_key="career",
    )
    assert "'Craft, Wealth & Public Calling' JSON blueprint" in prompt

    prompt_with_query = build_synthesizer_prompt(
        pillar_title=PILLAR_TITLES["career"],
        parashari_verdict="P evidence",
        kp_verdict="KP evidence",
        jaimini_verdict="J evidence",
        natal_summary="Ground truth summary",
        custom_query="Considering leaving corporate to consult",
        pillar_key="career",
    )
    assert 'Directly evaluate and resolve the seeker\'s crossroads in the "dilemma_counsel" block' in prompt_with_query

    # 5. Frontend index.html verification
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    assert '<div class="ai-pillar-title">Craft, Wealth & Public Calling</div>' in html

    # 6. Frontend app.js verification
    with open("frontend/js/app.js", "r", encoding="utf-8") as f:
        js = f.read()
    assert "function renderDilemmaCounselCard(" in js
    assert "function renderCraftWealthDeck(" in js
    assert "function scrollToCwpSection(" in js
    assert "function buildMarkdownFromCraftWealth(" in js
    assert 'career: { chapter: 2, name: "Craft, Wealth & Public Calling", title: "Vocational Mastery & Wealth Blueprint" }' in js
    assert "[YOUR WORK, WEALTH & CALLING]" in js
    assert "[YOUR WORK GENIUS & FLOW]" in js
    assert "[HOW YOU LEAD & HOW OTHERS SEE YOU]" in js
    assert "[HOW MONEY & WEALTH WORK FOR YOU]" in js
    assert "[BUILDING YOUR OWN THING VS. WORKING FOR OTHERS]" in js
    assert "[WHERE YOUR CAREER IS HEADING (NEXT 24 MONTHS)]" in js
    assert "[PRACTICAL WORK RULES FOR EVERYDAY LIFE]" in js
    assert "CAREER_SCHOOL_METRIC_CONFIGS" in js
    assert "[PARASHARI PERSPECTIVE • VOCATIONAL FOUNDATION & DHANA YOGAS]" in js
    assert "[KP STELLAR PERSPECTIVE • CAREER GATES & REAL-WORLD TIMING]" in js
    assert "[JAIMINI SUTRAS PERSPECTIVE • PUBLIC REPUTATION VS. INNER CRAFT]" in js

    # 7. Frontend style.css verification
    with open("frontend/css/style.css", "r", encoding="utf-8") as f:
        css = f.read()
    assert ".cwp-container" in css
    assert ".cwp-hero-card" in css
    assert ".cwp-timing-grid" in css
    assert ".cwp-dilemma-card" in css
    assert ".wwh-dilemma-win-pill" in css
    assert ".wwh-golden-strip" in css
    assert ".cwp-monetization-strip" in css
    assert ".wwh-golden-tag" in css
    assert ".wwh-golden-text" in css


def test_gender_field_integration_and_karaka_branching():
    """Verify gender field integration end-to-end: API payload, dossier, orchestrator, and frontend."""
    from engines.trinetri_orchestrator import TrinetriOrchestrator

    base_payload = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Jaipur, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
    }

    # 1. Default gender (male)
    resp_male = client.post("/api/calculate", json=base_payload)
    assert resp_male.status_code == 200
    data_male = resp_male.json()
    assert data_male["gender"] == "male"
    assert data_male["summary"]["gender"] == "male"
    assert "Male" in data_male["summary"]["birth_profile"]

    dossier_male = data_male["ai_dossier"]["markdown_dossier"]
    assert "- **Native Gender**: Male" in dossier_male
    assert "Venus (Kalatrakaraka - Wife/Partner)" in dossier_male
    assert "- **Native Age**:" in dossier_male
    assert "Birth Location" not in dossier_male
    assert "Effective Date & Time" not in dossier_male
    assert "Julian Day" not in dossier_male

    base_struct = data_male["ai_dossier"]["structured_payload"]["baseline"]
    assert "age" in base_struct
    assert "gender" in base_struct
    assert "operating_cycle" in base_struct
    assert "city" not in base_struct
    assert "latitude" not in base_struct

    # 2. Explicit female gender
    payload_female = dict(base_payload)
    payload_female["gender"] = "female"
    resp_female = client.post("/api/calculate", json=payload_female)
    assert resp_female.status_code == 200
    data_female = resp_female.json()
    assert data_female["gender"] == "female"
    assert data_female["summary"]["gender"] == "female"
    assert "Female" in data_female["summary"]["birth_profile"]

    dossier_female = data_female["ai_dossier"]["markdown_dossier"]
    assert "- **Native Gender**: Female" in dossier_female
    assert "Jupiter (Patikaraka - Husband/Partner, with Mars for attraction)" in dossier_female

    # 3. Orchestrator fact slicers and ground-truth matrix reflection
    p_facts_female = TrinetriOrchestrator.slice_parashari_facts(data_female)
    assert "- **Native Gender**: Female" in p_facts_female
    assert "Jupiter (Patikaraka" in p_facts_female

    gt_matrix_female = TrinetriOrchestrator.build_full_ground_truth_matrix(data_female)
    assert "- **Native Gender**: Female" in gt_matrix_female
    assert "Jupiter (Patikaraka" in gt_matrix_female

    # 4. Confluence scoring difference for relationship pillar based on gender karaka
    conf_male = TrinetriOrchestrator.calculate_triangulated_confluence(data_male, pillar="relationships")
    conf_female = TrinetriOrchestrator.calculate_triangulated_confluence(data_female, pillar="relationships")
    assert "score" in conf_male
    assert "score" in conf_female
    assert "components" in conf_male
    assert "components" in conf_female

    # 5. Frontend index.html verification
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    assert '<select id="select-quick-gender"' in html
    assert '<select id="select-birth-gender"' in html
    assert '<option value="male"' in html
    assert '<option value="female"' in html
    assert '<option value="other"' in html

    # 6. Frontend app.js verification
    with open("frontend/js/app.js", "r", encoding="utf-8") as f:
        js = f.read()
    assert 'gender: "male"' in js
    assert 'state.gender' in js
    assert 'select-quick-gender' in js
    assert 'select-birth-gender' in js
    assert 'state.gender || "male"' in js


def test_zero_pii_and_three_tier_vimshottari_timeline():
    """Verify complete Zero-PII anonymization and 3-tier Vimshottari temporal hierarchy in AI Dossier & Orchestrator."""
    payload = {
        "year": 1995,
        "month": 10,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 0.0,
        "city": "Secret City, Wonderland",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone_str": "Asia/Kolkata",
        "gender": "male",
    }
    resp = client.post("/api/calculate", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    ai_dossier = data["ai_dossier"]
    md_dossier = ai_dossier["markdown_dossier"]
    st_payload = ai_dossier["structured_payload"]

    # 1. Zero-PII Verification
    assert "Secret City" not in md_dossier
    assert "Wonderland" not in md_dossier
    assert "26.9124" not in md_dossier
    assert "75.7873" not in md_dossier
    assert "1995-10-15" not in md_dossier
    assert "14:30" not in md_dossier
    assert "Julian Day" not in md_dossier

    from datetime import date
    current_year = date.today().year
    expected_age = current_year - 1995
    assert f"**Native Age**: ~{expected_age} years (Operating Cycle: {current_year})" in md_dossier

    baseline = st_payload["baseline"]
    assert "city" not in baseline
    assert "latitude" not in baseline
    assert "longitude" not in baseline
    assert "effective_datetime" not in baseline
    assert baseline["age"] == expected_age
    assert baseline["operating_cycle"] == current_year

    # 2. 3-Tier Vimshottari Hierarchy in Markdown Dossier
    assert "## 5. VIMSHOTTARI DASHA CHRONOLOGY & RUNNING PERIOD" in md_dossier
    assert "### Macro Era Horizon (Mahadasha Eras):" in md_dossier
    assert "**Previous Era (Concluded)**:" in md_dossier
    assert "**Current Operating Era (ACTIVE)**:" in md_dossier
    assert "**Next Horizon Era (Upcoming)**:" in md_dossier

    assert "### Seasonal Strategic Timeline: Antardashas (Recent Past → Current → Upcoming):" in md_dossier
    assert "| Period (MD-AD) | Start Date | End Date | Duration | Operational Status |" in md_dossier
    assert "**CURRENT ACTIVE**" in md_dossier
    assert "Upcoming" in md_dossier

    assert "### Tactical Micro-Dial: Pratyantardasha (PD) Timeline (Immediate 3–6 Months):" in md_dossier
    assert "| Level (MD-AD-PD) | Start Date | End Date | Duration | Tactical Timing |" in md_dossier

    # 3. 3-Tier Vimshottari Hierarchy in TrinetriOrchestrator
    p_facts = TrinetriOrchestrator.slice_parashari_facts(data)
    assert "**Macro Era Horizon (Mahadasha Eras):**" in p_facts
    assert "**Seasonal Strategic Timeline: Antardashas" in p_facts
    assert "**Tactical Micro-Dial: Pratyantardasha (PD) Timeline" in p_facts

    gt_matrix = TrinetriOrchestrator.build_full_ground_truth_matrix(data)
    assert "**Macro Era Horizon (Mahadasha Eras):**" in gt_matrix
    assert "**Seasonal Strategic Timeline: Antardashas" in gt_matrix
    assert "**Tactical Micro-Dial: Pratyantardasha (PD) Timeline" in gt_matrix


