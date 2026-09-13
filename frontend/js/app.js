/**
 * TrinetriAI Vedic Studio — Pure Vanilla JavaScript Application Logic
 * Fast, lightweight, zero-dependency browser controller.
 */

// =============================================================================
// State Management
// =============================================================================

const state = {
  year: 1995,
  month: 10,
  day: 15,
  hour: 14,
  minute: 30,
  second: 0.0,
  city: "Jaipur, India",
  latitude: 26.9124,
  longitude: 75.7873,
  timezone_str: "Asia/Kolkata",
  time_offset_seconds: 0,
  ayanamsha: "Lahiri",
  node_type: "True",
  chart_style: "north", // "north" | "south"
  sign_mode: "sanskrit", // "sanskrit" | "english"
  theme_mode: "light", // "light" | "dark"
  selected_varga: "D1",
  active_tab: "kundali",
  active_yoga_filter: "all",
  selected_bav_planet: "Jupiter",
  show_gochar: false,
  activeRayPlanet: null,
  currentData: null,
};

// =============================================================================
// Astronomical & Glyph Dictionaries
// =============================================================================

const PLANET_GLYPHS = {
  "Ascendant (Lagna)": "✧",
  Ascendant: "✧",
  Sun: "☉",
  Moon: "☽",
  Mars: "♂",
  Mercury: "☿",
  Jupiter: "♃",
  Venus: "♀",
  Saturn: "♄",
  Rahu: "☊",
  Ketu: "☋",
  Uranus: "♅",
  Neptune: "♆",
  Pluto: "♇",
};

const KARAKA_DESCRIPTIONS = {
  AK: "Atmakaraka — Soul's highest purpose and karmic destiny",
  AmK: "Amatyakaraka — Career, intellect, and executive guidance",
  BK: "Bhratrikaraka — Siblings, courage, and spiritual teachers",
  MK: "Matrikaraka — Mother, happiness, home, and education",
  PK: "Putrakaraka — Children, creative intelligence, and disciples",
  GK: "Gnatikaraka — Obstacles, competition, and ancestral debt",
  DK: "Darakaraka — Spouse, life partner, and worldly partnerships",
};

const NORTH_HOUSE_CENTERS = {
  1:  { x: 400, y: 185 },
  2:  { x: 200, y: 80 },
  3:  { x: 80,  y: 200 },
  4:  { x: 195, y: 400 },
  5:  { x: 80,  y: 600 },
  6:  { x: 200, y: 720 },
  7:  { x: 400, y: 615 },
  8:  { x: 600, y: 720 },
  9:  { x: 720, y: 600 },
  10: { x: 605, y: 400 },
  11: { x: 720, y: 200 },
  12: { x: 600, y: 80 },
};

const SOUTH_SIGN_GRID = {
  12: { col: 0, row: 0 },
  1:  { col: 1, row: 0 },
  2:  { col: 2, row: 0 },
  3:  { col: 3, row: 0 },
  4:  { col: 3, row: 1 },
  5:  { col: 3, row: 2 },
  6:  { col: 3, row: 3 },
  7:  { col: 2, row: 3 },
  8:  { col: 1, row: 3 },
  9:  { col: 0, row: 3 },
  10: { col: 0, row: 2 },
  11: { col: 0, row: 1 },
};

// =============================================================================
// API Communication
// =============================================================================

async function calculateChart() {
  const payload = {
    year: state.year,
    month: state.month,
    day: state.day,
    hour: state.hour,
    minute: state.minute,
    second: state.second,
    city: state.city,
    latitude: state.latitude,
    longitude: state.longitude,
    timezone_str: state.timezone_str,
    time_offset_seconds: state.time_offset_seconds,
    ayanamsha: state.ayanamsha,
    node_type: state.node_type,
    chart_style: state.chart_style,
    sign_mode: state.sign_mode,
    theme_mode: state.theme_mode,
    selected_varga: state.selected_varga,
    show_gochar: state.show_gochar,
  };

  try {
    const res = await fetch("/api/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Chart calculation error");
    }

    const data = await res.json();
    state.currentData = data;
    renderAll();
  } catch (err) {
    console.error("Calculation failed:", err);
    alert("Error calculating chart: " + err.message);
  }
}

async function selectVarga(varga) {
  state.selected_varga = varga;

  // Update button highlights
  document.querySelectorAll(".varga-pill-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.varga === varga);
  });
  document.querySelectorAll(".quick-varga-pill").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.varga === varga);
  });

  const payload = {
    varga: varga,
    chart_params: {
      year: state.year,
      month: state.month,
      day: state.day,
      hour: state.hour,
      minute: state.minute,
      second: state.second,
      city: state.city,
      latitude: state.latitude,
      longitude: state.longitude,
      timezone_str: state.timezone_str,
      time_offset_seconds: state.time_offset_seconds,
      ayanamsha: state.ayanamsha,
      node_type: state.node_type,
      chart_style: state.chart_style,
      sign_mode: state.sign_mode,
      theme_mode: state.theme_mode,
      selected_varga: varga,
      show_gochar: state.show_gochar,
    },
  };

  try {
    const res = await fetch("/api/vargas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error("Varga calculation error");
    const data = await res.json();

    // Update state data
    if (state.currentData) {
      state.currentData.chart_svg = data.chart_svg;
      state.currentData.varga_table = data.varga_table;
    }

    renderKundaliChart();
    renderVargasWorkspace();
  } catch (err) {
    console.error("Failed to load varga:", err);
  }
}

async function geocodeLocation(query) {
  const feedback = document.getElementById("geocode-feedback");
  feedback.style.display = "block";
  feedback.textContent = "Resolving location coordinates...";

  try {
    const res = await fetch(`/api/geocode?query=${encodeURIComponent(query)}`);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Could not find location");
    }
    const data = await res.json();

    document.getElementById("input-city").value = data.display_name;
    document.getElementById("input-latitude").value = data.latitude;
    document.getElementById("input-longitude").value = data.longitude;
    document.getElementById("input-timezone").value = data.timezone_str;

    feedback.textContent = `✓ Found: ${data.display_name} (${data.timezone_str})`;
    setTimeout(() => {
      feedback.style.display = "none";
    }, 4000);
  } catch (err) {
    feedback.textContent = "⚠️ " + err.message;
  }
}

// =============================================================================
// DOM Rendering Functions
// =============================================================================

function renderAll() {
  if (!state.currentData) return;

  renderHeaderCapsule();
  renderScrubberDisplay();
  renderKundaliChart();
  renderAngles();
  renderActiveDashaStrip();
  renderYogasOverviewStrip();
  renderGocharWorkspace();
  renderPlanetsTable();
  renderBhavaAspectsWorkspace();
  renderTelemetry();
  renderVargasWorkspace();
  renderDashasWorkspace();
  renderKPWorkspace();
  renderJaiminiWorkspace();
  renderYogasWorkspace();
  renderAshtakavargaWorkspace();
}

function renderHeaderCapsule() {
  const d = state.currentData;
  const el = document.getElementById("birth-capsule-text");
  if (el && d.summary) {
    el.textContent = d.summary.birth_profile;
  }
}

function renderScrubberDisplay() {
  const el = document.getElementById("scrub-display");
  if (!el) return;

  const off = state.time_offset_seconds;
  if (off === 0) {
    el.textContent = "0s (Exact)";
    return;
  }

  const mins = Math.trunc(off / 60);
  const secs = Math.abs(off % 60);
  const sign = off > 0 ? "+" : "-";

  if (Math.abs(mins) > 0 && secs > 0) {
    el.textContent = `${sign}${Math.abs(mins)}m ${secs}s`;
  } else if (Math.abs(mins) > 0) {
    el.textContent = `${sign}${Math.abs(mins)}m`;
  } else {
    el.textContent = `${sign}${secs}s`;
  }
}

function renderKundaliChart() {
  const d = state.currentData;
  if (!d) return;

  const svgContainer = document.getElementById("main-chart-svg");
  if (svgContainer) {
    svgContainer.innerHTML = d.chart_svg;
    if (state.activeRayPlanet) {
      renderAspectRays(state.activeRayPlanet);
    }
  }

  const titleEl = document.getElementById("kundali-chart-title");
  if (titleEl) {
    const v = state.selected_varga;
    if (v === "D1") titleEl.textContent = "D1 RASHI CHART";
    else if (v === "D9") titleEl.textContent = "D9 NAVAMSHA CHART";
    else if (v === "D10") titleEl.textContent = "D10 DASHAMSHA CHART";
    else titleEl.textContent = `${v} DIVISIONAL CHART`;
  }
}

function renderAngles() {
  const d = state.currentData;
  if (!d || !d.summary) return;
  const s = d.summary;

  document.getElementById("angle-asc-sign").textContent = s.ascendant.sign;
  document.getElementById("angle-asc-deg").textContent = s.ascendant.degree;
  document.getElementById("angle-asc-nak").textContent = s.ascendant.nakshatra;

  document.getElementById("angle-moon-sign").textContent = s.moon.sign;
  document.getElementById("angle-moon-deg").textContent = s.moon.degree;
  document.getElementById("angle-moon-nak").textContent = s.moon.nakshatra;

  document.getElementById("angle-sun-sign").textContent = s.sun.sign;
  document.getElementById("angle-sun-deg").textContent = s.sun.degree;
  document.getElementById("angle-sun-nak").textContent = s.sun.nakshatra;

  document.getElementById("angle-mc-sign").textContent = s.mc.sign;
  document.getElementById("angle-mc-deg").textContent = s.mc.degree;
  document.getElementById("angle-mc-nak").textContent = s.mc.nakshatra;
}

function renderActiveDashaStrip() {
  const d = state.currentData;
  if (!d || !d.dasha_summary) return;
  const ds = d.dasha_summary;

  const elMd = document.getElementById("strip-dasha-md");
  if (elMd) elMd.textContent = ds.md;
  const elAd = document.getElementById("strip-dasha-ad");
  if (elAd) elAd.textContent = ds.ad;
  const elPd = document.getElementById("strip-dasha-pd");
  if (elPd) elPd.textContent = ds.pd;
  const elDates = document.getElementById("strip-dasha-dates");
  if (elDates) elDates.textContent = `${ds.ad} AD (${ds.ad_range}) • Active PD: ${ds.pd} (${ds.pd_range})`;

  // Also update hero in Tab 3
  const heroMd = document.getElementById("dasha-hero-md");
  if (heroMd) heroMd.textContent = ds.md;
  const heroAd = document.getElementById("dasha-hero-ad");
  if (heroAd) heroAd.textContent = ds.ad;
  const heroPd = document.getElementById("dasha-hero-pd");
  if (heroPd) heroPd.textContent = ds.pd;
  const heroDates = document.getElementById("dasha-hero-dates");
  if (heroDates) heroDates.textContent = `Current Mahadasha: ${ds.md_range} • Active Pratyantar: ${ds.pd_range}`;
}

