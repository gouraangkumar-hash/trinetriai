// TrinetriAI Vedic Studio - Frontend Controller

// --- Application State ---

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
  gender: "male",
  chart_style: "north", // "north" | "south"
  sign_mode: "sanskrit", // "sanskrit" | "english"
  theme_mode: "light", // "light" | "dark"
  selected_varga: "D1",
  active_tab: "kundali",
  active_yoga_filter: "all",
  selected_bav_planet: "Jupiter",
  show_gochar: false,
  target_date: null,
  activeRayPlanet: null,
  currentData: null,
  selected_pillar: "comprehensive",
  active_ai_persp: "synthesis",
  ai_readings_cache: {},
  last_ai_chart_sig: null,
  chat_messages: [],
  is_generating_synthesis: false,
  is_sending_chat: false,
  synthesis_abort_controller: null,
  chat_abort_controller: null,
};

// --- Glyph & Coordinate Mappings ---

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

// --- API Calls ---

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
    gender: state.gender,
    chart_style: state.chart_style,
    sign_mode: state.sign_mode,
    theme_mode: state.theme_mode,
    selected_varga: state.selected_varga,
    show_gochar: state.show_gochar,
    target_date: state.target_date,
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
      gender: state.gender,
      chart_style: state.chart_style,
      sign_mode: state.sign_mode,
      theme_mode: state.theme_mode,
      selected_varga: varga,
      show_gochar: state.show_gochar,
      target_date: state.target_date,
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

// --- View Rendering ---

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
  renderAiConsultationWorkspace();
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

function getFuncBadgeClass(badge) {
  if (!badge) return "neutral";
  const b = String(badge).toLowerCase();
  if (b.includes("yogakaraka")) return "yogakaraka";
  if (b.includes("maraka")) return "maraka";
  if (b.includes("badhaka")) return "badhaka";
  if (b.includes("benefic")) return "benefic";
  if (b.includes("malefic")) return "malefic";
  if (b.includes("dosha")) return "kendra-dosha";
  return "neutral";
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

      // Dignity Tags: Exalted [Ex], Debilitated [Deb], Own Sign [Own]
      let dignityBadges = "";
      if (p.is_exalted) {
        dignityBadges += `<span class="dignity-badge dignity-ex" title="${p.dignity_desc || 'Exalted (Uccha) in ' + p.sign}">[Ex]</span>`;
      } else if (p.is_debilitated) {
        const nbFlag = p.has_neechabhanga ? '*' : '';
        const nbNote = p.has_neechabhanga ? ' • Neechabhanga Cancelled' : '';
        dignityBadges += `<span class="dignity-badge dignity-deb" title="${p.dignity_desc || 'Debilitated (Neecha) in ' + p.sign}${nbNote}">[Deb${nbFlag}]</span>`;
      } else if (p.is_own_sign) {
        dignityBadges += `<span class="dignity-badge dignity-own" title="${p.dignity_desc || 'Own Sign (Swa Kshetra) in ' + p.sign}">[Own]</span>`;
      }

      // Shorter method for highlighting Vargottama: [V] pill badge
      if (p.is_vargottama) {
        dignityBadges += `<span class="dignity-badge dignity-v" title="${p.vargottama_status || 'Vargottama: Same sign in D1 & D9'}">[V]</span>`;
      }

      // Functional Nature Badges
      let funcHtml = "";
      if (p.functional_badges && p.functional_badges.length > 0) {
        funcHtml = `<div style="display: flex; flex-wrap: wrap; gap: 0.25rem;">
          ${p.functional_badges.map(b => `<span class="func-badge ${getFuncBadgeClass(b)}">${b}</span>`).join("")}
        </div>`;
      } else if (p.functional_role && p.functional_role !== "Neutral") {
        funcHtml = `<span class="func-badge ${getFuncBadgeClass(p.functional_role)}">${p.functional_role}</span>`;
      } else {
        funcHtml = `<span class="func-badge neutral">Neutral</span>`;
      }

      // Algorithmic Planetary Strength (Bala)
      let strengthHtml = `<span style="color: var(--text-muted); font-size: 0.8rem; text-align: center; display: block;">-</span>`;
      if (p.strength) {
        const gradeClass = (p.strength_grade || "moderate").toLowerCase().replace(/\s+/g, '-');
        strengthHtml = `
          <div class="strength-meter-wrap">
            <div class="strength-meter-top">
              <strong style="color: ${p.strength.grade_color}; font-size: 0.82rem;">${p.strength_percentage}</strong>
              <span class="strength-tag ${gradeClass}">${p.strength_grade}</span>
            </div>
            <div class="strength-bar-bg">
              <div class="strength-bar-fill" style="width: ${p.strength.total_score}%; background: ${p.strength.grade_color};"></div>
            </div>
          </div>
        `;
      }

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

      const isRayActive = (state.activeRayPlanet === p.planet);
      const isAscendant = p.planet.includes("Ascendant");
      const rowClass = isRayActive ? 'active-ray-row' : '';
      const rowId = `planet-row-${p.planet.replace(/[^a-zA-Z0-9]/g, '')}`;
      const drawerTarget = isAscendant ? 'Ascendant' : p.planet;

      return `
        <tr class="${rowClass}" id="${rowId}">
          <td onclick="openPlanetDrawer('${drawerTarget}')" 
              style="cursor: pointer;" 
              title="Click to inspect ${p.planet} in slide-over drawer">
            <strong style="color: var(--accent-primary); margin-right: 0.4rem;">${glyph}</strong> 
            <span class="planet-name-link">${p.planet}</span>${dignityBadges}
          </td>
          <td>${p.sign}</td>
          <td style="font-family: var(--font-mono);">${p.degree}</td>
          <td>${p.nakshatra}</td>
          <td>${motionHtml}</td>
          <td>${funcHtml}</td>
          <td class="strength-table-cell">${strengthHtml}</td>
          <td>${drishtiHtml}</td>
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

        // Mini Dignity Badges next to planet name
        let dignityBadgeHtml = "";
        if (row.is_exalted) {
          dignityBadgeHtml += ` <span class="varga-badge exalted" title="Exalted (Uccha)">[Ex]</span>`;
        } else if (row.is_debilitated) {
          dignityBadgeHtml += ` <span class="varga-badge debilitated" title="Debilitated (Neecha)">[Deb]</span>`;
        } else if (row.is_own_sign) {
          dignityBadgeHtml += ` <span class="varga-badge own" title="Own Sign (Swa Kshetra)">[Own]</span>`;
        }
        if (row.is_vargottama) {
          dignityBadgeHtml += ` <span class="varga-badge vargottama" title="Vargottama (Same sign in D1 and this Varga)">[V]</span>`;
        }

        const nameHtml = isAsc
          ? `<span class="cursor-pointer" onclick="window.openPlanetDrawer && window.openPlanetDrawer('Ascendant')" style="cursor: pointer;" title="Click to inspect Ascendant"><strong style="color: var(--accent-primary);">✧ ${row.planet}</strong></span>${dignityBadgeHtml}`
          : `<span class="cursor-pointer" onclick="window.openPlanetDrawer && window.openPlanetDrawer('${row.planet}')" style="cursor: pointer;" title="Click to inspect ${row.planet}"><strong style="color: var(--accent-primary); margin-right: 0.4rem;">${glyph}</strong> <span class="planet-name-link">${row.planet}</span></span>${dignityBadgeHtml}`;

        const statusBadges = [];
        if (row.is_retro) statusBadges.push(`<span class="status-badge retro">Retro</span>`);
        if (row.is_combust) statusBadges.push(`<span class="status-badge combust">Combust</span>`);
        if (row.dignity_label && row.dignity_label !== "Lagna" && !row.dignity_label.includes("Neutral")) {
          const cls = row.is_exalted ? "dignity-exalted" : (row.is_debilitated ? "dignity-debilitated" : (row.is_own_sign ? "dignity-own" : "upcoming"));
          statusBadges.push(`<span class="status-badge ${cls}">${row.dignity_label}</span>`);
        }
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

  // Jaimini Chara Dasha
  const charaBadge = document.getElementById("chara-dasha-order-badge");
  if (charaBadge) {
    if (d.chara_dasha_summary) {
      charaBadge.textContent = `Order: ${d.chara_dasha_summary.order}`;
      if (d.chara_dasha_summary.order && d.chara_dasha_summary.order.includes("Direct")) {
        charaBadge.className = "status-badge active";
        charaBadge.style.backgroundColor = "";
        charaBadge.style.color = "";
      } else {
        charaBadge.className = "status-badge";
        charaBadge.style.backgroundColor = "rgba(229, 184, 105, 0.15)";
        charaBadge.style.color = "#E5B869";
      }
    } else {
      charaBadge.textContent = "Order: Savya/Apasavya";
      charaBadge.className = "status-badge";
    }
  }

  const charaMd = document.getElementById("chara-hero-md");
  const charaAd = document.getElementById("chara-hero-ad");
  const charaDates = document.getElementById("chara-hero-dates");
  if (d.chara_dasha_summary) {
    const cs = d.chara_dasha_summary;
    if (charaMd) {
      charaMd.textContent = (cs.active_md && cs.active_md !== "-")
        ? `${cs.active_md} (${cs.active_md_lord})`
        : "—";
    }
    if (charaAd) {
      charaAd.textContent = (cs.active_ad && cs.active_ad !== "-")
        ? `${cs.active_ad} (${cs.active_ad_lord})`
        : "—";
    }
    if (charaDates) {
      charaDates.textContent = `Current Mahadasha: ${cs.md_range} • Active Antardasha: ${cs.ad_range}`;
    }
  } else {
    if (charaMd) charaMd.textContent = "—";
    if (charaAd) charaAd.textContent = "—";
    if (charaDates) {
      charaDates.innerHTML = '<span style="color: var(--accent-primary); cursor: pointer;" onclick="calculateChart()">✦ Click to recalculate chart & load Chara Dasha timeline</span>';
    }
  }

  const charaTbody = document.getElementById("chara-dasha-tbody");
  if (charaTbody) {
    if (d.chara_dasha_periods && d.chara_dasha_periods.length > 0) {
      charaTbody.innerHTML = d.chara_dasha_periods
        .map((md, idx) => {
          const glyph = PLANET_GLYPHS[md.lord] || "";
          const isActive = md.is_active;
          const statusBadgeClass = isActive ? "active" : (md.status === "COMPLETED" ? "completed" : "upcoming");
          const rowBg = isActive ? "style='background: rgba(200, 155, 60, 0.08); font-weight: 600;'" : "";

          const adRows = md.antardashas
            .map((ad, adIdx) => {
              const isAdActive = ad.is_active;
              const adStatusClass = isAdActive ? "active" : (ad.status === "COMPLETED" ? "completed" : "upcoming");
              const adGlyph = PLANET_GLYPHS[ad.lord] || "";
              const adBg = isAdActive ? "style='background: rgba(200, 155, 60, 0.12); font-weight: 600;'" : "";
              return `
                <tr ${adBg}>
                  <td style="font-family: var(--font-mono);">${adIdx + 1}</td>
                  <td><strong>${ad.sign}</strong></td>
                  <td><span style="color: var(--accent-primary); margin-right: 0.3rem;">${adGlyph}</span> ${ad.lord}</td>
                  <td style="font-family: var(--font-mono);">${ad.duration}</td>
                  <td style="font-family: var(--font-mono);">${ad.start} → ${ad.end}</td>
                  <td><span class="status-badge ${adStatusClass}">${ad.status}</span></td>
                </tr>
              `;
            })
            .join("");

          return `
            <tr ${rowBg} id="chara-md-row-${idx}">
              <td><span class="status-badge" style="font-family: var(--font-mono); font-size: 0.7rem;">C${md.cycle}</span></td>
              <td><strong style="font-size: 0.95rem; color: ${isActive ? 'var(--accent-primary)' : 'inherit'};">${md.sign}</strong></td>
              <td><strong style="color: var(--accent-primary); margin-right: 0.3rem;">${glyph}</strong> ${md.lord}</td>
              <td style="font-family: var(--font-mono);">${md.duration}</td>
              <td style="font-family: var(--font-mono);">${md.start} → ${md.end}</td>
              <td><span class="status-badge ${statusBadgeClass}">${md.status}</span></td>
              <td style="text-align: right;">
                <button class="varga-pill-btn" id="chara-ad-btn-${idx}" onclick="toggleCharaAntardashaRow(${idx})" style="padding: 0.25rem 0.65rem; font-size: 0.75rem;">
                  ${isActive ? 'Hide Antardashas ▲' : 'View Antardashas ▼'}
                </button>
              </td>
            </tr>
            <tr id="chara-ad-row-${idx}" class="chara-ad-nested-row" style="display: ${isActive ? 'table-row' : 'none'}; background: rgba(0,0,0,0.15);">
              <td colspan="7" style="padding: 0.75rem 1rem;">
                <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.5rem;">
                  ✦ ${md.sign} Mahadasha • 12 Antardashas (${md.duration} total)
                </div>
                <table class="studio-table pd-nested-table" style="margin: 0; background: transparent;">
                  <thead>
                    <tr>
                      <th style="width: 40px;">#</th>
                      <th>Antardasha Rashi</th>
                      <th>Ruler</th>
                      <th>Duration</th>
                      <th>Dates</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${adRows}
                  </tbody>
                </table>
              </td>
            </tr>
          `;
        })
        .join("");
    } else {
      charaTbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No Chara Dasha periods available. Click <a href="javascript:void(0)" onclick="calculateChart()" style="color: var(--accent-primary); text-decoration: underline;">Calculate Chart</a> to refresh.</td></tr>';
    }
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

function toggleCharaAntardashaRow(idx) {
  const row = document.getElementById(`chara-ad-row-${idx}`);
  const btn = document.getElementById(`chara-ad-btn-${idx}`);
  if (!row) return;
  const isHidden = row.style.display === "none" || !row.style.display;
  row.style.display = isHidden ? "table-row" : "none";
  if (btn) {
    btn.textContent = isHidden ? "Hide Antardashas ▲" : "View Antardashas ▼";
  }
}
window.toggleCharaAntardashaRow = toggleCharaAntardashaRow;

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

// --- Planet Detail Drawer ---

function openPlanetDrawer(planetName) {
  const d = state.currentData;
  if (!d || !d.planet_details) return;

  const p = d.planet_details[planetName];
  if (!p) return;

  document.getElementById("drawer-planet-glyph").textContent = PLANET_GLYPHS[p.planet] || "✧";
  document.getElementById("drawer-planet-name").textContent = p.planet;
  document.getElementById("drawer-planet-pos").textContent = `${p.sign} ${p.degree}`;

  // Classical Dignity (Avastha) Badge & Details
  const digBadge = document.getElementById("drawer-dignity-badge");
  const digBox = document.getElementById("box-dignity");
  const digVal = document.getElementById("drawer-dignity");

  if (digBadge) {
    if (p.is_exalted) {
      digBadge.style.display = "inline-flex";
      digBadge.className = "status-badge dignity-exalted";
      digBadge.textContent = "✦ Exalted (Uccha)";
    } else if (p.is_debilitated) {
      digBadge.style.display = "inline-flex";
      digBadge.className = "status-badge dignity-debilitated";
      digBadge.textContent = p.has_neechabhanga ? "✦ Neechabhanga Active" : "▼ Debilitated (Neecha)";
    } else if (p.is_own_sign) {
      digBadge.style.display = "inline-flex";
      digBadge.className = "status-badge dignity-own";
      digBadge.textContent = "✦ Own Sign";
    } else {
      digBadge.style.display = "none";
    }
  }

  if (digVal) {
    digVal.textContent = p.dignity_label || p.dignity || "Neutral";
    if (p.is_exalted) {
      digVal.style.color = "#059669";
    } else if (p.is_debilitated) {
      digVal.style.color = "#DC2626";
    } else if (p.is_own_sign) {
      digVal.style.color = "var(--accent-primary)";
    } else {
      digVal.style.color = "var(--text-secondary)";
    }
    if (digBox && p.dignity_desc) {
      digBox.setAttribute("title", p.dignity_desc);
    }
  }

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

  // Functional Nature & Bala Strength (BPHS Ch. 34)
  const funcRoleEl = document.getElementById("drawer-func-role");
  const funcBadgesEl = document.getElementById("drawer-func-badges");
  const strengthPctEl = document.getElementById("drawer-strength-pct");
  const strengthGradeEl = document.getElementById("drawer-strength-grade");
  const strengthFillEl = document.getElementById("drawer-strength-fill");
  const strSthanaEl = document.getElementById("drawer-str-sthana");
  const strDikEl = document.getElementById("drawer-str-dik");
  const strBavEl = document.getElementById("drawer-str-bav");
  const strDrishtiEl = document.getElementById("drawer-str-drishti");

  if (funcRoleEl) {
    funcRoleEl.textContent = p.functional_role || "Neutral";
  }

  if (funcBadgesEl) {
    if (p.functional_badges && p.functional_badges.length > 0) {
      funcBadgesEl.innerHTML = p.functional_badges.map(b => `
        <span class="func-badge ${getFuncBadgeClass(b)}">${b}</span>
      `).join("");
    } else {
      funcBadgesEl.innerHTML = `<span class="func-badge neutral">Neutral</span>`;
    }
  }

  if (p.strength) {
    const s = p.strength;
    const gradeClass = (p.strength_grade || "moderate").toLowerCase().replace(/\s+/g, '-');
    if (strengthPctEl) strengthPctEl.textContent = p.strength_percentage || `${Math.round(s.total_score)}%`;
    if (strengthGradeEl) {
      strengthGradeEl.textContent = p.strength_grade;
      strengthGradeEl.className = `strength-tag ${gradeClass}`;
    }
    if (strengthFillEl) {
      strengthFillEl.style.width = `${s.total_score}%`;
      strengthFillEl.style.backgroundColor = s.grade_color;
    }
    if (strSthanaEl) strSthanaEl.textContent = `${s.breakdown.sthana_score.toFixed(1)} / 35`;
    if (strDikEl) strDikEl.textContent = `${s.breakdown.dik_score.toFixed(1)} / 25`;
    if (strBavEl) strBavEl.textContent = `${s.breakdown.bav_score.toFixed(1)} / 25`;
    if (strDrishtiEl) strDrishtiEl.textContent = `${s.breakdown.drishti_score.toFixed(1)} / 15`;
  } else {
    if (strengthPctEl) strengthPctEl.textContent = "-";
    if (strengthGradeEl) {
      strengthGradeEl.textContent = "-";
      strengthGradeEl.className = "strength-tag";
    }
    if (strengthFillEl) strengthFillEl.style.width = "0%";
    if (strSthanaEl) strSthanaEl.textContent = "-";
    if (strDikEl) strDikEl.textContent = "-";
    if (strBavEl) strBavEl.textContent = "-";
    if (strDrishtiEl) strDrishtiEl.textContent = "-";
  }

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

  // Classical Planetary Friendships (Pancha-Dha Maitri)
  const friendshipSection = document.getElementById("drawer-friendships-section");
  const dispName = document.getElementById("drawer-dispositor-name");
  const dispPill = document.getElementById("drawer-dispositor-pill");
  const dispSanskrit = document.getElementById("drawer-dispositor-sanskrit");
  const friendshipTableBody = document.getElementById("drawer-friendships-table-body");

  if (p.friendships && friendshipSection) {
    friendshipSection.style.display = "block";
    const f = p.friendships;

    if (dispName) {
      dispName.textContent = `Dispositor: ${f.dispositor} (${f.sign_name})`;
    }

    if (dispPill) {
      dispPill.textContent = f.dispositor_kshetra;
      dispPill.className = "pancha-badge " + getPanchaBadgeClass(f.dispositor_relationship);
    }

    if (dispSanskrit) {
      dispSanskrit.textContent = f.dispositor_sanskrit || "";
    }

    if (friendshipTableBody) {
      if (f.relationships && f.relationships.length > 0) {
        friendshipTableBody.innerHTML = f.relationships.map(rel => {
          const badgeClass = getPanchaBadgeClass(rel.pancha_dha_relationship);
          return `
            <tr>
              <td style="font-weight: 700; white-space: nowrap;">
                <span style="color: var(--accent-primary); margin-right: 0.25rem;">${rel.target_glyph}</span>${rel.target_planet}
              </td>
              <td style="text-align: center; color: var(--text-secondary); font-size: 0.75rem;">${rel.natural_relationship}</td>
              <td style="text-align: center; color: var(--text-secondary); font-size: 0.75rem;">${rel.temporal_relationship} (H${rel.house_offset_from_source})</td>
              <td style="text-align: right;">
                <span class="pancha-badge ${badgeClass}" title="${rel.pancha_dha_sanskrit}">${rel.pancha_dha_relationship}</span>
              </td>
            </tr>
          `;
        }).join("");
      } else {
        friendshipTableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No relationship data available.</td></tr>`;
      }
    }
  } else if (friendshipSection) {
    friendshipSection.style.display = "none";
  }

  document.getElementById("drawer-backdrop").classList.add("open");
}

function getPanchaBadgeClass(rel) {
  if (!rel) return "sama";
  const s = String(rel).toLowerCase();
  if (s.includes("own") || s.includes("swa")) return "own-sign";
  if (s.includes("great friend") || s.includes("adhi mitra") || s.includes("adhimitra")) return "adhi-mitra";
  if (s.includes("great enemy") || s.includes("adhi shatru") || s.includes("adhishatru")) return "adhi-shatru";
  if (s.includes("friend") || s.includes("mitra")) return "mitra";
  if (s.includes("enemy") || s.includes("shatru")) return "shatru";
  return "sama";
}

function closePlanetDrawer() {
  document.getElementById("drawer-backdrop").classList.remove("open");
}

window.openPlanetDrawer = openPlanetDrawer;
window.closePlanetDrawer = closePlanetDrawer;

// --- AI Dossier Modal ---

let activeDossierTab = "md"; // "md" | "prompt" | "json"

function openAiDossierModal() {
  const d = state.currentData;
  if (!d || !d.ai_dossier) {
    alert("Please calculate a chart first before viewing the AI Dossier.");
    return;
  }

  const modal = document.getElementById("ai-dossier-modal");
  if (modal) {
    modal.classList.add("open");
    renderAiDossierContent();
  }
}

function closeAiDossierModal() {
  const modal = document.getElementById("ai-dossier-modal");
  if (modal) {
    modal.classList.remove("open");
  }
}

function switchDossierTab(tab) {
  activeDossierTab = tab;
  document.querySelectorAll(".dossier-tab-btn").forEach(btn => {
    btn.classList.remove("active");
  });
  const activeBtn = document.getElementById(`btn-tab-dossier-${tab}`);
  if (activeBtn) activeBtn.classList.add("active");

  renderAiDossierContent();
}

function renderAiDossierContent() {
  const d = state.currentData;
  if (!d || !d.ai_dossier) return;

  const codeEl = document.getElementById("ai-dossier-code-content");
  if (!codeEl) return;

  if (activeDossierTab === "md") {
    codeEl.textContent = d.ai_dossier.markdown_dossier;
  } else if (activeDossierTab === "prompt") {
    codeEl.textContent = d.ai_dossier.system_prompt_recommendation;
  } else if (activeDossierTab === "json") {
    codeEl.textContent = JSON.stringify(d.ai_dossier.structured_payload, null, 2);
  }
}

