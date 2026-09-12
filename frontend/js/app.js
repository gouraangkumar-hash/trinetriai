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
  currentData: null,
};

// =============================================================================
// Astronomical & Glyph Dictionaries
// =============================================================================

const PLANET_GLYPHS = {
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
    if (!res.ok) throw new Error("Could not find location");
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
  renderPlanetsTable();
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

  document.getElementById("strip-dasha-md").textContent = ds.md;
  document.getElementById("strip-dasha-ad").textContent = ds.ad;
  document.getElementById("strip-dasha-pd").textContent = ds.pd;
  document.getElementById("strip-dasha-dates").textContent = `${ds.ad_range} (AD)`;

  // Also update hero in Tab 3
  document.getElementById("dasha-hero-md").textContent = ds.md;
  document.getElementById("dasha-hero-ad").textContent = ds.ad;
  document.getElementById("dasha-hero-pd").textContent = ds.pd;
  document.getElementById("dasha-hero-dates").textContent = `Current Mahadasha: ${ds.md_range}`;
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

      return `
        <tr>
          <td><strong style="color: var(--accent-primary); margin-right: 0.4rem;">${glyph}</strong> ${p.planet}${vargottamaTag}</td>
          <td>${p.sign}</td>
          <td style="font-family: var(--font-mono);">${p.degree}</td>
          <td>${p.nakshatra}</td>
          <td>${p.star_lord}</td>
          <td>${p.sub_lord}</td>
          <td>${p.sub_sub_lord}</td>
          <td>${motionHtml}</td>
          <td>
            <button class="inspect-btn" onclick="openPlanetDrawer('${p.planet}')">Inspect</button>
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
  if (!d || !d.mahadashas) return;

  const container = document.getElementById("dasha-cards-container");
  if (!container) return;

  container.innerHTML = d.mahadashas
    .map((md, idx) => {
      const glyph = PLANET_GLYPHS[md.lord] || "";
      const statusClass = md.status.toLowerCase();
      const isCardActive = md.status === "ACTIVE";

      const adRows = md.antardashas
        .map((ad) => {
          const adGlyph = PLANET_GLYPHS[ad.lord] || "";
          const activeAdClass = ad.is_active ? "active-ad" : "";
          const adBadge = ad.is_active
            ? `<span class="status-badge active">Active</span>`
            : (ad.status === "COMPLETED" ? `<span class="status-badge completed">Done</span>` : `<span class="status-badge upcoming">Next</span>`);

          return `
            <tr class="${activeAdClass}">
              <td><strong>${adGlyph}</strong> ${ad.lord}</td>
              <td class="ad-dates-cell">${ad.start} → ${ad.end}</td>
              <td>${ad.duration}</td>
              <td>${adBadge}</td>
            </tr>
          `;
        })
        .join("");

      return `
        <div class="mahadasha-card ${isCardActive ? "active-md expanded" : ""}" id="md-card-${idx}">
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
          <button class="md-toggle-btn" onclick="toggleMahadashaCard(${idx})">
            <span>View 9 Antardashas</span>
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

  document.getElementById("drawer-backdrop").classList.add("open");
}

function closePlanetDrawer() {
  document.getElementById("drawer-backdrop").classList.remove("open");
}

// =============================================================================
// Modal Dialog Controller
// =============================================================================

function initDateTimeDropdowns() {
  const daySelect = document.getElementById("select-birth-day");
  const monthSelect = document.getElementById("select-birth-month");
  const yearSelect = document.getElementById("select-birth-year");
  const hourSelect = document.getElementById("select-birth-hour");
  const minuteSelect = document.getElementById("select-birth-minute");
  const secondSelect = document.getElementById("select-birth-second");

  if (!daySelect || !yearSelect || !hourSelect || !minuteSelect || !secondSelect) return;

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

  // Initial population of days
  updateDaysOptions(false);
}

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
  document.getElementById("scrub-minus-1m").addEventListener("click", () => {
    state.time_offset_seconds -= 60;
    calculateChart();
  });
  document.getElementById("scrub-minus-15s").addEventListener("click", () => {
    state.time_offset_seconds -= 15;
    calculateChart();
  });
  document.getElementById("scrub-plus-15s").addEventListener("click", () => {
    state.time_offset_seconds += 15;
    calculateChart();
  });
  document.getElementById("scrub-plus-1m").addEventListener("click", () => {
    state.time_offset_seconds += 60;
    calculateChart();
  });
  document.getElementById("scrub-reset").addEventListener("click", () => {
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

  // 10. Geocode Button in Modal
  document.getElementById("btn-geocode").addEventListener("click", () => {
    const q = document.getElementById("input-city").value.trim();
    if (q) geocodeLocation(q);
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

    closeBirthModal();
    calculateChart();
  });

  // 12. Initial Chart Calculation on Page Load
  calculateChart();
});