function renderPlanetsTable() {
  const d = state.currentData;
  if (!d || !d.planets_table) return;

  const tbody = document.getElementById("overview-planets-table-body");
  if (!tbody) return;

  tbody.innerHTML = d.planets_table
    .map((p) => {
      const glyph = PLANET_GLYPHS[p.planet] || "";
      const retroBadge = p.is_retro ? `<span class="status-badge retro">Retro</span>` : "";
      const combustBadge = p.is_combust ? `<span class="status-badge combust">Combust</span>` : "";
      const motionHtml = retroBadge || combustBadge ? `${retroBadge} ${combustBadge}` : `<span class="status-badge upcoming">Direct</span>`;

      const vargottamaTag = p.is_vargottama
        ? `<span class="status-badge active" style="font-size: 0.625rem; padding: 0.1rem 0.35rem; margin-left: 0.35rem; vertical-align: middle;" title="Vargottama: Same sign in D1 & D9">Vargottama</span>`
        : "";

      // Drishti Cast Pills
      let drishtiHtml = `<span style="color: var(--text-muted); font-size: 0.8rem;">-</span>`;
      if (p.drishti_badges && p.drishti_badges.length > 0) {
        drishtiHtml = `
          <div class="aspect-pills-wrap">
            ${p.drishti_badges.map(b => `
              <span class="aspect-pill ${b.is_special ? 'special' : ''}" 
                    title="${b.title}" 
                    onclick="togglePlanetAspectRays('${p.planet}', event)">
                ${b.label}
              </span>
            `).join("")}
          </div>
        `;
      }

      // Action Buttons
      const isRayActive = (state.activeRayPlanet === p.planet);
      const isAscendant = p.planet.includes("Ascendant");
      const raysBtnHtml = !isAscendant ? `
        <button class="action-pill aspect-rays-btn ${isRayActive ? 'active' : ''}" 
                id="rays-btn-${p.planet}" 
                onclick="togglePlanetAspectRays('${p.planet}', event)" 
                title="Toggle visual aspect rays on Kundali chart">
          ✦ Rays
        </button>
      ` : "";

      const rowClass = isRayActive ? 'active-ray-row' : '';
      const rowId = `planet-row-${p.planet.replace(/[^a-zA-Z0-9]/g, '')}`;

      return `
        <tr class="${rowClass}" id="${rowId}">
          <td onclick="${!isAscendant ? `togglePlanetAspectRays('${p.planet}', event)` : ''}" 
              style="${!isAscendant ? 'cursor: pointer;' : ''}" 
              title="${!isAscendant ? 'Click to toggle aspect rays on chart' : ''}">
            <strong style="color: var(--accent-primary); margin-right: 0.4rem;">${glyph}</strong> 
            <span class="${!isAscendant ? 'planet-name-link' : ''}">${p.planet}</span>${vargottamaTag}
          </td>
          <td>${p.sign}</td>
          <td style="font-family: var(--font-mono);">${p.degree}</td>
          <td>${p.nakshatra}</td>
          <td>${motionHtml}</td>
          <td>${drishtiHtml}</td>
          <td>
            <div style="display: flex; gap: 0.35rem; align-items: center;">
              ${raysBtnHtml}
              <button class="inspect-btn" onclick="openPlanetDrawer('${p.planet}')">Inspect</button>
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
}

function renderTelemetry() {
  const d = state.currentData;
  if (!d || !d.summary) return;
  const s = d.summary;

  document.getElementById("telemetry-jd-ut").textContent = `${s.julian_day_ut} UT`;
  document.getElementById("telemetry-jd-et").textContent = `${s.julian_day_et} ET`;
  document.getElementById("telemetry-ayanamsha").textContent = `${s.ayanamsha_name} (${s.ayanamsha_degree})`;
}

function renderVargasWorkspace() {
  const d = state.currentData;
  if (!d) return;

  const vargaSvg = document.getElementById("varga-chart-svg");
  if (vargaSvg) {
    vargaSvg.innerHTML = d.chart_svg;
  }

  const titleEl = document.getElementById("varga-chart-title");
  if (titleEl) {
    titleEl.textContent = `${state.selected_varga} DIVISIONAL CHART`;
  }

  const tableTitle = document.getElementById("varga-table-title");
  if (tableTitle) {
    tableTitle.textContent = `Planetary Placements in ${state.selected_varga}`;
  }

  const tbody = document.getElementById("varga-table-body");
  if (tbody && d.varga_table) {
    tbody.innerHTML = d.varga_table
      .map((row) => {
        const glyph = PLANET_GLYPHS[row.planet] || "";
        const isAsc = row.planet.includes("Ascendant");
        const nameHtml = isAsc
          ? `<strong style="color: var(--accent-primary);">✧ ${row.planet}</strong>`
          : `<strong style="color: var(--accent-primary); margin-right: 0.4rem;">${glyph}</strong> ${row.planet}`;

        const statusBadges = [];
        if (row.is_retro) statusBadges.push(`<span class="status-badge retro">Retro</span>`);
        if (row.is_combust) statusBadges.push(`<span class="status-badge combust">Combust</span>`);
        const statusHtml = statusBadges.length > 0 ? statusBadges.join(" ") : `<span class="status-badge upcoming">Normal</span>`;

        return `
          <tr>
            <td>${nameHtml}</td>
            <td>${row.sign}</td>
            <td style="font-family: var(--font-mono);">${row.degree}</td>
            <td>${row.sign_lord}</td>
            <td><span class="status-badge completed">${row.house}</span></td>
            <td>${statusHtml}</td>
          </tr>
        `;
      })
      .join("");
  }
}

function renderDashasWorkspace() {
  const d = state.currentData;
  if (!d) return;

  // Render 120-Year Mahadasha Cards Grid
  const container = document.getElementById("dasha-cards-container");
  if (!container || !d.mahadashas) return;

  container.innerHTML = d.mahadashas
    .map((md, mdIdx) => {
      const glyph = PLANET_GLYPHS[md.lord] || "";
      const statusClass = md.status.toLowerCase();
      const isCardActive = md.status === "ACTIVE";

      const adRows = md.antardashas
        .map((ad, adIdx) => {
          const adGlyph = PLANET_GLYPHS[ad.lord] || "";
          const activeAdClass = ad.is_active ? "active-ad" : "";
          const adBadge = ad.is_active
            ? `<span class="status-badge active">Active</span>`
            : (ad.status === "COMPLETED" ? `<span class="status-badge completed">Done</span>` : `<span class="status-badge upcoming">Next</span>`);

          const subPeriods = ad.pratyantardashas || [];
          const subCount = subPeriods.length;
          const pdRows = subCount > 0
            ? subPeriods.map((pd) => {
                const pdGlyph = PLANET_GLYPHS[pd.lord] || "";
                const activePdClass = pd.is_active ? "active-pd" : "";
                const pdBadge = pd.is_active
                  ? `<span class="status-badge active" style="font-size: 0.6rem; padding: 0.1rem 0.35rem;">Active</span>`
                  : (pd.status === "COMPLETED" ? `<span class="status-badge completed" style="font-size: 0.6rem; padding: 0.1rem 0.35rem;">Done</span>` : `<span class="status-badge upcoming" style="font-size: 0.6rem; padding: 0.1rem 0.35rem;">Next</span>`);

                return `
                  <tr class="${activePdClass}">
                    <td><strong style="color: var(--accent-primary); margin-right: 0.3rem;">${pdGlyph}</strong> ${pd.lord}</td>
                    <td style="font-family: var(--font-mono); font-size: 0.68rem; color: var(--text-secondary);">${pd.start} → ${pd.end}</td>
                    <td style="font-size: 0.68rem; color: var(--text-muted); text-align: center;">${pd.duration}</td>
                    <td>${pdBadge}</td>
                  </tr>
                `;
              }).join("")
            : `<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 0.5rem; font-size: 0.72rem;">No sub-periods recorded for this interval.</td></tr>`;

          const isAdActive = ad.is_active;

          return `
            <tr class="${activeAdClass} ad-clickable-row" onclick="togglePratyantardashaRow(${mdIdx}, ${adIdx})" title="Click to view/hide Pratyantardashas">
              <td>
                <span class="pd-toggle-icon" id="pd-icon-${mdIdx}-${adIdx}">${isAdActive ? '▾' : '▸'}</span>
                <strong>${adGlyph}</strong> ${ad.lord}
              </td>
              <td class="ad-dates-cell">${ad.start} → ${ad.end}</td>
              <td>${ad.duration}</td>
              <td>${adBadge}</td>
            </tr>
            <tr id="pd-panel-${mdIdx}-${adIdx}" class="pd-panel-row" style="display: ${isAdActive ? 'table-row' : 'none'};">
              <td colspan="4">
                <div style="padding: 0.5rem 0.6rem;">
                  <div style="font-size: 0.68rem; font-weight: 700; color: var(--accent-primary); text-transform: uppercase; margin-bottom: 0.35rem; display: flex; justify-content: space-between;">
                    <span>✦ ${md.lord}-${ad.lord} Pratyantar Dashas</span>
                    <span style="color: var(--text-muted); font-weight: 500;">${subCount} Sub-Periods</span>
                  </div>
                  <table class="pd-nested-table">
                    <tbody>
                      ${pdRows}
                    </tbody>
                  </table>
                </div>
              </td>
            </tr>
          `;
        })
        .join("");

      return `
        <div class="mahadasha-card ${isCardActive ? "active-md expanded" : ""}" id="md-card-${mdIdx}">
          <div class="md-card-top">
            <div class="md-header-row">
              <span class="md-lord-name"><strong style="color: var(--accent-primary);">${glyph}</strong> ${md.lord}</span>
              <span class="status-badge ${statusClass}">${md.status}</span>
            </div>
            <div class="md-dates-row">
              ${md.start} → ${md.end}
            </div>
            <div class="md-duration">
              Duration: ${md.duration}
            </div>
          </div>
          <button class="md-toggle-btn" onclick="toggleMahadashaCard(${mdIdx})">
            <span>View Antardashas &amp; Pratyantardashas</span>
            <span class="caret">▼</span>
          </button>
          <div class="antardasha-panel">
            <table class="ad-table">
              <tbody>
                ${adRows}
              </tbody>
            </table>
          </div>
        </div>
      `;
    })
    .join("");
}

