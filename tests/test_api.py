"""Integration Tests for FastAPI Backend API Endpoints."""

import pytest
from starlette.testclient import TestClient

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
    assert "api-key-modal" in html
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
    """Verify that Gemini API Key modal and its access entry points are present and correctly configured."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    # Header entry point
    assert "btn-header-api-key" in html
    assert "header-api-dot" in html
    # Chat drawer entry point
    assert "chat-api-key-btn" in html
    # Tab 8 entry point
    assert "btn-open-api-key-modal" in html
    # Modal structure: must not be hardcoded to display:none inline
    assert 'id="api-key-modal" class="modal-overlay"' in html
    assert "btn-toggle-key-visibility" in html
    assert "btn-save-api-key" in html
    assert "btn-clear-api-key" in html
    assert "input-custom-gemini-key" in html
    assert "select-gemini-model" in html


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
    assert "Vargottama" in md
    assert "KP 4-Fold Planetary Significators" in md
    assert "Level A" in md and "Level B" in md and "Level C" in md and "Level D" in md

    # Check structured payload
    structured_planets = dossier["structured_payload"]["planets"]
    sun_data = next(p for p in structured_planets if p["planet"] == "Sun")
    assert "d9_sign" in sun_data
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