function showCopyToast(msg = "✓ Copied to clipboard!") {
  let toast = document.querySelector(".copy-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "copy-toast";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 2400);
}

function copyAiDossier() {
  const codeEl = document.getElementById("ai-dossier-code-content");
  if (!codeEl) return;
  const text = codeEl.textContent;
  navigator.clipboard.writeText(text).then(() => {
    showCopyToast("✓ Copied AI Dossier to clipboard!");
  }).catch(err => {
    console.error("Copy failed:", err);
    showCopyToast("⚠️ Copy failed, please copy manually.");
  });
}

function downloadAiDossier() {
  const codeEl = document.getElementById("ai-dossier-code-content");
  if (!codeEl) return;
  const text = codeEl.textContent;
  const ext = activeDossierTab === "json" ? "json" : "md";
  const filename = `TrinetriAI_Vedic_Dossier_${state.city.replace(/[^a-zA-Z0-9]/g, '_')}_${state.year}.${ext}`;
  const blob = new Blob([text], { type: ext === "json" ? "application/json" : "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

window.openAiDossierModal = openAiDossierModal;
window.closeAiDossierModal = closeAiDossierModal;
window.switchDossierTab = switchDossierTab;
window.copyAiDossier = copyAiDossier;
window.downloadAiDossier = downloadAiDossier;

// --- Aspect Rays & Highlighting ---

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

// --- Birth Data Modal ---

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
  const gender = document.getElementById("select-quick-gender");
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
  if (gender) gender.value = state.gender;
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
  state.gender = "male";
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
  const genderSelect = document.getElementById("select-birth-gender");

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

  if (genderSelect) genderSelect.value = state.gender || "male";
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

// --- Transit (Gochar) Workspace ---

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
// Trinetri Multi-Agent AI Reading & Synthesis Controller
// =============================================================================

function formatMarkdown(text) {
  if (!text) return "";
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Chapter Headings (e.g. ## ✦ Chapter 1: ... or ## Chapter 1: ...)
  html = html.replace(/^##\s*(?:✦\s*)?Chapter\s*(\d+)[:\s–—\-]+(.*$)/gim, (match, num, rest) => {
    const chId = num ? `id="chapter-${num}"` : "";
    const prefix = num ? `Chapter ${num}: ` : "";
    return `<div class="reading-chapter-header" ${chId}><span class="chapter-ornament">✦</span><h2 class="chapter-title">${prefix}${rest}</h2></div>`;
  });

  // Headings
  html = html.replace(/^### (.*$)/gim, '<h3 style="font-family: var(--font-heading); margin-top: 1.35rem; margin-bottom: 0.5rem; color: var(--accent-primary); font-size: 1.12rem;">$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2 style="font-family: var(--font-heading); margin-top: 1.65rem; margin-bottom: 0.65rem; color: var(--accent-primary); border-bottom: 1px solid var(--border-subtle); padding-bottom: 0.4rem; font-size: 1.3rem;">$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1 style="font-family: var(--font-heading); margin-top: 1.25rem; margin-bottom: 0.85rem; color: var(--text-primary); font-size: 1.55rem; font-weight: 800;">$1</h1>');

  // Bold & Italic
  html = html.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong style="color: var(--text-primary); font-weight: 700;">$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Blockquotes
  html = html.replace(/^\>\s*(.*$)/gim, '<blockquote class="reading-blockquote">$1</blockquote>');

  // Horizontal divider
  html = html.replace(/^---$/gim, '<hr class="reading-divider" />');

  // Bullet points
  html = html.replace(/^\s*[\-\*]\s+(.*$)/gim, '<li style="margin-bottom: 0.45rem; line-height: 1.65;">$1</li>');

  // Paragraphs
  const paragraphs = html.split(/\n{2,}/);
  html = paragraphs.map(p => {
    p = p.trim();
    if (!p) return "";
    if (p.startsWith("<h") || p.startsWith("<ul") || p.startsWith("<li") || p.startsWith("<blockquote") || p.startsWith("<div") || p.startsWith("<pre") || p.startsWith("<hr")) {
      return p;
    }
    return `<p style="margin-bottom: 0.95rem; line-height: 1.75; font-size: 0.96rem; color: var(--text-secondary);">${p.replace(/\n/g, '<br/>')}</p>`;
  }).join("\n");

  return html;
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function toggleLifeProof(btn) {
  if (!btn) return;
  const content = btn.nextElementSibling;
  const chevron = btn.querySelector(".proof-chevron");
  if (!content) return;
  const isOpen = content.classList.toggle("open");
  if (chevron) {
    chevron.textContent = isOpen ? "▲" : "▼";
  }
}
window.toggleLifeProof = toggleLifeProof;

function extractConfluenceMetadata(markdown) {
  if (!markdown || typeof markdown !== "string") {
    return { metadata: null, cleanMarkdown: "" };
  }

  // 1. Check for ```json ... ``` code fence with balanced extraction
  const jsonFenceRegex = /```(?:json)?\s*([\s\S]*?)\s*```/;
  const fenceMatch = markdown.match(jsonFenceRegex);
  if (fenceMatch) {
    const candidate = fenceMatch[1].trim();
    if (candidate.startsWith("{") && candidate.endsWith("}")) {
      try {
        const parsed = JSON.parse(candidate);
        return {
          metadata: parsed,
          cleanMarkdown: markdown.replace(fenceMatch[0], "").trim(),
        };
      } catch (_) {}
    }
  }

  // 2. Check if the whole string is bare JSON
  const trimmed = markdown.trim();
  if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
    try {
      const parsed = JSON.parse(trimmed);
      return {
        metadata: parsed,
        cleanMarkdown: "",
      };
    } catch (_) {}
  }

  // 3. Check for any embedded JSON block from first '{' to last '}'
  const firstBrace = markdown.indexOf("{");
  const lastBrace = markdown.lastIndexOf("}");
  if (firstBrace !== -1 && lastBrace > firstBrace) {
    const candidate = markdown.slice(firstBrace, lastBrace + 1);
    try {
      const parsed = JSON.parse(candidate);
      return {
        metadata: parsed,
        cleanMarkdown: (markdown.slice(0, firstBrace) + markdown.slice(lastBrace + 1)).trim(),
      };
    } catch (_) {}
  }

  return { metadata: null, cleanMarkdown: markdown };
}

function getElementalBreakdown(d) {
  const elemMap = {
    1: "Fire", 2: "Earth", 3: "Air", 4: "Water",
    5: "Fire", 6: "Earth", 7: "Air", 8: "Water",
    9: "Fire", 10: "Earth", 11: "Air", 12: "Water"
  };

  const planets = (typeof state !== "undefined" && state?.currentData?.planets_table) ? state.currentData.planets_table : null;
  if (Array.isArray(planets) && planets.length > 0) {
    const weights = { Fire: 0, Earth: 0, Air: 0, Water: 0 };
    let totalW = 0;
    for (const p of planets) {
      const sId = p.sign_id;
      const elem = elemMap[sId];
      if (!elem) continue;
      const pl = p.planet || "";
      let w = 1.0;
      if (pl.includes("Ascendant") || pl.includes("Lagna")) w = 2.5;
      else if (pl.includes("Moon")) w = 2.5;
      else if (pl.includes("Sun")) w = 1.5;
      else if (pl.includes("Rahu") || pl.includes("Ketu")) w = 0.5;
      weights[elem] += w;
      totalW += w;
    }
    if (totalW > 0) {
      return {
        Fire: Math.round((weights.Fire / totalW) * 100),
        Earth: Math.round((weights.Earth / totalW) * 100),
        Air: Math.round((weights.Air / totalW) * 100),
        Water: Math.round((weights.Water / totalW) * 100)
      };
    }
  }

  // Fallback: parse from d?.constitution?.elements text string
  const text = (d?.constitution?.elements || "") + " " + (d?.constitution?.ayurvedic_prakriti || "");
  const fireMatch = text.match(/Fire\s*(\d+)%/i);
  const earthMatch = text.match(/Earth\s*(\d+)%/i);
  const airMatch = text.match(/Air\s*(\d+)%/i);
  const waterMatch = text.match(/Water\s*(\d+)%/i);

  if (fireMatch || earthMatch || airMatch || waterMatch) {
    return {
      Fire: fireMatch ? parseInt(fireMatch[1], 10) : 25,
      Earth: earthMatch ? parseInt(earthMatch[1], 10) : 25,
      Air: airMatch ? parseInt(airMatch[1], 10) : 25,
      Water: waterMatch ? parseInt(waterMatch[1], 10) : 25
    };
  }

  return { Fire: 25, Earth: 25, Air: 25, Water: 25 };
}
window.getElementalBreakdown = getElementalBreakdown;

// =============================================================================
// Constitutional Polarity Spectrum & Arena Switcher (Interactive Phase A)
// =============================================================================

function calculatePolaritySpectrum(d) {
  const elems = getElementalBreakdown(d);
  const total = (elems.Fire + elems.Earth + elems.Air + elems.Water) || 100;
  const fPct = elems.Fire / total;
  const ePct = elems.Earth / total;
  const aPct = elems.Air / total;
  const wPct = elems.Water / total;

  // 1. Pacing & Stamina: Sprint Bursts (Fire/Air) vs Marathon Grind (Earth/Water)
  let staminaScore = Math.round(((ePct * 1.3 + wPct * 0.7) / (ePct * 1.3 + wPct * 0.7 + fPct * 1.2 + aPct * 0.8 || 1)) * 100);
  staminaScore = Math.max(22, Math.min(84, staminaScore || 68));

  // 2. Emotional Shield & Vulnerability: Open Receiver (Fire/Air) vs Selective Inner Vault (Water/Earth)
  let vaultScore = Math.round(((wPct * 1.4 + ePct * 0.8) / (wPct * 1.4 + ePct * 0.8 + aPct * 1.0 + fPct * 0.8 || 1)) * 100);
  vaultScore = Math.max(28, Math.min(88, vaultScore || 76));

  // 3. Cognitive Strategy: Intuitive Synthesis (Fire/Water) vs Empirical Deconstruction (Earth/Air)
  let logicScore = Math.round(((aPct * 1.3 + ePct * 1.0) / (aPct * 1.3 + ePct * 1.0 + fPct * 0.9 + wPct * 0.8 || 1)) * 100);
  logicScore = Math.max(25, Math.min(85, logicScore || 72));

  // 4. Crisis Stance: Immediate Action (Fire/Air) vs Strategic Deliberate Hold (Earth/Water)
  let pauseScore = Math.round(((ePct * 1.2 + wPct * 1.1) / (ePct * 1.2 + wPct * 1.1 + fPct * 1.2 + aPct * 0.7 || 1)) * 100);
  pauseScore = Math.max(24, Math.min(82, pauseScore || 64));

  const traits = d?.traits || {};

  return [
    {
      id: "pacing",
      title: "ENERGY & STAMINA PACING",
      leftLabel: "Sprint Bursts (High Acceleration)",
      rightLabel: "Marathon Grind (Deep Endurance)",
      score: staminaScore,
      verdictTag: staminaScore >= 50 ? `${staminaScore}% Sustained Marathoner` : `${100 - staminaScore}% High-Velocity Sprinter`,
      bottomLine: traits.physical?.bottom_line || "Steady constitutional endurance that compounds over prolonged execution.",
      headline: traits.physical?.headline || "Physical Constitution & Energy Flow",
      description: traits.physical?.description || "",
      keyPoints: Array.isArray(traits.physical?.key_points) ? traits.physical.key_points : []
    },
    {
      id: "social",
      title: "EMOTIONAL ARMOR & SOCIAL FILTER",
      leftLabel: "Open Empathic Receiver",
      rightLabel: "Selective Vault (Vetted Circle)",
      score: vaultScore,
      verdictTag: vaultScore >= 50 ? `${vaultScore}% Selective Inner Circle` : `${100 - vaultScore}% Expansive Networker`,
      bottomLine: traits.social?.bottom_line || traits.emotional?.bottom_line || "Few are admitted inside, but loyalty to the vetted inner circle is absolute.",
      headline: traits.social?.headline || "Social Boundary Architecture & Filter",
      description: traits.social?.description || "",
      keyPoints: Array.isArray(traits.social?.key_points) ? traits.social.key_points : []
    },
    {
      id: "cognition",
      title: "COGNITIVE & DECISION STRATEGY",
      leftLabel: "Intuitive Synthesis (Pattern Flash)",
      rightLabel: "Empirical Deconstruction (Logical Proof)",
      score: logicScore,
      verdictTag: logicScore >= 50 ? `${logicScore}% Empirical Validation` : `${100 - logicScore}% Intuitive Synthesis`,
      bottomLine: traits.mental?.bottom_line || "Separates signal from noise through structured, empirical reasoning.",
      headline: traits.mental?.headline || "Intellectual Wiring & Problem Solving",
      description: traits.mental?.description || "",
      keyPoints: Array.isArray(traits.mental?.key_points) ? traits.mental.key_points : []
    },
    {
      id: "crisis",
      title: "CRISIS & PRESSURE REFLEX",
      leftLabel: "Immediate Action (Direct Doer)",
      rightLabel: "Strategic Deliberate Pause (Calculated Hold)",
      score: pauseScore,
      verdictTag: pauseScore >= 50 ? `${pauseScore}% Strategic Deliberate Hold` : `${100 - pauseScore}% Immediate Action First`,
      bottomLine: traits.emotional?.bottom_line || "Preserves calm under acute friction while quietly architecting the exit plan.",
      headline: traits.emotional?.headline || "Emotional Armor & Pressure Reflex",
      description: traits.emotional?.description || "",
      keyPoints: Array.isArray(traits.emotional?.key_points) ? traits.emotional.key_points : []
    }
  ];
}
window.calculatePolaritySpectrum = calculatePolaritySpectrum;

function togglePolarityCard(btn) {
  if (!btn) return;
  const card = btn.closest(".wwh-polarity-card");
  if (!card) return;
  const drawer = card.querySelector(".wwh-polarity-drawer");
  if (!drawer) return;
  const isOpen = drawer.classList.toggle("open");
  btn.textContent = isOpen ? "[-] Close Expression Details" : "[+] View Real-World Expression";
}
window.togglePolarityCard = togglePolarityCard;

function renderPolaritySpectrum(d) {
  const spectrum = calculatePolaritySpectrum(d);

  return `
    <div class="wwh-section-block" id="wwh-sec-traits">
      <div class="wwh-section-header">
        <span class="wwh-section-tag">[HOW YOU'RE WIRED]</span>
        <h3 class="wwh-section-title">Your Natural Balance & Core Tendencies</h3>
        <p class="wwh-section-subtitle" style="font-size: 0.86rem; color: var(--text-muted); margin-top: 0.25rem;">
          Where you naturally lean in everyday life—between action and patience, logic and feeling, society and solitude.
        </p>
      </div>

      <div class="wwh-polarity-grid">
        ${spectrum.map(item => `
          <div class="wwh-polarity-card" id="pol-card-${item.id}">
            <div class="wwh-polarity-head">
              <span class="wwh-polarity-dim-title">${escapeHtml(item.title)}</span>
              <span class="wwh-polarity-badge">${escapeHtml(item.verdictTag)}</span>
            </div>

            <!-- The Visual Slider Track -->
            <div class="wwh-polarity-slider-box">
              <div class="wwh-polarity-labels">
                <span class="wwh-pol-label left">${escapeHtml(item.leftLabel)}</span>
                <span class="wwh-pol-label right">${escapeHtml(item.rightLabel)}</span>
              </div>
              <div class="wwh-polarity-track">
                <div class="wwh-polarity-fill" style="width: ${item.score}%;"></div>
                <div class="wwh-polarity-marker" style="left: ${item.score}%;" title="${escapeHtml(item.verdictTag)}"></div>
              </div>
            </div>

            <!-- Bottom line summary -->
            ${item.bottomLine ? `<div class="wwh-polarity-bottom-line">"${escapeHtml(item.bottomLine)}"</div>` : ""}

            <!-- Micro-toggle to expand tangible expression -->
            <div style="display: flex; justify-content: flex-end; margin-top: 0.85rem;">
              <button type="button" class="wwh-expand-pill" onclick="togglePolarityCard(this)">[+] How This Shows Up in Real Life</button>
            </div>

            <!-- Expandable drawer with description and key points -->
            <div class="wwh-polarity-drawer">
              ${item.headline ? `<h4 class="wwh-trait-headline" style="margin-top: 0;">${escapeHtml(item.headline)}</h4>` : ""}
              ${item.description ? `<p class="wwh-trait-desc">${escapeHtml(item.description)}</p>` : ""}
              ${item.keyPoints.length ? `
                <ul class="wwh-trait-bullets">
                  ${item.keyPoints.map(pt => `<li>${escapeHtml(pt)}</li>`).join("")}
                </ul>
              ` : ""}
            </div>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}
window.renderPolaritySpectrum = renderPolaritySpectrum;

function getArenaData(d, arenaKey) {
  const traits = d?.traits || {};
  const qualities = d?.qualities || {};
  const superpowers = Array.isArray(qualities.superpowers) ? qualities.superpowers : [];
  const shadows = Array.isArray(qualities.shadows) ? qualities.shadows : [];
  const manual = d?.operating_manual || {};
  const levers = d?.growth_levers || {};
  const theWhy = d?.the_why || {};

  let fallback = {};
  switch (arenaKey) {
    case "work":
      fallback = {
        posture: manual.decision_style || traits.mental?.bottom_line || "Thoughtful and methodical—you take time to understand the problem before diving in, and you take real pride in doing things right.",
        advantage: (superpowers[0]?.name) || "Spotting what's broken before others do",
        advantage_desc: (superpowers[0]?.manifestation) || (superpowers[0]?.description) || "When a situation gets chaotic, you don't panic. You quietly organize the mess and handle the hardest piece first.",
        tripwire: (shadows[0]?.name) || "Taking on everything yourself because you don't trust others to do it right",
        antidote: (shadows[0]?.antidote) || "Learn to let others help with the day-to-day work so you don't burn out carrying the whole load.",
        master_rule: levers.golden_lever || "Pick one important thing each day and do it well, rather than scattering your energy across ten things."
      };
      break;
    case "relationships":
      fallback = {
        posture: traits.social?.bottom_line || traits.emotional?.bottom_line || "Cautious and slow to trust at first, but deeply devoted and protective once someone is in your inner circle.",
        advantage: (superpowers[1]?.name) || (superpowers[0]?.name) || "A steady, reliable presence",
        advantage_desc: (superpowers[1]?.manifestation) || (superpowers[0]?.manifestation) || "You show love through practical care and showing up when it really matters, not through empty words.",
        tripwire: (shadows[1]?.name) || (shadows[0]?.name) || "Bottling up your feelings and hoping your partner guesses what's wrong",
        antidote: (shadows[1]?.antidote) || (shadows[0]?.antidote) || "Say what you need out loud in simple, kind words instead of pulling away into silent frustration.",
        master_rule: levers.habit_to_unlearn || "You are responsible for speaking your truth, but not for managing how the other person reacts to it."
      };
      break;
    case "crisis":
      fallback = {
        posture: manual.stress_response?.reaction || "Quiet and watchful—you pull back to catch your breath and figure out your next move.",
        advantage: (superpowers[2]?.name) || (superpowers[0]?.name) || "Quiet resilience under fire",
        advantage_desc: manual.stress_response?.recovery || "You reset best by stepping away from the noise, getting into quiet space, and letting your mind clear.",
        tripwire: manual.stress_response?.trigger || "Feeling trapped or having your independence stripped away.",
        antidote: (shadows[2]?.antidote) || (Array.isArray(manual.drainers) && manual.drainers[0]) || "Step back from the panic. Don't solve the next five years right now; just take the very next right step.",
        master_rule: "Never make big, irreversible life decisions when your mind and body are completely exhausted."
      };
      break;
    case "solo":
    default:
      fallback = {
        posture: theWhy.driving_hunger?.headline || "Needing real solitude to breathe, think clearly, and feel like yourself again.",
        advantage: (Array.isArray(manual.energizers) && manual.energizers[0]) || "Deep, uninterrupted creative flow",
        advantage_desc: theWhy.driving_hunger?.explanation || "Your energy and clarity return the moment you have time to think without anyone demanding your attention.",
        tripwire: (theWhy.comfort_zone_vs_growth_edge?.comfort_zone) || "Getting trapped in your own head and putting off action until everything feels 100% safe.",
        antidote: (theWhy.comfort_zone_vs_growth_edge?.growth_edge) || (shadows[3]?.antidote) || "Take a small step forward into the real world even when you still feel some self-doubt.",
        master_rule: levers.grounding_practice || "Give yourself at least thirty minutes of quiet each day before the noise of the world rushes in."
      };
      break;
  }

  const customArenas = d?.arenas || {};
  const a = customArenas[arenaKey] || {};

  return {
    posture: a.posture || fallback.posture,
    advantage: a.advantage || fallback.advantage,
    advantage_desc: a.advantage_manifestation || a.advantage_desc || fallback.advantage_desc,
    tripwire: a.tripwire || fallback.tripwire,
    antidote: a.antidote || a.defuser || fallback.antidote,
    master_rule: a.master_rule || fallback.master_rule
  };
}
window.getArenaData = getArenaData;

function renderArenaPanel(d, arenaKey) {
  const data = getArenaData(d, arenaKey);

  return `
    <div class="wwh-arena-grid">
      <!-- 1. Instinctive Posture -->
      <div class="wwh-arena-card posture">
        <div class="wwh-arena-card-tag">[HOW YOU RESPOND]</div>
        <div class="wwh-arena-card-title">How You Naturally Show Up</div>
        <p class="wwh-arena-card-desc">${escapeHtml(data.posture)}</p>
      </div>

      <!-- 2. Greatest Strength -->
      <div class="wwh-arena-card advantage">
        <div class="wwh-arena-card-tag">[YOUR GREATEST STRENGTH]</div>
        <div class="wwh-arena-card-title">${escapeHtml(data.advantage)}</div>
        <p class="wwh-arena-card-desc">${escapeHtml(data.advantage_desc)}</p>
      </div>

      <!-- 3. Recurring Trap & Fix -->
      <div class="wwh-arena-card tripwire">
        <div class="wwh-arena-card-tag">[THE RECURRING TRAP & FIX]</div>
        <div class="wwh-arena-card-title">${escapeHtml(data.tripwire)}</div>
        ${data.antidote ? `
        <div class="wwh-arena-antidote-strip">
          <span class="wwh-arena-antidote-tag">[THE EASY FIX]:</span> ${escapeHtml(data.antidote)}
        </div>
        ` : ""}
      </div>

      <!-- 4. Master Rule -->
      <div class="wwh-arena-card master">
        <div class="wwh-arena-card-tag">[THE GOLDEN RULE]</div>
        <div class="wwh-arena-card-title">The One Rule to Remember</div>
        <p class="wwh-arena-card-desc" style="font-weight: 600; color: var(--text-primary);">${escapeHtml(data.master_rule)}</p>
      </div>
    </div>
  `;
}
window.renderArenaPanel = renderArenaPanel;

let activeWwhData = null;

function switchWwhArena(e, arenaKey) {
  if (e) {
    if (e.preventDefault) e.preventDefault();
    if (e.stopPropagation) e.stopPropagation();
  }
  const container = e?.currentTarget?.closest(".wwh-arena-switcher-box");
  if (container) {
    container.querySelectorAll(".wwh-arena-pill").forEach(p => p.classList.remove("active"));
    if (e?.currentTarget) e.currentTarget.classList.add("active");
  }

  const pane = document.getElementById("wwh-arena-pane");
  if (!pane || !activeWwhData) return;
  pane.style.opacity = "0";
  setTimeout(() => {
    pane.innerHTML = renderArenaPanel(activeWwhData, arenaKey);
    pane.style.opacity = "1";
  }, 120);
}
window.switchWwhArena = switchWwhArena;

function renderArenaSwitcher(d) {
  activeWwhData = d;
  return `
    <div class="wwh-section-block" id="wwh-sec-arenas">
      <div class="wwh-section-header">
        <span class="wwh-section-tag">[HOW YOU SHOW UP]</span>
        <h3 class="wwh-section-title">How You Respond Across Different Situations</h3>
        <p class="wwh-section-subtitle" style="font-size: 0.86rem; color: var(--text-muted); margin-top: 0.25rem;">
          See how your instincts play out at work, in relationships, under pressure, and when you are by yourself.
        </p>
      </div>

      <div class="wwh-arena-switcher-box">
        <div class="wwh-arena-nav">
          <button type="button" class="wwh-arena-pill active" onclick="switchWwhArena(event, 'work')">At Work</button>
          <button type="button" class="wwh-arena-pill" onclick="switchWwhArena(event, 'relationships')">In Relationships</button>
          <button type="button" class="wwh-arena-pill" onclick="switchWwhArena(event, 'crisis')">Under Pressure</button>
          <button type="button" class="wwh-arena-pill" onclick="switchWwhArena(event, 'solo')">When You're Alone</button>
        </div>

        <div class="wwh-arena-content-pane" id="wwh-arena-pane" style="transition: opacity 0.2s ease;">
          ${renderArenaPanel(d, "work")}
        </div>
      </div>
    </div>
  `;
}
window.renderArenaSwitcher = renderArenaSwitcher;

function scrollToWwhSection(e, id) {
  if (e) {
    if (e.preventDefault) e.preventDefault();
    if (e.stopPropagation) e.stopPropagation();
  }
  const target = document.getElementById(id);
  if (!target) return;

  if (id === "wwh-sec-proof" || id.endsWith("-sec-proof")) {
    const content = target.querySelector(".wwh-proof-content");
    const chevron = target.querySelector(".proof-chevron");
    if (content && !content.classList.contains("open")) {
      content.classList.add("open");
      if (chevron) chevron.textContent = "▲";
    }
  }

  target.scrollIntoView({ behavior: "smooth", block: "start" });

  const container = target.closest(".what-why-how-container") || document;
  const pills = container.querySelectorAll(".wwh-nav-pill");
  pills.forEach((p) => p.classList.remove("active"));
  if (e && e.currentTarget) {
    e.currentTarget.classList.add("active");
  }
}
window.scrollToWwhSection = scrollToWwhSection;

function renderDilemmaCounselCard(dc, isCareer = false) {
  if (!dc) return "";
  const queryText = (dc.seeker_query || dc.seeker_situation || "").trim();
  // Do not render phantom query cards if there was no genuine user question
  if (!queryText || queryText === "Consultation Query" || queryText === "null" || queryText === '""') return "";

  const directAns = dc.direct_answer || "";
  const timeline = dc.exact_timeline || {};
  const primaryWin = timeline.primary_window || dc.timing_window || "";
  const secondaryWin = timeline.secondary_window || "";
  const dashaTrig = timeline.active_dasha_trigger || "";
  const transitTrig = timeline.transits_trigger || "";
  const astroReality = dc.astrological_reality || "";
  const guidance = dc.mentor_guidance || dc.mentor_verdict || "";

  if (!directAns && !primaryWin && !guidance) return "";

  const tagLabel = isCareer
    ? "[CAREER CONSULTATION &bull; DATED TIMELINE]"
    : "[SEEKER CONSULTATION &bull; DATED TIMELINE]";

  return `
    <div class="wwh-dilemma-card ${isCareer ? "cwp-dilemma-card" : ""}">
      <div class="wwh-dilemma-badge-row">
        <span class="wwh-dilemma-tag">${tagLabel}</span>
        ${primaryWin ? `<span class="wwh-dilemma-win-pill">Window: ${escapeHtml(primaryWin)}</span>` : ""}
      </div>
      ${queryText ? `
        <div class="wwh-dilemma-query-row">
          <span class="wwh-dilemma-q-label">QUESTION:</span>
          <span class="wwh-dilemma-title">"${escapeHtml(queryText)}"</span>
        </div>
      ` : ""}
      ${directAns ? `
        <div class="wwh-dilemma-direct-box">
          <span class="wwh-dilemma-direct-tag">[DIRECT VERDICT]:</span>
          <p class="wwh-dilemma-direct-text">${escapeHtml(directAns)}</p>
        </div>
      ` : ""}
      ${(primaryWin || dashaTrig || transitTrig) ? `
        <div class="wwh-dilemma-timing-grid">
          ${primaryWin ? `
            <div class="wwh-dilemma-time-card primary">
              <span class="wwh-time-card-tag">[PRIMARY TIMELINE WINDOW]:</span>
              <span class="wwh-time-card-val">${escapeHtml(primaryWin)}</span>
            </div>
          ` : ""}
          ${secondaryWin ? `
            <div class="wwh-dilemma-time-card secondary">
              <span class="wwh-time-card-tag">[SECONDARY WINDOW]:</span>
              <span class="wwh-time-card-val">${escapeHtml(secondaryWin)}</span>
            </div>
          ` : ""}
          ${dashaTrig ? `
            <div class="wwh-dilemma-time-card dasha">
              <span class="wwh-time-card-tag">[DASHA ACTIVATION]:</span>
              <span class="wwh-time-card-val">${escapeHtml(dashaTrig)}</span>
            </div>
          ` : ""}
          ${transitTrig ? `
            <div class="wwh-dilemma-time-card transit">
              <span class="wwh-time-card-tag">[TRANSIT CATALYST]:</span>
              <span class="wwh-time-card-val">${escapeHtml(transitTrig)}</span>
            </div>
          ` : ""}
        </div>
      ` : ""}
      ${astroReality ? `
        <p class="wwh-dilemma-reality">${escapeHtml(astroReality)}</p>
      ` : ""}
      ${guidance ? `
        <div class="wwh-dilemma-verdict-box">
          <span class="wwh-dilemma-verdict-tag">[PRACTICAL MENTOR GUIDANCE & SAFEGUARDS]:</span>
          <span class="wwh-dilemma-verdict-text">${escapeHtml(guidance)}</span>
        </div>
      ` : ""}
    </div>
  `;
}

function renderWhatWhyHowDeck(d) {
  if (!d) return "";

  const archetype = d.archetype || "The Grounded Seeker";
  const verdict = d.summary_verdict || "";
  const consti = d.constitution || {};
  const traits = d.traits || {};
  const theWhy = d.the_why || {};
  const qualities = d.qualities || {};
  const manual = d.operating_manual || {};
  const levers = d.growth_levers || {};
  const proof = d.astrological_proof || "";

  const elems = getElementalBreakdown(d);
  const totalElemPct = (elems.Fire + elems.Earth + elems.Air + elems.Water) || 100;
  const firePct = Math.round((elems.Fire / totalElemPct) * 100);
  const earthPct = Math.round((elems.Earth / totalElemPct) * 100);
  const airPct = Math.round((elems.Air / totalElemPct) * 100);
  const waterPct = Math.max(0, 100 - (firePct + earthPct + airPct));

  let html = `<div class="what-why-how-container">`;

  // 0. QUICK-JUMP MICRO-NAVIGATION
  html += `
    <nav class="wwh-sticky-nav">
      <button type="button" class="wwh-nav-pill active" onclick="scrollToWwhSection(event, 'wwh-sec-identity')">Overview</button>
      <button type="button" class="wwh-nav-pill" onclick="scrollToWwhSection(event, 'wwh-sec-traits')">Your Balance</button>
      <button type="button" class="wwh-nav-pill" onclick="scrollToWwhSection(event, 'wwh-sec-arenas')">Daily Life</button>
      <button type="button" class="wwh-nav-pill" onclick="scrollToWwhSection(event, 'wwh-sec-why')">The Why</button>
      <button type="button" class="wwh-nav-pill" onclick="scrollToWwhSection(event, 'wwh-sec-qualities')">Strengths & Blind Spots</button>
      <button type="button" class="wwh-nav-pill" onclick="scrollToWwhSection(event, 'wwh-sec-manual')">Your Rhythm</button>
      <button type="button" class="wwh-nav-pill" onclick="scrollToWwhSection(event, 'wwh-sec-levers')">Daily Wisdom</button>
      ${proof ? `<button type="button" class="wwh-nav-pill" onclick="scrollToWwhSection(event, 'wwh-sec-proof')">Technical Proof</button>` : ""}
    </nav>
  `;

  // 1. HERO IDENTITY CARD
  html += `
    <div class="wwh-hero-card" id="wwh-sec-identity">
      <div class="wwh-section-tag">[YOUR CORE NATURE]</div>
      <h2 class="wwh-hero-title">WHO YOU ARE AT YOUR CORE</h2>
      ${verdict ? `<div class="wwh-verdict">"${escapeHtml(verdict)}"</div>` : ""}
      
      <div class="wwh-badges-row">
        <span class="wwh-badge primary">ARCHETYPE: ${escapeHtml(archetype)}</span>
        ${consti.elements ? `<span class="wwh-badge">${escapeHtml(consti.elements)}</span>` : ""}
        ${consti.ayurvedic_prakriti ? `<span class="wwh-badge">${escapeHtml(consti.ayurvedic_prakriti)}</span>` : ""}
      </div>

      <div class="wwh-elements-bar-wrapper">
        <div class="wwh-elements-bar-head">
          <span class="wwh-elements-bar-title">YOUR ELEMENTAL BALANCE</span>
          <span class="wwh-elements-bar-ratio">Fire ${elems.Fire}% • Earth ${elems.Earth}% • Air ${elems.Air}% • Water ${elems.Water}%</span>
        </div>
        <div class="wwh-elements-progress-track">
          <div class="wwh-elem-seg fire" style="flex: ${firePct};" title="Fire: ${elems.Fire}%"></div>
          <div class="wwh-elem-seg earth" style="flex: ${earthPct};" title="Earth: ${elems.Earth}%"></div>
          <div class="wwh-elem-seg air" style="flex: ${airPct};" title="Air: ${elems.Air}%"></div>
          <div class="wwh-elem-seg water" style="flex: ${waterPct};" title="Water: ${elems.Water}%"></div>
        </div>
        <div class="wwh-elements-legend">
          <div class="wwh-legend-item"><span class="wwh-legend-dot fire"></span>Fire (Initiative & Will)</div>
          <div class="wwh-legend-item"><span class="wwh-legend-dot earth"></span>Earth (Structure & Execution)</div>
          <div class="wwh-legend-item"><span class="wwh-legend-dot air"></span>Air (Intellect & Perspective)</div>
          <div class="wwh-legend-item"><span class="wwh-legend-dot water"></span>Water (Instinct & Depth)</div>
        </div>
      </div>

      <div class="wwh-triad-strip">
        <div class="wwh-triad-col">
          <span class="wwh-triad-role">OUTER INSTINCT</span>
          <span class="wwh-triad-val">${escapeHtml(consti.natural_instinct_tag || consti.lagna_tag || "-")}</span>
        </div>
        <div class="wwh-triad-col">
          <span class="wwh-triad-role">EMOTIONAL CORE</span>
          <span class="wwh-triad-val">${escapeHtml(consti.emotional_anchor_tag || consti.moon_tag || "-")}</span>
        </div>
        <div class="wwh-triad-col">
          <span class="wwh-triad-role">CORE DRIVE</span>
          <span class="wwh-triad-val">${escapeHtml(consti.core_drive_tag || consti.sun_tag || "-")}</span>
        </div>
        <div class="wwh-triad-col">
          <span class="wwh-triad-role">DEEPEST HUNGER</span>
          <span class="wwh-triad-val">${escapeHtml(consti.deepest_hunger_tag || consti.atmakaraka_tag || "-")}</span>
        </div>
      </div>
    </div>
  `;

  // 1.1 GROUNDED CURRENT LIFE SEASON CARD (WHERE YOU STAND TODAY)
  if (d.current_life_season) {
    const season = d.current_life_season;
    html += `
      <div class="wwh-season-card">
        <div class="wwh-season-badge-row">
          <span class="wwh-season-tag">[WHERE YOU STAND TODAY]</span>
          <span class="wwh-season-cycle">Operating Cycle: ${new Date().getFullYear()}</span>
        </div>
        <h3 class="wwh-season-headline">${escapeHtml(season.headline || "Your Current Life Chapter")}</h3>
        <p class="wwh-season-desc">${escapeHtml(season.season_summary || "")}</p>
        ${(season.what_to_lean_into || season.what_to_leave_behind) ? `
          <div class="wwh-season-split">
            ${season.what_to_lean_into ? `
              <div class="wwh-season-col lean">
                <span class="wwh-season-col-tag">[WHAT TO LEAN INTO]:</span>
                <span class="wwh-season-col-text">${escapeHtml(season.what_to_lean_into)}</span>
              </div>
            ` : ""}
            ${season.what_to_leave_behind ? `
              <div class="wwh-season-col leave">
                <span class="wwh-season-col-tag">[WHAT TO LEAVE BEHIND]:</span>
                <span class="wwh-season-col-text">${escapeHtml(season.what_to_leave_behind)}</span>
              </div>
            ` : ""}
          </div>
        ` : ""}
      </div>
    `;
  }

  // 1.2 GROUNDED SEEKER QUERY & DATED TIMELINE COUNSEL (Only render when a genuine query was asked)
  const userTypedQuery = (document.getElementById("ai-custom-query-input")?.value || "").trim();
  const rawQuery = (d.dilemma_counsel?.seeker_query || userTypedQuery || "").trim();
  const hasGenuineQuery = Boolean(rawQuery && rawQuery !== "Consultation Query" && rawQuery !== "null");
  if (hasGenuineQuery && d.dilemma_counsel) {
    html += renderDilemmaCounselCard({ ...d.dilemma_counsel, seeker_query: rawQuery }, false);
  }

  // 2. CONSTITUTIONAL POLARITY MATRIX (HOW YOU'RE WIRED)
  html += renderPolaritySpectrum(d);

  // 3. CONTEXTUAL ARENA OPERATING CONSOLE (HOW YOU SHOW UP)
  html += renderArenaSwitcher(d);

  // 4. THE WHY: INNER CONTRADICTIONS & TRUE MOTIVATIONS
  html += `
    <div class="wwh-section-block" id="wwh-sec-why">
      <div class="wwh-section-header">
        <span class="wwh-section-tag">[WHY YOU ACT THE WAY YOU DO]</span>
        <h3 class="wwh-section-title">Your Inner Contradictions & True Motivations</h3>
      </div>

      <div class="wwh-why-grid">
        ${theWhy.inner_paradox ? `
          <div class="wwh-why-card paradox">
            <div class="wwh-why-tag">[THE INNER CONTRADICTION]</div>
            <div class="wwh-why-title">${escapeHtml(theWhy.inner_paradox.headline || theWhy.inner_paradox.title || "The Inner Contradiction")}</div>
            <p class="wwh-why-desc">${escapeHtml(theWhy.inner_paradox.explanation || "")}</p>
          </div>
        ` : ""}
        ${theWhy.driving_hunger ? `
          <div class="wwh-why-card hunger">
            <div class="wwh-why-tag">[THE DEEP FUEL]</div>
            <div class="wwh-why-title">${escapeHtml(theWhy.driving_hunger.headline || theWhy.driving_hunger.title || "What Truly Moves You")}</div>
            <p class="wwh-why-desc">${escapeHtml(theWhy.driving_hunger.explanation || "")}</p>
          </div>
        ` : ""}
        ${(theWhy.comfort_zone_vs_growth_edge || theWhy.karmic_axis) ? `
          <div class="wwh-why-card axis">
            <div class="wwh-why-tag">[THE GROWTH EDGE]</div>
            <div class="wwh-why-title">${escapeHtml(theWhy.comfort_zone_vs_growth_edge?.headline || theWhy.karmic_axis?.title || "The Safe Trap vs. The Real Growth")}</div>
            ${theWhy.comfort_zone_vs_growth_edge?.comfort_zone ? `
              <div class="wwh-karmic-split">
                <div class="wwh-karmic-row">
                  <span class="wwh-karmic-tag">[THE SAFE TRAP]:</span>
                  <span class="wwh-karmic-text">${escapeHtml(theWhy.comfort_zone_vs_growth_edge.comfort_zone)}</span>
                </div>
                <div class="wwh-karmic-row growth">
                  <span class="wwh-karmic-tag growth">[THE REAL GROWTH]:</span>
                  <span class="wwh-karmic-text">${escapeHtml(theWhy.comfort_zone_vs_growth_edge.growth_edge)}</span>
                </div>
              </div>
            ` : `<p class="wwh-why-desc">${escapeHtml(theWhy.karmic_axis?.explanation || "")}</p>`}
          </div>
        ` : ""}
      </div>
    </div>
  `;

  // 5. QUALITIES: STRENGTHS & BLIND SPOTS
  const superpowers = Array.isArray(qualities.superpowers) ? qualities.superpowers : [];
  const shadows = Array.isArray(qualities.shadows) ? qualities.shadows : [];

  if (superpowers.length || shadows.length) {
    html += `
      <div class="wwh-section-block" id="wwh-sec-qualities">
        <div class="wwh-section-header">
          <span class="wwh-section-tag">[STRENGTHS & BLIND SPOTS]</span>
          <h3 class="wwh-section-title">What Gives You Wings & What Trips You Up</h3>
        </div>

        <div class="wwh-qualities-split">
          <!-- Superpowers Column -->
          <div class="wwh-qualities-col superpowers">
            <div class="wwh-qualities-col-header">
              <span class="wwh-col-label">[+] YOUR NATURAL GIFTS</span>
            </div>
            <div class="wwh-qualities-list">
              ${superpowers.map((sp, idx) => `
                <div class="wwh-quality-item power">
                  <div class="wwh-quality-title">${escapeHtml(sp.name || sp.title || `Gift ${idx + 1}`)}</div>
                  <p class="wwh-quality-desc">${escapeHtml(sp.description || "")}</p>
                  ${sp.manifestation ? `
                    <div class="wwh-quality-context power">
                      <span class="wwh-quality-context-tag">[WHEN IT SHINES]:</span> ${escapeHtml(sp.manifestation)}
                    </div>
                  ` : ""}
                </div>
              `).join("")}
            </div>
          </div>

          <!-- Shadows Column -->
          <div class="wwh-qualities-col shadows">
            <div class="wwh-qualities-col-header">
              <span class="wwh-col-label">[-] RECURRING BLIND SPOTS</span>
            </div>
            <div class="wwh-qualities-list">
              ${shadows.map((sh, idx) => `
                <div class="wwh-quality-item shadow">
                  <div class="wwh-quality-title">${escapeHtml(sh.name || sh.title || `Blind Spot ${idx + 1}`)}</div>
                  <p class="wwh-quality-desc">${escapeHtml(sh.description || "")}</p>
                  ${sh.antidote ? `
                    <div class="wwh-quality-context shadow">
                      <span class="wwh-quality-context-tag">[THE EASY FIX]:</span> ${escapeHtml(sh.antidote)}
                    </div>
                  ` : ""}
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // 6. HOW YOU OPERATE: YOUR DAILY RHYTHM
  html += `
    <div class="wwh-section-block" id="wwh-sec-manual">
      <div class="wwh-section-header">
        <span class="wwh-section-tag">[YOUR DAILY RHYTHM]</span>
        <h3 class="wwh-section-title">How to Protect Your Energy, Peace & Focus</h3>
      </div>

      <div class="wwh-manual-grid">
        <!-- Stress Protocol -->
        ${manual.stress_response ? `
          <div class="wwh-manual-card stress">
            <div class="wwh-manual-title">WHAT HAPPENS WHEN OVERWHELMED</div>
            <div class="wwh-stress-row">
              <span class="wwh-stress-tag">THE SPARK:</span>
              <span class="wwh-stress-text">${escapeHtml(manual.stress_response.trigger || "-")}</span>
            </div>
            <div class="wwh-stress-row">
              <span class="wwh-stress-tag">YOUR GUT REACTION:</span>
              <span class="wwh-stress-text">${escapeHtml(manual.stress_response.reaction || "-")}</span>
            </div>
            <div class="wwh-stress-row">
              <span class="wwh-stress-tag">HOW TO RESET:</span>
              <span class="wwh-stress-text">${escapeHtml(manual.stress_response.recovery || "-")}</span>
            </div>
          </div>
        ` : ""}

        <!-- Energizers & Drainers Split -->
        <div class="wwh-manual-card energy">
          <div class="wwh-manual-title">WHAT FEEDS YOU & WHAT DRAINS YOU</div>
          <div class="wwh-energy-split">
            <div class="wwh-energy-subcol">
              <span class="wwh-energy-label">[+] WHAT GIVES YOU ENERGY</span>
              <ul class="wwh-energy-list">
                ${(manual.energizers || []).map(en => `<li>${escapeHtml(en)}</li>`).join("")}
              </ul>
            </div>
            <div class="wwh-energy-subcol">
              <span class="wwh-energy-label">[-] WHAT DRAINS YOUR BATTERY</span>
              <ul class="wwh-energy-list drainers">
                ${(manual.drainers || []).map(dr => `<li>${escapeHtml(dr)}</li>`).join("")}
              </ul>
            </div>
          </div>
        </div>

        <!-- Decision Instinct -->
        ${manual.decision_style ? `
          <div class="wwh-manual-card decision">
            <div class="wwh-manual-title">HOW YOU MAKE BIG DECISIONS</div>
            <p class="wwh-decision-text">${escapeHtml(manual.decision_style)}</p>
          </div>
        ` : ""}
      </div>
    </div>
  `;

  // 7. ACTIONABLE DAILY WISDOM
  html += `
    <div class="wwh-section-block" id="wwh-sec-levers">
      <div class="wwh-section-header">
        <span class="wwh-section-tag">[DAILY WISDOM]</span>
        <h3 class="wwh-section-title">Three Grounded Rules for Peace & Growth</h3>
      </div>

      <div class="wwh-levers-grid">
        <div class="wwh-lever-card golden">
          <div class="wwh-lever-tag">[THE GOLDEN RULE]</div>
          <div class="wwh-lever-title">The One Shift That Changes Everything</div>
          <p class="wwh-lever-desc">${escapeHtml(levers.golden_lever || "Focus on one important thing each day rather than scattering your energy.")}</p>
        </div>

        <div class="wwh-lever-card unlearn">
          <div class="wwh-lever-tag">[THE OLD HABIT]</div>
          <div class="wwh-lever-title">What to Catch & Let Go Of</div>
          <p class="wwh-lever-desc">${escapeHtml(levers.habit_to_unlearn || "Carrying burdens and responsibilities that are not yours to fix.")}</p>
        </div>

        <div class="wwh-lever-card anchor">
          <div class="wwh-lever-tag">[DAILY ANCHOR]</div>
          <div class="wwh-lever-title">A Simple Habit to Keep You Centered</div>
          <p class="wwh-lever-desc">${escapeHtml(levers.grounding_practice || "A few minutes of quiet stillness every morning before the day's noise begins.")}</p>
        </div>
      </div>
    </div>
  `;

  // 8. COLLAPSIBLE ASTROLOGICAL PROOF
  if (proof) {
    html += `
      <div class="wwh-proof-accordion" id="wwh-sec-proof">
        <button type="button" class="wwh-proof-toggle" onclick="toggleLifeProof(this)">
          <span style="display:flex; align-items:center; gap:0.5rem;">
            <strong>[+] Classical Astrological Footnotes & Technical Derivations</strong>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:normal;">(Parashari • KP • Jaimini)</span>
          </span>
          <span class="proof-chevron">▼</span>
        </button>
        <div class="wwh-proof-content">
          <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.75rem; font-style:italic;">
            Cross-system technical derivations reconciling BPHS planetary yogas and dignities, KP cuspal sub-lords 1–249, and Jaimini Chara Karakas.
          </p>
          <div class="markdown-body">
            ${formatMarkdown(proof)}
          </div>
        </div>
      </div>
    `;
  }

  html += `</div>`; // .what-why-how-container
  return html;
}
window.renderWhatWhyHowDeck = renderWhatWhyHowDeck;

function scrollToCwpSection(e, targetId) {
  if (e && e.preventDefault) e.preventDefault();
  const target = document.getElementById(targetId);
  if (!target) return;

  target.scrollIntoView({ behavior: "smooth", block: "start" });

  const container = target.closest(".cwp-container") || document;
  const pills = container.querySelectorAll(".cwp-nav-pill");
  pills.forEach((p) => p.classList.remove("active"));
  if (e && e.currentTarget) {
    e.currentTarget.classList.add("active");
  }
}
window.scrollToCwpSection = scrollToCwpSection;

function renderCraftWealthDeck(d) {
  if (!d) return "";

  const archetype = d.vocation_archetype || d.archetype || "The Sovereign Strategist";
  const verdict = d.summary_verdict || "";
  const genius = d.work_genius || {};
  const leadership = d.leadership_and_authority || {};
  const wealth = d.wealth_engine || {};
  const enterprise = d.enterprise_vs_employment || {};
  const timing = d.timing_weather || {};
  const levers = d.tactical_levers || {};
  const proof = d.astrological_proof || "";

  let html = `<div class="cwp-container what-why-how-container">`;

  // 0. QUICK-JUMP MICRO-NAVIGATION
  html += `
    <nav class="wwh-sticky-nav cwp-sticky-nav">
      <button type="button" class="wwh-nav-pill cwp-nav-pill active" onclick="scrollToCwpSection(event, 'cwp-sec-overview')">Overview</button>
      <button type="button" class="wwh-nav-pill cwp-nav-pill" onclick="scrollToCwpSection(event, 'cwp-sec-genius')">Your Craft</button>
      <button type="button" class="wwh-nav-pill cwp-nav-pill" onclick="scrollToCwpSection(event, 'cwp-sec-leadership')">Leadership</button>
      <button type="button" class="wwh-nav-pill cwp-nav-pill" onclick="scrollToCwpSection(event, 'cwp-sec-wealth')">Wealth & Money</button>
      <button type="button" class="wwh-nav-pill cwp-nav-pill" onclick="scrollToCwpSection(event, 'cwp-sec-vehicle')">Career Path</button>
      <button type="button" class="wwh-nav-pill cwp-nav-pill" onclick="scrollToCwpSection(event, 'cwp-sec-timing')">Timing Windows</button>
      <button type="button" class="wwh-nav-pill cwp-nav-pill" onclick="scrollToCwpSection(event, 'cwp-sec-levers')">Work Rules</button>
      ${proof ? `<button type="button" class="wwh-nav-pill cwp-nav-pill" onclick="scrollToCwpSection(event, 'cwp-sec-proof')">Technical Proof</button>` : ""}
    </nav>
  `;

  // 1. HERO IDENTITY CARD
  html += `
    <div class="wwh-hero-card cwp-hero-card" id="cwp-sec-overview">
      <div class="wwh-section-tag">[YOUR WORK, WEALTH & CALLING]</div>
      <h2 class="wwh-hero-title">CRAFT, WEALTH & PUBLIC CALLING</h2>
      ${verdict ? `<div class="wwh-verdict">"${escapeHtml(verdict)}"</div>` : ""}
      
      <div class="wwh-badges-row">
        <span class="wwh-badge primary">VOCATION: ${escapeHtml(archetype)}</span>
        ${enterprise.recommended_path ? `<span class="wwh-badge">${escapeHtml(enterprise.recommended_path)}</span>` : ""}
        ${wealth.wealth_archetype ? `<span class="wwh-badge">${escapeHtml(wealth.wealth_archetype)}</span>` : ""}
        ${timing.current_season_headline ? `<span class="wwh-badge">${escapeHtml(timing.current_season_headline)}</span>` : ""}
      </div>

      <div class="wwh-triad-strip cwp-quad-strip">
        <div class="wwh-triad-col">
          <span class="wwh-triad-role">NATURAL CRAFT</span>
          <span class="wwh-triad-val">${escapeHtml(genius.craft_essence?.headline || "-")}</span>
        </div>
        <div class="wwh-triad-col">
          <span class="wwh-triad-role">LEADERSHIP STYLE</span>
          <span class="wwh-triad-val">${escapeHtml(leadership.leadership_stance?.headline || leadership.leadership_stance?.style || "-")}</span>
        </div>
        <div class="wwh-triad-col">
          <span class="wwh-triad-role">WEALTH STYLE</span>
          <span class="wwh-triad-val">${escapeHtml(wealth.wealth_archetype || "-")}</span>
        </div>
        <div class="wwh-triad-col">
          <span class="wwh-triad-role">BEST WORK SETUP</span>
          <span class="wwh-triad-val">${escapeHtml(enterprise.optimal_vehicle || enterprise.recommended_path || "-")}</span>
        </div>
      </div>
    </div>
  `;

  // 1.1 SEEKER'S VOCATIONAL CROSSROADS & DATED TIMELINE COUNSEL (Only render when a genuine query was asked)
  const userTypedQuery = (document.getElementById("ai-custom-query-input")?.value || "").trim();
  const rawQuery = (d.dilemma_counsel?.seeker_query || userTypedQuery || "").trim();
  const hasGenuineQuery = Boolean(rawQuery && rawQuery !== "Consultation Query" && rawQuery !== "null");
  if (hasGenuineQuery && d.dilemma_counsel) {
    html += renderDilemmaCounselCard({ ...d.dilemma_counsel, seeker_query: rawQuery }, true);
  }

  // 2. NATURAL WORK GENIUS & FLOW STATE
  if (genius.craft_essence || genius.autonomy_vs_hierarchy || genius.flow_state_trigger || genius.ideal_work_environment) {
    html += `
      <div class="wwh-section-block" id="cwp-sec-genius">
        <div class="wwh-section-header">
          <span class="wwh-section-tag">[YOUR WORK GENIUS & FLOW]</span>
          <h3 class="wwh-section-title">How You Work Best & Where You Excel</h3>
        </div>

        <div class="wwh-why-grid cwp-genius-grid">
          ${genius.craft_essence ? `
            <div class="wwh-why-card cwp-genius-card craft">
              <div class="wwh-why-tag">[YOUR CORE WORK GENIUS]</div>
              <div class="wwh-why-title">${escapeHtml(genius.craft_essence.headline || "Core Problem-Solving Mastery")}</div>
              <p class="wwh-why-desc">${escapeHtml(genius.craft_essence.description || "")}</p>
              ${genius.craft_essence.real_world_scenario ? `
                <div class="wwh-quality-context power" style="margin-top: 0.85rem;">
                  <span class="wwh-quality-context-tag">[TUESDAY MORNING TEST]:</span> ${escapeHtml(genius.craft_essence.real_world_scenario)}
                </div>
              ` : ""}
            </div>
          ` : ""}

          ${genius.autonomy_vs_hierarchy ? `
            <div class="wwh-why-card cwp-genius-card autonomy">
              <div class="wwh-why-tag">[HOW MUCH FREEDOM YOU NEED]</div>
              <div class="wwh-why-title">${escapeHtml(genius.autonomy_vs_hierarchy.headline || "Relationship with Authority")}</div>
              <p class="wwh-why-desc">${escapeHtml(genius.autonomy_vs_hierarchy.stance || "")}</p>
              ${genius.autonomy_vs_hierarchy.friction_trigger ? `
                <div class="wwh-quality-context shadow" style="margin-top: 0.85rem;">
                  <span class="wwh-quality-context-tag">[WHAT DRAINS YOUR DRIVE]:</span> ${escapeHtml(genius.autonomy_vs_hierarchy.friction_trigger)}
                </div>
              ` : ""}
            </div>
          ` : ""}

          ${genius.flow_state_trigger ? `
            <div class="wwh-why-card cwp-genius-card flow">
              <div class="wwh-why-tag">[WHEN YOU'RE IN THE ZONE]</div>
              <div class="wwh-why-title">${escapeHtml(genius.flow_state_trigger.headline || "Peak Focus Catalyst")}</div>
              <p class="wwh-why-desc">${escapeHtml(genius.flow_state_trigger.conditions || "")}</p>
            </div>
          ` : ""}

          ${genius.ideal_work_environment ? `
            <div class="wwh-why-card cwp-genius-card env">
              <div class="wwh-why-tag">[THE WORK ENVIRONMENT YOU NEED]</div>
              <div class="wwh-why-title">${escapeHtml(genius.ideal_work_environment.headline || "Ideal Cultural & Physical Arena")}</div>
              <p class="wwh-why-desc">${escapeHtml(genius.ideal_work_environment.description || "")}</p>
            </div>
          ` : ""}
        </div>
      </div>
    `;
  }

  // 3. LEADERSHIP, AUTHORITY & WORKPLACE PRESENCE
  if (leadership.leadership_stance || leadership.office_politics_reflex || leadership.delegation_tripwire || leadership.public_presence) {
    html += `
      <div class="wwh-section-block" id="cwp-sec-leadership">
        <div class="wwh-section-header">
          <span class="wwh-section-tag">[HOW YOU LEAD & HOW OTHERS SEE YOU]</span>
          <h3 class="wwh-section-title">How You Handle Power, Politics & People</h3>
        </div>

        <div class="wwh-traits-grid cwp-leadership-grid">
          ${leadership.leadership_stance ? `
            <div class="wwh-trait-card cwp-lead-card">
              <div class="wwh-trait-head">
                <span class="wwh-trait-label">[HOW YOU LEAD]</span>
              </div>
              <div class="wwh-trait-headline">${escapeHtml(leadership.leadership_stance.headline || "Command & Authority")}</div>
              <p class="wwh-trait-desc">${escapeHtml(leadership.leadership_stance.style || "")}</p>
              ${leadership.leadership_stance.how_others_perceive_you ? `
                <div class="wwh-quality-context power" style="margin-top: 0.75rem;">
                  <span class="wwh-quality-context-tag">[HOW OTHERS ACTUALLY SEE YOU]:</span> ${escapeHtml(leadership.leadership_stance.how_others_perceive_you)}
                </div>
              ` : ""}
            </div>
          ` : ""}

          ${leadership.office_politics_reflex ? `
            <div class="wwh-trait-card cwp-lead-card">
              <div class="wwh-trait-head">
                <span class="wwh-trait-label">[HOW YOU HANDLE WORKPLACE POLITICS]</span>
              </div>
              <div class="wwh-trait-headline">${escapeHtml(leadership.office_politics_reflex.headline || "Navigating Friction")}</div>
              <p class="wwh-trait-desc">${escapeHtml(leadership.office_politics_reflex.reflex || "")}</p>
              ${leadership.office_politics_reflex.antidote ? `
                <div class="wwh-quality-context shadow" style="margin-top: 0.75rem;">
                  <span class="wwh-quality-context-tag">[HOW TO PROTECT YOURSELF]:</span> ${escapeHtml(leadership.office_politics_reflex.antidote)}
                </div>
              ` : ""}
            </div>
          ` : ""}

          ${leadership.delegation_tripwire ? `
            <div class="wwh-trait-card cwp-lead-card">
              <div class="wwh-trait-head">
                <span class="wwh-trait-label">[THE DELEGATION & TRUST TRAP]</span>
              </div>
              <div class="wwh-trait-headline">${escapeHtml(leadership.delegation_tripwire.headline || "The Delegation Bottleneck")}</div>
              <p class="wwh-trait-desc">${escapeHtml(leadership.delegation_tripwire.trap || "")}</p>
              ${leadership.delegation_tripwire.fix ? `
                <div class="wwh-quality-context shadow" style="margin-top: 0.75rem;">
                  <span class="wwh-quality-context-tag">[HOW TO FIX THIS]:</span> ${escapeHtml(leadership.delegation_tripwire.fix)}
                </div>
              ` : ""}
            </div>
          ` : ""}

          ${leadership.public_presence ? `
            <div class="wwh-trait-card cwp-lead-card">
              <div class="wwh-trait-head">
                <span class="wwh-trait-label">[PUBLIC REPUTATION VS. PRIVATE REALITY]</span>
              </div>
              <div class="wwh-trait-headline">${escapeHtml(leadership.public_presence.headline || "Public vs. Private Stance")}</div>
              <div style="font-size: 0.86rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: 0.5rem;">
                <strong style="color: var(--accent-primary);">What People See Outside:</strong> ${escapeHtml(leadership.public_presence.external_reputation || "")}
              </div>
              <div style="font-size: 0.86rem; color: var(--text-muted); line-height: 1.5;">
                <strong style="color: var(--text-primary);">What You Feel Inside:</strong> ${escapeHtml(leadership.public_presence.internal_reality || "")}
              </div>
            </div>
          ` : ""}
        </div>
      </div>
    `;
  }

  // 4. WEALTH ENGINE & FINANCIAL DYNAMICS
  if (wealth.primary_inflow_channel || wealth.unconscious_financial_leak || wealth.monetization_rule) {
    html += `
      <div class="wwh-section-block" id="cwp-sec-wealth">
        <div class="wwh-section-header">
          <span class="wwh-section-tag">[HOW MONEY & WEALTH WORK FOR YOU]</span>
          <h3 class="wwh-section-title">Where Money Comes In, Where It Leaks & Your Golden Rule</h3>
        </div>

        <div class="wwh-qualities-split cwp-wealth-split">
          <!-- Inflows -->
          ${wealth.primary_inflow_channel ? `
            <div class="wwh-qualities-col superpowers">
              <div class="wwh-qualities-col-header">
                <span class="wwh-col-label">[WHERE MONEY FLOWS NATURALLY]</span>
              </div>
              <div class="wwh-qualities-list">
                <div class="wwh-quality-item power">
                  <div class="wwh-quality-title">${escapeHtml(wealth.primary_inflow_channel.headline || "Natural Wealth Inflow")}</div>
                  <p class="wwh-quality-desc">${escapeHtml(wealth.primary_inflow_channel.description || "")}</p>
                </div>
              </div>
            </div>
          ` : ""}

          <!-- Financial Leak -->
          ${wealth.unconscious_financial_leak ? `
            <div class="wwh-qualities-col shadows">
              <div class="wwh-qualities-col-header">
                <span class="wwh-col-label">[THE HIDDEN MONEY LEAK]</span>
              </div>
              <div class="wwh-qualities-list">
                <div class="wwh-quality-item shadow">
                  <div class="wwh-quality-title">${escapeHtml(wealth.unconscious_financial_leak.headline || "The Subtle Resource Drain")}</div>
                  <p class="wwh-quality-desc">${escapeHtml(wealth.unconscious_financial_leak.leak_pattern || "")}</p>
                  ${wealth.unconscious_financial_leak.antidote ? `
                    <div class="wwh-quality-context shadow" style="margin-top: 0.65rem;">
                      <span class="wwh-quality-context-tag">[HOW TO PLUG THIS LEAK]:</span> ${escapeHtml(wealth.unconscious_financial_leak.antidote)}
                    </div>
                  ` : ""}
                </div>
              </div>
            </div>
          ` : ""}
        </div>

        ${wealth.monetization_rule ? (() => {
          const mObj = typeof wealth.monetization_rule === "object" ? wealth.monetization_rule : { rule: String(wealth.monetization_rule) };
          const ruleText = mObj.rule || "";
          const headText = mObj.headline || "";
          const isGenericHeadline = !headText || /^(the\s+)?golden\s+(economic\s+)?rule$/i.test(headText.trim());
          const showHeadline = !isGenericHeadline && headText && headText !== ruleText;
          const bodyText = ruleText || headText || "";
          return `
            <div class="wwh-golden-strip cwp-monetization-strip" style="margin-top: 1.5rem;">
              <div class="wwh-golden-header">
                <span class="wwh-golden-tag">[YOUR GOLDEN MONEY RULE]</span>
                ${showHeadline ? `<span class="wwh-golden-headline">${escapeHtml(headText)}</span>` : ""}
              </div>
              <p class="wwh-golden-text">${escapeHtml(bodyText)}</p>
            </div>
          `;
        })() : ""}
      </div>
    `;
  }

  // 5. ENTERPRISE VS EMPLOYMENT CRUCIBLE
  if (enterprise.recommended_path || enterprise.strategic_rationale || enterprise.optimal_vehicle) {
    html += `
      <div class="wwh-section-block" id="cwp-sec-vehicle">
        <div class="wwh-section-header">
          <span class="wwh-section-tag">[BUILDING YOUR OWN THING VS. WORKING FOR OTHERS]</span>
          <h3 class="wwh-section-title">What Kind of Career Structure Fits You Best</h3>
        </div>

        <div class="cwp-vehicle-box" style="padding: 1.5rem; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);">
          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 0.85rem;">
            <div>
              <span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 800; color: var(--accent-primary);">[YOUR NATURAL FIT]</span>
              <h4 style="font-size: 1.2rem; font-weight: 700; color: var(--text-primary); margin: 0.25rem 0 0 0;">${escapeHtml(enterprise.recommended_path || "Sovereign Specialist")}</h4>
            </div>
            ${enterprise.optimal_vehicle ? `
              <div style="padding: 0.4rem 0.85rem; background: rgba(200, 155, 60, 0.12); border: 1px solid rgba(200, 155, 60, 0.35); border-radius: var(--radius-full); font-size: 0.82rem; font-weight: 700; color: var(--accent-primary);">
                Best Career Setup: ${escapeHtml(enterprise.optimal_vehicle)}
              </div>
            ` : ""}
          </div>

          <p style="font-size: 0.94rem; line-height: 1.6; color: var(--text-secondary); margin-bottom: 1.25rem;">
            ${escapeHtml(enterprise.strategic_rationale || "")}
          </p>

          ${enterprise.transition_guardrail ? `
            <div style="padding: 0.85rem 1.15rem; background: rgba(239, 68, 68, 0.08); border-left: 3px solid #EF4444; border-radius: 0 var(--radius-md) var(--radius-md) 0; font-size: 0.86rem; color: var(--text-secondary); line-height: 1.5;">
              <strong style="color: #EF4444; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; display: block; margin-bottom: 0.2rem;">[WATCH OUT FOR THIS BEFORE SWITCHING]</strong>
              ${escapeHtml(enterprise.transition_guardrail)}
            </div>
          ` : ""}
        </div>
      </div>
    `;
  }

  // 6. THE CAREER WEATHER & TIMING WINDOWS
  if (timing.current_season_headline || (Array.isArray(timing.windows) && timing.windows.length)) {
    const windows = Array.isArray(timing.windows) ? timing.windows : [];
    html += `
      <div class="wwh-section-block" id="cwp-sec-timing">
        <div class="wwh-section-header">
          <span class="wwh-section-tag">[WHERE YOUR CAREER IS HEADING (NEXT 24 MONTHS)]</span>
          <h3 class="wwh-section-title">Your Current Career Chapter & What Lies Ahead</h3>
        </div>

        ${timing.current_season_headline ? `
          <div style="margin-bottom: 1.25rem; padding: 1.15rem 1.35rem; background: linear-gradient(135deg, rgba(200, 155, 60, 0.12), rgba(200, 155, 60, 0.04)); border: 1px solid rgba(200, 155, 60, 0.35); border-radius: var(--radius-md);">
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent-primary); font-weight: 800; margin-bottom: 0.35rem;">
              [CURRENT WORK CHAPTER]: ${escapeHtml(timing.current_season_headline)}
            </div>
            ${timing.current_phase_nature ? `
              <p style="font-size: 0.94rem; color: var(--text-primary); line-height: 1.5; margin: 0;">${escapeHtml(timing.current_phase_nature)}</p>
            ` : ""}
          </div>
        ` : ""}

        ${windows.length ? `
          <div class="cwp-timing-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
            ${windows.map((win, idx) => `
              <div class="cwp-timing-card" style="padding: 1.25rem; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); display: flex; flex-direction: column; gap: 0.75rem;">
                <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 0.6rem;">
                  <span style="font-size: 0.72rem; font-family: var(--font-mono); font-weight: 800; color: var(--accent-primary); text-transform: uppercase;">${escapeHtml(win.window_label || `Window ${idx + 1}`)}</span>
                  <span style="font-size: 0.85rem; font-weight: 700; color: var(--text-primary);">${escapeHtml(win.phase_title || "")}</span>
                </div>
                ${win.focus ? `
                  <div style="font-size: 0.86rem; line-height: 1.5; color: var(--text-secondary);">
                    <strong style="color: #10B981; font-size: 0.75rem; display: block; margin-bottom: 0.2rem;">[WHAT TO FOCUS ON]:</strong>
                    ${escapeHtml(win.focus)}
                  </div>
                ` : ""}
                ${win.caution ? `
                  <div style="font-size: 0.84rem; line-height: 1.5; color: var(--text-muted); background: rgba(0,0,0,0.02); padding: 0.6rem; border-radius: var(--radius-sm); border-left: 2px solid var(--border-subtle);">
                    <strong style="color: #F59E0B; font-size: 0.75rem; display: block; margin-bottom: 0.2rem;">[WHAT TO AVOID]:</strong>
                    ${escapeHtml(win.caution)}
                  </div>
                ` : ""}
              </div>
            `).join("")}
          </div>
        ` : ""}
      </div>
    `;
  }

  // 7. TACTICAL CAREER LEVERS
  if (levers.golden_career_lever || levers.trap_to_eliminate || levers.negotiation_mantra) {
    html += `
      <div class="wwh-section-block" id="cwp-sec-levers">
        <div class="wwh-section-header">
          <span class="wwh-section-tag">[PRACTICAL WORK RULES FOR EVERYDAY LIFE]</span>
          <h3 class="wwh-section-title">Three Ground Rules to Work Smarter and Earn Fairly</h3>
        </div>

        <div class="wwh-levers-grid">
          ${levers.golden_career_lever ? `
            <div class="wwh-lever-card golden">
              <div class="wwh-lever-tag">[THE SINGLE BEST CAREER HABIT]</div>
              <div class="wwh-lever-title">The Daily Habit That Makes the Biggest Difference</div>
              <p class="wwh-lever-desc">${escapeHtml(levers.golden_career_lever)}</p>
            </div>
          ` : ""}

          ${levers.trap_to_eliminate ? `
            <div class="wwh-lever-card unlearn">
              <div class="wwh-lever-tag">[THE WORK HABIT TO UNLEARN]</div>
              <div class="wwh-lever-title">The Blindspot to Catch and Stop</div>
              <p class="wwh-lever-desc">${escapeHtml(levers.trap_to_eliminate)}</p>
            </div>
          ` : ""}

          ${levers.negotiation_mantra ? `
            <div class="wwh-lever-card anchor">
              <div class="wwh-lever-tag">[WHEN TALKING MONEY & RECOGNITION]</div>
              <div class="wwh-lever-title">What to Remember When Negotiating</div>
              <p class="wwh-lever-desc">${escapeHtml(levers.negotiation_mantra)}</p>
            </div>
          ` : ""}
        </div>
      </div>
    `;
  }

  // 8. COLLAPSIBLE ASTROLOGICAL PROOF
  if (proof) {
    html += `
      <div class="wwh-proof-accordion" id="cwp-sec-proof">
        <button type="button" class="wwh-proof-toggle" onclick="toggleLifeProof(this)">
          <span style="display:flex; align-items:center; gap:0.5rem;">
            <strong>[+] Classical Astrological Footnotes & Technical Derivations</strong>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:normal;">(D10 • KP Sub-Lords • Amatyakaraka • SAV)</span>
          </span>
          <span class="proof-chevron">▼</span>
        </button>
        <div class="wwh-proof-content">
          <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.75rem; font-style:italic;">
            Technical derivations reconciling BPHS 10th/2nd/11th houses, D10 Dashamsha placements, KP 10th/6th/11th cuspal sub-lords 1–249, Amatyakaraka, and A10 Rajya Pada.
          </p>
          <div class="markdown-body">
            ${formatMarkdown(proof)}
          </div>
        </div>
      </div>
    `;
  }

  html += `</div>`; // .cwp-container
  return html;
}
window.renderCraftWealthDeck = renderCraftWealthDeck;

function renderSchoolEyeDeck(d, schoolType) {
  if (!d) return "";
  const schoolKey = (schoolType || d.school || "parashari").toLowerCase();
  const isCareer = (d.pillar === "career" || state.selected_pillar === "career");

  const WWH_SCHOOL_METRIC_CONFIGS = {
    parashari: {
      name: "Parashari (BPHS)",
      traditionTag: "[PARASHARI PERSPECTIVE • ROOTS & CONDITIONING]",
      accentClass: "school-parashari",
      navWhatLabel: "What You Are",
      navWhyLabel: "The Why",
      navHowLabel: "How You Operate",
      metric1Label: "RULING GRAHA",
      metric1Val: d.metrics?.primary_ruling_graha || "-",
      metric2Label: "D9 NAVAMSHA",
      metric2Val: d.metrics?.d9_navamsha_affirmation || "-",
      metric3Label: "FUNCTIONAL NATURE",
      metric3Val: d.metrics?.functional_nature || "-",
      metric4Label: "STRENGTH PROFILE",
      metric4Val: d.metrics?.strength_profile || "-",
      whatTag: "[WHAT YOU ARE • INNATE TEMPERAMENT & ROOTS]",
      whatTitle: "Roots, Upbringing & Character Backbone",
      whyTag: "[WHY YOU ARE • BLESSINGS & LESSONS]",
      whyTitle: "Lifelong Blessings vs. Recurring Life Lessons",
      howTag: "[HOW YOU OPERATE • CURRENT MULTI-YEAR SEASON]",
      howTitle: "Your Current Multi-Year Life Season",
      proofTitle: "Classical Parashari Footnotes & Technical Derivations",
      proofSub: "Brihat Parashara Hora Shastra (BPHS) shloka references, D1/D9 degrees, Shadbala scores, and Vimshottari progression."
    },
    kp: {
      name: "KP Stellar",
      traditionTag: "[KP STELLAR PERSPECTIVE • REAL-WORLD OUTCOMES & DOORS]",
      accentClass: "school-kp",
      navWhatLabel: "What You Are",
      navWhyLabel: "The Why",
      navHowLabel: "How You Operate",
      metric1Label: "CUSP 1 SUB-LORD",
      metric1Val: d.metrics?.cuspal_sub_lord_1 || "-",
      metric2Label: "STAR-LORD LINK",
      metric2Val: d.metrics?.star_lord_link || "-",
      metric3Label: "SIGNIFIED HOUSES",
      metric3Val: d.metrics?.primary_house_group || "-",
      metric4Label: "NEGATING HOUSES",
      metric4Val: d.metrics?.negating_houses || "-",
      whatTag: "[WHAT YOU ARE • RESULTS & OUTCOMES]",
      whatTitle: "How Results Actually Materialize in Your Life",
      whyTag: "[WHY YOU ARE • DOORS & BOTTLENECKS]",
      whyTitle: "Your Green Lights vs. Hidden Bottlenecks",
      howTag: "[HOW YOU OPERATE • TIMING TRIGGERS]",
      howTitle: "What Is Unlocked Right Now — Timing Triggers",
      proofTitle: "KP Stellar Technical Footnotes & Cuspal Coordinates",
      proofSub: "Exact 1–249 cuspal degrees, Star-Lord/Sub-Lord/Sub-Sub-Lord hierarchies, and 4-fold A-D significator matrix."
    },
    jaimini: {
      name: "Jaimini Sutras",
      traditionTag: "[JAIMINI SUTRAS PERSPECTIVE • PUBLIC MASK VS SOUL]",
      accentClass: "school-jaimini",
      navWhatLabel: "What You Are",
      navWhyLabel: "The Why",
      navHowLabel: "How You Operate",
      metric1Label: "ATMAKARAKA (SOUL)",
      metric1Val: d.metrics?.atmakaraka_soul || "-",
      metric2Label: "AMATYAKARAKA (WORK)",
      metric2Val: d.metrics?.amatyakaraka_career || "-",
      metric3Label: "ARUDHA LAGNA (MASK)",
      metric3Val: d.metrics?.arudha_lagna_mask || "-",
      metric4Label: "CHARA DASHA",
      metric4Val: d.metrics?.active_chara_dasha || "-",
      whatTag: "[WHAT YOU ARE • PUBLIC MASK VS. PRIVATE SOUL]",
      whatTitle: "First Impressions vs. Who You Are When the Door Closes",
      whyTag: "[WHY YOU ARE • SOUL PURPOSE VS. MAYA]",
      whyTitle: "What Feeds Your Soul vs. Worldly Detours",
      howTag: "[HOW YOU OPERATE • SOUL ALIGNMENT & MIRROR]",
      howTitle: "Your Mirror in Intimacy & Soul Alignment",
      proofTitle: "Jaimini Upadesha Sutras Footnotes & Karaka Degrees",
      proofSub: "Chara Karaka replacement degrees, Arudha Pada exceptions, Rashi Drishti sign aspects, and Chara Dasha cycle."
    }
  };

  const CAREER_SCHOOL_METRIC_CONFIGS = {
    parashari: {
      name: "Parashari (BPHS)",
      traditionTag: "[PARASHARI PERSPECTIVE • VOCATIONAL FOUNDATION & DHANA YOGAS]",
      accentClass: "school-parashari",
      navWhatLabel: "Natural Craft",
      navWhyLabel: "Wealth & Lessons",
      navHowLabel: "Career Season",
      metric1Label: "10TH LORD & HOUSE",
      metric1Val: d.metrics?.tenth_house_lord || d.metrics?.primary_ruling_graha || "-",
      metric2Label: "D10 DASHAMSHA",
      metric2Val: d.metrics?.d10_dashamsha_dignity || d.metrics?.d9_navamsha_affirmation || "-",
      metric3Label: "DHANA & RAJA YOGAS",
      metric3Val: d.metrics?.dhana_raja_yogas || d.metrics?.functional_nature || "-",
      metric4Label: "CAREER DASHA",
      metric4Val: d.metrics?.career_dasha_impact || d.metrics?.strength_profile || "-",
      whatTag: "[CLASSICAL CRAFT & VOCATION]",
      whatTitle: "Your Natural Vocational Backbone & Calling",
      whyTag: "[WEALTH BLESSINGS & CAREER FRICTION]",
      whyTitle: "Where Wealth Flows Naturally vs. Professional Lessons",
      howTag: "[CURRENT CAREER SEASON]",
      howTitle: "What the Active Planetary Era Demands in Your Work",
      proofTitle: "Classical Parashari Footnotes & Technical Derivations",
      proofSub: "Brihat Parashara Hora Shastra (BPHS) 10th/2nd/11th/6th house mechanics, D10 Dashamsha placements, Dhana & Raja Yogas, and Vimshottari progression."
    },
    kp: {
      name: "KP Stellar",
      traditionTag: "[KP STELLAR PERSPECTIVE • CAREER GATES & REAL-WORLD TIMING]",
      accentClass: "school-kp",
      navWhatLabel: "Career Gates",
      navWhyLabel: "Promotions & Money",
      navHowLabel: "Timing Triggers",
      metric1Label: "CUSP 10 SUB-LORD",
      metric1Val: d.metrics?.cusp_10_sub_lord || d.metrics?.cuspal_sub_lord_1 || "-",
      metric2Label: "CUSP 2 SUB-LORD",
      metric2Val: d.metrics?.cusp_2_sub_lord || d.metrics?.star_lord_link || "-",
      metric3Label: "ELEVATION (2, 6, 10, 11)",
      metric3Val: d.metrics?.elevation_significators || d.metrics?.primary_house_group || "-",
      metric4Label: "DRAINAGE (5, 8, 12)",
      metric4Val: d.metrics?.drainage_houses || d.metrics?.negating_houses || "-",
      whatTag: "[REAL-WORLD TRACTION & OUTCOMES]",
      whatTitle: "Where Professional Results Come Easily vs. Stall",
      whyTag: "[PROMOTIONS & FINANCIAL GATES]",
      whyTitle: "Career Green Lights vs. Negotiation Bottlenecks",
      howTag: "[ACTIVE TIMING TRIGGERS]",
      howTitle: "What Moves & Deals Are Green-Lit Right Now",
      proofTitle: "KP Stellar Technical Footnotes & Cuspal Coordinates",
      proofSub: "Exact 1–249 10th/2nd/6th/11th CSL degrees, Star-Lord/Sub-Lord linkages, and 4-fold A-D significator matrix."
    },
    jaimini: {
      name: "Jaimini Sutras",
      traditionTag: "[JAIMINI SUTRAS PERSPECTIVE • PUBLIC REPUTATION VS. INNER CRAFT]",
      accentClass: "school-jaimini",
      navWhatLabel: "Public vs. Craft",
      navWhyLabel: "Mastery vs. Status",
      navHowLabel: "Career Chapter",
      metric1Label: "AMATYAKARAKA (AmK)",
      metric1Val: d.metrics?.amatyakaraka_work || d.metrics?.amatyakaraka_career || "-",
      metric2Label: "ATMAKARAKA (AK)",
      metric2Val: d.metrics?.atmakaraka_soul || "-",
      metric3Label: "RAJYA PADA (A10)",
      metric3Val: d.metrics?.rajya_pada_a10 || d.metrics?.arudha_lagna_mask || "-",
      metric4Label: "CHARA DASHA",
      metric4Val: d.metrics?.career_chara_dasha || d.metrics?.active_chara_dasha || "-",
      whatTag: "[PUBLIC STATUS VS. SOUL CRAFT]",
      whatTitle: "Your Professional Reputation vs. What Truly Fulfills You",
      whyTag: "[CAREER PURPOSE VS. STATUS TRAPS]",
      whyTitle: "Where Mastery Meets Ambition vs. Worldly Detours",
      howTag: "[CHARA DASHA CAREER ERA]",
      howTitle: "Your Active Sign Chapter & Public Impact",
      proofTitle: "Jaimini Upadesha Sutras Footnotes & Karaka Degrees",
      proofSub: "Amatyakaraka / Atmakaraka rankings, Rajya Pada A10 / Arudha Lagna degrees, and Chara Dasha career periods."
    }
  };

  const configMap = isCareer ? CAREER_SCHOOL_METRIC_CONFIGS : WWH_SCHOOL_METRIC_CONFIGS;
  const cfg = configMap[schoolKey] || configMap.parashari;
  const archetype = d.archetype || (isCareer ? "The Master Craftsman" : "The Sovereign Architect");
  const verdict = d.summary_verdict || "";
  const whatYouAre = d.what_you_are || {};
  const whatTraits = Array.isArray(whatYouAre.traits) ? whatYouAre.traits : (Array.isArray(d.traits) ? d.traits : []);
  const whyYouAre = d.why_you_are || {};
  const strengths = Array.isArray(whyYouAre.strengths) ? whyYouAre.strengths : [];
  const frictions = Array.isArray(whyYouAre.friction_points) ? whyYouAre.friction_points : [];
  const howYouOperate = d.how_you_operate || {};
  const proof = d.astrological_proof || "";

  let html = `<div class="what-why-how-container ${cfg.accentClass}">`;

  // 0. QUICK-JUMP MICRO-NAVIGATION
  html += `
    <nav class="wwh-sticky-nav">
      <button type="button" class="wwh-nav-pill active" onclick="scrollToWwhSection(event, '${schoolKey}-sec-identity')">Overview</button>
      <button type="button" class="wwh-nav-pill" onclick="scrollToWwhSection(event, '${schoolKey}-sec-what')">${escapeHtml(cfg.navWhatLabel || "What You Are")}</button>
      <button type="button" class="wwh-nav-pill" onclick="scrollToWwhSection(event, '${schoolKey}-sec-why')">${escapeHtml(cfg.navWhyLabel || "The Why")}</button>
      <button type="button" class="wwh-nav-pill" onclick="scrollToWwhSection(event, '${schoolKey}-sec-how')">${escapeHtml(cfg.navHowLabel || "How You Operate")}</button>
      ${proof ? `<button type="button" class="wwh-nav-pill" onclick="scrollToWwhSection(event, '${schoolKey}-sec-proof')">Technical Proof</button>` : ""}
    </nav>
  `;

  // 1. HERO IDENTITY CARD
  html += `
    <div class="wwh-hero-card" id="${schoolKey}-sec-identity">
      <div class="wwh-section-tag">${cfg.traditionTag}</div>
      <h2 class="wwh-hero-title">${escapeHtml(cfg.name.toUpperCase())} EVALUATION</h2>
      ${verdict ? `<div class="wwh-verdict">"${escapeHtml(verdict)}"</div>` : ""}
      
      <div class="wwh-badges-row">
        <span class="wwh-badge primary">ARCHETYPE: ${escapeHtml(archetype)}</span>
        <span class="wwh-badge">TRADITION: ${escapeHtml(cfg.name)}</span>
        ${isCareer ? `<span class="wwh-badge">PILLAR: Craft & Wealth</span>` : ""}
      </div>

      <div class="wwh-triad-strip" style="margin-top: 1.25rem;">
        <div class="wwh-triad-col">
          <span class="wwh-triad-role">${cfg.metric1Label}</span>
          <span class="wwh-triad-val">${escapeHtml(cfg.metric1Val)}</span>
        </div>
        <div class="wwh-triad-col">
          <span class="wwh-triad-role">${cfg.metric2Label}</span>
          <span class="wwh-triad-val">${escapeHtml(cfg.metric2Val)}</span>
        </div>
        <div class="wwh-triad-col">
          <span class="wwh-triad-role">${cfg.metric3Label}</span>
          <span class="wwh-triad-val">${escapeHtml(cfg.metric3Val)}</span>
        </div>
        <div class="wwh-triad-col">
          <span class="wwh-triad-role">${cfg.metric4Label}</span>
          <span class="wwh-triad-val">${escapeHtml(cfg.metric4Val)}</span>
        </div>
      </div>
    </div>
  `;

  // 1.1 SEEKER'S CONSULTATION COUNSEL / DATED TIMELINE (Only render when a genuine query was asked)
  const userTypedQuery = (document.getElementById("ai-custom-query-input")?.value || "").trim();
  const rawQuery = (d.dilemma_counsel?.seeker_query || d.query_resolution?.seeker_query || userTypedQuery || "").trim();
  const hasGenuineQuery = Boolean(rawQuery && rawQuery !== "Consultation Query" && rawQuery !== "null");

  if (hasGenuineQuery) {
    if (d.dilemma_counsel) {
      html += renderDilemmaCounselCard({ ...d.dilemma_counsel, seeker_query: rawQuery }, true);
    } else if (d.query_resolution) {
      const qr = d.query_resolution;
      const directAns = qr.event_promise || qr.cuspal_sub_lord_verdict || qr.manifestation_promise || "";
      const directHeadline = qr.governing_house_and_karaka || qr.queried_house || qr.governing_arudha_or_karaka || "";
      const activeReason = qr.astrological_reason || qr.fructification_rationale || qr.jaimini_rationale || "";
      html += renderDilemmaCounselCard({
        seeker_query: rawQuery,
        direct_answer: directAns ? `Verdict: ${directAns} — ${directHeadline}` : activeReason,
        exact_timeline: {
          primary_window: qr.exact_timing_window || "Active Period",
          active_dasha_trigger: activeReason,
          transits_trigger: directHeadline
        },
        astrological_reality: activeReason
      }, true);
    }
  }

  // 2. WHAT YOU ARE
  html += `
    <div class="wwh-section-block" id="${schoolKey}-sec-what">
      <div class="wwh-section-header">
        <span class="wwh-section-tag">${cfg.whatTag}</span>
        <h3 class="wwh-section-title">${escapeHtml(whatYouAre.headline || cfg.whatTitle)}</h3>
      </div>

      <div class="wwh-trait-card" style="margin-bottom: 0;">
        ${whatYouAre.bottom_line ? `<div class="wwh-trait-bottom-line" style="margin-bottom: 1rem;">"${escapeHtml(whatYouAre.bottom_line)}"</div>` : ""}
        ${whatTraits.length ? `
          <ul class="wwh-trait-bullets">
            ${whatTraits.map(pt => `<li>${escapeHtml(pt)}</li>`).join("")}
          </ul>
        ` : ""}
      </div>
    </div>
  `;

  // 3. WHY YOU ARE (CAUSAL ENGINE)
  if (strengths.length || frictions.length) {
    html += `
      <div class="wwh-section-block" id="${schoolKey}-sec-why">
        <div class="wwh-section-header">
          <span class="wwh-section-tag">${cfg.whyTag}</span>
          <h3 class="wwh-section-title">${escapeHtml(whyYouAre.headline || cfg.whyTitle)}</h3>
        </div>

        <div class="wwh-qualities-split">
          <!-- Strengths / Advantages Column -->
          <div class="wwh-qualities-col superpowers">
            <div class="wwh-qualities-col-header">
              <span class="wwh-col-label">[+] CORE GIFTS & STRATEGIC ADVANTAGES</span>
            </div>
            <div class="wwh-qualities-list">
              ${strengths.map((sp, idx) => `
                <div class="wwh-quality-item power">
                  <div class="wwh-quality-title">${escapeHtml(sp.name || sp.title || `Advantage ${idx + 1}`)}</div>
                  <p class="wwh-quality-desc">${escapeHtml(sp.description || "")}</p>
                  ${sp.manifestation ? `
                    <div class="wwh-quality-context power">
                      <span class="wwh-quality-context-tag">[REAL-WORLD TRIGGER]:</span> ${escapeHtml(sp.manifestation)}
                    </div>
                  ` : ""}
                </div>
              `).join("")}
            </div>
          </div>

          <!-- Friction Points Column -->
          <div class="wwh-qualities-col shadows">
            <div class="wwh-qualities-col-header">
              <span class="wwh-col-label">[-] FRICTION POINTS & CRITICAL BLINDSPOTS</span>
            </div>
            <div class="wwh-qualities-list">
              ${frictions.map((fp, idx) => `
                <div class="wwh-quality-item shadow">
                  <div class="wwh-quality-title">${escapeHtml(fp.name || fp.title || `Friction ${idx + 1}`)}</div>
                  <p class="wwh-quality-desc">${escapeHtml(fp.description || "")}</p>
                  ${fp.antidote ? `
                    <div class="wwh-quality-context shadow">
                      <span class="wwh-quality-context-tag">[IMMEDIATE ANTIDOTE]:</span> ${escapeHtml(fp.antidote)}
                    </div>
                  ` : ""}
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // 4. HOW YOU OPERATE
  html += `
    <div class="wwh-section-block" id="${schoolKey}-sec-how">
      <div class="wwh-section-header">
        <span class="wwh-section-tag">${cfg.howTag}</span>
        <h3 class="wwh-section-title">${escapeHtml(howYouOperate.headline || cfg.howTitle)}</h3>
      </div>

      <div class="wwh-manual-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
        ${howYouOperate.operating_dasha_rhythm ? `
          <div class="wwh-manual-card decision">
            <div class="wwh-manual-title">OPERATING LIFE SEASON & RHYTHM</div>
            <p class="wwh-decision-text">${escapeHtml(howYouOperate.operating_dasha_rhythm)}</p>
          </div>
        ` : ""}

        <div class="wwh-manual-card energy">
          <div class="wwh-manual-title">VITALITY DYNAMICS</div>
          <div class="wwh-energy-split">
            <div class="wwh-energy-subcol">
              <span class="wwh-energy-label">[+] PEAK ENERGIZER</span>
              <p style="font-size:0.86rem; color:var(--text-secondary); margin-top:0.4rem; line-height:1.45;">
                ${escapeHtml(howYouOperate.primary_energizer || "-")}
              </p>
            </div>
            <div class="wwh-energy-subcol">
              <span class="wwh-energy-label">[-] BURNOUT TRIGGER</span>
              <p style="font-size:0.86rem; color:var(--text-secondary); margin-top:0.4rem; line-height:1.45;">
                ${escapeHtml(howYouOperate.primary_burnout_trigger || "-")}
              </p>
            </div>
          </div>
        </div>

        ${howYouOperate.golden_directive ? `
          <div class="wwh-lever-card golden" style="border-radius: var(--radius-md);">
            <div class="wwh-lever-tag">[GOLDEN DIRECTIVE]</div>
            <div class="wwh-lever-title">High-Leverage Multiplier</div>
            <p class="wwh-lever-desc">${escapeHtml(howYouOperate.golden_directive)}</p>
          </div>
        ` : ""}
      </div>
    </div>
  `;

  // 5. TECHNICAL PROOF ACCORDION
  if (proof) {
    html += `
      <div class="wwh-proof-accordion" id="${schoolKey}-sec-proof">
        <button type="button" class="wwh-proof-toggle" onclick="toggleLifeProof(this)">
          <span style="display:flex; align-items:center; gap:0.5rem;">
            <strong>[+] ${escapeHtml(cfg.proofTitle)}</strong>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:normal;">(${escapeHtml(cfg.name)})</span>
          </span>
          <span class="proof-chevron">▼</span>
        </button>
        <div class="wwh-proof-content">
          <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.75rem; font-style:italic;">
            ${escapeHtml(cfg.proofSub)}
          </p>
          <div class="markdown-body">
            ${formatMarkdown(proof)}
          </div>
        </div>
      </div>
    `;
  }

  html += `</div>`;
  return html;
}
window.renderSchoolEyeDeck = renderSchoolEyeDeck;

function renderSchoolEyeOutput(markdown, schoolType) {
  if (!markdown) return "";
  const { metadata, cleanMarkdown } = extractConfluenceMetadata(markdown);
  if (metadata && (metadata.what_you_are || metadata.metrics || metadata.why_you_are || metadata.traits || metadata.archetype)) {
    return renderSchoolEyeDeck(metadata, schoolType);
  }
  return formatMarkdown(cleanMarkdown || markdown);
}
window.renderSchoolEyeOutput = renderSchoolEyeOutput;

function updateConfluenceCard(metadata) {
  const card = document.getElementById("ai-confluence-card");
  const scoreText = document.getElementById("ai-confluence-score-text");
  const levelBadge = document.getElementById("ai-confluence-level-badge");
  const verdictText = document.getElementById("ai-confluence-summary-verdict");
  const barFill = document.getElementById("ai-confluence-bar-fill");

  if (!card) return;
  card.style.display = "block";

  const score = metadata.confluence_score || 85;
  const level = metadata.confluence_level || "Triple Confluence";
  const verdict = metadata.summary_verdict || "Consensus reached across Parashari, KP, and Jaimini.";

  if (scoreText) scoreText.textContent = `${score}%`;
  if (levelBadge) {
    levelBadge.textContent = level;
    if (score >= 85) {
      levelBadge.className = "status-badge active";
      levelBadge.style.backgroundColor = "";
      levelBadge.style.color = "";
    } else if (score >= 60) {
      levelBadge.className = "status-badge";
      levelBadge.style.backgroundColor = "rgba(229, 184, 105, 0.15)";
      levelBadge.style.color = "#E5B869";
    } else {
      levelBadge.className = "status-badge";
      levelBadge.style.backgroundColor = "rgba(239, 68, 68, 0.15)";
      levelBadge.style.color = "#EF4444";
    }
  }
  if (verdictText) verdictText.textContent = verdict;
  if (barFill) barFill.style.width = `${score}%`;
}

function formatHumanReading(markdown, metadata) {
  if (!markdown) return "";

  const verdict = metadata ? (metadata.summary_verdict || metadata.headline || "") : "";

  // Split technical footnotes if present
  let mainText = markdown;
  let technicalText = "";

  const techMatch = markdown.match(/(?:^|\n)(?:##|###)\s*(?:Astrological Footnotes|Classical Astrological Verification|Astrological Foundations|Technical Derivations)[\s\S]*/i);
  if (techMatch) {
    technicalText = techMatch[0].trim();
    mainText = markdown.slice(0, techMatch.index).trim();
  }

  let html = `<div class="human-reading-dossier">`;

  // Hero headline banner if verdict is present
  if (verdict) {
    html += `
      <div class="human-reading-hero">
        <div class="human-reading-badge">✦ Personalized Vedic Consultation</div>
        <h2 class="human-reading-verdict">${escapeHtml(verdict)}</h2>
      </div>
    `;
  }

  // Main consultation reading body
  html += `<div class="human-reading-body">${formatMarkdown(mainText)}</div>`;

  // Collapsible Technical Footnotes Accordion
  if (technicalText) {
    const cleanTech = technicalText.replace(/^(?:##|###)\s*(?:Astrological Footnotes|Classical Astrological Verification|Astrological Foundations|Technical Derivations)[^\n]*\n?/i, "").trim();
    html += `
      <div class="reading-proof-accordion">
        <button type="button" class="reading-proof-toggle" onclick="toggleLifeProof(this)">
          <span style="display:flex; align-items:center; gap:0.55rem;">
            <strong>[+] Classical Astrological Footnotes & Technical Derivations</strong>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:normal;">(Parashari • KP • Jaimini)</span>
          </span>
          <span class="proof-chevron">▼</span>
        </button>
        <div class="reading-proof-content">
          <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.75rem; font-style:italic;">
            For astrologers and technical verification: How this reading was synthesized from exact mathematical Parashari yogas, KP cuspal sub-lords 1–249, and Jaimini Chara Karakas.
          </p>
          <div class="markdown-body">
            ${formatMarkdown(cleanTech)}
          </div>
        </div>
      </div>
    `;
  }

  html += `</div>`;
  return html;
}

function renderSynthesisProgressive(markdown) {
  const { metadata, cleanMarkdown } = extractConfluenceMetadata(markdown);
  if (metadata) {
    updateConfluenceCard(metadata);
  }
  const box = document.getElementById("ai-synthesis-rendered");
  if (!box) return;

  if (metadata) {
    if (metadata.work_genius || metadata.vocation_archetype || metadata.wealth_engine) {
      box.innerHTML = renderCraftWealthDeck(metadata);
    } else if (metadata.traits || metadata.the_why || metadata.archetype || metadata.qualities) {
      box.innerHTML = renderWhatWhyHowDeck(metadata);
    } else {
      box.innerHTML = formatHumanReading(cleanMarkdown, metadata);
    }
  } else {
    const trimmed = (markdown || "").trim();
    if (trimmed.startsWith("```json") || trimmed.startsWith("{")) {
      const isCwp = trimmed.includes('"work_genius"') || trimmed.includes('"vocation_archetype"') || trimmed.includes('"wealth_engine"');

      if (isCwp) {
        const archMatch = trimmed.match(/"vocation_archetype"\s*:\s*"([^"]+)"/) || trimmed.match(/"archetype"\s*:\s*"([^"]+)"/);
        const verdMatch = trimmed.match(/"summary_verdict"\s*:\s*"([^"]+)"/);

        const hasS1 = trimmed.includes('"work_genius"');
        const hasS2 = trimmed.includes('"leadership_and_authority"');
        const hasS3 = trimmed.includes('"wealth_engine"');
        const hasS4 = trimmed.includes('"enterprise_vs_employment"');
        const hasS5 = trimmed.includes('"timing_weather"');
        const hasS6 = trimmed.includes('"tactical_levers"') || trimmed.includes('"astrological_proof"');

        const stages = [
          { label: "Analyzing natural craft essence & cognitive flow state (10th Lord & AmK)", done: hasS2, active: hasS1 && !hasS2 },
          { label: "Mapping authority posture, leadership reflex & public presence", done: hasS3, active: hasS2 && !hasS3 },
          { label: "Auditing wealth engine, primary inflows & financial leaks", done: hasS4, active: hasS3 && !hasS4 },
          { label: "Evaluating sovereign enterprise vs. organizational leadership", done: hasS5, active: hasS4 && !hasS5 },
          { label: "Forecasting 24-month career weather & Dasha timing windows", done: hasS6, active: hasS5 && !hasS6 },
          { label: "Synthesizing classical BPHS, D10, KP & Jaimini derivations", done: false, active: hasS6 },
        ];

        const stageItemsHtml = stages.map(s => {
          let icon = `<span style="display:inline-block; width:18px; color:var(--text-muted); opacity:0.4;">○</span>`;
          let textStyle = `color: var(--text-muted); opacity: 0.6;`;
          if (s.done) {
            icon = `<span style="display:inline-block; width:18px; color: #10B981; font-weight: bold;">[✓]</span>`;
            textStyle = `color: var(--text-primary); font-weight: 500;`;
          } else if (s.active) {
            icon = `<span class="loading-spinner" style="display:inline-block; width:14px; height:14px; border-width:2px; vertical-align:middle; margin-right:4px;"></span>`;
            textStyle = `color: var(--accent-primary); font-weight: 700;`;
          }
          return `
            <div style="display: flex; align-items: center; gap: 0.6rem; font-size: 0.86rem; ${textStyle} padding: 0.35rem 0;">
              ${icon}
              <span>${escapeHtml(s.label)}</span>
            </div>
          `;
        }).join("");

        box.innerHTML = `
          <div class="ai-streaming-card" style="padding: 1.75rem; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);">
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.6rem; margin-bottom: 1.25rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 0.85rem;">
              <div style="display: flex; align-items: center; gap: 0.6rem; color: var(--accent-primary); font-weight: 700; font-size: 0.95rem;">
                <span class="loading-spinner" style="width: 15px; height: 15px; border-width: 2px;"></span>
                <span>Assembling Craft, Wealth & Public Calling Blueprint...</span>
              </div>
              <span style="font-size: 0.75rem; font-family: var(--font-mono); color: var(--text-muted);">Three Eyes Active</span>
            </div>

            ${(archMatch || verdMatch) ? `
            <div style="margin-bottom: 1.35rem; padding: 1.1rem 1.35rem; background: linear-gradient(135deg, rgba(200, 155, 60, 0.12), rgba(200, 155, 60, 0.04)); border: 1px solid rgba(200, 155, 60, 0.35); border-radius: var(--radius-md);">
              ${archMatch ? `<div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent-primary); font-weight: 800; margin-bottom: 0.35rem;">✦ Emerging Vocation: ${escapeHtml(archMatch[1])}</div>` : ""}
              ${verdMatch ? `<div style="font-size: 0.94rem; font-weight: 600; color: var(--text-primary); line-height: 1.5; font-style: italic;">"${escapeHtml(verdMatch[1])}"</div>` : ""}
            </div>
            ` : ""}

            <div style="display: flex; flex-direction: column; gap: 0.2rem;">
              ${stageItemsHtml}
            </div>
          </div>
        `;
        return;
      }

      const archMatch = trimmed.match(/"archetype"\s*:\s*"([^"]+)"/);
      const verdMatch = trimmed.match(/"summary_verdict"\s*:\s*"([^"]+)"/);

      const hasS1 = trimmed.includes('"constitution"');
      const hasS2 = trimmed.includes('"traits"');
      const hasS3 = trimmed.includes('"the_why"');
      const hasS4 = trimmed.includes('"qualities"');
      const hasS5 = trimmed.includes('"arenas"');
      const hasS6 = trimmed.includes('"astrological_proof"');

      const stages = [
        { label: "Reading elemental balance & Ayurvedic temperament", done: hasS2, active: hasS1 && !hasS2 },
        { label: "Mapping physical, emotional & cognitive reflexes", done: hasS3, active: hasS2 && !hasS3 },
        { label: "Uncovering your core inner paradox & growth edge", done: hasS4, active: hasS3 && !hasS4 },
        { label: "Extracting natural superpowers & blindspots", done: hasS5, active: hasS4 && !hasS5 },
        { label: "Building work, relationship & pressure arenas", done: hasS6, active: hasS5 && !hasS6 },
        { label: "Synthesizing classical BPHS, KP & Jaimini derivations", done: false, active: hasS6 },
      ];

      const stageItemsHtml = stages.map(s => {
        let icon = `<span style="display:inline-block; width:18px; color:var(--text-muted); opacity:0.4;">○</span>`;
        let textStyle = `color: var(--text-muted); opacity: 0.6;`;
        if (s.done) {
          icon = `<span style="display:inline-block; width:18px; color: #10B981; font-weight: bold;">[✓]</span>`;
          textStyle = `color: var(--text-primary); font-weight: 500;`;
        } else if (s.active) {
          icon = `<span class="loading-spinner" style="display:inline-block; width:14px; height:14px; border-width:2px; vertical-align:middle; margin-right:4px;"></span>`;
          textStyle = `color: var(--accent-primary); font-weight: 700;`;
        }
        return `
          <div style="display: flex; align-items: center; gap: 0.6rem; font-size: 0.86rem; ${textStyle} padding: 0.35rem 0;">
            ${icon}
            <span>${escapeHtml(s.label)}</span>
          </div>
        `;
      }).join("");

      box.innerHTML = `
        <div class="ai-streaming-card" style="padding: 1.75rem; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);">
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.6rem; margin-bottom: 1.25rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 0.85rem;">
            <div style="display: flex; align-items: center; gap: 0.6rem; color: var(--accent-primary); font-weight: 700; font-size: 0.95rem;">
              <span class="loading-spinner" style="width: 15px; height: 15px; border-width: 2px;"></span>
              <span>Assembling Your Personal Life Blueprint...</span>
            </div>
            <span style="font-size: 0.75rem; font-family: var(--font-mono); color: var(--text-muted);">Three Eyes Active</span>
          </div>

          ${(archMatch || verdMatch) ? `
          <div style="margin-bottom: 1.35rem; padding: 1.1rem 1.35rem; background: linear-gradient(135deg, rgba(200, 155, 60, 0.12), rgba(200, 155, 60, 0.04)); border: 1px solid rgba(200, 155, 60, 0.35); border-radius: var(--radius-md);">
            ${archMatch ? `<div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent-primary); font-weight: 800; margin-bottom: 0.35rem;">✦ Emerging Archetype: ${escapeHtml(archMatch[1])}</div>` : ""}
            ${verdMatch ? `<div style="font-size: 0.94rem; font-weight: 600; color: var(--text-primary); line-height: 1.5; font-style: italic;">"${escapeHtml(verdMatch[1])}"</div>` : ""}
          </div>
          ` : ""}

          <div style="display: flex; flex-direction: column; gap: 0.2rem;">
            ${stageItemsHtml}
          </div>
        </div>
      `;
    } else if (trimmed) {
      box.innerHTML = formatHumanReading(markdown, null);
    }
  }
}

function updateEyesRendered(eyes) {
  const pBox = document.getElementById("ai-parashari-rendered");
  const kpBox = document.getElementById("ai-kp-rendered");
  const jBox = document.getElementById("ai-jaimini-rendered");

  if (pBox && eyes.parashari) pBox.innerHTML = renderSchoolEyeOutput(eyes.parashari, "parashari");
  if (kpBox && eyes.kp) kpBox.innerHTML = renderSchoolEyeOutput(eyes.kp, "kp");
  if (jBox && eyes.jaimini) jBox.innerHTML = renderSchoolEyeOutput(eyes.jaimini, "jaimini");
}

const PILLAR_CHAPTER_MAP = {
  comprehensive: { chapter: 1, name: "What, Why and How You Are", title: "Identity Blueprint & Traits" },
  career: { chapter: 2, name: "Craft, Wealth & Public Calling", title: "Vocational Mastery & Wealth Blueprint" },
  relationships: { chapter: 3, name: "Relationships, Marriage & Compatibility", title: "Partnership & Intimacy Psychology" },
  dasha: { chapter: 4, name: "Current Dasha & Future Timings", title: "Operating Life Season & Future Timings" },
};

function getActiveChartSignature() {
  return `${state.year}-${state.month}-${state.day}_${state.hour}:${state.minute}:${state.second}_${state.city}_${state.gender || "male"}_${state.time_offset_seconds}_${state.ayanamsha}_${state.node_type}_${state.target_date || "now"}`;
}

function startAiButtonCooldown(seconds = 4) {
  const btn = document.getElementById("ai-generate-synthesis-btn");
  if (!btn) return;
  let remaining = seconds;
  btn.disabled = true;
  btn.textContent = `✦ Ready in ${remaining}s`;
  const interval = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      clearInterval(interval);
      btn.disabled = false;
      btn.textContent = "✦ Generate Synthesis ➔";
    } else {
      btn.textContent = `✦ Ready in ${remaining}s`;
    }
  }, 1000);
}

function renderAiConsultationWorkspace() {
  const d = state.currentData;
  if (!d) return;

  const chartSig = getActiveChartSignature();
  
  // Update floating chat drawer subtitle
  const chatSub = document.getElementById("chat-capsule-subtitle");
  if (chatSub) {
    chatSub.textContent = `${state.city} • ${state.hour.toString().padStart(2, "0")}:${state.minute.toString().padStart(2, "0")}`;
  }

  // Check invalidation
  const staleBanner = document.getElementById("ai-stale-banner");
  const reanchorBanner = document.getElementById("chat-reanchor-banner");
  if (state.last_ai_chart_sig && state.last_ai_chart_sig !== chartSig) {
    if (staleBanner) staleBanner.style.display = "flex";
    if (reanchorBanner) reanchorBanner.style.display = "block";
  } else {
    if (staleBanner) staleBanner.style.display = "none";
    if (reanchorBanner) reanchorBanner.style.display = "none";
  }

  // Check if active pillar reading is cached
  const customQuery = document.getElementById("ai-custom-query-input")?.value.trim() || "";
  const cacheKey = `${chartSig}_${state.selected_pillar}_${customQuery}`;
  if (state.ai_readings_cache[cacheKey]) {
    displayAiReading(state.ai_readings_cache[cacheKey]);
  } else if (state.selected_pillar !== "comprehensive" && !customQuery && state.ai_readings_cache[`${chartSig}_comprehensive_`]) {
    displayAiReadingFromComprehensive(state.ai_readings_cache[`${chartSig}_comprehensive_`], state.selected_pillar);
  }
}

function selectAiPillar(pillar) {
  state.selected_pillar = pillar;
  document.querySelectorAll(".ai-pillar-card").forEach(c => {
    c.classList.toggle("active", c.dataset.pillar === pillar);
  });

  const chartSig = getActiveChartSignature();
  const customQuery = document.getElementById("ai-custom-query-input")?.value.trim() || "";
  const cacheKey = `${chartSig}_${pillar}_${customQuery}`;

  // 1. Direct hit on dedicated reading for this pillar
  if (state.ai_readings_cache[cacheKey]) {
    displayAiReading(state.ai_readings_cache[cacheKey]);
    return;
  }

  // 2. If NO dedicated reading, but Comprehensive Master reading exists and no custom query:
  //    Display the Comprehensive reading focused on this chapter with 0 API requests!
  const compKey = `${chartSig}_comprehensive_`;
  if (state.ai_readings_cache[compKey] && !customQuery && pillar !== "comprehensive") {
    displayAiReadingFromComprehensive(state.ai_readings_cache[compKey], pillar);
    return;
  }
}

function displayAiReadingFromComprehensive(readingData, pillar) {
  updateEyesRendered(readingData.eyeVerdicts || {});

  const { metadata, cleanMarkdown } = extractConfluenceMetadata(readingData.fullSynthesisMarkdown || "");
  if (metadata) {
    updateConfluenceCard(metadata);
  }

  const box = document.getElementById("ai-synthesis-rendered");
  if (!box) return;

  const info = PILLAR_CHAPTER_MAP[pillar] || { chapter: 1, name: pillar, title: pillar };

  // Check if readingData is a What-Why-How JSON deck
  const isWwhDeck = metadata && (metadata.traits || metadata.the_why || metadata.archetype || metadata.qualities);

  if (isWwhDeck) {
    // Render focused Pillar Preview & Launch Card instead of duplicating full WWH foundation deck
    let previewContent = "";
    let domainTitle = info.name;
    let domainDesc = "";
    let btnLabel = `✦ Generate Full ${info.title} Consultation ➔`;

    if (pillar === "career") {
      domainTitle = "Craft, Wealth & Public Calling Snapshot";
      domainDesc = "Here is your foundational work & leadership posture from your core blueprint. Ready for your dedicated 6-card vocational, wealth, and timing consultation?";
      btnLabel = "✦ Generate Full Craft, Wealth & Public Calling Consultation ➔";
      const arenaWork = renderArenaPanel(metadata, "work");
      const goldenLever = metadata.growth_levers?.golden_lever;
      previewContent = `
        <div class="wwh-section-block" style="margin-top: 1rem;">
          <div class="wwh-section-header">
            <span class="wwh-section-tag">[WORK & LEADERSHIP ARENA]</span>
            <h3 class="wwh-section-title">Your Natural Operating Stance at Work</h3>
          </div>
          ${arenaWork}
          ${goldenLever ? `
          <div class="wwh-golden-strip" style="margin-top: 1.25rem;">
            <div class="wwh-golden-tag">[KEY WORKPLACE LEVER]:</div>
            <p class="wwh-golden-text">${escapeHtml(goldenLever)}</p>
          </div>
          ` : ""}
        </div>
      `;
    } else if (pillar === "relationships") {
      domainTitle = "Partnership & Emotional Wiring Snapshot";
      domainDesc = "Here is your intimate relationship reflex from your core blueprint. Ready for your complete 5-chapter love, marriage, and timing consultation?";
      const arenaRel = renderArenaPanel(metadata, "relationships");
      const emotionalTrait = metadata.traits?.emotional?.bottom_line;
      previewContent = `
        <div class="wwh-section-block" style="margin-top: 1rem;">
          <div class="wwh-section-header">
            <span class="wwh-section-tag">[RELATIONSHIP & INTIMACY ARENA]</span>
            <h3 class="wwh-section-title">How Your Heart Operates in Close Partnerships</h3>
          </div>
          ${arenaRel}
          ${emotionalTrait ? `
          <div class="wwh-golden-strip" style="margin-top: 1.25rem; border-color: rgba(244, 114, 182, 0.35); background: rgba(244, 114, 182, 0.06);">
            <div class="wwh-golden-tag" style="color: #F472B6;">[EMOTIONAL TRUTH]:</div>
            <p class="wwh-golden-text">${escapeHtml(emotionalTrait)}</p>
          </div>
          ` : ""}
        </div>
      `;
    } else if (pillar === "dasha") {
      domainTitle = "Operating Season & Growth Edge Snapshot";
      domainDesc = "Here is your operating season and comfort-zone vs. growth-edge from your core blueprint. Ready for your complete 24-month timeline consultation?";
      const op = metadata.operating_manual || {};
      const axis = metadata.the_why?.comfort_zone_vs_growth_edge || {};
      previewContent = `
        <div class="wwh-section-block" style="margin-top: 1rem;">
          <div class="wwh-section-header">
            <span class="wwh-section-tag">[SEASONAL WIRING & KARMIC AXIS]</span>
            <h3 class="wwh-section-title">Operating Rhythm & The Territory Calling You Forward</h3>
          </div>
          <div class="wwh-why-grid" style="margin-top: 1rem;">
            <div class="wwh-why-card paradox">
              <span class="wwh-why-tag">[COMFORT ZONE (HABITUAL TRAP)]</span>
              <h4 class="wwh-why-title">${escapeHtml(axis.comfort_zone || "Habitual default under stress")}</h4>
            </div>
            <div class="wwh-why-card axis">
              <span class="wwh-why-tag">[ACTIVE GROWTH EDGE]</span>
              <h4 class="wwh-why-title">${escapeHtml(axis.growth_edge || "Uncomfortable territory unlocking your next level")}</h4>
            </div>
          </div>
          ${op.stress_response ? `
          <div class="wwh-stress-box" style="margin-top: 1.25rem;">
            <div class="wwh-stress-title">Stress Response & Reset Mechanism</div>
            <p class="wwh-stress-desc"><strong>Trigger:</strong> ${escapeHtml(op.stress_response.trigger || "-")}</p>
            <p class="wwh-stress-desc"><strong>Recovery:</strong> ${escapeHtml(op.stress_response.recovery || "-")}</p>
          </div>
          ` : ""}
        </div>
      `;
    } else {
      previewContent = renderWhatWhyHowDeck(metadata);
    }

    const previewBannerHtml = `
      <div class="pillar-focus-banner" style="margin-bottom: 1.25rem;">
        <div class="pillar-focus-banner-text">
          <span class="pillar-focus-badge">✦ Core Blueprint Snapshot</span>
          <h4 class="pillar-focus-title">${escapeHtml(domainTitle)}</h4>
          <p class="pillar-focus-desc">${escapeHtml(domainDesc)}</p>
        </div>
        <button type="button" class="pillar-focus-btn" onclick="triggerAiSynthesis(true)">
          ${escapeHtml(btnLabel)}
        </button>
      </div>
    `;

    box.innerHTML = previewBannerHtml + previewContent;
    return;
  }

  // Otherwise, it is a multi-chapter Markdown reading:
  const bannerHtml = `
    <div class="pillar-focus-banner">
      <div class="pillar-focus-banner-text">
        <span class="pillar-focus-badge">✦ Master Blueprint Dimension</span>
        <h4 class="pillar-focus-title">Viewing Chapter ${info.chapter}: ${escapeHtml(info.name)}</h4>
        <p class="pillar-focus-desc">Extracted instantly from your Comprehensive Reading without consuming API requests.</p>
      </div>
      <button type="button" class="pillar-focus-btn" onclick="triggerAiSynthesis(true)">
        ✦ Generate Dedicated Deep-Dive
      </button>
    </div>
  `;

  box.innerHTML = bannerHtml + formatHumanReading(cleanMarkdown, metadata);

  // Smoothly scroll to chapter header and highlight it
  setTimeout(() => {
    const chEl = document.getElementById(`chapter-${info.chapter}`);
    if (chEl) {
      document.querySelectorAll(".reading-chapter-header").forEach(h => h.classList.remove("highlighted-chapter"));
      chEl.classList.add("highlighted-chapter");
      chEl.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, 100);
}


function selectAiPerspective(persp) {
  state.active_ai_persp = persp;
  document.querySelectorAll(".ai-persp-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.persp === persp);
  });
  document.querySelectorAll(".persp-view").forEach(v => {
    v.classList.remove("active");
    v.style.display = "none";
  });
  const target = document.getElementById(`persp-view-${persp}`);
  if (target) {
    target.classList.add("active");
    target.style.display = "block";
  }
}

function displayAiReading(readingData) {
  updateEyesRendered(readingData.eyeVerdicts || {});
  renderSynthesisProgressive(readingData.fullSynthesisMarkdown || "");
}

async function triggerAiSynthesis(forceRefresh = false) {
  if (state.is_generating_synthesis) return;
  const d = state.currentData;
  if (!d) {
    alert("Please calculate a chart first.");
    return;
  }

  const pillar = state.selected_pillar || "comprehensive";
  const customQueryInput = document.getElementById("ai-custom-query-input");
  const customQuery = customQueryInput ? customQueryInput.value.trim() : "";
  const userKey = localStorage.getItem("trinetri_gemini_key") || "";

  const chartSig = getActiveChartSignature();
  const cacheKey = `${chartSig}_${pillar}_${customQuery}`;

  // If not forcing refresh and reading is already cached for this exact pillar + query, display immediately (0 API calls)
  if (!forceRefresh && state.ai_readings_cache[cacheKey]) {
    displayAiReading(state.ai_readings_cache[cacheKey]);
    return;
  }

  // UI loading states
  if (state.synthesis_abort_controller) {
    try { state.synthesis_abort_controller.abort(); } catch (_) {}
  }
  state.synthesis_abort_controller = new AbortController();

  state.is_generating_synthesis = true;
  const statusEl = document.getElementById("ai-synthesis-status");
  const statusText = document.getElementById("ai-synthesis-status-text");
  const btn = document.getElementById("ai-generate-synthesis-btn");
  const renderBox = document.getElementById("ai-synthesis-rendered");
  const confluenceCard = document.getElementById("ai-confluence-card");

  if (statusEl) statusEl.style.display = "flex";
  if (statusText) statusText.textContent = "Awakening the Three Eyes (Parashara, KP, Jaimini)...";
  if (btn) {
    btn.disabled = true;
    btn.textContent = "✦ Analyzing...";
  }
  if (confluenceCard) confluenceCard.style.display = "none";

  // Switch to synthesis perspective tab
  selectAiPerspective("synthesis");

  if (renderBox) {
    renderBox.innerHTML = '<div style="color: var(--text-muted); font-style: italic; padding: 2rem; text-align: center;"><span class="ai-spinner"></span> Consulting classical canons & evaluating cusps...</div>';
  }

  let eyeVerdicts = { parashari: "", kp: "", jaimini: "" };
  let fullSynthesisMarkdown = "";

  const payload = {
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
      gender: state.gender,
      chart_style: state.chart_style,
      sign_mode: state.sign_mode,
      theme_mode: state.theme_mode,
      selected_varga: state.selected_varga,
      show_gochar: state.show_gochar,
      target_date: state.target_date,
    },
    pillar: pillar,
    custom_query: customQuery,
    user_api_key: userKey || null,
    model: (localStorage.getItem("trinetri_gemini_model") && localStorage.getItem("trinetri_gemini_model") !== "auto") ? localStorage.getItem("trinetri_gemini_model") : null,
    force_refresh: Boolean(forceRefresh),
  };

  try {
    const res = await fetch("/api/ai/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: state.synthesis_abort_controller.signal,
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail || `Server error (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop();

      for (const rawEvt of events) {
        if (!rawEvt.trim()) continue;
        const lines = rawEvt.split("\n");
        let eventName = "message";
        let eventData = "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventName = line.substring(7).trim();
          } else if (line.startsWith("data: ")) {
            eventData = line.substring(6).trim();
          }
        }

        if (eventName === "status") {
          try {
            const parsed = JSON.parse(eventData);
            if (statusText) statusText.textContent = parsed.message;
          } catch (_) {}
        } else if (eventName === "eyes_ready") {
          try {
            eyeVerdicts = JSON.parse(eventData);
            updateEyesRendered(eyeVerdicts);
          } catch (_) {}
        } else if (eventName === "confluence") {
          try {
            const parsed = JSON.parse(eventData);
            updateConfluenceCard({
              confluence_score: parsed.score,
              confluence_level: parsed.level,
              summary_verdict: `Mathematically Verified: Parashari ${parsed.components.parashari}% • KP ${parsed.components.kp}% • Jaimini ${parsed.components.jaimini}%`,
            });
          } catch (_) {}
        } else if (eventName === "token") {
          try {
            const parsed = JSON.parse(eventData);
            fullSynthesisMarkdown += parsed.token;
            renderSynthesisProgressive(fullSynthesisMarkdown);
          } catch (_) {}
        } else if (eventName === "error") {
          let errText = "Unknown AI error";
          try {
            const parsed = JSON.parse(eventData);
            errText = parsed.error || eventData;
          } catch (_) {
            errText = eventData || errText;
          }
          throw new Error(errText);
        }
      }
    }

    // Success
    state.last_ai_chart_sig = chartSig;
    const staleEl = document.getElementById("ai-stale-banner");
    if (staleEl) staleEl.style.display = "none";

    const readingData = {
      pillar,
      customQuery,
      chartSig,
      eyeVerdicts,
      fullSynthesisMarkdown,
    };
    state.ai_readings_cache[cacheKey] = readingData;
    displayAiReading(readingData);

  } catch (err) {
    if (err.name === "AbortError") {
      console.log("AI synthesis aborted by user or navigation.");
      return;
    }
    console.error("AI synthesis failed:", err);
    let msg = err.message || "Failed to generate AI synthesis.";
    if (typeof msg === "string" && msg.trim().startsWith("{") && msg.trim().endsWith("}")) {
      try {
        const parsed = JSON.parse(msg);
        if (parsed.error) msg = parsed.error;
      } catch (_) {}
    }
    if (msg.includes("Gemini API Key is not configured") || msg.includes("API key not valid")) {
      msg = `Gemini API Key is not configured. Please enter your personal Google Gemini API key to start generating readings.`;
    } else if (msg.includes("ReadTimeout") || msg.includes("Timeout")) {
      msg = `The Gemini API timed out while generating your reading (Google servers are experiencing temporary latency). You can switch model to Gemini 3.8 Flash in API Key settings, or try again in a moment.`;
    } else if (msg.includes("503") || msg.includes("overloaded") || msg.includes("busy")) {
      msg = `Google Gemini servers are currently overloaded (503 Service Unavailable). Switching model to Gemini 3.8 Flash in API Key settings or trying again in a moment is recommended.`;
    }
    if (renderBox) {
      renderBox.innerHTML = `
        <div style="padding: 1.5rem; background: rgba(220, 38, 38, 0.08); border: 1px solid rgba(220, 38, 38, 0.3); border-radius: 8px; color: #EF4444;">
          <strong style="display: block; font-size: 1rem; margin-bottom: 0.35rem;">[SYNTHESIS NOTICE]</strong>
          <p style="margin-top: 0.35rem; font-size: 0.9rem; line-height: 1.5;">${msg}</p>
          <button class="action-pill" onclick="openApiKeyModal()" style="margin-top: 0.75rem; background: var(--accent-primary); color: #000; font-weight: 700; border: none;">
            Configure Gemini API Key
          </button>
        </div>
      `;
    }
  } finally {
    state.is_generating_synthesis = false;
    state.synthesis_abort_controller = null;
    if (statusEl) statusEl.style.display = "none";
    startAiButtonCooldown(4);
  }
}

// API Key Modal Management
function openApiKeyModal() {
  const modal = document.getElementById("api-key-modal");
  const input = document.getElementById("input-custom-gemini-key");
  const modelSel = document.getElementById("select-gemini-model");
  if (modal) {
    modal.classList.add("open");
  }
  if (input) {
    input.value = localStorage.getItem("trinetri_gemini_key") || "";
    setTimeout(() => {
      input.focus();
      input.select();
    }, 100);
  }
  if (modelSel) {
    modelSel.value = localStorage.getItem("trinetri_gemini_model") || "auto";
  }
  checkAiConfig();
}

function closeApiKeyModal() {
  const modal = document.getElementById("api-key-modal");
  if (modal) {
    modal.classList.remove("open");
  }
}

window.openApiKeyModal = openApiKeyModal;
window.closeApiKeyModal = closeApiKeyModal;

function toggleApiKeyVisibility() {
  const input = document.getElementById("input-custom-gemini-key");
  const btn = document.getElementById("btn-toggle-key-visibility");
  if (!input) return;
  if (input.type === "password") {
    input.type = "text";
    if (btn) btn.textContent = "Hide";
  } else {
    input.type = "password";
    if (btn) btn.textContent = "Show";
  }
}

function saveApiKey() {
  const input = document.getElementById("input-custom-gemini-key");
  const modelSel = document.getElementById("select-gemini-model");
  const val = input ? input.value.trim() : "";
  const modelVal = modelSel ? modelSel.value : "auto";

  if (val) {
    localStorage.setItem("trinetri_gemini_key", val);
    localStorage.setItem("trinetri_gemini_model", modelVal);
    showCopyToast("✓ Gemini API Key saved to browser storage!");
  } else {
    localStorage.removeItem("trinetri_gemini_key");
    localStorage.removeItem("trinetri_gemini_model");
    showCopyToast("Custom Gemini API Key removed.");
  }
  closeApiKeyModal();
  checkAiConfig();
}

function clearApiKey() {
  localStorage.removeItem("trinetri_gemini_key");
  localStorage.removeItem("trinetri_gemini_model");
  const input = document.getElementById("input-custom-gemini-key");
  if (input) input.value = "";
  const modelSel = document.getElementById("select-gemini-model");
  if (modelSel) modelSel.value = "auto";
  showCopyToast("Gemini API Key cleared.");
  checkAiConfig();
}

async function checkAiConfig() {
  const badge = document.getElementById("ai-key-status-badge");
  const headerDot = document.getElementById("header-api-dot");
  const serverInfo = document.getElementById("api-key-server-status-info");
  const modelSel = document.getElementById("select-gemini-model");
  const userKey = localStorage.getItem("trinetri_gemini_key");
  const userModel = localStorage.getItem("trinetri_gemini_model") || "auto";

  try {
    const res = await fetch("/api/ai/config", {
      headers: userKey ? { "X-Gemini-Api-Key": userKey } : {},
    });
    const data = await res.json();
    const hasServerKey = data.has_server_key;
    const defaultModel = data.default_model || "gemini-3.5-flash-lite";
    const available = data.available_models || [];

    // If available models returned, populate select dropdown
    if (modelSel && available.length > 0) {
      const existingVals = new Set(Array.from(modelSel.options).map(o => o.value));
      for (const m of available) {
        if (!existingVals.has(m)) {
          const opt = document.createElement("option");
          opt.value = m;
          opt.textContent = m;
          modelSel.appendChild(opt);
        }
      }
      modelSel.value = userModel;
    }

    if (userKey) {
      const displayModel = userModel === "auto" ? defaultModel : userModel;
      if (badge) {
        badge.className = "status-badge active";
        badge.style.backgroundColor = "";
        badge.style.color = "";
        badge.innerHTML = `<span class="status-dot"></span> User Key Active (${displayModel})`;
      }
      if (headerDot) {
        headerDot.style.background = "#10B981";
      }
      if (serverInfo) {
        serverInfo.innerHTML = `✓ Custom key active in local storage. Active model: <strong>${displayModel}</strong>. (Server default: ${hasServerKey ? "Available" : "None"})`;
      }
    } else if (hasServerKey) {
      if (badge) {
        badge.className = "status-badge active";
        badge.style.backgroundColor = "";
        badge.style.color = "";
        badge.innerHTML = `<span class="status-dot"></span> Server Key Active (${defaultModel})`;
      }
      if (headerDot) {
        headerDot.style.background = "#10B981";
      }
      if (serverInfo) {
        serverInfo.innerHTML = `✓ Using default server GEMINI_API_KEY. Active model: <strong>${defaultModel}</strong>. You may optionally enter your own personal key below.`;
      }
    } else {
      if (badge) {
        badge.className = "status-badge";
        badge.style.backgroundColor = "rgba(245, 158, 11, 0.15)";
        badge.style.color = "#F59E0B";
        badge.innerHTML = '<span class="status-dot warning"></span> Key Missing';
      }
      if (headerDot) {
        headerDot.style.background = "#F59E0B";
      }
      if (serverInfo) {
        serverInfo.innerHTML = `No Gemini API key detected on server. Please enter your Google Gemini API key below to enable AI readings. (Default target: <code>${defaultModel}</code>)`;
      }
    }
  } catch (err) {
    console.warn("Could not check AI config:", err);
    if (headerDot) {
      headerDot.style.background = userKey ? "#10B981" : "#F59E0B";
    }
  }
}

function copyAiSynthesis() {
  const activePersp = state.active_ai_persp || "synthesis";
  let elId = "ai-synthesis-rendered";
  if (activePersp === "parashari") elId = "ai-parashari-rendered";
  else if (activePersp === "kp") elId = "ai-kp-rendered";
  else if (activePersp === "jaimini") elId = "ai-jaimini-rendered";

  const el = document.getElementById(elId);
  if (!el) return;
  const text = el.innerText || el.textContent;
  navigator.clipboard.writeText(text).then(() => {
    alert("Reading copied to clipboard!");
  }).catch(() => {
    alert("Failed to copy reading.");
  });
}

function buildMarkdownFromWhatWhyHow(d) {
  if (!d) return "";
  let md = `# WHAT, WHY AND HOW YOU ARE\n\n`;
  if (d.summary_verdict) md += `> "${d.summary_verdict}"\n\n`;
  if (d.archetype) md += `**Archetype**: ${d.archetype}\n`;
  if (d.constitution) {
    const c = d.constitution;
    md += `**Constitution**: ${c.elements || "-"} | ${c.ayurvedic_prakriti || "-"}\n`;
    md += `- Natural Instinct: ${c.natural_instinct_tag || c.lagna_tag || "-"}\n`;
    md += `- Emotional Core: ${c.emotional_anchor_tag || c.moon_tag || "-"}\n`;
    md += `- Core Drive: ${c.core_drive_tag || c.sun_tag || "-"}\n`;
    md += `- Deepest Hunger: ${c.deepest_hunger_tag || c.atmakaraka_tag || "-"}\n\n`;
  }

  if (d.current_life_season) {
    const s = d.current_life_season;
    md += `## Where You Stand Today (Current Life Season)\n\n`;
    if (s.headline) md += `### ${s.headline}\n\n`;
    if (s.season_summary) md += `${s.season_summary}\n\n`;
    if (s.what_to_lean_into) md += `- **What to Lean Into**: ${s.what_to_lean_into}\n`;
    if (s.what_to_leave_behind) md += `- **What to Leave Behind**: ${s.what_to_leave_behind}\n\n`;
  }

  if (d.dilemma_counsel && (d.dilemma_counsel.seeker_query || d.dilemma_counsel.seeker_situation || d.dilemma_counsel.direct_answer)) {
    const dc = d.dilemma_counsel;
    md += `## Seeker Consultation & Dated Timeline\n\n`;
    if (dc.seeker_query || dc.seeker_situation) md += `**Question**: "${dc.seeker_query || dc.seeker_situation}"\n\n`;
    if (dc.direct_answer) md += `> **Direct Verdict**: ${dc.direct_answer}\n\n`;
    if (dc.exact_timeline) {
      const et = dc.exact_timeline;
      if (et.primary_window) md += `- **Primary Timeline Window**: ${et.primary_window}\n`;
      if (et.secondary_window) md += `- **Secondary Window**: ${et.secondary_window}\n`;
      if (et.active_dasha_trigger) md += `- **Dasha Activation**: ${et.active_dasha_trigger}\n`;
      if (et.transits_trigger) md += `- **Transit Catalyst**: ${et.transits_trigger}\n`;
      md += `\n`;
    }
    if (dc.astrological_reality) md += `**Astrological Mechanism**: ${dc.astrological_reality}\n\n`;
    if (dc.mentor_guidance || dc.mentor_verdict) md += `**Practical Mentor Guidance**: ${dc.mentor_guidance || dc.mentor_verdict}\n\n`;
  }

  if (d.traits) {
    md += `## 1. Constitutional Traits & Wiring\n\n`;
    const tMap = { physical: "Physical & Vitality", emotional: "Emotional Architecture", mental: "Intellect & Problem-Solving", social: "Social Radar & Boundaries" };
    for (const [key, label] of Object.entries(tMap)) {
      const item = d.traits[key];
      if (!item) continue;
      md += `### ${label}\n`;
      if (item.bottom_line) md += `> "${item.bottom_line}"\n\n`;
      if (item.headline) md += `**${item.headline}**\n\n`;
      if (item.description) md += `${item.description}\n\n`;
      if (Array.isArray(item.key_points) && item.key_points.length) {
        item.key_points.forEach(pt => { md += `- ${pt}\n`; });
        md += `\n`;
      }
    }
  }
  if (d.the_why) {
    md += `## 2. The Why: Inner Paradox & Growth Engine\n\n`;
    if (d.the_why.inner_paradox) {
      md += `### ${d.the_why.inner_paradox.headline || d.the_why.inner_paradox.title || "The Inner Paradox"}\n${d.the_why.inner_paradox.explanation || ""}\n\n`;
    }
    if (d.the_why.driving_hunger) {
      md += `### ${d.the_why.driving_hunger.headline || d.the_why.driving_hunger.title || "Core Driving Motivation"}\n${d.the_why.driving_hunger.explanation || ""}\n\n`;
    }
    const karmic = d.the_why.comfort_zone_vs_growth_edge || d.the_why.karmic_axis;
    if (karmic) {
      md += `### ${karmic.headline || karmic.title || "Comfort Zone vs. Growth Edge"}\n`;
      if (karmic.comfort_zone) {
        md += `- **Comfort Trap**: ${karmic.comfort_zone}\n`;
        md += `- **Growth Edge**: ${karmic.growth_edge}\n\n`;
      } else {
        md += `${karmic.explanation || ""}\n\n`;
      }
    }
  }
  if (d.qualities) {
    md += `## 3. Qualities: Superpowers vs Shadows\n\n`;
    if (Array.isArray(d.qualities.superpowers) && d.qualities.superpowers.length) {
      md += `### Superpowers\n\n`;
      d.qualities.superpowers.forEach(sp => {
        md += `- **${sp.name || sp.title || "Superpower"}**: ${sp.description || ""}`;
        if (sp.manifestation) md += ` *(Real-world: ${sp.manifestation})*`;
        md += `\n`;
      });
      md += `\n`;
    }
    if (Array.isArray(d.qualities.shadows) && d.qualities.shadows.length) {
      md += `### Shadows & Blindspots\n\n`;
      d.qualities.shadows.forEach(sh => {
        md += `- **${sh.name || sh.title || "Shadow"}**: ${sh.description || ""}`;
        if (sh.antidote) md += ` *(Antidote: ${sh.antidote})*`;
        md += `\n`;
      });
      md += `\n`;
    }
  }
  if (d.operating_manual) {
    const man = d.operating_manual;
    md += `## 4. Personal Operating Manual\n\n`;
    if (man.stress_response) {
      md += `### Stress & Burnout Protocol\n`;
      md += `- Trigger: ${man.stress_response.trigger || "-"}\n`;
      md += `- Reaction: ${man.stress_response.reaction || "-"}\n`;
      md += `- Recovery: ${man.stress_response.recovery || "-"}\n\n`;
    }
    if (Array.isArray(man.energizers) && man.energizers.length) {
      md += `### Vitality Energizers\n`;
      man.energizers.forEach(en => { md += `- [+] ${en}\n`; });
      md += `\n`;
    }
    if (Array.isArray(man.drainers) && man.drainers.length) {
      md += `### Vitality Drainers\n`;
      man.drainers.forEach(dr => { md += `- [-] ${dr}\n`; });
      md += `\n`;
    }
    if (man.decision_style) {
      md += `### Decision Instinct\n${man.decision_style}\n\n`;
    }
  }
  if (d.growth_levers) {
    const gl = d.growth_levers;
    md += `## 5. Evolutionary Growth Levers\n\n`;
    if (gl.golden_lever) md += `- **The Single Multiplier Habit**: ${gl.golden_lever}\n`;
    if (gl.habit_to_unlearn) md += `- **The Critical Unlearn**: ${gl.habit_to_unlearn}\n`;
    if (gl.grounding_practice) md += `- **Daily Grounding Anchor**: ${gl.grounding_practice}\n`;
    md += `\n`;
  }
  if (d.astrological_proof) {
    md += `## 6. Classical Astrological Footnotes & Technical Derivations\n\n${d.astrological_proof}\n`;
  }
  return md;
}

function buildMarkdownFromCraftWealth(d) {
  if (!d) return "";
  let md = `# CRAFT, WEALTH & PUBLIC CALLING\n\n`;
  if (d.summary_verdict) md += `> "${d.summary_verdict}"\n\n`;
  if (d.vocation_archetype) md += `**Vocation Archetype**: ${d.vocation_archetype}\n`;
  if (d.enterprise_vs_employment?.recommended_path) md += `**Recommended Path**: ${d.enterprise_vs_employment.recommended_path}\n`;
  if (d.wealth_engine?.wealth_archetype) md += `**Wealth Style**: ${d.wealth_engine.wealth_archetype}\n`;
  if (d.timing_weather?.current_season_headline) md += `**Current Chapter**: ${d.timing_weather.current_season_headline}\n\n`;

  if (d.dilemma_counsel && (d.dilemma_counsel.seeker_query || d.dilemma_counsel.seeker_situation || d.dilemma_counsel.direct_answer)) {
    const dc = d.dilemma_counsel;
    md += `## Career Consultation & Dated Timeline\n\n`;
    if (dc.seeker_query || dc.seeker_situation) md += `**Question**: "${dc.seeker_query || dc.seeker_situation}"\n\n`;
    if (dc.direct_answer) md += `> **Direct Verdict**: ${dc.direct_answer}\n\n`;
    if (dc.exact_timeline) {
      const et = dc.exact_timeline;
      if (et.primary_window) md += `- **Primary Timeline Window**: ${et.primary_window}\n`;
      if (et.secondary_window) md += `- **Secondary Window**: ${et.secondary_window}\n`;
      if (et.active_dasha_trigger) md += `- **Dasha Activation**: ${et.active_dasha_trigger}\n`;
      if (et.transits_trigger) md += `- **Transit Catalyst**: ${et.transits_trigger}\n`;
      md += `\n`;
    }
    if (dc.astrological_reality) md += `**Astrological Mechanism**: ${dc.astrological_reality}\n\n`;
    if (dc.mentor_guidance || dc.mentor_verdict) md += `**Practical Mentor Guidance**: ${dc.mentor_guidance || dc.mentor_verdict}\n\n`;
  }

  if (d.work_genius) {
    const g = d.work_genius;
    md += `## 1. Your Natural Work Genius & Flow\n\n`;
    if (g.craft_essence) {
      md += `### ${g.craft_essence.headline || "Core Work Genius"}\n${g.craft_essence.description || ""}\n`;
      if (g.craft_essence.real_world_scenario) md += `> *Tuesday morning test: ${g.craft_essence.real_world_scenario}*\n\n`;
    }
    if (g.autonomy_vs_hierarchy) {
      md += `### ${g.autonomy_vs_hierarchy.headline || "How Much Freedom You Need"}\n${g.autonomy_vs_hierarchy.stance || ""}\n`;
      if (g.autonomy_vs_hierarchy.friction_trigger) md += `> *What drains your drive: ${g.autonomy_vs_hierarchy.friction_trigger}*\n\n`;
    }
    if (g.flow_state_trigger) {
      md += `### ${g.flow_state_trigger.headline || "When You're in the Zone"}\n${g.flow_state_trigger.conditions || ""}\n\n`;
    }
    if (g.ideal_work_environment) {
      md += `### ${g.ideal_work_environment.headline || "The Work Environment You Need"}\n${g.ideal_work_environment.description || ""}\n\n`;
    }
  }

  if (d.leadership_and_authority) {
    const l = d.leadership_and_authority;
    md += `## 2. How You Lead & How Others See You\n\n`;
    if (l.leadership_stance) {
      md += `### ${l.leadership_stance.headline || "How You Lead"}\n${l.leadership_stance.style || ""}\n`;
      if (l.leadership_stance.how_others_perceive_you) md += `> *How others actually see you: ${l.leadership_stance.how_others_perceive_you}*\n\n`;
    }
    if (l.office_politics_reflex) {
      md += `### ${l.office_politics_reflex.headline || "How You Handle Workplace Politics"}\n${l.office_politics_reflex.reflex || ""}\n`;
      if (l.office_politics_reflex.antidote) md += `> *How to protect yourself: ${l.office_politics_reflex.antidote}*\n\n`;
    }
    if (l.delegation_tripwire) {
      md += `### ${l.delegation_tripwire.headline || "The Delegation & Trust Trap"}\n${l.delegation_tripwire.trap || ""}\n`;
      if (l.delegation_tripwire.fix) md += `> *How to fix this: ${l.delegation_tripwire.fix}*\n\n`;
    }
    if (l.public_presence) {
      md += `### ${l.public_presence.headline || "Public Reputation vs. Private Reality"}\n`;
      md += `- **What People See Outside**: ${l.public_presence.external_reputation || ""}\n`;
      md += `- **What You Feel Inside**: ${l.public_presence.internal_reality || ""}\n\n`;
    }
  }

  if (d.wealth_engine) {
    const w = d.wealth_engine;
    md += `## 3. How Money & Wealth Work for You\n\n`;
    if (w.primary_inflow_channel) {
      md += `### Where Money Flows Naturally: ${w.primary_inflow_channel.headline || ""}\n${w.primary_inflow_channel.description || ""}\n\n`;
    }
    if (w.unconscious_financial_leak) {
      md += `### The Hidden Money Leak: ${w.unconscious_financial_leak.headline || ""}\n${w.unconscious_financial_leak.leak_pattern || ""}\n`;
      if (w.unconscious_financial_leak.antidote) md += `> *How to plug this leak: ${w.unconscious_financial_leak.antidote}*\n\n`;
    }
    if (w.monetization_rule) {
      md += `### Your Golden Money Rule\n> ${w.monetization_rule.rule || w.monetization_rule.headline || ""}\n\n`;
    }
  }

  if (d.enterprise_vs_employment) {
    const e = d.enterprise_vs_employment;
    md += `## 4. Building Your Own Thing vs. Working for Others\n\n`;
    md += `**Your Natural Fit**: ${e.recommended_path || ""}\n`;
    if (e.optimal_vehicle) md += `**Best Career Setup**: ${e.optimal_vehicle}\n`;
    if (e.strategic_rationale) md += `\n${e.strategic_rationale}\n\n`;
    if (e.transition_guardrail) md += `> *Watch out for this before switching: ${e.transition_guardrail}*\n\n`;
  }

  if (d.timing_weather) {
    const t = d.timing_weather;
    md += `## 5. Where Your Career Is Heading (Next 24 Months)\n\n`;
    if (t.current_season_headline) md += `### Current Work Chapter: ${t.current_season_headline}\n${t.current_phase_nature || ""}\n\n`;
    if (Array.isArray(t.windows) && t.windows.length) {
      t.windows.forEach(w => {
        md += `#### ${w.window_label || "Window"}: ${w.phase_title || ""}\n`;
        if (w.focus) md += `- **What to Focus On**: ${w.focus}\n`;
        if (w.caution) md += `- **What to Avoid**: ${w.caution}\n`;
        md += `\n`;
      });
    }
  }

  if (d.tactical_levers) {
    const tl = d.tactical_levers;
    md += `## 6. Practical Work Rules for Everyday Life\n\n`;
    if (tl.golden_career_lever) md += `- **The Single Best Career Habit**: ${tl.golden_career_lever}\n`;
    if (tl.trap_to_eliminate) md += `- **The Work Habit to Unlearn**: ${tl.trap_to_eliminate}\n`;
    if (tl.negotiation_mantra) md += `- **When Talking Money & Recognition**: ${tl.negotiation_mantra}\n\n`;
  }

  if (d.astrological_proof) {
    md += `## Classical Astrological Footnotes & Technical Derivations\n\n${d.astrological_proof}\n`;
  }

  return md;
}
window.buildMarkdownFromCraftWealth = buildMarkdownFromCraftWealth;

function buildSchoolEyeMarkdown(d, schoolType) {
  if (!d) return "";
  const schoolNames = { parashari: "Parashari (BPHS)", kp: "KP Stellar", jaimini: "Jaimini Sutras" };
  const sName = schoolNames[schoolType] || (schoolType ? schoolType.toUpperCase() : "VEDIC EYE");
  let md = `# ${sName.toUpperCase()} EVALUATION\n\n`;
  if (d.summary_verdict) md += `> "${d.summary_verdict}"\n\n`;
  if (d.archetype) md += `**Archetype**: ${d.archetype}\n\n`;
  if (d.metrics) {
    md += `## Astrological Metrics\n\n`;
    for (const [k, v] of Object.entries(d.metrics)) {
      md += `- **${k.replace(/_/g, " ").toUpperCase()}**: ${v}\n`;
    }
    md += `\n`;
  }
  if (d.what_you_are) {
    md += `## 1. What You Are\n\n`;
    if (d.what_you_are.headline) md += `**${d.what_you_are.headline}**\n\n`;
    if (d.what_you_are.bottom_line) md += `> "${d.what_you_are.bottom_line}"\n\n`;
    const traits = Array.isArray(d.what_you_are.traits) ? d.what_you_are.traits : [];
    if (traits.length) {
      traits.forEach(t => { md += `- ${t}\n`; });
      md += `\n`;
    }
  }
  if (d.why_you_are) {
    md += `## 2. Why You Are\n\n`;
    if (d.why_you_are.headline) md += `**${d.why_you_are.headline}**\n\n`;
    const strengths = Array.isArray(d.why_you_are.strengths) ? d.why_you_are.strengths : [];
    if (strengths.length) {
      md += `### Core Gifts & Strategic Advantages\n\n`;
      strengths.forEach(s => {
        md += `- **${s.name || "Gift"}**: ${s.description || ""}`;
        if (s.manifestation) md += ` *(Real-world: ${s.manifestation})*`;
        md += `\n`;
      });
      md += `\n`;
    }
    const frictions = Array.isArray(d.why_you_are.friction_points) ? d.why_you_are.friction_points : [];
    if (frictions.length) {
      md += `### Friction Points & Blindspots\n\n`;
      frictions.forEach(f => {
        md += `- **${f.name || "Friction"}**: ${f.description || ""}`;
        if (f.antidote) md += ` *(Antidote: ${f.antidote})*`;
        md += `\n`;
      });
      md += `\n`;
    }
  }
  if (d.how_you_operate) {
    md += `## 3. How You Operate\n\n`;
    const h = d.how_you_operate;
    if (h.headline) md += `**${h.headline}**\n\n`;
    if (h.operating_dasha_rhythm) md += `- **Operating Life Season**: ${h.operating_dasha_rhythm}\n`;
    if (h.primary_energizer) md += `- **Peak Energizer**: ${h.primary_energizer}\n`;
    if (h.primary_burnout_trigger) md += `- **Burnout Trigger**: ${h.primary_burnout_trigger}\n`;
    if (h.golden_directive) md += `- **Golden Directive**: ${h.golden_directive}\n`;
    md += `\n`;
  }
  if (d.astrological_proof) {
    md += `## 4. Technical Astrological Proof\n\n${d.astrological_proof}\n`;
  }
  return md;
}

function downloadAiSynthesis() {
  const chartSig = getActiveChartSignature();
  const fileSlug = `${state.year}-${state.month}-${state.day}_${(state.city || "").replace(/[^a-zA-Z0-9]/g, '_')}`;
  const customQuery = document.getElementById("ai-custom-query-input")?.value.trim() || "";
  const cacheKey = `${chartSig}_${state.selected_pillar}_${customQuery}`;
  const cached = state.ai_readings_cache[cacheKey];
  const activePersp = state.active_ai_persp || "synthesis";

  let content = "";
  let filename = `TrinetriAI_${state.selected_pillar}_${fileSlug}.md`;

  if (activePersp !== "synthesis") {
    filename = `TrinetriAI_${activePersp.toUpperCase()}_${state.selected_pillar}_${fileSlug}.md`;
    const eyeRaw = cached?.eyeVerdicts?.[activePersp];
    if (eyeRaw) {
      const { metadata } = extractConfluenceMetadata(eyeRaw);
      if (metadata && (metadata.what_you_are || metadata.metrics || metadata.why_you_are || metadata.traits)) {
        content = buildSchoolEyeMarkdown(metadata, activePersp);
      } else {
        content = eyeRaw;
      }
    } else {
      content = document.getElementById(`ai-${activePersp}-rendered`)?.innerText || "";
    }
  } else {
    if (cached && cached.fullSynthesisMarkdown) {
      const { metadata } = extractConfluenceMetadata(cached.fullSynthesisMarkdown);
      if (metadata && (metadata.work_genius || metadata.vocation_archetype || metadata.wealth_engine)) {
        content = buildMarkdownFromCraftWealth(metadata);
      } else if (metadata && (metadata.traits || metadata.the_why || metadata.archetype || metadata.qualities)) {
        content = buildMarkdownFromWhatWhyHow(metadata);
      } else {
        content = cached.fullSynthesisMarkdown;
      }
    } else {
      content = document.getElementById("ai-synthesis-rendered")?.innerText || "";
    }
  }
  
  const blob = new Blob([content], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// Floating Chat Drawer Controller
function toggleChatDrawer() {
  const drawer = document.getElementById("trinetri-chat-drawer");
  if (!drawer) return;
  const isHidden = drawer.style.display === "none" || !drawer.style.display;
  drawer.style.display = isHidden ? "flex" : "none";
  if (isHidden) {
    document.getElementById("chat-input-textarea")?.focus();
    scrollChatToBottom();
  }
}

function openChatDrawer() {
  const drawer = document.getElementById("trinetri-chat-drawer");
  if (drawer) {
    drawer.style.display = "flex";
    document.getElementById("chat-input-textarea")?.focus();
    scrollChatToBottom();
  }
}

function closeChatDrawer() {
  const drawer = document.getElementById("trinetri-chat-drawer");
  if (drawer) drawer.style.display = "none";
}

function clearChatMessages() {
  state.chat_messages = [];
  const container = document.getElementById("chat-messages-container");
  if (container) {
    container.innerHTML = `
      <div class="chat-msg system-msg">
        ✦ Conversation cleared. Your complete astrological dossier remains loaded. Ask any question to begin.
      </div>
      <div class="chat-starter-chips" id="chat-starter-chips">
        <button type="button" class="chat-starter-chip" onclick="askSuggestedChatQuestion('Why do I feel pulled in two directions right now?')">Why do I feel pulled in two directions right now?</button>
        <button type="button" class="chat-starter-chip" onclick="askSuggestedChatQuestion('What kind of work environment actually fits how I\\'m wired?')">What kind of work environment actually fits how I'm wired?</button>
        <button type="button" class="chat-starter-chip" onclick="askSuggestedChatQuestion('What is my biggest blindspot in close relationships?')">What is my biggest blindspot in close relationships?</button>
        <button type="button" class="chat-starter-chip" onclick="askSuggestedChatQuestion('When does this current heavy phase start to ease up?')">When does this current heavy phase start to ease up?</button>
      </div>
    `;
  }
}

function askSuggestedChatQuestion(questionText) {
  const textarea = document.getElementById("chat-input-textarea");
  if (textarea) {
    textarea.value = questionText;
  }
  const chips = document.getElementById("chat-starter-chips");
  if (chips) {
    chips.style.display = "none";
  }
  sendChatMessage();
}
window.askSuggestedChatQuestion = askSuggestedChatQuestion;

function scrollChatToBottom() {
  const container = document.getElementById("chat-messages-container");
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

function appendChatBubble(role, content) {
  const container = document.getElementById("chat-messages-container");
  if (!container) return null;

  const bubble = document.createElement("div");
  bubble.className = `chat-msg ${role === "user" ? "user-msg" : "ai-msg"}`;
  bubble.innerHTML = role === "user" ? content : formatMarkdown(content);
  container.appendChild(bubble);
  scrollChatToBottom();
  return bubble;
}

function getActiveReadingContextForChat() {
  const chartSig = getActiveChartSignature();
  const customQuery = document.getElementById("ai-custom-query-input")?.value.trim() || "";
  const pillarKey = `${chartSig}_${state.selected_pillar}_${customQuery}`;
  const compKey = `${chartSig}_comprehensive_`;

  const cached = state.ai_readings_cache[pillarKey] || state.ai_readings_cache[compKey];
  if (!cached || !cached.fullSynthesisMarkdown) return null;

  const { metadata, cleanMarkdown } = extractConfluenceMetadata(cached.fullSynthesisMarkdown);
  if (metadata && (metadata.work_genius || metadata.vocation_archetype || metadata.wealth_engine)) {
    const text = buildMarkdownFromCraftWealth(metadata);
    return text.slice(0, 3500);
  }
  if (metadata && (metadata.traits || metadata.the_why || metadata.archetype || metadata.qualities)) {
    const text = buildMarkdownFromWhatWhyHow(metadata);
    return text.slice(0, 3500);
  }
  return (cleanMarkdown || "").slice(0, 3500);
}

async function sendChatMessage() {
  if (state.is_sending_chat) return;
  const textarea = document.getElementById("chat-input-textarea");
  if (!textarea) return;
  const text = textarea.value.trim();
  if (!text) return;

  const d = state.currentData;
  if (!d) {
    alert("Please calculate a chart first before consulting.");
    return;
  }

  // Clear input
  textarea.value = "";
  textarea.style.height = "auto";

  // Hide starter chips once user starts chatting
  const chips = document.getElementById("chat-starter-chips");
  if (chips) chips.style.display = "none";

  // Append user bubble
  appendChatBubble("user", text);
  state.chat_messages.push({ role: "user", content: text });

  // Append placeholder AI bubble
  const aiBubble = appendChatBubble("ai", '<span class="ai-spinner" style="width: 12px; height: 12px;"></span> Consulting planetary anchors...');
  state.is_sending_chat = true;

  const userKey = localStorage.getItem("trinetri_gemini_key") || "";

  const payload = {
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
      gender: state.gender,
      chart_style: state.chart_style,
      sign_mode: state.sign_mode,
      theme_mode: state.theme_mode,
      selected_varga: state.selected_varga,
      show_gochar: state.show_gochar,
      target_date: state.target_date,
    },
    messages: state.chat_messages,
    user_api_key: userKey || null,
    model: (localStorage.getItem("trinetri_gemini_model") && localStorage.getItem("trinetri_gemini_model") !== "auto") ? localStorage.getItem("trinetri_gemini_model") : null,
    active_reading_summary: getActiveReadingContextForChat(),
  };

  if (state.chat_abort_controller) {
    try { state.chat_abort_controller.abort(); } catch (_) {}
  }
  state.chat_abort_controller = new AbortController();

  let assistantResponse = "";

  try {
    const res = await fetch("/api/ai/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: state.chat_abort_controller.signal,
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail || `Server error (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop();

      for (const rawEvt of events) {
        if (!rawEvt.trim()) continue;
        const lines = rawEvt.split("\n");
        let eventName = "message";
        let eventData = "";

        for (const line of lines) {
          if (line.startsWith("event: ")) eventName = line.substring(7).trim();
          else if (line.startsWith("data: ")) eventData = line.substring(6).trim();
        }

        if (eventName === "token") {
          try {
            const parsed = JSON.parse(eventData);
            assistantResponse += parsed.token;
            aiBubble.innerHTML = formatMarkdown(assistantResponse);
            scrollChatToBottom();
          } catch (_) {}
        } else if (eventName === "error") {
          try {
            const parsed = JSON.parse(eventData);
            throw new Error(parsed.error);
          } catch (e) {
            throw new Error(eventData || "Chat streaming error");
          }
        }
      }
    }

    state.chat_messages.push({ role: "assistant", content: assistantResponse });
    // Keep max 20 messages in active session memory
    if (state.chat_messages.length > 20) {
      state.chat_messages = state.chat_messages.slice(-20);
    }

  } catch (err) {
    if (err.name === "AbortError") {
      console.log("Chat generation cancelled.");
      return;
    }
    console.error("Chat error:", err);
    let errMsg = err.message || "Failed to get response.";
    if (errMsg.includes("Gemini API Key is not configured") || errMsg.includes("API key not valid")) {
      errMsg = 'Gemini API Key is not configured. <button onclick="openApiKeyModal()" class="action-pill" style="display:inline-block; margin-top:0.35rem; font-size:0.75rem; background:var(--accent-primary); color:#000; font-weight:700; border:none; cursor:pointer;">⚙️ Configure Gemini Key</button>';
    }
    aiBubble.innerHTML = `<span style="color: #EF4444; line-height: 1.5; display: block;">⚠️ ${errMsg}</span>`;
  } finally {
    state.is_sending_chat = false;
    state.chat_abort_controller = null;
  }
}

// Window bindings
window.copyAiSynthesis = copyAiSynthesis;
window.downloadAiSynthesis = downloadAiSynthesis;
window.openApiKeyModal = openApiKeyModal;
window.closeApiKeyModal = closeApiKeyModal;
window.triggerAiSynthesis = triggerAiSynthesis;
window.toggleLifeProof = toggleLifeProof;

// --- Initialization & Event Listeners ---

document.addEventListener("DOMContentLoaded", () => {
  initDateTimeDropdowns();

  // Tab navigation
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
      } else if (tabId === "ai-consult") {
        renderAiConsultationWorkspace();
      }
    });
  });

  // Transit toggle
  document.querySelectorAll(".gochar-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.show_gochar = !state.show_gochar;
      updateGocharButtonStates();
      calculateChart();
    });
  });

  // Target date picker for transits and dashas
  document.getElementById("btn-target-date-apply")?.addEventListener("click", () => {
    const val = document.getElementById("input-target-date")?.value;
    if (val) {
      state.target_date = val;
      calculateChart();
    }
  });

  document.getElementById("btn-target-date-now")?.addEventListener("click", () => {
    state.target_date = null;
    const inp = document.getElementById("input-target-date");
    if (inp) inp.value = "";
    calculateChart();
  });

  // Varga selection shortcuts
  document.querySelectorAll(".quick-varga-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectVarga(btn.dataset.varga);
    });
  });

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

    state.gender = document.getElementById("select-birth-gender")?.value || "male";
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

      state.gender = document.getElementById("select-quick-gender")?.value || "male";
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

  // 16b. AI Dossier Modal Trigger and Close
  document.getElementById("btn-ai-dossier")?.addEventListener("click", openAiDossierModal);
  document.getElementById("ai-dossier-close-btn")?.addEventListener("click", closeAiDossierModal);
  document.getElementById("ai-dossier-modal")?.addEventListener("click", (e) => {
    if (e.target.id === "ai-dossier-modal") closeAiDossierModal();
  });

  // 16c. AI Consultation & Multi-Agent Event Listeners
  checkAiConfig();

  document.querySelectorAll(".ai-pillar-card").forEach(card => {
    card.addEventListener("click", () => {
      selectAiPillar(card.dataset.pillar);
    });
  });

  document.querySelectorAll(".ai-persp-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      selectAiPerspective(btn.dataset.persp);
    });
  });

  document.getElementById("ai-generate-synthesis-btn")?.addEventListener("click", triggerAiSynthesis);
  document.getElementById("btn-recalc-synthesis")?.addEventListener("click", triggerAiSynthesis);

  document.getElementById("ai-custom-query-input")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      triggerAiSynthesis();
    }
  });

  // API Key Settings Modal
  document.getElementById("btn-header-api-key")?.addEventListener("click", openApiKeyModal);
  document.getElementById("chat-api-key-btn")?.addEventListener("click", openApiKeyModal);
  document.getElementById("btn-open-api-key-modal")?.addEventListener("click", openApiKeyModal);
  document.getElementById("api-key-modal-close")?.addEventListener("click", closeApiKeyModal);
  document.getElementById("btn-save-api-key")?.addEventListener("click", saveApiKey);
  document.getElementById("btn-clear-api-key")?.addEventListener("click", clearApiKey);
  document.getElementById("btn-toggle-key-visibility")?.addEventListener("click", toggleApiKeyVisibility);
  document.getElementById("input-custom-gemini-key")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      saveApiKey();
    }
  });
  document.getElementById("api-key-modal")?.addEventListener("click", (e) => {
    if (e.target.id === "api-key-modal") closeApiKeyModal();
  });

  // Floating Chat Drawer Listeners
  document.getElementById("trinetri-floating-chat-btn")?.addEventListener("click", toggleChatDrawer);
  document.getElementById("chat-close-btn")?.addEventListener("click", closeChatDrawer);
  document.getElementById("chat-minimize-btn")?.addEventListener("click", toggleChatDrawer);
  document.getElementById("chat-clear-btn")?.addEventListener("click", clearChatMessages);
  document.getElementById("chat-input-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    sendChatMessage();
  });
  document.getElementById("chat-input-textarea")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });

  // 16d. Keyboard ESC Handler for Modals and Drawer
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeAiDossierModal();
      closePlanetDrawer();
      closeBirthModal();
      closeApiKeyModal();
      closeChatDrawer();
    }
  });

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