function toggleMahadashaCard(idx) {
  const card = document.getElementById(`md-card-${idx}`);
  if (card) {
    card.classList.toggle("expanded");
  }
}

function togglePratyantardashaRow(mdIdx, adIdx) {
  const panel = document.getElementById(`pd-panel-${mdIdx}-${adIdx}`);
  const icon = document.getElementById(`pd-icon-${mdIdx}-${adIdx}`);
  if (panel) {
    const isHidden = panel.style.display === "none" || (panel.style.display === "" && window.getComputedStyle(panel).display === "none");
    panel.style.display = isHidden ? "table-row" : "none";
    if (icon) {
      icon.textContent = isHidden ? "▾" : "▸";
    }
  }
}

// Bind to window so inline onclick handlers in table HTML reliably resolve
window.toggleMahadashaCard = toggleMahadashaCard;
window.togglePratyantardashaRow = togglePratyantardashaRow;

function renderKPWorkspace() {
  const d = state.currentData;
  if (!d) return;

  // 12 Placidus Cusps
  const cuspsTbody = document.getElementById("cusps-table-body");
  if (cuspsTbody && d.cusps_table) {
    cuspsTbody.innerHTML = d.cusps_table
      .map((c) => `
        <tr>
          <td><strong>${c.house}</strong></td>
          <td>${c.sign}</td>
          <td style="font-family: var(--font-mono);">${c.degree}</td>
          <td>${c.star_lord}</td>
          <td><strong>${c.sub_lord}</strong></td>
          <td>${c.sub_sub_lord}</td>
          <td style="font-family: var(--font-mono);">${c.sig_a}</td>
          <td style="font-family: var(--font-mono);">${c.sig_b}</td>
          <td style="font-family: var(--font-mono);">${c.sig_c}</td>
          <td style="font-family: var(--font-mono);">${c.sig_d}</td>
        </tr>
      `)
      .join("");
  }

  // Planetary 4-Fold Significators
  const kpPlanetsTbody = document.getElementById("kp-planets-table-body");
  if (kpPlanetsTbody && d.planets_table) {
    kpPlanetsTbody.innerHTML = d.planets_table
      .map((p) => {
        const glyph = PLANET_GLYPHS[p.planet] || "";
        return `
          <tr>
            <td><strong style="color: var(--accent-primary); margin-right: 0.4rem;">${glyph}</strong> ${p.planet}</td>
            <td>${p.sign}</td>
            <td>${p.star_lord}</td>
            <td><strong>${p.sub_lord}</strong></td>
            <td style="font-family: var(--font-mono);">${p.sig_a}</td>
            <td style="font-family: var(--font-mono);">${p.sig_b}</td>
            <td style="font-family: var(--font-mono);">${p.sig_c}</td>
            <td style="font-family: var(--font-mono);">${p.sig_d}</td>
          </tr>
        `;
      })
      .join("");
  }
}

function renderJaiminiWorkspace() {
  const d = state.currentData;
  if (!d) return;

  // 7 Chara Karakas
  const karakasTbody = document.getElementById("karakas-table-body");
  if (karakasTbody && d.chara_karakas_7) {
    karakasTbody.innerHTML = d.chara_karakas_7
      .map((k) => {
        const glyph = PLANET_GLYPHS[k.planet] || "";
        const desc = KARAKA_DESCRIPTIONS[k.code] || k.role;
        return `
          <tr>
            <td><span class="status-badge active" style="font-family: var(--font-mono);">${k.code}</span></td>
            <td><strong>${k.role}</strong></td>
            <td style="color: var(--text-secondary);">${desc}</td>
            <td><strong style="color: var(--accent-primary); margin-right: 0.3rem;">${glyph}</strong> ${k.planet}</td>
            <td>${k.sign}</td>
            <td style="font-family: var(--font-mono);">${k.degree}</td>
          </tr>
        `;
      })
      .join("");
  }

  // 12 Arudha Padas
  const arudhaContainer = document.getElementById("arudha-grid-container");
  if (arudhaContainer && d.arudha_padas) {
    arudhaContainer.innerHTML = d.arudha_padas
      .map((ap) => {
        const isSpecial = ap.is_special;
        const shiftBadge = ap.exception !== "Standard"
          ? `<span class="status-badge active" style="margin-left: auto;">${ap.exception}</span>`
          : "";

        return `
          <div class="arudha-card ${isSpecial ? "special" : ""}">
            <div style="display: flex; align-items: center;">
              <span class="arudha-pada-name">${ap.pada_name}</span>
              ${shiftBadge}
            </div>
            <span class="arudha-sign">${ap.sign}</span>
            <span style="font-size: 0.8rem; color: var(--text-muted);">${ap.house}</span>
          </div>
        `;
      })
      .join("");
  }
}

function renderYogasOverviewStrip() {
  const d = state.currentData;
  const el = document.getElementById("strip-yogas-summary");
  if (!el || !d || !d.yogas_summary) return;
  const s = d.yogas_summary;
  const totalRaja = (s.raja_count || 0) + (s.mahapurusha_count || 0);
  el.innerHTML = `<strong>${s.total_yogas}</strong> Formations Active &bull; <strong>${totalRaja}</strong> Raja/Mahapurusha &bull; <strong>${s.dhana_count}</strong> Dhana &bull; Sade Sati: <strong>${s.sade_sati_status}</strong> &bull; Kuja: <strong>${s.kuja_dosha_status}</strong>`;
}

