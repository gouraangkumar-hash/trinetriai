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
    assert any(y["id"] == "mahapurusha_venus" for y in data["yogas_list"])
    assert "ashtakavarga" in data
    assert data["ashtakavarga"]["summary"]["total_bindus"] == 337
    assert len(data["ashtakavarga"]["sarvashtakavarga"]) == 12
    assert "Jupiter" in data["ashtakavarga"]["bhinna"]
    assert "sav_chart_svg" in data
    assert "<svg" in data["sav_chart_svg"]
    assert "SARVASHTAKAVARGA" in data["sav_chart_svg"]





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


def test_serve_index_and_static():
    """Test GET / returns HTML and static files exist."""
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "TRINETRI AI" in response.text
    assert "app.js" in response.text


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

    # Check anti-caching headers on root response
    assert response.headers.get("cache-control") == "no-cache, no-store, must-revalidate"

    # Check cache-busting query strings on static assets
    assert "/static/css/style.css?v=" in html
    assert "/static/js/app.js?v=" in html

    # Check Pratyantardasha elements in index.html
    assert "current-pd-card" in html
    assert "current-pd-table-body" in html
    assert "Active Pratyantardashas (Sub-Sub Periods)" in html

    css_res = client.get("/static/css/style.css")
    assert css_res.status_code == 200
    css = css_res.text
    assert ".overview-hero-layout" in css
    assert ".ad-dates-cell" in css
    assert "min-width: 0" in css
    assert ".pd-nested-table" in css
    assert "pd-panel-row" in css

    js_res = client.get("/static/js/app.js")
    assert js_res.status_code == 200
    js = js_res.text
    assert "initDateTimeDropdowns" in js
    assert "syncModalWithState" in js
    assert "select-birth-year" in js
    assert "drawer-vargottama" in js
    assert "p.is_vargottama" in js
    assert "togglePratyantardashaRow" in js
    assert "window.togglePratyantardashaRow" in js
    assert "window.toggleMahadashaCard" in js