function renderYogasWorkspace() {
  const d = state.currentData;
  if (!d) return;

  const s = d.yogas_summary;
  if (s) {
    const totalEl = document.getElementById("stat-total-yogas");
    if (totalEl) totalEl.textContent = s.total_yogas;

    const rajaEl = document.getElementById("stat-raja-yogas");
    if (rajaEl) rajaEl.textContent = (s.raja_count || 0) + (s.mahapurusha_count || 0);

    const dhanaEl = document.getElementById("stat-dhana-yogas");
    if (dhanaEl) dhanaEl.textContent = s.dhana_count;

    const doshasEl = document.getElementById("stat-doshas");
    if (doshasEl) doshasEl.textContent = s.doshas_count;

    const sadeEl = document.getElementById("stat-sade-sati");
    if (sadeEl) {
      sadeEl.textContent = s.sade_sati_status;
      if (s.sade_sati_status.includes("Rising") || s.sade_sati_status.includes("Peak") || s.sade_sati_status.includes("Setting") || s.sade_sati_status.includes("Dhaiya") || s.sade_sati_status.includes("Phase")) {
        sadeEl.style.color = "#E05638";
      } else if (s.sade_sati_status.includes("Inactive") || s.sade_sati_status.includes("Clear")) {
        sadeEl.style.color = "var(--accent-primary)";
      } else {
        sadeEl.style.color = "var(--text-primary)";
      }
    }

    const kujaEl = document.getElementById("stat-kuja-dosha");
    if (kujaEl) {
      kujaEl.textContent = s.kuja_dosha_status;
      if (s.kuja_dosha_status.includes("Active")) {
        kujaEl.style.color = "#E05638";
      } else if (s.kuja_dosha_status.includes("Cancelled")) {
        kujaEl.style.color = "var(--accent-primary)";
      } else {
        kujaEl.style.color = "var(--text-primary)";
      }
    }
  }

  const container = document.getElementById("yogas-cards-container");
  if (!container || !d.yogas_list) return;

  const filter = state.active_yoga_filter || "all";
  const list = d.yogas_list.filter((y) => {
    if (filter === "all") return true;
    if (filter === "Raja") return y.nature === "Raja" || y.category === "Raja";
    if (filter === "Mahapurusha") return y.nature === "Mahapurusha" || y.category === "Mahapurusha";
    if (filter === "Dhana") return y.nature === "Dhana" || y.category === "Dhana";
    if (filter === "Auspicious") return y.nature === "Auspicious" || y.category === "Solar" || y.category === "Lunar" || y.category === "Auspicious";
    if (filter === "Dosha") return y.nature === "Dosha" || y.category === "Dosha" || y.id === "sade_sati";
    return true;
  });

  if (list.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
        <p style="font-size: 1.1rem; font-weight: 600;">No formations found under this filter</p>
        <p style="font-size: 0.85rem; margin-top: 0.35rem;">Select "All Formations" to view all evaluated classical yogas and doshas.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = list
    .map((y) => {
      const natureLower = (y.nature || "neutral").toLowerCase();
      let cardClass = y.is_cancelled ? "cancelled" : natureLower;
      let badgeClass = y.is_cancelled ? "cancelled" : natureLower;
      let badgeText = y.is_cancelled ? "Cancelled (Apavada)" : `${y.nature} (${y.intensity})`;

      if (y.id === "sade_sati") {
        if (!y.is_active || y.is_cancelled) {
          badgeText = "Inactive (Clear)";
          badgeClass = "auspicious";
          cardClass = "cancelled";
        } else {
          badgeText = `Dosha (${y.intensity})`;
          badgeClass = "dosha";
          cardClass = "dosha";
        }
      }

      // Participating planets formatted
      const planetsHtml = (y.planets_involved || []).map((p) => {
        const glyph = PLANET_GLYPHS[p] || "✧";
        return `<span class="yoga-tag">${glyph} ${p}</span>`;
      }).join("");

      // Participating houses formatted
      const housesHtml = (y.houses_involved || []).map((h) => {
        return `<span class="yoga-tag">House ${h}</span>`;
      }).join("");

      // Cancellation callout
      const cancellationHtml = (y.is_cancelled && y.cancellation_reason)
        ? `<div class="cancellation-callout">
             ${y.id === "sade_sati" ? "✨" : "🛡️"} <strong>${y.id === "sade_sati" ? "Transit Assessment" : "Apavada (Cancellation)"}:</strong> ${y.cancellation_reason}
           </div>`
        : "";

      return `
        <div class="yoga-card ${cardClass}">
          <div class="yoga-card-header">
            <div class="yoga-title-wrap">
              <span class="yoga-title">${y.name}</span>
              <span class="yoga-sanskrit">${y.sanskrit_name} &bull; ${y.category}</span>
            </div>
            <span class="yoga-nature-badge ${badgeClass}">${badgeText}</span>
          </div>

          <div class="yoga-meta-row">
            ${planetsHtml}
            ${housesHtml}
          </div>

          <p class="yoga-description">${y.description}</p>

          <div class="yoga-effects">
            <strong>Classical BPHS Phala:</strong> ${y.classical_effects}
          </div>

          ${cancellationHtml}
        </div>
      `;
    })
    .join("");
}

function renderAshtakavargaWorkspace() {
  const d = state.currentData;
  if (!d || !d.ashtakavarga) return;

  const av = d.ashtakavarga;
  const s = av.summary;

  // 1. Update Summary Metrics
  const totalEl = document.getElementById("av-stat-total");
  if (totalEl) totalEl.textContent = s.total_bindus;

  const avgEl = document.getElementById("av-stat-avg");
  if (avgEl) avgEl.textContent = s.average_bindus_per_sign.toFixed(1);

  const strSignEl = document.getElementById("av-stat-strongest-sign");
  if (strSignEl) strSignEl.textContent = `${s.strongest_sign} (${s.strongest_sign_bindus})`;

  const weakSignEl = document.getElementById("av-stat-weakest-sign");
  if (weakSignEl) weakSignEl.textContent = `${s.weakest_sign} (${s.weakest_sign_bindus})`;

  const strHouseEl = document.getElementById("av-stat-strongest-house");
  if (strHouseEl) strHouseEl.textContent = `House ${s.strongest_house} (${s.strongest_house_bindus}b)`;

  const benefEl = document.getElementById("av-stat-benefic-count");
  if (benefEl) benefEl.textContent = `${s.benefic_signs_count} / 12 (${Math.round((s.benefic_signs_count / 12) * 100)}%)`;

  // 1b. Render Sarvashtakavarga (SAV) Visual Kundali SVG
  const svgContainer = document.getElementById("sav-chart-svg");
  if (svgContainer && d.sav_chart_svg) {
    svgContainer.innerHTML = d.sav_chart_svg;
  }

  // 1c. Update SAV Chart Subtitle with Lagna Degree, Kaksha & Scrubber Offset
  const savSubEl = document.getElementById("sav-chart-subtitle");
  if (savSubEl && d.summary && d.summary.ascendant) {
    const offStr = state.time_offset_seconds !== 0 ? ` • Offset: ${state.time_offset_seconds > 0 ? "+" : ""}${state.time_offset_seconds}s` : "";
    const kLordStr = av.lagna_kaksha ? ` • Kaksha ${av.lagna_kaksha.active_kaksha_number} (${av.lagna_kaksha.active_kaksha_lord_sanskrit})` : "";
    savSubEl.textContent = `Ascendant (Lagna): ${d.summary.ascendant.sign} ${d.summary.ascendant.degree}${kLordStr}${offStr}`;
  }

  // 1d. Render Prastarashtakavarga Lagna Kaksha & Rectification Monitor
  if (av.lagna_kaksha) {
    const lk = av.lagna_kaksha;
    // Active badge in header
    const badgeContainer = document.getElementById("kaksha-active-badge-container");
    if (badgeContainer) {
      badgeContainer.innerHTML = `
        <div class="action-pill" style="cursor: default; border-color: var(--accent-primary); background: var(--accent-subtle); color: var(--accent-text); font-weight: 700;">
          ✦ Active Kaksha ${lk.active_kaksha_number}/8: ${lk.active_kaksha_lord} (${lk.active_kaksha_lord_sanskrit}) • ${lk.active_kaksha_range} • ${lk.active_kaksha_bindus}/7 Bindus
        </div>
      `;
    }

    // Progress labels & bar
    const degLabel = document.getElementById("kaksha-progress-deg-label");
    if (degLabel) {
      degLabel.textContent = `Lagna: ${lk.lagna_sign_name} ${lk.lagna_degree_formatted} (Kaksha ${lk.active_kaksha_number} • ${lk.kaksha_progress_pct}% elapsed)`;
    }

    const barFill = document.getElementById("kaksha-bar-fill");
    if (barFill) {
      const totalSignPct = Math.min(100, Math.max(0, (lk.intra_sign_degree / 30.0) * 100.0));
      barFill.style.width = `${totalSignPct.toFixed(1)}%`;
    }

    // 8 Kakshas Grid
    const gridEl = document.getElementById("kaksha-grid");
    if (gridEl && lk.kakshas) {
      gridEl.innerHTML = lk.kakshas.map((k) => {
        const glyph = PLANET_GLYPHS[k.lord] || (k.lord === "Lagna" ? "✧" : "");
        const activeIndicator = k.is_current ? '<span class="kaksha-active-indicator">ACTIVE</span>' : '';
        const contribTooltip = k.contributed_planets.length > 0
          ? `Contributed to: ${k.contributed_planets.join(", ")}`
          : "No bindu contributed in this sign";
        return `
          <div class="kaksha-cell ${k.is_current ? "active" : ""}">
            ${activeIndicator}
            <span class="kaksha-num-badge">Kaksha ${k.kaksha_number}</span>
            <span class="kaksha-lord-name">${glyph} ${k.lord}</span>
            <span class="kaksha-lord-sanskrit">(${k.lord_sanskrit})</span>
            <span class="kaksha-range">${k.range_str}</span>
            <span class="kaksha-bindu-pill" title="${contribTooltip}">
              <span>✦</span> ${k.bindu_contributions_count}/7 Grahas
            </span>
          </div>
        `;
      }).join("");
    }
  }

  // 2. Render Master SAV Matrix Table
  const headerRow = document.getElementById("sav-matrix-header-row");
  const matrixBody = document.getElementById("sav-matrix-body");

  if (headerRow && matrixBody && av.sarvashtakavarga) {
    // Header row: Graha | 12 signs | Total
    headerRow.innerHTML = `
      <th style="min-width: 110px;">Graha</th>
      ${av.sarvashtakavarga
        .map(
          (sd) => `
        <th style="min-width: 60px;">
          <div>${sd.sign_name}</div>
          <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 500;">H${sd.house_from_lagna}</div>
        </th>
      `
        )
        .join("")}
      <th style="min-width: 65px;">Total</th>
    `;

    // 7 Planet Rows
    const grahas = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"];
    let rowsHtml = grahas
      .map((pName) => {
        const pReport = av.bhinna[pName];
        if (!pReport) return "";
        const glyph = PLANET_GLYPHS[pName] || "";
        const cellsHtml = pReport.signs
          .map((sd) => {
            const b = sd.raw_bindus;
            let cls = "avg";
            if (b >= 5) cls = "high";
            else if (b <= 2) cls = "low";
            return `<td class="bindu-cell ${cls}">${b}</td>`;
          })
          .join("");

        return `
          <tr>
            <td><strong>${glyph} ${pName}</strong></td>
            ${cellsHtml}
            <td style="font-weight: 700; font-family: var(--font-mono);">${pReport.total_raw_bindus}</td>
          </tr>
        `;
      })
      .join("");

    // Total SAV Row
    const totalCellsHtml = av.sarvashtakavarga
      .map((sd) => {
        const tot = sd.total_bindus;
        let cls = "avg";
        if (tot >= 30) cls = "high";
        else if (tot < 26) cls = "low";
        return `<td class="bindu-cell ${cls}" style="font-weight: 700; font-size: 0.95rem;">${tot}</td>`;
      })
      .join("");

    rowsHtml += `
      <tr class="sav-total-row">
        <td><strong>SAV Total</strong></td>
        ${totalCellsHtml}
        <td style="font-size: 1.05rem; font-weight: 800; font-family: var(--font-serif); color: var(--accent-primary);">${s.total_bindus}</td>
      </tr>
    `;

    matrixBody.innerHTML = rowsHtml;
  }

  // 3. Render Selected Planet BAV & Shodhana
  const selectedPlanet = state.selected_bav_planet || "Jupiter";
  const pData = av.bhinna[selectedPlanet];
  if (!pData) return;

  // Shodya Pinda Strip
  const pindaStrip = document.getElementById("bav-pinda-strip");
  if (pindaStrip) {
    pindaStrip.innerHTML = `
      <div class="pinda-stat-item">
        <span class="pinda-stat-val">${pData.total_raw_bindus}</span>
        <span class="pinda-stat-label">Raw Bindus Total</span>
      </div>
      <div class="pinda-stat-item">
        <span class="pinda-stat-val">${pData.total_trikona_reduced}</span>
        <span class="pinda-stat-label">Trikona Reduced Total</span>
      </div>
      <div class="pinda-stat-item">
        <span class="pinda-stat-val">${pData.total_ekadhipatya_reduced}</span>
        <span class="pinda-stat-label">Ekadhipatya Reduced</span>
      </div>
      <div class="pinda-stat-item">
        <span class="pinda-stat-val">${pData.rashi_pinda}</span>
        <span class="pinda-stat-label">Rashi Pinda</span>
      </div>
      <div class="pinda-stat-item">
        <span class="pinda-stat-val">${pData.graha_pinda}</span>
        <span class="pinda-stat-label">Graha Pinda</span>
      </div>
      <div class="pinda-stat-item">
        <span class="pinda-stat-val highlight">${pData.yoga_pinda}</span>
        <span class="pinda-stat-label">Yoga Pinda (Shodya Pinda)</span>
      </div>
    `;
  }

  // 12 Signs BAV Reduction Table
  const bavBody = document.getElementById("bav-signs-table-body");
  if (bavBody && pData.signs) {
    bavBody.innerHTML = pData.signs
      .map((sd) => {
        // Sources breakdown chips
        const sourcesOrder = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"];
        const chipsHtml = sourcesOrder
          .map((src) => {
            const hasBindu = sd.contributions[src] === 1;
            const shortName = src.substring(0, 2);
            return `<span class="contrib-chip ${hasBindu ? "active" : ""}" title="${src}: ${hasBindu ? "Contributed 1 bindu" : "0 bindus"}">${shortName}:${hasBindu ? "1" : "0"}</span>`;
          })
          .join("");

        return `
          <tr>
            <td><strong>${sd.sign_name}</strong> <span style="font-size: 0.75rem; color: var(--text-muted);">(${sd.sign_sanskrit})</span></td>
            <td>House ${sd.house_from_lagna}</td>
            <td style="font-family: var(--font-mono); font-weight: 700;">${sd.raw_bindus}</td>
            <td style="font-family: var(--font-mono);">${sd.trikona_reduced}</td>
            <td style="font-family: var(--font-mono); font-weight: 700; color: var(--accent-primary);">${sd.ekadhipatya_reduced}</td>
            <td><div class="contributor-chips-row">${chipsHtml}</div></td>
          </tr>
        `;
      })
      .join("");
  }
}

// =============================================================================
// Slide-Over Drawer Controller
// =============================================================================

function openPlanetDrawer(planetName) {
  const d = state.currentData;
  if (!d || !d.planet_details) return;

  const p = d.planet_details[planetName];
  if (!p) return;

  document.getElementById("drawer-planet-glyph").textContent = PLANET_GLYPHS[p.planet] || "✧";
  document.getElementById("drawer-planet-name").textContent = p.planet;
  document.getElementById("drawer-planet-pos").textContent = `${p.sign} ${p.degree}`;

  // Vargottama Dignity Status & Navamsha (D9) Sign
  const vBadge = document.getElementById("drawer-vargottama-badge");
  const vBox = document.getElementById("box-vargottama");
  const vVal = document.getElementById("drawer-vargottama");
  const d9Val = document.getElementById("drawer-d9-sign");

  if (vBadge) {
    if (p.is_vargottama) {
      vBadge.style.display = "inline-flex";
      vBadge.textContent = "✦ Vargottama";
    } else {
      vBadge.style.display = "none";
    }
  }

  if (vBox) {
    if (p.is_vargottama) {
      vBox.style.borderColor = "var(--accent-primary)";
      vBox.style.backgroundColor = "var(--accent-subtle)";
    } else {
      vBox.style.borderColor = "var(--border-subtle)";
      vBox.style.backgroundColor = "var(--bg-surface-elevated)";
    }
  }

  if (vVal) {
    if (p.is_vargottama) {
      vVal.textContent = `Yes (${p.sign})`;
      vVal.style.color = "var(--accent-primary)";
      vVal.style.fontWeight = "700";
    } else {
      vVal.textContent = `No (D9: ${p.d9_sign || "-"})`;
      vVal.style.color = "var(--text-secondary)";
      vVal.style.fontWeight = "500";
    }
  }

  if (d9Val) {
    d9Val.textContent = p.d9_sign ? `${p.d9_sign} ${p.d9_degree || ""}` : "-";
  }

  document.getElementById("drawer-speed").textContent = p.speed;
  document.getElementById("drawer-motion").textContent = p.is_retro ? "Retrograde (Vakri)" : "Direct (Marga)";
  document.getElementById("drawer-combust").textContent = p.is_combust ? "Combust (Astangata)" : "Clear";
  document.getElementById("drawer-nakshatra").textContent = p.nakshatra;

  document.getElementById("drawer-star-lord").textContent = p.star_lord;
  document.getElementById("drawer-sub-lord").textContent = p.sub_lord;
  document.getElementById("drawer-sub-sub-lord").textContent = p.sub_sub_lord;
  document.getElementById("drawer-karaka").textContent = p.karaka_role;

  document.getElementById("drawer-sig-a").textContent = p.sig_a;
  document.getElementById("drawer-sig-b").textContent = p.sig_b;
  document.getElementById("drawer-sig-c").textContent = p.sig_c;
  document.getElementById("drawer-sig-d").textContent = p.sig_d;

  // Parashari Graha Drishti (Aspects)
  const castContainer = document.getElementById("drawer-aspects-cast");
  const receivedContainer = document.getElementById("drawer-aspects-received");
  const mutualContainer = document.getElementById("drawer-mutual-conjunctions");

  if (castContainer) {
    if (p.aspects_cast && p.aspects_cast.length > 0) {
      castContainer.innerHTML = p.aspects_cast.map(c => {
        const targetGrahas = (c.aspected_planets && c.aspected_planets.length > 0)
          ? ` ➔ Aspecting: <strong>${c.aspected_planets.join(", ")}</strong>`
          : `<span style="color: var(--text-muted);"> (Vacant)</span>`;
        return `
          <div style="font-size: 0.825rem;">
            <strong style="color: var(--accent-primary);">House ${c.target_house} (${c.target_sign_name})</strong>
            via ${c.aspect_type}${targetGrahas}
          </div>
        `;
      }).join("");
    } else {
      castContainer.innerHTML = `<span style="color: var(--text-muted); font-size: 0.825rem;">No aspects cast (Lagna/Reference point)</span>`;
    }
  }

  if (receivedContainer) {
    if (p.aspects_received && p.aspects_received.length > 0) {
      receivedContainer.innerHTML = p.aspects_received.map(r => `
        <span class="bhava-aspect-tag ${r.is_benefic ? 'benefic' : 'malefic'}" style="font-size: 0.775rem;">
          ${r.from_planet} (${r.aspect_type})
        </span>
      `).join("");
    } else {
      receivedContainer.innerHTML = `<span style="color: var(--text-muted); font-size: 0.825rem;">None (Free from direct Graha Drishti)</span>`;
    }
  }

  if (mutualContainer) {
    let mcHtml = "";
    if (p.mutual_aspects && p.mutual_aspects.length > 0) {
      mcHtml += `<div><strong>Mutual Aspects with:</strong> ${p.mutual_aspects.join(", ")}</div>`;
    }
    if (p.conjunctions && p.conjunctions.length > 0) {
      mcHtml += `<div style="margin-top: 0.25rem;"><strong>Conjunct with:</strong> ${p.conjunctions.join(", ")}</div>`;
    }
    if (!mcHtml) {
      mcHtml = `<span style="color: var(--text-muted);">No mutual aspects or conjunctions.</span>`;
    }
    mutualContainer.innerHTML = mcHtml;
  }

  document.getElementById("drawer-backdrop").classList.add("open");
}

function closePlanetDrawer() {
  document.getElementById("drawer-backdrop").classList.remove("open");
}

// =============================================================================
// Planetary Aspects & Visual Rays Controller
// =============================================================================

function togglePlanetAspectRays(planetName, event) {
  if (event) event.stopPropagation();

  if (state.activeRayPlanet === planetName) {
    clearAspectRays();
  } else {
    renderAspectRays(planetName);
  }
}

function clearAspectRays() {
  state.activeRayPlanet = null;
  const svg = document.querySelector("#main-chart-svg svg");
  if (svg) {
    const layer = svg.querySelector("#aspect-rays-layer");
    if (layer) layer.remove();
  }
  const clearBtn = document.getElementById("clear-rays-btn");
  if (clearBtn) clearBtn.style.display = "none";

  document.querySelectorAll(".aspect-rays-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll("#overview-planets-table-body tr").forEach(tr => tr.classList.remove("active-ray-row"));
}

function renderAspectRays(planetName) {
  const d = state.currentData;
  if (!d || !d.aspects || !d.aspects.planets_aspects) return;
  const pAspect = d.aspects.planets_aspects[planetName];
  if (!pAspect) return;

  const svg = document.querySelector("#main-chart-svg svg");
  if (!svg) return;

  state.activeRayPlanet = planetName;

  // Remove existing rays layer
  const oldLayer = svg.querySelector("#aspect-rays-layer");
  if (oldLayer) oldLayer.remove();

  const isDark = (state.theme_mode === "dark");
  const rayColor = isDark ? pAspect.ray_color_dark : pAspect.ray_color_light;
  const themeBg = isDark ? "#1C1917" : "#FAF8F5";

  // Ascendant sign ID for South Indian calculations
  const ascSignId = d.planets_table.find(p => p.planet.includes("Ascendant"))?.sign_id || 1;

  const layer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  layer.setAttribute("id", "aspect-rays-layer");

  const markerId = `ray-head-${planetName.toLowerCase()}`;
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.innerHTML = `
    <marker id="${markerId}" markerWidth="8" markerHeight="8" refX="6.5" refY="4" orient="auto">
      <polygon points="0 1, 8 4, 0 7, 2 4" fill="${rayColor}" />
    </marker>
  `;
  layer.appendChild(defs);

  // Source coordinates
  let x1, y1;
  const srcHouse = pAspect.natal_house;
  if (state.chart_style === "north") {
    const sc = NORTH_HOUSE_CENTERS[srcHouse] || { x: 400, y: 400 };
    x1 = sc.x;
    y1 = sc.y;
  } else {
    const srcSignId = ((ascSignId - 1 + srcHouse - 1) % 12) + 1;
    const grid = SOUTH_SIGN_GRID[srcSignId] || { col: 0, row: 0 };
    x1 = grid.col * 200 + 100;
    y1 = grid.row * 200 + 100;
  }

  // Draw rays and target highlights for each cast
  pAspect.aspects_cast.forEach(cast => {
    let x2, y2, col, row;
    const tgtHouse = cast.target_house;
    if (state.chart_style === "north") {
      const tc = NORTH_HOUSE_CENTERS[tgtHouse] || { x: 400, y: 400 };
      x2 = tc.x;
      y2 = tc.y;
      // Target glow circle
      const glow = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      glow.setAttribute("cx", x2);
      glow.setAttribute("cy", y2);
      glow.setAttribute("r", "50");
      glow.setAttribute("fill", rayColor);
      glow.setAttribute("fill-opacity", "0.10");
      glow.setAttribute("stroke", rayColor);
      glow.setAttribute("stroke-width", "2.5");
      glow.setAttribute("class", "aspect-target-glow");
      layer.appendChild(glow);
    } else {
      const tgtSignId = ((ascSignId - 1 + tgtHouse - 1) % 12) + 1;
      const grid = SOUTH_SIGN_GRID[tgtSignId] || { col: 0, row: 0 };
      col = grid.col;
      row = grid.row;
      x2 = col * 200 + 100;
      y2 = row * 200 + 100;
      // Target glow rect
      const glow = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      glow.setAttribute("x", col * 200 + 8);
      glow.setAttribute("y", row * 200 + 8);
      glow.setAttribute("width", "184");
      glow.setAttribute("height", "184");
      glow.setAttribute("rx", "4");
      glow.setAttribute("fill", rayColor);
      glow.setAttribute("fill-opacity", "0.08");
      glow.setAttribute("stroke", rayColor);
      glow.setAttribute("stroke-width", "2.5");
      glow.setAttribute("class", "aspect-target-glow");
      layer.appendChild(glow);
    }

    // Gentle curve avoiding straight intersection
    const dx = x2 - x1;
    const dy = y2 - y1;
    const dist = Math.hypot(dx, dy);
    const normX = dist > 0 ? -dy / dist : 0;
    const normY = dist > 0 ? dx / dist : 0;
    const curveOffset = (dist > 350) ? 28 : 14;
    const cx = (x1 + x2) / 2 + normX * curveOffset;
    const cy = (y1 + y2) / 2 + normY * curveOffset;

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`);
    path.setAttribute("stroke", rayColor);
    path.setAttribute("stroke-width", "2.5");
    path.setAttribute("fill", "none");
    path.setAttribute("class", "aspect-ray-path");
    path.setAttribute("marker-end", `url(#${markerId})`);
    path.setAttribute("opacity", "0.9");
    layer.appendChild(path);

    // Aspect label badge along the curve (t = 0.65)
    const t = 0.65;
    const lx = (1 - t) * (1 - t) * x1 + 2 * (1 - t) * t * cx + t * t * x2;
    const ly = (1 - t) * (1 - t) * y1 + 2 * (1 - t) * t * cy + t * t * y2;
    const badgeLabel = cast.aspect_type.replace(" (100%)", "").replace(" (Vishesha)", " (V)");

    const badgeG = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", lx - 32);
    rect.setAttribute("y", ly - 10);
    rect.setAttribute("width", "64");
    rect.setAttribute("height", "20");
    rect.setAttribute("rx", "5");
    rect.setAttribute("fill", themeBg);
    rect.setAttribute("stroke", rayColor);
    rect.setAttribute("stroke-width", "1.2");
    rect.setAttribute("opacity", "0.95");
    badgeG.appendChild(rect);

    const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
    txt.setAttribute("x", lx);
    txt.setAttribute("y", ly + 4);
    txt.setAttribute("text-anchor", "middle");
    txt.setAttribute("font-size", "9.5");
    txt.setAttribute("font-family", "'JetBrains Mono', monospace");
    txt.setAttribute("font-weight", "700");
    txt.setAttribute("fill", rayColor);
    txt.textContent = badgeLabel;
    badgeG.appendChild(txt);

    layer.appendChild(badgeG);
  });

  svg.appendChild(layer);

  // Update button and row styles
  const clearBtn = document.getElementById("clear-rays-btn");
  if (clearBtn) {
    clearBtn.style.display = "inline-flex";
    const lbl = document.getElementById("active-rays-planet-label");
    if (lbl) lbl.textContent = planetName;
  }

  document.querySelectorAll(".aspect-rays-btn").forEach(btn => {
    btn.classList.toggle("active", btn.id === `rays-btn-${planetName}`);
  });

  document.querySelectorAll("#overview-planets-table-body tr").forEach(tr => {
    tr.classList.toggle("active-ray-row", tr.id === `planet-row-${planetName.replace(/[^a-zA-Z0-9]/g, '')}`);
  });
}

function renderBhavaAspectsWorkspace() {
  const d = state.currentData;
  if (!d || !d.aspects) return;

  const card = document.getElementById("bhava-aspects-card");
  if (!card) return;

  // 1. Mutual Aspects & Conjunctions Banner
  const stripEl = document.getElementById("mutual-aspects-strip");
  if (stripEl) {
    const mutuals = d.aspects.mutual_aspects || [];
    const conjuncts = d.aspects.conjunctions || [];

    let mutualHtml = "";
    if (mutuals.length > 0) {
      mutualHtml += `
        <span style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Mutual Drishti:</span>
        ${mutuals.map(m => `
          <span class="mutual-aspect-pill" title="Planets in reciprocal aspect">
            ✦ ${m.planet1} ↔ ${m.planet2} (${m.relation})
          </span>
        `).join("")}
      `;
    }

    let conjHtml = "";
    if (conjuncts.length > 0) {
      conjHtml += `
        <span style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-left: ${mutuals.length ? '1rem' : '0'};">Conjunctions (Yuti):</span>
        ${conjuncts.map(c => `
          <span class="mutual-aspect-pill" style="background: rgba(5, 150, 105, 0.08); border-color: rgba(5, 150, 105, 0.25); color: #059669;" title="Multiple planets sharing House ${c.house} (${c.sign})">
            ● House ${c.house} (${c.sign}): <strong>${c.planets.join(' + ')}</strong>
          </span>
        `).join("")}
      `;
    }

    if (!mutualHtml && !conjHtml) {
      stripEl.innerHTML = `<span style="font-size: 0.8rem; color: var(--text-muted);">No major mutual aspects or multi-planet conjunctions in this chart.</span>`;
    } else {
      stripEl.innerHTML = mutualHtml + conjHtml;
    }
  }

  // 2. 12 Bhavas Grid
  const gridEl = document.getElementById("bhava-aspects-grid");
  if (gridEl && d.aspects.bhava_aspects) {
    gridEl.innerHTML = d.aspects.bhava_aspects.map(b => {
      let badgeClass = "bhava-badge-neutral";
      if (b.net_influence.includes("Benefic")) badgeClass = "bhava-badge-benefic";
      else if (b.net_influence.includes("Malefic")) badgeClass = "bhava-badge-malefic";
      else if (b.net_influence.includes("Mixed")) badgeClass = "bhava-badge-mixed";

      const occHtml = b.occupants && b.occupants.length
        ? b.occupants.map(o => `<strong style="color: var(--accent-primary); font-size: 0.8rem;">${o}</strong>`).join(", ")
        : `<span style="color: var(--text-muted); font-size: 0.775rem;">Vacant</span>`;

      const beneficsHtml = b.benefics_aspecting && b.benefics_aspecting.length
        ? b.benefics_aspecting.map(g => `<span class="bhava-aspect-tag benefic">${g}</span>`).join("")
        : "";

      const maleficsHtml = b.malefics_aspecting && b.malefics_aspecting.length
        ? b.malefics_aspecting.map(g => `<span class="bhava-aspect-tag malefic">${g}</span>`).join("")
        : "";

      const aspectsHtml = (beneficsHtml || maleficsHtml)
        ? `<div class="bhava-aspect-list">${beneficsHtml}${maleficsHtml}</div>`
        : `<span style="color: var(--text-muted); font-size: 0.775rem;">No direct planetary aspects</span>`;

      return `
        <div class="bhava-card">
          <div class="bhava-card-header">
            <div>
              <span class="bhava-title">House ${b.house_number}</span>
              <span class="bhava-meta"> • ${b.sign_name} (${b.lord})</span>
            </div>
            <span class="bhava-badge ${badgeClass}">${b.net_influence.split(' ')[0]}</span>
          </div>
          <div style="font-size: 0.8rem; display: flex; align-items: baseline; gap: 0.35rem;">
            <span style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase;">Occupants:</span>
            ${occHtml}
          </div>
          <div>
            <span style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; display: block; margin-bottom: 0.25rem;">Aspects Received:</span>
            ${aspectsHtml}
          </div>
        </div>
      `;
    }).join("");
  }
}

function toggleBhavaAspectsCard() {
  const content = document.getElementById("bhava-aspects-content");
  const icon = document.getElementById("bhava-aspects-toggle-icon");
  if (!content || !icon) return;
  if (content.style.display === "none") {
    content.style.display = "block";
    icon.style.transform = "rotate(0deg)";
  } else {
    content.style.display = "none";
    icon.style.transform = "rotate(-90deg)";
  }
}

window.togglePlanetAspectRays = togglePlanetAspectRays;
window.clearAspectRays = clearAspectRays;
window.toggleBhavaAspectsCard = toggleBhavaAspectsCard;

// =============================================================================
// Modal Dialog Controller
// =============================================================================

function populateDateTimeSelects(prefix) {
  const daySelect = document.getElementById(`select-${prefix}-day`);
  const monthSelect = document.getElementById(`select-${prefix}-month`);
  const yearSelect = document.getElementById(`select-${prefix}-year`);
  const hourSelect = document.getElementById(`select-${prefix}-hour`);
  const minuteSelect = document.getElementById(`select-${prefix}-minute`);
  const secondSelect = document.getElementById(`select-${prefix}-second`);

  if (!daySelect || !monthSelect || !yearSelect || !hourSelect || !minuteSelect || !secondSelect) return;

  // Populate Years (1920 to 2040)
  yearSelect.innerHTML = "";
  for (let y = 1920; y <= 2040; y++) {
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;
    yearSelect.appendChild(opt);
  }

  // Populate Hours (00 to 23 with AM/PM indicator)
  hourSelect.innerHTML = "";
  for (let h = 0; h < 24; h++) {
    const opt = document.createElement("option");
    opt.value = h;
    const padH = String(h).padStart(2, "0");
    const ampm = h >= 12 ? "PM" : "AM";
    const h12 = h % 12 === 0 ? 12 : h % 12;
    opt.textContent = `${padH} (${h12} ${ampm})`;
    hourSelect.appendChild(opt);
  }

  // Populate Minutes (00 to 59)
  minuteSelect.innerHTML = "";
  for (let m = 0; m < 60; m++) {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = String(m).padStart(2, "0");
    minuteSelect.appendChild(opt);
  }

  // Populate Seconds (00 to 59)
  secondSelect.innerHTML = "";
  for (let s = 0; s < 60; s++) {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = String(s).padStart(2, "0");
    secondSelect.appendChild(opt);
  }

  // Dynamic Days helper based on month & year
  function updateDaysOptions(keepSelected = true) {
    const currentYear = parseInt(yearSelect.value, 10) || 1995;
    const currentMonth = parseInt(monthSelect.value, 10) || 10;
    const prevDay = parseInt(daySelect.value, 10) || 15;
    const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();

    daySelect.innerHTML = "";
    for (let d = 1; d <= daysInMonth; d++) {
      const opt = document.createElement("option");
      opt.value = d;
      opt.textContent = String(d).padStart(2, "0");
      daySelect.appendChild(opt);
    }

    if (keepSelected) {
      daySelect.value = Math.min(prevDay, daysInMonth);
    }
  }

  monthSelect.addEventListener("change", () => updateDaysOptions(true));
  yearSelect.addEventListener("change", () => updateDaysOptions(true));

  updateDaysOptions(false);
}

function initDateTimeDropdowns() {
  populateDateTimeSelects("birth");
  populateDateTimeSelects("quick");
  syncQuickFormWithState();
}

function syncQuickFormWithState() {
  const city = document.getElementById("input-quick-city");
  const lat = document.getElementById("input-quick-latitude");
  const lon = document.getElementById("input-quick-longitude");
  const tz = document.getElementById("input-quick-timezone");
  const day = document.getElementById("select-quick-day");
  const month = document.getElementById("select-quick-month");
  const year = document.getElementById("select-quick-year");
  const hour = document.getElementById("select-quick-hour");
  const minute = document.getElementById("select-quick-minute");
  const second = document.getElementById("select-quick-second");
  const ayanamsha = document.getElementById("select-quick-ayanamsha");
  const chartStyle = document.getElementById("select-quick-chart-style");

  if (city) city.value = state.city;
  if (lat) lat.value = state.latitude;
  if (lon) lon.value = state.longitude;
  if (tz) tz.value = state.timezone_str;
  if (year) year.value = state.year;
  if (month) month.value = state.month;
  if (day) day.value = state.day;
  if (hour) hour.value = state.hour;
  if (minute) minute.value = state.minute;
  if (second) second.value = Math.floor(state.second || 0);
  if (ayanamsha) ayanamsha.value = state.ayanamsha;
  if (chartStyle) chartStyle.value = state.chart_style;
}

async function geocodeLocationQuick(query) {
  const feedback = document.getElementById("quick-geocode-feedback");
  if (feedback) {
    feedback.style.display = "block";
    feedback.textContent = "Resolving location coordinates...";
  }

  try {
    const res = await fetch(`/api/geocode?query=${encodeURIComponent(query)}`);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Could not find location");
    }
    const data = await res.json();

    document.getElementById("input-quick-city").value = data.display_name;
    document.getElementById("input-quick-latitude").value = data.latitude;
    document.getElementById("input-quick-longitude").value = data.longitude;
    document.getElementById("input-quick-timezone").value = data.timezone_str;

    if (feedback) {
      feedback.textContent = `✓ Found: ${data.display_name} (${data.timezone_str})`;
      setTimeout(() => {
        feedback.style.display = "none";
      }, 4000);
    }
  } catch (err) {
    if (feedback) feedback.textContent = "⚠️ " + err.message;
  }
}

function showLandingView() {
  const landing = document.getElementById("landing-view");
  const studio = document.getElementById("studio-view");
  if (landing) landing.style.display = "flex";
  if (studio) studio.style.display = "none";

  document.querySelectorAll(".studio-only").forEach((el) => {
    el.style.display = "none";
  });

  const navBtn = document.getElementById("nav-view-toggle-btn");
  if (navBtn) {
    navBtn.textContent = "✦ Enter Studio";
    navBtn.classList.add("primary-action-pill");
  }

  if (window.location.hash === "#studio") {
    history.pushState("", document.title, window.location.pathname + window.location.search);
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showStudioView() {
  const landing = document.getElementById("landing-view");
  const studio = document.getElementById("studio-view");
  if (landing) landing.style.display = "none";
  if (studio) studio.style.display = "block";

  document.querySelectorAll(".studio-only").forEach((el) => {
    el.style.display = "";
  });

  const navBtn = document.getElementById("nav-view-toggle-btn");
  if (navBtn) {
    navBtn.textContent = "← Home";
    navBtn.classList.remove("primary-action-pill");
  }

  if (window.location.hash !== "#studio") {
    window.location.hash = "#studio";
  }

  if (!state.currentData) {
    calculateChart();
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function loadSampleChartAndEnterStudio() {
  state.year = 1995;
  state.month = 10;
  state.day = 15;
  state.hour = 14;
  state.minute = 30;
  state.second = 0.0;
  state.city = "Jaipur, India";
  state.latitude = 26.9124;
  state.longitude = 75.7873;
  state.timezone_str = "Asia/Kolkata";
  state.ayanamsha = "Lahiri";
  state.chart_style = "north";
  state.time_offset_seconds = 0;

  syncQuickFormWithState();
  syncModalWithState();
  showStudioView();
  calculateChart();
}

window.showLandingView = showLandingView;
window.showStudioView = showStudioView;
window.loadSampleChartAndEnterStudio = loadSampleChartAndEnterStudio;

function syncModalWithState() {
  document.getElementById("input-city").value = state.city;
  document.getElementById("input-latitude").value = state.latitude;
  document.getElementById("input-longitude").value = state.longitude;
  document.getElementById("input-timezone").value = state.timezone_str;

  const yearSelect = document.getElementById("select-birth-year");
  const monthSelect = document.getElementById("select-birth-month");
  const daySelect = document.getElementById("select-birth-day");
  const hourSelect = document.getElementById("select-birth-hour");
  const minuteSelect = document.getElementById("select-birth-minute");
  const secondSelect = document.getElementById("select-birth-second");

  if (yearSelect) yearSelect.value = state.year;
  if (monthSelect) monthSelect.value = state.month;

  const daysInMonth = new Date(state.year, state.month, 0).getDate();
  if (daySelect) {
    daySelect.innerHTML = "";
    for (let d = 1; d <= daysInMonth; d++) {
      const opt = document.createElement("option");
      opt.value = d;
      opt.textContent = String(d).padStart(2, "0");
      daySelect.appendChild(opt);
    }
    daySelect.value = Math.min(state.day, daysInMonth);
  }

  if (hourSelect) hourSelect.value = state.hour;
  if (minuteSelect) minuteSelect.value = state.minute;
  if (secondSelect) secondSelect.value = Math.floor(state.second || 0);

  document.getElementById("select-ayanamsha").value = state.ayanamsha;
  document.getElementById("select-node-type").value = state.node_type;
}

function openBirthModal() {
  syncModalWithState();
  document.getElementById("birth-modal").classList.add("open");
}

function closeBirthModal() {
  document.getElementById("birth-modal").classList.remove("open");
}

// =============================================================================
// Classical Gochar (Real-Time Transits) Workspace
// =============================================================================

function updateGocharButtonStates() {
  const btns = document.querySelectorAll(".gochar-pill");
  btns.forEach((btn) => {
    btn.classList.toggle("active", state.show_gochar);
    btn.innerHTML = state.show_gochar ? "✦ Gochar ON" : "✦ Gochar";
  });
}

function renderGocharWorkspace() {
  const card = document.getElementById("gochar-card");
  if (!card) return;

  // Sync button states
  updateGocharButtonStates();

  // Display Gochar card ONLY when Gochar is toggled ON
  if (!state.show_gochar) {
    card.style.display = "none";
    return;
  }
  card.style.display = "block";

  const d = state.currentData;
  if (!d || !d.gochar) return;
  const g = d.gochar;
  const s = g.summary;

  // Summary score badges
  const scoreBadge = document.getElementById("gochar-score-badge");
  if (scoreBadge) {
    scoreBadge.innerHTML = `<span style="color: #059669; font-weight: 700;">${s.benefic_count} Benefic</span> &bull; <span style="color: #DC2626; font-weight: 700;">${s.challenging_count} Challenging</span>`;
  }

  const timeBadge = document.getElementById("gochar-timestamp-badge");
  if (timeBadge) {
    timeBadge.textContent = `${s.transit_date_formatted} (UTC)`;
  }

  // Quick alert pills
  const sadeVal = document.getElementById("gochar-sade-sati-val");
  if (sadeVal) {
    sadeVal.textContent = s.sade_sati_phase;
    const isNone = s.sade_sati_phase.toLowerCase().includes("none") || s.sade_sati_phase.toLowerCase().includes("no ");
    sadeVal.className = "gochar-pill-val " + (isNone ? "val-good" : "val-warning");
  }

  const guruVal = document.getElementById("gochar-guru-val");
  if (guruVal) {
    guruVal.textContent = s.guru_gochar_summary;
    guruVal.className = "gochar-pill-val val-benefic";
  }

  const nodesVal = document.getElementById("gochar-nodes-val");
  if (nodesVal) {
    nodesVal.textContent = s.rahu_ketu_summary;
    nodesVal.className = "gochar-pill-val val-neutral";
  }

  const chandraVal = document.getElementById("gochar-chandra-val");
  if (chandraVal) {
    chandraVal.textContent = s.is_chandrashtama ? "ACTIVE (Moon in 8th)" : "Clear (No Chandrashtama)";
    chandraVal.className = "gochar-pill-val " + (s.is_chandrashtama ? "val-danger" : "val-good");
  }

  // Render 9 Graha Transit Table
  const tbody = document.getElementById("gochar-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";

  (g.transits || []).forEach((t) => {
    const tr = document.createElement("tr");

    // Status badge class
    const isBenefic = t.is_benefic_from_moon;
    const badgeClass = isBenefic ? "gochar-badge-benefic" : "gochar-badge-malefic";
    const statusText = isBenefic ? "Auspicious" : "Challenging";

    // SAV bindu color
    const savColorClass = t.sav_bindus >= 28 ? "gochar-sav-good" : "gochar-sav-low";

    // Retro indicator
    const motionStr = t.is_retrograde ? '<span class="retro-badge" title="Retrograde">R</span>' : '<span style="color: var(--text-muted); font-size: 0.75rem;">Dir</span>';

    // Combust indicator
    const combustStr = t.is_combust ? ' <span class="combust-badge" title="Combust with Sun">🔥</span>' : '';

    const signDisplayName = state.sign_mode === "english" ? t.sign_name : t.sign_sanskrit;

    tr.innerHTML = `
      <td>
        <div style="display: flex; align-items: center; gap: 0.4rem; font-weight: 600;">
          <span style="font-size: 1.05rem;">${t.glyph}</span>
          <span>${t.planet}</span>
          ${motionStr}
          ${combustStr}
        </div>
      </td>
      <td><strong>${signDisplayName}</strong></td>
      <td style="font-family: var(--font-mono); font-size: 0.85rem;">${t.degree_formatted}</td>
      <td>${t.nakshatra} <span style="color: var(--text-muted); font-size: 0.75rem;">(P${t.pada})</span></td>
      <td style="font-weight: 600; text-align: center;">H${t.house_from_lagna}</td>
      <td style="font-weight: 600; text-align: center;">H${t.house_from_moon}</td>
      <td style="text-align: center;"><span class="gochar-status-badge ${badgeClass}">${statusText}</span></td>
      <td><span class="${savColorClass}" style="font-family: var(--font-mono); font-weight: 700;">${t.sav_bindus}</span> <span style="font-size: 0.75rem; color: var(--text-muted);">(BAV: ${t.bav_bindus})</span></td>
      <td><span style="font-weight: 600;">${t.kaksha_lord}</span> <span style="font-size: 0.75rem; color: var(--text-muted);">(K${t.kaksha_number})</span></td>
      <td class="col-phala">${t.transit_phala}</td>
    `;
    tbody.appendChild(tr);
  });
}

// =============================================================================
// Event Listeners & Bootstrapping
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
  // 0. Initialize Birth Date & Time Dropdowns
  initDateTimeDropdowns();

  // 1. Tab Navigation switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      const tabId = btn.dataset.tab;
      state.active_tab = tabId;

      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
      const targetContent = document.getElementById(`tab-${tabId}`);
      if (targetContent) targetContent.classList.add("active");

      if (tabId === "vargas") {
        renderVargasWorkspace();
      } else if (tabId === "kundali") {
        renderKundaliChart();
      } else if (tabId === "dasha") {
        renderDashasWorkspace();
      } else if (tabId === "kp") {
        renderKPWorkspace();
      } else if (tabId === "jaimini") {
        renderJaiminiWorkspace();
      } else if (tabId === "yogas") {
        renderYogasWorkspace();
      } else if (tabId === "ashtakavarga") {
        renderAshtakavargaWorkspace();
      }
    });
  });

  // 1b. Gochar (Real-Time Transit) Toggle Buttons
  document.querySelectorAll(".gochar-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.show_gochar = !state.show_gochar;
      updateGocharButtonStates();
      calculateChart();
    });
  });

  // 2. Quick Varga Pills (Overview)
  document.querySelectorAll(".quick-varga-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectVarga(btn.dataset.varga);
    });
  });

  // 3. Divisional Harmonic Pills
  document.querySelectorAll(".varga-pill-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectVarga(btn.dataset.varga);
    });
  });

  // 3b. Yogas & Doshas Category Filter Pills
  document.querySelectorAll(".yoga-filter-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".yoga-filter-pill").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.active_yoga_filter = btn.dataset.filter;
      renderYogasWorkspace();
    });
  });

  // 3c. Ashtakavarga BAV Planet Selector Pills
  document.querySelectorAll(".bav-planet-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".bav-planet-pill").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.selected_bav_planet = btn.dataset.planet;
      renderAshtakavargaWorkspace();
    });
  });

  // 4. Scrubber Buttons
  document.getElementById("scrub-minus-5m")?.addEventListener("click", () => {
    state.time_offset_seconds -= 300;
    calculateChart();
  });
  document.getElementById("scrub-minus-1m")?.addEventListener("click", () => {
    state.time_offset_seconds -= 60;
    calculateChart();
  });
  document.getElementById("scrub-minus-15s")?.addEventListener("click", () => {
    state.time_offset_seconds -= 15;
    calculateChart();
  });
  document.getElementById("scrub-plus-15s")?.addEventListener("click", () => {
    state.time_offset_seconds += 15;
    calculateChart();
  });
  document.getElementById("scrub-plus-1m")?.addEventListener("click", () => {
    state.time_offset_seconds += 60;
    calculateChart();
  });
  document.getElementById("scrub-plus-5m")?.addEventListener("click", () => {
    state.time_offset_seconds += 300;
    calculateChart();
  });
  document.getElementById("scrub-reset")?.addEventListener("click", () => {
    state.time_offset_seconds = 0;
    calculateChart();
  });

  // 5. Chart Style Toggle (North Diamond / South Grid)
  const styleBtn = document.getElementById("chart-style-toggle");
  styleBtn.addEventListener("click", () => {
    state.chart_style = state.chart_style === "north" ? "south" : "north";
    styleBtn.textContent = state.chart_style === "north" ? "North Diamond" : "South Grid";
    calculateChart();
  });

  // 6. Sign Language Toggle (Sanskrit / English)
  const signBtn = document.getElementById("sign-mode-toggle");
  signBtn.addEventListener("click", () => {
    state.sign_mode = state.sign_mode === "sanskrit" ? "english" : "sanskrit";
    signBtn.textContent = state.sign_mode === "sanskrit" ? "Sanskrit" : "English";
    calculateChart();
  });

  // 7. Theme Toggle (Light / Dark)
  const themeBtn = document.getElementById("theme-toggle-btn");
  const savedTheme = localStorage.getItem("trinetri_theme") || "light";
  state.theme_mode = savedTheme;
  document.documentElement.dataset.theme = savedTheme;
  themeBtn.textContent = savedTheme === "light" ? "🌙" : "☀️";

  themeBtn.addEventListener("click", () => {
    state.theme_mode = state.theme_mode === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = state.theme_mode;
    localStorage.setItem("trinetri_theme", state.theme_mode);
    themeBtn.textContent = state.theme_mode === "light" ? "🌙" : "☀️";
    calculateChart();
  });

  // 8. Drawer Close Handlers
  document.getElementById("drawer-close-btn").addEventListener("click", closePlanetDrawer);
  document.getElementById("drawer-backdrop").addEventListener("click", (e) => {
    if (e.target.id === "drawer-backdrop") closePlanetDrawer();
  });

  // 9. Modal Open/Close Handlers
  document.getElementById("birth-profile-btn").addEventListener("click", openBirthModal);
  document.getElementById("modal-close-btn").addEventListener("click", closeBirthModal);
  document.getElementById("birth-modal").addEventListener("click", (e) => {
    if (e.target.id === "birth-modal") closeBirthModal();
  });

  // 10. Geocode Button & Enter Key in Modal
  const triggerGeocode = () => {
    const q = document.getElementById("input-city").value.trim();
    if (q) geocodeLocation(q);
  };
  document.getElementById("btn-geocode").addEventListener("click", triggerGeocode);
  document.getElementById("input-city").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      triggerGeocode();
    }
  });

  // 11. Modal Form Submission
  document.getElementById("birth-params-form").addEventListener("submit", (e) => {
    e.preventDefault();

    state.city = document.getElementById("input-city").value.trim();
    state.latitude = parseFloat(document.getElementById("input-latitude").value);
    state.longitude = parseFloat(document.getElementById("input-longitude").value);
    state.timezone_str = document.getElementById("input-timezone").value.trim();

    state.year = parseInt(document.getElementById("select-birth-year").value, 10);
    state.month = parseInt(document.getElementById("select-birth-month").value, 10);
    state.day = parseInt(document.getElementById("select-birth-day").value, 10);

    state.hour = parseInt(document.getElementById("select-birth-hour").value, 10);
    state.minute = parseInt(document.getElementById("select-birth-minute").value, 10);
    state.second = parseFloat(document.getElementById("select-birth-second").value) || 0.0;

    state.ayanamsha = document.getElementById("select-ayanamsha").value;
    state.node_type = document.getElementById("select-node-type").value;
    state.time_offset_seconds = 0; // Reset scrubber on new birth input

    syncQuickFormWithState();
    closeBirthModal();
    calculateChart();
  });

  // 12. Quick Birth Form Submission (Landing Page)
  const quickForm = document.getElementById("quick-birth-form");
  if (quickForm) {
    quickForm.addEventListener("submit", (e) => {
      e.preventDefault();

      state.city = document.getElementById("input-quick-city").value.trim();
      state.latitude = parseFloat(document.getElementById("input-quick-latitude").value) || 26.9124;
      state.longitude = parseFloat(document.getElementById("input-quick-longitude").value) || 75.7873;
      state.timezone_str = document.getElementById("input-quick-timezone").value.trim() || "Asia/Kolkata";

      state.year = parseInt(document.getElementById("select-quick-year").value, 10) || 1995;
      state.month = parseInt(document.getElementById("select-quick-month").value, 10) || 10;
      state.day = parseInt(document.getElementById("select-quick-day").value, 10) || 15;

      state.hour = parseInt(document.getElementById("select-quick-hour").value, 10) || 14;
      state.minute = parseInt(document.getElementById("select-quick-minute").value, 10) || 30;
      state.second = parseFloat(document.getElementById("select-quick-second").value) || 0.0;

      state.ayanamsha = document.getElementById("select-quick-ayanamsha").value || "Lahiri";
      state.chart_style = document.getElementById("select-quick-chart-style").value || "north";
      state.time_offset_seconds = 0;

      // Sync modal controls as well
      syncModalWithState();
      showStudioView();
      calculateChart();
    });
  }

  // 13. Quick Sample Chart Button
  document.getElementById("btn-quick-sample")?.addEventListener("click", loadSampleChartAndEnterStudio);

  // 14. Quick Geocode Search Button & Enter Key
  const triggerQuickGeocode = () => {
    const q = document.getElementById("input-quick-city").value.trim();
    if (q) geocodeLocationQuick(q);
  };
  document.getElementById("btn-quick-geocode")?.addEventListener("click", triggerQuickGeocode);
  document.getElementById("input-quick-city")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      triggerQuickGeocode();
    }
  });

  // 15. Header View Toggle (Landing <-> Studio)
  const navViewToggleBtn = document.getElementById("nav-view-toggle-btn");
  if (navViewToggleBtn) {
    navViewToggleBtn.addEventListener("click", () => {
      const studio = document.getElementById("studio-view");
      if (studio && studio.style.display !== "none") {
        showLandingView();
      } else {
        showStudioView();
      }
    });
  }

  // 16. Brand Logo / Title Click returns to Landing
  document.getElementById("brand-home-btn")?.addEventListener("click", showLandingView);

  // 17. URL Hash Router Listener
  window.addEventListener("hashchange", () => {
    if (window.location.hash === "#studio") {
      showStudioView();
    } else {
      showLandingView();
    }
  });

  // 18. Initial View State & Chart Calculation
  if (window.location.hash === "#studio") {
    showStudioView();
  } else {
    showLandingView();
  }
  calculateChart();
});
